"""
data_manager.py – Data access: SQLite ledger, workbook source, CRUD, audit log.

Two data sources exist:
  * Carbon_Emission_Data.xlsx – company-year totals used by the analytics pages
    (approved emissions) whenever the workbook is present.
  * data/emissions.db – the operational ledger that receives data-entry
    submissions, the approval queue and the activity log.
"""
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from data.emission_factors import (
    ALL_FACTORS, CARBON_TAX_RATE_MYR, COMPANIES, SCOPE1_SOURCES, SCOPE2_SOURCES,
)
from utils.analytics import detect_anomaly
from utils.carbon_calculator import KG_PER_TONNE, calculate_emission
from utils.config import (
    ACTIVITY_LOG_LIMIT, CARBON_EMISSION_DATA_PATH, DATABASE_PATH, DB_TIMEOUT_SECONDS,
)
from utils.seed_data import EMISSION_COLUMNS, generate_seed_records

DB_PATH = str(DATABASE_PATH)
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

WORKBOOK_SOURCE_NAME = "Carbon_Emission_Data"
WORKBOOK_REQUIRED_COLUMNS = frozenset({
    "company", "year", "scope1_mt_co2e", "scope2_location_mt_co2e",
    "scope1_plus_2_mt_co2e", "employees_000s", "data_notes",
})
WORKBOOK_SCOPE_COLUMNS = (
    (1, "scope1_mt_co2e", "Scope 1"),
    (2, "scope2_location_mt_co2e", "Scope 2"),
)
WORKBOOK_DATA_QUALITY_ISSUES = (
    "The workbook has company-year totals only; it does not contain facility-level records, "
    "emission sources, activity quantities, or transaction-level dates.",
    "Scope 2 is location-based only. Market-based Scope 2 data is not available.",
)

# Columns a pending submission carries over into the ledger on approval.
_SUBMISSION_FIELDS = (
    "date", "facility", "scope", "source", "unit", "quantity", "co2e_kg",
    "submitted_by", "submitted_at", "notes",
)

_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS emissions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        date        TEXT NOT NULL,
        facility    TEXT NOT NULL,
        scope       INTEGER NOT NULL,
        source      TEXT NOT NULL,
        unit        TEXT NOT NULL,
        quantity    REAL NOT NULL,
        co2e_kg     REAL NOT NULL,
        submitted_by TEXT NOT NULL,
        submitted_at TEXT NOT NULL,
        status      TEXT DEFAULT 'approved',
        approved_by TEXT,
        approved_at TEXT,
        notes       TEXT,
        is_anomaly  INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pending_submissions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        date        TEXT NOT NULL,
        facility    TEXT NOT NULL,
        scope       INTEGER NOT NULL,
        source      TEXT NOT NULL,
        unit        TEXT NOT NULL,
        quantity    REAL NOT NULL,
        co2e_kg     REAL NOT NULL,
        submitted_by TEXT NOT NULL,
        submitted_at TEXT NOT NULL,
        notes       TEXT,
        anomaly_reason TEXT,
        status      TEXT DEFAULT 'pending'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS activity_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp   TEXT NOT NULL,
        username    TEXT NOT NULL,
        action      TEXT NOT NULL,
        details     TEXT
    )
    """,
)


def _now() -> str:
    return datetime.now().strftime(TIMESTAMP_FORMAT)


# ── Connection ─────────────────────────────────────────────────────────────────
@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """Open a connection that commits on success and rolls back on error."""
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT_SECONDS)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _insert(conn: sqlite3.Connection, table: str, row: dict[str, Any]) -> None:
    """INSERT one row; ``table`` and the keys are internal names, never user input."""
    placeholders = ",".join("?" * len(row))
    conn.execute(f"INSERT INTO {table} ({', '.join(row)}) VALUES ({placeholders})", tuple(row.values()))


def _read_frame(query: str, params: tuple = ()) -> pd.DataFrame:
    with _connect() as conn:
        return pd.read_sql(query, conn, params=params)


# ── Schema initialisation ──────────────────────────────────────────────────────
def init_db() -> None:
    """Create tables if needed and seed synthetic data into an empty ledger."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        for statement in _SCHEMA:
            conn.execute(statement)
        is_empty = conn.execute("SELECT COUNT(*) FROM emissions").fetchone()[0] == 0
        if is_empty:
            placeholders = ",".join("?" * len(EMISSION_COLUMNS))
            conn.executemany(
                f"INSERT INTO emissions ({', '.join(EMISSION_COLUMNS)}) VALUES ({placeholders})",
                generate_seed_records(),
            )


# ── Read helpers ───────────────────────────────────────────────────────────────
def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["carbon_tax_myr"] = (df["co2e_kg"] / KG_PER_TONNE) * CARBON_TAX_RATE_MYR
    return df


@lru_cache(maxsize=4)
def _read_workbook(path: str, modified_ns: int) -> pd.DataFrame:
    """Parse the workbook once per file version (``modified_ns`` busts the cache)."""
    workbook = pd.read_excel(path)
    missing = sorted(WORKBOOK_REQUIRED_COLUMNS - set(workbook.columns))
    if missing:
        raise ValueError(
            f"{CARBON_EMISSION_DATA_PATH.name} is missing required columns: " + ", ".join(missing)
        )

    rows = []
    for record in workbook.to_dict("records"):
        period = pd.Timestamp(year=int(record["year"]), month=1, day=1)
        common = {
            "date": period,
            "facility": str(record["company"]),
            "unit": "tonnes CO2e",
            "quantity": 1.0,
            "submitted_by": WORKBOOK_SOURCE_NAME,
            "submitted_at": period,
            "status": "approved",
            "approved_by": WORKBOOK_SOURCE_NAME,
            "approved_at": period,
            "notes": str(record["data_notes"]),
            "is_anomaly": 0,
            "employees_000s": float(record["employees_000s"]),
        }
        for scope, column, source in WORKBOOK_SCOPE_COLUMNS:
            rows.append({
                **common,
                "scope": scope,
                "source": source,
                "co2e_kg": float(record[column]) * KG_PER_TONNE,
            })

    df = pd.DataFrame(rows)
    df["id"] = range(1, len(df) + 1)
    df = _add_derived_columns(df)
    df.attrs["data_quality_issues"] = list(WORKBOOK_DATA_QUALITY_ISSUES)
    return df.sort_values("date", ascending=False).reset_index(drop=True)


def _load_workbook_emissions() -> pd.DataFrame:
    modified_ns = CARBON_EMISSION_DATA_PATH.stat().st_mtime_ns
    # Callers may add columns, so never hand out the cached frame itself.
    return _read_workbook(str(CARBON_EMISSION_DATA_PATH), modified_ns).copy()


def load_database_emissions(status: str = "approved") -> pd.DataFrame:
    """Emission records from the SQLite ledger (data-entry submissions)."""
    df = _read_frame("SELECT * FROM emissions WHERE status=? ORDER BY date DESC", (status,))
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["submitted_at"] = pd.to_datetime(df["submitted_at"])
        _add_derived_columns(df)
    return df


def load_emissions() -> pd.DataFrame:
    """
    Approved emission records for the analytics pages: the workbook when
    present, otherwise the SQLite ledger.
    """
    if CARBON_EMISSION_DATA_PATH.exists():
        return _load_workbook_emissions()
    return load_database_emissions()


def _load_submissions(status: str | None = None) -> pd.DataFrame:
    """Anomalous submissions, optionally limited to one status."""
    df = _read_frame(
        "SELECT * FROM pending_submissions WHERE (? IS NULL OR status = ?) ORDER BY submitted_at DESC",
        (status, status),
    )
    if not df.empty:
        df["submitted_at"] = pd.to_datetime(df["submitted_at"])
    return df


def load_pending() -> pd.DataFrame:
    """Anomalous submissions still awaiting a decision."""
    return _load_submissions("pending")


def load_all_pending() -> pd.DataFrame:
    """Every anomalous submission regardless of outcome."""
    return _load_submissions()


def load_activity_log() -> pd.DataFrame:
    return _read_frame(
        "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?", (ACTIVITY_LOG_LIMIT,)
    )


# ── Write helpers ──────────────────────────────────────────────────────────────
def submit_emission(data: dict[str, Any], username: str) -> dict[str, Any]:
    """
    Submit a new emission record. Normal values go straight into the ledger;
    anomalous ones are queued for manager approval.
    Returns {'inserted': True, 'anomaly': bool, 'reason': str, 'co2e_kg': float}.
    Raises ValueError for invalid input.
    """
    _validate_submission(data, username)
    source = data["source"]
    qty = float(data["quantity"])
    co2e = calculate_emission(source, qty)
    row = {
        "date": data["date"], "facility": data["facility"], "scope": data["scope"],
        "source": source, "unit": ALL_FACTORS[source]["unit"], "quantity": qty, "co2e_kg": co2e,
        "submitted_by": username, "submitted_at": _now(), "notes": data.get("notes", ""),
    }
    anomaly, reason = detect_anomaly(_approved_history(source), co2e, source)

    with _connect() as conn:
        if anomaly:
            _insert(conn, "pending_submissions", {**row, "anomaly_reason": reason, "status": "pending"})
            _log(conn, username, "SUBMITTED_PENDING",
                 f"Source={source}, qty={qty}, co2e={co2e} — flagged as anomaly")
        else:
            _insert(conn, "emissions", {**row, "status": "approved", "is_anomaly": 0})
            _log(conn, username, "SUBMITTED_APPROVED", f"Source={source}, qty={qty}, co2e={co2e}")
    return {"inserted": True, "anomaly": anomaly, "reason": reason, "co2e_kg": co2e}


def _validate_submission(data: dict[str, Any], username: str) -> None:
    required = {"date", "facility", "scope", "source", "quantity"}
    missing = required.difference(data)
    if missing:
        raise ValueError(f"Missing emission fields: {', '.join(sorted(missing))}")
    if not username or not username.strip():
        raise ValueError("A submitting username is required")
    try:
        datetime.strptime(str(data["date"]), DATE_FORMAT)
    except ValueError:
        raise ValueError("Emission date must use the YYYY-MM-DD format") from None
    if data["facility"] not in COMPANIES:
        raise ValueError("Unknown company")
    if data["scope"] not in (1, 2):
        raise ValueError("Scope must be 1 or 2")
    source_scope = SCOPE1_SOURCES if data["scope"] == 1 else SCOPE2_SOURCES
    if data["source"] not in source_scope:
        raise ValueError("Emission source does not match the selected scope")
    try:
        quantity = float(data["quantity"])
    except (TypeError, ValueError):
        raise ValueError("Emission quantity must be a number") from None
    calculate_emission(data["source"], quantity)


def _approved_history(source: str) -> list[float]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT co2e_kg FROM emissions WHERE source=? AND status='approved'", (source,)
        ).fetchall()
    return [row[0] for row in rows]


def _fetch_pending(conn: sqlite3.Connection, record_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM pending_submissions WHERE id=? AND status='pending'", (record_id,)
    ).fetchone()


def approve_submission(record_id: int, approver: str) -> bool:
    """Move a pending submission into the ledger. Returns False if it was not pending."""
    with _connect() as conn:
        row = _fetch_pending(conn, record_id)
        if row is None:
            return False
        _insert(conn, "emissions", {
            **{field: row[field] for field in _SUBMISSION_FIELDS},
            "status": "approved", "approved_by": approver, "approved_at": _now(), "is_anomaly": 1,
        })
        conn.execute("UPDATE pending_submissions SET status='approved' WHERE id=?", (record_id,))
        _log(conn, approver, "APPROVED", f"Pending ID={record_id}, source={row['source']}")
    return True


def reject_submission(record_id: int, approver: str) -> bool:
    """Mark a pending submission as rejected. Returns False if it was not pending."""
    with _connect() as conn:
        row = _fetch_pending(conn, record_id)
        if row is None:
            return False
        conn.execute("UPDATE pending_submissions SET status='rejected' WHERE id=?", (record_id,))
        _log(conn, approver, "REJECTED", f"Pending ID={record_id}, source={row['source']}")
    return True


# ── Activity log ───────────────────────────────────────────────────────────────
def _log(conn: sqlite3.Connection, username: str, action: str, details: str = "") -> None:
    conn.execute(
        "INSERT INTO activity_log (timestamp, username, action, details) VALUES (?,?,?,?)",
        (_now(), username, action, details),
    )


def log_action(username: str, action: str, details: str = "") -> None:
    with _connect() as conn:
        _log(conn, username, action, details)

"""
data_manager.py – SQLite data layer: seeding, CRUD, queries.
"""
import sqlite3, os, json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.emission_factors import (
    SCOPE1_SOURCES, SCOPE2_SOURCES, ALL_FACTORS, FACILITIES,
    CARBON_TAX_RATE_MYR,
)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "emissions.db")


# ── Connection helper ──────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ── Schema initialisation ──────────────────────────────────────────────────────
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    c = conn.cursor()

    # Emissions records
    c.execute("""
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
    """)

    # Approval queue (pending submissions)
    c.execute("""
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
    """)

    # Activity log
    c.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            username    TEXT NOT NULL,
            action      TEXT NOT NULL,
            details     TEXT
        )
    """)

    conn.commit()
    conn.close()

    # Seed only if empty
    if _is_empty():
        _seed_data()


def _is_empty() -> bool:
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM emissions").fetchone()[0]
    conn.close()
    return count == 0


# ── Synthetic data seeder ──────────────────────────────────────────────────────
def _seed_data():
    np.random.seed(42)
    rng = np.random.default_rng(42)

    records = []
    users = ["admin", "user", "manager"]

    # 18 months of data, multiple facilities, multiple sources
    start = datetime(2025, 1, 1)
    for month_offset in range(18):
        month_date = start + timedelta(days=30 * month_offset)

        for facility in FACILITIES:
            # ---- Scope 1 ----
            for source in ["Natural Gas", "Diesel", "Petrol", "LPG"]:
                base_qty = {
                    "Natural Gas": 2800, "Diesel": 1500,
                    "Petrol": 600,  "LPG": 400,
                }.get(source, 500)
                # seasonal variation + trend
                seasonal = 1 + 0.15 * np.sin(2 * np.pi * month_offset / 12)
                trend    = 1 - 0.004 * month_offset  # slight downward trend
                noise    = rng.normal(1, 0.07)
                qty      = round(max(0, base_qty * seasonal * trend * noise), 2)
                co2e     = round(qty * ALL_FACTORS[source]["factor"], 2)
                date_str = (month_date + timedelta(days=int(rng.integers(0, 5)))).strftime("%Y-%m-%d")
                sub_at   = (month_date + timedelta(days=int(rng.integers(5, 10)))).strftime("%Y-%m-%d %H:%M:%S")
                records.append((
                    date_str, facility, 1, source,
                    ALL_FACTORS[source]["unit"], qty, co2e,
                    rng.choice(users), sub_at, "approved",
                    "manager", sub_at, None, 0,
                ))

            # ---- Scope 2 ----
            for source in ["Electricity (Peninsular Malaysia)", "Steam / Heat"]:
                base_qty = {"Electricity (Peninsular Malaysia)": 42000, "Steam / Heat": 8000}.get(source, 1000)
                seasonal = 1 + 0.20 * np.sin(2 * np.pi * (month_offset + 3) / 12)
                trend    = 1 - 0.003 * month_offset
                noise    = rng.normal(1, 0.06)
                qty      = round(max(0, base_qty * seasonal * trend * noise), 2)
                co2e     = round(qty * ALL_FACTORS[source]["factor"], 2)
                date_str = (month_date + timedelta(days=int(rng.integers(0, 5)))).strftime("%Y-%m-%d")
                sub_at   = (month_date + timedelta(days=int(rng.integers(5, 10)))).strftime("%Y-%m-%d %H:%M:%S")
                records.append((
                    date_str, facility, 2, source,
                    ALL_FACTORS[source]["unit"], qty, co2e,
                    rng.choice(users), sub_at, "approved",
                    "manager", sub_at, None, 0,
                ))

    conn = get_conn()
    conn.executemany("""
        INSERT INTO emissions
          (date, facility, scope, source, unit, quantity, co2e_kg,
           submitted_by, submitted_at, status, approved_by, approved_at, notes, is_anomaly)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, records)
    conn.commit()
    conn.close()


# ── Read helpers ───────────────────────────────────────────────────────────────
def load_emissions(status: str = "approved") -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql(
        "SELECT * FROM emissions WHERE status=? ORDER BY date DESC",
        conn, params=(status,)
    )
    conn.close()
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["submitted_at"] = pd.to_datetime(df["submitted_at"])
        df["month"] = df["date"].dt.to_period("M").astype(str)
        df["carbon_tax_myr"] = (df["co2e_kg"] / 1000) * CARBON_TAX_RATE_MYR
    return df


def load_pending() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql(
        "SELECT * FROM pending_submissions WHERE status='pending' ORDER BY submitted_at DESC",
        conn
    )
    conn.close()
    if not df.empty:
        df["submitted_at"] = pd.to_datetime(df["submitted_at"])
    return df


def load_all_pending() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql(
        "SELECT * FROM pending_submissions ORDER BY submitted_at DESC",
        conn
    )
    conn.close()
    if not df.empty:
        df["submitted_at"] = pd.to_datetime(df["submitted_at"])
    return df


def load_activity_log() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 200", conn)
    conn.close()
    return df


# ── Write helpers ──────────────────────────────────────────────────────────────
def submit_emission(data: dict, username: str) -> dict:
    """
    Submit a new emission record.
    Returns {'inserted': True/False, 'anomaly': True/False, 'reason': str}.
    """
    source  = data["source"]
    qty     = data["quantity"]
    co2e    = round(qty * ALL_FACTORS[source]["factor"], 4)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Anomaly detection: compare to historical mean ± 2σ for same source
    anomaly, reason = _detect_anomaly(source, co2e)

    conn = get_conn()
    if anomaly:
        conn.execute("""
            INSERT INTO pending_submissions
              (date, facility, scope, source, unit, quantity, co2e_kg,
               submitted_by, submitted_at, notes, anomaly_reason, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,'pending')
        """, (
            data["date"], data["facility"], data["scope"], source,
            ALL_FACTORS[source]["unit"], qty, co2e,
            username, now_str, data.get("notes", ""), reason,
        ))
        _log(conn, username, "SUBMITTED_PENDING",
             f"Source={source}, qty={qty}, co2e={co2e} — flagged as anomaly")
    else:
        conn.execute("""
            INSERT INTO emissions
              (date, facility, scope, source, unit, quantity, co2e_kg,
               submitted_by, submitted_at, status, notes, is_anomaly)
            VALUES (?,?,?,?,?,?,?,?,?,'approved',?,0)
        """, (
            data["date"], data["facility"], data["scope"], source,
            ALL_FACTORS[source]["unit"], qty, co2e,
            username, now_str, data.get("notes", ""),
        ))
        _log(conn, username, "SUBMITTED_APPROVED",
             f"Source={source}, qty={qty}, co2e={co2e}")
    conn.commit()
    conn.close()
    return {"inserted": True, "anomaly": anomaly, "reason": reason, "co2e_kg": co2e}


def approve_submission(record_id: int, approver: str):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM pending_submissions WHERE id=?", (record_id,)
    ).fetchone()
    if row:
        conn.execute("""
            INSERT INTO emissions
              (date, facility, scope, source, unit, quantity, co2e_kg,
               submitted_by, submitted_at, status, approved_by, approved_at, notes, is_anomaly)
            VALUES (?,?,?,?,?,?,?,?,?,'approved',?,?,?,1)
        """, (
            row["date"], row["facility"], row["scope"], row["source"],
            row["unit"], row["quantity"], row["co2e_kg"],
            row["submitted_by"], row["submitted_at"],
            approver, now_str, row["notes"],
        ))
        conn.execute(
            "UPDATE pending_submissions SET status='approved' WHERE id=?", (record_id,)
        )
        _log(conn, approver, "APPROVED", f"Pending ID={record_id}, source={row['source']}")
    conn.commit()
    conn.close()


def reject_submission(record_id: int, approver: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM pending_submissions WHERE id=?", (record_id,)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE pending_submissions SET status='rejected' WHERE id=?", (record_id,)
        )
        _log(conn, approver, "REJECTED", f"Pending ID={record_id}, source={row['source']}")
    conn.commit()
    conn.close()


# ── Anomaly detection ──────────────────────────────────────────────────────────
def _detect_anomaly(source: str, co2e: float):
    conn = get_conn()
    rows = conn.execute(
        "SELECT co2e_kg FROM emissions WHERE source=? AND status='approved'", (source,)
    ).fetchall()
    conn.close()
    values = [r[0] for r in rows]
    if len(values) < 5:
        return False, ""
    mean = np.mean(values)
    std  = np.std(values)
    if std == 0:
        return False, ""
    z = abs(co2e - mean) / std
    if z > 2.5:
        direction = "high" if co2e > mean else "low"
        reason = (
            f"Value {co2e:.1f} kg CO₂e is {z:.1f}σ {direction} of historical mean "
            f"({mean:.1f} ± {std:.1f} kg CO₂e) for '{source}'. Requires manager approval."
        )
        return True, reason
    return False, ""


# ── Activity log ───────────────────────────────────────────────────────────────
def _log(conn, username: str, action: str, details: str = ""):
    conn.execute(
        "INSERT INTO activity_log (timestamp, username, action, details) VALUES (?,?,?,?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username, action, details),
    )


def log_action(username: str, action: str, details: str = ""):
    conn = get_conn()
    _log(conn, username, action, details)
    conn.commit()
    conn.close()


# ── Aggregation helpers ────────────────────────────────────────────────────────
def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return monthly totals by scope."""
    if df.empty:
        return pd.DataFrame()
    grp = (
        df.groupby(["month", "scope"])["co2e_kg"]
        .sum()
        .reset_index()
    )
    grp["co2e_tonnes"] = grp["co2e_kg"] / 1000
    return grp


def source_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return total CO₂e by source."""
    if df.empty:
        return pd.DataFrame()
    grp = (
        df.groupby(["source", "scope"])["co2e_kg"]
        .sum()
        .reset_index()
    )
    grp["co2e_tonnes"] = grp["co2e_kg"] / 1000
    return grp.sort_values("co2e_kg", ascending=False)


def facility_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    grp = (
        df.groupby(["facility", "month"])["co2e_kg"]
        .sum()
        .reset_index()
    )
    grp["co2e_tonnes"] = grp["co2e_kg"] / 1000
    return grp

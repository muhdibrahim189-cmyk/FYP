import tempfile
import unittest
from pathlib import Path
from unittest import mock

from utils import data_manager
from utils.seed_data import SEED_MONTHS, generate_seed_records
from data.emission_factors import COMPANIES, ENERGY_SCOPE, ENERGY_SOURCES
from utils.analytics import monthly_ledger_summary, scope_totals

# March 2024 is before the seeded months, so a submission for it is not a duplicate.
VALID = {"date": "2024-03-01", "facility": COMPANIES[0], "scope": 1, "source": "Mobile – Diesel", "quantity": 10}


class DataManagerTests(unittest.TestCase):
    """Runs against a throwaway SQLite file so the real ledger is untouched."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        db_path = str(Path(self._tmp.name) / "nested" / "test.db")
        patcher = mock.patch.object(data_manager, "DB_PATH", db_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)
        data_manager.init_db()

    def test_init_seeds_once(self):
        expected = SEED_MONTHS * len(COMPANIES) * 6
        self.assertEqual(len(data_manager.load_database_emissions()), expected)
        data_manager.init_db()
        self.assertEqual(len(data_manager.load_database_emissions()), expected)

    def test_seed_has_one_entry_per_source_per_company_month(self):
        ledger = data_manager.load_database_emissions()
        self.assertFalse(ledger.duplicated(["facility", "source", "month"]).any())

    def test_second_entry_for_same_source_and_month_is_flagged_then_replaces(self):
        first = data_manager.submit_emission({**VALID, "quantity": 1500}, "user")
        self.assertFalse(first["anomaly"])
        second = data_manager.submit_emission({**VALID, "date": "2024-03-20", "quantity": 1600}, "user")
        self.assertTrue(second["anomaly"])
        self.assertIn("Duplicate entry", second["reason"])
        # Another source, or the same source in another month, is not a duplicate.
        self.assertFalse(data_manager.submit_emission({**VALID, "source": "Mobile – Petrol", "quantity": 600}, "user")["anomaly"])
        self.assertFalse(data_manager.submit_emission({**VALID, "date": "2024-04-01", "quantity": 1500}, "user")["anomaly"])

        data_manager.approve_submission(int(data_manager.load_pending().iloc[0]["id"]), "manager")
        march = data_manager.load_database_emissions().query("month == '2024-03' and source == 'Mobile – Diesel'")
        self.assertEqual(march["quantity"].tolist(), [1600])  # the approved entry replaced the first one
        self.assertEqual(data_manager.load_database_emissions("replaced")["quantity"].tolist(), [1500])

    def test_power_consumption_is_recorded_without_emissions(self):
        before = scope_totals(data_manager.load_database_emissions())
        energy = {**VALID, "scope": ENERGY_SCOPE, "source": ENERGY_SOURCES[0], "quantity": 250_000}
        result = data_manager.submit_emission(energy, "user")
        self.assertEqual(result["co2e_kg"], 0)
        ledger = data_manager.load_database_emissions()
        self.assertEqual(scope_totals(ledger), before)
        row = monthly_ledger_summary(ledger).query("Month == '2024-03' and Company == @COMPANIES[0]")
        self.assertEqual(row["Power Consumption (MWh)"].tolist(), [250.0])
        self.assertTrue(data_manager.submit_emission(energy, "user")["anomaly"])  # one per month too

    def test_seed_generation_is_deterministic(self):
        self.assertEqual(generate_seed_records()[:5], generate_seed_records()[:5])

    def test_normal_submission_goes_to_ledger_and_log(self):
        before = len(data_manager.load_database_emissions())
        result = data_manager.submit_emission({**VALID, "quantity": 1500}, "user")
        self.assertFalse(result["anomaly"])
        self.assertEqual(len(data_manager.load_database_emissions()), before + 1)
        self.assertEqual(data_manager.load_activity_log()["action"].tolist(), ["SUBMITTED_APPROVED"])

    def test_anomalous_submission_is_queued_then_approved(self):
        result = data_manager.submit_emission({**VALID, "quantity": 1_000_000}, "user")
        self.assertTrue(result["anomaly"])
        pending = data_manager.load_pending()
        self.assertEqual(len(pending), 1)

        record_id = int(pending.iloc[0]["id"])
        self.assertTrue(data_manager.approve_submission(record_id, "manager"))
        self.assertTrue(data_manager.load_pending().empty)
        self.assertFalse(data_manager.approve_submission(record_id, "manager"))  # already processed
        ledger = data_manager.load_database_emissions()
        self.assertEqual(int(ledger["is_anomaly"].sum()), 1)

    def test_reject_leaves_ledger_unchanged(self):
        data_manager.submit_emission({**VALID, "quantity": 1_000_000}, "user")
        before = len(data_manager.load_database_emissions())
        record_id = int(data_manager.load_pending().iloc[0]["id"])
        self.assertTrue(data_manager.reject_submission(record_id, "manager"))
        self.assertEqual(len(data_manager.load_database_emissions()), before)
        self.assertEqual(data_manager.load_all_pending()["status"].tolist(), ["rejected"])

    def test_invalid_submissions_are_rejected(self):
        cases = {
            "missing field": ({k: v for k, v in VALID.items() if k != "source"}, "user"),
            "scope mismatch": ({**VALID, "source": "Electricity – Sabah (SESB)"}, "user"),
            "energy as scope 1": ({**VALID, "source": ENERGY_SOURCES[0]}, "user"),
            "bad scope": ({**VALID, "scope": 3}, "user"),
            "unknown company": ({**VALID, "facility": "<script>"}, "user"),
            "bad date": ({**VALID, "date": "01/03/2025"}, "user"),
            "negative quantity": ({**VALID, "quantity": -1}, "user"),
            "non-numeric quantity": ({**VALID, "quantity": "ten"}, "user"),
            "blank user": (VALID, "  "),
        }
        for name, (data, user) in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                data_manager.submit_emission(data, user)

    def test_failed_write_is_rolled_back(self):
        before = len(data_manager.load_database_emissions())
        with mock.patch.object(data_manager, "_log", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                data_manager.submit_emission({**VALID, "quantity": 1500}, "user")
        # The emission INSERT ran before the failing log write and must be undone.
        self.assertEqual(len(data_manager.load_database_emissions()), before)


class WorkbookTests(unittest.TestCase):
    def test_workbook_rows_become_two_scopes_per_company_month(self):
        if not data_manager.CARBON_EMISSION_DATA_PATH.exists():
            self.skipTest("workbook not present")
        df = data_manager.load_emissions()
        self.assertEqual(set(df["scope"]), {1, 2})
        self.assertTrue(df.attrs["data_quality_issues"])

    def test_stirpat_panel_has_one_row_per_company_month(self):
        if not data_manager.CARBON_EMISSION_DATA_PATH.exists():
            self.skipTest("workbook not present")
        panel = data_manager.load_stirpat_panel()
        self.assertEqual(len(panel), len(data_manager.load_emissions()) // 2)
        self.assertFalse(panel[["I", "S1", "S2", "P", "A", "T"]].le(0).any().any())  # logs need positive values

    def test_workbook_emissions_are_million_tonnes(self):
        if not data_manager.CARBON_EMISSION_DATA_PATH.exists():
            self.skipTest("workbook not present")
        panel = data_manager.load_stirpat_panel()
        total_kg = data_manager.load_emissions()["co2e_kg"].sum()
        self.assertAlmostEqual(total_kg / 1e9, panel["I"].sum(), places=6)  # 1 Mt = 10⁹ kg

    def test_companies_match_workbook(self):
        if not data_manager.CARBON_EMISSION_DATA_PATH.exists():
            self.skipTest("workbook not present")
        self.assertEqual(sorted(data_manager.load_emissions()["facility"].unique()), sorted(COMPANIES))

    def test_cached_workbook_is_not_shared_between_callers(self):
        if not data_manager.CARBON_EMISSION_DATA_PATH.exists():
            self.skipTest("workbook not present")
        first = data_manager.load_emissions()
        first["co2e_kg"] = 0
        self.assertGreater(data_manager.load_emissions()["co2e_kg"].sum(), 0)


if __name__ == "__main__":
    unittest.main()

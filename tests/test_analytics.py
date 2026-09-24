import unittest
from datetime import date

import pandas as pd

from utils.analytics import (
    detect_anomaly, filter_emissions, forecast_monthly_totals, monthly_summary,
    period_over_period_change, scope_totals, search_rows, source_summary, to_safe_csv,
)


def make_records() -> pd.DataFrame:
    df = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-05", "2024-02-05", "2024-03-05", "2025-01-05"]),
        "facility": ["HQ", "HQ", "Plant", "Plant"],
        "scope": [1, 2, 1, 2],
        "source": ["Diesel", "Electricity", "Diesel", "Electricity"],
        "submitted_by": ["admin", "user", "user", "admin"],
        "co2e_kg": [1000.0, 2000.0, 3000.0, 4000.0],
    })
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


class ScopeTotalsTests(unittest.TestCase):
    def test_splits_by_scope(self):
        totals = scope_totals(make_records())
        self.assertEqual((totals.total_kg, totals.scope1_kg, totals.scope2_kg), (10000, 4000, 6000))

    def test_summaries_convert_to_tonnes(self):
        by_source = source_summary(make_records())
        self.assertEqual(by_source.iloc[0]["source"], "Electricity")
        self.assertEqual(by_source.iloc[0]["co2e_tonnes"], 6.0)
        self.assertEqual(monthly_summary(make_records())["co2e_tonnes"].sum(), 10.0)

    def test_summaries_of_empty_frame_are_empty(self):
        self.assertTrue(monthly_summary(pd.DataFrame()).empty)


class FilterTests(unittest.TestCase):
    def test_empty_selection_means_no_filter(self):
        self.assertEqual(len(filter_emissions(make_records(), scopes=[], facilities=[])), 4)

    def test_combines_filters(self):
        result = filter_emissions(make_records(), years=[2024], scopes=[1], facilities=["Plant"])
        self.assertEqual(result["co2e_kg"].tolist(), [3000.0])

    def test_date_range_is_inclusive(self):
        result = filter_emissions(make_records(), date_range=(date(2024, 2, 5), date(2024, 3, 5)))
        self.assertEqual(len(result), 2)

    def test_several_years(self):
        self.assertEqual(len(filter_emissions(make_records(), years=[2024, 2025])), 4)
        self.assertEqual(len(filter_emissions(make_records(), years=[2025])), 1)

    def test_submitted_by(self):
        self.assertEqual(len(filter_emissions(make_records(), submitted_by="admin")), 2)


class SearchTests(unittest.TestCase):
    def test_is_case_insensitive_across_columns(self):
        self.assertEqual(len(search_rows(make_records(), "PLANT")), 2)
        self.assertEqual(len(search_rows(make_records(), "user")), 2)

    def test_treats_term_literally(self):
        self.assertTrue(search_rows(make_records(), ".*").empty)

    def test_blank_term_returns_everything(self):
        self.assertEqual(len(search_rows(make_records(), "  ")), 4)


class TrendTests(unittest.TestCase):
    def test_period_change_compares_halves(self):
        # months: 2024-01, 2024-02 | 2024-03, 2025-01 -> 3000 vs 7000
        self.assertAlmostEqual(period_over_period_change(make_records()), 133.33)

    def test_forecast_extends_linear_trend(self):
        months = pd.period_range("2024-01", periods=6, freq="M")
        df = pd.DataFrame({
            "month": months.astype(str), "scope": 1,
            "co2e_kg": [1000.0 * (i + 1) for i in range(6)],
        })
        forecast = forecast_monthly_totals(df, periods=2)
        self.assertEqual(forecast["Month"].tolist(), ["2024-07", "2024-08"])
        self.assertAlmostEqual(forecast["Predicted"].iloc[0], 7.0)
        self.assertAlmostEqual(forecast["Predicted"].iloc[1], 8.0)

    def test_forecast_needs_enough_history(self):
        self.assertTrue(forecast_monthly_totals(make_records().head(2)).empty)


class AnomalyTests(unittest.TestCase):
    HISTORY = [100, 102, 98, 101, 99, 100]

    def test_needs_minimum_history(self):
        self.assertEqual(detect_anomaly([100, 200], 10_000, "Diesel"), (False, ""))

    def test_constant_history_never_flags(self):
        self.assertEqual(detect_anomaly([5] * 10, 500, "Diesel"), (False, ""))

    def test_flags_outlier_with_direction(self):
        flagged, reason = detect_anomaly(self.HISTORY, 500, "Diesel")
        self.assertTrue(flagged)
        self.assertIn("high", reason)
        self.assertIn("'Diesel'", reason)

    def test_accepts_normal_value(self):
        self.assertFalse(detect_anomaly(self.HISTORY, 101, "Diesel")[0])


class CsvExportTests(unittest.TestCase):
    def test_neutralises_formula_cells_only(self):
        df = pd.DataFrame({"notes": ["=HYPERLINK(\"x\")", "normal", "@SUM(A1)"], "value": [-1.5, 2.0, 3.0]})
        lines = to_safe_csv(df).splitlines()
        self.assertTrue(lines[1].startswith("\"'=HYPERLINK"))
        self.assertEqual(lines[2], "normal,2.0")
        self.assertTrue(lines[3].startswith("'@SUM"))
        self.assertTrue(lines[1].endswith(",-1.5"))


if __name__ == "__main__":
    unittest.main()

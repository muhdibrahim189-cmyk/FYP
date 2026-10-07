import unittest
from datetime import date

import numpy as np
import pandas as pd

from utils.analytics import (
    detect_anomaly, filter_emissions, monthly_summary, period_over_period_change, scope_totals,
    search_rows, stirpat_forecast, to_safe_csv,
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
        self.assertAlmostEqual(monthly_summary(make_records())["co2e_mt"].sum(), 1e-5)

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



def make_stirpat_panel(months: int = 36) -> pd.DataFrame:
    """Two companies whose emissions follow I = α·P^0.8·A^0.1·T^0.9 exactly."""
    dates = pd.date_range("2021-01-01", periods=months, freq="MS")
    t = np.arange(months)
    rows = []
    for company, alpha, scale in (("A Co", 0.02, 1.0), ("B Co", 0.05, 3.0)):
        P = scale * 1000 * (1.01 ** t) * (1 + 0.05 * np.sin(t))
        A = scale * 500 * (1.02 ** t) * (1 + 0.03 * np.cos(t))
        T = 100 * (0.995 ** t) * (1 + 0.04 * np.sin(2 * t))
        rows.append(pd.DataFrame({"company": company, "date": dates, "P": P, "A": A, "T": T,
                                  "I": alpha * P ** 0.8 * A ** 0.1 * T ** 0.9}))
    return pd.concat(rows, ignore_index=True)


class StirpatTests(unittest.TestCase):
    def test_recovers_elasticities_and_predicts_unseen_months(self):
        result = stirpat_forecast(make_stirpat_panel(), ["A Co", "B Co"], periods=6)
        for driver, expected in {"P": 0.8, "A": 0.1, "T": 0.9}.items():
            self.assertAlmostEqual(result.coefficients[driver], expected, delta=0.1)  # ridge shrinks them a little
        self.assertGreater(result.test_r2, 0.99)
        self.assertLess(result.test_mape_pct, 1.0)
        # 36 months, 80/20 split: train Jan 2021 – Apr 2023, test May 2023 – Dec 2023.
        self.assertEqual(result.train_end, "2023-04")
        self.assertEqual(result.test["Month"].tolist()[0], "2023-05")
        self.assertEqual(result.forecast["Month"].tolist(),
                         ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"])

    def test_totals_follow_selected_companies(self):
        panel = make_stirpat_panel()
        both = stirpat_forecast(panel, ["A Co", "B Co"])
        only_a = stirpat_forecast(panel, ["A Co"])
        self.assertLess(only_a.forecast["Predicted"].sum(), both.forecast["Predicted"].sum())

    def test_models_the_chosen_target_column(self):
        panel = make_stirpat_panel().assign(S1=lambda f: f["I"] * 0.9)
        total = stirpat_forecast(panel, ["A Co", "B Co"], target="I")
        scope1 = stirpat_forecast(panel, ["A Co", "B Co"], target="S1")
        self.assertAlmostEqual(scope1.forecast["Predicted"].sum() / total.forecast["Predicted"].sum(), 0.9, places=3)
        self.assertAlmostEqual(scope1.test["Actual"].sum() / total.test["Actual"].sum(), 0.9)

    def test_needs_two_years_of_history(self):
        self.assertIsNone(stirpat_forecast(make_stirpat_panel(months=20), ["A Co"]))


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

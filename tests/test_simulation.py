import unittest

import pandas as pd

from utils.simulation import ALL_LEVERS, describe_changes, reduction_fractions, simulate_emissions


class SimulationTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            "source": ["Natural Gas", "Petrol", "Electricity (Sabah)", "Scope 1"],
            "co2e_kg": [100.0, 100.0, 300.0, 50.0],
        })

    def test_no_levers_means_no_change(self):
        pd.testing.assert_series_equal(simulate_emissions(self.df, {}), self.df["co2e_kg"], check_names=False)

    def test_petrol_averages_reduction_and_ev_adoption(self):
        self.assertEqual(reduction_fractions({"p_red": 40, "ev_pct": 20})["Petrol"], 0.3)

    def test_electricity_averages_three_levers(self):
        self.assertEqual(reduction_fractions({"e_red": 30, "re_pct": 30, "eff": 30})["Electricity (Sabah)"], 0.3)

    def test_applies_fractions_and_ignores_unknown_sources(self):
        result = simulate_emissions(self.df, {"ng_red": 50, "e_red": 90, "re_pct": 90, "eff": 0})
        self.assertEqual(result.tolist(), [50.0, 100.0, 120.0, 50.0])

    def test_full_reduction_reaches_zero(self):
        self.assertEqual(simulate_emissions(self.df, {"ng_red": 100}).iloc[0], 0.0)

    def test_lever_keys_are_unique(self):
        keys = [lever.key for lever in ALL_LEVERS]
        self.assertEqual(len(keys), len(set(keys)))

    def test_describe_changes_lists_only_active_levers(self):
        self.assertEqual(describe_changes({"ng_red": 10, "d_red": 0, "eff": 5}),
                         ["Natural Gas -10%", "Energy Efficiency +5%"])


if __name__ == "__main__":
    unittest.main()

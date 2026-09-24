import unittest

from utils.carbon_calculator import carbon_tax, calculate_emission, share_pct, yoy_change


class CarbonCalculatorTests(unittest.TestCase):
    def test_calculates_known_factor(self):
        self.assertEqual(calculate_emission("Diesel", 10), 26.88)

    def test_unknown_source_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_emission("Unknown source", 10)

    def test_negative_or_non_finite_quantity_is_rejected(self):
        for quantity in (-1, float("nan"), float("inf")):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                calculate_emission("Diesel", quantity)

    def test_carbon_tax_uses_tonnes(self):
        self.assertEqual(carbon_tax(1000), 35.0)

    def test_carbon_tax_accepts_custom_rate(self):
        self.assertEqual(carbon_tax(2000, rate_myr=10), 20.0)

    def test_yoy_change_handles_zero_previous_period(self):
        self.assertEqual(yoy_change(100, 0), 0.0)

    def test_share_pct_handles_zero_total(self):
        self.assertEqual(share_pct(5, 0), 0.0)
        self.assertEqual(share_pct(1, 4), 25.0)


if __name__ == "__main__":
    unittest.main()

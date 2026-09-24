import tempfile
import unittest
from pathlib import Path

from utils.carbon_calculator import carbon_tax, calculate_emission, yoy_change


class CarbonCalculatorTests(unittest.TestCase):
    def test_calculates_known_factor(self):
        self.assertEqual(calculate_emission("Diesel", 10), 26.88)

    def test_unknown_source_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_emission("Unknown source", 10)

    def test_carbon_tax_uses_tonnes(self):
        self.assertEqual(carbon_tax(1000), 35.0)

    def test_yoy_change_handles_zero_previous_period(self):
        self.assertEqual(yoy_change(100, 0), 0.0)


if __name__ == "__main__":
    unittest.main()

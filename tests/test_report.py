import unittest
from datetime import datetime
from unittest import mock

import pandas as pd
from reportlab import rl_config

from data.emission_factors import company_display_name
from utils.report import amount_in_words, build_statement, statement_months


def make_ledger() -> pd.DataFrame:
    """BP 2025: 1,000 t Scope 1 and 100 t Scope 2 every month, plus one Chevron month."""
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    rows = [{"facility": "BP", "month": m, "scope": scope, "quantity": 0.0, "co2e_kg": kg,
             "submitted_by": "Carbon_Emission_Data", "notes": "Disaggregated (from annual)"}
            for m in months for scope, kg in ((1, 1_000_000.0), (2, 100_000.0))]
    rows.append({"facility": "Chevron", "month": "2025-01", "scope": 1, "quantity": 0.0, "co2e_kg": 5e6,
                 "submitted_by": "user", "notes": ""})
    return pd.DataFrame(rows)


def pdf_text(data: bytes) -> str:
    """The PDF's raw drawing commands; text appears as literal strings when compression is off."""
    return data.decode("latin-1")


def build(*args, **kwargs) -> str:
    with mock.patch.object(rl_config, "pageCompression", 0):
        data = build_statement(*args, **kwargs)
    assert data.startswith(b"%PDF"), "not a PDF"
    return pdf_text(data)


class AmountInWordsTests(unittest.TestCase):
    def test_matches_the_template_wording(self):
        self.assertEqual(amount_in_words(550_400_000),
                         "Ringgit Malaysia Five Hundred Fifty Million Four Hundred Thousand Only")

    def test_sen_and_small_numbers(self):
        self.assertEqual(amount_in_words(1_015.05), "Ringgit Malaysia One Thousand Fifteen and Sen Five Only")
        self.assertEqual(amount_in_words(0.99), "Ringgit Malaysia Zero and Sen Ninety Nine Only")


class StatementTests(unittest.TestCase):
    def test_annual_statement_totals_and_company_name(self):
        text = build(make_ledger(), "BP", 2025, "Annual", 16.0, issued=datetime(2026, 10, 23, 6, 53))
        self.assertIn(r"British Petroleum \(BP\)", text)   # PDF strings escape parentheses
        self.assertIn(r"Jan 2025 to Dec 2025 \(12 months\)", text)
        self.assertIn("SPK/CT/BP/202501-202512", text)
        self.assertIn("13,200.00", text)                     # (1,000 + 100) t × 12 months
        self.assertIn("RM 211,200.00", text)                 # 13,200 t × RM 16
        self.assertIn("22/11/2026", text)                    # due date = issue date + 30 days
        self.assertIn("Page 3 of 3", text)                   # one part per page
        self.assertIn("Two Hundred Eleven Thousand Two Hundred Only", text)

    def test_quarter_covers_three_months(self):
        months = statement_months(make_ledger(), "BP", 2025, "Q3")
        self.assertEqual(months["Month"].tolist(), ["2025-07", "2025-08", "2025-09"])
        text = build(make_ledger(), "BP", 2025, "Q3", 16.0)
        self.assertIn(r"Jul 2025 to Sep 2025 \(3 months\)", text)
        self.assertIn("3,300.00", text)

    def test_period_without_data_is_refused(self):
        with self.assertRaises(ValueError):
            build_statement(make_ledger(), "BP", 2024, "Q1", 16.0)

    def test_data_entry_records_are_mentioned_in_the_data_basis(self):
        self.assertIn(r"plus 1 data-entry record\(s\)", build(make_ledger(), "Chevron", 2025, "Q1", 16.0))


class CompanyNameTests(unittest.TestCase):
    def test_abbreviation_is_expanded(self):
        self.assertEqual(company_display_name("BP"), "British Petroleum (BP)")
        self.assertEqual(company_display_name("Chevron"), "Chevron")


if __name__ == "__main__":
    unittest.main()

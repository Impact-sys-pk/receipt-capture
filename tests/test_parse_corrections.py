"""Design document tests 10 and 11: parse_corrections coercion rules.

parse_corrections is the single coercion point for operator input, shared by
the CLI, the console form and the resolution back-feed. It must decide by key
presence rather than truthiness, and must never raise: bad input comes back as
a field error keyed by field name.
"""

import unittest

from worker.resolution.service import CORRECTABLE_FIELDS, parse_corrections


class ParseCorrectionsTest(unittest.TestCase):
    def test_omitted_and_none_keys_are_absent_from_values(self):
        corrections, errors = parse_corrections({
            "supplier_name": "Apcoa Parking",
            "vat_amount": None,
        })
        self.assertEqual(errors, {})
        self.assertEqual(corrections.values, {"supplier_name": "Apcoa Parking"})
        self.assertNotIn("vat_amount", corrections.values)
        self.assertNotIn("gross_amount", corrections.values)

    def test_zero_as_string_is_a_real_correction(self):
        # Zero-rated and exempt supplies: correcting VAT to 0.00 is routine.
        corrections, errors = parse_corrections({"vat_amount": "0"})
        self.assertEqual(errors, {})
        self.assertIn("vat_amount", corrections.values)
        self.assertEqual(corrections.values["vat_amount"], 0.0)
        self.assertIsInstance(corrections.values["vat_amount"], float)

        corrections, errors = parse_corrections({"vat_amount": "0.00"})
        self.assertEqual(errors, {})
        self.assertEqual(corrections.values["vat_amount"], 0.0)

    def test_zero_as_float_is_preserved(self):
        # The flags path already coerces with type=float, so 0.0 arrives typed.
        corrections, errors = parse_corrections({"vat_amount": 0.0})
        self.assertEqual(errors, {})
        self.assertIn("vat_amount", corrections.values)
        self.assertEqual(corrections.values["vat_amount"], 0.0)

    def test_empty_string_records_an_explicit_clear(self):
        # Distinct from omission: an operator must be able to remove a wrongly
        # extracted reference number.
        corrections, errors = parse_corrections({"receipt_ref_number": ""})
        self.assertEqual(errors, {})
        self.assertIn("receipt_ref_number", corrections.values)
        self.assertIsNone(corrections.values["receipt_ref_number"])

    def test_clear_is_available_for_amounts_and_dates_too(self):
        corrections, errors = parse_corrections({
            "vat_amount": "",
            "invoice_date": "",
        })
        self.assertEqual(errors, {})
        self.assertIsNone(corrections.values["vat_amount"])
        self.assertIsNone(corrections.values["invoice_date"])

    def test_rejects_thousands_separators_symbols_and_extra_decimals(self):
        for bad in ("1,234.56", "£10", "10.999", "12.5.1", "abc", "10 00"):
            with self.subTest(value=bad):
                corrections, errors = parse_corrections({"gross_amount": bad})
                self.assertIn("gross_amount", errors)
                self.assertNotIn("gross_amount", corrections.values)

    def test_rejects_non_iso_date_without_reparsing_it(self):
        # Guessing here would undo the day-first work in openai_vision.py.
        corrections, errors = parse_corrections({"invoice_date": "25/12/2026"})
        self.assertIn("invoice_date", errors)
        self.assertNotIn("invoice_date", corrections.values)

    def test_rejects_impossible_calendar_date(self):
        corrections, errors = parse_corrections({"invoice_date": "2026-02-30"})
        self.assertIn("invoice_date", errors)
        self.assertNotIn("invoice_date", corrections.values)

    def test_accepts_iso_date(self):
        corrections, errors = parse_corrections({"invoice_date": "2026-12-25"})
        self.assertEqual(errors, {})
        self.assertEqual(corrections.values["invoice_date"], "2026-12-25")

    def test_accepts_plain_and_negative_amounts(self):
        # Negatives are validate()'s business, not the parser's.
        corrections, errors = parse_corrections({
            "net_amount": "80",
            "vat_amount": "16.00",
            "gross_amount": "-96",
        })
        self.assertEqual(errors, {})
        self.assertEqual(corrections.values["net_amount"], 80.0)
        self.assertEqual(corrections.values["vat_amount"], 16.0)
        self.assertEqual(corrections.values["gross_amount"], -96.0)

    def test_text_fields_are_stripped(self):
        corrections, errors = parse_corrections({"supplier_name": "  Apcoa  "})
        self.assertEqual(errors, {})
        self.assertEqual(corrections.values["supplier_name"], "Apcoa")

    def test_unknown_keys_are_ignored(self):
        corrections, errors = parse_corrections({
            "csrf_token": "xyz",
            "supplier_name": "Apcoa",
        })
        self.assertEqual(errors, {})
        self.assertEqual(set(corrections.values), {"supplier_name"})

    def test_never_raises_on_hostile_input(self):
        corrections, errors = parse_corrections({
            "gross_amount": ["not", "a", "number"],
            "invoice_date": 20261225,
            "supplier_name": None,
        })
        self.assertIn("gross_amount", errors)
        self.assertIn("invoice_date", errors)
        self.assertEqual(corrections.values, {})

    def test_correctable_fields_matches_the_design_document(self):
        self.assertEqual(CORRECTABLE_FIELDS, (
            "supplier_name", "invoice_date", "net_amount",
            "vat_amount", "gross_amount", "receipt_ref_number", "receipt_time",
        ))


if __name__ == "__main__":
    unittest.main()

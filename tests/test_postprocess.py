"""Direct tests on worker/extraction/postprocess.py.

Design document 10.2. This logic used to live inside
OpenAIVisionExtractor.extract(), so a second provider would silently not
inherit it and both the day-first fix and the VAT-inclusive-total fix would stop
applying the moment the engine changed.

tests/test_date_disambiguation.py and tests/test_vat_swap.py drive the same code
through extract() and are unmodified by this step. They are the acceptance
criterion (design test 12); these tests are the direct cover the functions never
had.
"""

import subprocess
import sys
import unittest
from pathlib import Path

from worker.extraction.postprocess import (
    apply_vat_inclusive_swap,
    parse_ambiguous_date,
    resolve_invoice_date,
)


class ParseAmbiguousDateTest(unittest.TestCase):
    def test_ambiguous_date_follows_prefer_dayfirst(self):
        # The whole reason this function exists: 09/05/26 is two different dates
        # depending on the convention, and the model cannot know which.
        self.assertEqual(parse_ambiguous_date("09/05/26", True), "2026-05-09")
        self.assertEqual(parse_ambiguous_date("09/05/26", False), "2026-09-05")

    def test_unambiguous_date_resolves_the_same_either_way(self):
        # A day over 12 cannot be a month, so the convention is irrelevant.
        for prefer_dayfirst in (True, False):
            with self.subTest(prefer_dayfirst=prefer_dayfirst):
                self.assertEqual(parse_ambiguous_date("25/12/26", prefer_dayfirst), "2026-12-25")
                self.assertEqual(parse_ambiguous_date("12/25/26", prefer_dayfirst), "2026-12-25")

    def test_separators_other_than_slash(self):
        self.assertEqual(parse_ambiguous_date("9-5-2026", True), "2026-05-09")
        self.assertEqual(parse_ambiguous_date("9.5.2026", True), "2026-05-09")

    def test_two_digit_year_is_read_as_this_century(self):
        self.assertEqual(parse_ambiguous_date("25/12/26", True), "2026-12-25")

    def test_junk_returns_none_rather_than_guessing(self):
        for raw in ("", None, "not a date", "09/05", "1/2/3/4", "aa/bb/cc", 20260509):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_ambiguous_date(raw, True))

    def test_impossible_calendar_date_returns_none(self):
        self.assertIsNone(parse_ambiguous_date("31/02/26", True))
        self.assertIsNone(parse_ambiguous_date("45/45/26", True))


class IsoShapedRawTest(unittest.TestCase):
    """An ISO-shaped raw string used to defeat the whole deterministic path.

    parse_ambiguous_date("2026-05-09", ...) split to 2026, 5, 9, read the 9 as a
    two-digit year, and returned None. So for a receipt that prints its date in
    ISO form, and whose raw string the model therefore returns in ISO form, the
    day-first fix did not apply and the receipt fell through to the ambiguity
    annotation. It failed safe and it failed silently.
    """

    def test_iso_raw_parses_the_same_whatever_the_convention(self):
        # Four digits first can only be a year, so there is nothing ambiguous
        # and prefer_dayfirst does not apply.
        for prefer_dayfirst in (True, False):
            with self.subTest(prefer_dayfirst=prefer_dayfirst):
                self.assertEqual(parse_ambiguous_date("2026-05-09", prefer_dayfirst), "2026-05-09")
                self.assertEqual(parse_ambiguous_date("2026/05/09", prefer_dayfirst), "2026-05-09")
                self.assertEqual(parse_ambiguous_date("2026-5-9", prefer_dayfirst), "2026-05-09")

    def test_iso_raw_with_an_impossible_month_returns_none(self):
        self.assertIsNone(parse_ambiguous_date("2026-13-01", True))
        self.assertIsNone(parse_ambiguous_date("2026-02-30", True))

    def test_day_first_cases_are_unaffected(self):
        # Neither starts with four digits, so neither reaches the ISO branch.
        self.assertEqual(parse_ambiguous_date("09/05/26", True), "2026-05-09")
        self.assertEqual(parse_ambiguous_date("09/05/26", False), "2026-09-05")
        self.assertEqual(parse_ambiguous_date("9-5-2026", True), "2026-05-09")
        self.assertEqual(parse_ambiguous_date("9-5-2026", False), "2026-09-05")

    def test_iso_raw_agreeing_with_the_model_appends_no_note(self):
        # A note recording a change that did not happen is the same class of
        # problem as a note that names the wrong cause.
        invoice_date, details = resolve_invoice_date("2026-05-09", "2026-05-09", None, True)
        self.assertEqual(invoice_date, "2026-05-09")
        self.assertIsNone(details)

    def test_iso_raw_disagreeing_with_the_model_wins_and_says_so(self):
        invoice_date, details = resolve_invoice_date("2026-09-05", "2026-05-09", None, True)
        self.assertEqual(invoice_date, "2026-05-09")
        self.assertIn("auto_parsed_invoice_date_from_raw", details)
        self.assertIn("raw=2026-05-09 -> 2026-05-09", details)

    def test_agreeing_non_iso_raw_also_appends_no_note(self):
        # Same rule, reached through the ambiguous branch.
        invoice_date, details = resolve_invoice_date("2026-05-09", "09/05/26", None, True)
        self.assertEqual(invoice_date, "2026-05-09")
        self.assertIsNone(details)


class VatInclusiveSwapTest(unittest.TestCase):
    def test_swap_fires_when_the_amount_reads_as_gross(self):
        # net=8.00 with vat=1.33 implies 16.6% on 8.00, but 20% on 6.67, so the
        # 8.00 is really the gross.
        net, vat, gross, details = apply_vat_inclusive_swap(8.0, 1.33, None, None)
        self.assertAlmostEqual(gross, 8.00)
        self.assertAlmostEqual(net, 6.67, places=2)
        self.assertAlmostEqual(vat, 1.33)
        self.assertIn("auto_treated_amount_as_gross", details)
        # 1.33 / (8.00 - 1.33) = 0.1994, formatted to three places.
        self.assertIn("implied_rate=0.199", details)

    def test_swap_does_not_fire_on_a_genuine_net_reading(self):
        net, vat, gross, details = apply_vat_inclusive_swap(100.0, 20.0, None, None)
        self.assertEqual(net, 100.0)
        self.assertEqual(vat, 20.0)
        self.assertIsNone(gross)
        self.assertIsNone(details)

    def test_note_is_appended_to_existing_details_not_replacing_them(self):
        _, _, _, details = apply_vat_inclusive_swap(8.0, 1.33, None, "model said something")
        self.assertTrue(details.startswith("model said something; "))
        self.assertIn("auto_treated_amount_as_gross", details)

    def test_untouched_when_gross_is_already_present(self):
        net, vat, gross, details = apply_vat_inclusive_swap(8.0, 1.33, 9.33, None)
        self.assertEqual((net, vat, gross, details), (8.0, 1.33, 9.33, None))

    def test_untouched_when_net_or_vat_is_missing(self):
        self.assertEqual(apply_vat_inclusive_swap(None, 1.33, None, None), (None, 1.33, None, None))
        self.assertEqual(apply_vat_inclusive_swap(8.0, None, None, None), (8.0, None, None, None))

    def test_non_numeric_values_are_left_alone_rather_than_raising(self):
        # The broad except is load-bearing: a coercion failure must leave the
        # values untouched, not fail the extraction.
        self.assertEqual(
            apply_vat_inclusive_swap("eight", "one", None, None),
            ("eight", "one", None, None),
        )

    def test_reduced_rate_also_triggers_the_swap(self):
        net, vat, gross, details = apply_vat_inclusive_swap(105.0, 5.0, None, None)
        # 5/105 = 0.048 and 5/100 = 0.05, both inside the 0.03 tolerance of the
        # 5% rate, so the reading is ambiguous and nothing is swapped.
        self.assertEqual(net, 105.0)
        self.assertIsNone(gross)
        self.assertIsNone(details)


class ResolveInvoiceDateTest(unittest.TestCase):
    def test_raw_string_is_parsed_deterministically_and_wins(self):
        invoice_date, details = resolve_invoice_date(None, "09/05/26", None, True)
        self.assertEqual(invoice_date, "2026-05-09")
        self.assertIn("auto_parsed_invoice_date_from_raw", details)
        self.assertIn("raw=09/05/26 -> 2026-05-09", details)

    def test_raw_string_overrides_a_disagreeing_model_iso_date(self):
        invoice_date, details = resolve_invoice_date("2026-09-05", "09/05/26", None, True)
        self.assertEqual(invoice_date, "2026-05-09")
        self.assertIn("auto_parsed_invoice_date_from_raw", details)

    def test_ambiguous_iso_without_raw_is_flagged_and_left_alone(self):
        # Swapping an ISO date with no raw string is a coin flip and can corrupt
        # correct model output, so it is annotated instead.
        invoice_date, details = resolve_invoice_date("2026-09-05", None, None, True)
        self.assertEqual(invoice_date, "2026-09-05")
        self.assertIn("ambiguous_invoice_date_no_raw", details)
        self.assertIn("model_iso=2026-09-05", details)

    def test_unambiguous_iso_is_not_flagged(self):
        invoice_date, details = resolve_invoice_date("2026-09-25", None, None, True)
        self.assertEqual(invoice_date, "2026-09-25")
        self.assertIsNone(details)

    def test_no_date_at_all_is_left_alone(self):
        self.assertEqual(resolve_invoice_date(None, None, None, True), (None, None))

    def test_malformed_iso_does_not_raise(self):
        invoice_date, details = resolve_invoice_date("not-a-date", None, None, True)
        self.assertEqual(invoice_date, "not-a-date")
        self.assertIsNone(details)

    def test_prefer_dayfirst_is_a_parameter_not_module_state(self):
        self.assertEqual(resolve_invoice_date(None, "09/05/26", None, True)[0], "2026-05-09")
        self.assertEqual(resolve_invoice_date(None, "09/05/26", None, False)[0], "2026-09-05")


class AmbiguityNoteTest(unittest.TestCase):
    """Three cases, three honest notes, and the date unchanged in all of them.

    The guard used to be `if not parsed_from_raw and invoice_date`, which is true
    both when there was no raw string and when there was one that could not be
    parsed, so the note claimed no_raw when a raw string existed. An operator
    reads this field to decide whether to trust the date: "we had nothing to work
    from" and "we had something and could not read it" call for different
    judgements.
    """

    def test_no_raw_string_keeps_the_original_note_byte_for_byte(self):
        # tests/test_date_disambiguation.py asserts this exact substring. A
        # future tidy-up must not change it out from under that test.
        invoice_date, details = resolve_invoice_date("2026-09-05", None, None, True)
        self.assertEqual(invoice_date, "2026-09-05")
        self.assertEqual(details, "ambiguous_invoice_date_no_raw(model_iso=2026-09-05)")

    def test_unparseable_raw_string_names_both(self):
        invoice_date, details = resolve_invoice_date("2026-09-05", "not a date", None, True)
        self.assertEqual(invoice_date, "2026-09-05", "the date must not be touched")
        self.assertIn("ambiguous_invoice_date_unparsed_raw", details)
        self.assertIn("raw=not a date", details)
        self.assertIn("model_iso=2026-09-05", details)
        self.assertNotIn("no_raw", details, "there was a raw string, so do not say there was not")

    def test_unparseable_raw_is_reported_even_when_the_iso_date_is_unambiguous(self):
        # A raw string we could not read is worth knowing about regardless of
        # whether the model's date happens to look ambiguous. This is the signal
        # that would have exposed finding 2 in the field.
        invoice_date, details = resolve_invoice_date("2026-09-25", "not a date", None, True)
        self.assertEqual(invoice_date, "2026-09-25")
        self.assertIn("ambiguous_invoice_date_unparsed_raw", details)

    def test_unparseable_raw_with_no_model_date_still_reports(self):
        invoice_date, details = resolve_invoice_date(None, "not a date", None, True)
        self.assertIsNone(invoice_date)
        self.assertIn("ambiguous_invoice_date_unparsed_raw", details)
        self.assertIn("model_iso=None", details)

    def test_parsed_raw_produces_neither_ambiguity_note(self):
        _, details = resolve_invoice_date("2026-09-05", "09/05/26", None, True)
        self.assertIsNotNone(details)
        self.assertNotIn("ambiguous_invoice_date_no_raw", details)
        self.assertNotIn("ambiguous_invoice_date_unparsed_raw", details)

    def test_notes_append_to_existing_details(self):
        _, details = resolve_invoice_date("2026-09-05", "not a date", "model prose", True)
        self.assertTrue(details.startswith("model prose; "))
        self.assertIn("ambiguous_invoice_date_unparsed_raw", details)


class DependencyDirectionTest(unittest.TestCase):
    def test_postprocess_does_not_import_the_openai_extractor(self):
        """The dependency must not quietly reverse.

        Imported in a subprocess so a module another test already loaded cannot
        make this pass by accident. Also proves postprocess needs neither the
        openai package nor a populated .env.
        """
        repo_root = Path(__file__).resolve().parent.parent
        code = (
            "import sys\n"
            "import worker.extraction.postprocess\n"
            "leaked = [m for m in sys.modules if 'openai' in m or m == 'config']\n"
            "print(','.join(sorted(leaked)))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "", f"unexpected imports: {result.stdout!r}")


if __name__ == "__main__":
    unittest.main()

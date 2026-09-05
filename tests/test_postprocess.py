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

import logging
import subprocess
import sys
import unittest

import config
from pathlib import Path

from worker.extraction.postprocess import (
    establish_gross_from_vat,
    parse_ambiguous_date,
    resolve_invoice_date,
)

# The rate set these tests hold fixed. It was config.VAT_RATES_IMPLIABLE until
# 2026-09-05, when item 163 moved the rates into the published bundle.
#
# Stated here rather than read back through worker.vat_rates.impliable_rates(),
# for the two reasons tests/test_chart_bundle.py gives for writing its own charts
# instead of copying the real ones. These are direct tests of what
# establish_gross_from_vat() does with a set of rates, so the set has to be fixed
# or every expected percentage below moves the day IntelliCharts publishes; and a
# test that reads OneDrive stops the suite running on a machine with no practice
# root. That impliable_rates() returns this same tuple against the published
# table is asserted separately, by RealBundleRatesTest in tests/test_vat_rates.py.
RECOGNISED_RATES = (0.05, 0.2)


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


class EstablishGrossFromVatTest(unittest.TestCase):
    def test_the_assumption_verifies_and_the_figure_is_the_gross(self):
        # 10d.42. Assume 8.00 is the gross. The implied rate is then
        # 1.33 / (8.00 - 1.33) = 19.94%, which is 20% within the rounding
        # allowance, so the assumption verifies and is accepted.
        net, vat, gross, details = establish_gross_from_vat(8.0, 1.33, None, None, RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE)
        self.assertAlmostEqual(gross, 8.00)
        self.assertAlmostEqual(net, 6.67, places=2)
        self.assertAlmostEqual(vat, 1.33)
        self.assertIn("treated_amount_as_gross", details)
        self.assertIn("implied_rate=19.9%", details)

    def test_an_unrecognised_implied_rate_changes_nothing_and_says_the_percentage(self):
        # 100.00 with 20.00 of VAT implies 20 / 80 = 25%, which is no rate 18.4
        # knows. 10d.42: change nothing, and put the implied percentage in the
        # note so a person can see what the figures actually said.
        net, vat, gross, details = establish_gross_from_vat(100.0, 20.0, None, None, RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE)
        self.assertEqual(net, 100.0)
        self.assertEqual(vat, 20.0)
        self.assertIsNone(gross)
        self.assertIn("gross_not_established", details)
        self.assertIn("implied_rate=25.0%", details)

    def test_the_rounding_allowance_is_not_a_window(self):
        # The old code used a 0.03 tolerance, which is three percentage points,
        # so an implied 17% or 23% was accepted as 20%. Both must now be refused.
        for amount, vat_figure in ((117.0, 17.0), (123.0, 23.0)):
            with self.subTest(amount=amount):
                _, _, gross, details = establish_gross_from_vat(
                    amount, vat_figure, None, None,
                    RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE)
                self.assertIsNone(gross)
                self.assertIn("gross_not_established", details)

    def test_vat_not_less_than_the_amount_changes_nothing(self):
        # The assumption cannot even be stated: there is no net to imply a rate
        # against. Change nothing, and say which case it was.
        net, vat, gross, details = establish_gross_from_vat(5.0, 5.0, None, None, RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE)
        self.assertEqual((net, vat, gross), (5.0, 5.0, None))
        self.assertIn("vat_not_less_than_amount", details)

    def test_note_is_appended_to_existing_details_not_replacing_them(self):
        _, _, _, details = establish_gross_from_vat(8.0, 1.33, None, "model said something", RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE)
        self.assertTrue(details.startswith("model said something; "))
        self.assertIn("treated_amount_as_gross", details)

    def test_untouched_when_gross_is_already_present(self):
        net, vat, gross, details = establish_gross_from_vat(8.0, 1.33, 9.33, None, RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE)
        self.assertEqual((net, vat, gross, details), (8.0, 1.33, 9.33, None))

    def test_untouched_when_net_or_vat_is_missing(self):
        self.assertEqual(establish_gross_from_vat(None, 1.33, None, None, RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE), (None, 1.33, None, None))
        self.assertEqual(establish_gross_from_vat(8.0, None, None, None, RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE), (8.0, None, None, None))

    def test_non_numeric_values_are_left_alone_rather_than_raising(self):
        # The broad except is load-bearing: a coercion failure must leave the
        # values untouched, not fail the extraction.
        self.assertEqual(
            establish_gross_from_vat("eight", "one", None, None, RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE),
            ("eight", "one", None, None),
        )

    def test_the_reduced_rate_verifies_too(self):
        # 105.00 with 5.00 of VAT. Assume 105.00 is the gross: 5 / 100 is exactly
        # 5%, which 18.4 recognises, so it verifies.
        #
        # This changed at 10d.42 and the change is the point of the sub-step. The
        # old code asked whether the figure looked like a gross AND did not look
        # like a net, and 5/105 = 4.76% was inside its three-point tolerance of
        # 5% as well, so it called the reading ambiguous and did nothing.
        # Assume-and-verify has no second test to fail.
        net, vat, gross, details = establish_gross_from_vat(105.0, 5.0, None, None, RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE)
        self.assertAlmostEqual(gross, 105.0)
        self.assertAlmostEqual(net, 100.0)
        self.assertIn("implied_rate=5.0%", details)


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


class SilentHandlerTest(unittest.TestCase):
    """The broad handlers stay, but they must not swallow in silence.

    A genuine error from a shape the next provider returns used to produce no
    line in data/run.log, no note in details, and an extraction that looked as
    though it simply had nothing to correct.
    """

    def test_happy_path_logs_nothing(self):
        logger = logging.getLogger("worker.extraction.postprocess")
        with self.assertNoLogs(logger, level="DEBUG"):
            establish_gross_from_vat(8.0, 1.33, None, None, RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE)
            establish_gross_from_vat(100.0, 20.0, None, None, RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE)
            resolve_invoice_date("2026-09-05", "09/05/26", None, True)
            resolve_invoice_date("2026-09-05", None, None, True)
            parse_ambiguous_date("09/05/26", True)

    def test_vat_swap_warns_once_when_coercion_fails(self):
        with self.assertLogs("worker.extraction.postprocess", level="WARNING") as logs:
            net, vat, gross, details = establish_gross_from_vat("eight", "one", None, None, RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE)
        # Still leaves the values untouched rather than failing the extraction.
        self.assertEqual((net, vat, gross, details), ("eight", "one", None, None))
        self.assertEqual(len(logs.records), 1)
        self.assertIn("vat", logs.output[0].lower())
        self.assertIsNotNone(logs.records[0].exc_info, "the traceback must be attached")

    def test_date_resolution_warns_when_something_raises(self):
        class Hostile:
            """Not a string, and raises on the truthiness test the code performs."""
            def __bool__(self):
                raise RuntimeError("hostile value")

        with self.assertLogs("worker.extraction.postprocess", level="WARNING") as logs:
            invoice_date, details = resolve_invoice_date("2026-09-05", Hostile(), None, True)
        self.assertEqual(invoice_date, "2026-09-05")
        self.assertIsNone(details)
        self.assertEqual(len(logs.records), 1)
        self.assertIsNotNone(logs.records[0].exc_info)

    def test_no_log_line_carries_the_document(self):
        # A receipt is client data. The exception and the field being processed
        # belong in the log; the payload does not.
        with self.assertLogs("worker.extraction.postprocess", level="WARNING") as logs:
            establish_gross_from_vat("eight", "one", None, "supplier prose from the receipt", RECOGNISED_RATES, config.VAT_RATE_ROUNDING_ALLOWANCE)
        self.assertNotIn("supplier prose from the receipt", logs.output[0])


class DependencyDirectionTest(unittest.TestCase):
    def test_postprocess_does_not_import_the_openai_extractor(self):
        """The dependency must not quietly reverse.

        Imported in a subprocess so a module another test already loaded cannot
        make this pass by accident. Also proves postprocess needs neither the
        openai package, nor a populated .env, nor a published bundle.

        worker.vat_rates was added to the leak list on 2026-09-05, item 163, and
        the reason is narrower than the brief that asked for it said.

        The brief expected the old list, 'openai' or config, to be blind to
        postprocess importing worker.vat_rates. It is not: worker/vat_rates.py
        imports config itself, so that import leaks config and the old assertion
        already went red. Verified by mutation on 2026-09-05, adding the import to
        postprocess.py: the old list printed ['config'] and the test failed on it.

        What naming the module buys is that the failure says which import leaked
        rather than only 'config', and that the check survives worker/vat_rates.py
        ever ceasing to import config, at which point the old list would have gone
        quiet with nothing to say why.
        """
        repo_root = Path(__file__).resolve().parent.parent
        code = (
            "import sys\n"
            "import worker.extraction.postprocess\n"
            "leaked = [m for m in sys.modules\n"
            "          if 'openai' in m or m in ('config', 'worker.vat_rates')]\n"
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

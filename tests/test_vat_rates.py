"""The pipeline reads the published VAT rate table. Brief of 2026-09-05, item 163.

Covers `worker/vat_rates.py`, which replaced `config.VAT_RATES` and
`config.VAT_RATES_IMPLIABLE`. Those held the rates as a dict typed into this
repository by hand while `publish_master.py` was publishing the same rates into
`config.CHARTS_DIR`, so there were two copies and one of them was maintained.

**There was no red before green here, and that is the design rather than a gap.**
`impliable_rates()` returns `(0.05, 0.2)`, which is what `VAT_RATES_IMPLIABLE`
returned, so nothing the pipeline does changed and no existing test could go red.
What stands in for it is a mutation: letting the dated rows into the impliable set
must turn `DatedRowsAreNotInForceTest` and `TwelveAndAHalfPercentGuardTest` red.

The fixture writes its own small tables rather than copying the real bundle, for
the two reasons `tests/test_chart_bundle.py` gives: a copy would make the expected
values move whenever IntelliCharts publishes, and a test that reads OneDrive is
not a unit test. The real file is checked separately by RealBundleRatesTest, which
skips when the bundle is not on this machine.
"""

import logging
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import config
from live_paths import LiveBundle
from worker import vat_rates
from worker.extraction.postprocess import establish_gross_from_vat

RATE_HEADER = "name,rate,start,end"

# The table published on 2026-09-05, reproduced row for row because the two
# discriminators live in it: Zero-rated is excluded for being nought, and the
# three dated rows for being dated.
PUBLISHED_ROWS = [
    "Standard,20,,",
    "Reduced,5,,",
    "Zero-rated,0,,",
    "Hospitality (2020-21),5,2020-07-15,2021-09-30",
    "Hospitality (2021-22),12.5,2021-10-01,2022-03-31",
    "Family Attractions (2026),5,2026-06-25,2026-09-01",
]


class VatRateEnvironment:
    """A temp CHARTS_DIR holding a rate table, and an empty parse cache."""

    def __init__(self, rows=None, header=RATE_HEADER, write=True):
        self._rows = PUBLISHED_ROWS if rows is None else rows
        self._header = header
        self._write = write

    def __enter__(self):
        self._temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved_charts_dir = config.CHARTS_DIR
        config.CHARTS_DIR = self.path
        # A module-level cache, so it survives between tests unless cleared. It is
        # restored rather than just emptied, so this fixture cannot leave the real
        # bundle's entry missing for a test that runs after it.
        self._saved_cache = dict(vat_rates._CACHE)
        vat_rates._CACHE.clear()
        if self._write:
            self.write(self._rows, self._header)
        return self

    def __exit__(self, *exc):
        config.CHARTS_DIR = self._saved_charts_dir
        vat_rates._CACHE.clear()
        vat_rates._CACHE.update(self._saved_cache)
        self._temp.cleanup()
        return False

    @property
    def file(self):
        return self.path / vat_rates.VAT_RATES_FILENAME

    def write(self, rows, header=RATE_HEADER):
        # CRLF, because that is what the published file has. Written with
        # newline="" so the terminators reach the file as typed rather than being
        # translated, which is what makes this a test of the reader.
        text = "".join(f"{line}\r\n" for line in [header, *rows])
        with self.file.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return self.file


class PublishedTableTest(unittest.TestCase):
    def test_the_six_row_table_gives_the_two_rates_in_force(self):
        with VatRateEnvironment():
            self.assertEqual(vat_rates.impliable_rates(), (0.05, 0.2))

    def test_every_row_is_read_with_its_rate_as_a_fraction(self):
        with VatRateEnvironment():
            rows = vat_rates.load_rates()
        self.assertEqual(len(rows), 6)
        self.assertEqual(
            [(r.name, r.rate) for r in rows],
            [
                ("Standard", 0.2),
                ("Reduced", 0.05),
                ("Zero-rated", 0.0),
                ("Hospitality (2020-21)", 0.05),
                ("Hospitality (2021-22)", 0.125),
                ("Family Attractions (2026)", 0.05),
            ],
        )

    def test_the_dates_come_back_as_published(self):
        with VatRateEnvironment():
            by_name = {r.name: r for r in vat_rates.load_rates()}
        self.assertEqual((by_name["Standard"].start, by_name["Standard"].end), ("", ""))
        self.assertEqual(by_name["Hospitality (2021-22)"].start, "2021-10-01")
        self.assertEqual(by_name["Hospitality (2021-22)"].end, "2022-03-31")

    def test_a_nil_rate_cannot_be_implied(self):
        # Zero-rated is undated and in force. It is excluded because a positive
        # VAT figure cannot imply a nil rate, not because of its dates.
        with VatRateEnvironment():
            self.assertNotIn(0.0, vat_rates.impliable_rates())

    def test_the_fractions_are_the_ones_config_used_to_hold(self):
        # config.VAT_RATES_IMPLIABLE was (0.05, 0.20), built from float literals.
        # This builds them by dividing, so the equality is worth asserting rather
        # than assuming: a rate that came back as 0.19999999999999998 would sit
        # outside the 0.002 allowance for some receipts and inside it for others.
        with VatRateEnvironment():
            self.assertEqual(vat_rates.impliable_rates(), (0.05, 0.20))


class DatedRowsAreNotInForceTest(unittest.TestCase):
    """Paul's decision, 2026-09-05. An undated row is a rate in force; a dated row
    is a temporary sector relief that applied in a window and does not apply now.

    This is the rule the whole change turns on, so it is asserted directly and not
    only through the published table above."""

    def test_a_dated_row_never_reaches_the_impliable_set(self):
        with VatRateEnvironment(rows=[
            "In force,20,,",
            "Temporary relief,7,2021-10-01,2022-03-31",
        ]):
            self.assertEqual(vat_rates.impliable_rates(), (0.2,))

    def test_a_row_with_only_a_start_is_dated_too(self):
        # publish_master.py refuses to publish a half-dated row, so this cannot
        # reach the bundle. It is asserted because "not in force" has to mean the
        # same thing for a file that did not come from there.
        with VatRateEnvironment(rows=["In force,20,,", "Half dated,7,2021-10-01,"]):
            self.assertEqual(vat_rates.impliable_rates(), (0.2,))

    def test_a_row_with_only_an_end_is_dated_too(self):
        with VatRateEnvironment(rows=["In force,20,,", "Half dated,7,,2022-03-31"]):
            self.assertEqual(vat_rates.impliable_rates(), (0.2,))


class TwelveAndAHalfPercentGuardTest(unittest.TestCase):
    """This protects the Review net. It is not a test of arithmetic.

    A receipt showing 90.00 and VAT of 10.00, where the 90.00 is genuinely the
    figure before VAT, implies 10 / (90 - 10) = 12.5%. That is the 2021-22
    hospitality rate, and it is in the published file. If it were in the impliable
    set the receipt would be silently rewritten to a gross of 90.00 and a net of
    80.00, when the true figures are a gross of 100.00 and a net of 90.00: the
    expense goes in ten pounds light with nothing on screen to say so.

    Any receipt whose VAT is a ninth of the figure does this, and that is not rare.
    It has to reach a person instead, which is what gross_not_established does."""

    def test_a_receipt_implying_twelve_and_a_half_percent_goes_to_review(self):
        with VatRateEnvironment():
            rates = vat_rates.impliable_rates()
        net, vat, gross, details = establish_gross_from_vat(
            90.0, 10.0, None, None, rates, config.VAT_RATE_ROUNDING_ALLOWANCE)
        self.assertIsNone(gross, "12.5% must not verify: the figure is not a gross")
        self.assertEqual((net, vat), (90.0, 10.0), "no amount may be rewritten")
        self.assertIn("gross_not_established", details)
        self.assertIn("implied_rate=12.5%", details)

    def test_the_rate_is_in_the_published_file_but_not_in_the_set(self):
        # The other half. Without it the test above would also pass for a table
        # that had simply lost the row, which would be a publish fault going
        # unnoticed rather than the rule being enforced.
        with VatRateEnvironment():
            self.assertIn(0.125, [r.rate for r in vat_rates.load_rates()])
            self.assertNotIn(0.125, vat_rates.impliable_rates())


class UnreadableRowTest(unittest.TestCase):
    def test_a_rate_written_as_a_percentage_is_skipped_and_logged(self):
        # publish_master.py writes 20, not 20% and not 0.2. A file that did not
        # come from it must not raise on the extraction path.
        with VatRateEnvironment(rows=["Standard,20%,,", "Reduced,5,,"]):
            with self.assertLogs("worker.vat_rates", level=logging.ERROR) as logs:
                rates = vat_rates.impliable_rates()
        self.assertEqual(rates, (0.05,), "the rows that parse are still used")
        message = "\n".join(logs.output)
        self.assertIn("Standard", message)
        self.assertIn("20%", message)

    def test_a_blank_rate_is_skipped_the_same_way(self):
        with VatRateEnvironment(rows=["Standard,20,,", "Nothing there,,,"]):
            with self.assertLogs("worker.vat_rates", level=logging.ERROR):
                self.assertEqual(vat_rates.impliable_rates(), (0.2,))

    def test_a_file_with_no_rate_column_yields_no_rate_rather_than_raising(self):
        # Not a re-validation of the header, which publish_master.py already does.
        # Every row simply fails to parse, which is the safe direction: no rate is
        # recognised, so nothing is rewritten and the receipts reach a person.
        with VatRateEnvironment(rows=["Standard,20"], header="name,percentage"):
            with self.assertLogs("worker.vat_rates", level=logging.ERROR):
                self.assertEqual(vat_rates.impliable_rates(), ())


class MissingFileTest(unittest.TestCase):
    def test_a_missing_table_gives_an_empty_tuple_and_an_error(self):
        # Not an exception: a bundle that has not been published must cost a
        # receipt its implied-rate check, not stop the receipt being processed.
        with VatRateEnvironment(write=False) as env:
            with self.assertLogs("worker.vat_rates", level=logging.ERROR) as logs:
                rates = vat_rates.impliable_rates()
        self.assertEqual(rates, ())
        message = "\n".join(logs.output)
        self.assertIn(str(env.file), message, "the ERROR names the full path")
        self.assertIn("IntelliCharts", message)
        self.assertIn("nothing here creates it", message)

    def test_load_rates_returns_an_empty_list_rather_than_raising(self):
        with VatRateEnvironment(write=False):
            with self.assertLogs("worker.vat_rates", level=logging.ERROR):
                self.assertEqual(vat_rates.load_rates(), [])


class ModificationTimeCacheTest(unittest.TestCase):
    """The table must not be re-read from OneDrive once per receipt."""

    def test_a_second_call_does_not_re_read_the_file(self):
        with VatRateEnvironment() as env:
            first = vat_rates.impliable_rates()
            stat = env.file.stat()
            # Rewritten with different content, then stamped back to the mtime it
            # had. A loader that re-read on every call would return the new rate.
            env.write(["Standard,17.5,,"])
            os.utime(env.file, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            second = vat_rates.impliable_rates()
        self.assertEqual(second, first)
        self.assertNotIn(0.175, second)

    def test_a_changed_modification_time_is_re_read(self):
        # The other half of the same property. Without it the test above would
        # also pass for a loader that read the file once and never again, which
        # would mean a published rate change never reaching the pipeline.
        with VatRateEnvironment() as env:
            vat_rates.impliable_rates()
            env.write(["Standard,17.5,,"])
            stat = env.file.stat()
            os.utime(env.file, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
            self.assertEqual(vat_rates.impliable_rates(), (0.175,))


class CallSiteTest(unittest.TestCase):
    def test_the_extractor_reads_the_rates_at_call_time(self):
        # config.VAT_RATES_IMPLIABLE was a constant bound at import. The rates now
        # come from a file, so the call site has to read them per extraction or a
        # republished table would not reach a running pipeline until it restarted.
        import inspect

        from worker.extraction import openai_vision

        source = inspect.getsource(openai_vision.OpenAIVisionExtractor.extract)
        self.assertIn("vat_rates.impliable_rates()", source)
        self.assertNotIn("VAT_RATES_IMPLIABLE", source)


class DeletedConstantsTest(unittest.TestCase):
    def test_config_no_longer_holds_a_copy_of_the_rates(self):
        # The point of item 163. A second copy that comes back is the fault
        # returning, and it would return silently: everything still passes.
        self.assertFalse(hasattr(config, "VAT_RATES"))
        self.assertFalse(hasattr(config, "VAT_RATES_IMPLIABLE"))

    def test_the_rounding_allowance_stays(self):
        # A tolerance, not a rate. IntelliCharts does not publish it.
        self.assertEqual(config.VAT_RATE_ROUNDING_ALLOWANCE, 0.002)


class RealBundleRatesTest(unittest.TestCase):
    """The value the brief asks for, read from the published file itself.

    **Reads the real bundle through LiveBundle**, for the reason RealBundleTest
    in tests/test_chart_bundle.py gives: conftest redirects config.CHARTS_DIR
    into temp, and without this the class would skip and report success.

    Still skipped where the bundle is genuinely not on the machine.
    """

    def setUp(self):
        self._live = LiveBundle().__enter__()
        self.addCleanup(self._live.__exit__, None, None, None)
        if not (config.CHARTS_DIR / vat_rates.VAT_RATES_FILENAME).is_file():
            self.skipTest(f"no VAT rate table at {config.CHARTS_DIR}")

    def test_the_real_bundle_gives_the_two_rates_in_force(self):
        self.assertEqual(vat_rates.impliable_rates(), (0.05, 0.2))

    def test_the_real_bundle_still_carries_a_dated_row(self):
        # If this ever fails, the undated rule has stopped discriminating and the
        # test above has become a check that cannot fail.
        self.assertTrue(any(r.is_dated for r in vat_rates.load_rates()))


if __name__ == "__main__":
    unittest.main()

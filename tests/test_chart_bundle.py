"""The classifier reads the client's published chart. Brief of 2026-09-04.

Covers `worker/categorisation/chart.py`, which replaced `coa.py` and its 21, 15
and 7 hardcoded four-digit accounts.

The fixture writes small charts of its own rather than copying the real bundle,
for two reasons. A copy would make the test's expected counts move whenever
IntelliCharts publishes, and a test that reads OneDrive is not a unit test. The
real bundle's counts are checked separately, by RealBundleTest, which skips when
the bundle is not on this machine.

One property of the real bundle is reproduced deliberately: **Master_COA.csv has
13 columns and the eight industry and general charts have 14**, because only the
latter carry a leading `chart_code`. The loader reads by column name for that
reason, so the fixture has to have both shapes or the reason goes untested.
"""

import logging
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import config
from live_paths import LiveBundle
from worker.categorisation import chart

CHART_HEADER = (
    "chart_code,code,name,type,status,applies_to,vat_default,vat_variable,"
    "vat_explanation,vat_recoverability,sa103f_box,mtd_itsa_category,notes,"
    "classifier_eligible"
)
# The master chart's own header: the same columns without chart_code.
MASTER_HEADER = CHART_HEADER.replace("chart_code,", "", 1)


def _row(code, name, status="active", eligible="Yes", chart_code="TEST_CHART"):
    """One 14-column row, the shape of an industry or general chart."""
    return ",".join([
        chart_code, code, name, "expense", status, "sole_trader",
        "20", "No", "", "recoverable", "17", "other", "", eligible,
    ])


def _master_row(code, name, status="active", eligible="Yes"):
    """The same row without the leading chart_code, the master's 13-column shape."""
    return _row(code, name, status, eligible).split(",", 1)[1]


class ChartBundleEnvironment:
    """A temp CHARTS_DIR, an empty parse cache and a registry of one client."""

    def __init__(self, chart_code=None):
        self._chart_code = chart_code

    def __enter__(self):
        self._temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved = {
            "CHARTS_DIR": config.CHARTS_DIR,
            "CLIENTS_BY_ID": config.CLIENTS_BY_ID,
        }
        config.CHARTS_DIR = self.path
        record = {"client_id": "CLIENT001", "firm_id": "FIRM001", "trade": "UNSPECIFIED"}
        if self._chart_code is not None:
            record["chart_code"] = self._chart_code
        config.CLIENTS_BY_ID = {"CLIENT001": record}
        # A module-level cache, so it survives between tests unless cleared. It is
        # restored rather than just emptied, so this fixture cannot leave the real
        # bundle's entries missing for a test that runs after it.
        self._saved_cache = dict(chart._CACHE)
        chart._CACHE.clear()

        self.write(
            "TEST_CHART.csv",
            [
                _row("100", "Eligible and active"),
                _row("101", "Also eligible and active"),
                _row("102", "Eligible but retired", status="retired"),
                _row("103", "Active but not eligible", eligible="No"),
                _row("104", "Neither", status="retired", eligible="No"),
            ],
        )
        self.write(
            config.MASTER_CHART_FILENAME,
            [
                _master_row("900", "Master eligible"),
                _master_row("901", "Master not eligible", eligible="No"),
            ],
            header=MASTER_HEADER,
        )
        return self

    def __exit__(self, *exc):
        for name, value in self._saved.items():
            setattr(config, name, value)
        chart._CACHE.clear()
        chart._CACHE.update(self._saved_cache)
        self._temp.cleanup()
        return False

    def write(self, filename, rows, header=CHART_HEADER):
        path = self.path / filename
        path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
        return path


class EligibleFilterTest(unittest.TestCase):
    def test_only_eligible_and_active_rows_come_back(self):
        with ChartBundleEnvironment(chart_code="TEST_CHART"):
            accounts = chart.get_eligible_accounts_for_client("CLIENT001")
        self.assertEqual(
            accounts,
            [("100", "Eligible and active"), ("101", "Also eligible and active")],
        )

    def test_an_eligible_but_retired_account_is_not_offered(self):
        # Every row in today's real bundle is active, so this filter removes
        # nothing there. It is what stops a retired account being proposed the
        # day one appears, and the fixture is the only place it can be tested.
        with ChartBundleEnvironment(chart_code="TEST_CHART"):
            codes = [c for c, _ in chart.get_eligible_accounts_for_client("CLIENT001")]
        self.assertNotIn("102", codes)

    def test_the_master_chart_parses_without_a_chart_code_column(self):
        with ChartBundleEnvironment(chart_code="MASTER"):
            accounts = chart.get_eligible_accounts_for_client("CLIENT001")
        self.assertEqual(accounts, [("900", "Master eligible")])

    def test_a_file_missing_classifier_eligible_yields_nothing_and_logs_an_error(self):
        with ChartBundleEnvironment(chart_code="TEST_CHART") as env:
            env.write(
                "TEST_CHART.csv",
                ["TEST_CHART,200,Some account,expense,active"],
                header="chart_code,code,name,type,status",
            )
            with self.assertLogs("worker.categorisation.chart", level=logging.ERROR) as logs:
                accounts = chart.get_eligible_accounts_for_client("CLIENT001")
        self.assertEqual(accounts, [])
        self.assertIn("classifier_eligible", "\n".join(logs.output))


class MissingChartCodeTest(unittest.TestCase):
    """chart_code is absent from all five client records today, so the fall back
    is the normal case until IntelliBooks writes it."""

    def test_it_falls_back_to_the_master_chart(self):
        with ChartBundleEnvironment(chart_code=None):
            accounts = chart.get_eligible_accounts_for_client("CLIENT001")
        self.assertEqual(accounts, [("900", "Master eligible")])

    def test_the_fall_back_warns_and_names_the_client(self):
        with ChartBundleEnvironment(chart_code=None):
            with self.assertLogs("worker.categorisation.chart", level=logging.WARNING) as logs:
                chart.get_eligible_accounts_for_client("CLIENT001")
        message = "\n".join(logs.output)
        self.assertIn("WARNING", message)
        self.assertIn("CLIENT001", message)
        self.assertIn(config.MASTER_CHART_FILENAME, message)

    def test_an_empty_chart_code_counts_as_absent(self):
        with ChartBundleEnvironment(chart_code="   "):
            with self.assertLogs("worker.categorisation.chart", level=logging.WARNING):
                accounts = chart.get_eligible_accounts_for_client("CLIENT001")
        self.assertEqual(accounts, [("900", "Master eligible")])

    def test_a_client_absent_from_the_registry_falls_back_the_same_way(self):
        with ChartBundleEnvironment(chart_code="TEST_CHART"):
            with self.assertLogs("worker.categorisation.chart", level=logging.WARNING) as logs:
                accounts = chart.get_eligible_accounts_for_client("CLIENT999")
        self.assertEqual(accounts, [("900", "Master eligible")])
        self.assertIn("CLIENT999", "\n".join(logs.output))


class UnknownChartCodeTest(unittest.TestCase):
    def test_a_chart_code_with_no_file_warns_and_falls_back(self):
        with ChartBundleEnvironment(chart_code="NO_SUCH_CHART"):
            with self.assertLogs("worker.categorisation.chart", level=logging.WARNING) as logs:
                accounts = chart.get_eligible_accounts_for_client("CLIENT001")
        message = "\n".join(logs.output)
        self.assertEqual(accounts, [("900", "Master eligible")])
        self.assertIn("NO_SUCH_CHART", message)
        self.assertIn("CLIENT001", message)

    def test_a_missing_bundle_is_an_error_and_suggests_nothing(self):
        # Not an exception: this runs per receipt inside layer 5, so an
        # unpublished bundle must stop the classifier suggesting rather than stop
        # the receipt being processed.
        with ChartBundleEnvironment(chart_code="TEST_CHART") as env:
            (env.path / "TEST_CHART.csv").unlink()
            (env.path / config.MASTER_CHART_FILENAME).unlink()
            with self.assertLogs("worker.categorisation.chart", level=logging.ERROR) as logs:
                accounts = chart.get_eligible_accounts_for_client("CLIENT001")
        self.assertEqual(accounts, [])
        self.assertIn("chart bundle", "\n".join(logs.output))


class ModificationTimeCacheTest(unittest.TestCase):
    """A chart must not be re-read from OneDrive once per receipt."""

    def test_a_second_call_does_not_re_read_the_file(self):
        with ChartBundleEnvironment(chart_code="TEST_CHART") as env:
            first = chart.get_eligible_accounts_for_client("CLIENT001")
            path = env.path / "TEST_CHART.csv"
            stat = path.stat()
            # Rewritten with different content, then stamped back to the mtime it
            # had. A loader that re-read on every call would return the new row.
            env.write("TEST_CHART.csv", [_row("999", "Written after the first read")])
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            second = chart.get_eligible_accounts_for_client("CLIENT001")
        self.assertEqual(second, first)
        self.assertNotIn("999", [code for code, _ in second])

    def test_a_changed_modification_time_is_re_read(self):
        # The other half of the same property. Without it the test above would
        # also pass for a loader that read the file once and never again.
        with ChartBundleEnvironment(chart_code="TEST_CHART") as env:
            chart.get_eligible_accounts_for_client("CLIENT001")
            path = env.path / "TEST_CHART.csv"
            env.write("TEST_CHART.csv", [_row("999", "Published later")])
            stat = path.stat()
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
            second = chart.get_eligible_accounts_for_client("CLIENT001")
        self.assertEqual(second, [("999", "Published later")])

    def test_two_charts_are_cached_separately(self):
        with ChartBundleEnvironment(chart_code="TEST_CHART") as env:
            env.write("OTHER_CHART.csv", [_row("300", "Other chart account")])
            self.assertEqual(
                chart.load_chart("TEST_CHART.csv"),
                [("100", "Eligible and active"), ("101", "Also eligible and active")],
            )
            self.assertEqual(
                chart.load_chart("OTHER_CHART.csv"), [("300", "Other chart account")]
            )


class ChartCodeToFilenameTest(unittest.TestCase):
    def test_master_resolves_to_the_master_filename(self):
        # chart_library.csv calls the master chart MASTER, and its file is
        # Master_COA.csv. Formatting "{chart_code}.csv" would miss it and warn.
        self.assertEqual(chart.chart_filename("MASTER"), config.MASTER_CHART_FILENAME)

    def test_every_other_code_is_its_own_filename(self):
        self.assertEqual(chart.chart_filename("PHV_DRIVER"), "PHV_DRIVER.csv")


class EngineWiringTest(unittest.TestCase):
    """Layer 5 asks for the accounts Intellibills ships, and not for a chart.

    **Rewritten at sub-step 10j.10 on 2026-09-05**, and the replacement is the
    inverse of what was here. `test_ai_suggest_asks_the_loader_for_this_client`
    asserted layer 5 called `get_eligible_accounts_for_client(client_id)`; that
    is now false by design, so it is replaced rather than deleted, and a test
    that layer 5 does **not** reach the chart loader is added beside it. The
    chart is still read, by `fallback.resolve_against_chart()` after
    `categorise()` returns, which is a different question covered in
    tests/test_fallback_accounts.py.
    """

    def test_ai_suggest_asks_for_the_shipped_receipt_accounts(self):
        from worker.categorisation import engine as engine_module

        instance = engine_module.CategorisationEngine(repo=None, enable_ai_fallback=True)
        # OpenAI is patched truthy so the early return on a missing module cannot
        # be what makes this pass, and the loader returns nothing so no API call
        # is ever reached. Nothing here costs money.
        with patch.object(engine_module, "OpenAI", object()), \
             patch.object(engine_module, "load_receipt_accounts",
                          return_value=[]) as loader:
            self.assertIsNone(instance._ai_suggest("somevendor", "CLIENT001"))
        loader.assert_called_once_with()

    def test_ai_suggest_does_not_read_a_chart_at_all(self):
        """The half a rename could not have given us.

        Swapping the loader in the test without swapping it in the engine would
        leave this class green while layer 5 still chose from the client's
        chart: the new loader would simply never be called and the old one
        still would. This asserts the chart loader is untouched."""
        from worker.categorisation import chart as chart_module
        from worker.categorisation import engine as engine_module

        instance = engine_module.CategorisationEngine(repo=None, enable_ai_fallback=True)
        with patch.object(engine_module, "OpenAI", object()), \
             patch.object(engine_module, "load_receipt_accounts", return_value=[]), \
             patch.object(chart_module, "get_eligible_accounts_for_client") as chart_loader:
            instance._ai_suggest("somevendor", "CLIENT001")
        chart_loader.assert_not_called()

    def test_the_engine_module_no_longer_holds_the_chart_loader(self):
        # The sharper form of the test above: a name the engine does not hold
        # cannot be called by accident later. If layer 5 ever needs a chart
        # again that is a decision, and this goes red to make it one.
        from worker.categorisation import engine as engine_module

        self.assertFalse(hasattr(engine_module, "get_eligible_accounts_for_client"))
        self.assertTrue(hasattr(engine_module, "load_receipt_accounts"))

    def test_categorise_reaches_the_receipt_accounts_through_its_call_site(self):
        # The test above calls _ai_suggest() directly, so it says nothing about
        # the call site in categorise(). Found by mutation on 2026-09-04: putting
        # business_type back at that call site left the whole suite green until a
        # test like this was added. Kept for the same reason with the new loader,
        # because the call site is still the untested half.
        from worker.categorisation import engine as engine_module

        instance = engine_module.CategorisationEngine(repo=None, enable_ai_fallback=True)
        with patch.object(engine_module, "OpenAI", object()), \
             patch.object(engine_module, "load_receipt_accounts",
                          return_value=[]) as loader:
            instance.categorise(
                receipt_id="r-1", extraction_id="e-1", supplier_name="Some Vendor",
                client_id="CLIENT001", business_type="PHV_DRIVER",
            )
        loader.assert_called_once_with()

    def test_the_deleted_module_is_gone(self):
        with self.assertRaises(ImportError):
            from worker.categorisation import coa  # noqa: F401


class RealBundleTest(unittest.TestCase):
    """What `load_chart()` returns from the published bundle itself.

    **Renamed in place at sub-step 10j.10, rather than re-pointed or deleted, and
    what changed is what the numbers describe.** Until 2026-09-05 these two
    counts were the size of the pool layer 5 was offered, because layer 5 chose
    from `get_eligible_accounts_for_client()`. It now chooses from the 66
    accounts Intellibills ships, so **95 and 39 no longer describe layer 5 at
    all.** They still describe `load_chart()`'s `classifier_eligible` filter,
    which is still needed and is still the only reader of that column, so the
    assertions stand and the test method says what it is counting.

    The brief of 2026-09-05 asked for a re-point or a rename and for a note of
    which was done: **renamed, with the docstring and the method name changed and
    the numbers untouched.** Nothing was re-pointed, because nothing about what
    this class reads has moved.

    **Reads the real bundle through LiveBundle, not config.CHARTS_DIR.** Since
    tests/conftest.py redirects every config path into a session temp directory,
    the plain constant points at an empty folder and this class would skip, and a
    skipped test reports success. Paul's instruction, 2026-09-05: a test that
    silently skips under the redirect is a check that cannot fail.

    Still skipped where the bundle is genuinely not on the machine, which is the
    condition it always had.
    """

    def setUp(self):
        self._live = LiveBundle().__enter__()
        self.addCleanup(self._live.__exit__, None, None, None)
        if not (config.CHARTS_DIR / config.MASTER_CHART_FILENAME).is_file():
            self.skipTest(f"no chart bundle at {config.CHARTS_DIR}")

    def test_load_chart_returns_the_published_eligible_counts(self):
        # Not "the pool layer 5 is offered" any more. That is 66 for every
        # client and is asserted in tests/test_receipt_accounts.py.
        for filename, expected in (
            (config.MASTER_CHART_FILENAME, 95),
            ("PHV_DRIVER.csv", 39),
        ):
            with self.subTest(chart=filename):
                self.assertEqual(len(chart.load_chart(filename)), expected)

    def test_these_counts_are_no_longer_what_layer_5_sees(self):
        # The half that makes the rename mean something. Without it the class
        # reads as though nothing changed on 2026-09-05.
        from worker.categorisation.receipt_accounts import load_receipt_accounts

        eligible = len(chart.load_chart(config.MASTER_CHART_FILENAME))
        offered = len(load_receipt_accounts())
        self.assertNotEqual(eligible, offered)
        self.assertEqual(offered, len(load_receipt_accounts()),
                         "the shipped list does not depend on any chart")


if __name__ == "__main__":
    unittest.main()

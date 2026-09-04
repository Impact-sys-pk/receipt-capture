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
    """Layer 5 asks for the client's list, not for a business type's."""

    def test_ai_suggest_asks_the_loader_for_this_client(self):
        from worker.categorisation import engine as engine_module

        instance = engine_module.CategorisationEngine(repo=None, enable_ai_fallback=True)
        # OpenAI is patched truthy so the early return on a missing module cannot
        # be what makes this pass, and the loader returns nothing so no API call
        # is ever reached. Nothing here costs money.
        with patch.object(engine_module, "OpenAI", object()), \
             patch.object(engine_module, "get_eligible_accounts_for_client",
                          return_value=[]) as loader:
            self.assertIsNone(instance._ai_suggest("somevendor", "CLIENT001"))
        loader.assert_called_once_with("CLIENT001")

    def test_categorise_passes_the_client_and_not_the_business_type(self):
        # The test above calls _ai_suggest() directly, so it says nothing about
        # the call site in categorise(). Found by mutation: putting business_type
        # back at that call site left the whole suite green until this was added.
        from worker.categorisation import engine as engine_module

        instance = engine_module.CategorisationEngine(repo=None, enable_ai_fallback=True)
        with patch.object(engine_module, "OpenAI", object()), \
             patch.object(engine_module, "get_eligible_accounts_for_client",
                          return_value=[]) as loader:
            instance.categorise(
                receipt_id="r-1", extraction_id="e-1", supplier_name="Some Vendor",
                client_id="CLIENT001", business_type="PHV_DRIVER",
            )
        loader.assert_called_once_with("CLIENT001")

    def test_the_deleted_module_is_gone(self):
        with self.assertRaises(ImportError):
            from worker.categorisation import coa  # noqa: F401


class RealBundleTest(unittest.TestCase):
    """The two counts the brief of 2026-09-04 asks for, read from the published
    bundle itself.

    Skipped where the bundle is not present, so the suite still runs on a machine
    that has no practice root.
    """

    def setUp(self):
        if not (config.CHARTS_DIR / config.MASTER_CHART_FILENAME).is_file():
            self.skipTest(f"no chart bundle at {config.CHARTS_DIR}")

    def test_the_real_bundle_returns_the_published_counts(self):
        for filename, expected in (
            (config.MASTER_CHART_FILENAME, 95),
            ("PHV_DRIVER.csv", 39),
        ):
            with self.subTest(chart=filename):
                self.assertEqual(len(chart.load_chart(filename)), expected)


if __name__ == "__main__":
    unittest.main()

"""The redirect in tests/conftest.py is in force, and the live paths survive it.

**This is the test the whole arrangement needs and would otherwise not have.**
`tests/live_paths.py` redirects the two roots in the environment before `config`
computes eighteen paths from them. If that ever stops working, every test runs
against the live practice root and **every test still passes**, which is exactly
the failure the redirect was built to remove, arriving through a different door.

So the redirect is asserted, not assumed. Enumerated over all 18 constants rather
than a sample of them, because "every config path is redirected" is a set claim
and the way that claim has gone wrong on this project is by checking its members.
"""

import os
import unittest
from pathlib import Path

import config
import live_paths


class RedirectIsInForceTest(unittest.TestCase):
    def test_every_config_path_constant_is_under_a_temp_root(self):
        # BASE_DIR is the repository and is not derived from either root, so it
        # is the one exception and it is named rather than skipped by a rule.
        temp_roots = (live_paths.TEMP_PRACTICE_ROOT, live_paths.TEMP_UNSYNCED_ROOT)
        constants = {
            name: value for name, value in vars(config).items()
            if isinstance(value, Path) and not name.startswith("_")
        }
        self.assertEqual(len(constants), 18,
                         "the number of config Path constants moved; this test "
                         "and tests/live_paths.py both describe 18")

        for name, value in sorted(constants.items()):
            with self.subTest(constant=name):
                if name == "BASE_DIR":
                    self.assertEqual(value, Path(config.__file__).resolve().parent)
                    continue
                self.assertTrue(
                    any(value == r or r in value.parents for r in temp_roots),
                    f"{name} is {value}, which is under neither temp root. The "
                    "redirect is not in force and this test run is touching the "
                    "live practice root.",
                )

    def test_the_five_constants_no_fixture_pins_are_redirected_too(self):
        # The point of doing this in conftest rather than per fixture. Named
        # individually because these are the ones that had no cover at all.
        for name in ("FIRMS_JSON", "INTELLIBILLS_ROOT", "PIPELINE_LOCKFILE",
                     "UNSYNCED_ROOT", "RESOLUTIONS_DIR"):
            with self.subTest(constant=name):
                value = getattr(config, name)
                self.assertNotIn("OneDrive", str(value))
                self.assertTrue(str(value).startswith(str(live_paths.SESSION_ROOT)))

    def test_the_environment_variables_are_the_ones_config_reads(self):
        # Read from config.py's source, not copied, so a rename in config.py
        # cannot leave live_paths.py setting a variable nothing reads.
        self.assertEqual(os.environ[live_paths.PRACTICE_VAR],
                         str(live_paths.TEMP_PRACTICE_ROOT))
        self.assertEqual(os.environ[live_paths.UNSYNCED_VAR],
                         str(live_paths.TEMP_UNSYNCED_ROOT))
        self.assertEqual(config.PRACTICE_ROOT, live_paths.TEMP_PRACTICE_ROOT)
        self.assertEqual(config.UNSYNCED_ROOT, live_paths.TEMP_UNSYNCED_ROOT)


class LivePathsSurviveTest(unittest.TestCase):
    """The other half, and the reason Paul rejected the first proposal.

    A redirect that loses the real paths turns three real-bundle classes into
    skips and two isolation classes into vacuous assertions, and the suite still
    reports green."""

    def test_the_live_roots_are_not_the_temp_ones(self):
        self.assertNotEqual(live_paths.LIVE_PRACTICE_ROOT,
                            live_paths.TEMP_PRACTICE_ROOT)
        self.assertNotEqual(live_paths.LIVE_UNSYNCED_ROOT,
                            live_paths.TEMP_UNSYNCED_ROOT)

    def test_the_live_roots_are_what_config_would_have_resolved(self):
        # The defaults are read out of config.py's own source rather than copied
        # here, so this compares the capture against the file it came from.
        practice_var, practice_default = live_paths._root_declaration("PRACTICE_ROOT")
        unsynced_var, unsynced_default = live_paths._root_declaration("UNSYNCED_ROOT")
        self.assertEqual(live_paths.LIVE_PRACTICE_ROOT, Path(practice_default))
        self.assertEqual(live_paths.LIVE_UNSYNCED_ROOT, Path(unsynced_default))
        self.assertEqual((practice_var, unsynced_var),
                         ("PRACTICE_ROOT", "INTELLIBILLS_UNSYNCED_ROOT"))

    def test_live_maps_a_redirected_path_back(self):
        self.assertEqual(live_paths.live(config.CHARTS_DIR),
                         live_paths.LIVE_PRACTICE_ROOT / "Intellibills" / "Charts")
        self.assertEqual(live_paths.live(config.LOGS_DIR),
                         live_paths.LIVE_UNSYNCED_ROOT / "logs")
        self.assertEqual(live_paths.live(config.REVIEW_ROOT),
                         live_paths.LIVE_PRACTICE_ROOT / "Intellibills" / "Review")

    def test_live_refuses_a_path_under_neither_root(self):
        # Returning it unchanged would hand a test a temp path it believes is
        # live, which is how a vacuous assertion gets written.
        with self.assertRaises(ValueError):
            live_paths.live(Path("C:/somewhere/else"))

    def test_live_bundle_points_charts_dir_at_the_real_one(self):
        before = config.CHARTS_DIR
        with live_paths.LiveBundle() as bundle:
            self.assertEqual(bundle.path, live_paths.live(before))
            self.assertEqual(config.CHARTS_DIR, live_paths.live(before))
        self.assertEqual(config.CHARTS_DIR, before, "it must put it back")

    def test_the_real_bundle_classes_are_not_skipping(self):
        """The failure Paul's instruction rejected, asserted directly.

        Under the first version of this change these three classes read an empty
        temp directory, found no bundle and skipped, and a skipped test reports
        success. This runs them and requires that they ran.
        """
        import unittest as ut

        names = [
            ("test_chart_bundle", "RealBundleTest"),
            ("test_fallback_accounts", "RealBundleFallbackTest"),
            ("test_vat_rates", "RealBundleRatesTest"),
        ]
        if not (live_paths.LIVE_PRACTICE_ROOT / "Intellibills" / "Charts").is_dir():
            self.skipTest("no practice root on this machine, so they may skip")

        for module_name, class_name in names:
            with self.subTest(cls=class_name):
                module = __import__(module_name)
                suite = ut.TestLoader().loadTestsFromTestCase(
                    getattr(module, class_name))
                result = ut.TestResult()
                suite.run(result)
                self.assertTrue(result.wasSuccessful(),
                                result.errors + result.failures)
                self.assertGreater(result.testsRun, 0)
                self.assertEqual(
                    result.skipped, [],
                    f"{class_name} skipped under the redirect, which reports "
                    "success while testing nothing",
                )


class ImportOrderTest(unittest.TestCase):
    def test_live_paths_asserts_config_is_not_already_imported(self):
        # The assertion is at module scope and has already run by the time any
        # test executes, so it cannot be exercised here. This asserts it is
        # present and unconditional, which is what stops a silent regression.
        import ast
        import inspect

        tree = ast.parse(inspect.getsource(live_paths))
        asserts = [n for n in tree.body if isinstance(n, ast.Assert)]
        self.assertEqual(len(asserts), 1, "exactly one module-level assertion")
        source = ast.unparse(asserts[0].test)
        self.assertIn("config", source)
        self.assertIn("sys.modules", source)

    def test_conftest_imports_live_paths_and_nothing_of_ours_before_it(self):
        import ast

        conftest = Path(__file__).resolve().parent / "conftest.py"
        tree = ast.parse(conftest.read_text(encoding="utf-8"))
        imports = [n for n in ast.walk(tree)
                   if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertEqual(len(imports), 1, "conftest.py imports exactly one thing")
        self.assertEqual([a.name for a in imports[0].names], ["live_paths"])


if __name__ == "__main__":
    unittest.main()

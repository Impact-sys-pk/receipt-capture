"""The naming correction of 2026-09-06, held in place by tests.

In this project "code" means a four-digit account code. `7310`, `nominal_code`,
`suggested_code`, `correction_code`. `vendor_code` was the one place it did not:
it held `imo`, a lower-case word produced by `normalise_description()` and
`extract_vendor_key()`. That is a key, and the code already had a name for it.

And in the two learned tables the names were the wrong way round, so `vendor_key`
held a row UUID while `vendor_code` held the key. The correction:

  * the normalised key is `vendor_key`, everywhere
  * a learned mapping's row id is `mapping_id`, never `vendor_key`
  * `vendor_code` does not exist

That produced one `TypeError` in `learn_from_correction()` and one wrong comment
in `_apply_filed_note()` before it was made. These tests exist so it cannot come
back by someone copying a nearby line.
"""

import ast
import sqlite3
import unittest
from pathlib import Path

from worker.categorisation.engine import CategorisationEngine, CategorisationResult
from worker.database import schema

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKER = REPO_ROOT / "worker"

# Every line under worker\ that still contains the string, and why. A comment
# that names the old name is the point of the comment; anything else is a
# survivor of the rename and this test is what catches it.
ALLOWED_SURVIVORS = {
    (
        "worker/categorisation/engine.py",
        '# vendor_code on 2026-09-06: "code" means a four-digit account code',
    ): "names the old field name in CategorisationResult's own comment",
    (
        "worker/resolution/service.py",
        "# normalised key was called `vendor_code` and is now called",
    ): "names the old field name where the comment was reversed by the rename",
}


class VendorCodeIsGone(unittest.TestCase):
    def test_vendor_code_appears_nowhere_in_worker_but_the_named_survivors(self):
        found = {}
        for path in sorted(WORKER.rglob("*.py")):
            rel = path.relative_to(REPO_ROOT).as_posix()
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                if "vendor_code" not in line:
                    continue
                found[(rel, line.strip())] = number

        unexpected = {k: v for k, v in found.items() if k not in ALLOWED_SURVIVORS}
        self.assertEqual(
            unexpected, {},
            "vendor_code survives somewhere it is not allowed to: "
            f"{sorted(unexpected)}",
        )
        # The allowlist is not allowed to rot either. A survivor that has since
        # been removed leaves an entry here that can never fail, and a check
        # that cannot fail is not a check.
        stale = [k for k in ALLOWED_SURVIVORS if k not in found]
        self.assertEqual(stale, [], f"allowlist entries that no longer exist: {stale}")

    def test_every_survivor_is_a_comment(self):
        for (rel, text) in ALLOWED_SURVIVORS:
            self.assertTrue(
                text.startswith("#"),
                f"{rel}: a survivor that is not a comment is live code: {text}",
            )


class TheTwoNamesMeanTheRightThings(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.executescript(_create_statements())
        self.addCleanup(self.conn.close)

    def _columns(self, table):
        return [r[1] for r in self.conn.execute(f"PRAGMA table_info({table})")]

    def _primary_key(self, table):
        return [r[1] for r in self.conn.execute(f"PRAGMA table_info({table})") if r[5]]

    def test_the_learned_tables_are_keyed_on_mapping_id(self):
        for table in ("categorisations_client_vendors", "categorisations_firm_vendors"):
            with self.subTest(table=table):
                self.assertEqual(self._primary_key(table), ["mapping_id"])
                self.assertIn("vendor_key", self._columns(table))
                self.assertNotIn("vendor_code", self._columns(table))

    def test_rules_match_on_a_vendor_key(self):
        columns = self._columns("categorisations_client_rules")
        self.assertIn("vendor_key", columns)
        self.assertNotIn("vendor_code", columns)

    def test_categorisations_points_at_a_mapping_id(self):
        # It holds the row id of the learned mapping a layer matched, so it is a
        # mapping_id. It is not the normalised key and never was.
        columns = self._columns("categorisations")
        self.assertIn("mapping_id", columns)
        self.assertNotIn("vendor_key", columns)
        self.assertNotIn("vendor_code", columns)

    def test_the_result_carries_both_and_names_them_apart(self):
        fields = CategorisationResult.__dataclass_fields__
        self.assertIn("vendor_key", fields)
        self.assertIn("mapping_id", fields)
        self.assertNotIn("vendor_code", fields)


class LearnFromCorrectionIsGone(unittest.TestCase):
    """Item 54, and Paul's decision of 2026-09-06 was to delete it.

    It passed `vendor_key=` to a method taking `vendor_code` and would have
    raised `TypeError` if anything had reached it. Nothing did. It was also the
    only writer `categorisations_firm_vendors` had anywhere, and the firm write
    is item 166, deferred. The rename would have made it work, which is worse
    than leaving it broken: a dead function that raises cannot become a silent
    firm write by accident, and a working one can.
    """

    def test_the_engine_has_no_learn_from_correction(self):
        self.assertFalse(hasattr(CategorisationEngine, "learn_from_correction"))

    def test_nothing_in_the_repository_calls_it(self):
        callers = []
        for path in sorted(REPO_ROOT.rglob("*.py")):
            parts = set(path.parts)
            # docs\specs\ is excluded on purpose. It holds the frozen v0.1
            # spec, which has a .py extension and is a design document: its own
            # CategorisationEngine keeps JSON files in data\ and has never been
            # imported by anything. Its learn_from_correction() is not this one.
            if parts & {".git", ".venv", ".history", "__pycache__", "archive", "docs"}:
                continue
            if path == Path(__file__):
                continue
            if "learn_from_correction" in path.read_text(encoding="utf-8"):
                callers.append(path.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(callers, [], f"learn_from_correction is back in: {callers}")


def _create_statements() -> str:
    """The CREATE script out of init_db(), without opening the live database.

    init_db() connects to config.DB_PATH, and a test that reads the real
    database is a test that depends on what happens to be in it.
    """
    source = (REPO_ROOT / "worker" / "database" / "schema.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "executescript"):
            return ast.literal_eval(node.args[0])
    raise AssertionError("schema.init_db() no longer calls executescript()")


class TheScriptUnderTestIsTheRealOne(unittest.TestCase):
    def test_init_db_exists_and_is_what_was_parsed(self):
        # Guards _create_statements() above: if init_db() stops being one
        # executescript() call, these tests would silently test old SQL.
        self.assertTrue(callable(schema.init_db))
        self.assertIn("CREATE TABLE IF NOT EXISTS categorisations_client_vendors",
                      _create_statements())


if __name__ == "__main__":
    unittest.main()

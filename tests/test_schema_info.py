r"""`schema_info.py` takes its tables from the schema. Flag F9.

Brief `PROMPT_claude_code_2026-11-14_five_small_flags.md`, part 3. The script
kept its own list of eleven tables, which had drifted twice: four tables short
until 2026-09-04, and naming `categorisations_client_rules` after step 10bu
replaced it, until that commit corrected the list by hand.

**Now the names come from `worker.database.schema.declared_columns()`** and
only the descriptions are kept by hand, keyed by table name.

**Neither direction of drift may pass silently.** This suite goes red on
either, and the script itself names the table and exits non-zero.
"""

import contextlib
import io
import sqlite3
import unittest
from unittest import mock

import config
import schema_info
from resolution_fixtures import TempEnvironment
from worker.database import schema


class TheDescriptionsMatchTheSchemaTest(unittest.TestCase):
    """The guard that would have caught both drifts on this project."""

    def test_every_declared_table_is_described_and_nothing_else(self):
        self.assertEqual(set(schema_info.DESCRIPTIONS), set(schema.declared_columns()))


class TheComparisonTest(unittest.TestCase):

    def test_in_step(self):
        listed, undescribed, stale = schema_info.compare({"a": [], "b": []},
                                                         {"a": "A", "b": "B"})
        self.assertEqual((listed, undescribed, stale), ([("a", "A"), ("b", "B")], [], []))

    def test_a_declared_table_with_no_description_is_listed_and_named(self):
        listed, undescribed, stale = schema_info.compare({"a": [], "new": []}, {"a": "A"})
        self.assertEqual(listed, [("a", "A"), ("new", schema_info.NO_DESCRIPTION)])
        self.assertEqual((undescribed, stale), (["new"], []))

    def test_a_described_table_no_longer_declared_is_named_and_not_listed(self):
        listed, undescribed, stale = schema_info.compare({"a": []}, {"a": "A", "gone": "G"})
        self.assertEqual((listed, undescribed, stale), ([("a", "A")], [], ["gone"]))


class TheScriptTest(unittest.TestCase):
    """`main()` against a temporary database: what it prints and how it exits."""

    def run_main(self, descriptions=None):
        out = io.StringIO()
        patch = (mock.patch.object(schema_info, "DESCRIPTIONS", descriptions)
                 if descriptions is not None else contextlib.nullcontext())
        with patch, contextlib.redirect_stdout(out):
            code = schema_info.main()
        return code, out.getvalue()

    def test_in_step_it_lists_every_table_and_exits_nought(self):
        with TempEnvironment():
            schema.init_db()
            code, out = self.run_main()
        self.assertEqual(code, 0)
        for table in schema.declared_columns():
            with self.subTest(table=table):
                self.assertIn(f"TABLE: {table}\n", out)
        self.assertNotIn(schema_info.NO_DESCRIPTION, out)

    def test_drift_either_way_is_printed_and_exits_one(self):
        descriptions = dict(schema_info.DESCRIPTIONS)
        descriptions.pop("receipts")
        descriptions["categorisations_client_rules"] = "the table step 10bu replaced"
        with TempEnvironment():
            schema.init_db()
            code, out = self.run_main(descriptions)
        self.assertEqual(code, 1)
        self.assertIn("TABLE: receipts\n", out)
        self.assertIn(schema_info.NO_DESCRIPTION, out)
        self.assertIn("receipts", out.split("declared with no description:")[1])
        self.assertIn("categorisations_client_rules",
                      out.split("described but no longer declared:")[1])

    def test_no_database_still_refuses(self):
        """Unchanged: an sqlite connection to a missing file would create one."""
        with TempEnvironment():
            with self.assertRaises(SystemExit) as caught:
                schema_info.main()
            self.assertIn("no database at", str(caught.exception))
            self.assertFalse(config.DB_PATH.exists())


if __name__ == "__main__":
    unittest.main()

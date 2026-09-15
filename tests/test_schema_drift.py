"""Refuse to start when the live database is missing a column the schema declares.

## The fault this exists to catch

Step 10p added `line_items TEXT` to `extractions` in `worker/database/schema.py`
on 2026-09-12. `init_db()` runs `CREATE TABLE IF NOT EXISTS`, which creates a
missing table and never alters an existing one, and sub-step 10d.34 removed the
nine `ALTER TABLE ADD COLUMN` migrations. **So the code moved and the live
database did not.**

`save_extraction()` names `line_items` in its INSERT unconditionally, so every
write to `extractions` failed from nine production call sites. It surfaced two
days later, on 2026-09-14 at 12:24 BST, as `sqlite3.OperationalError: table
extractions has no column named line_items`, while applying a Desktop resolution
note. A receipt arriving in those two days would have failed the same way.
Amendment 466 of `2026-07-25_CONSOLE_DESIGN.md`.

**The rest of the suite cannot see this class of fault, and that is structural
rather than an oversight**: every other test builds its database from the
current `schema.py`, so the declared side and the live side are the same object
and can never disagree. These tests are the only ones that build a database
deliberately out of step with the schema.

## How the two sides are read, and why not a parser

Both sides are read by SQLite, from the one definition. The declared side is
`schema.SCHEMA_SQL` run into an in-memory database; the live side is the file on
disk. Neither is parsed.

A regex over `schema.py`'s text was the obvious alternative and it is the wrong
one: a second reader of the schema is a second definition and it drifts, which
is the reason 10d.34 removed the migrations in the first place.

## The out-of-step database is built by removing a column, never by patching the check

Every test below builds its database from `schema.SCHEMA_SQL` with one column
line removed, which is the shape the live fault had: a database created before a
column was declared. A test that stubbed the declared side instead would pass
against a check that read nothing.
"""

import ast
import os
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path

os.environ.setdefault("IMAP_HOST", "example.com")
os.environ.setdefault("IMAP_USERNAME", "test@example.com")
os.environ.setdefault("IMAP_PASSWORD", "password")
os.environ.setdefault("OPENAI_API_KEY", "testkey")

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402
import app  # noqa: E402
import source_guards  # noqa: E402
from worker.database import schema  # noqa: E402


def without_column(sql: str, old: str, new: str = "") -> str:
    """`SCHEMA_SQL` with one column definition removed, refusing unless unique.

    `mutation_harness.replace_once()`'s rule, applied here rather than imported,
    because that module is a script harness that shells out to pytest and this
    is one string operation. The rule is the part that matters: an anchor
    matching twice silently builds a database missing two columns and the test
    then asserts the wrong thing.

    **It has already earned its place here.** `filed_path` was written as a
    one-line anchor first and `SCHEMA_SQL` declares it identically on two
    tables, so the anchor matched twice and this refused before anything was
    built. `new` exists for exactly that case: an anchor made unique by
    carrying a neighbouring line has to put that neighbour back.
    """
    count = sql.count(old)
    if count != 1:
        raise AssertionError(
            f"the anchor {old!r} appears {count} times in SCHEMA_SQL and must "
            "appear once. Zero usually means the column was renamed or "
            "removed; more than one means two tables declare it identically "
            "and the anchor needs a neighbouring line to tell them apart."
        )
    return sql.replace(old, new)


#: The column step 10p added, and the one the live fault was about. Written out
#: with its exact indentation so `without_column()` above refuses if the shape
#: moves, rather than quietly matching nothing.
LINE_ITEMS_LINE = "            line_items          TEXT,\n"

#: `receipts.filed_path`, carrying the line above it because `statements`
#: declares `filed_path` byte-identically and the shorter anchor matches both.
#: A second column on a second table, so a test can prove the check names every
#: missing column rather than the first one it meets.
RECEIPTS_FILED_PATH = ("            file_hash           TEXT NOT NULL,\n"
                       "            filed_path          TEXT,\n")
RECEIPTS_FILED_PATH_KEPT = "            file_hash           TEXT NOT NULL,\n"

#: `statements.filed_path`, the other of the two. Its neighbour differs, which
#: is the only reason either can be named at all.
STATEMENTS_FILED_PATH = ("            file_path           TEXT NOT NULL,\n"
                         "            filed_path          TEXT,\n")
STATEMENTS_FILED_PATH_KEPT = "            file_path           TEXT NOT NULL,\n"


class Database:
    """A database file built from a given schema script, for one test."""

    def __init__(self, sql):
        self._dir = tempfile.TemporaryDirectory(prefix="schema-drift-")
        self.path = Path(self._dir.name) / "receipts.db"
        self.execute(sql)

    def execute(self, sql):
        conn = sqlite3.connect(self.path)
        try:
            conn.executescript(sql)
            conn.commit()
        finally:
            conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._dir.cleanup()
        return False


class MissingColumnsAreFound(unittest.TestCase):
    def test_the_live_fault_is_reported_by_name(self):
        with Database(without_column(schema.SCHEMA_SQL, LINE_ITEMS_LINE)) as db:
            self.assertEqual(schema.missing_columns(db.path),
                             {"extractions": ["line_items"]})

    def test_every_missing_column_is_named_not_only_the_first(self):
        sql = without_column(schema.SCHEMA_SQL, LINE_ITEMS_LINE)
        sql = without_column(sql, RECEIPTS_FILED_PATH, RECEIPTS_FILED_PATH_KEPT)
        with Database(sql) as db:
            self.assertEqual(schema.missing_columns(db.path),
                             {"extractions": ["line_items"],
                              "receipts": ["filed_path"]})

    def test_the_same_column_name_on_two_tables_is_told_apart(self):
        """`receipts` and `statements` both declare `filed_path`.

        So a check keyed on column names rather than on `(table, column)` would
        see the name present somewhere and report nothing. Removed from one
        table at a time, and each time the other table must be silent.
        """
        sql = without_column(schema.SCHEMA_SQL, RECEIPTS_FILED_PATH,
                             RECEIPTS_FILED_PATH_KEPT)
        with Database(sql) as db:
            self.assertEqual(schema.missing_columns(db.path),
                             {"receipts": ["filed_path"]})
        sql = without_column(schema.SCHEMA_SQL, STATEMENTS_FILED_PATH,
                             STATEMENTS_FILED_PATH_KEPT)
        with Database(sql) as db:
            self.assertEqual(schema.missing_columns(db.path),
                             {"statements": ["filed_path"]})

    def test_a_database_matching_the_schema_reports_nothing(self):
        with Database(schema.SCHEMA_SQL) as db:
            self.assertEqual(schema.missing_columns(db.path), {})

    def test_an_undeclared_column_is_not_a_missing_one(self):
        """A column the live database has and the schema does not is harmless.

        Nothing writes it and nothing reads it. The brief's scope: report it if
        that is free, but it must never refuse the start.
        """
        with Database(schema.SCHEMA_SQL) as db:
            db.execute("ALTER TABLE receipts ADD COLUMN invented_by_hand TEXT")
            self.assertEqual(schema.missing_columns(db.path), {})
            self.assertEqual(schema.undeclared_columns(db.path),
                             {"receipts": ["invented_by_hand"]})

    def test_a_missing_table_is_not_this_checks_business(self):
        """`init_db()` creates a missing table, so its columns are not missing.

        Without this the check would report every column of every table on a
        database that is merely younger than a table, and the message would run
        to hundreds of columns for a fault that fixes itself a line earlier.
        """
        with Database(schema.SCHEMA_SQL) as db:
            db.execute("DROP TABLE publish_events")
            self.assertEqual(schema.missing_columns(db.path), {})

    def test_a_database_file_that_does_not_exist_reports_nothing(self):
        """A first run has no database yet, and `init_db()` is about to make it.

        Opening a missing file with sqlite3 creates an empty one, so the check
        has to ask whether the file is there rather than find nought tables and
        agree with itself.
        """
        with tempfile.TemporaryDirectory() as tmp:
            absent = Path(tmp) / "not-here.db"
            self.assertEqual(schema.missing_columns(absent), {})
            self.assertFalse(absent.exists(),
                             "the check must not create the database it reads")


class TheMessageIsForPaul(unittest.TestCase):
    """It is read in a console window, so it says what is wrong and what to do."""

    def test_no_drift_gives_no_message(self):
        with Database(schema.SCHEMA_SQL) as db:
            self.assertIsNone(schema.schema_drift_message(db.path))

    def test_the_message_names_the_database_and_every_column(self):
        sql = without_column(schema.SCHEMA_SQL, LINE_ITEMS_LINE)
        sql = without_column(sql, RECEIPTS_FILED_PATH, RECEIPTS_FILED_PATH_KEPT)
        with Database(sql) as db:
            message = schema.schema_drift_message(db.path)
            self.assertIsNotNone(message)
            self.assertIn(str(db.path), message)
            self.assertIn("extractions.line_items", message)
            self.assertIn("receipts.filed_path", message)

    def test_the_message_is_one_line(self):
        """The log format puts its prefix on the first line and on no other.

        A message with a newline in it reaches `run.log` as a prefixed line
        followed by an orphan, and the console window the same way.
        """
        with Database(without_column(schema.SCHEMA_SQL, LINE_ITEMS_LINE)) as db:
            self.assertNotIn("\n", schema.schema_drift_message(db.path))


class TheStartUpRefuses(unittest.TestCase):
    """`app.main()` itself, in both directions.

    A check that cannot fail is not a check, so the same `main()` is driven over
    a drifted database and a matching one, and the difference is whether it ever
    reaches the lock.
    """

    def setUp(self):
        self._db_path = config.DB_PATH
        self._acquire = app.acquire_lock
        self._git = config.check_git_status_on_startup
        self.reached_lock = False

        def acquire_lock():
            self.reached_lock = True
            return False  # Stops main() here either way, so it never polls.

        app.acquire_lock = acquire_lock
        config.check_git_status_on_startup = lambda: None

    def tearDown(self):
        config.DB_PATH = self._db_path
        app.acquire_lock = self._acquire
        config.check_git_status_on_startup = self._git

    def test_a_drifted_database_stops_main_before_the_lock(self):
        with Database(without_column(schema.SCHEMA_SQL, LINE_ITEMS_LINE)) as db:
            config.DB_PATH = db.path
            with self.assertLogs("app", level="ERROR") as logged:
                app.main()
            self.assertFalse(self.reached_lock,
                             "main() went past the schema check to the lock")
            self.assertTrue(
                any("extractions.line_items" in line for line in logged.output),
                f"the refusal did not name the column: {logged.output}")

    def test_a_matching_database_gets_past_the_schema_check(self):
        with Database(schema.SCHEMA_SQL) as db:
            config.DB_PATH = db.path
            app.main()
            self.assertTrue(self.reached_lock,
                            "main() stopped before the lock on a sound database")

    def test_init_db_runs_before_the_check_so_a_first_run_starts(self):
        """No database file at all: `init_db()` makes it and the check passes.

        This is the ordering the brief names, and it is the direction that
        breaks if the check is moved above `init_db()`: a first run would then
        read a file that does not exist, and if that ever came to mean "every
        column is missing" the pipeline could never start on a clean machine.
        """
        with tempfile.TemporaryDirectory() as tmp:
            config.DB_PATH = Path(tmp) / "fresh.db"
            app.main()
            self.assertTrue(self.reached_lock)
            self.assertTrue(config.DB_PATH.exists(),
                            "main() did not create the database")
            self.assertEqual(schema.missing_columns(config.DB_PATH), {})


class TheCheckIsWiredIntoMain(unittest.TestCase):
    """Read off `app.py`'s syntax tree, so a comment about it cannot answer.

    `tests/source_guards.py`'s reason, and this file needs it: the refusal is
    described in prose in three places in this repository.
    """

    def setUp(self):
        tree = source_guards.tree_of("app.py")
        main = [node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "main"]
        self.assertEqual(len(main), 1, "app.py defines main() once")
        self.calls = source_guards.called_names(main[0])

    def test_main_calls_init_db_and_then_the_check_and_then_the_lock(self):
        for name in ("init_db", "schema_drift_message", "acquire_lock"):
            self.assertIn(name, self.calls, f"main() no longer calls {name}()")
        self.assertLess(max(self.calls["init_db"]),
                        min(self.calls["schema_drift_message"]),
                        "the check must run after init_db(), not before")
        self.assertLess(max(self.calls["schema_drift_message"]),
                        min(self.calls["acquire_lock"]),
                        "the check must run before the lock is taken")


class TheDeclaredSideIsReadBySqliteAndNotByAParser(unittest.TestCase):
    """The choice the brief asked to be made explicitly.

    `SCHEMA_SQL` is the one definition. `init_db()` executes it against the file
    and `declared_columns()` executes it against `:memory:`, so both sides are
    read by SQLite. If `init_db()` ever stops executing the constant, the two
    sides stop being the same definition and this check quietly starts comparing
    the live database against something nothing creates.
    """

    def test_init_db_executes_the_constant(self):
        tree = source_guards.tree_of("worker", "database", "schema.py")
        found = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == "init_db"]
        self.assertEqual(len(found), 1)
        scripts = [node for node in ast.walk(found[0])
                   if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Attribute)
                   and node.func.attr == "executescript"]
        self.assertEqual(len(scripts), 1, "init_db() runs one script")
        self.assertEqual(ast.unparse(scripts[0].args[0]), "SCHEMA_SQL",
                         "init_db() must execute SCHEMA_SQL itself, or the "
                         "declared side stops being the side that is created")

    def test_the_declared_side_is_every_table_the_schema_creates(self):
        declared = schema.declared_columns()
        with Database(schema.SCHEMA_SQL) as db:
            conn = sqlite3.connect(db.path)
            try:
                live = {row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' "
                    "AND name NOT LIKE 'sqlite_%'")}
            finally:
                conn.close()
        self.assertEqual(set(declared), live)
        self.assertIn("line_items", declared["extractions"])


if __name__ == "__main__":
    unittest.main()

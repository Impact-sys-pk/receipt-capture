r"""Which surfaces show London, which still show UTC, and a guard over the set.

Paul's decision of 2026-09-11, briefed as
`PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md`.
`tests/test_london_time.py` holds the conversion itself; this file holds the
surfaces it was applied to.

## Why there is a guard as well as per-surface tests

`CLAUDE.md`, 2026-09-08: **a per-path test proves a path works, and only a guard
over the set proves the set is complete.** The brief's own words are that half
of this change is worse than none of it, because a report showing London beside
a log showing UTC makes the two disagree about which day something happened and
both look authoritative. So
`test_no_f_string_renders_a_timestamp_column_without_converting_it` sweeps the
whole production tree from the syntax tree, and it is what catches the surface
somebody adds next month.

**The guard is narrowed to a READ of a timestamp column**, a subscript, a
`.get("...")` or an attribute, rather than to any text containing a column name.
A local variable called `filed_at` that was already converted on the line above
is not a finding, and matching on its name would have made the guard demand the
conversion twice.

## What deliberately still shows UTC, and why

Named here rather than left as an absence, because an absence is not a decision.

- **The database.** `tests/test_london_time.py` holds that every writer still
  passes `timezone.utc`. Stored local time cannot tell the two 01:30s on the
  last Sunday in October apart, and these columns are compared as text in SQL.
- **`runs.ndjson` and `receipt_events_<firm>.ndjson`**, machine-readable run and
  event logs.
- **`pipeline-status.json`**, whose five keys are a contract with IntelliBooks
  Desktop.
- **Resolution notes and the `note_resolved_at` that travels with them**,
  written by Desktop and parsed by the pipeline.
- **Sidecars**, parsed by `parseSidecar()` in IntelliBooks Desktop.
- **`C:\Intellibills\pipeline.lock`'s `started_at=` field**, compared against a
  process creation time by `_lock_describes_process()`. What `acquire_lock()`
  says out loud about it converts; the field does not.
- **`export_bookkeeping.py`'s `first_extracted_at` column**, whose header is the
  database's own column name. See `ExportPathTest`.
- **`_create_daily_backup()`'s filename**, which is an idempotency key and the
  sort key `_cleanup_old_backups()` rotates on, not a rendering.
"""

import ast
import json
import logging
import sqlite3
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import config

import source_guards
from worker import london_time
from worker.storage import store

REPO_ROOT = Path(source_guards.REPO_ROOT)

#: Stored at half past eleven at night on 30 June, UTC. In London that is half
#: past midnight on 1 July. Every test below that needs the boundary uses it.
JUNE_30_LATE_UTC = "2026-06-30T23:30:00+00:00"

#: The timestamp columns, as `worker\database\schema.py` spells them, plus the
#: two names a resolution note and a sidecar carry.
TIMESTAMP_COLUMNS = {
    "created_at", "filed_at", "locked_at", "extracted_at", "processed_at",
    "email_received_at", "categorised_at", "corrected_at", "alert_sent_at",
    "last_updated", "resolved_at", "reviewed_at",
}


def production_files():
    r"""The repository root and the worker tree.

    `.history\` is excluded by construction: the root glob is not recursive and
    the worker glob is rooted inside `worker\`. `CLAUDE.md`'s sixth trap.
    """
    return (sorted(REPO_ROOT.glob("*.py"))
            + sorted(REPO_ROOT.glob("worker/**/*.py")))


def _reads_a_timestamp_column(expr):
    """The column this expression reads, or None.

    `row["created_at"]`, `receipt.get("filed_at")`, `note.resolved_at`.
    """
    for node in ast.walk(expr):
        if isinstance(node, ast.Subscript):
            index = node.slice
            if isinstance(index, ast.Constant) and index.value in TIMESTAMP_COLUMNS:
                return index.value
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get" and node.args):
            first = node.args[0]
            if isinstance(first, ast.Constant) and first.value in TIMESTAMP_COLUMNS:
                return first.value
        if isinstance(node, ast.Attribute) and node.attr in TIMESTAMP_COLUMNS:
            return node.attr
    return None


def rendered_timestamps():
    """Every f-string interpolation in production that reads a timestamp column.

    (file, line, column, source text, converts).
    """
    found = []
    for path in production_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FormattedValue):
                continue
            column = _reads_a_timestamp_column(node.value)
            if column is None:
                continue
            text = ast.unparse(node.value)
            found.append((path.relative_to(REPO_ROOT), node.lineno, column,
                          text, "london_time" in text))
    return found


class TheSetOfSurfacesTest(unittest.TestCase):
    """The guard. A new surface added without the conversion goes red here."""

    def test_no_f_string_renders_a_timestamp_column_without_converting_it(self):
        rendered = rendered_timestamps()
        self.assertTrue(
            rendered,
            "no f-string in the production tree reads a timestamp column at "
            "all, which means this guard has stopped looking rather than that "
            "the tree is clean")
        bare = [f"{rel}:{line}  [{column}]  {{{text}}}"
                for rel, line, column, text, converts in rendered if not converts]
        self.assertEqual(
            bare, [],
            "these print a stored timestamp to a person without converting it "
            "to London. Store UTC, show London, Paul's decision of 2026-09-11: "
            "wrap the value in `london_time.stamp()`, or, if it is genuinely "
            "machine-readable, say so in this file's docstring and add it "
            "there:\n  " + "\n  ".join(bare))

    def test_the_sweep_never_reads_vscode_local_history(self):
        # CLAUDE.md's sixth trap: `.history\` holds a dated copy of every file
        # ever edited, so a sweep that includes it reports names that no longer
        # exist anywhere live.
        self.assertFalse(
            [p for p in production_files() if ".history" in p.parts],
            "the production sweep is reading VS Code's local history")


class ArchiveFolderTest(unittest.TestCase):
    r"""Section 5 of the brief. `Intellibills\Documents\{client}\{year}\{month}\`
    takes the London arrival date.

    A receipt arriving at 00:30 on 1 July British time was filed under June.
    That folder is browsed by a person, so it converts with the rest.
    """

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._temp.name)
        self._saved = config.FILES_DIR
        config.FILES_DIR = self.root / "Documents"

    def tearDown(self):
        config.FILES_DIR = self._saved
        self._temp.cleanup()

    def _at(self, iso_utc):
        """`london_time.now()` pinned to one instant, converted for real."""
        moment = datetime.fromisoformat(iso_utc).astimezone(london_time.london_zone())
        return mock.patch.object(london_time, "now", return_value=moment)

    def test_an_email_attachment_arriving_after_midnight_london_is_filed_in_july(self):
        with self._at(JUNE_30_LATE_UTC):
            written = store.save_file("r-1", "CLIENT001", "receipt.pdf", b"x")
        self.assertEqual(written.parent,
                         config.FILES_DIR / "CLIENT001" / "2026" / "07")

    def test_an_inbox_file_arriving_at_the_same_instant_is_filed_in_july_too(self):
        source = self.root / "inbox.pdf"
        source.write_bytes(b"x")
        with self._at(JUNE_30_LATE_UTC):
            written = store.save_inbox_file("r-2", "CLIENT001", source)
        self.assertEqual(written.parent,
                         config.FILES_DIR / "CLIENT001" / "2026" / "07")

    def test_the_middle_of_the_day_is_unaffected(self):
        # The other direction: a conversion that moved everything on by a month
        # would pass the two above and fail this.
        with self._at("2026-07-15T12:00:00+00:00"):
            written = store.save_file("r-3", "CLIENT001", "receipt.pdf", b"x")
        self.assertEqual(written.parent,
                         config.FILES_DIR / "CLIENT001" / "2026" / "07")

    def test_in_winter_the_two_zones_agree_and_the_folder_is_the_same(self):
        with self._at("2026-01-31T23:30:00+00:00"):
            written = store.save_file("r-4", "CLIENT001", "receipt.pdf", b"x")
        self.assertEqual(written.parent,
                         config.FILES_DIR / "CLIENT001" / "2026" / "01")

    def test_only_these_two_functions_build_the_archive_path(self):
        r"""The premise section 5 of the brief rests on, re-run rather than
        trusted: nothing recomputes this path to READ, so historic files keep
        the folder they are in and nothing has to move.

        Three references in the production tree. Two are these writers and the
        third is a log line naming the folder in an error message.
        """
        # Counted per FILE, never per line: `CLAUDE.md`, 2026-09-07, a name
        # does not move and a line number does. A document full of refreshed
        # numbers is a document that looks checked.
        references = {}
        for path in production_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Attribute) and node.attr == "FILES_DIR"
                        and isinstance(node.value, ast.Name)
                        and node.value.id == "config"):
                    key = str(path.relative_to(REPO_ROOT))
                    references[key] = references.get(key, 0) + 1
        self.assertEqual(
            references,
            {"worker\\storage\\store.py": 2,
             "worker\\resolution\\service.py": 1},
            "config.FILES_DIR is referenced somewhere new, or a different "
            "number of times. If the new one READS the path by recomputing the "
            "year and month, the London change of 2026-09-11 has split the "
            "archive in two and that needs deciding rather than accepting. "
            f"Found: {references}")


class StorageStillWritesUtcTest(unittest.TestCase):
    """The machine-readable outputs, driven rather than read.

    `tests/test_london_time.py` asserts from the syntax tree that every
    `datetime.now()` in production passes `timezone.utc`. This writes the four
    files and reads the value back, because a source guard and a behaviour test
    fail in different ways.
    """

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._temp.name)
        self._saved = {
            "LOGS_DIR": config.LOGS_DIR,
            "RUNS_LOG": config.RUNS_LOG,
            "PIPELINE_STATUS_PATH": config.PIPELINE_STATUS_PATH,
            "DB_PATH": config.DB_PATH,
        }
        config.LOGS_DIR = self.root / "logs"
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
        config.PIPELINE_STATUS_PATH = self.root / "pipeline-status.json"
        config.DB_PATH = self.root / "receipts.db"

    def tearDown(self):
        for name, value in self._saved.items():
            setattr(config, name, value)
        self._temp.cleanup()

    def assertStoredUtc(self, value, what):
        self.assertTrue(
            value.endswith("+00:00"),
            f"{what} is no longer stored in UTC. It reads {value!r}. Storage "
            "does not move: only what a person reads converts.")

    def test_runs_ndjson_keeps_utc(self):
        import app
        app._log_run("run-1", datetime.now(timezone.utc).isoformat(),
                     datetime.now(timezone.utc).isoformat(), {"receipts": 0})
        entry = json.loads(config.RUNS_LOG.read_text(encoding="utf-8").strip())
        self.assertStoredUtc(entry["started_at"], "runs.ndjson started_at")
        self.assertStoredUtc(entry["finished_at"], "runs.ndjson finished_at")

    def test_the_per_firm_event_log_keeps_utc(self):
        import app
        app._log_receipt("r-1", "<m@x>", "receipt.pdf", "created", "FIRM001")
        path = config.LOGS_DIR / "receipt_events_FIRM001.ndjson"
        entry = json.loads(path.read_text(encoding="utf-8").strip())
        self.assertStoredUtc(entry["timestamp"], "the per-firm event log")

    def test_pipeline_status_json_keeps_utc(self):
        import app
        app._write_pipeline_status(datetime.now(timezone.utc).isoformat(), 0, 0, None)
        payload = json.loads(config.PIPELINE_STATUS_PATH.read_text(encoding="utf-8"))
        self.assertStoredUtc(payload["last_run"], "pipeline-status.json last_run")

    def test_receipts_created_at_keeps_utc(self):
        from worker.database.repository import Repository
        repo = Repository()
        try:
            repo.save_receipt(
                receipt_id="r-1", message_id="<m@x>", email_subject="s",
                email_from="c@example.com", email_received_at=JUNE_30_LATE_UTC,
                filename="receipt.pdf", file_path="/store/receipt.pdf",
                file_hash="h" * 8, firm_id="FIRM001", client_id="CLIENT001",
                source="email")
            row = repo._conn.execute(
                "SELECT created_at FROM receipts WHERE receipt_id = 'r-1'").fetchone()
        finally:
            repo.close()
        self.assertStoredUtc(row[0], "receipts.created_at")

    def test_the_review_sidecar_keeps_utc(self):
        from worker import filing
        target = self.root / "review"
        target.mkdir()
        path = filing.write_review_file(
            target, "receipt.pdf", "r-1", "needs_review", ["a reason"], {})
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertStoredUtc(payload["timestamp"], "the review sidecar")


class ProcessLogTest(unittest.TestCase):
    """The four process logs, driven through `attach_log_handler()`."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._saved = config.LOGS_DIR
        config.LOGS_DIR = Path(self._temp.name) / "logs"
        self._root = logging.getLogger()
        self._saved_handlers = list(self._root.handlers)
        self._saved_level = self._root.level

    def tearDown(self):
        for handler in list(self._root.handlers):
            if handler not in self._saved_handlers:
                handler.close()
                self._root.removeHandler(handler)
        self._root.setLevel(self._saved_level)
        config.LOGS_DIR = self._saved
        self._temp.cleanup()

    def test_a_line_written_to_a_process_log_is_in_london_and_says_so(self):
        from worker import logging_setup
        path = logging_setup.attach_log_handler("run")

        # `record.created` is stamped inside `LogRecord.__init__`, from a clock
        # this test cannot reach on 3.13 and later. A filter is the documented
        # way to change a record before it is formatted, and it pins the one
        # field the formatter reads.
        moment = datetime.fromisoformat(JUNE_30_LATE_UTC).timestamp()

        class PinTheClock(logging.Filter):
            def filter(self, record):
                record.created = moment
                record.msecs = 0.0
                return True

        logger = logging.getLogger("worker.test")
        logger.addFilter(PinTheClock())
        try:
            logger.info("a line")
        finally:
            logger.filters.clear()
        for handler in self._root.handlers:
            handler.flush()
        text = path.read_text(encoding="utf-8")
        self.assertIn("a line", text)
        line = [ln for ln in text.splitlines() if "a line" in ln][-1]
        self.assertTrue(line.startswith("2026-07-01 00:30:00,000 BST "), line)

    def test_every_entry_point_shares_one_formatter(self):
        from worker import logging_setup
        for entry_point in sorted(logging_setup.ENTRY_POINT_LOGS):
            with self.subTest(entry_point=entry_point):
                logging_setup.attach_log_handler(entry_point)
        formatters = {type(h.formatter) for h in self._root.handlers
                      if isinstance(h, logging.handlers.RotatingFileHandler)}
        self.assertEqual(formatters, {london_time.LondonFormatter})


class ExportPathTest(unittest.TestCase):
    r"""Section 4 of the brief. `export_bookkeeping.py` wrote to
    `Path("exports/bookkeeping_export.csv")`, relative to the working directory,
    so running it from anywhere else created an `exports\` wherever the shell
    was standing. It now derives from `config.BASE_DIR`, as `capture_report.py`
    already did.

    Read from the syntax tree rather than by running the script, because the
    script does its work at module scope and importing it would open the
    database.
    """

    def _assignments(self):
        tree = source_guards.tree_of("export_bookkeeping.py")
        found = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        found[target.id] = ast.unparse(node.value)
        return found

    def test_the_output_folder_is_derived_from_config_base_dir(self):
        assignments = self._assignments()
        self.assertIn("OUTPUT_DIR", assignments)
        self.assertEqual(assignments["OUTPUT_DIR"], "config.BASE_DIR / 'exports'")

    def test_the_output_file_is_under_that_folder(self):
        assignments = self._assignments()
        self.assertEqual(assignments["output"],
                         "OUTPUT_DIR / 'bookkeeping_export.csv'")

    def test_no_path_in_it_is_relative_to_the_working_directory(self):
        tree = source_guards.tree_of("export_bookkeeping.py")
        relative = [f"line {lineno}: Path({value!r})"
                    for value, lineno in source_guards.string_constants(tree)
                    if value.startswith("exports/") or value.startswith("exports\\")]
        self.assertEqual(
            relative, [],
            "a path relative to the working directory is back. It scatters an "
            f"exports\\ wherever the shell is standing: {relative}")

    def test_it_writes_where_capture_report_writes(self):
        import capture_report
        assignments = self._assignments()
        self.assertEqual(
            assignments["OUTPUT_DIR"],
            f"config.BASE_DIR / {str(capture_report.OUTPUT_DIR.name)!r}")


class AlreadyFiledMessageTest(unittest.TestCase):
    """The one operator message whose timestamp reaches a person three ways:
    the CLI, `run.log`, and a `.error.txt` beside a failed resolution note."""

    def test_it_reads_the_filed_time_back_in_london(self):
        from worker.database.repository import Repository
        from worker.resolution.service import resolve_receipt
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
            saved = config.DB_PATH
            config.DB_PATH = Path(temp) / "receipts.db"
            repo = Repository()
            try:
                repo.save_receipt(
                    receipt_id="r-1", message_id="<m@x>", email_subject="s",
                    email_from="c@example.com",
                    email_received_at=JUNE_30_LATE_UTC, filename="receipt.pdf",
                    file_path="/store/receipt.pdf", file_hash="h" * 8,
                    firm_id="FIRM001", client_id="CLIENT001", source="email")
                repo._conn.execute(
                    "UPDATE receipts SET filed_path = ?, filed_at = ? "
                    "WHERE receipt_id = 'r-1'",
                    ("/clients/x/receipt.pdf", JUNE_30_LATE_UTC))
                repo._conn.commit()
                outcome = resolve_receipt(repo, None, "r-1", None,
                                          actor="paul", source="cli")
            finally:
                repo.close()
                config.DB_PATH = saved
        self.assertEqual(outcome.outcome, "already_filed")
        self.assertIn("2026-07-01 00:30 BST", outcome.message)
        self.assertNotIn("+00:00", outcome.message)


if __name__ == "__main__":
    unittest.main()

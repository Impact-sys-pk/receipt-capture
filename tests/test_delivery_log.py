"""Step 10az: the per-client delivery log, one line per document delivered.

**Amendment 456 of `2026-07-25_CONSOLE_DESIGN.md`, closing the half of
outstanding item 131 that the pipeline owns.** Step 10au is a reconciliation
check on the Desktop side, comparing what is actually in a client's folder
against what was recorded as delivered there. It could not be built because
nothing wrote the record. This is the record.

## What is held here

**One line per document actually written into `Clients\\`**, and nothing else
writes one. The gate is `copy_for_published_receipt()`'s own: whatever the
trigger, the `ok`-only rule and the one-copy rule refuse, the log refuses too,
because a line for a document that was never delivered is exactly the false
positive step 10au would then have to explain away.

**Append-only, never truncated, never deleted.** Rule 1 of `CLAUDE.md`, and the
same rule `receipt_events_{firm_id}.ndjson` has always had.

**The copy survives a log failure and the failure is said out loud.** Step 10af
in Desktop exists because a swallowed file failure is the wrong default, and
this is the same decision on this side: the document is already on disk by the
time the line is written, so refusing the copy would be undoing work that
succeeded, and saying nothing would leave a delivered document with no record
and nobody told.

**The field names are `receipt_events`' own spellings.** Amendment 456 offered
`posted_at` and asked for it to be confirmed against the convention rather than
taken. `_log_receipt()` in `app.py` and its near-copy in
`worker/extraction_pipeline.py` both spell the moment an event happened
`timestamp`, so that is the spelling here.
`TheFieldNamesFollowTheExistingConventionTest` reads that from `app.py`'s syntax
tree rather than repeating it, so the two cannot drift apart silently.
"""

import ast
import json
import logging
import sqlite3
import sys
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402
import source_guards  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    DOCUMENT,
    VERSION,
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    with_email_client,
)
from test_stage4_client_copy import (  # noqa: E402
    CLIENT,
    FOLDER,
    captured,
    everything_under,
    receipts,
    trigger,
)
from worker import client_copy  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

DOCUMENT_NAME = "2026-04-01_apcoa-parking_12.00.pdf"

#: Where the copy lands inside the client's own folder. The same three segments
#: `test_stage4_client_copy.py` asserts, kept here as the relative path the log
#: line is supposed to carry.
RELATIVE_DOCUMENT = (
    f"{config.CLIENT_INTELLIBOOKS_FOLDER_NAME}/"
    f"{config.CLIENT_RECEIPTS_FOLDER_NAME}/2025-26/{DOCUMENT_NAME}"
)


def delivery_dir() -> Path:
    return config.INTELLIBOOKS_ROOT / config.DELIVERY_FOLDER_NAME


def log_for(client_id=CLIENT) -> Path:
    return delivery_dir() / f"{client_id}{config.DELIVERY_LOG_SUFFIX}"


def lines(client_id=CLIENT):
    """Every entry in one client's delivery log, parsed. [] when there is none."""
    path = log_for(client_id)
    if not path.exists():
        return []
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def drive_ok(test_case, client_id=CLIENT, **kwargs):
    """One emailed receipt that extracts, validates `ok` and publishes."""
    with_email_client(test_case, client_id)
    Routes(RecordingExtractor(extraction_result())).email_attachment(**kwargs)


def copy_directly(repo, receipt_id="r-1", source=None, client_id=CLIENT,
                  filed_path=None, validation_status="ok", **kwargs):
    return client_copy.copy_for_published_receipt(
        repo,
        receipt_id=receipt_id,
        client_id=client_id,
        source_file=source,
        invoice_date="2026-04-01",
        supplier="Apcoa Parking",
        gross=12.0,
        validation_status=validation_status,
        filed_path=filed_path,
        **kwargs,
    )


# --------------------------------------------------------------------------
# Deliverable 1: a delivered document gets a line
# --------------------------------------------------------------------------

class ADeliveredDocumentIsLoggedTest(unittest.TestCase):
    def test_the_folder_is_not_there_until_something_is_delivered(self):
        """Created on demand, which is `config.py`'s rule for Review and
        Resolutions: the code that writes it makes it, and a test that asserts
        so has to start without it."""
        with TempEnvironment(), trigger("publish"):
            self.assertFalse(delivery_dir().exists())
            drive_ok(self)
            self.assertTrue(delivery_dir().is_dir())

    def test_it_sits_in_intellibooks_own_folder_and_not_in_ours(self):
        """Amendment 456 names `IntelliBooks\\Delivery\\{CODE}.log`.

        It is the other product's to read, so it belongs on that side of the
        tree in 18.2a, and not under `Intellibills\\` and not in `LOGS_DIR`,
        which is outside OneDrive and which IntelliBooks cannot see at all.
        """
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            written = log_for()
            self.assertTrue(written.is_relative_to(config.INTELLIBOOKS_ROOT))
            self.assertFalse(written.is_relative_to(config.INTELLIBILLS_ROOT))
            self.assertFalse(written.is_relative_to(config.LOGS_DIR))

    def test_the_file_is_named_for_the_client(self):
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            self.assertEqual([p.name for p in delivery_dir().iterdir()],
                             [f"{CLIENT}.log"])

    def test_one_copy_writes_exactly_one_line(self):
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            self.assertEqual(len(lines()), 1, lines())

    def test_the_line_carries_the_five_fields_and_no_others(self):
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            entry, = lines()
            self.assertEqual(
                sorted(entry),
                sorted(["client_id", "receipt_id", "document_path",
                        "timestamp", "pipeline_version"]))

    def test_the_ids_are_the_receipts_own(self):
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            receipt, = receipts()
            entry, = lines()
            self.assertEqual(entry["client_id"], CLIENT)
            self.assertEqual(entry["receipt_id"], receipt["receipt_id"])

    def test_the_document_path_is_relative_to_the_clients_own_folder(self):
        """Amendment 456: "the path written, relative to the client's own
        folder". So it starts inside `Clients\\{folder}\\` and names neither
        the practice root nor the firm's top folder, which is what makes it
        usable by a check walking one client's folder.
        """
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            entry, = lines()
            self.assertEqual(entry["document_path"], RELATIVE_DOCUMENT)
            # The control: it really is where the document is.
            self.assertTrue(
                (config.CLIENTS_ROOT / FOLDER / entry["document_path"]).is_file())

    def test_the_document_path_is_posix_separated(self):
        """One spelling, and it is the one that needs no escaping in JSON.

        A Windows separator is a backslash, which JSON escapes, so a reader
        that treats the value as a literal path gets a tab out of a folder
        beginning with a `t`. Desktop reads this file.
        """
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            entry, = lines()
            self.assertNotIn("\\", entry["document_path"])

    def test_the_timestamp_is_iso_8601_utc(self):
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            entry, = lines()
            parsed = datetime.fromisoformat(entry["timestamp"])
            self.assertEqual(parsed.utcoffset(), timezone.utc.utcoffset(None))

    def test_the_pipeline_version_is_the_runs_own(self):
        """`resolution_fixtures` patches `config.get_pipeline_version()` for the
        whole run, so this is the only thing that can have supplied the value.

        It is not passed in: `copy_for_published_receipt()` has no
        `pipeline_version` parameter and four of its five callers have no
        run-level version in scope, so the function is read where the line is
        written. `test_it_is_read_from_config_at_write_time` below drives that
        directly.
        """
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            entry, = lines()
            self.assertEqual(entry["pipeline_version"], VERSION)

    def test_it_is_read_from_config_at_write_time(self):
        with TempEnvironment(), trigger("publish"), \
                patch.object(config, "get_pipeline_version",
                             return_value="deadbee"):
            source = config.FILES_DIR / "doc.pdf"
            source.write_bytes(DOCUMENT)
            repo = Repository()
            try:
                self.assertIsNotNone(copy_directly(repo, source=source))
            finally:
                repo.close()
            entry, = lines()
            self.assertEqual(entry["pipeline_version"], "deadbee")

    def test_git_being_unavailable_does_not_stop_the_line(self):
        """`config.get_pipeline_version()` returns `"unknown"` rather than
        raising, so the field is always present and never invented."""
        with TempEnvironment(), trigger("publish"), \
                patch.object(config, "get_pipeline_version",
                             return_value="unknown"):
            source = config.FILES_DIR / "doc.pdf"
            source.write_bytes(DOCUMENT)
            repo = Repository()
            try:
                copy_directly(repo, source=source)
            finally:
                repo.close()
            entry, = lines()
            self.assertEqual(entry["pipeline_version"], "unknown")


# --------------------------------------------------------------------------
# Deliverable 2: append-only
# --------------------------------------------------------------------------

class TheLogIsAppendOnlyTest(unittest.TestCase):
    def test_a_second_delivery_adds_a_line_and_keeps_the_first(self):
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            first, = lines()

            other = config.FILES_DIR / "second.pdf"
            other.write_bytes(b"%PDF-1.4 a different document entirely")
            repo = Repository()
            try:
                self.assertIsNotNone(
                    copy_directly(repo, receipt_id="r-second", source=other))
            finally:
                repo.close()

            self.assertEqual(len(lines()), 2, lines())
            self.assertEqual(lines()[0], first)
            self.assertEqual(lines()[1]["receipt_id"], "r-second")

    def test_an_existing_file_is_never_truncated(self):
        """Driven by putting something there first, so the mode is asserted
        rather than read: a `w` would leave one line where there were two."""
        with TempEnvironment(), trigger("publish"):
            delivery_dir().mkdir(parents=True, exist_ok=True)
            log_for().write_text('{"already": "here"}\n', encoding="utf-8")
            drive_ok(self)
            entries = lines()
            self.assertEqual(len(entries), 2, entries)
            self.assertEqual(entries[0], {"already": "here"})

    def test_two_clients_get_two_files(self):
        with TempEnvironment(), trigger("publish"):
            config.CLIENTS_BY_ID = dict(config.CLIENTS_BY_ID)
            config.CLIENTS_BY_ID["CLIENT002"] = {
                "client_name": "Second Client",
                "client_folder_name": "Second Client",
                "client_id": "CLIENT002",
                "firm_id": "INTELLITAX",
                "trade": "UNSPECIFIED",
            }
            drive_ok(self)
            source = config.FILES_DIR / "other-client.pdf"
            source.write_bytes(b"%PDF-1.4 another client's document")
            repo = Repository()
            try:
                copy_directly(repo, receipt_id="r-2", source=source,
                              client_id="CLIENT002")
            finally:
                repo.close()
            self.assertEqual(sorted(p.name for p in delivery_dir().iterdir()),
                             ["CLIENT001.log", "CLIENT002.log"])
            self.assertEqual(len(lines("CLIENT001")), 1)
            self.assertEqual(len(lines("CLIENT002")), 1)


# --------------------------------------------------------------------------
# Deliverable 3: no copy, no line
# --------------------------------------------------------------------------

class NoCopyMeansNoLineTest(unittest.TestCase):
    """The gate is `copy_for_published_receipt()`'s own and is not duplicated.

    A line for a document that is not in the folder is the false positive step
    10au would have to explain away, so every refusal that stops the copy stops
    the line as well.
    """

    def test_the_never_trigger_writes_no_log_at_all(self):
        with TempEnvironment(), trigger("never"):
            drive_ok(self)
            self.assertEqual(everything_under(config.CLIENTS_ROOT), [])
            self.assertFalse(delivery_dir().exists())

    def test_the_post_trigger_writes_nothing_at_publish_time(self):
        with TempEnvironment(), trigger("post"):
            client_copy._reset_post_warning()
            drive_ok(self)
            self.assertEqual(everything_under(config.CLIENTS_ROOT), [])
            self.assertFalse(delivery_dir().exists())

    def test_a_status_the_copy_refuses_gets_no_line(self):
        """`needs_review` publishes since amendment 293 and is still not
        copied, so it must not be logged as delivered either."""
        with TempEnvironment(), trigger("publish"):
            with_email_client(self, CLIENT)
            Routes(RecordingExtractor(
                extraction_result(gross_amount=99.0))).email_attachment()
            receipt, = receipts()
            self.assertEqual(receipt["status"], "needs_review")
            self.assertEqual(everything_under(config.CLIENTS_ROOT), [])
            self.assertFalse(delivery_dir().exists())

    def test_a_receipt_that_already_has_a_copy_gets_no_second_line(self):
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            receipt, = receipts()
            repo = Repository()
            try:
                self.assertIsNone(copy_directly(
                    repo, receipt_id=receipt["receipt_id"],
                    source=Path(receipt["file_path"]),
                    filed_path=receipt["filed_path"]))
            finally:
                repo.close()
            self.assertEqual(len(lines()), 1, lines())

    def test_the_identical_bytes_skip_writes_no_second_line(self):
        """Sub-step 10f.25. Nothing was written, so nothing was delivered.

        The document already in the folder has a line of its own from the copy
        that put it there, and a second line would count one file twice.
        """
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            receipt, = receipts()
            before = everything_under(config.CLIENTS_ROOT)
            repo = Repository()
            try:
                # A different receipt, the same bytes, and no filed_path, so
                # only the byte comparison can refuse it.
                again = copy_directly(repo, receipt_id="r-identical",
                                      source=Path(receipt["file_path"]))
            finally:
                repo.close()
            self.assertIsNotNone(again, "the skip branch was not reached")
            self.assertEqual(everything_under(config.CLIENTS_ROOT), before)
            self.assertEqual(len(lines()), 1, lines())

    def test_a_client_with_no_folder_name_gets_no_line(self):
        with TempEnvironment(), trigger("publish"):
            config.CLIENTS_BY_ID = dict(config.CLIENTS_BY_ID)
            config.CLIENTS_BY_ID["CLIENT002"] = {
                "client_name": "No Folder", "client_id": "CLIENT002",
                "firm_id": "INTELLITAX", "trade": "UNSPECIFIED"}
            source = config.FILES_DIR / "doc.pdf"
            source.write_bytes(DOCUMENT)
            repo = Repository()
            try:
                with captured("worker.client_copy", logging.WARNING):
                    self.assertIsNone(copy_directly(
                        repo, source=source, client_id="CLIENT002"))
            finally:
                repo.close()
            self.assertFalse(delivery_dir().exists())

    def test_a_failing_copy_gets_no_line(self):
        with TempEnvironment(), trigger("publish"):
            source = config.FILES_DIR / "doc.pdf"
            source.write_bytes(DOCUMENT)
            repo = Repository()
            try:
                with patch.object(client_copy, "write_client_copy",
                                  side_effect=OSError("the folder is gone")):
                    with captured("worker.client_copy", logging.ERROR):
                        self.assertIsNone(copy_directly(repo, source=source))
            finally:
                repo.close()
            self.assertFalse(delivery_dir().exists())


# --------------------------------------------------------------------------
# Deliverable 4: a log failure must not undo the copy, and must be said
# --------------------------------------------------------------------------

class TheCopySurvivesALogFailureTest(unittest.TestCase):
    """Step 10af's decision on this side: a swallowed file failure is wrong.

    By the time the line is written the document is on disk, so refusing would
    undo work that succeeded. Saying nothing would leave a delivered document
    with no record and nobody told, which is exactly what step 10au would go
    looking for and report as a missing delivery.
    """

    def _break_the_log(self):
        return patch.object(client_copy, "_record_delivery",
                            side_effect=OSError("the delivery folder is gone"))

    def test_the_document_still_lands(self):
        with TempEnvironment(), trigger("publish"), self._break_the_log():
            with captured("worker.client_copy", logging.WARNING):
                drive_ok(self)
            written = everything_under(config.CLIENTS_ROOT)
            self.assertEqual(
                written,
                [f"{FOLDER}/{config.CLIENT_INTELLIBOOKS_FOLDER_NAME}/"
                 f"{config.CLIENT_RECEIPTS_FOLDER_NAME}/2025-26/"
                 f"{DOCUMENT_NAME}"])

    def test_the_copy_is_still_recorded_as_the_filed_path(self):
        with TempEnvironment(), trigger("publish"), self._break_the_log():
            with captured("worker.client_copy", logging.WARNING):
                drive_ok(self)
            receipt, = receipts()
            self.assertTrue(receipt["filed_path"])
            self.assertTrue(Path(receipt["filed_path"]).exists())

    def test_the_failure_is_a_warning_naming_the_receipt_and_the_reason(self):
        with TempEnvironment(), trigger("publish"), self._break_the_log():
            with captured("worker.client_copy", logging.WARNING) as log:
                drive_ok(self)
            receipt, = receipts()
            said = [m for m in log.messages(logging.WARNING)
                    if receipt["receipt_id"] in m]
            self.assertEqual(len(said), 1, log.messages(logging.WARNING))
            self.assertIn("the delivery folder is gone", said[0])

    def test_a_failing_database_write_still_leaves_the_line(self):
        """The reason the line is written before `mark_receipt_filed()`.

        Step 10ax's own failure: the database is locked, full or gone, the
        document is on disk and `filed_path` stays NULL. This log is the record
        of what is in the FOLDER, not of what the database knows, so a delivered
        document must still have its line. Written the other way round, the one
        case where the two records disagree is the one where the folder's record
        would be missing.

        The next poll's retry sweep offers the receipt again, finds the
        identical document already there and takes the skip, so no second line
        follows either.
        """
        with TempEnvironment(), trigger("publish"):
            source = config.FILES_DIR / "doc.pdf"
            source.write_bytes(DOCUMENT)
            repo = Repository()
            try:
                with patch.object(repo, "mark_receipt_filed",
                                  side_effect=sqlite3.OperationalError(
                                      "database is locked")):
                    with captured("worker.client_copy", logging.ERROR):
                        self.assertIsNone(copy_directly(repo, source=source))
            finally:
                repo.close()
            entry, = lines()
            self.assertEqual(entry["receipt_id"], "r-1")

    def test_nothing_is_raised_out_of_the_function(self):
        """`copy_for_published_receipt()`'s docstring says "this never raises",
        and step 10ax's own history is why that is asserted rather than read:
        it was aspirational for the database write until 2026-09-13."""
        with TempEnvironment(), trigger("publish"), self._break_the_log():
            source = config.FILES_DIR / "doc.pdf"
            source.write_bytes(DOCUMENT)
            repo = Repository()
            try:
                with captured("worker.client_copy", logging.WARNING):
                    self.assertIsNotNone(copy_directly(repo, source=source))
            finally:
                repo.close()


# --------------------------------------------------------------------------
# Deliverable 5: the field names follow the convention rather than inventing
# --------------------------------------------------------------------------

class TheFieldNamesFollowTheExistingConventionTest(unittest.TestCase):
    """Amendment 456 offered `posted_at` and asked for it to be confirmed.

    Read off `app.py`'s own `_log_receipt()` rather than repeated here, so the
    two cannot drift apart in silence. That function and its near-copy in
    `worker/extraction_pipeline.py` are the writers of
    `receipt_events_{firm_id}.ndjson`, which amendment 291 makes the convention
    for an event log on this project.
    """

    @staticmethod
    def _entry_keys(tree, function_name):
        """The literal keys of the first dict assigned to `entry` in it."""
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name != function_name:
                continue
            for statement in ast.walk(node):
                if (isinstance(statement, ast.Assign)
                        and isinstance(statement.value, ast.Dict)
                        and any(isinstance(t, ast.Name) and t.id == "entry"
                                for t in statement.targets)):
                    return [k.value for k in statement.value.keys
                            if isinstance(k, ast.Constant)]
        return None

    def test_the_two_receipt_event_writers_agree_on_the_moment(self):
        """The control: the convention this is aligned with is one convention."""
        app = self._entry_keys(source_guards.tree_of("app.py"), "_log_receipt")
        pipeline = self._entry_keys(
            source_guards.tree_of("worker", "extraction_pipeline.py"),
            "_log_receipt")
        self.assertIsNotNone(app)
        self.assertIsNotNone(pipeline)
        self.assertIn("timestamp", app)
        self.assertEqual(sorted(app), sorted(pipeline))

    def test_the_delivery_line_uses_that_spelling(self):
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            entry, = lines()
        app = self._entry_keys(source_guards.tree_of("app.py"), "_log_receipt")
        for shared in ("receipt_id", "timestamp"):
            with self.subTest(field=shared):
                self.assertIn(shared, app)
                self.assertIn(shared, entry)

    def test_posted_at_is_not_a_second_spelling_of_it(self):
        """Amendment 456's own starting point, corrected rather than taken.

        Asserted on the delivered line and on `worker/client_copy.py`'s string
        constants, because a name in a document that nothing writes is how the
        two products come to disagree about a field.
        """
        with TempEnvironment(), trigger("publish"):
            drive_ok(self)
            entry, = lines()
        self.assertNotIn("posted_at", entry)
        tree = source_guards.tree_of("worker", "client_copy.py")
        self.assertEqual(
            source_guards.string_constants_equal_to(tree, "posted_at"), [],
            "worker/client_copy.py names posted_at in code, and the log line "
            "spells the moment `timestamp`, as receipt_events does")


# --------------------------------------------------------------------------
# Deliverable 6: one writer, and the client id cannot escape the folder
# --------------------------------------------------------------------------

class OneWriterTest(unittest.TestCase):
    def test_only_client_copy_names_the_delivery_log_constants(self):
        """The set claim, enumerated from the syntax tree.

        `CLAUDE.md`: where a fact has one writer, assert it over the set rather
        than per site, because that is what catches the second one added later.
        """
        wanted = {"DELIVERY_FOLDER_NAME", "DELIVERY_LOG_SUFFIX"}
        found = {}
        for path in ([source_guards.REPO_ROOT / "app.py"]
                     + sorted((source_guards.REPO_ROOT / "worker").rglob("*.py"))
                     + sorted(p for p in source_guards.REPO_ROOT.glob("*.py")
                              if p.name != "app.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            names = {node.attr for node in ast.walk(tree)
                     if isinstance(node, ast.Attribute)}
            if names & wanted:
                found[path.relative_to(source_guards.REPO_ROOT).as_posix()] = \
                    sorted(names & wanted)
        self.assertEqual(sorted(found), ["worker/client_copy.py"],
                         f"the delivery log has more than one writer: {found}")


class TheClientIdCannotEscapeTheFolderTest(unittest.TestCase):
    """`clients.json` is written by the other product, so the id is input.

    The same reasoning `remove_client_copy()` already applies to `filed_path`:
    a stored value that does not compose to a path inside the folder this
    function owns is refused and reported, not used.
    """

    def _copy_with_client_id(self, bad_id):
        config.CLIENTS_BY_ID = dict(config.CLIENTS_BY_ID)
        config.CLIENTS_BY_ID[bad_id] = {
            "client_name": "Awkward", "client_folder_name": "Awkward",
            "client_id": bad_id, "firm_id": "INTELLITAX",
            "trade": "UNSPECIFIED"}
        source = config.FILES_DIR / "doc.pdf"
        source.write_bytes(DOCUMENT)
        repo = Repository()
        try:
            with captured("worker.client_copy", logging.WARNING) as log:
                written = copy_directly(repo, source=source, client_id=bad_id)
        finally:
            repo.close()
        return written, log

    def _delivery_files(self):
        directory = delivery_dir()
        if not directory.exists():
            return []
        return sorted(p.relative_to(directory).as_posix()
                      for p in directory.rglob("*") if p.is_file())

    def test_a_separator_in_the_id_is_refused_and_the_copy_still_lands(self):
        with TempEnvironment(), trigger("publish"):
            written, log = self._copy_with_client_id("..\\..\\escape")
            self.assertIsNotNone(written, "the copy itself must be unaffected")
            self.assertTrue(Path(written).is_file())
            self.assertEqual(self._delivery_files(), [])
            self.assertTrue(log.messages(logging.WARNING))

    def test_a_dotted_id_is_refused_too(self):
        with TempEnvironment(), trigger("publish"):
            written, log = self._copy_with_client_id("..")
            self.assertIsNotNone(written)
            self.assertEqual(self._delivery_files(), [])
            self.assertTrue(log.messages(logging.WARNING))


if __name__ == "__main__":
    unittest.main()

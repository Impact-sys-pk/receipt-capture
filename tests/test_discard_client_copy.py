r"""A discarded receipt gives up its client folder copy, and stops blocking a resend.

**Paul's four decisions of 2026-09-10.** An operator deletes a receipt from the
books in IntelliBooks Desktop. Until now that removed a row from one file and
nothing else: the document stayed in the client folder and the pipeline was
never told, so the database went on saying the receipt was `ok` and filed. The
two products disagreed about one receipt, which is what amendment 306 exists to
stop.

1. Deleting a receipt asks the operator whether to delete the copy in the
   client folder as well.
2. On discard, `filed_path` is cleared.
3. A discarded receipt no longer blocks a resend of the same document.
4. The delete writes a note back so the pipeline knows.

**This file is the pipeline half.** The Desktop half is the control, the second
question and the note itself, and it is the consultant session's.

## The one thing that removes work rather than adding it

**The pipeline already knows which file to delete.** `filed_path` is the path
`copy_for_published_receipt()` recorded when it wrote the copy, so Desktop does
not need to know it and must not have to guess it: the composed name carries a
`-2` on a collision and nothing on Desktop's side can tell one from the other.
So no path travels in the note, nothing travels in the published item, and no
publish ordering changes.

## Why the deletion lives in `worker\client_copy.py`

That module's own docstring says it is the only code that writes into
`Clients\`. A deletion is a write, so it belongs to the same owner, and the
containment guard that keeps it inside `config.CLIENTS_ROOT` is one decision in
one place. Before this, **production code deleted files in five places and not
one of them was under `Clients\`**: `_cleanup_old_backups()`, `acquire_lock()`
and `release_lock()` for the lock file, `_delete_review_pair()` for the Review
pair, and `write_item()` for its own partial. Enumerated from the syntax tree,
and `TheRemoverIsTheOnlyDeleterTest` below keeps it that way.
"""

import json
import logging
import sys
import types
import unittest
from pathlib import Path

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402

from resolution_fixtures import (  # noqa: E402
    DOCUMENT,
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    rows,
    with_email_client,
)
from worker import client_copy  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.resolution.service import (  # noqa: E402
    NOTE_DELETE_CLIENT_COPY_KEY,
    ResolutionNoteError,
    apply_resolution_note,
    discard_receipt,
    parse_resolution_note,
)

import app  # noqa: E402

#: Where the pipeline's own writer would have put this receipt's copy, relative
#: to the practice root. The convention is `write_client_copy()`'s:
#: `{invoice_date}_{supplier}_{gross}.{suffix}`, under the client's IntelliBooks
#: Receipts folder in the document date's tax year.
COPY_RELATIVE = (
    r"Clients\Test Client\IntelliBooks\Receipts\2025-26"
    r"\2026-04-01_apcoa-parking_96.00.pdf"
)


def discard_note(**overrides):
    """A `discarded` note as 12.2 shapes one: no `values`, no `filed_path`."""
    payload = {
        "schema": 1,
        "receipt_id": "r-1",
        "client_id": "CLIENT001",
        "action": "discarded",
        "resolved_by": "desktop",
        "resolved_at": "2026-09-10T09:00:00.000Z",
        "reason": "deleted from the books in IntelliBooks Desktop",
        "original_review_files": ["r-1.json"],
    }
    payload.update(overrides)
    return payload


class Capture(logging.Handler):
    """Every record the resolution service and the copy module emitted."""

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def __enter__(self):
        self.loggers = [logging.getLogger("worker.resolution.service"),
                        logging.getLogger("worker.client_copy")]
        for logger in self.loggers:
            logger.addHandler(self)
            logger.setLevel(logging.DEBUG)
        return self

    def __exit__(self, *exc):
        for logger in self.loggers:
            logger.removeHandler(self)
        return False

    def messages(self, level=None):
        return [r.getMessage() for r in self.records
                if level is None or r.levelno == level]


class DiscardTestCase(unittest.TestCase):
    """A published, filed, `ok` receipt: the state an operator deletes from."""

    def seed_published_and_filed(self, env, receipt_id="r-1",
                                 relative=COPY_RELATIVE, write_file=True,
                                 filed=True):
        """The live shape. `ok`, a `published` row, and a copy in `Clients\\`.

        **`published` matters and is separate from `filed` on purpose.** Sub-step
        10f.24 moved the semantic duplicate check on to a `publish_events` row,
        and the two are independent: on the `never` trigger a receipt publishes
        and is never filed. Both are set here because both are true of the
        receipt an operator deletes from the books.

        Returns the path of the client folder copy, whether or not it was
        written.
        """
        repo = Repository()
        try:
            env.seed(repo, receipt_id=receipt_id, status="ok",
                     supplier_name="Apcoa Parking", invoice_date="2026-04-01",
                     net_amount=80.0, vat_amount=16.0, gross_amount=96.0,
                     validation_status="ok", validation_notes=[])
            repo.save_publish_event(
                event_id=f"pub-{receipt_id}", receipt_id=receipt_id,
                destination="intellibooks", outcome="published",
                created_at="2026-09-10T08:00:00+00:00",
                item_path=f"/published/{receipt_id}.json")
            target = config.PRACTICE_ROOT / Path(relative.replace("\\", "/"))
            if write_file:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"the copy in the client folder")
            if filed:
                repo.mark_receipt_filed(receipt_id, str(target))
        finally:
            repo.close()
        return target

    def receipt(self, receipt_id="r-1"):
        repo = Repository()
        try:
            return repo.get_receipt(receipt_id)
        finally:
            repo.close()

    def events(self, receipt_id="r-1"):
        repo = Repository()
        try:
            return repo.list_resolution_events(receipt_id)
        finally:
            repo.close()

    def payload(self, receipt_id="r-1"):
        """The `corrections_json` blob off the discard event."""
        discard = [e for e in self.events(receipt_id) if e["action"] == "discard"]
        self.assertEqual(len(discard), 1, f"expected one discard row, got {discard}")
        return json.loads(discard[0]["corrections_json"] or "{}")

    def apply(self, **overrides):
        repo = Repository()
        try:
            return apply_resolution_note(
                repo, env_engine(repo), discard_note(**overrides))
        finally:
            repo.close()


def env_engine(repo):
    from worker.categorisation.engine import CategorisationEngine

    return CategorisationEngine(repo=repo, enable_ai_fallback=False)


class TheNoteFieldTest(unittest.TestCase):
    """Deliverable 1. One optional boolean, and the Desktop half matches it.

    **The field is `delete_client_copy`.** Absent or false means today's
    behaviour, which is that nothing in the client folder is touched. It is
    carried at the top level of the note rather than inside `values`, on the
    precedent of `remember_gl_for_supplier`: it is not something read off the
    receipt, it is what the operator asked the pipeline to do with one.

    **`schema` stays 1.** The field is optional on read, so neither half has to
    ship first, which is the same arrangement amendment 231 used for
    `category_code`.
    """

    def test_the_key_is_the_one_the_desktop_half_will_write(self):
        # Named from the constant rather than typed, so this test and the
        # parser cannot disagree about the spelling.
        self.assertEqual(NOTE_DELETE_CLIENT_COPY_KEY, "delete_client_copy")

    def test_true_parses_to_true(self):
        note = parse_resolution_note(
            discard_note(**{NOTE_DELETE_CLIENT_COPY_KEY: True}))
        self.assertIs(note.delete_client_copy, True)

    def test_false_parses_to_false(self):
        note = parse_resolution_note(
            discard_note(**{NOTE_DELETE_CLIENT_COPY_KEY: False}))
        self.assertIs(note.delete_client_copy, False)

    def test_absent_means_todays_behaviour(self):
        note = parse_resolution_note(discard_note())
        self.assertIs(note.delete_client_copy, False)

    def test_a_non_boolean_is_refused_rather_than_coerced(self):
        """The same strictness `remember_gl_for_supplier` gets, and for the same
        reason: this flag decides an irreversible deletion, and `"false"` is a
        true string in every language that would send one."""
        for value in ("true", "false", 1, 0, [], {}, "yes"):
            with self.subTest(value=value):
                with self.assertRaises(ResolutionNoteError) as caught:
                    parse_resolution_note(
                        discard_note(**{NOTE_DELETE_CLIENT_COPY_KEY: value}))
                self.assertIn(NOTE_DELETE_CLIENT_COPY_KEY, str(caught.exception))

    def test_null_is_refused_too(self):
        with self.assertRaises(ResolutionNoteError):
            parse_resolution_note(
                discard_note(**{NOTE_DELETE_CLIENT_COPY_KEY: None}))


class TheDeletionTest(DiscardTestCase):
    """Deliverable 1. The copy in the client folder goes, and only that file."""

    def test_the_copy_is_deleted_and_filed_path_is_cleared(self):
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)
            self.assertTrue(target.exists())

            outcome = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertEqual(outcome.outcome, "discarded")
            self.assertFalse(
                target.exists(),
                "the operator asked for the client folder copy to go and it is "
                "still there")
            receipt = self.receipt()
            self.assertEqual(receipt["status"], "discarded")
            self.assertIsNone(receipt["filed_path"])

    def test_without_the_flag_the_copy_stays(self):
        """The control. Absent means today's behaviour, and today's behaviour is
        that `discard_receipt()` touches no file at all."""
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)

            self.apply()

            self.assertTrue(
                target.exists(),
                "the copy was deleted without the operator asking, which is a "
                "deletion nobody authorised")
            self.assertIsNone(self.receipt()["filed_path"],
                              "filed_path is cleared on every discard")

    def test_false_is_the_same_as_absent(self):
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)
            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: False})
            self.assertTrue(target.exists())

    def test_it_deletes_exactly_one_file_and_leaves_the_folder(self):
        """Not a glob, not a directory, not the neighbours.

        Two other documents sit in the same tax year folder, which is the
        ordinary case for a client with more than one receipt in a year.
        """
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)
            neighbour = target.parent / "2026-04-02_someone-else_10.00.pdf"
            neighbour.write_bytes(b"another receipt entirely")
            collision = target.parent / "2026-04-01_apcoa-parking_96.00-2.pdf"
            collision.write_bytes(b"the second document under the same name")

            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertFalse(target.exists())
            self.assertTrue(neighbour.exists(), "a neighbour was deleted")
            self.assertTrue(
                collision.exists(),
                "the `-2` was deleted, so the deletion is matching on a "
                "composed name rather than on the path filed_path names")
            self.assertTrue(target.parent.is_dir(), "the folder itself went")

    def test_the_document_store_is_never_touched(self):
        """18.2a. `Intellibills\\Documents\\` is the archive of record, and it is
        the reason this deletion is safe at all."""
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)
            original = Path(self.receipt()["file_path"])
            self.assertTrue(original.exists())

            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertFalse(target.exists())
            self.assertTrue(
                original.exists(),
                "the file in the document store was deleted, and that is the "
                "archive of record per 18.2a")

    def test_no_extraction_row_is_touched(self):
        with TempEnvironment() as env:
            self.seed_published_and_filed(env)
            repo = Repository()
            try:
                before = rows(repo, "SELECT * FROM extractions")
            finally:
                repo.close()

            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            repo = Repository()
            try:
                self.assertEqual(rows(repo, "SELECT * FROM extractions"), before)
            finally:
                repo.close()

    def test_the_event_records_the_path_deleted_and_the_path_cleared(self):
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)

            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            payload = self.payload()
            self.assertEqual(payload.get("client_copy_deleted"), str(target))
            self.assertEqual(payload.get("filed_path_cleared"), str(target))

    def test_a_discard_that_deletes_nothing_records_only_the_clear(self):
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)

            self.apply()

            payload = self.payload()
            self.assertNotIn("client_copy_deleted", payload)
            self.assertEqual(payload.get("filed_path_cleared"), str(target))


class TheAwkwardCasesTest(DiscardTestCase):
    """The four states the file can be in, and none of them fails the note.

    **Why none of them fails it.** The status change is the point of the note. A
    file left behind is untidy and recoverable; a note stuck in
    `Resolutions\\failed\\` leaves the database saying `ok` while the books say
    the receipt is gone, which is the disagreement this work exists to remove.
    """

    def test_a_null_filed_path_is_a_normal_outcome(self):
        """Nothing to delete, and that is not an error.

        This is the live shape for a firm whose `client_copy_trigger` is `never`
        or `post`: the receipt publishes and no copy is ever written, so
        `filed_path` is NULL on a receipt an operator can still delete from the
        books.
        """
        with TempEnvironment() as env:
            self.seed_published_and_filed(env, write_file=False, filed=False)
            self.assertIsNone(self.receipt()["filed_path"])

            with Capture() as log:
                outcome = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertEqual(outcome.outcome, "discarded")
            self.assertEqual(self.receipt()["status"], "discarded")
            self.assertEqual(log.messages(logging.ERROR), [],
                             "a NULL filed_path was reported as a failure")
            self.assertNotIn("client_copy_deleted", self.payload())

    def test_a_file_that_is_already_gone_is_not_a_failure(self):
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env, write_file=False)
            self.assertEqual(self.receipt()["filed_path"], str(target))
            self.assertFalse(target.exists())

            with Capture() as log:
                outcome = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertEqual(outcome.outcome, "discarded")
            self.assertEqual(log.messages(logging.ERROR), [])
            self.assertIsNone(self.receipt()["filed_path"])
            self.assertNotIn("client_copy_deleted", self.payload(),
                             "nothing was deleted, so nothing is recorded as "
                             "deleted")

    def test_a_path_outside_the_client_root_is_refused_and_reported(self):
        """The guard that makes this safe, driven with a real stored path.

        A `filed_path` naming anything outside `config.CLIENTS_ROOT` is a
        corrupt value rather than a copy, so it is refused, the file is left
        exactly where it is, and the note still applies.
        """
        with TempEnvironment() as env:
            self.seed_published_and_filed(env, write_file=False, filed=False)
            elsewhere = env.path / "not-a-client-folder" / "something.pdf"
            elsewhere.parent.mkdir(parents=True, exist_ok=True)
            elsewhere.write_bytes(b"a file that is nobody's client copy")
            repo = Repository()
            try:
                repo.mark_receipt_filed("r-1", str(elsewhere))
            finally:
                repo.close()

            with Capture() as log:
                outcome = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertEqual(outcome.outcome, "discarded")
            self.assertTrue(elsewhere.exists(),
                            "a path outside the client folder root was deleted")
            self.assertTrue(log.messages(logging.ERROR),
                            "the refusal was not reported")
            self.assertIsNone(self.receipt()["filed_path"])
            self.assertNotIn("client_copy_deleted", self.payload())

    def test_a_filed_path_naming_the_document_store_is_refused(self):
        """The case the guard exists for, stated as its own test.

        `Intellibills\\Documents\\` is not under `Clients\\`, so the containment
        check refuses it. Without this the deletion would be one bad stored
        value away from destroying the archive of record.
        """
        with TempEnvironment() as env:
            self.seed_published_and_filed(env, write_file=False, filed=False)
            in_the_store = config.FILES_DIR / "CLIENT001" / "2026" / "04" / "r-1.pdf"
            in_the_store.parent.mkdir(parents=True, exist_ok=True)
            in_the_store.write_bytes(b"the archive of record")
            repo = Repository()
            try:
                repo.mark_receipt_filed("r-1", str(in_the_store))
            finally:
                repo.close()

            outcome = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertEqual(outcome.outcome, "discarded")
            self.assertTrue(in_the_store.exists())

    def test_a_deletion_that_fails_does_not_fail_the_note(self):
        """An unlink that raises, which on OneDrive is the ordinary case.

        `copy_for_published_receipt()` already swallows its own failures for the
        same reason: a folder in the firm's own tree being unavailable must not
        decide the fate of a receipt.
        """
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)

            def explode(self, *args, **kwargs):
                raise PermissionError(32, "the file is open in another program")

            with Capture() as log:
                original_unlink = Path.unlink
                Path.unlink = explode
                try:
                    outcome = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})
                finally:
                    Path.unlink = original_unlink

            self.assertEqual(outcome.outcome, "discarded")
            self.assertEqual(self.receipt()["status"], "discarded")
            self.assertIsNone(self.receipt()["filed_path"])
            self.assertTrue(target.exists(), "the stub did not stop the delete")
            self.assertTrue(
                any("PermissionError" in m for m in log.messages(logging.ERROR)),
                f"the failure was not logged as an ERROR: {log.messages()}")

    def test_a_directory_is_never_removed(self):
        """`filed_path` naming a folder rather than a file.

        The whole tax year folder is one bad stored value away, so the refusal
        is explicit rather than left to `unlink()` raising.
        """
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)
            folder = target.parent
            repo = Repository()
            try:
                repo.mark_receipt_filed("r-1", str(folder))
            finally:
                repo.close()

            outcome = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertEqual(outcome.outcome, "discarded")
            self.assertTrue(folder.is_dir(), "a directory was removed")
            self.assertTrue(target.exists())


class TheFlagOnlyMeansSomethingOnADiscardTest(DiscardTestCase):
    """A `filed` or settle note carrying the flag deletes nothing.

    The field's meaning is "the operator deleted this receipt and asked for its
    copy to go with it". On a note that files or settles a receipt it is a
    contradiction, so it is ignored and said out loud, which is the treatment
    12.2 already gives `values` and `filed_path` on a discard.
    """

    def test_a_settle_note_carrying_the_flag_deletes_nothing(self):
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)
            settle = {
                "schema": 1, "receipt_id": "r-1", "client_id": "CLIENT001",
                "action": "filed", "resolved_by": "desktop",
                "resolved_at": "2026-09-10T09:30:00.000Z",
                "values": {"supplier_name": "Apcoa Parking",
                           "invoice_date": "2026-04-01", "gross_amount": 96,
                           "currency": "GBP"},
                "original_review_files": ["r-1.json"],
                NOTE_DELETE_CLIENT_COPY_KEY: True,
            }

            with Capture() as log:
                repo = Repository()
                try:
                    apply_resolution_note(repo, env_engine(repo), settle)
                finally:
                    repo.close()

            self.assertTrue(target.exists(),
                            "a note that was not a discard deleted the copy")
            self.assertTrue(
                any(NOTE_DELETE_CLIENT_COPY_KEY in m
                    for m in log.messages(logging.WARNING)),
                f"the contradiction was not reported: {log.messages()}")


class ADiscardAppliesToAnOkReceiptTest(DiscardTestCase):
    """What the brief asked to be confirmed rather than assumed.

    Nothing imposes a status precondition on a discard: `discard_receipt()`
    reads the row, takes the lock and sets the status. **The Desktop half
    depends on it**, because the receipt an operator deletes from the books is
    `ok` by definition: it got there by being published.
    """

    def test_an_ok_receipt_is_discarded_by_a_note(self):
        with TempEnvironment() as env:
            self.seed_published_and_filed(env)
            self.assertEqual(self.receipt()["status"], "ok")

            outcome = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertEqual(outcome.outcome, "discarded")
            self.assertEqual(self.receipt()["status"], "discarded")

    def test_there_is_no_status_precondition_anywhere_on_the_path(self):
        """Read off the syntax tree rather than from four passing statuses.

        A behavioural test proves the statuses it drives. This asks whether
        `discard_receipt()` reads `status` at all, which is what a precondition
        would have to do.
        """
        import ast

        source = Path(app.__file__).resolve().parent / "worker" / "resolution" / "service.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        function, = [n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef)
                     and n.name == "discard_receipt"]
        reads = [ast.unparse(n) for n in ast.walk(function)
                 if isinstance(n, ast.Subscript)
                 and isinstance(n.slice, ast.Constant)
                 and n.slice.value == "status"]
        self.assertEqual(
            reads, [],
            "discard_receipt() reads the receipt's status, so it may have "
            f"gained a precondition the Desktop half does not expect: {reads}")

    def test_every_status_can_be_discarded(self):
        for status in ("ok", "needs_review", "failed", "possible_duplicate",
                       "retry_exhausted", "pending"):
            with self.subTest(status=status):
                with TempEnvironment() as env:
                    repo = Repository()
                    try:
                        env.seed(repo, receipt_id="r-s", status=status)
                        outcome = discard_receipt(
                            repo, "r-s", reason="a test", actor="cli",
                            source="cli")
                        self.assertEqual(outcome.outcome, "discarded")
                        self.assertEqual(
                            repo.get_receipt("r-s")["status"], "discarded")
                    finally:
                        repo.close()


class FiledPathIsClearedOnEveryDiscardTest(DiscardTestCase):
    """Deliverable 2, including the paths that are not the back-feed."""

    def test_the_cli_path_clears_it_too(self):
        """`discard_receipt()`'s other two callers are the CLI and the console,
        and neither passes the new parameter. The clear is not conditional on
        it."""
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)
            repo = Repository()
            try:
                outcome = discard_receipt(
                    repo, "r-1", reason="a confirmed duplicate",
                    actor="paul", source="cli")
            finally:
                repo.close()

            self.assertEqual(outcome.outcome, "discarded")
            self.assertIsNone(self.receipt()["filed_path"])
            self.assertTrue(target.exists(),
                            "the CLI deleted a file, and it asked for no such "
                            "thing")

    def test_the_receipt_is_no_longer_recorded_and_filed(self):
        """The second effect, and it is intended: this is what lets the
        identical file be sent again. `is_recorded_and_filed()` is unchanged;
        the data it reads is what moved."""
        with TempEnvironment() as env:
            self.seed_published_and_filed(env)
            repo = Repository()
            try:
                self.assertTrue(repo.is_recorded_and_filed("r-1"))
            finally:
                repo.close()

            self.apply()

            repo = Repository()
            try:
                self.assertFalse(repo.is_recorded_and_filed("r-1"))
            finally:
                repo.close()

    def test_the_discarded_receipt_is_not_offered_to_the_client_copy_sweep(self):
        """The risk clearing the column creates, and the reason it does not bite.

        `get_published_receipts_without_client_copy()` selects on
        `filed_path IS NULL`, and `_copy_missing_client_copies()` runs it every
        poll, so a cleared column looks exactly like a copy that failed. **It
        does not bite because that query also filters `status = 'ok'`**, and a
        discarded receipt is not `ok`. Asserted rather than reasoned about,
        because without it the next poll would write the copy back and the
        deletion would be undone in five minutes.
        """
        with TempEnvironment() as env:
            self.seed_published_and_filed(env)

            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            repo = Repository()
            try:
                offered = repo.get_published_receipts_without_client_copy()
                self.assertEqual(
                    [r["receipt_id"] for r in offered], [],
                    "the discarded receipt is queued for a client folder copy, "
                    "so the next poll writes back the file the operator just "
                    "deleted")
                self.assertEqual(
                    [r["receipt_id"] for r in repo.get_unpublished_ok_receipts()],
                    [], "and it is not queued for a second publish either")
            finally:
                repo.close()

    def test_the_copy_is_not_rewritten_by_a_real_poll(self):
        """The same thing through a real `process_once()`, on the live trigger.

        The query test above is the mechanism. This is the outcome, and it is
        the one that would have been noticed on Paul's machine.
        """
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)
            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})
            self.assertFalse(target.exists())

            client_copy._reset_post_warning()
            run_a_poll()

            self.assertFalse(
                target.exists(),
                "a poll wrote the client folder copy back after the operator "
                "deleted it")


def run_a_poll():
    """One `process_once()` with the mailbox and the extractor stubbed out."""
    Routes(RecordingExtractor(extraction_result()))._run()


class ADiscardedReceiptDoesNotBlockAResendTest(DiscardTestCase):
    """Deliverable 3. Paul's case: the operator changes their mind.

    Two arms, because a resend takes one of two shapes. **The identical file**
    is caught by the hash, which reads `filed_path` through
    `is_recorded_and_filed()`, so deliverable 2 answers it. **A re-photograph**
    has different bytes, so only the semantic check sees it, and that reads a
    `published` row which a discarded receipt keeps for ever.
    """

    def test_the_loose_lookup_does_not_return_a_discarded_receipt(self):
        with TempEnvironment() as env:
            self.seed_published_and_filed(env)
            repo = Repository()
            try:
                self.assertEqual(
                    repo.find_by_transaction_loose(
                        "Apcoa Parking", "2026-04-01", 96.0,
                        client_id="CLIENT001"),
                    "r-1",
                    "the control: before the discard it is found")
            finally:
                repo.close()

            self.apply()

            repo = Repository()
            try:
                self.assertIsNone(
                    repo.find_by_transaction_loose(
                        "Apcoa Parking", "2026-04-01", 96.0,
                        client_id="CLIENT001"),
                    "a discarded receipt was returned as the earlier half of a "
                    "semantic duplicate, so the resend goes to Review")
            finally:
                repo.close()

    def test_the_no_date_branch_asks_the_same_question(self):
        """The function has two queries and the no-date one is the wider.

        Sub-steps 10f.19 and 10f.24 each had to say this. It is the branch that
        gets left behind.
        """
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-1", status="ok",
                         supplier_name="Apcoa Parking", invoice_date=None,
                         gross_amount=96.0, validation_status="ok",
                         validation_notes=[])
                repo.save_publish_event(
                    event_id="pub-r-1", receipt_id="r-1",
                    destination="intellibooks", outcome="published",
                    created_at="2026-09-10T08:00:00+00:00")
                self.assertEqual(
                    repo.find_by_transaction_loose(
                        "Apcoa Parking", None, 96.0, client_id="CLIENT001"),
                    "r-1")
                discard_receipt(repo, "r-1", reason="deleted", actor="desktop",
                                source="desktop")
                self.assertIsNone(
                    repo.find_by_transaction_loose(
                        "Apcoa Parking", None, 96.0, client_id="CLIENT001"))
            finally:
                repo.close()

    def test_the_call_site_guard_asks_it_too(self):
        """The marker has to hold in the query and at the call site.

        `find_by_transaction_loose()`'s own docstring says why: it narrows and
        then takes `LIMIT 1`, so a query that let a discarded row through would
        hand it back while a live one existed.
        """
        with TempEnvironment() as env:
            self.seed_published_and_filed(env)
            repo = Repository()
            try:
                self.assertTrue(repo.is_published("r-1"))
                self.assertFalse(repo.is_discarded("r-1"))
            finally:
                repo.close()

            self.apply()

            repo = Repository()
            try:
                self.assertTrue(
                    repo.is_published("r-1"),
                    "is_published() changed meaning: a discarded receipt did "
                    "publish, and publish_events is append-only")
                self.assertTrue(repo.is_discarded("r-1"))
            finally:
                repo.close()

    def test_the_call_site_refuses_a_discarded_row_the_query_handed_back(self):
        """The call-site guard on its own, with the query made to hand one back.

        **Without this the guard is unreachable and untestable**, because the
        query it pairs with already refuses a discarded row, so a mutation
        removing the guard would survive the whole suite. That is the shape of
        redundancy `find_by_transaction_loose()`'s docstring defends: it
        narrows and then takes `LIMIT 1`, so a query that let a discarded row
        through would hand it back while a live one existed, and the guard is
        what catches that.

        So the lookup is stubbed to return the discarded receipt, which is the
        failure the pairing exists for, and the receipt must still reach `ok`.
        """
        from unittest.mock import patch

        from worker.extraction_pipeline import process_extraction_result

        with TempEnvironment() as env:
            self.seed_published_and_filed(env)
            self.apply()

            repo = Repository()
            try:
                self.assertTrue(repo.is_discarded("r-1"))
                arriving = env.path / "resend.pdf"
                arriving.write_bytes(b"a second photograph of the same receipt")
                repo.save_receipt(
                    receipt_id="r-2", message_id="msg-r-2", email_subject=None,
                    email_from="sender@example.com",
                    email_received_at="2026-09-10T09:00:00Z",
                    filename="resend.pdf", file_path=arriving,
                    file_hash="hash-r-2", firm_id="INTELLITAX",
                    client_id="CLIENT001", source="email")

                with patch.object(repo, "find_by_transaction_loose",
                                  lambda *a, **k: "r-1"):
                    status, _filed = process_extraction_result(
                        receipt_id="r-2",
                        extraction=extraction_result(
                            supplier_name="Apcoa Parking",
                            invoice_date="2026-04-01", net_amount=80.0,
                            vat_amount=16.0, gross_amount=96.0),
                        file_path=arriving, filename="resend.pdf",
                        firm_id="INTELLITAX", client_id="CLIENT001",
                        source="email", message_id="msg-r-2", repo=repo,
                        categorisation_engine=env_engine(repo), stats={},
                        run_id="test-run", pipeline_version="test-version")

                self.assertEqual(
                    status, "ok",
                    "the call site accepted a discarded receipt as the earlier "
                    "half of a semantic duplicate, so the only thing stopping "
                    "it is the query")
                self.assertIsNone(repo.get_receipt("r-2")["duplicate_of"])
            finally:
                repo.close()

    def test_a_rephotographed_resend_reaches_ok_through_the_real_pipeline(self):
        """The whole of deliverable 3, end to end.

        Different bytes, so the hash cannot answer and the semantic check is
        the one deciding. Before this the resend came back
        `possible_duplicate` against a receipt the operator deliberately
        deleted, and 10f.24 routes a `possible_duplicate` to Review and never
        publishes it.
        """
        with TempEnvironment() as env:
            self.seed_published_and_filed(env)
            self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            with_email_client(self)
            Routes(RecordingExtractor(extraction_result(
                supplier_name="Apcoa Parking", invoice_date="2026-04-01",
                net_amount=80.0, vat_amount=16.0, gross_amount=96.0,
            ))).email_attachment(message_id="the-resend",
                                 data=b"a second photograph of the same receipt")

            arrived = [r for r in self.all_receipts() if r["receipt_id"] != "r-1"]
            self.assertEqual(len(arrived), 1, f"the resend produced {arrived}")
            self.assertEqual(
                arrived[0]["status"], "ok",
                "the resend was flagged against a receipt the operator "
                "deleted, so it is in Review rather than in the books")
            self.assertIsNone(arrived[0]["duplicate_of"])

    def test_the_identical_file_can_be_sent_again(self):
        """The hash arm, driven rather than reasoned about.

        The same bytes, so `find_by_hash()` matches and
        `is_recorded_and_filed()` decides. `filed_path` is NULL after the
        discard, so the resend is processed.
        """
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-1", status="ok",
                         supplier_name="Apcoa Parking",
                         invoice_date="2026-04-01", gross_amount=96.0,
                         validation_status="ok", validation_notes=[])
                repo._conn.execute(
                    "UPDATE receipts SET file_hash = ? WHERE receipt_id = ?",
                    (app.compute_hash(DOCUMENT), "r-1"))
                repo._conn.commit()
                repo.mark_receipt_filed("r-1", str(
                    config.CLIENTS_ROOT / "Test Client" / "copy.pdf"))
                self.assertTrue(repo.is_recorded_and_filed("r-1"))
            finally:
                repo.close()

            with_email_client(self)
            Routes(RecordingExtractor(extraction_result())).email_attachment(
                message_id="before-the-discard", data=DOCUMENT)
            self.assertEqual(
                [r["receipt_id"] for r in self.all_receipts()], ["r-1"],
                "the control: while it is filed, the identical file is a "
                "duplicate and nothing is created")

            self.apply()

            with_email_client(self)
            Routes(RecordingExtractor(extraction_result())).email_attachment(
                message_id="after-the-discard", data=DOCUMENT)
            created = [r for r in self.all_receipts() if r["receipt_id"] != "r-1"]
            self.assertEqual(
                len(created), 1,
                "the identical file was still treated as a duplicate of a "
                "discarded receipt, so the operator's resend produced nothing")

    def test_another_published_receipt_still_protects_the_transaction(self):
        """How much protection a discard actually gives up, measured.

        Paul's decision gives up the discarded receipt's protection, and the
        brief asks to say plainly if that costs more than he has allowed for.
        **It costs less than it sounds**, and this is why: the ordinary shape is
        one `ok` published receipt plus a duplicate the operator discards, and
        the surviving `ok` one still answers. What is genuinely given up is only
        the case where the discarded receipt was the last published receipt for
        that transaction, which is the case Paul's resend depends on working.
        """
        with TempEnvironment() as env:
            repo = Repository()
            try:
                for receipt_id in ("r-kept", "r-discarded"):
                    env.seed(repo, receipt_id=receipt_id, status="ok",
                             supplier_name="Apcoa Parking",
                             invoice_date="2026-04-01", gross_amount=96.0,
                             validation_status="ok", validation_notes=[],
                             extraction_id=f"ext-{receipt_id}")
                    repo.save_publish_event(
                        event_id=f"pub-{receipt_id}", receipt_id=receipt_id,
                        destination="intellibooks", outcome="published",
                        created_at="2026-09-10T08:00:00+00:00")
                discard_receipt(repo, "r-discarded", reason="a duplicate",
                                actor="desktop", source="desktop")
                self.assertEqual(
                    repo.find_by_transaction_loose(
                        "Apcoa Parking", "2026-04-01", 96.0,
                        client_id="CLIENT001"),
                    "r-kept",
                    "the surviving published receipt no longer answers, so a "
                    "discard gives up more protection than Paul allowed for")
            finally:
                repo.close()

    def test_a_replayed_discard_note_deletes_nothing_a_second_time(self):
        """12.3 step 3's idempotency, with a deletion behind it now.

        The second application is skipped on the note's own `resolved_at`, so
        nothing is deleted twice. Worth asserting because the thing being
        skipped is no longer only a status change.
        """
        with TempEnvironment() as env:
            target = self.seed_published_and_filed(env)
            neighbour = target.parent / "2026-04-02_someone-else_10.00.pdf"
            neighbour.write_bytes(b"another receipt entirely")

            first = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})
            second = self.apply(**{NOTE_DELETE_CLIENT_COPY_KEY: True})

            self.assertEqual(first.outcome, "discarded")
            self.assertEqual(second.outcome, "discarded")
            self.assertIn("Already applied", second.message)
            self.assertTrue(neighbour.exists())
            self.assertEqual(
                len([e for e in self.events() if e["action"] == "discard"]), 1,
                "the replay wrote a second discard row")

    def all_receipts(self):
        repo = Repository()
        try:
            return rows(repo, "SELECT * FROM receipts ORDER BY created_at, receipt_id")
        finally:
            repo.close()


class TheRemoverIsTheOnlyDeleterTest(unittest.TestCase):
    """The set claims, from the syntax tree rather than from a grep.

    `worker\\client_copy.py`'s docstring says one gated entry point owns
    `Clients\\`, and `CLAUDE.md`'s rule is that where two or more call sites
    must all use one helper, you assert it on the source: a per-path test
    proves a path, and only a guard over the set proves the set is complete.
    """

    #: Anything that removes a file or a tree. `move`, `rename` and `replace`
    #: are included because each can destroy a target.
    DELETERS = ("unlink", "rmdir", "rmtree", "removedirs")

    def _deleting_calls(self, path: Path):
        import ast

        tree = ast.parse(path.read_text(encoding="utf-8"))
        found = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (func.attr if isinstance(func, ast.Attribute)
                    else func.id if isinstance(func, ast.Name) else None)
            if name in self.DELETERS:
                found.append((node.lineno, ast.unparse(node)))
        return found

    def _enclosing_function(self, path: Path, lineno: int):
        import ast

        tree = ast.parse(path.read_text(encoding="utf-8"))
        best = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.lineno <= lineno:
                if node.end_lineno and node.end_lineno >= lineno:
                    if best is None or node.lineno > best.lineno:
                        best = node
        return best.name if best else None

    def test_client_copy_deletes_in_exactly_one_function(self):
        source = Path(client_copy.__file__)
        calls = self._deleting_calls(source)
        self.assertTrue(calls, "worker/client_copy.py deletes nothing at all")
        where = {self._enclosing_function(source, lineno) for lineno, _ in calls}
        self.assertEqual(
            where, {"remove_client_copy"},
            "something else in worker/client_copy.py deletes from disk, and "
            f"that module owns `Clients\\`: {calls}")

    def test_the_service_reaches_the_deletion_only_through_the_remover(self):
        """`discard_receipt()` calls the helper and unlinks nothing itself."""
        source = Path(Path(client_copy.__file__).parent / "resolution" / "service.py")
        calls = self._deleting_calls(source)
        self.assertEqual(
            calls, [],
            "worker/resolution/service.py deletes from disk directly rather "
            f"than through worker/client_copy.py: {calls}")

    def _calls_within(self, source: Path, function_name: str):
        import ast

        tree = ast.parse(source.read_text(encoding="utf-8"))
        function, = [n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef) and n.name == function_name]
        return {n.func.attr if isinstance(n.func, ast.Attribute) else
                n.func.id if isinstance(n.func, ast.Name) else None
                for n in ast.walk(function) if isinstance(n, ast.Call)}

    def test_the_chain_from_discard_receipt_reaches_the_remover(self):
        """Two links, because the reporting is split from the deciding.

        `discard_receipt()` calls `_delete_the_client_copy()`, which does the
        logging because only it knows the receipt id, and that calls
        `remove_client_copy()`, which owns `Clients\\` and does the deciding.
        **The chain is asserted rather than the single call**, because the first
        version of this test named the call one function too high and passed
        only until the reporting moved.
        """
        source = Path(Path(client_copy.__file__).parent / "resolution" / "service.py")
        from_discard = self._calls_within(source, "discard_receipt")
        self.assertIn("_delete_the_client_copy", from_discard)
        self.assertIn("clear_receipt_filed_path", from_discard)
        self.assertIn(
            "remove_client_copy",
            self._calls_within(source, "_delete_the_client_copy"),
            "the deletion no longer goes through worker/client_copy.py, which "
            "is the module that owns `Clients\\` and holds the containment "
            "guard")


class TheRemoverOnItsOwnTest(unittest.TestCase):
    """`remove_client_copy()` against a temporary tree, one case each.

    Never against anything under the live practice root: `TempEnvironment`
    redirects `config.CLIENTS_ROOT`, and every path here is built from it.
    """

    def test_it_deletes_a_file_inside_the_client_root(self):
        with TempEnvironment():
            target = config.CLIENTS_ROOT / "Test Client" / "a.pdf"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"x")
            result = client_copy.remove_client_copy(target)
            self.assertEqual(result.outcome, client_copy.REMOVAL_DELETED)
            self.assertFalse(target.exists())

    def test_a_missing_file_is_already_gone(self):
        with TempEnvironment():
            target = config.CLIENTS_ROOT / "Test Client" / "gone.pdf"
            result = client_copy.remove_client_copy(target)
            self.assertEqual(result.outcome, client_copy.REMOVAL_ALREADY_GONE)

    def test_a_path_outside_the_root_is_refused(self):
        with TempEnvironment() as env:
            outside = env.path / "elsewhere.pdf"
            outside.write_bytes(b"x")
            result = client_copy.remove_client_copy(outside)
            self.assertEqual(result.outcome, client_copy.REMOVAL_REFUSED)
            self.assertTrue(outside.exists())

    def test_a_traversal_back_out_of_the_root_is_refused(self):
        """`..` is resolved before the containment test, not after.

        A stored path of `{clients root}\\..\\Documents\\x.pdf` is inside the
        root by string prefix and outside it in fact, which is the whole reason
        the check resolves first.
        """
        with TempEnvironment():
            outside = config.FILES_DIR / "x.pdf"
            outside.parent.mkdir(parents=True, exist_ok=True)
            outside.write_bytes(b"x")
            traversal = config.CLIENTS_ROOT / ".." / "Documents" / "x.pdf"
            result = client_copy.remove_client_copy(traversal)
            self.assertEqual(result.outcome, client_copy.REMOVAL_REFUSED)
            self.assertTrue(outside.exists())

    def test_a_directory_is_refused(self):
        with TempEnvironment():
            folder = config.CLIENTS_ROOT / "Test Client"
            folder.mkdir(parents=True, exist_ok=True)
            result = client_copy.remove_client_copy(folder)
            self.assertEqual(result.outcome, client_copy.REMOVAL_REFUSED)
            self.assertTrue(folder.is_dir())

    def test_the_client_root_itself_is_refused(self):
        with TempEnvironment():
            result = client_copy.remove_client_copy(config.CLIENTS_ROOT)
            self.assertEqual(result.outcome, client_copy.REMOVAL_REFUSED)
            self.assertTrue(config.CLIENTS_ROOT.is_dir())

    def test_a_relative_path_is_refused_rather_than_guessed_at(self):
        """The caller resolves. `resolve_practice_path()` in the resolution
        service is the one reader of 12.2's relative convention, and a second
        copy of it here would be the drift `worker\\client_copy.py` already
        warns about for `_unique_path()`."""
        with TempEnvironment():
            result = client_copy.remove_client_copy(
                Path("Clients/Test Client/a.pdf"))
            self.assertEqual(result.outcome, client_copy.REMOVAL_REFUSED)

    def test_an_unlink_that_raises_is_reported_rather_than_propagated(self):
        with TempEnvironment():
            target = config.CLIENTS_ROOT / "Test Client" / "a.pdf"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"x")

            def explode(self, *args, **kwargs):
                raise PermissionError(32, "in use")

            original = Path.unlink
            Path.unlink = explode
            try:
                result = client_copy.remove_client_copy(target)
            finally:
                Path.unlink = original
            self.assertEqual(result.outcome, client_copy.REMOVAL_FAILED)
            self.assertIn("PermissionError", result.detail)
            self.assertTrue(target.exists())


class FiledAtOutlivesFiledPathTest(unittest.TestCase):
    """The one column this change leaves stale, and the reason it is harmless.

    Paul's decision named `filed_path`, so `filed_at` is not cleared and a row
    with a filing time and no filing path is now reachable. **The one
    production reader of `filed_at` reads it only inside `if filed_path:`**,
    which is `resolve_receipt()`'s already-filed refusal, so the stale value
    cannot be reached. Asserted from the syntax tree, because the first draft
    of `clear_receipt_filed_path()`'s docstring said nothing read the column at
    all and that was wrong.
    """

    def test_the_only_reader_of_filed_at_is_guarded_by_filed_path(self):
        """`app.py`, everything under `worker\\` and the root scripts.

        **Not `rglob` from the repository root**, which is what the first draft
        did: it reached into `.venv\\` and died on a vendored module with a
        byte-order mark. `.history\\` would have been the worse version of the
        same mistake, because it holds a dated copy of every file edited and
        would have reported readers that no longer exist.
        """
        import ast

        root = Path(client_copy.__file__).resolve().parent.parent
        production = ([root / "app.py"]
                      + sorted((root / "worker").rglob("*.py"))
                      + sorted(p for p in root.glob("*.py") if p.name != "app.py"))
        readers = []
        for path in production:
            if "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Subscript)
                        and isinstance(node.slice, ast.Constant)
                        and node.slice.value == "filed_at"):
                    readers.append((path, node))
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "get"
                        and node.args
                        and isinstance(node.args[0], ast.Constant)
                        and node.args[0].value == "filed_at"):
                    readers.append((path, node))
        where = sorted(f"{p.name}:{n.lineno}" for p, n in readers)
        self.assertEqual(
            where, ["service.py:801"],
            "the set of readers of filed_at has changed, and a stale filed_at "
            f"with a NULL filed_path is reachable since 2026-09-10: {where}")

    def test_a_discarded_receipt_keeps_its_filed_at(self):
        """Stated rather than left as a surprise to whoever reads the row."""
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-1", status="ok")
                repo.mark_receipt_filed(
                    "r-1", str(config.CLIENTS_ROOT / "Test Client" / "a.pdf"))
                self.assertIsNotNone(repo.get_receipt("r-1")["filed_at"])
                from worker.resolution.service import discard_receipt as discard
                discard(repo, "r-1", reason="deleted", actor="cli", source="cli")
                receipt = repo.get_receipt("r-1")
                self.assertIsNone(receipt["filed_path"])
                self.assertIsNotNone(
                    receipt["filed_at"],
                    "filed_at was cleared, which is a behaviour change Paul's "
                    "decision of 2026-09-10 did not ask for")
            finally:
                repo.close()



if __name__ == "__main__":
    unittest.main()

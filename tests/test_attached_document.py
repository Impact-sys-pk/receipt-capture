r"""Sub-step 10f.38: a document attached from the Bank Transactions tab.

**Paul's requirement of 2026-09-10 and his decisions of 2026-09-11, amendments
320 and 321.** He is looking at a bank line, he has the document in his hand,
and he should not have to go to the Receipts tab and send it through the
pipeline first. IntelliBooks attaches it immediately and hands it to
Intellibills to archive and to file.

**Four conditions, all his.** Not extracted and not validated, because the
transaction already carries the date, the amount and the description and a
document that is not a receipt would otherwise fail into Review. Never
published back. Never in the receipts list. And the client folder copy happens
on the same trigger as 10f.37, at Post, through the `attached` note that
already exists.

## Why the marker is a `receipts.status` value

The pipeline's record of a document is a row in `receipts`: the client folder
copy path reads that row, and `filed_path` lives on it, so an attached document
needs one or the copy has to be reimplemented.

**A plain `ok` row breaks the third condition.**
`get_unpublished_ok_receipts()` offers every `ok` receipt with no `published`
row, so such a row would be published on the next poll, drained by Desktop and
would appear in the receipts list.

`config.BANK_ATTACHMENT_STATUS` is what stops that, and it is the only new
value in the system. It is not `ok` and not `failed`: it says what happened to
this document, which is that it was recorded and never offered to extraction.
**The publishing sweep's own `status = 'ok'` is what excludes it**, which is a
clause that already exists and is load-bearing rather than one added here that
could never fire. `TheSweepsTest` below enumerates the set from the syntax tree
and drives the two mutations that matter: make the writer say `ok`, or take the
`status = 'ok'` out of the sweep, and this receipt publishes.

**A separate table was refused**, amendment 320, because the client copy path
would then take its inputs from two shapes.
"""

import ast
import json
import logging
import subprocess
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402

from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    rows,
)
from worker import attached, client_copy  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.resolution.service import ATTACHED_ACTION  # noqa: E402

import app  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

DOCUMENT = b"%PDF-1.4 a supplier invoice for a bank line"

RECEIPT_ID = "9f1c8a52-0b3e-4f6a-8d21-6c4f0b5e7a13"
TRANSACTION_ID = "txn-4417"


@contextmanager
def trigger(value):
    """Set the firm's client copy trigger for one test, and put it back.

    A local copy of `tests/test_post_time_client_copy.py`'s, six lines, for the
    reason that file gives: importing a test module from another makes pytest
    collect it twice under two names.
    """
    saved = config.CLIENT_COPY_TRIGGER
    config.CLIENT_COPY_TRIGGER = value
    try:
        yield
    finally:
        config.CLIENT_COPY_TRIGGER = saved


class Capture(logging.Handler):
    def __init__(self, *names):
        super().__init__(level=logging.DEBUG)
        self.records = []
        self.names = names or ("worker.attached", "worker.client_copy",
                               "worker.resolution.service", "app")

    def emit(self, record):
        self.records.append(record)

    def __enter__(self):
        self.loggers = [logging.getLogger(name) for name in self.names]
        self._saved = [(logger, logger.level) for logger in self.loggers]
        for logger in self.loggers:
            logger.addHandler(self)
            logger.setLevel(logging.DEBUG)
        return self

    def __exit__(self, *exc):
        for logger, level in self._saved:
            logger.removeHandler(self)
            logger.setLevel(level)
        return False

    def messages(self, level=None):
        return [r.getMessage() for r in self.records
                if level is None or r.levelno == level]


def attach_message(**overrides):
    """The handoff message, exactly as the Desktop half is written to write it.

    Which client, which transaction, which file, and the three values the
    pipeline names the client folder copy from. **No path and no filename for
    the copy**: 10f.37's rule, because a name composed by Desktop cannot tell a
    collision's `-2` from its original.
    """
    payload = {
        "schema": 1,
        "action": attached.ATTACH_ACTION,
        "receipt_id": RECEIPT_ID,
        "client_id": "CLIENT001",
        "transaction_id": TRANSACTION_ID,
        "transaction_date": "2026-04-01",
        "transaction_description": "APCOA PARKING 8841 LONDON",
        "transaction_amount": -96.0,
        "filename": "bank-line-invoice.pdf",
        "attached_by": "desktop",
        "attached_at": "2026-09-11T10:00:00.000Z",
    }
    payload.update(overrides)
    return payload


def everything_under(root: Path):
    if not root.exists():
        return []
    return sorted(p.relative_to(root).as_posix()
                  for p in root.rglob("*") if p.is_file())


class AttachedTestCase(unittest.TestCase):
    """One attached document handed over, and a real poll to pick it up."""

    def hand_over(self, payload=None, data=DOCUMENT, name=None,
                  document=True):
        """Write the message and the document into the handoff folder.

        The message is what the pipeline scans and it names the document, so
        there is no sidecar convention to get the wrong way round. 10d.12 is
        why that matters: an inbox sidecar replaces the extension and a filed
        receipt's appends to it, and one was written for the other once.
        """
        payload = attach_message() if payload is None else payload
        config.ATTACHED_DIR.mkdir(parents=True, exist_ok=True)
        message_name = name or f"{payload.get('transaction_id', 'x')}_1757583600000.json"
        message_path = config.ATTACHED_DIR / message_name
        message_path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        if document and payload.get("filename"):
            (config.ATTACHED_DIR / payload["filename"]).write_bytes(data)
        return message_path

    def poll(self):
        """One real `app.process_once()`, mailbox and extractor stubbed.

        The brief asks for a real poll rather than a call to the handler,
        because what this change is worth is that a file appears in two folders
        and does not appear in a third.
        """
        client_copy._reset_post_warning()
        Routes(RecordingExtractor(extraction_result()))._run()

    def receipt(self, receipt_id=RECEIPT_ID):
        repo = Repository()
        try:
            return repo.get_receipt(receipt_id)
        finally:
            repo.close()

    def table(self, sql, params=()):
        repo = Repository()
        try:
            return rows(repo, sql, params)
        finally:
            repo.close()

    def names_in(self, subfolder=None):
        base = (config.ATTACHED_DIR if subfolder is None
                else config.ATTACHED_DIR / subfolder)
        if not base.is_dir():
            return []
        return sorted(p.name for p in base.iterdir() if p.is_file())

    def write_attached_note(self, receipt_id=RECEIPT_ID,
                            resolved_at="2026-09-11T11:00:00.000Z"):
        """The 10f.37 Post-time note, which is what makes the copy due."""
        config.RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": 1,
            "receipt_id": receipt_id,
            "client_id": "CLIENT001",
            "action": ATTACHED_ACTION,
            "resolved_by": "desktop",
            "resolved_at": resolved_at,
        }
        path = config.RESOLUTIONS_DIR / f"{receipt_id}_1757587200000.json"
        path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        return path


# ---------------------------------------------------------------------------
# The contract the Desktop half is written from
# ---------------------------------------------------------------------------


class TheHandoffContractTest(unittest.TestCase):
    """The folder, the action word and every field the message must carry."""

    def test_the_handoff_folder_is_intellibills_attached(self):
        """Desktop's own tree is not an option: 18.2 gives
        `Intellibills\\Documents\\` one writer, and this folder is the way in.

        **Not `Attachments\\`**, which 18.2a plans under `IntelliBooks\\` for
        the evidence attached to a transaction. Two folders one word apart in
        two product trees is the trap `CLAUDE.md` names about `postTxn()` and
        `postReceiptToCashbook()`.
        """
        self.assertEqual(config.ATTACHED_DIR,
                         config.INTELLIBILLS_ROOT / "Attached")

    def test_the_action_word_says_what_the_message_is(self):
        self.assertEqual(attached.ATTACH_ACTION, "attach_document")
        self.assertEqual(attached.ATTACHED_SCHEMA, 1)

    def test_it_parses(self):
        message = attached.parse_attached_message(attach_message())
        self.assertEqual(message.receipt_id, RECEIPT_ID)
        self.assertEqual(message.client_id, "CLIENT001")
        self.assertEqual(message.transaction_id, TRANSACTION_ID)
        self.assertEqual(message.transaction_date, "2026-04-01")
        self.assertEqual(message.transaction_description,
                         "APCOA PARKING 8841 LONDON")
        self.assertEqual(message.filename, "bank-line-invoice.pdf")
        self.assertEqual(message.attached_at, "2026-09-11T10:00:00.000Z")

    def test_the_amount_is_the_absolute_value(self):
        """A bank payment is negative in the books and a receipt's gross is
        not, and the filename convention is the receipt one. The same
        `Math.abs()` Desktop applies to a note's amounts, per 12.2.
        """
        self.assertEqual(
            attached.parse_attached_message(attach_message()).amount, 96.0)
        self.assertEqual(
            attached.parse_attached_message(
                attach_message(transaction_amount=96)).amount, 96.0)

    def test_every_required_field_is_required(self):
        for field in ("receipt_id", "client_id", "transaction_id",
                      "transaction_date", "transaction_description",
                      "transaction_amount", "filename", "attached_at"):
            with self.subTest(missing=field):
                payload = attach_message()
                del payload[field]
                with self.assertRaises(attached.AttachedMessageError) as caught:
                    attached.parse_attached_message(payload)
                self.assertIn(field, str(caught.exception))

    def test_a_resolution_note_dropped_in_here_is_refused(self):
        """The control. This folder is a different channel from
        `Resolutions\\`, and a note that lands in the wrong one must fail
        loudly rather than be half-read.
        """
        note = {"schema": 1, "receipt_id": RECEIPT_ID, "action": "filed",
                "resolved_by": "desktop", "resolved_at": "2026-09-11T10:00:00Z"}
        with self.assertRaises(attached.AttachedMessageError) as caught:
            attached.parse_attached_message(note)
        self.assertIn(attached.ATTACH_ACTION, str(caught.exception))

    def test_an_unknown_schema_is_refused(self):
        with self.assertRaises(attached.AttachedMessageError):
            attached.parse_attached_message(attach_message(schema=2))

    def test_a_filename_that_is_a_path_is_refused(self):
        """10f.37's rule: a path composed by Desktop is not trusted for
        anything the pipeline composes itself. The document sits beside the
        message and the message names it, so a separator in that name is a
        Desktop that has misread the contract, or worse.
        """
        for bad in (r"sub\x.pdf", "sub/x.pdf", r"..\..\x.pdf",
                    r"C:\Windows\x.pdf", ".", ".."):
            with self.subTest(filename=bad):
                with self.assertRaises(attached.AttachedMessageError) as caught:
                    attached.parse_attached_message(
                        attach_message(filename=bad))
                self.assertIn("filename", str(caught.exception))

    def test_an_unsupported_file_type_is_refused(self):
        with self.assertRaises(attached.AttachedMessageError) as caught:
            attached.parse_attached_message(attach_message(filename="notes.txt"))
        self.assertIn("notes.txt", str(caught.exception))

    def test_a_date_that_is_not_a_plain_iso_day_is_refused(self):
        """It names the tax year folder and the file, so a loose date here is a
        document filed into the wrong year. `2026-4-1` is what `strptime`
        accepts and this does not, the same rule `_ISO_DATE_RE` applies to a
        note's `invoice_date`.
        """
        for bad in ("2026-4-1", "01/04/2026", "2026-04-01T00:00:00Z", ""):
            with self.subTest(date=bad):
                with self.assertRaises(attached.AttachedMessageError):
                    attached.parse_attached_message(
                        attach_message(transaction_date=bad))

    def test_a_receipt_id_that_is_not_a_uuid_is_refused(self):
        """**Desktop mints the `receipt_id` and that is the whole reason the
        handoff needs no reply channel.** Desktop has to send the 10f.37
        `attached` note at Post, which is keyed on `receipt_id`, and 18.3 is
        one way: the pipeline cannot tell Desktop an id it invented. So Desktop
        invents it, and the pipeline holds it to being a uuid rather than
        anything a keystroke could produce.
        """
        for bad in ("", "r-1", "not-a-uuid", RECEIPT_ID + "x"):
            with self.subTest(receipt_id=bad):
                with self.assertRaises(attached.AttachedMessageError):
                    attached.parse_attached_message(
                        attach_message(receipt_id=bad))


# ---------------------------------------------------------------------------
# Arrival
# ---------------------------------------------------------------------------


class OnArrivalTest(AttachedTestCase):
    """What one poll does with a handed-over document."""

    def test_the_document_reaches_the_archive_of_record(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()

            self.poll()

            landed = everything_under(config.FILES_DIR)
            self.assertEqual(len(landed), 1, f"the archive holds {landed}")
            self.assertTrue(
                landed[0].startswith("CLIENT001/"),
                f"the store is keyed on client_id, 10d.53: {landed[0]}")
            self.assertTrue(
                landed[0].endswith(f"{RECEIPT_ID}_bank-line-invoice.pdf"),
                f"the store names a file {{receipt_id}}_{{filename}}: {landed[0]}")
            self.assertEqual(
                (config.FILES_DIR / landed[0]).read_bytes(), DOCUMENT)

    def test_the_row_is_written_and_it_carries_the_marker(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()

            self.poll()

            row = self.receipt()
            self.assertIsNotNone(row, "no receipts row was written")
            self.assertEqual(row["status"], config.BANK_ATTACHMENT_STATUS)
            self.assertEqual(row["client_id"], "CLIENT001")
            self.assertEqual(row["firm_id"], "INTELLITAX")
            # 10d.40's four words and no fifth. IntelliBooks Desktop is the
            # route in, which is what `desktop` already means.
            self.assertEqual(row["source"], "desktop")
            self.assertEqual(row["filename"], "bank-line-invoice.pdf")
            self.assertIn(TRANSACTION_ID, row["message_id"])
            self.assertIsNone(row["filed_path"])
            self.assertIsNone(row["filed_at"])
            self.assertIsNone(row["email_from"])
            self.assertIsNone(row["email_subject"])
            self.assertTrue(Path(row["file_path"]).exists())

    def test_nothing_is_extracted_categorised_or_published(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()

            self.poll()

            for table in ("extractions", "categorisations", "publish_events"):
                with self.subTest(table=table):
                    self.assertEqual(
                        self.table(f"SELECT * FROM {table} WHERE receipt_id = ?",
                                   (RECEIPT_ID,)),
                        [], f"a {table} row was written for an attached document")

    def test_nothing_reaches_the_folder_intellibooks_drains(self):
        """Paul's second condition, and it is what keeps it out of the receipts
        list: that list is fed by the drain, per 18.3.
        """
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()

            self.poll()
            self.poll()

            self.assertEqual(
                everything_under(config.INTELLIBOOKS_PUBLISH_DIR), [],
                "an attached document was published to IntelliBooks")

    def test_no_client_folder_copy_is_written_on_arrival(self):
        """The copy is due at Post, on the same trigger as 10f.37, and arrival
        is not that moment.
        """
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()

            self.poll()

            self.assertEqual(everything_under(config.CLIENTS_ROOT), [])
            self.assertIsNone(self.receipt()["filed_path"])

    def test_the_message_and_the_document_move_to_processed(self):
        """Both, and neither is deleted: `Resolutions\\`'s rule, because a
        handover that cannot be re-read is a handover nobody can audit.

        **The document has to move too.** Left in the folder it would be
        archived again on the next poll under a second receipt id, since the
        message is gone and nothing would connect the two.
        """
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            message = self.hand_over()

            self.poll()

            self.assertEqual(self.names_in(), [], "the handoff folder is drained")
            self.assertEqual(sorted(self.names_in("processed")),
                             ["bank-line-invoice.pdf", message.name])
            self.assertEqual(self.names_in("failed"), [])

    def test_the_transaction_is_recorded_so_the_copy_can_be_named_later(self):
        """The three values arrive at Attach and the copy is composed at Post,
        so they have to be kept. `resolution_events.corrections_json` is where
        this project already puts what 5.1 has no column for.
        """
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()

            self.poll()

            values = attached.transaction_values(Repository(), RECEIPT_ID)
            self.assertEqual(values["transaction_date"], "2026-04-01")
            self.assertEqual(values["transaction_description"],
                             "APCOA PARKING 8841 LONDON")
            self.assertEqual(values["amount"], 96.0)
            self.assertEqual(values["transaction_id"], TRANSACTION_ID)

    def test_a_second_delivery_of_the_same_message_changes_nothing(self):
        """Idempotency, on `receipt_id`. Desktop mints it, so the same attach
        re-delivered names the same row and must not archive a second copy.
        """
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()
            self.poll()
            first = everything_under(config.FILES_DIR)

            self.hand_over(name=f"{TRANSACTION_ID}_1757583600001.json")
            self.poll()

            self.assertEqual(everything_under(config.FILES_DIR), first)
            self.assertEqual(
                len(self.table("SELECT * FROM receipts WHERE receipt_id = ?",
                               (RECEIPT_ID,))), 1)

    def test_an_unknown_client_fails_the_message_rather_than_guessing(self):
        """A bank line lives in a client's books, so Desktop knows the client.
        An id the registry does not hold is a registry disagreement, which is
        the case `failed\\` exists for. **Not `UNKNOWN`**: this document cannot
        be filed for a client nobody can name, and 10d.18 already refuses that
        at the copy.
        """
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            message = self.hand_over(attach_message(client_id="CLIENT999"))

            self.poll()

            self.assertEqual(self.receipt(), None)
            self.assertIn(message.name, self.names_in("failed"))
            self.assertTrue(
                (config.ATTACHED_DIR / "failed" /
                 (message.name + ".error.txt")).exists(),
                "the reason was not written beside the failed message")

    def test_a_missing_document_fails_the_message(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            message = self.hand_over(document=False)

            self.poll()

            self.assertEqual(self.receipt(), None)
            self.assertIn(message.name, self.names_in("failed"))

    def test_an_unreadable_message_fails_and_is_never_deleted(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            config.ATTACHED_DIR.mkdir(parents=True, exist_ok=True)
            broken = config.ATTACHED_DIR / "txn-9_1757583600000.json"
            broken.write_text("{ not json", encoding="utf-8")

            self.poll()

            self.assertIn(broken.name, self.names_in("failed"))


# ---------------------------------------------------------------------------
# The sweeps
# ---------------------------------------------------------------------------


class TheSweepsTest(AttachedTestCase):
    """Paul's decision: every sweep that offers receipts for publishing
    excludes this row. Verified over the set, not over its members.
    """

    def test_the_publishing_sweep_never_offers_it(self):
        """**The sweep's own `status = 'ok'` is what excludes it**, and this
        test had to be rewritten to measure that rather than something else.

        As first written it seeded nothing but the attached document, and it
        passed with the status filter taken out of the query, because the
        second clause is `created_at >= (SELECT MIN(created_at) FROM
        publish_events)`: with that table empty the comparison is NULL and no
        row satisfies it, so the cutover was doing the excluding and the filter
        under test was never reached. Amendment 97's rule, arriving in a
        mutation run rather than in a reading: **a check that cannot fail is
        not a check.** Recorded in
        `2026-09-11_REPORT_claude_code_attached_document.md`.

        So one ordinary published receipt is seeded first, older than the
        attached document, which puts a real row in `publish_events` and makes
        the cutover pass for this receipt. The status filter is then the only
        thing between it and the sweep.
        """
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            repo = Repository()
            try:
                env.seed(repo, receipt_id="already-published", status="ok",
                         supplier_name="Someone Else", invoice_date="2026-04-01",
                         gross_amount=12.0, validation_status="ok",
                         validation_notes=[])
                repo.save_publish_event(
                    event_id="pub-1", receipt_id="already-published",
                    destination=config.INTELLIBOOKS_DESTINATION,
                    outcome="published", created_at="2020-01-01T00:00:00+00:00",
                    item_path="/published/already-published.json")
            finally:
                repo.close()

            self.hand_over()
            self.poll()

            repo = Repository()
            try:
                # The control: the cutover is satisfied, so this query is
                # answering rather than returning nothing because it cannot.
                self.assertIsNotNone(
                    rows(repo, "SELECT MIN(created_at) AS m FROM publish_events")
                    [0]["m"], "the cutover is not armed and this test would "
                              "pass with the status filter removed")
                self.assertEqual(
                    [r["receipt_id"] for r in repo.get_unpublished_ok_receipts()],
                    [], "the publishing sweep offered the attached document")
                # **Not empty**, and that is right: the seeded receipt is `ok`,
                # published and has no copy, which is exactly what this query
                # is for. What matters is that the attached document is not in
                # it, because it has no `published` row.
                waiting = [r["receipt_id"] for r in
                           repo.get_published_receipts_without_client_copy()]
                self.assertEqual(waiting, ["already-published"])
                self.assertNotIn(RECEIPT_ID, waiting)
                self.assertFalse(repo.is_published(RECEIPT_ID))
            finally:
                repo.close()

            self.poll()
            self.assertEqual(
                [name for name in
                 everything_under(config.INTELLIBOOKS_PUBLISH_DIR)
                 if RECEIPT_ID in name], [])
            self.assertEqual(
                self.table("SELECT * FROM publish_events WHERE receipt_id = ?",
                           (RECEIPT_ID,)), [])

    def test_the_retry_sweep_never_offers_it(self):
        """Two reasons and both are read rather than assumed: the status is not
        one of the two it asks for, and it joins `extractions`, of which this
        receipt has none.
        """
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()
            self.poll()

            repo = Repository()
            try:
                found = repo.find_failed_by_version("other-version", "2099-01-01")
            finally:
                repo.close()
            self.assertEqual([r["receipt_id"] for r in found], [])

    def test_the_review_count_does_not_include_it(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()
            self.poll()

            repo = Repository()
            try:
                self.assertEqual(app._count_review_items(repo), 0)
            finally:
                repo.close()

    def test_the_semantic_duplicate_check_cannot_see_it(self):
        """`find_by_transaction_loose()` joins `extractions` and this receipt
        has none, so it can never be returned by it. A consequence rather than
        a guard, and stated so a reader does not go looking for one.
        """
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()
            self.poll()

            repo = Repository()
            try:
                self.assertIsNone(repo.find_by_transaction_loose(
                    "APCOA PARKING 8841 LONDON", "2026-04-01", 96.0,
                    "CLIENT001"))
            finally:
                repo.close()

    def test_the_file_hash_check_does_find_it_and_the_paired_guard_decides(self):
        """**This is the one I got wrong, and it is recorded rather than
        hidden.** `find_by_hash()` was read as joining `processed_attachments`,
        of which an attached document has no row, so it looked unable to see
        one. **It has a SECOND query** straight off `receipts.file_hash` with
        no join and no status filter, and that one finds it.

        `CLAUDE.md`'s rule about never reasoning from a filter's output applied
        to reading rather than to a shell: the first query was read and the
        function was described.

        **What actually decides is the guard all three callers pair it with.**
        `existing and repo.is_recorded_and_filed(existing)` is the duplicate
        test, and that asks `filed_path IS NOT NULL`, which an attached
        document has only once its copy has been written at Post. So before
        Post it blocks nothing, and after Post the same bytes arriving by email
        for the same client are a duplicate of it. **Reported as flag 3**: it
        is defensible and it was not asked for either way.
        """
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()
            self.poll()
            file_hash = self.receipt()["file_hash"]

            repo = Repository()
            try:
                self.assertEqual(repo.find_by_hash(file_hash, "CLIENT001"),
                                 RECEIPT_ID)
                self.assertFalse(
                    repo.is_recorded_and_filed(RECEIPT_ID),
                    "before Post it has no filed_path, so it blocks nothing")
                # Another client's identical bytes are not this client's
                # duplicate. 10f.18, and it holds here too.
                self.assertIsNone(repo.find_by_hash(file_hash, "CLIENT002"))
            finally:
                repo.close()

            self.write_attached_note()
            self.poll()

            repo = Repository()
            try:
                self.assertTrue(
                    repo.is_recorded_and_filed(RECEIPT_ID),
                    "after Post it has a filed_path, which is flag 3")
            finally:
                repo.close()

    def test_every_production_selector_of_receipts_is_accounted_for(self):
        """The set claim, enumerated from the syntax tree and printed whole.

        `CLAUDE.md`: a claim about a set is not verified by verifying its
        members, and a grep for `FROM receipts` returns it from the prose too,
        which on this project is guaranteed because superseded wording is kept
        beside every correction. So the SQL is read out of string constants on
        the tree, docstrings excluded.

        **What this holds is the list, not the behaviour.** A function added
        here later fails this test and has to be considered against an attached
        document, which is the only way "every sweep" can stay true.
        """
        expected = {
            # Asked by receipt_id, so they answer about whatever row is named
            # and there is nothing to exclude.
            "get_receipt", "get_filed_path", "is_recorded_and_filed",
            "is_discarded",
            # Filter status = 'ok', which the marker is not.
            "get_unpublished_ok_receipts",
            "get_published_receipts_without_client_copy",
            # Filters status IN ('failed', 'needs_review') and joins
            # extractions, of which an attached document has none.
            "find_failed_by_version",
            # Joins extractions, same reason.
            "find_by_transaction_loose",
            # **Finds it.** Its second query is straight off
            # `receipts.file_hash` with no join. What decides is the
            # `is_recorded_and_filed()` its three callers pair it with, which
            # asks `filed_path IS NOT NULL`. Flag 3, and the test above.
            "find_by_hash",
            # Counts the statuses in app.REVIEW_STATUSES, which the marker is
            # not one of.
            "count_receipts_by_status",
            # Counts every receipt created today, marker included. Reported in
            # `2026-09-11_REPORT_claude_code_attached_document.md` as flag 1:
            # an attached document is a document processed today, and changing
            # what that number means was not asked for.
            "count_processed_today",
            # The back-feed's filename fallback for a note with no receipt_id.
            # Reported as flag 2.
            "find_receipts_by_filename",
            # Three root diagnostic scripts, not sweeps: nothing in the poll
            # calls them and a person runs them to look at the database.
            # `probe_layer5.py`, `check_test41.py` and `probe_extract.py`. Here
            # because this test holds the whole list rather than the part of it
            # that matters, so a new selector anywhere fails it and gets
            # considered.
            "latest_extractions", "main", "recent_receipt_paths",
        }
        found = set()
        for path in tracked_python_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for text in sql_constants(node):
                    if "from receipts" in text.lower():
                        found.add(node.name)
        self.assertEqual(
            found, expected,
            "the set of production functions that SELECT from `receipts` has "
            f"moved.\nfound:    {sorted(found)}\nexpected: {sorted(expected)}\n"
            "Each one has to be considered against a row carrying "
            f"{config.BANK_ATTACHMENT_STATUS!r} before this list is updated.")


class TheModuleDoesNotReachForTheReceiptPathTest(unittest.TestCase):
    """Held on the source, because the tests above prove the absences for one
    document and this proves them for the function.

    `CLAUDE.md`: where a property must hold over a set of call sites, assert it
    on the source. The behavioural tests say "this document produced no
    extraction row"; a guard here says the module cannot produce one for any
    input, which is what stops a later edit quietly adding extraction to the
    handoff because it looked incomplete without it.

    **Parsed from the syntax tree rather than string-matched**, which is this
    project's third rule about guards: two earlier ones failed on their own
    docstrings, quoting the sentence they asserted absent, and a third failed
    on a comment explaining why a constant was deliberately not used. This
    module's docstring names every one of these on purpose.
    """

    FORBIDDEN = (
        # It would put the document in the folder IntelliBooks drains, which is
        # how it would reach the receipts list. Paul's second and third
        # conditions.
        "publish_receipt", "save_publish_event",
        # Not extracted and not validated. Paul's first condition.
        "save_extraction", "validate", "extract",
        # No category without an extraction to categorise.
        "save_categorisation", "categorise",
        # The copy is due at Post and is written by the one gated caller, not
        # here. Writing it on arrival is the write amendment 73 cancelled.
        "write_client_copy", "copy_for_published_receipt",
    )

    def called_names(self, module_path):
        tree = ast.parse(Path(module_path).read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            if isinstance(function, ast.Attribute):
                names.add(function.attr)
            elif isinstance(function, ast.Name):
                names.add(function.id)
        return names

    def test_the_attached_module_calls_none_of_them(self):
        called = self.called_names(REPO_ROOT / "worker" / "attached.py")
        for name in self.FORBIDDEN:
            with self.subTest(call=name):
                self.assertNotIn(
                    name, called,
                    f"worker\\attached.py calls {name}(), which an attached "
                    "document must not reach")

    def test_the_consumer_calls_none_of_them_either(self):
        """`_consume_attached_documents()` alone, off the tree, because
        `app.py` calls most of these elsewhere and a whole-file check would
        pass for the wrong reason or fail for one.
        """
        tree = ast.parse((REPO_ROOT / "app.py").read_text(encoding="utf-8"))
        consumer = [node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "_consume_attached_documents"]
        self.assertEqual(len(consumer), 1,
                         "_consume_attached_documents() is not in app.py")
        names = set()
        for node in ast.walk(consumer[0]):
            if isinstance(node, ast.Call):
                function = node.func
                if isinstance(function, ast.Attribute):
                    names.add(function.attr)
                elif isinstance(function, ast.Name):
                    names.add(function.id)
        for name in self.FORBIDDEN:
            with self.subTest(call=name):
                self.assertNotIn(name, names)

    def test_it_is_reached_before_the_resolution_notes(self):
        """The ordering, off the tree rather than from the comment beside it.

        Both messages can be waiting in one poll, and the other order puts the
        note in `failed\\` naming a receipt that does not exist yet.
        `TheThreeTriggersTest` drives that; this says why it passes.
        """
        tree = ast.parse((REPO_ROOT / "app.py").read_text(encoding="utf-8"))
        process_once = [node for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "process_once"][0]
        order = [node.func.id for node in ast.walk(process_once)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id in ("_consume_attached_documents",
                                      "_consume_resolution_notes",
                                      "_retry_failed_receipts")]
        self.assertEqual(order, ["_consume_attached_documents",
                                 "_consume_resolution_notes",
                                 "_retry_failed_receipts"])


def tracked_python_files():
    """Every production Python file git tracks. `.history\\` is excluded by
    construction, being gitignored, which `CLAUDE.md`'s sixth trap requires:
    it holds a dated copy of every file ever edited and an enumeration that
    includes it reports names that no longer exist anywhere live.
    """
    listed = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True).stdout.split()
    return [REPO_ROOT / name for name in listed
            if not name.startswith("tests/")]


def sql_constants(node):
    """Every string constant in this function's body, docstring excluded.

    The docstring is dropped for `tests/test_step10d_pipeline.py`'s reason: it
    is a string constant too, and the comment recording a correction is exactly
    the prose this project writes next to the code it corrects.
    """
    body = list(node.body)
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    out = []
    for statement in body:
        for child in ast.walk(statement):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                out.append(child.value)
    return out


# ---------------------------------------------------------------------------
# The three triggers
# ---------------------------------------------------------------------------


class TheThreeTriggersTest(AttachedTestCase):
    """What Desktop needs to know before it decides whether to send at all."""

    def receipts_dir(self, tax_year="2025-26"):
        return (config.CLIENTS_ROOT / "Test Client" /
                config.CLIENT_INTELLIBOOKS_FOLDER_NAME /
                config.CLIENT_RECEIPTS_FOLDER_NAME / tax_year)

    def test_on_post_the_copy_is_written_and_named_from_the_transaction(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()
            self.poll()
            self.assertEqual(everything_under(config.CLIENTS_ROOT), [],
                             "the control: nothing is there before the note")

            self.write_attached_note()
            self.poll()

            self.assertEqual(
                everything_under(config.CLIENTS_ROOT),
                ["Test Client/IntelliBooks/Receipts/2025-26/"
                 "2026-04-01_apcoa-parking-8841-london_96.00.pdf"],
                "the Post-time message did not produce the copy, or named it "
                "from something other than the transaction")
            filed = self.receipt()["filed_path"]
            self.assertTrue(Path(filed).exists())
            self.assertEqual(Path(filed).read_bytes(), DOCUMENT)

    def test_on_post_one_poll_is_enough_for_both_messages(self):
        """The handoff is consumed before the resolution notes, so a document
        attached and posted between two polls does not need a second one. The
        other order leaves the note in `failed\\` naming a receipt that did not
        exist yet, and nothing retries a failed note.
        """
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()
            self.write_attached_note()

            self.poll()

            self.assertEqual(len(everything_under(config.CLIENTS_ROOT)), 1)
            failed = config.RESOLUTIONS_DIR / "failed"
            self.assertEqual(
                [] if not failed.is_dir() else sorted(p.name for p in failed.iterdir()),
                [])

    def test_on_publish_no_copy_is_ever_written_and_it_says_so(self):
        """**An attached document never publishes, so the `publish` trigger's
        moment never arrives for one.** That is the same rule a receipt gets
        rather than a different one, and the consequence is worth a line in the
        log rather than silence: a firm on `publish` that attaches documents
        from bank lines gets no copies of them.
        """
        with TempEnvironment(), trigger(config.CLIENT_COPY_ON_PUBLISH):
            self.hand_over()
            self.poll()
            self.write_attached_note()

            with Capture() as log:
                self.poll()

            self.assertEqual(everything_under(config.CLIENTS_ROOT), [])
            self.assertIsNone(self.receipt()["filed_path"])
            self.assertTrue(
                any(config.CLIENT_COPY_ON_PUBLISH in m and RECEIPT_ID[:8] in m
                    for m in log.messages()),
                f"nothing said why no copy was written: {log.messages()}")

    def test_on_never_nothing_is_written(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_NEVER):
            self.hand_over()
            self.poll()
            self.write_attached_note()
            self.poll()

            self.assertEqual(everything_under(config.CLIENTS_ROOT), [])
            self.assertIsNone(self.receipt()["filed_path"])

    def test_the_note_is_applied_on_all_three(self):
        """A firm can be on any of the three and Desktop sends the same message
        to all of them, so the pipeline decides and the note is never an error
        anywhere. 10f.37's rule, kept.
        """
        for value in (config.CLIENT_COPY_AT_POST, config.CLIENT_COPY_ON_PUBLISH,
                      config.CLIENT_COPY_NEVER):
            with self.subTest(trigger=value):
                with TempEnvironment(), trigger(value):
                    self.hand_over()
                    self.poll()
                    note = self.write_attached_note()
                    self.poll()

                    processed = config.RESOLUTIONS_DIR / "processed"
                    self.assertIn(
                        note.name,
                        sorted(p.name for p in processed.iterdir()))

    def test_the_copy_happens_once_and_a_second_note_does_not_duplicate_it(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.hand_over()
            self.poll()
            self.write_attached_note()
            self.poll()

            self.write_attached_note(resolved_at="2026-09-11T12:00:00.000Z")
            self.poll()

            self.assertEqual(len(everything_under(config.CLIENTS_ROOT)), 1)


# ---------------------------------------------------------------------------
# Detaching, amendment 321
# ---------------------------------------------------------------------------


class DetachingTest(AttachedTestCase):
    """Paul's decision of 2026-09-11: the same dialogue as the receipt Delete,
    and the copy goes only if he ticks the box. **The removal already exists**
    and nothing about it is rebuilt: Desktop sends a `discarded` note carrying
    `delete_client_copy`, which is 10f.27's mechanism.
    """

    def discard_note(self, delete_client_copy):
        config.RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": 1,
            "receipt_id": RECEIPT_ID,
            "client_id": "CLIENT001",
            "action": "discarded",
            "resolved_by": "desktop",
            "resolved_at": "2026-09-11T13:00:00.000Z",
            "reason": "detached from the transaction",
            "delete_client_copy": delete_client_copy,
        }
        path = config.RESOLUTIONS_DIR / f"{RECEIPT_ID}_1757595600000.json"
        path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        return path

    def attach_and_post(self):
        self.hand_over()
        self.poll()
        self.write_attached_note()
        self.poll()
        self.assertEqual(len(everything_under(config.CLIENTS_ROOT)), 1)

    def test_ticking_the_box_removes_the_copy(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.attach_and_post()

            self.discard_note(True)
            self.poll()

            self.assertEqual(everything_under(config.CLIENTS_ROOT), [])
            self.assertEqual(self.receipt()["status"], "discarded")
            self.assertIsNone(self.receipt()["filed_path"])

    def test_leaving_it_unticked_leaves_the_copy(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.attach_and_post()

            self.discard_note(False)
            self.poll()

            self.assertEqual(len(everything_under(config.CLIENTS_ROOT)), 1)
            self.assertEqual(self.receipt()["status"], "discarded")

    def test_the_archive_of_record_is_never_touched(self):
        """18.2a. It is what makes deleting the client folder copy safe."""
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            self.attach_and_post()
            before = everything_under(config.FILES_DIR)

            self.discard_note(True)
            self.poll()

            self.assertEqual(everything_under(config.FILES_DIR), before)


if __name__ == "__main__":
    unittest.main()

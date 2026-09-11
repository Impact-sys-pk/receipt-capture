r"""Sub-step 10f.37: the Post-time message, so the copy happens at Post.

**Paul's decision of 2026-09-10, amendment 315.** `client_copy_trigger` has had
three values since 10f.12 and the `post` one has never worked:
`copy_for_published_receipt()` said so in its own warning, that the Post-time
trigger needs a message from IntelliBooks Desktop and no copy is written until
it exists.

**That message had no sub-step.** 10f.12 said it was 10f.16's, 10f.16 said it
was 10f.12's, both are BUILT, and the code comment pointed at 10f.16. Three
places pointing elsewhere and none holding the work. Amendment 315 gave it a
number.

**Why Paul wants it, in his words.** On the `publish` trigger the client folder
holds whatever the pipeline succeeded on, including duplicates that got
through, strays and documents that turned out to be personal, and nothing
removes them. `Clients\{client}\IntelliBooks\Receipts\{tax year}\` should hold
the receipts relating to that client's transactions and make sense to him and
to the client years later. **On `post` a document reaches that folder because it
was attached to a transaction, so the folder is curated by construction.**

## The action word is `attached`, and it is a third action rather than a field

**Amendment 307's rule is that the field chooses the path, not the action
word**, so this needs justifying rather than asserting. It is a third action
because of what the current pipeline does with each shape:

- **A new action word fails loudly.** `parse_resolution_note()` refuses an
  action outside `NOTE_ACTIONS`, so a Desktop that ships first leaves its notes
  in `Resolutions\failed\` with an `.error.txt` beside each. The two halves are
  meant to land together and this is what that looks like when they do not.
- **A field on a `filed` note would be applied silently and wrongly.**
  `parse_resolution_note()`'s documented leniency is that extra keys are
  ignored, so a pipeline that did not know the field would treat the note as a
  filing: `_settle_note()` would re-settle an already-`ok` receipt, write a new
  `manual_correction` extraction row and recategorise it. Worse than a refusal
  and invisible.

**And the two existing actions both change the receipt's status.** This one
changes nothing about the receipt: no status, no extraction, no
categorisation. It writes a client folder copy and an audit row and that is
all.

**`attached` names the receipt's state, not the moment Desktop sent it.** It is
true from Attach onwards and still true after Post, so it does not presuppose
the answer to whether Desktop sends at Attach, at Post or at both, which is
Paul's to rule on and is set out in the report.
"""

import ast
import json
import logging
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
from worker import client_copy  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.resolution.service import (  # noqa: E402
    NOTE_ACTIONS,
    NOTE_APPLIED_OUTCOMES,
    ATTACHED_ACTION,
    ResolutionNoteError,
    parse_resolution_note,
)

import app  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


@contextmanager
def trigger(value):
    """Set the firm's client copy trigger for one test, and put it back.

    A local copy of `tests/test_stage4_client_copy.py`'s, six lines, because
    importing a test module from another one makes pytest collect it twice
    under two names.
    """
    saved = config.CLIENT_COPY_TRIGGER
    config.CLIENT_COPY_TRIGGER = value
    try:
        yield
    finally:
        config.CLIENT_COPY_TRIGGER = saved


class Capture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def __enter__(self):
        self.loggers = [logging.getLogger("worker.resolution.service"),
                        logging.getLogger("worker.client_copy")]
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


def attached_note(**overrides):
    """The message, exactly as section 12.2 shapes one.

    **Which receipt, which client, that it is attached, and when. No path.**
    The pipeline composes the client folder name itself, and a name composed by
    Desktop cannot tell a collision's `-2` from its original.
    """
    payload = {
        "schema": 1,
        "receipt_id": "r-1",
        "client_id": "CLIENT001",
        "action": ATTACHED_ACTION,
        "resolved_by": "desktop",
        "resolved_at": "2026-09-10T17:00:00.000Z",
    }
    payload.update(overrides)
    return payload


def statements_or_receipts_dir(tax_year="2025-26"):
    return (config.CLIENTS_ROOT / "Test Client" /
            config.CLIENT_INTELLIBOOKS_FOLDER_NAME /
            config.CLIENT_RECEIPTS_FOLDER_NAME / tax_year)


def everything_under(root: Path):
    if not root.exists():
        return []
    return sorted(p.relative_to(root).as_posix()
                  for p in root.rglob("*") if p.is_file())


class PostTimeTestCase(unittest.TestCase):
    """A published, `ok` receipt with no client folder copy: the `post` shape."""

    def seed(self, env, receipt_id="r-1", status="ok", published=True,
             filed=False):
        repo = Repository()
        try:
            env.seed(repo, receipt_id=receipt_id, status=status,
                     supplier_name="Apcoa Parking", invoice_date="2026-04-01",
                     net_amount=80.0, vat_amount=16.0, gross_amount=96.0,
                     validation_status="ok", validation_notes=[])
            if published:
                repo.save_publish_event(
                    event_id=f"pub-{receipt_id}", receipt_id=receipt_id,
                    destination="intellibooks", outcome="published",
                    created_at="2026-09-10T16:00:00+00:00",
                    item_path=f"/published/{receipt_id}.json")
            if filed:
                target = statements_or_receipts_dir() / "already-there.pdf"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"the copy the publish trigger wrote")
                repo.mark_receipt_filed(receipt_id, str(target))
        finally:
            repo.close()

    def write_note(self, payload, name=None):
        config.RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        receipt_id = payload.get("receipt_id", "unknown")
        path = config.RESOLUTIONS_DIR / (name or f"{receipt_id}_1757520000000.json")
        path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        return path

    def poll(self):
        """One real `process_once()` with the mailbox and extractor stubbed.

        The brief asks for a real poll rather than a call to the handler,
        because the value of this change is that a file appears in a folder.
        `_consume_resolution_notes()` runs first inside it, per 12.3.
        """
        client_copy._reset_post_warning()
        Routes(RecordingExtractor(extraction_result()))._run()

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

    def note_names(self, subfolder=None):
        base = (config.RESOLUTIONS_DIR if subfolder is None
                else config.RESOLUTIONS_DIR / subfolder)
        if not base.is_dir():
            return []
        return sorted(p.name for p in base.iterdir() if p.is_file())


class TheNoteShapeTest(unittest.TestCase):
    """Deliverable 1's contract, which the Desktop half is written to."""

    def test_the_action_word_is_attached_and_it_is_a_third_action(self):
        """**A fourth word joined it on 2026-09-11**, `corrected`, step 10k.
        This assertion holds the whole tuple rather than membership, so a word
        added to it fails here and has to be considered against this sub-step
        before the list is updated. That is what it is for.
        """
        self.assertEqual(ATTACHED_ACTION, "attached")
        self.assertEqual(NOTE_ACTIONS,
                         ("filed", "discarded", "attached", "corrected"))

    def test_it_parses_with_no_values_and_no_filed_path(self):
        note = parse_resolution_note(attached_note())
        self.assertEqual(note.action, "attached")
        self.assertEqual(note.receipt_id, "r-1")
        self.assertEqual(note.client_id, "CLIENT001")
        self.assertEqual(note.resolved_at, "2026-09-10T17:00:00.000Z")
        self.assertIsNone(note.filed_path)
        self.assertEqual(note.values, {})

    def test_resolved_at_is_still_required_because_it_is_the_idempotency_key(self):
        payload = attached_note()
        del payload["resolved_at"]
        with self.assertRaises(ResolutionNoteError) as caught:
            parse_resolution_note(payload)
        self.assertIn("resolved_at", str(caught.exception))

    def test_a_path_on_an_attached_note_is_ignored_and_said_out_loud(self):
        """The same treatment 12.2 gives `values` and `filed_path` on a discard.

        **The pipeline composes the name**, so a path here is a Desktop that
        has misread the contract, and ignoring it silently would let that go on.
        """
        with Capture() as log:
            note = parse_resolution_note(attached_note(
                filed_path=r"Clients\Test Client\somewhere.pdf",
                values={"gross_amount": 96}))
        self.assertIsNone(note.filed_path)
        self.assertEqual(note.values, {})
        self.assertTrue(
            any("filed_path" in m for m in log.messages(logging.WARNING)),
            f"the ignored path was not reported: {log.messages()}")

    def test_an_action_nobody_understands_still_fails(self):
        """The control. Adding a third word must not open the gate."""
        with self.assertRaises(ResolutionNoteError) as caught:
            parse_resolution_note(attached_note(action="posted"))
        self.assertIn("attached", str(caught.exception))

    def test_the_applied_outcomes_are_one_definition(self):
        """`app.py` decides `processed\\` against this rather than its own tuple.

        Two literals in two files that must agree is how the third word would
        have gone to `failed\\` on success, which is what the first red run
        showed.
        """
        self.assertEqual(NOTE_APPLIED_OUTCOMES,
                         ("filed", "discarded", "attached", "corrected"))


class OnThePostTriggerTest(PostTimeTestCase):
    """The point of the sub-step: a file appears in the client folder."""

    def test_the_copy_is_written_when_the_message_arrives(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            self.seed(env)
            self.assertEqual(everything_under(config.CLIENTS_ROOT), [],
                             "the control: nothing is there before the note")
            note = self.write_note(attached_note())

            self.poll()

            self.assertEqual(
                everything_under(config.CLIENTS_ROOT),
                ["Test Client/IntelliBooks/Receipts/2025-26/"
                 "2026-04-01_apcoa-parking_96.00.pdf"],
                "the Post-time message did not produce the client folder copy")
            self.assertIn(note.name, self.note_names("processed"))

    def test_filed_path_is_recorded_by_the_one_writer(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            self.seed(env)
            self.write_note(attached_note())

            self.poll()

            filed = self.receipt()["filed_path"]
            self.assertIsNotNone(filed, "filed_path was not recorded")
            self.assertTrue(Path(filed).exists())
            self.assertTrue(str(filed).startswith(str(config.CLIENTS_ROOT)))

    def test_the_audit_row_records_it(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            self.seed(env)
            self.write_note(attached_note())

            self.poll()

            attached = [e for e in self.events() if e["outcome"] == "attached"]
            self.assertEqual(len(attached), 1, f"{self.events()}")
            row = attached[0]
            self.assertEqual(row["actor"], "desktop")
            self.assertEqual(row["source"], "desktop")
            payload = json.loads(row["corrections_json"] or "{}")
            self.assertEqual(payload.get("note_resolved_at"),
                             "2026-09-10T17:00:00.000Z")

    def test_it_changes_nothing_about_the_receipt_itself(self):
        """No status change, no extraction row, no categorisation row.

        The receipt was already `ok` and published. All this message does is
        say the document is in the accounts.
        """
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            self.seed(env)
            repo = Repository()
            try:
                before_extractions = rows(repo, "SELECT * FROM extractions")
                before_categorisations = rows(repo, "SELECT * FROM categorisations")
            finally:
                repo.close()
            self.write_note(attached_note())

            self.poll()

            repo = Repository()
            try:
                self.assertEqual(rows(repo, "SELECT * FROM extractions"),
                                 before_extractions)
                self.assertEqual(rows(repo, "SELECT * FROM categorisations"),
                                 before_categorisations)
            finally:
                repo.close()
            self.assertEqual(self.receipt()["status"], "ok")

    def test_the_document_store_is_untouched(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            self.seed(env)
            original = Path(self.receipt()["file_path"])
            self.write_note(attached_note())

            self.poll()

            self.assertTrue(original.exists(),
                            "the archive of record was touched, and 18.2a says "
                            "it is never written to or deleted from")


class OnTheOtherTwoTriggersTest(PostTimeTestCase):
    """`publish` and `never`, because the same Desktop sends the same message.

    **Neither is an error.** A firm can be on any of the three and Desktop does
    not know which, so the pipeline decides. That is the answer to question 2
    of the report.
    """

    def test_on_publish_the_copy_already_exists_and_nothing_is_written(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_ON_PUBLISH):
            self.seed(env, filed=True)
            before = everything_under(config.CLIENTS_ROOT)
            self.assertEqual(len(before), 1, "the control: the copy is there")
            note = self.write_note(attached_note())

            with Capture() as log:
                self.poll()

            self.assertEqual(everything_under(config.CLIENTS_ROOT), before,
                             "a second copy was written on the publish trigger")
            self.assertIn(note.name, self.note_names("processed"),
                          "the note was not applied, and on publish it must be")
            self.assertEqual(log.messages(logging.ERROR), [],
                             f"an error was logged: {log.messages()}")

    def test_on_publish_this_message_is_not_what_writes_the_copy(self):
        """The narrower half, and `filed_path` cannot answer it.

        **The first version of this test asserted `filed_path` was still
        NULL and it went red for the right reason.** On `publish`, a published
        receipt with no copy is exactly what `_copy_missing_client_copies()`
        sweeps up, so a copy DOES appear in that poll: the sweep wrote it, not
        this note. The column records that a copy exists and not who made one,
        so it cannot tell the two apart.

        **The audit row can.** `client_copy_written` is written only where the
        Post-time handler itself produced a path, so its absence is the
        assertion that wants making.
        """
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_ON_PUBLISH):
            self.seed(env, filed=False)
            self.write_note(attached_note())

            self.poll()

            attached = [e for e in self.events() if e["outcome"] == "attached"]
            self.assertEqual(len(attached), 1)
            payload = json.loads(attached[0]["corrections_json"] or "{}")
            self.assertNotIn(
                "client_copy_written", payload,
                "the Post-time message wrote the copy on the publish trigger, "
                "and on that trigger the publish path owns it")

    def test_on_never_nothing_is_written_and_the_note_is_applied(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_NEVER):
            self.seed(env)
            note = self.write_note(attached_note())

            self.poll()

            self.assertEqual(everything_under(config.CLIENTS_ROOT), [],
                             "`never` wrote a copy, which is the setting not "
                             "doing its job")
            self.assertIn(note.name, self.note_names("processed"))

    def test_never_means_never_whatever_moment_the_caller_claims(self):
        """The `never` branch is subsumed by the trigger comparison, and kept.

        **Found by a mutation that survived.** Removing
        `if CLIENT_COPY_TRIGGER == CLIENT_COPY_NEVER: return None` left the
        whole suite green, because the next check is
        `if CLIENT_COPY_TRIGGER != at` and on a `never` firm that is true for
        either moment a real caller can be at.

        **So the branch is defence rather than logic, and this is what makes it
        load-bearing.** A caller passing `at=never` would otherwise satisfy
        `never != never` as False and fall through to write a copy on the one
        trigger whose whole purpose is that nothing is written. Nothing passes
        that today; the branch is what means a future one cannot.
        """
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_NEVER):
            self.seed(env)
            receipt = self.receipt()
            repo = Repository()
            try:
                result = client_copy.copy_for_published_receipt(
                    repo,
                    receipt_id="r-1",
                    client_id="CLIENT001",
                    source_file=Path(receipt["file_path"]),
                    invoice_date="2026-04-01",
                    supplier="Apcoa Parking",
                    gross=96.0,
                    validation_status="ok",
                    filed_path=None,
                    at=config.CLIENT_COPY_NEVER,
                )
            finally:
                repo.close()
            self.assertIsNone(result)
            self.assertEqual(
                everything_under(config.CLIENTS_ROOT), [],
                "a caller claiming to be at the `never` moment got a copy "
                "written on the `never` trigger")

    def test_every_trigger_applies_the_note(self):
        for value in (config.CLIENT_COPY_ON_PUBLISH, config.CLIENT_COPY_AT_POST,
                      config.CLIENT_COPY_NEVER):
            with self.subTest(trigger=value):
                with TempEnvironment() as env, trigger(value):
                    self.seed(env)
                    note = self.write_note(attached_note())
                    self.poll()
                    self.assertIn(
                        note.name, self.note_names("processed"),
                        f"on the {value!r} trigger the note went to failed\\, "
                        "and the same Desktop sends the same message to every "
                        "firm")


class TwoMessagesWriteNothingTwiceTest(PostTimeTestCase):
    """Three layers hold this, and the brief asks which. All three.

    1. **The idempotency key**, 12.3 step 3: a second note with the same
       `resolved_at` is skipped before the action branch is reached.
    2. **The one-copy gate** in `copy_for_published_receipt()`: a receipt with a
       `filed_path` is not copied again, so a genuinely later note writes
       nothing.
    3. **The identical-bytes skip** in `write_client_copy()`, 10f.25, which
       would catch it even if the other two were bypassed.

    Each is asserted separately below rather than inferred from one pass.
    """

    def test_the_same_note_twice_is_skipped_on_the_key(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            self.seed(env)
            self.write_note(attached_note(), name="r-1_1.json")
            self.poll()
            first = everything_under(config.CLIENTS_ROOT)

            self.write_note(attached_note(), name="r-1_2.json")
            self.poll()

            self.assertEqual(everything_under(config.CLIENTS_ROOT), first,
                             "a replayed note wrote a second file")
            self.assertEqual(
                len([e for e in self.events() if e["outcome"] == "attached"]), 1,
                "a replayed note wrote a second audit row")

    def test_a_genuinely_later_note_writes_nothing_twice_either(self):
        """A different `resolved_at`, so the key does not skip it. The one-copy
        gate is what holds here."""
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            self.seed(env)
            self.write_note(attached_note(), name="r-1_1.json")
            self.poll()
            first = everything_under(config.CLIENTS_ROOT)
            self.assertEqual(len(first), 1)

            self.write_note(
                attached_note(resolved_at="2026-09-10T18:00:00.000Z"),
                name="r-1_2.json")
            self.poll()

            self.assertEqual(
                everything_under(config.CLIENTS_ROOT), first,
                "a later note wrote a second file, so the one-copy gate is not "
                "holding")
            self.assertEqual(
                len([e for e in self.events() if e["outcome"] == "attached"]), 2,
                "a genuinely later note should still leave its own audit row")

    def test_the_identical_bytes_skip_is_the_third_layer(self):
        """Asserted on the writer, because the two gates above stop the caller
        reaching it. 10f.25."""
        with TempEnvironment():
            destination = statements_or_receipts_dir()
            destination.mkdir(parents=True, exist_ok=True)
            source = config.FILES_DIR / "r.pdf"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"one document")
            first = client_copy.write_client_copy(
                source_file=source, client_folder_name="Test Client",
                tax_year="2025-26", supplier="Apcoa Parking", gross=96.0,
                invoice_date="2026-04-01")
            second = client_copy.write_client_copy(
                source_file=source, client_folder_name="Test Client",
                tax_year="2025-26", supplier="Apcoa Parking", gross=96.0,
                invoice_date="2026-04-01")
            self.assertTrue(first.written)
            self.assertFalse(second.written, "the identical bytes were copied "
                                             "again under a -2")
            self.assertEqual(first.path, second.path)


class TheSweepDoesNotInterfereTest(PostTimeTestCase):
    """The brief's question 2, established from the code and then driven.

    `_copy_missing_client_copies()` returns before its query unless the trigger
    is `publish`:

        if config.CLIENT_COPY_TRIGGER != config.CLIENT_COPY_ON_PUBLISH:
            return

    So on `post` it does nothing at all, and the two cannot write the same file
    because only one of them runs.
    """

    def test_the_guard_is_the_first_statement_of_the_sweep(self):
        """Read off the tree, so a later edit that moves it below the query
        goes red rather than costing a query every poll."""
        tree = ast.parse((REPO_ROOT / "app.py").read_text(encoding="utf-8"))
        function, = [n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef)
                     and n.name == "_copy_missing_client_copies"]
        body = [n for n in function.body if not isinstance(n, ast.Expr)]
        first = body[0]
        self.assertIsInstance(first, ast.If)
        self.assertEqual(
            ast.unparse(first.test),
            "config.CLIENT_COPY_TRIGGER != config.CLIENT_COPY_ON_PUBLISH")
        self.assertIsInstance(first.body[0], ast.Return)

    def test_a_poll_with_no_note_writes_nothing_on_post(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            self.seed(env)

            self.poll()

            self.assertEqual(
                everything_under(config.CLIENTS_ROOT), [],
                "something wrote a client folder copy on the post trigger "
                "without a Post-time message")
            self.assertIsNone(self.receipt()["filed_path"])

    def test_the_publish_time_caller_says_why_it_wrote_nothing_on_post(self):
        """Once per process, not once per receipt, and it names 10f.37.

        **A receipt has to actually publish for that line to be reached**, and
        the first version of this test seeded an already-published receipt and
        asserted the line, which produced an empty log. Nothing in such a poll
        calls the publish-time gate at all: `_publish_unpublished_receipts()`
        skips a receipt that has published and `_copy_missing_client_copies()`
        returns before its query on `post`. So this drives a real arrival.
        """
        from resolution_fixtures import with_email_client

        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            with_email_client(self)
            client_copy._reset_post_warning()
            with Capture() as log:
                Routes(RecordingExtractor(extraction_result())).email_attachment(
                    message_id="an-arrival", data=b"a receipt arriving now")

            said = " ".join(log.messages())
            self.assertIn("10f.37", said,
                          f"the log does not name the sub-step: {said[:600]}")
            self.assertEqual(
                everything_under(config.CLIENTS_ROOT), [],
                "the arrival wrote a client folder copy on the post trigger")

    def test_that_line_is_said_once_per_process_and_not_once_per_receipt(self):
        from resolution_fixtures import with_email_client

        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            with_email_client(self)
            client_copy._reset_post_warning()
            with Capture() as log:
                Routes(RecordingExtractor(extraction_result())).email_attachment(
                    message_id="one", data=b"the first receipt")
                Routes(RecordingExtractor(extraction_result())).email_attachment(
                    message_id="two", data=b"the second receipt")

            said = [m for m in log.messages() if "10f.37" in m]
            self.assertEqual(len(said), 1,
                             f"the line was said {len(said)} times")


class TheAwkwardCasesTest(PostTimeTestCase):
    """What the brief asked to be established rather than assumed."""

    def test_a_receipt_that_is_not_ok_is_refused_by_the_existing_gate(self):
        """`copy_for_published_receipt()` already refuses anything but `ok`,
        per 18.2b: the folder shows the result of the work, and a receipt with
        no gross is not a result. The receipt's own status is what is passed."""
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            self.seed(env, status="needs_review")
            note = self.write_note(attached_note())

            self.poll()

            self.assertEqual(everything_under(config.CLIENTS_ROOT), [],
                             "a needs_review receipt reached a client folder")
            self.assertIn(note.name, self.note_names("processed"),
                          "the note is still applied: the receipt's status is "
                          "not the note's fault")

    def test_a_receipt_with_no_published_row_is_copied_and_reported(self):
        """Question 1 of the report, and the answer is that it cannot happen.

        A receipt reaches the books through the drain, which needs a publish, so
        a note naming a receipt with no `published` row means the two products
        disagree about how it got there. **It is not refused**: Desktop owns the
        books and is the authority on what is in them, and refusing would leave
        a receipt in the accounts with no copy AND a note in `failed\\`, which
        is the worse of the two states. It is a WARNING.
        """
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            self.seed(env, published=False)
            note = self.write_note(attached_note())

            with Capture() as log:
                self.poll()

            self.assertEqual(
                len(everything_under(config.CLIENTS_ROOT)), 1,
                "the copy was refused for a receipt Desktop says is in the "
                "accounts")
            self.assertIn(note.name, self.note_names("processed"))
            self.assertTrue(
                any("published" in m for m in log.messages(logging.WARNING)),
                f"the anomaly was not reported: {log.messages(logging.WARNING)}")

    def test_a_note_for_a_receipt_that_does_not_exist_goes_to_failed(self):
        with TempEnvironment(), trigger(config.CLIENT_COPY_AT_POST):
            note = self.write_note(attached_note(receipt_id="r-nobody"))

            self.poll()

            self.assertIn(note.name, self.note_names("failed"))

    def test_a_client_with_no_folder_name_is_refused_by_the_existing_gate(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_AT_POST):
            self.seed(env)
            config.CLIENTS_BY_ID = {
                "CLIENT001": {"client_name": "Test Client",
                              "client_id": "CLIENT001", "firm_id": "INTELLITAX",
                              "trade": "UNSPECIFIED"}}
            note = self.write_note(attached_note())

            with Capture() as log:
                self.poll()

            self.assertEqual(everything_under(config.CLIENTS_ROOT), [])
            self.assertIn(note.name, self.note_names("processed"))
            self.assertTrue(
                any("client_folder_name" in m
                    for m in log.messages(logging.WARNING)),
                f"10d.18's refusal was not reported: {log.messages()}")


class TheSetClaimsTest(unittest.TestCase):
    """From the syntax tree, `.history\\` excluded. `CLAUDE.md`'s rule."""

    def production_files(self):
        files = [REPO_ROOT / "app.py"]
        files += sorted((REPO_ROOT / "worker").rglob("*.py"))
        files += sorted(p for p in REPO_ROOT.glob("*.py") if p.name != "app.py")
        return [p for p in files if "__pycache__" not in p.parts]

    def _owner(self, tree, node):
        best = None
        for candidate in ast.walk(tree):
            if not isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if candidate.lineno <= node.lineno <= (candidate.end_lineno
                                                   or candidate.lineno):
                if best is None or candidate.lineno > best.lineno:
                    best = candidate
        return best.name if best else "<module scope>"

    def test_every_caller_of_the_gated_copier_is_the_allowed_set(self):
        """Five now. The fifth is this sub-step's, and it reaches the same
        gated function rather than writing beside it, which is what keeps
        10f.11's one writer true."""
        sites = []
        for path in self.production_files():
            if path.name == "client_copy.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and ast.unparse(node.func).split(".")[-1]
                        == "copy_for_published_receipt"):
                    sites.append(f"{path.name}::{self._owner(tree, node)}")
        self.assertEqual(
            sorted(sites),
            ["app.py::_copy_missing_client_copies",
             "app.py::_publish_unpublished_receipts",
             "extraction_pipeline.py::process_extraction_result",
             "service.py::_apply_attached_note",
             "service.py::resolve_receipt"],
            "the set of callers of the gated client folder copier has changed")

    def test_write_client_copy_is_still_reached_from_one_place(self):
        sites = []
        for path in self.production_files():
            if path.name == "client_copy.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and ast.unparse(node.func).split(".")[-1]
                        == "write_client_copy"):
                    sites.append(f"{path.name}:{node.lineno}")
        self.assertEqual(sites, [],
                         f"write_client_copy() is called from {sites}, and "
                         "every caller goes through the gated function")

    def test_app_py_does_not_carry_its_own_tuple_of_applied_outcomes(self):
        """One definition. The third word had to reach both files and a literal
        in each is how it would reach only one."""
        tree = ast.parse((REPO_ROOT / "app.py").read_text(encoding="utf-8"))
        function, = [n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef)
                     and n.name == "_consume_resolution_notes"]
        literals = [ast.unparse(n) for n in ast.walk(function)
                    if isinstance(n, ast.Tuple)
                    and all(isinstance(e, ast.Constant) for e in n.elts)
                    and any(getattr(e, "value", None) == "filed" for e in n.elts)]
        self.assertEqual(
            literals, [],
            f"app.py still decides processed\\ against its own tuple: {literals}")
        self.assertIn("NOTE_APPLIED_OUTCOMES",
                      ast.unparse(function))

    def test_the_code_no_longer_sends_its_reader_to_a_built_sub_step(self):
        """10f.16 is BUILT and the Post-time message is 10f.37.

        `worker\\client_copy.py` named 10f.16 in the comment and in the warning
        of its `post` branch, which is a reader sent to a finished sub-step.

        **This asserts where 10f.16 may still appear, not that it is gone.**
        The first version of this test required the string to be absent, and
        that was wrong: this project keeps superseded wording beside the
        correction, so naming 10f.16 as the number that WAS pointed at is
        right and deleting it would lose the trail. What must not survive is a
        mention that reads as somewhere to look, so every surviving one has to
        say `BUILT` on its own line.
        """
        source = (REPO_ROOT / "worker" / "client_copy.py").read_text(
            encoding="utf-8")
        self.assertIn("10f.37", source,
                      "the Post-time message's own sub-step is not named")
        stale = [line.strip() for line in source.splitlines()
                 if "10f.16" in line and "BUILT" not in line]
        self.assertEqual(
            stale, [],
            "worker/client_copy.py names sub-step 10f.16 without saying it is "
            f"BUILT, so a reader is sent to finished work: {stale}")


if __name__ == "__main__":
    unittest.main()

r"""The Review seam: an item the pipeline published, resolved, and applied back.

**Step 10am, the Python half. Paul's decision of 2026-09-13 at amendment 399,
and his decision of 2026-09-19 to split the step between the two sessions.**

## What was already covered, and is not repeated here

`tests\test_publish_trigger.py` drives a real `app.process_once()` with only the
mailbox and the extractor replaced, and four of its tests already prove that a
receipt which is not `ok` publishes an item:
`test_needs_review_publishes_one_item`, `test_a_failed_extraction_publishes_one_item`,
`test_a_possible_duplicate_publishes_too` and
`test_an_extraction_that_raised_publishes_nothing`.
`tests\test_publish_item.py` holds the item's shape in 30 tests.

`tests\test_resolution_backfeed.py` covers the consumer in over forty tests,
`DiscardedNoteTest` among them. **Every one of them seeds the database
directly** through `BackfeedTestCase.seed_desktop_filed()` or
`seed_awaiting_settlement()`, and drives `_consume_resolution_notes()` on its
own through `consume_notes()`.

## So what is new here is the join, and only the join

**Nothing proved that an item the pipeline itself produced is taken up, resolved
and applied back.** The two ends had been exercised separately and never in one
run: one end starts from a real poll and stops at the published item, the other
starts from a hand-seeded row. A receipt that this file discards is one this
file's own first poll created, published and archived.

**The second poll is a real `app.process_once()` with an empty mailbox**, so the
note is consumed by the live consumer in the live order, not by a call written
to suit the test.

## The fixture, and why it is guarded rather than just committed

The Desktop half of step 10am is a node harness run against
`IntelliBooks-Desktop-v3.html`, which lives in OneDrive and can import nothing
from this repository. It needs one real published item to read, and
`tests\fixtures\published_item_needs_review.json` is it: **written by production
code on a real poll, not typed.**

**A committed fixture goes stale, and the guard is the point of it.**
`TheCommittedFixtureIsWhatThePipelineProducesTest` regenerates the item from a
fresh poll and compares it with what is committed. **The four volatile fields
are named rather than skipped**, and each is checked for its own shape, so
"normalised" does not quietly mean "unchecked".
"""

import json
import os
import re
import sys
import types
import unittest
import uuid
from datetime import datetime
from pathlib import Path

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import ast  # noqa: E402

import config  # noqa: E402
import source_guards  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    run_pipeline_once,
    with_email_client,
)
from worker import publish  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.resolution import service  # noqa: E402

CLIENT = "CLIENT001"

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Where the Desktop harness reads the item from. `tests\fixtures\` is a new
#: directory: this is the first fixture in the repository that is a data file
#: rather than a `*_fixtures.py` module, and `Test Receipts\` at the root is for
#: documents a receipt is made of rather than for the pipeline's own output.
#: A path under `tests\` says what it is for without anybody having to ask.
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "published_item_needs_review.json"

#: The keys of a published item that cannot be the same twice, with what each
#: one is. **Named rather than skipped**: every one is asserted to have the
#: right shape below, so the comparison loses nothing it could have checked.
#:
#: - `receipt_id` and `pipeline_receipt_id` are a uuid4 minted per receipt
#: - `capture_date` is when the poll ran
#: - `archive_path` carries the receipt id and the arrival year and month
VOLATILE_KEYS = ("receipt_id", "pipeline_receipt_id", "capture_date",
                 "archive_path")

#: `Intellibills\Documents\{client_id}\{year}\{month}\{receipt_id}_{filename}`,
#: which is `archive_address()`'s documented form with backslashes, relative to
#: the practice root. Held here so the guard checks the address's shape rather
#: than waving it through as volatile.
#:
#: **The `Intellibills\` segment is required, and that is the point of this
#: pattern rather than a detail of it.** It read `^Documents\\` until
#: 2026-09-20, and the committed fixture matched it, because
#: `tests\resolution_fixtures.py` restated `config.py`'s folder layout and
#: dropped that segment. `archive_address()` returns a path relative to
#: `PRACTICE_ROOT` and the fixture moved both ends, so the short address was
#: internally consistent and wrong, and this guard could not see it.
#:
#: **The address is the field IntelliBooks Desktop uses to open the document**,
#: so against the short form a Desktop test would look for a file where the
#: live system never writes one, and pass.
#:
#: `tests\test_publish_item.py` already asserted the live form, so the suite
#: disagreed with itself for as long as this file existed.
ARCHIVE_PATH_RE = re.compile(
    r"^Intellibills\\Documents\\CLIENT001\\\d{4}\\\d{2}\\"
    r"[0-9a-f-]{36}_shared\.pdf$")

#: The extraction that makes a review item: gross is not net + VAT, so
#: `validate()` returns `needs_review`, which is a status the Review queue holds.
#: The same shape `tests\test_publish_trigger.py` uses for `needs_review`.
REVIEW_EXTRACTION = dict(gross_amount=99.0)


def publish_one_review_item(test_case):
    """One real poll that produces one published, archived review receipt.

    Returns `(item dict, receipt row)`. The caller is inside a
    `TempEnvironment()`.
    """
    with_email_client(test_case, CLIENT)
    Routes(RecordingExtractor(extraction_result(**REVIEW_EXTRACTION))).email_attachment()

    items = sorted(config.INTELLIBOOKS_PUBLISH_DIR.glob("*.json"))
    test_case.assertEqual(
        len(items), 1,
        "the poll did not publish exactly one item, so nothing below is "
        "measuring the seam")
    item = json.loads(items[0].read_text(encoding="utf-8"))

    repo = Repository()
    try:
        rows = [dict(r) for r in repo._conn.execute("SELECT * FROM receipts")]
    finally:
        repo.close()
    test_case.assertEqual(len(rows), 1)
    test_case.assertNotEqual(
        rows[0]["status"], "ok",
        "the fixture receipt must not be ok, or it is not an item the Review "
        "queue would hold")
    return item, rows[0]


def normalised(item):
    """The item with the four volatile values replaced by their key names."""
    return {key: ("<volatile>" if key in VOLATILE_KEYS else value)
            for key, value in item.items()}


def keys_the_note_parser_reads():
    r"""Every top-level note key `parse_resolution_note()` looks at, from the tree.

    Read off `worker\resolution\service.py`'s syntax tree rather than from any
    brief. The parser reaches a key three ways, `raw.get("x")`,
    `_note_text(raw, "x")` and `_note_flag(raw, "x")`, and the flag call is
    handed a constant rather than a literal for one of them, so the constant is
    resolved against the module.
    """
    tree = source_guards.tree_of("worker", "resolution", "service.py")
    parser = next(node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef)
                  and node.name == "parse_resolution_note")
    found = set()
    for node in ast.walk(parser):
        if not isinstance(node, ast.Call):
            continue
        call = ast.unparse(node.func)
        if call == "raw.get" and node.args:
            argument = node.args[0]
        elif call in ("_note_text", "_note_flag") and len(node.args) >= 2 \
                and ast.unparse(node.args[0]) == "raw":
            argument = node.args[1]
        else:
            continue
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            found.add(argument.value)
        elif isinstance(argument, ast.Name) and argument.id.isupper():
            # A module-level constant, `NOTE_DELETE_CLIENT_COPY_KEY`. The name
            # test is what keeps the loop variable in `raw.get(unexpected)` out:
            # it is not a constant and it is not resolvable here, and the two
            # keys that loop covers are collected below instead.
            found.add(getattr(service, argument.id))
    # The loop that warns about keys a discard must not carry names two more.
    for node in ast.walk(parser):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Tuple):
            for element in node.iter.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    found.add(element.value)
    return found


class TheCommittedFixtureIsWhatThePipelineProducesTest(unittest.TestCase):
    """The fixture is regenerated on every run and compared with what is committed.

    **This is the fixture's guard and it is the reason the fixture may exist at
    all.** A committed data file that nothing regenerates is a description of
    the pipeline as it was on the day somebody saved it.
    """

    def test_the_fixture_is_present(self):
        self.assertTrue(
            FIXTURE_PATH.is_file(),
            f"{FIXTURE_PATH} is missing. It is read by the Desktop half of "
            f"step 10am, which cannot run Python, so it is committed rather "
            f"than generated on demand")

    def test_a_fresh_poll_produces_the_committed_item(self):
        committed = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        with TempEnvironment():
            produced, _ = publish_one_review_item(self)

        self.assertEqual(
            sorted(committed), sorted(produced),
            "the published item's keys have changed since the fixture was "
            "committed. Regenerate tests/fixtures/published_item_needs_review."
            "json from a real poll and tell the session that owns the Desktop "
            "harness, because the item is a contract between two products")
        self.assertEqual(
            normalised(committed), normalised(produced),
            "the published item's values have changed since the fixture was "
            "committed. Everything but receipt_id, pipeline_receipt_id, "
            "capture_date and archive_path must be reproducible")

    def _assert_volatile_fields_are_sound(self, item, label):
        """What `normalised()` drops is asserted here instead.

        Otherwise the comparison above could pass on an item whose id was not an
        id and whose address pointed nowhere in particular.
        """
        self.assertEqual(
            item["receipt_id"], item["pipeline_receipt_id"],
            f"{label}: the two id keys carry one value and always have")
        uuid.UUID(item["receipt_id"])

        parsed = datetime.fromisoformat(item["capture_date"])
        self.assertIsNotNone(
            parsed.tzinfo, f"{label}: capture_date carries its offset")

        self.assertRegex(item["archive_path"], ARCHIVE_PATH_RE,
                         f"{label}: the address is not the archive's shape")
        self.assertIn(
            item["receipt_id"], item["archive_path"],
            f"{label}: the address names the receipt whose document it is")

    def test_the_committed_fixtures_volatile_fields_are_sound(self):
        self._assert_volatile_fields_are_sound(
            json.loads(FIXTURE_PATH.read_text(encoding="utf-8")), "committed")

    def test_a_fresh_polls_volatile_fields_are_sound(self):
        r"""**The half that was missing, and its absence was measured.**

        Added 2026-09-20 after a mutation that dropped the `Intellibills`
        segment from the test environment's derivation was caught by NOTHING:
        the whole suite passed, 1602 tests.

        **The reason is worth keeping, because it is a shape this project has
        named before.** The shape check ran against the COMMITTED fixture only,
        and `normalised()` replaces `archive_path` on both sides of the equality
        check, so a regression in the derivation left the committed file
        matching the pattern and hid the produced value entirely. **A guard over
        a stored artefact is not a guard over the thing that produced it**, and
        this one asserted the file it was meant to be checking against rather
        than the output it was meant to be checking.

        `tests\test_publish_item.py` asserts the live form too and did not catch
        it either, because it builds its own environment and never reaches
        `TempEnvironment`.
        """
        with TempEnvironment():
            produced, _ = publish_one_review_item(self)
        self._assert_volatile_fields_are_sound(produced, "freshly produced")

    def test_the_fixture_is_an_item_the_review_queue_would_hold(self):
        """Not `ok`, or the Desktop harness has nothing to put in the queue."""
        committed = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertNotEqual(committed["validation_status"], "ok")
        self.assertEqual(committed["validation_status"], "needs_review")
        self.assertTrue(
            committed["validation_notes"],
            "a needs_review item says why, and the queue shows it")


@unittest.skipUnless(
    os.environ.get("REGENERATE_REVIEW_FIXTURE"),
    "set REGENERATE_REVIEW_FIXTURE=1 to rewrite the committed fixture")
class RegenerateTheFixture(unittest.TestCase):
    r"""Not a test. The executable form of "regenerate the fixture".

    `REGENERATE_REVIEW_FIXTURE=1 .\.venv\Scripts\python.exe -m pytest
    tests/test_review_seam.py -q`

    **It has to run under pytest and cannot be a script**, because
    `tests\conftest.py` imports `tests\live_paths.py` before anything imports
    `config`, and that is what redirects the two roots into a temp directory. A
    standalone `python tests\test_review_seam.py` would import `config` against
    the LIVE roots, which is `CLAUDE.md`'s fourth trap and would run the mkdir
    block against OneDrive.

    **Skipped by default rather than absent**, so the failure message above can
    name a command that exists. A guard that regenerated the fixture itself
    whenever it differed would be a check that cannot fail.
    """

    def test_write_the_fixture(self):
        with TempEnvironment():
            item, _ = publish_one_review_item(self)
        FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE_PATH.write_text(json.dumps(item, indent=2) + "\n",
                                encoding="utf-8")
        print(f"wrote {FIXTURE_PATH}")


class TheNoteDesktopWritesMatchesTheContractTest(unittest.TestCase):
    """The shape below is checked against the parser, not against a brief.

    **A brief that supplies a fact gets it repeated back**, and then one
    session's error looks like two sessions agreeing. The note in
    `DESKTOP_DISCARD_NOTE` was given to this session as what Desktop wrote on
    Paul's machine on 2026-09-19; what makes it usable is that every key in it
    is one `parse_resolution_note()` reads, enumerated from the syntax tree.
    """

    def test_every_key_in_the_note_is_one_the_parser_reads(self):
        known = keys_the_note_parser_reads()
        self.assertIn("schema", known,
                      "the enumeration found nothing, so it proves nothing")
        unknown = sorted(set(DESKTOP_DISCARD_NOTE) - known)
        self.assertEqual(
            [], unknown,
            f"the note Desktop writes carries keys the pipeline's contract "
            f"does not read: {unknown}. The parser ignores extra keys by "
            f"design, so this would not fail at runtime and would still mean "
            f"the two halves disagree")

    def test_the_note_parses(self):
        note = service.parse_resolution_note(desktop_note_for("r-1"))
        self.assertEqual(note.action, "discarded")
        self.assertEqual(note.resolved_by, "desktop")
        self.assertIn(note.action, service.NOTE_ACTIONS)
        self.assertEqual(DESKTOP_DISCARD_NOTE["schema"], service.NOTE_SCHEMA)


#: The note IntelliBooks Desktop writes when an operator deletes a receipt from
#: the Review queue, read off `Intellibills\Resolutions\` on Paul's machine on
#: 2026-09-19 after a real delete. `receipt_id` is filled in per test, because
#: the whole point of this file is that the receipt is one the pipeline made.
DESKTOP_DISCARD_NOTE = {
    "schema": 1,
    "receipt_id": None,
    "client_id": "Client_004",
    "action": "discarded",
    "resolved_by": "desktop",
    "resolved_at": "2026-09-19T08:48:50.970Z",
    "original_review_files": [None],
}


def desktop_note_for(receipt_id):
    """The live note shape, pointed at a receipt this run actually produced.

    `client_id` is left exactly as Desktop wrote it, `Client_004`, and it does
    not match this fixture's `CLIENT001`. **That is deliberate and it is a
    property of the contract**: `_receipt_for_note()` finds the receipt by
    `receipt_id` and nothing reconciles the note's `client_id` against the row.
    A test that quietly corrected it would hide that.
    """
    note = dict(DESKTOP_DISCARD_NOTE)
    note["receipt_id"] = receipt_id
    note["original_review_files"] = [f"{receipt_id}.json"]
    return note


class TheRoundTripTest(unittest.TestCase):
    """Published by one poll, resolved by Desktop, applied by the next poll.

    One test, because splitting it is what left the seam untested: each half
    passes on its own today.
    """

    def _write_note(self, receipt_id):
        config.RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        path = config.RESOLUTIONS_DIR / f"{receipt_id}_1758268130970.json"
        path.write_text(json.dumps(desktop_note_for(receipt_id), indent=1),
                        encoding="utf-8")
        return path

    def _archived_document(self):
        documents = sorted(p for p in config.FILES_DIR.rglob("*") if p.is_file())
        self.assertEqual(
            len(documents), 1,
            "the poll did not archive exactly one document")
        return documents[0]

    def _events(self, receipt_id):
        repo = Repository()
        try:
            return [dict(r) for r in repo._conn.execute(
                "SELECT * FROM resolution_events WHERE receipt_id = ? "
                "ORDER BY created_at", (receipt_id,))]
        finally:
            repo.close()

    def _receipt(self, receipt_id):
        repo = Repository()
        try:
            return repo.get_receipt(receipt_id)
        finally:
            repo.close()

    def test_a_published_item_is_resolved_and_applied_back_in_one_run(self):
        with TempEnvironment():
            item, receipt = publish_one_review_item(self)
            receipt_id = receipt["receipt_id"]

            # The pipeline's own output is what the other product answered.
            self.assertEqual(item["receipt_id"], receipt_id)
            self.assertEqual(receipt["status"], "needs_review")
            self.assertEqual(
                [r["outcome"] for r in self._publish_rows()],
                [publish.PUBLISHED])

            document = self._archived_document()
            bytes_before = document.read_bytes()

            note_path = self._write_note(receipt_id)

            # The second poll. A real process_once() with an empty mailbox, so
            # the consumer runs in the live order and nothing is extracted.
            run_pipeline_once(RecordingExtractor(
                RuntimeError("the second poll must not extract anything")))

            # 1. What it did to the receipt.
            after = self._receipt(receipt_id)
            self.assertEqual(
                after["status"], "discarded",
                "the note did not reach the receipt, so the seam is open")
            self.assertIsNone(
                after["filed_path"],
                "a discarded receipt is not filed, whatever became of the file")

            events = self._events(receipt_id)
            self.assertEqual([e["action"] for e in events], ["discard"])
            # The back-feed's own call site passes these two, so the pair is
            # what says the note took the Desktop path rather than the CLI.
            # Asserted against the constants, because the row would read the
            # same whatever they were renamed to.
            self.assertEqual(events[0]["actor"], service.DESKTOP_ACTOR)
            self.assertEqual(events[0]["source"], service.DESKTOP_SOURCE)
            # The note's own timestamp is the idempotency key, and it goes in
            # `corrections_json` because the table has no column for it.
            blob = json.loads(events[0]["corrections_json"])
            self.assertEqual(
                blob[service.NOTE_RESOLVED_AT_KEY],
                DESKTOP_DISCARD_NOTE["resolved_at"],
                "the audit row carries the note's own timestamp, which is what "
                "a replay of the same note is checked against")

            # 2. What it did to the note file.
            self.assertFalse(
                note_path.exists(),
                "an applied note is moved out of the folder it was read from")
            self.assertEqual(
                sorted(p.name for p in
                       (config.RESOLUTIONS_DIR / "processed").iterdir()),
                [note_path.name],
                "an applied note goes to processed\\, not to failed\\")
            self.assertFalse(
                (config.RESOLUTIONS_DIR / "failed").exists(),
                "nothing failed, so the failed folder was never made")

            # 3. What it did to the document in the archive: nothing.
            self.assertTrue(
                document.is_file(),
                "discard_receipt() says the original file in the document "
                "store is never deleted on any path")
            self.assertEqual(
                document.read_bytes(), bytes_before,
                "the archived document is the archive of record and is never "
                "changed once written")

            # And no second extraction was appended by the discard.
            repo = Repository()
            try:
                extractions = [dict(r) for r in repo._conn.execute(
                    "SELECT * FROM extractions WHERE receipt_id = ?",
                    (receipt_id,))]
            finally:
                repo.close()
            self.assertEqual(
                len(extractions), 1,
                "a discard writes no extraction row")

    def _publish_rows(self):
        repo = Repository()
        try:
            return [dict(r) for r in repo._conn.execute(
                "SELECT * FROM publish_events ORDER BY created_at")]
        finally:
            repo.close()


class TheArchiveSurvivesADiscardTest(unittest.TestCase):
    """`discard_receipt()`'s first line of docstring, given a test.

    The round trip above asserts it on the back-feed path. This asserts it on
    the path the docstring is actually about: **any** caller, including one
    that asks for the client folder copy to be deleted, which is the only flag
    that deletes anything at all.
    """

    def _discard(self, receipt_id, **kwargs):
        repo = Repository()
        try:
            return service.discard_receipt(
                repo, receipt_id, reason="not resolvable",
                actor="test", source="cli", **kwargs)
        finally:
            repo.close()

    def test_the_document_is_untouched_by_a_plain_discard(self):
        with TempEnvironment():
            _, receipt = publish_one_review_item(self)
            document = next(p for p in config.FILES_DIR.rglob("*") if p.is_file())
            before = document.read_bytes()

            outcome = self._discard(receipt["receipt_id"])

            self.assertEqual(outcome.outcome, "discarded")
            self.assertTrue(document.is_file())
            self.assertEqual(document.read_bytes(), before)

    def test_the_document_is_untouched_when_the_client_copy_is_asked_for_too(self):
        """The one flag that deletes a file still does not reach the archive."""
        with TempEnvironment():
            _, receipt = publish_one_review_item(self)
            document = next(p for p in config.FILES_DIR.rglob("*") if p.is_file())
            before = document.read_bytes()

            outcome = self._discard(receipt["receipt_id"],
                                    delete_client_copy=True)

            self.assertEqual(outcome.outcome, "discarded")
            self.assertTrue(
                document.is_file(),
                "delete_client_copy deletes the copy in the client folder and "
                "never the archive")
            self.assertEqual(document.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

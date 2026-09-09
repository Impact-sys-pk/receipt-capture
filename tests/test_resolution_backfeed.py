"""Design document 12: the resolution back-feed contract. Tests 22 to 28.

This is one half of a two-sided contract. IntelliBooks Desktop writes a note into
`Resolutions\\`; the pipeline reads it and writes the database. Desktop still never
writes `receipts.db`, which keeps the letter of the Phase 1 rule intact, and the
pipeline stops being blind to what a human decided in Desktop.

**The assertion that matters is that the image is not filed a second time.** For a
`filed` note the file is already at `filed_path`, put there by Desktop, so
`apply_resolution_note()` records the filing with `mark_receipt_filed()` and must
never call `file_receipt()`. Getting that wrong means every Desktop resolution
leaves a second copy on disk under a `-2` name, which is the exact bug this
contract exists to prevent. Every filed-note test therefore counts the files in the
target folder before and after.

The other rule with no exceptions: **nothing in `Resolutions\\` is ever deleted.**
A failure moves the note to `failed\\` with a `.error.txt` beside it, so a note that
the pipeline could not apply is still on disk and still readable.

## Two shapes of `filed` note since 2026-09-09, and the field decides

**Sub-step 10f.14 and Paul's decision of 2026-09-09.** A note that carries
`filed_path` still means "Desktop filed this at that path", and everything above
about the second copy applies to it unchanged. **A note with no `filed_path`
means "these are the corrected values, settle this receipt"**, and it goes
through `resolve_receipt()`, which writes the client folder copy itself on the
firm's trigger.

**That second shape used to be refused, and the refusal was a live fault**:
receipt `a587b166-35a1-473c-aa5a-409749f7b642` was in the books in Desktop and
`status failed` in the database with no `resolution_events` row.
`NoteWithNoFiledPathSettlesTest` and `TheTwoShapesTakeDifferentPathsTest` hold
the new half; `ValidFiledNoteTest` still holds the old one.
"""

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
    TempEnvironment,
    rows,
    run_pipeline_once,
)
from worker import client_copy  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.filing import _review_dir_for_client_id  # noqa: E402
from worker.resolution.service import apply_resolution_note  # noqa: E402

import app  # noqa: E402

# The one string both products must agree on, per amendment 170: the IntelliBooks
# parent sits between the client folder and Receipts. IntelliBooks-Desktop-v3.html
# writes this and resolve_practice_path() reads it.
FILED_RELATIVE = (
    r"Clients\Test Client\IntelliBooks\Receipts\2026-27"
    r"\2026-04-01_apcoa-parking_96.00.pdf"
)


def note_payload(**overrides):
    """The note shape in 12.2, verbatim, including the real-world details.

    Amounts are JSON numbers and arrive as integers where they are whole, because
    JavaScript drops the trailing `.0`. `category_name` is a name, not a code:
    Desktop has no codes.
    """
    payload = {
        "schema": 1,
        "receipt_id": "r-1",
        "client_id": "CLIENT001",
        "action": "filed",
        "resolved_by": "desktop",
        "resolved_at": "2026-07-25T14:02:11.000Z",
        "values": {
            "supplier_name": "Apcoa Parking",
            "invoice_date": "2026-04-01",
            "net_amount": 80,
            "vat_amount": 16,
            "gross_amount": 96,
            "currency": "GBP",
            "category_name": "Parking and tolls",
        },
        "filed_path": FILED_RELATIVE,
        "original_review_files": ["r-1.pdf", "r-1.pdf.review.json"],
    }
    payload.update(overrides)
    return payload


def settle_payload(**overrides):
    """The shape Desktop writes SINCE 2026-09-09: no `filed_path`.

    Sub-step 10f.14 and amendment 296. `fileReviewReceipt()` stopped writing
    into `Clients\\` and stopped naming a path, because the pipeline is the only
    writer there and the firm's `client_copy_trigger` decides whether a copy
    happens at all. **Everything else is `note_payload()`'s shape**, so the two
    differ in exactly the field the pipeline chooses on.

    `original_review_files` is the inbox item now rather than a review pair, per
    the Desktop comment at `fileReviewReceipt()`, so it is written that way here.
    """
    payload = {k: v for k, v in note_payload().items() if k != "filed_path"}
    payload["original_review_files"] = ["r-1.json"]
    payload.update(overrides)
    return payload


#: The note that failed on Paul's machine at 17:16:48 on 2026-09-09, verbatim.
#:
#: Read from `Intellibills\Resolutions\failed\`. Kept as text rather than as a
#: dict so nobody tidies it: `net_amount` and `vat_amount` are both null, the
#: category is a four-digit code with its name beside it, and
#: `original_review_files` names the published inbox item. `receipt_id` and
#: `client_id` are replaced by the test, because `TempEnvironment` knows one
#: client and it is not `Client_004`.
LIVE_NOTE = (
    '{"schema":1,"receipt_id":"a587b166-35a1-473c-aa5a-409749f7b642",'
    '"client_id":"Client_004","action":"filed","resolved_by":"desktop",'
    '"resolved_at":"2026-09-09T16:14:23.045Z","values":{'
    '"supplier_name":"LA BELLA RESTAURANT","invoice_date":"2025-06-04",'
    '"net_amount":null,"vat_amount":null,"gross_amount":27.5,"currency":"GBP",'
    '"category_code":"7406","category_name":"Subsistence"},'
    '"remember_gl_for_supplier":false,'
    '"original_review_files":["a587b166-35a1-473c-aa5a-409749f7b642.json"]}'
)


#: The repository root, for the tests that read a production file's own source.
REPO_ROOT = Path(__file__).resolve().parent.parent


class Capture(logging.Handler):
    """Collect records off one logger. A third copy, and four lines.

    `tests/test_stage4_client_copy.py` and `tests/test_client_copy_collision.py`
    each carry one, for the reason `trigger()` below carries: importing a test
    module from a test module makes the import order decide whether a fixture is
    in place.
    """

    def __init__(self):
        super().__init__(level=logging.INFO)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def messages(self, level=None):
        return [r.getMessage() for r in self.records
                if level is None or r.levelno == level]


@contextmanager
def captured(name, level=logging.INFO):
    logger = logging.getLogger(name)
    handler = Capture()
    saved_level, saved_propagate = logger.level, logger.propagate
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(saved_level)
        logger.propagate = saved_propagate


@contextmanager
def trigger(value):
    """Set the firm's client copy trigger for one test, and put it back.

    A third copy of `tests/test_stage4_client_copy.py`'s helper, and four lines
    for the reason recorded there: importing a test module from a test module
    makes the import order decide whether a fixture is in place.
    """
    saved = config.CLIENT_COPY_TRIGGER
    config.CLIENT_COPY_TRIGGER = value
    try:
        yield
    finally:
        config.CLIENT_COPY_TRIGGER = saved


class BackfeedTestCase(unittest.TestCase):
    """Shared setup: a receipt Desktop has already filed, and the note for it."""

    def seed_desktop_filed(self, env, receipt_id="r-1", status="needs_review",
                           relative=FILED_RELATIVE, write_file=True, **extraction):
        """The state Desktop leaves behind.

        The image is at filed_path with a sidecar Desktop wrote. The Review pair is
        gone, because Desktop removes it itself, per the 12.4 amendment. The
        database still says needs_review and filed_path is still NULL, because
        Desktop never writes the database.
        """
        repo = Repository()
        try:
            env.seed(repo, receipt_id=receipt_id, status=status, **extraction)
        finally:
            repo.close()

        target = config.PRACTICE_ROOT / Path(relative.replace("\\", "/"))
        if write_file:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("the copy Desktop filed", encoding="utf-8")
            target.with_suffix(target.suffix + ".json").write_text(
                json.dumps({"receipt_id": receipt_id, "corrected_by": "desktop"}),
                encoding="utf-8",
            )
        return target

    def write_note(self, payload, name=None):
        config.RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        receipt_id = payload.get("receipt_id") if isinstance(payload, dict) else "unparseable"
        path = config.RESOLUTIONS_DIR / (name or f"{receipt_id}_1753452131000.json")
        if isinstance(payload, (dict, list)):
            path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        else:
            path.write_text(str(payload), encoding="utf-8")
        return path

    def seed_awaiting_settlement(self, env, receipt_id="r-1", status="failed",
                                 **extraction):
        """The state Desktop leaves behind NOW: nothing on disk, nothing filed.

        Contrast `seed_desktop_filed()` above, which writes the image into
        `Clients\\` because Desktop used to put it there. Desktop removes the
        inbox item and writes the note, and that is all.

        `status` defaults to `failed` rather than `needs_review`, because that is
        the live receipt's status: its only extraction had no gross amount, which
        is exactly the case an operator settles by typing one in.
        """
        repo = Repository()
        try:
            return env.seed(repo, receipt_id=receipt_id, status=status, **extraction)
        finally:
            repo.close()

    def client_receipts_dir(self, tax_year="2025-26"):
        """`2025-26`, and it is computed rather than eyeballed.

        The UK tax year starts on 6 April, so the note's `2026-04-01` falls in
        2025-26. `FILED_RELATIVE` above says `2026-27` and is not wrong: that is
        a path Desktop composed and this fixture writes verbatim, never a value
        `determine_tax_year()` produced. The settle path computes it, so the two
        legitimately differ.
        """
        return (config.CLIENTS_ROOT / "Test Client" /
                config.CLIENT_INTELLIBOOKS_FOLDER_NAME /
                config.CLIENT_RECEIPTS_FOLDER_NAME / tax_year)

    def everything_under_clients(self):
        root = config.CLIENTS_ROOT
        if not root.exists():
            return []
        return sorted(p.relative_to(root).as_posix()
                      for p in root.rglob("*") if p.is_file())

    def receipt(self, receipt_id="r-1"):
        repo = Repository()
        try:
            return repo.get_receipt(receipt_id)
        finally:
            repo.close()

    def folder_listing(self, path: Path):
        return sorted(p.name for p in path.iterdir()) if path.is_dir() else []

    def note_names(self, subfolder=None):
        base = config.RESOLUTIONS_DIR if subfolder is None else config.RESOLUTIONS_DIR / subfolder
        if not base.is_dir():
            return []
        return sorted(p.name for p in base.iterdir() if p.is_file())


def env_engine(repo):
    from worker.categorisation.engine import CategorisationEngine

    return CategorisationEngine(repo=repo, enable_ai_fallback=False)


def consume_notes():
    """Drive the pipeline's consumer with a fresh Repository, as a poll would."""
    repo = Repository()
    try:
        stats = {}
        app._consume_resolution_notes(repo, env_engine(repo), stats)
        return stats
    finally:
        repo.close()


class ValidFiledNoteTest(BackfeedTestCase):
    """Test 22."""

    def test_it_updates_the_database_and_does_not_file_a_second_copy(self):
        with TempEnvironment() as env:
            target = self.seed_desktop_filed(env)
            before = self.folder_listing(target.parent)
            note = self.write_note(note_payload())

            stats = consume_notes()

            self.assertEqual(stats.get("notes_applied"), 1)
            self.assertEqual(
                self.folder_listing(target.parent), before,
                "THE BUG THIS CONTRACT EXISTS TO PREVENT: a second copy on disk",
            )

            repo = Repository()
            try:
                receipt = repo.get_receipt("r-1")
                self.assertEqual(receipt["status"], "ok")
                self.assertEqual(receipt["filed_path"], str(target))
                self.assertIsNotNone(receipt["filed_at"])
                self.assertIsNone(receipt["locked_at"], "the lock is released")

                manual = rows(
                    repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'"
                )
                self.assertEqual(len(manual), 1)
                self.assertEqual(manual[0]["supplier_name"], "Apcoa Parking")
                self.assertEqual(manual[0]["gross_amount"], 96.00)
                self.assertEqual(manual[0]["validation_status"], "ok")

                events = rows(repo, "SELECT * FROM resolution_events")
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["actor"], "desktop")
                self.assertEqual(events[0]["source"], "desktop")
                self.assertEqual(events[0]["outcome"], "filed")

                seed = rows(repo, "SELECT * FROM extractions WHERE engine = 'openai_vision'")
                self.assertEqual(len(seed), 1, "append-only: the seed row is untouched")
            finally:
                repo.close()

            self.assertFalse(note.exists(), "the note moved")
            self.assertEqual(self.note_names("processed"), [note.name])
            self.assertEqual(self.note_names("failed"), [])

    def test_whole_number_amounts_are_stored_as_money(self):
        # Desktop sends "net": 80 because JSON.stringify drops the trailing .0.
        # Ruled by Paul 2026-07-28: round to two decimal places on ingest.
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            self.write_note(note_payload())
            consume_notes()

            repo = Repository()
            try:
                manual = rows(
                    repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'"
                )[0]
                self.assertEqual(
                    (manual["net_amount"], manual["vat_amount"], manual["gross_amount"]),
                    (80.00, 16.00, 96.00),
                )
            finally:
                repo.close()

    def test_a_third_decimal_place_is_rounded_rather_than_stored(self):
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            values = dict(note_payload()["values"])
            values.update({"net_amount": 79.999, "vat_amount": 16.001, "gross_amount": 96.004})
            self.write_note(note_payload(values=values))
            consume_notes()

            repo = Repository()
            try:
                manual = rows(
                    repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'"
                )[0]
                self.assertEqual(
                    (manual["net_amount"], manual["vat_amount"], manual["gross_amount"]),
                    (80.00, 16.00, 96.00),
                )
            finally:
                repo.close()

    def test_a_receipt_with_no_extraction_at_all_can_still_be_applied(self):
        # 4.2 as amended: a receipt can exist with no extraction, and the read side
        # does not decide policy. The note carries every value it needs.
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            repo = Repository()
            try:
                repo._conn.execute("DELETE FROM extractions WHERE receipt_id = 'r-1'")
                repo._conn.commit()
            finally:
                repo.close()

            self.write_note(note_payload())
            consume_notes()

            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "ok")
                self.assertEqual(len(rows(repo, "SELECT * FROM extractions")), 1)
            finally:
                repo.close()

    def test_a_review_pair_that_desktop_already_deleted_is_not_a_failure(self):
        """The 12.4 amendment: Desktop removes the pair itself, so
        remove_review_pair() finds nothing. Zero is not an error.

        **The precondition below was a check that could not fail until
        2026-09-07.** It read
        `config.CLIENTS_ROOT / "Test Client" / "Review"`, which is where Review
        sat before sub-step 10d.54 moved it to `REVIEW_ROOT / client_id`.
        Nothing has written that path since, so the assertion was true whatever
        the code did. Proved by creating a real review folder for CLIENT001 and
        watching the old line stay green.

        The folder is derived through `_review_dir_for_client_id()` rather than
        composed here, so if the Review layout moves again this test moves with
        it instead of going quiet. `tests/test_step10d_pipeline.py` already
        imports the same helper for the same reason.
        """
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            review_dir = _review_dir_for_client_id("CLIENT001")
            self.assertFalse(review_dir.exists())

            self.write_note(note_payload())
            stats = consume_notes()

            self.assertEqual(stats.get("notes_applied"), 1)
            self.assertEqual(self.note_names("failed"), [])


class IdempotencyTest(BackfeedTestCase):
    """Test 23."""

    def test_applying_the_same_note_twice_changes_nothing_the_second_time(self):
        with TempEnvironment() as env:
            target = self.seed_desktop_filed(env)
            before = self.folder_listing(target.parent)

            first = self.write_note(note_payload())
            consume_notes()
            second = self.write_note(note_payload(), name=first.name)
            stats = consume_notes()

            self.assertEqual(stats.get("notes_applied"), 1)
            repo = Repository()
            try:
                self.assertEqual(
                    len(rows(repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'")),
                    1, "one extraction row, not two",
                )
                self.assertEqual(
                    len(rows(repo, "SELECT * FROM resolution_events")), 1,
                    "one event row, not two",
                )
            finally:
                repo.close()

            self.assertEqual(self.folder_listing(target.parent), before)
            self.assertEqual(self.note_names("failed"), [])
            self.assertEqual(len(self.note_names("processed")), 2,
                             "both copies of the note are kept, neither is deleted")

    def test_a_later_note_for_the_same_receipt_is_not_mistaken_for_a_repeat(self):
        # Idempotency keys on the note's own resolved_at, not on the receipt.
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            self.write_note(note_payload())
            consume_notes()

            later = note_payload(resolved_at="2026-07-26T09:00:00.000Z", action="discarded")
            later.pop("values")
            later.pop("filed_path")
            self.write_note(later, name="r-1_1753539000000.json")
            consume_notes()

            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "discarded")
                self.assertEqual(len(rows(repo, "SELECT * FROM resolution_events")), 2)
            finally:
                repo.close()


class MalformedNoteTest(BackfeedTestCase):
    """Test 24."""

    def _assert_failed_and_kept(self, note):
        self.assertFalse(note.exists(), "moved out of the queue")
        self.assertEqual(self.note_names("processed"), [])
        failed = self.note_names("failed")
        self.assertIn(note.name, failed, "never deleted")
        self.assertIn(note.name + ".error.txt", failed, "with the reason beside it")
        error_text = (config.RESOLUTIONS_DIR / "failed" / (note.name + ".error.txt")).read_text(
            encoding="utf-8"
        )
        self.assertTrue(error_text.strip(), "the error file says something")

    def test_unparseable_json_moves_to_failed_and_is_not_deleted(self):
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            note = self.write_note("{not json at all", name="r-1_1753452131000.json")

            stats = consume_notes()

            self.assertEqual(stats.get("notes_failed"), 1)
            self._assert_failed_and_kept(note)
            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "needs_review")
                self.assertEqual(rows(repo, "SELECT * FROM resolution_events"), [])
            finally:
                repo.close()

    def test_every_shape_the_contract_forbids_moves_to_failed(self):
        cases = {
            "unknown schema": note_payload(schema=2),
            "no action": {k: v for k, v in note_payload().items() if k != "action"},
            "unknown action": note_payload(action="filedish"),
            "no resolved_at": {
                k: v for k, v in note_payload().items() if k != "resolved_at"
            },
            # ~~"filed with no filed_path"~~ **Removed 2026-09-09 by sub-step
            # 10f.14.** That shape is what Desktop writes now and is legal: it
            # means "settle this receipt" and goes through resolve_receipt().
            # `NoteWithNoFiledPathSettlesTest` holds it. **This case was the
            # live fault asserted as correct**, which is why it is struck here
            # rather than deleted quietly.
            "filed with no values": {
                k: v for k, v in note_payload().items() if k != "values"
            },
            "amount as a string": note_payload(
                values=dict(note_payload()["values"], gross_amount="96.00")
            ),
            "amount as a boolean": note_payload(
                values=dict(note_payload()["values"], gross_amount=True)
            ),
            "no gross amount": note_payload(
                values={
                    k: v for k, v in note_payload()["values"].items() if k != "gross_amount"
                }
            ),
            "no supplier": note_payload(
                values={
                    k: v for k, v in note_payload()["values"].items() if k != "supplier_name"
                }
            ),
            "date in the wrong format": note_payload(
                values=dict(note_payload()["values"], invoice_date="25/12/2026")
            ),
            "not an object": ["a", "list"],
        }
        for label, payload in cases.items():
            with self.subTest(case=label):
                with TempEnvironment() as env:
                    self.seed_desktop_filed(env)
                    note = self.write_note(payload)

                    consume_notes()

                    self._assert_failed_and_kept(note)
                    repo = Repository()
                    try:
                        self.assertEqual(repo.get_receipt("r-1")["status"], "needs_review")
                    finally:
                        repo.close()

    def test_a_filed_path_that_is_not_on_disk_moves_to_failed(self):
        # Desktop writes the file before the note, so this should not happen. The
        # pipeline is trusting another application's output, and a database row
        # pointing at nothing is worse than a note in failed\.
        with TempEnvironment() as env:
            self.seed_desktop_filed(env, write_file=False)
            note = self.write_note(note_payload())

            consume_notes()

            self._assert_failed_and_kept(note)
            repo = Repository()
            try:
                receipt = repo.get_receipt("r-1")
                self.assertIsNone(receipt["filed_path"])
                self.assertEqual(receipt["status"], "needs_review")
            finally:
                repo.close()


class UnknownReceiptTest(BackfeedTestCase):
    """Test 25."""

    def test_a_note_for_a_receipt_that_does_not_exist_moves_to_failed(self):
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            note = self.write_note(
                note_payload(receipt_id="no-such-receipt", original_review_files=[]),
                name="no-such-receipt_1753452131000.json",
            )

            consume_notes()

            self.assertIn(note.name, self.note_names("failed"))
            self.assertEqual(self.note_names("processed"), [])

    def test_a_null_receipt_id_is_matched_on_the_review_filenames(self):
        # 12.2: receipt_id may be null if the review sidecar lacked one, and then
        # original_review_files is used for a filename match.
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            note = self.write_note(
                note_payload(
                    receipt_id=None,
                    original_review_files=["R-1.PDF", "R-1.PDF.review.json"],
                ),
                name="null_1753452131000.json",
            )

            consume_notes()

            self.assertIn(note.name, self.note_names("processed"),
                          "matched case-insensitively: the two tools case names differently")
            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "ok")
            finally:
                repo.close()

    def test_an_ambiguous_filename_match_is_not_a_match(self):
        with TempEnvironment() as env:
            self.seed_desktop_filed(env, receipt_id="r-1")
            repo = Repository()
            try:
                # A second receipt with the same original filename.
                env.seed(repo, receipt_id="r-2")
                repo._conn.execute("UPDATE receipts SET filename = 'r-1.pdf' WHERE receipt_id = 'r-2'")
                repo._conn.commit()
            finally:
                repo.close()

            note = self.write_note(
                note_payload(receipt_id=None), name="null_1753452131000.json"
            )

            consume_notes()

            self.assertIn(note.name, self.note_names("failed"))


class CategoryLookupTest(BackfeedTestCase):
    """Test 26. Until the Default CoA is loaded at step 12 this is every note."""

    def test_a_name_with_no_chart_of_accounts_stores_the_name_and_learns_nothing(self):
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            self.write_note(note_payload())

            consume_notes()

            repo = Repository()
            try:
                categorisation = repo.get_categorisation_for_receipt("r-1")
                self.assertIsNotNone(categorisation)
                self.assertEqual(categorisation["correction_name"], "Parking and tolls",
                                 "the name is kept even though there is no code for it")
                self.assertIsNone(categorisation["correction_code"])

                self.assertEqual(
                    rows(repo, "SELECT * FROM categorisations_client_vendors"), [],
                    "no vendor learning without a code",
                )

                manual = rows(
                    repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'"
                )[0]
                self.assertIn("Parking and tolls", manual["validation_notes"])
                self.assertIn("chart of accounts", manual["validation_notes"].lower())
                self.assertEqual(manual["validation_status"], "ok",
                                 "expected and not an error, per 12.3 step 6")
            finally:
                repo.close()

    def test_a_blank_category_is_not_looked_up_and_not_stored_as_a_name(self):
        # Desktop does not require a category before filing, so "" is the common
        # case, per the 12.4 amendment of 2026-07-28.
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            values = dict(note_payload()["values"], category_name="")
            self.write_note(note_payload(values=values))

            consume_notes()

            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "ok")
                categorisation = repo.get_categorisation_for_receipt("r-1")
                self.assertIsNone(categorisation["correction_name"])
                self.assertIsNone(categorisation["correction_code"])
                manual = rows(
                    repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'"
                )[0]
                self.assertNotIn("chart of accounts", (manual["validation_notes"] or "").lower())
            finally:
                repo.close()


class DiscardedNoteTest(BackfeedTestCase):
    """Test 27."""

    def test_a_discarded_note_sets_the_status_and_deletes_no_files(self):
        with TempEnvironment() as env:
            target = self.seed_desktop_filed(env)
            original = Path(self.receipt()["file_path"])
            payload = note_payload(action="discarded")
            payload.pop("values")
            payload.pop("filed_path")
            note = self.write_note(payload)

            stats = consume_notes()

            self.assertEqual(stats.get("notes_applied"), 1)
            repo = Repository()
            try:
                receipt = repo.get_receipt("r-1")
                self.assertEqual(receipt["status"], "discarded")
                self.assertIsNone(receipt["filed_path"])
                event = rows(repo, "SELECT * FROM resolution_events")[0]
                self.assertEqual(event["action"], "discard")
                self.assertEqual(event["actor"], "desktop")
                self.assertEqual(event["source"], "desktop")
                self.assertIsNotNone(event["reason"])
                self.assertEqual(len(rows(repo, "SELECT * FROM extractions")), 1,
                                 "a discard writes no extraction row")
            finally:
                repo.close()

            self.assertTrue(original.exists(), "no file is ever deleted")
            self.assertTrue(target.exists())
            self.assertIn(note.name, self.note_names("processed"))


class ConsumerRunsFirstTest(BackfeedTestCase):
    """Test 28, driven through a real process_once()."""

    def test_a_receipt_resolved_by_note_is_not_retried_in_the_same_cycle(self):
        with TempEnvironment() as env:
            # An old pipeline_version, so this receipt IS auto-retry eligible.
            # Whether it gets retried is decided purely by the order of the two
            # steps inside process_once().
            self.seed_desktop_filed(env, pipeline_version="an-older-version")
            self.write_note(note_payload())

            extractor = RecordingExtractor(RuntimeError("the retry must never happen"))
            run_pipeline_once(extractor)

            self.assertEqual(
                extractor.calls, 0,
                "THE MONEY BUG: the note was applied after the retry, so the receipt "
                "was re-extracted in the same cycle it was resolved",
            )
            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "ok")
                self.assertEqual(
                    len(rows(repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'")),
                    1,
                )
            finally:
                repo.close()
            self.assertEqual(len(self.note_names("processed")), 1)

    def test_an_empty_folder_is_a_no_op(self):
        with TempEnvironment() as env:
            self.seed_desktop_filed(env, pipeline_version="test-version")
            self.assertFalse(config.RESOLUTIONS_DIR.exists())

            extractor = RecordingExtractor(RuntimeError("nothing should be extracted"))
            run_pipeline_once(extractor)

            self.assertEqual(self.note_names(), [])
            self.assertFalse((config.RESOLUTIONS_DIR / "failed").exists())
            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "needs_review")
            finally:
                repo.close()

    def test_notes_are_applied_oldest_first(self):
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            # Two notes for the same receipt: file it, then discard it. Applied in
            # filename order the receipt ends discarded; in reverse order it ends
            # ok, which is why the order is part of the contract.
            self.write_note(note_payload(), name="r-1_1753452131000.json")
            discard = note_payload(action="discarded", resolved_at="2026-07-26T09:00:00.000Z")
            discard.pop("values")
            discard.pop("filed_path")
            self.write_note(discard, name="r-1_1753539000000.json")

            consume_notes()

            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "discarded")
            finally:
                repo.close()


class NeverDeleteTest(BackfeedTestCase):
    """The rule with no exceptions."""

    def test_every_note_written_is_still_on_disk_afterwards(self):
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            written = {
                self.write_note(note_payload(), name="r-1_1.json").name,
                self.write_note("not json", name="r-1_2.json").name,
                self.write_note(
                    note_payload(receipt_id="nope", original_review_files=[]), name="r-1_3.json"
                ).name,
            }

            consume_notes()

            surviving = set(self.note_names()) | set(self.note_names("processed")) | {
                n for n in self.note_names("failed") if not n.endswith(".error.txt")
            }
            self.assertEqual(surviving, written)

    def test_a_second_note_of_the_same_name_does_not_overwrite_the_first(self):
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            self.write_note("not json", name="clash.json")
            consume_notes()
            self.write_note("also not json", name="clash.json")
            consume_notes()

            failed = [n for n in self.note_names("failed") if not n.endswith(".error.txt")]
            self.assertEqual(len(failed), 2, failed)


class NoteWithNoFiledPathSettlesTest(BackfeedTestCase):
    """Sub-step 10f.14 finished, and it began as a live fault.

    **What happened.** Amendment 299 stopped `fileReviewReceipt()` writing into
    `Clients\\` and removed `filed_path` from the note, correctly: the pipeline
    is the only writer there and its `client_copy_trigger` decides whether a
    copy happens at all. **The other half of the contract still refused a
    `filed` note without that field**, so on 2026-09-09 at 17:16:48 receipt
    `a587b166-35a1-473c-aa5a-409749f7b642` sat at `status failed` with no
    `resolution_events` row while being in the books in Desktop as LA BELLA
    RESTAURANT, GBP 27.50. That is the disagreement between the database and the
    books that section 12 exists to prevent.

    **What the note means now.** Paul's decision of 2026-09-09: not "Desktop
    filed this" but "these are the corrected values, settle this receipt". So a
    note with no `filed_path` goes through `resolve_receipt()`, the same path
    the console and the CLI use, which applies the corrections, re-validates,
    categorises, calls the one gated client folder copy on the firm's trigger,
    sets the receipt to `ok` and records the event.

    **Desktop's own comment already said so**, read in
    `IntelliBooks-Desktop-v3.html` on 2026-09-09: "The copy still happens: the
    resolution note below reaches the pipeline, `resolve_receipt()` applies the
    corrections and calls the client copy on the firm's own trigger". The two
    halves were built by sessions that cannot see each other and one of them was
    written against a pipeline that did not exist yet.

    **A note that DOES carry `filed_path` is unchanged**, held by
    `ValidFiledNoteTest` above and by `TheTwoShapesTakeDifferentPathsTest` below.
    """

    def test_the_receipt_is_settled_and_the_note_is_processed(self):
        """The live fault, driven through a real `_consume_resolution_notes()`.

        The three assertions that were false on Paul's machine: `ok`, a
        `resolution_events` row, and the note out of the queue rather than in
        `failed\\`.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            note = self.write_note(settle_payload())

            stats = consume_notes()

            self.assertEqual(stats.get("notes_applied"), 1,
                             f"the note was not applied: {stats}")
            self.assertEqual(self.note_names("failed"), [])
            self.assertIn(note.name, self.note_names("processed"))

            repo = Repository()
            try:
                receipt = repo.get_receipt("r-1")
                self.assertEqual(receipt["status"], "ok")
                self.assertIsNone(receipt["locked_at"], "the lock is released")

                events = rows(repo, "SELECT * FROM resolution_events")
                self.assertEqual(len(events), 1, events)
                self.assertEqual(events[0]["actor"], "desktop")
                self.assertEqual(events[0]["source"], "desktop")
                self.assertEqual(events[0]["action"], "resolve")
                self.assertEqual(events[0]["outcome"], "filed")

                manual = rows(
                    repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'")
                self.assertEqual(len(manual), 1)
                self.assertEqual(manual[0]["supplier_name"], "Apcoa Parking")
                self.assertEqual(manual[0]["gross_amount"], 96.00)
                self.assertEqual(manual[0]["validation_status"], "ok")
            finally:
                repo.close()

    def test_the_original_extraction_is_kept_because_extractions_are_append_only(self):
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            self.write_note(settle_payload())
            consume_notes()
            repo = Repository()
            try:
                engines = [r["engine"] for r in rows(
                    repo, "SELECT engine FROM extractions WHERE receipt_id = 'r-1' "
                          "ORDER BY extracted_at")]
                self.assertEqual(engines, ["openai_vision", "manual_correction"])
            finally:
                repo.close()

    def test_the_client_folder_copy_is_written_on_the_publish_trigger(self):
        """The copy Desktop stopped writing, written by the one gated function.

        Named from the note's own values, which is 18.2b's convention, and
        recorded in `filed_path`. **One file, not two**: the same count the
        Desktop-filed tests make, for the same reason.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            self.assertEqual(self.everything_under_clients(), [],
                             "the fixture pre-filed something")
            self.write_note(settle_payload())

            consume_notes()

            self.assertEqual(
                self.everything_under_clients(),
                ["Test Client/IntelliBooks/Receipts/2025-26/"
                 "2026-04-01_apcoa-parking_96.00.pdf"])
            repo = Repository()
            try:
                receipt = repo.get_receipt("r-1")
                self.assertEqual(
                    receipt["filed_path"],
                    str(self.client_receipts_dir() /
                        "2026-04-01_apcoa-parking_96.00.pdf"))
                self.assertIsNotNone(receipt["filed_at"])
            finally:
                repo.close()

    def test_no_sidecar_lands_beside_it(self):
        """18.2b: image only. Amendment 296 is why it matters.

        `scanFiledReceipts()` pairs an image with a sidecar on the full
        filename, so a sidecar here becomes a books row with a gross of nought.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            self.write_note(settle_payload())
            consume_notes()
            self.assertEqual(
                [f for f in self.everything_under_clients() if f.endswith(".json")],
                [])

    def test_every_trigger_settles_the_receipt(self):
        """The brief's own requirement, and `post` is here as well as `never`.

        On `never` and on `post` no copy is written and the receipt must still
        reach `ok`: the settling is the database's business and the copy is the
        firm's setting, and conflating them is what put a receipt in the books
        and not in the database.
        """
        for value in ("publish", "post", "never"):
            with self.subTest(trigger=value):
                with TempEnvironment() as env, trigger(value):
                    client_copy._reset_post_warning()
                    self.seed_awaiting_settlement(env)
                    self.write_note(settle_payload())

                    stats = consume_notes()

                    self.assertEqual(stats.get("notes_applied"), 1, stats)
                    repo = Repository()
                    try:
                        receipt = repo.get_receipt("r-1")
                        self.assertEqual(receipt["status"], "ok")
                        self.assertEqual(
                            len(rows(repo, "SELECT * FROM resolution_events")), 1)
                    finally:
                        repo.close()
                    if value == "publish":
                        self.assertEqual(len(self.everything_under_clients()), 1)
                        self.assertIsNotNone(receipt["filed_path"])
                    else:
                        self.assertEqual(self.everything_under_clients(), [])
                        self.assertIsNone(receipt["filed_path"])

    def test_the_notes_category_wins_and_the_engines_suggestion_is_kept(self):
        """A decision the brief left open: both, exactly as today.

        The engine re-categorises for the audit trail and its suggestion is
        never overwritten; the note's category goes into the correction columns
        beside it and is the effective code. That is what `_apply_filed_note()`
        does and what `resolve_receipt()` does with a GL override, so routing
        the note's category through the override reproduces it rather than
        changing it.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            self.write_note(settle_payload(values=dict(
                settle_payload()["values"],
                category_code="7100", category_name="Rent")))

            consume_notes()

            repo = Repository()
            try:
                categorisation, = rows(repo, "SELECT * FROM categorisations")
                self.assertEqual(categorisation["correction_code"], "7100")
                self.assertEqual(categorisation["correction_name"], "Rent")
                self.assertIn("IntelliBooks Desktop",
                              categorisation["correction_reason"])
                self.assertNotEqual(
                    categorisation["suggested_code"], "7100",
                    "the engine's suggestion was overwritten, which is the audit "
                    "trail this column exists to be")
            finally:
                repo.close()

    def test_a_note_with_no_category_at_all_still_settles(self):
        """Desktop does not require a category before filing, so `""` is common."""
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            values = dict(settle_payload()["values"],
                          category_code="", category_name="")
            self.write_note(settle_payload(values=values))

            self.assertEqual(consume_notes().get("notes_applied"), 1)

            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "ok")
                categorisation, = rows(repo, "SELECT * FROM categorisations")
                self.assertIsNone(categorisation["correction_code"])
            finally:
                repo.close()

    def test_the_idempotency_key_is_recorded_so_a_replay_changes_nothing(self):
        """12.3 step 3, and it needed carrying onto the new path.

        `resolve_receipt()` writes the event and knew nothing about notes, so
        without the `note_resolved_at` it now takes, a note put back by hand
        would be applied twice: a second `manual_correction` row and a second
        client folder copy.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            payload = settle_payload()
            self.write_note(payload)
            consume_notes()

            repo = Repository()
            try:
                first = rows(repo, "SELECT * FROM resolution_events")
                self.assertEqual(len(first), 1)
                self.assertIn(
                    "note_resolved_at", first[0]["corrections_json"] or "",
                    "the note's own timestamp is not in corrections_json, so "
                    "_note_already_applied() cannot find this event")
            finally:
                repo.close()

            # The note put back by hand, which is what Paul does with anything in
            # failed\, and what a retry after a crash looks like.
            again = self.write_note(payload, name="r-1_1753452131000.json")
            stats = consume_notes()

            self.assertEqual(stats.get("notes_applied"), 1, stats)
            self.assertIn(again.name, self.note_names("processed"))
            repo = Repository()
            try:
                self.assertEqual(
                    len(rows(repo, "SELECT * FROM resolution_events")), 1,
                    "the note was applied a second time")
                self.assertEqual(
                    len(rows(repo, "SELECT * FROM extractions "
                                   "WHERE engine = 'manual_correction'")), 1)
            finally:
                repo.close()
            self.assertEqual(len(self.everything_under_clients()), 1,
                             "a second client folder copy")

    def test_a_receipt_that_is_already_filed_is_refused_rather_than_refiled(self):
        """The double-filing guard, on the new path.

        `resolve_receipt()` step 1a refuses a receipt that already has a
        `filed_path`, and that refusal is what stops a settle note re-filing a
        receipt the pipeline has already copied. The note goes to `failed\\`,
        which is where a disagreement belongs.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            repo = Repository()
            try:
                repo.mark_receipt_filed("r-1", str(
                    self.client_receipts_dir() / "already-there.pdf"))
            finally:
                repo.close()
            note = self.write_note(settle_payload())

            stats = consume_notes()

            self.assertEqual(stats.get("notes_failed"), 1, stats)
            self.assertIn(note.name, self.note_names("failed"))
            repo = Repository()
            try:
                self.assertEqual(rows(repo, "SELECT * FROM resolution_events"), [])
            finally:
                repo.close()

    # ~~test_values_that_do_not_validate_are_refused_and_the_note_fails~~
    # **Removed 2026-09-09 by amendment 307, and it was this report's flag 1.**
    # It asserted that a settle note whose net plus VAT does not equal its gross
    # lands in `Resolutions\failed\` as `still_invalid`, which is what the code
    # did and what its own docstring called a behaviour change flagged rather
    # than smoothed over. **Paul decided: build it.** A person filed the row into
    # the books, so the database must agree; the failed checks are recorded on
    # the extraction row and in `run.log` rather than used to block.
    # `SettledDespiteFailedChecksTest` below is what replaced it, and it drives
    # the same note through the same real `process_once()`.

    def test_the_live_note_from_pauls_machine_settles(self):
        """The exact bytes from `Resolutions\\failed\\`, read on 2026-09-09.

        Copied rather than paraphrased, because the shape a real Desktop writes
        is the thing under test: `net_amount` and `vat_amount` are both null,
        the category is a four-digit code with its name beside it, and
        `original_review_files` names the inbox item.

        `client_id` and `receipt_id` are the fixture's, because
        `TempEnvironment` knows one client and it is not `Client_004`. Nothing
        else is altered.
        """
        payload = json.loads(LIVE_NOTE)
        payload["receipt_id"] = "r-1"
        payload["client_id"] = "CLIENT001"
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            self.write_note(payload)

            self.assertEqual(consume_notes().get("notes_applied"), 1)

            repo = Repository()
            try:
                receipt = repo.get_receipt("r-1")
                self.assertEqual(receipt["status"], "ok")
                manual, = rows(repo, "SELECT * FROM extractions "
                                     "WHERE engine = 'manual_correction'")
                self.assertEqual(manual["supplier_name"], "LA BELLA RESTAURANT")
                self.assertEqual(manual["gross_amount"], 27.5)
                self.assertIsNone(manual["net_amount"])
                self.assertIsNone(manual["vat_amount"])
                categorisation, = rows(repo, "SELECT * FROM categorisations")
                self.assertEqual(categorisation["correction_code"], "7406")
                self.assertEqual(categorisation["correction_name"], "Subsistence")
            finally:
                repo.close()
            self.assertEqual(
                self.everything_under_clients(),
                ["Test Client/IntelliBooks/Receipts/2025-26/"
                 "2025-06-04_la-bella-restaurant_27.50.pdf"])

    def test_a_null_amount_in_the_note_overwrites_a_figure_the_extractor_read(self):
        """The stale-figure risk `_apply_filed_note()` guards against, on the
        merging path, and it is handled by key presence rather than by not
        merging.

        `_merge_corrections()` merges by key presence, not truthiness, so a
        `net_amount` of null in the note lands as NULL rather than inheriting
        the extractor's number. Without that a corrected gross could sit beside
        a stale net and `validate()` would call it a mismatch.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(
                env, net_amount=70.0, vat_amount=14.0, gross_amount=84.0,
                supplier_name="Apcoa Parking", validation_status="ok")
            self.write_note(settle_payload(values=dict(
                settle_payload()["values"],
                net_amount=None, vat_amount=None, gross_amount=96)))

            self.assertEqual(consume_notes().get("notes_applied"), 1)

            repo = Repository()
            try:
                manual, = rows(repo, "SELECT * FROM extractions "
                                     "WHERE engine = 'manual_correction'")
                self.assertIsNone(manual["net_amount"])
                self.assertIsNone(manual["vat_amount"])
                self.assertEqual(manual["gross_amount"], 96.0)
            finally:
                repo.close()

    def test_the_two_fields_desktop_never_sends_are_carried_forward(self):
        """`receipt_ref_number` and `receipt_time`.

        The extractor read them, Desktop has no input for either, and nobody has
        contradicted them. `_apply_filed_note()` carries them forward
        explicitly; `_merge_corrections()` does it by key presence, so this is
        the same answer reached a different way and is worth pinning.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(
                env, receipt_ref_number="INV-9001", receipt_time="13:45")
            self.write_note(settle_payload())

            consume_notes()

            repo = Repository()
            try:
                manual, = rows(repo, "SELECT * FROM extractions "
                                     "WHERE engine = 'manual_correction'")
                self.assertEqual(manual["receipt_ref_number"], "INV-9001")
                self.assertEqual(manual["receipt_time"], "13:45")
            finally:
                repo.close()


class TheTwoShapesTakeDifferentPathsTest(BackfeedTestCase):
    """Deliverable 2: the choice is on the field, and both paths survive.

    Older notes exist on disk and the console may still send one, so
    `_apply_filed_note()` is not deleted. **The discriminator is observable
    rather than asserted on a mock**: the Desktop-filed path writes no client
    folder copy and records the note's own path, while the settle path writes
    one copy and records where it put it.
    """

    def test_a_note_with_filed_path_records_it_and_writes_no_copy(self):
        with TempEnvironment() as env:
            target = self.seed_desktop_filed(env)
            before = self.folder_listing(target.parent)

            self.write_note(note_payload())
            stats = consume_notes()

            self.assertEqual(stats.get("notes_applied"), 1, stats)
            self.assertEqual(
                self.folder_listing(target.parent), before,
                "the settle path ran for a note that carries filed_path, so a "
                "second copy was written")
            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["filed_path"], str(target))
            finally:
                repo.close()

    def test_a_note_without_filed_path_writes_the_copy_and_records_that(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-1", status="failed")
            finally:
                repo.close()
            self.write_note(settle_payload())

            stats = consume_notes()

            self.assertEqual(stats.get("notes_applied"), 1, stats)
            repo = Repository()
            try:
                filed = repo.get_receipt("r-1")["filed_path"]
            finally:
                repo.close()
            self.assertTrue(filed, "nothing was filed at all")
            self.assertTrue(Path(filed).exists(), filed)
            self.assertTrue(
                Path(filed).is_relative_to(config.CLIENTS_ROOT), filed)

    def test_the_choice_is_made_on_the_field_and_from_the_syntax_tree(self):
        """A guard over the set, not a test of one path.

        `apply_resolution_note()` must reach both functions and choose between
        them, so deleting either branch fails here rather than passing quietly.
        `CLAUDE.md`: only a guard over the set proves the set.
        """
        import ast
        import inspect

        import worker.resolution.service as service

        tree = ast.parse(inspect.getsource(service))
        target = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "apply_resolution_note")
        called = sorted({
            ast.unparse(node.func).split(".")[-1]
            for node in ast.walk(target) if isinstance(node, ast.Call)})
        for name in ("_apply_filed_note", "_settle_note"):
            self.assertIn(name, called, f"{name}() is unreachable: {called}")
        self.assertNotIn(
            "resolve_receipt", called,
            "apply_resolution_note() reaches resolve_receipt() directly, so the "
            "note-to-corrections translation is not in one place")

    def test_the_settle_path_never_calls_the_client_folder_writer_itself(self):
        """10f.11's one writer. The copy goes through the gated function.

        Asked of the tree rather than of a run, because a run on the `never`
        trigger would pass against a second writer that simply had not fired.
        """
        import ast
        import inspect

        import worker.resolution.service as service

        tree = ast.parse(inspect.getsource(service))
        target = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_settle_note")
        called = sorted({
            ast.unparse(node.func).split(".")[-1]
            for node in ast.walk(target) if isinstance(node, ast.Call)})
        for forbidden in ("write_client_copy", "file_receipt",
                          "mark_receipt_filed", "save_extraction"):
            self.assertNotIn(forbidden, called,
                             f"_settle_note() calls {forbidden}() itself rather "
                             "than going through resolve_receipt()")
        self.assertIn("resolve_receipt", called)


class LearningFromASettleNoteTest(BackfeedTestCase):
    """A decision the brief did not settle, taken here and stated.

    `_apply_filed_note()` learns only when the client's chart confirmed the
    code: `if note.remember_gl_for_supplier and code and category.chart_confirmed`.
    `resolve_receipt()`'s step 13 has no chart test, because its `Corrections`
    come from a person looking at a picker built from the chart.

    **So `_settle_note()` withholds the tick rather than passing it on when the
    chart did not confirm the code**, which keeps the guarantee without adding a
    parameter to `resolve_receipt()` and changing it for the console and the
    CLI. A mapping is read back by layer 1 as an exact match with confidence
    `high`, so writing one nothing has confirmed is the fault worth avoiding.

    **The chart cannot be read at all in this fixture**, because
    `TempEnvironment` points `CHARTS_DIR` at a folder it deliberately does not
    create. That is the "could not be read" arm of `_CategoryDecision`, which
    holds a code and does not confirm it, and it is the arm that must not
    learn.

    **Every note here carries `category_code`, and that is not cosmetic.**
    Without a code `_resolve_category()` returns `code=None`, so
    `_settle_note()` withholds the tick for want of a code and the chart test
    is never reached. Written without one first, and a mutation dropping
    `chart_confirmed` was then caught only by the source guard below, because
    the two behavioural tests could not fail. Disclosed in
    `2026-09-09_REPORT_claude_code_desktop_note.md`.
    """

    def note(self, remember):
        """A settle note carrying a real four-digit code and the tick."""
        return settle_payload(
            remember_gl_for_supplier=remember,
            values=dict(settle_payload()["values"],
                        category_code="7100", category_name="Rent"))

    def test_the_tick_does_not_learn_a_code_no_chart_confirmed(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-1", status="failed")
            finally:
                repo.close()
            self.write_note(self.note(remember=True))

            self.assertEqual(consume_notes().get("notes_applied"), 1)

            repo = Repository()
            try:
                self.assertEqual(
                    rows(repo, "SELECT * FROM categorisations_client_vendors"), [],
                    "a mapping was learned from a code the client's chart never "
                    "confirmed, and layer 1 reads it back as high confidence")
                self.assertEqual(
                    [e["action"] for e in rows(repo, "SELECT * FROM resolution_events")],
                    ["resolve"],
                    "a learn_vendor row was written for a mapping that was not "
                    "learned")
            finally:
                repo.close()

    def test_without_the_tick_nothing_is_learned_either(self):
        """The control. Both arms answer "nothing learned", so without this the
        test above would pass against a path that can never learn at all.

        It is asserted on the tick's own journey rather than on the chart,
        because making the chart CONFIRM a code needs a published bundle and
        `tests/test_chart_bundle.py` is where that lives. What both tests do
        drive is the unreadable-chart arm, which is the one that must not learn.
        """
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-1", status="failed")
            finally:
                repo.close()
            self.write_note(self.note(remember=False))

            self.assertEqual(consume_notes().get("notes_applied"), 1,
                             "the note did not apply, so an empty mapping table "
                             "proves nothing about the tick")

            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "ok")
                self.assertEqual(
                    rows(repo, "SELECT * FROM categorisations_client_vendors"), [])
            finally:
                repo.close()

    def test_the_suppression_is_where_it_says_it_is(self):
        """From the tree: `_settle_note()` reads `chart_confirmed`.

        Without this the two tests above are satisfied by a fixture that could
        not learn anyway, which is exactly what they are: the chart is
        unreadable here. So the mechanism is asserted on the source as well.
        """
        import ast
        import inspect

        import worker.resolution.service as service

        tree = ast.parse(inspect.getsource(service))
        target = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_settle_note")
        read = {node.attr for node in ast.walk(target)
                if isinstance(node, ast.Attribute)}
        self.assertIn("chart_confirmed", read,
                      "_settle_note() passes remember_gl_for_supplier on without "
                      "asking whether the chart confirmed the code")


class SettledDespiteFailedChecksTest(BackfeedTestCase):
    """Sub-step 10f.14, amendment 307. Paul's decision of 2026-09-09: build it.

    **This was flag 1 of `2026-09-09_REPORT_claude_code_desktop_note.md` and it
    is the last hole in amendment 306's fix.** `_apply_filed_note()` forces
    `validation_status="ok"` on the reasoning that a person filed it, and
    `resolve_receipt()` did not, so a settle note whose values did not validate
    landed in `Resolutions\\failed\\` as `still_invalid` **while its row was
    already in the books in IntelliBooks Desktop**. That is the disagreement
    between the two products that amendment 306 exists to stop, reappearing for
    a narrower input.

    **What changed:** `resolve_receipt()` takes `decided_by_operator`, default
    False, and `_settle_note()` is the only production caller that passes True.
    The checks still run and still produce their notes; the notes go on the
    extraction row and into `run.log` instead of blocking the receipt.
    `DecidedByOperatorTest` in `tests/test_resolution_service.py` holds the
    keyword's own contract and the guard that the CLI did not move.

    **Exactly two failures can reach this, and they were enumerated rather than
    assumed.** `validate()` can append six distinct notes; `parse_resolution_note()`
    refuses a note that could produce four of them, so a note that gets this far
    can only ever carry a **gross mismatch** or a **negative amount**. Both are
    driven below, and
    `test_a_note_that_could_reach_the_other_four_is_refused_by_the_parser` holds
    the other half.

    **So `decided_by_operator` can never turn a `failed` receipt green**, only a
    `needs_review` one: `failed` needs a missing gross or a missing supplier and
    the parser requires both.
    """

    MISMATCH = "gross mismatch: 80.0 + 16.0 = 96.0, got 100.0"

    def mismatched_note(self, **overrides):
        """A settle note whose net plus VAT does not equal its gross.

        80 and 16 against a gross of 100, which is 4.00 out and far past
        18.4's one penny.
        """
        values = dict(settle_payload()["values"],
                      net_amount=80, vat_amount=16, gross_amount=100)
        return settle_payload(values=values, **overrides)

    def test_a_mismatched_settle_note_reaches_ok_and_the_note_is_processed(self):
        """The red case. Before amendment 307 this landed in `failed\\`.

        The three assertions that were false: `ok`, a `resolution_events` row
        saying `filed`, and the note out of the queue.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            note = self.write_note(self.mismatched_note())

            stats = consume_notes()

            self.assertEqual(stats.get("notes_applied"), 1, stats)
            self.assertEqual(self.note_names("failed"), [])
            self.assertIn(note.name, self.note_names("processed"))

            repo = Repository()
            try:
                receipt = repo.get_receipt("r-1")
                self.assertEqual(receipt["status"], "ok")
                self.assertIsNone(receipt["locked_at"])
                events = rows(repo, "SELECT * FROM resolution_events")
                self.assertEqual(len(events), 1, events)
                self.assertEqual(
                    events[0]["outcome"], "filed",
                    "deliverable 3: the outcome column says what happened to "
                    "the receipt, and what happened is that it was settled. "
                    "still_invalid would be false, and it would also strand the "
                    "note, because the idempotency key is stamped on filed only")
                self.assertIn("note_resolved_at", events[0]["corrections_json"])
            finally:
                repo.close()

    def test_the_failed_checks_are_readable_afterwards_on_the_extraction_row(self):
        """Where the failures live, and it is one join from the event.

        `resolution_events.extraction_id` points at this row, which is where
        `_apply_filed_note()` already puts its own "despite" line. Nothing is
        recalculated and nothing is dropped: the figures on the row are the ones
        the note sent.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            self.write_note(self.mismatched_note())

            consume_notes()

            repo = Repository()
            try:
                manual, = rows(repo, "SELECT * FROM extractions "
                                     "WHERE engine = 'manual_correction'")
                self.assertEqual(manual["validation_status"], "ok")
                self.assertIn("manually corrected and filed",
                              manual["validation_notes"])
                self.assertIn("despite", manual["validation_notes"])
                self.assertIn(self.MISMATCH, manual["validation_notes"])
                self.assertEqual(manual["net_amount"], 80.0)
                self.assertEqual(manual["vat_amount"], 16.0)
                self.assertEqual(manual["gross_amount"], 100.0,
                                 "the gross was recalculated, which 18.4 forbids")
                events = rows(repo, "SELECT * FROM resolution_events")
                self.assertEqual(events[0]["extraction_id"],
                                 manual["extraction_id"],
                                 "the event does not point at the row carrying "
                                 "the failures, so they are not one join away")
            finally:
                repo.close()

    def test_the_log_says_it_reached_ok_despite_the_failures(self):
        """Deliverable 2. **Paul reads `run.log`.**

        A receipt that silently turns green is worse than the fault being
        fixed, so the line is a WARNING, names the receipt, names who decided,
        and quotes every failed check.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            self.write_note(self.mismatched_note())

            with captured("worker.resolution.service", logging.WARNING) as log:
                consume_notes()

            warnings = log.messages(logging.WARNING)
            self.assertEqual(len(warnings), 1, warnings)
            self.assertIn("r-1", warnings[0])
            self.assertIn("desktop", warnings[0])
            self.assertIn("ok", warnings[0])
            self.assertIn(self.MISMATCH, warnings[0])

    def test_a_note_that_validates_logs_no_such_warning(self):
        """The negative control, and it is not optional.

        A warning on every settled receipt would be noise and a reader who saw
        it every time would stop reading it, which is `CLAUDE.md`'s check that
        cannot fail in its other form.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            self.write_note(settle_payload())

            with captured("worker.resolution.service", logging.WARNING) as log:
                self.assertEqual(consume_notes().get("notes_applied"), 1)

            self.assertEqual(log.messages(logging.WARNING), [])
            repo = Repository()
            try:
                manual, = rows(repo, "SELECT * FROM extractions "
                                     "WHERE engine = 'manual_correction'")
                self.assertNotIn("despite", manual["validation_notes"])
                self.assertEqual(manual["validation_notes"],
                                 "manually corrected and filed")
            finally:
                repo.close()

    def test_the_client_folder_copy_still_happens(self):
        """A settled-despite-failures receipt is `ok`, so 18.2b applies to it.

        The name comes from the note's own figures, the mismatched gross
        included, because nothing is recalculated.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            self.write_note(self.mismatched_note())

            consume_notes()

            self.assertEqual(
                self.everything_under_clients(),
                ["Test Client/IntelliBooks/Receipts/2025-26/"
                 "2026-04-01_apcoa-parking_100.00.pdf"])
            repo = Repository()
            try:
                self.assertTrue(repo.get_receipt("r-1")["filed_path"])
            finally:
                repo.close()

    def test_a_negative_amount_is_the_other_failure_that_reaches_this(self):
        """The second of the two reachable failures, and it is not a VAT one.

        `_note_amount()` accepts any finite JSON number, so a negative is a
        legal note even though `fileReviewReceipt()` sends `Math.abs()` and
        cannot produce one. Driven because it is reachable from any other
        writer of a note, and because 18.4's "the system alerts, it never
        prevents" is a VAT rule and does not cover it. Flagged in
        `2026-09-09_REPORT_claude_code_decided_by_operator.md`.
        """
        with TempEnvironment() as env:
            self.seed_awaiting_settlement(env)
            values = dict(settle_payload()["values"],
                          net_amount=-80, vat_amount=-16, gross_amount=-96)
            self.write_note(settle_payload(values=values))

            self.assertEqual(consume_notes().get("notes_applied"), 1)

            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "ok")
                manual, = rows(repo, "SELECT * FROM extractions "
                                     "WHERE engine = 'manual_correction'")
                self.assertIn("net_amount is negative: -80.0",
                              manual["validation_notes"])
                self.assertEqual(manual["gross_amount"], -96.0)
            finally:
                repo.close()

    def test_a_note_that_could_reach_the_other_four_is_refused_by_the_parser(self):
        """The safety property, and it is what bounds this change.

        `validate()` can append six distinct notes, enumerated from its own
        syntax tree by `test_validate_can_append_exactly_six_notes` below. Four
        of them need a shape `parse_resolution_note()` refuses, so
        `decided_by_operator` can never force one through. **The consequence
        that matters: it can only ever turn a `needs_review` receipt `ok`, never
        a `failed` one**, because `failed` needs a missing gross or a missing
        supplier.
        """
        base = settle_payload()["values"]
        cases = {
            "missing supplier_name": {k: v for k, v in base.items()
                                      if k != "supplier_name"},
            "missing gross_amount": {k: v for k, v in base.items()
                                     if k != "gross_amount"},
            "missing invoice_date": {k: v for k, v in base.items()
                                     if k != "invoice_date"},
            "invalid date": dict(base, invoice_date="2026-02-31"),
        }
        for label, values in cases.items():
            with self.subTest(case=label):
                with TempEnvironment() as env:
                    self.seed_awaiting_settlement(env)
                    note = self.write_note(settle_payload(values=values))

                    stats = consume_notes()

                    self.assertEqual(stats.get("notes_failed"), 1, stats)
                    self.assertIn(note.name, self.note_names("failed"))
                    repo = Repository()
                    try:
                        self.assertEqual(repo.get_receipt("r-1")["status"],
                                         "failed")
                        self.assertEqual(
                            rows(repo, "SELECT * FROM resolution_events"), [],
                            "the parser let it through and resolve_receipt() "
                            "then forced it ok, so decided_by_operator can "
                            "turn a failed receipt green")
                    finally:
                        repo.close()

    def test_validate_can_append_exactly_six_notes(self):
        """The set the test above reasons about, enumerated rather than named.

        `CLAUDE.md`: a claim about a set is not verified by verifying its
        members. If `worker\\validation\\rules.py` gains a seventh check, this
        fails and somebody has to decide whether
        `decided_by_operator` may force it through.
        """
        import ast

        source = (REPO_ROOT / "worker" / "validation" / "rules.py"
                  ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        target = next(node for node in ast.walk(tree)
                      if isinstance(node, ast.FunctionDef)
                      and node.name == "validate")
        appended = sorted({
            ast.unparse(node.args[0]) for node in ast.walk(target)
            if isinstance(node, ast.Call)
            and ast.unparse(node.func) == "notes.append"})
        self.assertEqual(len(appended), 6, appended)
        self.assertEqual(
            appended,
            ["'missing gross_amount'",
             "'missing invoice_date'",
             "'missing supplier_name'",
             "f'gross mismatch: {result.net_amount} + {result.vat_amount} = "
             "{expected}, got {actual}'",
             "f'invalid date: {result.invoice_date}'",
             "f'{field} is negative: {val}'"])


class ContractShapeTest(unittest.TestCase):
    """The half of the contract the other session cannot see."""

    def test_apply_resolution_note_never_calls_file_receipt(self):
        import ast
        import inspect

        import worker.resolution.service as service

        source = inspect.getsource(service)
        tree = ast.parse(source)
        target = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "apply_resolution_note"
        )
        called = {
            node.func.id for node in ast.walk(target)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("file_receipt", called,
                         "12.3 step 5: the file is already at filed_path")
        self.assertNotIn("make_enriched_sidecar", called,
                         "Desktop wrote its own sidecar; rewriting it is Paul's call at step 10")


if __name__ == "__main__":
    unittest.main()

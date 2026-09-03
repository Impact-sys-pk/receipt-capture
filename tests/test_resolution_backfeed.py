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
"""

import json
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
    RecordingExtractor,
    TempEnvironment,
    rows,
    run_pipeline_once,
)
from worker.database.repository import Repository  # noqa: E402
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
        # The 12.4 amendment: Desktop removes the pair itself, so
        # remove_review_pair() finds nothing. Zero is not an error.
        with TempEnvironment() as env:
            self.seed_desktop_filed(env)
            review_dir = config.CLIENTS_ROOT / "Test Client" / "Review"
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
            "filed with no filed_path": {
                k: v for k, v in note_payload().items() if k != "filed_path"
            },
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

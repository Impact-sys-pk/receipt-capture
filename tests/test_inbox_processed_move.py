"""Design document 3.13: a folder-intake receipt that is not `ok` is re-extracted
on every poll.

`_remove_inbox_pair(intake)` ran only `if status == "ok"`, so anything else left
the original in `Receipt Inbox\\{CODE}\\`. On the next poll `find_by_hash()` finds
the existing receipt, `is_recorded_and_filed()` is false because `filed_path` is
NULL, and app.py then deliberately allows reprocessing. The receipt is therefore
re-extracted every five minutes for ever, at one OpenAI call each, with a new
receipt row, a new extraction row and a new Review pair every time.

The fix moves the original to a `Processed\\` subfolder under the client's inbox
folder on **every** outcome. A move rather than a delete, per CLAUDE.md's
no-data-loss rule, and that applies to the `ok` path too, which used to delete.

These tests drive a real `process_once()` twice. Asserting on the extractor's call
count across two polls is the only assertion that actually describes the bug.
"""

import sys
import types
import unittest
from unittest.mock import patch

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    TempEnvironment,
    extraction_result,
    rows,
    run_pipeline_once,
)
from worker.database.repository import Repository  # noqa: E402

import app  # noqa: E402

PROCESSED = "Processed"


class InboxProcessedMoveTest(unittest.TestCase):
    def _receipt_count(self):
        repo = Repository()
        try:
            return len(rows(repo, "SELECT receipt_id FROM receipts"))
        finally:
            repo.close()

    def _statuses(self):
        repo = Repository()
        try:
            return [r["status"] for r in rows(repo, "SELECT status FROM receipts")]
        finally:
            repo.close()

    def _drop_receipt(self, env, name="TEST_receipt.png", sidecar_text=None):
        inbox = env.inbox_dir("ABC")
        original = inbox / name
        original.write_text("dummy image bytes", encoding="utf-8")
        sidecar = None
        if sidecar_text is not None:
            sidecar = original.with_suffix(".json")
            sidecar.write_text(sidecar_text, encoding="utf-8")
        return inbox, original, sidecar

    def test_a_needs_review_receipt_leaves_the_inbox_and_is_not_re_extracted(self):
        with TempEnvironment() as env:
            inbox, original, _ = self._drop_receipt(env)

            # Supplier missing with a valid date and gross: needs_review, per
            # worker/validation/rules.py.
            extractor = RecordingExtractor(extraction_result(supplier_name=None))
            run_pipeline_once(extractor)

            self.assertEqual(extractor.calls, 1)
            self.assertEqual(self._statuses(), ["needs_review"])
            self.assertFalse(
                original.exists(),
                "THE BUG: a needs_review original left in the inbox is re-extracted every poll",
            )
            moved = inbox / PROCESSED / original.name
            self.assertTrue(moved.exists(), "moved, not deleted: no data loss")

            # Second poll, same pipeline_version. Nothing to find, nothing to do.
            run_pipeline_once(extractor)

            self.assertEqual(extractor.calls, 1, "THE MONEY BUG: a second OpenAI call")
            self.assertEqual(self._receipt_count(), 1, "no second receipt row")

    def test_a_failed_receipt_leaves_the_inbox_and_is_not_re_extracted(self):
        with TempEnvironment() as env:
            inbox, original, _ = self._drop_receipt(env, name="TEST_unreadable.png")

            # No gross: unrecoverable, so `failed`.
            extractor = RecordingExtractor(extraction_result(gross_amount=None))
            run_pipeline_once(extractor)

            self.assertEqual(extractor.calls, 1)
            self.assertEqual(self._statuses(), ["failed"])
            self.assertFalse(original.exists())
            self.assertTrue((inbox / PROCESSED / original.name).exists())

            run_pipeline_once(extractor)

            self.assertEqual(extractor.calls, 1)
            self.assertEqual(self._receipt_count(), 1)

    def test_an_extraction_that_raises_still_leaves_the_inbox(self):
        # The exception branch never removed the pair either, and it is the branch
        # 3.1 showed costs three OpenAI calls per poll through the retry helper.
        with TempEnvironment() as env:
            inbox, original, _ = self._drop_receipt(env, name="TEST_crash.png")

            extractor = RecordingExtractor(RuntimeError("simulated API failure"))
            with patch("worker.extraction.retry_helper.time.sleep"):
                run_pipeline_once(extractor)

            self.assertFalse(original.exists())
            self.assertTrue((inbox / PROCESSED / original.name).exists())

    def test_the_ok_path_still_clears_the_inbox_but_now_by_moving(self):
        with TempEnvironment() as env:
            inbox, original, _ = self._drop_receipt(env, name="TEST_good.png")

            extractor = RecordingExtractor(extraction_result())
            run_pipeline_once(extractor)

            self.assertEqual(self._statuses(), ["ok"])
            self.assertFalse(original.exists(), "the inbox is still cleared")
            self.assertTrue(
                (inbox / PROCESSED / original.name).exists(),
                "and the original is retained rather than deleted",
            )

    def test_a_sidecar_moves_with_its_original_rather_than_being_orphaned(self):
        with TempEnvironment() as env:
            inbox, original, sidecar = self._drop_receipt(
                env,
                name="TEST_with_sidecar.png",
                sidecar_text='{"supplier_name": "Apcoa Parking"}',
            )
            self.assertTrue(sidecar.exists())

            extractor = RecordingExtractor(extraction_result(supplier_name=None))
            run_pipeline_once(extractor)

            self.assertFalse(original.exists())
            self.assertFalse(sidecar.exists(), "an orphaned sidecar is rescanned for ever")
            self.assertTrue((inbox / PROCESSED / original.name).exists())
            self.assertTrue((inbox / PROCESSED / sidecar.name).exists())

    def test_a_second_file_of_the_same_name_does_not_overwrite_the_first(self):
        # An operator putting the same filename back deliberately is the case
        # app.py:717's reprocessing rule still guards, so Processed\ has to cope.
        with TempEnvironment() as env:
            inbox, original, _ = self._drop_receipt(env, name="TEST_resend.png")
            extractor = RecordingExtractor(extraction_result(supplier_name=None))
            run_pipeline_once(extractor)

            first = inbox / PROCESSED / "TEST_resend.png"
            self.assertTrue(first.exists())
            first_bytes = first.read_bytes()

            resend = inbox / "TEST_resend.png"
            resend.write_text("different content, same name", encoding="utf-8")
            run_pipeline_once(extractor)

            self.assertFalse(resend.exists())
            self.assertEqual(
                first.read_bytes(), first_bytes, "the first original must not be overwritten"
            )
            self.assertTrue(
                (inbox / PROCESSED / "TEST_resend-2.png").exists(),
                "the same -2 convention the filing code uses",
            )

    def test_the_processed_folder_is_not_rescanned_as_new_intake(self):
        with TempEnvironment() as env:
            inbox, original, _ = self._drop_receipt(env, name="TEST_once.png")
            extractor = RecordingExtractor(extraction_result())
            run_pipeline_once(extractor)

            from worker.intake.folder_reader import scan_inbox

            self.assertEqual(
                scan_inbox(), [], "scan_inbox() must not walk into Processed\\"
            )


if __name__ == "__main__":
    unittest.main()

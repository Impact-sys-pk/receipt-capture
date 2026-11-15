r"""A reply that is a list fails cleanly, and says so. 2026-11-15.

Brief `PROMPT_claude_code_2026-11-15_a_raised_extraction_must_not_vanish.md`,
part 3. **The small version only: no multi-receipt support.**

Paul dropped a photo of four receipts into Add Receipts and the model replied
with a JSON list. `parsed.get()` raised `'list' object has no attribute 'get'`,
which is what the operator would have read, had anything been published.

**What the operator now reads** on the receipt's row in IntelliBooks Desktop's
review list: `MULTIPLE_RECEIPTS_NOTE`. **It is not the note an unreadable image
gets**, which is `validate()`'s `missing supplier_name` and the rest, and the
two need different actions from him: one is sent again as one image per
receipt, the other is read by hand or sent again as a better picture.

**The note does not state a count.** Nobody has established that one entry in
the list is one receipt: the reply Paul's test produced was never stored, the
extraction row holds a 36-character exception message, so there is no list to
examine. The count is in the exception's message and the log, as a fact about
the reply, and not in the note, which would make it a claim about the paper.

**Only a list of two or more entries gets the note.** An empty list or a list
of one is not evidence of several receipts, and gets the generic note.

No live model call: the replies below are stored-shape JSON handed to the real
`extract()` through a fake client, as `tests/test_declined_receipt_no_retry.py`
does.
"""

import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import config

from resolution_fixtures import Routes, TempEnvironment, rows
from worker.database.repository import Repository
from worker.extraction.base import MULTIPLE_RECEIPTS_NOTE, ExtractionReplyError
from worker.publish import NOTES_KEY

FOUR = json.dumps([
    {"supplier_name": "Shell Co-op Harborne", "gross_amount": 41.58},
    {"supplier_name": "Shell Co-op Harborne", "gross_amount": 51.11},
    {"supplier_name": "PGG Harborne", "gross_amount": 50.50},
    {"supplier_name": "PGG Harborne", "gross_amount": 13.07},
], indent=4)


class _FakeVision:
    """The real extractor with its client replaced. Counts calls."""

    def __init__(self, reply):
        from worker.extraction.openai_vision import OpenAIVisionExtractor

        self.calls = 0
        self.inner = OpenAIVisionExtractor()

        def create(**kwargs):
            self.calls += 1
            return SimpleNamespace(choices=[SimpleNamespace(
                message=SimpleNamespace(content=reply))])

        self.inner._client = SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(create=create)))
        self.name = self.inner.name

    def extract(self, file_path, filename):
        return self.inner.extract(file_path, filename)


class TheExtractorTest(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".jpg")
        os.write(fd, b"not really a jpeg")
        os.close(fd)
        self.addCleanup(os.remove, self.path)

    def _raised(self, reply):
        with self.assertRaises(ExtractionReplyError) as caught:
            _FakeVision(reply).extract(self.path, "x.jpg")
        return caught.exception

    def test_a_list_of_four_names_more_than_one_receipt(self):
        exc = self._raised(FOUR)
        self.assertEqual(exc.note, MULTIPLE_RECEIPTS_NOTE)
        self.assertEqual(exc.raw_response, FOUR)

    def test_a_fenced_list_is_the_same(self):
        self.assertEqual(self._raised("```json\n" + FOUR + "\n```").note,
                         MULTIPLE_RECEIPTS_NOTE)

    def test_an_empty_list_or_a_list_of_one_is_not_called_several(self):
        for reply in ("[]", '[{"supplier_name": "Shell"}]'):
            with self.subTest(reply=reply):
                self.assertNotEqual(self._raised(reply).note, MULTIPLE_RECEIPTS_NOTE)

    def test_the_note_states_no_count(self):
        self.assertFalse(any(ch.isdigit() for ch in MULTIPLE_RECEIPTS_NOTE))


class TheOperatorCanTellTheTwoApartTest(unittest.TestCase):
    """Through a real `process_once()`, the inbox route Paul used."""

    def _item_notes(self, reply):
        from chart_fixtures import TempChartBundle

        # The bundle because an unreadable reply goes on through post-processing,
        # which reads the published VAT rate table.
        with TempEnvironment(), TempChartBundle():
            extractor = _FakeVision(reply)
            with patch("worker.extraction.retry_helper.time.sleep", lambda s: None):
                Routes(extractor).inbox_file("photo of four.jpg", "desktop")
            repo = Repository()
            try:
                receipt, = rows(repo, "SELECT * FROM receipts")
                extraction, = rows(repo, "SELECT * FROM extractions WHERE receipt_id = ?",
                                   (receipt["receipt_id"],))
            finally:
                repo.close()
            item = json.loads((config.INTELLIBOOKS_PUBLISH_DIR /
                               f"{receipt['receipt_id']}.json").read_text(encoding="utf-8"))
            return extractor.calls, receipt, extraction, item

    def test_a_photo_of_four_is_one_call_failed_and_says_so(self):
        calls, receipt, extraction, item = self._item_notes(FOUR)
        self.assertEqual(calls, 1, "a list reply was sent again")
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(item["validation_status"], "failed")
        self.assertEqual(item[NOTES_KEY], [MULTIPLE_RECEIPTS_NOTE])
        self.assertEqual(extraction["raw_response"], FOUR)

    def test_an_unreadable_image_gets_a_different_note(self):
        _, receipt, _, item = self._item_notes("I can't read this image.")
        self.assertEqual(receipt["status"], "failed")
        self.assertNotIn(MULTIPLE_RECEIPTS_NOTE, item[NOTES_KEY])
        self.assertIn("missing supplier_name", item[NOTES_KEY])


if __name__ == "__main__":
    unittest.main()

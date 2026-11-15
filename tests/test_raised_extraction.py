r"""A receipt whose extraction raised still reaches the operator.

Brief `PROMPT_claude_code_2026-11-15_a_raised_extraction_must_not_vanish.md`,
part 1. Paul's live test of 2026-11-15 at 10:19 GMT: a photo of four receipts,
dropped into Add Receipts on `Client_004`, made the model reply with a JSON
list, `extract()` raised on `parsed.get()`, and the capture route's `except`
branch wrote a `failed` extraction row and published nothing. Receipt
`c1060e30` had no item in `Intellibills\Incoming\`, so it reached no screen.

**What these assert, route by route**: the item is published, it says
`failed`, and its notes say what happened. The three arrival routes are driven
through a real `app.process_once()` by `resolution_fixtures.Routes`, with only
the mailbox and the extractor replaced.

**And the guard on the new behaviour**: a raise that comes AFTER
`process_extraction_result()` has already published must not publish a
`failed` item over the one that landed.
"""

import glob
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import config

from resolution_fixtures import (
    RecordingExtractor, Routes, TempEnvironment, extraction_result, rows,
    with_email_client,
)
from worker.database.repository import Repository
from worker.publish import NOTES_KEY

ERROR = "simulated API failure"


def _only_receipt():
    repo = Repository()
    try:
        found = rows(repo, "SELECT * FROM receipts")
        assert len(found) == 1, found
        receipt = found[0]
        extractions = rows(repo, "SELECT * FROM extractions WHERE receipt_id = ? "
                                 "ORDER BY extracted_at", (receipt["receipt_id"],))
        events = rows(repo, "SELECT * FROM publish_events WHERE receipt_id = ?",
                      (receipt["receipt_id"],))
        return receipt, extractions, events
    finally:
        repo.close()


def _item(receipt_id):
    path = Path(config.INTELLIBOOKS_PUBLISH_DIR) / f"{receipt_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _event_actions(receipt_id):
    actions = []
    for name in glob.glob(str(Path(config.LOGS_DIR) / "receipt_events_*.ndjson")):
        for line in Path(name).read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if event.get("receipt_id") == receipt_id:
                actions.append(event.get("action"))
    return actions


class ARaisedExtractionIsPublishedTest(unittest.TestCase):
    """Every arrival route, because the brief names none of them as the only one."""

    def _drive(self, route):
        extractor = RecordingExtractor(RuntimeError(ERROR))
        routes = Routes(extractor)
        if route == "inbox":
            routes.inbox_file("photo.jpg", "desktop")
        else:
            with_email_client(self)
            getattr(routes, route)()
        return _only_receipt()

    def _assert_visible(self, receipt, extractions, events):
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(len(extractions), 1, "one extraction row for one attempt")
        self.assertEqual([e["outcome"] for e in events], ["published"],
                         "a raised extraction published nothing, so it reached no screen")
        item = _item(receipt["receipt_id"])
        self.assertIsNotNone(item, "no item in Intellibills\\Incoming\\")
        self.assertEqual(item["validation_status"], "failed")
        self.assertIn(f"extraction error: {ERROR}", item[NOTES_KEY],
                      "the item does not say what happened")

    def test_the_inbox_route(self):
        with TempEnvironment():
            self._assert_visible(*self._drive("inbox"))

    def test_the_email_attachment_route(self):
        with TempEnvironment():
            self._assert_visible(*self._drive("email_attachment"))

    def test_the_embedded_image_route(self):
        with TempEnvironment():
            self._assert_visible(*self._drive("embedded_image"))

    def test_the_event_log_still_says_extraction_failed(self):
        """The event log is append-only history, so the word it has always
        written for a raised extraction does not change with this fix."""
        with TempEnvironment():
            receipt, _, _ = self._drive("inbox")
            actions = _event_actions(receipt["receipt_id"])
            self.assertIn("extraction_failed", actions)
            self.assertNotIn("extracted", actions)


class TheReplyIsKeptTest(unittest.TestCase):
    """Where a reply was received and the failure came afterwards."""

    def test_the_stored_raw_response_is_the_reply_not_the_message(self):
        from worker.extraction.base import ExtractionReplyError

        reply = '[{"supplier_name": "Shell"}, {"supplier_name": "PGG"}]'
        with TempEnvironment():
            extractor = RecordingExtractor(
                ExtractionReplyError("could not use the reply", raw_response=reply))
            Routes(extractor).inbox_file("photo.jpg", "desktop")
            _, extractions, _ = _only_receipt()
            self.assertEqual(extractions[0]["raw_response"], reply,
                             "the model's reply was replaced by the error message")


class TheExtractorCarriesItsReplyTest(unittest.TestCase):
    """The real `extract()`, with a fake client: a failure after the reply
    arrives is raised carrying the reply, whatever the failure was."""

    def test_a_failure_after_the_reply_carries_it(self):
        import os
        import tempfile
        from types import SimpleNamespace

        from chart_fixtures import TempChartBundle
        from worker.extraction.base import ExtractionReplyError
        from worker.extraction.openai_vision import OpenAIVisionExtractor

        reply = '"just a string"'
        fd, path = tempfile.mkstemp(suffix=".jpg")
        os.write(fd, b"not really a jpeg")
        os.close(fd)
        self.addCleanup(os.remove, path)
        with TempChartBundle():
            extractor = OpenAIVisionExtractor()
            extractor._client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(
                    message=SimpleNamespace(content=reply))]))))
            with self.assertRaises(ExtractionReplyError) as caught:
                extractor.extract(path, "x.jpg")
        self.assertEqual(caught.exception.raw_response, reply)


class TheAutoRetryKeepsTheReplyTooTest(unittest.TestCase):
    """The fourth extracting path. Not an arrival route, so it publishes nothing
    new: the receipt was published when it arrived. But the row it writes on a
    raise is the record of what the model read, so it keeps the reply too."""

    def test_the_auto_retry_row_stores_the_reply(self):
        import app
        from worker.categorisation.engine import CategorisationEngine
        from worker.extraction.base import ExtractionReplyError

        reply = '[{"supplier_name": "Shell"}]'
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, pipeline_version="old-version")
                extractor = RecordingExtractor(
                    ExtractionReplyError("could not use the reply", raw_response=reply))
                with patch("worker.extraction.retry_helper.time.sleep", lambda s: None):
                    app._retry_failed_receipts(
                        repo=repo, extractor=extractor,
                        categorisation_engine=CategorisationEngine(
                            repo=repo, enable_ai_fallback=False),
                        stats={}, run_id="test-run", pipeline_version="new-version")
                latest = repo.get_extraction_for_receipt("r-1")
                self.assertEqual(latest["pipeline_version"], "new-version")
                self.assertEqual(latest["raw_response"], reply)
            finally:
                repo.close()


class ALateRaiseDoesNotRepublishTest(unittest.TestCase):
    """The new publish must not land on top of one that already happened.

    Each route's `except` wraps `process_extraction_result()` as well as the
    extraction, so a raise from inside it, after it has saved and published,
    reaches the same branch.
    """

    def test_an_ok_item_is_not_overwritten_by_a_failed_one(self):
        with TempEnvironment():
            extractor = RecordingExtractor(extraction_result())
            with patch("worker.extraction_pipeline.copy_for_published_receipt",
                       side_effect=RuntimeError("raised after the publish")):
                Routes(extractor).inbox_file("receipt.jpg", "desktop")
            receipt, _, events = _only_receipt()
            self.assertEqual([e["outcome"] for e in events], ["published"],
                             "published twice: the late raise republished")
            self.assertEqual(_item(receipt["receipt_id"])["validation_status"], "ok")

    def test_a_late_raise_writes_nothing_over_the_row(self):
        """F3 of `2026-11-15_REPORT_claude_code_raised_extraction.md`, Paul's
        decision of 2026-11-15. The row `process_extraction_result()` wrote is
        the record of the attempt. The `except` used to write a `failed` row on
        top, flipping an `ok` receipt to `failed`, and an `extraction_failed`
        event for a receipt that was extracted. As `_retry_failed_receipts()`
        already does since sub-step 10ay: write nothing."""
        for route in ("inbox", "email_attachment", "embedded_image"):
            with self.subTest(route=route), TempEnvironment():
                routes = Routes(RecordingExtractor(extraction_result()))
                with patch("worker.extraction_pipeline.copy_for_published_receipt",
                           side_effect=RuntimeError("raised after the publish")):
                    if route == "inbox":
                        routes.inbox_file("receipt.jpg", "desktop")
                    else:
                        with_email_client(self)
                        getattr(routes, route)()
                receipt, extractions, _ = _only_receipt()
                self.assertEqual(len(extractions), 1, "a failed row was written on top")
                self.assertEqual(receipt["status"], "ok",
                                 "the late raise flipped the receipt to failed")
                self.assertNotIn("extraction_failed",
                                 _event_actions(receipt["receipt_id"]))


if __name__ == "__main__":
    unittest.main()

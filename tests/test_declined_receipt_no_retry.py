r"""A receipt the extractor declined is not auto-retried. Flag H4.

Brief `PROMPT_claude_code_2026-11-14_three_flags.md`, part 1. **Paul's
decision of 2026-11-14, in his words: "Not until it is reviewed."** At the
moment the pipeline is about to re-send a receipt, it reads what the extractor
stored last time and skips the receipt if that reply is not usable.

**Why.** Receipt `0e8fdbdc`, an HMRC account screenshot, was sent to OpenAI and
republished to `Intellibills\Incoming\` on every restart on a new commit, 26
attempts by 2026-11-14, and declined every time.

**Paul's further decision of 2026-11-14, asked during the build**: the rule is
literal. A stored exception message, written by `app.py` when an extraction
raises, will not parse either, so such a receipt is skipped too and waits for
review rather than being retried on the next commit.

**"Usable" is decided by `worker.extraction.stored_reply.reply_is_usable()`**,
and `TheTwoParsersAgreeTest` holds it to `OpenAIVisionExtractor.extract()`'s own
parsing on every reply shape listed, by driving `extract()` itself.
"""

import logging
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import config

from chart_fixtures import TempChartBundle
from resolution_fixtures import TempEnvironment, rows
from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.extraction.openai_vision import OpenAIVisionExtractor
from worker.extraction.stored_reply import reply_is_usable

OLD = "old-version"
NEW = "new-version"

REFUSAL = ("I'm unable to extract data from this type of document as it doesn't "
           "match a traditional receipt or invoice format.")
GOOD = '{"supplier_name": "Shell", "gross_amount": 10.0, "invoice_date": "2026-11-01"}'

#: Reply shapes, and whether `extract()` can use each. The verdict is NOT
#: asserted from this table: `TheTwoParsersAgreeTest` asks `extract()` itself
#: and compares. The second column is here for a reader.
REPLIES = (
    (GOOD, True),
    ("```json\n" + GOOD + "\n```", True),
    ("```\n" + GOOD + "\n```", True),
    ("```json\n" + GOOD, True),
    ("   \n" + GOOD + "\n  ", True),
    ("{}", True),
    (REFUSAL, False),
    ("", False),
    ("   ", False),
    ('{"supplier_name": "Sh', False),        # a reply cut short
    ("```json\n{\"supplier_name\": \"Sh\n```", False),
    ("null", False),
    ("[]", False),
    ('"just a string"', False),
    ("```json\n```", False),
    (GOOD + " and some words after", False),
    ("auto-retry extraction error: simulated API failure", False),
)


class FakeResponse:
    def __init__(self, content):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]


class TheTwoParsersAgreeTest(unittest.TestCase):
    """**The check must not disagree with the extractor about one reply.**

    `openai_vision.py` is not to be changed by this brief, so the parsing could
    not be shared by moving it. It is held in step here instead: each reply is
    put through `extract()` with a fake client, and `extract()` is counted as
    unable to use it if it logged the non-JSON warning or raised.
    """

    def setUp(self):
        self._bundle = TempChartBundle().__enter__()
        self.addCleanup(self._bundle.__exit__, None, None, None)
        fd, self.path = tempfile.mkstemp(suffix=".jpg")
        os.write(fd, b"not really a jpeg")
        os.close(fd)
        self.addCleanup(os.remove, self.path)

    def extract_can_use(self, reply):
        extractor = OpenAIVisionExtractor()
        extractor._client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=lambda **kwargs: FakeResponse(reply))))
        with self.assertLogs("worker.extraction.openai_vision", level="WARNING") as logs:
            logging.getLogger("worker.extraction.openai_vision").warning("sentinel")
            try:
                extractor.extract(self.path, "x.jpg")
            except Exception:
                return False
        return not any("Non-JSON response" in line for line in logs.output)

    def test_every_reply_shape(self):
        for reply, expected in REPLIES:
            with self.subTest(reply=reply[:40]):
                self.assertEqual(reply_is_usable(reply), self.extract_can_use(reply))
                self.assertEqual(reply_is_usable(reply), expected)

    def test_no_reply_at_all_is_not_usable(self):
        self.assertFalse(reply_is_usable(None))


class CountingExtractor:
    name = "counting"

    def __init__(self):
        self.calls = 0

    def extract(self, file_path, filename):
        self.calls += 1
        raise RuntimeError("would have been a paid call")


class TheRetryTest(unittest.TestCase):

    def setUp(self):
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.repo = Repository()
        self.addCleanup(self.repo.close)

    def seed(self, receipt_id, raw, status="failed", age_days=0):
        self.env.seed(self.repo, receipt_id=receipt_id, status=status,
                      extraction_id=f"ext-{receipt_id}", raw_response=raw,
                      pipeline_version=OLD, validation_status=status)
        if age_days:
            created = (datetime.now(timezone.utc) - timedelta(days=age_days)).isoformat()
            self.repo._conn.execute("UPDATE receipts SET created_at = ? WHERE receipt_id = ?",
                                    (created, receipt_id))
            self.repo._conn.commit()

    def run_retry(self):
        import app
        extractor = CountingExtractor()
        with patch("worker.extraction.retry_helper.time.sleep"):
            app._retry_failed_receipts(
                repo=self.repo, extractor=extractor,
                categorisation_engine=CategorisationEngine(repo=self.repo),
                stats={}, run_id="test", pipeline_version=NEW)
        return extractor

    def state(self, receipt_id):
        return (rows(self.repo, "SELECT status, locked_at FROM receipts WHERE receipt_id = ?",
                     (receipt_id,)),
                rows(self.repo, "SELECT * FROM extractions WHERE receipt_id = ?", (receipt_id,)),
                rows(self.repo, "SELECT * FROM publish_events WHERE receipt_id = ?", (receipt_id,)))

    def incoming(self):
        folder = config.INTELLIBOOKS_PUBLISH_DIR
        return sorted(p.name for p in folder.iterdir()) if folder.exists() else []

    def test_a_declined_receipt_is_not_sent_again_and_nothing_changes(self):
        for status in ("failed", "needs_review"):
            with self.subTest(status=status):
                receipt_id = f"r-{status}"
                self.seed(receipt_id, REFUSAL, status=status)
                before, files = self.state(receipt_id), self.incoming()
                extractor = self.run_retry()
                self.assertEqual(extractor.calls, 0)
                self.assertEqual(self.state(receipt_id), before)
                self.assertEqual(self.incoming(), files)

    def test_however_many_times_the_version_moves(self):
        self.seed("r-1", REFUSAL)
        for _ in range(3):
            self.assertEqual(self.run_retry().calls, 0)

    def test_no_reply_or_an_empty_one_is_not_usable_either(self):
        for raw in (None, "", "   "):
            with self.subTest(raw=raw):
                receipt_id = f"r-{raw!r}"
                self.seed(receipt_id, raw)
                self.assertEqual(self.run_retry().calls, 0)

    def test_a_stored_exception_message_is_skipped_too(self):
        """Paul's decision, 2026-11-14: literal. See the module docstring."""
        self.seed("r-crash", "Connection timed out")
        self.assertEqual(self.run_retry().calls, 0)

    def test_a_usable_reply_is_still_retried(self):
        """Everything else the auto-retry does is unchanged."""
        for label, raw in (("plain", GOOD), ("fenced", "```json\n" + GOOD + "\n```")):
            with self.subTest(reply=label):
                receipt_id = f"r-{label}"
                self.seed(receipt_id, raw)
                self.assertGreater(self.run_retry().calls, 0)

    def test_the_latest_reply_decides(self):
        """A declined first attempt followed by a usable one is retried; the
        other way round it is not."""
        self.seed("r-good-last", REFUSAL)
        self.repo.save_extraction(
            extraction_id="ext-r-good-last-2", receipt_id="r-good-last", engine="x",
            supplier_name=None, invoice_date=None, net_amount=None, vat_amount=None,
            gross_amount=None, currency="GBP", raw_response=GOOD,
            validation_status="failed", validation_notes=[], pipeline_version=OLD,
            update_status=False)
        self.assertGreater(self.run_retry().calls, 0)

        self.seed("r-bad-last", GOOD)
        self.repo.save_extraction(
            extraction_id="ext-r-bad-last-2", receipt_id="r-bad-last", engine="x",
            supplier_name=None, invoice_date=None, net_amount=None, vat_amount=None,
            gross_amount=None, currency="GBP", raw_response=REFUSAL,
            validation_status="failed", validation_notes=[], pipeline_version=OLD,
            update_status=False)
        extractor = CountingExtractor()
        import app
        with patch("worker.extraction.retry_helper.time.sleep"):
            app._retry_failed_receipts(
                repo=self.repo, extractor=extractor,
                categorisation_engine=CategorisationEngine(repo=self.repo),
                stats={}, run_id="t", pipeline_version="newer-again")
        # r-good-last was retried above and now holds a NEW-version row, so the
        # only receipt this run can reach is r-bad-last, which must be skipped.
        self.assertEqual(extractor.calls, 0)

    def test_a_declined_receipt_keeps_its_status_past_the_retry_window(self):
        """**It stays where it is and waits for the operator.** The skip comes
        before the seven-day check, so a declined receipt is never moved to
        `retry_exhausted`. A usable one past the window still is."""
        self.seed("r-old-declined", REFUSAL, age_days=30)
        self.seed("r-old-usable", GOOD, age_days=30)
        self.run_retry()
        statuses = {r["receipt_id"]: r["status"] for r in rows(
            self.repo, "SELECT receipt_id, status FROM receipts")}
        self.assertEqual(statuses["r-old-declined"], "failed")
        self.assertEqual(statuses["r-old-usable"], "retry_exhausted")


if __name__ == "__main__":
    unittest.main()

r"""Two places an attached document reached and should not.

Amendment 345, Paul's decisions of 2026-09-12, from
`PROMPT_claude_code_2026-09-12_attached_documents.md`. Both items were carried
open from session 22.

## What an attached document is, and why it is neither of these things

Sub-step 10f.38: IntelliBooks Desktop attaches a document to a bank line and
hands it to Intellibills to archive and to file. **It is not extracted, not
validated, never published back and never in the receipts list.** Its `receipts`
row carries `config.BANK_ATTACHMENT_STATUS` as a marker, which is Paul's
decision of 2026-09-11 over the two alternatives he refused: a status that is
not `ok`, which would make the row lie about a validation that never ran, and a
separate table, which would make the client copy path take its inputs from two
shapes.

**So it was never read**, and `count_processed_today()` counted it. **And a
back-feed note cannot be about it**, because it came from the books rather than
from capture and has no review sidecar for a note to have come from, and the
filename fallback could match it.

## The real writer, not a hand-written row

Both halves of item 1 are driven through `record_attached_document()` by way of
a real `app.process_once()`, because the brief says so and the reason is good:
**seeding the row by hand would prove the test reads a row the test invented.**
The marker, the absence of an extraction row and the client the row is written
for would all be this file's opinion rather than the writer's behaviour.
"""

import ast
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config

import source_guards
from resolution_fixtures import TempEnvironment, rows
from worker import london_time
from worker.database.repository import Repository
from worker.resolution.service import parse_resolution_note, _receipt_for_note

from test_attached_document import (
    RECEIPT_ID,
    AttachedTestCase,
    attach_message,
)

REPO_ROOT = Path(source_guards.REPO_ROOT)


# ---------------------------------------------------------------------------
# Item 1: count_processed_today() counts what the pipeline actually read
# ---------------------------------------------------------------------------

class WhatCountsAsProcessedTest(AttachedTestCase):
    """Driven through the real writer, by a real poll."""

    def count(self):
        repo = Repository()
        try:
            return repo.count_processed_today()
        finally:
            repo.close()

    def seed_receipt(self, repo, receipt_id, status):
        """An ordinary captured receipt, at a status the pipeline can give it."""
        file_path = config.FILES_DIR / f"{receipt_id}.pdf"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("x", encoding="utf-8")
        repo.save_receipt(
            receipt_id=receipt_id, message_id=f"<{receipt_id}@x>",
            email_subject="s", email_from="c@example.com",
            email_received_at=None, filename=f"{receipt_id}.pdf",
            file_path=file_path, file_hash=receipt_id * 3,
            firm_id="FIRM001", client_id="CLIENT001", source="email")
        if status != "pending":
            repo.update_receipt_status(receipt_id, status)

    def test_a_handed_over_document_is_not_counted(self):
        """**The headline.** It was never read, never extracted, never published."""
        with TempEnvironment(), self._post_trigger():
            self.hand_over()
            self.assertEqual(self.count(), 0, "the control: nothing yet")

            self.poll()

            row = self.receipt()
            self.assertIsNotNone(row, "the real writer wrote no row")
            self.assertEqual(row["status"], config.BANK_ATTACHMENT_STATUS,
                             "this test is not driving the writer it thinks")
            self.assertEqual(
                self.count(), 0,
                "a document handed over from the books was counted as something "
                "the pipeline read")

    def test_a_receipt_the_pipeline_read_today_is_counted(self):
        """The control. Without it the test above would pass on a count that
        returned nought for everything."""
        with TempEnvironment():
            repo = Repository()
            try:
                self.seed_receipt(repo, "r-ok", "ok")
            finally:
                repo.close()
            self.assertEqual(self.count(), 1)

    def test_a_receipt_still_waiting_to_be_read_is_not_counted(self):
        """`pending` is what `save_receipt()` writes before anything reads the
        document. The brief names it as one of the three things wrongly counted."""
        with TempEnvironment():
            repo = Repository()
            try:
                self.seed_receipt(repo, "r-pending", "pending")
            finally:
                repo.close()
            self.assertEqual(self.count(), 0)

    def test_every_status_the_pipeline_can_reach_is_decided_one_way_or_the_other(self):
        """The set, enumerated, so a ninth status is a decision rather than an
        accident. `CLAUDE.md`: a claim about a set is not verified by verifying
        its members."""
        from worker.database import repository
        counted = set(repository.PROCESSED_STATUSES)
        not_counted = {"pending", config.BANK_ATTACHMENT_STATUS}
        import test_capture_report
        every = set(test_capture_report.statuses_from_source())
        self.assertEqual(
            counted | not_counted, every,
            "a status the database can hold is neither counted nor excluded. "
            f"Counted {sorted(counted)}; excluded {sorted(not_counted)}; the "
            f"database can hold {sorted(every)}")
        self.assertEqual(counted & not_counted, set())

    def test_a_discarded_receipt_is_counted(self):
        """**A decision, reported rather than taken quietly.**

        It was READ before it was discarded, and the pipeline's work on it is
        not unmade by a person's later judgement about the document. And a count
        that fell retroactively as the day went on would be a worse figure for
        an intake panel than one that does not.
        """
        with TempEnvironment():
            repo = Repository()
            try:
                self.seed_receipt(repo, "r-gone", "discarded")
            finally:
                repo.close()
            self.assertEqual(self.count(), 1)

    def test_a_failed_extraction_is_counted(self):
        """The pipeline read it and could not get data off it. That is work
        done, and hiding it would make a bad day look like a quiet one."""
        with TempEnvironment():
            repo = Repository()
            try:
                self.seed_receipt(repo, "r-failed", "failed")
            finally:
                repo.close()
            self.assertEqual(self.count(), 1)

    def test_a_statement_is_still_counted(self):
        """`statements` were counted before this change and still are. A
        platform statement IS something the pipeline read; the brief does not
        mention them and nothing here narrows them."""
        with TempEnvironment():
            repo = Repository()
            try:
                repo.save_statement(
                    statement_id="s-1", client_id="CLIENT001",
                    platform="uber", week_ending="2026-09-30",
                    source="email", file_hash="h" * 8,
                    file_path="/s.pdf", filed_path="/filed/s.pdf")
            finally:
                repo.close()
            self.assertEqual(self.count(), 1)

    def _post_trigger(self):
        from test_attached_document import trigger
        return trigger(config.CLIENT_COPY_AT_POST)


class WhichDayTest(unittest.TestCase):
    r"""**A decision, reported rather than taken quietly: the LONDON day.**

    `pipeline-status.json` keeps UTC for its `last_run` TIMESTAMP, and this is
    not a timestamp. It is a count whose whole meaning is the word "today", and
    "today" is a word about the reader's calendar. The London work of 2026-09-11
    settled that what a person reads is in their own clock, and
    `capture_report.py`'s date range already selects on the London day: a
    "processed today" figure on the UTC day would disagree with the capture
    report about the same day, which is the half-change that work exists to
    avoid.

    A London day is 23, 24 or 25 hours, so the bounds are computed as instants
    rather than by taking the first ten characters of anything.
    """

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._saved = config.DB_PATH
        config.DB_PATH = Path(self._temp.name) / "receipts.db"

    def tearDown(self):
        config.DB_PATH = self._saved
        self._temp.cleanup()

    def _seed_at(self, repo, receipt_id, created_at):
        repo.save_receipt(
            receipt_id=receipt_id, message_id=f"<{receipt_id}@x>",
            email_subject="s", email_from="c@example.com",
            email_received_at=None, filename=f"{receipt_id}.pdf",
            file_path=f"/{receipt_id}.pdf", file_hash=receipt_id * 3,
            firm_id="FIRM001", client_id="CLIENT001", source="email")
        repo.update_receipt_status(receipt_id, "ok")
        repo._conn.execute(
            "UPDATE receipts SET created_at = ? WHERE receipt_id = ?",
            (created_at, receipt_id))
        repo._conn.commit()

    def test_the_bounds_are_the_london_day_and_not_the_utc_day(self):
        """The receipt arrives at 23:30 UTC, which is 00:30 tomorrow in London.

        Counted against the UTC day it belongs to today; against the London day
        it belongs to tomorrow. The bounds are asked for directly so this does
        not depend on when the test runs.
        """
        from worker.database import repository
        # A summer date, so London is an hour ahead and the two days differ.
        start, end = repository.london_day_bounds(
            datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc))
        self.assertEqual(start, "2026-06-30T23:00:00+00:00",
                         "the London day begins at 23:00 UTC in summer")
        self.assertEqual(end, "2026-07-01T23:00:00+00:00")

    def test_a_winter_day_is_the_utc_day(self):
        from worker.database import repository
        start, end = repository.london_day_bounds(
            datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc))
        self.assertEqual(start, "2026-01-15T00:00:00+00:00")
        self.assertEqual(end, "2026-01-16T00:00:00+00:00")

    def test_the_clock_change_day_is_twenty_five_hours(self):
        """The last Sunday in October. A day that is not 24 hours long is
        exactly what a string comparison on the first ten characters gets wrong."""
        from worker.database import repository
        start, end = repository.london_day_bounds(
            datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc))
        hours = (datetime.fromisoformat(end)
                 - datetime.fromisoformat(start)).total_seconds() / 3600
        self.assertEqual(hours, 25)

    def test_a_receipt_in_the_last_hour_of_the_utc_day_counts_tomorrow(self):
        """Driven, not only computed."""
        today = london_time.now()
        # 23:30 UTC on the London day BEFORE today, which in summer is 00:30
        # today. Built from the real bounds so it holds in either season.
        from worker.database import repository
        start, _end = repository.london_day_bounds()
        just_inside = (datetime.fromisoformat(start)
                       + timedelta(minutes=30)).isoformat()
        just_outside = (datetime.fromisoformat(start)
                        - timedelta(minutes=30)).isoformat()
        repo = Repository()
        try:
            self._seed_at(repo, "r-in", just_inside)
            self._seed_at(repo, "r-out", just_outside)
            self.assertEqual(repo.count_processed_today(), 1)
        finally:
            repo.close()


class TheStatusFilterIsRealTest(unittest.TestCase):
    """The query asks about status, read off the source rather than inferred."""

    def test_the_count_query_filters_on_status(self):
        tree = source_guards.tree_of("worker", "database", "repository.py")
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name != "count_processed_today":
                continue
            sql = " ".join(
                value for value, _line
                in source_guards.string_constants(ast.Module(body=node.body,
                                                             type_ignores=[])))
            self.assertIn("status IN", sql,
                          "the count has no status filter, so it counts every "
                          "row created today again")
            self.assertNotIn("DATE('now','utc')", sql,
                             "the count is back on the UTC day")
            return
        self.fail("count_processed_today() has gone")


# ---------------------------------------------------------------------------
# Item 2: the filename fallback excludes an attached document, at the caller
# ---------------------------------------------------------------------------

class TheFilenameFallbackTest(unittest.TestCase):
    r"""A back-feed note with no receipt id cannot match an attached document.

    **The exclusion is in the caller and not in the query.**
    `find_receipts_by_filename()`'s docstring says it returns every match and
    that refusing an ambiguous one is the caller's problem rather than its own
    to guess at. A status filter in the query would make a general-purpose
    lookup carry one caller's rule.
    """

    FILENAME = "bank-line-invoice.pdf"

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._saved = config.DB_PATH
        config.DB_PATH = Path(self._temp.name) / "receipts.db"
        self.repo = Repository()
        self.addCleanup(self.repo.close)
        self.addCleanup(setattr, config, "DB_PATH", self._saved)
        self.addCleanup(self._temp.cleanup)

    def _receipt(self, receipt_id, status, filename=None):
        self.repo.save_receipt(
            receipt_id=receipt_id, message_id=f"<{receipt_id}@x>",
            email_subject="s", email_from="c@example.com",
            email_received_at=None, filename=filename or self.FILENAME,
            file_path=f"/{receipt_id}.pdf", file_hash=receipt_id * 3,
            firm_id="FIRM001", client_id="CLIENT001", source="email")
        self.repo.update_receipt_status(receipt_id, status)

    def _note(self):
        return parse_resolution_note({
            "schema": 1,
            "receipt_id": None,
            "client_id": "CLIENT001",
            "action": "filed",
            "resolved_by": "desktop",
            "resolved_at": "2026-09-12T11:00:00.000Z",
            "original_review_files": [self.FILENAME, self.FILENAME + ".review.json"],
            "values": {"supplier_name": "X", "gross_amount": 1.0,
                       "invoice_date": "2026-09-01"},
            "filed_path": r"Clients\X\IntelliBooks\Receipts\2026-27\x.pdf",
        })

    def test_the_lookup_itself_is_left_alone_and_still_returns_everything(self):
        """The method keeps its contract. This is what makes the exclusion a
        caller's rule rather than a change to a general-purpose query."""
        self._receipt("r-attached", config.BANK_ATTACHMENT_STATUS)
        found = self.repo.find_receipts_by_filename(self.FILENAME)
        self.assertEqual(len(found), 1,
                         "find_receipts_by_filename() has grown a status filter")

    def test_a_note_with_no_receipt_id_does_not_match_an_attached_document(self):
        self._receipt("r-attached", config.BANK_ATTACHMENT_STATUS)
        self.assertIsNone(_receipt_for_note(self.repo, self._note()))

    def test_it_still_matches_an_ordinary_receipt(self):
        """The control. Without it the test above would pass on a fallback that
        matched nothing at all."""
        self._receipt("r-ok", "ok")
        found = _receipt_for_note(self.repo, self._note())
        self.assertIsNotNone(found)
        self.assertEqual(found["receipt_id"], "r-ok")

    def test_the_ambiguity_refusal_still_fires_on_two_real_candidates(self):
        self._receipt("r-one", "ok")
        self._receipt("r-two", "needs_review")
        with self.assertLogs("worker.resolution.service", level="ERROR") as caught:
            self.assertIsNone(_receipt_for_note(self.repo, self._note()))
        self.assertIn("ambiguous", "\n".join(caught.output))

    def test_two_candidates_where_one_is_attached_is_a_match_and_not_a_refusal(self):
        """**The behaviour change the brief asks to be worked out and reported.**

        Before, this was two candidates and a refusal. Now the attached document
        is not a candidate at all, so it is one candidate and a match.

        **That is right rather than a loosening.** The refusal exists because
        two receipts can share an original filename and the note cannot say
        which it means. An attached document was never one of the things the
        note could mean: it came from the books rather than from capture and has
        no review sidecar for a note to have come from. Removing a non-candidate
        does not resolve an ambiguity; it shows there was never one.
        """
        self._receipt("r-attached", config.BANK_ATTACHMENT_STATUS)
        self._receipt("r-real", "ok")
        found = _receipt_for_note(self.repo, self._note())
        self.assertIsNotNone(found, "the only real candidate was refused")
        self.assertEqual(found["receipt_id"], "r-real")

    def test_a_note_carrying_a_receipt_id_is_unaffected(self):
        """The fallback is the only path this touches. A note that names its
        receipt still finds it, whatever the status."""
        self._receipt("r-attached", config.BANK_ATTACHMENT_STATUS)
        note = parse_resolution_note({
            "schema": 1, "receipt_id": "r-attached", "client_id": "CLIENT001",
            "action": "attached", "resolved_by": "desktop",
            "resolved_at": "2026-09-12T11:00:00.000Z",
        })
        found = _receipt_for_note(self.repo, note)
        self.assertIsNotNone(found)
        self.assertEqual(found["receipt_id"], "r-attached")


if __name__ == "__main__":
    unittest.main()

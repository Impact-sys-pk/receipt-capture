"""The publish record: one row per receipt per destination per attempt.

**Stage 1 piece 3, deliverable 4. Sub-step 10f.36 and amendment 283.** The
pipeline records that it published, so three states can be told apart and the
answer does not depend on looking in a folder that Desktop will later drain:

- **no row at all**, the receipt was never offered to that destination;
- **a row saying `failed`**, it was tried and did not land, with the reason;
- **a row saying `published`**, it landed, with the path it landed at.

Built on the `resolution_events` pattern, which is the precedent named by 10f.36
and by the brief. **No foreign key on `receipt_id`**, for the reason
`schema.py` gives for that table: an audit row that cannot be written because
the thing it describes has gone is worse than a dangling id, and a receipt a
rebuild has dropped is exactly when somebody wants its history.

**Why a row per attempt rather than a state on `receipts`.** A column would hold
the latest answer and lose the failure that preceded it, and the failures are
the interesting half while Desktop is not yet draining the folder. `receipts`
carries `filed_path` and `filed_at` for filing and gains nothing here.
"""

import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path

import config

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

from worker import publish  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

EXPECTED_COLUMNS = [
    "event_id", "receipt_id", "destination", "outcome", "item_path",
    "reason", "created_at",
]


class TempDb:
    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._original = config.DB_PATH
        config.DB_PATH = self.path / "receipts.db"
        return self

    def __exit__(self, *exc):
        config.DB_PATH = self._original
        self._temp.cleanup()
        return False


class PublishEventsSchemaTest(unittest.TestCase):
    def test_the_table_exists_with_the_columns_10f_36_needs(self):
        with TempDb():
            repo = Repository()
            try:
                columns = [row[1] for row in repo._conn.execute(
                    "PRAGMA table_info(publish_events)").fetchall()]
                self.assertEqual(set(columns), set(EXPECTED_COLUMNS))
            finally:
                repo.close()

    def test_the_event_id_is_the_primary_key(self):
        with TempDb():
            repo = Repository()
            try:
                keys = [row[1] for row in repo._conn.execute(
                    "PRAGMA table_info(publish_events)").fetchall() if row[5]]
                self.assertEqual(keys, ["event_id"])
            finally:
                repo.close()

    def test_the_four_columns_a_row_must_have_are_not_null(self):
        """`item_path` is null on a failure and `reason` on a success.

        Neither can be NOT NULL, so four columns are and two are not.

        **`event_id` is the primary key and the pragma reports it nullable**,
        which is SQLite's long-standing quirk: only an INTEGER PRIMARY KEY
        rejects NULL, and a TEXT one does not unless it says NOT NULL as well.
        `resolution_events` is the same and this table matches it. Expected
        wrongly here on the first run, which is how the quirk was noticed.
        """
        with TempDb():
            repo = Repository()
            try:
                notnull = {row[1] for row in repo._conn.execute(
                    "PRAGMA table_info(publish_events)").fetchall() if row[3]}
                self.assertEqual(
                    notnull,
                    {"receipt_id", "destination", "outcome", "created_at"})
            finally:
                repo.close()

    def test_no_column_carries_a_sql_default(self):
        # Sub-steps 10d.23 to 10d.28: a default is a value arriving as a
        # fallback rather than as a recorded conclusion. The writer states
        # every one.
        with TempDb():
            repo = Repository()
            try:
                defaults = {row[1]: row[4] for row in repo._conn.execute(
                    "PRAGMA table_info(publish_events)").fetchall() if row[4] is not None}
                self.assertEqual(defaults, {})
            finally:
                repo.close()

    def test_there_is_no_foreign_key_on_the_receipt(self):
        """`resolution_events`' reasoning, and it applies here for the same reason.

        A publish event about a receipt a rebuild has dropped is exactly when
        somebody wants the history, and a key would refuse to write it.
        """
        with TempDb():
            repo = Repository()
            try:
                keys = repo._conn.execute(
                    "PRAGMA foreign_key_list(publish_events)").fetchall()
                self.assertEqual(list(keys), [])
            finally:
                repo.close()

    def test_the_receipt_is_indexed_with_the_time(self):
        with TempDb():
            repo = Repository()
            try:
                indexes = [row[1] for row in repo._conn.execute(
                    "PRAGMA index_list(publish_events)").fetchall()]
                self.assertIn("idx_publish_events_receipt", indexes)
                columns = [row[2] for row in repo._conn.execute(
                    "PRAGMA index_info(idx_publish_events_receipt)").fetchall()]
                self.assertEqual(columns, ["receipt_id", "created_at"])
            finally:
                repo.close()


class PublishEventsWriterTest(unittest.TestCase):
    def setUp(self):
        self._db = TempDb().__enter__()
        self.addCleanup(self._db.__exit__)
        self.repo = Repository()
        self.addCleanup(self.repo.close)

    def test_no_row_is_the_third_state_and_it_is_distinguishable(self):
        # The state the brief names first: never offered. An empty list means
        # that and nothing else.
        self.assertEqual(self.repo.list_publish_events("never-tried"), [])

    def test_a_successful_row_carries_the_path_and_no_reason(self):
        self.repo.save_publish_event(
            event_id="e1", receipt_id="r1", destination="intellibooks",
            outcome=publish.PUBLISHED, created_at="2026-09-09T10:00:00+00:00",
            item_path=r"C:\practice\IntelliBooks\Incoming\r1.json")
        row, = self.repo.list_publish_events("r1")
        self.assertEqual(row["outcome"], "published")
        self.assertEqual(row["item_path"],
                         r"C:\practice\IntelliBooks\Incoming\r1.json")
        self.assertIsNone(row["reason"])

    def test_a_failed_row_carries_the_reason_and_no_path(self):
        self.repo.save_publish_event(
            event_id="e2", receipt_id="r2", destination="intellibooks",
            outcome=publish.FAILED, created_at="2026-09-09T10:00:00+00:00",
            reason="no media type for '.docx'")
        row, = self.repo.list_publish_events("r2")
        self.assertEqual(row["outcome"], "failed")
        self.assertIn(".docx", row["reason"])
        self.assertIsNone(row["item_path"])

    def test_the_two_outcomes_are_two_words_and_they_differ(self):
        self.assertNotEqual(publish.PUBLISHED, publish.FAILED)

    def test_one_receipt_can_hold_a_failure_then_a_success(self):
        """One row per attempt, which a column on `receipts` could not hold.

        The failure is the interesting half while nothing drains the folder.
        """
        self.repo.save_publish_event(
            event_id="e3", receipt_id="r3", destination="intellibooks",
            outcome=publish.FAILED, created_at="2026-09-09T10:00:00+00:00",
            reason="the folder was not there")
        self.repo.save_publish_event(
            event_id="e4", receipt_id="r3", destination="intellibooks",
            outcome=publish.PUBLISHED, created_at="2026-09-09T10:05:00+00:00",
            item_path="x.json")
        rows = self.repo.list_publish_events("r3")
        self.assertEqual([r["outcome"] for r in rows], ["published", "failed"],
                         "newest first, as list_resolution_events orders")

    def test_one_receipt_can_be_published_to_two_destinations(self):
        # 10f.36 says per receipt per destination. Only one exists today, and
        # the row shape does not assume that.
        self.repo.save_publish_event(
            event_id="e5", receipt_id="r4", destination="intellibooks",
            outcome=publish.PUBLISHED, created_at="2026-09-09T10:00:00+00:00",
            item_path="a.json")
        self.repo.save_publish_event(
            event_id="e6", receipt_id="r4", destination="somewhere_else",
            outcome=publish.PUBLISHED, created_at="2026-09-09T10:00:01+00:00",
            item_path="b.json")
        rows = self.repo.list_publish_events("r4")
        self.assertEqual(sorted(r["destination"] for r in rows),
                         ["intellibooks", "somewhere_else"])

    def test_the_event_id_cannot_repeat(self):
        self.repo.save_publish_event(
            event_id="e7", receipt_id="r5", destination="intellibooks",
            outcome=publish.PUBLISHED, created_at="2026-09-09T10:00:00+00:00",
            item_path="a.json")
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.save_publish_event(
                event_id="e7", receipt_id="r6", destination="intellibooks",
                outcome=publish.PUBLISHED, created_at="2026-09-09T10:00:00+00:00",
                item_path="b.json")

    def test_a_row_about_a_receipt_that_is_not_in_the_database_still_writes(self):
        # The property the missing foreign key exists for, driven rather than
        # inferred from PRAGMA output.
        self.repo.save_publish_event(
            event_id="e8", receipt_id="gone-in-a-rebuild",
            destination="intellibooks", outcome=publish.FAILED,
            created_at="2026-09-09T10:00:00+00:00", reason="the receipt has gone")
        self.assertEqual(len(self.repo.list_publish_events("gone-in-a-rebuild")), 1)


if __name__ == "__main__":
    unittest.main()

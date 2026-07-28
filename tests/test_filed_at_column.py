"""Design document 5.1a: `receipts.filed_at`.

4.3 step 1a's `already_filed` message promises the operator a date, and 8.3 lists
a "filed" column that would otherwise only ever be a yes or no. There was no
timestamp anywhere: `receipts` has `filed_path` and `created_at` and nothing in
between.

`mark_receipt_filed()` is the only writer of `filed_path`, so it is the only place
this needs setting and the two stay consistent by construction.

Existing rows keep NULL and must not be back-filled from a file mtime, which
records when a copy was written rather than when the practice filed it. A
plausible wrong date is worse than a NULL.
"""

import sqlite3
import sys
import types
import unittest
from datetime import datetime, timezone

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402

from resolution_fixtures import TempEnvironment, good_corrections  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.database.schema import init_db  # noqa: E402
from worker.resolution.service import resolve_receipt  # noqa: E402


def receipt_columns():
    conn = sqlite3.connect(config.DB_PATH)
    try:
        return [row[1] for row in conn.execute("PRAGMA table_info(receipts)").fetchall()]
    finally:
        conn.close()


class FiledAtColumnTest(unittest.TestCase):
    def test_the_column_exists_after_init_db(self):
        with TempEnvironment():
            init_db()
            self.assertIn("filed_at", receipt_columns())

    def test_init_db_is_still_idempotent(self):
        with TempEnvironment():
            init_db()
            before = receipt_columns()
            init_db()
            init_db()
            self.assertEqual(receipt_columns(), before, "no duplicate column, no error")

    def test_mark_receipt_filed_stamps_the_time(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                self.assertIsNone(repo.get_receipt("r-1")["filed_at"])

                repo.mark_receipt_filed("r-1", str(env.path / "filed.pdf"))

                receipt = repo.get_receipt("r-1")
                self.assertIsNotNone(receipt["filed_path"])
                stamped = datetime.fromisoformat(receipt["filed_at"])
                delta = abs((datetime.now(timezone.utc) - stamped).total_seconds())
                self.assertLess(delta, 60, "an ISO timestamp of roughly now")
            finally:
                repo.close()

    def test_a_resolution_sets_it_alongside_filed_path(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", good_corrections(),
                    actor="paul", source="cli",
                )
                self.assertEqual(outcome.outcome, "filed", outcome.message)
                receipt = repo.get_receipt("r-1")
                self.assertIsNotNone(receipt["filed_at"])
            finally:
                repo.close()

    def test_the_already_filed_message_carries_the_date(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                resolve_receipt(
                    repo, env.engine(repo), "r-1", good_corrections(),
                    actor="paul", source="cli",
                )
                filed_at = repo.get_receipt("r-1")["filed_at"]

                second = resolve_receipt(
                    repo, env.engine(repo), "r-1", good_corrections(),
                    actor="paul", source="cli",
                )
                self.assertEqual(second.outcome, "already_filed")
                self.assertIn(filed_at[:10], second.message,
                              "4.3 step 1a promises the operator a date")
            finally:
                repo.close()

    def test_existing_rows_are_not_back_filled(self):
        # The migration path the live database will take: a receipt filed before
        # the column existed keeps NULL rather than acquiring a plausible wrong
        # date from a file mtime.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="ok")
            finally:
                repo.close()

            conn = sqlite3.connect(config.DB_PATH)
            try:
                try:
                    conn.execute("ALTER TABLE receipts DROP COLUMN filed_at")
                except sqlite3.OperationalError as exc:
                    self.skipTest(f"this SQLite cannot DROP COLUMN: {exc}")
                conn.execute(
                    "UPDATE receipts SET filed_path = ? WHERE receipt_id = 'r-1'",
                    (str(env.path / "filed-long-ago.pdf"),),
                )
                conn.commit()
                self.assertNotIn(
                    "filed_at", [r[1] for r in conn.execute("PRAGMA table_info(receipts)")]
                )
            finally:
                conn.close()

            init_db()

            self.assertIn("filed_at", receipt_columns())
            repo = Repository()
            try:
                receipt = repo.get_receipt("r-1")
                self.assertIsNotNone(receipt["filed_path"], "still filed")
                self.assertIsNone(receipt["filed_at"], "and honestly undated")
            finally:
                repo.close()


if __name__ == "__main__":
    unittest.main()

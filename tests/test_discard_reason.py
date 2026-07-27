"""Design document 5.1 as amended: resolution_events.reason.

discard_receipt() takes a reason and the table had nowhere to put it, so it
reached a log line and the operator's message and then vanished. For a discard
the reason is the single most useful thing to keep: the difference between
"duplicate of r-x" and "the client sent a bank statement by mistake"."""

import sys
import types
import unittest

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config

from resolution_fixtures import TempEnvironment, good_corrections, rows
from worker.database.repository import Repository
from worker.resolution.service import discard_receipt, parse_corrections, resolve_receipt


class DiscardReasonTest(unittest.TestCase):
    """5.1 as amended: the reason is the most useful thing to keep about a discard."""

    def test_the_reason_round_trips_out_of_its_own_column(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="possible_duplicate", gross_amount=12.0)
                discard_receipt(
                    repo, "r-1", "the client sent a bank statement by mistake",
                    actor="paul", source="cli",
                )
                event = rows(repo, "SELECT * FROM resolution_events")[0]
                self.assertEqual(event["reason"], "the client sent a bank statement by mistake")
                self.assertIsNone(
                    event["corrections_json"],
                    "the reason must not be smuggled into corrections_json",
                )
            finally:
                repo.close()

    def test_a_resolve_leaves_the_reason_null(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                resolve_receipt(
                    repo, env.engine(repo), "r-1", good_corrections(), actor="paul", source="cli",
                )
                event = rows(repo, "SELECT * FROM resolution_events")[0]
                self.assertIsNone(event["reason"])
            finally:
                repo.close()

    def test_the_column_exists_on_an_older_database(self):
        # The PRAGMA table_info guard pattern, exercised: build the table without
        # the column, then let init_db() add it.
        with TempEnvironment() as env:
            import sqlite3
            conn = sqlite3.connect(config.DB_PATH)
            conn.executescript("""
                CREATE TABLE receipts (receipt_id TEXT PRIMARY KEY, firm_id TEXT,
                    client_id TEXT, message_id TEXT, filename TEXT, file_path TEXT,
                    file_hash TEXT, status TEXT, created_at TEXT);
                CREATE TABLE resolution_events (
                    event_id TEXT PRIMARY KEY, receipt_id TEXT NOT NULL,
                    extraction_id TEXT, actor TEXT NOT NULL, source TEXT NOT NULL,
                    action TEXT NOT NULL, corrections_json TEXT, gl_override_code TEXT,
                    outcome TEXT NOT NULL, created_at TEXT NOT NULL);
            """)
            conn.commit()
            conn.close()

            repo = Repository()  # runs init_db()
            try:
                cols = [
                    r[1] for r in
                    repo._conn.execute("PRAGMA table_info(resolution_events)").fetchall()
                ]
                self.assertIn("reason", cols)
            finally:
                repo.close()


if __name__ == "__main__":
    unittest.main()

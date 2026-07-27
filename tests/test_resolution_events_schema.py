"""Design document 5.1: the resolution_events table.

Every resolution writes one row whatever the entry point, so a correction records
who made it and through which tool. A correction previously recorded
engine='manual_correction' and nothing about the actor, which is not tenable with
two console users plus 'desktop' resolutions arriving via the back-feed.

extraction_id is nullable and carries no foreign key, deliberately. 5.1 says why:
a foreign key would make the event row fail on an outcome with no extraction,
which is the same class of bug as b480a7e.
"""

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

from worker.database.repository import Repository
from worker.database.schema import init_db

EXPECTED_COLUMNS = [
    "event_id", "receipt_id", "extraction_id", "actor", "source",
    "action", "corrections_json", "gl_override_code", "outcome", "reason", "created_at",
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


class ResolutionEventsSchemaTest(unittest.TestCase):
    def test_the_table_exists_with_the_columns_5_1_specifies(self):
        with TempDb():
            repo = Repository()
            try:
                cols = [
                    row[1] for row in
                    repo._conn.execute("PRAGMA table_info(resolution_events)").fetchall()
                ]
                # Set, not sequence. A database created fresh has `reason` before
                # created_at, from the CREATE TABLE; one migrated by the PRAGMA
                # guard has it appended last, because that is what ALTER TABLE
                # does. Harmless, because every read and write here is by name,
                # and asserting order would fail on one of the two.
                self.assertEqual(sorted(cols), sorted(EXPECTED_COLUMNS))
            finally:
                repo.close()

    def test_extraction_id_is_nullable_and_carries_no_foreign_key(self):
        with TempDb():
            repo = Repository()
            try:
                info = {
                    row[1]: row for row in
                    repo._conn.execute("PRAGMA table_info(resolution_events)").fetchall()
                }
                # notnull is column 3 of table_info
                self.assertEqual(info["extraction_id"][3], 0, "extraction_id must be nullable")
                self.assertEqual(info["actor"][3], 1)
                self.assertEqual(info["source"][3], 1)
                self.assertEqual(info["outcome"][3], 1)

                fk_targets = [
                    row[2] for row in
                    repo._conn.execute("PRAGMA foreign_key_list(resolution_events)").fetchall()
                ]
                self.assertEqual(fk_targets, ["receipts"], "only receipt_id may carry a FK")
            finally:
                repo.close()

    def test_the_receipt_index_exists(self):
        with TempDb():
            repo = Repository()
            try:
                indexes = [
                    row[1] for row in
                    repo._conn.execute("PRAGMA index_list(resolution_events)").fetchall()
                ]
                self.assertIn("idx_resolution_events_receipt", indexes)
            finally:
                repo.close()

    def test_a_row_with_no_extraction_id_inserts(self):
        # The still_invalid path before the 2026-07-27 amendment produced no
        # extraction row, and the back-feed may too. A FK here would raise.
        with TempDb():
            repo = Repository()
            try:
                repo._conn.execute(
                    "INSERT INTO receipts (receipt_id, firm_id, client_id, message_id, "
                    "filename, file_path, file_hash, status, created_at) "
                    "VALUES ('r-1','INTELLITAX','C1','m1','f.pdf','p','h','needs_review','now')"
                )
                repo._conn.execute(
                    "INSERT INTO resolution_events (event_id, receipt_id, extraction_id, "
                    "actor, source, action, outcome, created_at) "
                    "VALUES ('e-1','r-1',NULL,'paul','cli','resolve','still_invalid','now')"
                )
                repo._conn.commit()
                row = repo._conn.execute(
                    "SELECT extraction_id FROM resolution_events WHERE event_id = 'e-1'"
                ).fetchone()
                self.assertIsNone(row["extraction_id"])
            finally:
                repo.close()

    def test_init_db_is_idempotent(self):
        with TempDb():
            init_db()
            first = self._schema_fingerprint()
            init_db()
            init_db()
            self.assertEqual(self._schema_fingerprint(), first)

    def _schema_fingerprint(self):
        repo = Repository()
        try:
            rows = repo._conn.execute(
                "SELECT type, name, sql FROM sqlite_master ORDER BY type, name"
            ).fetchall()
            return [(r["type"], r["name"], r["sql"]) for r in rows]
        finally:
            repo.close()


class ListResolutionEventsTest(unittest.TestCase):
    def test_returns_events_for_the_receipt_newest_first(self):
        with TempDb():
            repo = Repository()
            try:
                repo._conn.execute(
                    "INSERT INTO receipts (receipt_id, firm_id, client_id, message_id, "
                    "filename, file_path, file_hash, status, created_at) "
                    "VALUES ('r-1','INTELLITAX','C1','m1','f.pdf','p','h','ok','now')"
                )
                repo._conn.execute(
                    "INSERT INTO receipts (receipt_id, firm_id, client_id, message_id, "
                    "filename, file_path, file_hash, status, created_at) "
                    "VALUES ('r-2','INTELLITAX','C1','m2','g.pdf','p','h2','ok','now')"
                )
                for event_id, receipt_id, created_at in [
                    ("e-old", "r-1", "2026-07-01T00:00:00+00:00"),
                    ("e-new", "r-1", "2026-07-27T00:00:00+00:00"),
                    ("e-other", "r-2", "2026-07-27T00:00:00+00:00"),
                ]:
                    repo._conn.execute(
                        "INSERT INTO resolution_events (event_id, receipt_id, actor, source, "
                        "action, outcome, created_at) VALUES (?,?,'paul','cli','resolve','filed',?)",
                        (event_id, receipt_id, created_at),
                    )
                repo._conn.commit()

                events = repo.list_resolution_events("r-1")
                self.assertEqual([e["event_id"] for e in events], ["e-new", "e-old"])
                self.assertEqual(events[0]["actor"], "paul")
            finally:
                repo.close()

    def test_returns_an_empty_list_for_a_receipt_with_no_events(self):
        with TempDb():
            repo = Repository()
            try:
                self.assertEqual(repo.list_resolution_events("r-nothing"), [])
            finally:
                repo.close()


if __name__ == "__main__":
    unittest.main()

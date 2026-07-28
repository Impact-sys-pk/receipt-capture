"""Design document test 8: review_count and processed_today come from the database.

_count_review_items() counted files under Clients\\*\\Review\\, so it counted
each pair twice and, because nothing was ever removed, only ever grew.

processed_today was stats["receipts_created"], which is "created in this run",
not "today". repo.count_processed_today() does the real thing and was wired to
nothing.
"""

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import config

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

from worker.database.repository import Repository
from worker.filing import file_review
import app


class TempEnvironment:
    """Temp DB, client root, status file, backups and redirected event logs."""

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved = {
            "DB_PATH": config.DB_PATH,
            "CLIENTS_ROOT": config.CLIENTS_ROOT,
            "CLIENTS_BY_CODE": config.CLIENTS_BY_CODE,
            "LOGS_DIR": config.LOGS_DIR,
            "RUNS_LOG": config.RUNS_LOG,
            "PIPELINE_STATUS_PATH": config.PIPELINE_STATUS_PATH,
            "BACKUPS_ROOT": config.BACKUPS_ROOT,
            "RESOLUTIONS_DIR": config.RESOLUTIONS_DIR,
        }
        config.DB_PATH = self.path / "receipts.db"
        config.CLIENTS_ROOT = self.path / "Clients"
        config.CLIENTS_ROOT.mkdir(parents=True, exist_ok=True)
        config.LOGS_DIR = self.path / "logs"
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
        # IntelliBooks Desktop reads the live status file, and the live backups
        # folder is not somewhere a test should be writing databases.
        config.PIPELINE_STATUS_PATH = self.path / "pipeline-status.json"
        config.BACKUPS_ROOT = self.path / "Backups"
        # process_once() consumes back-feed notes and creates this folder on
        # demand, so without the redirect the suite makes one in OneDrive.
        config.RESOLUTIONS_DIR = self.path / "Resolutions"
        config.CLIENTS_BY_CODE = {
            "ABC": {"client_name": "Test Client", "business_type": "UNSPECIFIED"}
        }
        return self

    def __exit__(self, *exc):
        for name, value in self._saved.items():
            setattr(config, name, value)
        self._temp.cleanup()
        return False

    def seed(self, repo, receipt_id, status, created_at=None):
        file_path = self.path / f"{receipt_id}.pdf"
        file_path.write_text("dummy", encoding="utf-8")
        repo.save_receipt(
            receipt_id=receipt_id,
            message_id=f"msg-{receipt_id}",
            email_subject="Test",
            email_from="sender@example.com",
            email_received_at="2026-01-01T00:00:00Z",
            filename=f"{receipt_id}.pdf",
            file_path=file_path,
            file_hash=f"hash-{receipt_id}",
            firm_id="INTELLITAX",
            client_id="CLIENT001",
            client_code="ABC",
            source="email",
        )
        repo._conn.execute(
            "UPDATE receipts SET status = ? WHERE receipt_id = ?", (status, receipt_id)
        )
        if created_at is not None:
            repo._conn.execute(
                "UPDATE receipts SET created_at = ? WHERE receipt_id = ?",
                (created_at, receipt_id),
            )
        repo._conn.commit()


ALL_STATUSES = [
    ("r-ok", "ok"),
    ("r-discarded", "discarded"),
    ("r-pending", "pending"),
    ("r-failed", "failed"),
    ("r-exhausted", "retry_exhausted"),
    ("r-needs-review", "needs_review"),
    ("r-possible-dup", "possible_duplicate"),
]


class ReviewCountTest(unittest.TestCase):
    def test_counts_needs_review_and_possible_duplicate_only(self):
        # failed and retry_exhausted are not review items: they are receipts the
        # system could not read, and counting them here would send an operator
        # to look at something there is nothing to look at yet.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                for receipt_id, status in ALL_STATUSES:
                    env.seed(repo, receipt_id, status)

                self.assertEqual(app._count_review_items(repo), 2)
                self.assertEqual(
                    repo.count_receipts_by_status(("needs_review", "possible_duplicate")), 2
                )
                self.assertEqual(repo.count_receipts_by_status(("failed",)), 1)
                self.assertEqual(repo.count_receipts_by_status(("retry_exhausted",)), 1)
                self.assertEqual(repo.count_receipts_by_status(()), 0)
            finally:
                repo.close()

    def test_review_files_on_disk_do_not_affect_the_count(self):
        # The old body walked CLIENTS_ROOT.rglob("Review/*") and counted every
        # file, so one review item counted twice and nothing ever came off.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-needs-review", "needs_review")
                before = app._count_review_items(repo)

                source = env.path / "parking.pdf"
                source.write_text("dummy", encoding="utf-8")
                image, sidecar = file_review(
                    source, "Test Client", "parking.pdf", "needs_review",
                    ["missing gross_amount"], {"receipt_id": "r-needs-review"},
                )
                self.assertEqual(app._count_review_items(repo), before)

                image.unlink()
                sidecar.unlink()
                self.assertEqual(app._count_review_items(repo), before)
                self.assertEqual(before, 1)
            finally:
                repo.close()

    def test_no_repo_returns_zero_rather_than_raising(self):
        # The only call site is inside process_once()'s finally block, where a
        # failed Repository() leaves repo as None. Raising there would mask the
        # original error.
        with TempEnvironment():
            self.assertEqual(app._count_review_items(None), 0)


class ProcessedTodayTest(unittest.TestCase):
    def test_status_file_reports_receipts_created_today_not_this_run(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                # Two receipts created today by an earlier run, plus one review
                # item and one possible duplicate for review_count.
                env.seed(repo, "r-earlier-1", "ok")
                env.seed(repo, "r-earlier-2", "needs_review")
                env.seed(repo, "r-possible-dup", "possible_duplicate")
                env.seed(repo, "r-last-week", "ok", created_at="2026-07-01T09:00:00+00:00")
            finally:
                repo.close()

            # This run finds nothing, so stats["receipts_created"] stays 0.
            with patch.object(app, "scan_inbox", return_value=[]), \
                 patch.object(app, "fetch_emails_without_attachments", return_value=[]), \
                 patch.object(app, "fetch_new_messages", return_value=[]):
                app.process_once()

            payload = json.loads(config.PIPELINE_STATUS_PATH.read_text(encoding="utf-8"))

            self.assertEqual(payload["processed_today"], 3, payload)
            self.assertEqual(payload["review_count"], 2, payload)
            self.assertIsNone(payload["last_error"])
            # The shape IntelliBooks Desktop reads must not change.
            self.assertEqual(
                sorted(payload.keys()),
                ["last_error", "last_run", "processed_today", "review_count"],
            )

    def test_count_processed_today_ignores_older_receipts(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-today", "ok")
                env.seed(repo, "r-old", "ok", created_at="2026-07-01T09:00:00+00:00")
                self.assertEqual(repo.count_processed_today(), 1)
            finally:
                repo.close()


if __name__ == "__main__":
    unittest.main()

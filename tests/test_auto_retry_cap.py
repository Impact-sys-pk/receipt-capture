import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

from worker.database.repository import Repository
from worker.categorisation.engine import CategorisationEngine
from worker.extraction.base import ExtractionResult
import app


class FakeExtractor:
    """Always succeeds, so a retried receipt files as 'ok'."""

    def extract(self, file_path, filename):
        return ExtractionResult(
            supplier_name="Recovered Supplier",
            invoice_date="2026-04-01",
            net_amount=80.0,
            vat_amount=16.0,
            gross_amount=96.0,
            currency="GBP",
            raw_response="{}",
            engine="fake_retry",
        )


class AutoRetryCapTest(unittest.TestCase):
    def _make_stuck_receipt(self, repo, temp_path, receipt_id, age_days, client_id):
        file_path = temp_path / f"{receipt_id}.pdf"
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
            source="email",
        )
        repo.save_extraction(
            extraction_id=f"ext-{receipt_id}",
            receipt_id=receipt_id,
            engine="openai_vision",
            supplier_name=None,
            invoice_date=None,
            net_amount=None,
            vat_amount=None,
            gross_amount=None,
            currency="GBP",
            raw_response="{}",
            validation_status="failed",
            validation_notes=["missing supplier_name", "missing gross_amount"],
            pipeline_version="old-pipeline-version",
        )
        # save_receipt/save_extraction always stamp "now"; backdate created_at
        # directly to simulate a receipt that has been stuck for age_days.
        backdated = (datetime.now(timezone.utc) - timedelta(days=age_days)).isoformat()
        repo._conn.execute(
            "UPDATE receipts SET created_at = ? WHERE receipt_id = ?",
            (backdated, receipt_id)
        )
        repo._conn.commit()
        return file_path

    def test_just_under_cutoff_retries_just_over_cutoff_exhausts(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            temp_db = temp_path / "receipts.db"
            temp_client_root = temp_path / "Clients"
            temp_client_root.mkdir(parents=True, exist_ok=True)

            original_db = config.DB_PATH
            original_clients_root = config.CLIENTS_ROOT
            original_clients_by_id = config.CLIENTS_BY_ID
            original_logs_dir = config.LOGS_DIR
            original_runs_log = config.RUNS_LOG

            config.DB_PATH = temp_db
            config.CLIENTS_ROOT = temp_client_root
            # Event logs resolve config.LOGS_DIR at call time. Without this the
            # suite appends synthetic rows to the live operational logs that
            # the console's intake panel reads as real intake problems.
            config.LOGS_DIR = temp_path / "logs"
            config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
            config.CLIENTS_BY_ID = {
                "CLIENT001": {"client_name": "Test Client", "client_folder_name": "Test Client",
                          "client_id": "CLIENT001", "firm_id": "INTELLITAX", "trade": "UNSPECIFIED"}
            }

            repo = None
            try:
                repo = Repository()
                recent_id = "recent-receipt"
                old_id = "old-receipt"

                self._make_stuck_receipt(repo, temp_path, recent_id, age_days=6.9, client_id="CLIENT001")
                self._make_stuck_receipt(repo, temp_path, old_id, age_days=7.1, client_id="CLIENT001")

                engine = CategorisationEngine(repo=repo, enable_ai_fallback=False)
                stats = {}
                app._retry_failed_receipts(
                    repo=repo,
                    extractor=FakeExtractor(),
                    categorisation_engine=engine,
                    stats=stats,
                    run_id="test-run",
                    pipeline_version="new-pipeline-version",
                )

                recent_row = repo._conn.execute(
                    "SELECT status, filed_path FROM receipts WHERE receipt_id = ?",
                    (recent_id,)
                ).fetchone()
                old_row = repo._conn.execute(
                    "SELECT status, filed_path FROM receipts WHERE receipt_id = ?",
                    (old_id,)
                ).fetchone()

                # Just under the cutoff: retried and filed.
                self.assertEqual(recent_row["status"], "ok")
                self.assertIsNotNone(recent_row["filed_path"])

                # Just over the cutoff: not retried, transitioned instead.
                self.assertEqual(old_row["status"], "retry_exhausted")
                self.assertIsNone(old_row["filed_path"])

                self.assertEqual(stats.get("retry_exhausted_count"), 1)
                self.assertEqual(stats.get("auto_retried_ok"), 1)
            finally:
                if repo is not None:
                    repo.close()
                config.DB_PATH = original_db
                config.CLIENTS_ROOT = original_clients_root
                config.CLIENTS_BY_ID = original_clients_by_id
                config.LOGS_DIR = original_logs_dir
                config.RUNS_LOG = original_runs_log

    def test_exhausted_receipt_is_not_reconsidered_on_next_run(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            temp_db = temp_path / "receipts.db"
            temp_client_root = temp_path / "Clients"
            temp_client_root.mkdir(parents=True, exist_ok=True)

            original_db = config.DB_PATH
            original_clients_root = config.CLIENTS_ROOT
            original_clients_by_id = config.CLIENTS_BY_ID
            original_logs_dir = config.LOGS_DIR
            original_runs_log = config.RUNS_LOG

            config.DB_PATH = temp_db
            config.CLIENTS_ROOT = temp_client_root
            # Event logs resolve config.LOGS_DIR at call time. Without this the
            # suite appends synthetic rows to the live operational logs that
            # the console's intake panel reads as real intake problems.
            config.LOGS_DIR = temp_path / "logs"
            config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
            config.CLIENTS_BY_ID = {
                "CLIENT001": {"client_name": "Test Client", "client_folder_name": "Test Client",
                          "client_id": "CLIENT001", "firm_id": "INTELLITAX", "trade": "UNSPECIFIED"}
            }

            repo = None
            try:
                repo = Repository()
                old_id = "old-receipt-2"
                self._make_stuck_receipt(repo, temp_path, old_id, age_days=10, client_id="CLIENT001")

                engine = CategorisationEngine(repo=repo, enable_ai_fallback=False)

                stats_first = {}
                app._retry_failed_receipts(
                    repo=repo, extractor=FakeExtractor(), categorisation_engine=engine,
                    stats=stats_first, run_id="run-1", pipeline_version="new-pipeline-version",
                )
                self.assertEqual(stats_first.get("retry_exhausted_count"), 1)

                # Second run: query no longer returns it (status != failed/needs_review),
                # so it isn't re-examined or re-counted.
                stats_second = {}
                app._retry_failed_receipts(
                    repo=repo, extractor=FakeExtractor(), categorisation_engine=engine,
                    stats=stats_second, run_id="run-2", pipeline_version="new-pipeline-version",
                )
                self.assertEqual(stats_second.get("retry_exhausted_count", 0), 0)
            finally:
                if repo is not None:
                    repo.close()
                config.DB_PATH = original_db
                config.CLIENTS_ROOT = original_clients_root
                config.CLIENTS_BY_ID = original_clients_by_id
                config.LOGS_DIR = original_logs_dir
                config.RUNS_LOG = original_runs_log


if __name__ == "__main__":
    unittest.main()

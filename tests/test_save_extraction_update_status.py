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


class SaveExtractionUpdateStatusTest(unittest.TestCase):
    """save_extraction(update_status=False) records the attempt without
    re-stamping receipts.status.

    The auto-retry exception path needs this: a crashed API call is
    information about the API, not about the document, so it must not flip a
    needs_review receipt to failed.
    """

    def _seed(self, repo, receipt_id, temp_path, status):
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
        repo.update_receipt_status(receipt_id, status)

    def _status(self, repo, receipt_id):
        return repo._conn.execute(
            "SELECT status FROM receipts WHERE receipt_id = ?", (receipt_id,)
        ).fetchone()["status"]

    def test_update_status_false_leaves_receipt_status_untouched(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            original_db = config.DB_PATH
            config.DB_PATH = temp_path / "receipts.db"
            repo = None
            try:
                repo = Repository()
                receipt_id = "r-keep-status"
                self._seed(repo, receipt_id, temp_path, "needs_review")

                repo.save_extraction(
                    extraction_id="ext-crashed-retry",
                    receipt_id=receipt_id,
                    engine="openai_vision",
                    supplier_name=None,
                    invoice_date=None,
                    net_amount=None,
                    vat_amount=None,
                    gross_amount=None,
                    currency="GBP",
                    raw_response="boom",
                    validation_status="failed",
                    validation_notes=["auto-retry extraction error: boom"],
                    pipeline_version="v-current",
                    update_status=False,
                )

                # The row is recorded...
                row = repo._conn.execute(
                    "SELECT validation_status, pipeline_version FROM extractions WHERE extraction_id = ?",
                    ("ext-crashed-retry",)
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row["validation_status"], "failed")
                self.assertEqual(row["pipeline_version"], "v-current")

                # ...but the receipt keeps the status the document earned.
                self.assertEqual(self._status(repo, receipt_id), "needs_review")
            finally:
                if repo is not None:
                    repo.close()
                config.DB_PATH = original_db

    def test_default_still_updates_receipt_status(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            original_db = config.DB_PATH
            config.DB_PATH = temp_path / "receipts.db"
            repo = None
            try:
                repo = Repository()
                receipt_id = "r-follow-status"
                self._seed(repo, receipt_id, temp_path, "needs_review")

                repo.save_extraction(
                    extraction_id="ext-normal",
                    receipt_id=receipt_id,
                    engine="openai_vision",
                    supplier_name="Supplier",
                    invoice_date="2026-04-01",
                    net_amount=80.0,
                    vat_amount=16.0,
                    gross_amount=96.0,
                    currency="GBP",
                    raw_response="{}",
                    validation_status="ok",
                    validation_notes=[],
                    pipeline_version="v-current",
                )

                # Default behaviour is unchanged: status follows validation_status.
                self.assertEqual(self._status(repo, receipt_id), "ok")
            finally:
                if repo is not None:
                    repo.close()
                config.DB_PATH = original_db


if __name__ == "__main__":
    unittest.main()

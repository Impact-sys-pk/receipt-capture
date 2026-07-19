import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

os.environ.setdefault("IMAP_HOST", "example.com")
os.environ.setdefault("IMAP_USERNAME", "test@example.com")
os.environ.setdefault("IMAP_PASSWORD", "password")
os.environ.setdefault("OPENAI_API_KEY", "testkey")

# Stub openai module so app can import without the dependency.
fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules["openai"] = fake_openai

import config
from worker.database.repository import Repository
from worker.intake.folder_reader import scan_inbox
from worker.extraction.base import ExtractionResult
import app
import unittest.mock as mock


class CaptureInboxCleanupTest(unittest.TestCase):
    def test_remove_hash_duplicate_inbox_pair_for_filed_receipt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            temp_inbox = temp_path / "Receipt Inbox"
            temp_clients_root = temp_path / "Clients"
            temp_db = temp_path / "receipts.db"
            temp_inbox.mkdir(parents=True, exist_ok=True)
            temp_clients_root.mkdir(parents=True, exist_ok=True)

            original_inbox = config.RECEIPT_INBOX_ROOT
            original_clients_root = config.CLIENTS_ROOT
            original_db = config.DB_PATH
            original_clients_by_code = config.CLIENTS_BY_CODE

            config.RECEIPT_INBOX_ROOT = temp_inbox
            config.CLIENTS_ROOT = temp_clients_root
            config.DB_PATH = temp_db
            config.CLIENTS_BY_CODE = {"ABC": {"client_name": "Test Client", "client_id": "CLIENT001", "firm_id": "FIRM001"}}

            try:
                client_dir = temp_inbox / "ABC"
                client_dir.mkdir(parents=True, exist_ok=True)

                receipt_file = client_dir / "duplicate.pdf"
                receipt_file.write_text("dummy receipt content", encoding="utf-8")
                sidecar_file = client_dir / "duplicate.json"
                sidecar_file.write_text('{"type":"capture"}', encoding="utf-8")

                receipt_dir = temp_path / "stored"
                receipt_dir.mkdir(parents=True, exist_ok=True)

                repo = Repository()
                try:
                    actual_hash = app.compute_hash(receipt_file.read_bytes())

                    receipt_id = "receipt-duplicate-001"
                    repo.save_receipt(
                        receipt_id=receipt_id,
                        message_id="capture:duplicate.pdf",
                        email_subject=None,
                        email_from=None,
                        email_received_at="2026-07-17T00:00:00Z",
                        filename="duplicate.pdf",
                        file_path=receipt_dir / "duplicate.pdf",
                        file_hash=actual_hash,
                        firm_id="FIRM001",
                        client_id="CLIENT001",
                        client_code="ABC",
                        source="capture",
                    )
                    repo.mark_receipt_filed(receipt_id, str(temp_path / "filed" / "duplicate.pdf"))

                    intake_records = scan_inbox()
                    self.assertEqual(len(intake_records), 1)
                    intake = intake_records[0]
                    self.assertIsNotNone(intake.sidecar_path)
                    self.assertTrue(repo.is_recorded_and_filed(intake.file_hash))

                    app._remove_inbox_pair(intake)
                    self.assertFalse(receipt_file.exists())
                    self.assertFalse(sidecar_file.exists())
                finally:
                    repo.close()
            finally:
                config.RECEIPT_INBOX_ROOT = original_inbox
                config.CLIENTS_ROOT = original_clients_root
                config.DB_PATH = original_db
                config.CLIENTS_BY_CODE = original_clients_by_code

    def test_remove_hash_duplicate_inbox_statement_pair(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            temp_inbox = temp_path / "Receipt Inbox"
            temp_clients_root = temp_path / "Clients"
            temp_db = temp_path / "receipts.db"
            temp_inbox.mkdir(parents=True, exist_ok=True)
            temp_clients_root.mkdir(parents=True, exist_ok=True)

            original_inbox = config.RECEIPT_INBOX_ROOT
            original_clients_root = config.CLIENTS_ROOT
            original_db = config.DB_PATH
            original_clients_by_code = config.CLIENTS_BY_CODE

            config.RECEIPT_INBOX_ROOT = temp_inbox
            config.CLIENTS_ROOT = temp_clients_root
            config.DB_PATH = temp_db
            config.CLIENTS_BY_CODE = {"ABC": {"client_name": "Test Client", "client_id": "CLIENT001", "firm_id": "FIRM001"}}

            try:
                client_dir = temp_inbox / "ABC"
                client_dir.mkdir(parents=True, exist_ok=True)

                statement_file = client_dir / "stmt_001.pdf"
                statement_file.write_text("dummy statement content", encoding="utf-8")
                sidecar_file = client_dir / "stmt_001.json"
                sidecar_file.write_text('{"type":"statement","platform":"Xero","week_ending":"2026-07-10"}', encoding="utf-8")

                repo = Repository()
                try:
                    actual_hash = app.compute_hash(statement_file.read_bytes())
                    statement_id = "statement-001"
                    repo.save_statement(
                        statement_id=statement_id,
                        client_id="CLIENT001",
                        client_code="ABC",
                        platform="Xero",
                        week_ending="2026-07-10",
                        source="capture",
                        file_hash=actual_hash,
                        file_path=temp_path / "filed" / "stmt_001.pdf",
                    )

                    intake_records = scan_inbox()
                    self.assertEqual(len(intake_records), 1)
                    intake = intake_records[0]
                    self.assertTrue(intake.is_statement)
                    self.assertIsNotNone(intake.sidecar_path)

                    app._remove_inbox_pair(intake)
                    self.assertFalse(statement_file.exists())
                    self.assertFalse(sidecar_file.exists())
                finally:
                    repo.close()
            finally:
                config.RECEIPT_INBOX_ROOT = original_inbox
                config.CLIENTS_ROOT = original_clients_root
                config.DB_PATH = original_db
                config.CLIENTS_BY_CODE = original_clients_by_code

    def test_failed_capture_receipt_routes_to_review_and_clears_inbox(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            temp_inbox = temp_path / "Receipt Inbox"
            temp_clients_root = temp_path / "Clients"
            temp_db = temp_path / "receipts.db"
            temp_inbox.mkdir(parents=True, exist_ok=True)
            temp_clients_root.mkdir(parents=True, exist_ok=True)

            original_inbox = config.RECEIPT_INBOX_ROOT
            original_clients_root = config.CLIENTS_ROOT
            original_db = config.DB_PATH
            original_clients_by_code = config.CLIENTS_BY_CODE

            config.RECEIPT_INBOX_ROOT = temp_inbox
            config.CLIENTS_ROOT = temp_clients_root
            config.DB_PATH = temp_db
            config.CLIENTS_BY_CODE = {"ABC": {"client_name": "Test Client", "client_id": "CLIENT001", "firm_id": "FIRM001"}}

            try:
                client_dir = temp_inbox / "ABC"
                client_dir.mkdir(parents=True, exist_ok=True)

                receipt_file = client_dir / "capture_001.pdf"
                receipt_file.write_text("dummy receipt content", encoding="utf-8")

                repo = Repository()
                try:
                    config.BACKUPS_ROOT = temp_path / "Backups"
                    config.PIPELINE_STATUS_PATH = temp_path / "pipeline-status.json"
                    config.BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)

                    with mock.patch.object(app, "fetch_new_messages", return_value=[]), \
                         mock.patch.object(app.OpenAIVisionExtractor, "extract", return_value=ExtractionResult(
                             supplier_name=None,
                             invoice_date=None,
                             net_amount=None,
                             vat_amount=None,
                             gross_amount=None,
                             currency='GBP',
                             raw_response='{}',
                             engine='openai_vision'
                         )):
                        app.process_once()

                    self.assertFalse(receipt_file.exists())
                    self.assertFalse((client_dir / 'Review').exists())

                    review_folder = temp_clients_root / 'Test Client' / 'Review'
                    self.assertTrue(review_folder.exists())
                    self.assertTrue(any(review_folder.iterdir()))
                finally:
                    repo.close()
            finally:
                config.RECEIPT_INBOX_ROOT = original_inbox
                config.CLIENTS_ROOT = original_clients_root
                config.DB_PATH = original_db
                config.CLIENTS_BY_CODE = original_clients_by_code


if __name__ == "__main__":
    unittest.main()

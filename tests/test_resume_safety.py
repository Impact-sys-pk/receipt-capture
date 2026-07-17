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

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules["openai"] = fake_openai

import config
from worker.database.repository import Repository
import app


class ResumeSafetyTest(unittest.TestCase):
    def test_recover_validated_receipt_without_filed_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            temp_db = temp_path / "receipts.db"
            temp_client_root = temp_path / "Clients"
            temp_client_root.mkdir(parents=True, exist_ok=True)

            original_db = config.DB_PATH
            original_clients_root = config.CLIENTS_ROOT
            original_clients_by_code = config.CLIENTS_BY_CODE

            config.DB_PATH = temp_db
            config.CLIENTS_ROOT = temp_client_root
            config.CLIENTS_BY_CODE = {}

            try:
                repo = Repository()
                receipt_id = "test-receipt-001"
                file_path = temp_path / "test-receipt.pdf"
                file_path.write_text("dummy", encoding="utf-8")

                repo.save_receipt(
                    receipt_id=receipt_id,
                    message_id="msg-001",
                    email_subject="Test",
                    email_from="sender@example.com",
                    email_received_at="2026-01-01T00:00:00Z",
                    filename="test-receipt.pdf",
                    file_path=file_path,
                    file_hash="hash1",
                    firm_id="INTELLITAX",
                    client_id="CLIENT001",
                    client_code="UNKNOWN",
                    source="email",
                )

                repo.save_extraction(
                    extraction_id="ext-001",
                    receipt_id=receipt_id,
                    engine="openai_vision",
                    supplier_name="Test Supplier",
                    invoice_date="2026-04-01",
                    net_amount=100.0,
                    vat_amount=20.0,
                    gross_amount=120.0,
                    currency="GBP",
                    raw_response="{}",
                    validation_status="ok",
                    validation_notes=["ok"],
                )

                receipts = repo.get_unfiled_ok_receipts()
                self.assertEqual(len(receipts), 1)
                stats = {}
                app._file_unfiled_ok_receipts(repo, stats)

                self.assertEqual(stats.get("recovery_filed"), 1)
                row = repo._conn.execute(
                    "SELECT filed_path FROM receipts WHERE receipt_id = ?",
                    (receipt_id,)
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertIsNotNone(row["filed_path"])

                filed_path = Path(row["filed_path"])
                self.assertTrue(filed_path.exists())
            finally:
                if repo is not None:
                    repo.close()
                config.DB_PATH = original_db
                config.CLIENTS_ROOT = original_clients_root
                config.CLIENTS_BY_CODE = original_clients_by_code


if __name__ == "__main__":
    unittest.main()

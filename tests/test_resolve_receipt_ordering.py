import contextlib
import io
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
import resolve_receipt


class ResolveReceiptOrderingTest(unittest.TestCase):
    def test_manual_correction_files_without_fk_violation(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            temp_db = temp_path / "receipts.db"
            temp_client_root = temp_path / "Clients"
            temp_client_root.mkdir(parents=True, exist_ok=True)

            original_db = config.DB_PATH
            original_clients_root = config.CLIENTS_ROOT
            original_clients_by_code = config.CLIENTS_BY_CODE
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
            config.CLIENTS_BY_CODE = {
                "ABC": {"client_name": "Test Client", "business_type": "UNSPECIFIED"}
            }

            repo = None
            try:
                repo = Repository()
                receipt_id = "test-receipt-002"
                file_path = temp_path / "test-receipt.pdf"
                file_path.write_text("dummy", encoding="utf-8")

                repo.save_receipt(
                    receipt_id=receipt_id,
                    message_id="msg-002",
                    email_subject="Test",
                    email_from="sender@example.com",
                    email_received_at="2026-01-01T00:00:00Z",
                    filename="test-receipt.pdf",
                    file_path=file_path,
                    file_hash="hash2",
                    firm_id="INTELLITAX",
                    client_id="CLIENT001",
                    client_code="ABC",
                    source="email",
                )
                repo.save_extraction(
                    extraction_id="ext-original",
                    receipt_id=receipt_id,
                    engine="openai_vision",
                    supplier_name=None,
                    invoice_date="2026-04-01",
                    net_amount=None,
                    vat_amount=None,
                    gross_amount=None,
                    currency="GBP",
                    raw_response="{}",
                    validation_status="needs_review",
                    validation_notes=["missing supplier_name", "missing gross_amount"],
                )
                repo.close()

                test_argv = [
                    "resolve_receipt.py",
                    receipt_id,
                    "--supplier", "T3 Test Supplies Ltd",
                    "--gross", "96.00",
                ]
                # Redirect stdout: this test environment's console codepage can't
                # encode the script's checkmark output, which is unrelated to the
                # FK-ordering behaviour under test.
                with patch.object(sys, "argv", test_argv), contextlib.redirect_stdout(io.StringIO()):
                    exit_code = resolve_receipt.main()

                self.assertEqual(exit_code, 0)

                repo = Repository()
                row = repo._conn.execute(
                    "SELECT status, filed_path FROM receipts WHERE receipt_id = ?",
                    (receipt_id,)
                ).fetchone()
                self.assertEqual(row["status"], "ok")
                self.assertIsNotNone(row["filed_path"])
                self.assertTrue(Path(row["filed_path"]).exists())

                cat_row = repo._conn.execute(
                    "SELECT extraction_id FROM categorisations WHERE receipt_id = ?",
                    (receipt_id,)
                ).fetchone()
                self.assertIsNotNone(cat_row)

                extraction_row = repo._conn.execute(
                    "SELECT extraction_id FROM extractions WHERE extraction_id = ?",
                    (cat_row["extraction_id"],)
                ).fetchone()
                self.assertIsNotNone(extraction_row, "categorisation must reference an extraction row that exists")
            finally:
                if repo is not None:
                    repo.close()
                config.DB_PATH = original_db
                config.CLIENTS_ROOT = original_clients_root
                config.CLIENTS_BY_CODE = original_clients_by_code
                config.LOGS_DIR = original_logs_dir
                config.RUNS_LOG = original_runs_log

    def test_still_invalid_after_correction_records_note_without_crash(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            temp_db = temp_path / "receipts.db"
            temp_client_root = temp_path / "Clients"
            temp_client_root.mkdir(parents=True, exist_ok=True)

            original_db = config.DB_PATH
            original_clients_root = config.CLIENTS_ROOT
            original_clients_by_code = config.CLIENTS_BY_CODE
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
            config.CLIENTS_BY_CODE = {
                "ABC": {"client_name": "Test Client", "business_type": "UNSPECIFIED"}
            }

            repo = None
            try:
                repo = Repository()
                receipt_id = "test-receipt-003"
                file_path = temp_path / "test-receipt.pdf"
                file_path.write_text("dummy", encoding="utf-8")

                repo.save_receipt(
                    receipt_id=receipt_id,
                    message_id="msg-003",
                    email_subject="Test",
                    email_from="sender@example.com",
                    email_received_at="2026-01-01T00:00:00Z",
                    filename="test-receipt.pdf",
                    file_path=file_path,
                    file_hash="hash3",
                    firm_id="INTELLITAX",
                    client_id="CLIENT001",
                    client_code="ABC",
                    source="email",
                )
                repo.save_extraction(
                    extraction_id="ext-original-3",
                    receipt_id=receipt_id,
                    engine="openai_vision",
                    supplier_name=None,
                    invoice_date="2026-04-01",
                    net_amount=None,
                    vat_amount=None,
                    gross_amount=None,
                    currency="GBP",
                    raw_response="{}",
                    validation_status="failed",
                    validation_notes=["missing supplier_name", "missing gross_amount"],
                )
                repo.close()

                # Correct supplier only; gross_amount is still missing, so
                # validation still fails and resolve_receipt.py must hit its
                # add_validation_note() call instead of crashing.
                test_argv = [
                    "resolve_receipt.py",
                    receipt_id,
                    "--supplier", "T3 Test Supplies Ltd",
                ]
                with patch.object(sys, "argv", test_argv), contextlib.redirect_stdout(io.StringIO()):
                    exit_code = resolve_receipt.main()

                self.assertEqual(exit_code, 1)

                repo = Repository()
                extraction_row = repo._conn.execute(
                    "SELECT validation_notes FROM extractions WHERE extraction_id = ?",
                    ("ext-original-3",)
                ).fetchone()
                self.assertIn("Manual correction attempted", extraction_row["validation_notes"])
            finally:
                if repo is not None:
                    repo.close()
                config.DB_PATH = original_db
                config.CLIENTS_ROOT = original_clients_root
                config.CLIENTS_BY_CODE = original_clients_by_code
                config.LOGS_DIR = original_logs_dir
                config.RUNS_LOG = original_runs_log


if __name__ == "__main__":
    unittest.main()

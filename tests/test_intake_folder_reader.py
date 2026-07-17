import json
import tempfile
import unittest
from pathlib import Path

import config
from worker.intake.folder_reader import scan_inbox


class FolderReaderTest(unittest.TestCase):
    def test_scan_inbox_missing_sidecar_still_detects_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            receipt_inbox = temp_path / "Receipt Inbox"
            client_folder = receipt_inbox / "ABC"
            client_folder.mkdir(parents=True)

            # Create a receipt file without any accompanying sidecar
            receipt_file = client_folder / "rcpt_123.pdf"
            receipt_file.write_text("dummy pdf content", encoding="utf-8")

            # Replace config values for the test environment
            original_inbox = config.RECEIPT_INBOX_ROOT
            original_client_map = config.CLIENTS_BY_CODE
            config.RECEIPT_INBOX_ROOT = receipt_inbox
            config.CLIENTS_BY_CODE = {"ABC": {"client_name": "Test Client", "client_id": "CLIENT001", "firm_id": "FIRM001"}}

            try:
                intake_records = scan_inbox()
                self.assertEqual(len(intake_records), 1)
                intake = intake_records[0]
                self.assertEqual(intake.client_code, "ABC")
                self.assertEqual(intake.filename, "rcpt_123.pdf")
                self.assertFalse(intake.is_statement)
                self.assertIsNone(intake.sidecar)
                self.assertIsNone(intake.sidecar_path)
            finally:
                config.RECEIPT_INBOX_ROOT = original_inbox
                config.CLIENTS_BY_CODE = original_client_map


if __name__ == "__main__":
    unittest.main()

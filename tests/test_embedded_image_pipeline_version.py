"""Design document 3.12: the embedded-image path must stamp pipeline_version.

find_failed_by_version() treats a NULL pipeline_version on the latest extraction
as eligible for retry, so a receipt written without it is re-extracted on the next
poll whatever the version. That is three OpenAI calls for nothing per affected
receipt, self-correcting after one retry because the retry writes a versioned row.

The assertion is "not selected for retry on a second pass", not "the column is
non-null", because that is what the defect actually costs and it catches the whole
family rather than one column.
"""

import base64
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone
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
from worker.extraction.base import BaseExtractor, ExtractionResult
import app

VERSION = "test-version-1"


class NeedsReviewExtractor(BaseExtractor):
    """Returns a result that validates as needs_review: no supplier, valid date and gross."""

    @property
    def name(self) -> str:
        return "stub_engine"

    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        return ExtractionResult(
            engine=self.name,
            supplier_name=None,
            invoice_date="2026-04-01",
            net_amount=None,
            vat_amount=None,
            gross_amount=12.0,
            currency="GBP",
            raw_response="{}",
        )


class TempEnvironment:
    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved = {
            "DB_PATH": config.DB_PATH,
            "CLIENTS_ROOT": config.CLIENTS_ROOT,
            "CLIENTS_BY_CODE": config.CLIENTS_BY_CODE,
            "CLIENTS": config.CLIENTS,
            "FILES_DIR": config.FILES_DIR,
            "LOGS_DIR": config.LOGS_DIR,
            "RUNS_LOG": config.RUNS_LOG,
            "PIPELINE_STATUS_PATH": config.PIPELINE_STATUS_PATH,
            "BACKUPS_ROOT": config.BACKUPS_ROOT,
            "RESOLUTIONS_DIR": config.RESOLUTIONS_DIR,
        }
        config.DB_PATH = self.path / "receipts.db"
        config.CLIENTS_ROOT = self.path / "Clients"
        config.CLIENTS_ROOT.mkdir(parents=True, exist_ok=True)
        config.FILES_DIR = self.path / "files"
        config.FILES_DIR.mkdir(parents=True, exist_ok=True)
        config.LOGS_DIR = self.path / "logs"
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
        config.PIPELINE_STATUS_PATH = self.path / "pipeline-status.json"
        config.BACKUPS_ROOT = self.path / "Backups"
        # process_once() consumes back-feed notes and creates this folder on
        # demand, so without the redirect the suite makes one in OneDrive.
        config.RESOLUTIONS_DIR = self.path / "Resolutions"
        config.CLIENTS_BY_CODE = {
            "ABC": {
                "client_name": "Test Client", "business_type": "UNSPECIFIED",
                "client_id": "CLIENT001", "firm_id": "INTELLITAX", "client_code": "ABC",
            }
        }
        config.CLIENTS = {
            "sender@example.com": {
                "client_id": "CLIENT001", "firm_id": "INTELLITAX", "client_code": "ABC",
            }
        }
        return self

    def __exit__(self, *exc):
        for name, value in self._saved.items():
            setattr(config, name, value)
        self._temp.cleanup()
        return False


def _embedded_image_run(extractor):
    email_msg = {
        "id": "msg-embedded", "uid": 7, "subject": "receipt",
        "from": "sender@example.com",
        "receivedDateTime": "2026-07-27T00:00:00Z",
        "msg": None,
    }
    embedded = {
        "id": "emb-1", "name": "photo.jpg",
        "contentBytes": base64.standard_b64encode(b"dummy").decode(),
    }
    stubs = {
        "scan_inbox": lambda *a, **k: [],
        "fetch_emails_without_attachments": lambda *a, **k: [email_msg],
        "extract_embedded_images": lambda *a, **k: [embedded],
        "fetch_new_messages": lambda *a, **k: [],
        "fetch_attachments": lambda *a, **k: [],
        "move_email_to_folder": lambda *a, **k: None,
        "send_no_attachment_alert": lambda *a, **k: False,
        "send_unknown_sender_alert": lambda *a, **k: False,
        "get_extractor": lambda *a, **k: extractor,
    }
    patches = [patch.object(app, name, value) for name, value in stubs.items()]
    patches.append(patch.object(config, "get_pipeline_version", lambda: VERSION))
    patches.append(patch("worker.extraction.retry_helper.time.sleep", lambda seconds: None))
    for p in patches:
        p.start()
    try:
        app.process_once()
    finally:
        for p in reversed(patches):
            p.stop()


class EmbeddedImagePipelineVersionTest(unittest.TestCase):
    def _retry_candidates(self):
        repo = Repository()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=60)
            return [r["receipt_id"] for r in repo.find_failed_by_version(VERSION, cutoff)]
        finally:
            repo.close()

    def test_needs_review_receipt_is_not_retried_under_the_same_version(self):
        with TempEnvironment():
            _embedded_image_run(NeedsReviewExtractor())

            repo = Repository()
            try:
                rows = repo._conn.execute(
                    "SELECT receipt_id, status FROM receipts"
                ).fetchall()
                self.assertEqual(len(rows), 1, "the embedded image should have created one receipt")
                self.assertEqual(rows[0]["status"], "needs_review")
            finally:
                repo.close()

            # Nothing has changed, so a second pass under the same version must
            # not select it. A NULL pipeline_version makes it eligible forever.
            self.assertEqual(self._retry_candidates(), [])

    def test_the_stamped_version_is_the_running_one(self):
        with TempEnvironment():
            _embedded_image_run(NeedsReviewExtractor())
            repo = Repository()
            try:
                row = repo._conn.execute(
                    "SELECT pipeline_version FROM extractions"
                ).fetchone()
                self.assertEqual(row["pipeline_version"], VERSION)
            finally:
                repo.close()


if __name__ == "__main__":
    unittest.main()

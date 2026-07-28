"""Design document 3.8: failure paths must record the engine that actually ran.

Three save_extraction() calls in process_once() hardcoded engine="openai_vision"
on their failure branches, so after any provider change the extractions table
would say OpenAI produced a failure that a different provider produced.

The test drives all three paths with a stub extractor whose name is not
openai_vision. A hardcoded string passes every test that uses the real extractor,
which is why the defect survived this long.
"""

import base64
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
from worker.extraction.base import BaseExtractor, ExtractionResult
from worker.intake.folder_reader import IntakeRecord
import app


class RaisingStubExtractor(BaseExtractor):
    """Fails the way a provider outage does, under a name that is not OpenAI's."""

    @property
    def name(self) -> str:
        return "stub_engine"

    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        raise RuntimeError("simulated provider failure")


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

    def engines_recorded(self):
        """Every engine string written to extractions, with its status."""
        repo = Repository()
        try:
            rows = repo._conn.execute(
                "SELECT engine, validation_status FROM extractions"
            ).fetchall()
            return [(r["engine"], r["validation_status"]) for r in rows]
        finally:
            repo.close()


def _run_process_once(**overrides):
    """process_once() with the stub extractor and everything external stubbed off."""
    # *a, **k throughout: these are real signatures in app.py, e.g.
    # fetch_new_messages(repo), and the test is not about how they are called.
    stubs = {
        "scan_inbox": lambda *a, **k: [],
        "fetch_emails_without_attachments": lambda *a, **k: [],
        "fetch_new_messages": lambda *a, **k: [],
        "fetch_attachments": lambda *a, **k: [],
        "extract_embedded_images": lambda *a, **k: [],
        "move_email_to_folder": lambda *a, **k: None,
        "send_no_attachment_alert": lambda *a, **k: False,
        "send_unknown_sender_alert": lambda *a, **k: False,
    }
    stubs.update(overrides)
    patches = [patch.object(app, name, value) for name, value in stubs.items()]
    patches.append(patch.object(app, "get_extractor", lambda *a, **k: RaisingStubExtractor()))
    # The capture-inbox path goes through extract_with_transient_retry, whose
    # exponential back-off sleeps 2s then 4s. The recorded engine is what is
    # under test, not the timing, and 6s per call is 10x the whole suite.
    patches.append(patch("worker.extraction.retry_helper.time.sleep", lambda seconds: None))
    for p in patches:
        p.start()
    try:
        app.process_once()
    finally:
        for p in reversed(patches):
            p.stop()


class FailurePathEngineTest(unittest.TestCase):
    def test_email_attachment_failure_records_the_running_engine(self):
        # app.py:962
        message = {
            "id": "msg-1", "uid": 1, "subject": "receipt",
            "from": {"emailAddress": {"address": "sender@example.com"}},
            "receivedDateTime": "2026-07-27T00:00:00Z",
            "msg": None,
        }
        attachment = {
            "id": "att-1", "name": "receipt.pdf",
            "contentBytes": base64.standard_b64encode(b"dummy").decode(),
        }
        with TempEnvironment() as env:
            _run_process_once(
                fetch_new_messages=lambda *a, **k: [message],
                fetch_attachments=lambda *a, **k: [attachment],
            )
            recorded = env.engines_recorded()

        self.assertEqual(recorded, [("stub_engine", "failed")], recorded)

    def test_embedded_image_failure_records_the_running_engine(self):
        # app.py:612
        email_msg = {
            "id": "msg-2", "uid": 2, "subject": "receipt",
            "from": "sender@example.com",
            "receivedDateTime": "2026-07-27T00:00:00Z",
            "msg": None,
        }
        embedded = {
            "id": "emb-1", "name": "photo.jpg",
            "contentBytes": base64.standard_b64encode(b"dummy").decode(),
        }
        with TempEnvironment() as env:
            _run_process_once(
                fetch_emails_without_attachments=lambda *a, **k: [email_msg],
                extract_embedded_images=lambda *a, **k: [embedded],
            )
            recorded = env.engines_recorded()

        self.assertEqual(recorded, [("stub_engine", "failed")], recorded)

    def test_capture_inbox_failure_records_the_running_engine(self):
        # app.py:791
        with TempEnvironment() as env:
            source = env.path / "inbox-receipt.pdf"
            source.write_text("dummy", encoding="utf-8")
            intake = IntakeRecord(
                source="folder",
                client_code="ABC",
                client_id="CLIENT001",
                firm_id="INTELLITAX",
                source_path=source,
                filename="inbox-receipt.pdf",
                file_hash="hash-inbox",
                sidecar_path=None,
                sidecar=None,
                original_name="inbox-receipt.pdf",
                is_statement=False,
                statement_metadata=None,
            )
            _run_process_once(scan_inbox=lambda *a, **k: [intake])
            recorded = env.engines_recorded()

        self.assertEqual(recorded, [("stub_engine", "failed")], recorded)

    def test_no_path_records_openai_when_a_different_engine_ran(self):
        # The assertion that would have failed before this fix, stated directly.
        message = {
            "id": "msg-3", "uid": 3, "subject": "receipt",
            "from": {"emailAddress": {"address": "sender@example.com"}},
            "receivedDateTime": "2026-07-27T00:00:00Z",
            "msg": None,
        }
        attachment = {
            "id": "att-3", "name": "receipt.pdf",
            "contentBytes": base64.standard_b64encode(b"dummy").decode(),
        }
        with TempEnvironment() as env:
            _run_process_once(
                fetch_new_messages=lambda *a, **k: [message],
                fetch_attachments=lambda *a, **k: [attachment],
            )
            engines = [engine for engine, _ in env.engines_recorded()]

        self.assertNotIn("openai_vision", engines)


if __name__ == "__main__":
    unittest.main()

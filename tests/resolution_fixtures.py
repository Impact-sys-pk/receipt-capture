"""Shared fixtures for the resolution tests.

Not named test_*, so neither runner collects it. Imported by the resolution test
modules the way tests/test_prefer_dayfirst_isolation.py imports its subjects.

Every environment redirects config.LOGS_DIR and config.RUNS_LOG as well as
DB_PATH: the console's intake panel reads the live event logs, so a synthetic row
there reads as a real intake problem, and RUNS_LOG resolves from LOGS_DIR at
import so redirecting one does not move the other.

It also redirects every path that lives under OneDrive: the Receipt Inbox, the
practice status file, the backup folder and the Resolutions folder. A test that
drives process_once() writes all four, and three of them are read by IntelliBooks
Desktop.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import config

from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.resolution.service import parse_corrections

VERSION = "test-version"


class TempEnvironment:
    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved = {
            "DB_PATH": config.DB_PATH,
            "CLIENTS_ROOT": config.CLIENTS_ROOT,
            "CLIENTS_BY_CODE": config.CLIENTS_BY_CODE,
            "DATA_DIR": config.DATA_DIR,
            "FILES_DIR": config.FILES_DIR,
            "LOGS_DIR": config.LOGS_DIR,
            "RUNS_LOG": config.RUNS_LOG,
            "RECEIPT_INBOX_ROOT": config.RECEIPT_INBOX_ROOT,
            "PIPELINE_STATUS_PATH": config.PIPELINE_STATUS_PATH,
            "BACKUPS_ROOT": config.BACKUPS_ROOT,
        }
        config.DB_PATH = self.path / "receipts.db"
        config.CLIENTS_ROOT = self.path / "Clients"
        config.CLIENTS_ROOT.mkdir(parents=True, exist_ok=True)
        # DATA_DIR as well as LOGS_DIR: attach_log_handler() resolves DATA_DIR at
        # call time, so a test that runs a CLI entry point appends to the live
        # data/resolve.log without this. Same class of leak as the ndjson one that
        # 2d19521 fixed, found the same way: by checking rather than assuming.
        config.DATA_DIR = self.path / "data"
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        config.FILES_DIR = config.DATA_DIR / "files"
        config.FILES_DIR.mkdir(parents=True, exist_ok=True)
        config.LOGS_DIR = self.path / "logs"
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
        # Under OneDrive in real life. The inbox is deliberately not created
        # here: the tests that use it create the client folders they need.
        config.RECEIPT_INBOX_ROOT = self.path / "Receipt Inbox"
        config.PIPELINE_STATUS_PATH = self.path / "pipeline-status.json"
        config.BACKUPS_ROOT = self.path / "Backups"
        config.CLIENTS_BY_CODE = {
            "ABC": {
                "client_name": "Test Client",
                "client_id": "CLIENT001",
                "firm_id": "INTELLITAX",
                "business_type": "UNSPECIFIED",
            }
        }
        return self

    def __exit__(self, *exc):
        for name, value in self._saved.items():
            setattr(config, name, value)
        self._temp.cleanup()
        return False

    def seed(self, repo, receipt_id="r-1", status="needs_review", **extraction):
        """A receipt plus one seed extraction. Defaults to needs_review."""
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
        defaults = dict(
            extraction_id=f"ext-{receipt_id}",
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
            pipeline_version=VERSION,
        )
        defaults.update(extraction)
        repo.save_extraction(**defaults)
        repo._conn.execute(
            "UPDATE receipts SET status = ? WHERE receipt_id = ?", (status, receipt_id)
        )
        repo._conn.commit()
        return file_path

    def engine(self, repo):
        return CategorisationEngine(repo=repo, enable_ai_fallback=False)

    def inbox_dir(self, client_code="ABC"):
        """The client's folder inside the redirected Receipt Inbox."""
        path = config.RECEIPT_INBOX_ROOT / client_code
        path.mkdir(parents=True, exist_ok=True)
        return path


class RecordingExtractor:
    """Returns a fixed result and counts calls.

    The call count is the assertion that matters for design document 3.13: a
    receipt left in the inbox is re-extracted every poll, and every extraction is
    a real OpenAI call.
    """

    name = "fake_extractor"

    def __init__(self, result=None):
        self.calls = 0
        self.result = result

    def extract(self, file_path, filename):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def extraction_result(**overrides):
    from worker.extraction.base import ExtractionResult

    values = dict(
        supplier_name="Apcoa Parking",
        invoice_date="2026-04-01",
        net_amount=10.0,
        vat_amount=2.0,
        gross_amount=12.0,
        currency="GBP",
        raw_response="{}",
        engine="fake_extractor",
    )
    values.update(overrides)
    return ExtractionResult(**values)


def run_pipeline_once(extractor, pipeline_version=VERSION):
    """Drive a real app.process_once() with the mailbox stubbed out.

    Only the two IMAP reads and the extractor are replaced. Everything else is the
    live code path, because the defects this exercises are about what the pipeline
    does across two consecutive polls, and a hand-rolled call sequence would only
    test the sequence the test author had in mind.
    """
    import app

    with patch.object(app, "get_extractor", lambda: extractor), \
         patch.object(app, "fetch_emails_without_attachments", lambda: []), \
         patch.object(app, "fetch_new_messages", lambda repo: []), \
         patch.object(config, "get_pipeline_version", lambda: pipeline_version):
        app.process_once()


def rows(repo, sql, params=()):
    return [dict(r) for r in repo._conn.execute(sql, params).fetchall()]


def good_corrections():
    """Corrections that make the default seed valid."""
    corrections, errors = parse_corrections(
        {"supplier_name": "Apcoa Parking", "gross_amount": "12.00"}
    )
    assert errors == {}, errors
    return corrections

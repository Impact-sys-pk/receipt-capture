"""Shared fixtures for the resolution tests.

Not named test_*, so neither runner collects it. Imported by the resolution test
modules the way tests/test_prefer_dayfirst_isolation.py imports its subjects.

Every environment redirects config.LOGS_DIR and config.RUNS_LOG as well as
DB_PATH: the console's intake panel reads the live event logs, so a synthetic row
there reads as a real intake problem, and RUNS_LOG resolves from LOGS_DIR at
import so redirecting one does not move the other.
"""

import tempfile
from pathlib import Path

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
            "LOGS_DIR": config.LOGS_DIR,
            "RUNS_LOG": config.RUNS_LOG,
        }
        config.DB_PATH = self.path / "receipts.db"
        config.CLIENTS_ROOT = self.path / "Clients"
        config.CLIENTS_ROOT.mkdir(parents=True, exist_ok=True)
        config.LOGS_DIR = self.path / "logs"
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
        config.CLIENTS_BY_CODE = {
            "ABC": {"client_name": "Test Client", "business_type": "UNSPECIFIED"}
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


def rows(repo, sql, params=()):
    return [dict(r) for r in repo._conn.execute(sql, params).fetchall()]


def good_corrections():
    """Corrections that make the default seed valid."""
    corrections, errors = parse_corrections(
        {"supplier_name": "Apcoa Parking", "gross_amount": "12.00"}
    )
    assert errors == {}, errors
    return corrections

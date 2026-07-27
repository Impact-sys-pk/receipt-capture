"""Design document 3.11: extractions.details must actually be written.

The column exists at schema.py:120, with a migration for older databases, but
save_extraction() took no details parameter and its INSERT never listed it. So
every automatic amendment the post-processing made went unrecorded.

That matters most for apply_vat_inclusive_swap(), which rewrites net and gross on
the strength of an implied VAT rate. CLAUDE.md requires a full audit trail, and an
unrecorded amendment to two financial figures is the gap that matters most here.

Every assertion below reads the column back out of a database. The whole defect
was a value that existed in memory and never reached a row, so asserting on the
object passed in would have passed throughout.
"""

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

from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.extraction.base import ExtractionResult
from worker.extraction.postprocess import apply_vat_inclusive_swap
from worker.extraction_pipeline import process_extraction_result
import resolve_receipt


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

    def seed_receipt(self, repo, receipt_id):
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
        return file_path

    def details_from_db(self, receipt_id, engine=None):
        """Read details straight out of the row, newest first."""
        repo = Repository()
        try:
            sql = "SELECT details FROM extractions WHERE receipt_id = ?"
            params = [receipt_id]
            if engine:
                sql += " AND engine = ?"
                params.append(engine)
            sql += " ORDER BY extracted_at DESC LIMIT 1"
            row = repo._conn.execute(sql, params).fetchone()
            self_row = row
            assert self_row is not None, f"no extraction row for {receipt_id}"
            return self_row["details"]
        finally:
            repo.close()


class SaveExtractionDetailsTest(unittest.TestCase):
    def test_details_round_trips_through_the_column(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed_receipt(repo, "r-direct")
                repo.save_extraction(
                    extraction_id="ext-direct",
                    receipt_id="r-direct",
                    engine="openai_vision",
                    supplier_name="Apcoa",
                    invoice_date="2026-04-01",
                    net_amount=6.67,
                    vat_amount=1.33,
                    gross_amount=8.0,
                    currency="GBP",
                    raw_response="{}",
                    validation_status="ok",
                    validation_notes=[],
                    details="auto_treated_amount_as_gross(implied_rate=0.199)",
                )
            finally:
                repo.close()

            self.assertEqual(
                env.details_from_db("r-direct"),
                "auto_treated_amount_as_gross(implied_rate=0.199)",
            )

    def test_omitted_details_stores_null_not_an_empty_string(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed_receipt(repo, "r-none")
                repo.save_extraction(
                    extraction_id="ext-none",
                    receipt_id="r-none",
                    engine="openai_vision",
                    supplier_name="Apcoa",
                    invoice_date="2026-04-01",
                    net_amount=None,
                    vat_amount=None,
                    gross_amount=8.0,
                    currency="GBP",
                    raw_response="{}",
                    validation_status="ok",
                    validation_notes=[],
                )
            finally:
                repo.close()

            stored = env.details_from_db("r-none")
            self.assertIsNone(stored, f"expected NULL, got {stored!r}")


class PipelineDetailsTest(unittest.TestCase):
    def test_vat_amendment_is_recorded_against_the_receipt(self):
        # Build the note the way the pipeline does, so the test breaks if the
        # note text changes rather than asserting a string I typed.
        net, vat, gross, details = apply_vat_inclusive_swap(8.0, 1.33, None, None)
        self.assertIn("auto_treated_amount_as_gross", details)

        with TempEnvironment() as env:
            repo = Repository()
            try:
                file_path = env.seed_receipt(repo, "r-swap")
                extraction = ExtractionResult(
                    engine="openai_vision",
                    supplier_name="Apcoa Parking",
                    invoice_date="2026-04-01",
                    net_amount=net,
                    vat_amount=vat,
                    gross_amount=gross,
                    currency="GBP",
                    raw_response="{}",
                    details=details,
                )
                process_extraction_result(
                    receipt_id="r-swap",
                    extraction=extraction,
                    file_path=file_path,
                    filename="r-swap.pdf",
                    client_code="ABC",
                    firm_id="INTELLITAX",
                    client_id="CLIENT001",
                    message_id="msg-r-swap",
                    repo=repo,
                    categorisation_engine=CategorisationEngine(repo=repo, enable_ai_fallback=False),
                    stats={},
                    run_id="test-run",
                    pipeline_version="test-version",
                )
            finally:
                repo.close()

            stored = env.details_from_db("r-swap")
            self.assertEqual(stored, details)
            self.assertIn("auto_treated_amount_as_gross", stored)

    def test_an_extraction_with_no_amendments_stores_null(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                file_path = env.seed_receipt(repo, "r-clean")
                extraction = ExtractionResult(
                    engine="openai_vision",
                    supplier_name="Apcoa Parking",
                    invoice_date="2026-04-01",
                    net_amount=10.0,
                    vat_amount=2.0,
                    gross_amount=12.0,
                    currency="GBP",
                    raw_response="{}",
                    details=None,
                )
                process_extraction_result(
                    receipt_id="r-clean",
                    extraction=extraction,
                    file_path=file_path,
                    filename="r-clean.pdf",
                    client_code="ABC",
                    firm_id="INTELLITAX",
                    client_id="CLIENT001",
                    message_id="msg-r-clean",
                    repo=repo,
                    categorisation_engine=CategorisationEngine(repo=repo, enable_ai_fallback=False),
                    stats={},
                    run_id="test-run",
                    pipeline_version="test-version",
                )
            finally:
                repo.close()

            self.assertIsNone(env.details_from_db("r-clean"))


class ManualCorrectionDetailsTest(unittest.TestCase):
    def test_manual_correction_stores_null(self):
        # resolve_receipt.py builds its own ExtractionResult with no details, so
        # NULL is correct and explicit. An operator's correction is recorded in
        # the row itself, not as an automatic amendment.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed_receipt(repo, "r-manual")
                repo.save_extraction(
                    extraction_id="ext-manual-seed",
                    receipt_id="r-manual",
                    engine="openai_vision",
                    supplier_name=None,
                    invoice_date="2026-04-01",
                    net_amount=None,
                    vat_amount=None,
                    gross_amount=None,
                    currency="GBP",
                    raw_response="{}",
                    validation_status="needs_review",
                    validation_notes=["missing supplier_name"],
                )
            finally:
                repo.close()

            argv = ["resolve_receipt.py", "r-manual", "--supplier", "Apcoa", "--gross", "12.00"]
            with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                exit_code = resolve_receipt.main()
            self.assertEqual(exit_code, 0)

            self.assertIsNone(env.details_from_db("r-manual", engine="manual_correction"))


if __name__ == "__main__":
    unittest.main()

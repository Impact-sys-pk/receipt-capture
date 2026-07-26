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
from worker.categorisation.engine import CategorisationEngine
import app

CURRENT_VERSION = "new-pipeline-version"
OLD_VERSION = "old-pipeline-version"


class RaisingExtractor:
    """Simulates the API failing: a declined card, a quota block, a timeout."""

    name = "fake_raiser"

    def __init__(self):
        self.calls = 0

    def extract(self, file_path, filename):
        self.calls += 1
        raise RuntimeError("simulated API failure")


class AutoRetryNoLoopTest(unittest.TestCase):
    """A crashed or unretryable auto-retry must not stay eligible forever.

    find_failed_by_version() selects on the latest extraction's
    pipeline_version differing from the current one. If a retry ends without
    writing an extraction row, that version never advances, so the receipt is
    picked up again on every five-minute poll. For the extraction branch that
    is three real OpenAI calls per poll, indefinitely.
    """

    def _seed(self, repo, temp_path, receipt_id, file_exists=True):
        file_path = temp_path / f"{receipt_id}.pdf"
        if file_exists:
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
        repo.save_extraction(
            extraction_id=f"ext-seed-{receipt_id}",
            receipt_id=receipt_id,
            engine="openai_vision",
            supplier_name=None,
            invoice_date=None,
            net_amount=None,
            vat_amount=None,
            gross_amount=None,
            currency="GBP",
            raw_response="{}",
            validation_status="needs_review",
            validation_notes=["gross mismatch"],
            pipeline_version=OLD_VERSION,
        )
        # The document earned needs_review. A crashed retry must not change that.
        repo.update_receipt_status(receipt_id, "needs_review")
        return file_path

    def _extractions(self, repo, receipt_id):
        return repo._conn.execute(
            "SELECT extraction_id, validation_status, validation_notes, pipeline_version, engine"
            " FROM extractions WHERE receipt_id = ? ORDER BY extracted_at",
            (receipt_id,)
        ).fetchall()

    def _receipt(self, repo, receipt_id):
        return repo._conn.execute(
            "SELECT status, locked_at FROM receipts WHERE receipt_id = ?", (receipt_id,)
        ).fetchone()

    def _run(self, repo, extractor, stats):
        app._retry_failed_receipts(
            repo=repo,
            extractor=extractor,
            categorisation_engine=CategorisationEngine(repo=repo, enable_ai_fallback=False),
            stats=stats,
            run_id="test-run",
            pipeline_version=CURRENT_VERSION,
        )

    def _env(self, temp_path):
        """Redirect DB, client tree and logs so nothing touches live data."""
        return {
            "DB_PATH": temp_path / "receipts.db",
            "CLIENTS_ROOT": temp_path / "Clients",
            "LOGS_DIR": temp_path / "logs",
            "CLIENTS_BY_CODE": {"ABC": {"client_name": "Test Client", "business_type": "UNSPECIFIED"}},
        }

    def test_extraction_error_is_recorded_so_the_receipt_is_not_retried_next_poll(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            env = self._env(temp_path)
            env["CLIENTS_ROOT"].mkdir(parents=True, exist_ok=True)
            env["LOGS_DIR"].mkdir(parents=True, exist_ok=True)
            originals = {k: getattr(config, k) for k in env}
            for k, v in env.items():
                setattr(config, k, v)

            repo = None
            try:
                repo = Repository()
                receipt_id = "r-api-crash"
                self._seed(repo, temp_path, receipt_id)
                extractor = RaisingExtractor()

                # Pass 1: the extractor is tried, and the transient-retry
                # helper burns three calls before giving up.
                stats1 = {}
                with patch("worker.extraction.retry_helper.time.sleep"):
                    self._run(repo, extractor, stats1)

                self.assertEqual(extractor.calls, 3, "transient retry should make 3 attempts")
                self.assertEqual(stats1.get("auto_retry_errors"), 1)

                rows = self._extractions(repo, receipt_id)
                self.assertEqual(len(rows), 2, "the crash must be recorded as a new extraction row")
                new = rows[-1]
                self.assertEqual(new["validation_status"], "failed")
                self.assertEqual(new["pipeline_version"], CURRENT_VERSION,
                                 "the row must carry the CURRENT version or the receipt stays eligible")
                self.assertEqual(new["engine"], "fake_raiser",
                                 "engine must come from extractor.name, not a hardcoded string")
                self.assertIn("auto-retry extraction error", new["validation_notes"])

                # The document is still needs_review. The API broke, not the receipt.
                r = self._receipt(repo, receipt_id)
                self.assertEqual(r["status"], "needs_review")
                self.assertIsNone(r["locked_at"], "lock must be released on the exception path")

                # Pass 2: same version, so it must not be picked up again.
                stats2 = {}
                with patch("worker.extraction.retry_helper.time.sleep"):
                    self._run(repo, extractor, stats2)

                self.assertEqual(extractor.calls, 3,
                                 "THE MONEY BUG: extractor called again on the next poll")
                self.assertEqual(len(self._extractions(repo, receipt_id)), 2,
                                 "no further rows should be written on pass 2")
                self.assertEqual(stats2.get("auto_retry_errors", 0), 0)
            finally:
                if repo is not None:
                    repo.close()
                for k, v in originals.items():
                    setattr(config, k, v)

    def test_missing_source_file_is_recorded_so_it_is_not_reconsidered_next_poll(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_path = Path(temp_dir)
            env = self._env(temp_path)
            env["CLIENTS_ROOT"].mkdir(parents=True, exist_ok=True)
            env["LOGS_DIR"].mkdir(parents=True, exist_ok=True)
            originals = {k: getattr(config, k) for k in env}
            for k, v in env.items():
                setattr(config, k, v)

            repo = None
            try:
                repo = Repository()
                receipt_id = "r-file-gone"
                missing = self._seed(repo, temp_path, receipt_id, file_exists=False)
                self.assertFalse(missing.exists())
                extractor = RaisingExtractor()

                stats1 = {}
                self._run(repo, extractor, stats1)

                self.assertEqual(extractor.calls, 0, "must not reach the extractor at all")
                rows = self._extractions(repo, receipt_id)
                self.assertEqual(len(rows), 2, "the missing file must be recorded as a new row")
                new = rows[-1]
                self.assertEqual(new["validation_status"], "failed")
                self.assertEqual(new["pipeline_version"], CURRENT_VERSION)
                self.assertIn("missing", new["validation_notes"].lower())

                # The seed row must be left alone: extractions are append-only,
                # and appending a note to it every poll was the old noise.
                self.assertEqual(rows[0]["validation_notes"], "gross mismatch")

                r = self._receipt(repo, receipt_id)
                self.assertEqual(r["status"], "needs_review")
                self.assertIsNone(r["locked_at"])

                # Pass 2: no second row, no second note.
                stats2 = {}
                self._run(repo, extractor, stats2)

                rows_after = self._extractions(repo, receipt_id)
                self.assertEqual(len(rows_after), 2, "no second row on the next poll")
                self.assertEqual(rows_after[0]["validation_notes"], "gross mismatch",
                                 "no second note appended to the original row")
            finally:
                if repo is not None:
                    repo.close()
                for k, v in originals.items():
                    setattr(config, k, v)


if __name__ == "__main__":
    unittest.main()

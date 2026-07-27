"""Design document test 7: the Review pair must be removed when a receipt's
life in the Review folder ends.

Until now nothing removed it, so IntelliBooks still showed every resolved
receipt as needing review, and completing it there filed a duplicate.

The pair is located by reading the sidecars, never by reconstructing the
filename: file_review() names the image through _unique_path(), so a second
review item for the same original filename is written as {stem}-2{ext}.
"""

import contextlib
import io
import json
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
from worker.filing import file_review, remove_review_pair
import resolve_receipt


class TempEnvironment:
    """Temp DB, temp client root and redirected event logs.

    The log redirection is not tidiness: the console's intake panel reads the
    live event logs, so a synthetic row there reads as a real intake problem.
    """

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved = {
            "DB_PATH": config.DB_PATH,
            "DATA_DIR": config.DATA_DIR,
            "CLIENTS_ROOT": config.CLIENTS_ROOT,
            "CLIENTS_BY_CODE": config.CLIENTS_BY_CODE,
            "LOGS_DIR": config.LOGS_DIR,
            "RUNS_LOG": config.RUNS_LOG,
        }
        config.DB_PATH = self.path / "receipts.db"
        # attach_log_handler() resolves DATA_DIR at call time, so a test that
        # runs a CLI entry point appends to the live data/*.log without this.
        config.DATA_DIR = self.path / "data"
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        config.CLIENTS_ROOT = self.path / "Clients"
        config.CLIENTS_ROOT.mkdir(parents=True, exist_ok=True)
        config.LOGS_DIR = self.path / "logs"
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
        config.CLIENTS_BY_CODE = {
            "ABC": {"client_name": "Test Client", "business_type": "UNSPECIFIED"},
            "XYZ": {"client_name": "Other Client", "business_type": "UNSPECIFIED"},
        }
        return self

    def __exit__(self, *exc):
        for name, value in self._saved.items():
            setattr(config, name, value)
        self._temp.cleanup()
        return False

    @property
    def review_dir(self):
        return config.CLIENTS_ROOT / "Test Client" / "Review"

    def source_file(self, name):
        path = self.path / name
        path.write_text("dummy", encoding="utf-8")
        return path

    def write_pair(self, client_name, receipt_id, original_filename, extra=None):
        """Write a Review pair through the real writer, so _unique_path applies."""
        extracted = {"receipt_id": receipt_id, "original_filename": original_filename}
        if extra is not None:
            extracted = extra
        return file_review(
            self.source_file(original_filename),
            client_name,
            original_filename,
            "needs_review",
            ["missing gross_amount"],
            extracted,
        )

    def seed_receipt(self, receipt_id, filename="receipt.pdf", client_code="ABC", **extraction):
        file_path = self.path / f"src-{receipt_id}.pdf"
        file_path.write_text("dummy", encoding="utf-8")
        repo = Repository()
        try:
            repo.save_receipt(
                receipt_id=receipt_id,
                message_id=f"msg-{receipt_id}",
                email_subject="Test",
                email_from="sender@example.com",
                email_received_at="2026-01-01T00:00:00Z",
                filename=filename,
                file_path=file_path,
                file_hash=f"hash-{receipt_id}",
                firm_id="INTELLITAX",
                client_id="CLIENT001",
                client_code=client_code,
                source="email",
            )
            defaults = dict(
                extraction_id=f"ext-{receipt_id}",
                receipt_id=receipt_id,
                engine="openai_vision",
                supplier_name="Seed Supplier",
                invoice_date="2026-04-01",
                net_amount=None,
                vat_amount=None,
                gross_amount=None,
                currency="GBP",
                raw_response="{}",
                validation_status="needs_review",
                validation_notes=["seeded"],
            )
            defaults.update(extraction)
            repo.save_extraction(**defaults)
        finally:
            repo.close()


def run_cli(argv):
    out = io.StringIO()
    with patch.object(sys, "argv", ["resolve_receipt.py"] + argv), contextlib.redirect_stdout(out):
        exit_code = resolve_receipt.main()
    return exit_code, out.getvalue()


class RemoveReviewPairTest(unittest.TestCase):
    def test_removes_both_files_and_leaves_the_folder_empty(self):
        with TempEnvironment() as env:
            image, sidecar = env.write_pair("Test Client", "r-1", "parking.pdf")
            self.assertTrue(image.exists() and sidecar.exists())

            removed = remove_review_pair("r-1", "ABC", "parking.pdf")

            self.assertEqual(removed, 2)
            self.assertFalse(image.exists())
            self.assertFalse(sidecar.exists())
            self.assertEqual(list(env.review_dir.iterdir()), [])

    def test_second_review_item_for_the_same_filename_removes_only_its_own_pair(self):
        # _unique_path() writes the second item as parking-2.pdf. Reconstructing
        # {stem}{ext} would delete the first receipt's pair instead of this one.
        with TempEnvironment() as env:
            first_image, first_sidecar = env.write_pair("Test Client", "r-first", "parking.pdf")
            second_image, second_sidecar = env.write_pair("Test Client", "r-second", "parking.pdf")

            self.assertEqual(first_image.name, "parking.pdf")
            self.assertEqual(second_image.name, "parking-2.pdf")

            removed = remove_review_pair("r-second", "ABC", "parking.pdf")

            self.assertEqual(removed, 2)
            self.assertFalse(second_image.exists())
            self.assertFalse(second_sidecar.exists())
            self.assertTrue(first_image.exists(), "the other receipt's image must survive")
            self.assertTrue(first_sidecar.exists(), "the other receipt's sidecar must survive")

    def test_missing_pair_returns_zero_and_does_not_raise(self):
        with TempEnvironment():
            self.assertEqual(remove_review_pair("r-never-existed", "ABC", "gone.pdf"), 0)

    def test_review_folder_that_does_not_exist_returns_zero(self):
        with TempEnvironment():
            self.assertEqual(remove_review_pair("r-1", "NO_SUCH_CODE", "gone.pdf"), 0)

    def test_sidecar_without_a_receipt_id_is_left_alone(self):
        # app.py:666 files a statement to Review with `intake.sidecar or {}`,
        # so that payload has no receipt_id and no receipt row exists.
        with TempEnvironment() as env:
            image, sidecar = env.write_pair(
                "Test Client", "unused", "uber-statement.csv",
                extra={"type": "statement", "platform": "uber"},
            )

            removed = remove_review_pair("r-unrelated", "ABC", "uber-statement.csv")

            self.assertEqual(removed, 0)
            self.assertTrue(image.exists())
            self.assertTrue(sidecar.exists())

    def test_pair_under_a_different_client_is_found_and_removed_with_a_warning(self):
        # The receipt was reassigned to another client after the review item was
        # written. Matching on a UUID is exact, so the scan is safe.
        with TempEnvironment() as env:
            image, sidecar = env.write_pair("Other Client", "r-moved", "parking.pdf")

            with self.assertLogs("worker.filing", level="WARNING") as logs:
                removed = remove_review_pair("r-moved", "ABC", "parking.pdf")

            self.assertEqual(removed, 2)
            self.assertFalse(image.exists())
            self.assertFalse(sidecar.exists())
            joined = "\n".join(logs.output)
            self.assertIn("Other Client", joined)
            self.assertIn("Test Client", joined)

    def test_file_review_writes_receipt_id_at_the_top_level(self):
        # Forward-only, so a future reader need not reach into extracted_values.
        with TempEnvironment() as env:
            _, sidecar = env.write_pair("Test Client", "r-top-level", "parking.pdf")
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertEqual(payload["receipt_id"], "r-top-level")

    def test_a_statement_sidecar_gets_no_receipt_id_key(self):
        with TempEnvironment() as env:
            _, sidecar = env.write_pair(
                "Test Client", "unused", "uber-statement.csv",
                extra={"type": "statement"},
            )
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertNotIn("receipt_id", payload)


class ResolveRemovesReviewPairTest(unittest.TestCase):
    def test_successful_resolve_removes_the_pair(self):
        with TempEnvironment() as env:
            env.seed_receipt("r-resolve", filename="parking.pdf")
            image, sidecar = env.write_pair("Test Client", "r-resolve", "parking.pdf")

            exit_code, out = run_cli([
                "r-resolve", "--supplier", "Apcoa Parking", "--gross", "12.00",
            ])

            self.assertEqual(exit_code, 0, out)
            self.assertFalse(image.exists())
            self.assertFalse(sidecar.exists())

    def test_discard_as_duplicate_removes_the_pair(self):
        with TempEnvironment() as env:
            env.seed_receipt(
                "r-discard", filename="parking.pdf",
                validation_status="possible_duplicate",
                gross_amount=12.0,
            )
            image, sidecar = env.write_pair("Test Client", "r-discard", "parking.pdf")

            exit_code, out = run_cli(["r-discard", "--duplicate-decision", "discard"])

            self.assertEqual(exit_code, 0, out)
            self.assertFalse(image.exists())
            self.assertFalse(sidecar.exists())

    def test_still_invalid_correction_leaves_the_pair(self):
        # That receipt still needs review, so its pair must stay on disk.
        with TempEnvironment() as env:
            env.seed_receipt("r-still-invalid", filename="parking.pdf", validation_status="failed")
            image, sidecar = env.write_pair("Test Client", "r-still-invalid", "parking.pdf")

            exit_code, out = run_cli(["r-still-invalid", "--supplier", "Apcoa Parking"])

            self.assertEqual(exit_code, 1)
            self.assertTrue(image.exists(), out)
            self.assertTrue(sidecar.exists(), out)


if __name__ == "__main__":
    unittest.main()

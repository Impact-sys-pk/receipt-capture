"""Design document tests 4, 5 and 6: the zero-value and typing defects in resolve_receipt.py.

4. Correcting a non-zero extracted VAT to 0 must store 0.0, not keep the old value.
5. `--vat 0` alone must take the flags path, not fall through to interactive mode.
6. Amounts supplied as strings must be coerced or reported as field errors,
   never surface as a TypeError out of validate().
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

from worker.database.repository import Repository
import resolve_receipt


class TempEnvironment:
    """Temp DB, temp client root and redirected event logs.

    The log redirection is not tidiness: the intake panel reads the live event
    logs, so a synthetic row there reads as a real intake problem.
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
            "ABC": {"client_name": "Test Client", "business_type": "UNSPECIFIED"}
        }
        return self

    def __exit__(self, *exc):
        for name, value in self._saved.items():
            setattr(config, name, value)
        self._temp.cleanup()
        return False

    def seed(self, receipt_id, **extraction):
        """Create one receipt plus one seed extraction row."""
        file_path = self.path / f"{receipt_id}.pdf"
        file_path.write_text("dummy", encoding="utf-8")

        repo = Repository()
        try:
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

    def latest_manual_extraction(self, receipt_id):
        repo = Repository()
        try:
            return repo._conn.execute(
                """SELECT * FROM extractions
                   WHERE receipt_id = ? AND engine = 'manual_correction'
                   ORDER BY extracted_at DESC LIMIT 1""",
                (receipt_id,),
            ).fetchone()
        finally:
            repo.close()

    def extraction_count(self, receipt_id):
        repo = Repository()
        try:
            return repo._conn.execute(
                "SELECT COUNT(*) AS n FROM extractions WHERE receipt_id = ?",
                (receipt_id,),
            ).fetchone()["n"]
        finally:
            repo.close()


def run_cli(argv):
    """Run resolve_receipt.main() with argv, returning (exit_code, stdout)."""
    out = io.StringIO()
    with patch.object(sys, "argv", ["resolve_receipt.py"] + argv), contextlib.redirect_stdout(out):
        exit_code = resolve_receipt.main()
    return exit_code, out.getvalue()


class CorrectedZeroTest(unittest.TestCase):
    def test_vat_corrected_to_zero_is_stored_as_zero(self):
        # Zero-rated supply: the extractor read 16.00 VAT off a gross-only
        # receipt, so net + vat does not equal gross and it sits in review.
        with TempEnvironment() as env:
            env.seed(
                "zero-vat-receipt",
                net_amount=96.0,
                vat_amount=16.0,
                gross_amount=96.0,
                validation_notes=["gross mismatch: 96.0 + 16.0 = 112.0, got 96.0"],
            )

            exit_code, out = run_cli(["zero-vat-receipt", "--vat", "0"])

            self.assertEqual(exit_code, 0, out)
            row = env.latest_manual_extraction("zero-vat-receipt")
            self.assertIsNotNone(row, "a manual_correction row should have been written")
            self.assertEqual(row["vat_amount"], 0.0)
            self.assertEqual(row["net_amount"], 96.0)
            self.assertEqual(row["gross_amount"], 96.0)
            self.assertEqual(row["supplier_name"], "Seed Supplier")

    def test_vat_zero_alone_does_not_fall_through_to_interactive(self):
        with TempEnvironment() as env:
            env.seed(
                "zero-vat-flags-path",
                net_amount=96.0,
                vat_amount=16.0,
                gross_amount=96.0,
            )

            def fail_if_called(extraction):
                raise AssertionError(
                    "--vat 0 fell through to interactive mode; the guard is testing "
                    "truthiness rather than key presence"
                )

            with patch.object(resolve_receipt, "get_corrections_interactive", fail_if_called):
                exit_code, out = run_cli(["zero-vat-flags-path", "--vat", "0"])

            self.assertEqual(exit_code, 0, out)

    def test_zero_gross_reaches_validation_rather_than_the_old_value(self):
        # A gross of 0 is not valid, but the operator's 0 must be what gets
        # validated. Silently keeping 104.99 and filing it would be worse.
        with TempEnvironment() as env:
            env.seed(
                "zero-gross-receipt",
                net_amount=None,
                vat_amount=None,
                gross_amount=104.99,
            )

            exit_code, out = run_cli(["zero-gross-receipt", "--gross", "0"])

            self.assertEqual(exit_code, 0, out)
            row = env.latest_manual_extraction("zero-gross-receipt")
            self.assertIsNotNone(row)
            self.assertEqual(row["gross_amount"], 0.0)


class StringAmountTest(unittest.TestCase):
    def test_interactive_string_amounts_are_coerced_not_crashed(self):
        # get_corrections_interactive() returns input().strip(), so strings.
        # validate() does round(net + vat), which raises TypeError on a string.
        with TempEnvironment() as env:
            env.seed("string-amounts", validation_status="failed")

            answers = iter([
                "",         # supplier: keep existing
                "",         # invoice date: keep existing
                "80",       # net
                "16.00",    # vat
                "96.00",    # gross
                "",         # ref number
                "",         # time
            ])
            with patch("builtins.input", lambda *a: next(answers)):
                exit_code, out = run_cli(["string-amounts"])

            self.assertEqual(exit_code, 0, out)
            row = env.latest_manual_extraction("string-amounts")
            self.assertIsNotNone(row)
            self.assertEqual(row["net_amount"], 80.0)
            self.assertEqual(row["vat_amount"], 16.0)
            self.assertEqual(row["gross_amount"], 96.0)
            self.assertIsInstance(row["net_amount"], float)
            self.assertIsInstance(row["vat_amount"], float)
            self.assertIsInstance(row["gross_amount"], float)
            # Blank still means "keep existing".
            self.assertEqual(row["supplier_name"], "Seed Supplier")
            self.assertEqual(row["invoice_date"], "2026-04-01")

    def test_interactive_bad_amount_reports_a_field_error_and_writes_nothing(self):
        with TempEnvironment() as env:
            env.seed("bad-interactive-amount", validation_status="failed")

            answers = iter(["", "", "", "", "£96", "", ""])
            with patch("builtins.input", lambda *a: next(answers)):
                exit_code, out = run_cli(["bad-interactive-amount"])

            self.assertEqual(exit_code, 1)
            self.assertIn("gross_amount", out)
            self.assertNotIn("unsupported operand", out)
            self.assertEqual(env.extraction_count("bad-interactive-amount"), 1)

    def test_flag_amounts_with_thousands_separator_are_a_field_error(self):
        with TempEnvironment() as env:
            env.seed("bad-flag-amount", validation_status="failed")

            exit_code, out = run_cli([
                "bad-flag-amount", "--supplier", "Apcoa", "--gross", "1,234.56",
            ])

            self.assertEqual(exit_code, 1)
            self.assertIn("gross_amount", out)
            self.assertEqual(env.extraction_count("bad-flag-amount"), 1)

    def test_flag_date_in_day_first_form_is_a_field_error(self):
        # Reparsing here would undo the day-first handling in openai_vision.py.
        with TempEnvironment() as env:
            env.seed("bad-flag-date", validation_status="failed")

            exit_code, out = run_cli([
                "bad-flag-date", "--gross", "96.00", "--invoice-date", "25/12/2026",
            ])

            self.assertEqual(exit_code, 1)
            self.assertIn("invoice_date", out)
            self.assertEqual(env.extraction_count("bad-flag-date"), 1)


if __name__ == "__main__":
    unittest.main()

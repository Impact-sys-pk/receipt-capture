"""Design document 4.4: resolve_receipt.py and discard_receipt.py as thin CLIs.

This is the step where the second caller of the service appears, so it is the step
where "four callers, one implementation" is either true or not. The CLI keeps
argparse, the rendering, the prompts and every print(); everything else goes to the
service.

Existing behaviour must not change. Every command in RECEIPT_CAPTURE_GUIDE.md keeps
working verbatim, except that zero works and string amounts no longer crash, both
of which landed in 0cae398.
"""

import ast
import contextlib
import io
import sys
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

from resolution_fixtures import TempEnvironment, rows
from worker.database.repository import Repository
import discard_receipt as discard_cli
import resolve_receipt as resolve_cli

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_cli(module, argv):
    out = io.StringIO()
    with patch.object(sys, "argv", [module.__name__ + ".py"] + argv), \
         contextlib.redirect_stdout(out):
        exit_code = module.main()
    return exit_code, out.getvalue()


class ResolveCliFlagsTest(unittest.TestCase):
    def test_the_documented_flag_command_files_a_receipt(self):
        # RECEIPT_CAPTURE_GUIDE.md:295, verbatim shape.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
            finally:
                repo.close()

            exit_code, out = run_cli(
                resolve_cli, ["r-1", "--supplier", "Correct Name", "--gross", "104.99"]
            )

            self.assertEqual(exit_code, 0, out)
            self.assertIn("Filed to", out)
            repo = Repository()
            try:
                receipt = repo.get_receipt("r-1")
                self.assertEqual(receipt["status"], "ok")
                self.assertIsNotNone(receipt["filed_path"])
                events = rows(repo, "SELECT * FROM resolution_events")
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["source"], "cli")
                self.assertEqual(events[0]["outcome"], "filed")
            finally:
                repo.close()

    def test_a_correction_that_is_still_invalid_exits_one_and_appends_a_row(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
            finally:
                repo.close()

            exit_code, out = run_cli(resolve_cli, ["r-1", "--supplier", "Correct Name"])

            self.assertEqual(exit_code, 1)
            self.assertIn("Still not valid", out)
            repo = Repository()
            try:
                extractions = rows(repo, "SELECT * FROM extractions ORDER BY extracted_at")
                self.assertEqual(len(extractions), 2, "the attempt is recorded as a new row")
                self.assertEqual(extractions[-1]["engine"], "manual_correction")
                self.assertIsNone(repo.get_receipt("r-1")["filed_path"])
            finally:
                repo.close()

    def test_vat_zero_alone_still_works(self):
        # 0cae398's behaviour must survive the rewrite.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(
                    repo, supplier_name="Apcoa Parking",
                    net_amount=96.0, vat_amount=16.0, gross_amount=96.0,
                )
            finally:
                repo.close()

            exit_code, out = run_cli(resolve_cli, ["r-1", "--vat", "0"])

            self.assertEqual(exit_code, 0, out)
            repo = Repository()
            try:
                row = rows(repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'")[0]
                self.assertEqual(row["vat_amount"], 0.0)
            finally:
                repo.close()

    def test_a_bad_amount_is_a_field_error_and_writes_nothing(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
            finally:
                repo.close()

            exit_code, out = run_cli(resolve_cli, ["r-1", "--gross", "1,234.56"])

            self.assertEqual(exit_code, 1)
            self.assertIn("gross_amount", out)
            repo = Repository()
            try:
                self.assertEqual(len(rows(repo, "SELECT * FROM extractions")), 1)
            finally:
                repo.close()

    def test_an_unknown_receipt_exits_one_without_a_traceback(self):
        with TempEnvironment():
            exit_code, out = run_cli(resolve_cli, ["no-such-receipt"])
            self.assertEqual(exit_code, 1)
            self.assertIn("no-such-receipt", out)

    def test_an_already_filed_receipt_says_where_the_file_is(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="ok")
                filed = env.path / "previously-filed.pdf"
                filed.write_text("filed", encoding="utf-8")
                repo.mark_receipt_filed("r-1", str(filed))
            finally:
                repo.close()

            exit_code, out = run_cli(resolve_cli, ["r-1", "--supplier", "Correct Name"])

            self.assertEqual(exit_code, 1, "not a success, so not 0")
            self.assertIn("previously-filed.pdf", out, "the operator must be told where it is")
            self.assertNotIn("ERROR", out, "and it must not read as a failure")


class ResolveCliInteractiveTest(unittest.TestCase):
    def test_blank_answers_keep_existing_values(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, supplier_name="Seed Supplier", gross_amount=12.0)
            finally:
                repo.close()

            # supplier, date, net, vat, gross, ref, time
            answers = iter(["", "", "", "", "", "", ""])
            with patch("builtins.input", lambda *a: next(answers)):
                exit_code, out = run_cli(resolve_cli, ["r-1"])

            self.assertEqual(exit_code, 0, out)
            repo = Repository()
            try:
                row = rows(repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'")[0]
                self.assertEqual(row["supplier_name"], "Seed Supplier")
                self.assertEqual(row["gross_amount"], 12.0)
            finally:
                repo.close()

    def test_interactive_string_amounts_are_coerced_not_crashed(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, supplier_name="Seed Supplier")
            finally:
                repo.close()

            answers = iter(["", "", "80", "16.00", "96.00", "", ""])
            with patch("builtins.input", lambda *a: next(answers)):
                exit_code, out = run_cli(resolve_cli, ["r-1"])

            self.assertEqual(exit_code, 0, out)
            repo = Repository()
            try:
                row = rows(repo, "SELECT * FROM extractions WHERE engine = 'manual_correction'")[0]
                self.assertEqual((row["net_amount"], row["vat_amount"], row["gross_amount"]),
                                 (80.0, 16.0, 96.0))
            finally:
                repo.close()

    def test_duplicate_decision_discard_discards(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="possible_duplicate", supplier_name="Apcoa", gross_amount=12.0)
            finally:
                repo.close()

            exit_code, out = run_cli(resolve_cli, ["r-1", "--duplicate-decision", "discard"])

            self.assertEqual(exit_code, 0, out)
            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "discarded")
                events = rows(repo, "SELECT * FROM resolution_events")
                self.assertEqual(events[0]["action"], "discard")
                self.assertIsNotNone(events[0]["reason"])
            finally:
                repo.close()

    def test_duplicate_decision_file_files_it_anyway(self):
        # --duplicate-decision file with no correction flags has always dropped
        # into the prompts, so the answers are supplied here. Resolving a
        # possible_duplicate is the "file it anyway" path, per 4.3 as amended.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="possible_duplicate", supplier_name="Apcoa", gross_amount=12.0)
            finally:
                repo.close()

            answers = iter(["", "", "", "", "", "", ""])
            with patch("builtins.input", lambda *a: next(answers)):
                exit_code, out = run_cli(resolve_cli, ["r-1", "--duplicate-decision", "file"])

            self.assertEqual(exit_code, 0, out)
            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "ok")
            finally:
                repo.close()


class DiscardCliTest(unittest.TestCase):
    def test_discards_with_a_reason(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="failed")
                original = Path(repo.get_receipt("r-1")["file_path"])
            finally:
                repo.close()

            exit_code, out = run_cli(
                discard_cli, ["r-1", "--reason", "client sent a bank statement by mistake"]
            )

            self.assertEqual(exit_code, 0, out)
            self.assertTrue(original.exists(), "no file is ever deleted")
            repo = Repository()
            try:
                self.assertEqual(repo.get_receipt("r-1")["status"], "discarded")
                event = rows(repo, "SELECT * FROM resolution_events")[0]
                self.assertEqual(event["reason"], "client sent a bank statement by mistake")
                self.assertEqual(event["source"], "cli")
                self.assertEqual(len(rows(repo, "SELECT * FROM extractions")), 1)
            finally:
                repo.close()

    def test_the_reason_is_required(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
            finally:
                repo.close()
            with self.assertRaises(SystemExit) as caught:
                run_cli(discard_cli, ["r-1"])
            self.assertEqual(caught.exception.code, 2, "argparse rejects a missing required flag")

    def test_an_unknown_receipt_exits_one(self):
        with TempEnvironment():
            exit_code, out = run_cli(discard_cli, ["nope", "--reason", "whatever"])
            self.assertEqual(exit_code, 1)
            self.assertIn("nope", out)


class ExitCodeMappingTest(unittest.TestCase):
    """4.4: filed and discarded are 0, everything else 1."""

    def test_every_outcome_maps_to_the_documented_exit_code(self):
        expected = {
            "filed": 0,
            "discarded": 0,
            "still_invalid": 1,
            "stale": 1,
            "locked": 1,
            "not_found": 1,
            "already_filed": 1,
            "error": 1,
        }
        for outcome, code in expected.items():
            with self.subTest(outcome=outcome):
                self.assertEqual(resolve_cli.exit_code_for(outcome), code)

    def test_an_unrecognised_outcome_is_not_silently_a_success(self):
        self.assertEqual(resolve_cli.exit_code_for("something_new"), 1)


class ThinWrapperTest(unittest.TestCase):
    """4.1: the CLI is a wrapper. The logic lives in one place."""

    def _source(self, name):
        return (REPO_ROOT / name).read_text(encoding="utf-8")

    def test_the_cli_calls_the_service_rather_than_reimplementing_it(self):
        source = self._source("resolve_receipt.py")
        for symbol in ("resolve_receipt", "discard_receipt", "get_resolution_view",
                       "parse_corrections"):
            self.assertIn(symbol, source)
        self.assertIn("from worker.resolution.service import", source)

    def test_the_cli_holds_no_validation_categorisation_filing_or_locking_logic(self):
        # Calls, from the AST, not substrings: the docstrings legitimately mention
        # validate() when explaining why coercion moved to parse_corrections.
        banned = {
            "validate",                 # validation
            "categorise", "save_categorisation", "update_categorisation",
            "file_receipt", "make_enriched_sidecar", "mark_receipt_filed",
            "determine_tax_year",       # filing
            "acquire_receipt_lock", "release_receipt_lock",  # locking
            "save_extraction", "update_receipt_status", "add_validation_note",
            "remove_review_pair", "upsert_client_vendor",
            "ExtractionResult",
        }
        for name in ("resolve_receipt.py", "discard_receipt.py"):
            tree = ast.parse(self._source(name))
            called = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name):
                        called.add(func.id)
                    elif isinstance(func, ast.Attribute):
                        called.add(func.attr)
            with self.subTest(cli=name):
                overlap = sorted(called & banned)
                self.assertEqual(
                    overlap, [],
                    f"{overlap} belong in the service, not in {name}",
                )

    def test_the_cli_imports_none_of_the_service_internals(self):
        # It must not reach past the service to the pieces the service composes.
        for name in ("resolve_receipt.py", "discard_receipt.py"):
            tree = ast.parse(self._source(name))
            imported_from = {
                node.module for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
            with self.subTest(cli=name):
                for module in ("worker.filing", "worker.validation.rules",
                               "worker.extraction.base"):
                    self.assertNotIn(module, imported_from)

    def test_neither_cli_imports_the_repository_write_path_directly(self):
        # Reading is fine, and both need a Repository to hand to the service.
        # Rewriting rows is not.
        for name in ("resolve_receipt.py", "discard_receipt.py"):
            tree = ast.parse(self._source(name))
            calls = {
                node.func.attr for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            }
            with self.subTest(cli=name):
                self.assertNotIn("add_validation_note", calls)
                self.assertNotIn("save_extraction", calls)
                self.assertNotIn("update_categorisation", calls)

    def test_add_validation_note_is_gone_from_the_repository(self):
        # Its last production caller was resolve_receipt.py, replaced by an
        # appended extraction row per 4.3 step 6. Leaving the method would leave a
        # tempting mutation of a table CLAUDE.md says is never modified.
        self.assertFalse(
            hasattr(Repository, "add_validation_note"),
            "add_validation_note() must not survive step 9",
        )


if __name__ == "__main__":
    unittest.main()

r"""_retry_failed_receipts() must not write a second extraction row over its own.

Sub-step 10ay, 2026-09-13. Found verifying step 10ax's report.

The `except` block in `_retry_failed_receipts()` writes a `failed` extraction
row, and its comment said "process_extraction_result() never ran, so no
extraction row was written". That is false whenever the exception comes from
INSIDE `process_extraction_result()` after its own `repo.save_extraction()`,
which runs near the top of that function, well before categorisation, the
publish step and the client-folder copy. By that point a row for this attempt
already exists, carrying the current `pipeline_version` and whatever status the
document genuinely earned, and the handler wrote a second row marked `failed`
over the top of it.

Step 10ax stopped the one call site this was found through from raising. The
assumption is about `process_extraction_result()` in general, not about that one
call site, so it is guarded here rather than left to the next caller to break.

The two tests are a pair and differ in one thing only: WHERE the induced failure
fires relative to `repo.save_extraction()` in `process_extraction_result()`.

- before it, `validate()` raising       -> no row this attempt, so the `failed`
                                           row is written exactly as before.
- after it, `resolve_against_chart()`
  raising                               -> a row for this attempt already
                                           exists, so nothing is written and it
                                           is left alone.

Each reads the `extractions` table back rather than trusting a return value.

`tests/test_auto_retry_no_loop.py` covers a third position, the extractor
raising before `process_extraction_result()` is entered at all. That is the same
BRANCH as the first test here and is deliberately not repeated: what is new here
is the position of the failure INSIDE that function, which no existing test
varies.
"""

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
from worker.extraction.base import ExtractionResult
import worker.extraction_pipeline as extraction_pipeline
import app

CURRENT_VERSION = "current-version"
OLD_VERSION = "old-version"

SEED_EXTRACTION_ID = "ext-seed"

#: Enough of a reading to validate `ok`, so the ok branch is reached. The ok
#: branch is where resolve_against_chart() sits, which is the anchor for the
#: after-the-save failure.
SUPPLIER = "Apcoa Parking"


class CleanExtractor:
    """Returns a result that validates `ok`. Never raises: the failure is
    induced further in, which is the whole point of the pair."""

    name = "clean_stub"

    def __init__(self):
        self.calls = 0

    def extract(self, file_path, filename):
        self.calls += 1
        return ExtractionResult(
            supplier_name=SUPPLIER,
            invoice_date="2026-01-15",
            net_amount=10.00,
            vat_amount=2.00,
            gross_amount=12.00,
            currency="GBP",
            raw_response='{"supplier_name": "' + SUPPLIER + '"}',
            engine=self.name,
        )


class RetryDoesNotDoubleWriteTest(unittest.TestCase):

    # ----------------------------------------------------------------- fixture

    def _env(self, temp_path):
        return {
            "DB_PATH": temp_path / "receipts.db",
            "CLIENTS_ROOT": temp_path / "Clients",
            "LOGS_DIR": temp_path / "logs",
            "CLIENTS_BY_ID": {"CLIENT001": {
                "client_name": "Test Client",
                "client_folder_name": "Test Client",
                "client_id": "CLIENT001",
                "firm_id": "INTELLITAX",
                "trade": "UNSPECIFIED",
            }},
        }

    def _seed(self, repo, temp_path, receipt_id):
        """A needs_review receipt whose only extraction carries the OLD version.

        That is what makes find_failed_by_version() select it, and it is also
        what makes the version comparison meaningful: on entry the latest row is
        guaranteed NOT to carry the current version, because that query selects
        on exactly that condition.
        """
        file_path = temp_path / (receipt_id + ".pdf")
        file_path.write_text("dummy", encoding="utf-8")
        repo.save_receipt(
            receipt_id=receipt_id,
            message_id="msg-" + receipt_id,
            email_subject="Test",
            email_from="sender@example.com",
            email_received_at="2026-01-01T00:00:00Z",
            filename=receipt_id + ".pdf",
            file_path=file_path,
            file_hash="hash-" + receipt_id,
            firm_id="INTELLITAX",
            client_id="CLIENT001",
            source="email",
        )
        repo.save_extraction(
            extraction_id=SEED_EXTRACTION_ID,
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
        repo.update_receipt_status(receipt_id, "needs_review")
        return file_path

    def _extractions(self, repo, receipt_id):
        return repo._conn.execute(
            "SELECT extraction_id, validation_status, validation_notes,"
            " pipeline_version, engine, raw_response"
            " FROM extractions WHERE receipt_id = ? ORDER BY extracted_at, rowid",
            (receipt_id,),
        ).fetchall()

    def _run(self, repo, extractor, stats):
        app._retry_failed_receipts(
            repo=repo,
            extractor=extractor,
            categorisation_engine=CategorisationEngine(repo=repo, enable_ai_fallback=False),
            stats=stats,
            run_id="test-run",
            pipeline_version=CURRENT_VERSION,
        )

    def _retry_with_failure_at(self, target, receipt_id, poll_again=False):
        """Run one auto-retry pass with `target` in extraction_pipeline raising.

        With poll_again, runs a SECOND pass afterwards with nothing patched, to
        ask whether the receipt is selected again. Returns (extraction rows as
        dicts, stats, receipt row as a dict), plus, when polling again, the
        extractor call count after the second pass and the row count after it.
        """
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
                self._seed(repo, temp_path, receipt_id)
                extractor = CleanExtractor()
                stats = {}
                with patch.object(
                    extraction_pipeline, target,
                    side_effect=RuntimeError("simulated " + target + " failure"),
                ):
                    self._run(repo, extractor, stats)
                rows = [dict(r) for r in self._extractions(repo, receipt_id)]
                receipt = dict(repo._conn.execute(
                    "SELECT status, locked_at FROM receipts WHERE receipt_id = ?",
                    (receipt_id,),
                ).fetchone())
                self.assertEqual(
                    extractor.calls, 1,
                    "the extractor should have run exactly once, so the failure "
                    "under test is the induced one and not a transient retry",
                )
                if poll_again:
                    self._run(repo, extractor, {})
                    after = [dict(r) for r in self._extractions(repo, receipt_id)]
                    return rows, stats, receipt, extractor.calls, after
                return rows, stats, receipt
            finally:
                if repo is not None:
                    repo.close()
                for k, v in originals.items():
                    setattr(config, k, v)

    # -------------------------------------------------- the pair, by position

    def test_a_failure_before_the_save_still_writes_the_failed_row(self):
        """validate() raises, so process_extraction_result() writes no row.

        Today's behaviour, and it must not change: without a row carrying the
        current version, find_failed_by_version() re-selects this receipt on
        every five-minute poll for ever.
        """
        rows, stats, receipt = self._retry_with_failure_at("validate", "r-before")

        self.assertEqual(stats.get("auto_retry_errors"), 1)
        self.assertEqual(
            len(rows), 2,
            "the crash must be recorded, or the receipt loops for ever",
        )
        seeded, written = rows
        self.assertEqual(seeded["extraction_id"], SEED_EXTRACTION_ID)
        self.assertEqual(written["validation_status"], "failed")
        self.assertEqual(
            written["pipeline_version"], CURRENT_VERSION,
            "the row must carry the CURRENT version or the receipt stays eligible",
        )
        self.assertEqual(
            written["engine"], "clean_stub",
            "engine comes from extractor.name, not a hardcoded string",
        )
        self.assertIn("auto-retry extraction error", written["validation_notes"])

        # The API broke, not the document.
        self.assertEqual(receipt["status"], "needs_review")
        self.assertIsNone(receipt["locked_at"], "the lock must be released")

    def test_a_failure_after_the_save_writes_no_second_row(self):
        """resolve_against_chart() raises, so a row for this attempt exists.

        THE BUG. The handler used to write a `failed` row on top of a row this
        same attempt had just written with a genuine status, so the extractions
        table recorded a failure that did not happen and buried the reading that
        did.
        """
        rows, stats, receipt = self._retry_with_failure_at(
            "resolve_against_chart", "r-after")

        self.assertEqual(
            stats.get("auto_retry_errors"), 1,
            "the error is still counted and still logged: only the second row goes",
        )
        self.assertEqual(
            len(rows), 2,
            "expected the seed row plus this attempt's own row and no more, got "
            + repr([(r["extraction_id"], r["validation_status"]) for r in rows]),
        )
        seeded, written = rows
        self.assertEqual(seeded["extraction_id"], SEED_EXTRACTION_ID)

        # The row this attempt wrote is process_extraction_result()'s own, not
        # the handler's: it carries the real reading, not the exception text.
        self.assertEqual(written["pipeline_version"], CURRENT_VERSION)
        self.assertEqual(written["engine"], "clean_stub")
        self.assertNotIn(
            "auto-retry extraction error", written["validation_notes"] or "",
            "the handler wrote over the row this attempt already had",
        )
        self.assertIn(
            SUPPLIER, written["raw_response"],
            "the surviving row must be the one holding the real extraction",
        )

        self.assertIsNone(receipt["locked_at"], "the lock must be released")

    def test_neither_branch_leaves_the_receipt_eligible_on_the_next_poll(self):
        """The anti-loop property, on BOTH branches, by polling again.

        This is the guard on the fix rather than a demonstration of it: it
        passes with or without the change, because both the handler's `failed`
        row and process_extraction_result()'s own row carry the current
        version. What it catches is the obvious way to get 10ay wrong, a guard
        that skips the write when there is no row for this attempt either. Then
        the version never advances, find_failed_by_version() selects the receipt
        on every five-minute poll, and via extract_with_transient_retry that is
        three real OpenAI calls a poll, indefinitely. Proved to catch exactly
        that by mutation, see the report for sub-step 10ay.

        `poll_again` runs a second pass with nothing patched, so the extractor
        being called a second time means the receipt was selected again.
        """
        for target, receipt_id, where in (
            ("validate", "r-loop-before", "before the save"),
            ("resolve_against_chart", "r-loop-after", "after the save"),
        ):
            with self.subTest(failure=where):
                rows, _stats, _receipt, calls_after, rows_after = (
                    self._retry_with_failure_at(target, receipt_id, poll_again=True))

                self.assertEqual(
                    rows[-1]["pipeline_version"], CURRENT_VERSION,
                    "the latest row must carry the current version, whichever "
                    "branch wrote it",
                )
                self.assertEqual(
                    calls_after, 1,
                    "THE MONEY BUG: the receipt was selected again on the next "
                    "poll and the extractor ran a second time",
                )
                self.assertEqual(
                    len(rows_after), len(rows),
                    "the second poll wrote another row, so the receipt is still "
                    "eligible: " + repr([(r["extraction_id"], r["validation_status"])
                                         for r in rows_after]),
                )


if __name__ == "__main__":
    unittest.main()

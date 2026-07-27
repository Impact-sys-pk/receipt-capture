"""Design document tests 13 to 21: resolve_receipt() and discard_receipt().

Four callers must go through one implementation. Three independent
implementations of resolution is what caused the divergence the design exists to
fix, so these tests pin the behaviour the CLI, the console and the back-feed will
all inherit.

Temp database throughout, with config.LOGS_DIR and config.RUNS_LOG redirected: the
console's intake panel reads the live event logs, so a synthetic row there reads as
a real intake problem.
"""

import json
import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone
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
from worker.resolution import service
from worker.resolution.service import (
    Corrections,
    discard_receipt,
    parse_corrections,
    resolve_receipt,
)


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
        )
        defaults.update(extraction)
        repo.save_extraction(**defaults)
        repo._conn.execute(
            "UPDATE receipts SET status = ? WHERE receipt_id = ?", (status, receipt_id)
        )
        repo._conn.commit()
        return defaults["extraction_id"]

    def engine(self, repo):
        return CategorisationEngine(repo=repo, enable_ai_fallback=False)


def _rows(repo, sql, params=()):
    return [dict(r) for r in repo._conn.execute(sql, params).fetchall()]


def _good_corrections():
    corrections, errors = parse_corrections({"supplier_name": "Apcoa Parking", "gross_amount": "12.00"})
    assert errors == {}
    return corrections


class StaleTest(unittest.TestCase):
    """Test 13."""

    def test_mismatched_expected_extraction_id_writes_nothing(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                before_extractions = _rows(repo, "SELECT * FROM extractions")

                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", _good_corrections(),
                    actor="paul", source="console",
                    expected_extraction_id="someone-elses-extraction",
                )

                self.assertEqual(outcome.outcome, "stale")
                self.assertEqual(_rows(repo, "SELECT * FROM extractions"), before_extractions)
                self.assertEqual(_rows(repo, "SELECT * FROM resolution_events"), [])
                self.assertEqual(
                    repo.get_receipt("r-1")["status"], "needs_review",
                    "status must not change",
                )
                self.assertIsNone(repo.get_receipt("r-1")["filed_path"])
                self.assertEqual(list(config.CLIENTS_ROOT.rglob("*.pdf")), [])
                # The lock must not be left held.
                self.assertIsNone(repo.get_receipt("r-1")["locked_at"])
            finally:
                repo.close()

    def test_matching_expected_extraction_id_proceeds(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                extraction_id = env.seed(repo)
                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", _good_corrections(),
                    actor="paul", source="console",
                    expected_extraction_id=extraction_id,
                )
                self.assertEqual(outcome.outcome, "filed", outcome.message)
            finally:
                repo.close()

    def test_a_second_save_against_a_superseded_extraction_is_stale(self):
        # The optimistic-concurrency property the console depends on: two
        # operators on the same page, second Save must not overwrite the first.
        #
        # The first attempt is deliberately one that does NOT file, because a
        # filed receipt is caught by step 1a's already_filed guard first. Both
        # guards protect the same thing from different directions.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                extraction_id = env.seed(repo)
                incomplete, _ = parse_corrections({"supplier_name": "Apcoa Parking"})

                first = resolve_receipt(
                    repo, env.engine(repo), "r-1", incomplete,
                    actor="paul", source="console", expected_extraction_id=extraction_id,
                )
                second = resolve_receipt(
                    repo, env.engine(repo), "r-1", _good_corrections(),
                    actor="someone-else", source="console", expected_extraction_id=extraction_id,
                )

                self.assertEqual(first.outcome, "still_invalid")
                self.assertEqual(
                    second.outcome, "stale",
                    "the second operator's expected extraction is no longer the latest",
                )
                events = _rows(repo, "SELECT * FROM resolution_events")
                self.assertEqual(len(events), 1, "the stale attempt must not write an event")
            finally:
                repo.close()

    def test_already_filed_takes_precedence_over_stale(self):
        # 4.3 puts step 1a before step 3, so a filed receipt reports what it is
        # rather than what the caller's expectations were. The more useful answer.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                extraction_id = env.seed(repo)
                first = resolve_receipt(
                    repo, env.engine(repo), "r-1", _good_corrections(),
                    actor="paul", source="console", expected_extraction_id=extraction_id,
                )
                second = resolve_receipt(
                    repo, env.engine(repo), "r-1", _good_corrections(),
                    actor="someone-else", source="console", expected_extraction_id=extraction_id,
                )
                self.assertEqual(first.outcome, "filed")
                self.assertEqual(second.outcome, "already_filed")
                self.assertIsNotNone(second.filed_path)
            finally:
                repo.close()


class LockedTest(unittest.TestCase):
    """Test 14."""

    def test_a_locked_receipt_returns_locked(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                self.assertTrue(repo.acquire_receipt_lock("r-1"))

                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", _good_corrections(),
                    actor="paul", source="console",
                )

                self.assertEqual(outcome.outcome, "locked")
                self.assertEqual(_rows(repo, "SELECT * FROM resolution_events"), [])
                self.assertEqual(len(_rows(repo, "SELECT * FROM extractions")), 1)
                # The other holder's lock must survive.
                self.assertIsNotNone(repo.get_receipt("r-1")["locked_at"])
            finally:
                repo.close()


class NotFoundTest(unittest.TestCase):
    """Test 15."""

    def test_a_nonexistent_receipt_returns_not_found_without_raising(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                outcome = resolve_receipt(
                    repo, env.engine(repo), "no-such-receipt", _good_corrections(),
                    actor="paul", source="console",
                )
                self.assertEqual(outcome.outcome, "not_found")
                self.assertIn("no-such-receipt", outcome.message)
                self.assertEqual(_rows(repo, "SELECT * FROM resolution_events"), [])
            finally:
                repo.close()

    def test_a_receipt_with_no_extraction_returns_not_found_saying_so(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                file_path = env.path / "bare.pdf"
                file_path.write_text("dummy", encoding="utf-8")
                repo.save_receipt(
                    receipt_id="r-bare", message_id="m", email_subject=None,
                    email_from=None, email_received_at=None, filename="bare.pdf",
                    file_path=file_path, file_hash="h", client_code="ABC",
                )
                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-bare", _good_corrections(),
                    actor="paul", source="console",
                )
                self.assertEqual(outcome.outcome, "not_found")
                self.assertIn("no extraction", outcome.message)
            finally:
                repo.close()


class StillInvalidTest(unittest.TestCase):
    """Test 16, as amended 2026-07-27: a new row, not a mutated one."""

    def test_appends_a_row_leaves_the_original_and_does_not_file(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                original_id = env.seed(repo)
                before = _rows(repo, "SELECT * FROM extractions WHERE extraction_id = ?", (original_id,))

                # Supplier corrected, gross still missing, so still invalid.
                corrections, errors = parse_corrections({"supplier_name": "Apcoa Parking"})
                self.assertEqual(errors, {})
                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", corrections,
                    actor="paul", source="cli",
                )

                self.assertEqual(outcome.outcome, "still_invalid")
                self.assertIn("missing gross_amount", outcome.validation_notes)

                after = _rows(repo, "SELECT * FROM extractions WHERE extraction_id = ?", (original_id,))
                self.assertEqual(after, before, "the previous row must be byte-identical")

                rows = _rows(repo, "SELECT * FROM extractions ORDER BY extracted_at")
                self.assertEqual(len(rows), 2, "exactly one row appended")
                appended = [r for r in rows if r["extraction_id"] != original_id][0]
                self.assertEqual(appended["engine"], "manual_correction")
                self.assertEqual(appended["supplier_name"], "Apcoa Parking")
                self.assertIn("missing gross_amount", appended["validation_notes"])
                self.assertEqual(appended["extraction_id"], outcome.extraction_id)

                events = _rows(repo, "SELECT * FROM resolution_events")
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["outcome"], "still_invalid")
                self.assertEqual(events[0]["extraction_id"], appended["extraction_id"])

                # Not filed.
                self.assertIsNone(repo.get_receipt("r-1")["filed_path"])
                self.assertEqual(list(config.CLIENTS_ROOT.rglob("*.pdf")), [])
                self.assertIsNone(repo.get_receipt("r-1")["locked_at"])
            finally:
                repo.close()

    def test_no_row_mutating_method_survives_on_the_repository(self):
        # This used to patch Repository.add_validation_note and fail the test if it
        # was called. The method was removed at step 9, so there is nothing left to
        # patch and the assertion becomes its absence. The "previous row must be
        # byte-identical" assertion above is what actually guards the behaviour.
        self.assertFalse(hasattr(Repository, "add_validation_note"))


class SuccessfulResolveTest(unittest.TestCase):
    """Test 17."""

    def test_writes_exactly_one_new_extraction_row_and_files(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                original_id = env.seed(repo)
                before = _rows(repo, "SELECT * FROM extractions WHERE extraction_id = ?", (original_id,))

                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", _good_corrections(),
                    actor="paul", source="console",
                )

                self.assertEqual(outcome.outcome, "filed", outcome.message)
                rows = _rows(repo, "SELECT * FROM extractions")
                self.assertEqual(len(rows), 2)
                self.assertEqual(
                    _rows(repo, "SELECT * FROM extractions WHERE extraction_id = ?", (original_id,)),
                    before, "the original row must be untouched",
                )

                receipt = repo.get_receipt("r-1")
                self.assertEqual(receipt["status"], "ok")
                self.assertIsNotNone(receipt["filed_path"])
                self.assertTrue(Path(receipt["filed_path"]).exists())
                self.assertEqual(outcome.filed_path, receipt["filed_path"])
                self.assertIsNone(receipt["locked_at"])
            finally:
                repo.close()

    def test_the_categorisation_references_an_extraction_row_that_exists(self):
        # Steps 7 and 8 in order. Reversed, this is the IntegrityError from b480a7e.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                resolve_receipt(
                    repo, env.engine(repo), "r-1", _good_corrections(),
                    actor="paul", source="console",
                )
                cat = _rows(repo, "SELECT * FROM categorisations WHERE receipt_id = 'r-1'")[0]
                referenced = _rows(
                    repo, "SELECT * FROM extractions WHERE extraction_id = ?",
                    (cat["extraction_id"],),
                )
                self.assertEqual(len(referenced), 1)
            finally:
                repo.close()


class GlOverrideTest(unittest.TestCase):
    """Test 18."""

    def _seed_mapping(self, repo):
        repo.upsert_client_vendor(
            client_id="CLIENT001", vendor_code="apcoa parking",
            nominal_code="271", account_name="Parking and tolls",
            last_updated=datetime.now(timezone.utc).isoformat(),
            vendor_name="Apcoa Parking",
        )

    def test_override_sets_correction_code_and_leaves_the_suggestion(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                self._seed_mapping(repo)

                corrections = _good_corrections()
                corrections.gl_nominal_code = "999"
                corrections.gl_account_name = "Sundry expenses"
                corrections.gl_correction_reason = "not parking, a car wash"

                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", corrections,
                    actor="paul", source="console",
                )
                self.assertEqual(outcome.outcome, "filed", outcome.message)

                cat = _rows(repo, "SELECT * FROM categorisations WHERE receipt_id = 'r-1'")[0]
                self.assertEqual(cat["suggested_code"], "271", "the audit trail must survive")
                self.assertEqual(cat["suggested_name"], "Parking and tolls")
                self.assertEqual(cat["correction_code"], "999")
                self.assertEqual(cat["correction_name"], "Sundry expenses")
                self.assertIsNotNone(cat["corrected_at"])

                self.assertEqual(outcome.category_code, "999")
                self.assertEqual(outcome.category_name, "Sundry expenses")
            finally:
                repo.close()

    def test_the_sidecar_on_disk_carries_the_corrected_code_and_name(self):
        # Read the file back rather than asserting on the payload: 11.2's whole
        # point is that a sidecar written before the override would disagree with
        # the database permanently.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                self._seed_mapping(repo)
                corrections = _good_corrections()
                corrections.gl_nominal_code = "999"
                corrections.gl_account_name = "Sundry expenses"

                resolve_receipt(
                    repo, env.engine(repo), "r-1", corrections,
                    actor="paul", source="console",
                )

                sidecars = list(config.CLIENTS_ROOT.rglob("*.pdf.json"))
                self.assertEqual(len(sidecars), 1)
                payload = json.loads(sidecars[0].read_text(encoding="utf-8"))
                self.assertEqual(payload["category_code"], "999")
                self.assertEqual(payload["category_name"], "Sundry expenses")
                self.assertEqual(payload["category"], "Sundry expenses")
            finally:
                repo.close()

    def test_no_override_files_the_engine_suggestion(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                self._seed_mapping(repo)
                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", _good_corrections(),
                    actor="paul", source="console",
                )
                self.assertEqual(outcome.category_code, "271")
                cat = _rows(repo, "SELECT * FROM categorisations WHERE receipt_id = 'r-1'")[0]
                self.assertIsNone(cat["correction_code"])
            finally:
                repo.close()


class RememberMappingTest(unittest.TestCase):
    """Test 19."""

    def test_opt_in_off_leaves_the_mapping_table_unchanged_row_for_row(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                before = _rows(repo, "SELECT * FROM categorisations_client_vendors")

                corrections = _good_corrections()
                corrections.gl_nominal_code = "999"
                corrections.gl_account_name = "Sundry expenses"
                self.assertFalse(corrections.remember_gl_for_supplier)

                resolve_receipt(
                    repo, env.engine(repo), "r-1", corrections,
                    actor="paul", source="console",
                )

                self.assertEqual(_rows(repo, "SELECT * FROM categorisations_client_vendors"), before)
            finally:
                repo.close()

    def test_opt_in_on_learns_the_mapping(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                corrections = _good_corrections()
                corrections.gl_nominal_code = "999"
                corrections.gl_account_name = "Sundry expenses"
                corrections.remember_gl_for_supplier = True

                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", corrections,
                    actor="paul", source="console",
                )
                self.assertEqual(outcome.outcome, "filed", outcome.message)

                rows = _rows(repo, "SELECT * FROM categorisations_client_vendors")
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["nominal_code"], "999")
                self.assertEqual(rows[0]["account_name"], "Sundry expenses")
                self.assertEqual(rows[0]["client_id"], "CLIENT001")
            finally:
                repo.close()


class DiscardTest(unittest.TestCase):
    """Test 20."""

    def test_sets_discarded_deletes_no_file_and_removes_no_extraction(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="possible_duplicate", gross_amount=12.0)
                original_file = Path(repo.get_receipt("r-1")["file_path"])
                extractions_before = _rows(repo, "SELECT * FROM extractions")

                outcome = discard_receipt(
                    repo, "r-1", reason="confirmed duplicate of r-original",
                    actor="paul", source="cli",
                )

                self.assertEqual(outcome.outcome, "discarded")
                self.assertEqual(repo.get_receipt("r-1")["status"], "discarded")
                self.assertTrue(original_file.exists(), "the original file must never be deleted")
                self.assertEqual(_rows(repo, "SELECT * FROM extractions"), extractions_before)

                events = _rows(repo, "SELECT * FROM resolution_events")
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["action"], "discard")
                self.assertEqual(events[0]["outcome"], "discarded")
                self.assertIsNone(repo.get_receipt("r-1")["locked_at"])
            finally:
                repo.close()

    def test_discarding_a_receipt_that_does_not_exist_returns_not_found(self):
        with TempEnvironment():
            repo = Repository()
            try:
                outcome = discard_receipt(repo, "nope", "reason", actor="paul", source="cli")
                self.assertEqual(outcome.outcome, "not_found")
                self.assertEqual(_rows(repo, "SELECT * FROM resolution_events"), [])
            finally:
                repo.close()

    def test_a_locked_receipt_is_not_discarded(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                repo.acquire_receipt_lock("r-1")
                outcome = discard_receipt(repo, "r-1", "reason", actor="paul", source="cli")
                self.assertEqual(outcome.outcome, "locked")
                self.assertEqual(repo.get_receipt("r-1")["status"], "needs_review")
            finally:
                repo.close()


class LockReleaseTest(unittest.TestCase):
    """Test 21."""

    def test_the_lock_is_released_on_the_exception_path(self):
        # Forced in the middle of the flow, after the extraction row is written,
        # rather than at the start where the finally is trivially reached.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                with patch.object(
                    service, "file_receipt",
                    side_effect=RuntimeError("disk went away mid-flow"),
                ):
                    outcome = resolve_receipt(
                        repo, env.engine(repo), "r-1", _good_corrections(),
                        actor="paul", source="console",
                    )

                self.assertEqual(outcome.outcome, "error")
                self.assertEqual(outcome.error_detail, "disk went away mid-flow")
                self.assertNotIn("disk went away", outcome.message,
                                 "error_detail is for logs, message is for operators")
                self.assertIsNone(repo.get_receipt("r-1")["locked_at"], "the lock must be released")
                # error writes no event row: the state is unknown.
                self.assertEqual(_rows(repo, "SELECT * FROM resolution_events"), [])
                # The receipt is not left claiming to be filed.
                self.assertIsNone(repo.get_receipt("r-1")["filed_path"])
            finally:
                repo.close()

    def test_the_lock_is_released_on_every_normal_path(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                for receipt_id, corrections in [
                    ("r-filed", _good_corrections()),
                    ("r-invalid", parse_corrections({"supplier_name": "Apcoa"})[0]),
                ]:
                    env.seed(repo, receipt_id=receipt_id)
                    resolve_receipt(
                        repo, env.engine(repo), receipt_id, corrections,
                        actor="paul", source="console",
                    )
                    self.assertIsNone(
                        repo.get_receipt(receipt_id)["locked_at"],
                        f"lock left held on {receipt_id}",
                    )

                env.seed(repo, receipt_id="r-discarded")
                discard_receipt(repo, "r-discarded", "reason", actor="paul", source="cli")
                self.assertIsNone(repo.get_receipt("r-discarded")["locked_at"])
            finally:
                repo.close()


class EventAttributionTest(unittest.TestCase):
    def test_the_event_records_the_actor_and_source_the_caller_passed(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                resolve_receipt(
                    repo, env.engine(repo), "r-1", _good_corrections(),
                    actor="clare@intellitax.co.uk", source="console",
                )
                event = _rows(repo, "SELECT * FROM resolution_events")[0]
                self.assertEqual(event["actor"], "clare@intellitax.co.uk")
                self.assertEqual(event["source"], "console")
                self.assertEqual(event["action"], "resolve")
                self.assertEqual(event["outcome"], "filed")
                # The corrections that were applied are recorded with the event.
                self.assertEqual(
                    json.loads(event["corrections_json"]),
                    {"supplier_name": "Apcoa Parking", "gross_amount": 12.0},
                )
            finally:
                repo.close()

    def test_source_and_actor_are_required(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                with self.assertRaises(TypeError):
                    resolve_receipt(repo, env.engine(repo), "r-1", Corrections(), actor="paul")
                with self.assertRaises(TypeError):
                    discard_receipt(repo, "r-1", "reason", actor="paul")
            finally:
                repo.close()


class ZeroCorrectionTest(unittest.TestCase):
    def test_a_corrected_zero_survives_the_merge(self):
        # 3.2 in the service rather than the CLI: key presence, not truthiness.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(
                    repo, supplier_name="Apcoa Parking",
                    net_amount=96.0, vat_amount=16.0, gross_amount=96.0,
                )
                corrections, errors = parse_corrections({"vat_amount": "0"})
                self.assertEqual(errors, {})

                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-1", corrections,
                    actor="paul", source="console",
                )

                self.assertEqual(outcome.outcome, "filed", outcome.message)
                row = _rows(
                    repo,
                    "SELECT * FROM extractions WHERE engine = 'manual_correction'",
                )[0]
                self.assertEqual(row["vat_amount"], 0.0)
                self.assertEqual(row["net_amount"], 96.0)
            finally:
                repo.close()


if __name__ == "__main__":
    unittest.main()

"""Design document 4.2: get_resolution_view, the read side of the service.

Read-only, takes no lock, returns None if the receipt does not exist. It is what
both the console's receipt detail page and the rewritten CLI render, so the two
cannot drift into showing different things.

Also asserts the layering constraint from 4.1, which is the one that erodes
quietly: no Flask, no argparse, nothing under worker/email/, nothing that prints
or reads input.
"""

import subprocess
import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path

import config

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

from worker.database.repository import Repository
from worker.resolution.service import ResolutionView, get_resolution_view


class TempEnvironment:
    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved = {
            "DB_PATH": config.DB_PATH,
            "CLIENTS_BY_CODE": config.CLIENTS_BY_CODE,
            "LOGS_DIR": config.LOGS_DIR,
            "RUNS_LOG": config.RUNS_LOG,
        }
        config.DB_PATH = self.path / "receipts.db"
        config.LOGS_DIR = self.path / "logs"
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
        config.CLIENTS_BY_CODE = {
            "ABC": {"client_name": "Test Client", "business_type": "PHV_DRIVER"}
        }
        return self

    def __exit__(self, *exc):
        for name, value in self._saved.items():
            setattr(config, name, value)
        self._temp.cleanup()
        return False

    def seed(self, repo, receipt_id, status="needs_review", client_code="ABC"):
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
            client_code=client_code,
            source="email",
        )
        repo._conn.execute(
            "UPDATE receipts SET status = ? WHERE receipt_id = ?", (status, receipt_id)
        )
        repo._conn.commit()
        return file_path

    def add_extraction(self, repo, receipt_id, extraction_id, extracted_at, **kwargs):
        defaults = dict(
            engine="openai_vision",
            supplier_name="Apcoa Parking",
            invoice_date="2026-04-01",
            net_amount=10.0,
            vat_amount=2.0,
            gross_amount=12.0,
            currency="GBP",
            raw_response="{}",
            validation_status="needs_review",
            validation_notes=["seeded"],
        )
        defaults.update(kwargs)
        repo.save_extraction(extraction_id=extraction_id, receipt_id=receipt_id, **defaults)
        # save_extraction stamps its own timestamp; force a known order.
        repo._conn.execute(
            "UPDATE extractions SET extracted_at = ? WHERE extraction_id = ?",
            (extracted_at, extraction_id),
        )
        repo._conn.commit()


class GetResolutionViewTest(unittest.TestCase):
    def test_returns_none_for_a_receipt_that_does_not_exist(self):
        with TempEnvironment():
            repo = Repository()
            try:
                self.assertIsNone(get_resolution_view(repo, "no-such-receipt"))
            finally:
                repo.close()

    def test_history_is_newest_first_and_extraction_is_the_latest(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-1")
                env.add_extraction(repo, "r-1", "ext-old", "2026-07-01T00:00:00+00:00")
                env.add_extraction(repo, "r-1", "ext-new", "2026-07-27T00:00:00+00:00")

                view = get_resolution_view(repo, "r-1")
                self.assertIsInstance(view, ResolutionView)
                self.assertEqual(view.extraction["extraction_id"], "ext-new")
                self.assertEqual(
                    [e["extraction_id"] for e in view.extraction_history],
                    ["ext-new", "ext-old"],
                )
            finally:
                repo.close()

    def test_client_name_and_business_type_come_from_the_client_lookup(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-1")
                env.add_extraction(repo, "r-1", "ext-1", "2026-07-27T00:00:00+00:00")
                view = get_resolution_view(repo, "r-1")
                self.assertEqual(view.client_name, "Test Client")
                self.assertEqual(view.business_type, "PHV_DRIVER")
            finally:
                repo.close()

    def test_unknown_client_code_falls_back_to_the_code_itself(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-1", client_code="NOPE")
                env.add_extraction(repo, "r-1", "ext-1", "2026-07-27T00:00:00+00:00")
                view = get_resolution_view(repo, "r-1")
                self.assertEqual(view.client_name, "NOPE")
                self.assertEqual(view.business_type, "UNSPECIFIED")
            finally:
                repo.close()

    def test_categorisation_may_legitimately_be_none(self):
        # The non-ok path saves no categorisation, so this is normal rather than
        # an error, and the console must render it.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-1")
                env.add_extraction(repo, "r-1", "ext-1", "2026-07-27T00:00:00+00:00")
                view = get_resolution_view(repo, "r-1")
                self.assertIsNone(view.categorisation)
                self.assertIsNone(view.effective_gl_code)
            finally:
                repo.close()

    def test_effective_gl_code_prefers_the_correction(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-1", status="ok")
                env.add_extraction(repo, "r-1", "ext-1", "2026-07-27T00:00:00+00:00")
                repo.save_categorisation(
                    categorisation_id="cat-1",
                    receipt_id="r-1",
                    extraction_id="ext-1",
                    client_id="CLIENT001",
                    business_type="PHV_DRIVER",
                    vendor_key=None,
                    suggested_code="271",
                    suggested_name="Parking and tolls",
                    confidence="high",
                    match_source="client_lookup",
                    matched_vendor="apcoa parking",
                    needs_review=False,
                    categorised_at=datetime.now(timezone.utc).isoformat(),
                )

                view = get_resolution_view(repo, "r-1")
                self.assertEqual(view.effective_gl_code, "271")

                repo.update_categorisation("cat-1", "999", "Sundry expenses", "operator override")
                view = get_resolution_view(repo, "r-1")
                self.assertEqual(view.effective_gl_code, "999")
                # suggested_code is the audit trail and must survive.
                self.assertEqual(view.categorisation["suggested_code"], "271")
            finally:
                repo.close()

    def test_duplicate_of_is_resolved_for_a_possible_duplicate(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-original", status="ok")
                env.add_extraction(repo, "r-original", "ext-original", "2026-07-01T00:00:00+00:00")
                env.seed(repo, "r-dup", status="possible_duplicate")
                env.add_extraction(repo, "r-dup", "ext-dup", "2026-07-27T00:00:00+00:00")
                repo.set_duplicate_of("r-dup", "r-original")

                view = get_resolution_view(repo, "r-dup")
                self.assertEqual(view.duplicate_of_receipt["receipt_id"], "r-original")
                self.assertEqual(view.duplicate_of_extraction["extraction_id"], "ext-original")
            finally:
                repo.close()

    def test_no_duplicate_fields_when_the_receipt_is_not_a_duplicate(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-1")
                env.add_extraction(repo, "r-1", "ext-1", "2026-07-27T00:00:00+00:00")
                view = get_resolution_view(repo, "r-1")
                self.assertIsNone(view.duplicate_of_receipt)
                self.assertIsNone(view.duplicate_of_extraction)
            finally:
                repo.close()

    def test_is_locked_reports_the_lock_without_acting_on_it(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-1")
                env.add_extraction(repo, "r-1", "ext-1", "2026-07-27T00:00:00+00:00")
                self.assertFalse(get_resolution_view(repo, "r-1").is_locked)

                self.assertTrue(repo.acquire_receipt_lock("r-1"))
                view = get_resolution_view(repo, "r-1")
                self.assertTrue(view.is_locked)
                # Informational only: the view still returns everything.
                self.assertEqual(view.extraction["extraction_id"], "ext-1")
            finally:
                repo.close()

    def test_the_view_takes_no_lock_of_its_own(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-1")
                env.add_extraction(repo, "r-1", "ext-1", "2026-07-27T00:00:00+00:00")
                get_resolution_view(repo, "r-1")
                # If the view had locked it, this would fail.
                self.assertTrue(repo.acquire_receipt_lock("r-1"))
            finally:
                repo.close()

    def test_resolution_events_are_included(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-1")
                env.add_extraction(repo, "r-1", "ext-1", "2026-07-27T00:00:00+00:00")
                repo.save_resolution_event(
                    event_id="e-1", receipt_id="r-1", actor="paul", source="cli",
                    action="resolve", outcome="still_invalid",
                    created_at="2026-07-27T00:00:00+00:00",
                )
                view = get_resolution_view(repo, "r-1")
                self.assertEqual([e["event_id"] for e in view.resolution_events], ["e-1"])
            finally:
                repo.close()

    def test_gl_code_options_fall_back_to_the_vendor_tables(self):
        # The CoA is loaded at step 12. Until then 11.1 says fall back to
        # distinct (nominal_code, account_name) pairs so the console still works.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-1")
                env.add_extraction(repo, "r-1", "ext-1", "2026-07-27T00:00:00+00:00")
                now = datetime.now(timezone.utc).isoformat()
                repo.upsert_client_vendor(
                    client_id="CLIENT001", vendor_code="apcoa parking",
                    nominal_code="271", account_name="Parking and tolls",
                    last_updated=now, vendor_name="Apcoa Parking",
                )
                repo.upsert_firm_vendor(
                    business_type="PHV_DRIVER", vendor_code="shell",
                    nominal_code="500", account_name="Fuel", last_updated=now,
                    vendor_name="Shell",
                )

                options = get_resolution_view(repo, "r-1").gl_code_options
                pairs = {(o["nominal_code"], o["account_name"]) for o in options}
                self.assertIn(("271", "Parking and tolls"), pairs)
                self.assertIn(("500", "Fuel"), pairs)
            finally:
                repo.close()

    def test_a_receipt_with_no_extraction_still_returns_a_view(self):
        # get_resolution_view is read-only and must not decide policy: whether a
        # missing extraction is not_found is resolve_receipt()'s judgement.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, "r-bare")
                view = get_resolution_view(repo, "r-bare")
                self.assertIsNotNone(view)
                self.assertIsNone(view.extraction)
                self.assertEqual(view.extraction_history, [])
            finally:
                repo.close()


class LayeringTest(unittest.TestCase):
    """4.1: the constraint that makes the service reusable by four callers."""

    def test_the_service_imports_no_web_cli_or_email_modules(self):
        repo_root = Path(__file__).resolve().parent.parent
        code = (
            "import sys\n"
            "import worker.resolution.service\n"
            "banned = [m for m in sys.modules\n"
            "          if m == 'flask' or m.startswith('flask.')\n"
            "          or m == 'argparse'\n"
            "          or m.startswith('worker.email')]\n"
            "print(','.join(sorted(banned)))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=str(repo_root),
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "", f"forbidden imports: {result.stdout!r}")

    def test_the_service_neither_prints_nor_reads_input(self):
        source = (
            Path(__file__).resolve().parent.parent
            / "worker" / "resolution" / "service.py"
        ).read_text(encoding="utf-8")
        for banned in ("print(", "input(", "sys.exit"):
            self.assertNotIn(banned, source, f"{banned} does not belong in the domain layer")


if __name__ == "__main__":
    unittest.main()

"""Design document test 9: the sidecar carries a nominal code and a name, and
never a match_source.

IntelliBooks' catOptions() matches categories on name with no codes, so a
nominal code in `category` matches nothing and the receipt arrives
uncategorised. "Post to cashbook" then copies that value into a real
transaction, which is why this reaches the books.

Four call sites build this file. They must all produce the same key set, or the
format depends on which path filed the receipt, which is how it drifted into
four different kinds of value in the first place.
"""

import contextlib
import io
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
from worker.extraction.base import ExtractionResult
from worker.extraction_pipeline import process_extraction_result
from worker.filing import make_enriched_sidecar
import app
import resolve_receipt


class TempEnvironment:
    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved = {
            "DB_PATH": config.DB_PATH,
            "CLIENTS_ROOT": config.CLIENTS_ROOT,
            "CLIENTS_BY_ID": config.CLIENTS_BY_ID,
            # 10d.35 re-reads the registry at the top of every poll. Pinned at a
            # path that does not exist, with the remembered mtime set to match, so
            # the re-read sees no change and leaves the registry this fixture
            # built. Without it a test would silently run against the live
            # clients.json the moment somebody saved it.
            "CLIENTS_JSON": config.CLIENTS_JSON,
            "_CLIENTS_MTIME": config._CLIENTS_MTIME,
            "LOGS_DIR": config.LOGS_DIR,
            "RUNS_LOG": config.RUNS_LOG,
            "REVIEW_ROOT": config.REVIEW_ROOT,
        }
        config.DB_PATH = self.path / "receipts.db"
        config.CLIENTS_ROOT = self.path / "Clients"
        config.CLIENTS_ROOT.mkdir(parents=True, exist_ok=True)
        # Not created: file_review() makes it on demand.
        config.REVIEW_ROOT = self.path / "Review"
        # attach_log_handler() resolves LOGS_DIR at call time, so a test that runs
        # a CLI entry point appends to the live resolve.log without this. The four
        # process logs moved here from DATA_DIR with 18.2a.
        config.LOGS_DIR = self.path / "logs"
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
        config.CLIENTS_JSON = self.path / "clients-not-placed.json"
        config._CLIENTS_MTIME = config._registry_mtime()
        config.CLIENTS_BY_ID = {
            "CLIENT001": {"client_name": "Test Client", "client_folder_name": "Test Client",
                          "client_id": "CLIENT001", "firm_id": "INTELLITAX", "trade": "UNSPECIFIED"}
        }
        return self

    def __exit__(self, *exc):
        for name, value in self._saved.items():
            setattr(config, name, value)
        self._temp.cleanup()
        return False

    def source_file(self, name):
        path = self.path / name
        path.write_text("dummy", encoding="utf-8")
        return path

    def seed_receipt(self, repo, receipt_id, filename="parking.pdf", status=None):
        file_path = self.source_file(f"src-{receipt_id}.pdf")
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
            source="email",
        )
        if status:
            repo._conn.execute(
                "UPDATE receipts SET status = ? WHERE receipt_id = ?", (status, receipt_id)
            )
            repo._conn.commit()
        return file_path

    def seed_mapping(self, repo, vendor_code="apcoa parking", code="271", name="Parking and tolls"):
        # vendor_code is normalise_description("Apcoa Parking"), which is what
        # the engine looks up. Seeding "apcoa" would silently never match.
        repo.upsert_client_vendor(
            client_id="CLIENT001",
            vendor_code=vendor_code,
            nominal_code=code,
            account_name=name,
            last_updated=datetime.now(timezone.utc).isoformat(),
            vendor_name="Apcoa Parking",
        )

    def filed_sidecar(self):
        # Amendment 170: Clients\{name}\IntelliBooks\Receipts\{tax year}\.
        # Spelled out rather than built from config, so a wrong constant is caught
        # here instead of agreeing with itself.
        found = sorted(config.CLIENTS_ROOT.glob("*/IntelliBooks/Receipts/*/*.json"))
        self_assert = len(found)
        assert self_assert == 1, f"expected exactly one filed sidecar, found {found}"
        return json.loads(found[0].read_text(encoding="utf-8"))

    def review_sidecar(self):
        # Intellibills\Review\{CODE}\, not the client folder, since 18.2a.
        found = sorted(config.REVIEW_ROOT.glob("*/*.review.json"))
        assert len(found) == 1, f"expected exactly one review sidecar, found {found}"
        return json.loads(found[0].read_text(encoding="utf-8"))


def _extraction(supplier="Apcoa Parking", gross=12.0, net=10.0, vat=2.0, date="2026-04-01"):
    return ExtractionResult(
        engine="openai_vision",
        supplier_name=supplier,
        invoice_date=date,
        net_amount=net,
        vat_amount=vat,
        gross_amount=gross,
        currency="GBP",
        raw_response="{}",
    )


def _run_pipeline(env, repo, receipt_id, extraction, file_path):
    engine = CategorisationEngine(repo=repo, enable_ai_fallback=False)
    return process_extraction_result(
        receipt_id=receipt_id,
        extraction=extraction,
        file_path=file_path,
        filename="parking.pdf",
        firm_id="INTELLITAX",
        client_id="CLIENT001",
        source="email",
        message_id=f"msg-{receipt_id}",
        repo=repo,
        categorisation_engine=engine,
        stats={},
        run_id="test-run",
        pipeline_version="test-version",
    )


class MatchedCategoryTest(unittest.TestCase):
    def test_matched_receipt_carries_the_code_and_the_name(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed_mapping(repo)
                file_path = env.seed_receipt(repo, "r-matched")
                _run_pipeline(env, repo, "r-matched", _extraction(), file_path)
            finally:
                repo.close()

            payload = env.filed_sidecar()
            self.assertEqual(payload["category_code"], "271")
            self.assertEqual(payload["category_name"], "Parking and tolls")
            # The legacy key holds the name, which is what Desktop matches on.
            self.assertEqual(payload["category"], "Parking and tolls")


class UnmatchedCategoryTest(unittest.TestCase):
    def test_unmatched_receipt_writes_three_nulls_and_never_a_match_source(self):
        # 18 of the 32 sidecars on disk hold the literal string "unmatched",
        # which is a match_source. Desktop cannot match it, and someone then
        # posts it to the cashbook. null fails honestly.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                file_path = env.seed_receipt(repo, "r-unmatched")
                _run_pipeline(env, repo, "r-unmatched", _extraction(supplier="Totally Unknown Ltd"), file_path)
            finally:
                repo.close()

            payload = env.filed_sidecar()
            for key in ("category_code", "category_name", "category"):
                self.assertIn(key, payload)
                self.assertIsNone(payload[key], f"{key} was {payload[key]!r}")
            self.assertNotIn("unmatched", [payload[k] for k in payload])
            self.assertNotIn("none", [payload[k] for k in ("category_code", "category_name", "category")])


class AllFourCallSitesTest(unittest.TestCase):
    """Four writers of one file format is how it diverged. Lock the key set."""

    def _keys_from_pipeline_ok_path(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed_mapping(repo)
                file_path = env.seed_receipt(repo, "r-ok")
                _run_pipeline(env, repo, "r-ok", _extraction(), file_path)
            finally:
                repo.close()
            return sorted(env.filed_sidecar().keys())

    def _keys_from_pipeline_review_path(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                file_path = env.seed_receipt(repo, "r-review")
                # No supplier: validation returns failed, so the review branch runs.
                _run_pipeline(env, repo, "r-review", _extraction(supplier=None, gross=None), file_path)
            finally:
                repo.close()
            payload = env.review_sidecar()
            return sorted(payload["extracted_values"].keys())

    def _keys_from_app_recovery_path(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed_mapping(repo)
                env.seed_receipt(repo, "r-recover")
                repo.save_extraction(
                    extraction_id="ext-recover",
                    receipt_id="r-recover",
                    engine="openai_vision",
                    supplier_name="Apcoa Parking",
                    invoice_date="2026-04-01",
                    net_amount=10.0,
                    vat_amount=2.0,
                    gross_amount=12.0,
                    currency="GBP",
                    raw_response="{}",
                    validation_status="ok",
                    validation_notes=[],
                )
                engine = CategorisationEngine(repo=repo, enable_ai_fallback=False)
                app._file_unfiled_ok_receipts(repo, engine, {})
            finally:
                repo.close()
            return sorted(env.filed_sidecar().keys())

    def _keys_from_resolve_receipt_path(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed_mapping(repo)
                env.seed_receipt(repo, "r-resolve")
                repo.save_extraction(
                    extraction_id="ext-resolve",
                    receipt_id="r-resolve",
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

            argv = ["resolve_receipt.py", "r-resolve", "--supplier", "Apcoa Parking", "--gross", "12.00"]
            with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                exit_code = resolve_receipt.main()
            self.assertEqual(exit_code, 0)
            return sorted(env.filed_sidecar().keys()), env.filed_sidecar()

    def test_all_four_call_sites_write_the_same_keys(self):
        pipeline_ok = self._keys_from_pipeline_ok_path()
        pipeline_review = self._keys_from_pipeline_review_path()
        app_recovery = self._keys_from_app_recovery_path()
        resolve_keys, _ = self._keys_from_resolve_receipt_path()

        for name, keys in [
            ("pipeline review path", pipeline_review),
            ("app recovery path", app_recovery),
            ("resolve_receipt path", resolve_keys),
        ]:
            self.assertEqual(pipeline_ok, keys, f"{name} disagrees with the pipeline ok path")

        for key in ("category", "category_code", "category_name"):
            self.assertIn(key, pipeline_ok)

    def test_resolve_receipt_writes_the_three_keys_after_a_manual_correction(self):
        _, payload = self._keys_from_resolve_receipt_path()
        self.assertEqual(payload["category_code"], "271")
        self.assertEqual(payload["category_name"], "Parking and tolls")
        self.assertEqual(payload["category"], "Parking and tolls")


class MakeEnrichedSidecarTest(unittest.TestCase):
    def test_signature_takes_a_code_and_a_name(self):
        payload = make_enriched_sidecar(
            receipt_id="r-1",
            source="email",
            client_id="CLIENT001",
            client_name="Test Client",
            capture_date="2026-04-01T00:00:00+00:00",
            invoice_date="2026-04-01",
            supplier="Apcoa Parking",
            net=10.0,
            vat=2.0,
            gross=12.0,
            currency="GBP",
            category_code="271",
            category_name="Parking and tolls",
            confidence="high",
            validation_status="ok",
            asserted=None,
            original_filename="parking.pdf",
        )
        self.assertEqual(payload["category_code"], "271")
        self.assertEqual(payload["category_name"], "Parking and tolls")
        self.assertEqual(payload["category"], "Parking and tolls")

    def test_no_code_and_no_name_gives_three_nulls(self):
        payload = make_enriched_sidecar(
            receipt_id="r-1",
            source="email",
            client_id="CLIENT001",
            client_name="Test Client",
            capture_date="2026-04-01T00:00:00+00:00",
            invoice_date="2026-04-01",
            supplier="Apcoa Parking",
            net=None,
            vat=None,
            gross=12.0,
            currency="GBP",
            category_code=None,
            category_name=None,
            confidence="none",
            validation_status="ok",
            asserted=None,
            original_filename="parking.pdf",
        )
        self.assertIsNone(payload["category_code"])
        self.assertIsNone(payload["category_name"])
        self.assertIsNone(payload["category"])


if __name__ == "__main__":
    unittest.main()

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
from worker import publish
from tests.chart_fixtures import TempChartBundle

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
            # Sub-step 10f.2, added 2026-09-09 by stage 4. **This
            # environment never redirected them and, until stage 4, never
            # needed to: nothing this file drove published anything.**
            # Amendment 293 made every receipt publish, so without these
            # two every test here writes into the one folder
            # tests/live_paths.py set up for the whole run and each test
            # sees every earlier test's items. That is the fourth instance
            # of the leak tests/test_logs_isolation.py exists to catch,
            # and it was found the same way its docstring describes: a
            # test that passed on its own and failed in the file.
            "INTELLIBOOKS_ROOT": config.INTELLIBOOKS_ROOT,
            "INTELLIBOOKS_PUBLISH_DIR": config.INTELLIBOOKS_PUBLISH_DIR,
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
        config.INTELLIBOOKS_ROOT = self.path / "IntelliBooks"
        config.INTELLIBOOKS_PUBLISH_DIR = config.INTELLIBOOKS_ROOT / "Published"
        config.INTELLIBOOKS_PUBLISH_DIR.mkdir(parents=True, exist_ok=True)
        config.CLIENTS_JSON = self.path / "clients-not-placed.json"
        config._CLIENTS_MTIME = config._registry_mtime()
        config.CLIENTS_BY_ID = {
            "CLIENT001": {"client_name": "Test Client", "client_folder_name": "Test Client",
                          "client_id": "CLIENT001", "firm_id": "INTELLITAX", "trade": "UNSPECIFIED"}
        }
        # A chart holding the codes this file seeds, so the fallback check has
        # something to check against and the test does not read the real bundle
        # out of OneDrive. See tests/chart_fixtures.py for why it was needed.
        self._chart = TempChartBundle().__enter__()
        return self

    def __exit__(self, *exc):
        self._chart.__exit__(*exc)
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

    def seed_mapping(self, repo, vendor_key="apcoa parking", code="271", name="Parking and tolls"):
        # vendor_key is normalise_description("Apcoa Parking"), which is what
        # the engine looks up. Seeding "apcoa" would silently never match.
        repo.upsert_client_vendor(
            client_id="CLIENT001",
            vendor_key=vendor_key,
            nominal_code=code,
            account_name=name,
            last_updated=datetime.now(timezone.utc).isoformat(),
            vendor_name="Apcoa Parking",
        )

    def filed_sidecar(self):
        """The payload that travelled with this receipt, minus the item's own keys.

        **Repointed 2026-09-09 by stage 4, and the name is kept on purpose.**
        ~~Amendment 170: Clients\{name}\IntelliBooks\Receipts\{tax year}\.~~
        18.2b's rules table makes the client folder copy **image only**, so
        there is no sidecar there to read. The same `make_enriched_sidecar()`
        payload now travels inside the published item, so this reads that and
        drops the four keys the item adds on top of it: the document, its media
        type, the validation notes and the id it duplicates. ~~the four keys the
        item adds on top of it~~ **Five from 2026-09-11, step 10l's
        `category_unconfirmed`, and the list is no longer written out here.**

        Every assertion in this file is about the sidecar's own keys, so
        dropping the item's own is what keeps those assertions saying the same
        thing rather than being loosened to fit.

        **`publish.ITEM_ONLY_KEYS` rather than a list repeated here.** The four
        were written out until step 10l added a fifth, and this comparison then
        failed with the new key counted as a sidecar key. A list in a test of
        what another module adds goes stale the moment that module adds one, so
        the module states it and this reads it.
        """
        found = sorted(config.INTELLIBOOKS_PUBLISH_DIR.glob("*.json"))
        assert len(found) == 1, f"expected exactly one published item, found {found}"
        payload = json.loads(found[0].read_text(encoding="utf-8"))
        for item_only in publish.ITEM_ONLY_KEYS:
            payload.pop(item_only, None)
        # And the copy under Clients\ carries no data file at all, which is the
        # other half of the same rule and is free to assert here.
        assert not sorted(config.CLIENTS_ROOT.rglob("*.json")), (
            "a data file landed under Clients\\, and 18.2b says image only")
        return payload

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
                # The sweep publishes what was never published, and it
                # ignores anything created before the earliest publish_events
                # row. Sub-step 10f.13's cutover, which stops the first run
                # after stage 4 backfilling every historical receipt. So a row
                # has to exist and be old enough for this receipt to be in
                # scope: without it the sweep correctly does nothing and this
                # test would prove nothing.
                repo.save_publish_event(
                    event_id="cutover", receipt_id="r-someone-else",
                    destination="intellibooks", outcome="published",
                    created_at="2000-01-01T00:00:00+00:00",
                    item_path="somewhere.json")
                engine = CategorisationEngine(repo=repo, enable_ai_fallback=False)
                app._publish_unpublished_receipts(repo, engine, {})
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

            # **The payload is captured at the point it is built, not read
            # off disk, and that is a finding rather than a convenience.**
            # Stage 4, 2026-09-09: `resolve_receipt()` no longer writes it
            # anywhere. It used to hand it to `file_receipt()`, which wrote it
            # beside the filed image; 18.2b makes that copy image only, and
            # `resolve_receipt()` does not publish. So a CLI-resolved receipt's
            # corrected values reach the database and no file at all, which is
            # flagged in `2026-09-09_REPORT_claude_code_stage4_pipeline.md` and
            # is 10f.15's to answer. This call site still builds the payload,
            # so the four-way comparison below is still a real comparison.
            from worker.resolution import service as resolution_service

            built = []
            real = resolution_service.make_enriched_sidecar

            def spy(**kwargs):
                payload = real(**kwargs)
                built.append(payload)
                return payload

            argv = ["resolve_receipt.py", "r-resolve", "--supplier", "Apcoa Parking", "--gross", "12.00"]
            with patch.object(resolution_service, "make_enriched_sidecar", spy), \
                    patch.object(sys, "argv", argv), \
                    contextlib.redirect_stdout(io.StringIO()):
                exit_code = resolve_receipt.main()
            self.assertEqual(exit_code, 0)
            payload, = built
            return sorted(payload.keys()), payload

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


class ChartFallbackThroughThePipelineTest(unittest.TestCase):
    """The whole of Task 2, through process_extraction_result() rather than
    against resolve_against_chart() on its own.

    tests/test_fallback_accounts.py covers the check in isolation. This is the
    other half: the substituted code reaching the sidecar on disk, the audit row
    reaching the database, and the event log naming the outcome. Without it the
    unit tests would pass for a check that was never called.
    """

    def _run(self, mapping_code, mapping_name, accounts, fallbacks):
        with TempEnvironment() as env:
            with TempChartBundle(accounts=accounts, fallbacks=fallbacks):
                repo = Repository()
                try:
                    env.seed_mapping(repo, code=mapping_code, name=mapping_name)
                    file_path = env.seed_receipt(repo, "r-fb")
                    _run_pipeline(env, repo, "r-fb", _extraction(), file_path)
                    events = repo.list_resolution_events("r-fb")
                finally:
                    repo.close()
                sidecar = env.filed_sidecar()
                log = config.LOGS_DIR / "receipt_events_INTELLITAX.ndjson"
                entries = [json.loads(line) for line in
                           log.read_text(encoding="utf-8").splitlines() if line.strip()]
        return sidecar, events, entries

    def test_a_substitution_reaches_the_sidecar_the_database_and_the_log(self):
        sidecar, events, entries = self._run(
            "7391", "Car wash",
            accounts=[("7310", "Vehicle repairs and servicing")],
            fallbacks=[("7391", "7310")],
        )
        # The sidecar carries an account the client's chart actually holds.
        self.assertEqual(sidecar["category_code"], "7310")
        self.assertEqual(sidecar["category_name"], "Vehicle repairs and servicing")
        self.assertEqual(sidecar["category"], "Vehicle repairs and servicing")
        # And the swap is not silent.
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["actor"], "pipeline")
        self.assertEqual(events[0]["outcome"], "substituted")
        self.assertEqual(
            [e.get("chart_outcome") for e in entries if e["action"] == "extracted"],
            ["substituted"],
        )

    def test_an_unusable_code_files_the_receipt_with_no_account(self):
        sidecar, events, entries = self._run(
            "7391", "Car wash",
            accounts=[("7500", "Printing and postage")],
            fallbacks=[],
        )
        # Three nulls, not the string "unmatched": Desktop cannot match that and
        # someone then posts it to the cashbook.
        self.assertIsNone(sidecar["category_code"])
        self.assertIsNone(sidecar["category_name"])
        self.assertIsNone(sidecar["category"])
        self.assertEqual(events[0]["outcome"], "unusable")
        self.assertEqual(
            [e.get("chart_outcome") for e in entries if e["action"] == "extracted"],
            ["unusable"],
        )

    def test_the_ordinary_case_leaves_no_event_and_no_log_key(self):
        # The other half. Without it both tests above would pass for a check that
        # fired on every receipt, which would bury the two that matter.
        sidecar, events, entries = self._run(
            "7310", "Vehicle repairs and servicing",
            accounts=[("7310", "Vehicle repairs and servicing")],
            fallbacks=[("7391", "7310")],
        )
        self.assertEqual(sidecar["category_code"], "7310")
        self.assertEqual(events, [])
        self.assertEqual(
            [e.get("chart_outcome") for e in entries if e["action"] == "extracted"],
            [None],
        )


if __name__ == "__main__":
    unittest.main()

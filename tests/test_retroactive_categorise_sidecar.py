"""retroactive_categorise.py must not invent values it did not measure.

It writes into a filed sidecar directly, bypassing make_enriched_sidecar()
entirely, and it can still be run by hand. Its `or "unmatched"` fallback is the
source of the 18 sidecars on disk holding a match_source in the category field.
Fixing the writer in worker/filing.py does not stop this script undoing it.
"""

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import config
from tests.chart_fixtures import TempChartBundle

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

from worker.database.repository import Repository
import retroactive_categorise


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
        }
        config.DB_PATH = self.path / "receipts.db"
        config.CLIENTS_ROOT = self.path / "Clients"
        config.CLIENTS_ROOT.mkdir(parents=True, exist_ok=True)
        config.LOGS_DIR = self.path / "logs"
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.RUNS_LOG = config.LOGS_DIR / "runs.ndjson"
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

    def seed_filed_receipt(self, receipt_id, supplier):
        """A filed receipt with its sidecar on disk, and no categorisation row."""
        # Amendment 170. Literal, so it describes the layout rather than deriving it.
        filed_dir = (
            config.CLIENTS_ROOT / "Test Client" / "IntelliBooks" / "Receipts" / "2026-27"
        )
        filed_dir.mkdir(parents=True, exist_ok=True)
        filed_image = filed_dir / f"2026-04-01_{receipt_id}_12.00.pdf"
        filed_image.write_text("dummy", encoding="utf-8")
        sidecar_path = filed_dir / (filed_image.name + ".json")
        sidecar_path.write_text(
            json.dumps({
                "receipt_id": receipt_id,
                "supplier": supplier,
                "gross": 12.0,
                "category_code": None,
                "category_name": None,
                "category": None,
                "confidence": "none",
            }, indent=2),
            encoding="utf-8",
        )

        source = self.path / f"src-{receipt_id}.pdf"
        source.write_text("dummy", encoding="utf-8")
        repo = Repository()
        try:
            repo.save_receipt(
                receipt_id=receipt_id,
                message_id=f"msg-{receipt_id}",
                email_subject="Test",
                email_from="sender@example.com",
                email_received_at="2026-01-01T00:00:00Z",
                filename=f"{receipt_id}.pdf",
                file_path=source,
                file_hash=f"hash-{receipt_id}",
                firm_id="INTELLITAX",
                client_id="CLIENT001",
                source="email",
            )
            repo.save_extraction(
                extraction_id=f"ext-{receipt_id}",
                receipt_id=receipt_id,
                engine="openai_vision",
                supplier_name=supplier,
                invoice_date="2026-04-01",
                net_amount=10.0,
                vat_amount=2.0,
                gross_amount=12.0,
                currency="GBP",
                raw_response="{}",
                validation_status="ok",
                validation_notes=[],
            )
            repo.mark_receipt_filed(receipt_id, str(filed_image))
        finally:
            repo.close()
        return sidecar_path


class RetroactiveCategoriseTest(unittest.TestCase):
    def test_unmatched_receipt_leaves_three_nulls_not_the_string_unmatched(self):
        with TempEnvironment() as env:
            sidecar_path = env.seed_filed_receipt("r-unmatched", "Totally Unknown Ltd")

            with patch.object(retroactive_categorise, "AFFECTED_RECEIPTS", ["r-unmatched"]):
                retroactive_categorise.main()

            payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
            for key in ("category_code", "category_name", "category"):
                self.assertIn(key, payload)
                self.assertIsNone(payload[key], f"{key} was {payload[key]!r}")
            self.assertNotIn("unmatched", list(payload.values()))
            self.assertNotIn("none", [payload[k] for k in ("category_code", "category_name", "category")])

    def test_matched_receipt_gets_the_code_and_the_name(self):
        with TempEnvironment() as env:
            sidecar_path = env.seed_filed_receipt("r-matched", "Apcoa Parking")
            repo = Repository()
            try:
                repo.upsert_client_vendor(
                    client_id="CLIENT001",
                    vendor_code="apcoa parking",
                    nominal_code="271",
                    account_name="Parking and tolls",
                    last_updated="2026-07-27T00:00:00+00:00",
                    vendor_name="Apcoa Parking",
                )
            finally:
                repo.close()

            with patch.object(retroactive_categorise, "AFFECTED_RECEIPTS", ["r-matched"]):
                retroactive_categorise.main()

            payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["category_code"], "271")
            self.assertEqual(payload["category_name"], "Parking and tolls")
            self.assertEqual(payload["category"], "Parking and tolls")

    def test_existing_categorisation_row_supplies_the_name_too(self):
        # The existing-row branch reads a full categorisations row, so it has
        # suggested_name available and must use it rather than falling back.
        with TempEnvironment() as env:
            sidecar_path = env.seed_filed_receipt("r-existing", "Apcoa Parking")
            repo = Repository()
            try:
                repo.save_categorisation(
                    categorisation_id="cat-existing",
                    receipt_id="r-existing",
                    extraction_id="ext-r-existing",
                    client_id="CLIENT001",
                    trade="UNSPECIFIED",
                    vendor_key=None,
                    suggested_code="999",
                    suggested_name="Sundry expenses",
                    confidence="medium",
                    match_source="firm_lookup",
                    matched_vendor="apcoa parking",
                    needs_review=False,
                    categorised_at="2026-07-27T00:00:00+00:00",
                )
            finally:
                repo.close()

            with patch.object(retroactive_categorise, "AFFECTED_RECEIPTS", ["r-existing"]):
                retroactive_categorise.main()

            payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["category_code"], "999")
            self.assertEqual(payload["category_name"], "Sundry expenses")
            self.assertEqual(payload["category"], "Sundry expenses")
            self.assertEqual(payload["confidence"], "medium")


if __name__ == "__main__":
    unittest.main()

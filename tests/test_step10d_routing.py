"""Step 10d, end to end through a real poll: where an unresolved receipt goes.

Sub-steps 10d.16, 10d.18, 10d.40, 10d.53, 10d.55 and 10d.56. Driven through
app.process_once() rather than through the functions, because the thing being
asserted is a routing decision that spans the intake reader, the shared pipeline
and the filer, and a hand-rolled call sequence would only test the sequence I had
in mind.

The defect all of this exists to prevent: a receipt whose client cannot be worked
out used to be filed anyway, into a folder named from whatever the lookup fell
back to, with nothing on screen. Four receipts went into a TESTST folder on
2026-09-01 and nobody found out until somebody looked.
"""

import sys
import types
import unittest

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import json  # noqa: E402

import config  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    TempEnvironment,
    extraction_result,
    rows,
    run_pipeline_once,
)
from worker.database.repository import Repository  # noqa: E402

SIDECAR = {"client_id": "CLIENT001", "source": "phone"}


def drop(env, name="rcpt_1.png", sidecar=SIDECAR, folder="CLIENT001"):
    inbox = env.inbox_dir(folder)
    original = inbox / name
    original.write_text("dummy image bytes", encoding="utf-8")
    if sidecar is not None:
        original.with_suffix(".json").write_text(json.dumps(sidecar), encoding="utf-8")
    return original


def receipts():
    repo = Repository()
    try:
        return rows(repo, "SELECT * FROM receipts")
    finally:
        repo.close()


def statements():
    repo = Repository()
    try:
        return rows(repo, "SELECT * FROM statements")
    finally:
        repo.close()


class UnresolvedClientRoutingTest(unittest.TestCase):
    """10d.16 and 10d.18, and this is the only part of step 10d that reports."""

    def test_a_file_with_no_sidecar_is_a_review_item_and_never_ok(self):
        with TempEnvironment() as env:
            drop(env, sidecar=None)

            # A clean extraction. Under the old code this would have been `ok`
            # and filed, because validation says nothing about the client.
            run_pipeline_once(RecordingExtractor(extraction_result()))

            row = receipts()[0]
            self.assertEqual(row["status"], "needs_review")
            self.assertEqual(row["client_id"], config.UNKNOWN_CLIENT_ID)
            self.assertEqual(row["firm_id"], config.UNATTRIBUTED_FIRM_ID)
            self.assertEqual(row["source"], "other")
            self.assertIsNone(row["filed_path"], "nothing was filed into Clients")

    def test_it_lands_in_review_under_the_reserved_id(self):
        with TempEnvironment() as env:
            drop(env, sidecar=None)
            run_pipeline_once(RecordingExtractor(extraction_result()))

            review_dir = config.REVIEW_ROOT / config.UNKNOWN_CLIENT_ID
            self.assertTrue(review_dir.is_dir(), "the item has somewhere to be looked at")
            self.assertTrue(any(review_dir.iterdir()))

    def test_nothing_is_written_into_clients(self):
        with TempEnvironment() as env:
            drop(env, sidecar=None)
            run_pipeline_once(RecordingExtractor(extraction_result()))

            self.assertEqual(list(config.CLIENTS_ROOT.iterdir()), [],
                             "an unresolved client files nothing into Clients")

    def test_the_review_note_says_why(self):
        with TempEnvironment() as env:
            drop(env, sidecar=None)
            run_pipeline_once(RecordingExtractor(extraction_result()))

            sidecar = next((config.REVIEW_ROOT / config.UNKNOWN_CLIENT_ID)
                           .glob("*.review.json"))
            payload = json.loads(sidecar.read_text(encoding="utf-8"))
            self.assertIn("client could not be resolved", " ".join(payload["reasons"]))

    def test_a_sidecar_naming_a_client_the_registry_does_not_hold_is_the_same_case(self):
        with TempEnvironment() as env:
            drop(env, sidecar={"client_id": "Client_999", "source": "phone"})
            run_pipeline_once(RecordingExtractor(extraction_result()))

            row = receipts()[0]
            self.assertEqual(row["client_id"], config.UNKNOWN_CLIENT_ID)
            self.assertEqual(row["status"], "needs_review")

    def test_the_file_is_kept_and_reported_never_refused(self):
        # 10d.11. The file is somebody's receipt whatever the pipeline can work
        # out about it, so it produces a row and a Review pair rather than being
        # skipped.
        with TempEnvironment() as env:
            drop(env, sidecar=None)
            run_pipeline_once(RecordingExtractor(extraction_result()))
            self.assertEqual(len(receipts()), 1)


class ResolvedClientStillFilesTest(unittest.TestCase):
    """The other side of the gate: a resolved client is unaffected."""

    def test_a_resolved_receipt_is_ok_and_filed_under_the_folder_name(self):
        with TempEnvironment() as env:
            drop(env)
            run_pipeline_once(RecordingExtractor(extraction_result()))

            row = receipts()[0]
            self.assertEqual(row["status"], "ok")
            self.assertEqual(row["client_id"], "CLIENT001")
            self.assertIsNotNone(row["filed_path"])
            self.assertIn("Test Client", row["filed_path"],
                          "filed under client_folder_name, not under the id")

    def test_the_document_store_copy_is_keyed_on_the_client_id(self):
        # 10d.53. Two different keys for two different jobs, deliberately: the
        # document store is the archive of record and is keyed on the id, the
        # client folder is the firm's filing and is keyed on the folder name.
        with TempEnvironment() as env:
            drop(env)
            run_pipeline_once(RecordingExtractor(extraction_result()))

            row = receipts()[0]
            self.assertIn("CLIENT001", row["file_path"])
            self.assertTrue((config.FILES_DIR / "CLIENT001").is_dir())

    def test_the_source_word_survives_into_the_row_and_the_sidecar(self):
        # 10d.40. `capture` in the database and `folder` in the sidecar, for one
        # receipt, is what this replaces.
        with TempEnvironment() as env:
            drop(env, sidecar={"client_id": "CLIENT001", "source": "desktop"})
            run_pipeline_once(RecordingExtractor(extraction_result()))

            row = receipts()[0]
            self.assertEqual(row["source"], "desktop")

            filed_sidecar = next(config.CLIENTS_ROOT.rglob("*.json"))
            payload = json.loads(filed_sidecar.read_text(encoding="utf-8"))
            self.assertEqual(payload["source"], "desktop")

    def test_the_arrival_timestamp_is_written_as_iso_utc(self):
        # 10d.27 at the call site, not in the helper. This path used to pass
        # int(source_path.stat().st_mtime) straight into the same TEXT column the
        # email path fills with a date string, so the two could not be compared.
        with TempEnvironment() as env:
            drop(env)
            run_pipeline_once(RecordingExtractor(extraction_result()))

            from datetime import datetime

            stamp = receipts()[0]["email_received_at"]
            self.assertIsInstance(stamp, str)
            parsed = datetime.fromisoformat(stamp)
            self.assertIsNotNone(parsed.tzinfo, "ISO 8601 UTC, with the offset stated")
            self.assertEqual(parsed.utcoffset().total_seconds(), 0)

    def test_the_filed_sidecar_carries_client_id_and_no_code(self):
        # parseSidecar() in IntelliBooks-Desktop-v3.html reads data.client_id and
        # no longer reads any code, so this is the contract with the other half.
        with TempEnvironment() as env:
            drop(env)
            run_pipeline_once(RecordingExtractor(extraction_result()))

            filed_sidecar = next(config.CLIENTS_ROOT.rglob("*.json"))
            payload = json.loads(filed_sidecar.read_text(encoding="utf-8"))
            self.assertEqual(payload["client_id"], "CLIENT001")
            self.assertNotIn("client_code", payload)
            self.assertNotIn("claimed_client_code", payload)


class StatementCopyTest(unittest.TestCase):
    """10d.55 and 10d.56, Paul's decisions of 2026-09-02.

    Until now the statement branch never called into worker/storage/store.py at
    all, so the copy in the client folder was the only copy: a receipt could be
    reconstructed from the document store and a statement could not.
    """

    def _drop_statement(self, env, client_id="CLIENT001"):
        return drop(env, name="stmt_uber.pdf", sidecar={
            "client_id": client_id, "source": "desktop", "type": "statement",
            "platform": "Uber", "week_ending": "2026-04-05",
        })

    def test_a_statement_gets_a_document_store_copy_before_it_is_filed(self):
        with TempEnvironment() as env:
            self._drop_statement(env)
            run_pipeline_once(RecordingExtractor(extraction_result()))

            row = statements()[0]
            self.assertTrue((config.FILES_DIR / "CLIENT001").is_dir())
            self.assertIn("CLIENT001", row["file_path"])
            self.assertTrue(config.FILES_DIR.joinpath().exists())

    def test_file_path_and_filed_path_mean_the_same_as_on_receipts(self):
        with TempEnvironment() as env:
            self._drop_statement(env)
            run_pipeline_once(RecordingExtractor(extraction_result()))

            row = statements()[0]
            self.assertTrue(row["file_path"].startswith(str(config.FILES_DIR)),
                            "file_path is the document store copy")
            self.assertTrue(row["filed_path"].startswith(str(config.CLIENTS_ROOT)),
                            "filed_path is the client folder copy")
            self.assertNotEqual(row["file_path"], row["filed_path"])
            # app.py:361 is why it matters: it takes file_path as the file to copy
            # FROM when filing, and the same line written against a statement
            # would have copied the filed copy onto itself.
            self.assertNotIn("client_code", row)

    def test_both_copies_exist_on_disk(self):
        with TempEnvironment() as env:
            self._drop_statement(env)
            run_pipeline_once(RecordingExtractor(extraction_result()))

            from pathlib import Path

            row = statements()[0]
            self.assertTrue(Path(row["file_path"]).exists())
            self.assertTrue(Path(row["filed_path"]).exists())

    def test_a_statement_with_no_resolvable_client_goes_to_review(self):
        with TempEnvironment() as env:
            self._drop_statement(env, client_id="Client_999")
            run_pipeline_once(RecordingExtractor(extraction_result()))

            self.assertEqual(statements(), [], "nothing was filed")
            review_dir = config.REVIEW_ROOT / config.UNKNOWN_CLIENT_ID
            self.assertTrue(review_dir.is_dir())
            self.assertTrue(any(review_dir.iterdir()))


if __name__ == "__main__":
    unittest.main()

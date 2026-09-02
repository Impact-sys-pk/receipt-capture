"""scan_inbox() reads the client out of the sidecar, never out of the folder name.

Sub-steps 10d.11, 10d.19 and 10d.40. The folder under Receipt Inbox used to be
the client code, resolved through CLIENTS_BY_CODE with a silent fallback, so a
folder named after a client the registry did not hold produced an intake record
attributed to nobody and filed anyway. The folder name is now decoration and
nothing reads it.
"""

import json
import tempfile
import unittest
from pathlib import Path

import config
from worker.intake.folder_reader import scan_inbox

REGISTRY = {
    "CLIENT001": {
        "client_id": "CLIENT001",
        "client_name": "Test Client",
        "client_folder_name": "Test Client",
        "firm_id": "FIRM001",
        "trade": "UNSPECIFIED",
    }
}


class FolderReaderTest(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self._temp.cleanup)
        self.addCleanup(setattr, config, "RECEIPT_INBOX_ROOT", config.RECEIPT_INBOX_ROOT)
        self.addCleanup(setattr, config, "CLIENTS_BY_ID", config.CLIENTS_BY_ID)

        self.inbox = Path(self._temp.name) / "Receipt Inbox"
        # Deliberately named neither after the client_id nor after anything in the
        # registry: nothing may read it.
        self.client_folder = self.inbox / "whatever the operator called it"
        self.client_folder.mkdir(parents=True)
        config.RECEIPT_INBOX_ROOT = self.inbox
        config.CLIENTS_BY_ID = dict(REGISTRY)

    def _write(self, name="rcpt_123.pdf", sidecar=None):
        path = self.client_folder / name
        path.write_text("dummy pdf content", encoding="utf-8")
        if sidecar is not None:
            path.with_suffix(".json").write_text(json.dumps(sidecar), encoding="utf-8")
        return path

    def test_a_file_with_no_sidecar_is_kept_and_has_no_client(self):
        # 10d.11: kept and reported, never refused. It gets source = other and
        # goes to Review, per 10d.16 and 10d.18.
        self._write()

        records = scan_inbox()

        self.assertEqual(len(records), 1)
        intake = records[0]
        self.assertIsNone(intake.client_id)
        self.assertIsNone(intake.firm_id)
        self.assertEqual(intake.source, "other")
        self.assertEqual(intake.filename, "rcpt_123.pdf")
        self.assertFalse(intake.is_statement)
        self.assertIsNone(intake.sidecar)
        self.assertIsNone(intake.sidecar_path)

    def test_the_client_comes_out_of_the_sidecar(self):
        self._write(sidecar={"client_id": "CLIENT001", "source": "phone"})

        intake = scan_inbox()[0]

        self.assertEqual(intake.client_id, "CLIENT001")
        self.assertEqual(intake.firm_id, "FIRM001", "the firm comes off the client record")
        self.assertEqual(intake.source, "phone")

    def test_the_folder_name_is_not_read(self):
        # The proof that 10d.11 landed: the folder is named after a client that
        # is in the registry, and the sidecar names a different one that is not.
        # The old code would have resolved the folder; this must resolve neither.
        renamed = self.inbox / "CLIENT001"
        self.client_folder.rename(renamed)
        self.client_folder = renamed
        self._write(sidecar={"client_id": "NOT_IN_THE_REGISTRY", "source": "desktop"})

        intake = scan_inbox()[0]

        self.assertIsNone(intake.client_id)
        self.assertIsNone(intake.firm_id)

    def test_a_sidecar_with_no_client_id_resolves_to_nobody(self):
        self._write(sidecar={"source": "desktop", "added_by": "desktop"})

        intake = scan_inbox()[0]

        self.assertIsNone(intake.client_id)
        self.assertEqual(intake.source, "desktop", "the source is still what the writer declared")

    def test_source_has_four_values_and_no_others(self):
        # 10d.40. `capture` was a fifth and was hardcoded here.
        for declared, expected in (
            ("email", "email"),
            ("phone", "phone"),
            ("desktop", "desktop"),
            ("other", "other"),
            ("capture", "other"),
            ("folder", "other"),
            (None, "other"),
        ):
            with self.subTest(declared=declared):
                for existing in self.client_folder.iterdir():
                    existing.unlink()
                sidecar = {"client_id": "CLIENT001"}
                if declared is not None:
                    sidecar["source"] = declared
                self._write(sidecar=sidecar)
                self.assertEqual(scan_inbox()[0].source, expected)

    def test_a_statement_sidecar_still_carries_its_metadata(self):
        self._write(name="stmt_001.pdf", sidecar={
            "client_id": "CLIENT001", "source": "desktop", "type": "statement",
            "platform": "Uber", "week_ending": "2026-04-05",
        })

        intake = scan_inbox()[0]

        self.assertTrue(intake.is_statement)
        self.assertEqual(intake.statement_metadata["platform"], "Uber")
        self.assertEqual(intake.statement_metadata["week_ending"], "2026-04-05")
        self.assertEqual(intake.client_id, "CLIENT001")


if __name__ == "__main__":
    unittest.main()

"""Step 10d, the pipeline half: one client registry, keyed on client_id.

The sub-steps here had no cover of their own, either because the behaviour is
new (10d.35's re-read, 10d.55's statement copy) or because the old cover asserted
the thing being removed (the client code as a folder key).

What each class is for is stated on it. The theme running through all of them is
the same defect: a lookup that missed returned something plausible instead of
nothing, so a receipt was filed somewhere IntelliBooks does not look and nobody
was told. On 2026-09-01 that put four receipts in a TESTST folder.
"""

import json
import sqlite3
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

import app  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.email import alerts  # noqa: E402
from worker.filing import _review_dir_for_client_id  # noqa: E402
from worker.storage.store import save_file, save_inbox_file  # noqa: E402

ALERTS_PY = Path(__file__).resolve().parent.parent / "worker" / "email" / "alerts.py"

CLIENT = {
    "client_id": "Client_004",
    "client_name": "Test Sole Trader",
    "client_folder_name": "Test Sole Trader",
    "firm_id": "FIRM001",
    "trade": "UNSPECIFIED",
    "emails": ["st@example.invalid"],
}


def write_registry(path, records, firm_records=None):
    path.write_text(
        json.dumps({"version": 1, "clients": records}, indent=2), encoding="utf-8"
    )


class RegistryRereadTest(unittest.TestCase):
    """10d.35. The registry is re-read while the pipeline runs.

    config read clients.json once at import and main() polls until the process
    ends, so a client registered mid-run was invisible until a restart. The two
    conditions the sub-step names are the last two tests here, and they are the
    ones that matter: a failed parse must keep what is in memory, and it must
    never end the poll.
    """

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self._temp.cleanup)
        self.addCleanup(setattr, config, "CLIENTS_JSON", config.CLIENTS_JSON)
        self.addCleanup(setattr, config, "CLIENTS", config.CLIENTS)
        self.addCleanup(setattr, config, "CLIENTS_BY_ID", config.CLIENTS_BY_ID)
        self.addCleanup(setattr, config, "_CLIENTS_MTIME", config._CLIENTS_MTIME)

        self.path = Path(self._temp.name) / "clients.json"
        write_registry(self.path, [CLIENT])
        config.CLIENTS_JSON = self.path
        config.CLIENTS, config.CLIENTS_BY_ID = config.load_clients()
        config._CLIENTS_MTIME = config._registry_mtime()

    def _touch_with_a_new_mtime(self, records):
        write_registry(self.path, records)
        # A same-second write can land on the same mtime on some filesystems, so
        # the stamp is moved explicitly rather than relied on. Testing the
        # mechanism, not the clock resolution.
        stamp = self.path.stat().st_mtime + 10
        import os

        os.utime(self.path, (stamp, stamp))

    def test_nothing_changed_means_no_reload(self):
        self.assertFalse(config.reload_clients_if_changed())

    def test_a_client_added_mid_run_becomes_visible(self):
        second = dict(CLIENT, client_id="Client_005", client_name="Test Partnership",
                      client_folder_name="Test Partnership", emails=["p@example.invalid"])
        self._touch_with_a_new_mtime([CLIENT, second])

        self.assertTrue(config.reload_clients_if_changed())
        self.assertEqual(sorted(config.CLIENTS_BY_ID), ["Client_004", "Client_005"])
        self.assertIn("p@example.invalid", config.CLIENTS)

    def test_a_broken_file_keeps_the_registry_and_does_not_raise(self):
        self.path.write_text("{ this is not json", encoding="utf-8")
        stamp = self.path.stat().st_mtime + 10
        import os

        os.utime(self.path, (stamp, stamp))

        self.assertFalse(config.reload_clients_if_changed(), "nothing was replaced")
        self.assertEqual(sorted(config.CLIENTS_BY_ID), ["Client_004"],
                         "the registry already in memory survives a failed parse")

    def test_a_broken_file_is_tried_again_on_the_next_poll(self):
        # The remembered mtime must NOT move on a failure, or a file that was
        # half written when it was read would never be read again.
        self.path.write_text("{ this is not json", encoding="utf-8")
        import os

        stamp = self.path.stat().st_mtime + 10
        os.utime(self.path, (stamp, stamp))
        config.reload_clients_if_changed()

        write_registry(self.path, [CLIENT])
        os.utime(self.path, (stamp, stamp))  # the same mtime as the broken write

        self.assertTrue(config.reload_clients_if_changed(),
                        "the failed read did not move the remembered mtime, so this retries")


class DocumentStoreKeyTest(unittest.TestCase):
    """10d.53. Intellibills\\Documents\\ is keyed on client_id, not on a code."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self._temp.cleanup)
        self.addCleanup(setattr, config, "FILES_DIR", config.FILES_DIR)
        self.addCleanup(setattr, config, "CLIENTS_BY_ID", config.CLIENTS_BY_ID)
        config.FILES_DIR = Path(self._temp.name) / "Documents"
        # The client_name and the client_folder_name are deliberately different
        # from the client_id here. Without that, keying this store on either of
        # them would produce the same path and the assertions below would hold
        # for the wrong reason.
        config.CLIENTS_BY_ID = {"Client_004": dict(CLIENT)}

    def test_save_file_writes_under_the_client_id(self):
        dest = save_file("r-1", "Client_004", "invoice.pdf", b"bytes")
        self.assertEqual(dest.parent.parent.parent.name, "Client_004")
        self.assertEqual(dest.name, "r-1_invoice.pdf")

    def test_the_year_and_month_are_the_arrival_date(self):
        # Deliberately asserted. The save happens before extraction, so there is
        # no invoice date to file by, and an arrival date never needs correcting
        # where an invoice date does, so no file here ever has to move.
        now = datetime.now(timezone.utc)
        dest = save_file("r-1", "Client_004", "invoice.pdf", b"bytes")
        self.assertEqual(dest.parent.name, f"{now.month:02d}")
        self.assertEqual(dest.parent.parent.name, str(now.year))

    def test_the_client_name_is_not_the_key(self):
        # 10d.53 and the reason for it. client_name is display only and freely
        # editable, so a store keyed on it loses the file the moment somebody
        # corrects a spelling. client_folder_name is fixed once a folder exists
        # but is still the firm's filing name, not an identifier.
        dest = save_file("r-1", "Client_004", "invoice.pdf", b"bytes")
        parts = set(dest.parts)
        self.assertNotIn("Test Sole Trader", parts)

    def test_save_inbox_file_uses_the_same_key(self):
        source = Path(self._temp.name) / "in.pdf"
        source.write_bytes(b"bytes")
        dest = save_inbox_file("r-2", "Client_004", source)
        self.assertEqual(dest.parent.parent.parent.name, "Client_004")
        self.assertNotIn("Test Sole Trader", set(dest.parts))


class ReviewFolderKeyTest(unittest.TestCase):
    """10d.54. Intellibills\\Review\\ is keyed on client_id.

    scanReview() in IntelliBooks-Desktop-v3.html is the reader and it fails
    silently, so a mismatch here shows up as an empty Review list rather than as
    an error. That is the 2026-09-01 TESTST failure exactly.
    """

    def test_the_folder_is_named_by_the_client_id(self):
        self.assertEqual(_review_dir_for_client_id("Client_004"),
                         config.REVIEW_ROOT / "Client_004")

    def test_the_case_is_not_folded(self):
        # Client_004 is not CLIENT_004. NTFS would forgive it and S3 would not.
        self.assertEqual(_review_dir_for_client_id("Client_004").name, "Client_004")


class SaveReceiptHasNoDefaultsTest(unittest.TestCase):
    """10d.17. Python supplied four values before the SQL was reached.

    Removing the column defaults in 10d.24 to 10d.26 without removing these
    would have changed nothing at all, which is why the sub-step names both.
    """

    def test_the_four_arguments_are_required(self):
        import inspect

        signature = inspect.signature(Repository.save_receipt)
        for name in ("firm_id", "client_id", "source"):
            with self.subTest(argument=name):
                self.assertIs(
                    signature.parameters[name].default, inspect.Parameter.empty,
                    f"{name} has a default again, so a caller can omit it and the "
                    "row records a value nobody wrote",
                )
        self.assertNotIn("client_code", signature.parameters)


class SchemaShapeTest(unittest.TestCase):
    """10d.22 to 10d.34. One definition is the only definition.

    A fresh database from init_db(), read back with PRAGMA rather than from the
    source, so this describes the table rather than the CREATE statement.
    """

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self._temp.cleanup)
        self.addCleanup(setattr, config, "DB_PATH", config.DB_PATH)
        config.DB_PATH = Path(self._temp.name) / "receipts.db"
        from worker.database.schema import init_db

        init_db()
        self.conn = sqlite3.connect(config.DB_PATH)
        self.addCleanup(self.conn.close)

    def _columns(self, table):
        return {row[1]: row for row in self.conn.execute(f"PRAGMA table_info({table})")}

    def test_no_table_carries_a_client_code(self):
        tables = [r[0] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")]
        for table in tables:
            with self.subTest(table=table):
                self.assertNotIn("client_code", self._columns(table))

    def test_both_tables_carry_file_path_and_filed_path(self):
        # 10d.56. file_path is the document store copy and filed_path is the
        # client folder copy, on both. One column name meant the original on one
        # table and the copy on the other.
        for table in ("receipts", "statements"):
            with self.subTest(table=table):
                columns = self._columns(table)
                self.assertIn("file_path", columns)
                self.assertIn("filed_path", columns)

    def test_receipts_carries_no_defaults(self):
        # 10d.24 to 10d.26. dflt_value is column 4 of table_info.
        for name, row in self._columns("receipts").items():
            with self.subTest(column=name):
                self.assertIsNone(row[4], f"receipts.{name} has a default again")

    def test_firm_id_and_client_id_are_not_null(self):
        columns = self._columns("receipts")
        self.assertEqual(columns["firm_id"][3], 1)
        self.assertEqual(columns["client_id"][3], 1)

    def test_locked_at_is_text(self):
        self.assertEqual(self._columns("receipts")["locked_at"][2], "TEXT")

    def test_extractions_currency_has_no_default(self):
        self.assertIsNone(self._columns("extractions")["currency"][4])

    def test_the_cautious_default_stays(self):
        # categorisations.needs_review is the only default in the schema pointing
        # the cautious way, and 10d records it as deliberate.
        self.assertEqual(self._columns("categorisations")["needs_review"][4], "1")

    def test_the_categorisation_trade_column_is_named_trade(self):
        columns = self._columns("categorisations")
        self.assertIn("trade", columns)
        self.assertNotIn("business_type", columns)

    def test_processed_attachments_gained_a_firm_and_kept_its_key(self):
        self.assertIn("firm_id", self._columns("processed_attachments"))
        key = [r[1] for r in self.conn.execute("PRAGMA table_info(processed_attachments)")
               if r[5]]
        self.assertEqual(key, ["message_id", "attachment_id"])

    def test_firm_vendors_gained_a_nullable_firm_and_kept_its_unique_key(self):
        columns = self._columns("categorisations_firm_vendors")
        self.assertIn("firm_id", columns)
        self.assertEqual(columns["firm_id"][3], 0, "nullable, so the pool stays shared")
        sql = self.conn.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'categorisations_firm_vendors'"
        ).fetchone()[0]
        self.assertIn("UNIQUE(business_type, vendor_code, vendor_name)", sql)
        self.assertNotIn("UNIQUE(business_type, vendor_code, vendor_name, firm_id)", sql)

    def test_no_migration_survives(self):
        # 10d.34. Eleven ALTER TABLE ADD COLUMN guards, all removed, and the
        # columns they added are now in the CREATE statements.
        source = (Path(__file__).resolve().parent.parent / "worker" / "database"
                  / "schema.py").read_text(encoding="utf-8")
        self.assertNotIn("ALTER TABLE", source)
        for column in ("filed_at", "duplicate_of", "locked_at", "source"):
            with self.subTest(column=column):
                self.assertIn(column, self._columns("receipts"))
        for column in ("pipeline_version", "receipt_ref_number", "receipt_time", "details"):
            with self.subTest(column=column):
                self.assertIn(column, self._columns("extractions"))
        self.assertIn("reason", self._columns("resolution_events"))


class ArrivalTimestampTest(unittest.TestCase):
    """10d.27. One format for receipts.email_received_at: ISO 8601 UTC.

    It used to take an integer mtime on one path and an RFC-shaped string on the
    other, into the same TEXT column, so the two could not be compared or sorted
    against each other.
    """

    def test_an_epoch_becomes_iso_utc(self):
        self.assertEqual(app._iso_utc(0), "1970-01-01T00:00:00+00:00")

    def test_an_rfc_email_date_becomes_iso_utc(self):
        self.assertEqual(
            app._iso_utc("Tue, 01 Apr 2026 09:30:00 +0100"),
            "2026-04-01T08:30:00+00:00",
        )

    def test_an_iso_string_with_a_z_is_normalised(self):
        self.assertEqual(app._iso_utc("2026-04-01T09:30:00Z"), "2026-04-01T09:30:00+00:00")

    def test_a_naive_iso_string_is_read_as_utc(self):
        self.assertEqual(app._iso_utc("2026-04-01T09:30:00"), "2026-04-01T09:30:00+00:00")

    def test_something_unreadable_is_null_rather_than_a_guess(self):
        # A NULL says the arrival time is not known. A plausible wrong timestamp
        # does not, and this column is what an operator sorts an intake list by.
        self.assertIsNone(app._iso_utc("last Tuesday"))
        self.assertIsNone(app._iso_utc(""))
        self.assertIsNone(app._iso_utc(None))


class UnknownSenderAlertTest(unittest.TestCase):
    """10d.36. The only automatic email that reaches a non-client.

    Row F7 records it as a wall: a literal in source cannot vary by firm, and
    this one named Lasting Impact twice and gave a Lasting Impact support
    address, to somebody who had written to a different firm's mailbox.
    """

    def test_the_source_carries_none_of_the_three_literals(self):
        source = ALERTS_PY.read_text(encoding="utf-8")
        body = source[source.index("def send_unknown_sender_alert"):]
        # The docstring names them to say they are gone, so the check is on the
        # code below it rather than on the whole function.
        code = body[body.index('"""', body.index('"""') + 3):]
        for literal in ("support@lastingimpact.co.uk", "Lasting Impact"):
            with self.subTest(literal=literal):
                self.assertNotIn(literal, code)

    def test_the_firm_name_reaches_the_message(self):
        sent = {}

        class FakeSMTP:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def login(self, *args):
                pass

            def send_message(self, msg):
                sent["from"] = msg["From"]
                sent["body"] = msg.get_payload()[0].get_payload()

        with patch.object(alerts.smtplib, "SMTP_SSL", FakeSMTP):
            self.assertTrue(alerts.send_unknown_sender_alert("x@example.invalid", "Best Accounting"))

        self.assertIn("Best Accounting", sent["from"])
        self.assertIn("Best Accounting", sent["body"])
        self.assertNotIn("Lasting Impact", sent["body"])

    def test_no_firm_name_names_nobody_rather_than_the_wrong_firm(self):
        sent = {}

        class FakeSMTP:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def login(self, *args):
                pass

            def send_message(self, msg):
                sent["from"] = msg["From"]
                sent["body"] = msg.get_payload()[0].get_payload()

        with patch.object(alerts.smtplib, "SMTP_SSL", FakeSMTP):
            alerts.send_unknown_sender_alert("x@example.invalid")

        self.assertIn("Receipt Capture System", sent["from"])
        self.assertNotIn("Lasting Impact", sent["body"])


class MailboxFirmTest(unittest.TestCase):
    """10d.36's other half: which firm an unknown sender's alert names.

    There is no client to take a firm from, so it is the firm that owns the
    mailbox. One pipeline instance polls one mailbox.
    """

    def setUp(self):
        self.addCleanup(setattr, config, "FIRMS", config.FIRMS)

    def test_one_firm_is_the_answer(self):
        config.FIRMS = {"FIRM001": {"firm_id": "FIRM001", "name": "Intellitax"}}
        self.assertEqual(app._mailbox_firm_name(), "Intellitax")

    def test_two_firms_name_nobody_rather_than_the_first(self):
        config.FIRMS = {
            "FIRM001": {"firm_id": "FIRM001", "name": "Intellitax"},
            "FIRM002": {"firm_id": "FIRM002", "name": "Best Accounting"},
        }
        self.assertEqual(app._mailbox_firm_name(), "")

    def test_no_firms_names_nobody(self):
        config.FIRMS = {}
        self.assertEqual(app._mailbox_firm_name(), "")


class ClientFolderResolutionTest(unittest.TestCase):
    """10d.13 and 10d.18. A lookup that misses returns nothing, not a guess."""

    def setUp(self):
        self.addCleanup(setattr, config, "CLIENTS_BY_ID", config.CLIENTS_BY_ID)
        config.CLIENTS_BY_ID = {"Client_004": dict(CLIENT)}

    def test_a_resolved_client_names_its_folder(self):
        self.assertEqual(app._client_folder_name("Client_004"), "Test Sole Trader")

    def test_an_unresolved_client_names_nothing(self):
        # THE 2026-09-01 DEFECT. This used to return the client code, so a
        # receipt was filed into Clients\TESTST\ while IntelliBooks looked under
        # Clients\Test Sole Trader\ and found nothing, with no message on screen.
        self.assertIsNone(app._client_folder_name("Client_999"))

    def test_unknown_names_nothing(self):
        self.assertIsNone(app._client_folder_name(config.UNKNOWN_CLIENT_ID))

    def test_a_record_with_an_empty_folder_name_names_nothing(self):
        config.CLIENTS_BY_ID = {"Client_004": dict(CLIENT, client_folder_name="")}
        self.assertIsNone(app._client_folder_name("Client_004"))

    def test_the_review_key_falls_back_to_unknown_and_not_to_an_empty_path(self):
        # An item with no client still needs somewhere to go, per 10d.18, and an
        # empty string would make Review\ itself the folder.
        self.assertEqual(app._review_key(None), config.UNKNOWN_CLIENT_ID)
        self.assertEqual(app._review_key("Client_004"), "Client_004")


if __name__ == "__main__":
    unittest.main()

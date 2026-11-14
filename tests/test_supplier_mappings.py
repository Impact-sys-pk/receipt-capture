r"""Each client's taught supplier mappings, published. Sub-step 10bs.10, pipeline half.

Amendment 554 of `2026-07-25_CONSOLE_DESIGN.md`, brief
`PROMPT_claude_code_2026-11-13_published_mappings.md`.

**Why.** Sub-step 10bs.9 made layer 1 match on the supplier name first and fall
back to the key only where every name on the key agrees on the code. So when the
operator ticks Remember, they need to see which other names the key already
holds and what codes those carry. The mappings are in `receipts.db`, which
IntelliBooks Desktop never reads. Paul's decision, option A: the pipeline
publishes them.

**Where.** `Intellibills\Supplier Mappings\{client_id}-mappings.json`, reached
by Desktop through its one practice-root grant as
`getDir(["Intellibills", "Supplier Mappings"])`.

**The vocabulary is `config.py`'s.** Every key in the file is a named constant
there, and `TheKeysAreTheConstantsTest` pins both the values and that the file
carries exactly those keys, so the Desktop reader can be written against the
names rather than against an example.

**Empty and missing are different states.** A registered client with no
mappings gets a file with an empty list. A missing file means the pipeline has
not published for that client.
"""

import ast
import json
import logging
import unittest
from pathlib import Path
from unittest import mock

import config

from resolution_fixtures import TempEnvironment, rows
from worker import supplier_mappings
from worker.database.repository import Repository

CLIENT = "CLIENT001"
OTHER = "CLIENT002"
WHEN = "2026-11-13T12:00:00+00:00"


def path_for(client_id):
    return config.SUPPLIER_MAPPINGS_DIR / f"{client_id}{config.SUPPLIER_MAPPINGS_SUFFIX}"


def read(client_id):
    return json.loads(path_for(client_id).read_text(encoding="utf-8"))


class _Base(unittest.TestCase):
    def setUp(self):
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.repo = Repository()
        self.addCleanup(self.repo.close)

    def teach(self, name, key, code, name_of_code, client_id=CLIENT, when=WHEN):
        self.repo.upsert_client_vendor(
            client_id=client_id, vendor_key=key, nominal_code=code,
            account_name=name_of_code, last_updated=when, vendor_name=name)

    def publish(self):
        return supplier_mappings.publish_all(self.repo)


class TheKeysAreTheConstantsTest(unittest.TestCase):
    """The shared vocabulary, pinned by value so the Desktop reader can rely on it."""

    def test_the_constants_and_their_values(self):
        self.assertEqual(
            {
                "SUPPLIER_MAPPINGS_SUFFIX": config.SUPPLIER_MAPPINGS_SUFFIX,
                "SUPPLIER_MAPPINGS_SCHEMA": config.SUPPLIER_MAPPINGS_SCHEMA,
                "MAPPINGS_SCHEMA_FIELD": config.MAPPINGS_SCHEMA_FIELD,
                "MAPPINGS_CLIENT_ID_FIELD": config.MAPPINGS_CLIENT_ID_FIELD,
                "MAPPINGS_LIST_FIELD": config.MAPPINGS_LIST_FIELD,
                "MAPPING_VENDOR_KEY_FIELD": config.MAPPING_VENDOR_KEY_FIELD,
                "MAPPING_VENDOR_NAME_FIELD": config.MAPPING_VENDOR_NAME_FIELD,
                "MAPPING_NOMINAL_CODE_FIELD": config.MAPPING_NOMINAL_CODE_FIELD,
                "MAPPING_ACCOUNT_NAME_FIELD": config.MAPPING_ACCOUNT_NAME_FIELD,
                "MAPPING_TIMES_SEEN_FIELD": config.MAPPING_TIMES_SEEN_FIELD,
                "MAPPING_LAST_UPDATED_FIELD": config.MAPPING_LAST_UPDATED_FIELD,
                "MAPPING_ID_FIELD": config.MAPPING_ID_FIELD,
            },
            {
                "SUPPLIER_MAPPINGS_SUFFIX": "-mappings.json",
                "SUPPLIER_MAPPINGS_SCHEMA": 1,
                "MAPPINGS_SCHEMA_FIELD": "schema",
                "MAPPINGS_CLIENT_ID_FIELD": "client_id",
                "MAPPINGS_LIST_FIELD": "mappings",
                "MAPPING_VENDOR_KEY_FIELD": "vendor_key",
                "MAPPING_VENDOR_NAME_FIELD": "vendor_name",
                "MAPPING_NOMINAL_CODE_FIELD": "nominal_code",
                "MAPPING_ACCOUNT_NAME_FIELD": "account_name",
                "MAPPING_TIMES_SEEN_FIELD": "times_seen",
                "MAPPING_LAST_UPDATED_FIELD": "last_updated",
                "MAPPING_ID_FIELD": "mapping_id",
            })

    def test_the_folder_is_under_intellibills_and_named(self):
        self.assertEqual(config.SUPPLIER_MAPPINGS_DIR.name, "Supplier Mappings")
        self.assertEqual(config.SUPPLIER_MAPPINGS_DIR.parent, config.INTELLIBILLS_ROOT)


class WhatIsPublishedTest(_Base):

    def test_one_file_per_registered_client_with_every_field(self):
        self.teach("Shell Co-op Harborne", "shell", "7301", "Fuel and oil")
        self.publish()
        payload = read(CLIENT)
        self.assertEqual(set(payload), {config.MAPPINGS_SCHEMA_FIELD,
                                        config.MAPPINGS_CLIENT_ID_FIELD,
                                        config.MAPPINGS_LIST_FIELD})
        self.assertEqual(payload[config.MAPPINGS_SCHEMA_FIELD], config.SUPPLIER_MAPPINGS_SCHEMA)
        self.assertEqual(payload[config.MAPPINGS_CLIENT_ID_FIELD], CLIENT)
        mapping_id = rows(self.repo, "SELECT mapping_id FROM "
                                     "categorisations_client_vendors")[0]["mapping_id"]
        self.assertEqual(payload[config.MAPPINGS_LIST_FIELD], [{
            # Flag F2 of step 10bu, 2026-11-14: the row's id, so Desktop can
            # name one row to change or delete.
            config.MAPPING_ID_FIELD: mapping_id,
            config.MAPPING_VENDOR_KEY_FIELD: "shell",
            config.MAPPING_VENDOR_NAME_FIELD: "Shell Co-op Harborne",
            config.MAPPING_NOMINAL_CODE_FIELD: "7301",
            config.MAPPING_ACCOUNT_NAME_FIELD: "Fuel and oil",
            config.MAPPING_TIMES_SEEN_FIELD: 1,
            config.MAPPING_LAST_UPDATED_FIELD: WHEN,
        }])

    def test_a_client_with_no_mappings_gets_an_empty_list_not_no_file(self):
        self.publish()
        self.assertTrue(path_for(CLIENT).exists())
        self.assertEqual(read(CLIENT)[config.MAPPINGS_LIST_FIELD], [])

    def test_only_this_clients_rows_and_only_registered_clients(self):
        self.teach("Shell Co-op Harborne", "shell", "7301", "Fuel and oil")
        self.teach("Shell Elsewhere", "shell", "7302", "EV charging", client_id=OTHER)
        self.publish()
        names = [m[config.MAPPING_VENDOR_NAME_FIELD]
                 for m in read(CLIENT)[config.MAPPINGS_LIST_FIELD]]
        self.assertEqual(names, ["Shell Co-op Harborne"])
        self.assertFalse(path_for(OTHER).exists(),
                         "CLIENT002 is not in the registry, so it is not published")
        self.assertFalse(path_for(config.UNKNOWN_CLIENT_ID).exists())

    def test_published_as_stored_with_no_normalising_and_in_a_fixed_order(self):
        self.teach("  shell co-op HARBORNE ", "shell", "7301", "Fuel and oil")
        self.teach("Shell Co-op Harborne", "shell", "7301", "Fuel and oil")
        self.teach("Apcoa Parking", "apcoa parking", "7304", "Parking and tolls")
        self.publish()
        published = [(m[config.MAPPING_VENDOR_KEY_FIELD], m[config.MAPPING_VENDOR_NAME_FIELD])
                     for m in read(CLIENT)[config.MAPPINGS_LIST_FIELD]]
        self.assertEqual(published, [
            ("apcoa parking", "Apcoa Parking"),
            ("shell", "  shell co-op HARBORNE "),
            ("shell", "Shell Co-op Harborne"),
        ])

    def test_publishing_teaches_nothing(self):
        self.teach("Shell Co-op Harborne", "shell", "7301", "Fuel and oil")
        before = rows(self.repo, "SELECT * FROM categorisations_client_vendors")
        self.publish()
        self.assertEqual(rows(self.repo, "SELECT * FROM categorisations_client_vendors"), before)


class WhenItIsWrittenTest(_Base):

    def writes(self):
        with mock.patch.object(supplier_mappings, "write_atomically",
                               wraps=supplier_mappings.write_atomically) as spy:
            self.publish()
        return spy.call_count

    def test_written_when_missing(self):
        self.assertEqual(self.writes(), 1)

    def test_not_rewritten_when_nothing_changed(self):
        self.publish()
        self.assertEqual(self.writes(), 0)

    def test_rewritten_after_a_teach(self):
        self.publish()
        self.teach("Shell Co-op Harborne", "shell", "7301", "Fuel and oil")
        self.assertEqual(self.writes(), 1)
        self.assertEqual(len(read(CLIENT)[config.MAPPINGS_LIST_FIELD]), 1)

    def test_rewritten_when_the_file_on_disk_is_out_of_date(self):
        self.teach("Shell Co-op Harborne", "shell", "7301", "Fuel and oil")
        self.publish()
        path_for(CLIENT).write_text('{"mappings": []}', encoding="utf-8")
        self.assertEqual(self.writes(), 1)
        self.assertEqual(len(read(CLIENT)[config.MAPPINGS_LIST_FIELD]), 1)

    def test_rewritten_when_the_file_on_disk_is_not_json(self):
        self.publish()
        path_for(CLIENT).write_text("not json", encoding="utf-8")
        self.assertEqual(self.writes(), 1)

    def test_a_failed_write_is_logged_and_does_not_raise(self):
        with mock.patch.object(supplier_mappings, "write_atomically",
                               side_effect=OSError("disk full")), \
                self.assertLogs("worker.supplier_mappings", level=logging.WARNING) as logs:
            self.publish()
        self.assertIn(CLIENT, "\n".join(logs.output))


class APollThatTeachesPublishesTest(_Base):
    """End to end: a real `process_once()` consumes a filed note with the
    Remember tick, and the same poll's file carries the mapping it taught."""

    def test_the_taught_mapping_is_in_the_file_after_the_poll(self):
        from chart_fixtures import TempChartBundle
        from resolution_fixtures import RecordingExtractor, run_pipeline_once

        chart = TempChartBundle(accounts=(("7304", "Parking and tolls"),)).__enter__()
        self.addCleanup(chart.__exit__, None, None, None)
        self.env.seed(self.repo, receipt_id="r-1")
        relative = r"Clients\Test Client\IntelliBooks\Receipts\2026-27\r-1.pdf"
        target = config.PRACTICE_ROOT / relative.replace("\\", "/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("the copy Desktop filed", encoding="utf-8")
        config.RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        (config.RESOLUTIONS_DIR / "r-1_1763042531000.json").write_text(json.dumps({
            "schema": 1, "receipt_id": "r-1", "client_id": CLIENT, "action": "filed",
            "resolved_by": "desktop", "resolved_at": "2026-11-13T14:02:11.000Z",
            "remember_gl_for_supplier": True, "filed_path": relative,
            "values": {"supplier_name": "Apcoa Parking", "invoice_date": "2026-04-01",
                       "net_amount": 10, "vat_amount": 2, "gross_amount": 12,
                       "currency": "GBP", "category_code": "7304",
                       "category_name": "Parking and tolls"},
        }), encoding="utf-8")
        self.assertFalse(path_for(CLIENT).exists())

        run_pipeline_once(RecordingExtractor(None))

        published = read(CLIENT)[config.MAPPINGS_LIST_FIELD]
        self.assertEqual(
            [(m[config.MAPPING_VENDOR_NAME_FIELD], m[config.MAPPING_NOMINAL_CODE_FIELD])
             for m in published],
            [("Apcoa Parking", "7304")])


class ThePollPublishesTest(unittest.TestCase):
    """The poll calls the publish after the resolution notes, which is where a
    poll teaches. Read off `process_once()`'s syntax tree."""

    def test_process_once_publishes_after_consuming_the_notes(self):
        source = Path(__file__).resolve().parent.parent / "app.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        process_once = next(n for n in tree.body
                            if isinstance(n, ast.FunctionDef) and n.name == "process_once")
        order = []
        for node in ast.walk(process_once):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
                # ~~Any `publish_all`~~: step 10bu added
                # `receipt_rules.publish_all()` beside this one, so the call is
                # matched on its module as well as its name, 2026-11-14.
                if name == "publish_all" and not (
                        isinstance(func, ast.Attribute)
                        and isinstance(func.value, ast.Name)
                        and func.value.id == "supplier_mappings"):
                    continue
                if name in ("_consume_resolution_notes", "publish_all"):
                    order.append((node.lineno, name))
        self.assertEqual([name for _, name in sorted(order)],
                         ["_consume_resolution_notes", "publish_all"])


if __name__ == "__main__":
    unittest.main()

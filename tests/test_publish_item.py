"""The published item: one JSON file per receipt, with the document inside it.

**Stage 1 piece 3, deliverable 3. Sub-steps 10f.6 and 10f.7.** Intellibills
writes one file per receipt into `IntelliBooks\\{publish folder}\\`, named
`{receipt_id}.json`. The payload is the enriched sidecar's own key set plus the
document's bytes base64-encoded and its media type, so IntelliBooks needs
nothing else from the file system to take the receipt in.

**Why the sidecar's key set exactly**, per amendment 283 and confirmed by 285:
`parseSidecar()` in `IntelliBooks-Desktop-v3.html` sets `out.id` from
`data.receipt_id` and `books.receipts` is keyed on it, so an item carrying the
same keys produces the same id as the same receipt arriving the old way, and
Desktop tells the two apart with the mechanism it already has. Giving the item
a new shape would have made two ids for one receipt.

**`make_enriched_sidecar()` is frozen by 18.2b**, so this file reads its key set
by calling it rather than by restating it. A list written out here would be a
second definition of the contract, and the two would drift.

**Why temp-then-rename.** Desktop drains the folder in stage 2 and will glob it.
A file appearing at its final name while it is still being written is readable
and incomplete, and a base64 document is large enough for that window to be
real. The temp name deliberately does not end in `.json`, so a reader globbing
`*.json` cannot see a partial one whatever it does.

**Why the media type is a table and not `mimetypes.guess_type()`.** On Windows
`mimetypes` reads the registry, so the answer depends on what is installed on
the machine, and two installations would publish the same receipt with two
different media types. The table is checked against `SUPPORTED_EXTENSIONS`
below rather than kept in step by hand.
"""

import base64
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from worker import publish
from worker.filing import make_enriched_sidecar
from worker.storage.store import SUPPORTED_EXTENSIONS

RECEIPT_ID = "11111111-2222-3333-4444-555555555555"


def sidecar():
    """A receipt's worth of sidecar, built the way the pipeline builds it.

    **A function and not a module constant, and the reason is a defect this
    file had.** It was a constant, and `test_the_sidecar_passed_in_is_not_
    modified` then compared the dict against a copy taken after earlier tests
    in the class had already been handed the same object. A mutation making
    `build_item()` write into its argument survived the whole suite because of
    it. One fresh dict per test, so no test can be answered by another one's
    leftovers.
    """
    return make_enriched_sidecar(
        receipt_id=RECEIPT_ID,
        source="email",
        client_id="CLIENT01",
        client_name="A Client Ltd",
        capture_date="2026-09-09T10:00:00+00:00",
        invoice_date="2026-09-01",
        supplier="Caffè Nerø",
        net=10.0,
        vat=2.0,
        gross=12.0,
        currency="GBP",
        category_code="7500",
        category_name="Motor expenses",
        confidence="high",
        validation_status="ok",
        asserted=None,
        original_filename="receipt.pdf",
        claimed_client_id=None,
    )

DOCUMENT_BYTES = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\nnot really a pdf\n\x00\xff"


class ItemShapeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        self.document = self.tmp / "receipt.pdf"
        self.document.write_bytes(DOCUMENT_BYTES)
        self.sidecar = sidecar()

    def test_the_item_carries_the_sidecar_key_set_and_two_more(self):
        """The contract with Desktop, read off `make_enriched_sidecar()` itself.

        Amendment 283 and the brief both say 19 keys. It returns 20. The count
        is not restated here for that reason: the set is asked for rather than
        remembered.
        """
        item = publish.build_item(self.sidecar, self.document)
        self.assertEqual(
            set(item),
            set(self.sidecar) | {publish.IMAGE_KEY, publish.MEDIA_TYPE_KEY},
        )

    def test_every_sidecar_value_survives_unchanged(self):
        original = dict(self.sidecar)
        item = publish.build_item(self.sidecar, self.document)
        for key, value in original.items():
            with self.subTest(key=key):
                self.assertEqual(item[key], value)

    def test_the_receipt_id_is_the_sidecars_own(self):
        # Amendment 285 turns on this: Desktop keys `books.receipts` on it, so
        # both routes must produce one id for one receipt.
        item = publish.build_item(self.sidecar, self.document)
        self.assertEqual(item["receipt_id"], RECEIPT_ID)

    def test_the_document_round_trips_byte_for_byte(self):
        item = publish.build_item(self.sidecar, self.document)
        self.assertEqual(base64.b64decode(item[publish.IMAGE_KEY]), DOCUMENT_BYTES)

    def test_the_encoded_document_is_plain_ascii(self):
        # It has to survive json.dumps and a JSON.parse the other side.
        item = publish.build_item(self.sidecar, self.document)
        self.assertIsInstance(item[publish.IMAGE_KEY], str)
        item[publish.IMAGE_KEY].encode("ascii")

    def test_the_media_type_comes_off_the_extension(self):
        item = publish.build_item(self.sidecar, self.document)
        self.assertEqual(item[publish.MEDIA_TYPE_KEY], "application/pdf")

    def test_the_sidecar_passed_in_is_not_modified(self):
        """It is the same dict the filing route writes into the client folder.

        Adding two keys to it in place would put the base64 document into that
        sidecar as well, roughly doubling what goes into OneDrive per receipt
        and changing a file 18.2b froze the shape of.

        **This test passed against a `build_item()` that did modify it**, until
        the sidecar stopped being a module-level constant shared with the rest
        of the class. See `sidecar()`.
        """
        before = dict(self.sidecar)
        publish.build_item(self.sidecar, self.document)
        self.assertEqual(self.sidecar, before)
        self.assertNotIn(publish.IMAGE_KEY, self.sidecar)


class MediaTypeTest(unittest.TestCase):
    def test_the_table_covers_exactly_what_the_pipeline_accepts(self):
        """A guard over the set, not over its members.

        `SUPPORTED_EXTENSIONS` is what `store.py` lets in, so anything it lets
        in reaches here, and anything it does not cannot. A per-extension test
        proves one type works; only this proves the set is complete. Note it
        holds `.tiff` and not `.tif`.
        """
        self.assertEqual(set(publish.MEDIA_TYPES), set(SUPPORTED_EXTENSIONS))

    def test_every_supported_extension_answers(self):
        for extension in sorted(SUPPORTED_EXTENSIONS):
            with self.subTest(extension=extension):
                answer = publish.media_type_for(f"receipt{extension}")
                self.assertTrue(answer)
                self.assertIn("/", answer)

    def test_the_extension_is_matched_case_insensitively(self):
        self.assertEqual(publish.media_type_for("RECEIPT.PDF"), "application/pdf")

    def test_an_unsupported_extension_raises_rather_than_guessing(self):
        # A wrong media type is worse than a refusal: Desktop would render it
        # and get a broken image with no explanation. The refusal becomes a
        # recorded publish failure and the receipt itself still stands.
        with self.assertRaises(publish.PublishError) as caught:
            publish.media_type_for("receipt.docx")
        self.assertIn(".docx", str(caught.exception))

    def test_no_extension_at_all_raises(self):
        with self.assertRaises(publish.PublishError):
            publish.media_type_for("receipt")


class WriteItemTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        self.destination = self.tmp / "Incoming"
        self.destination.mkdir()
        self.document = self.tmp / "receipt.pdf"
        self.document.write_bytes(DOCUMENT_BYTES)
        self.item = publish.build_item(sidecar(), self.document)

    def test_the_file_is_named_after_the_receipt(self):
        written = publish.write_item(self.destination, RECEIPT_ID, self.item)
        self.assertEqual(written.name, f"{RECEIPT_ID}.json")
        self.assertEqual(written.parent, self.destination)

    def test_the_folder_holds_that_file_and_nothing_else(self):
        publish.write_item(self.destination, RECEIPT_ID, self.item)
        self.assertEqual([p.name for p in self.destination.iterdir()],
                         [f"{RECEIPT_ID}.json"])

    def test_the_content_reloads_as_the_item(self):
        written = publish.write_item(self.destination, RECEIPT_ID, self.item)
        self.assertEqual(json.loads(written.read_text(encoding="utf-8")), self.item)

    def test_a_non_ascii_supplier_survives(self):
        written = publish.write_item(self.destination, RECEIPT_ID, self.item)
        reloaded = json.loads(written.read_text(encoding="utf-8"))
        self.assertEqual(reloaded["supplier"], "Caffè Nerø")

    def test_the_file_on_disk_is_pure_ascii(self):
        """The bytes, not the parsed value, and it is a deliberate constraint.

        A JSON reader cannot tell `ensure_ascii` on from off, so the round trip
        above passes either way and a mutation flipping it survived the whole
        suite. **The setting is pinned rather than left free**, because the
        file crosses to a product written by a session that cannot see this
        one: an ASCII file cannot be mangled by being read in the wrong
        encoding, and a supplier name coming out wrong is the kind of defect
        nobody reports.
        """
        written = publish.write_item(self.destination, RECEIPT_ID, self.item)
        written.read_bytes().decode("ascii")

    def test_the_temporary_name_is_not_visible_to_a_json_glob(self):
        """The property temp-then-rename exists for, checked on the name.

        Renaming into place is worth nothing if the temporary name is itself
        something a reader picks up, so the folder is globbed the way Desktop
        will glob it **at the moment the item is fully written and not yet
        renamed**, which is the widest the window ever gets.

        Written first as a listing taken after a forced failure, and that was
        wrong: `write_item()` removes its own part file, so the listing was
        empty and the test proved nothing. The control caught it. It now looks
        while the part file is still there.
        """
        seen = {}
        # Held before the patch. `publish.os` is the `os` module itself, so
        # patching the attribute patches it for everyone, and calling
        # `os.replace` inside the replacement recurses. Caught on the first run.
        real_replace = os.replace

        def look_then_rename(source, target):
            seen["all"] = sorted(p.name for p in self.destination.iterdir())
            seen["json"] = sorted(p.name for p in self.destination.glob("*.json"))
            return real_replace(source, target)

        with mock.patch.object(publish.os, "replace", look_then_rename):
            publish.write_item(self.destination, RECEIPT_ID, self.item)

        self.assertEqual(len(seen["all"]), 1,
                         "nothing was part-written, so this test proves nothing")
        self.assertEqual(seen["json"], [],
                         f"a reader globbing *.json would have seen {seen['json']}")

    def test_the_part_file_is_removed_when_the_rename_fails(self):
        # The counterpart to the test above: nothing is left behind either.
        with mock.patch.object(publish.os, "replace", side_effect=OSError("no")):
            with self.assertRaises(OSError):
                publish.write_item(self.destination, RECEIPT_ID, self.item)
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_a_failure_before_the_rename_leaves_no_item(self):
        with mock.patch.object(publish.json, "dumps", side_effect=ValueError("no")):
            with self.assertRaises(ValueError):
                publish.write_item(self.destination, RECEIPT_ID, self.item)
        self.assertEqual(list(self.destination.glob("*.json")), [])

    def test_writing_twice_leaves_one_file(self):
        publish.write_item(self.destination, RECEIPT_ID, self.item)
        publish.write_item(self.destination, RECEIPT_ID, self.item)
        self.assertEqual(len(list(self.destination.iterdir())), 1)

    def test_two_receipts_get_two_files(self):
        publish.write_item(self.destination, "aaa", self.item)
        publish.write_item(self.destination, "bbb", self.item)
        self.assertEqual(sorted(p.name for p in self.destination.iterdir()),
                         ["aaa.json", "bbb.json"])


class SourceGuardTest(unittest.TestCase):
    """The properties a behavioural test cannot reach.

    Parsed rather than string-matched, per `CLAUDE.md`: superseded wording is
    kept beside every correction on this project, so the prose in a module is
    always a few lines from the code and a text search reads both.
    """

    def setUp(self):
        import source_guards
        self.guards = source_guards
        self.tree = source_guards.tree_of("worker", "publish.py")

    def test_the_module_does_not_use_mimetypes(self):
        # On Windows it reads the registry, so the same receipt would publish
        # with different media types on two machines.
        self.assertNotIn("mimetypes", self.guards.called_names(self.tree))
        self.assertNotIn(
            "mimetypes",
            [alias.name for node in self.guards.ast.walk(self.tree)
             if isinstance(node, self.guards.ast.Import) for alias in node.names],
        )

    def test_the_final_name_is_never_opened_for_writing(self):
        """The rename is the only thing that may create `{receipt_id}.json`.

        A second `open()` added later would defeat the whole arrangement while
        every test above still passed, because they check the end state.
        """
        opens = [node for node in self.guards.ast.walk(self.tree)
                 if isinstance(node, self.guards.ast.Call)
                 and self.guards.ast.unparse(node.func).endswith("open")]
        self.assertEqual(len(opens), 1,
                         f"{len(opens)} open() calls in worker/publish.py; the "
                         "writer opens the temporary file and nothing else")


if __name__ == "__main__":
    unittest.main()

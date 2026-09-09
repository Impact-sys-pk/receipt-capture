"""A receipt that reaches `ok` is published, once, and nothing else is.

**Stage 1 piece 3, deliverable 5.** The three arrival routes all end in
`process_extraction_result()`, so the trigger sits there once rather than at
each of the four call sites in `app.py`. Every test below drives a real
`app.process_once()` with only the mailbox and the extractor replaced, so what
is being asserted is the live path rather than a call sequence written to suit
the test.

**Only `ok` publishes.** `possible_duplicate` does not, which 10f.24 makes
explicit and which is not in this scope, so nothing whose status is not `ok`
is published at all. Neither is `needs_review`, `failed`, or a receipt whose
client could not be resolved to a folder.

**Publishing failing must not fail the receipt.** The filing route into
`Clients\\` is still live and is still what IntelliBooks reads, so a receipt
that files correctly and fails to publish is `ok`, filed, and carries a
`publish_events` row saying what went wrong. Nothing about it changes.

**No existing receipt is published.** Amendment 283, Paul's decision: the first
run publishes only what arrives from then on. That follows from where the
trigger sits, and `NothingElsePublishesTest` holds it on the source rather than
on any one behaviour, because "nothing else publishes" is a set claim.
"""

import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import ast  # noqa: E402

import config  # noqa: E402
import source_guards  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    DOCUMENT,
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    with_email_client,
)
from worker import publish  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

CLIENT = "CLIENT001"

#: One extraction result per status the pipeline can reach, as
#: `tests/test_embedded_email_routing.py` reads them out of the validation
#: rules: a missing gross is unrecoverable, and a gross that is not net + VAT
#: is present-but-inconsistent.
OUTCOMES = {
    "ok": extraction_result(),
    "needs_review": extraction_result(gross_amount=99.0),
    "failed": extraction_result(gross_amount=None),
}


def published_items():
    """Every item file sitting in the publish folder, by name."""
    return sorted(p.name for p in config.INTELLIBOOKS_PUBLISH_DIR.glob("*.json"))


def everything_in_the_publish_folder():
    return sorted(p.name for p in config.INTELLIBOOKS_PUBLISH_DIR.iterdir())


def receipts():
    repo = Repository()
    try:
        return [dict(r) for r in repo._conn.execute("SELECT * FROM receipts")]
    finally:
        repo.close()


def publish_rows():
    repo = Repository()
    try:
        return [dict(r) for r in repo._conn.execute(
            "SELECT * FROM publish_events ORDER BY created_at")]
    finally:
        repo.close()


class OkPublishesTest(unittest.TestCase):
    def test_one_ok_receipt_produces_one_item_and_one_row(self):
        with TempEnvironment():
            with_email_client(self, CLIENT)
            Routes(RecordingExtractor(OUTCOMES["ok"])).email_attachment()

            receipt, = receipts()
            self.assertEqual(receipt["status"], "ok")
            self.assertEqual(published_items(), [f"{receipt['receipt_id']}.json"])

            row, = publish_rows()
            self.assertEqual(row["receipt_id"], receipt["receipt_id"])
            self.assertEqual(row["outcome"], publish.PUBLISHED)
            self.assertEqual(row["destination"], config.INTELLIBOOKS_DESTINATION)
            self.assertIsNone(row["reason"])
            self.assertEqual(
                Path(row["item_path"]),
                config.INTELLIBOOKS_PUBLISH_DIR / f"{receipt['receipt_id']}.json")

    def test_the_item_carries_the_client_inside_it(self):
        """Sub-step 10f.5, and it is the reason 10f.4 can use one folder.

        The item is in a folder shared by every client, so the client has to
        travel in the payload.
        """
        with TempEnvironment():
            with_email_client(self, CLIENT)
            Routes(RecordingExtractor(OUTCOMES["ok"])).email_attachment()

            receipt, = receipts()
            item = json.loads(
                (config.INTELLIBOOKS_PUBLISH_DIR / f"{receipt['receipt_id']}.json")
                .read_text(encoding="utf-8"))
            self.assertEqual(item["client_id"], CLIENT)
            self.assertEqual(item["receipt_id"], receipt["receipt_id"])
            self.assertEqual(item["validation_status"], "ok")
            self.assertEqual(item["supplier"], "Apcoa Parking")

    def test_the_item_carries_the_document_that_arrived(self):
        import base64
        with TempEnvironment():
            with_email_client(self, CLIENT)
            Routes(RecordingExtractor(OUTCOMES["ok"])).email_attachment()

            receipt, = receipts()
            item = json.loads(
                (config.INTELLIBOOKS_PUBLISH_DIR / f"{receipt['receipt_id']}.json")
                .read_text(encoding="utf-8"))
            self.assertEqual(base64.b64decode(item[publish.IMAGE_KEY]), DOCUMENT)
            self.assertEqual(item[publish.MEDIA_TYPE_KEY], "application/pdf")

    def test_the_folder_intake_route_publishes_too(self):
        # The trigger is in the shared pipeline, so it serves every route. A
        # per-route test is what shows that rather than assumes it.
        with TempEnvironment():
            Routes(RecordingExtractor(OUTCOMES["ok"])).inbox_file(
                "receipt.pdf", "phone", client_id=CLIENT)
            receipt, = receipts()
            self.assertEqual(receipt["status"], "ok")
            self.assertEqual(published_items(), [f"{receipt['receipt_id']}.json"])

    def test_the_embedded_image_route_publishes_too(self):
        with TempEnvironment():
            with_email_client(self, CLIENT)
            Routes(RecordingExtractor(OUTCOMES["ok"])).embedded_image()
            receipt, = receipts()
            self.assertEqual(receipt["status"], "ok")
            self.assertEqual(published_items(), [f"{receipt['receipt_id']}.json"])

    def test_the_filing_route_still_runs(self):
        """Stage 1 is additive and nothing changes route.

        The copy into the client folder is still what IntelliBooks reads.
        """
        with TempEnvironment():
            with_email_client(self, CLIENT)
            Routes(RecordingExtractor(OUTCOMES["ok"])).email_attachment()
            receipt, = receipts()
            self.assertTrue(receipt["filed_path"])
            self.assertTrue(Path(receipt["filed_path"]).exists())

    def test_the_document_comes_from_the_store_and_not_from_the_client_folder(self):
        """Which of the two copies the item carries.

        **The two are byte-identical today, so nothing observable separates
        them** and a mutation swapping one for the other survived the whole
        suite. It is pinned anyway: `Intellibills\\Documents\\` is the archive
        of record per 18.2a and this product owns it, while the copy under
        `Clients\\` is the firm's own filing structure and is theirs to move or
        rename. An item built from a path the firm controls would start failing
        the day somebody tidied a client folder.
        """
        seen = []
        real = publish.build_item

        def spy(sidecar, document):
            seen.append(Path(document))
            return real(sidecar, document)

        with TempEnvironment():
            with_email_client(self, CLIENT)
            with patch.object(publish, "build_item", spy):
                Routes(RecordingExtractor(OUTCOMES["ok"])).email_attachment()
            document, = seen
            self.assertTrue(
                document.is_relative_to(config.FILES_DIR),
                f"the item was built from {document}, which is not under the "
                f"document store at {config.FILES_DIR}")
            self.assertFalse(document.is_relative_to(config.CLIENTS_ROOT))

    def test_no_part_file_is_left_in_the_folder(self):
        with TempEnvironment():
            with_email_client(self, CLIENT)
            Routes(RecordingExtractor(OUTCOMES["ok"])).email_attachment()
            self.assertEqual(everything_in_the_publish_folder(), published_items())


class NothingButOkPublishesTest(unittest.TestCase):
    def _drive(self, outcome):
        with_email_client(self, CLIENT)
        Routes(RecordingExtractor(OUTCOMES[outcome])).email_attachment()

    def test_needs_review_publishes_nothing(self):
        with TempEnvironment():
            self._drive("needs_review")
            self.assertEqual(receipts()[0]["status"], "needs_review")
            self.assertEqual(published_items(), [])
            self.assertEqual(publish_rows(), [])

    def test_a_failed_extraction_publishes_nothing(self):
        with TempEnvironment():
            self._drive("failed")
            self.assertEqual(receipts()[0]["status"], "failed")
            self.assertEqual(published_items(), [])
            self.assertEqual(publish_rows(), [])

    def test_an_extraction_that_raised_publishes_nothing(self):
        with TempEnvironment():
            with_email_client(self, CLIENT)
            Routes(RecordingExtractor(RuntimeError("unreadable"))).email_attachment()
            self.assertEqual(published_items(), [])
            self.assertEqual(publish_rows(), [])

    def test_a_possible_duplicate_publishes_nothing(self):
        """10f.24 makes it explicit and it is not in this scope.

        **The two documents are different bytes and the same purchase.** Sending
        the same bytes twice does not reach the semantic check at all: the file
        hash matches first and the second arrival is skipped with no receipt
        row, which is what this test did on its first run and it proved nothing.
        Different bytes give a second receipt, and the same supplier, date and
        amount then make it a possible duplicate.
        """
        with TempEnvironment():
            with_email_client(self, CLIENT)
            extractor = RecordingExtractor(OUTCOMES["ok"])
            Routes(extractor).email_attachment(message_id="one", data=DOCUMENT)
            Routes(extractor).email_attachment(
                message_id="two", data=b"the same purchase, a different scan")

            statuses = sorted(r["status"] for r in receipts())
            self.assertEqual(statuses, ["ok", "possible_duplicate"],
                             "the fixture did not produce a possible duplicate, "
                             "so this test proves nothing")
            self.assertEqual(len(published_items()), 1)
            self.assertEqual([r["outcome"] for r in publish_rows()],
                             [publish.PUBLISHED])

    def test_an_unknown_sender_publishes_nothing(self):
        """No client, no receipt, and so nothing to publish.

        Written as "an unresolved client is a review item and never reaches
        `ok`", which is 10d.16 and 10d.18 and is true of a receipt. **An email
        from an address on no client record does not get that far**: the
        unknown-sender branch alerts and moves the email, and no `receipts` row
        is written at all. The premise was corrected rather than the assertion
        loosened.
        """
        with TempEnvironment():
            Routes(RecordingExtractor(OUTCOMES["ok"])).email_attachment()
            self.assertEqual(receipts(), [])
            self.assertEqual(published_items(), [])
            self.assertEqual(publish_rows(), [])


class PublishingFailingDoesNotFailTheReceiptTest(unittest.TestCase):
    """The brief's condition, driven three ways it can actually break."""

    def _drive_with_publish_broken(self, error):
        with_email_client(self, CLIENT)
        with patch.object(publish, "write_item", side_effect=error):
            Routes(RecordingExtractor(OUTCOMES["ok"])).email_attachment()

    def test_the_receipt_is_still_ok_and_still_filed(self):
        with TempEnvironment():
            self._drive_with_publish_broken(OSError("the folder has gone"))
            receipt, = receipts()
            self.assertEqual(receipt["status"], "ok")
            self.assertTrue(receipt["filed_path"])
            self.assertTrue(Path(receipt["filed_path"]).exists())

    def test_the_failure_is_recorded_with_its_reason(self):
        with TempEnvironment():
            self._drive_with_publish_broken(OSError("the folder has gone"))
            row, = publish_rows()
            self.assertEqual(row["outcome"], publish.FAILED)
            self.assertIn("the folder has gone", row["reason"])
            self.assertIsNone(row["item_path"])

    def test_the_email_still_reports_itself_as_processed(self):
        # The mailbox says what became of the receipt, and the receipt is fine.
        with TempEnvironment():
            with_email_client(self, CLIENT)
            routes = Routes(RecordingExtractor(OUTCOMES["ok"]))
            with patch.object(publish, "write_item", side_effect=OSError("gone")):
                routes.email_attachment()
            self.assertEqual(routes.only_landing(), "INBOX.Processed Receipts")

    def test_a_document_of_a_type_with_no_media_type_records_a_failure(self):
        """The one failure this code can cause on its own.

        `store.SUPPORTED_EXTENSIONS` should stop it arriving, so this drives
        `build_item()` failing rather than pretending the pipeline let a `.docx`
        in.
        """
        with TempEnvironment():
            with_email_client(self, CLIENT)
            with patch.object(publish, "build_item",
                              side_effect=publish.PublishError("no media type for '.docx'")):
                Routes(RecordingExtractor(OUTCOMES["ok"])).email_attachment()
            self.assertEqual(receipts()[0]["status"], "ok")
            row, = publish_rows()
            self.assertEqual(row["outcome"], publish.FAILED)
            self.assertIn(".docx", row["reason"])

    def test_the_database_write_failing_does_not_fail_the_receipt_either(self):
        # The last thing that could take the run down: recording the outcome.
        with TempEnvironment():
            with_email_client(self, CLIENT)
            with patch.object(Repository, "save_publish_event",
                              side_effect=RuntimeError("the database is locked")):
                Routes(RecordingExtractor(OUTCOMES["ok"])).email_attachment()
            self.assertEqual(receipts()[0]["status"], "ok")


class NothingElsePublishesTest(unittest.TestCase):
    """A guard over the set, not over its members.

    Each test above proves one path publishes or does not. Only a read of the
    source shows that the set of publish sites is the one intended, which is
    the rule `CLAUDE.md` states and the brief repeats. Parsed rather than
    string-matched, because superseded wording is kept beside every correction
    on this project and a text search reads the prose too.
    """

    def setUp(self):
        self.pipeline = source_guards.tree_of("worker", "extraction_pipeline.py")

    def _calls_to(self, tree, name):
        return [node for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and ast.unparse(node.func).split(".")[-1] == name]

    def test_publish_receipt_is_called_exactly_once_in_the_whole_pipeline(self):
        sites = []
        for path in [Path("app.py")] + sorted(Path("worker").rglob("*.py")):
            if path.name == "publish.py":
                continue
            tree = source_guards.tree_of(*path.parts)
            for node in self._calls_to(tree, "publish_receipt"):
                sites.append(f"{path.as_posix()}:{node.lineno}")
        self.assertEqual(
            len(sites), 1,
            f"publish_receipt() is called at {sites}; the trigger is one site "
            "in the shared pipeline, which is what makes all three arrival "
            "routes publish the same way")

    def test_the_item_writer_is_reached_only_through_publish_receipt(self):
        """`build_item()` and `write_item()` have one caller each.

        A second caller would write an item without recording it, which is the
        state 10f.36 exists to make impossible.
        """
        strays = []
        for path in [Path("app.py")] + sorted(Path("worker").rglob("*.py")):
            if path.name == "publish.py":
                continue
            tree = source_guards.tree_of(*path.parts)
            for name in ("build_item", "write_item"):
                for node in self._calls_to(tree, name):
                    strays.append(f"{name} at {path.as_posix()}:{node.lineno}")
        self.assertEqual(strays, [])

    def test_the_call_sits_inside_the_ok_branch(self):
        """Where it sits, computed rather than eyeballed.

        The enclosing `if` is found by taking the innermost `If` whose body
        contains the call, because `ast.walk` reports a node against every
        enclosing statement, which counted one call site eleven times on this
        project once already.
        """
        call, = self._calls_to(self.pipeline, "publish_receipt")
        enclosing = None
        for node in ast.walk(self.pipeline):
            if not isinstance(node, ast.If):
                continue
            if any(node.lineno <= c.lineno <= (node.end_lineno or node.lineno)
                   for c in [call]):
                if enclosing is None or node.lineno > enclosing.lineno:
                    enclosing = node
        self.assertIsNotNone(enclosing, "the call is in no if statement at all")
        test = ast.unparse(enclosing.test)
        self.assertIn("validation.status", test)
        self.assertIn("'ok'", test)
        in_the_ok_branch = any(
            statement.lineno <= call.lineno <= (statement.end_lineno or statement.lineno)
            for statement in enclosing.body)
        self.assertTrue(in_the_ok_branch,
                        "the call is in the else branch, not the ok branch")

    def test_the_trigger_does_not_wrap_itself_in_a_try(self):
        """`publish_receipt()` is the thing that must not raise.

        A `try` around the call site would make the guarantee depend on the
        caller remembering, and there are four callers of
        `process_extraction_result()`. Held so the responsibility stays in one
        place. This is a design decision recorded as a check, not a style rule.
        """
        call, = self._calls_to(self.pipeline, "publish_receipt")
        wrappers = [node for node in ast.walk(self.pipeline)
                    if isinstance(node, ast.Try)
                    and node.lineno <= call.lineno <= (node.end_lineno or node.lineno)]
        self.assertEqual(
            wrappers, [],
            "the publish call is inside a try; publish_receipt() swallows its "
            "own failures, so a try here hides which one is doing the work")

    def test_publish_receipt_swallows_every_exception(self):
        # The counterpart to the test above, on the module that must do it.
        tree = source_guards.tree_of("worker", "publish.py")
        function = next(n for n in ast.walk(tree)
                        if isinstance(n, ast.FunctionDef)
                        and n.name == "publish_receipt")
        handlers = [h for node in ast.walk(function)
                    if isinstance(node, ast.Try) for h in node.handlers]
        self.assertTrue(handlers, "publish_receipt() catches nothing")
        caught = {ast.unparse(h.type) for h in handlers if h.type is not None}
        self.assertIn("Exception", caught)


if __name__ == "__main__":
    unittest.main()

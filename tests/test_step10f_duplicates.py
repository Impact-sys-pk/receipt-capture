"""Step 10f, sub-steps 10f.18 to 10f.23: what counts as a duplicate, and of whom.

**Six sub-steps split out of step 10f on Paul's decision of 2026-09-07**, because
none of them depends on the publish step or on the client folder copy. Amendments
136 and 137 carry the reasoning.

**The one idea underneath all of them: a duplicate is a duplicate of a receipt
belonging to the same client.** One capture mailbox serves every client, and a
PDF is produced by software, so the same PDF is the same bytes every time: a
shared insurance schedule, MOT or breakdown-cover document between two drivers on
one car arrives byte-identical from two people. Today the second one is discarded
and credited to the first, and nothing reports it. Amendment 136, and Paul's
reasoning decided the shape rather than only the answer: scoping the lookup
removes the case rather than deprioritising it.

**Two people photographing one receipt produce different bytes**, which is why
this was invisible until the file type was considered separately.
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

import base64  # noqa: E402
import json  # noqa: E402
from unittest.mock import patch  # noqa: E402

import config  # noqa: E402
from resolution_fixtures import TempEnvironment  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

CLIENT_A = "CLIENT001"
CLIENT_B = "CLIENT002"
SHARED_HASH = "a" * 64

#: The one document every route in this file carries. Bytes rather than a
#: fixture file, so the three routes are provably carrying the same thing.
DOCUMENT = b"one document, sent three ways"
SENDER = "driver@example.com"


class Routes:
    """Drive one arrival route at a time through a real `app.process_once()`.

    **Only the mailbox and the extractor are replaced.** Everything from the
    duplicate check inwards is the live code path, which is what 10f.22 is
    asking about: whether the three routes reach the same verdict is a property
    of the code between them, and a hand-rolled call sequence would only test
    the sequence I had in mind.

    `moved_to` records what `move_email_to_folder()` was asked to do, because
    the disposal is the one thing 10f.22 expects to differ.
    """

    def __init__(self, extractor):
        self.extractor = extractor
        self.moved_to = []

    def _run(self, **overrides):
        import app

        stubs = {
            "scan_inbox": app.scan_inbox,
            "fetch_emails_without_attachments": lambda *a, **k: [],
            "extract_embedded_images": lambda *a, **k: [],
            "fetch_new_messages": lambda *a, **k: [],
            "fetch_attachments": lambda *a, **k: [],
            "move_email_to_folder": lambda uid, folder: self.moved_to.append(folder),
            "send_no_attachment_alert": lambda *a, **k: False,
            "send_unknown_sender_alert": lambda *a, **k: False,
            "get_extractor": lambda *a, **k: self.extractor,
        }
        stubs.update(overrides)
        patches = [patch.object(app, name, value) for name, value in stubs.items()]
        patches.append(patch.object(config, "get_pipeline_version", lambda: "test-version"))
        for p in patches:
            p.start()
        try:
            app.process_once()
        finally:
            for p in reversed(patches):
                p.stop()

    def email_attachment(self, message_id="msg-att", data=DOCUMENT):
        """The attachment path: an email carrying a real attachment."""
        message = {"id": message_id, "uid": 1, "subject": "receipt",
                   "from": {"emailAddress": {"address": SENDER}},
                   "receivedDateTime": "2026-04-01T00:00:00Z", "msg": None}
        attachment = {"id": "att-1", "name": "shared.pdf",
                      "contentBytes": base64.standard_b64encode(data).decode()}
        self._run(fetch_new_messages=lambda *a, **k: [message],
                  fetch_attachments=lambda *a, **k: [attachment])

    def embedded_image(self, message_id="msg-emb", data=DOCUMENT):
        """The embedded-image path: an iOS share with the image in the body."""
        message = {"id": message_id, "uid": 2, "subject": "receipt",
                   "from": SENDER,
                   "receivedDateTime": "2026-04-01T00:00:00Z", "msg": None}
        embedded = {"id": "emb-1", "name": "shared.pdf",
                    "contentBytes": base64.standard_b64encode(data).decode()}
        self._run(fetch_emails_without_attachments=lambda *a, **k: [message],
                  extract_embedded_images=lambda *a, **k: [embedded])

    def inbox_file(self, name, source, data=DOCUMENT, client_id=CLIENT_A):
        """The folder-intake path, which serves both phone and Add Receipts.

        `source` is the sidecar's own word, one of sub-step 10d.40's four. The
        phone app writes `phone` and IntelliBooks Desktop writes `desktop` when
        Add Receipts imports a file, and both land in the same loop.
        """
        inbox = config.RECEIPT_INBOX_ROOT / client_id
        inbox.mkdir(parents=True, exist_ok=True)
        original = inbox / name
        original.write_bytes(data)
        original.with_suffix(".json").write_text(
            json.dumps({"client_id": client_id, "source": source}), encoding="utf-8")
        self._run()
        return original


def with_email_client(test_case, client_id=CLIENT_A):
    """Point `config.CLIENTS` at one client, and put it back.

    `TempEnvironment` sets `CLIENTS_BY_ID` and deliberately leaves `CLIENTS`
    alone, per `tests/live_paths.py`'s note that the registries are each test's
    own business. The email routes resolve the sender through `CLIENTS`, so a
    test that drives one has to say who is sending.
    """
    record = dict(config.CLIENTS_BY_ID[client_id])
    test_case.addCleanup(setattr, config, "CLIENTS", config.CLIENTS)
    config.CLIENTS = {SENDER: record}


def seed_receipt(repo, receipt_id, client_id, file_hash=SHARED_HASH, filed=True,
                 firm_id="FIRM001"):
    """One receipt row for `client_id`, filed unless told otherwise.

    Filed matters: every caller of find_by_hash() pairs it with
    is_recorded_and_filed(), from 10f.20 onwards, so an unfiled seed tests a
    different thing.
    """
    repo.save_receipt(
        receipt_id=receipt_id,
        message_id=f"seed:{receipt_id}",
        email_subject=None,
        email_from=None,
        email_received_at="2026-04-01T00:00:00+00:00",
        filename="shared.pdf",
        file_path=f"/store/{receipt_id}.pdf",
        file_hash=file_hash,
        firm_id=firm_id,
        client_id=client_id,
        source="email",
    )
    if filed:
        repo.mark_receipt_filed(receipt_id, f"/clients/{client_id}/shared.pdf")
    return receipt_id


class HashLookupIsScopedToTheClientTest(unittest.TestCase):
    """10f.18. `find_by_hash()` matches within one client and no further.

    **Both of its queries, and the first one is the awkward half.**
    `processed_attachments` carries no `client_id` column, only a `receipt_id`,
    so the scope has to come from a join onto `receipts`. Read out of
    `worker/database/schema.py` rather than assumed.
    """

    def test_another_clients_identical_file_is_not_a_duplicate(self):
        with TempEnvironment():
            repo = Repository()
            try:
                seed_receipt(repo, "r-a", CLIENT_A)
                self.assertEqual(repo.find_by_hash(SHARED_HASH, CLIENT_A), "r-a")
                self.assertIsNone(
                    repo.find_by_hash(SHARED_HASH, CLIENT_B),
                    "client B's identical PDF was credited to client A, which is "
                    "the shared insurance schedule case in amendment 136",
                )
            finally:
                repo.close()

    def test_the_same_client_resending_is_still_a_duplicate(self):
        # The other half. Scoping must not switch the check off.
        with TempEnvironment():
            repo = Repository()
            try:
                seed_receipt(repo, "r-a", CLIENT_A)
                self.assertEqual(repo.find_by_hash(SHARED_HASH, CLIENT_A), "r-a")
            finally:
                repo.close()

    def test_the_processed_attachments_query_is_scoped_too(self):
        """The first of the two queries, exercised on its own.

        A receipt row alone would be found by the second query, so this seeds a
        receipt for client A and asks as client B with the attachment row
        present: if only the `receipts` query were scoped, the attachment row
        would still answer.
        """
        with TempEnvironment():
            repo = Repository()
            try:
                seed_receipt(repo, "r-a", CLIENT_A)
                repo.mark_processed("msg-1", "att-1", SHARED_HASH, "r-a", "FIRM001")
                self.assertEqual(repo.find_by_hash(SHARED_HASH, CLIENT_A), "r-a")
                self.assertIsNone(repo.find_by_hash(SHARED_HASH, CLIENT_B))
            finally:
                repo.close()

    def test_an_attachment_row_whose_receipt_is_gone_matches_nobody(self):
        """A consequence of the join, pinned rather than left to be discovered.

        `processed_attachments` outlives the receipt it names if a rebuild drops
        the receipt row, which is the case `worker/database/schema.py` describes
        for `resolution_events`. Before 10f.18 the unscoped query returned that
        dangling id; the join cannot, because there is no row to take a client
        from.

        **It changes nothing a caller can see**, and that is the point of
        asserting it: all three call sites pair the lookup with
        `is_recorded_and_filed()` from 10f.20, and a receipt with no row is not
        filed, so both the old answer and the new one allow reprocessing.
        """
        with TempEnvironment():
            repo = Repository()
            try:
                repo.mark_processed("msg-1", "att-1", SHARED_HASH, "r-gone", "FIRM001")
                self.assertIsNone(repo.find_by_hash(SHARED_HASH, CLIENT_A))
                self.assertFalse(repo.is_recorded_and_filed("r-gone"),
                                 "and it was never filed, so the outcome for a "
                                 "caller is unchanged")
            finally:
                repo.close()

    def test_the_client_is_required_rather_than_defaulted(self):
        """No caller may reach this without a client, so none may omit one.

        A keyword with a default of None would have let a call site keep
        compiling while asking the old, unscoped question. All three callers
        already hold the client at the point of the call, established by reading
        them, so there is nothing for a default to serve.
        """
        import inspect

        signature = inspect.signature(Repository.find_by_hash)
        parameters = list(signature.parameters.values())
        self.assertEqual([p.name for p in parameters],
                         ["self", "file_hash", "client_id"])
        self.assertIs(parameters[2].default, inspect.Parameter.empty,
                      "client_id has a default, so a call site can still ask "
                      "the unscoped question")


def seed_extraction(repo, receipt_id, supplier="Apcoa Parking",
                    invoice_date="2026-04-01", gross=12.0):
    """One filed receipt's extraction, so the loose lookup can find it.

    `find_by_transaction_loose()` requires `r.filed_path IS NOT NULL`, which
    `seed_receipt()` supplies.
    """
    repo.save_extraction(
        extraction_id=f"x-{receipt_id}",
        receipt_id=receipt_id,
        engine="fake",
        supplier_name=supplier,
        invoice_date=invoice_date,
        net_amount=10.0,
        vat_amount=2.0,
        gross_amount=gross,
        currency="GBP",
        raw_response="{}",
        validation_status="ok",
        validation_notes=[],
    )


class SemanticLookupIsScopedToTheClientTest(unittest.TestCase):
    """10f.19. `find_by_transaction_loose()` matches within one client.

    **This is amendment 107's "same client", which step 10f dropped when it was
    written.** Supplier, date and amount within a penny is a wide net on purpose,
    and across clients it is far wider than the hash: two drivers filling up at
    the same garage on the same day for the same amount need not have shared any
    document at all.

    Without it, two clients sending one document reach Review rather than being
    no duplicate at all, which is worse than it sounds: 10f.24 routes a
    `possible_duplicate` to Review and never publishes it.
    """

    def test_another_clients_identical_transaction_is_not_a_duplicate(self):
        with TempEnvironment():
            repo = Repository()
            try:
                seed_receipt(repo, "r-a", CLIENT_A, file_hash="h-a")
                seed_extraction(repo, "r-a")
                self.assertEqual(
                    repo.find_by_transaction_loose(
                        "Apcoa Parking", "2026-04-01", 12.0, client_id=CLIENT_A),
                    "r-a")
                self.assertIsNone(
                    repo.find_by_transaction_loose(
                        "Apcoa Parking", "2026-04-01", 12.0, client_id=CLIENT_B),
                    "two clients buying the same thing on the same day for the "
                    "same amount are not a duplicate")
            finally:
                repo.close()

    def test_the_same_client_buying_it_twice_is_still_caught(self):
        # Scoping must not switch the check off. `_signals_differ()` in
        # worker/extraction_pipeline.py is what separates a genuine second
        # purchase from a resend, and it is untouched by this sub-step.
        with TempEnvironment():
            repo = Repository()
            try:
                seed_receipt(repo, "r-a", CLIENT_A, file_hash="h-a")
                seed_extraction(repo, "r-a")
                self.assertEqual(
                    repo.find_by_transaction_loose(
                        "Apcoa Parking", "2026-04-01", 12.0, client_id=CLIENT_A),
                    "r-a")
            finally:
                repo.close()

    def test_it_is_scoped_on_the_no_date_branch_too(self):
        """The function has two queries and only one is the obvious one.

        A receipt with no invoice date takes the second branch, matching on
        supplier and amount alone. That is the wider of the two, so leaving it
        unscoped would have left the worse half of the fault in place.
        """
        with TempEnvironment():
            repo = Repository()
            try:
                seed_receipt(repo, "r-a", CLIENT_A, file_hash="h-a")
                seed_extraction(repo, "r-a", invoice_date=None)
                self.assertEqual(
                    repo.find_by_transaction_loose(
                        "Apcoa Parking", None, 12.0, client_id=CLIENT_A),
                    "r-a")
                self.assertIsNone(
                    repo.find_by_transaction_loose(
                        "Apcoa Parking", None, 12.0, client_id=CLIENT_B))
            finally:
                repo.close()

    def test_the_client_is_required_rather_than_defaulted(self):
        import inspect

        parameters = inspect.signature(
            Repository.find_by_transaction_loose).parameters
        self.assertIn("client_id", parameters)
        self.assertIs(parameters["client_id"].default, inspect.Parameter.empty,
                      "client_id has a default, so the one caller can still ask "
                      "the unscoped question")


class EmbeddedImageGuardTest(unittest.TestCase):
    """10f.20. The third hash call site gains the guard the other two have.

    Two of the three `find_by_hash()` call sites in `app.py` check
    `is_recorded_and_filed()` before treating a match as a duplicate. The
    embedded-image path did not, so it skipped on **any** hash match, including
    one against a receipt that failed extraction and was never filed.

    **The reprocessing rule this restores is deliberate and is described on
    `_move_inbox_pair_to_processed()`'s docstring**: a hash matching a receipt
    with a NULL `filed_path` is not a reason to skip, because that receipt never
    became anything and the resend is the operator's second attempt. This change
    makes that rule reachable on a route where it was not.

    **It cannot loop.** The embedded path calls `mark_processed()` for every
    image and moves the email to `INBOX.Processed Receipts` afterwards, so the
    same email is not offered again. Established by reading the block, because
    "allow reprocessing" on a path that re-reads its own input is how you get an
    OpenAI call every five minutes indefinitely.
    """

    def _receipts(self):
        repo = Repository()
        try:
            return [dict(r) for r in repo._conn.execute(
                "SELECT * FROM receipts ORDER BY created_at").fetchall()]
        finally:
            repo.close()

    def test_an_unfiled_hash_match_is_reprocessed_rather_than_skipped(self):
        from resolution_fixtures import RecordingExtractor, extraction_result

        with TempEnvironment():
            with_email_client(self)
            import app
            repo = Repository()
            try:
                seed_receipt(repo, "r-unfiled", CLIENT_A,
                             file_hash=app.compute_hash(DOCUMENT), filed=False)
            finally:
                repo.close()

            Routes(RecordingExtractor(extraction_result())).embedded_image()

            created = [r for r in self._receipts() if r["receipt_id"] != "r-unfiled"]
            self.assertEqual(
                len(created), 1,
                "the embedded path skipped on a hash match against a receipt "
                "that was never filed, so the operator's resend produced "
                "nothing at all")

    def test_a_filed_hash_match_is_still_skipped(self):
        # The other half. The guard must not switch the duplicate check off.
        from resolution_fixtures import RecordingExtractor, extraction_result

        with TempEnvironment():
            with_email_client(self)
            import app
            repo = Repository()
            try:
                seed_receipt(repo, "r-filed", CLIENT_A,
                             file_hash=app.compute_hash(DOCUMENT), filed=True)
            finally:
                repo.close()

            routes = Routes(RecordingExtractor(extraction_result()))
            routes.embedded_image()

            created = [r for r in self._receipts() if r["receipt_id"] != "r-filed"]
            self.assertEqual(created, [], "a filed duplicate was processed again")
            self.assertIn("INBOX.Duplicates", routes.moved_to)

    def test_all_three_hash_call_sites_read_the_same_way(self):
        """The set claim, read off `app.py` rather than trusted to three tests.

        Every `find_by_hash()` call in `app.py` must sit in a condition that also
        calls `is_recorded_and_filed()`. Reading the source catches a fourth call
        site being added later without the guard, which no behavioural test would.
        """
        import ast
        from pathlib import Path

        source = (Path(__file__).resolve().parent.parent / "app.py").read_text(
            encoding="utf-8")
        tree = ast.parse(source)
        lines = source.splitlines()

        call_lines = [
            node.lineno for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "find_by_hash"
        ]
        self.assertEqual(len(call_lines), 3,
                         f"the number of find_by_hash call sites moved: {call_lines}")

        for lineno in call_lines:
            with self.subTest(line=lineno):
                # The call, then the `if` that acts on it. Two lines is enough
                # for both shapes app.py uses.
                window = "\n".join(lines[lineno - 1:lineno + 2])
                self.assertIn(
                    "is_recorded_and_filed", window,
                    f"the find_by_hash call at app.py:{lineno} treats a match as "
                    "a duplicate without checking it was ever filed")


class StatementHashLookupIsScopedToTheClientTest(unittest.TestCase):
    """Amendment 1 to the brief, Paul's ruling of 2026-09-07 19:35 BST.

    **No sub-step of step 10f covers this**, which is why it arrived as an
    amendment after the work had started. `find_statement_by_hash()` filtered on
    the hash alone in exactly the way `find_by_hash()` did, so a platform
    statement sent by two clients collided and the second client's was credited
    to the first.

    **A statement is more exposed to this than a receipt, not less.** An uber,
    bolt or freenow weekly statement is a generated PDF, which is the file type
    amendment 136 identified as the one where byte-identical copies actually
    happen, and two drivers on one account is an ordinary arrangement.

    `statements` held 0 rows when this landed, so nothing on disk was affected
    and no migration arose.
    """

    def _seed_statement(self, repo, statement_id, client_id, file_hash="s" * 64):
        repo.save_statement(
            statement_id=statement_id,
            client_id=client_id,
            platform="uber",
            week_ending="2026-04-05",
            source="desktop",
            file_hash=file_hash,
            file_path=f"/store/{statement_id}.pdf",
            filed_path=f"/clients/{client_id}/{statement_id}.pdf",
        )

    def test_another_clients_identical_statement_is_not_a_duplicate(self):
        with TempEnvironment():
            repo = Repository()
            try:
                self._seed_statement(repo, "s-a", CLIENT_A)
                self.assertEqual(
                    repo.find_statement_by_hash("s" * 64, CLIENT_A), "s-a")
                self.assertIsNone(
                    repo.find_statement_by_hash("s" * 64, CLIENT_B),
                    "client B's identical weekly statement was credited to "
                    "client A and B's copy was removed from the inbox")
            finally:
                repo.close()

    def test_the_same_client_resending_is_still_a_duplicate(self):
        with TempEnvironment():
            repo = Repository()
            try:
                self._seed_statement(repo, "s-a", CLIENT_A)
                self.assertEqual(
                    repo.find_statement_by_hash("s" * 64, CLIENT_A), "s-a")
            finally:
                repo.close()

    def test_the_client_is_required_rather_than_defaulted(self):
        import inspect

        parameters = list(
            inspect.signature(Repository.find_statement_by_hash).parameters.values())
        self.assertEqual([p.name for p in parameters],
                         ["self", "file_hash", "client_id"])
        self.assertIs(parameters[2].default, inspect.Parameter.empty)


class DeadFunctionsAreGoneTest(unittest.TestCase):
    """10f.23. Two duplicate lookups nothing called.

    They are the strict ancestors of `find_by_transaction_loose()`: exact
    supplier and exact amount, one with a date and one without. Neither was
    reachable, so neither was ever going to gain the client filter that 10f.19
    gives the one that is, and leaving them would have left two functions that
    look like duplicate detection and answer without regard to whose receipt it
    is.

    **Kept as a test rather than trusted to the deletion**, in the shape
    `tests/test_path_layout.py` uses for `DATA_DIR`: the risk is not that
    somebody fails to delete them, it is that somebody writes them again.
    """

    def test_neither_dead_transaction_lookup_is_on_the_repository(self):
        for name in ("find_by_transaction", "find_by_transaction_no_date"):
            with self.subTest(method=name):
                self.assertFalse(
                    hasattr(Repository, name),
                    f"Repository.{name}() is back. It matched on supplier and "
                    "amount with no client, which is the fault 10f.18 and "
                    "10f.19 exist to remove, and nothing called it.",
                )

    def test_the_lookup_that_survived_is_still_there(self):
        # Without this the test above is satisfied by deleting all three, which
        # would take the semantic duplicate check with them.
        self.assertTrue(hasattr(Repository, "find_by_transaction_loose"))


if __name__ == "__main__":
    unittest.main()

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

from resolution_fixtures import TempEnvironment  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

CLIENT_A = "CLIENT001"
CLIENT_B = "CLIENT002"
SHARED_HASH = "a" * 64


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

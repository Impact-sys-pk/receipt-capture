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

from worker.database.repository import Repository  # noqa: E402


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

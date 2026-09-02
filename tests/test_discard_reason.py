"""Design document 5.1 as amended: resolution_events.reason.

discard_receipt() takes a reason and the table had nowhere to put it, so it
reached a log line and the operator's message and then vanished. For a discard
the reason is the single most useful thing to keep: the difference between
"duplicate of r-x" and "the client sent a bank statement by mistake"."""

import sys
import types
import unittest

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config

from resolution_fixtures import TempEnvironment, good_corrections, rows
from worker.database.repository import Repository
from worker.resolution.service import discard_receipt, parse_corrections, resolve_receipt


class DiscardReasonTest(unittest.TestCase):
    """5.1 as amended: the reason is the most useful thing to keep about a discard."""

    def test_the_reason_round_trips_out_of_its_own_column(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, status="possible_duplicate", gross_amount=12.0)
                discard_receipt(
                    repo, "r-1", "the client sent a bank statement by mistake",
                    actor="paul", source="cli",
                )
                event = rows(repo, "SELECT * FROM resolution_events")[0]
                self.assertEqual(event["reason"], "the client sent a bank statement by mistake")
                self.assertIsNone(
                    event["corrections_json"],
                    "the reason must not be smuggled into corrections_json",
                )
            finally:
                repo.close()

    def test_a_resolve_leaves_the_reason_null(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo)
                resolve_receipt(
                    repo, env.engine(repo), "r-1", good_corrections(), actor="paul", source="cli",
                )
                event = rows(repo, "SELECT * FROM resolution_events")[0]
                self.assertIsNone(event["reason"])
            finally:
                repo.close()

    # test_the_column_exists_on_an_older_database() was deleted at sub-step
    # 10d.34, with the eleven ALTER TABLE ADD COLUMN migrations it exercised. It
    # built resolution_events without `reason` and proved init_db() added it.
    # The column is now in the CREATE TABLE, which is the only definition.


if __name__ == "__main__":
    unittest.main()

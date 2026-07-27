"""Design document 4.3 step 6 as amended: possible_duplicate survives a
still_invalid correction.

save_extraction() stamps receipts.status with the new validation_status, which
is right for needs_review and failed and wrong for possible_duplicate. That is
a statement about the relationship between two receipts, not about the validity
of one, and overwriting it hands a receipt a human has already examined back to
the pipeline for re-extraction."""

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

from datetime import datetime, timedelta, timezone

VERSION = "test-version"

class PreservePossibleDuplicateTest(unittest.TestCase):
    """4.3 step 6 as amended."""

    def _retry_candidates(self, repo):
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=60)
        return [r["receipt_id"] for r in repo.find_failed_by_version(VERSION, cutoff)]

    def test_possible_duplicate_survives_a_still_invalid_correction(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-dup", status="possible_duplicate", gross_amount=12.0)
                env.seed(repo, receipt_id="r-original", status="ok")
                repo.set_duplicate_of("r-dup", "r-original")

                # Supplier corrected, gross removed, so it fails validation.
                corrections, errors = parse_corrections(
                    {"supplier_name": "Apcoa Parking", "gross_amount": ""}
                )
                self.assertEqual(errors, {})

                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-dup", corrections, actor="paul", source="cli",
                )

                self.assertEqual(outcome.outcome, "still_invalid")
                receipt = repo.get_receipt("r-dup")
                self.assertEqual(
                    receipt["status"], "possible_duplicate",
                    "a statement about two receipts must not be overwritten by validation",
                )
                self.assertEqual(receipt["duplicate_of"], "r-original")
                # The attempt is still recorded.
                self.assertEqual(
                    len(rows(repo, "SELECT * FROM extractions WHERE receipt_id = 'r-dup'")), 2
                )
            finally:
                repo.close()

    def test_needs_review_still_follows_validate(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-review", status="needs_review", gross_amount=12.0)
                corrections, _ = parse_corrections({"gross_amount": ""})

                outcome = resolve_receipt(
                    repo, env.engine(repo), "r-review", corrections, actor="paul", source="cli",
                )

                self.assertEqual(outcome.outcome, "still_invalid")
                # No supplier and no gross: validate() calls that failed.
                self.assertEqual(repo.get_receipt("r-review")["status"], "failed")
            finally:
                repo.close()

    def test_the_preserved_receipt_is_not_handed_back_to_auto_retry(self):
        # This is why it matters. possible_duplicate is not retry-eligible;
        # needs_review and failed are.
        with TempEnvironment() as env:
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-dup", status="possible_duplicate", gross_amount=12.0)
                env.seed(repo, receipt_id="r-review", status="needs_review", gross_amount=12.0)

                corrections, _ = parse_corrections({"gross_amount": ""})
                for receipt_id in ("r-dup", "r-review"):
                    resolve_receipt(
                        repo, env.engine(repo), receipt_id, corrections,
                        actor="paul", source="cli",
                    )

                candidates = self._retry_candidates(repo)
                self.assertNotIn("r-dup", candidates, "a human has already examined this one")
                self.assertIn("r-review", candidates)
            finally:
                repo.close()


if __name__ == "__main__":
    unittest.main()

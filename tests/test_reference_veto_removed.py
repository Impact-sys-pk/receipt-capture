"""Item 35, Paul's decision of 2026-11-14: the reference number no longer vetoes.

**What was wrong.** `find_by_transaction_loose()` matched on supplier, invoice
date and gross, `is_published()` and `is_discarded()` both passed, and
`_signals_differ()` then vetoed the `possible_duplicate` flag because both
readings carried a reference number and they differed. **It returned before it
reached the receipt-time comparison**, and the times were identical.

The two readings of one image gave `16871102102` and `000013`. Both are real
fields on that receipt, the footer line and `Receipt no.`, so the model chose
different fields rather than disagreeing about one. **The second time this
comparison has let a duplicate through**: the RingGo receipt of 10f.30's check 5
was the first.

**The decision.** Remove the veto, keep the receipt-time comparison, and carry
both differing reference numbers into the validation note so a flagged row
says why. **The trade, accepted by Paul**: `possible_duplicate` routes to
review rather than refusing, so a false positive costs one row to dismiss and a
false negative is a double-counted expense in a client's books.

**These tests use different bytes on purpose**, so item 34's file-hash block
cannot answer and the semantic check is the defence under test.
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

from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    with_email_client,
)
from worker.database.repository import Repository  # noqa: E402

FOOTER = "16871102102"
RECEIPT_NO = "000013"


def shell(ref, time="06:23"):
    """The 2026-11-14 receipt, as the live extractions read it."""
    return extraction_result(
        supplier_name="Shell Co-op Harborne",
        invoice_date="2026-07-08",
        net_amount=None,
        vat_amount=None,
        gross_amount=51.11,
        receipt_ref_number=ref,
        receipt_time=time,
    )


class TwoReadingsTest(unittest.TestCase):

    def _two(self, first, second):
        """Drive one receipt twice as two different scans. Returns
        (receipts in arrival order, the second receipt's newest extraction)."""
        with_email_client(self)
        Routes(RecordingExtractor(first)).email_attachment(
            message_id="first", data=b"the first scan")
        Routes(RecordingExtractor(second)).email_attachment(
            message_id="second", data=b"the second scan, different bytes")
        repo = Repository()
        try:
            receipts = [dict(r) for r in repo._conn.execute(
                "SELECT * FROM receipts ORDER BY created_at, rowid").fetchall()]
            extraction = repo.get_extraction_for_receipt(receipts[-1]["receipt_id"])
        finally:
            repo.close()
        return receipts, extraction

    def test_the_2026_11_14_receipt_is_flagged(self):
        """The red case. Same supplier, date, gross and time; the model read
        the footer once and `Receipt no.` once."""
        with TempEnvironment():
            (first, second), _ = self._two(shell(FOOTER), shell(RECEIPT_NO))
            self.assertEqual(first["status"], "ok")
            self.assertEqual(
                second["status"], "possible_duplicate",
                "two different reference numbers still veto the match, which "
                "is how the receipt reached the books twice")
            self.assertEqual(second["duplicate_of"], first["receipt_id"])

    def test_the_note_says_which_two_reference_numbers_differed(self):
        with TempEnvironment():
            (first, _), extraction = self._two(shell(FOOTER), shell(RECEIPT_NO))
            notes = extraction["validation_notes"]
            self.assertIn(first["receipt_id"][:8], notes)
            self.assertIn(RECEIPT_NO, notes)
            self.assertIn(FOOTER, notes)
            self.assertIn("reference numbers differ", notes)

    def test_matching_reference_numbers_add_nothing_to_the_note(self):
        """Only a difference is worth saying. The note is the one it was."""
        with TempEnvironment():
            (first, second), extraction = self._two(shell(FOOTER), shell(FOOTER))
            self.assertEqual(second["status"], "possible_duplicate")
            self.assertEqual(extraction["validation_notes"],
                             f"matches {first['receipt_id'][:8]}... "
                             "(supplier, date, amount)")

    def test_a_missing_reference_number_adds_nothing_to_the_note(self):
        with TempEnvironment():
            (_, second), extraction = self._two(shell(FOOTER), shell(None))
            self.assertEqual(second["status"], "possible_duplicate")
            self.assertNotIn("reference numbers differ", extraction["validation_notes"])

    def test_a_difference_of_case_alone_is_not_called_a_difference(self):
        """`_comparable_ref()` still decides what differs, Paul's ruling of
        2026-09-10: case and surrounding whitespace only."""
        with TempEnvironment():
            (_, second), extraction = self._two(
                shell("LBCAMRL-01303"), shell("  LBcAMRL-01303 "))
            self.assertEqual(second["status"], "possible_duplicate")
            self.assertNotIn("reference numbers differ", extraction["validation_notes"])

    def test_the_receipt_time_still_separates_two_transactions(self):
        """Kept, per the decision. Over five minutes apart is two purchases."""
        with TempEnvironment():
            (first, second), _ = self._two(shell(FOOTER, "06:23"),
                                           shell(RECEIPT_NO, "14:10"))
            self.assertEqual([first["status"], second["status"]], ["ok", "ok"])
            self.assertIsNone(second["duplicate_of"])

    def test_the_receipt_time_within_five_minutes_still_flags(self):
        with TempEnvironment():
            (_, second), _ = self._two(shell(FOOTER, "06:23"),
                                       shell(RECEIPT_NO, "06:27"))
            self.assertEqual(second["status"], "possible_duplicate")


if __name__ == "__main__":
    unittest.main()

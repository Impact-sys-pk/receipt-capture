r"""A correction carries the item lines the extractor read. Outstanding item 33.

Brief `PROMPT_claude_code_2026-11-16_line_items_at_every_save.md`, Paul's
decision of 2026-11-16.

## The defect

**A correction appends a `manual_correction` extraction row, and that row is the
receipt's latest.** The three correction writes in `worker\resolution\service.py`
did not pass `line_items`, so after a correction the latest row said "no item
lines" about a document the extractor had read lines off. Every reader of the
latest row then saw none: the recovery sweep's published `line_item_count`,
which is the Lines column in IntelliBooks Desktop, and the classifier's lines on
`retroactive_categorise.py`.

Read-only on 2026-11-16: 39 of 186 rows carry `line_items`, and **all 52
`manual_correction` rows carry none.**

## Why carrying them forward is right on these three and not on the other two

**Desktop has no input for item lines, so a correction cannot have changed
them.** `_apply_filed_note()` already carries `receipt_ref_number` and
`receipt_time` forward for exactly that reason, "because the extractor read them
and nobody has contradicted them", and `resolve_receipt()` merges by key
presence, so every field the correction does not name keeps the extraction's
value. Item lines are the same case and were the one field left out.

The two auto-retry writes in `app.py` record an attempt that read nothing, with
every figure None, so there are no lines to carry and that row is not a reading.
They are unchanged.
"""

import unittest

import config

from chart_fixtures import TempChartBundle
from resolution_fixtures import TempEnvironment, good_corrections
from worker.database.repository import Repository
from worker.line_items import LineItem, to_json
from worker.resolution.service import (
    apply_resolution_note, parse_corrections, resolve_receipt,
)
from worker.categorisation.engine import CategorisationEngine

LINES = [LineItem("Parking 2 hours", 6.40), LineItem("Text message reminder", 0.20)]
STORED = to_json(LINES)
CATEGORY = ("7304", "Parking and tolls")
FILED_RELATIVE = (
    r"Clients\Test Client\IntelliBooks\Receipts\2026-27"
    r"\2026-04-01_apcoa-parking_12.00.pdf")


class _Base(unittest.TestCase):
    def setUp(self):
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.chart = TempChartBundle(accounts=(CATEGORY,)).__enter__()
        self.addCleanup(self.chart.__exit__, None, None, None)
        self.repo = Repository()
        self.addCleanup(self.repo.close)
        self.engine = CategorisationEngine(repo=self.repo, enable_ai_fallback=False)

    def seed(self, line_items=LINES):
        self.env.seed(self.repo, receipt_id="r-1", line_items=line_items)

    def latest(self):
        return self.repo.get_extraction_for_receipt("r-1")

    def resolve(self, corrections):
        return resolve_receipt(self.repo, self.engine, "r-1", corrections,
                               actor="test", source="cli")


class ACorrectionKeepsTheLinesTest(_Base):

    def test_a_correction_that_files_keeps_them(self):
        self.seed()
        outcome = self.resolve(good_corrections())
        self.assertEqual(outcome.outcome, "filed", outcome.message)
        self.assertEqual(self.latest()["engine"], "manual_correction")
        self.assertEqual(self.latest()["line_items"], STORED,
                         "the correction row dropped the lines the extractor read")

    def test_a_correction_still_invalid_keeps_them(self):
        """The attempt row is the latest row too, so it drops them just the same."""
        self.seed()
        corrections, errors = parse_corrections({"supplier_name": "Apcoa Parking"})
        self.assertEqual(errors, {})
        outcome = self.resolve(corrections)
        self.assertEqual(outcome.outcome, "still_invalid", outcome.message)
        self.assertEqual(self.latest()["engine"], "manual_correction")
        self.assertEqual(self.latest()["line_items"], STORED,
                         "the still-invalid attempt row dropped the lines")

    def test_a_filed_note_keeps_them(self):
        self.seed()
        target = config.PRACTICE_ROOT / FILED_RELATIVE.replace("\\", "/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("the copy Desktop filed", encoding="utf-8")
        outcome = apply_resolution_note(self.repo, self.engine, {
            "schema": 1, "receipt_id": "r-1", "client_id": "CLIENT001",
            "action": "filed", "resolved_by": "desktop",
            "resolved_at": "2026-11-16T12:00:00.000Z",
            "values": {"supplier_name": "Apcoa Parking", "invoice_date": "2026-04-01",
                       "net_amount": 10, "vat_amount": 2, "gross_amount": 12,
                       "currency": "GBP", "category_code": CATEGORY[0],
                       "category_name": CATEGORY[1]},
            "filed_path": FILED_RELATIVE,
        })
        self.assertEqual(outcome.outcome, "filed", outcome.message)
        self.assertEqual(self.latest()["engine"], "manual_correction")
        self.assertEqual(self.latest()["line_items"], STORED,
                         "the filed note's row dropped the lines")


class NoLinesStaysNoLinesTest(_Base):
    """Regression guard, green before and after: a document with no lines gives
    a correction row with none, stored as NULL and never as an empty list."""

    def test_no_lines_in_gives_null_out(self):
        self.seed(line_items=None)
        self.resolve(good_corrections())
        self.assertIsNone(self.latest()["line_items"])


if __name__ == "__main__":
    unittest.main()

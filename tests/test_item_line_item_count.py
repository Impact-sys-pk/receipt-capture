"""Every published item says how many line items its extraction holds.

Paul's decision of 2026-11-14. `LINE_ITEM_COUNT_KEY` in `worker\\publish.py`,
written by `extra_for()` beside `vendor_key`, on both of its callers: the poll
in `process_extraction_result()` and the recovery sweep in `app.py`.

* A number, or `null` where the extraction holds none. Never `0`, because
  `worker\\line_items.py` already gives "no item lines" one representation,
  `None`, and the item should not invent a second.
* Taken from the extraction the publisher already has. The poll holds the
  `ExtractionResult` that produced the item; the sweep reads the stored row.
  Nothing is re-extracted and no image is read.
* On the review branch too, the receipts that are not `ok`. Those are the ones
  the count is most use on.
* A count only. The lines themselves are not published.
"""

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import live_paths  # noqa: E402,F401

from resolution_fixtures import TempEnvironment, extraction_result  # noqa: E402
from worker import publish  # noqa: E402
from worker.line_items import LineItem, to_json  # noqa: E402

from test_category_hold import drive, item_for, raw_item_text, receipts  # noqa: E402
from test_item_vendor_key import drive_with  # noqa: E402
from test_recovery_sweep_fallback import (  # noqa: E402
    RECEIPT as SWEPT,
    run_the_sweep,
    seed_unpublished_ok,
)

LINES = [LineItem(description="Parking 2h", amount=8.0),
         LineItem(description="Card fee", amount=0.5),
         LineItem(description="Unreadable line", amount=None)]


class TheConstantTest(unittest.TestCase):

    def test_the_name_and_its_value(self):
        self.assertEqual(publish.LINE_ITEM_COUNT_KEY, "line_item_count")

    def test_it_is_one_of_the_keys_the_item_adds(self):
        self.assertIn(publish.LINE_ITEM_COUNT_KEY, publish.ITEM_ONLY_KEYS)


class OnThePollTest(unittest.TestCase):

    def test_an_ok_receipt_carries_its_count(self):
        with TempEnvironment():
            drive_with(self, extraction_result(line_items=LINES))
            receipt, = receipts()
            self.assertEqual(receipt["status"], "ok")
            self.assertEqual(
                item_for(receipt["receipt_id"])[publish.LINE_ITEM_COUNT_KEY], 3)

    def test_a_receipt_for_review_carries_its_count(self):
        """The review branch, which categorises nothing."""
        for outcome, overrides in (("needs_review", dict(gross_amount=99.0)),
                                   ("failed", dict(gross_amount=None))):
            with self.subTest(outcome=outcome):
                with TempEnvironment():
                    drive_with(self, extraction_result(line_items=LINES[:2],
                                                       **overrides))
                    receipt, = receipts()
                    self.assertEqual(receipt["status"], outcome)
                    self.assertEqual(
                        item_for(receipt["receipt_id"])[publish.LINE_ITEM_COUNT_KEY],
                        2)

    def test_no_line_items_is_null_and_the_key_is_present(self):
        for outcome in ("ok", "needs_review", "failed"):
            with self.subTest(outcome=outcome):
                with TempEnvironment():
                    drive(self, outcome)
                    receipt, = receipts()
                    item = item_for(receipt["receipt_id"])
                    self.assertIn(publish.LINE_ITEM_COUNT_KEY, item)
                    self.assertIsNone(item[publish.LINE_ITEM_COUNT_KEY])

    def test_null_is_spelt_null_in_the_file(self):
        with TempEnvironment():
            drive(self, "ok")
            receipt, = receipts()
            text = raw_item_text(receipt["receipt_id"]).replace(": ", ":")
            self.assertIn(f'"{publish.LINE_ITEM_COUNT_KEY}":null', text)

    def test_the_lines_themselves_are_not_published(self):
        with TempEnvironment():
            drive_with(self, extraction_result(line_items=LINES))
            receipt, = receipts()
            text = raw_item_text(receipt["receipt_id"])
            self.assertNotIn('"line_items"', text)
            for line in LINES:
                self.assertNotIn(line.description, text)


class ThePollStoresWhatTheModelReadTest(unittest.TestCase):
    """Paul's decision of 2026-11-14. Step 10p added `extractions.line_items`
    on 2026-09-12 and no call to `save_extraction()` passed it, so the column
    was NULL on every row. This is the poll's call only; the other eight get
    their own brief."""

    def test_the_column_holds_the_lines_the_poll_read(self):
        from test_category_hold import extractions
        with TempEnvironment():
            drive_with(self, extraction_result(line_items=LINES))
            row, = extractions()
            self.assertEqual(row["line_items"], to_json(LINES))


class OnTheSweepTest(unittest.TestCase):
    """The second caller, which reads the extraction back out of the database."""

    def test_stored_lines_are_counted(self):
        with TempEnvironment() as env:
            seed_unpublished_ok(env, line_items=LINES[:2])
            run_the_sweep()
            self.assertEqual(item_for(SWEPT)[publish.LINE_ITEM_COUNT_KEY], 2)

    def test_no_stored_lines_is_null(self):
        with TempEnvironment() as env:
            seed_unpublished_ok(env)
            run_the_sweep()
            item = item_for(SWEPT)
            self.assertIn(publish.LINE_ITEM_COUNT_KEY, item)
            self.assertIsNone(item[publish.LINE_ITEM_COUNT_KEY])


class ExtraForTest(unittest.TestCase):

    def test_none_and_empty_are_null(self):
        self.assertIsNone(publish.extra_for([])[publish.LINE_ITEM_COUNT_KEY])
        self.assertIsNone(
            publish.extra_for([], line_items=[])[publish.LINE_ITEM_COUNT_KEY])

    def test_a_list_is_counted(self):
        self.assertEqual(
            publish.extra_for([], line_items=LINES)[publish.LINE_ITEM_COUNT_KEY], 3)

    def test_it_is_an_int_and_survives_json(self):
        extra = publish.extra_for([], line_items=LINES)
        self.assertIs(type(extra[publish.LINE_ITEM_COUNT_KEY]), int)
        self.assertEqual(json.loads(json.dumps(extra))[publish.LINE_ITEM_COUNT_KEY], 3)

    def test_the_stored_form_round_trips_to_the_same_count(self):
        """The sweep's route: the column as written, read back."""
        from worker.line_items import from_json
        self.assertEqual(
            publish.extra_for([], line_items=from_json(to_json(LINES)))
            [publish.LINE_ITEM_COUNT_KEY], 3)


if __name__ == "__main__":
    unittest.main()

"""The published item carries the receipt's vendor key.

Sub-step 10bs.10, second and last piece of its pipeline half. Amendment 555 of
`2026-07-25_CONSOLE_DESIGN.md` and `PROMPT_claude_code_2026-11-13_vendor_key_on_item.md`.

## Why

`b600b8a` publishes each client's taught supplier mappings, and each mapping
carries its `vendor_key`. IntelliBooks Desktop is to tell the operator, at the
`Remember this category for this supplier on this client` tick, which other
names sit on the same key. **It can only do that if the receipt in front of the
operator says which key it is on**, and until this change no item did. Paul's
decision, option A: the pipeline publishes the key the engine computed. Desktop
working it out for itself was refused, because that would put the key builder
in two products in two languages.

## The three states, and why the key is on every item

- **A string**: the key the engine computed for this receipt's supplier name.
- **`null`**: the pipeline says this receipt has no key. Either it was never
  categorised, which is every receipt that is not `ok`, or its supplier name
  normalised to nothing.
- **Absent**: an item written before this key existed. The pipeline does not
  know, and says nothing.

**`null` rather than absent for "no key"**, so a JavaScript reader can tell
"the pipeline says there is none" (`=== null`) from "this item predates the
question" (`=== undefined`), and both from "a key no mapping carries yet",
which is a string the mappings file does not contain. **An empty string is
never published**: `""` is falsy like `null` but is a string, and a reader
testing `typeof` would take it for a key. `extra_for()` turns one into `null`.
"""

import json
import sys
import types
import unittest

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402
from chart_fixtures import TempChartBundle  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    with_email_client,
)
from worker import publish  # noqa: E402
from worker.categorisation.engine import (  # noqa: E402
    CategorisationEngine,
    CategorisationResult,
)
from worker.database.repository import Repository  # noqa: E402

from test_category_hold import (  # noqa: E402
    CLIENT,
    NOW,
    categorisations,
    drive,
    item_for,
    raw_item_text,
    receipts,
)
from test_recovery_sweep_fallback import (  # noqa: E402
    RECEIPT as SWEPT,
    run_the_sweep,
    seed_unpublished_ok,
)

#: The fixture's supplier, `extraction_result()`'s default.
SUPPLIER = "Apcoa Parking"


def key_for(supplier):
    """What the engine computes, asked of the engine rather than written here.

    Writing the expected key out by hand is how `Euro Car Parks` was once
    expected to key on `euro car parks` when it keys on `euro`."""
    repo = Repository()
    try:
        return CategorisationEngine(repo=repo).vendor_key_for(supplier)
    finally:
        repo.close()


def drive_with(test_case, extraction):
    """`drive()` for an extraction `OUTCOMES` does not hold."""
    with_email_client(test_case, CLIENT)
    Routes(RecordingExtractor(extraction)).email_attachment()


def result(**overrides):
    values = dict(receipt_id="r", extraction_id="e", client_id=CLIENT,
                  business_type="UNSPECIFIED")
    values.update(overrides)
    return CategorisationResult(**values)


class TheConstantTest(unittest.TestCase):

    def test_the_name_and_its_value(self):
        """The reader is written against this, so its value is pinned."""
        self.assertEqual(publish.VENDOR_KEY_KEY, "vendor_key")

    def test_it_is_one_of_the_keys_the_item_adds(self):
        self.assertIn(publish.VENDOR_KEY_KEY, publish.ITEM_ONLY_KEYS)

    def test_it_is_spelt_as_the_mappings_file_spells_it(self):
        """Not required for the join, which is on values, but one word for one
        thing across the two files the reader opens costs nothing and stops a
        reader writing `item.vendor_key` against one and `m.vendorKey` against
        the other."""
        self.assertEqual(publish.VENDOR_KEY_KEY, config.MAPPING_VENDOR_KEY_FIELD)


class OnThePollTest(unittest.TestCase):

    def test_an_unmatched_ok_receipt_carries_its_key(self):
        """**The case the whole change exists for**: a name nobody has taught.
        No mappings at all, so the engine finds nothing, and the item still
        says which key the name is on."""
        with TempEnvironment():
            drive(self, "ok")
            receipt, = receipts()
            row, = categorisations()
            self.assertEqual(row["match_source"], "unmatched")
            expected = key_for(SUPPLIER)
            self.assertTrue(expected, "the fixture's supplier must have a key")
            self.assertEqual(item_for(receipt["receipt_id"])[publish.VENDOR_KEY_KEY],
                             expected)

    def test_a_matched_receipt_carries_the_same_key(self):
        """Layer 1, with a readable chart so the code stands."""
        with TempEnvironment(), TempChartBundle(accounts=(("7300", "Parking"),)):
            repo = Repository()
            try:
                repo.upsert_client_vendor(
                    CLIENT, key_for(SUPPLIER), "7300", "Parking", NOW,
                    vendor_name=SUPPLIER)
            finally:
                repo.close()
            drive(self, "ok")
            receipt, = receipts()
            row, = categorisations()
            self.assertEqual(row["match_source"], "client")
            self.assertEqual(item_for(receipt["receipt_id"])[publish.VENDOR_KEY_KEY],
                             key_for(SUPPLIER))

    def test_a_receipt_that_is_not_ok_carries_its_key_and_is_not_categorised(self):
        """**Paul's decision of 2026-11-13, flag 5.1 of
        `2026-11-13_REPORT_claude_code_vendor_key_on_item.md`.** ~~Never
        categorised, so no key, and the key is present to say so.~~ A receipt
        that arrived for review is the one the operator is most likely to be
        editing when the Remember tick is offered, so its item says which key
        its name is on. **It is still not categorised**: no `categorisations`
        row, and the item's category is still empty."""
        for outcome in ("needs_review", "failed"):
            with self.subTest(outcome=outcome):
                with TempEnvironment():
                    drive(self, outcome)
                    receipt, = receipts()
                    self.assertEqual(categorisations(), [],
                                     "nothing is categorised on this branch")
                    item = item_for(receipt["receipt_id"])
                    self.assertEqual(item[publish.VENDOR_KEY_KEY],
                                     key_for(SUPPLIER))
                    self.assertIsNone(item["category_code"])
                    self.assertIs(item[publish.CATEGORY_UNCONFIRMED_KEY], False)

    def test_a_receipt_with_no_supplier_name_carries_null(self):
        """No name, no key. The key is present to say so."""
        with TempEnvironment():
            drive_with(self, extraction_result(supplier_name=None))
            receipt, = receipts()
            self.assertNotEqual(receipt["status"], "ok")
            item = item_for(receipt["receipt_id"])
            self.assertIn(publish.VENDOR_KEY_KEY, item)
            self.assertIsNone(item[publish.VENDOR_KEY_KEY])

    def test_null_is_spelt_null_in_the_file(self):
        """The bytes, because the reader sees JSON and not a Python None."""
        with TempEnvironment():
            drive_with(self, extraction_result(supplier_name=None))
            receipt, = receipts()
            text = raw_item_text(receipt["receipt_id"]).replace(": ", ":")
            self.assertIn(f'"{publish.VENDOR_KEY_KEY}":null', text)


class OnTheSweepTest(unittest.TestCase):

    def test_a_receipt_recovered_by_the_sweep_carries_its_key(self):
        """The second of `extra_for()`'s two callers. The call-site guard in
        `tests/test_category_hold.py` proves both pass the categorisation; this
        proves the key arrives through the one that is not the poll."""
        with TempEnvironment() as env:
            seed_unpublished_ok(env)
            run_the_sweep()
            self.assertEqual(item_for(SWEPT)[publish.VENDOR_KEY_KEY],
                             key_for(SUPPLIER))


class ExtraForTest(unittest.TestCase):

    def test_no_categorisation_gives_null(self):
        extra = publish.extra_for([])
        self.assertIn(publish.VENDOR_KEY_KEY, extra)
        self.assertIsNone(extra[publish.VENDOR_KEY_KEY])

    def test_a_categorisation_with_no_key_gives_null(self):
        """`categorise()`'s two early returns, an empty name and a name that
        normalises to nothing, build a result with no key at all."""
        extra = publish.extra_for([], categorisation=result())
        self.assertIsNone(extra[publish.VENDOR_KEY_KEY])

    def test_an_empty_string_is_published_as_null(self):
        extra = publish.extra_for([], categorisation=result(vendor_key=""))
        self.assertIsNone(extra[publish.VENDOR_KEY_KEY])

    def test_the_key_is_passed_through_exactly(self):
        """No trimming and no case folding: the reader matches it against the
        mappings file, which publishes the stored key as stored."""
        extra = publish.extra_for([], categorisation=result(vendor_key="shell"))
        self.assertEqual(extra[publish.VENDOR_KEY_KEY], "shell")

    def test_nothing_else_moves(self):
        """The other keys `extra_for()` builds are what they were."""
        extra = publish.extra_for(["a note"], duplicate_of="r-0",
                                  categorisation=result(vendor_key="shell",
                                                        match_source="ai"))
        self.assertEqual(
            extra,
            {publish.NOTES_KEY: ["a note"],
             publish.CATEGORY_UNCONFIRMED_KEY: True,
             publish.DUPLICATE_OF_KEY: "r-0",
             publish.VENDOR_KEY_KEY: "shell",
             # Added 2026-11-14 with the key; no lines were passed.
             publish.LINE_ITEM_COUNT_KEY: None,
             # Added 2026-11-16 with item 55; nothing was referred.
             publish.CAPITAL_ITEM_KEY: None})

    def test_with_no_categorisation_the_key_passed_is_published(self):
        """The non-`ok` branch's route: a key worked out from the name, with
        nothing categorised."""
        extra = publish.extra_for([], vendor_key="apcoa parking")
        self.assertEqual(extra[publish.VENDOR_KEY_KEY], "apcoa parking")

    def test_an_empty_key_passed_is_published_as_null(self):
        extra = publish.extra_for([], vendor_key="")
        self.assertIsNone(extra[publish.VENDOR_KEY_KEY])

    def test_a_categorisation_and_a_key_together_are_refused(self):
        """One source per item. Two would let a caller publish a key the
        categorisation it also passed disagrees with."""
        with self.assertRaises(ValueError):
            publish.extra_for([], categorisation=result(vendor_key="shell"),
                              vendor_key="shell")

    def test_it_survives_json(self):
        extra = publish.extra_for([], categorisation=result(vendor_key="apcoa"))
        self.assertEqual(json.loads(json.dumps(extra))[publish.VENDOR_KEY_KEY],
                         "apcoa")


if __name__ == "__main__":
    unittest.main()

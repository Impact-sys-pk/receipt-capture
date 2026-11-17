r"""Layers 1 and 2 look up a supplier by name first. Sub-step 10bs.9.

Step 10bs of `2026-07-25_BUILD_STATUS.md`, amendment 548 of
`2026-07-25_CONSOLE_DESIGN.md`, brief
`PROMPT_claude_code_2026-11-13_vendor_lookup.md`.

## The defect

`upsert_client_vendor()` writes one row per `(client_id, vendor_key,
vendor_name)` and the table is unique on all three, but `get_client_vendor()`
read on `(client_id, vendor_key)` alone and took the most-seen row. So where one
key holds several names with different codes, whichever name had been taught
most often answered for all of them, at confidence `high` and `match_source`
`client`, which nothing holds for review. `get_firm_vendor()` had the same shape.

**Reachable on the live database on 2026-11-13**: `Client_007` holds three rows
on key `shell`, two at `7302 EV charging` and one at `7301 Fuel and oil`.

## Paul's rule, option C of three, 2026-11-13

1. An exact `vendor_name` match wins.
2. With no exact row, fall back to the key only where every variant for that
   key carries the same nominal code.
3. Variants disagreeing on the code means no answer from this layer.

## The name the lookup is given

`categorise()`'s own `supplier_name`, unchanged. Every teaching route writes
`vendor_name=merged["supplier_name"]` and derives the key from that same string,
so the taught name and the name the next receipt arrives with are one string by
construction. Checked against the live database the same day: every one of the
16 `categorisations_client_vendors` names equals at least one stored
`extractions.supplier_name` for the same client, byte for byte.

## Layer 3 and the mapping this refuses, recorded rather than designed around

`LayerThreeHandsBackTheRefusedMappingTest` pins what happens next to a name the
layers above refused. It is a FINDING for Paul, not a design: the fuzzy layer
matches on the key, the key is unchanged, so it finds the same key at a score of
1.0 and returns the most-seen variant as `fuzzy_client` at `medium`.
`category_is_unconfirmed()` in `worker\publish.py` holds that as unconfirmed, so
the receipt is held rather than landing silently. If Paul decides otherwise,
that test is the one to change.
"""

import unittest

from resolution_fixtures import TempEnvironment
from worker.categorisation.engine import (
    CategorisationEngine,
    extract_vendor_key,
    normalise_description,
)
from worker.database.repository import Repository

CLIENT = "CLIENT001"
SECTOR = "UNSPECIFIED"
WHEN = "2026-11-13T12:00:00+00:00"
LATER = "2026-11-13T13:00:00+00:00"

# Three names that collapse to one key, and the codes Client_007 holds for them.
SHELL_EV_LONG = "Shell U.K. Oil Products Limited on behalf of Shell UK Limited"
SHELL_EV = "Shell U.K. Oil Products Limited"
SHELL_FUEL = "Shell Co-op Harborne"
SHELL_UNSEEN = "Shell Forecourt Bromley Common"
EV = ("7302", "EV charging")
FUEL = ("7301", "Fuel and oil")


def key_of(name):
    return extract_vendor_key(normalise_description(name))


class TheNamesCollapseTest(unittest.TestCase):
    """The premise. If these stopped sharing a key, nothing below would test the defect."""

    def test_all_four_names_share_the_key_shell(self):
        for name in (SHELL_EV_LONG, SHELL_EV, SHELL_FUEL, SHELL_UNSEEN):
            with self.subTest(name=name):
                self.assertEqual(key_of(name), "shell")


class _Base(unittest.TestCase):
    def setUp(self):
        self.env = TempEnvironment()
        self.env.__enter__()
        self.repo = Repository()

    def tearDown(self):
        self.repo.close()
        self.env.__exit__(None, None, None)

    def teach_client(self, name, code, times=1, when=WHEN):
        for _ in range(times):
            self.repo.upsert_client_vendor(
                client_id=CLIENT, vendor_key=key_of(name),
                nominal_code=code[0], account_name=code[1],
                last_updated=when, vendor_name=name)

    def teach_firm(self, name, code, times=1, when=WHEN):
        for _ in range(times):
            self.repo.upsert_firm_vendor(
                sector=SECTOR, vendor_key=key_of(name),
                nominal_code=code[0], account_name=code[1],
                last_updated=when, vendor_name=name, firm_id="TESTFIRM001")

    def categorise(self, name):
        return CategorisationEngine(repo=self.repo, enable_ai_fallback=False).categorise(
            receipt_id="r-1", extraction_id="e-1", supplier_name=name,
            client_id=CLIENT, sector=SECTOR)


class ClientLookupTest(_Base):
    """Layer 1, driven through categorise() so the name it is given is the real one."""

    def test_one_key_one_name_answers_as_before(self):
        self.teach_client(SHELL_EV, EV)
        result = self.categorise(SHELL_EV)
        self.assertEqual((result.match_source, result.suggested_code, result.confidence),
                         ("client", "7302", "high"))

    def test_one_name_answers_for_an_unseen_name_on_the_same_key(self):
        """One variant agrees with itself, so the key level fallback stands."""
        self.teach_client(SHELL_EV, EV)
        result = self.categorise(SHELL_UNSEEN)
        self.assertEqual((result.match_source, result.suggested_code), ("client", "7302"))

    def test_several_names_agreeing_still_answer_by_key(self):
        self.teach_client(SHELL_EV, EV, times=2)
        self.teach_client(SHELL_EV_LONG, EV)
        result = self.categorise(SHELL_UNSEEN)
        self.assertEqual((result.match_source, result.suggested_code), ("client", "7302"))

    def test_disagreeing_names_each_answer_with_their_own_code(self):
        """The live shape. The fuel name is taught LESS often, so the old lookup
        answered it with EV charging."""
        self.teach_client(SHELL_EV_LONG, EV, times=3, when=LATER)
        self.teach_client(SHELL_EV, EV, times=2)
        self.teach_client(SHELL_FUEL, FUEL, times=1)
        for name, code in ((SHELL_FUEL, "7301"), (SHELL_EV, "7302"),
                           (SHELL_EV_LONG, "7302")):
            with self.subTest(name=name):
                result = self.categorise(name)
                self.assertEqual((result.match_source, result.suggested_code),
                                 ("client", code))

    def test_disagreeing_names_give_an_unseen_name_nothing_from_layer_one(self):
        self.teach_client(SHELL_EV_LONG, EV, times=3)
        self.teach_client(SHELL_FUEL, FUEL, times=1)
        self.assertIsNone(self.repo.get_client_vendor(CLIENT, "shell", SHELL_UNSEEN))
        result = self.categorise(SHELL_UNSEEN)
        self.assertNotEqual(result.match_source, "client")

    def test_the_mapping_id_is_the_matched_names_row(self):
        """Not just the code: the row id must be the variant that matched."""
        self.teach_client(SHELL_EV_LONG, EV, times=3)
        self.teach_client(SHELL_FUEL, FUEL)
        fuel_row = self.repo._conn.execute(
            "SELECT mapping_id FROM categorisations_client_vendors WHERE vendor_name = ?",
            (SHELL_FUEL,)).fetchone()[0]
        self.assertEqual(self.categorise(SHELL_FUEL).mapping_id, fuel_row)

    def test_another_clients_rows_are_not_consulted(self):
        self.repo.upsert_client_vendor(
            client_id="CLIENT002", vendor_key="shell", nominal_code=FUEL[0],
            account_name=FUEL[1], last_updated=WHEN, vendor_name=SHELL_FUEL)
        self.teach_client(SHELL_EV, EV)
        self.assertEqual(self.repo.get_client_vendor(CLIENT, "shell", SHELL_UNSEEN)["nominal_code"],
                         "7302")


class FirmLookupTest(_Base):
    """Layer 2, the same four cases. The client table is empty throughout."""

    def assert_client_table_empty(self):
        self.assertEqual(self.repo._conn.execute(
            "SELECT COUNT(*) FROM categorisations_client_vendors").fetchone()[0], 0)

    def test_one_key_one_name_answers_as_before(self):
        self.teach_firm(SHELL_EV, EV)
        self.assert_client_table_empty()
        result = self.categorise(SHELL_EV)
        self.assertEqual((result.match_source, result.suggested_code, result.confidence),
                         ("firm", "7302", "high"))

    def test_several_names_agreeing_still_answer_by_key(self):
        self.teach_firm(SHELL_EV, EV, times=2)
        self.teach_firm(SHELL_EV_LONG, EV)
        result = self.categorise(SHELL_UNSEEN)
        self.assertEqual((result.match_source, result.suggested_code), ("firm", "7302"))

    def test_disagreeing_names_each_answer_with_their_own_code(self):
        self.teach_firm(SHELL_EV_LONG, EV, times=3, when=LATER)
        self.teach_firm(SHELL_FUEL, FUEL)
        for name, code in ((SHELL_FUEL, "7301"), (SHELL_EV_LONG, "7302")):
            with self.subTest(name=name):
                result = self.categorise(name)
                self.assertEqual((result.match_source, result.suggested_code),
                                 ("firm", code))

    def test_disagreeing_names_give_an_unseen_name_nothing_from_layer_two(self):
        self.teach_firm(SHELL_EV_LONG, EV, times=3)
        self.teach_firm(SHELL_FUEL, FUEL)
        self.assertIsNone(self.repo.get_firm_vendor(SECTOR, "shell", SHELL_UNSEEN))
        self.assertNotEqual(self.categorise(SHELL_UNSEEN).match_source, "firm")


class MatchedVendorIsTheVariantThatAnsweredTest(_Base):
    """Paul's decision of 2026-11-14, amendment 557.

    `matched_vendor` recorded the key at layers 1 and 2, so the two live Shell
    receipts both read `shell` and the audit row could not say which of three
    taught names decided the code. Since 10bs.9 that name is what decides it.
    """

    def test_layer_one_by_name_records_that_name(self):
        self.teach_client(SHELL_EV_LONG, EV, times=3)
        self.teach_client(SHELL_FUEL, FUEL)
        for name in (SHELL_FUEL, SHELL_EV_LONG):
            with self.subTest(name=name):
                self.assertEqual(self.categorise(name).matched_vendor, name)

    def test_layer_one_by_key_records_the_variant_not_the_receipts_name(self):
        """The key-only answer: every variant agrees, and the most-seen one
        is the row that answered, so its name is recorded."""
        self.teach_client(SHELL_EV, EV, times=2)
        self.teach_client(SHELL_EV_LONG, EV)
        result = self.categorise(SHELL_UNSEEN)
        self.assertEqual(result.match_source, "client")
        self.assertEqual(result.matched_vendor, SHELL_EV)

    def test_layer_two_records_the_variant(self):
        self.teach_firm(SHELL_EV_LONG, EV, times=3)
        self.teach_firm(SHELL_FUEL, FUEL)
        result = self.categorise(SHELL_FUEL)
        self.assertEqual((result.match_source, result.matched_vendor),
                         ("firm", SHELL_FUEL))

    def test_the_key_is_still_on_the_result(self):
        self.teach_client(SHELL_FUEL, FUEL)
        self.assertEqual(self.categorise(SHELL_FUEL).vendor_key, "shell")

    # Layers 3 and 4, Paul's decision of 2026-11-14, amendment 558, so the
    # field means one thing at every layer. They recorded the matched KEY,
    # while the most-seen variant on that key supplied the code.

    def test_layer_three_records_the_variant_not_the_matched_key(self):
        self.teach_client(SHELL_EV_LONG, EV, times=3)
        self.teach_client(SHELL_FUEL, FUEL)
        result = self.categorise(SHELL_UNSEEN)
        self.assertEqual(result.match_source, "fuzzy_client")
        self.assertEqual(result.matched_vendor, SHELL_EV_LONG)

    def test_layer_five_records_nothing(self):
        """No variant answered at the AI layer, so it records what the
        unmatched branch records. Paul's decision of 2026-11-14. The model is
        stubbed: no real call."""
        engine = CategorisationEngine(repo=self.repo, enable_ai_fallback=True)
        engine._ai_suggest = lambda *a, **k: {"code": "7500", "name": "Sundries"}
        result = engine.categorise(
            receipt_id="r-1", extraction_id="e-1", supplier_name=SHELL_UNSEEN,
            client_id=CLIENT, sector=SECTOR)
        self.assertEqual(result.match_source, "ai")
        self.assertIsNone(result.matched_vendor)
        self.assertEqual(result.vendor_key, "shell", "the key is still on the result")

    def test_layer_four_records_the_variant_not_the_matched_key(self):
        self.teach_firm(SHELL_EV_LONG, EV, times=3)
        self.teach_firm(SHELL_FUEL, FUEL)
        result = self.categorise(SHELL_UNSEEN)
        self.assertEqual(result.match_source, "fuzzy_firm")
        self.assertEqual(result.matched_vendor, SHELL_EV_LONG)


class LayerThreeHandsBackTheRefusedMappingTest(_Base):
    """A FINDING for Paul, pinned so a change to it is deliberate. See the module docstring."""

    def test_client_fuzzy_layer_returns_the_most_seen_variant(self):
        self.teach_client(SHELL_EV_LONG, EV, times=3)
        self.teach_client(SHELL_FUEL, FUEL)
        result = self.categorise(SHELL_UNSEEN)
        self.assertEqual(
            (result.match_source, result.suggested_code, result.confidence,
             result.needs_review),
            ("fuzzy_client", "7302", "medium", True))

    def test_firm_fuzzy_layer_does_the_same(self):
        self.teach_firm(SHELL_EV_LONG, EV, times=3)
        self.teach_firm(SHELL_FUEL, FUEL)
        result = self.categorise(SHELL_UNSEEN)
        self.assertEqual((result.match_source, result.suggested_code, result.confidence),
                         ("fuzzy_firm", "7302", "medium"))


if __name__ == "__main__":
    unittest.main()

r"""What a LAYER 2 match stores. Part A of step 10m, and it comes before the writer.

Step 10m of `2026-07-25_CONSOLE_DESIGN.md`, amendment 238, from
`PROMPT_claude_code_2026-09-12_firm_vendor_table.md`.

## The reason this exists, and it is measured rather than asserted

**No test had ever checked what a matched row stores at layer 2**, because every
`categorisations` row that has ever existed on this project reads `unmatched`.
Step 10k closed the same hole at layer 1, in
`tests/test_corrected_note.py::WhatACorrectedRowStoresTest`, after a mutation
swapping `mapping_id` and `matched_vendor` at layer 1 left the whole suite
green.

**The identical swap at layer 2 was still live on 2026-09-12.** Run through
`tests/mutation_harness.py` against the suite as it then stood: **1294 passed, 1
skipped, 904 subtests, and nothing caught it.** That measurement is what this
file was written from, and it is quoted in
`2026-09-12_REPORT_claude_code_firm_vendor_table.md`.

## Why it is a separate file rather than more of `test_corrected_note.py`

That file is step 10k's and its docstring says in terms that the layer 2 swap is
step 10m's, not its. **The fixture is reused rather than rebuilt**, because "the
same shape as the layer 1 assertions" is the brief's requirement and a
second fixture would differ from it in ways nobody chose.

## What makes the receipt reach layer 2 rather than layer 1

**Only the firm table is seeded.** Layer 1 is an exact match in this client's own
mappings and runs first, so a client mapping would answer and layer 2 would
never be reached. `seed_only_the_firm_table()` below asserts the client table is
empty afterwards, because a test that silently matched at layer 1 would assert
everything here except `match_source` and would still pass four of its five
assertions.

`business_type` is `UNSPECIFIED`, which is the `trade` on the fixture's
`CLIENT001` record and what `_client_details()` hands `categorise()`.
"""

import unittest

import config

from resolution_fixtures import rows
from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository

from test_corrected_note import (
    ALSO_IN_CHART,
    IN_CHART,
    SUPPLIER,
    VENDOR_KEY,
    CorrectedNoteTestCase,
    corrected_note,
    values_with,
)

#: The `trade` on the fixture's client record, which `_client_details()` returns
#: and `categorise()` receives as `business_type`. Read from the fixture rather
#: than written as a literal twice.
BUSINESS_TYPE = "UNSPECIFIED"


class LayerTwoTestCase(CorrectedNoteTestCase):
    """The step 10k fixture, with the firm table seeded instead of the client's."""

    def seed_only_the_firm_table(self, code=IN_CHART[0], name=IN_CHART[1],
                                 business_type=BUSINESS_TYPE):
        """A mapping layer 2 will match, and nothing layer 1 can answer with.

        Returns the row, so a test can compare `mapping_id` against the real row
        id rather than against a value it made up.
        """
        repo = Repository()
        try:
            repo.upsert_firm_vendor(
                business_type=business_type, vendor_key=VENDOR_KEY,
                nominal_code=code, account_name=name,
                last_updated="2026-09-01T00:00:00+00:00",
                vendor_name=SUPPLIER, firm_id="INTELLITAX")
            firm = rows(repo, "SELECT * FROM categorisations_firm_vendors")
            client = rows(repo, "SELECT * FROM categorisations_client_vendors")
        finally:
            repo.close()
        self.assertEqual(len(firm), 1, "one firm mapping seeded")
        self.assertEqual(
            client, [],
            "the client table must be empty, or layer 1 answers and this test "
            "never reaches layer 2 while still passing most of its assertions")
        return firm[0]

    def firm_vendors(self):
        return self.table("SELECT * FROM categorisations_firm_vendors")

    def client_vendors(self):
        return self.table("SELECT * FROM categorisations_client_vendors")


class WhatALayerTwoRowStoresTest(LayerTwoTestCase):
    """Every column of the `categorisations` row a layer 2 match writes.

    The mirror of `WhatACorrectedRowStoresTest`, one seed different.
    """

    def test_the_row_records_the_firm_mapping_and_the_persons_choice(self):
        self.seed_filed()
        mapping = self.seed_only_the_firm_table()
        self.assertEqual(self.categorisations(), [],
                         "the control: no categorisation row yet")

        self.write_note(corrected_note(
            values=values_with(category_code=ALSO_IN_CHART[0],
                               category_name=ALSO_IN_CHART[1])))
        self.poll()

        written = self.categorisations()
        self.assertEqual(len(written), 1, "one row per correction")
        row = written[0]

        # What the ENGINE found. `firm` and not `client`: this is the whole
        # reason the file exists, and it is asserted first because every other
        # assertion below is also true of a layer 1 row.
        self.assertEqual(row["match_source"], "firm")
        self.assertEqual(row["confidence"], "high")
        self.assertEqual(row["suggested_code"], IN_CHART[0],
                         "suggested_code holds the firm mapping's nominal_code")
        self.assertEqual(row["suggested_name"], IN_CHART[1],
                         "suggested_name holds the firm mapping's account_name")
        self.assertEqual(row["needs_review"], 0)

        # **The two fields the layer 1 mutation swapped, and the swap at layer 2
        # was still live until this line.** `mapping_id` is the row id of the
        # firm mapping that answered; `matched_vendor` is the normalised key
        # layer 2 looked up. Swapping them leaves both populated and every
        # other assertion in this test true.
        self.assertEqual(row["mapping_id"], mapping["mapping_id"],
                         "mapping_id is the row id of the firm mapping that answered")
        self.assertEqual(row["matched_vendor"], VENDOR_KEY,
                         "matched_vendor is the normalised key, not a row id")
        self.assertNotEqual(row["mapping_id"], row["matched_vendor"])

        # What the PERSON chose, beside the suggestion and never over it.
        self.assertEqual(row["correction_code"], ALSO_IN_CHART[0])
        self.assertEqual(row["correction_name"], ALSO_IN_CHART[1])
        self.assertIsNotNone(row["corrected_at"])

        # And the row belongs to the receipt and the client it was written for.
        self.assertEqual(row["receipt_id"], "r-1")
        self.assertEqual(row["client_id"], "CLIENT001")
        self.assertEqual(row["trade"], BUSINESS_TYPE)


class TheEngineAnswersFromTheFirmPoolTest(LayerTwoTestCase):
    """Layer 2 driven directly, without a note.

    The test above goes through a real poll, which is what proves the stored
    row. This drives `categorise()` itself, so a failure says whether the engine
    or the write is at fault rather than leaving that to be worked out.
    """

    def _categorise(self, business_type=BUSINESS_TYPE, client_id="CLIENT001"):
        repo = Repository()
        try:
            engine = CategorisationEngine(repo=repo, enable_ai_fallback=False)
            return engine.categorise(
                receipt_id="r-1", extraction_id="e-1", supplier_name=SUPPLIER,
                client_id=client_id, business_type=business_type)
        finally:
            repo.close()

    def test_it_returns_the_firm_mapping_row_id_and_the_normalised_key(self):
        mapping = self.seed_only_the_firm_table()
        result = self._categorise()
        self.assertEqual(result.match_source, "firm")
        self.assertEqual(result.mapping_id, mapping["mapping_id"])
        self.assertEqual(result.matched_vendor, VENDOR_KEY)
        self.assertEqual(result.vendor_key, VENDOR_KEY)
        self.assertNotEqual(result.mapping_id, result.matched_vendor)
        self.assertEqual(result.suggested_code, IN_CHART[0])
        self.assertEqual(result.suggested_name, IN_CHART[1])
        self.assertEqual(result.confidence, "high")
        self.assertFalse(result.needs_review)

    def test_a_client_mapping_wins_over_the_firm_pool(self):
        """Layer 1 runs first, and this is what proves the test above reaches
        layer 2 rather than layer 1 by luck."""
        self.seed_only_the_firm_table()
        self.learn(code=ALSO_IN_CHART[0], name=ALSO_IN_CHART[1])
        result = self._categorise()
        self.assertEqual(result.match_source, "client")
        self.assertEqual(result.suggested_code, ALSO_IN_CHART[0])

    def test_another_business_type_does_not_see_this_pool(self):
        """The firm pool is keyed on `business_type`, so a client of another
        trade must not match. This is the cross-client reach that makes the
        table worth having and makes a wrong row in it worse than a wrong row
        in the client table."""
        self.seed_only_the_firm_table()
        result = self._categorise(business_type="PHV_DRIVER")
        self.assertNotEqual(result.match_source, "firm")


class ACorrectionDoesNotTouchTheFirmTableTest(LayerTwoTestCase):
    """Paul's decision of 2026-09-05, amendment 231, still standing.

    A Desktop correction writes the client table only. Amendment 238 opens one
    exception to that and it cannot arise here: it needs a classifier answer to
    confirm, and this receipt was answered by layer 2 out of the firm pool.

    **This is the control for part B.** If part B ever widens the rule, this
    test is what goes red.
    """

    def test_a_ticked_correction_on_a_layer_two_match_writes_the_client_table_only(self):
        self.seed_filed()
        before = self.seed_only_the_firm_table()

        self.write_note(corrected_note(
            values=values_with(category_code=ALSO_IN_CHART[0],
                               category_name=ALSO_IN_CHART[1]),
            remember_gl_for_supplier=True))
        self.poll()

        learned = self.client_vendors()
        self.assertEqual(len(learned), 1,
                         "the tick teaches the client table")
        self.assertEqual(learned[0]["nominal_code"], ALSO_IN_CHART[0])

        firm = self.firm_vendors()
        self.assertEqual(len(firm), 1, "no new firm row")
        self.assertEqual(
            firm[0]["nominal_code"], before["nominal_code"],
            "the firm mapping the engine matched must not be rewritten by a "
            "correction. Amendment 231: a Desktop correction writes the client "
            "table only, and amendment 238's exception needs a classifier "
            "answer, which a layer 2 match is not")
        self.assertEqual(firm[0]["mapping_id"], before["mapping_id"])

    def test_an_unticked_correction_teaches_neither_table(self):
        """Section 11.3: learning is opt-in. A correction with no tick teaches
        neither table, and that is the half of the rule most easily lost."""
        self.seed_filed()
        before = self.seed_only_the_firm_table()

        self.write_note(corrected_note(
            values=values_with(category_code=ALSO_IN_CHART[0],
                               category_name=ALSO_IN_CHART[1])))
        self.poll()

        self.assertEqual(self.client_vendors(), [],
                         "no tick, so the client table is untouched")
        firm = self.firm_vendors()
        self.assertEqual(len(firm), 1)
        self.assertEqual(firm[0]["mapping_id"], before["mapping_id"])
        self.assertEqual(firm[0]["nominal_code"], before["nominal_code"])


class TheFirmTableHasNoProductionWriterTest(unittest.TestCase):
    r"""The premise step 10m rests on, enumerated rather than believed.

    `upsert_firm_vendor()` and `increment_firm_vendor_count()` are the only two
    functions in the production tree that write `categorisations_firm_vendors`,
    and on 2026-09-12 neither had a single caller anywhere in production.

    **This test is expected to change when part B lands**, and that is the
    point: it names the moment the firm table stops being unreachable, so the
    change cannot happen silently.
    """

    import ast as _ast
    from pathlib import Path as _Path

    WRITERS = ("upsert_firm_vendor", "increment_firm_vendor_count")

    def production_files(self):
        import source_guards
        root = self._Path(source_guards.REPO_ROOT)
        # `.history\` is excluded by construction: the root glob is not
        # recursive and the worker glob is rooted inside `worker\`.
        return sorted(root.glob("*.py")) + sorted(root.glob("worker/**/*.py"))

    def callers_of(self, name):
        found = []
        for path in self.production_files():
            tree = self._ast.parse(path.read_text(encoding="utf-8"),
                                   filename=str(path))
            for node in self._ast.walk(tree):
                if not isinstance(node, self._ast.Call):
                    continue
                func = node.func
                called = (func.attr if isinstance(func, self._ast.Attribute)
                          else func.id if isinstance(func, self._ast.Name)
                          else None)
                if called == name:
                    found.append(f"{path.name}:{node.lineno}")
        return sorted(found)

    def test_increment_firm_vendor_count_has_no_caller(self):
        """It bumps `times_seen` on a row that already exists, so it can never
        create one. It has been uncalled since it was written."""
        self.assertEqual(self.callers_of("increment_firm_vendor_count"), [])

    def test_the_writers_are_the_only_two(self):
        """Read off the source: no third function writes this table.

        Asserted as a SET rather than by checking the two known ones, because a
        third writer added elsewhere is exactly what this would otherwise miss.
        `CLAUDE.md`, 2026-09-08.
        """
        import re
        import source_guards
        pattern = re.compile(
            r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|REPLACE\s+INTO)\s+"
            r"categorisations_firm_vendors\b", re.IGNORECASE)
        writers = set()
        for path in self.production_files():
            tree = self._ast.parse(path.read_text(encoding="utf-8"),
                                   filename=str(path))
            owners = {}

            def walk(node, stack):
                for child in self._ast.iter_child_nodes(node):
                    chain = stack
                    if isinstance(child, (self._ast.FunctionDef,
                                          self._ast.AsyncFunctionDef,
                                          self._ast.ClassDef)):
                        chain = stack + [child.name]
                    owners[id(child)] = chain
                    walk(child, chain)
            walk(tree, [])
            skip = set()
            for node in self._ast.walk(tree):
                if isinstance(node, (self._ast.Module, self._ast.FunctionDef,
                                     self._ast.AsyncFunctionDef,
                                     self._ast.ClassDef)) and node.body:
                    first = node.body[0]
                    if (isinstance(first, self._ast.Expr)
                            and isinstance(first.value, self._ast.Constant)
                            and isinstance(first.value.value, str)):
                        skip.add(id(first.value))
            for node in self._ast.walk(tree):
                if (isinstance(node, self._ast.Constant)
                        and isinstance(node.value, str)
                        and id(node) not in skip
                        and pattern.search(node.value)):
                    chain = owners.get(id(node), [])
                    writers.add(chain[-1] if chain else "<module>")
        self.assertEqual(
            writers, set(self.WRITERS),
            "the set of functions writing categorisations_firm_vendors has "
            f"changed. Found: {sorted(writers)}")


if __name__ == "__main__":
    unittest.main()

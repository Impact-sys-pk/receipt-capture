r"""Part B of step 10m: the firm vendor table gets a writer.

Step 10m of `2026-07-25_CONSOLE_DESIGN.md`, amendment 238, from
`PROMPT_claude_code_2026-09-12_firm_vendor_table.md`. Part A is
`tests/test_layer_two_row.py` and comes first.

## The rule, which is Paul's

The operator's chosen code is compared with the code the chart check resolved
the classifier's suggestion to.

- **Equal**: both tables are written. The client table with the operator's code,
  the firm table with **the account out of the shipped receipt-account list that
  the classifier named**, keyed on business type and vendor key.
- **Different**: the client table only. Several master codes collapse into one
  under the chart fallback, so the operator's pick cannot be run backwards to a
  receipt account.
- **The tick governs both.** A correction with no tick teaches neither.
- **The confirm case arises only on a classifier answer.**

## Why the evidence here is tests and not a live run

**The classifier is off.** `app.py` builds its engine with
`enable_ai_fallback=False`, and so does every other production construction site
bar the two probe scripts. So `match_source` can never read `ai` on this
machine, **no row will ever appear in `categorisations_firm_vendors` until Paul
turns the classifier on**, and that is expected rather than a shortfall. It is
stated here so nobody reads an empty table as a broken writer.

## Two routes, one rule

**Paul's decision, 2026-09-12.** There are two learning sites and their guards
differ. Both call one helper, so the rule cannot be live on one route and absent
from the other. `BothRoutesTest` is what holds that, and
`OneCallerTest` holds that no third route reaches the table without going
through the rule.
"""

import ast
import unittest
from pathlib import Path
from unittest import mock

import config

from chart_fixtures import TempChartBundle
from resolution_fixtures import rows
from worker.categorisation.engine import CategorisationResult
from worker.categorisation.fallback import resolve_against_chart
from worker.database.repository import Repository
from worker.resolution import service

import source_guards

from test_corrected_note import (
    ALSO_IN_CHART,
    FILED_RELATIVE,
    IN_CHART,
    SUPPLIER,
    VENDOR_KEY,
    CorrectedNoteTestCase,
    corrected_note,
    values_with,
)

BUSINESS_TYPE = "UNSPECIFIED"

#: An account the classifier may name that is NOT in this client's chart, with a
#: fallback that is. The substitution case, which is where the firm table must
#: learn the account the classifier named and not the one the client got.
NOT_IN_CHART = ("7391", "Car wash")


def ai_result(code, name, client_id="CLIENT001", business_type=BUSINESS_TYPE):
    """What layer 5 returns, in the shape `categorise()` builds it.

    Built here rather than by calling the engine with the fallback enabled,
    because enabling it would make a real OpenAI call. The fields are copied
    from the layer 5 branch of `categorise()` and
    `test_the_shape_matches_what_layer_five_builds` asserts they still match it.
    """
    return CategorisationResult(
        receipt_id="r-1", extraction_id="e-1",
        client_id=client_id, business_type=business_type,
        vendor_key=VENDOR_KEY, suggested_code=code, suggested_name=name,
        confidence="low", match_source="ai",
        matched_vendor=VENDOR_KEY, needs_review=True,
    )


class TheRuleTest(CorrectedNoteTestCase):
    """`_learn_firm_mapping_if_confirmed()` driven directly over its cases.

    The chart check is run for real on the way in, rather than the
    `chart_outcome` being set by hand, because which outcome a given code
    produces is exactly the thing a hand-set field would stop testing.
    """

    def decide(self, *, classifier_code, classifier_name, chosen_code,
               business_type=BUSINESS_TYPE):
        repo = Repository()
        try:
            result = ai_result(classifier_code, classifier_name,
                               business_type=business_type)
            resolve_against_chart(result, repo=repo)
            taught = service._learn_firm_mapping_if_confirmed(
                repo, {"firm_id": "INTELLITAX", "client_id": "CLIENT001"},
                result, chosen_code=chosen_code,
                vendor_key=VENDOR_KEY, vendor_name=SUPPLIER)
            firm = rows(repo, "SELECT * FROM categorisations_firm_vendors")
        finally:
            repo.close()
        return taught, firm, result

    def test_equal_codes_write_the_firm_table(self):
        taught, firm, result = self.decide(
            classifier_code=IN_CHART[0], classifier_name=IN_CHART[1],
            chosen_code=IN_CHART[0])
        self.assertEqual(result.chart_outcome, "in_chart")
        self.assertEqual(taught, (IN_CHART[0], IN_CHART[1]))
        self.assertEqual(len(firm), 1)
        self.assertEqual(firm[0]["nominal_code"], IN_CHART[0])
        self.assertEqual(firm[0]["account_name"], IN_CHART[1])
        self.assertEqual(firm[0]["business_type"], BUSINESS_TYPE)
        self.assertEqual(firm[0]["vendor_key"], VENDOR_KEY)
        self.assertEqual(firm[0]["vendor_name"], SUPPLIER)
        self.assertEqual(firm[0]["firm_id"], "INTELLITAX")
        self.assertEqual(firm[0]["times_seen"], 1)

    def test_different_codes_write_nothing(self):
        taught, firm, _ = self.decide(
            classifier_code=IN_CHART[0], classifier_name=IN_CHART[1],
            chosen_code=ALSO_IN_CHART[0])
        self.assertIsNone(taught)
        self.assertEqual(firm, [])

    def test_only_a_classifier_answer_can_confirm(self):
        """A layer 1 or layer 2 match returns a stored code and there is no
        suggestion out of the shipped list to agree with."""
        for source in ("client", "firm", "rule", "fuzzy_client", "fuzzy_firm",
                       "unmatched"):
            with self.subTest(match_source=source):
                repo = Repository()
                try:
                    result = ai_result(IN_CHART[0], IN_CHART[1])
                    result.match_source = source
                    resolve_against_chart(result, repo=repo)
                    taught = service._learn_firm_mapping_if_confirmed(
                        repo, {"firm_id": "INTELLITAX"}, result,
                        chosen_code=IN_CHART[0], vendor_key=VENDOR_KEY,
                        vendor_name=SUPPLIER)
                    firm = rows(repo,
                                "SELECT * FROM categorisations_firm_vendors")
                finally:
                    repo.close()
                self.assertIsNone(taught)
                self.assertEqual(firm, [])

    def test_a_missing_code_confirms_nothing(self):
        taught, firm, _ = self.decide(
            classifier_code=IN_CHART[0], classifier_name=IN_CHART[1],
            chosen_code=None)
        self.assertIsNone(taught)
        self.assertEqual(firm, [])


class TheSubstitutionTest(CorrectedNoteTestCase):
    """The firm table learns the account the CLASSIFIER named.

    **This is the case the rule turns on and the one most easily got wrong.**
    The classifier names an account the client's chart does not hold, the
    fallback table substitutes one the client does hold, and the operator
    accepts it. The client gets the fallback; the firm pool must get the
    account the classifier named, because the pool is shared across a trade and
    the fallback is this client's chart's business.
    """

    def setUp(self):
        super().setUp()
        # Re-enter the chart with a fallback: 7391 is not in this client's
        # chart and 7304 is, so the classifier's 7391 is substituted to 7304.
        self.chart.__exit__(None, None, None)
        self.chart = TempChartBundle(
            accounts=(IN_CHART, ALSO_IN_CHART),
            fallbacks=((NOT_IN_CHART[0], IN_CHART[0]),)).__enter__()
        self.addCleanup(self.chart.__exit__, None, None, None)

    def test_the_firm_pool_learns_the_classifiers_account_not_the_fallback(self):
        repo = Repository()
        try:
            result = ai_result(NOT_IN_CHART[0], NOT_IN_CHART[1])
            resolve_against_chart(result, repo=repo)
            self.assertEqual(result.chart_outcome, "substituted")
            self.assertEqual(result.suggested_code, IN_CHART[0],
                             "the client gets the fallback")
            self.assertEqual(result.original_code, NOT_IN_CHART[0],
                             "and the classifier's account is kept beside it")

            # The operator accepts what is on screen, which is the fallback.
            taught = service._learn_firm_mapping_if_confirmed(
                repo, {"firm_id": "INTELLITAX"}, result,
                chosen_code=IN_CHART[0], vendor_key=VENDOR_KEY,
                vendor_name=SUPPLIER)
            firm = rows(repo, "SELECT * FROM categorisations_firm_vendors")
        finally:
            repo.close()

        self.assertEqual(taught, NOT_IN_CHART)
        self.assertEqual(len(firm), 1)
        self.assertEqual(
            firm[0]["nominal_code"], NOT_IN_CHART[0],
            "the firm pool must hold the account the classifier named. Writing "
            "the substituted code here would teach every client of this trade "
            "one client's fallback")
        self.assertEqual(firm[0]["account_name"], NOT_IN_CHART[1])


class TheUnreadableChartTest(CorrectedNoteTestCase):
    """A narrowing, and it is stated rather than assumed.

    On an unreadable chart the check does not run: the code stands unchecked
    and `needs_review` is forced. Amendment 238's rule compares the operator's
    code with "the code the chart check resolved the suggestion to", and there
    is no such code here, so the rule's input is absent. Writing a firm row on
    an unchecked code is the failure amendment 238 exists to prevent.
    """

    def setUp(self):
        super().setUp()
        # Point CHARTS_DIR at a folder with no bundle in it, which is what an
        # unreadable chart is: an empty read, not an empty chart.
        self.chart.__exit__(None, None, None)
        empty = self.env.path / "no-bundle"
        empty.mkdir(exist_ok=True)
        saved = config.CHARTS_DIR
        config.CHARTS_DIR = empty
        self.addCleanup(setattr, config, "CHARTS_DIR", saved)
        from worker.categorisation import chart
        chart._CACHE.clear()
        chart._ACCOUNT_CACHE.clear()

    def test_nothing_is_learned_when_the_chart_could_not_be_read(self):
        repo = Repository()
        try:
            result = ai_result(IN_CHART[0], IN_CHART[1])
            resolve_against_chart(result, repo=repo)
            self.assertEqual(result.chart_outcome, "unreadable_chart")
            taught = service._learn_firm_mapping_if_confirmed(
                repo, {"firm_id": "INTELLITAX"}, result,
                chosen_code=IN_CHART[0], vendor_key=VENDOR_KEY,
                vendor_name=SUPPLIER)
            firm = rows(repo, "SELECT * FROM categorisations_firm_vendors")
        finally:
            repo.close()
        self.assertIsNone(taught)
        self.assertEqual(firm, [])


class BothRoutesTest(CorrectedNoteTestCase):
    r"""The rule reaches the table through a real resolution, on both routes.

    `categorise()` is replaced so it returns a classifier answer, because the
    production engine is built with the fallback disabled and enabling it would
    make a real OpenAI call. **Everything after `categorise()` is the real
    path**: the chart check runs, the service decides, and the helper writes.

    ## Which note reaches which route, read off `apply_resolution_note()`

    **A `filed` note carrying a `filed_path` goes to `_apply_filed_note()`**,
    the Desktop back-feed route, which records a filing Desktop has already
    done. **A `filed` note with no `filed_path` goes through `_settle_note()`
    to `resolve_receipt()`**, the route the CLI and the console share.

    **The receipt must not already be filed on either.** `resolve_receipt()`
    refuses one at step 1a, which is right for every caller but a correction,
    and the first version of this class seeded a filed receipt and got
    `already_filed` back on both routes. Disclosed rather than quietly fixed.
    """

    def seed_unfiled(self, receipt_id="r-1"):
        """A receipt that has been read but not filed, which is the premise of
        both note routes below."""
        repo = Repository()
        try:
            self.env.seed(repo, receipt_id=receipt_id, status="needs_review",
                          supplier_name=SUPPLIER, invoice_date="2026-04-01",
                          net_amount=80.0, vat_amount=16.0, gross_amount=96.0,
                          validation_status="needs_review",
                          validation_notes=["a reason"])
        finally:
            repo.close()

    def _with_classifier(self, code=IN_CHART[0], name=IN_CHART[1]):
        def fake(self_engine, **kwargs):
            return ai_result(code, name,
                             client_id=kwargs.get("client_id", "CLIENT001"),
                             business_type=kwargs.get("business_type",
                                                      BUSINESS_TYPE))
        return mock.patch(
            "worker.categorisation.engine.CategorisationEngine.categorise",
            new=fake)

    def firm(self):
        return self.table("SELECT * FROM categorisations_firm_vendors")

    def client(self):
        return self.table("SELECT * FROM categorisations_client_vendors")

    def _filed_note(self, code, name, *, tick, with_path):
        """A `filed` note. `with_path` decides which route consumes it."""
        payload = corrected_note(
            action="filed",
            values=values_with(category_code=code, category_name=name))
        if tick:
            payload["remember_gl_for_supplier"] = True
        if with_path:
            payload["filed_path"] = FILED_RELATIVE
            target = config.PRACTICE_ROOT / Path(FILED_RELATIVE.replace("\\", "/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("the copy Desktop filed", encoding="utf-8")
        return payload

    # -- the Desktop back-feed route, _apply_filed_note() ------------------

    def test_the_desktop_route_writes_both_tables_on_a_confirmation(self):
        self.seed_unfiled()
        self.write_note(self._filed_note(IN_CHART[0], IN_CHART[1],
                                         tick=True, with_path=True))
        with self._with_classifier():
            self.poll()
        self.assertEqual(len(self.client()), 1, "the client table is written")
        firm = self.firm()
        self.assertEqual(len(firm), 1, "and so is the firm pool")
        self.assertEqual(firm[0]["nominal_code"], IN_CHART[0])
        self.assertEqual(firm[0]["business_type"], BUSINESS_TYPE)
        self.assertEqual(firm[0]["vendor_key"], VENDOR_KEY)

    def test_the_desktop_route_writes_the_client_table_only_when_they_differ(self):
        self.seed_unfiled()
        self.write_note(self._filed_note(ALSO_IN_CHART[0], ALSO_IN_CHART[1],
                                         tick=True, with_path=True))
        with self._with_classifier(IN_CHART[0], IN_CHART[1]):
            self.poll()
        self.assertEqual(len(self.client()), 1)
        self.assertEqual(self.firm(), [],
                         "the operator overrode the classifier, so the receipt "
                         "account is not knowable and the firm pool is untouched")

    def test_the_desktop_route_teaches_neither_table_with_no_tick(self):
        self.seed_unfiled()
        self.write_note(self._filed_note(IN_CHART[0], IN_CHART[1],
                                         tick=False, with_path=True))
        with self._with_classifier():
            self.poll()
        self.assertEqual(self.client(), [], "11.3: learning is opt-in")
        self.assertEqual(self.firm(), [], "and the tick governs both tables")

    # -- the settle route, resolve_receipt() -------------------------------

    def test_the_settle_route_writes_both_tables_on_a_confirmation(self):
        """The other learning site, reached by a `filed` note with no path.

        This is the one amendment 231 never spoke about, and it is why the rule
        lives in a helper: the two routes' guards differ and the decision must
        not.
        """
        self.seed_unfiled()
        self.write_note(self._filed_note(IN_CHART[0], IN_CHART[1],
                                         tick=True, with_path=False))
        with self._with_classifier():
            self.poll()
        self.assertEqual(len(self.client()), 1)
        firm = self.firm()
        self.assertEqual(len(firm), 1)
        self.assertEqual(firm[0]["nominal_code"], IN_CHART[0])
        self.assertEqual(firm[0]["business_type"], BUSINESS_TYPE)

    def test_the_settle_route_writes_the_client_table_only_when_they_differ(self):
        self.seed_unfiled()
        self.write_note(self._filed_note(ALSO_IN_CHART[0], ALSO_IN_CHART[1],
                                         tick=True, with_path=False))
        with self._with_classifier(IN_CHART[0], IN_CHART[1]):
            self.poll()
        self.assertEqual(len(self.client()), 1)
        self.assertEqual(self.firm(), [])

    def test_the_settle_route_teaches_neither_table_with_no_tick(self):
        self.seed_unfiled()
        self.write_note(self._filed_note(IN_CHART[0], IN_CHART[1],
                                         tick=False, with_path=False))
        with self._with_classifier():
            self.poll()
        self.assertEqual(self.client(), [])
        self.assertEqual(self.firm(), [])


class OneCallerTest(unittest.TestCase):
    r"""`upsert_firm_vendor()` has exactly one caller, and it is the rule.

    **A guard over the set, not a check of the two sites.** `CLAUDE.md`,
    2026-09-08: where several call sites must all use one helper, assert on the
    source that no unwrapped call remains and that the count of wrapped ones is
    what you expect. A third learning route added later must go through the
    rule, and this is what makes it go red if it does not.
    """

    HELPER = "_learn_firm_mapping_if_confirmed"

    def production_files(self):
        root = source_guards.REPO_ROOT
        # `.history\` excluded by construction: the root glob is not recursive
        # and the worker glob is rooted inside `worker\`.
        return sorted(root.glob("*.py")) + sorted(root.glob("worker/**/*.py"))

    def _calls(self, name):
        found = []
        for path in self.production_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            owners = {}

            def walk(node, chain):
                for child in ast.iter_child_nodes(node):
                    nxt = chain
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                          ast.ClassDef)):
                        nxt = chain + [child.name]
                    owners[id(child)] = nxt
                    walk(child, nxt)
            walk(tree, [])
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                called = (func.attr if isinstance(func, ast.Attribute)
                          else func.id if isinstance(func, ast.Name) else None)
                if called == name:
                    chain = owners.get(id(node), [])
                    found.append((path.name, chain[-1] if chain else "<module>"))
        return sorted(found)

    def test_upsert_firm_vendor_is_called_only_by_the_rule(self):
        self.assertEqual(
            self._calls("upsert_firm_vendor"),
            [("service.py", self.HELPER)],
            "every write of the firm pool must go through amendment 238's "
            "rule. A direct call elsewhere would teach it a code nobody "
            "confirmed, applied by layer 2 to every client of that trade")

    def test_the_rule_is_called_from_both_learning_routes(self):
        self.assertEqual(
            self._calls(self.HELPER),
            [("service.py", "_apply_filed_note"),
             ("service.py", "resolve_receipt")],
            "both learning routes must call the rule. Paul's decision of "
            "2026-09-12: a rule live on one route and absent from the other is "
            "the half-built change this project has paid for before")

    def test_every_route_that_teaches_the_client_table_also_offers_the_firm_pool(self):
        """The set comparison the two tests above only imply.

        Any function in `service.py` that writes the client table must also
        reach the rule. The two seed scripts are excluded by name: they import
        mappings wholesale and are not corrections.
        """
        client = {owner for name, owner in self._calls("upsert_client_vendor")
                  if name == "service.py"}
        firm = {owner for name, owner in self._calls(self.HELPER)
                if name == "service.py"}
        self.assertEqual(
            client, firm,
            "a route teaches the client table without ever offering the firm "
            f"pool. Client: {sorted(client)}. Rule: {sorted(firm)}")


class TheShapeTest(unittest.TestCase):
    """`ai_result()` above is a copy of layer 5's construction, so it is
    asserted against the source rather than trusted."""

    def test_the_shape_matches_what_layer_five_builds(self):
        tree = source_guards.tree_of("worker", "categorisation", "engine.py")
        found = None
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Name)
                    and node.func.id == "CategorisationResult"):
                continue
            fields = {k.arg: ast.unparse(k.value) for k in node.keywords}
            if fields.get("match_source") == "'ai'":
                found = fields
        self.assertIsNotNone(found, "layer 5 no longer builds a result with "
                                    "match_source 'ai'")
        self.assertEqual(found["confidence"], "'low'")
        self.assertEqual(found["needs_review"], "True")
        self.assertEqual(found["matched_vendor"], "vendor_key")
        self.assertEqual(service.CLASSIFIER_MATCH_SOURCE, "ai")


if __name__ == "__main__":
    unittest.main()

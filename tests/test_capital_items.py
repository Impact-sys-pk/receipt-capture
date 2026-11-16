r"""Capital items: the classifier asks three questions, in Paul's order.

Outstanding item 55, brief `PROMPT_claude_code_2026-11-16_capital_items.md`,
Paul's decisions of 2026-11-16.

1. **Does it look capital?** Layer 5 answers this in the same call as the
   account, as a boolean, `looks_capital`. No capital account is among the
   codes it may choose: the 66 are unchanged.
2. **If so, is the gross at or above the threshold?** The client's own
   `capitalisation_threshold`, else the firm's.
3. **Only below the threshold does the expense account it named get used.**

At or above, the receipt is a review item, `needs_review`, with a note that
begins "capital item", the published key `capital_item` holding the gross and
the threshold, no categorisation saved and nothing copied into Clients. It is
**never posted by the system**. The accounting method is not consulted.

Both callers that run layer 5 are covered: the poll, through
`process_extraction_result()`, and the recovery sweep in `app.py`, which
publishes too and would otherwise post a capital item the poll refers.
"""

import contextlib
import json
import unittest
from unittest.mock import patch

import config

from resolution_fixtures import TempEnvironment, extraction_result, rows
from test_category_hold import item_for, receipts
from test_item_vendor_key import drive_with
from test_recovery_sweep_fallback import RECEIPT as SWEPT, seed_unpublished_ok
from worker import capital, publish
from worker.categorisation import engine as engine_module
from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository

CLIENT = "CLIENT001"
#: One of the 66, so the answer is a real expense account.
EXPENSE = {"code": "7500", "name": "Printing, postage and stationery"}
ABSENT = object()

#: (gross, net, vat), each set consistent so validation passes and the receipt
#: reaches layer 5 on the `ok` branch.
OVER = (120.0, 100.0, 20.0)
AT = (50.0, 41.67, 8.33)
UNDER = (49.99, 41.66, 8.33)


@contextlib.contextmanager
def thresholds(client=ABSENT, firm=ABSENT, **client_fields):
    """Set the client's and the firm's `capitalisation_threshold` for one test.

    ABSENT leaves the key off the record, which is what four of the six live
    client records do; None is the stated "use the firm default" Desktop writes.
    """
    record = dict(config.CLIENTS_BY_ID[CLIENT])
    record.pop("capitalisation_threshold", None)
    if client is not ABSENT:
        record["capitalisation_threshold"] = client
    record.update(client_fields)
    firm_id = record["firm_id"]
    firm_record = dict(config.FIRMS.get(firm_id) or {"firm_id": firm_id})
    firm_record.pop("capitalisation_threshold", None)
    if firm is not ABSENT:
        firm_record["capitalisation_threshold"] = firm
    with patch.dict(config.CLIENTS_BY_ID, {CLIENT: record}), \
         patch.dict(config.FIRMS, {firm_id: firm_record}):
        yield


@contextlib.contextmanager
def layer5(looks_capital):
    """Layer 5 switched on, answering one of the 66 and the capital question."""
    answer = dict(EXPENSE, looks_capital=looks_capital)
    with patch.object(config, "CLASSIFIER_ENABLED", True), \
         patch.object(CategorisationEngine, "_ai_suggest",
                      lambda self, *a, **k: dict(answer)):
        yield


def poll(test_case, looks_capital, amounts):
    gross, net, vat = amounts
    with layer5(looks_capital):
        drive_with(test_case, extraction_result(
            gross_amount=gross, net_amount=net, vat_amount=vat))
    receipt, = receipts()
    return receipt, item_for(receipt["receipt_id"])


def categorisations(receipt_id):
    repo = Repository()
    try:
        return rows(repo, "SELECT * FROM categorisations WHERE receipt_id = ?",
                    (receipt_id,))
    finally:
        repo.close()


class TheClassifierIsAskedTest(unittest.TestCase):
    """Question one, on the engine."""

    def test_the_reply_carries_a_required_capital_answer(self):
        field = engine_module.AiAccountSuggestion.model_fields.get("looks_capital")
        self.assertIsNotNone(field, "the reply has no looks_capital field")
        self.assertTrue(field.is_required(),
                        "a default would make the field optional in the schema")

    def test_layer_five_passes_the_answer_on(self):
        for looks in (True, False):
            with self.subTest(looks_capital=looks):
                engine = CategorisationEngine(repo=None, enable_ai_fallback=True)
                with patch.object(engine_module, "OpenAI", object()), \
                     patch.object(engine, "_ai_suggest",
                                  return_value=dict(EXPENSE, looks_capital=looks)):
                    result = engine.categorise(
                        receipt_id="r", extraction_id="e", supplier_name="Halfords",
                        client_id=CLIENT, business_type="PHV_DRIVER", gross_amount=120.0)
                self.assertEqual(result.match_source, "ai")
                self.assertIs(result.looks_capital, looks)
                self.assertEqual(result.suggested_code, EXPENSE["code"])

    def test_no_other_layer_says_capital(self):
        """A result nobody asked the question of says no, which is how every
        receipt behaves today."""
        self.assertIs(engine_module.CategorisationResult(
            receipt_id="r", extraction_id="e", client_id=CLIENT,
            business_type="X").looks_capital, False)

    def test_the_prompt_asks_and_no_capital_account_is_offered(self):
        from test_layer5_context import _PromptRecorder
        from worker.categorisation.receipt_accounts import load_receipt_accounts

        engine = CategorisationEngine(repo=None, enable_ai_fallback=True)
        with patch.object(engine_module, "OpenAI", _PromptRecorder):
            result = engine._ai_suggest("halfords", CLIENT, "Halfords", 120.0)
        prompt = _PromptRecorder.prompts[0]
        self.assertIn("capital", prompt.lower(), "the prompt never asks the question")
        offered = {code for code, _ in load_receipt_accounts()}
        for code in ("0051", "0061", "0071", "0081", "0091"):
            with self.subTest(code=code):
                self.assertNotIn(code, offered)
                self.assertNotIn(f"- {code}:", prompt)
        self.assertIn("looks_capital", result)

    def test_a_capital_reply_is_read_off_the_parsed_answer(self):
        """The real `_ai_suggest()`, with the model answering True. Added after
        the mutations: the recorder above answers False, so nothing drove the
        line that reads the reply with a True in it."""
        from test_layer5_context import _FakeResponse, _PromptRecorder

        class SaysCapital(_PromptRecorder):
            def parse(self, **kwargs):
                return _FakeResponse(engine_module.AiAccountSuggestion(
                    code=EXPENSE["code"], name=EXPENSE["name"], looks_capital=True))

        engine = CategorisationEngine(repo=None, enable_ai_fallback=True)
        with patch.object(engine_module, "OpenAI", SaysCapital):
            result = engine._ai_suggest("halfords", CLIENT, "Halfords", 120.0)
        self.assertEqual(result, dict(EXPENSE, looks_capital=True))


class TheThresholdTest(unittest.TestCase):
    """The client's figure where it has one, the firm's otherwise."""

    def test_where_it_comes_from(self):
        cases = [
            ("client override", dict(client=200, firm=50), 200.0),
            ("client null uses the firm", dict(client=None, firm=50), 50.0),
            ("client absent uses the firm", dict(firm=50), 50.0),
            ("a zero override is a figure", dict(client=0, firm=50), 0.0),
            ("nothing anywhere", dict(), None),
            ("a bad client value is not a figure", dict(client="lots", firm=50), None),
            ("a boolean is not a figure", dict(client=True, firm=50), None),
            ("a negative is not a figure", dict(client=-1, firm=50), None),
            ("a bad firm value is not a figure", dict(firm="fifty"), None),
        ]
        for name, kwargs, expected in cases:
            with self.subTest(case=name), TempEnvironment(), thresholds(**kwargs):
                self.assertEqual(capital.threshold_for(CLIENT), expected)


class OnThePollTest(unittest.TestCase):

    def assertReferred(self, receipt, item, gross, threshold):
        self.assertEqual(receipt["status"], "needs_review")
        self.assertEqual(item["validation_status"], "needs_review")
        self.assertEqual(item[publish.CAPITAL_ITEM_KEY],
                         {"gross": gross, "threshold": threshold})
        self.assertTrue(any(n.startswith("capital item") for n in item[publish.NOTES_KEY]),
                        item[publish.NOTES_KEY])
        self.assertIsNone(receipt["filed_path"], "a capital item was copied into Clients")
        self.assertEqual(categorisations(receipt["receipt_id"]), [],
                         "the expense account was saved for a capital item")
        self.assertIsNone(item["category_code"])

    def assertOrdinary(self, receipt, item):
        self.assertEqual(receipt["status"], "ok")
        self.assertIsNone(item[publish.CAPITAL_ITEM_KEY])
        cat, = categorisations(receipt["receipt_id"])
        self.assertEqual(cat["match_source"], "ai")

    def test_over_the_threshold_is_referred(self):
        with TempEnvironment(), thresholds(firm=50):
            self.assertReferred(*poll(self, True, OVER), gross=120.0, threshold=50.0)

    def test_exactly_at_the_threshold_is_referred(self):
        with TempEnvironment(), thresholds(firm=50):
            self.assertReferred(*poll(self, True, AT), gross=50.0, threshold=50.0)

    def test_under_the_threshold_is_an_ordinary_expense(self):
        with TempEnvironment(), thresholds(firm=50):
            self.assertOrdinary(*poll(self, True, UNDER))

    def test_not_capital_is_unchanged_whatever_the_amount(self):
        with TempEnvironment(), thresholds(firm=50):
            self.assertOrdinary(*poll(self, False, OVER))

    def test_the_client_override_decides(self):
        with TempEnvironment(), thresholds(client=200, firm=50):
            self.assertOrdinary(*poll(self, True, OVER))

    def test_no_threshold_anywhere_refers(self):
        """Nothing to compare with, so it is not posted. Referral is the
        direction that can be undone by a person."""
        with TempEnvironment(), thresholds():
            self.assertReferred(*poll(self, True, UNDER), gross=49.99, threshold=None)

    def test_the_accounting_method_is_not_consulted(self):
        for method in ("cash", "accruals"):
            with self.subTest(method=method), TempEnvironment(), \
                    thresholds(firm=50, accounting_method=method):
                self.assertReferred(*poll(self, True, OVER), gross=120.0, threshold=50.0)

    def test_the_key_is_null_on_every_other_item_and_spelt_null(self):
        with TempEnvironment(), thresholds(firm=50):
            receipt, item = poll(self, False, OVER)
            self.assertIn(publish.CAPITAL_ITEM_KEY, item)
            self.assertIsNone(item[publish.CAPITAL_ITEM_KEY])


class OnTheSweepTest(unittest.TestCase):
    """The recovery sweep publishes too, so it refers too."""

    def _sweep(self, looks_capital, amounts):
        import app
        gross, net, vat = amounts
        with TempEnvironment() as env, thresholds(firm=50):
            seed_unpublished_ok(env, gross_amount=gross, net_amount=net, vat_amount=vat)
            repo = Repository()
            try:
                engine = CategorisationEngine(repo=repo, enable_ai_fallback=True)
                with patch.object(CategorisationEngine, "_ai_suggest",
                                  lambda self, *a, **k: dict(EXPENSE,
                                                             looks_capital=looks_capital)):
                    app._publish_unpublished_receipts(repo, engine, {})
                receipt = repo.get_receipt(SWEPT)
            finally:
                repo.close()
            return receipt, item_for(SWEPT), categorisations(SWEPT)

    def test_over_the_threshold_is_referred(self):
        receipt, item, cats = self._sweep(True, OVER)
        self.assertEqual(receipt["status"], "needs_review")
        self.assertEqual(item["validation_status"], "needs_review")
        self.assertEqual(item[publish.CAPITAL_ITEM_KEY], {"gross": 120.0, "threshold": 50.0})
        self.assertTrue(any(n.startswith("capital item") for n in item[publish.NOTES_KEY]))
        self.assertIsNone(receipt["filed_path"])
        self.assertEqual(cats, [])

    def test_under_the_threshold_is_an_ordinary_expense(self):
        receipt, item, cats = self._sweep(True, UNDER)
        self.assertEqual(receipt["status"], "ok")
        self.assertEqual(item["validation_status"], "ok")
        self.assertIsNone(item[publish.CAPITAL_ITEM_KEY])
        self.assertEqual(len(cats), 1)


class TheKeyTest(unittest.TestCase):

    def test_the_name_and_that_it_is_an_item_key(self):
        self.assertEqual(publish.CAPITAL_ITEM_KEY, "capital_item")
        self.assertIn(publish.CAPITAL_ITEM_KEY, publish.ITEM_ONLY_KEYS)

    def test_extra_for_states_it_on_every_item(self):
        self.assertIsNone(publish.extra_for([])[publish.CAPITAL_ITEM_KEY])
        referral = {"gross": 120.0, "threshold": 50.0}
        extra = publish.extra_for([], capital_item=referral)
        self.assertEqual(json.loads(json.dumps(extra))[publish.CAPITAL_ITEM_KEY], referral)


if __name__ == "__main__":
    unittest.main()

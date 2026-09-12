"""Layer 5 is told the amount and the item lines, and both reach the prompt.

Brief of 2026-09-05, `PROMPT_claude_code_2026-09-05_layer5_context.md`. The
first run layer 5 ever had on this project returned
"0081 Motor vehicles - cars - additions" for a Halfords receipt, because nothing
in the prompt said how much had been spent, and "7520 Stationery and office
supplies" for an Asda Wallington receipt, because nothing said what was bought.

Nothing here calls OpenAI. `OpenAI` is patched, either to a sentinel that would
raise if it were called or to a fake that records the prompt it was handed.

These tests are about context reaching the model. They are deliberately NOT
about what the model does with it: there is no capitalisation threshold in the
engine and there must not be one until outstanding item 33 is decided.
"""

import inspect
import unittest
from pathlib import Path
from unittest.mock import patch

from worker.categorisation import engine as engine_module
from worker.extraction.base import ExtractionResult
from worker.extraction.openai_vision import _SYSTEM_PROMPT, _normalise_line_items
from worker.line_items import MAX_LINE_ITEMS, LineItem


class _FakeMessage:
    def __init__(self, parsed):
        self.parsed = parsed


class _FakeChoice:
    def __init__(self, parsed):
        self.message = _FakeMessage(parsed)


class _FakeResponse:
    def __init__(self, parsed):
        self.choices = [_FakeChoice(parsed)]


class _PromptRecorder:
    """Stands in for OpenAI(), and keeps the prompt AND the parameters.

    It answers with a code that is in the pool the test supplies, so
    _ai_suggest() runs all the way to its return rather than stopping at the
    "not in COA" branch, which would let a test pass for the wrong reason.

    **`parse()` names every parameter the real call passes rather than taking
    `**kwargs`, and that is deliberate.** `CLAUDE.md`, 2026-09-08: a stub must
    model what the real function does. A stub taking `**kwargs` would have
    swallowed `temperature` and `seed` silently when step 10p part two added
    them, and every test here would have stayed green while the two parameters
    went unasserted. Instead the stub went red on the first run after they were
    added, which is how it should behave.

    `calls` keeps the whole keyword set, so a test can assert what was sent
    rather than only what was in the prompt text.
    """

    prompts = []
    calls = []

    def __init__(self, *args, **kwargs):
        _PromptRecorder.prompts = []
        _PromptRecorder.calls = []
        self.beta = self

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    def parse(self, *, model, messages, response_format, temperature, seed):
        _PromptRecorder.prompts.append(messages[0]["content"])
        _PromptRecorder.calls.append({
            "model": model, "response_format": response_format,
            "temperature": temperature, "seed": seed,
        })
        return _FakeResponse(engine_module.AiAccountSuggestion(code="7391", name="Car wash"))


# Two accounts, and both are deliberate. 7391 Car wash is one of the 66 and is
# absent from most library charts, which is the case the fallback exists for.
# 0081 is a capital addition and is NOT one of the 66: Paul removed the five
# capital additions on 2026-09-05, so a real pool cannot offer it. It is kept
# here because these tests are about context reaching the model rather than
# about the pool's membership, and a pool of one would not show a list.
POOL = [("7391", "Car wash"), ("0081", "Motor vehicles - cars - additions")]


class CategorisePassesTheContextOnTest(unittest.TestCase):
    """categorise() hands both values to _ai_suggest().

    Asserted at the boundary between the two methods rather than on the prompt,
    because a test that only reads the prompt stays green when the call site in
    categorise() drops an argument and _ai_suggest()'s own default fills it in.
    That is the mutation recorded in the report.
    """

    def _categorise(self, **kwargs):
        instance = engine_module.CategorisationEngine(repo=None, enable_ai_fallback=True)
        with patch.object(engine_module, "OpenAI", object()), \
             patch.object(instance, "_ai_suggest", return_value=None) as suggest:
            instance.categorise(
                receipt_id="r-1", extraction_id="e-1",
                supplier_name="Halfords Autocentre",
                client_id="CLIENT001", business_type="PHV_DRIVER",
                **kwargs,
            )
        suggest.assert_called_once()
        args, kwargs_seen = suggest.call_args
        return list(args) + list(kwargs_seen.values())

    def test_the_amount_reaches_ai_suggest(self):
        self.assertIn(24.99, self._categorise(gross_amount=24.99))

    def test_the_line_items_reach_ai_suggest(self):
        items = [LineItem("OIL FILTER", 8.99), LineItem("WIPER BLADE", 16.00)]
        self.assertIn(items, self._categorise(line_items=items))

    def test_both_default_to_none_when_the_caller_has_neither(self):
        # ~~A caller that reads an extraction back out of the database has no
        # item lines, because nothing stores them.~~ **Struck 2026-09-12 by step
        # 10p: they are stored and every caller passes them.** What is still
        # true, and is what this asserts, is that a receipt whose document had
        # no itemised lines passes None and that must not be an error.
        passed = self._categorise()
        self.assertNotIn(24.99, passed)
        self.assertEqual([v for v in passed if isinstance(v, list)], [])


class TheyReachThePromptTest(unittest.TestCase):
    """_ai_suggest() states both in the prompt, and leaves them out cleanly."""

    def _prompt(self, **kwargs):
        instance = engine_module.CategorisationEngine(repo=None, enable_ai_fallback=True)
        with patch.object(engine_module, "OpenAI", _PromptRecorder), \
             patch.object(engine_module, "load_receipt_accounts",
                          return_value=POOL):
            result = instance._ai_suggest("halfords", "CLIENT001", "Halfords Autocentre",
                                          **kwargs)
        self.assertEqual(result, {"code": "7391", "name": "Car wash"})
        self.assertEqual(len(_PromptRecorder.prompts), 1)
        return _PromptRecorder.prompts[0]

    def test_the_amount_is_in_the_prompt_and_is_named_as_the_gross(self):
        prompt = self._prompt(gross_amount=24.99)
        # Named, so the model is not left to work out net from gross. The brief
        # asks for this in as many words.
        self.assertIn("Gross amount on the receipt, VAT included: 24.99", prompt)

    def test_a_zero_amount_is_stated_rather_than_dropped(self):
        # `if gross_amount:` would drop 0.0, and a free receipt is not the same
        # thing as an unknown one. The guard is `is not None`.
        self.assertIn("Gross amount on the receipt, VAT included: 0.0",
                      self._prompt(gross_amount=0.0))

    def test_the_item_lines_are_in_the_prompt(self):
        """**The model sees what it always saw**, description then amount.

        Step 10p part one changed where the lines come from and the shape they
        are stored in. It deliberately did NOT change what the model is looking
        at, because part two changes the same call in the same commit and two
        changes to one call at once would leave neither measurable.
        """
        prompt = self._prompt(line_items=[LineItem("OIL FILTER", 8.99),
                                          LineItem("WIPER BLADE", 16.00)])
        self.assertIn("Item lines on the receipt:", prompt)
        self.assertIn("OIL FILTER 8.99", prompt)
        self.assertIn("WIPER BLADE 16.00", prompt)
        # And never the dataclass repr, which is what an f-string over the
        # objects themselves would have put in the prompt.
        self.assertNotIn("LineItem(", prompt)

    def test_a_line_with_no_amount_is_shown_without_one(self):
        # Not "OIL FILTER None", and not "OIL FILTER 0.00": an amount that could
        # not be read is absent, and nought is a real amount a receipt can print.
        prompt = self._prompt(line_items=[LineItem("LOOSE ITEM", None)])
        self.assertIn("LOOSE ITEM", prompt)
        self.assertNotIn("None", prompt)
        self.assertNotIn("LOOSE ITEM 0.00", prompt)

    def test_a_line_at_nought_says_nought(self):
        prompt = self._prompt(line_items=[LineItem("FREE GIFT", 0.0)])
        self.assertIn("FREE GIFT 0.00", prompt)

    def test_neither_leaves_a_trace_when_both_are_none(self):
        prompt = self._prompt()
        self.assertNotIn("Gross amount", prompt)
        self.assertNotIn("Item lines", prompt)
        self.assertNotIn("None", prompt)
        # The two facts that are always there are still there.
        self.assertIn('Supplier as it appeared on the receipt: "Halfords Autocentre"', prompt)
        self.assertIn('Normalised lookup key: "halfords"', prompt)

    def test_an_empty_item_list_is_left_out_rather_than_printed_empty(self):
        self.assertNotIn("Item lines", self._prompt(line_items=[]))

    def test_the_pool_is_still_the_only_thing_that_names_a_code(self):
        # Guard on the brief's "do not change what layer 5 chooses from".
        prompt = self._prompt(gross_amount=24.99,
                              line_items=[LineItem("OIL FILTER", 8.99)])
        self.assertIn("- 7391: Car wash", prompt)
        self.assertIn("- 0081: Motor vehicles - cars - additions", prompt)


class ExtractionCarriesLineItemsTest(unittest.TestCase):
    """ExtractionResult carries them, and the extractor normalises the shape."""

    def test_line_items_defaults_to_none(self):
        result = ExtractionResult(
            supplier_name="Asda", invoice_date="2026-09-01", net_amount=None,
            vat_amount=None, gross_amount=12.34, currency="GBP",
            raw_response="{}", engine="test",
        )
        self.assertIsNone(result.line_items)

    def test_a_list_of_objects_is_what_the_prompt_now_asks_for(self):
        """Step 10p part one. The shape reversed: objects are the answer and
        strings are the fallback, where it was the other way round."""
        self.assertEqual(
            _normalise_line_items([{"description": "MILK 2L", "amount": 1.45}]),
            [LineItem("MILK 2L", 1.45)],
        )

    def test_a_missing_amount_is_none_and_not_nought(self):
        # Nought and absent are different answers and the difference reaches
        # 18.4's split, whose lines must sum to the original amount.
        self.assertEqual(
            _normalise_line_items([{"description": "LOOSE ITEM", "amount": None}]),
            [LineItem("LOOSE ITEM", None)],
        )

    def test_an_amount_of_nought_survives_as_nought(self):
        self.assertEqual(
            _normalise_line_items([{"description": "FREE GIFT", "amount": 0}]),
            [LineItem("FREE GIFT", 0.0)],
        )

    def test_a_list_of_strings_still_parses_and_the_amount_is_split_off(self):
        """A model answers the prompt it was given and this one has changed, so
        the old shape is still read. It is tolerance for a model that ignores
        the schema, not for stored data: nothing stored is read through here."""
        self.assertEqual(_normalise_line_items(["MILK 1.45", "BREAD 1.10"]),
                         [LineItem("MILK", 1.45), LineItem("BREAD", 1.10)])

    def test_a_string_with_no_trailing_amount_is_all_description(self):
        self.assertEqual(_normalise_line_items(["LOOSE ITEM"]),
                         [LineItem("LOOSE ITEM", None)])

    def test_one_newline_separated_string_becomes_a_list(self):
        self.assertEqual(_normalise_line_items("MILK 1.45\nBREAD 1.10"),
                         [LineItem("MILK", 1.45), LineItem("BREAD", 1.10)])

    def test_the_cap_is_enforced_and_not_merely_asked_for(self):
        """It was advisory: the prompt said "at most 40" and nothing truncated a
        model that answered with more. Harmless while the lines were held in
        memory and dropped; not harmless now they are written to a column."""
        many = [{"description": f"ITEM {i}", "amount": 1.0} for i in range(60)]
        self.assertEqual(len(_normalise_line_items(many)), MAX_LINE_ITEMS)
        self.assertEqual(_normalise_line_items(many)[0], LineItem("ITEM 0", 1.0))

    def test_nothing_and_empty_both_come_back_as_none(self):
        for value in (None, [], "", "   ", 17):
            with self.subTest(value=value):
                self.assertIsNone(_normalise_line_items(value))

    def test_the_extraction_prompt_asks_for_them(self):
        self.assertIn("line_items", _SYSTEM_PROMPT)

    def test_the_reply_ceiling_has_room_for_them(self):
        # 500 tokens fitted nine scalar fields and does not fit them plus 40
        # item lines. A truncated reply is not JSON, json.loads() raises, and
        # every field comes back null. This is the guard on that.
        from worker.extraction import openai_vision
        self.assertIn("max_tokens=1500", inspect.getsource(openai_vision.OpenAIVisionExtractor))

    def test_they_are_stored_on_the_extraction(self):
        """~~Nothing stores them.~~ **Reversed 2026-09-12 by step 10p part one,
        amendment 340, on Paul's decision.**

        The old test asserted the column's absence and was the guard on a
        decision of 2026-09-05 that they were carried in memory only. That
        decision is superseded: they were read once and stored nowhere, so the
        same receipt was categorised from less on every run after the first.
        """
        from worker.database import schema
        self.assertIn("line_items", inspect.getsource(schema))

    def test_the_column_is_on_extractions_and_not_on_receipts(self):
        # Evidence of what a document said belongs with the reading that said
        # it. `extractions` is append-only, so a re-read gets its own lines
        # rather than overwriting the first read's.
        from worker.database import schema
        source = inspect.getsource(schema)
        extractions = source.split("CREATE TABLE IF NOT EXISTS extractions")[1]
        self.assertIn("line_items", extractions.split("CREATE TABLE")[0])


class EveryCallSitePassesTheAmountTest(unittest.TestCase):
    """The set is enumerated, not listed.

    The previous brief said there were three call sites and there are five. The
    two it missed were `worker/resolution/service.py`, once on the console
    resolution path and once on the Desktop resolution-note path, and both were
    found by grepping rather than by reading the brief. So this walks the
    repository's own syntax trees and asserts a property of every call it finds,
    which is the habit CLAUDE.md asks for in front of the word "the" and a
    plural: a sixth call site added tomorrow is checked without anyone editing a
    list here.
    """

    # Read-only measurement scripts. They call categorise() to print what it
    # says and write no database row, so passing the amount is a property of
    # what they measure rather than of the pipeline. probe_extract.py does pass
    # it; probe_layer5.py reads the database and passes what it has.
    PROBES = {"probe_layer5.py", "probe_extract.py"}

    def _call_sites(self):
        import ast
        import config

        root = Path(config.__file__).resolve().parent
        skip = {".venv", ".history", "tests", "docs", "__pycache__", "archive"}
        found = []
        for path in root.rglob("*.py"):
            parts = set(path.relative_to(root).parts)
            if parts & skip or path.name in self.PROBES:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
                if name != "categorise":
                    continue
                found.append((
                    str(path.relative_to(root)).replace("\\", "/"),
                    node.lineno,
                    {kw.arg for kw in node.keywords},
                ))
        return sorted(found)

    def test_there_are_five_of_them_and_the_files_are_named(self):
        # The files and their counts, not the line numbers. A line number moves
        # whenever anything above it is edited, and a test that fails for that
        # is a test nobody trusts by the third time.
        sites = self._call_sites()
        counted = {}
        for filename, _line, _kws in sites:
            counted[filename] = counted.get(filename, 0) + 1
        self.assertEqual(
            counted,
            {
                "app.py": 1,
                "retroactive_categorise.py": 1,
                "worker/extraction_pipeline.py": 1,
                "worker/resolution/service.py": 2,
            },
            "the set moved; here it is in full: "
            + "; ".join(f"{f}:{line}" for f, line, _ in sites),
        )
        self.assertEqual(len(sites), 5)

    def test_every_one_of_them_passes_the_gross_amount(self):
        missing = [f"{f}:{line}" for f, line, kws in self._call_sites()
                   if "gross_amount" not in kws]
        self.assertEqual(missing, [], f"these call sites do not pass it: {missing}")

    def test_every_one_of_them_passes_the_line_items(self):
        """~~Only the live path can pass them.~~ **Reversed 2026-09-12 by step
        10p part one.**

        The old test asserted that only `worker/extraction_pipeline.py` passed
        them, because the other four read an extraction row back out of the
        database and `extractions` had no column for them. **That asymmetry is
        the defect step 10p exists to fix**: the same receipt was categorised
        from less on every run after the first, and nothing said so.

        **This is the guard the brief asks for over the SET**, so a sixth path
        added later fails here rather than silently sending the classifier
        nothing. A per-path test cannot do that.
        """
        missing = [f"{f}:{line}" for f, line, kws in self._call_sites()
                   if "line_items" not in kws]
        self.assertEqual(
            missing, [],
            "these re-run the engine without passing the item lines the first "
            f"read stored, so the classifier sees less than it saw: {missing}")


if __name__ == "__main__":
    unittest.main()

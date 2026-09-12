r"""Step 10p: the classifier's inputs, its determinism and its switch.

From `PROMPT_claude_code_2026-09-12_classifier_inputs_and_switch.md`, amendment
340, on Paul's decisions after he ran `probe_layer5.py` against the live
database.

`tests/test_layer5_context.py` holds what reaches the prompt and the guard over
the set of call sites; this file holds storage, determinism and the setting.

## The three parts ship together, and that is not a preference

**Turning the classifier on without the first two is what the probe showed going
wrong.** It returned two different codes for the same supplier, the same amount
and the same client, from a prompt that had never been told what was on the
receipt because nothing stored the item lines. A permanent firm-wide mapping
would then be taught, by step 10m, from whichever answer the operator happened
to see.
"""

import ast
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import config

import source_guards
from worker import line_items as line_items_module
from worker.categorisation import engine as engine_module
from worker.database.repository import Repository
from worker.line_items import MAX_LINE_ITEMS, LineItem, for_prompt, from_json, to_json

REPO_ROOT = Path(source_guards.REPO_ROOT)


# ---------------------------------------------------------------------------
# Part 1: the lines are stored, and they round-trip
# ---------------------------------------------------------------------------

class TheStoredShapeTest(unittest.TestCase):
    """`worker/line_items.py` is the only thing that knows the column's format."""

    def test_an_amount_that_could_not_be_read_is_none_and_not_nought(self):
        """**The decision this file exists to hold.** Nought and absent are
        different answers and the difference reaches 18.4's split, whose lines
        must sum to the original amount. A receipt can print a line at 0.00."""
        items = from_json(json.dumps([
            {"description": "LOOSE ITEM", "amount": None},
            {"description": "FREE GIFT", "amount": 0},
        ]))
        self.assertIsNone(items[0].amount)
        self.assertEqual(items[1].amount, 0.0)
        self.assertIsNot(items[0].amount, items[1].amount)

    def test_the_amount_is_stored_as_a_number_and_not_as_text(self):
        stored = to_json([LineItem("MILK 2L", 1.45)])
        raw = json.loads(stored)
        self.assertIsInstance(raw[0]["amount"], float)
        self.assertNotIsInstance(raw[0]["amount"], str)
        self.assertEqual(raw[0]["amount"], 1.45)

    def test_a_bool_is_never_read_as_an_amount(self):
        # bool is a subclass of int in Python, so True would otherwise store 1.0.
        self.assertIsNone(LineItem.from_dict(
            {"description": "X", "amount": True}).amount)

    def test_a_quoted_number_is_read_rather_than_thrown_away(self):
        # A model asked for a number sometimes answers with one in quotes.
        self.assertEqual(
            LineItem.from_dict({"description": "X", "amount": "1.45"}).amount, 1.45)
        self.assertEqual(
            LineItem.from_dict({"description": "X", "amount": "£1,234.50"}).amount,
            1234.50)

    def test_no_lines_is_none_and_never_an_empty_list(self):
        self.assertIsNone(to_json([]))
        self.assertIsNone(to_json(None))
        self.assertIsNone(from_json(None))
        self.assertIsNone(from_json("[]"))

    def test_a_line_with_no_description_is_dropped(self):
        self.assertIsNone(from_json(json.dumps([{"amount": 1.45}])))

    def test_reading_a_broken_column_never_raises(self):
        """It parses a column an older database does not have at all, and a
        categorisation must not fail because a line could not be read."""
        for value in ("not json", "{}", "17", b"\xff\xfe", 17, ""):
            with self.subTest(value=value):
                self.assertIsNone(from_json(value))

    def test_the_cap_is_applied_on_the_way_back_out_too(self):
        many = json.dumps([{"description": f"I{i}", "amount": 1.0}
                           for i in range(MAX_LINE_ITEMS + 20)])
        self.assertEqual(len(from_json(many)), MAX_LINE_ITEMS)

    def test_the_round_trip_is_lossless(self):
        items = [LineItem("MILK 2L", 1.45), LineItem("LOOSE", None),
                 LineItem("FREE", 0.0)]
        self.assertEqual(from_json(to_json(items)), items)


class TheColumnTest(unittest.TestCase):
    """The column exists, the writer fills it, and a reader gets it back."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._saved = config.DB_PATH
        config.DB_PATH = Path(self._temp.name) / "receipts.db"

    def tearDown(self):
        config.DB_PATH = self._saved
        self._temp.cleanup()

    def _seed(self, repo, items):
        repo.save_receipt(
            receipt_id="r-1", message_id="<m@x>", email_subject="s",
            email_from="c@example.com", email_received_at=None,
            filename="a.pdf", file_path="/a.pdf", file_hash="h" * 8,
            firm_id="FIRM001", client_id="CLIENT001", source="email")
        repo.save_extraction(
            extraction_id="e-1", receipt_id="r-1", engine="openai_vision",
            supplier_name="Asda", invoice_date="2026-09-01", net_amount=None,
            vat_amount=None, gross_amount=12.34, currency="GBP",
            raw_response="{}", validation_status="ok", validation_notes=[],
            line_items=items)

    def test_what_was_written_is_what_comes_back(self):
        items = [LineItem("MILK 2L", 1.45), LineItem("LOOSE ITEM", None)]
        repo = Repository()
        try:
            self._seed(repo, items)
            row = repo.get_extraction_for_receipt("r-1")
        finally:
            repo.close()
        self.assertEqual(from_json(row["line_items"]), items)

    def test_a_receipt_with_no_item_lines_stores_null(self):
        repo = Repository()
        try:
            self._seed(repo, None)
            row = repo.get_extraction_for_receipt("r-1")
        finally:
            repo.close()
        self.assertIsNone(row["line_items"])

    def test_the_amount_survives_as_a_number_through_the_database(self):
        repo = Repository()
        try:
            self._seed(repo, [LineItem("MILK 2L", 1.45)])
            stored = repo._conn.execute(
                "SELECT line_items FROM extractions WHERE extraction_id = 'e-1'"
            ).fetchone()[0]
        finally:
            repo.close()
        self.assertIsInstance(json.loads(stored)[0]["amount"], float)

    def test_extractions_is_still_append_only_and_each_read_keeps_its_own_lines(self):
        """One receipt, two readings, two different sets of lines. The second
        does not overwrite the first: `extractions` is append-only."""
        repo = Repository()
        try:
            self._seed(repo, [LineItem("FIRST READ", 1.0)])
            repo.save_extraction(
                extraction_id="e-2", receipt_id="r-1", engine="manual_correction",
                supplier_name="Asda", invoice_date="2026-09-01", net_amount=None,
                vat_amount=None, gross_amount=12.34, currency="GBP",
                raw_response="{}", validation_status="ok", validation_notes=[],
                line_items=[LineItem("SECOND READ", 2.0)])
            rows = repo.get_extractions_for_receipt("r-1")
        finally:
            repo.close()
        self.assertEqual(len(rows), 2)
        both = {from_json(r["line_items"])[0].description for r in rows}
        self.assertEqual(both, {"FIRST READ", "SECOND READ"})


class TheSameInputEveryTimeTest(unittest.TestCase):
    r"""A receipt read once, then re-run, sends the classifier the same lines.

    **This is what step 10p is for**, stated as behaviour rather than as a
    property of a call site. `tests/test_layer5_context.py` holds the guard over
    the SET of paths, which is what catches a sixth path added later; this holds
    that the mechanism those paths use actually carries the lines through the
    database and back.

    The classifier is stubbed. What is measured is what it was HANDED, not what
    it answered: the answer is OpenAI's business and costs money, and the input
    is the pipeline's business and is what changed.
    """

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._saved = config.DB_PATH
        config.DB_PATH = Path(self._temp.name) / "receipts.db"

    def tearDown(self):
        config.DB_PATH = self._saved
        self._temp.cleanup()

    #: What the first read got off the document.
    FIRST_READ = [LineItem("PARKING SESSION", 3.50),
                  LineItem("SERVICE FEE", 0.30),
                  LineItem("LOOSE ITEM", None)]

    def _seen_by_the_classifier(self, line_items):
        """`_ai_suggest()`'s `line_items` argument, for one categorise() call."""
        engine = engine_module.CategorisationEngine(repo=None,
                                                    enable_ai_fallback=True)
        with patch.object(engine, "_ai_suggest", return_value=None) as suggest:
            engine.categorise(
                receipt_id="r-1", extraction_id="e-1",
                supplier_name="London Borough of Camden",
                client_id="CLIENT001", business_type="PHV_DRIVER",
                gross_amount=3.80, line_items=line_items)
        suggest.assert_called_once()
        # **Positionally, not by keyword.** `categorise()` calls
        # `_ai_suggest(vendor_key, client_id, supplier_name, gross_amount,
        # line_items)`, so reading `call_args.kwargs` alone returns None for
        # every input and this test would have passed by comparing None with
        # None. It did, on the first run, and that is why both forms are read.
        args, kwargs = suggest.call_args
        if "line_items" in kwargs:
            return kwargs["line_items"]
        return args[4] if len(args) > 4 else None

    def test_the_first_read_and_a_re_run_send_the_same_lines(self):
        repo = Repository()
        try:
            repo.save_receipt(
                receipt_id="r-1", message_id="<m@x>", email_subject="s",
                email_from="c@example.com", email_received_at=None,
                filename="a.pdf", file_path="/a.pdf", file_hash="h" * 8,
                firm_id="FIRM001", client_id="CLIENT001", source="email")
            # The first read, straight off the extraction object, as
            # `process_extraction_result()` does it.
            repo.save_extraction(
                extraction_id="e-1", receipt_id="r-1", engine="openai_vision",
                supplier_name="London Borough of Camden",
                invoice_date="2026-09-01", net_amount=None, vat_amount=None,
                gross_amount=3.80, currency="GBP", raw_response="{}",
                validation_status="ok", validation_notes=[],
                line_items=self.FIRST_READ)
            # A re-run, reading the extraction back out of the database, as
            # every other path does it.
            stored = repo.get_extraction_for_receipt("r-1")
        finally:
            repo.close()

        first = self._seen_by_the_classifier(self.FIRST_READ)
        again = self._seen_by_the_classifier(from_json(stored["line_items"]))

        self.assertEqual(first, again)
        self.assertEqual(again, self.FIRST_READ)
        # And the prompt rendering of each is the same string, which is the
        # thing the model actually reads.
        self.assertEqual(for_prompt(first), for_prompt(again))
        self.assertEqual(
            for_prompt(again),
            ["PARKING SESSION 3.50", "SERVICE FEE 0.30", "LOOSE ITEM"])

    def test_a_re_run_of_a_receipt_read_before_this_step_sends_nothing(self):
        """**Nothing is backfilled**, so a row written before 2026-09-12 holds
        NULL and reads as no item lines. That is expected and must not be an
        error: it is the state every receipt already in the database is in."""
        repo = Repository()
        try:
            repo.save_receipt(
                receipt_id="r-2", message_id="<m2@x>", email_subject="s",
                email_from="c@example.com", email_received_at=None,
                filename="b.pdf", file_path="/b.pdf", file_hash="g" * 8,
                firm_id="FIRM001", client_id="CLIENT001", source="email")
            repo.save_extraction(
                extraction_id="e-2", receipt_id="r-2", engine="openai_vision",
                supplier_name="Old Receipt", invoice_date="2026-01-01",
                net_amount=None, vat_amount=None, gross_amount=1.0,
                currency="GBP", raw_response="{}", validation_status="ok",
                validation_notes=[])
            stored = repo.get_extraction_for_receipt("r-2")
        finally:
            repo.close()
        self.assertIsNone(stored["line_items"])
        self.assertIsNone(self._seen_by_the_classifier(
            from_json(stored["line_items"])))


class NothingIsBackfilledTest(unittest.TestCase):
    r"""Paul's instruction: he does not care about the receipts already in the
    database, whose lines were never captured and cannot be recovered."""

    def test_the_migration_only_adds_a_column(self):
        tree = source_guards.tree_of("migrate_2026_09_12_line_items.py")
        statements = [value for value, _line
                      in source_guards.string_constants(tree, include_docstrings=True)]
        forbidden = ("UPDATE ", "INSERT ", "DELETE ", "DROP ")
        offenders = [s for s in statements
                     if any(word in s.upper() for word in forbidden)]
        self.assertEqual(
            offenders, [],
            f"the migration writes rows as well as adding a column: {offenders}")

    def test_it_needs_an_explicit_write_flag(self):
        """The command that changes something cannot be reached by pressing
        return."""
        source = (REPO_ROOT / "migrate_2026_09_12_line_items.py").read_text(
            encoding="utf-8")
        self.assertIn('"--write", action="store_true"', source)
        self.assertIn("if not args.write:", source)


# ---------------------------------------------------------------------------
# Part 2: the call is deterministic
# ---------------------------------------------------------------------------

class DeterminismTest(unittest.TestCase):
    """`temperature` and a fixed seed reach the call."""

    def test_the_constants_are_named_rather_than_written_at_the_call_site(self):
        self.assertEqual(engine_module.CLASSIFIER_TEMPERATURE, 0)
        self.assertIsInstance(engine_module.CLASSIFIER_SEED, int)

    def test_both_are_passed_to_the_api_call(self):
        """Read off the syntax tree of the call itself.

        A stubbed client proves the parameters are passed and not that the
        answer is stable, which is why the brief also asks for one run against
        the real API. This is the half a test can hold.
        """
        tree = source_guards.tree_of("worker", "categorisation", "engine.py")
        found = None
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if ast.unparse(node.func).endswith("completions.parse"):
                found = {k.arg: ast.unparse(k.value) for k in node.keywords}
        self.assertIsNotNone(found, "the classifier call has moved or gone")
        self.assertEqual(found.get("temperature"), "CLASSIFIER_TEMPERATURE")
        self.assertEqual(found.get("seed"), "CLASSIFIER_SEED")

    def test_the_call_passes_nothing_the_engine_did_not_choose(self):
        """The set, so a sixth parameter added later is a decision rather than
        an accident. The brief's own description of the defect was that the
        call passed three things and nothing else."""
        tree = source_guards.tree_of("worker", "categorisation", "engine.py")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and ast.unparse(node.func).endswith(
                    "completions.parse"):
                self.assertEqual(
                    {k.arg for k in node.keywords},
                    {"model", "messages", "response_format", "temperature", "seed"})


# ---------------------------------------------------------------------------
# Part 3: the switch
# ---------------------------------------------------------------------------

class TheSwitchTest(unittest.TestCase):
    """Per firm, on the firm record, default off."""

    def _read(self, firm):
        firms = {"FIRM001": firm} if firm is not None else {}
        return config._classifier_enabled(firms)

    def test_a_firm_record_with_no_setting_leaves_the_classifier_off(self):
        """**The case that matters most.** Every firm record written before
        2026-09-12 is this one, and an upgrade must not switch anybody on."""
        self.assertFalse(self._read({"firm_id": "FIRM001", "name": "Test"}))

    def test_no_firm_record_at_all_is_off(self):
        self.assertFalse(self._read(None))

    def test_true_turns_it_on_and_false_leaves_it_off(self):
        self.assertTrue(self._read({config.CLASSIFIER_ENABLED_FIELD: True}))
        self.assertFalse(self._read({config.CLASSIFIER_ENABLED_FIELD: False}))

    def test_a_value_that_is_not_a_boolean_refuses(self):
        """A string `"false"` is TRUTHY in Python, so reading it loosely would
        turn the classifier on for a firm whose record says the opposite."""
        for value in ("false", "true", 0, 1, "", None, [], {}):
            with self.subTest(value=value):
                with self.assertRaises(RuntimeError) as caught:
                    self._read({config.CLASSIFIER_ENABLED_FIELD: value})
                self.assertIn(config.CLASSIFIER_ENABLED_FIELD,
                              str(caught.exception))

    def test_the_live_poll_reads_the_setting(self):
        """And it is the ONLY construction site that does."""
        tree = source_guards.tree_of("app.py")
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and ast.unparse(node.func).endswith(
                    "CategorisationEngine"):
                found.append({k.arg: ast.unparse(k.value) for k in node.keywords})
        self.assertEqual(len(found), 1, "app.py builds the engine more than once")
        self.assertEqual(found[0].get("enable_ai_fallback"),
                         "config.CLASSIFIER_ENABLED")

    def test_retroactive_categorise_stays_hard_off(self):
        """Turning it on re-runs history and spends money on receipts already
        dealt with. The brief says so in terms."""
        tree = source_guards.tree_of("retroactive_categorise.py")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and ast.unparse(node.func).endswith(
                    "CategorisationEngine"):
                kw = {k.arg: ast.unparse(k.value) for k in node.keywords}
                self.assertEqual(kw.get("enable_ai_fallback"), "False")

    def test_no_environment_variable_decides_this(self):
        r"""An environment variable cannot be per firm and the cloud version is
        one service serving several firms. Amendment 340 records the refusal,
        and it was the consultant session's first recommendation.

        **Asked of the reader function itself**, not of config.py's string
        constants: the first version of this test matched the FIELD NAME,
        `classifier_enabled`, and failed on it. A field name on a firm record
        and an environment variable are different things that share a word, and
        a guard that cannot tell them apart is a guard that fails for the wrong
        reason. My own mistake, recorded rather than quietly corrected.
        """
        tree = source_guards.tree_of("config.py")
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name != "_classifier_enabled":
                continue
            reads = [ast.unparse(sub) for sub in ast.walk(node)
                     if isinstance(sub, ast.Call)
                     and ("environ" in ast.unparse(sub)
                          or "getenv" in ast.unparse(sub))]
            self.assertEqual(
                reads, [],
                f"the setting is read from the environment: {reads}. Amendment "
                "340 refused that: an environment variable cannot be per firm.")
            return
        self.fail("config.py no longer defines _classifier_enabled()")


class TheSettingIsAContractTest(unittest.TestCase):
    """The key name is written into two products by two sessions that cannot
    see each other, so it is held in one place and asserted here.

    The same reason `CLIENT_TOP_FOLDER_FIELD` and `CLIENT_COPY_TRIGGER_FIELD`
    are constants: either the two halves agree on a field name or they silently
    stop meeting.
    """

    def test_the_key_is_exactly_this(self):
        self.assertEqual(config.CLASSIFIER_ENABLED_FIELD, "classifier_enabled")

    def test_the_field_name_appears_nowhere_as_a_second_literal(self):
        tree = source_guards.tree_of("config.py")
        lines = source_guards.string_constants_equal_to(
            tree, config.CLASSIFIER_ENABLED_FIELD)
        self.assertEqual(len(lines), 1,
                         f"the key is written twice, at lines {lines}")


if __name__ == "__main__":
    unittest.main()

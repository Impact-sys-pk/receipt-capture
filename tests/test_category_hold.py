r"""A guessed category holds the receipt, and the published item says so.

Step 10l of `2026-07-25_CONSOLE_DESIGN.md`, the pipeline half. Amendment 237
decided it, 330 decided where the hold lives, 331 split it, and
`PROMPT_claude_code_2026-09-11_category_hold.md` is the brief.

## The receipt this exists to stop

**A receipt whose figures are perfect and whose category is a machine's answer
reaches the client's books today with nobody having looked at the category.**
`validation.status` carries an arithmetic meaning, supplier and date and net plus
VAT against gross, and a guessed category makes none of those wrong. So the
receipt is `ok`, `drainInbox()` routes on `s.validation` alone, and it becomes a
books row with the guess attached.

## The contract this module holds

**`category_unconfirmed`, a JSON boolean, on every published item.**
`worker\publish.py` owns the name as a constant, for the reason
`IMAGE_KEY` and `NOTES_KEY` are constants: the other end of the contract is
written by a session that cannot see this file, and a rename that goes half done
makes two products that silently stop meeting.

**Why not `category_needs_review`.** Desktop already tests
`s==="needs_review"` against a **validation status**, at line 3184 of
`IntelliBooks-Desktop-v3.html`. Two keys one word apart meaning different things
is the `postTxn()` and `postReceiptToCashbook()` trap `CLAUDE.md` names.
`category_unconfirmed` also matches amendment 330's screen wording exactly,
`Category unconfirmed`.

**Why the positive sense and not `category_confirmed`.** A missing key must not
hold a receipt that is fine, which is the rule `drainInbox()` already follows for
a blank validation status. `undefined` is falsy, so an absent
`category_unconfirmed` reads as "not held" with no special case in the reader,
while an absent `category_confirmed` would read as "not confirmed" and hold every
item written before the key existed.

## One value decides it, in one place

`publish.category_is_unconfirmed()` is the whole trigger, and it takes the
categorisation object rather than a boolean so no call site can pass the wrong
answer.

## It reads `match_source`, and it did not always

**Amendment 333, Paul's decision of 2026-09-12, which amends his own of
2026-09-11.** ~~The hold reads `categorisations.needs_review`.~~ **Amendment
330's first point is superseded.** `category_unconfirmed` is true where **a
machine produced a category** and nobody has confirmed it, and nothing else.

**What decided it was that `needs_review` is true for three more things.**
`PerLayerTest` below drove every layer through the real engine and reported it,
and amendment 330 had been taken without that being read:

| Layer | `match_source` | `needs_review` | Holds now |
|---|---|---|---|
| 0 rule | `rule` | False | no |
| 1 client exact | `client` | False | no |
| 2 firm exact | `firm` | False | no |
| 3 fuzzy client | `fuzzy_client` | True | **yes** |
| 4 fuzzy firm | `fuzzy_firm` | True | **yes** |
| 5 AI | `ai` | True | **yes** |
| no match | `unmatched` | True | **no** |

**An unmatched receipt is not a guess.** It carries no category at all, the empty
field says so on screen, and it is already in the uncategorised count. Holding it
would also stop it draining into the books, which moves where nearly all the work
happens as a side effect of a decision aimed at the classifier.

**And `resolve_against_chart()` no longer holds anything.** It forces
`needs_review` True on an unreadable bundle and on an unusable code, and it
leaves `match_source` alone, so a trigger reading `match_source` does not fire
on a hand-taught mapping when the chart is missing. That was flag 2 of
`2026-09-11_REPORT_claude_code_category_hold.md` and amendment 333 disposes of
it. `TheReadableChartTest` below holds the inversion.
"""

import ast
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
import source_guards  # noqa: E402
from chart_fixtures import TempChartBundle  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    with_email_client,
)
from worker import publish  # noqa: E402
from worker.categorisation.engine import CategorisationEngine  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

CLIENT = "CLIENT001"
TRADE = "PHV_DRIVER"
NOW = "2026-09-11T00:00:00+00:00"

#: One extraction result per validation outcome, the same three
#: `tests/test_stage4_client_copy.py` uses.
OUTCOMES = {
    "ok": extraction_result(),
    "needs_review": extraction_result(gross_amount=99.0),
    "failed": extraction_result(gross_amount=None),
}


def receipts():
    repo = Repository()
    try:
        return [dict(r) for r in repo._conn.execute(
            "SELECT * FROM receipts ORDER BY created_at")]
    finally:
        repo.close()


def extractions():
    repo = Repository()
    try:
        return [dict(r) for r in repo._conn.execute(
            "SELECT * FROM extractions ORDER BY extracted_at")]
    finally:
        repo.close()


def categorisations():
    repo = Repository()
    try:
        return [dict(r) for r in repo._conn.execute(
            "SELECT * FROM categorisations ORDER BY categorised_at")]
    finally:
        repo.close()


def item_for(receipt_id):
    return json.loads(
        (config.INTELLIBOOKS_PUBLISH_DIR / f"{receipt_id}.json")
        .read_text(encoding="utf-8"))


def raw_item_text(receipt_id):
    """The item's bytes, so the JSON spelling of the value can be asserted."""
    return (config.INTELLIBOOKS_PUBLISH_DIR / f"{receipt_id}.json") \
        .read_text(encoding="utf-8")


def drive(test_case, outcome, client_id=CLIENT):
    with_email_client(test_case, client_id)
    Routes(RecordingExtractor(OUTCOMES[outcome])).email_attachment()


def production_files():
    r"""`app.py`, the root scripts and the `worker\` tree.

    Not `docs\specs\categorisation_engine.py`, which is the v0.1 prototype and
    which nothing imports. Counting it as production was my own error on
    2026-09-11 and it inflated an enumeration by six.
    """
    root = source_guards.REPO_ROOT
    return sorted(root.glob("*.py")) + sorted(root.glob("worker/**/*.py"))


def categorise(repo, supplier, ai=False):
    """One real categorisation, through the real engine."""
    engine = CategorisationEngine(repo=repo, enable_ai_fallback=ai)
    if ai:
        engine._ai_suggest = lambda *a, **k: {"code": "7500", "name": "Sundries"}
    return engine.categorise(
        receipt_id="r", extraction_id="e", supplier_name=supplier,
        client_id=CLIENT, business_type=TRADE, gross_amount=10.0)


# ---------------------------------------------------------------------------
# What the engine writes, per layer, measured
# ---------------------------------------------------------------------------

class PerLayerTest(unittest.TestCase):
    """The table in the module docstring, driven rather than read.

    **This is the evidence for the whole contract**, because the hold is
    `categorisations.needs_review` per amendment 330 and this is what that column
    actually holds. It is also the evidence for the divergence reported against
    the brief's section 6, which expected layers 0 to 4 not to hold.

    **This is the engine's own answer, before `resolve_against_chart()` runs.**
    That function forces `needs_review` True on two further outcomes, and one of
    them is an unreadable chart, so the answer a published item carries can be
    True where the table below says False. `TheUnreadableChartTest` holds that
    case separately rather than muddying this one.
    """

    def test_layers_nought_to_two_do_not_need_review(self):
        with TempEnvironment():
            repo = Repository()
            try:
                repo.upsert_firm_vendor(TRADE, "apcoa", "7300", "Parking", NOW,
                                        vendor_name="Apcoa")
                firm = categorise(repo, "Apcoa Parking Leeds")
                with self.subTest(layer="2 firm exact"):
                    self.assertEqual(firm.match_source, "firm")
                    self.assertFalse(firm.needs_review)

                repo.upsert_client_vendor(CLIENT, "apcoa", "7301", "Parking", NOW,
                                          vendor_name="Apcoa")
                client = categorise(repo, "Apcoa Parking Leeds")
                with self.subTest(layer="1 client exact"):
                    self.assertEqual(client.match_source, "client")
                    self.assertFalse(client.needs_review)

                repo.create_client_rule("rule-1", CLIENT, "always parking", 90,
                                        None, "contains", "detail", "apcoa",
                                        "7400", "Fuel")
                rule = categorise(repo, "Apcoa Parking Leeds")
                with self.subTest(layer="0 rule"):
                    self.assertEqual(rule.match_source, "rule")
                    self.assertFalse(rule.needs_review)
            finally:
                repo.close()

    def test_layers_three_four_and_five_all_need_review(self):
        """**The brief's section 6 expected 3 and 4 not to.** They do."""
        with TempEnvironment():
            repo = Repository()
            try:
                repo.upsert_client_vendor(CLIENT, "shell", "7400", "Fuel", NOW,
                                          vendor_name="Shell")
                fuzzy_client = categorise(repo, "Shel")
                with self.subTest(layer="3 fuzzy client"):
                    self.assertEqual(fuzzy_client.match_source, "fuzzy_client")
                    self.assertTrue(fuzzy_client.needs_review)
            finally:
                repo.close()

        with TempEnvironment():
            repo = Repository()
            try:
                repo.upsert_firm_vendor(TRADE, "shell", "7400", "Fuel", NOW,
                                        vendor_name="Shell")
                fuzzy_firm = categorise(repo, "Shel")
                with self.subTest(layer="4 fuzzy firm"):
                    self.assertEqual(fuzzy_firm.match_source, "fuzzy_firm")
                    self.assertTrue(fuzzy_firm.needs_review)

                ai = categorise(repo, "Something Unseen Ltd", ai=True)
                with self.subTest(layer="5 ai"):
                    self.assertEqual(ai.match_source, "ai")
                    self.assertTrue(ai.needs_review)

                unmatched = categorise(repo, "Something Unseen Ltd")
                with self.subTest(layer="no match"):
                    self.assertEqual(unmatched.match_source, "unmatched")
                    self.assertTrue(unmatched.needs_review)
            finally:
                repo.close()

    def test_the_trigger_holds_exactly_the_three_machine_answers(self):
        """Amendment 333. Every layer, through the real engine, against the
        trigger, with the expected answer written per layer rather than derived
        from the thing being tested.
        """
        expected = {
            "rule": False,
            "client": False,
            "firm": False,
            "fuzzy_client": True,
            "fuzzy_firm": True,
            "ai": True,
            "unmatched": False,
        }
        seen = {}
        with TempEnvironment():
            repo = Repository()
            try:
                repo.upsert_firm_vendor(TRADE, "shell", "7400", "Fuel", NOW,
                                        vendor_name="Shell")
                repo.upsert_client_vendor(CLIENT, "apcoa parking", "7300",
                                          "Parking", NOW,
                                          vendor_name="Apcoa Parking")
                repo.create_client_rule("rule-1", CLIENT, "always fuel", 90,
                                        None, "contains", "detail", "esso",
                                        "7400", "Fuel")
                cases = (("Esso Garage", False), ("Apcoa Parking", False),
                         ("Shell", False), ("Apcoa Parkin", False),
                         ("Shel", False), ("Unseen Ltd", True),
                         ("Unseen Ltd", False))
                for supplier, ai in cases:
                    result = categorise(repo, supplier, ai=ai)
                    seen[result.match_source] = result
            finally:
                repo.close()

        self.assertEqual(
            set(seen), set(expected),
            "the seven cases above no longer produce the seven match_source "
            f"values between them; produced {sorted(seen)}")
        for source, result in sorted(seen.items()):
            with self.subTest(source=source):
                self.assertIs(publish.category_is_unconfirmed(result),
                              expected[source])

    def test_the_trigger_no_longer_tracks_the_needs_review_column(self):
        """The two disagree on `unmatched`, and that disagreement IS amendment
        333. A test asserting they agree would pass again if the trigger were
        reverted, so this one asserts they differ where the decision says.
        """
        with TempEnvironment():
            repo = Repository()
            try:
                result = categorise(repo, "Unseen Ltd")
            finally:
                repo.close()
        self.assertEqual(result.match_source, "unmatched")
        self.assertTrue(result.needs_review,
                        "the column is unchanged: amendment 333 moves the "
                        "trigger, not the column")
        self.assertIs(publish.category_is_unconfirmed(result), False,
                      "an unmatched receipt is not a guess and must not hold")


# ---------------------------------------------------------------------------
# The vocabulary the trigger partitions
# ---------------------------------------------------------------------------

class MatchSourceSetTest(unittest.TestCase):
    r"""Every `match_source` value, enumerated from the engine's syntax tree.

    **Amendment 333 asks for this by name**, so that a value added to the engine
    later fails a test rather than falling silently into one side of the
    trigger. A new value in neither set below is neither held nor confirmed by
    anyone's decision; it simply would not hold, and that quiet default is what
    this guard exists to prevent.

    **From the tree and not by grep.** This project keeps superseded wording
    beside every correction, so a text search for `match_source` returns the
    prose about it too, and `worker\categorisation\fallback.py`'s docstring
    discusses the field at length precisely because it does not write it.

    **The partition lives here rather than in `worker\publish.py`**, which
    states only the holding half. That follows this project's own convention:
    `ClientFolderWritersTest.ALLOWED` and `TheSweepsTest`'s expected set are
    both held in a test with the reasoning beside them, because the claim being
    made is "somebody considered every member", which is a statement about a
    decision rather than about the module's behaviour.
    """

    #: A machine chose which account this is, and nobody has confirmed it.
    #: Amendment 333. Written out independently of
    #: `publish.MACHINE_MATCH_SOURCES`, so a change to that constant fails here
    #: rather than agreeing with itself.
    HOLDS = {"fuzzy_client", "fuzzy_firm", "ai"}

    #: A person's answer, or no answer at all.
    #:
    #: `rule` is a rule somebody wrote. `client` and `firm` are stored mappings
    #: somebody taught. **`unmatched` is the one worth explaining**: it carries
    #: no category, so there is no guess to confirm, the empty field already
    #: says so on screen, and holding it would stop it draining into the books
    #: at all. Whether uncategorised receipts should be held at the door is a
    #: separate decision and it has not been taken.
    DOES_NOT_HOLD = {"rule", "client", "firm", "unmatched"}

    @staticmethod
    def engine_match_sources():
        """Every string literal the engine assigns to `match_source`."""
        tree = source_guards.tree_of("worker", "categorisation", "engine.py")
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if (kw.arg == "match_source"
                            and isinstance(kw.value, ast.Constant)
                            and isinstance(kw.value.value, str)):
                        found.add(kw.value.value)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (isinstance(target, ast.Attribute)
                            and target.attr == "match_source"
                            and isinstance(node.value, ast.Constant)
                            and isinstance(node.value.value, str)):
                        found.add(node.value.value)
        return found

    def test_the_two_sets_partition_the_engines_whole_vocabulary(self):
        found = self.engine_match_sources()
        decided = self.HOLDS | self.DOES_NOT_HOLD
        self.assertEqual(
            found, decided,
            "the engine's match_source vocabulary and the decided sets "
            "disagree.\n"
            f"  written by the engine ({len(found)}): {sorted(found)}\n"
            f"  decided here ({len(decided)}): {sorted(decided)}\n"
            f"  in the engine and undecided: {sorted(found - decided)}\n"
            f"  decided and no longer written: {sorted(decided - found)}\n"
            "A new value has to go in one set or the other deliberately. Left "
            "alone it would simply not hold, which is a decision nobody took.")

    def test_the_two_sets_do_not_overlap(self):
        self.assertEqual(self.HOLDS & self.DOES_NOT_HOLD, set())

    def test_publish_holds_exactly_the_machine_set(self):
        r"""`worker\publish.py`'s constant against this file's own copy.

        Two independent statements of one set. A check that read the constant
        and compared it with itself could not fail, which is the tell
        `CLAUDE.md` names.
        """
        self.assertEqual(set(publish.MACHINE_MATCH_SOURCES), self.HOLDS)

    def test_the_enumeration_is_not_silently_empty(self):
        """A sweep matching nothing would pass the partition test if both sets
        were emptied to match. `CLAUDE.md`: a check that cannot fail is not a
        check."""
        found = self.engine_match_sources()
        self.assertEqual(len(found), 7, sorted(found))
        for known in ("rule", "client", "firm", "fuzzy_client", "fuzzy_firm",
                      "ai", "unmatched"):
            with self.subTest(value=known):
                self.assertIn(known, found)

    def test_nothing_outside_the_engine_writes_a_match_source_literal(self):
        r"""The vocabulary is the engine's alone, which is what makes reading
        one file enough.

        `resolve_against_chart()` says in its docstring that it leaves
        `match_source` alone in every case, including `unusable`. This is that
        claim tested rather than quoted. The five writes elsewhere all pass
        `categorisation.match_source` straight into `save_categorisation()`.
        """
        strays = []
        for path in production_files():
            if path.parts[-3:] == ("worker", "categorisation", "engine.py"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    for kw in node.keywords:
                        if (kw.arg == "match_source"
                                and isinstance(kw.value, ast.Constant)):
                            strays.append(
                                f"{path.name}:{node.lineno} "
                                f"match_source={kw.value.value!r}")
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (isinstance(target, ast.Attribute)
                                and target.attr == "match_source"
                                and isinstance(node.value, ast.Constant)):
                            strays.append(
                                f"{path.name}:{node.lineno} "
                                f"{ast.unparse(target)} = {node.value.value!r}")
        self.assertEqual(strays, [], "\n".join(strays))


# ---------------------------------------------------------------------------
# The key on a published item
# ---------------------------------------------------------------------------

class TheKeyTest(unittest.TestCase):

    def test_a_guessed_category_publishes_the_key_true(self):
        """Layer 3. A near-miss mapping, so the machine chose which one it meant.

        **`apcoa parkin` and not `apcoa parking`.** The fixture's supplier keys
        on `apcoa parking`, so an exact seed would answer at layer 1 and this
        test would assert the opposite of what it means to. The near miss scores
        0.96, which is over the 0.70 threshold, measured rather than assumed.
        """
        with TempEnvironment():
            repo = Repository()
            try:
                repo.upsert_client_vendor(CLIENT, "apcoa parkin", "7300",
                                          "Parking", NOW,
                                          vendor_name="Apcoa Parkin")
            finally:
                repo.close()
            drive(self, "ok")
            receipt, = receipts()
            self.assertEqual(receipt["status"], "ok")
            row, = categorisations()
            self.assertEqual(row["match_source"], "fuzzy_client")
            item = item_for(receipt["receipt_id"])
            self.assertIs(item[publish.CATEGORY_UNCONFIRMED_KEY], True)

    def test_an_unmatched_receipt_publishes_the_key_false(self):
        """Amendment 333, and the row it turns on. No mappings at all.

        The column still says the categorisation needs review; the item says the
        receipt must not be held for it. An unmatched receipt carries no
        category, so there is no guess to confirm, and holding it would stop it
        draining into the books at all.
        """
        with TempEnvironment():
            drive(self, "ok")
            receipt, = receipts()
            row, = categorisations()
            self.assertEqual(row["match_source"], "unmatched")
            self.assertEqual(row["needs_review"], 1, "the column is unchanged")
            item = item_for(receipt["receipt_id"])
            self.assertIs(item[publish.CATEGORY_UNCONFIRMED_KEY], False)

    def test_a_category_from_an_exact_match_publishes_the_key_false(self):
        """Layer 1. A stored mapping is a person's earlier answer, so nothing
        is unconfirmed and the receipt must not hold.

        **`TempChartBundle` is not decoration here and this test failed without
        it.** `resolve_against_chart()` forces `needs_review` True when the
        client's chart cannot be read, so with no bundle every categorisation
        holds, layer 1 included. That is deliberate in `fallback.py` and it is
        the flag this work reports: it was harmless while nothing read the
        column and it is not harmless now. `TheUnreadableChartTest` below holds
        the behaviour so the flag cannot be lost.
        """
        with TempEnvironment(), TempChartBundle(accounts=(("7300", "Parking"),)):
            repo = Repository()
            try:
                # **`"apcoa parking"` and not `"apcoa"`.** The fixture's
                # supplier is `Apcoa Parking`, two words, and
                # `extract_vendor_key()` keeps both; `Apcoa Parking Leeds`,
                # three words, keys on `apcoa` alone. Measured rather than
                # guessed, having guessed it wrong first and been caught by
                # this test asserting `unmatched`.
                repo.upsert_client_vendor(
                    CLIENT, "apcoa parking", "7300", "Parking", NOW,
                    vendor_name="Apcoa Parking")
            finally:
                repo.close()
            drive(self, "ok")
            receipt, = receipts()
            row, = categorisations()
            self.assertEqual(row["match_source"], "client")
            self.assertEqual(row["needs_review"], 0)
            item = item_for(receipt["receipt_id"])
            self.assertIs(item[publish.CATEGORY_UNCONFIRMED_KEY], False)

    def test_every_item_carries_the_key_whatever_the_status(self):
        """On every item, not only the held ones. `NOTES_KEY`'s reasoning:
        a reader must never have to tell "not held" from "an old item"."""
        for outcome in ("ok", "needs_review", "failed"):
            with self.subTest(outcome=outcome):
                with TempEnvironment():
                    drive(self, outcome)
                    receipt, = receipts()
                    item = item_for(receipt["receipt_id"])
                    self.assertIn(publish.CATEGORY_UNCONFIRMED_KEY, item)
                    self.assertIsInstance(
                        item[publish.CATEGORY_UNCONFIRMED_KEY], bool)

    def test_an_uncategorised_receipt_says_the_category_is_not_unconfirmed(self):
        """A receipt that is not `ok` is never categorised at all, so there is
        no category to be unconfirmed about. The item is held by its validation
        status, which is a different question and is not this key's job."""
        with TempEnvironment():
            drive(self, "failed")
            receipt, = receipts()
            self.assertEqual(categorisations(), [])
            item = item_for(receipt["receipt_id"])
            self.assertIs(item[publish.CATEGORY_UNCONFIRMED_KEY], False)
            self.assertEqual(item["validation_status"], "failed")

    def test_the_value_is_a_json_boolean_and_not_one_or_nought(self):
        """**Desktop is JavaScript and `1 === true` is false there.**

        The database stores the column as 0 or 1, so a value passed through
        without coercion would publish as a number and a reader testing
        `=== true` would never hold anything. The reader has to be able to test
        identity, because that is what gives the blank case for free.

        Seeded to a fuzzy match so the value under test is `true`: since
        amendment 333 an unmatched receipt publishes `false`, and asserting the
        spelling of `false` would not catch a `0` published as the truthy case.
        """
        with TempEnvironment():
            repo = Repository()
            try:
                repo.upsert_client_vendor(CLIENT, "apcoa parkin", "7300",
                                          "Parking", NOW,
                                          vendor_name="Apcoa Parkin")
            finally:
                repo.close()
            drive(self, "ok")
            receipt, = receipts()
            text = raw_item_text(receipt["receipt_id"])
            self.assertIn(f'"{publish.CATEGORY_UNCONFIRMED_KEY}": true'
                          .replace(": ", ":"), text.replace(": ", ":"))
            self.assertNotIn(f'"{publish.CATEGORY_UNCONFIRMED_KEY}":1',
                             text.replace(": ", ":"))


# ---------------------------------------------------------------------------
# The chart check no longer holds anything
# ---------------------------------------------------------------------------

class TheReadableChartTest(unittest.TestCase):
    r"""An unreadable chart holds nothing, and that is amendment 333's point 3.

    ~~`TheUnreadableChartTest`: an unreadable chart holds every receipt, layer 1
    included.~~ **Inverted 2026-09-12 by amendment 333, deliberately and not by
    accident.** The old class asserted the behaviour that flag 2 of
    `2026-09-11_REPORT_claude_code_category_hold.md` reported: under amendment
    330 a missing or mid-sync chart bundle held every receipt in the practice,
    because `resolve_against_chart()` forces `needs_review` True on an
    unreadable bundle whatever the layer.

    **`resolve_against_chart()` is unchanged and still forces the column.** What
    changed is what the trigger reads. That function leaves `match_source`
    alone, in every one of its five outcomes and by its own docstring, so a
    trigger reading `match_source` cannot fire on a hand-taught layer 1 mapping
    just because the chart could not be read. **The flag is disposed of by the
    decision rather than by a second change.**

    Both halves are kept: the same receipt with a readable bundle, and with
    none. Without the pair, the first would prove only that something was False.
    """

    def test_an_exact_match_with_no_chart_does_not_hold(self):
        with TempEnvironment():
            repo = Repository()
            try:
                repo.upsert_client_vendor(
                    CLIENT, "apcoa parking", "7300", "Parking", NOW,
                    vendor_name="Apcoa Parking")
            finally:
                repo.close()
            drive(self, "ok")
            row, = categorisations()
            receipt, = receipts()
            self.assertEqual(row["match_source"], "client",
                             "the layer is still recorded as the one that answered")
            self.assertEqual(row["needs_review"], 1,
                             "the chart forcing is unchanged: it still sets the "
                             "column, and the trigger no longer reads it")
            self.assertIs(
                item_for(receipt["receipt_id"])[publish.CATEGORY_UNCONFIRMED_KEY],
                False,
                "a hand-taught mapping must not be held because the chart is "
                "missing")

    def test_the_same_receipt_does_not_hold_when_the_chart_reads_either(self):
        """The control. The two now agree, which is the whole change: before
        amendment 333 they differed and the bundle decided."""
        with TempEnvironment(), TempChartBundle(accounts=(("7300", "Parking"),)):
            repo = Repository()
            try:
                repo.upsert_client_vendor(
                    CLIENT, "apcoa parking", "7300", "Parking", NOW,
                    vendor_name="Apcoa Parking")
            finally:
                repo.close()
            drive(self, "ok")
            row, = categorisations()
            receipt, = receipts()
            self.assertEqual(row["needs_review"], 0)
            self.assertIs(
                item_for(receipt["receipt_id"])[publish.CATEGORY_UNCONFIRMED_KEY],
                False)

    def test_a_fuzzy_match_holds_whether_the_chart_reads_or_not(self):
        """And the other side of it: the bundle decides nothing either way now."""
        for label, bundle in (("no bundle", None),
                              ("readable bundle",
                               TempChartBundle(accounts=(("7300", "Parking"),)))):
            with self.subTest(chart=label):
                with TempEnvironment():
                    repo = Repository()
                    try:
                        repo.upsert_client_vendor(
                            CLIENT, "apcoa parkin", "7300", "Parking", NOW,
                            vendor_name="Apcoa Parkin")
                    finally:
                        repo.close()
                    if bundle is None:
                        drive(self, "ok")
                    else:
                        with bundle:
                            drive(self, "ok")
                    row, = categorisations()
                    receipt, = receipts()
                    self.assertEqual(row["match_source"], "fuzzy_client")
                    self.assertIs(
                        item_for(receipt["receipt_id"])[
                            publish.CATEGORY_UNCONFIRMED_KEY],
                        True)


# ---------------------------------------------------------------------------
# The blank case, and the set of call sites
# ---------------------------------------------------------------------------

class BlankAndSetTest(unittest.TestCase):

    def test_an_item_built_with_no_extra_carries_no_such_key(self):
        """The item written before this change. It must read as not held, which
        on the other side is `data[KEY] === true` returning false for
        `undefined`. Nothing here can assert Desktop's half; what it asserts is
        that the pipeline genuinely produced such items and can again."""
        with TempEnvironment():
            document = next(iter(config.FILES_DIR.glob("**/*")), None) \
                if config.FILES_DIR.exists() else None
            if document is None:
                config.FILES_DIR.mkdir(parents=True, exist_ok=True)
                document = config.FILES_DIR / "old.pdf"
                document.write_bytes(b"%PDF-1.4 old item")
            item = publish.build_item({"receipt_id": "r-old"}, document)
            self.assertNotIn(publish.CATEGORY_UNCONFIRMED_KEY, item)

    def test_item_only_keys_is_exactly_what_the_item_adds(self):
        """The set claim, computed from `build_item()` rather than listed.

        `publish.ITEM_ONLY_KEYS` exists because
        `tests/test_sidecar_category_keys.py` had the four written out and step
        10l added a fifth, which made a new item key count as a sidecar key and
        failed a comparison that had nothing to do with this work. **A tuple is
        only better than a list in a test if something holds it to the truth**,
        so this subtracts the sidecar's keys from a real item and asserts the
        difference.
        """
        with TempEnvironment():
            config.FILES_DIR.mkdir(parents=True, exist_ok=True)
            document = config.FILES_DIR / "doc.pdf"
            document.write_bytes(b"%PDF-1.4 test")
            sidecar = {"receipt_id": "r-1", "supplier": "Apcoa Parking",
                       "validation_status": "possible_duplicate"}
            item = publish.build_item(
                sidecar, document,
                publish.extra_for(["a note"], duplicate_of="r-0"))
            self.assertEqual(
                set(item) - set(sidecar), set(publish.ITEM_ONLY_KEYS),
                "publish.ITEM_ONLY_KEYS no longer names exactly what a "
                "published item adds on top of the sidecar")

    def test_extra_for_defaults_to_not_unconfirmed(self):
        """A caller that says nothing must not hold a receipt."""
        extra = publish.extra_for([])
        self.assertIs(extra[publish.CATEGORY_UNCONFIRMED_KEY], False)

    def test_category_is_unconfirmed_of_nothing_is_false(self):
        self.assertIs(publish.category_is_unconfirmed(None), False)

    def test_every_extra_for_call_site_passes_the_categorisation(self):
        """The set claim, enumerated from the syntax tree and printed whole.

        `extra_for()` is the one builder of these keys and it has two callers.
        A per-path test proves a path; only a guard over the set proves the set,
        which is `CLAUDE.md`'s rule about `extract_with_transient_retry()` and
        the fourth intake path nobody noticed for weeks.
        """
        found = []
        for path in source_guards.REPO_ROOT.glob("*.py"):
            found.extend(self._sites(path))
        for path in source_guards.REPO_ROOT.glob("worker/**/*.py"):
            found.extend(self._sites(path))
        listing = "\n".join(f"  {where}: {text}" for where, text in found)
        self.assertEqual(
            len(found), 2,
            f"extra_for() has {len(found)} call sites and two are expected. "
            f"A new one that does not pass a categorisation publishes an item "
            f"that can never hold.\n{listing}")
        for where, text in found:
            with self.subTest(site=where):
                self.assertIn("categorisation", text,
                              f"{where} does not pass a categorisation: {text}")

    @staticmethod
    def _sites(path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        out = []
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and ast.unparse(node.func).split(".")[-1] == "extra_for"):
                out.append((f"{path.relative_to(source_guards.REPO_ROOT)}"
                            f":{node.lineno}", ast.unparse(node)))
        return out


# ---------------------------------------------------------------------------
# Nothing about the figures moved
# ---------------------------------------------------------------------------

class ValidationDidNotMoveTest(unittest.TestCase):
    """`validation.status` keeps its arithmetic meaning. Section 5 of the brief
    and amendment 330's first point."""

    def test_a_held_category_leaves_the_receipt_status_ok(self):
        """Seeded to a fuzzy match so the receipt really is held. It used to
        drive an unmatched one and call that held, which stopped being true at
        amendment 333."""
        with TempEnvironment():
            repo = Repository()
            try:
                repo.upsert_client_vendor(CLIENT, "apcoa parkin", "7300",
                                          "Parking", NOW,
                                          vendor_name="Apcoa Parkin")
            finally:
                repo.close()
            drive(self, "ok")
            receipt, = receipts()
            extraction, = extractions()
            row, = categorisations()
            self.assertEqual(row["match_source"], "fuzzy_client")
            self.assertIs(
                item_for(receipt["receipt_id"])[publish.CATEGORY_UNCONFIRMED_KEY],
                True, "the category is held")
            self.assertEqual(receipt["status"], "ok")
            self.assertEqual(extraction["validation_status"], "ok")

    def test_an_exact_match_leaves_the_receipt_status_ok_too(self):
        with TempEnvironment():
            repo = Repository()
            try:
                # **`"apcoa parking"` and not `"apcoa"`.** The fixture's
                # supplier is `Apcoa Parking`, two words, and
                # `extract_vendor_key()` keeps both; `Apcoa Parking Leeds`,
                # three words, keys on `apcoa` alone. Measured rather than
                # guessed, having guessed it wrong first and been caught by
                # this test asserting `unmatched`.
                repo.upsert_client_vendor(
                    CLIENT, "apcoa parking", "7300", "Parking", NOW,
                    vendor_name="Apcoa Parking")
            finally:
                repo.close()
            drive(self, "ok")
            receipt, = receipts()
            extraction, = extractions()
            self.assertEqual(receipt["status"], "ok")
            self.assertEqual(extraction["validation_status"], "ok")

    def test_the_three_statuses_are_unchanged_by_this_work(self):
        for outcome in ("ok", "needs_review", "failed"):
            with self.subTest(outcome=outcome):
                with TempEnvironment():
                    drive(self, outcome)
                    receipt, = receipts()
                    extraction, = extractions()
                    self.assertEqual(receipt["status"], outcome)
                    self.assertEqual(extraction["validation_status"], outcome)

    def test_validation_rules_never_mention_a_category(self):
        """The one field keeps one meaning, asked of the tree rather than read.

        `worker\\validation\\rules.py` decides `validation.status` from the
        figures. A category reaching it would be the overload amendment 237
        flagged and amendment 330 refused.
        """
        tree = source_guards.tree_of("worker", "validation", "rules.py")
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id)
            if isinstance(node, ast.Attribute):
                names.add(node.attr)
        for forbidden in ("needs_review_category", "match_source",
                          "categorisation", "category_unconfirmed",
                          "suggested_code"):
            with self.subTest(name=forbidden):
                self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()

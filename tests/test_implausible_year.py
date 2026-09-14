"""The implausible year guard: one rule, one helper, three doors.

**Paul's decision, 2026-09-14, corrected the same day.** An `invoice_date` whose
year is before 2000 or later than next year is not readable. ~~later than the
current year~~ **The ceiling is the current year PLUS ONE**, because
**IntelliBooks Desktop has shipped exactly that rule since 2026-09-06** and two
products built by sessions that cannot see each other have to agree on the
boundary. The pipeline takes Desktop's, which is the one already in front of the
operator.

`badYear()` in `IntelliBooks-Desktop-v3.html`, read rather than taken on trust:

    if(y>=2000&&y<=new Date().getFullYear()+1)return false;

Its own comment names this same incident, and its last two lines are the
reasoning this file inherits: "The rule is the year alone: four digits, this
century, and not more than one year ahead. A date genuinely before 2000 is not a
case this system has."

## Why it exists, and it is not hypothetical

Receipt `abe4a034-878b-43cd-965d-e4096b5a6bcd`, Client_001, is filed in the live
database at
`Clients\\TEST\\IntelliBooks\\Receipts\\26-27\\0026-08-30_IMO-CAR-WASH_24.00.png`.
Its first extraction carried no `invoice_date` and it went to Review. It was
completed in IntelliBooks Desktop, somebody typed a two-digit year into a date
field, the browser made it year 26, and the `manual_correction` row carries
`invoice_date = '0026-08-30'`. `determine_tax_year()` then composed `26-27` from
it. **Nothing between the keystroke and the folder name questioned the year.**

## What is held here

**Three doors accept a four-digit year, and each one now asks the same
question.** `validate()` in `worker\\validation\\rules.py` on the extraction
path; `parse_corrections()` in `worker\\resolution\\service.py`, the CLI route;
and `parse_resolution_note()` in the same file, the back-feed note validator,
which is the route this receipt actually came through.

**The extraction path gets the treatment an invalid date already gets**, which
is a note naming the year and a route to Review. It is not silently corrected
and no century is inferred: 10d.41's reasoning applies unchanged, a pivot tight
enough to read 99 as 1999 reads 28 as 1928.

**The two correction doors raise the error each already raises for a date that
is not a real calendar date**, worded the same way as each other and naming the
year that was supplied.

**One helper holds the bound and `TheSetOfDoorsTest` asserts the set**, so a
fourth door added later goes red rather than passing. That guard is
`tests/test_delivery_log.py`'s `OneWriterTest` in a different subject.

## The one place that is deliberately stricter

**Sub-step 10d.41's two-digit branch in `worker\\extraction\\postprocess.py` is
left exactly as it is, refusing anything past the current year**, and that is a
decision rather than an inconsistency nobody noticed. `2000 + c` is an inference
the system made from two digits; a four-digit year is a figure somebody stated.
The system may be stricter with its own guesses than with a person's statement.
`TenD41IsLeftStricterTest` holds that difference so a later session does not
tidy it away.

## What is deliberately not here

`determine_tax_year()` is unchanged and the row on disk is not repaired. That
receipt is test data and step 10i clears it.
"""

import ast
import subprocess
import unittest
from datetime import date

from tests import source_guards
from worker.extraction.base import ExtractionResult
from worker.extraction.postprocess import parse_ambiguous_date
from worker.resolution.service import (
    ResolutionNoteError,
    parse_corrections,
    parse_resolution_note,
)
from worker.validation import rules
from worker.validation.rules import validate

#: The value that is actually on the row, typed by a person into Desktop.
THE_REAL_ONE = "0026-08-30"


def extraction(invoice_date, supplier_name="Imo Car Wash", gross_amount=24.00):
    """An extraction result that passes every check but the one under test."""
    return ExtractionResult(
        supplier_name=supplier_name,
        invoice_date=invoice_date,
        net_amount=None,
        vat_amount=None,
        gross_amount=gross_amount,
        currency="GBP",
        raw_response={},
        engine="test",
    )


def note_payload(invoice_date):
    """A `filed` back-feed note carrying that date. Design document 12.2."""
    return {
        "schema": 1,
        "action": "filed",
        "resolved_at": "2026-09-14T10:00:00+00:00",
        "receipt_id": "abe4a034-878b-43cd-965d-e4096b5a6bcd",
        "values": {
            "supplier_name": "Imo Car Wash",
            "invoice_date": invoice_date,
            "gross_amount": 24.00,
        },
    }


class TheRuleTest(unittest.TestCase):
    """The bound itself, which lives in exactly one function."""

    def test_the_floor_is_2000_inclusive(self):
        self.assertFalse(rules.year_is_readable(1999))
        self.assertTrue(rules.year_is_readable(2000))

    def test_the_ceiling_is_next_year_inclusive(self):
        """Desktop's `+1`, not the current year.

        The two products have to agree on the boundary, and Desktop's is the
        one already in front of the operator. A receipt dated in January that
        arrives in the December before it is the case the extra year is for.
        """
        this_year = date.today().year
        self.assertTrue(rules.year_is_readable(this_year))
        self.assertTrue(rules.year_is_readable(this_year + 1))
        self.assertFalse(rules.year_is_readable(this_year + 2))

    def test_the_year_the_receipt_carries_is_refused(self):
        self.assertFalse(rules.year_is_readable(26))

    def test_the_current_year_is_read_when_the_check_runs(self):
        """Not at import, which is Paul's instruction of 2026-09-14.

        A module-level `date.today().year` would fix the ceiling at whatever
        year the process started, so a pipeline left running across New Year
        would refuse January's receipts. Held by moving the clock rather than
        by reading the source, because the source can be right and the value
        still captured by a default argument.
        """
        class Clock:
            @staticmethod
            def today():
                return date(2030, 1, 1)

        original = rules.date
        rules.date = Clock
        try:
            self.assertTrue(rules.year_is_readable(2030))
            self.assertTrue(rules.year_is_readable(2031))
            self.assertFalse(rules.year_is_readable(2032))
        finally:
            rules.date = original

    def test_unreadable_year_returns_the_year_or_none(self):
        self.assertEqual(rules.unreadable_year(THE_REAL_ONE), 26)
        self.assertIsNone(rules.unreadable_year("2026-08-30"))

    def test_unreadable_year_says_nothing_about_a_date_that_is_not_a_date(self):
        """Not this helper's error to raise, and not its place to duplicate one.

        Every door already refuses a date that is not a real calendar date, with
        its own wording. A helper that also refused it would give two different
        messages for one fault depending on which check ran first.
        """
        for bad in ("2026-02-31", "not a date", "", None, "26-08-30"):
            with self.subTest(value=bad):
                self.assertIsNone(rules.unreadable_year(bad))


class TheExtractionPathTest(unittest.TestCase):
    """`validate()`. The same treatment an invalid date already gets."""

    def test_the_year_is_named_in_the_note(self):
        result = validate(extraction(THE_REAL_ONE))
        self.assertIn("implausible year 26: 0026-08-30", result.notes)

    def test_it_routes_to_review(self):
        self.assertEqual(validate(extraction(THE_REAL_ONE)).status,
                         "needs_review")

    def test_the_date_is_not_corrected(self):
        """No century is inferred. 10d.41's reasoning, unchanged.

        The note names the date as supplied. Nothing in `validate()` writes a
        value back, and this asserts the message carries the original rather
        than a repaired one.
        """
        result = validate(extraction(THE_REAL_ONE))
        self.assertIn("0026-08-30", " ".join(result.notes))
        self.assertNotIn("2026-08-30", " ".join(result.notes))

    def test_a_real_date_in_range_still_passes(self):
        result = validate(extraction("2026-08-30"))
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.notes, [])

    def test_next_year_passes_and_the_year_after_does_not(self):
        """The boundary, on the door the extractor reaches."""
        self.assertEqual(validate(extraction(
            f"{date.today().year + 1}-01-31")).notes, [])
        two_ahead = f"{date.today().year + 2}-01-31"
        self.assertIn(f"implausible year {date.today().year + 2}: {two_ahead}",
                      validate(extraction(two_ahead)).notes)

    def test_1999_is_refused_and_2000_is_not(self):
        self.assertEqual(validate(extraction("2000-01-01")).notes, [])
        self.assertIn("implausible year 1999: 1999-12-31",
                      validate(extraction("1999-12-31")).notes)

    def test_with_no_supplier_it_is_as_unrecoverable_as_an_invalid_date(self):
        """The `date_valid` recheck, and this is a judgement recorded as a test.

        The brief says the extraction path gives an implausible year the same
        treatment an invalid date already gets. `validate()` treats a date that
        does not parse as making the receipt `failed` rather than
        `needs_review` when the supplier is also missing, so an implausible year
        does the same. The control below is the same receipt with a readable
        year, which is `needs_review`.
        """
        self.assertEqual(
            validate(extraction("2026-02-31", supplier_name=None)).status,
            "failed")
        self.assertEqual(
            validate(extraction(THE_REAL_ONE, supplier_name=None)).status,
            "failed")
        self.assertEqual(
            validate(extraction("2026-08-30", supplier_name=None)).status,
            "needs_review")


class TheFieldErrorTest(unittest.TestCase):
    """`parse_corrections()`, the CLI route."""

    def test_the_year_is_named_and_the_value_is_refused(self):
        corrections, errors = parse_corrections({"invoice_date": THE_REAL_ONE})
        self.assertIn("invoice_date", errors)
        self.assertIn("26", errors["invoice_date"])
        self.assertNotIn("invoice_date", corrections.values)

    def test_it_is_worded_the_way_the_note_error_is(self):
        _, errors = parse_corrections({"invoice_date": THE_REAL_ONE})
        with self.assertRaises(ResolutionNoteError) as raised:
            parse_resolution_note(note_payload(THE_REAL_ONE))
        self.assertIn(rules.unreadable_year_reason(26), errors["invoice_date"])
        self.assertIn(rules.unreadable_year_reason(26), str(raised.exception))

    def test_a_readable_date_still_passes(self):
        corrections, errors = parse_corrections({"invoice_date": "2026-08-30"})
        self.assertEqual(errors, {})
        self.assertEqual(corrections.values["invoice_date"], "2026-08-30")

    def test_next_year_is_accepted_here_too(self):
        stated = f"{date.today().year + 1}-01-31"
        corrections, errors = parse_corrections({"invoice_date": stated})
        self.assertEqual(errors, {})
        self.assertEqual(corrections.values["invoice_date"], stated)

    def test_a_date_that_is_not_a_date_keeps_its_own_error(self):
        """The existing message, not the new one.

        Two faults, two messages. A real calendar date is a different question
        from a readable year and the person reading the error needs to know
        which one they have.
        """
        _, errors = parse_corrections({"invoice_date": "2026-02-31"})
        self.assertEqual(errors["invoice_date"],
                         "'2026-02-31' is not a real calendar date.")


class TheNoteErrorTest(unittest.TestCase):
    """`parse_resolution_note()`, the route this receipt came through."""

    def test_the_year_is_named_and_the_note_is_refused(self):
        with self.assertRaises(ResolutionNoteError) as raised:
            parse_resolution_note(note_payload(THE_REAL_ONE))
        self.assertIn("26", str(raised.exception))
        self.assertIn("invoice_date", str(raised.exception))

    def test_a_readable_date_still_parses(self):
        note = parse_resolution_note(note_payload("2026-08-30"))
        self.assertEqual(note.values["invoice_date"], "2026-08-30")

    def test_next_year_is_accepted_here_too(self):
        stated = f"{date.today().year + 1}-01-31"
        note = parse_resolution_note(note_payload(stated))
        self.assertEqual(note.values["invoice_date"], stated)

    def test_a_date_that_is_not_a_date_keeps_its_own_error(self):
        with self.assertRaises(ResolutionNoteError) as raised:
            parse_resolution_note(note_payload("2026-02-31"))
        self.assertIn("is not a real date", str(raised.exception))


class TenD41IsLeftStricterTest(unittest.TestCase):
    """Sub-step 10d.41's branch is untouched, and the difference is the point.

    `parse_ambiguous_date()` refuses a two-digit year that resolves past the
    CURRENT year. The three doors accept next year. **That is deliberate**,
    Paul's correction of 2026-09-14: `2000 + c` is an inference the system made
    from two digits, and a four-digit year is a figure somebody stated. The
    system may be stricter with its own guesses than with a person's statement.

    Held here so a later session reading the two bounds side by side does not
    tidy one into the other.
    """

    def test_every_two_digit_year_answers_as_it_did(self):
        """Exhaustive over the branch's whole domain, rather than sampled."""
        this_year = date.today().year
        for c in range(100):
            with self.subTest(two_digit_year=c):
                got = parse_ambiguous_date(f"30/08/{c:02d}",
                                           prefer_dayfirst=True)
                if 2000 + c > this_year:
                    self.assertIsNone(got)
                else:
                    self.assertEqual(got, f"{2000 + c:04d}-08-30")

    def test_next_year_as_two_digits_is_refused_where_stated_in_full_it_is_not(
            self):
        """The one boundary where the two rules differ, stated as a test."""
        nxt = date.today().year + 1
        self.assertIsNone(
            parse_ambiguous_date(f"30/08/{nxt % 100:02d}", prefer_dayfirst=True))
        self.assertEqual(validate(extraction(f"{nxt}-08-30")).notes, [])

    def test_a_three_digit_year_is_still_refused(self):
        """126, not 026, and the difference is a finding this test records.

        10d.41's branch reads `c < 1000` on the INTEGER, and `int("026")` is 26,
        so a year written with a leading zero takes the two-digit branch and is
        read as 2026. Only 100 to 999 reach the refusal. That is narrower than
        the comment beside it says, which is flagged in the report and not
        repaired here.
        """
        self.assertIsNone(parse_ambiguous_date("30/08/126",
                                               prefer_dayfirst=True))
        self.assertEqual(
            parse_ambiguous_date("30/08/026", prefer_dayfirst=True),
            "2026-08-30",
            "a leading zero makes it a two-digit year to int(), and this is "
            "the behaviour as found rather than the behaviour as intended")

    def test_a_four_digit_year_below_the_floor_is_still_read(self):
        """**Deliberately unchanged, and this test exists to say so.**

        A four-digit year takes `parse_ambiguous_date()`'s `else` branch, which
        has never had a lower bound, and giving it one would change behaviour
        this task did not ask to change. It is not a hole: whatever this returns
        is an `invoice_date` and `validate()` is the door it must pass through,
        which now refuses 1995. Flagged in the report rather than fixed here.
        """
        self.assertEqual(
            parse_ambiguous_date("30/08/1995", prefer_dayfirst=True),
            "1995-08-30")
        self.assertIn("implausible year 1995: 1995-08-30",
                      validate(extraction("1995-08-30")).notes)


class TheSetOfDoorsTest(unittest.TestCase):
    """The set claim, enumerated from the syntax tree rather than named.

    `CLAUDE.md`: a claim about a set is not verified by verifying its members,
    and a check that sits at one door and not the others is the shape of steps
    10ab and 10ac. A fourth door added later lands in neither list below and
    goes red.
    """

    #: Every function that must ask the question, and does.
    DOORS = {
        ("worker/validation/rules.py", "validate"),
        ("worker/resolution/service.py", "parse_corrections"),
        ("worker/resolution/service.py", "parse_resolution_note"),
    }

    #: The helper itself, which parses a date and takes an `invoice_date`, so
    #: the predicate catches it. Its own category rather than an exemption: it
    #: is the thing every door is required to call, and asserting that it
    #: exists under that exact name is part of the set claim.
    THE_HELPER = {("worker/validation/rules.py", "unreadable_year")}

    #: Caught by the predicate, and not a door. Each needs a reason.
    EXEMPT = {
        # Parses `created_at`, a row timestamp. Its `invoice_date` mentions are
        # keyword arguments it passes on without reading.
        ("app.py", "_retry_failed_receipts"),
        # Parses `started_at` and `finished_at` for the run summary. Same shape.
        ("app.py", "process_once"),
        # Parses an `invoice_date` and never rejects one: it annotates
        # `details` and leaves the date exactly as the model gave it, by
        # design, so `validate()` is the door that decides. 10d.41's own
        # rejection already lands here as an unparsed-raw note.
        ("worker/extraction/postprocess.py", "resolve_invoice_date"),
    }

    PARSERS = {"strptime", "fromisoformat"}
    GUARDS = {"rules.unreadable_year", "unreadable_year",
              "rules.year_is_readable", "year_is_readable"}

    def production_files(self):
        """Every tracked production file.

        `.history\\` cannot appear: it is gitignored and therefore untracked,
        which `CLAUDE.md`'s sixth trap requires.
        """
        listed = subprocess.run(
            ["git", "ls-files", "*.py"], cwd=source_guards.REPO_ROOT,
            capture_output=True, text=True, check=True).stdout.split()
        return [name for name in listed if not name.startswith("tests/")]

    def _mentions_invoice_date(self, function, docstrings):
        for node in ast.walk(function):
            if isinstance(node, ast.Name) and node.id == "invoice_date":
                return True
            if isinstance(node, ast.Attribute) and node.attr == "invoice_date":
                return True
            if isinstance(node, ast.arg) and node.arg == "invoice_date":
                return True
            if isinstance(node, ast.keyword) and node.arg == "invoice_date":
                return True
            if (isinstance(node, ast.Constant) and node.value == "invoice_date"
                    and id(node) not in docstrings):
                return True
        return False

    def date_readers(self):
        """Every production function that turns a string into a date and
        mentions an `invoice_date`, mapped to what it calls.

        Off the tree, never off a grep: a grep returns the prose too, and this
        project keeps superseded wording beside every correction.
        """
        found = {}
        for name in self.production_files():
            tree = source_guards.tree_of(*name.split("/"))
            docstrings = {
                id(node.body[0].value)
                for node in ast.walk(tree)
                if isinstance(node, (ast.Module, ast.FunctionDef,
                                     ast.AsyncFunctionDef, ast.ClassDef))
                and node.body and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)}
            for function in ast.walk(tree):
                if not isinstance(function, (ast.FunctionDef,
                                             ast.AsyncFunctionDef)):
                    continue
                calls = {ast.unparse(node.func) for node in ast.walk(function)
                         if isinstance(node, ast.Call)}
                if not any(call.rsplit(".", 1)[-1] in self.PARSERS
                           for call in calls):
                    continue
                if not self._mentions_invoice_date(function, docstrings):
                    continue
                found[(name, function.name)] = calls
        return found

    def test_no_door_is_missing_from_this_test(self):
        found = set(self.date_readers())
        self.assertEqual(
            found, self.DOORS | self.EXEMPT | self.THE_HELPER,
            "a production function reads an invoice_date and is in none of "
            "DOORS, EXEMPT or THE_HELPER. Decide which it is: if it validates "
            "the date, it must call the helper; if it does not, say why here.")

    def test_every_door_calls_the_one_helper(self):
        readers = self.date_readers()
        for door in sorted(self.DOORS):
            with self.subTest(door=door):
                self.assertTrue(
                    readers[door] & self.GUARDS,
                    f"{door[1]} validates an invoice_date without asking "
                    f"worker/validation/rules.py's helper. Calls: "
                    f"{sorted(readers[door])}")

    def test_the_bound_is_written_in_exactly_one_place(self):
        """Floor once, ceiling once, and every caller asks for both.

        **`worker\\extraction\\postprocess.py` is not exempted by name and does
        not need to be.** It writes `2000 + c` and does not call the helper, so
        it is not one of this rule's three doors: it is 10d.41's separate and
        deliberately stricter rule, held by `TenD41IsLeftStricterTest`. What
        this refuses is a file that calls the helper AND writes the floor
        itself, which is the drift the one-helper rule exists to stop.
        """
        tree = source_guards.tree_of("worker", "validation", "rules.py")
        self.assertEqual(
            [node.lineno for node in ast.walk(tree)
             if isinstance(node, ast.Constant) and node.value == 2000],
            [node.lineno for node in ast.walk(tree)
             if isinstance(node, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "_YEAR_FLOOR"
                     for t in node.targets)],
            "the floor is written somewhere other than _YEAR_FLOOR")

        #: The ceiling moves with the clock, so it is the half a second copy
        #: would break silently rather than loudly.
        clock_readers = sorted(
            function.name
            for function in ast.walk(tree)
            if isinstance(function, ast.FunctionDef)
            and any(ast.unparse(node) == "date.today()"
                    for node in ast.walk(function)
                    if isinstance(node, ast.Call)))
        self.assertEqual(clock_readers, ["readable_year_range"], clock_readers)

        for name in self.production_files():
            if name == "worker/validation/rules.py":
                continue
            with self.subTest(file=name):
                tree = source_guards.tree_of(*name.split("/"))
                calls = {ast.unparse(node.func) for node in ast.walk(tree)
                         if isinstance(node, ast.Call)}
                if not calls & self.GUARDS:
                    continue
                self.assertEqual(
                    [node.lineno for node in ast.walk(tree)
                     if isinstance(node, ast.Constant) and node.value == 2000],
                    [],
                    f"{name} calls the helper and also writes the floor")


if __name__ == "__main__":
    unittest.main()

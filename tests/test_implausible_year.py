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
from worker import attached
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


class TheAttachedDoorTest(unittest.TestCase):
    """The fourth door, on `transaction_date`. Flag 8.2, Paul's decision 2026-09-14.

    **A different field, and the same rule.** `parse_attached_message()` in
    `worker\\attached.py` validated `transaction_date` with the shape the three
    receipt doors had before 2026-09-14: `_ISO_DATE_RE` for the form, then
    `datetime.fromisoformat()` for the calendar, and nothing about the year. So
    `0026-08-30` passed.

    **Paul's reason for taking it, and it is a scope decision rather than a bug
    fix:** the point of one rule is that nobody has to ask which fields it
    covers.

    **What is at stake here is smaller than on a receipt date, and saying so is
    part of the record.** `transaction_date` reaches a `resolution_events` audit
    row through `record_attached_document()`, as `corrections_json`. It composes
    no filed path and it does not reach `determine_tax_year()`, so a bad year
    corrupts a record of what happened rather than a tax year. Traced in
    `2026-09-14_REPORT_claude_code_implausible_year_guard.md` section 8.2 and
    not re-argued here.
    """

    def message(self, transaction_date):
        """One valid handoff message carrying that date. 10f.38's contract."""
        return {
            "schema": attached.ATTACHED_SCHEMA,
            "action": attached.ATTACH_ACTION,
            "receipt_id": "abe4a034-878b-43cd-965d-e4096b5a6bcd",
            "client_id": "CLIENT001",
            "transaction_id": "TXN-0001",
            "transaction_date": transaction_date,
            "transaction_description": "APCOA PARKING 8841 LONDON",
            "transaction_amount": -96.0,
            "filename": "bank-line-invoice.pdf",
            "attached_by": "desktop",
            "attached_at": "2026-09-11T10:00:00.000Z",
        }

    def test_the_year_is_named_and_the_message_is_refused(self):
        with self.assertRaises(attached.AttachedMessageError) as raised:
            attached.parse_attached_message(self.message(THE_REAL_ONE))
        self.assertIn("reads as year 26", str(raised.exception))
        self.assertIn(THE_REAL_ONE, str(raised.exception))

    def test_it_is_worded_the_way_the_other_doors_are(self):
        """One fault, one wording, whichever door meets it.

        The subject prefix stays this door's own, exactly as the CLI names the
        value supplied and the note validator names the field. What the four
        must not do is describe the same fault four different ways.
        """
        with self.assertRaises(attached.AttachedMessageError) as raised:
            attached.parse_attached_message(self.message(THE_REAL_ONE))
        self.assertIn(rules.unreadable_year_reason(26), str(raised.exception))
        self.assertIn("'transaction_date'", str(raised.exception))

    def test_a_readable_date_still_passes(self):
        message = attached.parse_attached_message(self.message("2026-04-01"))
        self.assertEqual(message.transaction_date, "2026-04-01")

    def test_next_year_is_accepted_here_too(self):
        """The same ceiling as the other three, not a fourth bound."""
        nxt = f"{date.today().year + 1}-04-01"
        self.assertEqual(
            attached.parse_attached_message(self.message(nxt)).transaction_date,
            nxt)

    def test_1999_is_refused_and_2000_is_not(self):
        with self.assertRaises(attached.AttachedMessageError):
            attached.parse_attached_message(self.message("1999-12-31"))
        self.assertEqual(
            attached.parse_attached_message(
                self.message("2000-01-01")).transaction_date,
            "2000-01-01")

    def test_a_date_that_is_not_a_date_keeps_its_own_error(self):
        """One fault, one message. The year check must not shadow this one.

        `unreadable_year()` answers None for anything that is not a real
        calendar date, which is what makes the two mutually exclusive.
        """
        with self.assertRaises(attached.AttachedMessageError) as raised:
            attached.parse_attached_message(self.message("2026-02-31"))
        self.assertIn("is not a date", str(raised.exception))
        self.assertNotIn("reads as year", str(raised.exception))

    def test_a_date_of_the_wrong_shape_keeps_its_own_error(self):
        with self.assertRaises(attached.AttachedMessageError) as raised:
            attached.parse_attached_message(self.message("2026-4-1"))
        self.assertIn("must be YYYY-MM-DD", str(raised.exception))
        self.assertNotIn("reads as year", str(raised.exception))


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

    def test_a_three_digit_year_is_refused_however_it_is_spelled(self):
        """**This test pinned the opposite on 2026-09-14, and that is the point.**

        It was written that morning to assert the comment beside the branch, "A
        three-digit year is a misread, not a year", and it failed. The branch
        read `c < 1000` on the INTEGER, and `int("026")` is 26, so a year
        written with a leading zero took the TWO-digit branch and came back as
        `2026-08-30`. Only 100 to 999 ever reached the refusal.

        **It was then rewritten to pin the behaviour as found**, with the
        discrepancy stated in the test rather than hidden by it, and flagged as
        8.3 rather than repaired, because changing it changes 10d.41's
        behaviour and that was not the morning's task.

        **Paul took the flag on 2026-09-14 and this is the other side of it.**
        The branch now counts the digits that were written, which is what its
        own comment always claimed. `30/08/026` returns None and the receipt
        routes to Review with the note that branch already produces.

        ~~"a leading zero makes it a two-digit year to int(), and this is the
        behaviour as found rather than the behaviour as intended"~~ **The
        superseded assertion, struck rather than deleted.**
        """
        self.assertIsNone(parse_ambiguous_date("30/08/126",
                                               prefer_dayfirst=True))
        self.assertIsNone(parse_ambiguous_date("30/08/026",
                                               prefer_dayfirst=True))
        self.assertIsNone(parse_ambiguous_date("30/08/000",
                                               prefer_dayfirst=True))

    def test_the_value_bound_is_kept_as_well_as_the_digit_count(self):
        """**Change the behaviour, keep the bound.** Paul's instruction, 8.3.

        `elif c < 1000` is not replaced by the digit count, it is joined by it.
        A year spelled with four characters that still adds up to less than
        1000 has always returned None here, and it still does. Removing the
        value test would have quietly made `30/08/0126` readable, which nobody
        asked for.
        """
        self.assertIsNone(parse_ambiguous_date("30/08/0126",
                                               prefer_dayfirst=True))
        self.assertIsNone(parse_ambiguous_date("30/08/0999",
                                               prefer_dayfirst=True))

    def test_a_four_character_year_under_a_hundred_is_unchanged_and_flagged(self):
        """`30/08/0026` still comes back as 2026, and that is left alone.

        **The adjacent case, one digit further out.** Four characters, value
        under 100, so it takes the two-digit branch before either refusal can
        see it. It is the same family as 8.3 and it is outside 8.3's scope: the
        brief says three digits, and the comment beside the branch says three
        digits.

        **Pinned rather than ignored**, so the day somebody widens the rule the
        change is loud. Flagged in
        `2026-09-14_REPORT_claude_code_two_year_flags.md`.
        """
        self.assertEqual(
            parse_ambiguous_date("30/08/0026", prefer_dayfirst=True),
            "2026-08-30",
            "behaviour as found, flagged and deliberately not built")
        self.assertEqual(
            parse_ambiguous_date("30/08/6", prefer_dayfirst=True),
            "2006-08-30",
            "one character, same branch, same flag")

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
    #:
    #: **Four from 2026-09-14, flag 8.2 taken.** `parse_attached_message()` is
    #: the one that validates a `transaction_date` rather than an
    #: `invoice_date`, which is why the predicate below reads both names. Paul's
    #: reason: the point of one rule is that nobody has to ask which fields it
    #: covers.
    DOORS = {
        ("worker/validation/rules.py", "validate"),
        ("worker/resolution/service.py", "parse_corrections"),
        ("worker/resolution/service.py", "parse_resolution_note"),
        ("worker/attached.py", "parse_attached_message"),
    }

    #: The date fields this rule covers, and the sweep's predicate is built
    #: from this rather than from a literal, so widening it again is one line.
    FIELDS = {"invoice_date", "transaction_date"}

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

    def _mentions_a_covered_date(self, function, docstrings):
        """Does this function name one of `FIELDS`, other than in a docstring?

        ~~`_mentions_invoice_date`, one field~~ **Widened 2026-09-14 to the set
        above, flag 8.2.** The widening adds exactly one function to the sweep,
        `parse_attached_message()`, measured before it was made rather than
        after: the predicate was run over all 58 tracked production files with
        each field set in turn and the two results differed by that one entry.
        **So no new exemption was needed**, which is the outcome that made this
        a four-line change rather than a scope argument.
        """
        for node in ast.walk(function):
            if isinstance(node, ast.Name) and node.id in self.FIELDS:
                return True
            if isinstance(node, ast.Attribute) and node.attr in self.FIELDS:
                return True
            if isinstance(node, ast.arg) and node.arg in self.FIELDS:
                return True
            if isinstance(node, ast.keyword) and node.arg in self.FIELDS:
                return True
            if (isinstance(node, ast.Constant) and node.value in self.FIELDS
                    and id(node) not in docstrings):
                return True
        return False

    def date_readers(self):
        """Every production function that turns a string into a date and
        mentions a date field this rule covers, mapped to what it calls.

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
                if not self._mentions_a_covered_date(function, docstrings):
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

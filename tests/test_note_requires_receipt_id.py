r"""A resolution note must carry a `receipt_id`, and the filename fallback is gone.

Paul's decision of 2026-09-17. It replaces what step 10aw was scheduled to do.

## What was there

`_receipt_for_note()` looked a receipt up by `receipt_id`, and where the note
carried none it fell back to matching each name in `original_review_files`
against `receipts.filename`, case-insensitively, refusing an ambiguous match.

**That fallback could not run and could not have matched if it had.**

- **It could not run.** It is reached only when `note.receipt_id` is falsy, and
  IntelliBooks Desktop is the only writer into `Intellibills\Resolutions\`; the
  pipeline reads that folder and never writes a note into it. Its two writers
  that send `original_review_files` take the id from a Review row, and the
  function building those rows skips any tray item without an id.
- **It could not have matched.** `original_review_files` now carries the tray
  item's name, `{receipt_id}.json`, while `receipts.filename` holds the
  document's original filename. The two can never be equal. Flag 3 of
  `2026-09-09_REPORT_claude_code_desktop_note.md`, written into the
  `ResolutionNote` field comment on the same day.

## What replaces it

`parse_resolution_note()` refuses a note with no `receipt_id`, the way it
already refuses a missing `resolved_at`, naming the field in the reason. A
person opening the `.error.txt` in `Intellibills\Resolutions\failed\` reads why.

**Before, such a note failed later and less usefully**, as `outcome: not_found`
with "no receipt matched by id or by review filename", which names two ways of
matching when only one exists.

## The test that matters

`TheFallbackIsGoneTest` builds a fixture where the fallback **would** have
worked: a receipt whose `filename` really is one of the names in
`original_review_files`. Today that note resolves. After this change it is
refused. **Without a genuinely matching filename in the fixture these tests
cannot tell the fallback was removed from one that was merely never taken**, and
a test that cannot fail is not a test.
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
from resolution_fixtures import TempEnvironment  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.resolution.service import (  # noqa: E402
    ResolutionNoteError,
    _receipt_for_note,
    apply_resolution_note,
    parse_resolution_note,
)

#: The document's own name, which is what `receipts.filename` holds.
DOCUMENT_NAME = "r-1.pdf"


def payload(**overrides):
    """A note that parses today, so a refusal below is about the one field."""
    note = {
        "schema": 1,
        "receipt_id": "r-1",
        "client_id": "CLIENT001",
        "action": "filed",
        "resolved_by": "desktop",
        "resolved_at": "2026-09-17T11:00:00.000Z",
        "original_review_files": [],
        "values": {"supplier_name": "Apcoa Parking", "gross_amount": 12.0,
                   "invoice_date": "2026-04-01"},
        "filed_path": r"Clients\Test Client\IntelliBooks\Receipts\2026-27\x.pdf",
    }
    note.update(overrides)
    return note


def settle_payload(**overrides):
    r"""A note with no `filed_path`: "these are the corrected values, settle it".

    **`TheFallbackIsGoneTest` needs this shape and the other does not.** A note
    carrying a `filed_path` is refused anyway when that path is not on disk, so
    against today's code it produces `outcome: error` whatever the fallback did.
    A test asserting only "error" would pass today for a reason that has nothing
    to do with this change, which is a test that cannot fail. Without
    `filed_path` the note really does settle the receipt today, so removing the
    fallback is the only thing that can stop it. Sub-step 10f.14 is where the
    two meanings of a `filed` note are decided.
    """
    note = payload(**overrides)
    note.pop("filed_path", None)
    return note


class TheContractRequiresTheIdTest(unittest.TestCase):
    """`parse_resolution_note()`, driven directly. No database needed."""

    def refusal(self, **overrides):
        with self.assertRaises(ResolutionNoteError) as caught:
            parse_resolution_note(payload(**overrides))
        return str(caught.exception)

    def test_a_note_with_no_receipt_id_is_refused(self):
        self.refusal(receipt_id=None)

    def test_a_note_with_the_key_absent_altogether_is_refused(self):
        note = payload()
        del note["receipt_id"]
        with self.assertRaises(ResolutionNoteError):
            parse_resolution_note(note)

    def test_an_empty_string_is_refused_too(self):
        """`_note_text()` strips and returns None for whitespace, so `"  "` and
        `""` reach the check as the same thing a null does."""
        for value in ("", "   "):
            with self.subTest(receipt_id=value):
                self.refusal(receipt_id=value)

    def test_the_reason_names_the_field_and_says_why(self):
        reason = self.refusal(receipt_id=None)
        self.assertIn("receipt_id", reason)
        self.assertIn("required", reason.lower())

    def test_a_note_that_carries_an_id_still_parses(self):
        """The control. Without it every test above passes on a parser that
        refuses everything."""
        note = parse_resolution_note(payload())
        self.assertEqual(note.receipt_id, "r-1")

    def test_a_non_string_id_is_still_refused_by_the_type_check(self):
        """`_note_text()` raised on this before and still does, so the new check
        adds a reason rather than replacing one."""
        reason = self.refusal(receipt_id=7)
        self.assertIn("must be text", reason)


class TheContractStillCarriesReviewFilesTest(unittest.TestCase):
    """`original_review_files` stays in the contract and stays parsed.

    Retiring it was considered by Paul on 2026-09-17 and decided against for
    now, so this holds it in place: what is gone is the lookup that read it, not
    the field.
    """

    def test_it_is_still_carried_onto_the_note(self):
        note = parse_resolution_note(payload(original_review_files=["a.pdf"]))
        self.assertEqual(note.original_review_files, ["a.pdf"])

    def test_it_is_still_refused_when_it_is_not_a_list_of_strings(self):
        for bad in ("a.pdf", [1], [None], {"a": 1}):
            with self.subTest(value=bad):
                with self.assertRaises(ResolutionNoteError) as caught:
                    parse_resolution_note(payload(original_review_files=bad))
                self.assertIn("original_review_files", str(caught.exception))

    def test_absent_is_still_an_empty_list_rather_than_an_error(self):
        note = payload()
        del note["original_review_files"]
        self.assertEqual(parse_resolution_note(note).original_review_files, [])


class TheFallbackIsGoneTest(unittest.TestCase):
    r"""Gone, rather than merely never taken.

    **The fixture is the point.** The receipt's `filename` is `r-1.pdf` and the
    note names `r-1.pdf` in `original_review_files`, so the fallback would have
    found it. That is what makes these able to fail: against the old code the
    note resolves.
    """

    def seed(self, env, repo):
        """A receipt AND a seed extraction, which `TempEnvironment.seed()` gives.

        **The extraction is not optional here.** A settle note against a receipt
        with no extraction returns `not_found` with "This receipt has no
        extraction to correct", so a fixture without one leaves every assertion
        below passing against today's code for a reason that has nothing to do
        with the fallback. Found by running it.

        `TempEnvironment.seed()` writes `filename` as `{receipt_id}.pdf`, which
        is `r-1.pdf` and is exactly what `original_review_files` names, so the
        fallback really does match. `payload()`'s values are the ones
        `resolution_fixtures.good_corrections()` uses to make that seed valid.
        """
        env.seed(repo, receipt_id="r-1", status="needs_review")

    def test_a_note_that_the_fallback_would_have_matched_is_now_refused(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                self.seed(env, repo)
                self.assertEqual(
                    repo.find_receipts_by_filename(DOCUMENT_NAME)[0]["receipt_id"],
                    "r-1",
                    "the fixture does not actually match, so this test cannot "
                    "tell the fallback was removed")

                outcome = apply_resolution_note(
                    repo, env.engine(repo),
                    settle_payload(
                        receipt_id=None,
                        original_review_files=[DOCUMENT_NAME,
                                               DOCUMENT_NAME + ".review.json"]))
            finally:
                repo.close()

            self.assertEqual(outcome.outcome, "error")
            self.assertIn("receipt_id", outcome.error_detail)

    def test_the_receipt_is_untouched_by_the_refused_note(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                self.seed(env, repo)
                apply_resolution_note(
                    repo, env.engine(repo),
                    settle_payload(receipt_id=None,
                                   original_review_files=[DOCUMENT_NAME]))
                receipt = repo.get_receipt("r-1")
            finally:
                repo.close()
            self.assertEqual(receipt["status"], "needs_review")
            self.assertIsNone(receipt["filed_path"])

    def test_a_note_carrying_an_id_still_finds_its_receipt(self):
        """`_receipt_for_note()` keeps the half it is supposed to keep."""
        with TempEnvironment() as env:
            repo = Repository()
            try:
                self.seed(env, repo)
                found = _receipt_for_note(repo, parse_resolution_note(payload()))
            finally:
                repo.close()
            self.assertIsNotNone(found)
            self.assertEqual(found["receipt_id"], "r-1")

    def test_the_not_found_reason_names_one_way_of_matching_and_not_two(self):
        r"""**Paul chose this wording, 2026-09-17.**

        ~~"no receipt matched by id or by review filename"~~ named two ways of
        matching, and the filename fallback went the same day. A person reading
        the `.error.txt` in `Resolutions\failed\` is deciding whether the
        pipeline or Desktop is at fault, and a reason naming a path that does
        not exist sends them looking for it.

        Held as a test rather than left to a comment, because it is a string a
        person reads and nothing else would notice it drifting back.
        """
        with TempEnvironment() as env:
            repo = Repository()
            try:
                self.seed(env, repo)
                outcome = apply_resolution_note(
                    repo, env.engine(repo),
                    settle_payload(receipt_id="no-such-receipt"))
            finally:
                repo.close()
            self.assertEqual(outcome.error_detail, "no receipt matched this id")
            self.assertNotIn("filename", outcome.error_detail)

    def test_an_id_that_matches_nothing_is_still_not_found(self):
        """The other refusal is untouched: this adds a reason and removes none.

        It also proves the parse check is not swallowing the `not_found` path,
        which would make a mistyped id report as a contract error.
        """
        with TempEnvironment() as env:
            repo = Repository()
            try:
                self.seed(env, repo)
                outcome = apply_resolution_note(
                    repo, env.engine(repo),
                    settle_payload(receipt_id="no-such-receipt"))
            finally:
                repo.close()
            self.assertEqual(outcome.outcome, "not_found")


class TheErrorFileAPersonOpensTest(unittest.TestCase):
    r"""What lands in `Intellibills\Resolutions\failed\` beside the note.

    The three lines are composed by `_move_note()` in `app.py` from the
    outcome's fields, so this drives the real consumer rather than formatting
    them here.
    """

    def consume(self, note_payload, name="bad_1757600531000.json"):
        import app

        config.RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        path = config.RESOLUTIONS_DIR / name
        path.write_text(json.dumps(note_payload), encoding="utf-8")

        repo = Repository()
        try:
            app._consume_resolution_notes(repo, None, {})
        finally:
            repo.close()
        failed = config.RESOLUTIONS_DIR / "failed"
        return (failed / (name + ".error.txt")).read_text(encoding="utf-8")

    def test_the_error_file_says_which_field_and_why(self):
        with TempEnvironment():
            text = self.consume(payload(receipt_id=None))
            self.assertIn("outcome: error", text)
            self.assertIn("receipt_id", text)
            self.assertIn("required", text.lower())

    def test_the_note_itself_is_kept_beside_it(self):
        """Nothing is ever deleted, which is the rule `_move_note()` carries."""
        with TempEnvironment():
            self.consume(payload(receipt_id=None))
            failed = config.RESOLUTIONS_DIR / "failed"
            self.assertEqual(
                sorted(p.name for p in failed.iterdir()),
                ["bad_1757600531000.json", "bad_1757600531000.json.error.txt"])


class NothingMatchesOnAFilenameTest(unittest.TestCase):
    r"""A guard over the set, on the source rather than on the text.

    **Parsed from the syntax tree.** This file keeps superseded wording beside
    every correction, the `ResolutionNote` field comment names the fallback in
    prose, and `_receipt_for_note()`'s docstring described it, so a text search
    would read the tombstone as the thing itself. `CLAUDE.md`, 2026-09-08.
    """

    FILENAME_LOOKUP = "find_receipts_by_filename"

    def the_function(self):
        tree = source_guards.tree_of("worker", "resolution", "service.py")
        return next(node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "_receipt_for_note")

    def test_it_makes_no_call_that_matches_on_a_filename(self):
        calls = [ast.unparse(node) for node in ast.walk(self.the_function())
                 if isinstance(node, ast.Call)
                 and (node.func.attr if isinstance(node.func, ast.Attribute)
                      else getattr(node.func, "id", None)) == self.FILENAME_LOOKUP]
        self.assertEqual(
            calls, [],
            "_receipt_for_note() matches on a filename again, and Desktop sends "
            "`{receipt_id}.json` in original_review_files, which can never "
            f"equal receipts.filename: {calls}")

    def test_it_does_not_read_original_review_files(self):
        reads = [node.lineno for node in ast.walk(self.the_function())
                 if isinstance(node, ast.Attribute)
                 and node.attr == "original_review_files"]
        self.assertEqual(reads, [], f"read at lines {reads}")

    def test_it_has_no_loop_left(self):
        """The fallback was the only loop in it. Stated as its own assertion
        because a loop that read something else would be a different function
        than the one this change leaves behind."""
        loops = [node.lineno for node in ast.walk(self.the_function())
                 if isinstance(node, (ast.For, ast.While))]
        self.assertEqual(loops, [], f"a loop is back, at lines {loops}")

    def test_the_guard_is_looking_at_a_real_function(self):
        """A guard that cannot find its target passes for ever. Amendment 97."""
        self.assertTrue(
            any(isinstance(node, ast.Call) for node in ast.walk(self.the_function())),
            "_receipt_for_note() has no calls at all, so this guard is probably "
            "reading the wrong thing")


if __name__ == "__main__":
    unittest.main()

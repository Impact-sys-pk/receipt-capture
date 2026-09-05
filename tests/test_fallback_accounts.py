"""The pipeline reads the published fallback table and follows it.

Brief of 2026-09-05, `PROMPT_claude_code_2026-09-05_fallback_accounts.md`,
sub-steps 10j.7 and 10j.8.

Two halves, matching the module. `FallbackEnvironment` and the classes above
`ChartCheckTest` cover the reader, in the shape of `VatRateEnvironment` in
`tests/test_vat_rates.py`. `ChartCheckTest` and the classes below it cover
`resolve_against_chart()`, which is the half that changes what a receipt is
categorised as.

**There was no red before green for the reader, and that is the design rather
than a gap.** It is a new module: nothing called it, so nothing could go red.
What stands in for it is the mutation record in the report, which breaks each
branch of the check in turn and names the test that catches it.

**What was red before green is the check.** Adding it turned five existing tests
red at once, in four files, because they seed the legacy three-digit code 271 and
none of them pinned `config.CHARTS_DIR`, so they were reading the real bundle out
of OneDrive. That is recorded in `tests/chart_fixtures.py`, which is the fix.

The fixture writes its own small files rather than copying the real bundle, for
the two reasons `tests/test_chart_bundle.py` gives: a copy would make the
expected values move whenever IntelliCharts publishes, and a test that reads
OneDrive is not a unit test. The real file is checked separately by
`RealBundleFallbackTest`, which skips when the bundle is not on this machine.
"""

import json
import logging
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import config
from tests.chart_fixtures import MASTER_HEADER, _row
from worker.categorisation import chart, fallback
from worker.categorisation.engine import CategorisationResult

FALLBACK_HEADER = "code,fallback_code"

# The table published on 2026-09-05, in full. It is one row, which is the point:
# only accounts that have a fallback appear, so an account absent from the file
# has none and that means Review.
PUBLISHED_ROWS = ["7391,7310"]

# A small chart standing in for a client's. 7391 Car wash is deliberately absent,
# which is the case Paul's ruling is about; 7310 is present and is its fallback.
# 7999 is present but marked classifier_eligible No, and 7888 is present but
# retired, and both are here to pin the two filters on the membership reader.
CHART_ROWS = [
    _row("7310", "Vehicle repairs and servicing"),
    _row("7500", "Printing and postage"),
    _row("7999", "In the chart but not classifier-eligible", eligible="No"),
    _row("7888", "In the chart but retired", status="retired"),
]


class FallbackEnvironment:
    """A temp CHARTS_DIR holding a fallback table and a chart, caches emptied."""

    def __init__(self, rows=None, header=FALLBACK_HEADER, write=True,
                 chart_rows=None, write_chart=True):
        self._rows = PUBLISHED_ROWS if rows is None else rows
        self._header = header
        self._write = write
        self._chart_rows = CHART_ROWS if chart_rows is None else chart_rows
        self._write_chart = write_chart

    def __enter__(self):
        self._temp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved_charts_dir = config.CHARTS_DIR
        self._saved_clients = config.CLIENTS_BY_ID
        config.CHARTS_DIR = self.path
        config.CLIENTS_BY_ID = {
            "CLIENT001": {"client_id": "CLIENT001", "firm_id": "FIRM001",
                          "trade": "UNSPECIFIED"}
        }
        # Module-level caches, so they survive between tests unless cleared. They
        # are restored rather than only emptied, so this fixture cannot leave the
        # real bundle's entries missing for a test that runs after it.
        self._saved_caches = (
            dict(fallback._CACHE), dict(chart._CACHE), dict(chart._ACCOUNT_CACHE),
        )
        for cache in (fallback._CACHE, chart._CACHE, chart._ACCOUNT_CACHE):
            cache.clear()
        if self._write:
            self.write(self._rows, self._header)
        if self._write_chart:
            self.write_chart(self._chart_rows)
        return self

    def __exit__(self, *exc):
        config.CHARTS_DIR = self._saved_charts_dir
        config.CLIENTS_BY_ID = self._saved_clients
        for cache, saved in zip(
            (fallback._CACHE, chart._CACHE, chart._ACCOUNT_CACHE), self._saved_caches
        ):
            cache.clear()
            cache.update(saved)
        self._temp.cleanup()
        return False

    @property
    def file(self):
        return self.path / fallback.FALLBACK_ACCOUNTS_FILENAME

    def write(self, rows, header=FALLBACK_HEADER):
        # CRLF, because that is what the published file has, and newline="" so
        # the terminators reach the file as typed rather than being translated.
        # That is what makes this a test of the reader.
        text = "".join(f"{line}\r\n" for line in [header, *rows])
        with self.file.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return self.file

    def write_chart(self, rows):
        path = self.path / config.MASTER_CHART_FILENAME
        path.write_text("\n".join([MASTER_HEADER, *rows]) + "\n", encoding="utf-8")
        # The chart caches key on modification time, and a rewrite inside one
        # test can land in the same nanosecond on Windows. Clearing is cheaper
        # than fighting the clock.
        chart._CACHE.clear()
        chart._ACCOUNT_CACHE.clear()
        return path


# ---------------------------------------------------------------- the reader


class PublishedTableTest(unittest.TestCase):
    def test_the_published_row_resolves(self):
        with FallbackEnvironment():
            self.assertEqual(fallback.fallback_for("7391"), "7310")

    def test_a_code_that_is_not_in_the_file_returns_none(self):
        # Not an error, and not a blank string. Only accounts that have a
        # fallback appear in the file, so absent means "no fallback", which means
        # Review.
        with FallbackEnvironment():
            self.assertIsNone(fallback.fallback_for("7500"))

    def test_the_whole_table_comes_back_as_a_mapping(self):
        with FallbackEnvironment(rows=["7391,7310", "7392,7310"]):
            self.assertEqual(fallback.load_fallbacks(), {"7391": "7310", "7392": "7310"})

    def test_a_code_with_surrounding_space_still_resolves(self):
        with FallbackEnvironment():
            self.assertEqual(fallback.fallback_for(" 7391 "), "7310")

    def test_an_empty_code_asks_nothing_of_the_file(self):
        with FallbackEnvironment():
            self.assertIsNone(fallback.fallback_for(""))
            self.assertIsNone(fallback.fallback_for(None))


class UnreadableRowTest(unittest.TestCase):
    """Not a re-validation of the file. publish_master.py does that."""

    def test_a_row_with_no_target_is_skipped_and_the_rest_are_kept(self):
        with FallbackEnvironment(rows=["7391,", "7392,7310"]):
            self.assertEqual(fallback.load_fallbacks(), {"7392": "7310"})

    def test_a_file_with_no_fallback_column_yields_no_fallback(self):
        # Every row simply fails to yield a pair, which is the safe direction: no
        # fallback is found, so a code outside the chart reaches Review.
        with FallbackEnvironment(rows=["7391,7310"], header="code,target"):
            self.assertEqual(fallback.load_fallbacks(), {})
            self.assertIsNone(fallback.fallback_for("7391"))


class MissingFileTest(unittest.TestCase):
    def test_a_missing_table_gives_an_empty_mapping_and_an_error(self):
        # Not an exception: a bundle that has not been published must cost a
        # receipt its fallback, not stop the receipt being processed.
        with FallbackEnvironment(write=False) as env:
            with self.assertLogs("worker.categorisation.fallback", level=logging.ERROR) as logs:
                result = fallback.load_fallbacks()
        self.assertEqual(result, {})
        message = "\n".join(logs.output)
        self.assertIn(str(env.file), message, "the ERROR names the full path")
        self.assertIn("IntelliCharts", message)
        self.assertIn("nothing here creates it", message)

    def test_fallback_for_returns_none_rather_than_raising(self):
        with FallbackEnvironment(write=False):
            with self.assertLogs("worker.categorisation.fallback", level=logging.ERROR):
                self.assertIsNone(fallback.fallback_for("7391"))


class ModificationTimeCacheTest(unittest.TestCase):
    """The table must not be re-read from OneDrive once per receipt."""

    def test_a_second_call_does_not_re_read_the_file(self):
        with FallbackEnvironment() as env:
            first = fallback.fallback_for("7391")
            stat = env.file.stat()
            # Rewritten with different content, then stamped back to the mtime it
            # had. A loader that re-read on every call would return the new target.
            env.write(["7391,7500"])
            os.utime(env.file, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            second = fallback.fallback_for("7391")
        self.assertEqual(second, first)
        self.assertEqual(second, "7310")

    def test_a_changed_modification_time_is_re_read(self):
        # The other half of the same property. Without it the test above would
        # also pass for a loader that read the file once and never again, which
        # would mean a republished table never reaching a running pipeline.
        with FallbackEnvironment() as env:
            fallback.fallback_for("7391")
            env.write(["7391,7500"])
            stat = env.file.stat()
            os.utime(env.file, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
            self.assertEqual(fallback.fallback_for("7391"), "7500")


class NoSecondHopTest(unittest.TestCase):
    """publish_master.py refuses a chain, so nothing here walks one."""

    def test_a_chain_in_a_hand_edited_file_is_followed_exactly_one_hop(self):
        # 7391 -> 7392 -> 7310 cannot be published: validate_fallbacks() refuses
        # a target that itself carries a fallback. If a file like this appears
        # anyway, one hop is taken and no more.
        with FallbackEnvironment(rows=["7391,7392", "7392,7310"]):
            self.assertEqual(fallback.fallback_for("7391"), "7392")


# ------------------------------------------------- the membership reader


class ChartMembershipTest(unittest.TestCase):
    """`get_chart_accounts_for_client()` asks a different question from
    `get_eligible_accounts_for_client()`, and applies a different filter."""

    def test_an_account_that_is_not_classifier_eligible_is_still_in_the_chart(self):
        # The whole reason for a second reader. chart.py's docstring says
        # classifier_eligible "is not a rule about what a person may post", so
        # using it here would strip a learned code that is perfectly postable.
        with FallbackEnvironment():
            accounts = chart.get_chart_accounts_for_client("CLIENT001")
        self.assertIn("7999", accounts)
        self.assertEqual(accounts["7999"], "In the chart but not classifier-eligible")

    def test_a_retired_account_is_not_in_the_chart(self):
        with FallbackEnvironment():
            self.assertNotIn("7888", chart.get_chart_accounts_for_client("CLIENT001"))

    def test_the_eligible_reader_still_applies_both_filters(self):
        # The other half. Without it, this file could pass for a change that
        # simply deleted the eligibility filter from the module.
        with FallbackEnvironment():
            eligible = dict(chart.get_eligible_accounts_for_client("CLIENT001"))
        self.assertNotIn("7999", eligible)
        self.assertNotIn("7888", eligible)
        self.assertEqual(sorted(eligible), ["7310", "7500"])


# ----------------------------------------------------------- the check


def _result(code="7391", name="Car wash", match_source="client",
            confidence="high", needs_review=False):
    return CategorisationResult(
        receipt_id="r-1", extraction_id="e-1", client_id="CLIENT001",
        business_type="UNSPECIFIED", vendor_code="canary",
        suggested_code=code, suggested_name=name, confidence=confidence,
        match_source=match_source, matched_vendor="canary",
        needs_review=needs_review,
    )


class ChartCheckTest(unittest.TestCase):
    """The three outcomes of Task 2, one test class each below this one."""

    def test_a_code_in_the_chart_is_left_exactly_as_it_was(self):
        with FallbackEnvironment():
            result = fallback.resolve_against_chart(
                _result(code="7310", name="Vehicle repairs and servicing"))
        self.assertEqual(result.chart_outcome, "in_chart")
        self.assertEqual(result.suggested_code, "7310")
        self.assertEqual(result.suggested_name, "Vehicle repairs and servicing")
        self.assertIsNone(result.original_code)
        self.assertIsNone(result.chart_note)
        self.assertFalse(result.needs_review)


class SubstitutionTest(unittest.TestCase):
    """Outcome 2. Paul's ruling of 2026-09-05, and the case the table exists for."""

    def test_the_published_fallback_becomes_the_suggestion(self):
        with FallbackEnvironment():
            result = fallback.resolve_against_chart(_result())
        self.assertEqual(result.chart_outcome, "substituted")
        self.assertEqual(result.suggested_code, "7310")
        self.assertEqual(result.suggested_name, "Vehicle repairs and servicing")

    def test_the_original_is_kept_beside_it_and_is_not_lost(self):
        # "Do not silently substitute." A receipt whose account was swapped has
        # to be distinguishable from one posted where the classifier said.
        with FallbackEnvironment():
            result = fallback.resolve_against_chart(_result())
        self.assertEqual(result.original_code, "7391")
        self.assertEqual(result.original_name, "Car wash")
        self.assertIn("7391", result.chart_note)
        self.assertIn("7310", result.chart_note)
        self.assertIn(fallback.FALLBACK_ACCOUNTS_FILENAME, result.chart_note)

    def test_the_swap_is_logged_at_warning_naming_the_receipt(self):
        with FallbackEnvironment():
            with self.assertLogs("worker.categorisation.fallback", level=logging.WARNING) as logs:
                fallback.resolve_against_chart(_result())
        message = "\n".join(logs.output)
        self.assertIn("r-1", message)
        self.assertIn("7391", message)
        self.assertIn("7310", message)

    def test_a_substituted_receipt_is_not_made_a_review_item(self):
        # Paul's ruling makes the fallback an accounting fact about the account,
        # so a substituted receipt is not a less certain one. needs_review and
        # confidence are left as the layer set them.
        with FallbackEnvironment():
            result = fallback.resolve_against_chart(_result())
        self.assertFalse(result.needs_review)
        self.assertEqual(result.confidence, "high")
        self.assertEqual(result.match_source, "client")


class UnusableTest(unittest.TestCase):
    """Outcome 3. No code, needs_review, and a note saying which account and why."""

    def test_an_account_with_no_fallback_leaves_no_code(self):
        with FallbackEnvironment():
            result = fallback.resolve_against_chart(
                _result(code="7600", name="Some other account"))
        self.assertEqual(result.chart_outcome, "unusable")
        self.assertIsNone(result.suggested_code)
        self.assertIsNone(result.suggested_name)
        self.assertTrue(result.needs_review)
        self.assertEqual(result.confidence, "none")

    def test_the_note_names_the_account_and_says_why_it_could_not_be_used(self):
        with FallbackEnvironment():
            result = fallback.resolve_against_chart(
                _result(code="7600", name="Some other account"))
        self.assertIn("7600", result.chart_note)
        self.assertIn("Some other account", result.chart_note)
        self.assertIn("no fallback", result.chart_note)
        # "flagged for review", not "goes to Review". categorisations.needs_review
        # is written by all four save_categorisation() call sites and read by
        # nothing; what routes a receipt into Intellibills/Review/ is
        # validation.status, which this module does not touch.
        self.assertIn("flagged for review", result.chart_note)
        self.assertNotIn("goes to Review", result.chart_note)
        self.assertEqual(result.original_code, "7600")

    def test_a_fallback_that_is_not_in_the_chart_either_is_also_unusable(self):
        # The second half of outcome 3, and it is a different sentence: the
        # account has a fallback, and the client's chart does not hold that one.
        with FallbackEnvironment(rows=["7391,7777"]):
            result = fallback.resolve_against_chart(_result())
        self.assertEqual(result.chart_outcome, "unusable")
        self.assertIsNone(result.suggested_code)
        self.assertIn("7777", result.chart_note)
        self.assertIn("not in that chart either", result.chart_note)

    def test_match_source_still_says_which_layer_answered(self):
        # A layer did answer. Overwriting this with "unmatched" would record that
        # nothing matched, which is untrue, and would lose the only record of
        # which layer produced an unusable code.
        with FallbackEnvironment():
            result = fallback.resolve_against_chart(
                _result(code="7600", match_source="fuzzy_firm"))
        self.assertEqual(result.match_source, "fuzzy_firm")


class NothingToCheckTest(unittest.TestCase):
    def test_an_unmatched_result_passes_through_untouched(self):
        with FallbackEnvironment():
            result = fallback.resolve_against_chart(
                _result(code=None, name=None, match_source="unmatched",
                        confidence="none", needs_review=True))
        self.assertEqual(result.chart_outcome, "no_code")
        self.assertIsNone(result.suggested_code)
        self.assertIsNone(result.chart_note)


class NeedsReviewIsAFlagNotARouteTest(unittest.TestCase):
    """`categorisations.needs_review` is written and read by nothing.

    Recorded as a test because the module's notes make a claim about it, and a
    claim in a docstring goes stale silently. If a reader appears, this goes red
    and the notes need rewriting rather than quietly becoming true.

    **The first version of this test was too crude and it is disclosed because
    the correction is the useful part.** It flagged every SQL line containing
    `needs_review` and a `WHERE`, which caught `query_receipts.py:46`,
    `WHERE e.validation_status = 'needs_review'`. That is the *status value* on
    `extractions`, a different column entirely that happens to take a string of
    the same name. **The discriminator is that the column is named as a bare
    identifier inside a statement that also names `categorisations`**, while the
    status is a quoted value, so the check is now on statements rather than on
    lines."""

    SKIP = {".venv", ".history", "tests", "docs", "__pycache__", "archive"}

    def _statements_naming_both(self):
        """Every string literal in production code naming the table and column."""
        import ast
        from pathlib import Path

        root = Path(config.__file__).resolve().parent
        found = []
        for path in root.rglob("*.py"):
            if set(path.relative_to(root).parts) & self.SKIP:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            # Docstrings dropped first. fallback.py's own notes name the table
            # and the column in the same paragraph, explaining why nothing reads
            # it, so a scan over every string constant finds the explanation and
            # calls it a reader. Found by writing it that way.
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                     ast.AsyncFunctionDef)) and ast.get_docstring(node):
                    node.body = node.body[1:]
            for node in ast.walk(tree):
                if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                    continue
                text = node.value
                if "categorisations" in text and "needs_review" in text:
                    found.append((path.relative_to(root).as_posix(), node.lineno, text))
        return found

    def test_the_column_is_only_ever_created_and_inserted(self):
        statements = self._statements_naming_both()
        self.assertTrue(statements, "no statement names both, so this check "
                        "would pass whatever the schema did")
        offenders = [
            f"{f}:{line}" for f, line, text in statements
            if "CREATE TABLE" not in text.upper() and "INSERT INTO" not in text.upper()
        ]
        self.assertEqual(offenders, [],
                         f"a statement now reads the column: {offenders}")

    def test_the_two_statements_are_where_they_should_be(self):
        # The other half. Without it the test above would also pass for a schema
        # that had lost the column, or a repository that had stopped writing it.
        places = sorted({f for f, _line, _text in self._statements_naming_both()})
        self.assertEqual(places, ["worker/database/repository.py",
                                  "worker/database/schema.py"])

    def test_nothing_branches_on_the_value_off_a_result_object(self):
        # The five attribute loads of .needs_review in production are all
        # `needs_review=categorisation.needs_review` inside a save_categorisation
        # call. A load anywhere else would be code acting on the flag.
        import ast
        from pathlib import Path

        root = Path(config.__file__).resolve().parent
        stray = []
        for path in root.rglob("*.py"):
            if set(path.relative_to(root).parts) & self.SKIP:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            passed = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    for kw in node.keywords:
                        if kw.arg == "needs_review":
                            for sub in ast.walk(kw.value):
                                if isinstance(sub, ast.Attribute):
                                    passed.add(id(sub))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Attribute) and node.attr == "needs_review"
                        and isinstance(node.ctx, ast.Load) and id(node) not in passed):
                    stray.append(f"{path.relative_to(root).as_posix()}:{node.lineno}")
        self.assertEqual(stray, [], f"something now acts on the flag: {stray}")


class UnreadableChartTest(unittest.TestCase):
    """An empty read is not evidence of absence, and the difference is large.

    Stripping every code on an unpublished bundle would put every receipt in the
    practice into Review at once."""

    def test_a_missing_chart_leaves_the_suggestion_standing(self):
        with FallbackEnvironment(write_chart=False):
            with self.assertLogs("worker.categorisation", level=logging.ERROR):
                result = fallback.resolve_against_chart(_result())
        self.assertEqual(result.chart_outcome, "unreadable_chart")
        self.assertEqual(result.suggested_code, "7391")
        self.assertEqual(result.suggested_name, "Car wash")
        self.assertIn("could not be read", result.chart_note)

    def test_an_unchecked_code_is_forced_to_review(self):
        """Paul's instruction, 2026-09-05, and it closes a real hole.

        The first version left the code standing and left `needs_review` alone.
        `_result()`'s defaults are a layer 1 exact vendor match: confidence
        `high`, needs_review False. So an account nobody could check against a
        chart would have gone to the books looking verified. It survives as a
        suggestion for a person instead."""
        source = _result()
        self.assertFalse(source.needs_review, "the fixture must start False or "
                         "this test cannot discriminate")
        with FallbackEnvironment(write_chart=False):
            with self.assertLogs("worker.categorisation", level=logging.ERROR):
                result = fallback.resolve_against_chart(source)
        self.assertTrue(result.needs_review)
        self.assertIn("flagged for review", result.chart_note)

    def test_the_confidence_is_left_as_the_layer_set_it(self):
        # Deliberate, and the reason is in the module. The layer was confident
        # about the vendor and was right to be; what could not be established is
        # whether the client's chart holds the account, and needs_review carries
        # that. Asserted so a later change to confidence is a decision rather
        # than a side effect.
        with FallbackEnvironment(write_chart=False):
            with self.assertLogs("worker.categorisation", level=logging.ERROR):
                result = fallback.resolve_against_chart(_result())
        self.assertEqual(result.confidence, "high")
        self.assertEqual(result.match_source, "client")

    def test_no_audit_row_is_written_because_the_answer_did_not_change(self):
        # The code was not swapped and was not cleared, so there is nothing to
        # record as a substitution. The ERROR in the log is the record.
        import tempfile as _tempfile
        temp = _tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        saved = config.DB_PATH
        config.DB_PATH = Path(temp.name) / "receipts.db"
        try:
            from worker.database.repository import Repository
            repo = Repository()
            try:
                with FallbackEnvironment(write_chart=False):
                    with self.assertLogs("worker.categorisation", level=logging.ERROR):
                        fallback.resolve_against_chart(_result(), repo=repo)
                self.assertEqual(repo.list_resolution_events("r-1"), [])
            finally:
                repo.close()
        finally:
            config.DB_PATH = saved
            temp.cleanup()

    def test_a_missing_fallback_table_still_sends_an_absent_code_to_review(self):
        # The chart is readable and the fallback table is not, which is a
        # different failure from the one above and must not be confused with it.
        with FallbackEnvironment(write=False):
            with self.assertLogs("worker.categorisation.fallback", level=logging.ERROR):
                result = fallback.resolve_against_chart(_result())
        self.assertEqual(result.chart_outcome, "unusable")
        self.assertIsNone(result.suggested_code)


# ------------------------------------------------------------ the audit row


class AuditRowTest(unittest.TestCase):
    """Paul's decision, 2026-09-05: the substitution is an event, and `actor`
    says plainly that no person did it.

    Not the `categorisations` correction columns, which mean a person changed it,
    and not a sidecar key, because `make_enriched_sidecar()` is frozen by design
    document 18.2b."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._saved_db = config.DB_PATH
        config.DB_PATH = Path(self._temp.name) / "receipts.db"
        from worker.database.repository import Repository
        self.repo = Repository()

    def tearDown(self):
        self.repo.close()
        config.DB_PATH = self._saved_db
        self._temp.cleanup()

    def _events(self):
        return self.repo.list_resolution_events("r-1")

    def test_a_substitution_writes_one_row_naming_the_pipeline(self):
        with FallbackEnvironment():
            fallback.resolve_against_chart(_result(), repo=self.repo)
        events = self._events()
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["actor"], "pipeline")
        self.assertEqual(event["source"], "categorisation")
        self.assertEqual(event["action"], "chart_fallback")
        self.assertEqual(event["outcome"], "substituted")
        self.assertEqual(event["gl_override_code"], "7310")

    def test_the_row_carries_both_codes_so_the_swap_is_reconstructable(self):
        with FallbackEnvironment():
            fallback.resolve_against_chart(_result(), repo=self.repo)
        corrections = json.loads(self._events()[0]["corrections_json"])
        self.assertEqual(corrections["suggested_code"], "7391")
        self.assertEqual(corrections["suggested_name"], "Car wash")
        self.assertEqual(corrections["resolved_code"], "7310")
        self.assertEqual(corrections["match_source"], "client")

    def test_an_unusable_code_writes_a_row_too(self):
        with FallbackEnvironment():
            fallback.resolve_against_chart(_result(code="7600"), repo=self.repo)
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["outcome"], "unusable")
        self.assertIsNone(events[0]["gl_override_code"])
        self.assertEqual(json.loads(events[0]["corrections_json"])["resolved_code"], None)

    def test_the_ordinary_case_writes_no_row(self):
        # The other half. Without it this class would pass for a check that wrote
        # an event on every receipt, which would bury the two that matter.
        with FallbackEnvironment():
            fallback.resolve_against_chart(_result(code="7310"), repo=self.repo)
        self.assertEqual(self._events(), [])

    def test_no_person_column_is_written_by_this_module(self):
        # The reason the correction columns were not used. A machine writing
        # corrected_at would make a substitution indistinguishable from an
        # operator's correction.
        #
        # Asserted against the module's source and not against a row count. A
        # count of categorisations rows in this fixture's database is zero
        # whatever the module does, so it would be a check that cannot fail.
        # Docstrings stripped first. The module explains at length why it does
        # NOT write those columns, so a plain substring search over the source
        # finds its own reasoning and fails. Found by writing it that way.
        import ast
        import inspect

        tree = ast.parse(inspect.getsource(fallback))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)) and ast.get_docstring(node):
                node.body = node.body[1:]
        body = ast.unparse(tree)
        for forbidden in ("update_categorisation", "corrected_at", "correction_code",
                          "correction_name", "correction_reason"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, body)

    def test_a_missing_repo_is_not_an_error(self):
        with FallbackEnvironment():
            result = fallback.resolve_against_chart(_result(), repo=None)
        self.assertEqual(result.suggested_code, "7310")


class NoSchemaChangeTest(unittest.TestCase):
    """There is no ALTER TABLE anywhere in this repository and schema.py only
    creates, so a new column would exist only in a database made after the
    change. That is why the substitution is an event."""

    def test_categorisations_gained_no_column(self):
        from worker.database import schema
        import inspect
        source = inspect.getsource(schema)
        self.assertNotIn("fallback_code", source)
        self.assertNotIn("fallback_from", source)

    def test_the_sidecar_gained_no_key(self):
        # make_enriched_sidecar() is frozen by design document 18.2b and
        # sub-step 10d.14. This is the guard on that.
        from worker.filing import make_enriched_sidecar
        keys = set(make_enriched_sidecar(
            receipt_id="r", source="email", client_id="c", client_name="n",
            capture_date="", invoice_date="", supplier="", net=None, vat=None,
            gross=None, currency="GBP", category_code=None, category_name=None,
            confidence="none", validation_status="ok", asserted=None,
            original_filename="f.pdf",
        ))
        self.assertEqual(len(keys), 20)
        self.assertFalse([k for k in keys if "fallback" in k or "chart" in k])


# ------------------------------------------------------------ the real bundle


class RealBundleFallbackTest(unittest.TestCase):
    """The values the brief asks to see printed, read from the published file.

    Skipped where the bundle is not present, so the suite still runs on a machine
    with no practice root."""

    def setUp(self):
        if not (config.CHARTS_DIR / fallback.FALLBACK_ACCOUNTS_FILENAME).is_file():
            self.skipTest(f"no fallback table at {config.CHARTS_DIR}")

    def test_7391_falls_back_to_7310(self):
        self.assertEqual(fallback.fallback_for("7391"), "7310")

    def test_a_code_that_is_not_in_the_real_file_returns_none(self):
        self.assertIsNone(fallback.fallback_for("7310"))

    def test_the_real_table_is_one_hop_and_not_a_chain(self):
        # publish_master.py refuses a target that itself carries a fallback, so
        # no key of this mapping may appear among its values. A real property of
        # the published file that could genuinely fail, unlike asserting the
        # parser did not produce a blank key, which it cannot.
        table = fallback.load_fallbacks()
        self.assertGreaterEqual(len(table), 1, "an empty file would make the two "
                                "tests above checks that cannot fail")
        chained = sorted(set(table.values()) & set(table))
        self.assertEqual(chained, [], f"these targets carry a fallback: {chained}")


if __name__ == "__main__":
    unittest.main()

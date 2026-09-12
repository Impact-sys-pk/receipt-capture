r"""Two corrections in `resolve_receipt()`, from amendments 343 and 344.

From `PROMPT_claude_code_2026-09-12_service_corrections.md`, items 2 and 4.
Items 1 and 3 are deletions and their evidence is an enumeration and a green
suite, so they have no tests of their own beyond the two assertions item 1
removes.

## Item 2: the command-line route checks the code against the client's chart

**Amendment 344, point three. Paul's decision, and it changes behaviour.**

Two routes teach `categorisations_client_vendors` and their guards differed.
`_apply_filed_note()` requires the operator's code to be in the client's chart,
through `_resolve_category()`'s `chart_confirmed`. `resolve_receipt()` required
only that a code existed.

**On the command line the code is typed**, so a typo, an old code or another
client's code all taught happily, and **a mapping taught from a code the chart
does not hold can never work as taught**: layer 1 returns it with confidence
`high` and the chart check substitutes or strips it on every future receipt,
silently.

**What is given up is intended and small.** A correction carrying a code the
chart does not hold no longer teaches the mapping. The receipt is still
corrected and still filed, which `test_the_receipt_is_still_corrected_and_filed`
holds.

**The firm write is unaffected either way**, because
`_learn_firm_mapping_if_confirmed()` checks the chart outcome itself. Asserted
in `TheFirmWriteIsUnaffectedTest` rather than left to be inferred.

## Item 4: a correction that clears `possible_duplicate` says so in `run.log`

**Amendment 343. Paul's decision, and it is a control against a double-claimed
expense.**

`resolve_receipt()` ends with an unconditional status write of `ok`, so
correcting a receipt flagged `possible_duplicate` clears the flag and the
receipt drains into the books. **The guard against that is already written and
sits in a branch a corrected receipt with sound figures never reaches.**

**The guard is deliberately NOT moved.** Hoisting it would leave a corrected
receipt at `possible_duplicate` for ever, because nothing else clears that
status, so it would strand receipts rather than fix anything. What is wanted is
that the pipeline says it out loud.

**The precedent is three lines away**: the `despite` warning that fires when a
receipt reaches `ok` by decision despite failed checks. Same reason, in
amendment 343's words: Paul reads `run.log`, and a receipt that silently turns
green is worse than the fault being fixed.
"""

import unittest
from datetime import datetime, timezone

import config

from chart_fixtures import TempChartBundle
from resolution_fixtures import TempEnvironment, rows
from worker.database.repository import Repository
from worker.resolution import service
from worker.resolution.service import parse_corrections, resolve_receipt

#: The two accounts the fixture's chart holds, as the other chart-aware test
#: files name them. Four digits: any three-digit code is legacy, amendment 96.
IN_CHART = ("7304", "Parking and tolls")
ALSO_IN_CHART = ("7300", "Motor expenses")

#: A code no chart in these tests holds. The typo case.
NOT_IN_CHART = "9999"

SUPPLIER = "Apcoa Parking"
VENDOR_KEY = "apcoa parking"


def corrections_with(**overrides):
    """The good corrections every other resolution test uses, plus overrides."""
    corrections, errors = parse_corrections(
        {"supplier_name": SUPPLIER, "gross_amount": "12.00"})
    assert errors == {}
    for key, value in overrides.items():
        setattr(corrections, key, value)
    return corrections


class ServiceCorrectionTestCase(unittest.TestCase):
    """A temp environment and a chart holding two accounts."""

    def setUp(self):
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.chart = TempChartBundle(accounts=(IN_CHART, ALSO_IN_CHART)).__enter__()
        self.addCleanup(self.chart.__exit__, None, None, None)

    def resolve(self, corrections, *, receipt_id="r-1", status="needs_review",
                seed=True, **seed_kwargs):
        repo = Repository()
        try:
            if seed:
                self.env.seed(repo, receipt_id=receipt_id, status=status,
                              **seed_kwargs)
                if status != "needs_review":
                    repo.update_receipt_status(receipt_id, status)
            outcome = resolve_receipt(
                repo, self.env.engine(repo), receipt_id, corrections,
                actor="paul", source="console")
            learned = rows(repo, "SELECT * FROM categorisations_client_vendors")
            firm = rows(repo, "SELECT * FROM categorisations_firm_vendors")
            row = repo.get_receipt(receipt_id)
        finally:
            repo.close()
        return outcome, learned, firm, row


class TheChartConfirmedGuardTest(ServiceCorrectionTestCase):
    """Item 2. The command-line route now matches the Desktop route."""

    def test_a_code_the_chart_holds_still_teaches_the_mapping(self):
        """The control. Without this the test below would pass on a guard that
        refused everything."""
        outcome, learned, _firm, _row = self.resolve(corrections_with(
            remember_gl_for_supplier=True,
            gl_nominal_code=IN_CHART[0],
            gl_account_name=IN_CHART[1]))
        self.assertEqual(outcome.outcome, "filed", outcome.message)
        self.assertEqual(len(learned), 1, "a code in the chart teaches")
        self.assertEqual(learned[0]["nominal_code"], IN_CHART[0])
        self.assertEqual(learned[0]["vendor_key"], VENDOR_KEY)

    def test_a_code_the_chart_does_not_hold_teaches_nothing(self):
        outcome, learned, _firm, _row = self.resolve(corrections_with(
            remember_gl_for_supplier=True,
            gl_nominal_code=NOT_IN_CHART,
            gl_account_name="Something typed by hand"))
        self.assertEqual(outcome.outcome, "filed", outcome.message)
        self.assertEqual(
            learned, [],
            "a mapping taught from a code the client's chart does not hold can "
            "never work as taught: layer 1 returns it with confidence high and "
            "the chart check strips it on every future receipt")

    def test_the_receipt_is_still_corrected_and_filed(self):
        """What is given up is the learning and nothing else."""
        outcome, _learned, _firm, row = self.resolve(corrections_with(
            remember_gl_for_supplier=True,
            gl_nominal_code=NOT_IN_CHART,
            gl_account_name="Something typed by hand"))
        self.assertEqual(outcome.outcome, "filed")
        self.assertEqual(row["status"], "ok")
        self.assertEqual(outcome.category_code, NOT_IN_CHART,
                         "the operator's code still wins on the receipt itself")

    def test_it_says_why_it_did_not_learn(self):
        """A silent refusal would be the fault this project objects to most.

        The Desktop route already says it, through `_resolve_category()`'s
        validation note. This is the same thing on the other route.
        """
        repo = Repository()
        try:
            self.env.seed(repo)
            with self.assertLogs("worker.resolution.service",
                                 level="WARNING") as captured:
                resolve_receipt(
                    repo, self.env.engine(repo), "r-1",
                    corrections_with(remember_gl_for_supplier=True,
                                     gl_nominal_code=NOT_IN_CHART,
                                     gl_account_name="Typed"),
                    actor="paul", source="console")
        finally:
            repo.close()
        message = "\n".join(captured.output)
        self.assertIn(NOT_IN_CHART, message)
        self.assertIn("r-1", message)

    def test_an_unreadable_chart_teaches_nothing_either(self):
        """`get_chart_accounts_for_client()` returns an empty mapping both when
        the chart is empty and when the bundle is missing, and an empty read is
        not evidence the account is absent. `_resolve_category()` already
        refuses to learn there; this route now matches.
        """
        self.chart.__exit__(None, None, None)
        empty = self.env.path / "no-bundle"
        empty.mkdir(exist_ok=True)
        saved = config.CHARTS_DIR
        config.CHARTS_DIR = empty
        self.addCleanup(setattr, config, "CHARTS_DIR", saved)
        from worker.categorisation import chart
        chart._CACHE.clear()
        chart._ACCOUNT_CACHE.clear()

        _outcome, learned, _firm, _row = self.resolve(corrections_with(
            remember_gl_for_supplier=True,
            gl_nominal_code=IN_CHART[0],
            gl_account_name=IN_CHART[1]))
        self.assertEqual(learned, [])

    def test_no_tick_still_teaches_nothing(self):
        """11.3 is unchanged by any of this."""
        _outcome, learned, _firm, _row = self.resolve(corrections_with(
            gl_nominal_code=IN_CHART[0], gl_account_name=IN_CHART[1]))
        self.assertEqual(learned, [])


class TheFirmWriteIsUnaffectedTest(ServiceCorrectionTestCase):
    """Item 2 does not touch the firm pool, and that is asserted rather than
    inferred.

    `_learn_firm_mapping_if_confirmed()` checks the chart outcome itself, and it
    needs a classifier answer, which no engine built here can produce.
    """

    def test_the_firm_pool_is_untouched_whichever_way_the_guard_falls(self):
        for code in (IN_CHART[0], NOT_IN_CHART):
            with self.subTest(code=code):
                _outcome, _learned, firm, _row = self.resolve(
                    corrections_with(remember_gl_for_supplier=True,
                                     gl_nominal_code=code,
                                     gl_account_name="Whatever"),
                    receipt_id=f"r-{code}")
                self.assertEqual(firm, [])


class ThePossibleDuplicateWarningTest(ServiceCorrectionTestCase):
    """Item 4. The finding is cleared, and now it is said out loud."""

    def seed_possible_duplicate(self, repo, receipt_id="r-1",
                                duplicate_of="r-original"):
        self.env.seed(repo, receipt_id=receipt_id)
        repo.update_receipt_status(receipt_id, "possible_duplicate")
        repo._conn.execute(
            "UPDATE receipts SET duplicate_of = ? WHERE receipt_id = ?",
            (duplicate_of, receipt_id))
        repo._conn.commit()

    def test_it_warns_and_names_both_receipts(self):
        repo = Repository()
        try:
            self.seed_possible_duplicate(repo)
            with self.assertLogs("worker.resolution.service",
                                 level="WARNING") as captured:
                outcome = resolve_receipt(
                    repo, self.env.engine(repo), "r-1", corrections_with(),
                    actor="paul", source="console")
            row = repo.get_receipt("r-1")
        finally:
            repo.close()

        self.assertEqual(outcome.outcome, "filed", outcome.message)
        warnings = [line for line in captured.output
                    if service.POSSIBLE_DUPLICATE_STATUS in line]
        self.assertEqual(len(warnings), 1,
                         f"one warning, not none and not two: {captured.output}")
        self.assertIn("r-1", warnings[0])
        self.assertIn("r-original", warnings[0],
                      "the receipt it looked like a duplicate of must be named, "
                      "or the warning cannot be acted on")

        # And the status really did move, which is what makes the warning
        # necessary rather than decorative.
        self.assertEqual(row["status"], "ok")
        self.assertEqual(row["duplicate_of"], "r-original",
                         "the link survives the status change, which is the "
                         "other half of amendment 343's finding")

    def test_it_does_not_fire_on_an_ordinary_correction(self):
        """The negative control. A check that cannot fail is not a check.

        `CLAUDE.md`, amendment 97: the tell is that it has never once returned
        anything but a pass.
        """
        repo = Repository()
        try:
            self.env.seed(repo)  # needs_review, not possible_duplicate
            with self.assertLogs("worker.resolution.service",
                                 level="INFO") as captured:
                resolve_receipt(
                    repo, self.env.engine(repo), "r-1", corrections_with(),
                    actor="paul", source="console")
        finally:
            repo.close()
        offenders = [line for line in captured.output
                     if service.POSSIBLE_DUPLICATE_STATUS in line
                     and line.startswith("WARNING")]
        self.assertEqual(
            offenders, [],
            f"the warning fired on a receipt that was never a possible "
            f"duplicate: {offenders}")

    def test_a_receipt_that_was_already_ok_does_not_warn(self):
        """The other direction of the same control."""
        repo = Repository()
        try:
            self.env.seed(repo, receipt_id="r-2")
            repo.update_receipt_status("r-2", "needs_review")
            with self.assertLogs("worker.resolution.service",
                                 level="INFO") as captured:
                resolve_receipt(
                    repo, self.env.engine(repo), "r-2", corrections_with(),
                    actor="paul", source="console")
        finally:
            repo.close()
        offenders = [line for line in captured.output
                     if line.startswith("WARNING")
                     and service.POSSIBLE_DUPLICATE_STATUS in line]
        self.assertEqual(offenders, [])


class TheStatusLiteralTest(unittest.TestCase):
    r"""One name for the status, not two literals that have to agree.

    `preserve_status` and the new warning both ask whether this receipt was a
    possible duplicate. Two copies of the string in one function is the drift
    this project's own flag list objects to, so there is one constant and both
    read it.
    """

    def test_the_constant_holds_the_status_the_pipeline_writes(self):
        # Read off the writer rather than asserted as a literal here, so a
        # rename in the pipeline goes red rather than leaving this agreeing
        # with itself.
        import source_guards
        tree = source_guards.tree_of("worker", "extraction_pipeline.py")
        found = source_guards.string_constants_equal_to(
            tree, service.POSSIBLE_DUPLICATE_STATUS)
        self.assertTrue(
            found,
            f"{service.POSSIBLE_DUPLICATE_STATUS!r} is no longer written by "
            "worker\\extraction_pipeline.py, so the resolution service is "
            "watching for a status nothing produces")

    def test_the_service_holds_no_second_copy_of_the_literal(self):
        import source_guards
        tree = source_guards.tree_of("worker", "resolution", "service.py")
        lines = source_guards.string_constants_equal_to(
            tree, service.POSSIBLE_DUPLICATE_STATUS)
        self.assertEqual(
            len(lines), 1,
            f"the status literal appears at lines {lines}. One constant, read "
            "by everything that needs it, or the two copies drift")


if __name__ == "__main__":
    unittest.main()

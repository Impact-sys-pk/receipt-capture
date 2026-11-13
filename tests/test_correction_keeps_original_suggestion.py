r"""A correction carries the original run's suggestion. Sub-step 10bs.11.

Step 10bs of `2026-07-25_BUILD_STATUS.md`, amendment 548 item 11 of
`2026-07-25_CONSOLE_DESIGN.md`, brief
`PROMPT_claude_code_2026-11-13_vendor_lookup.md`.

## The defect

Every correction re-ran `categorise()` and stored what it said beside the
operator's choice. That stored a suggestion nobody was shown: on receipt
`52e76e99` the original run said `7301 Fuel and oil` and the correction run,
five minutes later on the same document, said `7340 Parking and tolls`, and the
second is the row kept. On a receipt no mapping answers it also cost an OpenAI
call, for an answer overwritten in the same transaction.

## Paul's decision, option B of three, 2026-11-13

A correction does not re-run the engine. Its new `categorisations` row carries
the suggestion from the original run. Append-only is unchanged: the correction
still writes its own `manual_correction` extraction row and its own
categorisation row.

## Two routes and three entry points

`categorise()` was called from two places in `worker\resolution\service.py`:
`resolve_receipt()`, which serves the CLI, the console, `_settle_note()` and
`_apply_corrected_note()`; and `_apply_filed_note()`. Both are driven here.

## Which run is "the original"

The most recent `categorisations` row attached to an extraction that is NOT a
`manual_correction`. That is the pipeline's answer, from the live poll, the
recovery sweep or an auto-retry, and it is what the receipt was published with.
A correction row written before this change is skipped, because it is exactly
the kind of row this sub-step says was never on screen.

## Where there is no original run

A receipt that reached review never reached the engine, because the pipeline
categorises only an `ok` receipt. Its correction now writes an `unmatched` row:
no code, confidence `none`. Nothing was suggested and nothing is invented.
"""

import json
import unittest
import uuid

import config

from chart_fixtures import TempChartBundle
from resolution_fixtures import TempEnvironment, good_corrections, rows
from worker.categorisation.engine import (
    CategorisationEngine,
    extract_vendor_key,
    normalise_description,
)
from worker.database.repository import Repository
from worker.resolution.service import apply_resolution_note, resolve_receipt

IN_CHART = ("7304", "Parking and tolls")
ALSO_IN_CHART = ("7300", "Motor expenses")
# The account the classifier named before the chart check substituted it.
NOT_IN_CHART = ("7391", "Car wash")
SUPPLIER = "Apcoa Parking"
KEY = "apcoa parking"
TRADE = "UNSPECIFIED"
FILED_RELATIVE = (
    r"Clients\Test Client\IntelliBooks\Receipts\2026-27"
    r"\2026-04-01_apcoa-parking_96.00.pdf")


class CountingEngine(CategorisationEngine):
    """The real engine, counting calls to categorise(). It must stay at nought."""

    def __init__(self, repo):
        super().__init__(repo=repo, enable_ai_fallback=False)
        self.calls = 0

    def categorise(self, *args, **kwargs):
        self.calls += 1
        return super().categorise(*args, **kwargs)


class _Base(unittest.TestCase):
    def setUp(self):
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.chart = TempChartBundle(accounts=(IN_CHART, ALSO_IN_CHART)).__enter__()
        self.addCleanup(self.chart.__exit__, None, None, None)
        self.repo = Repository()
        self.addCleanup(self.repo.close)
        self.engine = CountingEngine(self.repo)

    def seed(self, status="needs_review"):
        self.env.seed(self.repo, receipt_id="r-1", status=status,
                      supplier_name=SUPPLIER, gross_amount=12.0,
                      validation_status="ok", validation_notes=[])

    def original_run(self, code=IN_CHART, match_source="ai", confidence="low",
                     extraction_id="ext-r-1", when="2026-11-13T12:22:16+00:00",
                     mapping_id=None):
        self.repo.save_categorisation(
            categorisation_id=str(uuid.uuid4()), receipt_id="r-1",
            extraction_id=extraction_id, client_id="CLIENT001", trade=TRADE,
            mapping_id=mapping_id, suggested_code=code[0] if code else None,
            suggested_name=code[1] if code else None, confidence=confidence,
            match_source=match_source, matched_vendor=KEY,
            needs_review=match_source not in ("client", "firm", "rule"),
            categorised_at=when)

    def latest(self):
        return rows(self.repo,
                    "SELECT * FROM categorisations WHERE receipt_id = 'r-1' "
                    "ORDER BY categorised_at DESC, rowid DESC")[0]

    def resolve(self, remember=False, code=ALSO_IN_CHART, supplier=SUPPLIER):
        corrections = good_corrections()
        corrections.values["supplier_name"] = supplier
        corrections.gl_nominal_code = code[0]
        corrections.gl_account_name = code[1]
        corrections.remember_gl_for_supplier = remember
        return resolve_receipt(self.repo, self.engine, "r-1", corrections,
                               actor="test", source="cli")


class TheCorrectionCopiesTheOriginalTest(_Base):

    def test_resolve_receipt_copies_and_never_calls_the_engine(self):
        self.seed()
        self.original_run(code=IN_CHART, match_source="ai", confidence="low")
        outcome = self.resolve(code=ALSO_IN_CHART)
        self.assertEqual(outcome.outcome, "filed", outcome.message)
        self.assertEqual(self.engine.calls, 0)
        row = self.latest()
        extraction = rows(self.repo, "SELECT engine FROM extractions WHERE extraction_id = ?",
                          (row["extraction_id"],))[0]
        self.assertEqual(extraction["engine"], "manual_correction",
                         "the new row hangs off the correction's own extraction")
        self.assertEqual(
            (row["suggested_code"], row["suggested_name"], row["match_source"],
             row["confidence"], row["matched_vendor"]),
            (IN_CHART[0], IN_CHART[1], "ai", "low", KEY))
        self.assertEqual((row["correction_code"], row["correction_name"]), ALSO_IN_CHART)

    def test_a_layer_one_original_keeps_its_mapping_id(self):
        self.seed()
        self.original_run(code=IN_CHART, match_source="client", confidence="high",
                          mapping_id="m-123")
        self.resolve()
        row = self.latest()
        self.assertEqual((row["mapping_id"], row["match_source"], row["needs_review"]),
                         ("m-123", "client", 0))

    def test_an_earlier_correction_row_is_not_the_original(self):
        """The 52e76e99 shape: a correction run that disagreed with the original."""
        self.seed()
        self.original_run(code=IN_CHART, when="2026-11-13T12:22:16+00:00")
        self.repo.save_extraction(
            extraction_id="ext-corr-old", receipt_id="r-1", engine="manual_correction",
            supplier_name=SUPPLIER, invoice_date="2026-04-01", net_amount=None,
            vat_amount=None, gross_amount=12.0, currency="GBP", raw_response="{}",
            validation_status="ok", validation_notes=[], update_status=False)
        self.original_run(code=ALSO_IN_CHART, extraction_id="ext-corr-old",
                          when="2026-11-13T12:27:18+00:00")
        self.resolve()
        self.assertEqual(self.latest()["suggested_code"], IN_CHART[0])

    def test_no_original_run_writes_an_unmatched_row_and_calls_nothing(self):
        self.seed()
        outcome = self.resolve(code=ALSO_IN_CHART)
        self.assertEqual(outcome.outcome, "filed", outcome.message)
        self.assertEqual(self.engine.calls, 0)
        row = self.latest()
        self.assertEqual(
            (row["suggested_code"], row["match_source"], row["confidence"], row["mapping_id"]),
            (None, "unmatched", "none", None))
        self.assertEqual(row["correction_code"], ALSO_IN_CHART[0],
                         "the operator's choice is still recorded")

    def test_the_filed_note_route_copies_too(self):
        self.seed()
        self.original_run(code=IN_CHART, match_source="ai")
        target = config.PRACTICE_ROOT / FILED_RELATIVE.replace("\\", "/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("the copy Desktop filed", encoding="utf-8")
        outcome = apply_resolution_note(self.repo, self.engine, {
            "schema": 1, "receipt_id": "r-1", "client_id": "CLIENT001",
            "action": "filed", "resolved_by": "desktop",
            "resolved_at": "2026-11-13T14:02:11.000Z",
            "values": {"supplier_name": SUPPLIER, "invoice_date": "2026-04-01",
                       "net_amount": 10, "vat_amount": 2, "gross_amount": 12,
                       "currency": "GBP", "category_code": ALSO_IN_CHART[0],
                       "category_name": ALSO_IN_CHART[1]},
            "filed_path": FILED_RELATIVE,
        })
        self.assertEqual(outcome.outcome, "filed", outcome.message)
        self.assertEqual(self.engine.calls, 0)
        row = self.latest()
        self.assertEqual((row["suggested_code"], row["match_source"]), (IN_CHART[0], "ai"))
        self.assertEqual(row["correction_code"], ALSO_IN_CHART[0])


class TheTeachingSurvivesTest(_Base):

    def client_rows(self):
        return rows(self.repo, "SELECT * FROM categorisations_client_vendors")

    def firm_rows(self):
        return rows(self.repo, "SELECT * FROM categorisations_firm_vendors")

    def test_the_tick_still_teaches_the_client_table(self):
        self.seed()
        self.original_run(code=IN_CHART)
        self.resolve(remember=True, code=ALSO_IN_CHART)
        taught = self.client_rows()
        self.assertEqual(len(taught), 1)
        self.assertEqual((taught[0]["vendor_key"], taught[0]["vendor_name"],
                          taught[0]["nominal_code"]),
                         (KEY, SUPPLIER, ALSO_IN_CHART[0]))

    def test_the_key_comes_from_the_corrected_name_not_the_original(self):
        """The operator fixed the supplier name. The key must be the new name's,
        or the taught row pairs one name with another name's key."""
        self.seed()
        self.original_run(code=IN_CHART)
        self.resolve(remember=True, supplier="Euro Car Parks")
        taught = self.client_rows()
        # Three words, so the key builder keeps the first: "euro". Taken from
        # the builder rather than written out, which is what got it wrong once.
        expected = extract_vendor_key(normalise_description("Euro Car Parks"))
        self.assertNotEqual(expected, KEY)
        self.assertEqual((taught[0]["vendor_key"], taught[0]["vendor_name"]),
                         (expected, "Euro Car Parks"))

    def test_without_an_original_run_the_tick_still_teaches_the_client_table(self):
        self.seed()
        self.resolve(remember=True)
        self.assertEqual(len(self.client_rows()), 1)

    def test_confirming_the_original_classifier_still_teaches_the_firm_pool(self):
        self.seed()
        self.original_run(code=IN_CHART, match_source="ai")
        self.resolve(remember=True, code=IN_CHART)
        firm = self.firm_rows()
        self.assertEqual([(r["vendor_key"], r["nominal_code"]) for r in firm],
                         [(KEY, IN_CHART[0])])

    def test_a_substituted_original_teaches_the_firm_pool_the_classifiers_account(self):
        """The original run's chart check moved 7391 to 7304 and recorded it.
        The firm pool must learn 7391, which is what the classifier named."""
        self.seed()
        self.original_run(code=IN_CHART, match_source="ai")
        self.repo.save_resolution_event(
            event_id="ev-1", receipt_id="r-1", extraction_id="ext-r-1",
            actor="pipeline", source="categorisation", action="chart_fallback",
            outcome="substituted",
            corrections_json=json.dumps({
                "match_source": "ai", "suggested_code": NOT_IN_CHART[0],
                "suggested_name": NOT_IN_CHART[1], "resolved_code": IN_CHART[0],
                "resolved_name": IN_CHART[1]}),
            gl_override_code=IN_CHART[0], reason="substituted",
            created_at="2026-11-13T12:22:16+00:00")
        self.resolve(remember=True, code=IN_CHART)
        self.assertEqual([r["nominal_code"] for r in self.firm_rows()], [NOT_IN_CHART[0]])

    def test_without_an_original_run_the_firm_pool_is_not_taught(self):
        """Nothing was proposed, so there is nothing for the operator to confirm."""
        self.seed()
        self.resolve(remember=True, code=IN_CHART)
        self.assertEqual(self.firm_rows(), [])


class TheTwoRoutesReportConfidenceAlikeTest(_Base):
    """Amendment 552, Paul's decision of 2026-11-13: both routes give no
    confidence where the operator overrode the suggestion, and the
    suggestion's own where they did not. Nothing prints `_apply_filed_note()`'s
    today; this exists so the two routes cannot drift."""

    def filed_note(self, category):
        target = config.PRACTICE_ROOT / FILED_RELATIVE.replace("\\", "/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("the copy Desktop filed", encoding="utf-8")
        values = {"supplier_name": SUPPLIER, "invoice_date": "2026-04-01",
                  "net_amount": 10, "vat_amount": 2, "gross_amount": 12,
                  "currency": "GBP", "category_name": ""}
        if category:
            values.update(category_code=category[0], category_name=category[1])
        return apply_resolution_note(self.repo, self.engine, {
            "schema": 1, "receipt_id": "r-1", "client_id": "CLIENT001",
            "action": "filed", "resolved_by": "desktop",
            "resolved_at": "2026-11-13T14:02:11.000Z",
            "values": values, "filed_path": FILED_RELATIVE})

    def cli(self, category):
        corrections = good_corrections()
        if category:
            corrections.gl_nominal_code, corrections.gl_account_name = category
        return resolve_receipt(self.repo, self.engine, "r-1", corrections,
                               actor="test", source="cli")

    def confidence(self, route, category):
        self.seed()
        self.original_run(code=IN_CHART, confidence="low")
        outcome = route(category)
        self.assertEqual(outcome.outcome, "filed", outcome.message)
        return outcome.category_confidence

    def test_cli_route_override_gives_no_confidence(self):
        self.assertIsNone(self.confidence(self.cli, ALSO_IN_CHART))

    def test_filed_note_route_override_gives_no_confidence(self):
        self.assertIsNone(self.confidence(self.filed_note, ALSO_IN_CHART))

    def test_cli_route_no_override_gives_the_suggestions_confidence(self):
        self.assertEqual(self.confidence(self.cli, None), "low")

    def test_filed_note_route_no_override_gives_the_suggestions_confidence(self):
        self.assertEqual(self.confidence(self.filed_note, None), "low")


class NoCategoriseCallRemainsTest(unittest.TestCase):
    """Set guard: no correction route calls categorise(). Read from the syntax tree."""

    def test_service_py_calls_categorise_nowhere(self):
        import ast
        from pathlib import Path
        source = Path(__file__).resolve().parent.parent / "worker" / "resolution" / "service.py"
        calls = [n.lineno for n in ast.walk(ast.parse(source.read_text(encoding="utf-8")))
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "categorise"]
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()

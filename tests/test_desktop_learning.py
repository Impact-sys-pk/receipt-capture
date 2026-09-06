"""Sub-step 10j.11, the pipeline half: a Desktop filing that teaches a mapping.

Design document 12.2, 12.3 step 6 and 11.3, and Paul's three decisions of
2026-09-05 recorded in amendment 231. Three things are under test and they are
separable:

- **The note carries the code and the tick.** `category_code` beside
  `category_name`, `remember_gl_for_supplier` at the top level, `schema` still 1,
  and a note carrying neither field parses exactly as it did before they existed.
- **`_resolve_category()` validates rather than looks up.** It stopped returning
  None for every note. Five outcomes, one test each.
- **`_apply_filed_note()` learns, on the tick, and to the client table only.**

**The test that matters most here is the one that asserts a negative.**
`upsert_firm_vendor()` must not be called on this route. The firm pool is shared
across every client on a business_type, the only code Desktop can send comes from
one client's own chart, and Paul deferred the firm half as item 166. Nothing in
the code says "do not call this", so the assertion is the thing that protects it.

The learned row is checked twice over: once by reading it, and once by putting a
second receipt from the same supplier through the engine and watching layer 1
return the learned code. The second is what proves `vendor_key` and not
`mapping_id` is the right thing to write, because `vendor_key` is what layer 1
looks up. Both fields were renamed on 2026-09-06 and this sentence said the
same thing under the old names, `vendor_code` and `vendor_key`.
"""

import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402

from chart_fixtures import TempChartBundle  # noqa: E402
from resolution_fixtures import TempEnvironment, rows  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
from worker.resolution.service import (  # noqa: E402
    ResolutionNoteError,
    _resolve_category,
    parse_resolution_note,
)

import app  # noqa: E402

# The two accounts the client's chart holds in these tests. Four digits, because
# any three-digit code is legacy per amendment 96.
IN_CHART = ("7304", "Parking and tolls")
ALSO_IN_CHART = ("7300", "Motor expenses")
# In the master's vocabulary in real life, and deliberately not in this chart.
NOT_IN_CHART = "7391"

FILED_RELATIVE = (
    r"Clients\Test Client\IntelliBooks\Receipts\2026-27"
    r"\2026-04-01_apcoa-parking_96.00.pdf"
)


class _Absent:
    """Marks a key to remove rather than set. Absent is not the same as empty."""


_ABSENT = _Absent()


def note_payload(**overrides):
    """A filed note in the 12.2 shape, with the fields amendment 231 added."""
    payload = {
        "schema": 1,
        "receipt_id": "r-1",
        "client_id": "CLIENT001",
        "action": "filed",
        "resolved_by": "desktop",
        "resolved_at": "2026-09-05T14:02:11.000Z",
        "values": {
            "supplier_name": "Apcoa Parking",
            "invoice_date": "2026-04-01",
            "net_amount": 80,
            "vat_amount": 16,
            "gross_amount": 96,
            "currency": "GBP",
            "category_code": IN_CHART[0],
            "category_name": IN_CHART[1],
        },
        "filed_path": FILED_RELATIVE,
        "original_review_files": ["r-1.pdf", "r-1.pdf.review.json"],
    }
    payload.update(overrides)
    return payload


def values_with(**overrides):
    values = dict(note_payload()["values"])
    for key, value in overrides.items():
        if isinstance(value, _Absent):
            values.pop(key, None)
        else:
            values[key] = value
    return values


class NoteFieldsTest(unittest.TestCase):
    """12.2 as amended: two optional fields, and `schema` stays 1."""

    def test_a_note_with_neither_new_field_parses_exactly_as_it_did(self):
        # The whole reason `schema` stays 1: an old note must not fail, and must
        # not acquire behaviour it never asked for.
        payload = note_payload(
            values=values_with(category_code=_ABSENT, category_name="Parking and tolls")
        )
        note = parse_resolution_note(payload)

        self.assertEqual(note.action, "filed")
        self.assertEqual(note.receipt_id, "r-1")
        self.assertEqual(note.resolved_at, "2026-09-05T14:02:11.000Z")
        self.assertEqual(note.category_name, "Parking and tolls")
        self.assertEqual(note.values["supplier_name"], "Apcoa Parking")
        self.assertEqual(note.values["gross_amount"], 96.00)
        self.assertIsNone(note.category_code, "no code was sent, so none is invented")
        self.assertFalse(note.remember_gl_for_supplier, "absent means no")

    def test_an_older_note_puts_the_code_in_category_name_and_is_read_as_a_code(self):
        # Every note Desktop has written to date: catOptions() builds the option
        # with the code as its value and fileReviewReceipt() writes that value
        # into category_name.
        note = parse_resolution_note(
            note_payload(values=values_with(category_code=_ABSENT, category_name="7304"))
        )
        self.assertEqual(note.category_code, "7304")
        self.assertIsNone(note.category_name, "it was never a name")

    def test_a_three_digit_legacy_code_in_category_name_is_left_as_a_name(self):
        # Amendment 96: codes are four digits. The older-note rule is narrow on
        # purpose, because it is a guess and the guess has to be safe.
        note = parse_resolution_note(
            note_payload(values=values_with(category_code=_ABSENT, category_name="271"))
        )
        self.assertIsNone(note.category_code)
        self.assertEqual(note.category_name, "271")

    def test_the_code_wins_over_a_four_digit_name_when_both_are_sent(self):
        note = parse_resolution_note(
            note_payload(values=values_with(category_code="7300", category_name="7304"))
        )
        self.assertEqual(note.category_code, "7300")
        self.assertEqual(note.category_name, "7304")

    def test_a_blank_or_padded_code_is_normalised(self):
        self.assertIsNone(
            parse_resolution_note(
                note_payload(values=values_with(category_code="  "))
            ).category_code
        )
        self.assertEqual(
            parse_resolution_note(
                note_payload(values=values_with(category_code=" 7304 "))
            ).category_code,
            "7304",
        )

    def test_a_non_text_code_is_refused(self):
        with self.assertRaises(ResolutionNoteError) as raised:
            parse_resolution_note(note_payload(values=values_with(category_code=7304)))
        self.assertIn("category_code", str(raised.exception))

    def test_the_tick_is_read_from_the_top_level_of_the_note(self):
        self.assertTrue(
            parse_resolution_note(
                note_payload(remember_gl_for_supplier=True)
            ).remember_gl_for_supplier
        )
        self.assertFalse(
            parse_resolution_note(
                note_payload(remember_gl_for_supplier=False)
            ).remember_gl_for_supplier
        )

    def test_a_tick_inside_values_is_not_the_tick(self):
        # 12.2 states it at the top level. A note that puts it in `values` has not
        # set it, and must not be half-read as if it had.
        note = parse_resolution_note(
            note_payload(values=values_with(remember_gl_for_supplier=True))
        )
        self.assertFalse(note.remember_gl_for_supplier)

    def test_a_non_boolean_tick_is_a_note_error(self):
        for supplied in ("true", 1, [], {}):
            with self.subTest(supplied=supplied):
                with self.assertRaises(ResolutionNoteError) as raised:
                    parse_resolution_note(note_payload(remember_gl_for_supplier=supplied))
                self.assertIn("remember_gl_for_supplier", str(raised.exception))

    def test_the_schema_number_did_not_move(self):
        from worker.resolution.service import NOTE_SCHEMA

        self.assertEqual(NOTE_SCHEMA, 1)
        with self.assertRaises(ResolutionNoteError):
            parse_resolution_note(note_payload(schema=2))


class ResolveCategoryTest(unittest.TestCase):
    """12.3 step 6 reversed: one test per outcome of the chart validation."""

    def setUp(self):
        self._chart = TempChartBundle(accounts=(IN_CHART, ALSO_IN_CHART)).__enter__()
        self.addCleanup(self._chart.__exit__, None, None, None)

    def decide(self, **values):
        return _resolve_category(
            parse_resolution_note(note_payload(values=values_with(**values))),
            "CLIENT001",
        )

    def test_no_code_and_no_name_decides_nothing(self):
        decision = self.decide(category_code=_ABSENT, category_name="")
        self.assertEqual(
            (decision.code, decision.name, decision.validation_note),
            (None, None, None),
        )
        self.assertFalse(decision.chart_confirmed)

    def test_a_code_in_the_chart_is_stored_with_the_charts_own_name(self):
        # The name comes from the chart and not from the note, so the stored pair
        # cannot disagree. The note here sends a name that is wrong on purpose.
        decision = self.decide(category_code=IN_CHART[0], category_name="Parkin & tols")
        self.assertEqual(decision.code, IN_CHART[0])
        self.assertEqual(decision.name, IN_CHART[1])
        self.assertIsNone(decision.validation_note)
        self.assertTrue(decision.chart_confirmed)

    def test_a_code_the_chart_does_not_hold_is_rejected_and_named(self):
        decision = self.decide(category_code=NOT_IN_CHART, category_name="Car wash")
        self.assertIsNone(decision.code, "a code the chart does not hold is not stored")
        self.assertEqual(decision.name, "Car wash", "the name the operator sent is kept")
        self.assertIn(NOT_IN_CHART, decision.validation_note)
        self.assertIn("not in client CLIENT001's chart", decision.validation_note)
        self.assertFalse(decision.chart_confirmed)

    def test_the_fallback_table_is_not_applied_to_a_code_a_person_chose(self):
        # Paul's decision, 2026-09-05. fallback_accounts.csv substitutes for an
        # account the classifier proposed. This code came out of the operator's
        # own chart, so if it has since left that chart a person sees it.
        self._chart.__exit__(None, None, None)
        with TempChartBundle(
            accounts=(IN_CHART, ALSO_IN_CHART),
            fallbacks=((NOT_IN_CHART, ALSO_IN_CHART[0]),),
        ):
            decision = self.decide(category_code=NOT_IN_CHART, category_name="Car wash")
        self._chart = TempChartBundle(accounts=(IN_CHART, ALSO_IN_CHART)).__enter__()

        self.assertIsNone(decision.code)
        self.assertNotIn(ALSO_IN_CHART[0], decision.validation_note or "")

    def test_a_name_and_no_code_is_stored_as_a_name(self):
        decision = self.decide(category_code=_ABSENT, category_name="Parking and tolls")
        self.assertIsNone(decision.code)
        self.assertEqual(decision.name, "Parking and tolls")
        self.assertIn("chart of accounts", decision.validation_note.lower())
        self.assertFalse(decision.chart_confirmed)

    def test_a_chart_that_cannot_be_read_leaves_the_code_standing_unconfirmed(self):
        # An empty read is not evidence the account is absent, which is what
        # resolve_against_chart() already rules for the same situation. The code
        # stands so an unpublished bundle does not strip every category in the
        # practice, and it stands unconfirmed so nothing learns from it.
        self._chart.__exit__(None, None, None)
        with TempChartBundle(accounts=()) as bundle:
            (bundle.path / config.MASTER_CHART_FILENAME).unlink()
            decision = self.decide(category_code=IN_CHART[0], category_name="Parking")
        self._chart = TempChartBundle(accounts=(IN_CHART, ALSO_IN_CHART)).__enter__()

        self.assertEqual(decision.code, IN_CHART[0], "the code stands")
        self.assertFalse(decision.chart_confirmed, "and it is not confirmed")
        self.assertIn("could not be read", decision.validation_note)


class FiledNoteLearningTest(unittest.TestCase):
    """Task 3: the write, the tick that gates it, and the table not written."""

    def setUp(self):
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.chart = TempChartBundle(accounts=(IN_CHART, ALSO_IN_CHART)).__enter__()
        self.addCleanup(self.chart.__exit__, None, None, None)

    def seed(self, receipt_id="r-1", relative=FILED_RELATIVE):
        repo = Repository()
        try:
            self.env.seed(repo, receipt_id=receipt_id)
        finally:
            repo.close()
        target = config.PRACTICE_ROOT / Path(relative.replace("\\", "/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("the copy Desktop filed", encoding="utf-8")
        return target

    def write_note(self, payload):
        config.RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        path = config.RESOLUTIONS_DIR / f"{payload['receipt_id']}_1757080931000.json"
        path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        return path

    def consume(self):
        from worker.categorisation.engine import CategorisationEngine

        repo = Repository()
        try:
            stats = {}
            app._consume_resolution_notes(
                repo, CategorisationEngine(repo=repo, enable_ai_fallback=False), stats
            )
            return stats
        finally:
            repo.close()

    def learned(self):
        repo = Repository()
        try:
            return rows(repo, "SELECT * FROM categorisations_client_vendors")
        finally:
            repo.close()

    def test_the_tick_writes_one_client_vendor_row(self):
        self.seed()
        self.assertEqual(self.learned(), [], "nothing has ever been learned")

        self.write_note(note_payload(remember_gl_for_supplier=True))
        stats = self.consume()

        self.assertEqual(stats.get("notes_applied"), 1)
        learned = self.learned()
        self.assertEqual(len(learned), 1)
        self.assertEqual(learned[0]["client_id"], "CLIENT001")
        self.assertEqual(learned[0]["nominal_code"], IN_CHART[0])
        self.assertEqual(learned[0]["account_name"], IN_CHART[1])
        self.assertEqual(learned[0]["vendor_name"], "Apcoa Parking")
        self.assertEqual(learned[0]["times_seen"], 1)

    def test_what_is_written_is_the_vendor_key_layer_one_looks_up(self):
        # Not the mapping_id, which is the row id of a mapping that
        # already exists and is None on exactly the receipts worth learning from.
        # The proof is a second receipt from the same supplier: it must come back
        # from layer 1 with the learned code.
        self.seed()
        self.write_note(note_payload(remember_gl_for_supplier=True))
        self.consume()

        second = r"Clients\Test Client\IntelliBooks\Receipts\2026-27\second.pdf"
        self.seed(receipt_id="r-2", relative=second)
        self.write_note(note_payload(
            receipt_id="r-2",
            filed_path=second,
            values=values_with(category_code=_ABSENT, category_name=""),
            original_review_files=["r-2.pdf"],
        ))
        self.consume()

        repo = Repository()
        try:
            categorisation = repo.get_categorisation_for_receipt("r-2")
        finally:
            repo.close()
        self.assertEqual(categorisation["match_source"], "client")
        self.assertEqual(categorisation["suggested_code"], IN_CHART[0])
        self.assertEqual(categorisation["suggested_name"], IN_CHART[1])

        # And the row points back at the mapping that answered, by its row id.
        #
        # Added 2026-09-06 because a mutation survived: swapping the two kwargs
        # at layer 1 in engine.py, so that `vendor_key` carried the row id and
        # `mapping_id` carried the normalised key, turned the whole suite green.
        # Nothing anywhere asserted what a matched receipt stores in either
        # field, because every categorisations row in existence is unmatched.
        learned = self.learned()
        self.assertEqual(len(learned), 1)
        self.assertEqual(categorisation["mapping_id"], learned[0]["mapping_id"])
        self.assertEqual(learned[0]["vendor_key"], "apcoa parking",
                         "the normalised key, not a row id")

    def test_without_the_tick_the_same_note_learns_nothing(self):
        self.seed()
        self.write_note(note_payload())
        stats = self.consume()

        self.assertEqual(stats.get("notes_applied"), 1, "the filing still happened")
        self.assertEqual(self.learned(), [], "and it taught nothing")

    def test_a_code_the_chart_does_not_hold_teaches_nothing_even_with_the_tick(self):
        self.seed()
        self.write_note(note_payload(
            remember_gl_for_supplier=True,
            values=values_with(category_code=NOT_IN_CHART, category_name="Car wash"),
        ))
        self.consume()

        self.assertEqual(self.learned(), [])
        repo = Repository()
        try:
            categorisation = repo.get_categorisation_for_receipt("r-1")
            self.assertIsNone(categorisation["correction_code"])
            self.assertEqual(categorisation["correction_name"], "Car wash")
        finally:
            repo.close()

    def test_a_name_with_no_code_teaches_nothing_even_with_the_tick(self):
        self.seed()
        self.write_note(note_payload(
            remember_gl_for_supplier=True,
            values=values_with(category_code=_ABSENT, category_name="Parking and tolls"),
        ))
        self.consume()

        self.assertEqual(self.learned(), [])

    def test_an_unreadable_chart_teaches_nothing_even_with_the_tick(self):
        # _resolve_category() leaves the code standing when the bundle cannot be
        # read, because an empty read is not evidence the account is absent. It
        # leaves it unconfirmed, and this is the half that matters: a mapping is
        # a durable write that layer 1 reads back as an exact match, so nothing
        # is learned from a code nothing could check.
        self.seed()
        (self.chart.path / config.MASTER_CHART_FILENAME).unlink()
        self.write_note(note_payload(remember_gl_for_supplier=True))
        self.consume()

        self.assertEqual(self.learned(), [], "nothing was learned")
        repo = Repository()
        try:
            categorisation = repo.get_categorisation_for_receipt("r-1")
            self.assertEqual(
                categorisation["correction_code"], IN_CHART[0],
                "and the code still stands on the row",
            )
        finally:
            repo.close()

    def test_the_firm_table_is_never_written_on_this_route(self):
        # Item 166 is deferred, and this assertion is what defers it. The firm
        # pool is shared across every client on a business_type; the only code
        # Desktop can send comes from one client's own chart.
        self.seed()
        self.write_note(note_payload(remember_gl_for_supplier=True))

        with patch.object(Repository, "upsert_firm_vendor") as firm:
            self.consume()

        self.assertEqual(firm.call_count, 0, "upsert_firm_vendor() is item 166")
        self.assertEqual(len(self.learned()), 1, "and the client table was written")

        repo = Repository()
        try:
            self.assertEqual(
                rows(repo, "SELECT * FROM categorisations_firm_vendors"), []
            )
        finally:
            repo.close()

    def test_learning_leaves_its_own_audit_row(self):
        self.seed()
        self.write_note(note_payload(remember_gl_for_supplier=True))
        self.consume()

        repo = Repository()
        try:
            events = rows(
                repo, "SELECT * FROM resolution_events WHERE action = 'learn_vendor'"
            )
        finally:
            repo.close()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["actor"], "desktop", "a person ticked the box")
        self.assertEqual(events[0]["source"], "desktop")
        self.assertEqual(events[0]["outcome"], "learned")
        self.assertEqual(events[0]["gl_override_code"], IN_CHART[0])
        recorded = json.loads(events[0]["corrections_json"])
        self.assertTrue(recorded["remember_gl_for_supplier"], "11.3: record the choice")
        self.assertEqual(recorded["nominal_code"], IN_CHART[0])
        # The blob's key was `vendor_code` until 2026-09-06 and nothing asserted
        # it, so the rename could have moved it silently. It holds the normalised
        # merchant key, which is what layer 1 looks up.
        self.assertEqual(recorded["vendor_key"], "apcoa parking")
        self.assertNotIn("vendor_code", recorded)

    def test_no_audit_row_and_no_learning_when_the_tick_is_off(self):
        self.seed()
        self.write_note(note_payload())
        self.consume()

        repo = Repository()
        try:
            self.assertEqual(
                rows(repo, "SELECT * FROM resolution_events WHERE action = 'learn_vendor'"),
                [],
            )
        finally:
            repo.close()

    def test_the_row_count_before_and_after(self):
        # Verification step 6 of the brief: 0 then 1, against a temp database.
        self.seed()
        before = len(self.learned())
        self.write_note(note_payload(remember_gl_for_supplier=True))
        self.consume()
        after = len(self.learned())
        print(
            f"\ncategorisations_client_vendors in {config.DB_PATH}: "
            f"before={before} after={after}"
        )
        self.assertEqual((before, after), (0, 1))


if __name__ == "__main__":
    unittest.main()

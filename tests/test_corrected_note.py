r"""Step 10k: an edit to an already-filed receipt writes a `corrected` note.

**Added 2026-09-06 by amendment 235, on Paul's decision closing outstanding
items 36 and 167.** A receipt has been through the pipeline, validated,
categorised and filed, and its figures are in the books. Paul then finds one of
them is wrong. Until now there was no route for that correction to reach the
pipeline's own record, so the database went on holding what the extraction read.

## The rule that decides the shape

**A `corrected` note does not re-file anything.** The receipt is already filed,
`filed_path` is already set, and the client folder copy is already written.
18.2b: a copy is never withdrawn. So this is the first note action that changes
the pipeline's record **without moving a file**, which is what separates it from
`filed`, from the settle shape and from `attached`.

**`resolve_receipt()` refuses an already-filed receipt at step 1a**, and that
refusal is right for every other caller: nothing below it inspects `filed_path`,
so without it an `ok` receipt is re-filed and leaves a second copy on disk under
a `-2` name. `filing_already_settled` is what lets a correction past it, and the
name says the reason rather than the effect, which is amendment 309's rule for
`decided_by_operator`.

## The assertions come before the writer

**Step 10k says so in terms and it is not a formality.** Nothing had ever tested
what a matched `categorisations` row stores, because **every row in existence
reads `unmatched`**. During the `vendor_key` rename a mutation swapping two
fields at layer 1 left the whole suite green for exactly that reason.
`WhatACorrectedRowStoresTest` below is this step's share of closing that: it
drives a correction against a receipt whose supplier layer 1 already knows, and
asserts every column of the row that comes out.

**The identical swap at layer 2 is still live and is step 10m's**, not this
one's. Reported in `2026-09-11_REPORT_claude_code_corrected_note.md` with the
evidence rather than repaired here.
"""

import ast
import json
import subprocess
import sys
import types
import unittest
from pathlib import Path

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402

from chart_fixtures import TempChartBundle  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    rows,
)
from worker.database.repository import Repository  # noqa: E402
from worker.resolution.service import (  # noqa: E402
    CORRECTED_ACTION,
    NOTE_ACTIONS,
    NOTE_APPLIED_OUTCOMES,
    ResolutionNoteError,
    parse_resolution_note,
)

import app  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# The two accounts the client's chart holds in these tests, as
# `tests/test_desktop_learning.py` names them. Four digits, because any
# three-digit code is legacy per amendment 96.
IN_CHART = ("7304", "Parking and tolls")
ALSO_IN_CHART = ("7300", "Motor expenses")

# Where the receipt was already filed, which is the premise of this whole step.
FILED_RELATIVE = (
    r"Clients\Test Client\IntelliBooks\Receipts\2026-27"
    r"\2026-04-01_apcoa-parking_96.00.pdf"
)

SUPPLIER = "Apcoa Parking"
# What `normalise_vendor()` makes of it, which is what layer 1 looks up and what
# `matched_vendor` records.
VENDOR_KEY = "apcoa parking"


def corrected_note(**overrides):
    """A `corrected` note in the 12.2 shape.

    **The same shape a settle note carries**, so Desktop has one vocabulary:
    the receipt, the client, the action, who and when, the corrected `values`
    and the tick. **No `filed_path`**, because the receipt was filed earlier and
    the pipeline holds the path.
    """
    payload = {
        "schema": 1,
        "receipt_id": "r-1",
        "client_id": "CLIENT001",
        "action": CORRECTED_ACTION,
        "resolved_by": "desktop",
        "resolved_at": "2026-09-11T15:02:11.000Z",
        "values": {
            "supplier_name": SUPPLIER,
            "invoice_date": "2026-04-01",
            "net_amount": 70,
            "vat_amount": 14,
            "gross_amount": 84,
            "currency": "GBP",
            "category_code": IN_CHART[0],
            "category_name": IN_CHART[1],
        },
    }
    payload.update(overrides)
    return payload


def values_with(**overrides):
    values = dict(corrected_note()["values"])
    for key, value in overrides.items():
        if value is _ABSENT:
            values.pop(key, None)
        else:
            values[key] = value
    return values


class _Absent:
    """Marks a key to remove rather than to set. Absent is not empty."""


_ABSENT = _Absent()


def everything_under(root: Path):
    if not root.exists():
        return []
    return sorted((p.relative_to(root).as_posix(), p.stat().st_size)
                  for p in root.rglob("*") if p.is_file())


class CorrectedNoteTestCase(unittest.TestCase):
    """A receipt that is already `ok`, already filed, and already in the books."""

    def setUp(self):
        # **The environment first, then the chart.** `TempEnvironment` pins
        # `CHARTS_DIR` at a folder it deliberately does not create, so a chart
        # bundle entered outside it is overwritten by it and every code reads
        # as unconfirmed. The order is `tests/test_desktop_learning.py`'s.
        self.env = TempEnvironment().__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)
        self.chart = TempChartBundle(accounts=(IN_CHART, ALSO_IN_CHART)).__enter__()
        self.addCleanup(self.chart.__exit__, None, None, None)

    def seed_filed(self, receipt_id="r-1", status="ok",
                   relative=FILED_RELATIVE, with_extraction=True):
        """One receipt that has been through the pipeline and been filed.

        The copy in the client folder is written to disk as well as recorded,
        because the tests below list that folder whole before and after and an
        absent file would make "nothing moved" true for the wrong reason.
        """
        repo = Repository()
        try:
            if with_extraction:
                self.env.seed(
                    repo, receipt_id=receipt_id, status=status,
                    supplier_name=SUPPLIER, invoice_date="2026-04-01",
                    net_amount=80.0, vat_amount=16.0, gross_amount=96.0,
                    validation_status="ok", validation_notes=[])
            else:
                # An attached document, sub-step 10f.38: a row with no
                # extraction behind it, which is the one receipt shape a
                # correction has nothing to correct.
                file_path = self.env.path / f"{receipt_id}.pdf"
                file_path.write_text("dummy", encoding="utf-8")
                repo.save_receipt(
                    receipt_id=receipt_id, message_id=f"msg-{receipt_id}",
                    email_subject=None, email_from=None, email_received_at=None,
                    filename=f"{receipt_id}.pdf", file_path=file_path,
                    file_hash=f"hash-{receipt_id}", firm_id="INTELLITAX",
                    client_id="CLIENT001", source="desktop")
                repo.update_receipt_status(receipt_id, status)
            if relative:
                target = config.PRACTICE_ROOT / Path(relative.replace("\\", "/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"the copy the pipeline wrote at Post")
                repo.mark_receipt_filed(receipt_id, str(target))
        finally:
            repo.close()

    def learn(self, code=IN_CHART[0], name=IN_CHART[1], client_id="CLIENT001"):
        """A mapping layer 1 will match, so the row under test is not
        `unmatched`. Step 10k's own reason for existing as a test.
        """
        repo = Repository()
        try:
            repo.upsert_client_vendor(
                client_id=client_id, vendor_key=VENDOR_KEY,
                nominal_code=code, account_name=name,
                last_updated="2026-09-01T00:00:00+00:00", vendor_name=SUPPLIER)
            return rows(repo, "SELECT * FROM categorisations_client_vendors")[0]
        finally:
            repo.close()

    def write_note(self, payload=None, name=None):
        payload = corrected_note() if payload is None else payload
        config.RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        path = config.RESOLUTIONS_DIR / (
            name or f"{payload.get('receipt_id', 'x')}_1757600531000.json")
        path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        return path

    def poll(self):
        """One real `app.process_once()`, mailbox and extractor stubbed.

        The brief asks for a real poll rather than a call to the handler,
        because what has to be true of a correction is as much about what does
        not happen as about what does.
        """
        Routes(RecordingExtractor(extraction_result()))._run()

    def receipt(self, receipt_id="r-1"):
        repo = Repository()
        try:
            return repo.get_receipt(receipt_id)
        finally:
            repo.close()

    def table(self, sql, params=()):
        repo = Repository()
        try:
            return rows(repo, sql, params)
        finally:
            repo.close()

    def note_names(self, subfolder=None):
        base = (config.RESOLUTIONS_DIR if subfolder is None
                else config.RESOLUTIONS_DIR / subfolder)
        if not base.is_dir():
            return []
        return sorted(p.name for p in base.iterdir() if p.is_file())

    def categorisations(self, receipt_id="r-1"):
        return self.table(
            "SELECT * FROM categorisations WHERE receipt_id = ? "
            "ORDER BY categorised_at", (receipt_id,))

    def extractions(self, receipt_id="r-1"):
        return self.table(
            "SELECT * FROM extractions WHERE receipt_id = ? "
            "ORDER BY extracted_at", (receipt_id,))


# ---------------------------------------------------------------------------
# Section 4 of the brief: the assertions come before the writer
# ---------------------------------------------------------------------------


class WhatACorrectedRowStoresTest(CorrectedNoteTestCase):
    """Every column of the `categorisations` row a correction writes.

    **This is the test step 10k asks for first.** No test had ever asserted
    what a MATCHED row stores, because every `categorisations` row in existence
    reads `unmatched`, and a mutation swapping two fields at layer 1 survived
    the whole suite because of it. So the receipt here has a supplier layer 1
    already knows, and the row that comes out is read column by column.
    """

    def test_the_row_records_the_engine_suggestion_and_the_persons_choice(self):
        self.seed_filed()
        mapping = self.learn()
        self.assertEqual(self.categorisations(), [],
                         "the control: no categorisation row yet")

        self.write_note(corrected_note(
            values=values_with(category_code=ALSO_IN_CHART[0],
                               category_name=ALSO_IN_CHART[1])))
        self.poll()

        written = self.categorisations()
        self.assertEqual(len(written), 1, "one row per correction")
        row = written[0]

        # What the ENGINE found, which is the audit trail and must never be
        # overwritten by the person's choice. Layer 1, because the mapping
        # above is this client's own.
        self.assertEqual(row["match_source"], "client")
        self.assertEqual(row["confidence"], "high")
        self.assertEqual(row["suggested_code"], IN_CHART[0],
                         "suggested_code holds the mapping's nominal_code")
        self.assertEqual(row["suggested_name"], IN_CHART[1],
                         "suggested_name holds the mapping's account_name")
        self.assertEqual(row["needs_review"], 0)

        # **The two fields the layer 1 mutation swapped.** `mapping_id` is
        # the row id of the mapping that answered; `matched_vendor` is the
        # normalised key layer 1 looked up. Swapping them leaves both
        # populated and every other assertion true.
        self.assertEqual(row["mapping_id"], mapping["mapping_id"],
                         "mapping_id is the row id of the mapping that answered")
        self.assertEqual(row["matched_vendor"], VENDOR_KEY,
                         "matched_vendor is the normalised key, not a row id")
        self.assertNotEqual(row["mapping_id"], row["matched_vendor"])

        # What the PERSON chose, which sits beside the suggestion and never
        # over it. `CLAUDE.md`'s schema section: a correction sits beside
        # the suggestion.
        self.assertEqual(row["correction_code"], ALSO_IN_CHART[0])
        self.assertEqual(row["correction_name"], ALSO_IN_CHART[1])
        self.assertIsNotNone(row["corrected_at"])
        self.assertIn("resolution note", row["correction_reason"])

        # And the row belongs to the receipt and the client it was written
        # for, and to the extraction the correction produced.
        self.assertEqual(row["receipt_id"], "r-1")
        self.assertEqual(row["client_id"], "CLIENT001")
        self.assertEqual(row["extraction_id"], self.extractions()[-1]["extraction_id"])

    def test_the_corrected_figures_reach_a_new_extraction_row(self):
        """Append-only: the correction is a second row, not an edit of the
        first. `CLAUDE.md` rule 1, and it is what makes the original reading
        still readable afterwards.
        """
        self.seed_filed()
        self.learn()
        before = self.extractions()
        self.assertEqual(len(before), 1)

        self.write_note()
        self.poll()

        after = self.extractions()
        self.assertEqual(len(after), 2, "the correction appends a row")
        self.assertEqual(after[0]["gross_amount"], 96.0,
                         "the original reading is untouched")
        corrected = after[-1]
        self.assertEqual(corrected["engine"], "manual_correction")
        self.assertEqual(corrected["net_amount"], 70.0)
        self.assertEqual(corrected["vat_amount"], 14.0)
        self.assertEqual(corrected["gross_amount"], 84.0)
        self.assertEqual(corrected["supplier_name"], SUPPLIER)
        self.assertEqual(corrected["validation_status"], "ok")

    def test_one_audit_row_carries_the_idempotency_key(self):
        self.seed_filed()
        self.learn()

        self.write_note()
        self.poll()

        events = self.table(
            "SELECT * FROM resolution_events WHERE receipt_id = ?", ("r-1",))
        self.assertEqual(len(events), 1, "one row per correction")
        self.assertEqual(events[0]["actor"], "desktop")
        self.assertEqual(events[0]["source"], "desktop")
        self.assertEqual(events[0]["outcome"], CORRECTED_ACTION,
                         "the outcome says what became of the receipt, and "
                         "nothing was filed")
        payload = json.loads(events[0]["corrections_json"])
        self.assertEqual(payload["note_resolved_at"],
                         "2026-09-11T15:02:11.000Z")
        self.assertEqual(payload["gross_amount"], 84)


# ---------------------------------------------------------------------------
# The contract the Desktop half is written from
# ---------------------------------------------------------------------------


class TheNoteShapeTest(unittest.TestCase):
    """Deliverable 1's contract."""

    def test_corrected_is_a_fourth_action(self):
        self.assertEqual(CORRECTED_ACTION, "corrected")
        self.assertEqual(NOTE_ACTIONS,
                         ("filed", "discarded", "attached", "corrected"))

    def test_it_is_an_applied_outcome_so_the_note_reaches_processed(self):
        """`app.py` decides `processed\\` against this one definition rather
        than its own tuple. Two literals in two files that must agree is how
        every successfully applied Post-time message went to `failed\\` on the
        first run of sub-step 10f.37.
        """
        self.assertEqual(NOTE_APPLIED_OUTCOMES,
                         ("filed", "discarded", "attached", "corrected"))

    def test_it_parses_with_values_and_no_filed_path(self):
        note = parse_resolution_note(corrected_note())
        self.assertEqual(note.action, CORRECTED_ACTION)
        self.assertEqual(note.receipt_id, "r-1")
        self.assertIsNone(note.filed_path)
        self.assertEqual(note.values["gross_amount"], 84.0)
        self.assertEqual(note.category_code, IN_CHART[0])
        self.assertEqual(note.category_name, IN_CHART[1])

    def test_the_same_three_values_are_required_as_for_a_filed_note(self):
        """One vocabulary, so Desktop writes one validator. It also keeps
        amendment 309's enumeration true: `validate()` can return `failed` only
        on a missing gross or a missing supplier, and a note that could produce
        either is refused here, so **a correction can never turn a `failed`
        receipt green by removing a figure.**
        """
        for field in ("supplier_name", "gross_amount", "invoice_date"):
            with self.subTest(missing=field):
                with self.assertRaises(ResolutionNoteError) as caught:
                    parse_resolution_note(corrected_note(
                        values=values_with(**{field: _ABSENT})))
                self.assertIn(field, str(caught.exception))

    def test_the_tick_parses_and_defaults_to_off(self):
        self.assertFalse(
            parse_resolution_note(corrected_note()).remember_gl_for_supplier)
        self.assertTrue(parse_resolution_note(
            corrected_note(remember_gl_for_supplier=True)
        ).remember_gl_for_supplier)

    def test_a_filed_path_is_ignored_and_said_out_loud(self):
        """**Ignored rather than refused, and that is amendment 306's lesson.**
        A refusal puts the note in `failed\\` and leaves the database holding
        figures the books have already replaced, which is the single
        disagreement section 12 exists to prevent. The warning is what surfaces
        a Desktop that has misread the contract.
        """
        with self.assertLogs("worker.resolution.service", "WARNING") as caught:
            note = parse_resolution_note(corrected_note(
                filed_path=r"Clients\Test Client\somewhere.pdf"))
        self.assertIsNone(note.filed_path)
        self.assertTrue(any("filed_path" in line for line in caught.output))

    def test_delete_client_copy_is_refused_on_a_correction(self):
        """It means "the operator deleted this receipt and asked for its copy
        to go with it", and a correction is not that. The existing guard covers
        every action but `discarded`; this holds it for the fourth one.
        """
        with self.assertLogs("worker.resolution.service", "WARNING"):
            note = parse_resolution_note(
                corrected_note(delete_client_copy=True))
        self.assertFalse(note.delete_client_copy)

    def test_an_action_nobody_understands_still_fails(self):
        """The control. A fourth word must not open the gate to a fifth."""
        with self.assertRaises(ResolutionNoteError) as caught:
            parse_resolution_note(corrected_note(action="amended"))
        self.assertIn("corrected", str(caught.exception))


# ---------------------------------------------------------------------------
# Nothing moves
# ---------------------------------------------------------------------------


class NoFileMovesTest(CorrectedNoteTestCase):
    """Section 2's rule, asserted on the folders rather than on the calls."""

    def test_the_client_folder_and_the_document_store_are_untouched(self):
        self.seed_filed()
        self.learn()
        clients_before = everything_under(config.CLIENTS_ROOT)
        documents_before = everything_under(config.FILES_DIR)
        self.assertTrue(clients_before, "the control: the copy is there")

        self.write_note()
        self.poll()

        self.assertEqual(everything_under(config.CLIENTS_ROOT),
                         clients_before,
                         "a correction touched the client folder")
        self.assertEqual(everything_under(config.FILES_DIR),
                         documents_before,
                         "a correction touched the archive of record")

    def test_filed_path_and_filed_at_are_left_exactly_as_they_were(self):
        self.seed_filed()
        self.learn()
        before = self.receipt()

        self.write_note()
        self.poll()

        after = self.receipt()
        self.assertEqual(after["filed_path"], before["filed_path"])
        self.assertEqual(after["filed_at"], before["filed_at"])

    def test_a_correction_does_not_write_a_copy_the_retry_sweep_owes(self):
        """**The one combination the skip at step 11 actually decides**, and I
        named the wrong one first: see the report's section 7.

        On the `publish` trigger, a receipt whose copy failed when it published
        has a NULL `filed_path`, so neither the trigger gate nor the one-copy
        gate inside `copy_for_published_receipt()` refuses it. A correction
        would write that copy there and then, which makes a correction into a
        filing and takes the write away from
        `_copy_missing_client_copies()`, whose job it is.

        Everywhere else the skip is defence in depth: on `never` and on `post`
        a gate below refuses anyway, and on `publish` with a path already
        recorded the one-copy rule does. **So without this test the skip could
        be removed and nothing in the suite would notice**, which the first
        mutation run showed by surviving. Amendment 97's rule, arriving through
        a mutation rather than a reading.
        """
        saved = config.CLIENT_COPY_TRIGGER
        config.CLIENT_COPY_TRIGGER = config.CLIENT_COPY_ON_PUBLISH
        try:
            # Filed nowhere: published, awaiting Post. `relative=None` leaves
            # `filed_path` NULL, which is what makes this the case it is.
            self.seed_filed(relative=None)
            self.learn()
            self.assertEqual(everything_under(config.CLIENTS_ROOT), [],
                             "the control: no copy yet, which is the premise")

            self.write_note()
            self.poll()

            self.assertEqual(
                everything_under(config.CLIENTS_ROOT), [],
                "the correction wrote the client folder copy early. It is due "
                "at Post, from the `attached` note, and by then it takes these "
                "corrected figures")
            self.assertIsNone(self.receipt()["filed_path"])
            self.assertEqual(self.note_names("failed"), [],
                             "and the correction itself still applied")
        finally:
            config.CLIENT_COPY_TRIGGER = saved

    def test_nothing_is_published(self):
        """A correction is not a re-publish. The item IntelliBooks drains was
        written when the receipt published and Desktop already holds the row:
        that is `_settle_note()`'s reasoning and it holds here with more force,
        because the figures are already in the books.
        """
        self.seed_filed()
        self.learn()
        published_before = everything_under(config.INTELLIBOOKS_PUBLISH_DIR)

        self.write_note()
        self.poll()

        self.assertEqual(everything_under(config.INTELLIBOOKS_PUBLISH_DIR),
                         published_before)
        self.assertEqual(
            self.table("SELECT * FROM publish_events WHERE receipt_id = ?",
                       ("r-1",)), [])


# ---------------------------------------------------------------------------
# Applying it twice, and the tick
# ---------------------------------------------------------------------------


class IdempotencyTest(CorrectedNoteTestCase):
    """12.3 step 3, keyed on the note's own `resolved_at`."""

    def test_the_same_note_twice_changes_nothing_the_second_time(self):
        self.seed_filed()
        self.learn()
        self.write_note()
        self.poll()
        extractions = self.extractions()
        categorisations = self.categorisations()
        events = self.table(
            "SELECT * FROM resolution_events WHERE receipt_id = ?", ("r-1",))

        self.write_note(name="r-1_1757600531001.json")
        self.poll()

        self.assertEqual(self.extractions(), extractions,
                         "the replay appended a second extraction row")
        self.assertEqual(self.categorisations(), categorisations)
        self.assertEqual(
            self.table("SELECT * FROM resolution_events WHERE receipt_id = ?",
                       ("r-1",)), events)
        self.assertEqual(self.note_names("failed"), [],
                         "a replay is applied, not failed")
        self.assertEqual(len(self.note_names("processed")), 2)

    def test_a_genuinely_later_correction_is_applied(self):
        """The key is the note's `resolved_at`, not the receipt, so a second
        correction of the same receipt is a second correction.
        """
        self.seed_filed()
        self.learn()
        self.write_note()
        self.poll()

        self.write_note(corrected_note(
            resolved_at="2026-09-11T16:30:00.000Z",
            values=values_with(gross_amount=90, net_amount=75,
                               vat_amount=15)),
            name="r-1_1757605800000.json")
        self.poll()

        extractions = self.extractions()
        self.assertEqual(len(extractions), 3)
        self.assertEqual(extractions[-1]["gross_amount"], 90.0)
        self.assertEqual(len(self.categorisations()), 2)


class TheTickTest(CorrectedNoteTestCase):
    """11.3: learning is opt-in from an operator who ticked a box."""

    def learned(self):
        return self.table("SELECT * FROM categorisations_client_vendors")

    def test_the_tick_teaches(self):
        self.seed_filed()
        self.assertEqual(self.learned(), [], "nothing has been learned")

        self.write_note(corrected_note(remember_gl_for_supplier=True))
        self.poll()

        learned = self.learned()
        self.assertEqual(len(learned), 1)
        self.assertEqual(learned[0]["client_id"], "CLIENT001")
        self.assertEqual(learned[0]["vendor_key"], VENDOR_KEY,
                         "the normalised key, not a row id")
        self.assertEqual(learned[0]["nominal_code"], IN_CHART[0])
        self.assertEqual(learned[0]["account_name"], IN_CHART[1])

    def test_no_tick_teaches_nothing(self):
        self.seed_filed()

        self.write_note()
        self.poll()

        self.assertEqual(self.note_names("failed"), [],
                         "the correction still applied")
        self.assertEqual(self.learned(), [])

    def test_the_firm_pool_is_never_written_on_this_route(self):
        """The negative assertion, which is the one that protects it: nothing
        in the code says "do not call this". The firm half is step 10m and
        Paul deferred it as item 166.
        """
        self.seed_filed()
        self.write_note(corrected_note(remember_gl_for_supplier=True))
        self.poll()

        self.assertEqual(
            self.table("SELECT * FROM categorisations_firm_vendors"), [])

    def test_a_code_the_chart_does_not_confirm_teaches_nothing(self):
        """Carried across from `_apply_filed_note()` by hand: a mapping is read
        back by layer 1 as an exact match with confidence `high`, so writing
        one nothing has confirmed applies a code confidently to every future
        receipt from that vendor.
        """
        self.seed_filed()

        self.write_note(corrected_note(
            remember_gl_for_supplier=True,
            values=values_with(category_code="7391", category_name="")))
        self.poll()

        self.assertEqual(self.learned(), [])


# ---------------------------------------------------------------------------
# The two things the brief said to establish rather than assume
# ---------------------------------------------------------------------------


class ACorrectionOnAReceiptThatIsNotOkTest(CorrectedNoteTestCase):
    """Brief question 1. A `failed` or `possible_duplicate` receipt can be
    edited in Desktop like any other.
    """

    def test_a_failed_receipt_is_corrected_and_reaches_ok(self):
        """`decided_by_operator` is the right instrument, and amendment 309's
        reasoning applies with more force here than where it was built: there
        a person had filed the row into the books, here the row has been in the
        books since before the edit.
        """
        self.seed_filed(status="failed")
        self.learn()

        self.write_note()
        self.poll()

        self.assertEqual(self.receipt()["status"], "ok")
        self.assertEqual(self.note_names("failed"), [])

    def test_a_correction_whose_figures_do_not_add_up_still_applies(self):
        """The case amendment 309 was built for. A gross that is not net plus
        VAT would otherwise leave the note in `failed\\` while the books hold
        the corrected row, which is the disagreement section 12 prevents.
        """
        self.seed_filed()
        self.learn()

        self.write_note(corrected_note(
            values=values_with(net_amount=70, vat_amount=14,
                               gross_amount=100)))
        self.poll()

        self.assertEqual(self.receipt()["status"], "ok")
        self.assertEqual(self.note_names("failed"), [])
        despite = [n for n in
                   (self.extractions()[-1]["validation_notes"] or "").split(", ")
                   if "despite" in n]
        self.assertTrue(despite,
                        "the failed check was not recorded on the row")

    def test_a_receipt_with_no_extraction_is_refused_and_says_why(self):
        """An attached document, sub-step 10f.38. It was never offered to
        extraction, so there are no figures to correct: 18.1 says the
        transaction carries them. The note goes to `failed\\` with the reason,
        which is where something a person has to look at belongs.
        """
        self.seed_filed(status=config.BANK_ATTACHMENT_STATUS,
                        with_extraction=False)

        self.write_note()
        self.poll()

        self.assertEqual(self.extractions(), [])
        # The note and the `.error.txt` beside it, which is what a failure in
        # `Resolutions\failed\` looks like. Nothing is ever deleted.
        self.assertEqual(
            self.note_names("failed"),
            ["r-1_1757600531000.json", "r-1_1757600531000.json.error.txt"])
        self.assertEqual(self.receipt()["status"],
                         config.BANK_ATTACHMENT_STATUS,
                         "the row is left exactly as it was")


class ACorrectionForAReceiptThePipelineNeverIssuedTest(CorrectedNoteTestCase):
    """Brief question 2. Desktop tests the identifier before it sends, so it
    should not arise; this is what happens if it does.
    """

    def test_it_goes_to_failed_with_the_reason_and_writes_nothing(self):
        note = self.write_note(corrected_note(receipt_id="never-issued"))

        self.poll()

        self.assertIn(note.name, self.note_names("failed"))
        self.assertTrue(
            (config.RESOLUTIONS_DIR / "failed" /
             (note.name + ".error.txt")).exists())
        self.assertEqual(
            self.table("SELECT * FROM resolution_events"), [])


# ---------------------------------------------------------------------------
# Set claims, from the syntax tree
# ---------------------------------------------------------------------------


class TheSetClaimsTest(unittest.TestCase):
    """Anything asserted about a set, enumerated rather than sampled."""

    def tracked_python_files(self):
        listed = subprocess.run(
            ["git", "ls-files", "*.py"], cwd=REPO_ROOT,
            capture_output=True, text=True, check=True).stdout.split()
        return [REPO_ROOT / name for name in listed
                if not name.startswith("tests/")]

    def calls_passing(self, keyword):
        """Every production call site passing this keyword, off the tree.

        `.history\\` is excluded by construction, being gitignored and untracked.
        A grep would return the prose too, which on this project is guaranteed:
        superseded wording is kept beside every correction.
        """
        found = []
        for path in self.tracked_python_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if any(kw.arg == keyword for kw in node.keywords):
                    name = node.func.attr if isinstance(node.func, ast.Attribute) \
                        else getattr(node.func, "id", "?")
                    found.append(
                        f"{path.relative_to(REPO_ROOT).as_posix()}:{node.lineno} {name}()")
        return sorted(found)

    def test_filing_already_settled_is_passed_by_one_place(self):
        """The keyword that lets a correction past step 1a. **One caller**, and
        the guard is what keeps it one: a second would be a route to re-file a
        receipt that step 1a exists to refuse.
        """
        passing = self.calls_passing("filing_already_settled")
        self.assertEqual(
            len(passing), 1,
            f"filing_already_settled is passed at {len(passing)} call sites, "
            f"and must be passed at one:\n  " + "\n  ".join(passing))
        self.assertIn("worker/resolution/service.py", passing[0])

    def test_decided_by_operator_is_passed_by_two_places(self):
        """Amendment 309 enumerated one, `_settle_note()`. A correction is the
        second, for the same reason and with more force. Named here so the set
        claim in that amendment does not quietly go stale.
        """
        passing = self.calls_passing("decided_by_operator")
        self.assertEqual(
            len(passing), 2,
            "decided_by_operator is passed at:\n  " + "\n  ".join(passing))
        for site in passing:
            self.assertIn("worker/resolution/service.py", site)

    def test_the_correction_path_never_reaches_the_client_folder_writer(self):
        """Held on the source, because the folder tests above prove it for one
        receipt and this proves it for the function. 10f.11: `Clients\\` has one
        writer and `copy_for_published_receipt()` is the only way to reach it.
        """
        tree = ast.parse(
            (REPO_ROOT / "worker" / "resolution" / "service.py")
            .read_text(encoding="utf-8"))
        handler = [node for node in ast.walk(tree)
                   if isinstance(node, ast.FunctionDef)
                   and node.name == "_apply_corrected_note"]
        self.assertEqual(len(handler), 1,
                         "_apply_corrected_note() is not in the service")
        called = {node.func.attr if isinstance(node.func, ast.Attribute)
                  else getattr(node.func, "id", "")
                  for node in ast.walk(handler[0])
                  if isinstance(node, ast.Call)}
        for forbidden in ("copy_for_published_receipt", "write_client_copy",
                          "mark_receipt_filed", "publish_receipt",
                          "remove_client_copy"):
            with self.subTest(call=forbidden):
                self.assertNotIn(forbidden, called)


if __name__ == "__main__":
    unittest.main()

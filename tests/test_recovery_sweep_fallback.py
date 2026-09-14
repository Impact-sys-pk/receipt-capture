r"""Step 10aq: the recovery sweep routes a fallback to Review.

`_publish_unpublished_receipts()` re-reads the extraction row for a receipt
marked `ok` that was never published, and supplies a value of its own when that
row is missing one of four fields: `invoice_date`, `supplier`, `gross` and
`currency`. Until 2026-09-14 it did so silently and published the result as an
`ok` receipt. The invented `invoice_date` is today's date, and the invoice date
is what decides the tax year the client folder copy is filed under.

Paul's decision, amendment 405 closing outstanding item 112: any of the four
falling back sends the receipt to Review instead of publishing it as `ok`, and a
warning names the field either way.

**What "routes to Review" means here, measured rather than assumed, and it is
the one thing this file's design turns on.** Since sub-step 10f.15 the Review
queue in `IntelliBooks-Desktop-v3.html` reads the PUBLISHED INBOX rather than
`Intellibills\Review\`: `scanReview()` calls `inboxItems()`, and the string
`Intellibills\Review` appears nowhere in that file. What puts an item in the
queue is `itemIsHeld()`, which is true when the item's `validation` is anything
other than `"ok"`. So a receipt marked for review reaches the operator BY
publishing, carrying `validation_status: "needs_review"`, and a receipt that is
not published reaches the operator nowhere at all.

This is therefore the same mechanism the normal validation path already uses.
`process_extraction_result()` publishes every validation status and lets
`copy_for_published_receipt()` decide about the client folder, and that function
already refuses any status but `ok` and `bank_attachment`. Nothing new is built
here: the sweep stops asserting `"ok"` and passes the status it actually has.

The tests are three:

- the control, a complete extraction row, which must still publish as `ok` and
  still be copied, so the change is confined to the fallback case.
- one subtest per field, each asserting the warning, the item's validation, and
  the receipt's status.
- the client folder, which must stay empty on a fallback even with the firm's
  trigger set to `publish`, because that is the outcome an invented date would
  otherwise have written into a live client's folder under the wrong tax year.
"""

import logging
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
from resolution_fixtures import TempEnvironment  # noqa: E402
from worker.database.repository import Repository  # noqa: E402
import app  # noqa: E402

from test_stage4_client_copy import (  # noqa: E402
    captured,
    everything_under,
    item_for,
    items,
    publish_rows,
    receipts,
    trigger,
)

CLIENT = "CLIENT001"
RECEIPT = "r-sweep"

#: A complete extraction row: none of the four fields falls back.
COMPLETE = dict(
    supplier_name="Apcoa Parking",
    invoice_date="2026-04-01",
    net_amount=10.0,
    vat_amount=2.0,
    gross_amount=12.0,
    currency="GBP",
)

#: What each field is called in the warning, and what to null on the row to make
#: it fall back. The two names differ for two of the four, which is why this is a
#: table rather than one name used twice: the extraction COLUMN is
#: `supplier_name` and `gross_amount`, the sidecar KEY is `supplier` and `gross`,
#: and the warning names the sidecar key because that is what the invented value
#: becomes.
FIELDS = [
    ("invoice_date", "invoice_date"),
    ("supplier", "supplier_name"),
    ("gross", "gross_amount"),
    ("currency", "currency"),
]


def seed_unpublished_ok(env, client_id=None, **extraction):
    """An `ok` receipt in scope for the sweep, with no publish row of its own.

    The cutover in `get_unpublished_ok_receipts()` ignores anything created
    before the earliest `publish_events` row, so one belonging to another
    receipt has to exist or the sweep correctly does nothing.

    `client_id` overrides the fixture's own CLIENT001 after the row is written,
    for the unresolved-client tests below. It is set with an UPDATE rather than
    through `env.seed()` because that helper hardcodes the id, and the receipt
    has to exist before anything can point it at a client the registry does not
    hold.
    """
    repo = Repository()
    try:
        row = dict(COMPLETE)
        row.update(extraction)
        env.seed(repo, receipt_id=RECEIPT, status="ok",
                 validation_status="ok", validation_notes=[], **row)
        if client_id is not None:
            repo._conn.execute(
                "UPDATE receipts SET client_id = ? WHERE receipt_id = ?",
                (client_id, RECEIPT))
            repo._conn.commit()
        repo.save_publish_event(
            event_id="cutover", receipt_id="r-someone-else",
            destination="intellibooks", outcome="published",
            created_at="2000-01-01T00:00:00+00:00",
            item_path="somewhere.json")
        assert len(repo.get_unpublished_ok_receipts()) == 1
    finally:
        repo.close()


def run_the_sweep():
    """One sweep pass, returning the warnings it logged and the stats it wrote."""
    repo = Repository()
    stats = {}
    try:
        with captured("app", level=logging.WARNING) as log:
            app._publish_unpublished_receipts(repo, env_engine(repo), stats)
    finally:
        repo.close()
    return log.messages(logging.WARNING), stats


def env_engine(repo):
    from worker.categorisation.engine import CategorisationEngine
    return CategorisationEngine(repo=repo, enable_ai_fallback=False)


def receipt_row():
    return next(r for r in receipts() if r["receipt_id"] == RECEIPT)


class TheControlTest(unittest.TestCase):
    """A complete row is untouched by this change.

    Without this the fallback tests below would pass just as well against a
    sweep that sent EVERY receipt to Review, which would be a worse defect than
    the one being fixed.

    **This is not the only guard on that, and the docstring says so rather than
    implying otherwise.** Mutating the routing to fire unconditionally also
    turns `test_resume_safety.py`'s
    `test_recover_validated_receipt_without_filed_path` and
    `test_stage4_client_copy.py`'s
    `TheSweepPublishesRatherThanFilesTest.test_the_sweep_writes_nothing_into_the_client_folder`
    red, measured on 2026-09-14 by running the suite against that mutant. What
    this test adds over those two is the pair of properties step 10aq is
    actually about: that a complete row's published item still says `ok`, and
    that it produces no fallback warning.
    """

    def test_a_complete_extraction_row_still_publishes_as_ok_and_is_copied(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_ON_PUBLISH):
            seed_unpublished_ok(env)
            warnings, stats = run_the_sweep()

            self.assertEqual(stats.get("recovery_published"), 1)
            self.assertEqual(
                [r["outcome"] for r in publish_rows()
                 if r["receipt_id"] == RECEIPT],
                ["published"])
            self.assertEqual(item_for(RECEIPT)["validation_status"], "ok")
            self.assertEqual(receipt_row()["status"], "ok")

            self.assertEqual(
                [w for w in warnings if "fallback" in w], [],
                "a complete row must produce no fallback warning")

            # The client folder copy happens, which is the thing a fallback must
            # not do. Asserted here so the negative below means something.
            self.assertIsNotNone(receipt_row()["filed_path"])
            self.assertNotEqual(everything_under(config.CLIENTS_ROOT), [])


class AFallbackRoutesToReviewTest(unittest.TestCase):

    def test_each_missing_field_sends_the_receipt_to_review(self):
        for sidecar_key, column in FIELDS:
            with self.subTest(field=sidecar_key):
                with TempEnvironment() as env:
                    seed_unpublished_ok(env, **{column: None})
                    warnings, stats = run_the_sweep()

                    named = [w for w in warnings if sidecar_key in w]
                    self.assertTrue(
                        named,
                        f"no warning named {sidecar_key}; got {warnings}")

                    # It still publishes, which is what puts it in Desktop's
                    # Review queue: itemIsHeld() is true when validation is
                    # anything but "ok".
                    item = item_for(RECEIPT)
                    self.assertEqual(
                        item["validation_status"], "needs_review",
                        f"{sidecar_key} fell back and the item still says "
                        f"{item['validation_status']!r}, so Desktop would drain it "
                        f"into the books")
                    self.assertEqual(
                        [r["outcome"] for r in publish_rows()
                         if r["receipt_id"] == RECEIPT],
                        ["published"],
                        "a review item that does not publish reaches the "
                        "operator nowhere at all since 10f.15")

                    # And the database agrees with what Desktop was told.
                    self.assertEqual(receipt_row()["status"], "needs_review")

    def test_the_note_says_which_field_so_the_operator_can_see_why(self):
        with TempEnvironment() as env:
            seed_unpublished_ok(env, invoice_date=None, supplier_name=None)
            run_the_sweep()
            notes = item_for(RECEIPT)["validation_notes"]
            joined = " ".join(notes) if isinstance(notes, list) else str(notes)
            for expected in ("invoice_date", "supplier"):
                with self.subTest(field=expected):
                    self.assertIn(expected, joined)

    def test_every_field_that_fell_back_gets_its_own_warning(self):
        """All four at once, so the warning is per field and not per receipt."""
        with TempEnvironment() as env:
            seed_unpublished_ok(env, invoice_date=None, supplier_name=None,
                                gross_amount=None, currency=None)
            warnings, _stats = run_the_sweep()
            for sidecar_key, _column in FIELDS:
                with self.subTest(field=sidecar_key):
                    self.assertTrue(
                        [w for w in warnings if sidecar_key in w],
                        f"no warning named {sidecar_key}; got {warnings}")


class AFallbackWritesNoClientCopyTest(unittest.TestCase):
    """The outcome the step exists to prevent, asserted on the folder itself.

    18.2b says a copy into a live client folder is never withdrawn, and the
    invented `invoice_date` is what decides the tax year subfolder it lands in.
    The trigger is set to `publish` here deliberately: on `never` this would
    pass without the change.
    """

    def test_nothing_reaches_the_client_folder_when_a_field_fell_back(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_ON_PUBLISH):
            seed_unpublished_ok(env, invoice_date=None)
            run_the_sweep()

            self.assertEqual(
                everything_under(config.CLIENTS_ROOT), [],
                "a receipt with an invented invoice date was copied into a "
                "client folder, under a tax year nobody chose")
            self.assertIsNone(
                receipt_row()["filed_path"],
                "filed_path records a copy that must not have happened")


class AnUnresolvedClientIsNotPublishedTest(unittest.TestCase):
    r"""The sweep's OTHER guard, which nothing covered until 2026-09-14.

    Flag arising from flag 3 of
    `2026-09-14_REPORT_claude_code_three_flags.md`, built on Paul's decision the
    same day. `tests/test_resume_safety.py` carried a comment pointing at
    `test_an_unresolved_client_is_not_filed` as "the other half" of the
    registry-entry requirement; no such test existed anywhere, and striking that
    reference recorded the gap rather than closing it. This closes it.

    The guard is the one above the four fallbacks:

        client_folder_name = _client_folder_name(receipt["client_id"])
        if not client_folder_name:
            logger.warning(...)
            continue

    **It is a different thing from the fallback routing in this file's other
    tests, and the difference is the point.** A fallback publishes the receipt
    marked for review, because the document was read and only a value is
    missing. An unresolved client publishes NOTHING: 10d.18 says a receipt whose
    client cannot be named files nowhere, and `_client_folder_name()` returns
    None rather than guessing, which is the 2026-09-01 defect it exists to
    prevent. The receipt keeps its `ok` status and is offered again on the next
    poll, which is what makes leaving it the honest outcome rather than a loss.

    Three ways the guard fires, from `_client_folder_name()` read directly: the
    client is absent from the registry, its record has a blank
    `client_folder_name`, or the id is the reserved UNKNOWN. Each gets its own
    test rather than a subtest, because the branch is one line and the three
    ways into it fail independently: a regression that closes one of them should
    not be masked by the other two passing.
    """

    def _assert_nothing_happened(self, warnings):
        self.assertTrue(
            [w for w in warnings if RECEIPT in w and "client_folder_name" in w],
            f"no warning naming the receipt and the missing folder name; "
            f"got {warnings}")

        self.assertEqual(
            items(), [],
            "an unresolved client must publish nothing at all, and something "
            "was written into the inbox")
        self.assertEqual(
            [r for r in publish_rows() if r["receipt_id"] == RECEIPT], [],
            "a publish_events row was written for a receipt that never published")
        self.assertEqual(
            everything_under(config.CLIENTS_ROOT), [],
            "something reached Clients\\ for a client that cannot be named, "
            "which is the 2026-09-01 defect")

        row = receipt_row()
        self.assertIsNone(row["filed_path"])
        self.assertEqual(
            row["status"], "ok",
            "the receipt must be left alone: nothing about it was decided, so "
            "its status is not a place to record that")

        # And it is offered again, which is what makes leaving it honest.
        repo = Repository()
        try:
            again = [r["receipt_id"] for r in repo.get_unpublished_ok_receipts()]
        finally:
            repo.close()
        self.assertIn(
            RECEIPT, again,
            "the receipt was dropped from the sweep, so it would never be "
            "picked up once its client is registered")

    def test_a_client_the_registry_does_not_hold_publishes_nothing(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_ON_PUBLISH):
            seed_unpublished_ok(env, client_id="CLIENT999")
            self.assertNotIn("CLIENT999", config.CLIENTS_BY_ID)
            warnings, _stats = run_the_sweep()
            self._assert_nothing_happened(warnings)

    def test_a_record_with_a_blank_folder_name_publishes_nothing(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_ON_PUBLISH):
            seed_unpublished_ok(env)
            # The client IS in the registry. Only the folder name is missing,
            # which is the case a registry edit produces rather than a lookup
            # miss.
            config.CLIENTS_BY_ID = {
                CLIENT: dict(config.CLIENTS_BY_ID[CLIENT], client_folder_name="")
            }
            warnings, _stats = run_the_sweep()
            self._assert_nothing_happened(warnings)

    def test_the_reserved_unknown_id_publishes_nothing(self):
        with TempEnvironment() as env, trigger(config.CLIENT_COPY_ON_PUBLISH):
            seed_unpublished_ok(env, client_id=config.UNKNOWN_CLIENT_ID)
            warnings, _stats = run_the_sweep()
            self._assert_nothing_happened(warnings)


if __name__ == "__main__":
    unittest.main()

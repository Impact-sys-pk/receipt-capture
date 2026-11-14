"""Item 34, amendment 571: the file-hash duplicate block asks about status.

**Paul's decision of 2026-11-14.** A byte-identical file is refused where the
existing receipt's status is `ok` and it is not discarded. It is allowed in
every other case.

**What was wrong.** The block asked `is_recorded_and_filed()`, which reads
`filed_path`, and `filed_path` is written only when the client folder copy is
made. With `client_copy_trigger` on `post` that waits until IntelliBooks
Desktop says the receipt has been attached to a transaction, so from arrival
until the operator posts it no receipt had one and the block could refuse
nothing.

**Why it is narrow.** `needs_review`, `failed`, `retry_exhausted` and
`possible_duplicate` mean the operator is giving the document another go, and
amendment 303 records why a `needs_review` receipt must not count. A discarded
receipt stopped blocking a resend on Paul's decision of 2026-09-10. An `ok`
receipt worked the first time, so a second copy of the same bytes is a
duplicate and nothing more.

**The status test is inside the query, and it has to be.** On 2026-11-14 one
hash named three receipts for one client: `87c1ecec`, ok and then discarded;
`cf74484c`, ok; and the arrival `12495a90`. `find_by_hash()` is `LIMIT 1` with
no order and returned the discarded row, so asking about the status of the one
row it handed back would have let the arrival through under the new rule as
well. `find_by_transaction_loose()`'s docstring records the same lesson for the
semantic check: the marker belongs in the query as well as at the call site.

Read off the live database read-only on 2026-11-14 for the shape of the
incident; the values below are that receipt's, the ids are not.
"""

import json
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
import live_paths  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    DOCUMENT,
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    with_email_client,
)
from worker.database.repository import Repository  # noqa: E402

CLIENT = "CLIENT001"
OTHER = "CLIENT002"

#: Every receipt status there is, per `CLAUDE.md`'s list of the eight, split by
#: the answer. ~~`ok` is the only one that refuses~~ **`bank_attachment` joined
#: `ok` on 2026-11-14, Paul's decision**: it is finished work, filed against a
#: posted transaction, so there is nothing to retry. The other six are listed so
#: a test can walk them rather than pick two.
REFUSED_STATUSES = ("ok", config.BANK_ATTACHMENT_STATUS)
ALLOWED_STATUSES = (
    "pending",
    "needs_review",
    "failed",
    "retry_exhausted",
    "possible_duplicate",
    "discarded",
)

#: The 2026-11-14 receipt, as both readings gave it.
SHELL = dict(
    supplier_name="Shell Co-op Harborne",
    invoice_date="2026-07-08",
    gross_amount=51.11,
    receipt_time="06:23",
)


def seed(repo, receipt_id, status, file_hash, client_id=CLIENT,
         published=True, ref="16871102102"):
    """One receipt with one extraction, at `status`, never filed.

    **Never filed is the point.** Every receipt in the 2026-11-14 incident had
    `filed_path` NULL, because the client copy waits for Post, and that is
    exactly why the old block saw nothing.
    """
    repo.save_receipt(
        receipt_id=receipt_id,
        message_id=f"seed:{receipt_id}",
        email_subject=None,
        email_from=None,
        email_received_at="2026-11-14T12:34:00+00:00",
        filename="shell.jpg",
        file_path=f"/store/{receipt_id}.jpg",
        file_hash=file_hash,
        firm_id="TESTFIRM001",
        client_id=client_id,
        source="desktop",
    )
    repo.save_extraction(
        extraction_id=f"ext-{receipt_id}",
        receipt_id=receipt_id,
        engine="openai_vision",
        net_amount=None,
        vat_amount=None,
        currency="GBP",
        raw_response="{}",
        validation_status="ok",
        validation_notes=None,
        receipt_ref_number=ref,
        **SHELL,
    )
    repo.update_receipt_status(receipt_id, status)
    if published:
        repo.save_publish_event(
            event_id=f"pub-{receipt_id}",
            receipt_id=receipt_id,
            destination="intellibooks",
            outcome="published",
            created_at="2026-11-14T12:34:13+00:00",
            item_path=f"/published/{receipt_id}.json",
        )


def receipt_ids():
    repo = Repository()
    try:
        return {r["receipt_id"] for r in repo._conn.execute(
            "SELECT receipt_id FROM receipts").fetchall()}
    finally:
        repo.close()


def arrival():
    """What the second reading of the 2026-11-14 image returned."""
    return RecordingExtractor(extraction_result(
        net_amount=None, vat_amount=None, receipt_ref_number="000013", **SHELL))


class TheLookupAsksAboutStatusTest(unittest.TestCase):
    """`find_blocker_by_hash()` on its own, against every status."""

    def test_an_ok_receipt_that_was_never_filed_is_found(self):
        with TempEnvironment():
            repo = Repository()
            try:
                seed(repo, "r-ok", "ok", "h" * 64)
                self.assertIsNone(
                    repo._conn.execute(
                        "SELECT filed_path FROM receipts WHERE receipt_id='r-ok'"
                    ).fetchone()[0])
                self.assertEqual(repo.find_blocker_by_hash("h" * 64, CLIENT), ("r-ok", "ok"))
            finally:
                repo.close()

    def test_a_bank_attachment_is_found_too(self):
        """Paul's decision of 2026-11-14: finished work, like `ok`."""
        with TempEnvironment():
            repo = Repository()
            try:
                seed(repo, "r-att", config.BANK_ATTACHMENT_STATUS, "h" * 64)
                self.assertEqual(repo.find_blocker_by_hash("h" * 64, CLIENT), ("r-att", config.BANK_ATTACHMENT_STATUS))
            finally:
                repo.close()

    def test_the_refused_set_is_read_from_config(self):
        self.assertEqual(tuple(config.HASH_DUPLICATE_STATUSES), REFUSED_STATUSES)

    def test_every_other_status_is_not_found(self):
        self.assertEqual(len(ALLOWED_STATUSES) + len(REFUSED_STATUSES), 8,
                         "the eight receipt statuses moved; read CLAUDE.md")
        for status in ALLOWED_STATUSES:
            with self.subTest(status=status):
                with TempEnvironment():
                    repo = Repository()
                    try:
                        seed(repo, "r-1", status, "h" * 64)
                        self.assertIsNone(repo.find_blocker_by_hash("h" * 64, CLIENT))
                    finally:
                        repo.close()

    def test_a_discarded_row_ahead_of_the_ok_one_does_not_hide_it(self):
        """The 2026-11-14 shape. The discarded receipt was written first."""
        with TempEnvironment():
            repo = Repository()
            try:
                seed(repo, "r-first", "discarded", "h" * 64)
                seed(repo, "r-second", "ok", "h" * 64)
                # The trap is live: the old lookup hands back the discarded one.
                self.assertEqual(repo.find_by_hash("h" * 64, CLIENT), "r-first")
                self.assertEqual(repo.find_blocker_by_hash("h" * 64, CLIENT), ("r-second", "ok"))
            finally:
                repo.close()

    def test_another_clients_ok_receipt_is_not_found(self):
        """10f.18 holds: another client's identical bytes are not a duplicate."""
        with TempEnvironment():
            repo = Repository()
            try:
                seed(repo, "r-other", "ok", "h" * 64, client_id=OTHER)
                self.assertIsNone(repo.find_blocker_by_hash("h" * 64, CLIENT))
                self.assertEqual(repo.find_blocker_by_hash("h" * 64, OTHER), ("r-other", "ok"))
            finally:
                repo.close()

    def test_a_match_through_processed_attachments_is_found(self):
        """`find_by_hash()` has two sources and this keeps both."""
        with TempEnvironment():
            repo = Repository()
            try:
                seed(repo, "r-ok", "ok", "other" * 8)
                repo.mark_processed("msg-1", "att-1", "h" * 64, "r-ok", "TESTFIRM001")
                self.assertEqual(repo.find_blocker_by_hash("h" * 64, CLIENT), ("r-ok", "ok"))
            finally:
                repo.close()

    def test_the_client_is_required_rather_than_defaulted(self):
        import inspect
        parameter = inspect.signature(Repository.find_blocker_by_hash).parameters["client_id"]
        self.assertIs(parameter.default, inspect.Parameter.empty)


class TheIncidentIsRefusedOnEveryRouteTest(unittest.TestCase):
    """The receipt that got through on 2026-11-14, on all four arrival routes.

    **No new receipt row is the assertion, and that is what makes it this
    defence's alone.** Item 35's semantic check can only flag a second receipt
    `possible_duplicate`, which still writes the row; only the hash block can
    stop the row being written at all. The arrival reads `000013` against the
    seed's `16871102102`, which is the pair that vetoed the semantic check on
    the day.
    """

    ROUTES = (
        ("email attachment", lambda r: r.email_attachment()),
        ("embedded image", lambda r: r.embedded_image()),
        ("phone", lambda r: r.inbox_file("shell.jpg", "phone")),
        ("Add Receipts", lambda r: r.inbox_file("shell.jpg", "desktop")),
    )

    def test_an_ok_receipt_behind_a_discarded_one_refuses_the_arrival(self):
        import app

        for name, drive in self.ROUTES:
            with self.subTest(route=name):
                with TempEnvironment():
                    with_email_client(self)
                    file_hash = app.compute_hash(DOCUMENT)
                    repo = Repository()
                    try:
                        seed(repo, "r-87c1ecec", "discarded", file_hash)
                        seed(repo, "r-cf74484c", "ok", file_hash)
                    finally:
                        repo.close()
                    before = receipt_ids()
                    extractor = arrival()
                    drive(Routes(extractor))
                    self.assertEqual(receipt_ids(), before,
                                     f"the {name} route let the duplicate in")
                    self.assertEqual(extractor.calls, 0,
                                     "a refused file must cost no extraction")

    def test_a_bank_attachment_refuses_the_arrival_on_every_route(self):
        """Paul's decision of 2026-11-14. The resend of a document attached to
        a bank line would otherwise be extracted and published beside it, and
        nothing else could flag it: an attachment has no extraction row for the
        semantic check to join."""
        import app

        for name, drive in self.ROUTES:
            with self.subTest(route=name):
                with TempEnvironment():
                    with_email_client(self)
                    repo = Repository()
                    try:
                        seed(repo, "r-attached", config.BANK_ATTACHMENT_STATUS,
                             app.compute_hash(DOCUMENT))
                    finally:
                        repo.close()
                    before = receipt_ids()
                    extractor = arrival()
                    drive(Routes(extractor))
                    self.assertEqual(receipt_ids(), before,
                                     f"the {name} route let the resend in")
                    self.assertEqual(extractor.calls, 0)


class EveryRefusalLeavesARecordTest(unittest.TestCase):
    """Paul's decision of 2026-11-14, flag 2 of the duplicates report.

    Until item 34 the block could not fire before Post, so a refusal was rare.
    It fires on arrival now, and only the attachment route wrote an event: the
    embedded image wrote a `processed_attachments` row and a log line, and the
    capture inbox wrote nothing but a log line and a move. **A document that
    vanishes with no searchable record is the one Paul would be trying to
    explain.** Every route now writes the attachment route's
    `duplicate_skipped` event.
    """

    def _events(self):
        path = config.LOGS_DIR / f"receipt_events_{live_paths.TEST_FIRM_ID}.ndjson"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()]

    def test_each_route_writes_one_duplicate_skipped_event(self):
        import app

        expected_message_id = {
            "email attachment": "msg-att",
            "embedded image": "msg-emb",
            "phone": "phone:shell.jpg",
            "Add Receipts": "desktop:shell.jpg",
        }
        for name, drive in TheIncidentIsRefusedOnEveryRouteTest.ROUTES:
            with self.subTest(route=name):
                with TempEnvironment():
                    with_email_client(self)
                    repo = Repository()
                    try:
                        seed(repo, "r-earlier", "ok", app.compute_hash(DOCUMENT))
                    finally:
                        repo.close()
                    drive(Routes(arrival()))
                    skipped = [e for e in self._events()
                               if e["action"] == "duplicate_skipped"]
                    self.assertEqual(len(skipped), 1, f"{name}: {skipped}")
                    event = skipped[0]
                    self.assertEqual(event["duplicate_of"], "r-earlier")
                    self.assertEqual(event["duplicate_reason"], "file_hash_match")
                    self.assertEqual(event["message_id"], expected_message_id[name])
                    self.assertEqual(event["filename"], "shell.jpg" if name in (
                        "phone", "Add Receipts") else "shared.pdf")
                    self.assertNotEqual(event["receipt_id"], "r-earlier",
                                        "the event's own id, not the matched receipt's")

    def test_an_allowed_resend_writes_no_duplicate_event(self):
        import app

        for name, drive in TheIncidentIsRefusedOnEveryRouteTest.ROUTES:
            with self.subTest(route=name):
                with TempEnvironment():
                    with_email_client(self)
                    repo = Repository()
                    try:
                        seed(repo, "r-earlier", "needs_review", app.compute_hash(DOCUMENT))
                    finally:
                        repo.close()
                    drive(Routes(arrival()))
                    self.assertEqual(
                        [e for e in self._events() if e["action"] == "duplicate_skipped"], [])


class EveryOtherStatusIsAllowedTest(unittest.TestCase):
    """The other direction, on every status and every route."""

    def test_a_resend_of_a_receipt_that_is_not_ok_is_processed(self):
        import app

        for status in ALLOWED_STATUSES:
            for name, drive in TheIncidentIsRefusedOnEveryRouteTest.ROUTES:
                with self.subTest(status=status, route=name):
                    with TempEnvironment():
                        with_email_client(self)
                        repo = Repository()
                        try:
                            seed(repo, "r-earlier", status, app.compute_hash(DOCUMENT))
                        finally:
                            repo.close()
                        before = receipt_ids()
                        drive(Routes(arrival()))
                        self.assertEqual(len(receipt_ids() - before), 1,
                                         f"a resend of a {status} receipt was refused")


class TheCaptureLogSaysWhatWasTestedTest(unittest.TestCase):
    """The log line went with the change. It used to read "by hash of failed
    receipt" whatever the matched receipt's status, and the one it matched on
    2026-11-14 was ok and then discarded."""

    def _capture_log(self, statuses):
        import app

        with TempEnvironment():
            repo = Repository()
            try:
                for index, status in enumerate(statuses):
                    seed(repo, f"r-{index}", status, app.compute_hash(DOCUMENT))
            finally:
                repo.close()
            with self.assertLogs("app", level=logging.INFO) as captured:
                Routes(arrival()).inbox_file("shell.jpg", "desktop")
        return [line for line in captured.output if "capture" in line and "hash" in line]

    def test_a_refusal_names_the_status_it_found(self):
        """~~`test_a_refusal_names_the_ok_receipt`~~. Paul's decision of
        2026-11-14: the line prints the status the lookup read, rather than
        asserting one. It said `ok` for a `bank_attachment` match after
        `e4e1d47`, the fault amendment 571 had corrected that morning."""
        for status in REFUSED_STATUSES:
            with self.subTest(status=status):
                lines = self._capture_log(["discarded", status])
                self.assertEqual(len(lines), 1, lines)
                self.assertIn(f"by hash of {status} receipt r-1,", lines[0])
                self.assertNotIn("filed", lines[0])

    def test_an_allowance_names_no_status_it_did_not_test(self):
        lines = self._capture_log(["discarded"])
        self.assertEqual(len(lines), 1, lines)
        self.assertNotIn("failed receipt", lines[0])
        # ~~"no ok receipt"~~: it matched nothing in the refused set, so it
        # names no status and says what it did. Paul's decision, 2026-11-14.
        self.assertNotIn("ok receipt", lines[0])
        self.assertIn("matches r-0 but nothing that blocks a resend", lines[0])


# The set claim, that three call sites ask `find_blocker_by_hash()` and none asks
# `is_recorded_and_filed()`, is held by the two source guards that already
# held the old one: `test_all_three_hash_call_sites_read_the_same_way` in
# tests/test_step10f_duplicates.py and
# `test_the_guard_is_asked_at_the_one_call_site_and_it_is_the_new_one` in
# tests/test_stage4_client_copy.py. A third copy here was written first and
# removed, because two guards over one set drift.


class TheOldGuardIsGoneTest(unittest.TestCase):
    """`is_recorded_and_filed()` is deleted, 2026-11-14, Paul's decision.

    Item 34 took its three callers and nothing called it after. **Asserted as
    absent from the repository class rather than as uncalled**, the shape
    `tests/test_layer_two_row.py` uses for `increment_firm_vendor_count()` at
    amendment 344: uncalled is what it already was, and a function nobody calls
    is one edit away from looking as though it decides something. Its reasoning
    is in amendments 303 and 538 of `2026-07-25_CONSOLE_DESIGN.md`.
    """

    def test_it_has_not_come_back(self):
        import source_guards
        tree = source_guards.tree_of("worker", "database", "repository.py")
        self.assertFalse(
            source_guards.defines(tree, "is_recorded_and_filed"),
            "it was deleted on 2026-11-14 and is back. The file-hash block is "
            "find_blocker_by_hash(), which asks the status, not filed_path")


if __name__ == "__main__":
    unittest.main()

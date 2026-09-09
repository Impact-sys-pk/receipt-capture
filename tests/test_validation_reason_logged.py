"""The reason a receipt did not reach `ok` goes into `run.log`, not only the database.

**Paul's instruction, 2026-09-09: "I need a reason in the log."**

On 2026-09-09 an emailed receipt failed and all `run.log` held for it was the
OpenAI request and `Moved email uid=26 to INBOX.Failed Processing`. The reason,
`missing gross_amount`, existed only in `extractions.validation_notes`, so an
operator reading the log could see that a receipt failed and had to open SQLite
to see why. The ndjson event log was no better: it carried
`extraction_status: failed` and no reason, through a `review_reason` parameter
`_log_receipt()` already had and that call site did not pass.

**One line per receipt, at WARNING, carrying the notes verbatim.** The notes are
joined the way `save_extraction()` joins them, `", "`, so the string in the log
is the string in the database and one search finds both. That is the point of
logging them unaltered: two wordings for one condition is how a search for the
reason stops finding it.

**Every status but `ok`, and the set is read from the source rather than typed
out here.** `failed`, `needs_review` and `possible_duplicate` are equally
unexplainable from the log, and a fourth status added later has to fail this
guard rather than pass it silently, so `statuses_from_the_source()` enumerates
them from `validate()` and from the two overrides in the shared pipeline.

**And `ok` logs nothing.** A warning on the ordinary case is noise and stops the
line being read, so silence is asserted with a control: the same capture, the
same driver, a receipt that failed, one record.
"""

import ast
import json
import logging
import sys
import types
import unittest
from contextlib import contextmanager

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402
import source_guards  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    DOCUMENT,
    RecordingExtractor,
    Routes,
    TempEnvironment,
    extraction_result,
    with_email_client,
)
from worker import extraction_pipeline  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

#: The logger the line comes from. `worker/extraction_pipeline.py` had no logger
#: of any kind before this change, so a WARNING on this name is this line and
#: nothing else.
LOGGER_NAME = "worker.extraction_pipeline"

CLIENT = "CLIENT001"

#: The firm on `TempEnvironment`'s one client record, which is what names the
#: ndjson event log file.
FIRM = "INTELLITAX"

#: One extraction result per outcome, read out of `worker/validation/rules.py`
#: the way `tests/test_publish_trigger.py` reads them: a missing gross is
#: unrecoverable, and a gross that is not net + VAT is present but inconsistent.
OUTCOMES = {
    "ok": extraction_result(),
    "needs_review": extraction_result(gross_amount=99.0),
    "failed": extraction_result(gross_amount=None),
    # Two notes rather than one, and the reason it is here: every other outcome
    # above produces a single note, so the join is invisible and a mutation
    # changing `", "` to anything else was caught by one test driving the
    # function directly and by nothing driving the pipeline. A supplier that was
    # not read AND a gross that is not net + VAT is a real receipt with two
    # things wrong, and it is the only case where the log line and the database
    # string can disagree about how the notes are put together.
    "two_notes": extraction_result(supplier_name=None, gross_amount=99.0),
}


class Capture(logging.Handler):
    """Every record it is handed, kept rather than formatted."""

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    @property
    def messages(self):
        return [record.getMessage() for record in self.records]


@contextmanager
def captured(name=LOGGER_NAME, level=logging.WARNING):
    """Records at `level` or above from one logger, and nothing else.

    **Deliberately not `assertLogs`.** That fails when nothing was logged, and
    deliverable 3 is that an `ok` receipt logs nothing, so the test proving
    silence would have had to use different machinery from the test proving
    noise and neither would then be a control for the other.

    The logger's own level is set rather than assumed: it is NOTSET in
    production and inherits from root, so a suite where anything had raised root
    above WARNING would drop the record and read as a pass.
    """
    logger = logging.getLogger(name)
    handler = Capture()
    saved_level, saved_propagate = logger.level, logger.propagate
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(saved_level)
        logger.propagate = saved_propagate


def statuses_from_the_source():
    """Every status a receipt can reach through validation, read off the tree.

    Two places, because there are two: `validate()` assigns three to a local
    called `status`, and the shared pipeline overrides that status twice, for
    the semantic duplicate check and for the unresolved-client gate. Parsed
    rather than grepped, per `CLAUDE.md`: this project keeps superseded wording
    beside every correction, so a text search reads the prose about a status as
    though it were a status.

    Returns {status: [(file, line), ...]}, so a failure can say where.
    """
    found = {}
    rules = source_guards.tree_of("worker", "validation", "rules.py")
    validate = next(node for node in ast.walk(rules)
                    if isinstance(node, ast.FunctionDef) and node.name == "validate")
    for node in ast.walk(validate):
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "status":
                found.setdefault(node.value.value, []).append(
                    ("worker/validation/rules.py", node.lineno))
    pipeline = source_guards.tree_of("worker", "extraction_pipeline.py")
    for node in ast.walk(pipeline):
        if (isinstance(node, ast.keyword) and node.arg == "status"
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            found.setdefault(node.value.value, []).append(
                ("worker/extraction_pipeline.py", node.lineno))
    return found


def receipts():
    repo = Repository()
    try:
        return [dict(r) for r in repo._conn.execute("SELECT * FROM receipts")]
    finally:
        repo.close()


def notes_in_the_database(receipt_id):
    """`extractions.validation_notes` for this receipt: the string on the row."""
    repo = Repository()
    try:
        row = repo._conn.execute(
            "SELECT validation_notes FROM extractions WHERE receipt_id = ?",
            (receipt_id,)).fetchone()
        return None if row is None else row["validation_notes"]
    finally:
        repo.close()


def extraction_status_in_the_database(receipt_id):
    """`extractions.validation_status`, which is not always `receipts.status`."""
    repo = Repository()
    try:
        row = repo._conn.execute(
            "SELECT validation_status FROM extractions WHERE receipt_id = ?",
            (receipt_id,)).fetchone()
        return None if row is None else row["validation_status"]
    finally:
        repo.close()


def events(action="extracted"):
    """The ndjson event log entries for one action, in the order written."""
    path = config.LOGS_DIR / f"receipt_events_{FIRM}.ndjson"
    if not path.exists():
        return []
    entries = [json.loads(line) for line in
               path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [entry for entry in entries if entry.get("action") == action]


def drive(test_case, outcome, client_id=CLIENT):
    """One email arrival through a real `app.process_once()`, warnings captured.

    Only the mailbox and the extractor are replaced, per `Routes`, so what is
    asserted is the live path rather than a call sequence written to suit the
    test.
    """
    with_email_client(test_case, client_id)
    with captured() as log:
        Routes(RecordingExtractor(OUTCOMES[outcome])).email_attachment()
    return log


class TheReasonIsInTheLogTest(unittest.TestCase):
    """Deliverable 1, driven through a real `app.process_once()` per status."""

    def _assert_one_line_explaining(self, log, status):
        receipt, = receipts()
        self.assertEqual(receipt["status"], status,
                         "the fixture did not produce this status, so the test "
                         "proves nothing about it")
        record, = log.records
        self.assertEqual(record.levelno, logging.WARNING,
                         "a receipt that failed validation is an outcome the "
                         "pipeline is designed to produce, so WARNING and not "
                         "ERROR")
        message = record.getMessage()
        self.assertIn(receipt["receipt_id"], message)
        self.assertIn(receipt["client_id"], message)
        self.assertIn(status, message)
        notes = notes_in_the_database(receipt["receipt_id"])
        self.assertTrue(notes, "the extraction row carries no notes, so there "
                               "is nothing for the log line to have carried")
        self.assertIn(notes, message,
                      f"the log says {message!r} and the database says "
                      f"{notes!r}; one search has to find both")
        return receipt, notes

    def test_a_failed_receipt_says_why(self):
        with TempEnvironment():
            log = drive(self, "failed")
            _, notes = self._assert_one_line_explaining(log, "failed")
            self.assertEqual(notes, "missing gross_amount")

    def test_a_needs_review_receipt_says_why(self):
        with TempEnvironment():
            log = drive(self, "needs_review")
            _, notes = self._assert_one_line_explaining(log, "needs_review")
            self.assertIn("gross mismatch", notes)

    def test_a_receipt_with_two_things_wrong_is_one_line_matching_the_row(self):
        """Decision 1 and decision 5, on a receipt the pipeline actually filed.

        `test_several_notes_are_one_line_joined_as_the_database_joins_them`
        below drives the function directly and was the only test that noticed
        the join being changed, because every other outcome here produces one
        note. This one goes through `app.process_once()`, so the string the log
        carries and the string `save_extraction()` wrote are compared after both
        were built by the live code.

        The whole string is pinned rather than counting separators, which is
        what this test tried first and got wrong: **a note can contain the
        separator itself**, and the gross-mismatch note does, so `", "` appears
        twice in a string holding two notes. That is a property of
        `save_extraction()`'s join and it means the notes string cannot be split
        back into notes. Recorded here, out of scope, and not repaired.
        """
        with TempEnvironment():
            log = drive(self, "two_notes")
            _, notes = self._assert_one_line_explaining(log, "needs_review")
            self.assertEqual(
                notes,
                "missing supplier_name, "
                "gross mismatch: 10.0 + 2.0 = 12.0, got 99.0")
            entry, = events()
            self.assertEqual(entry["review_reason"], notes)

    def test_a_possible_duplicate_says_why(self):
        """The same purchase, a different scan.

        Same bytes twice never reaches the semantic check: the file hash matches
        first and no second receipt row is written at all, which is the trap
        `tests/test_publish_trigger.py` records having fallen into. Different
        bytes give a second receipt, and the same supplier, date and amount then
        make it a possible duplicate.
        """
        with TempEnvironment():
            with_email_client(self, CLIENT)
            extractor = RecordingExtractor(OUTCOMES["ok"])
            with captured() as log:
                Routes(extractor).email_attachment(message_id="one", data=DOCUMENT)
                Routes(extractor).email_attachment(
                    message_id="two", data=b"the same purchase, a different scan")

            statuses = sorted(r["status"] for r in receipts())
            self.assertEqual(statuses, ["ok", "possible_duplicate"],
                             "the fixture did not produce a possible duplicate, "
                             "so this test proves nothing")
            record, = log.records
            duplicate, = [r for r in receipts() if r["status"] == "possible_duplicate"]
            message = record.getMessage()
            self.assertIn("possible_duplicate", message)
            self.assertIn(duplicate["receipt_id"], message)
            self.assertIn(notes_in_the_database(duplicate["receipt_id"]), message)

    def test_the_reason_the_client_gate_added_reaches_the_log(self):
        """Proof the line is written from the final status, not from `validate()`.

        This extraction validates as `ok`. The gate of 10d.16 and 10d.18 then
        turns it into a review item with a reason of its own, because a client
        with no `client_folder_name` files nothing into the client folder. A
        line written from `validate()`'s answer would say `ok` and log nothing.

        **And this is the one receipt whose reason the database does not hold**,
        which is a pre-existing divergence flagged on 2026-09-09 and deliberately
        not repaired here. `save_extraction()` runs before the gate, so the
        extraction row says `ok` with no notes while the receipt row says
        `needs_review`. The reason reached the Review folder and nothing else.
        It now also reaches both logs, so for this class of receipt the log line
        is the only machine-readable record of why it went to Review.

        The two assertions on the row below record that, they do not endorse it.
        If they go red because the gate's reason now reaches the extraction row,
        that is the flag being fixed: read the log line assertions, which are
        the ones this test is for, and then update these two.
        """
        with TempEnvironment():
            config.CLIENTS_BY_ID = dict(config.CLIENTS_BY_ID)
            config.CLIENTS_BY_ID["CLIENT002"] = {
                "client_name": "No Folder Client",
                "client_id": "CLIENT002",
                "firm_id": FIRM,
                "trade": "UNSPECIFIED",
            }
            log = drive(self, "ok", client_id="CLIENT002")
            receipt, = receipts()
            self.assertEqual(receipt["status"], "needs_review")
            record, = log.records
            message = record.getMessage()
            self.assertEqual(record.levelno, logging.WARNING)
            self.assertIn(receipt["receipt_id"], message)
            self.assertIn("needs_review", message)
            self.assertIn("client CLIENT002 has no client_folder_name in the "
                          "registry", message)

            self.assertIsNone(notes_in_the_database(receipt["receipt_id"]))
            self.assertEqual(extraction_status_in_the_database(
                receipt["receipt_id"]), "ok")

    def test_the_folder_intake_route_says_why_too(self):
        """The line sits in the shared pipeline, so it serves every route.

        A per-route test is what shows that rather than assumes it.
        """
        with TempEnvironment():
            with captured() as log:
                Routes(RecordingExtractor(OUTCOMES["failed"])).inbox_file(
                    "receipt.pdf", "phone", client_id=CLIENT)
            self._assert_one_line_explaining(log, "failed")

    def test_the_embedded_image_route_says_why_too(self):
        with TempEnvironment():
            with_email_client(self, CLIENT)
            with captured() as log:
                Routes(RecordingExtractor(OUTCOMES["failed"])).embedded_image()
            self._assert_one_line_explaining(log, "failed")


class TheSameReasonReachesTheEventLogTest(unittest.TestCase):
    """Deliverable 2, through the `review_reason` parameter that already existed."""

    def test_the_event_log_carries_the_reason_a_failure_gives(self):
        with TempEnvironment():
            log = drive(self, "failed")
            receipt, = receipts()
            entry, = events()
            self.assertEqual(entry["receipt_id"], receipt["receipt_id"])
            self.assertEqual(entry["extraction_status"], "failed")
            self.assertEqual(entry["review_reason"],
                             notes_in_the_database(receipt["receipt_id"]))
            # One string, two logs. Written from one call, so they cannot drift.
            self.assertIn(entry["review_reason"], log.records[0].getMessage())

    def test_the_event_log_carries_the_reason_a_review_gives(self):
        with TempEnvironment():
            drive(self, "needs_review")
            entry, = events()
            self.assertEqual(entry["extraction_status"], "needs_review")
            self.assertIn("gross mismatch", entry["review_reason"])

    def test_an_ok_receipt_carries_no_reason_at_all(self):
        with TempEnvironment():
            drive(self, "ok")
            self.assertEqual(receipts()[0]["status"], "ok")
            entry, = events()
            self.assertEqual(entry["extraction_status"], "ok")
            self.assertNotIn("review_reason", entry)


class AnOkReceiptSaysNothingTest(unittest.TestCase):
    """Deliverable 3, with a control, so silence cannot be a broken capture."""

    def test_ok_logs_nothing_and_the_same_capture_catches_a_failure(self):
        with TempEnvironment():
            quiet = drive(self, "ok")
            self.assertEqual(receipts()[0]["status"], "ok",
                             "the fixture did not produce an ok receipt")
            self.assertEqual(quiet.messages, [],
                             "an ok receipt logged a warning; a warning on the "
                             "ordinary case is noise and stops the line being "
                             "read")
        with TempEnvironment():
            loud = drive(self, "failed")
            self.assertEqual(receipts()[0]["status"], "failed")
            self.assertEqual(
                len(loud.records), 1,
                "the control caught nothing, so the silence above was the "
                "capture being broken rather than the pipeline being quiet")


class EveryStatusIsAccountedForTest(unittest.TestCase):
    """A guard over the set, not over its members.

    Each test above drives one status. Only reading the statuses out of the
    source shows that the set is the one this module was written against, which
    is `CLAUDE.md`'s rule: a claim about a set is not verified by verifying its
    members, so enumerate the set first.
    """

    #: The four this module was written against, and the reason the assertion
    #: below is worth failing on: a fifth needs a person to decide whether it is
    #: an outcome to explain or another `ok`.
    KNOWN = {"ok", "failed", "needs_review", "possible_duplicate"}

    def test_the_set_of_statuses_is_the_one_this_module_covers(self):
        found = statuses_from_the_source()
        self.assertEqual(
            set(found), self.KNOWN,
            "the statuses validation can reach have changed. Found "
            f"{dict(sorted(found.items()))}. Decide whether the new one is an "
            "outcome that needs explaining in run.log, then update KNOWN here.")

    def test_every_status_but_ok_produces_exactly_one_warning(self):
        for status in sorted(statuses_from_the_source()):
            with self.subTest(status=status):
                with captured() as log:
                    returned = extraction_pipeline.report_validation_outcome(
                        "r-1", CLIENT, status, ["missing gross_amount"])
                if status == "ok":
                    self.assertEqual(log.records, [])
                    self.assertIsNone(returned)
                    continue
                record, = log.records
                self.assertEqual(record.levelno, logging.WARNING)
                message = record.getMessage()
                self.assertIn("r-1", message)
                self.assertIn(CLIENT, message)
                self.assertIn(status, message)
                self.assertIn("missing gross_amount", message)
                self.assertEqual(returned, "missing gross_amount")

    def test_several_notes_are_one_line_joined_as_the_database_joins_them(self):
        """Decision 5, and decision 1's mechanism.

        A receipt with three notes is one outcome, so one line; and the join is
        `save_extraction()`'s `", "`, so the string in the log is the string on
        the row.
        """
        with captured() as log:
            returned = extraction_pipeline.report_validation_outcome(
                "r-2", CLIENT, "needs_review",
                ["missing supplier_name", "invalid date: 15/08/2026",
                 "net_amount is negative: -1.0"])
        record, = log.records
        self.assertEqual(
            returned,
            "missing supplier_name, invalid date: 15/08/2026, "
            "net_amount is negative: -1.0")
        self.assertIn(returned, record.getMessage())

    def test_no_notes_still_says_something(self):
        """Nothing reaches this today and an empty line would be the worst answer.

        Every non-`ok` path has at least one note: `validate()` only leaves `ok`
        when the list is empty, and both overrides in the shared pipeline write
        one. Held anyway, because the cost of a receipt logging `failed:` with
        nothing after the colon is an operator reading the blank as the reason.
        """
        with captured() as log:
            returned = extraction_pipeline.report_validation_outcome(
                "r-3", CLIENT, "failed", [])
        record, = log.records
        self.assertTrue(returned)
        self.assertIn(returned, record.getMessage())
        self.assertEqual(
            extraction_pipeline.report_validation_outcome("r-3", CLIENT, "failed", None),
            returned)


class OneCallSiteTest(unittest.TestCase):
    """Where the line is written, read off the tree rather than eyeballed.

    The two deliverables share one string because they share one call. A second
    call site, or a `review_reason` built somewhere else, is how the log line
    and the event log come to say two different things about one receipt, which
    is the condition decision 1 exists to prevent.
    """

    def setUp(self):
        self.pipeline = source_guards.tree_of("worker", "extraction_pipeline.py")

    def _calls_to(self, tree, name):
        return [node for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and ast.unparse(node.func).split(".")[-1] == name]

    def test_the_reason_is_reported_from_exactly_one_place(self):
        calls = self._calls_to(self.pipeline, "report_validation_outcome")
        self.assertEqual(
            len(calls), 1,
            f"report_validation_outcome() is called at "
            f"{[c.lineno for c in calls]}; one receipt is one line")

    def test_the_event_log_call_passes_a_review_reason(self):
        call, = self._calls_to(self.pipeline, "_log_receipt")
        keywords = {keyword.arg for keyword in call.keywords}
        self.assertIn(
            "review_reason", keywords,
            "_log_receipt() has had a review_reason parameter all along and "
            "this call site did not pass it, which is the whole of "
            "deliverable 2")

    def test_the_line_is_written_after_the_status_is_final(self):
        """It is not inside either branch of the `ok` test.

        The status is overridden twice after `validate()` returns, so a line
        written inside the `if` would report a status that later changed.
        """
        call, = self._calls_to(self.pipeline, "report_validation_outcome")
        enclosing = [node for node in ast.walk(self.pipeline)
                     if isinstance(node, ast.If)
                     and node.lineno <= call.lineno <= (node.end_lineno or node.lineno)]
        self.assertEqual(
            [ast.unparse(node.test) for node in enclosing], [],
            "the call is inside an if statement; the status is final only "
            "after the filing branches have run")


if __name__ == "__main__":
    unittest.main()

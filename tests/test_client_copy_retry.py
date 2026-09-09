"""A client folder copy that failed after a successful publish is retried.

**Claude Code's own flag 6 of `2026-09-09_REPORT_claude_code_stage4_pipeline.md`,
briefed 2026-09-09 once stage 4 was complete and 18.2b's freeze closed by
amendment 298.**

`copy_for_published_receipt()` swallows its own failures, and that is right: by
the time it runs the item is already in the folder IntelliBooks drains and
`Intellibills\\Documents\\` holds the archive of record, so a folder in the
firm's own tree being unavailable must not fail a complete receipt. **On
OneDrive a locked or syncing folder is the ordinary case, not a hypothetical.**

**But nothing retried it.** The repointed sweep of sub-step 10f.13 asks "was this
published", and a receipt whose publish succeeded and whose copy failed **has** a
`published` row, so it was never offered again. The document never reached the
client folder and the only trace was an ERROR in `run.log`.

## The four conditions, and each has a test

`ok`, a `published` row, `filed_path` NULL, **and the firm's
`client_copy_trigger` is `publish`.** The fourth is a deliverable rather than a
detail: on `never` and on `post` no receipt ever gets a `filed_path`, so without
it the clause selects every `ok` receipt in the database on every poll for ever.
`TheTriggerGatesTheWholeSweepTest` holds that the query is **not executed at
all** on those two, rather than executed and discarded.

## And the cutover, which is where the damage would be

The publish half ignores anything created before the earliest `publish_events`
row, because amendment 283 is Paul's decision that the first run publishes only
what arrives from then on. **The same clause is here**, and
`TheCutoverHoldsHereTooTest` is seeded so that the cutover is the only thing that
can answer: the receipt satisfies every other condition and differs only in its
`created_at`.

**What the cutover does NOT protect against is in the report, and it is the
finding of this change:** nothing in the database records *why* a receipt was
not copied, so this clause cannot tell "the copy failed" from "the trigger said
`never` when it published". A firm moving from `never` to `publish` copies its
backlog on the next poll.
"""

import ast
import logging
import sys
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

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
from worker import client_copy  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

CLIENT = "CLIENT001"


class Capture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.INFO)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def messages(self, level=None):
        return [r.getMessage() for r in self.records
                if level is None or r.levelno == level]


@contextmanager
def captured(name, level=logging.INFO):
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


@contextmanager
def trigger(value):
    saved = config.CLIENT_COPY_TRIGGER
    config.CLIENT_COPY_TRIGGER = value
    try:
        yield
    finally:
        config.CLIENT_COPY_TRIGGER = saved


def documents_under_clients():
    if not config.CLIENTS_ROOT.exists():
        return []
    return sorted(p.relative_to(config.CLIENTS_ROOT).as_posix()
                  for p in config.CLIENTS_ROOT.rglob("*") if p.is_file())


def receipts():
    repo = Repository()
    try:
        return [dict(r) for r in repo._conn.execute(
            "SELECT * FROM receipts ORDER BY created_at")]
    finally:
        repo.close()


def publish_rows():
    repo = Repository()
    try:
        return [dict(r) for r in repo._conn.execute(
            "SELECT * FROM publish_events ORDER BY created_at")]
    finally:
        repo.close()


def seed_the_cutover(created_at="2000-01-01T00:00:00+00:00"):
    """A `published` row for another receipt, old enough to be the cutover.

    **Every end-to-end test here needs this and the reason is worth reading.**
    The clause ignores anything created before the earliest `publish_events`
    row, and **on a fresh database the only publish row is the arriving
    receipt's own, written a moment AFTER the receipt row**, so
    `created_at >= MIN(created_at)` is false for it and the clause offers
    nothing. Three tests here failed on that and three more passed on it, which
    is the same trap section 4 of
    `2026-09-09_REPORT_claude_code_stage4_pipeline.md` records for the publish
    half: a test that names one clause and is answered by another.

    So an earlier row exists, and **`arrive_with_a_broken_copy()` asserts the
    query actually offers the receipt** before any test relies on it.

    On a real installation this is not a fixture convenience: amendment 291
    records the live database's earliest `published` row at
    2026-09-09T10:43:37Z, so every receipt after that is in scope.
    """
    repo = Repository()
    try:
        repo.save_publish_event(
            event_id="cutover", receipt_id="r-somebody-else",
            destination="intellibooks", outcome="published",
            created_at=created_at, item_path="somewhere.json")
    finally:
        repo.close()


def arrive_with_a_broken_copy(test_case):
    """One email arrival whose client folder copy raises. Returns the receipt.

    **A real failure driven through a real `process_once()`**, rather than a row
    written to look like one. `write_client_copy()` is the one function that
    touches the file system, so making it raise is the closest thing to the
    OneDrive folder being locked, and everything above it runs unchanged.

    It asserts the state the retry has to start from, **including that the
    clause offers this receipt**. Without that last assertion every test built
    on this helper would pass or fail on the cutover rather than on the thing
    it names.
    """
    seed_the_cutover()
    with_email_client(test_case, CLIENT)
    with patch.object(client_copy, "write_client_copy",
                      side_effect=OSError("the folder is locked by OneDrive")):
        Routes(RecordingExtractor(extraction_result())).email_attachment()
    receipt, = [r for r in receipts() if r["receipt_id"] != "r-somebody-else"]
    assert receipt["status"] == "ok", receipt["status"]
    assert receipt["filed_path"] is None, "the copy did not fail, so nothing to retry"
    assert documents_under_clients() == [], "a document reached the client folder"

    repo = Repository()
    try:
        offered = [r["receipt_id"] for r in
                   repo.get_published_receipts_without_client_copy()]
    finally:
        repo.close()
    assert offered == [receipt["receipt_id"]], (
        f"the clause offers {offered}, not this receipt, so anything built on "
        f"this helper would be answered by the cutover rather than by the "
        f"condition it names")
    return receipt


def another_poll():
    """A second `process_once()` with nothing in the mailbox and nothing to read."""
    Routes(RecordingExtractor(None))._run()


class ACopyThatFailedIsRetriedOnTheNextPollTest(unittest.TestCase):
    """The deliverable, end to end, on the trigger Paul's firm is set to."""

    def test_the_document_reaches_the_client_folder_on_the_next_poll(self):
        with TempEnvironment(), trigger("publish"):
            receipt = arrive_with_a_broken_copy(self)

            another_poll()

            written = documents_under_clients()
            self.assertEqual(len(written), 1, f"the retry wrote {written}")
            self.assertTrue(written[0].endswith(".pdf"), written[0])
            self.assertEqual((config.CLIENTS_ROOT / written[0]).read_bytes(),
                             DOCUMENT)
            after, = [r for r in receipts() if r["receipt_id"] != "r-somebody-else"]
            self.assertEqual(after["filed_path"],
                             str(config.CLIENTS_ROOT / written[0]))
            self.assertTrue(after["filed_at"])
            self.assertEqual(after["receipt_id"], receipt["receipt_id"])

    def test_the_failure_was_an_error_in_the_log_and_the_receipt_was_untouched(self):
        """The state the retry starts from, asserted rather than assumed."""
        with TempEnvironment(), trigger("publish"):
            with_email_client(self, CLIENT)
            with captured("worker.client_copy", logging.ERROR) as log:
                with patch.object(client_copy, "write_client_copy",
                                  side_effect=OSError("the folder is locked")):
                    Routes(RecordingExtractor(extraction_result())).email_attachment()
            errors = log.messages(logging.ERROR)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("the folder is locked", errors[0])
            receipt, = receipts()
            self.assertEqual(receipt["status"], "ok")
            self.assertEqual([r["outcome"] for r in publish_rows()], ["published"])

    def test_the_retry_neither_republishes_nor_recategorises(self):
        """One publish row and one categorisation before and after.

        The retry is a copy and nothing else. Republishing would overwrite the
        item Desktop may already have drained, and a second `categorisations`
        row for one receipt would be a duplicate nobody asked for.
        """
        with TempEnvironment(), trigger("publish"):
            arrive_with_a_broken_copy(self)
            repo = Repository()
            try:
                before = repo._conn.execute(
                    "SELECT COUNT(*) FROM categorisations").fetchone()[0]
            finally:
                repo.close()
            publishes_before = publish_rows()

            another_poll()

            repo = Repository()
            try:
                after = repo._conn.execute(
                    "SELECT COUNT(*) FROM categorisations").fetchone()[0]
            finally:
                repo.close()
            self.assertEqual(after, before, "the retry categorised again")
            self.assertEqual(publish_rows(), publishes_before,
                             "the retry published again")

    def test_a_retry_that_fails_again_leaves_the_receipt_alone(self):
        """The swallow is kept, and this is what it buys.

        A folder that is still locked on the next poll must not take the poll
        down, and the receipt must be offered again after that.
        """
        with TempEnvironment(), trigger("publish"):
            receipt = arrive_with_a_broken_copy(self)

            with patch.object(client_copy, "write_client_copy",
                              side_effect=OSError("still locked")):
                another_poll()

            after, = [r for r in receipts() if r["receipt_id"] != "r-somebody-else"]
            self.assertIsNone(after["filed_path"])
            self.assertEqual(after["status"], "ok")
            self.assertEqual(documents_under_clients(), [])

            # And a third poll, with the folder available, still gets it.
            another_poll()
            self.assertEqual(len(documents_under_clients()), 1)
            later, = [r for r in receipts() if r["receipt_id"] != "r-somebody-else"]
            self.assertTrue(later["filed_path"])
            self.assertEqual(later["receipt_id"], receipt["receipt_id"])

    def test_an_already_copied_receipt_is_not_copied_a_second_time(self):
        """The ordinary case, and it is the control for every test above.

        A receipt whose copy worked has a `filed_path`, so the clause must not
        see it. Without this the tests above would pass against a sweep that
        copied everything every poll.

        The cutover is seeded here too, so that what stops the second copy is
        `filed_path IS NULL` and not the cutover answering first.
        """
        with TempEnvironment(), trigger("publish"):
            seed_the_cutover()
            with_email_client(self, CLIENT)
            Routes(RecordingExtractor(extraction_result())).email_attachment()
            first = documents_under_clients()
            self.assertEqual(len(first), 1, "the arrival did not copy at all")

            repo = Repository()
            try:
                self.assertEqual(
                    repo.get_published_receipts_without_client_copy(), [],
                    "a receipt with a filed_path was offered for copying")
            finally:
                repo.close()

            another_poll()
            self.assertEqual(documents_under_clients(), first)


class OnlyASUCCESSFULPublishIsCopiedTest(unittest.TestCase):
    """A receipt whose publish FAILED must not be copied. F16's whole meaning.

    **Added after a mutation, not before.** Dropping the `published` condition
    from the query was caught by nothing on its first run, because no test drove
    the one state it protects: `ok`, no client copy, and a publish that did not
    land. F16's trigger is "on a successful publish", so copying a document into
    a client folder for a receipt IntelliBooks never received would put a
    document in front of a client before the work reached the books.

    **That receipt is the publish sweep's**, not this clause's. It has no
    `published` row, so `get_unpublished_ok_receipts()` offers it and the copy
    follows the publish that then succeeds.
    """

    def test_a_receipt_whose_publish_failed_is_not_offered_for_copying(self):
        from worker import publish

        with TempEnvironment(), trigger("publish"):
            seed_the_cutover()
            with_email_client(self, CLIENT)
            with patch.object(publish, "write_item",
                              side_effect=OSError("the inbox has gone")):
                Routes(RecordingExtractor(extraction_result())).email_attachment()

            receipt, = [r for r in receipts() if r["receipt_id"] != "r-somebody-else"]
            self.assertEqual(receipt["status"], "ok")
            self.assertIsNone(receipt["filed_path"])
            self.assertIn(
                publish.FAILED,
                [r["outcome"] for r in publish_rows()
                 if r["receipt_id"] == receipt["receipt_id"]],
                "the publish did not fail, so this test proves nothing")
            self.assertEqual(documents_under_clients(), [])

            repo = Repository()
            try:
                offered = [r["receipt_id"] for r in
                           repo.get_published_receipts_without_client_copy()]
                # And the publish sweep is the one that owns it.
                waiting = [r["receipt_id"] for r in
                           repo.get_unpublished_ok_receipts()]
            finally:
                repo.close()
            self.assertNotIn(
                receipt["receipt_id"], offered,
                "a receipt whose publish failed was offered for copying; F16 "
                "copies on a SUCCESSFUL publish, so this would put a document "
                "in a client folder for a receipt IntelliBooks never received")
            self.assertIn(receipt["receipt_id"], waiting,
                          "and it is the publish sweep's to recover")


class TheTriggerGatesTheWholeSweepTest(unittest.TestCase):
    """The fourth condition, and it is a deliverable.

    On `never` and on `post` no receipt ever has a `filed_path`, so a clause
    that did not ask the trigger would select every `ok` receipt in the database
    on every poll. `copy_for_published_receipt()` would no-op on each of them,
    so nothing would be written; **what it would cost is a query answering with
    the whole table every five minutes and a sweep line that means nothing.**

    So the trigger is asked **above** the query, and these tests assert the
    query was never executed rather than that its answer was discarded.
    """

    def test_never_never_runs_the_query_and_writes_nothing(self):
        with TempEnvironment(), trigger("never"):
            seed_the_cutover()
            with_email_client(self, CLIENT)
            Routes(RecordingExtractor(extraction_result())).email_attachment()
            receipt, = [r for r in receipts() if r["receipt_id"] != "r-somebody-else"]
            self.assertIsNone(receipt["filed_path"])
            self.assertEqual([r["outcome"] for r in publish_rows()],
                             ["published", "published"],
                             "the receipt did not publish, so it is not a "
                             "candidate and this test proves nothing")

            calls = []
            real = Repository.get_published_receipts_without_client_copy
            with patch.object(
                    Repository, "get_published_receipts_without_client_copy",
                    lambda s: (calls.append(True), real(s))[1]):
                another_poll()

            self.assertEqual(calls, [], "the query ran on the `never` trigger")
            self.assertEqual(documents_under_clients(), [])
            after, = [r for r in receipts() if r["receipt_id"] != "r-somebody-else"]
            self.assertIsNone(after["filed_path"])

    def test_post_never_runs_the_query_and_writes_nothing(self):
        with TempEnvironment(), trigger("post"):
            client_copy._reset_post_warning()
            seed_the_cutover()
            with_email_client(self, CLIENT)
            Routes(RecordingExtractor(extraction_result())).email_attachment()
            after, = [r for r in receipts() if r["receipt_id"] != "r-somebody-else"]
            self.assertIsNone(after["filed_path"])

            calls = []
            real = Repository.get_published_receipts_without_client_copy
            with patch.object(
                    Repository, "get_published_receipts_without_client_copy",
                    lambda s: (calls.append(True), real(s))[1]):
                another_poll()

            self.assertEqual(calls, [], "the query ran on the `post` trigger")
            self.assertEqual(documents_under_clients(), [])

    def test_publish_does_run_the_query(self):
        """The control. Without it the two tests above pass against a sweep
        that never runs the query on any trigger at all."""
        with TempEnvironment(), trigger("publish"):
            arrive_with_a_broken_copy(self)
            calls = []
            real = Repository.get_published_receipts_without_client_copy
            with patch.object(
                    Repository, "get_published_receipts_without_client_copy",
                    lambda s: (calls.append(True), real(s))[1]):
                another_poll()
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(documents_under_clients()), 1)


class TheCutoverHoldsHereTooTest(unittest.TestCase):
    """Amendment 283 applied to the copy, and the seeding is the point.

    Section 4 of `2026-09-09_REPORT_claude_code_stage4_pipeline.md` records a
    test of the publish half that passed for the wrong reason: it named the
    `NOT EXISTS` clause and was answered by the cutover, and only a mutation
    showed it. **These two tests are built the other way round on purpose.**
    Both receipts satisfy `ok`, a `published` row and a NULL `filed_path`, and
    an earlier `publish_events` row exists for somebody else so that the
    cutover is not the receipt's own publish time. **They differ in one value,
    `receipts.created_at`**, so the cutover is the only thing that can decide
    between them.
    """

    #: A publish row for another receipt, old enough to be the cutover.
    CUTOVER = "2026-05-01T00:00:00+00:00"

    def _seed(self, env, created_at, receipt_id="r-candidate"):
        """An ok receipt that published, was never copied, and is on disk."""
        repo = Repository()
        try:
            repo.save_publish_event(
                event_id="earlier", receipt_id="r-somebody-else",
                destination="intellibooks", outcome="published",
                created_at=self.CUTOVER, item_path="somewhere.json")
            env.seed(repo, receipt_id=receipt_id, status="ok",
                     extraction_id=f"ext-{receipt_id}",
                     supplier_name="Apcoa Parking", invoice_date="2026-04-01",
                     net_amount=10.0, vat_amount=2.0, gross_amount=12.0,
                     validation_status="ok", validation_notes=[])
            repo.save_publish_event(
                event_id=f"pub-{receipt_id}", receipt_id=receipt_id,
                destination="intellibooks", outcome="published",
                created_at="2026-06-01T00:00:00+00:00",
                item_path=f"{receipt_id}.json")
            repo._conn.execute(
                "UPDATE receipts SET created_at = ?, filed_path = NULL "
                "WHERE receipt_id = ?", (created_at, receipt_id))
            repo._conn.commit()

            selected = [r["receipt_id"] for r in
                        repo.get_published_receipts_without_client_copy()]
        finally:
            repo.close()
        return selected

    def test_a_receipt_created_after_the_cutover_is_offered(self):
        with TempEnvironment() as env, trigger("publish"):
            selected = self._seed(env, created_at="2026-05-02T00:00:00+00:00")
            self.assertIn("r-candidate", selected)

    def test_a_receipt_created_before_the_cutover_is_left_alone(self):
        """The same receipt, one value different, and nothing else can decide it."""
        with TempEnvironment() as env, trigger("publish"):
            selected = self._seed(env, created_at="2026-04-30T23:59:59+00:00")
            self.assertNotIn(
                "r-candidate", selected,
                "a receipt that predates publishing on this installation was "
                "offered for copying. 18.2b says a copy is never withdrawn, so "
                "a backfill into live client folders could not be undone")

    def test_an_empty_publish_log_offers_nothing(self):
        with TempEnvironment() as env, trigger("publish"):
            repo = Repository()
            try:
                env.seed(repo, receipt_id="r-1", status="ok",
                         validation_status="ok", validation_notes=[],
                         gross_amount=12.0, supplier_name="Apcoa Parking")
                repo._conn.execute(
                    "UPDATE receipts SET filed_path = NULL WHERE receipt_id = 'r-1'")
                repo._conn.commit()
                self.assertEqual(publish_rows(), [])
                self.assertEqual(
                    repo.get_published_receipts_without_client_copy(), [])
            finally:
                repo.close()


class StillOneWriterTest(unittest.TestCase):
    """Section 3 of the brief: nothing new writes into the client folder.

    The clause reaches the same gated function every other route reaches, so
    the set of callers grows by one and the set of writers does not.
    """

    def _calls_to(self, name):
        found = []
        files = [REPO_ROOT / "app.py"]
        files += sorted((REPO_ROOT / "worker").rglob("*.py"))
        for path in files:
            if path.name == "client_copy.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call)
                        and ast.unparse(node.func).split(".")[-1] == name):
                    found.append(f"{path.relative_to(REPO_ROOT).as_posix()}"
                                 f"::{_owner(tree, node)}")
        return sorted(found)

    def test_nothing_but_client_copy_calls_the_writer(self):
        self.assertEqual(self._calls_to("write_client_copy"), [])

    def test_the_gated_entry_point_has_four_callers_and_this_is_the_fourth(self):
        self.assertEqual(
            self._calls_to("copy_for_published_receipt"),
            ["app.py::_copy_missing_client_copies",
             "app.py::_publish_unpublished_receipts",
             "worker/extraction_pipeline.py::process_extraction_result",
             "worker/resolution/service.py::resolve_receipt"])

    def test_the_retry_sweep_publishes_nothing_and_categorises_nothing(self):
        """Held on the tree as well as on the row counts above.

        A retry that publishes would overwrite an item Desktop may have
        drained; one that categorises would write a duplicate row. Neither
        belongs in a function whose job is one `shutil.copy2`.
        """
        tree = source_guards.tree_of("app.py")
        function = next(node for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "_copy_missing_client_copies")
        called = {ast.unparse(node.func).split(".")[-1]
                  for node in ast.walk(function) if isinstance(node, ast.Call)}
        for forbidden in ("publish_receipt", "categorise", "save_categorisation",
                          "make_enriched_sidecar", "write_client_copy"):
            self.assertNotIn(forbidden, called)
        self.assertIn("copy_for_published_receipt", called)

    def test_the_sweep_takes_no_stats_and_so_writes_nothing_to_the_run_summary(self):
        """Section 3 of the brief: nothing in the run summary.

        `stats` is what `_log_run()` spreads into `runs.ndjson`, which is the
        run summary per rule 1 of `CLAUDE.md`. **Taking no `stats` parameter
        makes that structural rather than a thing to remember**, and it is
        asserted on the signature rather than on the absence of a key, because
        a key that is never incremented is not the same as a function that
        cannot add one.
        """
        tree = source_guards.tree_of("app.py")
        function = next(node for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "_copy_missing_client_copies")
        parameters = [arg.arg for arg in function.args.args]
        self.assertEqual(parameters, ["repo"])

    def test_the_sweep_is_called_once_from_process_once(self):
        tree = source_guards.tree_of("app.py")
        sites = [_owner(tree, node) for node in ast.walk(tree)
                 if isinstance(node, ast.Call)
                 and ast.unparse(node.func).split(".")[-1]
                 == "_copy_missing_client_copies"]
        self.assertEqual(sites, ["process_once"])


def _owner(tree, node):
    best = None
    for owner in ast.walk(tree):
        if isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                owner.lineno <= node.lineno <= (owner.end_lineno or owner.lineno):
            if best is None or owner.lineno > best.lineno:
                best = owner
    return best.name if best else "<module scope>"


if __name__ == "__main__":
    unittest.main()

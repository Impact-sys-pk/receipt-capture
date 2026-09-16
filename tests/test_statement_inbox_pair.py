r"""Every exit from the statement branch moves the inbox pair out, exactly once.

Paul's decision of 2026-09-16, from the finding in
`2026-09-16_REPORT_claude_code_statement_end_to_end.md` and the consultant
session's check of it against `app.py`.

## What was wrong

The folder-intake loop at `app.py` has five `continue` statements. The receipt
path's `try/finally` moves the inbox pair on every outcome, and the statement
branch `continue`s long before that `try` is entered, so **three of the five
left the document and its sidecar sitting in the Receipt Inbox**:

- the client could not be resolved, so it went to Review
- `platform` or `week_ending` was missing, so it went to Review
- **the statement was filed successfully**

The fourth, a duplicate by hash, already called `_move_inbox_pair_to_processed()`
before going, and was correctly excluded.

**Two of the three never corrected themselves.** `file_review()` uses
`_unique_path()`, so every poll wrote a fresh copy into `Intellibills\Review\`:
`-2`, `-3`, and onwards, at 288 polls a day on the five-minute default.
`review_flags_issued` climbed with them. Measured over three polls before the
change, not reasoned about.

**The third self-corrected on the next poll**, by matching its own hash and
taking the branch that does move the pair, which cost one wasted poll and
inflated `duplicates_skipped` and `inbox_duplicates_removed` by one for every
statement the system ever filed.

## The mechanism, and why exactly once needs saying

**A `try/finally` around the branch, opened AFTER the duplicate-by-hash check.**
The receipt path's own comment records why that shape was chosen over repeating
the call: the failure branch copies the original into Review first, so the move
has to happen after it, and a `finally` is the only place that covers every
branch without repeating the call. **The second half of that reasoning is what
makes it right here**: a fourth statement branch added later is covered without
anybody remembering, which is the class of defect this change is fixing.

**The duplicate branch stays exactly as it was and is not inside the `try`.** It
`continue`s before the `try` is entered, so its explicit call is still the only
one that runs on that path. **That is what holds "exactly once"**, and it cannot
be shown by looking at the files: `_move_inbox_pair_to_processed()` returns early
when neither the document nor the sidecar still exists, so a second call leaves
the disk identical. `ExactlyOnceTest` counts the calls.

## Self-contained on purpose

`tests/test_statement_end_to_end.py` has a fuller statement fixture and this file
deliberately does not import it: that file is a separate piece of work awaiting
its own decision, and a test of this change should not stop working if that one
never lands.
"""

import json
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402

from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    TempEnvironment,
    extraction_result,
    rows,
    run_pipeline_once,
)
from worker.database.repository import Repository  # noqa: E402

#: A statement is a document, so its extension has to be in
#: `SUPPORTED_EXTENSIONS`. `is_supported()` skips anything else before the
#: statement branch is reached at all.
STATEMENT_BYTES = b"a weekly uber statement"

FILENAME = "stmt_uber_2026-04-05_ab12cd.pdf"


def sidecar(**overrides):
    """A statement sidecar of the shape the phone app writes."""
    payload = {
        "type": "statement",
        "client_id": "CLIENT001",
        "source": "phone",
        "platform": "uber",
        "week_ending": "2026-04-05",
    }
    payload.update(overrides)
    for key, value in list(payload.items()):
        if value is REMOVE:
            del payload[key]
    return payload


#: A sentinel for `sidecar(week_ending=REMOVE)`, so a test can say "this key is
#: absent" in the same call that says what the rest of it holds.
class _Remove:
    def __repr__(self):
        return "REMOVE"


REMOVE = _Remove()


def drop_pair(name=FILENAME, payload=None, data=STATEMENT_BYTES,
              folder="CLIENT001"):
    """Write a document and its sidecar into the client's inbox folder."""
    inbox = config.RECEIPT_INBOX_ROOT / folder
    inbox.mkdir(parents=True, exist_ok=True)
    document = inbox / name
    document.write_bytes(data)
    document.with_suffix(".json").write_text(
        json.dumps(payload if payload is not None else sidecar()),
        encoding="utf-8")
    return document


def files_under(root: Path):
    if not root.exists():
        return []
    return sorted(p.relative_to(root).as_posix()
                  for p in root.rglob("*") if p.is_file())


def inbox_files():
    return files_under(config.RECEIPT_INBOX_ROOT)


def review_files():
    return files_under(config.REVIEW_ROOT)


def poll():
    run_pipeline_once(RecordingExtractor(extraction_result()))


def poll_counting_moves():
    """One poll, returning the filenames `_move_inbox_pair_to_processed()` saw.

    The real function still runs, so the poll behaves exactly as it would
    without the spy. Counting is the only way to tell one call from two: the
    function returns early when neither file is left, so two calls leave the
    same disk as one.
    """
    import app

    real = app._move_inbox_pair_to_processed
    seen = []

    def spy(intake):
        seen.append(intake.filename)
        return real(intake)

    with mock.patch.object(app, "_move_inbox_pair_to_processed", spy):
        poll()
    return seen


def statements_rows():
    repo = Repository()
    try:
        return rows(repo, "SELECT * FROM statements")
    finally:
        repo.close()


def last_run_stats():
    """The stats of the most recent poll, off `runs.ndjson`."""
    lines = [line for line in
             config.RUNS_LOG.read_text(encoding="utf-8").splitlines()
             if line.strip()]
    return json.loads(lines[-1])


PROCESSED = f"CLIENT001/Processed/{FILENAME}"
PROCESSED_SIDECAR = PROCESSED.replace(".pdf", ".json")


class EveryStatementExitMovesThePairTest(unittest.TestCase):
    """One test per branch, and the brief names all three."""

    def assert_the_pair_moved(self):
        """Both files, and nothing left loose in the inbox folder.

        `sorted()` round the expected list rather than writing it in the order
        `files_under()` happens to return: a sidecar sorts before its document,
        which is true and is not what this test is about.
        """
        self.assertEqual(
            inbox_files(), sorted([PROCESSED, PROCESSED_SIDECAR]),
            "the document and its sidecar did not both move out of the inbox")

    def test_a_filed_statement_leaves_the_inbox(self):
        with TempEnvironment():
            drop_pair()
            poll()
            self.assertEqual(len(statements_rows()), 1, "it was not filed")
            self.assert_the_pair_moved()

    def test_a_statement_whose_client_cannot_be_resolved_leaves_the_inbox(self):
        with TempEnvironment():
            drop_pair(payload=sidecar(client_id="Client_999"))
            poll()
            self.assertEqual(statements_rows(), [], "it was filed anyway")
            self.assertTrue(review_files(), "it did not reach Review")
            self.assert_the_pair_moved()

    def test_a_statement_with_no_week_ending_leaves_the_inbox(self):
        with TempEnvironment():
            drop_pair(payload=sidecar(week_ending=REMOVE))
            poll()
            self.assertEqual(statements_rows(), [])
            self.assertTrue(review_files())
            self.assert_the_pair_moved()

    def test_a_statement_with_no_platform_leaves_the_inbox(self):
        """The other half of the same guard. `platform` and `week_ending` are
        checked in one condition, so either alone has to reach it."""
        with TempEnvironment():
            drop_pair(payload=sidecar(platform=REMOVE))
            poll()
            self.assertEqual(statements_rows(), [])
            self.assertTrue(review_files())
            self.assert_the_pair_moved()

    def test_the_duplicate_branch_still_leaves_the_inbox(self):
        """Unchanged by this work, and asserted so that a mechanism which
        covered the other three by breaking this one would be caught."""
        with TempEnvironment():
            drop_pair()
            poll()
            drop_pair()
            poll()
            self.assertEqual(len(statements_rows()), 1,
                             "the resend was filed a second time")
            self.assertEqual(
                inbox_files(),
                sorted([PROCESSED, PROCESSED_SIDECAR,
                        f"CLIENT001/Processed/{Path(FILENAME).stem}-2.json",
                        f"CLIENT001/Processed/{Path(FILENAME).stem}-2.pdf"]),
                "the resent pair did not join the first in Processed")


class ExactlyOnceTest(unittest.TestCase):
    r"""The pair is moved once per item, never twice.

    **This cannot be seen on disk.** `_move_inbox_pair_to_processed()` returns
    early when neither the document nor the sidecar still exists, so a second
    call writes nothing and the folder looks identical. The calls are counted.
    """

    def test_the_duplicate_branch_moves_the_pair_once(self):
        """The branch that already moved it explicitly must not now also be
        covered by the `finally`, which is what a `try` around the whole
        statement branch would have done."""
        with TempEnvironment():
            drop_pair()
            poll()
            drop_pair()
            self.assertEqual(poll_counting_moves(), [FILENAME])

    def test_a_filed_statement_moves_the_pair_once(self):
        with TempEnvironment():
            drop_pair()
            self.assertEqual(poll_counting_moves(), [FILENAME])

    def test_a_review_branch_moves_the_pair_once(self):
        with TempEnvironment():
            drop_pair(payload=sidecar(client_id="Client_999"))
            self.assertEqual(poll_counting_moves(), [FILENAME])

    def test_a_missing_metadata_branch_moves_the_pair_once(self):
        with TempEnvironment():
            drop_pair(payload=sidecar(week_ending=REMOVE))
            self.assertEqual(poll_counting_moves(), [FILENAME])

    def test_the_processed_folder_holds_one_pair_and_not_two(self):
        """The observable half. It cannot catch a double call on its own, and
        it can catch a mechanism that moves the file and then copies it."""
        with TempEnvironment():
            drop_pair()
            poll()
            self.assertEqual(inbox_files(),
                             sorted([PROCESSED, PROCESSED_SIDECAR]))


class TheReviewCopiesStopAccumulatingTest(unittest.TestCase):
    r"""The behaviour this change exists for, over more than one poll.

    Before the change these two wrote a fresh copy into `Intellibills\Review\`
    on every poll, for ever, because the pair stayed in the inbox and
    `file_review()` uses `_unique_path()`. A single-poll test cannot see it,
    which is why nothing did.
    """

    POLLS = 3

    def test_an_unresolvable_statement_is_reviewed_once_and_not_once_a_poll(self):
        with TempEnvironment():
            drop_pair(payload=sidecar(client_id="Client_999"))
            for _ in range(self.POLLS):
                poll()

            copies = [name for name in review_files()
                      if name.endswith(".pdf")]
            self.assertEqual(
                len(copies), 1,
                f"{self.POLLS} polls wrote {len(copies)} copies into Review: "
                f"{review_files()}")

    def test_a_statement_missing_metadata_is_reviewed_once(self):
        with TempEnvironment():
            drop_pair(payload=sidecar(week_ending=REMOVE))
            for _ in range(self.POLLS):
                poll()

            copies = [name for name in review_files()
                      if name.endswith(".pdf")]
            self.assertEqual(len(copies), 1, review_files())

    def test_the_flag_is_counted_once_rather_than_once_a_poll(self):
        """`review_flags_issued` climbed with the copies. The stat is the thing
        an operator would have seen first, so it is asserted too."""
        with TempEnvironment():
            drop_pair(payload=sidecar(client_id="Client_999"))
            poll()
            self.assertEqual(last_run_stats()["review_flags_issued"], 1)
            poll()
            self.assertEqual(
                last_run_stats()["review_flags_issued"], 0,
                "the second poll flagged the same statement again")

    def test_a_filed_statement_is_not_counted_as_its_own_duplicate(self):
        """The success path cost one wasted poll and one false duplicate. Both
        stats are per-run, so the second poll should now see nothing at all."""
        with TempEnvironment():
            drop_pair()
            poll()
            poll()
            stats = last_run_stats()
            self.assertEqual(stats["duplicates_skipped"], 0)
            self.assertEqual(stats.get("inbox_duplicates_removed", 0), 0)


if __name__ == "__main__":
    unittest.main()

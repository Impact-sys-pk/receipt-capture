"""Sub-step 10f.21: an inbox duplicate is moved to `Processed\\`, never deleted.

**Rewritten 2026-09-07 against the new behaviour rather than made to pass.**
Both tests in this file used to call `app._remove_inbox_pair(intake)` directly
and assert the image and its sidecar were gone from disk. That function was the
subject and it no longer exists, so the file is the same class as
`tests/test_logging_setup.py` in section 18.2a: a test whose whole subject is
the behaviour being changed.

**What changed.** Step 9c moved the `ok` path from a delete to a move, on
`CLAUDE.md`'s no-data-loss rule, and left the two duplicate paths deleting. So
the rule held everywhere except where a duplicate arrived, which is the one case
Paul is about to produce in quantity: an identical resend through the phone or
**Add Receipts** removed the file from disk with one log line and no receipt
row. Amendment 137 and outstanding item 144.

**What these tests now assert**, and it is more than the old pair did. They drive
a real `app.process_once()` rather than calling the mover, so they cover the two
callers as well as the move itself:

1. The original and its sidecar are **gone from the inbox folder**.
2. Both are **present in `Processed\\`**, under the same stem.
3. The duplicate is still recognised, so nothing is filed twice and no second
   receipt or statement row appears.

The old direct call could not have caught a caller that deleted instead of
moving, because it never ran a caller.
"""

import json
import sys
import types
import unittest

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import app  # noqa: E402
import config  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    TempEnvironment,
    extraction_result,
    rows,
    run_pipeline_once,
)
from worker.database.repository import Repository  # noqa: E402

CLIENT = "CLIENT001"
CONTENT = b"the same bytes, sent twice by one client"


def drop(env, name, sidecar):
    """Put one file and its sidecar in this client's inbox folder."""
    inbox = env.inbox_dir(CLIENT)
    original = inbox / name
    original.write_bytes(CONTENT)
    sidecar_path = original.with_suffix(".json")
    sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
    return original, sidecar_path


class InboxDuplicateIsMovedNotDeletedTest(unittest.TestCase):
    def assert_moved_to_processed(self, original, sidecar_path):
        processed = original.parent / app.INBOX_PROCESSED_DIRNAME
        self.assertFalse(original.exists(),
                         "the original is still in the inbox, so it will be "
                         "reprocessed on the next poll")
        self.assertFalse(sidecar_path.exists())
        self.assertTrue((processed / original.name).exists(),
                        f"{original.name} was deleted rather than moved into "
                        f"{app.INBOX_PROCESSED_DIRNAME}\\")
        self.assertTrue((processed / sidecar_path.name).exists(),
                        "the sidecar was deleted rather than moved, so the pair "
                        "is broken")
        self.assertEqual((processed / original.name).read_bytes(), CONTENT,
                         "the bytes that arrived are the bytes that were kept")

    def test_a_duplicate_receipt_is_kept_in_processed(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                repo.save_receipt(
                    receipt_id="r-already-filed",
                    message_id="phone:earlier.pdf",
                    email_subject=None,
                    email_from=None,
                    email_received_at="2026-04-01T00:00:00+00:00",
                    filename="earlier.pdf",
                    file_path=env.path / "Documents" / "earlier.pdf",
                    file_hash=app.compute_hash(CONTENT),
                    firm_id="FIRM001",
                    client_id=CLIENT,
                    source="phone",
                )
                repo.mark_receipt_filed(
                    "r-already-filed", str(env.path / "filed" / "earlier.pdf"))
            finally:
                repo.close()

            original, sidecar_path = drop(
                env, "duplicate.pdf", {"type": "capture", "client_id": CLIENT})

            extractor = RecordingExtractor(extraction_result())
            run_pipeline_once(extractor)

            self.assert_moved_to_processed(original, sidecar_path)
            self.assertEqual(extractor.calls, 0,
                             "a duplicate must not reach the extractor, which "
                             "is a real OpenAI call")

            repo = Repository()
            try:
                self.assertEqual(
                    [r["receipt_id"] for r in rows(repo, "SELECT * FROM receipts")],
                    ["r-already-filed"],
                    "a second receipt row was written for a duplicate")
            finally:
                repo.close()

    def test_a_duplicate_statement_is_kept_in_processed(self):
        with TempEnvironment() as env:
            repo = Repository()
            try:
                repo.save_statement(
                    statement_id="s-already-filed",
                    client_id=CLIENT,
                    platform="uber",
                    week_ending="2026-04-05",
                    source="desktop",
                    file_hash=app.compute_hash(CONTENT),
                    file_path=env.path / "Documents" / "earlier.pdf",
                    filed_path=env.path / "filed" / "earlier.pdf",
                )
            finally:
                repo.close()

            original, sidecar_path = drop(env, "stmt_dup.pdf", {
                "type": "statement",
                "client_id": CLIENT,
                "platform": "uber",
                "week_ending": "2026-04-05",
            })

            run_pipeline_once(RecordingExtractor(extraction_result()))

            self.assert_moved_to_processed(original, sidecar_path)

            repo = Repository()
            try:
                self.assertEqual(
                    [r["statement_id"] for r in rows(repo, "SELECT * FROM statements")],
                    ["s-already-filed"],
                    "a second statement row was written for a duplicate")
            finally:
                repo.close()


class TheDeletingFunctionIsGoneTest(unittest.TestCase):
    """10f.21 again, as a guard rather than as behaviour.

    `_remove_inbox_pair()` is deleted once no caller remains. Held here in the
    shape `tests/test_path_layout.py` uses for `DATA_DIR`: the risk is that
    somebody writes it again, because a delete is the obvious thing to reach for
    when clearing an inbox.
    """

    def test_app_has_no_function_that_unlinks_an_inbox_pair(self):
        self.assertFalse(
            hasattr(app, "_remove_inbox_pair"),
            "_remove_inbox_pair() is back. Nothing in the inbox is deleted; "
            "_move_inbox_pair_to_processed() is the one disposal and it moves.")

    def test_the_mover_is_still_there(self):
        # Without this the assertion above is satisfied by deleting both, which
        # would leave every inbox file where it was and reprocess it every poll.
        self.assertTrue(hasattr(app, "_move_inbox_pair_to_processed"))

    def test_nothing_in_app_unlinks_anything_that_arrived_from_outside(self):
        """The shape rather than the one function.

        `_remove_inbox_pair()` could come back under another name, so every
        `.unlink()` in `app.py` is enumerated and matched against a named list
        of the three that are legitimate. **The three are named individually
        rather than passed by a pattern**, so adding a fourth is a decision
        somebody has to record here rather than something a rule quietly covers,
        which is how the `IMAP_PORT` exception is held in
        `tests/test_required_smtp.py`.

        **What separates them from what this sub-step forbids is provenance**:
        the pipeline made all three itself. Two are the pipeline lock, which is
        process state, and one is backup rotation, which deletes the pipeline's
        own database copies beyond fourteen days. Nothing a client sent is
        deleted, which is `CLAUDE.md`'s no-data-loss rule.

        The first draft of this test asserted no `.unlink()` at all and went red
        on all three. Recorded because the over-broad version would have been
        satisfied only by deleting the lock handling.
        """
        import ast
        from pathlib import Path

        #: (receiver, what it deletes and why that is not received data)
        ALLOWED = {
            "lock_path": "the pipeline lock, which is this process's own state",
            "old": "a database backup older than fourteen days, made by "
                   "_create_daily_backup()",
        }

        tree = ast.parse(
            (Path(__file__).resolve().parent.parent / "app.py").read_text(
                encoding="utf-8"))
        unlinks = [
            (ast.unparse(node.func.value), node.lineno)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "unlink"
        ]
        self.assertTrue(unlinks, "no unlink found at all; this test has stopped "
                                 "looking at anything")

        offenders = sorted(f"{receiver}.unlink() at app.py:{line}"
                           for receiver, line in unlinks
                           if receiver not in ALLOWED)
        self.assertEqual(
            offenders, [],
            "app.py deletes something that arrived from outside. Nothing the "
            "pipeline receives is deleted, per CLAUDE.md's no-data-loss rule "
            f"and sub-step 10f.21: {offenders}")

        self.assertEqual(
            sorted({receiver for receiver, _ in unlinks}), sorted(ALLOWED),
            "one of the three permitted unlinks has gone. They are the two "
            "pipeline-lock removals and backup rotation, and losing one is a "
            "change rather than a tidy-up.")


if __name__ == "__main__":
    unittest.main()

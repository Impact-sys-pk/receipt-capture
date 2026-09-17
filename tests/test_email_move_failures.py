r"""A failed email move is retried, and every run says how many failed.

Paul's decisions of 2026-09-16, from the flag in
`2026-09-16_REPORT_claude_code_inbox_pair_moves.md` and from what checking it
turned up.

## Deliverable one: the stranded email

`move_email_to_folder()` **returns False and logs a warning rather than
raising**, at `worker/email/reader.py`. An email with no attachments got its
alert, `record_alert_sent()` wrote the row, and then the move to
`INBOX.No Attachments` was attempted. **If that move failed the email stayed in
INBOX**, and on every run afterwards the already-alerted check passed over it
before the move was reached. Never re-alerted, which is right. Never re-moved,
which is not, so it sat in INBOX with one log line per poll and nobody knew.

**The move is now attempted before the email is passed over.**

**The retry cannot misfire**, and that is the property worth holding rather than
asserting in prose: `move_email_to_folder()` copies, flags `\Deleted` and
expunges, so a second move of a uid that has already gone has nothing to copy
and returns False. **Only an email still in INBOX can be retried**, which is
exactly the failed case. `Mailbox` below models that, and a stub that merely
recorded every call as a success would hide this defect and report the fix as
broken. `CLAUDE.md`, 2026-09-08, and `Routes._move()` in
`tests/resolution_fixtures.py` carries the same lesson from the same rule.

## Deliverable two: the callers listen

`move_email_to_folder()` is honest and its five callers were not: every one
discarded the bool as a bare expression statement. Enumerated from the syntax
tree over the 57 production files, not grepped, because tombstone comments in
this repository name deleted functions and prose sits beside every correction.

**One mechanism at all five sites and not five.** `app._move_email()` wraps the
call and counts a failure into `stats`, which `_log_run()` writes into
`runs.ndjson`. `TheCallSitesTest` asserts on the source that no unwrapped call
remains and that the number of wrapped ones is what it should be, because a
per-site test proves a site and only a guard over the set catches the sixth
site.

**What a failed move now causes:** the email stays in INBOX, the run's
`email_moves_failed` count goes up by one in `runs.ndjson`, and the next run
tries the move again.
"""

import ast
import json
import pathlib
import sys
import types
import unittest
from unittest import mock

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import config  # noqa: E402

import source_guards  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    RecordingExtractor,
    TempEnvironment,
    extraction_result,
)

REPO_ROOT = pathlib.Path(source_guards.REPO_ROOT)

SENDER = "driver@example.com"
NO_ATTACHMENT_FOLDER = "INBOX.No Attachments"

#: How many times the helper is used. One per call site, and the sites are
#: enumerated in the class that asserts this.
EXPECTED_CALL_SITES = 5


class Mailbox:
    r"""A mailbox that behaves like the real one, including when a move fails.

    Three properties, each read off `worker/email/reader.py`:

    - **An email is fetched only while it is still in INBOX.**
      `fetch_emails_without_attachments()` searches the live mailbox, so an
      email that moved is simply not offered again.
    - **A move copies, flags `\Deleted` and expunges.** Once a uid has gone, a
      second move of it has nothing to copy and returns False.
    - **A failed move leaves the email exactly where it was**, because the
      function returns before flagging anything when the copy does not respond
      OK.

    `fail_moves` is how many move attempts fail before one succeeds, which is
    the only thing here that is a test's choice rather than the mailbox's
    behaviour.
    """

    def __init__(self, fail_moves=0, uid="7", message_id="msg-no-attachment"):
        self.uid = uid
        self.message_id = message_id
        self.fail_moves = fail_moves
        self.in_inbox = True
        #: Every attempt, as (uid, folder), whether or not it worked.
        self.attempts = []
        #: Every attempt that returned True.
        self.successes = []
        self.landed = None
        self.alerts = []

    def emails_without_attachments(self, *args, **kwargs):
        if not self.in_inbox:
            return []
        return [{"id": self.message_id, "uid": self.uid, "from": SENDER,
                 "msg": None}]

    def move(self, uid, folder):
        self.attempts.append((uid, folder))
        if not self.in_inbox:
            # Already gone. The copy finds nothing, which is what stops the
            # retry from being able to move an email twice.
            return False
        if self.fail_moves > 0:
            self.fail_moves -= 1
            return False
        self.in_inbox = False
        self.landed = folder
        self.successes.append((uid, folder))
        return True

    def send_no_attachment_alert(self, recipient, firm_name=None):
        self.alerts.append((recipient, firm_name))
        return True

    def poll(self):
        """One real `app.process_once()`, with only the mailbox replaced."""
        import app

        stubs = {
            "fetch_emails_without_attachments": self.emails_without_attachments,
            "extract_embedded_images": lambda *a, **k: [],
            "fetch_new_messages": lambda *a, **k: [],
            "fetch_attachments": lambda *a, **k: [],
            "scan_inbox": lambda *a, **k: [],
            "move_email_to_folder": self.move,
            "send_no_attachment_alert": self.send_no_attachment_alert,
            "get_extractor": lambda *a, **k: RecordingExtractor(
                extraction_result()),
        }
        patches = [mock.patch.object(app, name, value)
                   for name, value in stubs.items()]
        for p in patches:
            p.start()
        try:
            app.process_once()
        finally:
            for p in reversed(patches):
                p.stop()


def run_stats():
    """Every run's stats, oldest first, off `runs.ndjson`."""
    return [json.loads(line) for line
            in config.RUNS_LOG.read_text(encoding="utf-8").splitlines()
            if line.strip()]


class TheStrandedEmailIsRetriedTest(unittest.TestCase):
    """Deliverable one, over two consecutive polls.

    A single poll cannot see any of this, which is why nothing did.
    """

    def test_a_failed_move_is_attempted_again_on_the_next_run(self):
        with TempEnvironment():
            box = Mailbox(fail_moves=1)
            box.poll()
            self.assertEqual(len(box.attempts), 1, "the first poll never tried")
            self.assertTrue(box.in_inbox, "the failed move took it anyway")

            box.poll()
            self.assertEqual(
                len(box.attempts), 2,
                "the second poll passed over the email without trying the move "
                "again, so it is stranded in INBOX for good")
            self.assertEqual(box.landed, NO_ATTACHMENT_FOLDER)
            self.assertFalse(box.in_inbox)

    def test_the_alert_is_sent_once_however_many_runs_it_takes(self):
        """The already-alerted check is untouched: where it is tested moved,
        not whether."""
        with TempEnvironment():
            box = Mailbox(fail_moves=2)
            for _ in range(3):
                box.poll()
            self.assertEqual(len(box.alerts), 1,
                             f"the client was alerted {len(box.alerts)} times")

    def test_it_keeps_trying_until_it_works(self):
        with TempEnvironment():
            box = Mailbox(fail_moves=2)
            for _ in range(3):
                box.poll()
            self.assertEqual(len(box.attempts), 3)
            self.assertEqual(box.landed, NO_ATTACHMENT_FOLDER)

    def test_a_move_that_worked_is_not_tried_again(self):
        """The email is out of INBOX, so it is never offered to the run again.

        Without this the retry could be satisfied by a loop that moves every
        email on every poll for ever.
        """
        with TempEnvironment():
            box = Mailbox(fail_moves=0)
            box.poll()
            box.poll()
            self.assertEqual(len(box.attempts), 1)

    def test_the_retry_can_never_move_one_email_twice(self):
        """Why it cannot misfire, as an assertion rather than a paragraph.

        `move_email_to_folder()` copies, flags `\\Deleted` and expunges, so a
        second move of a uid that has gone returns False. Over three polls with
        two failures, exactly one attempt succeeds and the email is in one
        folder.
        """
        with TempEnvironment():
            box = Mailbox(fail_moves=2)
            for _ in range(3):
                box.poll()
            self.assertEqual(len(box.successes), 1,
                             f"the email moved {len(box.successes)} times")
            self.assertEqual(box.landed, NO_ATTACHMENT_FOLDER)


class TheRunCountsFailedMovesTest(unittest.TestCase):
    """Deliverable two: the number leaves the run, in `runs.ndjson`."""

    def test_a_failed_move_is_counted(self):
        with TempEnvironment():
            box = Mailbox(fail_moves=1)
            box.poll()
            self.assertEqual(run_stats()[-1]["email_moves_failed"], 1)

    def test_a_clean_run_reports_nought_rather_than_omitting_the_key(self):
        """The same reason every other counter is stated in the initial dict:
        a run summary with a fixed shape lets a reader tell nought from a field
        this version of the code does not write."""
        with TempEnvironment():
            Mailbox(fail_moves=0).poll()
            stats = run_stats()[-1]
            self.assertIn("email_moves_failed", stats)
            self.assertEqual(stats["email_moves_failed"], 0)

    def test_the_count_is_this_run_and_not_a_running_total(self):
        with TempEnvironment():
            box = Mailbox(fail_moves=1)
            box.poll()
            box.poll()
            first, second = run_stats()[-2:]
            self.assertEqual(first["email_moves_failed"], 1)
            self.assertEqual(second["email_moves_failed"], 0,
                             "the second run's move succeeded, so its own "
                             "count is nought")

    def test_two_failures_in_one_run_count_twice(self):
        """The counter counts moves, not runs."""
        with TempEnvironment():
            box = Mailbox(fail_moves=1)
            second = Mailbox(fail_moves=1, uid="8", message_id="msg-two")

            def both(*args, **kwargs):
                return (box.emails_without_attachments()
                        + second.emails_without_attachments())

            def move(uid, folder):
                return (box.move(uid, folder) if uid == box.uid
                        else second.move(uid, folder))

            import app

            patches = [
                mock.patch.object(app, "fetch_emails_without_attachments", both),
                mock.patch.object(app, "extract_embedded_images",
                                  lambda *a, **k: []),
                mock.patch.object(app, "fetch_new_messages", lambda *a, **k: []),
                mock.patch.object(app, "fetch_attachments", lambda *a, **k: []),
                mock.patch.object(app, "scan_inbox", lambda *a, **k: []),
                mock.patch.object(app, "move_email_to_folder", move),
                mock.patch.object(app, "send_no_attachment_alert",
                                  box.send_no_attachment_alert),
                mock.patch.object(app, "get_extractor",
                                  lambda *a, **k: RecordingExtractor(
                                      extraction_result())),
            ]
            for p in patches:
                p.start()
            try:
                app.process_once()
            finally:
                for p in reversed(patches):
                    p.stop()

            self.assertEqual(run_stats()[-1]["email_moves_failed"], 2)


class TheCallSitesTest(unittest.TestCase):
    r"""One mechanism at every site, asserted on the source.

    **A per-site test proves a site works; only a guard over the set proves the
    set is complete**, and it is what catches the sixth call site added without
    it. `CLAUDE.md`, 2026-09-08, which records `extract_with_transient_retry()`
    being used by three of four intake paths for weeks with every per-path test
    passing.

    **From the syntax tree, not the text.** A grep returns the name from
    comments and docstrings, and `app.py` carries tombstone comments naming
    functions that no longer exist.
    """

    HELPER = "_move_email"
    RAW = "move_email_to_folder"

    def production_files(self):
        files = sorted(REPO_ROOT.glob("*.py"))
        files += sorted((REPO_ROOT / "worker").rglob("*.py"))
        return [p for p in files if "__pycache__" not in p.parts]

    def calls_to(self, name):
        """(file, line, is_bare, enclosing function) for every call to `name`."""
        found = []
        for path in self.production_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            parents = {}
            for node in ast.walk(tree):
                for child in ast.iter_child_nodes(node):
                    parents[child] = node
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                called = (node.func.attr if isinstance(node.func, ast.Attribute)
                          else getattr(node.func, "id", None))
                if called != name:
                    continue
                enclosing = None
                cur = node
                while cur in parents:
                    cur = parents[cur]
                    if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        enclosing = cur.name
                        break
                found.append((path.relative_to(REPO_ROOT).as_posix(),
                              node.lineno,
                              isinstance(parents.get(node), ast.Expr),
                              enclosing))
        return found

    def test_the_raw_function_is_called_once_and_only_by_the_helper(self):
        raw = self.calls_to(self.RAW)
        where = [f"{f}:{line} in {fn}()" for f, line, _bare, fn in raw]
        self.assertEqual(
            len(raw), 1,
            "move_email_to_folder() should be called in exactly one place, the "
            f"helper that counts its failures. Found: {where}")
        self.assertEqual(
            raw[0][3], self.HELPER,
            f"the one call is in {raw[0][3]}() and should be in "
            f"{self.HELPER}()")

    def test_no_call_to_the_raw_function_discards_the_result(self):
        r"""The defect in one sentence: `move_email_to_folder()` returns a bool
        saying whether it worked, and every caller dropped it.

        **This asks about the raw function and deliberately not about the
        helper.** The first version of this asked about both, which is the
        wrong rule: the helper exists precisely so that the five sites do not
        each have to listen, and none of them needs the answer. Requiring them
        to take it would be five treatments again, which is the thing the
        helper replaced.
        """
        bare = [f"{f}:{line} in {fn}()"
                for f, line, is_bare, fn in self.calls_to(self.RAW) if is_bare]
        self.assertEqual(
            bare, [],
            "these calls discard the result as a bare expression statement, so "
            "a failed move is silent: " + ", ".join(bare))

    def test_every_site_goes_through_the_helper(self):
        r"""The count is stated, so a sixth site is a decision rather than an
        accident. Same reasoning as `MkdirMembershipTest`."""
        sites = self.calls_to(self.HELPER)
        where = "\n      ".join(f"{f}:{line} in {fn}()"
                                for f, line, _b, fn in sites)
        self.assertEqual(
            len(sites), EXPECTED_CALL_SITES,
            f"expected {EXPECTED_CALL_SITES} sites and found {len(sites)}. If "
            "a site was added deliberately, move this number; if one was "
            "removed, say why. Found:\n      " + where)

    def test_the_helper_takes_the_stats_dict(self):
        """It counts into the run's own stats, so the number leaves the run.
        Without this the helper could log and count nothing."""
        tree = source_guards.tree_of("app.py")
        helper = next(node for node in ast.walk(tree)
                      if isinstance(node, ast.FunctionDef)
                      and node.name == self.HELPER)
        self.assertIn("stats", [arg.arg for arg in helper.args.args])


if __name__ == "__main__":
    unittest.main()

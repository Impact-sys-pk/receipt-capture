"""Sub-step 10f.35: the unknown-sender check runs above the attachment loop.

**The case that decides it.** `is_supported()` is checked before the sender is,
and it `continue`s, so **a stranger who sends only an unsupported file got
silence**: no registration alert, and their email filed in
`INBOX.Unsupported Files` as though the format were the problem. **The
unknown-sender alert is the only thing an unregistered sender ever hears back**,
so it has to fire on that case too.

**Why above the loop rather than given a rank.** Whose email this is, is a
question about the email rather than about an attachment, and
`resolve_client_info(email_from)` already answers it above the loop. Ranking the
branch would have left the silent case exactly as it was, because the format
check would still `continue` before the sender was ever considered.

**The embedded-image path already had it above its loop**, at the point where it
resolves the client. So this sub-step makes the two paths agree rather than
moving both, which is what 10f.22 and 10f.33 exist for. Amendment 274.

**What does not change**: `has_alert_been_sent()` still allows one alert per
email, 10f.33's ranking and every folder in it are untouched, and the eleven
single-item combinations `tests/test_one_ranking_both_paths.py` pins stay pinned.
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

import config  # noqa: E402
from resolution_fixtures import (  # noqa: E402
    DOCUMENT,
    Routes,
    SENDER,
    TempEnvironment,
    rows,
    with_email_client,
)
from test_embedded_email_routing import OUTCOMES, Extractor  # noqa: E402
from worker.database.repository import Repository  # noqa: E402

CLIENT = "CLIENT001"


def stranger(test_case, names, alert_result=False, path="email_attachment"):
    """Send `names` from an address the registry does not hold."""
    test_case.addCleanup(setattr, config, "CLIENTS", config.CLIENTS)
    config.CLIENTS = {}
    routes = Routes(Extractor({n: OUTCOMES["ok"] for n in names}),
                    alert_result=alert_result)
    getattr(routes, path)(names=tuple(names),
                          data=[DOCUMENT + n.encode() for n in names])
    return routes


def events(action=None):
    """The unattributed event log, which is where an unknown sender lands."""
    path = config.LOGS_DIR / "receipt_events_UNATTRIBUTED.ndjson"
    if not path.exists():
        return []
    entries = [json.loads(line) for line in
               path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [e for e in entries if action is None or e["action"] == action]


class AStrangerIsAlwaysToldTest(unittest.TestCase):
    """The one the old shape could not pass, and the reason for the sub-step."""

    def test_an_unsupported_file_alone_still_reaches_unknown_sender(self):
        with TempEnvironment():
            routes = stranger(self, ["a.docx"])
            self.assertEqual(
                routes.only_landing(), "INBOX.Unknown Sender",
                "a stranger's email was filed as a format problem, so nobody "
                "was ever going to tell them to register")

    def test_an_unsupported_file_alone_still_sends_the_alert(self):
        """The half of it that matters more, and the folder does not imply it.

        A version that moved the email but left the alert inside the loop would
        pass the test above and still leave the sender hearing nothing.
        """
        with TempEnvironment():
            routes = stranger(self, ["a.docx"])
            self.assertEqual(
                len(routes.alerts), 1,
                f"no registration alert was sent: {routes.alerts}")

    def test_a_supported_file_from_a_stranger_is_unchanged(self):
        with TempEnvironment():
            routes = stranger(self, ["a.pdf"])
            self.assertEqual(routes.only_landing(), "INBOX.Unknown Sender")
            self.assertEqual(len(routes.alerts), 1)

    def test_a_mixed_email_from_a_stranger_reaches_unknown_sender(self):
        """Flag 1 of the 2026-09-08 report, in the shape Paul chose.

        Under first-wins this landed in `INBOX.Unsupported Files` when the
        `.docx` came first and `INBOX.Unknown Sender` when it came second. Under
        10f.33's ranking it landed in `INBOX.Unknown Sender` either way, which
        removed the order-dependence without anybody choosing the answer. Now
        the sender is settled before any attachment is looked at, so it is
        `INBOX.Unknown Sender` because that is what the email is.
        """
        for names in (["a.docx", "b.pdf"], ["a.pdf", "b.docx"]):
            with self.subTest(order="+".join(names)):
                with TempEnvironment():
                    routes = stranger(self, names)
                    self.assertEqual(routes.only_landing(),
                                     "INBOX.Unknown Sender")


class OneAlertPerEmailTest(unittest.TestCase):
    """`has_alert_been_sent()` still guards it, and the hoist must not change that."""

    def test_a_two_attachment_email_sends_one_alert(self):
        with TempEnvironment():
            routes = stranger(self, ["a.pdf", "b.pdf"], alert_result=True)
            self.assertEqual(
                len(routes.alerts), 1,
                f"{len(routes.alerts)} alerts for one email: {routes.alerts}")

    def test_one_email_alerts_row_is_recorded(self):
        with TempEnvironment():
            stranger(self, ["a.pdf", "b.pdf"], alert_result=True)
            repo = Repository()
            try:
                recorded = rows(repo, "SELECT * FROM email_alerts")
            finally:
                repo.close()
            self.assertEqual(len(recorded), 1, recorded)
            self.assertEqual(recorded[0]["alert_type"], "unknown_sender")

    def test_a_second_poll_of_the_same_email_sends_no_second_alert(self):
        """The guard's real job: the same email is offered again next poll.

        `fetch_new_messages()` searches ALL every time, so a stranger's email
        sits in INBOX until it is moved and is seen again on the next poll if
        the move failed.
        """
        with TempEnvironment():
            self.addCleanup(setattr, config, "CLIENTS", config.CLIENTS)
            config.CLIENTS = {}
            first = Routes(Extractor({"a.pdf": OUTCOMES["ok"]}), alert_result=True)
            first.email_attachment(names=("a.pdf",))
            second = Routes(Extractor({"a.pdf": OUTCOMES["ok"]}), alert_result=True)
            second.email_attachment(names=("a.pdf",))

            self.assertEqual(len(first.alerts), 1)
            self.assertEqual(
                second.alerts, [],
                "the same email was alerted twice across two polls")


class TheEventIsLoggedOncePerEmailTest(unittest.TestCase):
    """Section 3 of the brief: the shape was mine to settle.

    **One event per email, with a null filename and a synthetic receipt id.**

    Per attachment was never right: it wrote one row per file for a decision
    taken once about the message, and above the loop there is no filename to
    put in it. A null is honest, and `_log_receipt()` writes the key
    unconditionally so a reader sees `"filename": null` rather than the key
    going missing.

    The synthetic id is the shape `app.py` already uses for the other
    message-level events, `unsupported_file_type` and `duplicate_skipped`, both
    of which pass a fresh uuid because no receipt exists for them either.
    """

    def test_one_event_for_a_two_attachment_email(self):
        with TempEnvironment():
            stranger(self, ["a.pdf", "b.pdf"])
            self.assertEqual(
                len(events("unknown_sender")), 1,
                "the event is still written per attachment")

    def test_the_event_carries_no_filename(self):
        with TempEnvironment():
            stranger(self, ["a.pdf", "b.pdf"])
            entry = events("unknown_sender")[0]
            self.assertIn("filename", entry,
                          "the key must be present and null rather than absent")
            self.assertIsNone(entry["filename"])

    def test_the_event_still_exists_for_an_unsupported_only_email(self):
        """It did not before, because that email never reached the branch."""
        with TempEnvironment():
            stranger(self, ["a.docx"])
            self.assertEqual(len(events("unknown_sender")), 1)


class TheCheckIsAboveBothLoopsTest(unittest.TestCase):
    """Read off `app.py`, because the behaviour has other explanations.

    Everything above would also pass if the check were left in the loop and the
    format branch reordered beneath it, which would be a different change with
    the same visible result on these cases and a worse one on others.
    """

    def _positions(self):
        import ast
        from pathlib import Path

        tree = ast.parse(
            (Path(__file__).resolve().parent.parent / "app.py").read_text(
                encoding="utf-8"))
        loops = {n.target.id: (n.lineno, n.end_lineno) for n in ast.walk(tree)
                 if isinstance(n, ast.For) and isinstance(n.target, ast.Name)
                 and n.target.id in ("att", "embedded_img")}
        self.assertEqual(sorted(loops), ["att", "embedded_img"])
        inside = {}
        for node in ast.walk(tree):
            if (isinstance(node, ast.Compare)
                    and "UNKNOWN_CLIENT_ID" in ast.unparse(node)
                    and "==" in ast.unparse(node)):
                for name, (start, end) in loops.items():
                    if start <= node.lineno <= end:
                        inside.setdefault(name, []).append(node.lineno)
        return inside

    def test_neither_email_loop_decides_who_the_sender_is(self):
        inside = self._positions()
        self.assertEqual(
            inside, {},
            "an unknown-sender check sits inside an email loop, so a message-level "
            f"question is being answered per item: {inside}")


if __name__ == "__main__":
    unittest.main()

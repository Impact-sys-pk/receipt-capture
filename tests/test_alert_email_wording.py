"""Step 10bq: the two automatic client emails, reworded, with a Reply-To.

Brief `PROMPT_claude_code_2026-10-20_alert_email_wording.md`, Paul's decision of
2026-10-20, amendments 543 and 545 of `2026-07-25_CONSOLE_DESIGN.md`.

**The wording is Paul's and is asserted whole**, so a reworded line goes red
rather than slipping past a test that looked for one phrase in it.

**Nothing here opens a connection.** `smtplib.SMTP_SSL` is replaced by a fake
that keeps the message it was handed, which is the message a client would get.

**The reply address is the firm record's `email` field**, which nobody reads in
the mailbox the alerts are sent from. Where none can be established the header
is left off entirely and the wording names no receiving address, the way the
firm name already degrades to naming nobody.
"""

import ast
import re
import sys
import types
import unittest
from email.utils import formataddr
from unittest.mock import patch

import config
import source_guards

fake_openai = types.ModuleType("openai")


class OpenAI:
    def __init__(self, *args, **kwargs):
        pass


fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

import app  # noqa: E402
from resolution_fixtures import TempEnvironment  # noqa: E402
from test_email_move_failures import Mailbox  # noqa: E402
from worker.email import alerts  # noqa: E402

ALERT_MAILBOX = "alerts@example.net"
REPLY_ADDRESS = "bills@example.org"
FIRM_NAME = "Example Accounting Limited"
CLIENT_ADDRESS = "driver@example.com"

#: An email address, loosely. Loose is right for a guard: it should catch
#: anything that looks like one.
ADDRESS = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

UNKNOWN_SENDER_BODY = f"""Hello,

You sent a receipt to {REPLY_ADDRESS}. It reached our receipt system, but we could not
match the address you sent it from to a client record, so the receipt has not been
filed.

This reply comes from {ALERT_MAILBOX}, which is the address our receipt system sends
from. It is us. Replies go back to {REPLY_ADDRESS}.

Please reply and we will register your address and file your receipt.
Nothing is lost in the meantime: your email is held here.

Thank you,
{FIRM_NAME}
"""

NO_ATTACHMENT_BODY = f"""Hello,

You sent an email to {REPLY_ADDRESS}, but there was no attachment on it, so there was
no receipt for us to file.

Please reply with the receipt attached, as a PDF or a photo.

This reply comes from {ALERT_MAILBOX}, which is the address our receipt system sends
from. It is us. Replies go back to {REPLY_ADDRESS}.

Thank you,
{FIRM_NAME}
"""


class FakeSMTP:
    """Stands in for `smtplib.SMTP_SSL` and keeps what it was asked to send."""

    sent = []
    connected = []
    logged_in = []

    def __init__(self, host, port):
        FakeSMTP.connected.append((host, port))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def login(self, username, password):
        FakeSMTP.logged_in.append(username)

    def send_message(self, msg):
        FakeSMTP.sent.append(msg)


class FailingSMTP(FakeSMTP):
    def send_message(self, msg):
        raise OSError("relay refused")


def render(send, *args, **kwargs):
    """Call a real alert function and return (result, the message it sent)."""
    FakeSMTP.sent = []
    FakeSMTP.connected = []
    FakeSMTP.logged_in = []
    with patch.object(alerts.smtplib, "SMTP_SSL", FakeSMTP), \
            patch.object(config, "SMTP_USERNAME", ALERT_MAILBOX):
        result = send(*args, **kwargs)
    assert len(FakeSMTP.sent) == 1, f"{len(FakeSMTP.sent)} messages sent"
    return result, FakeSMTP.sent[0]


def body_of(msg):
    return msg.get_payload()[0].get_payload(decode=True).decode("utf-8")


class UnknownSenderAlertTest(unittest.TestCase):

    def test_headers(self):
        result, msg = render(alerts.send_unknown_sender_alert, CLIENT_ADDRESS,
                             FIRM_NAME, reply_address=REPLY_ADDRESS)
        self.assertTrue(result)
        self.assertEqual(msg["From"], formataddr((FIRM_NAME, ALERT_MAILBOX)))
        self.assertEqual(msg["To"], CLIENT_ADDRESS)
        self.assertEqual(msg["Subject"], "We could not match your email address")
        self.assertEqual(msg["Reply-To"], REPLY_ADDRESS)

    def test_body_is_pauls_wording_exactly(self):
        _, msg = render(alerts.send_unknown_sender_alert, CLIENT_ADDRESS,
                        FIRM_NAME, reply_address=REPLY_ADDRESS)
        self.assertEqual(body_of(msg), UNKNOWN_SENDER_BODY)


class NoAttachmentAlertTest(unittest.TestCase):

    def test_headers(self):
        result, msg = render(alerts.send_no_attachment_alert, CLIENT_ADDRESS,
                             FIRM_NAME, reply_address=REPLY_ADDRESS)
        self.assertTrue(result)
        self.assertEqual(msg["From"], formataddr((FIRM_NAME, ALERT_MAILBOX)))
        self.assertEqual(msg["To"], CLIENT_ADDRESS)
        self.assertEqual(msg["Subject"],
                         "Your email reached us with no receipt attached")
        self.assertEqual(msg["Reply-To"], REPLY_ADDRESS)

    def test_body_is_pauls_wording_exactly(self):
        _, msg = render(alerts.send_no_attachment_alert, CLIENT_ADDRESS,
                        FIRM_NAME, reply_address=REPLY_ADDRESS)
        self.assertEqual(body_of(msg), NO_ATTACHMENT_BODY)


class NoReplyAddressTest(unittest.TestCase):
    """No header, and no receiving address named in the body.

    An empty or wrong `Reply-To` is worse than none, so a value that is not an
    address is treated as no address.
    """

    SENDS = (("unknown_sender", alerts.send_unknown_sender_alert),
             ("no_attachment", alerts.send_no_attachment_alert))
    NOT_ADDRESSES = ("", "   ", None, "not an address", "bills@", "@example.org")

    def test_no_reply_to_header_and_only_the_sending_mailbox_named(self):
        for label, send in self.SENDS:
            for value in self.NOT_ADDRESSES:
                with self.subTest(alert=label, reply_address=value):
                    result, msg = render(send, CLIENT_ADDRESS, FIRM_NAME,
                                         reply_address=value)
                    self.assertTrue(result)
                    self.assertIsNone(msg["Reply-To"])
                    body = body_of(msg)
                    self.assertEqual(set(ADDRESS.findall(body)), {ALERT_MAILBOX})
                    self.assertNotIn("Replies go back", body)
                    self.assertNotIn(" to ,", body)
                    self.assertNotIn(" to .", body)

    def test_reply_address_defaults_to_none(self):
        for label, send in self.SENDS:
            with self.subTest(alert=label):
                _, msg = render(send, CLIENT_ADDRESS, FIRM_NAME)
                self.assertIsNone(msg["Reply-To"])

    def test_the_degraded_wording(self):
        """Stated whole, so the fallback is a decision and not an accident."""
        _, msg = render(alerts.send_unknown_sender_alert, CLIENT_ADDRESS, FIRM_NAME)
        self.assertEqual(body_of(msg), UNKNOWN_SENDER_BODY
                         .replace(f"You sent a receipt to {REPLY_ADDRESS}.",
                                  "You sent us a receipt.")
                         .replace(f" Replies go back to {REPLY_ADDRESS}.", ""))
        _, msg = render(alerts.send_no_attachment_alert, CLIENT_ADDRESS, FIRM_NAME)
        self.assertEqual(body_of(msg), NO_ATTACHMENT_BODY
                         .replace(f"You sent an email to {REPLY_ADDRESS},",
                                  "You sent us an email,")
                         .replace(f" Replies go back to {REPLY_ADDRESS}.", ""))


class NoFirmNameTest(unittest.TestCase):
    """The sign-off is the firm name and nothing else, so no name signs nobody."""

    def test_nothing_stands_in_for_a_missing_firm_name(self):
        for label, send in NoReplyAddressTest.SENDS:
            with self.subTest(alert=label):
                _, msg = render(send, CLIENT_ADDRESS, "", reply_address=REPLY_ADDRESS)
                self.assertEqual(msg["From"], ALERT_MAILBOX)
                self.assertTrue(body_of(msg).endswith("Thank you,\n\n"))


class NoProductNameTest(unittest.TestCase):
    """`Receipt Capture System` names no product, so it appears nowhere."""

    def test_in_no_header_or_body(self):
        for label, send in NoReplyAddressTest.SENDS:
            for firm in (FIRM_NAME, ""):
                for reply in (REPLY_ADDRESS, ""):
                    with self.subTest(alert=label, firm=firm, reply=reply):
                        _, msg = render(send, CLIENT_ADDRESS, firm,
                                        reply_address=reply)
                        self.assertNotIn("Receipt Capture System", msg.as_string())


class SendingPathUnchangedTest(unittest.TestCase):
    """Same host, port and login as before, and it logs rather than raises."""

    def test_sends_through_the_configured_relay_as_the_alert_mailbox(self):
        for label, send in NoReplyAddressTest.SENDS:
            with self.subTest(alert=label):
                render(send, CLIENT_ADDRESS, FIRM_NAME, reply_address=REPLY_ADDRESS)
                self.assertEqual(FakeSMTP.connected,
                                 [(config.SMTP_HOST, config.SMTP_PORT)])
                self.assertEqual(FakeSMTP.logged_in, [ALERT_MAILBOX])

    def test_a_failed_send_returns_false(self):
        for label, send in NoReplyAddressTest.SENDS:
            with self.subTest(alert=label), \
                    patch.object(alerts.smtplib, "SMTP_SSL", FailingSMTP):
                self.assertFalse(send(CLIENT_ADDRESS, FIRM_NAME,
                                      reply_address=REPLY_ADDRESS))


class NoAddressLiteralTest(unittest.TestCase):
    """Sub-step 10d.36's rule: a literal address cannot vary by firm.

    Read off the syntax tree, so the docstring that records the old literal
    having been removed is not mistaken for code carrying it.
    """

    def test_no_string_in_alerts_py_carries_an_email_address(self):
        tree = source_guards.tree_of("worker", "email", "alerts.py")
        found = [(value, line) for value, line in source_guards.string_constants(tree)
                 if ADDRESS.search(value)]
        self.assertEqual(found, [])

    def test_the_guard_would_see_one(self):
        """Control: the same walk over a source that does carry one."""
        tree = ast.parse('x = f"write to someone@example.com about {y}"')
        found = [value for value, _ in source_guards.string_constants(tree)
                 if ADDRESS.search(value)]
        self.assertEqual(len(found), 1)


class MailboxFirmReplyAddressTest(unittest.TestCase):
    """The unknown-sender case: no client, so the firm that owns the mailbox.

    The same shape as `_mailbox_firm_name()`: exactly one firm is the answer,
    and none or several is no answer.
    """

    def setUp(self):
        self.addCleanup(setattr, config, "FIRMS", config.FIRMS)

    def test_one_firm_gives_its_email(self):
        config.FIRMS = {"FIRM001": {"firm_id": "FIRM001", "name": FIRM_NAME,
                                    "email": REPLY_ADDRESS}}
        self.assertEqual(app._mailbox_firm_reply_address(), REPLY_ADDRESS)

    def test_one_firm_with_no_email_gives_nothing(self):
        config.FIRMS = {"FIRM001": {"firm_id": "FIRM001", "name": FIRM_NAME}}
        self.assertEqual(app._mailbox_firm_reply_address(), "")

    def test_several_firms_give_nothing(self):
        config.FIRMS = {
            "FIRM001": {"firm_id": "FIRM001", "name": "A", "email": "a@example.org"},
            "FIRM002": {"firm_id": "FIRM002", "name": "B", "email": "b@example.org"},
        }
        self.assertEqual(app._mailbox_firm_reply_address(), "")

    def test_no_firms_give_nothing(self):
        config.FIRMS = {}
        self.assertEqual(app._mailbox_firm_reply_address(), "")


class EveryCallSitePassesAReplyAddressTest(unittest.TestCase):
    """A guard over the set: each call to either alert in `app.py` passes one.

    A per-path test proves one path. This proves none was left out, and a
    fourth call site added without it goes red here.
    """

    def test_each_call_names_reply_address(self):
        tree = source_guards.tree_of("app.py")
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and ast.unparse(node.func) in ("send_unknown_sender_alert",
                                                "send_no_attachment_alert")]
        self.assertEqual(len(calls), 3, [c.lineno for c in calls])
        for call in calls:
            with self.subTest(line=call.lineno):
                self.assertIn("reply_address", [k.arg for k in call.keywords])


class NoAttachmentPathUsesTheFirmEmailTest(unittest.TestCase):
    """Through one real `app.process_once()`: the firm record's `email` arrives."""

    def test_the_firm_records_email_reaches_the_alert(self):
        received = []

        class Box(Mailbox):
            def send_no_attachment_alert(self, recipient, firm_name=None,
                                         reply_address=None):
                received.append((recipient, firm_name, reply_address))
                return True

        with TempEnvironment():
            saved = config.FIRMS
            config.FIRMS = {config.DEFAULT_FIRM_ID: {
                "firm_id": config.DEFAULT_FIRM_ID, "name": FIRM_NAME,
                "email": REPLY_ADDRESS}}
            try:
                Box().poll()
            finally:
                config.FIRMS = saved
        self.assertEqual(received, [("driver@example.com", FIRM_NAME, REPLY_ADDRESS)])

    def test_no_firm_record_signs_nobody_and_gives_no_reply_address(self):
        """The sign-off is the firm name and nothing else, so never the id."""
        received = []

        class Box(Mailbox):
            def send_no_attachment_alert(self, recipient, firm_name=None,
                                         reply_address=None):
                received.append((recipient, firm_name, reply_address))
                return True

        with TempEnvironment():
            saved = config.FIRMS
            config.FIRMS = {}
            try:
                Box().poll()
            finally:
                config.FIRMS = saved
        self.assertEqual(received, [("driver@example.com", "", "")])


if __name__ == "__main__":
    unittest.main()

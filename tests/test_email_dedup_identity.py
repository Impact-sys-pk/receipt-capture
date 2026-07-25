import email.message
import unittest
from unittest.mock import MagicMock, patch

from worker.email.reader import _resolve_message_id, fetch_new_messages, move_email_to_folder


def _make_email(message_id=None, subject="Receipt"):
    msg = email.message.Message()
    msg["Subject"] = subject
    msg["From"] = "client@example.com"
    msg["Date"] = "Fri, 24 Jul 2026 10:00:00 +0000"
    if message_id is not None:
        msg["Message-ID"] = message_id
    return msg


class ResolveMessageIdTest(unittest.TestCase):
    def test_prefers_message_id_header(self):
        msg = _make_email(message_id="<abc123@mail.example.com>")
        self.assertEqual(_resolve_message_id(msg, "1"), "<abc123@mail.example.com>")

    def test_falls_back_when_header_missing(self):
        msg = _make_email(message_id=None)
        result = _resolve_message_id(msg, "1")
        self.assertIn("1", result)
        self.assertNotEqual(result, "1")

    def test_reused_sequence_number_does_not_collide(self):
        # Same IMAP uid_str ("1") but two genuinely different emails must not
        # resolve to the same identity when both have real Message-ID headers.
        first = _resolve_message_id(_make_email(message_id="<first@mail.example.com>"), "1")
        second = _resolve_message_id(_make_email(message_id="<second@mail.example.com>"), "1")
        self.assertNotEqual(first, second)


class FetchNewMessagesUsesUidCommandsTest(unittest.TestCase):
    @patch("worker.email.reader.imaplib.IMAP4_SSL")
    def test_uses_uid_search_and_fetch_not_sequence_numbers(self, mock_imap_cls):
        mock_imap = MagicMock()
        mock_imap_cls.return_value = mock_imap

        raw = _make_email(message_id="<real@mail.example.com>").as_bytes()
        # A multipart message so _has_attachments' payload-is-list check applies;
        # attachment presence isn't the focus of this test, so just avoid errors.
        mock_imap.uid.side_effect = [
            ("OK", [b"5"]),  # uid("search", ...)
            ("OK", [(b"1 (RFC822 {n}", raw)]),  # uid("fetch", ...)
        ]

        fetch_new_messages(repo=MagicMock())

        # Non-uid search/fetch must never be called: they return sequence
        # numbers that renumber whenever the mailbox is modified.
        mock_imap.search.assert_not_called()
        mock_imap.fetch.assert_not_called()
        self.assertEqual(mock_imap.uid.call_args_list[0].args[0], "search")
        self.assertEqual(mock_imap.uid.call_args_list[1].args[0], "fetch")


class MoveEmailToFolderUsesUidCommandsTest(unittest.TestCase):
    @patch("worker.email.reader.imaplib.IMAP4_SSL")
    def test_uses_uid_copy_and_store_not_sequence_numbers(self, mock_imap_cls):
        mock_imap = MagicMock()
        mock_imap_cls.return_value = mock_imap
        mock_imap.uid.return_value = ("OK", [b"done"])

        result = move_email_to_folder("42", "INBOX.Processed Receipts")

        self.assertTrue(result)
        mock_imap.copy.assert_not_called()
        mock_imap.store.assert_not_called()
        commands = [call.args[0] for call in mock_imap.uid.call_args_list]
        self.assertEqual(commands, ["copy", "store"])


if __name__ == "__main__":
    unittest.main()

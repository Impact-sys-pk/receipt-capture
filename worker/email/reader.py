import base64
import email
import imaplib
import logging

import config

logger = logging.getLogger(__name__)


def _has_attachments(msg):
    """Check if email has file attachments."""
    payload = msg.get_payload()
    if not isinstance(payload, list):
        return False
    for part in payload:
        if part.get_content_disposition() == "attachment" and part.get_filename():
            return True
    return False


def fetch_new_messages(repo):
    """Fetch messages with attachments from IMAP since last UID."""
    last_uid = repo.get_last_uid()

    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    imap.login(config.IMAP_USERNAME, config.IMAP_PASSWORD)
    imap.select("INBOX")

    try:
        if last_uid:
            search_criterion = f"UID {last_uid}:*"
        else:
            search_criterion = "ALL"

        _, message_uids = imap.search(None, search_criterion)
        uids = message_uids[0].split() if message_uids[0] else []

        if last_uid:
            uids = [u for u in uids if int(u) > int(last_uid)]

        messages = []
        for uid in uids:
            _, msg_data = imap.fetch(uid, "(RFC822)")
            msg_bytes = msg_data[0][1]
            msg = email.message_from_bytes(msg_bytes)

            if _has_attachments(msg):
                uid_str = uid.decode() if isinstance(uid, bytes) else uid
                messages.append({
                    "id": uid_str,
                    "subject": msg.get("Subject", ""),
                    "from": {"emailAddress": {"address": msg.get("From", "")}},
                    "receivedDateTime": msg.get("Date", ""),
                    "uid": uid_str,
                    "msg": msg
                })

        if uids:
            last_uid = uids[-1]
            if isinstance(last_uid, bytes):
                last_uid = last_uid.decode()
            repo.save_last_uid(last_uid)

        return messages
    finally:
        imap.close()
        imap.logout()


def fetch_attachments(message_id: str, msg=None):
    """Extract attachments from an email message."""
    if msg is None:
        imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
        imap.login(config.IMAP_USERNAME, config.IMAP_PASSWORD)
        imap.select("INBOX")

        try:
            _, msg_data = imap.fetch(message_id, "(RFC822)")
            msg_bytes = msg_data[0][1]
            msg = email.message_from_bytes(msg_bytes)
        finally:
            imap.close()
            imap.logout()

    attachments = []
    payload = msg.get_payload()
    if isinstance(payload, list):
        for part in payload:
            if part.get_content_disposition() == "attachment" and part.get_filename():
                filename = part.get_filename()
                content_bytes = part.get_payload(decode=True)
                attachments.append({
                    "id": f"{message_id}_{filename}",
                    "name": filename,
                    "contentBytes": base64.b64encode(content_bytes).decode()
                })

    return attachments

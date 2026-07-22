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
    """Fetch all messages with attachments from IMAP inbox.

    Uses message_id from email headers for deduplication instead of UID tracking,
    which is more robust when inbox is modified (deleted/cleared).
    """
    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    imap.login(config.IMAP_USERNAME, config.IMAP_PASSWORD)
    imap.select("INBOX")

    try:
        _, message_uids = imap.search(None, "ALL")
        uids = message_uids[0].split() if message_uids[0] else []

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


def fetch_emails_without_attachments():
    """Fetch emails from inbox that have NO attachments.

    Used to detect emails where client forgot to attach a receipt.
    Returns list of email objects for alerting.
    """
    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    imap.login(config.IMAP_USERNAME, config.IMAP_PASSWORD)
    imap.select("INBOX")

    try:
        _, message_uids = imap.search(None, "ALL")
        uids = message_uids[0].split() if message_uids[0] else []

        emails = []
        for uid in uids:
            _, msg_data = imap.fetch(uid, "(RFC822)")
            msg_bytes = msg_data[0][1]
            msg = email.message_from_bytes(msg_bytes)

            # Only include emails WITHOUT attachments
            if not _has_attachments(msg):
                uid_str = uid.decode() if isinstance(uid, bytes) else uid
                emails.append({
                    "id": uid_str,
                    "subject": msg.get("Subject", ""),
                    "from": msg.get("From", ""),
                    "receivedDateTime": msg.get("Date", ""),
                    "msg": msg
                })

        return emails
    finally:
        imap.close()
        imap.logout()


def move_email_to_folder(message_id: str, target_folder: str) -> bool:
    """Move email from INBOX to target folder. Returns True if successful.

    Args:
        message_id: IMAP UID of the email
        target_folder: Target folder name (e.g., "INBOX.Processed Receipts", "INBOX.Failed Processing")

    Returns:
        True if move succeeded, False if failed (logs warning, does not raise)
    """
    try:
        imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
        imap.login(config.IMAP_USERNAME, config.IMAP_PASSWORD)
        imap.select("INBOX")

        try:
            # Quote folder name if it contains spaces (IMAP requirement)
            quoted_folder = f'"{target_folder}"' if " " in target_folder else target_folder

            # Copy email to target folder
            copy_resp = imap.copy(message_id, quoted_folder)
            if copy_resp[0] != "OK":
                logger.warning(f"Failed to copy email {message_id} to {target_folder}: {copy_resp}")
                return False

            # Mark original for deletion
            store_resp = imap.store(message_id, "+FLAGS", "\\Deleted")
            if store_resp[0] != "OK":
                logger.warning(f"Failed to mark email {message_id} for deletion: {store_resp}")
                return False

            imap.expunge()
            logger.info(f"Moved email {message_id} to {target_folder}")
            return True
        finally:
            imap.close()
            imap.logout()
    except Exception as exc:
        logger.warning(f"Failed to move email {message_id} to {target_folder}: {exc}")
        return False

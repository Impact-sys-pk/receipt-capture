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


def _resolve_message_id(msg, uid_str: str) -> str:
    """Return the email's Message-ID header, or a fallback if it's missing.

    The Message-ID header is the only identifier stable across polls: IMAP
    sequence numbers renumber whenever the mailbox changes (e.g. after every
    processed email is moved out of INBOX), and even UIDs are only meant for
    addressing the mailbox within a session, not as a durable dedup key.
    """
    header = msg.get("Message-ID")
    if header:
        return header.strip()
    logger.warning(f"email uid={uid_str} has no Message-ID header, falling back to uid+date")
    return f"no-message-id:{uid_str}:{msg.get('Date', '')}"


def fetch_new_messages(repo):
    """Fetch all messages with attachments from IMAP inbox.

    Uses each email's Message-ID header as the stable identity for
    deduplication. IMAP UIDs are used only to address the mailbox for
    fetch/copy/store within this poll — they must not be reused as a
    cross-poll dedup key.
    """
    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    imap.login(config.IMAP_USERNAME, config.IMAP_PASSWORD)
    imap.select("INBOX")

    try:
        _, message_uids = imap.uid("search", None, "ALL")
        uids = message_uids[0].split() if message_uids[0] else []

        messages = []
        for uid in uids:
            _, msg_data = imap.uid("fetch", uid, "(RFC822)")
            msg_bytes = msg_data[0][1]
            msg = email.message_from_bytes(msg_bytes)

            if _has_attachments(msg):
                uid_str = uid.decode() if isinstance(uid, bytes) else uid
                messages.append({
                    "id": _resolve_message_id(msg, uid_str),
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


def fetch_attachments(message_id: str, msg=None, uid: str = None):
    """Extract attachments from an email message.

    message_id is used only to build each attachment's "id" field. If msg is
    not already available, uid (a real IMAP UID) is required to fetch it.
    """
    if msg is None:
        if uid is None:
            raise ValueError("fetch_attachments requires uid when msg is not provided")
        imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
        imap.login(config.IMAP_USERNAME, config.IMAP_PASSWORD)
        imap.select("INBOX")

        try:
            _, msg_data = imap.uid("fetch", uid, "(RFC822)")
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


def extract_embedded_images(msg) -> list:
    """Extract embedded images from email message.

    Looks for inline images (Content-Disposition: inline) in email MIME structure.
    Returns list of image data dicts compatible with fetch_attachments() format.
    """
    images = []

    if not isinstance(msg.get_payload(), list):
        return images

    for part in msg.walk():
        # Skip if not image
        if not part.get_content_type().startswith("image/"):
            continue

        # Check if it's inline (embedded in email body)
        disposition = part.get("Content-Disposition", "")
        is_inline = "inline" in disposition or part.get("Content-ID")

        if not is_inline:
            continue

        # Extract image data
        try:
            filename = part.get_filename()
            if not filename:
                # Generate filename for inline image without name
                content_type = part.get_content_type()
                ext = content_type.split("/")[1]  # e.g., "jpeg" from "image/jpeg"
                filename = f"embedded_image_{len(images)}.{ext}"

            content_bytes = part.get_payload(decode=True)
            if content_bytes:
                images.append({
                    "id": f"embedded_{filename}",
                    "name": filename,
                    "contentBytes": base64.b64encode(content_bytes).decode(),
                    "is_embedded": True
                })
                logger.info(f"Extracted embedded image: {filename}")
        except Exception as exc:
            logger.warning(f"Failed to extract embedded image: {exc}")

    return images


def fetch_emails_without_attachments():
    """Fetch emails from inbox that have NO attachments.

    Used to detect emails where client forgot to attach a receipt.
    Returns list of email objects for alerting.
    """
    imap = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT)
    imap.login(config.IMAP_USERNAME, config.IMAP_PASSWORD)
    imap.select("INBOX")

    try:
        _, message_uids = imap.uid("search", None, "ALL")
        uids = message_uids[0].split() if message_uids[0] else []

        emails = []
        for uid in uids:
            _, msg_data = imap.uid("fetch", uid, "(RFC822)")
            msg_bytes = msg_data[0][1]
            msg = email.message_from_bytes(msg_bytes)

            # Only include emails WITHOUT attachments
            if not _has_attachments(msg):
                uid_str = uid.decode() if isinstance(uid, bytes) else uid
                emails.append({
                    "id": _resolve_message_id(msg, uid_str),
                    "subject": msg.get("Subject", ""),
                    "from": msg.get("From", ""),
                    "receivedDateTime": msg.get("Date", ""),
                    "uid": uid_str,
                    "msg": msg
                })

        return emails
    finally:
        imap.close()
        imap.logout()


def move_email_to_folder(uid: str, target_folder: str) -> bool:
    """Move email from INBOX to target folder. Returns True if successful.

    Args:
        uid: IMAP UID of the email (not the Message-ID header — UIDs are what
            IMAP COPY/STORE operate on)
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
            copy_resp = imap.uid("copy", uid, quoted_folder)
            if copy_resp[0] != "OK":
                logger.warning(f"Failed to copy email uid={uid} to {target_folder}: {copy_resp}")
                return False

            # Mark original for deletion
            store_resp = imap.uid("store", uid, "+FLAGS", "\\Deleted")
            if store_resp[0] != "OK":
                logger.warning(f"Failed to mark email uid={uid} for deletion: {store_resp}")
                return False

            imap.expunge()
            logger.info(f"Moved email uid={uid} to {target_folder}")
            return True
        finally:
            imap.close()
            imap.logout()
    except Exception as exc:
        logger.warning(f"Failed to move email uid={uid} to {target_folder}: {exc}")
        return False

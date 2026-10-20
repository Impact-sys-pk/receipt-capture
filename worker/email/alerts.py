import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, parseaddr

import config

logger = logging.getLogger(__name__)


def _usable_reply_address(value) -> str:
    """The reply address if it is one, or "" if it is not.

    Step 10bq. An empty or wrong Reply-To is worse than none, so anything that
    does not parse to a single bare address with something either side of the @
    is treated as no address at all.
    """
    value = (value or "").strip()
    _name, address = parseaddr(value)
    if address != value or " " in address:
        return ""
    local, at, domain = address.partition("@")
    if not (local and at and domain):
        return ""
    return address


def _send(subject: str, body: str, recipient_email: str, firm_name: str,
          reply_address: str) -> None:
    """Build the message and send it from the alert mailbox. Raises on failure.

    The From address is config.SMTP_USERNAME exactly as before. With no firm
    name it is the bare address, so nothing stands in for the firm.
    """
    msg = MIMEMultipart()
    msg["From"] = formataddr((firm_name, config.SMTP_USERNAME))
    msg["To"] = recipient_email
    msg["Subject"] = subject
    if reply_address:
        msg["Reply-To"] = reply_address
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as smtp:
        smtp.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        smtp.send_message(msg)


def send_no_attachment_alert(recipient_email: str, firm_name: str,
                             reply_address: str = "") -> bool:
    """Send alert to client that email arrived without attachment.

    Step 10bq rewrote the wording, Paul's of 2026-10-20, and added the Reply-To.
    The reply address is the firm record's `email` field, because nobody reads
    the mailbox this is sent from. With none, the header is left off and the
    wording names no receiving address.

    Args:
        recipient_email: Client email address to send alert to
        firm_name: Firm name for display (e.g., "Best Accounting")
        reply_address: The firm's own address for replies, or "" if not known

    Returns:
        True if sent successfully, False if failed (logs warning, does not raise)
    """
    try:
        reply_address = _usable_reply_address(reply_address)
        alert_mailbox = config.SMTP_USERNAME
        subject = "Your email reached us with no receipt attached"
        if reply_address:
            sent_to = f"You sent an email to {reply_address},"
            replies = f" Replies go back to {reply_address}."
        else:
            sent_to = "You sent us an email,"
            replies = ""
        body = f"""Hello,

{sent_to} but there was no attachment on it, so there was
no receipt for us to file.

Please reply with the receipt attached, as a PDF or a photo.

This reply comes from {alert_mailbox}, which is the address our receipt system sends
from. It is us.{replies}

Thank you,
{firm_name}
"""

        _send(subject, body, recipient_email, firm_name, reply_address)

        logger.info(f"Sent no-attachment alert to {recipient_email} "
                    f"(firm: {firm_name}, reply-to: {reply_address or 'none'})")
        return True

    except Exception as exc:
        logger.warning(f"Failed to send no-attachment alert to {recipient_email}: {exc}")
        return False


def send_unknown_sender_alert(recipient_email: str, firm_name: str = "",
                              reply_address: str = "") -> bool:
    """Tell an unrecognised sender we cannot place their address.

    Sub-step 10d.36, row F7 of 2026-08-20_LIST_settings_firm_and_client.md.
    This is the only automatic email that reaches somebody who is not a known
    client, so it is the first thing an unregistered sender sees, and it named
    the wrong company: three literals, "support@lastingimpact.co.uk" and
    "Lasting Impact" twice, in a system that is meant to serve any firm.

    F7 records that as a wall, because a literal in source cannot vary by firm.
    All three are gone. The firm's name comes in as a parameter, the way
    send_no_attachment_alert() already takes it, and the contact address is the
    mailbox this alert is sent from, which is per-deployment configuration rather
    than source.

    ~~It is deliberately NOT read off the firm record's `email` field. Sub-step
    10d.51 says that field comes across from firms.csv unchanged and gains no
    reader; it is outstanding item 24.~~ Reversed 2026-10-20 by Paul's decision,
    step 10bq and amendment 545, which closes outstanding item 24. Nobody reads
    the mailbox this alert is sent from, so the email now carries a Reply-To of
    the firm record's `email` field, which is that field's first reader. The
    sending mailbox is unchanged and is still named in the body, as the address
    the email comes from rather than the one to write to.

    firm_name and reply_address default to empty because there is genuinely no
    client to take a firm from here. An empty name produces wording that names
    nobody, and an empty reply address leaves the Reply-To header off and the
    wording names no receiving address, which is better than naming the wrong
    firm or the wrong mailbox.

    Args:
        recipient_email: Sender's email address to reply to
        firm_name: The firm behind the capture mailbox, or "" if not known
        reply_address: That firm's own address for replies, or "" if not known

    Returns:
        True if sent successfully, False if failed (logs warning, does not raise)
    """
    try:
        reply_address = _usable_reply_address(reply_address)
        alert_mailbox = config.SMTP_USERNAME
        subject = "We could not match your email address"
        if reply_address:
            sent_to = f"You sent a receipt to {reply_address}."
            replies = f" Replies go back to {reply_address}."
        else:
            sent_to = "You sent us a receipt."
            replies = ""
        body = f"""Hello,

{sent_to} It reached our receipt system, but we could not
match the address you sent it from to a client record, so the receipt has not been
filed.

This reply comes from {alert_mailbox}, which is the address our receipt system sends
from. It is us.{replies}

Please reply and we will register your address and file your receipt.
Nothing is lost in the meantime: your email is held here.

Thank you,
{firm_name}
"""

        _send(subject, body, recipient_email, firm_name, reply_address)

        logger.info(f"Sent unknown sender alert to {recipient_email} "
                    f"(firm: {firm_name or 'none'}, reply-to: {reply_address or 'none'})")
        return True

    except Exception as exc:
        logger.warning(f"Failed to send unknown sender alert to {recipient_email}: {exc}")
        return False

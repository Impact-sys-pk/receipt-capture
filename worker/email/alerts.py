import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import config

logger = logging.getLogger(__name__)


def send_no_attachment_alert(recipient_email: str, firm_name: str) -> bool:
    """Send alert to client that email arrived without attachment.

    Args:
        recipient_email: Client email address to send alert to
        firm_name: Firm name for display (e.g., "Best Accounting")

    Returns:
        True if sent successfully, False if failed (logs warning, does not raise)
    """
    try:
        subject = "Receipt Missing Attachment"
        body = f"""Hello,

We received your email but no receipt attachment was found.

Please resend your email with the receipt file attached (PDF, JPG, PNG, or similar image format).

Thank you,
{firm_name}
Receipt Capture System
"""

        # Create email
        msg = MIMEMultipart()
        msg["From"] = f"{firm_name} <{config.SMTP_USERNAME}>"
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send via SMTP
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as smtp:
            smtp.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            smtp.send_message(msg)

        logger.info(f"Sent no-attachment alert to {recipient_email} (firm: {firm_name})")
        return True

    except Exception as exc:
        logger.warning(f"Failed to send no-attachment alert to {recipient_email}: {exc}")
        return False


def send_unknown_sender_alert(recipient_email: str, firm_name: str = "") -> bool:
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

    It is deliberately NOT read off the firm record's `email` field. Sub-step
    10d.51 says that field comes across from firms.csv unchanged and gains no
    reader; it is outstanding item 24.

    firm_name defaults to empty because there is genuinely no client to take a
    firm from here. An empty name produces wording that names nobody, which is
    better than naming the wrong firm.

    Args:
        recipient_email: Sender's email address to reply to
        firm_name: The firm behind the capture mailbox, or "" if not known

    Returns:
        True if sent successfully, False if failed (logs warning, does not raise)
    """
    try:
        subject = "Receipt Submission - Unrecognized Sender"
        sender_label = firm_name or "Receipt Capture System"
        sign_off = f"Thank you,\nReceipt Capture System\n{firm_name}" if firm_name else "Thank you,\nReceipt Capture System"
        body = f"""Hello,

We received your email but we don't recognize your email address in our system.

If you are a client, please reply to this email at {config.SMTP_USERNAME} so your address can be registered.

If you believe this is an error, please reply to this email.

{sign_off}
"""

        # Create email
        msg = MIMEMultipart()
        msg["From"] = f"{sender_label} <{config.SMTP_USERNAME}>"
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send via SMTP
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as smtp:
            smtp.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            smtp.send_message(msg)

        logger.info(f"Sent unknown sender alert to {recipient_email} (firm: {firm_name or 'none'})")
        return True

    except Exception as exc:
        logger.warning(f"Failed to send unknown sender alert to {recipient_email}: {exc}")
        return False

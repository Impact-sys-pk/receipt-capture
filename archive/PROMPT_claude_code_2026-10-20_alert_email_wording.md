# AUTOMATIC task. Claude Code brief, 2026-10-20: the two automatic client emails are rewritten

Written by the consultant session, 2026-10-20, 16:13 BST, read off the clock in this reply. Paul's
decision of 2026-10-20. Step 10bq of `2026-07-25_BUILD_STATUS.md`, raised by amendment 543 and
settled by amendment 545 of `2026-07-25_CONSOLE_DESIGN.md`.

**This runs under `CLAUDE.md`'s AUTOMATIC Task Mode.** Its stop list is unchanged and outranks this
brief.

**Report to `2026-10-20_REPORT_claude_code_alert_email_wording.md` in the repository root.**

---

## Three rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** You report; the consultant session marks
the step.

**2. `2026-07-25_CONSOLE_DESIGN.md` is not yours either.**

**3. Enumerate rather than take this brief's word.** This brief states no counts on purpose. Where
you need to know what reads a thing, walk it from the syntax tree in this task and state what you
found.

---

## Why this exists

Both automatic emails were read on 2026-10-20 and rendered with the values they carry in a live run.
Six faults in the unknown-sender alert, two of which the no-attachment alert shares. Step 10bq
carries all six with the reasoning. The sending address was the first decision and it is taken: the
emails keep going out from the configured alert mailbox, because the DMARC record for the domain the
client writes to publishes `p=quarantine; pct=100` and nothing sent from the current relay aligns
with it. So **the work is the wording and the headers, and the sending path does not change.**

## What to build

Both functions in `worker\email\alerts.py`: `send_unknown_sender_alert()` and
`send_no_attachment_alert()`.

### 1. The bodies and subjects

The text below is the deliverable and is Paul's. **Do not improve it.** Every address and name in it
is interpolated, never a literal: `{firm_name}` is the firm name the function already takes,
`{alert_mailbox}` is the mailbox the pipeline sends from, and `{reply_address}` is the new one in
part 2 below.

**`send_unknown_sender_alert()`**

```
Subject: We could not match your email address

Hello,

You sent a receipt to {reply_address}. It reached our receipt system, but we could not
match the address you sent it from to a client record, so the receipt has not been
filed.

This reply comes from {alert_mailbox}, which is the address our receipt system sends
from. It is us. Replies go back to {reply_address}.

Please reply and we will add your address. Nothing is lost in the meantime: your email
is held and the receipt will be filed once the address is registered.

Thank you,
{firm_name}
```

**`send_no_attachment_alert()`**

```
Subject: Your email reached us with no receipt attached

Hello,

You sent an email to {reply_address}, but there was no attachment on it, so there was
no receipt for us to file.

Please reply with the receipt attached, as a PDF or a photo.

This reply comes from {alert_mailbox}, which is the address our receipt system sends
from. It is us. Replies go back to {reply_address}.

Thank you,
{firm_name}
```

### 2. A `Reply-To` header on both, and where the address comes from

Both emails invite a reply and **nobody reads the mailbox they are sent from**. Paul, 2026-10-20,
asked directly. So the reply has to be directed somewhere a person opens.

**The address is the `email` field on the firm record, and this gives that field its first reader.**
Paul's decision of 2026-10-20. Outstanding item 24 closes with it. The docstring in this file
currently records the opposite decision, that the field deliberately gains no reader; **rewrite that
paragraph to record the reversal and its date rather than leaving it contradicting the code.**

- **No email address may be a literal in this file.** Sub-step 10d.36 removed three literals from
  this exact function and the reasoning holds: a literal cannot vary by firm. Establish for yourself
  that none remains afterwards.
- `send_no_attachment_alert()` runs where a firm has been resolved. `send_unknown_sender_alert()`
  runs where, by definition, no client and so no firm was resolved. **That second case is already
  solved in this codebase for the firm's name.** Find how, follow the same shape, and say in your
  report what you followed.
- **Where no reply address can be established**, send no `Reply-To` header at all and use wording
  that names no receiving address, the way the firm name already degrades to naming nobody. An empty
  or wrong header is worse than none.

## What it has to do

- Both emails send from the same mailbox as today, by the same path. **Nothing about SMTP changes.**
- Both carry a `Reply-To` of the firm's own address when one can be established.
- Both return `True` or `False` and log rather than raise, exactly as today.
- British spelling throughout. There is American spelling in the current subject and body.
- No occurrence of the phrase `Receipt Capture System` survives in either email. It names no product.
- The sign-off is the firm name from the firm record and nothing else.

## Red before green

- A test that renders each message and asserts the headers: `From`, `To`, `Subject` and `Reply-To`.
- A test for the no-reply-address case, asserting no `Reply-To` header is present and the body names
  no receiving address.
- A source guard that fails if an email address literal reappears in `worker\email\alerts.py`.
  `tests\source_guards.py` is already used this way elsewhere in the suite.
- Then prove the suite discriminates: put the old wording back and show which tests go red. **If
  nothing goes red, say so** and propose the check that would.

## What not to do

- **No real SMTP connection and no email sent anywhere.** Build the message object and inspect it.
- **Do not change which mailbox the pipeline sends from.** That was decided today and it is not in
  this brief.
- **Do not touch `worker\email\reader.py`**, the routing folders, or anything about how email is
  read.
- **Do not edit `Intellibills\firms.json`.** Paul maintains the firm record through Firm Settings.
- Nothing is deleted anywhere, and nothing is written outside `C:\LastingImpact\receipt_capture`.
- **Do not fix anything else.** Flag, do not fix.

## How to report

- Both emails rendered in full, exactly as they would reach a client, against the live firm record.
- How you established that no address literal remains.
- What you followed for the unresolved-firm case, named.
- The tests that went red, then green, and the discrimination result.
- Suite totals before and after.
- Whether the docstring paragraph recording the old decision was rewritten, and what it now says.
- Propose the commit and wait for Paul's yes.
- Disclose your own mistakes, including ones you caught and corrected.

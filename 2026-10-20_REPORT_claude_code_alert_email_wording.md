# Report: step 10bq, the two automatic client emails reworded

Claude Code, 2026-10-20, 16:55 BST. The clock was read in this session with `date`, which gave
`Tue Oct 20 16:55:47 GMTDT 2026`. GMTDT is BST.

Brief: `PROMPT_claude_code_2026-10-20_alert_email_wording.md`. Nothing is committed. A proposed
commit is at the end and waits for Paul's yes, as the brief says.

`2026-07-25_BUILD_STATUS.md` and `2026-07-25_CONSOLE_DESIGN.md` were already modified when this
session started. I have not touched either.

---

## 1. What changed

| File | Change |
|---|---|
| `worker\email\alerts.py` | Both functions reworded to Paul's text. Both take a new `reply_address=""` argument and set `Reply-To` when it is a usable address. The shared build-and-send code moved into `_send()`. A new `_usable_reply_address()` decides what counts as an address. The `From` header is built with `email.utils.formataddr`, so an empty firm name gives the bare mailbox. The docstring paragraph has been rewritten (see section 6). |
| `app.py` | New `_mailbox_firm_reply_address()`, next to `_mailbox_firm_name()`. Both unknown-sender call sites pass `reply_address=_mailbox_firm_reply_address()`. The no-attachment call site reads `name` and `email` off the firm record and passes the email. The multi-firm warning now says "without a firm name or a reply address". |
| `tests\test_alert_email_wording.py` | New. 20 tests, described in section 4. |
| `tests\test_step10d_pipeline.py` | One assertion changed. It used to require `Receipt Capture System` in the `From` header when there is no firm name. The brief removes that phrase, so it now requires the bare sending mailbox. The old line is struck through in a comment beside the new one. |
| `tests\resolution_fixtures.py`, `tests\test_email_move_failures.py` | The two alert stubs now accept `reply_address=None`. Without this, the new argument at the call sites raises `TypeError` inside the stub. |

The sending path is unchanged: same `SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT)`, same login as
`config.SMTP_USERNAME`, same `From` mailbox. Both functions still return `True` or `False` and log
rather than raise. `worker\email\reader.py`, the routing folders and `firms.json` are untouched.

## 2. Both emails, rendered against the live firm record

Live values were read directly from the files without importing `config`, because that import runs
the `mkdir` block against the live roots:

- `name` and `email` came from `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\firms.json`, which holds one firm, `FIRM001`.
- `SMTP_USERNAME` came from `.env`.

The real functions were called with `smtplib.SMTP_SSL` replaced by a fake that keeps the message.
No connection was made. The recipient `someone@example.com` is a placeholder.

**Unknown sender**

```
From: Intellitax Accounting Limited <alerts@lastingimpact.co.uk>
To: someone@example.com
Subject: We could not match your email address
Reply-To: bills@intellitax.co.uk

Hello,

You sent a receipt to bills@intellitax.co.uk. It reached our receipt system, but we could not
match the address you sent it from to a client record, so the receipt has not been
filed.

This reply comes from alerts@lastingimpact.co.uk, which is the address our receipt system sends
from. It is us. Replies go back to bills@intellitax.co.uk.

Please reply and we will register your address and file your receipt.
Nothing is lost in the meantime: your email is held here.

Thank you,
Intellitax Accounting Limited
```

That paragraph was corrected after the first version of this report. Section 11 has the details.

**No attachment**

```
From: Intellitax Accounting Limited <alerts@lastingimpact.co.uk>
To: someone@example.com
Subject: Your email reached us with no receipt attached
Reply-To: bills@intellitax.co.uk

Hello,

You sent an email to bills@intellitax.co.uk, but there was no attachment on it, so there was
no receipt for us to file.

Please reply with the receipt attached, as a PDF or a photo.

This reply comes from alerts@lastingimpact.co.uk, which is the address our receipt system sends
from. It is us. Replies go back to bills@intellitax.co.uk.

Thank you,
Intellitax Accounting Limited
```

**When no reply address can be established.** I wrote this wording myself, so it needs Paul's
approval. The brief asked for wording that names no receiving address but did not supply the text.
I made the smallest change to Paul's text that does this:

| Paul's line | Without a reply address |
|---|---|
| `You sent a receipt to {reply_address}.` | `You sent us a receipt.` |
| `You sent an email to {reply_address},` | `You sent us an email,` |
| `It is us. Replies go back to {reply_address}.` | `It is us.` |

There is no `Reply-To` header in this case. `NoReplyAddressTest.test_the_degraded_wording` states
both bodies in full.

**What counts as "no reply address" is also my judgement.** `_usable_reply_address()` turns any of
these into no header: an empty or blank value, `None`, anything with a space, anything that does not
parse to exactly itself, and anything without text on both sides of the `@`. It is deliberately
loose: it rejects obvious junk and does not try to validate addresses fully.

## 3. How I established that no address literal remains

I walked the syntax tree of `worker\email\alerts.py` with `tests\source_guards.string_constants()`
and matched every string constant against an address pattern:

- **Code only, docstrings excluded:** `[]`, so no address appears anywhere in the code.
- **Docstrings included:** one hit, `support@lastingimpact.co.uk` at line 103. This is the
  docstring of `send_unknown_sender_alert()`, recording sub-step 10d.36 removing that literal. It is
  history, not code, and I left it as written.

The f-string bodies are covered by this check, because the literal parts of an f-string are
`Constant` nodes. The guard is `NoAddressLiteralTest`. It has a control test,
`test_the_guard_would_see_one`, which proves the same walk finds an address inside an f-string.

## 4. What I followed for the unresolved-firm case

**`_mailbox_firm_name()` in `app.py`.** It is the existing answer to "which firm, when no client
was resolved": exactly one firm in `config.FIRMS` is the answer, and none or several is no answer.
`_mailbox_firm_reply_address()` applies the same rule to `email`. It does not log a warning of its
own, because the two are always called together and `_mailbox_firm_name()` already warns once. I
widened that warning's wording to name the reply address as well.

## 5. Tests: red, green and discrimination

**Suite totals**

| When | Result |
|---|---|
| Before any change | 1611 passed, 2 skipped, 1208 subtests |
| After the change | 1630 passed, 2 skipped, 1239 subtests |
| After adding the test found missing below | **1631 passed, 2 skipped, 1239 subtests** |

**Red first.** With only the new test file in place: 39 failed, 9 passed. **Most of that red was
weak:** the tests pass a `reply_address` argument the old functions did not have, so they failed
with `TypeError` rather than on the wording. The wording-specific red comes from the mutations
below, where the old wording sits behind the new signature. Two tests passed before the change, and
should have: the address-literal guard and its control. The old code also carried no literal.

**Discrimination.** I ran ten mutations. Each was anchored to a string asserted to match exactly
once, applied to the finished file, run against the full suite, and then the file was restored and
its md5 checked. Both files were back to their pre-run hashes afterwards:
`app.py 0819aa86f25b877c08d3e637d10729fb` and `alerts.py 1a74e8c2bc0ac5dcd65b3c54958f1b1d`.

| # | Mutation | Caught by | Failed / suite |
|---|---|---|---|
| 1 | Old unknown-sender subject and wording | `UnknownSenderAlertTest` (both), `test_the_degraded_wording`, `NoFirmNameTest`, `NoProductNameTest` (4 subtests) | 8 failed |
| 2 | Old no-attachment subject and wording | `NoAttachmentAlertTest` (both), `test_the_degraded_wording`, `NoFirmNameTest`, `NoProductNameTest` (4), `NoReplyAddressTest` (6) | 14 failed |
| 3 | `Reply-To` never set | both `test_headers` | 2 failed |
| 4 | `Reply-To` falls back to the literal `support@lastingimpact.co.uk` | `NoAddressLiteralTest`, `NoReplyAddressTest` (14 subtests) | 15 failed |
| 5 | `Receipt Capture System` back in `From` when there is no firm name | `test_step10d_pipeline`'s no-firm test, `NoFirmNameTest` (2), `NoProductNameTest` (4) | 7 failed |
| 6 | Reply address not validated | `NoReplyAddressTest` (6 subtests: `not an address`, `bills@`, `@example.org` on each email) | 6 failed |
| 7 | No-attachment call site drops `reply_address` | `NoAttachmentPathUsesTheFirmEmailTest`, `EveryCallSitePassesAReplyAddressTest` | 2 failed |
| 8 | `_mailbox_firm_reply_address()` guesses the first of several firms | `test_several_firms_give_nothing` | 1 failed |
| 9 | No-attachment firm name falls back to the firm id | **nothing, on the first run** | 0 failed |

**Mutation 9 survived, so the suite had a gap.** Nothing tested a no-attachment alert where the
firm has no record. I added
`NoAttachmentPathUsesTheFirmEmailTest.test_no_firm_record_signs_nobody_and_gives_no_reply_address`
and re-applied mutation 9 against the new test file. It failed with
`[('driver@example.com', 'FIRM001', '')] != [('driver@example.com', '', '')]`. The file was restored
and its md5 matched. Mutation 9 was not re-run against the full suite.

No mutation was caught by a test outside the ones listed. That list is the whole `FAILED` and
`SUBFAILED` output of each run, not a selection.

## 6. The docstring paragraph

**Rewritten.** The old paragraph said the address is "deliberately NOT read off the firm record's
`email` field". It is now struck through rather than deleted, and followed by:

> Reversed 2026-10-20 by Paul's decision, step 10bq and amendment 545, which closes outstanding
> item 24. Nobody reads the mailbox this alert is sent from, so the email now carries a Reply-To of
> the firm record's `email` field, which is that field's first reader. The sending mailbox is
> unchanged and is still named in the body, as the address the email comes from rather than the
> one to write to.

The paragraph about `firm_name` defaulting to empty now covers `reply_address` as well.

## 7. One behaviour change at a call site, for Paul to confirm

At the no-attachment call site, `firm_name` was `config.FIRMS.get(firm_id, {}).get("name",
firm_id)`. That fallback put the firm id, for example `FIRM001`, in the sign-off when the firm had
no record. I changed it to fall back to `""`, because the brief says "The sign-off is the firm name
from the firm record and nothing else."

**A side effect:** in that edge case, `record_alert_sent()` now records `""` rather than the id as
the firm name in `email_alerts`. On today's registry the case cannot arise, because the one firm is
`FIRM001` and `DEFAULT_FIRM_ID` is `FIRM001`.

## 8. Flags. Not fixed.

1. **Two other docstrings still say the `email` field has no reader, and that is now false.** One
   is `config.load_firms()`: "deliberately gains no reader: it is outstanding item 24". The other
   is `tests\live_paths.py` `write_firm_record()`: "nothing in the pipeline reads either".
   **Recommendation:** rewrite both sentences to say that `app.py` reads `email` as the alert
   reply address from step 10bq. Each is a one-line edit and I can do both now if you say yes.
2. ~~**"Your email is held and the receipt will be filed once the address is registered" depends on
   a manual step.**~~ **Resolved 2026-10-20 by Paul's corrected wording, section 11.** The rest of
   this flag is kept as written. Nothing in the code reads `INBOX.Unknown Sender` back. Enumerated: the folder
   name appears in `app.py` only as two `_move_email()` destinations. So registering the address
   does not file the receipt by itself: somebody has to move the email back to INBOX.
   **Speculation, not verified:** a moved-back email would then process normally, because the
   unknown-sender branch `continue`s before anything is marked processed. **Recommendation:** Paul
   decides whether the promise stays as written and the manual move becomes a documented step, or
   the sentence changes.
3. **With no reply address, both emails still say "Please reply".** That reply goes to the sending
   mailbox, which nobody reads. It cannot happen on today's registry, where the firm has an
   `email`. **Recommendation:** leave it, because the brief's wording is Paul's and the case is
   theoretical on one firm. Flagged so it is a decision rather than an accident.
4. **A stranger who sends no attachment gets `FIRM001`'s name and reply address.** This predates
   the change. The no-attachment path takes its firm from `resolve_client_info()`, which returns
   `DEFAULT_FIRM_ID` for an unknown sender. On a single-firm install that is the right firm, so
   **recommendation: no change.** Recorded because the unknown-sender path deliberately avoids
   `DEFAULT_FIRM_ID` and this path does not.

## 9. My own mistakes, including ones I caught

- **The first mutation run refused all three `app.py` mutations, with zero anchor matches.**
  `app.py` uses CRLF line endings and my anchors used LF. The harness's exactly-once rule refused
  them rather than reporting a pass. I made the anchors follow each file's line endings and
  re-ran those three.
- **A scripted edit to the mutation harness silently did not apply.** It was meant to replace a
  nested f-string in the old-wording mutation. I caught it by searching the harness file
  afterwards, and fixed it with a direct edit before any run.
- **The initial red was mostly `TypeError`, not wording.** Disclosed in section 5. The mutations
  are what show the wording tests discriminate.
- **I did not have a test for the firm-id fallback until mutation 9 showed it.**

## 11. Wording correction, 2026-10-20, after the first version of this report

Paul's text. **The unknown-sender email only.** The old paragraph promised the receipt "will be
filed once the address is registered", which the code does not do. Flag 2 established that nothing
reads `INBOX.Unknown Sender` back.

| Was | Now |
|---|---|
| `Please reply and we will add your address. Nothing is lost in the meantime: your email` / `is held and the receipt will be filed once the address is registered.` | `Please reply and we will register your address and file your receipt.` / `Nothing is lost in the meantime: your email is held here.` |

**The fallback wording for "no reply address" changes the same way, with no separate edit.** The
paragraph names no address, so both versions of the email share it. Rendered both ways against the
live firm record: the paragraph is identical in each, and the version without a reply address
still has no `Reply-To` and names only the sending mailbox.

**Tests that changed.** One constant, `UNKNOWN_SENDER_BODY` in
`tests\test_alert_email_wording.py`, used by two tests:

- `UnknownSenderAlertTest.test_body_is_pauls_wording_exactly`
- `NoReplyAddressTest.test_the_degraded_wording`

I found these by searching the repository for both old sentences, excluding `.history\`. The only
other hits were the brief and this report, and the brief is left as written. **Red first:** with the
constant updated and the code not yet changed, those two tests failed and the other 18 passed.
After the code change: **1631 passed, 2 skipped, 1239 subtests**, the same totals as before,
because no test was added or removed.

The `send_no_attachment_alert()` wording is unchanged.

## 10. Proposed commit. Waiting for Paul's yes.

The two design documents modified before this session are **excluded**. Because the commit adds a
new test file, I will run the suite again after committing, per `CLAUDE.md`.

```
feat(alerts): reword both client alert emails and add a firm Reply-To

Step 10bq. Paul's wording for the unknown-sender and no-attachment alerts.
Reply-To is the firm record's email field, its first reader, closing item 24.
No Reply-To and no receiving address named when none can be established.

Files: worker/email/alerts.py, app.py, tests/test_alert_email_wording.py,
tests/test_step10d_pipeline.py, tests/resolution_fixtures.py,
tests/test_email_move_failures.py, 2026-10-20_REPORT_claude_code_alert_email_wording.md
Suggested branch: feat/console-phase0 (current)

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
```

**Confidence: high that both emails render as shown in section 2.** That rests on calling the real
functions with live values and printing the result. **Confidence: high that no address literal
remains in the code of `alerts.py`.** That rests on the syntax-tree enumeration in section 3, which
the guard now repeats on every run. **Confidence: medium that a client sees exactly this text.** I
have not checked how a mail client wraps lines of up to 95 characters, and no real email was sent.

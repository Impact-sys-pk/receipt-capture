# Report: sub-step 10f.35, the unknown-sender check moves above the attachment loop

**Written 2026-09-08, 12:36 BST (11:36 UTC), by the implementation session in Claude Code.**
**Branch `feat/console-phase0`. Sub-step 10f.35, amendment 274.**
**Brief: `PROMPT_claude_code_2026-09-08_unknown_sender_above_loop.md`.**

**Built. One commit, `0894f88`, and it is not pushed.**

**Paul's third option is better than either I offered, and the reason is the case neither of mine
reached.** I framed the choice as which folder a mixed email should land in. The thing that mattered
was that a stranger sending only an unsupported file heard nothing at all, and **ranking the branch
would have left that untouched**, because the format check `continue`s before the sender is ever
considered.

---

## 1. The suite

| When | Result |
|---|---|
| Before, the committed tree at `76593ba` | **678 passed, 507 subtests** |
| After, at `0894f88` | **689 passed, 518 subtests** |

**Both measured, at 12:02 and 12:33 BST.** Eleven new tests and eleven new subtests.

---

## 2. Every `move_email_to_folder()` call in `app.py`

**Five before and five after**, from the syntax tree, with each call's loop membership computed
rather than eyeballed.

**Before:**

```
5 calls
  app.py:1134: move_email_to_folder(uid, "INBOX.Unknown Sender")    inside=no loop   <- embedded
  app.py:1291: move_email_to_folder(uid, outcome_folder)            inside=no loop   <- embedded ranked
  app.py:1317: move_email_to_folder(uid, "INBOX.No Attachments")    inside=no loop
  app.py:1621: move_email_to_folder(uid, "INBOX.Unknown Sender")    inside=['att']   <- the one that moved
  app.py:1708: move_email_to_folder(uid, outcome_folder)            inside=no loop   <- attachment ranked
```

**After:**

```
5 calls
  app.py:1134: move_email_to_folder(uid, "INBOX.Unknown Sender")    inside=no loop
  app.py:1291: move_email_to_folder(uid, outcome_folder)            inside=no loop
  app.py:1317: move_email_to_folder(uid, "INBOX.No Attachments")    inside=no loop
  app.py:1583: move_email_to_folder(uid, "INBOX.Unknown Sender")    inside=no loop
  app.py:1722: move_email_to_folder(uid, outcome_folder)            inside=no loop
```

**The count is unchanged and the membership is not.** **No `move_email_to_folder()` call sits inside
either email loop any more**, which was not true of any earlier state of this code. Three sub-steps
got it there: 10f.33 took eight out of the attachment loop, and this one took the last.

---

## 3. The six combinations, before and after

**Driven rather than reasoned.** The same probe from flag 1, run against `76593ba` and against `0894f88`.
`attempts` is every move the run tried; `landed` is where the email actually ended up, since
`move_email_to_folder()` expunges and a second move of one uid cannot succeed.

| Case | Before | After |
|---|---|---|
| Known sender, two identical receipts | `Possible Duplicate`, 1 attempt | `Possible Duplicate`, 1 attempt |
| **Unknown, `.docx` only** | **`Unsupported Files`, no alert** | **`Unknown Sender`, alert sent** |
| Unknown, two supported | `Unknown Sender`, 2 attempts | `Unknown Sender`, **1 attempt** |
| Unknown, `.docx` then `.pdf` | `Unknown Sender`, 2 attempts | `Unknown Sender`, **1 attempt** |
| Unknown, `.pdf` then `.docx` | `Unknown Sender`, 2 attempts | `Unknown Sender`, **1 attempt** |
| Known sender, `.docx` then `.pdf` | `Unsupported Files`, 1 attempt | `Unsupported Files`, 1 attempt |

**One folder changed and it is the one this sub-step exists for.** Every other row keeps its
destination.

**Three rows lost a wasted move.** Before, the unknown-sender branch moved from inside the loop and
then the ranked move was attempted against an expunged uid and failed, writing a warning. Now the
email is settled before the loop and the loop is not entered at all.

**The two known-sender rows are the regression check** and both are unchanged, along with the eleven
single-item combinations `tests/test_one_ranking_both_paths.py` pins, which stayed green throughout.

---

## 4. Red before green

Six failures before the change. The two that matter:

```
FAILED ...::AStrangerIsAlwaysToldTest::test_an_unsupported_file_alone_still_reaches_unknown_sender
    AssertionError: 'INBOX.Unsupported Files' != 'INBOX.Unknown Sender'
FAILED ...::AStrangerIsAlwaysToldTest::test_an_unsupported_file_alone_still_sends_the_alert
    AssertionError: 0 != 1 : no registration alert was sent: []
```

**The second is the brief's requirement to assert the alert rather than the folder**, and it is the
one that shows the silence. A change that moved the email but left the alert inside the loop would
have passed the first and failed only this one.

The rest:

```
FAILED ...::TheEventIsLoggedOncePerEmailTest::test_one_event_for_a_two_attachment_email
    AssertionError: 2 != 1 : the event is still written per attachment
FAILED ...::TheEventIsLoggedOncePerEmailTest::test_the_event_carries_no_filename
    AssertionError: 'a.pdf' is not None
FAILED ...::TheEventIsLoggedOncePerEmailTest::test_the_event_still_exists_for_an_unsupported_only_email
    AssertionError: 0 != 1
FAILED ...::TheCheckIsAboveBothLoopsTest::test_neither_email_loop_decides_who_the_sender_is
    AssertionError: {'att': [1604]} != {}
```

**The last one names the line**, which is the whole fault in one number.

**Five tests were green throughout**, all of them regression guards: the supported-file case, both
orderings of the mixed case, and the one-alert-per-email pair.

---

## 5. One alert per email

**Three tests, because the guard has three ways to fail.**

- `test_a_two_attachment_email_sends_one_alert` drives a two-attachment email from a stranger and
  asserts exactly one alert was attempted.
- `test_one_email_alerts_row_is_recorded` asserts one `email_alerts` row, so the record matches the
  send.
- `test_a_second_poll_of_the_same_email_sends_no_second_alert` drives **two polls** of the same
  email and asserts the second sends nothing. **That is the guard's real job**: `fetch_new_messages()`
  searches `ALL` every poll, so an email whose move failed is offered again.

`has_alert_been_sent()` is untouched. Mutation C removes it and only the two-poll test notices, which
is the right shape: the other two cannot see it because within one run the alert is sent once anyway.

---

## 6. The event log's shape, which was mine to settle

**One event per email, with a null filename and a synthetic receipt id.**

**Per attachment was never right.** It wrote one row per file for a decision taken once about the
message, so a stranger sending three files produced three identical `unknown_sender` events. Above
the loop there is no filename to put in one.

**Null rather than omitted.** `_log_receipt()` writes `filename` into the entry unconditionally, so a
reader sees `"filename": null` and can tell the field was considered and found empty. A key that
simply vanished would look like a different event shape.

**The synthetic id is the established pattern rather than an invention.** `app.py`'s other two
message-level events, `unsupported_file_type` and `duplicate_skipped`, both pass `str(uuid.uuid4())`
because no receipt exists for them either. This is the third of that kind.

**What I rejected.** Dropping the event to match the embedded path, which logs none: that loses the
only record that a stranger wrote in, and the console's intake panel reads this log. It is flag 1
below instead.

---

## 7. The embedded path's own branch did not move, because it was already there

**It has been above its own loop all along**, at the point where it resolves the client, and I
checked that from the syntax tree rather than by reading: before the change, the two
`client_id == UNKNOWN_CLIENT_ID` comparisons sat at `app.py:1121`, in no loop, and `app.py:1604`,
inside `att`.

**So the same argument applies and was already satisfied.** This sub-step makes the two paths agree
rather than moving both, which is the outcome 10f.22 and 10f.33 exist for.

**The half-done mutation the brief asked for is therefore the reverse of the one it imagined**: there
is no state where the embedded path lags. Mutation A puts the attachment path's check back inside its
loop, which is the only asymmetry available, and it is caught seven times.

`test_neither_email_loop_decides_who_the_sender_is` holds both, so a future edit that pushes either
check into its loop fails.

---

## 8. The mutations

| # | Mutation | Places | Suite | Caught by |
|---|---|---|---|---|
| A | The check back inside the attachment loop | 3 hunks, 30 lines | 7 failed, 682 passed | All three `TheEventIsLoggedOncePerEmailTest`, both silent-case tests, the source guard, and the reversed test in `test_one_ranking_both_paths.py` |
| B | Move the email but never alert | 1 hunk, 2 lines | 5 failed, 684 passed | Both alert assertions and all three `OneAlertPerEmailTest` |
| C | Drop the `has_alert_been_sent()` guard | 1 hunk, 2 lines | 1 failed, 688 passed | `test_a_second_poll_of_the_same_email_sends_no_second_alert`, alone |
| D | Put a filename in the event anyway | 1 hunk, 2 lines | 1 failed, 688 passed | `test_the_event_carries_no_filename` |
| E | Drop the event entirely | 1 hunk, 2 lines | 3 failed, 686 passed | All three `TheEventIsLoggedOncePerEmailTest` |

All five restored byte for byte, asserted by the harness and confirmed with `git status`.

**Mutation B is the important one.** It is the half-done version where the folder is right and the
sender still hears nothing, which is the fault this sub-step fixes wearing a different hat. Every
folder assertion in the file passes under it.

**Mutations B and C were refused by the harness on their first run, and that is worth recording.**
The anchor was the guard line with its sixteen spaces of indentation, and **the embedded path has the
identical line four spaces further in**, so a sixteen-space string is a substring of a twenty-space
one and `str.count()` saw two. The harness stopped rather than mutating both paths at once. **That is
the check I added after making exactly this mistake on 2026-09-07**, when a `str.replace()` hit two
byte-identical blocks and I did not notice until a result did not fit. It earned its place. Both
anchors now include the unique comment above the guard.

---

## 9. Two consequences beyond the folder, both measured

**Measured at `HEAD~1` and at `HEAD` with the same probe**, a two-attachment email from a stranger:

| Statistic | Before | After |
|---|---|---|
| `review_flags_issued` | 2 | **1** |
| `attachments_processed` | 2 | **0** |

**`review_flags_issued` counted attachments for a decision taken once about the email.** One is
right, and it is what the embedded path already recorded, so this is the two paths agreeing on a
third thing.

**`attachments_processed` going to zero is the one worth a moment.** The loop is not entered at all
now, so a stranger's files are not counted as processed. **Nothing was processed, so zero is
accurate**, and the counter feeds the run summary the console shows. Recorded rather than flagged,
because the alternative reading, that two files arrived and were looked at, is the one that was
wrong.

---

## 10. Flags

### Flag 1: the embedded-image path writes no `unknown_sender` event at all

The attachment path now logs one per email. **The embedded path logs none**, and never has: its
branch sends the alert, moves the email and `continue`s without calling `_log_receipt()`.

**So a stranger who sends a photo from a share button leaves no trace in
`receipt_events_UNATTRIBUTED.ndjson`, where one who attaches a file leaves a row.** The alert and the
folder are the same on both; only the audit trail differs.

**Not fixed**, because adding an event is a new row rather than a hoist and the brief's question was
about the check's position. **Small and obviously right: one `_log_receipt()` call, identical to the
one I just wrote, in the branch four hundred lines above.** Say the word.

### Flag 2: `.env.example` is modified in the working tree and is not mine

`git status` shows it changed. The diff is a rewritten IMAP comment block describing item 173's
required settings, and one correction of `IntelliBooks\Resolutions` to `Intellibills\Resolutions`.
**I have not touched that file and have not committed it.** Raising it so nobody assumes it came with
this change.

---

## 11. My own mistakes

**One, and it is the mutation anchor in section 8**, which the harness caught before it could
mislead. I reached for the guard line and its indentation, forgot the embedded path has the same line
more deeply indented, and the substring match found two. **The refusal cost one round trip and saved
a mutation report that would have overstated what the suite caught.**

**Nothing else.** The one test I had to rewrite,
`test_an_unsupported_file_from_an_unknown_sender_is_unsupported`, was **mine from yesterday and it
pinned the fault as behaviour to preserve.** I wrote it because the brief's section 5 said that
ordering "must stay today's behaviour", and it was the wrong thing to preserve. It is now
`..._reaches_the_sender_branch` and asserts the opposite, with its class docstring rewritten to say
why.

**On the judgement I got wrong yesterday**, which this brief accepted: I measured the folder change,
carried on, and said the earlier stop would have been better. It would, and the reason is sharper now
than when I wrote it. **My flag offered two options and both were about the folder**, because I had
measured the mixed case and not the silent one. **Stopping would not only have got the decision to
Paul sooner, it would have surfaced the case I had not looked for**, which is the one that decided it.

---

## 12. What the brief got wrong

**Nothing.** Its diagnosis of the silent case, its reason for choosing position over rank, and its
prediction that the fix is small all held.

**One thing to add.** Section 4 asks whether the same argument applies to the embedded path and says
to move it in the same change if so. **It applies and needed no change**, because that path already
had its check above its loop. Section 7 shows it from the syntax tree.

---

## 13. Confidence

**High that a stranger is now always told.** It rests on the alert assertion failing before the change
with `no registration alert was sent: []` and passing after, on the six-combination table measured at
both commits, and on five mutations each with its diff.

**High that nothing else moved.** Five of the six combinations keep their folder, the eleven
single-item combinations 10f.33 pins were green throughout, and the two statistics that did change
were measured at both commits rather than reasoned about.

**High that the two paths now agree on this**, and it rests on the syntax tree showing no
unknown-sender comparison inside either loop, held by a test.

**Flag 1 is a fact rather than a judgement**, established by reading the embedded branch and by the
attachment path's event now existing where the embedded one's does not.

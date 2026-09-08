# Brief: sub-step 10f.35, the unknown-sender check moves above the attachment loop

**Written 2026-09-08 by the consultant session, on Paul's decision the same day.**
**Report to `2026-09-08_REPORT_claude_code_unknown_sender_above_loop.md` in this repository root.**

**Sub-step 10f.35 of `2026-07-25_CONSOLE_DESIGN.md`, added by amendment 274. Read it first.**

---

## 1. This corrects an error in the last brief, and the error was mine

**Your flag 1 was right and section 4 of `PROMPT_claude_code_2026-09-08_one_ranking_both_paths.md`
was wrong.** It stated as fact that leaving the unknown-sender branch unranked could never change a
folder, because `resolve_client_info()` runs once per message. **The premise is true and the
conclusion does not follow**, for the reason you gave: that branch is reached only by attachments
that got past `is_supported()` and the two duplicate checks.

**Your judgement call is also accepted as the right one on reflection.** You measured the change,
saw the folder move, and carried on because the brief was explicit. You said the earlier stop would
have been better. It would. **Nothing was lost, because the fix is small.**

**Paul has chosen a third option over the two the flag offered.**

## 2. What has to be true when you are done

**The unknown-sender check runs above the attachment loop, not inside it.**

**So any email from an address the registry does not hold reaches `INBOX.Unknown Sender` and gets the
registration alert, whatever was attached.**

**The case that decides it, and it is why neither of your two options was taken.** The format check
sits above the sender check and `continue`s, so **a stranger who sends only an unsupported file
currently gets silence**: no alert, and their email filed in `INBOX.Unsupported Files` as a format
problem. **Ranking the branch would have left that exactly as it is.** The unknown-sender alert is
the only thing an unregistered sender ever hears back, so it has to fire on that case too.

**Why above the loop rather than ranked.** Whose email this is, is a question about the email rather
than about an attachment, and `resolve_client_info(email_from)` already answers it above the loop.
**The check sitting inside the loop is where it was written rather than where it belongs.**

## 3. One detail is yours to settle, and the design deliberately does not

**The `unknown_sender` event is logged per attachment today and carries the filename.** Above the
loop there is one email and no filename.

**Choose the shape and say in the report what you chose and why.** The design document records this
as yours rather than guessing at it.

## 4. What must not change

- **`has_alert_been_sent()` still guards a second alert for one message.** One alert per email.
- **Every folder in 10f.33's ranking is untouched**, and so is the ranking itself.
- **The eleven single-item path-and-outcome combinations 10f.33 pinned must stay pinned.**
- **The embedded-image path's own unknown-sender branch.** Decide whether the same argument applies
  to it and say so either way. **If it does, do it in the same change**: the two paths agreeing is
  what 10f.22 and 10f.33 both exist for, and leaving one hoisted and one not would be a new
  divergence of exactly the kind this sub-step is cleaning up. **If it does not, say why.**
- **Section 18.2b's freeze stands.**

## 5. Out of scope

- **Item 174**, the missing `is_duplicate(message_id, att_id)` check on the embedded path.
- **Sub-step 10f.34**, the Review queue's all-clients view.
- **Your flag 2**, the `no_attachment` alert path. It is outside both loops and has nothing to rank,
  and you raised it only for completeness. Leave it.

## 6. Standard of evidence

- **Red before green**, quoted. The test that matters most is the one the old shape could not pass:
  a stranger sending only an unsupported file now lands in `INBOX.Unknown Sender` **and gets an
  alert**. Assert the alert, not only the folder.
- **Drive the same six combinations you measured for flag 1, before and after, and print the table.**
  That table is what a reader will check first, and it is the evidence that this fixed the thing it
  was written for and changed nothing else.
- **Prove one alert per email**, on a two-attachment email from a stranger.
- **Mutations from a pristine copy, each anchored to one place with its diff printed.** **Include the
  half-done one**: hoisted on the attachment path and left in the loop on the embedded path, if you
  conclude both should move.
- **Quote passes and subtests separately.**
- **Flag, do not fix. Disclose your own mistakes. State confidence and say what it rests on.**

## 7. What the report has to carry

`2026-09-08_REPORT_claude_code_unknown_sender_above_loop.md`, in this repository root.

1. Every `move_email_to_folder()` call in `app.py`, before and after, from the syntax tree.
2. The six-combination table, before and after.
3. Red output, including the alert assertion.
4. The one-alert-per-email proof.
5. What you chose for the log entry's shape, and why.
6. Whether the embedded path's own unknown-sender branch moved, and why either way.
7. The mutation results with diffs.
8. The suite, passes and subtests, measured both ends.
9. Anything you flagged, and anything this brief got wrong.

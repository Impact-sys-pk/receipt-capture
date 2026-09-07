# Brief: the embedded-image path routes its email on the outcome

**Written 2026-09-07 by the consultant session, on Paul's decision the same day.**
**Report to `2026-09-07_REPORT_claude_code_embedded_email_routing.md` in this repository root.**

---

## 1. Why this exists, and what it corrects in your own flag

**This is flag 1 of `2026-09-07_REPORT_claude_code_step10f_duplicates.md`, and it is three times
wider than that flag says.** You analysed the duplicate case and stopped there, and on the duplicate
case you were right: the earlier move expunges, so the trailing move fails and writes a warning, and
the email lands in `INBOX.Duplicates`. **Harmless, as you said.**

**The consultant session then enumerated every `move_email_to_folder()` call inside the
embedded-image loop in `app.py`. There is exactly one, and it is the duplicate branch.** There is no
move on extraction failure, none on `needs_review`, none on `possible_duplicate`. So the trailing
unconditional move catches all three of those, **and none of them is protected by the expunge,
because nothing moved the email first.**

**Where each outcome lands today:**

| Outcome | Embedded-image path | Attachment path |
|---|---|---|
| Duplicate | `INBOX.Duplicates`, plus a failed second move and a warning | `INBOX.Duplicates` |
| Extraction raised | **`INBOX.Processed Receipts`** | `INBOX.Failed Processing` |
| `needs_review` | **`INBOX.Processed Receipts`** | `INBOX.Needs Review` |
| `possible_duplicate` | **`INBOX.Processed Receipts`** | `INBOX.Possible Duplicate` |
| `ok` | `INBOX.Processed Receipts` | `INBOX.Processed Receipts` |

**Nothing is lost and this is not a data fault.** The receipt row, its `validation_status` and its
route into Review inside Intellibills are all written whatever happens here. **What is wrong is the
mailbox**, which Paul opens to see what became of each email, and which currently reports three
different failures as a success.

## 2. What has to be true when you are done

**The embedded-image path routes its email on the outcome, the way the attachment path already
does.** Four folders, the same four, with the same names.

**Copy the pattern that exists rather than inventing one.** The attachment path's routing block is
already in `app.py` and already correct. **Say why it is right rather than that it was already
there**, per `CLAUDE.md`, and in particular satisfy yourself about what it does on the exception
branch before you mirror it.

**The comment goes with the code.** It currently reads "move to Processed Receipts if all ok" and
describes a guard that is not there. Whatever the line ends up doing, the comment says that.

## 3. The one rule Paul has decided, because the two paths differ here

**One email can carry several embedded images with different outcomes.** The attachment path routes
one email on one outcome and does not face this.

**Paul's decision, 2026-09-07: the worst outcome wins.** In order, worst first:

1. extraction raised
2. `needs_review`
3. `possible_duplicate`
4. `ok`

**The reasoning, so it is not re-litigated:** a person looking in `INBOX.Failed Processing` wants to
see every email that needs them, and an email holding one good image and one failure needs them.

**The duplicate branch keeps its `continue` and its own move.** It is a per-image decision taken
before extraction and it is already correct. **Do not fold it into the ranking**, and say in the
report what happens to an email whose images are all duplicates, which is the one case where the
loop ends with no outcome to rank.

## 4. Out of scope

- **Flag 2 of your report**, the missing `is_duplicate(message_id, att_id)` check on this path. It is
  going on the outstanding items list. **Leave it alone.**
- **The attachment path.** It is the pattern, and it does not change.
- Nothing else in step 10f. Section 18.2b's freeze stands and none of `get_client_directory()`,
  `file_receipt()` or `make_enriched_sidecar()` is touched.

## 5. Standard of evidence

- **Red before green**, with the failing output quoted, per outcome. Four outcomes and the mixed
  case is five.
- **Enumerate before asserting.** Print every `move_email_to_folder()` call in `app.py` whole, before
  and after, rather than counting.
- **Mutate from a pristine copy** for anything that could not be red first, and show which tests
  catch each mutation and that no others do. **Anchor each mutation so it changes one thing:** your
  own fifth mistake in the last report was a `str.replace()` hitting two byte-identical blocks, and
  the folder-name strings in this change are a similar shape.
- **Your move stub has to model copy, flag, expunge**, which is the first mistake in your last
  report. A stub that records every call will report this change as working when it is not.
- **Flag, do not fix.** State a confidence level and say what it rests on.
- **Commit once, or once per outcome if that is cleaner. None pushed.**

## 6. What the report has to carry

`2026-09-07_REPORT_claude_code_embedded_email_routing.md`, in this repository root.

1. The enumeration of every `move_email_to_folder()` call in `app.py`, before and after, printed whole.
2. The red output per outcome.
3. The mutation results, each anchored so it changed one thing, and the proof that it did.
4. A printed table of outcome against destination folder for both paths, produced by the test rather
   than transcribed, so the two can be read side by side.
5. What happens to an email whose images are all duplicates.
6. The full suite result, before and after, measured rather than carried forward.
7. Anything you flagged, and anything this brief got wrong.

# Brief: sub-step 10f.33, one ranking on both email paths, plus the retry swap

**Written 2026-09-08 by the consultant session, on Paul's decisions the same day.**
**Report to `2026-09-08_REPORT_claude_code_one_ranking_both_paths.md` in this repository root.**

**Sub-step 10f.33 of `2026-07-25_CONSOLE_DESIGN.md`, added by amendment 269 and its ranking settled
by amendments 270 and 272. Read the sub-step before this brief.** **Plus your own flag from
`2026-09-08_REPORT_claude_code_embedded_shared_pipeline.md`, which Paul has approved.**

---

## 1. The fault

**Amendment 268 gave the embedded-image path a ranked move after its loop. The attachment path has
no ranking at all.** Its routing block sits **inside** its loop, and `move_email_to_folder()` in
`worker/email/reader.py` copies, flags `\Deleted` and calls `expunge()`, so the uid is gone after the
first move and every later move of that email fails.

**So on a two-item email the first outcome wins on one path and the worst outcome wins on the other.**
That is the two paths disagreeing, in the opposite direction from the agreement 10f.22 established,
and your own 10f.32 report measured it: two identical receipts in one email give
`['ok', 'possible_duplicate']` on both paths, landing in `INBOX.Processed Receipts` on the attachment
path and `INBOX.Possible Duplicate` on the embedded one.

## 2. What has to be true when you are done

**One ranking, stated once, used by both email paths, applied after the loop.**

**Paul's ranking, worst first, and every part of it is his decision:**

| Rank | Outcome | Folder |
|---|---|---|
| 1 | `unsupported` | `INBOX.Unsupported Files` |
| 2 | `failed` | `INBOX.Failed Processing` |
| 3 | `needs_review` | `INBOX.Needs Review` |
| 4 | `possible_duplicate` | `INBOX.Possible Duplicate` |
| 5 | `ok` | `INBOX.Processed Receipts` |
| 6 | `duplicate` | `INBOX.Duplicates` |

**Two of those ranks were decided rather than derived and the reasoning belongs where the table is.**

**`duplicate` is last, below `ok`. Paul, 2026-09-08.** A hash duplicate means the receipt is already
held, so it is the most benign state in the set: an email carrying one duplicate and one filed
receipt has both accounted for, and `INBOX.Processed Receipts` is a true statement about it while
`INBOX.Duplicates` is not. **An email whose every item was a duplicate still lands in
`INBOX.Duplicates`**, because `duplicate` is then the only outcome to rank.

**`unsupported` is first, above `failed`. Paul, 2026-09-08.** An unsupported file is a wrong-format
problem with one fix, telling the client to send a photo or a PDF, and that conversation attaches to
the email whatever else happened in it. A failed extraction is a per-receipt problem. **Keeping the
two apart is worth more than ranking them by urgency.**

**Note that the table is not a list of `validation_status` values.** `ok`, `needs_review`, `failed`
and `possible_duplicate` are statuses; `unsupported` and `duplicate` are decisions taken before any
extraction exists. **Say so where the table is**, so nobody later tries to derive one from the other.

## 3. What changes on each path

### The attachment path

**Its four-branch routing block moves out of the loop and becomes one ranked move after it**, which
is the shape the embedded path already has.

**Every branch that currently moves the email and continues instead records an outcome and
continues.** From reading the loop, those are: the unsupported-file branch, the already-handled
attachment branch, the hash-duplicate branch, and the `except` branch. **The two duplicate branches
both record `duplicate`.**

### The embedded-image path

**Its duplicate branch stops moving the email immediately and records `duplicate` instead**, so the
ranking decides rather than the order the images happen to arrive in. **This is flag 2 of
`2026-09-07_REPORT_claude_code_embedded_email_routing.md`**, which you raised and which this
sub-step subsumes.

### Both

**One helper and one table, not two of each.** `_worst_outcome_folder()` and
`EMAIL_OUTCOME_FOLDERS` already exist in `app.py` from amendment 268. **Extend them; do not write a
second pair.** `None` keeps both its meanings, being nothing to rank and an outcome the table does
not name, and the docstring already states them.

## 4. The unknown-sender branch stays exactly as it is, and the report has to prove that is a no-op

**Do not rank it.** `resolve_client_info(email_from)` runs **once per message, above the loop**, so
every attachment in one email gets the same answer and ranking it could never change a folder.

**Show that rather than asserting it**: a test driving a two-attachment email from an unknown sender,
asserting the email lands in `INBOX.Unknown Sender` and that the ranked move was not made. **After
the change the outcome list is empty in that case and `_worst_outcome_folder([])` returns `None`**,
which is the same shape as the all-duplicates case.

## 5. One ordering case to test, because it exists today and must not change

**The unsupported branch comes before the unknown-sender branch in the loop.** So an unknown sender
who sends a `.docx` records `unsupported` and never reaches the unknown-sender branch, and no alert
is sent. **That is today's behaviour under first-wins and it must stay today's behaviour under the
ranking.** Pin it.

## 6. The retry swap, which is not part of 10f.33

**Your flag, approved by Paul on 2026-09-08.** The embedded-image path is the only one of the four
that calls `extractor.extract()` directly. The other three use `extract_with_transient_retry()`.
**Swap it.** Both are already imported in `app.py`.

**It is in this brief rather than its own because it is a two-line edit already agreed**, which
`CLAUDE.md` says goes on no list. **It gets its own commit** so it is separable from the ranking.

**Report it under its own heading**, and say what a transient failure now does on that path that it
did not do before.

## 7. Out of scope

- **Item 174**, the missing `is_duplicate(message_id, att_id)` check on the embedded path. Still absent.
- **Sub-step 10f.34**, the Review queue's all-clients view. Not this brief and it comes after 10f.15.
- The folder-intake and auto-retry paths. Neither moves an email.
- **Section 18.2b's freeze stands.**

## 8. Standard of evidence

- **Red before green**, quoted, per path and per outcome.
- **The main risk of this change is a regression in what already works**, because the attachment
  path's routing has been correct for every single-attachment email since before any of this. **Drive
  every outcome down both paths as a single-item email and show the folder is unchanged**, then drive
  the multi-item cases.
- **Print one table of outcome against folder for both paths, single-item and multi-item**, produced
  by the test rather than transcribed. That table is the deliverable a reader will check first.
- **Mutations from a pristine copy, each anchored to one place with its diff printed.** **Include the
  half-done one**: rank on one path and leave the other moving inside its loop, which is what the
  system looks like today and is the state this sub-step exists to end.
- **Quote passes and subtests separately.** Both your last two findings came from a subtest count
  moving.
- **Flag, do not fix. Disclose your own mistakes. State confidence and say what it rests on.**

## 9. What the report has to carry

`2026-09-08_REPORT_claude_code_one_ranking_both_paths.md`, in this repository root.

1. Every `move_email_to_folder()` call in `app.py`, before and after, from the syntax tree.
2. The outcome-to-folder table for both paths, single-item and multi-item.
3. Red output per path and per outcome.
4. The mutation results with diffs, including the half-done one.
5. The unknown-sender no-op proof, and the unsupported-before-unknown-sender ordering case.
6. The retry swap under its own heading, with its own commit named.
7. The suite, passes and subtests, measured both ends.
8. Anything you flagged, and anything this brief got wrong.

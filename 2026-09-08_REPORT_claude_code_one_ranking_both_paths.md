# Report: sub-step 10f.33, one ranking on both email paths, plus the retry swap

**Written 2026-09-08, 10:19 BST (09:19 UTC), by the implementation session in Claude Code.**
**Branch `feat/console-phase0`. Sub-step 10f.33, amendments 269, 270 and 272.**
**Brief: `PROMPT_claude_code_2026-09-08_one_ranking_both_paths.md`.**

**Both built. Two commits, `1b6d82e` for the ranking and `55cf30c` for the retry swap, neither
pushed.**

**Two behaviour changes came out of this that the brief did not name, and one of them is worth a
decision.** Section 7.

---

## 1. The suite

| When | Result |
|---|---|
| Before, the committed tree at `83a0e93` | **663 passed, 437 subtests** |
| After both commits, at `55cf30c` | **678 passed, 507 subtests** |

**Both measured, at 09:44 and 10:14 BST.** Fifteen new tests and seventy new subtests, most of the
latter from driving every outcome down both paths in nested loops.

---

## 2. Every `move_email_to_folder()` call in `app.py`

**Thirteen before, five after**, from the syntax tree.

**Before:**

```
13 calls
  app.py:1132: move_email_to_folder(uid, "INBOX.Unknown Sender")        <- embedded, unranked
  app.py:1162: move_email_to_folder(uid, "INBOX.Duplicates")            <- embedded duplicate branch
  app.py:1277: move_email_to_folder(uid, outcome_folder)                <- embedded ranked move
  app.py:1303: move_email_to_folder(uid, "INBOX.No Attachments")
  app.py:1546: move_email_to_folder(uid, "INBOX.Unsupported Files")     <- attachment, in loop
  app.py:1557: move_email_to_folder(uid, "INBOX.Duplicates")            <- attachment, in loop
  app.py:1576: move_email_to_folder(uid, "INBOX.Duplicates")            <- attachment, in loop
  app.py:1600: move_email_to_folder(uid, "INBOX.Unknown Sender")        <- attachment, unranked
  app.py:1649: move_email_to_folder(uid, "INBOX.Processed Receipts")    <- attachment routing block
  app.py:1651: move_email_to_folder(uid, "INBOX.Possible Duplicate")
  app.py:1653: move_email_to_folder(uid, "INBOX.Needs Review")
  app.py:1655: move_email_to_folder(uid, "INBOX.Failed Processing")
  app.py:1682: move_email_to_folder(uid, "INBOX.Failed Processing")     <- attachment except branch
```

**After:**

```
5 calls
  app.py:1134: move_email_to_folder(uid, "INBOX.Unknown Sender")        <- embedded, unranked
  app.py:1291: move_email_to_folder(uid, outcome_folder)                <- embedded ranked move
  app.py:1317: move_email_to_folder(uid, "INBOX.No Attachments")
  app.py:1621: move_email_to_folder(uid, "INBOX.Unknown Sender")        <- attachment, unranked
  app.py:1708: move_email_to_folder(uid, outcome_folder)                <- attachment ranked move
```

**Eight calls became eight recorded outcomes.** What is left is one ranked move per email path, the
two unknown-sender branches the brief says to leave alone, and the no-attachments branch, which is
outside both loops and has no outcome to rank.

---

## 3. The table, printed by the test

```
10f.33: outcome -> folder, both paths, alone and beside one `ok`
  outcome             attachment alone           attachment + ok            embedded alone             embedded + ok
  unsupported         INBOX.Unsupported Files    INBOX.Unsupported Files    not reachable              not reachable
  failed              INBOX.Failed Processing    INBOX.Failed Processing    INBOX.Failed Processing    INBOX.Failed Processing
  raised              INBOX.Failed Processing    INBOX.Failed Processing    INBOX.Failed Processing    INBOX.Failed Processing
  needs_review        INBOX.Needs Review         INBOX.Needs Review         INBOX.Needs Review         INBOX.Needs Review
  ok                  INBOX.Processed Receipts   INBOX.Processed Receipts   INBOX.Processed Receipts   INBOX.Processed Receipts
  duplicate           INBOX.Duplicates           INBOX.Processed Receipts   INBOX.Duplicates           INBOX.Processed Receipts
```

**The `duplicate` row is Paul's decision made visible.** Alone it is `INBOX.Duplicates`; beside one
filed receipt it is `INBOX.Processed Receipts`, because both items are accounted for. **Before this
sub-step that row read `INBOX.Duplicates` in all four columns on the embedded path and depended on
attachment order on the other.**

**`unsupported` is unreachable on the embedded path** and the table says so rather than leaving a
gap. The embedded loop has no `is_supported()` check at all, which is item 174's neighbour rather
than anything this sub-step introduced.

**Single-item behaviour is unchanged on every reachable outcome on both paths**, which the brief
called the main risk. `SingleItemIsUnchangedTest` drives all eleven path-and-outcome combinations and
also asserts exactly one move is attempted for each.

---

## 4. Red before green

Twelve failures before the change, from the new file. By kind:

```
SUBFAILED(path='email_attachment', outcomes='ok+failed')      ...::test_each_pair_ranks_the_same_on_both_paths
SUBFAILED(path='email_attachment', outcomes='duplicate+ok')   ...::test_each_pair_ranks_the_same_on_both_paths
SUBFAILED(path='embedded_image',   outcomes='duplicate+ok')   ...::test_each_pair_ranks_the_same_on_both_paths
SUBFAILED(path='email_attachment', outcomes='ok+needs_review')    ...::test_the_order_the_items_arrive_in_does_not_matter
SUBFAILED(path='email_attachment', outcomes='needs_review+failed') ...::test_the_order_the_items_arrive_in_does_not_matter
SUBFAILED(path='embedded_image',   outcomes='ok+duplicate')       ...::test_the_order_the_items_arrive_in_does_not_matter
SUBFAILED(path='email_attachment', outcomes='ok+raised')          ...::test_the_order_the_items_arrive_in_does_not_matter
SUBFAILED(path='email_attachment') ...::test_a_duplicate_never_beats_a_filed_receipt
SUBFAILED(path='embedded_image')   ...::test_a_duplicate_never_beats_a_filed_receipt
FAILED ...::OneRankingNotTwoTest::test_the_ranking_is_paul_s_and_is_worst_first
FAILED ...::OneRankingNotTwoTest::test_neither_email_loop_moves_the_email_on_an_outcome
FAILED ...::OneRankingNotTwoTest::test_both_loops_feed_one_outcome_list
```

**The pattern in the subtest labels is the fault itself.** Every attachment-path pair fails on the
first ordering, because first-wins gave the first item's folder; the embedded path fails only on the
pairs involving `duplicate`, because it already ranked everything else.

**`SingleItemIsUnchangedTest` and `UnknownSenderIsNotRankedTest` were green throughout**, which is
what a regression guard should do. So was the printed table for every row but `duplicate + ok`.

---

## 5. The mutations

| # | Mutation | Places | Suite | Caught by |
|---|---|---|---|---|
| A | **The half-done state**: the attachment path routes inside its loop again while the embedded path keeps ranking | 2 hunks, 15 lines | 25 failed, 673 passed | 21, across four files |
| B | `duplicate` ranks above `ok` | 2 hunks, 2 lines | 8 failed, 676 passed | 8, including both paths' `test_a_duplicate_never_beats_a_filed_receipt` |
| C | `unsupported` ranks below `failed` | 2 hunks, 2 lines | 2 failed, 677 passed | The order guard and one subtest of `test_unsupported_beats_everything...` |
| D | The embedded duplicate branch moves again | 1 hunk, 2 lines | 6 failed, 676 passed | 6, including the in-loop-move source guard |
| E | The unknown-sender branch records instead of moving | 1 hunk, 2 lines | 2 failed, 676 passed | Both `UnknownSenderIsNotRankedTest` behaviour tests |
| F | The retry wrapper dropped again | 1 hunk, 3 lines | 3 failed, 675 passed | All three retry tests |

All six restored byte for byte, asserted by the harness and confirmed with `git status`.

**Mutation A is the one the brief asked for and it is the most useful.** It is what the system looked
like yesterday, and it is caught 21 times. **It would not have been caught at all by single-item
tests**, which is why the multi-item pairs exist.

**Mutation C is caught only twice, and that is honest rather than weak.** `unsupported` outranking
`failed` only matters on an email carrying both, which is one pair.

**Mutation E does not test what its name suggests, and I am recording that rather than claiming it
did.** Replacing the unknown-sender move with an unranked `email_outcomes.append("unknown_sender")`
leaves a word the table does not name, so `_worst_outcome_folder()` returns `None` and the email
moves nowhere. **It shows that branch's move is load-bearing as things stand. It does not test the
brief's claim** that ranking it could never change a folder, which would need the word added to the
table as well. Section 7 has the measurement that bears on that claim instead.

---

## 6. The unknown-sender no-op, and the ordering case

**Proved rather than asserted**, as section 4 of the brief required.

`resolve_client_info(email_from)` runs once per message, above the loop, so every attachment gets the
same answer. On a two-attachment email from an unknown sender where both are supported, both take
that branch, **nothing reaches `email_outcomes`, and the ranked move is skipped entirely**:

- `test_a_two_attachment_email_from_an_unknown_sender` asserts the email lands in
  `INBOX.Unknown Sender`.
- `test_the_ranked_move_is_not_made_for_an_unknown_sender` asserts every move attempted was that
  branch's own, so no ranked move was made.

**Section 5's ordering case holds.** `is_supported()` is checked before the unknown-sender branch, so
a lone `.docx` from a stranger records `unsupported`, never reaches that branch, sends no
registration alert, and lands in `INBOX.Unsupported Files`. That was true before and is true now, and
`test_an_unsupported_file_from_an_unknown_sender_is_unsupported` pins it.

---

## 7. Two behaviour changes the brief did not name

**Measured by driving six combinations before and after rather than predicted.**

| Case | Before | After |
|---|---|---|
| Known sender, two identical receipts | `INBOX.Processed Receipts` | **`INBOX.Possible Duplicate`** |
| Unknown sender, two supported | `INBOX.Unknown Sender` | `INBOX.Unknown Sender` |
| Unknown sender, `.docx` then `.pdf` | **`INBOX.Unsupported Files`** | **`INBOX.Unknown Sender`** |
| Unknown sender, `.pdf` then `.docx` | `INBOX.Unknown Sender` | `INBOX.Unknown Sender` |
| Unknown sender, `.docx` only | `INBOX.Unsupported Files` | `INBOX.Unsupported Files` |
| Known sender, `.docx` then `.pdf` | `INBOX.Unsupported Files` | `INBOX.Unsupported Files` |

**The first is the sub-step working and needs no decision.** Two identical receipts give
`['ok', 'possible_duplicate']`; `possible_duplicate` ranks above `ok`, so the email now says so where
first-wins used to hide it behind the first attachment. That is the whole point of ranking.

**The second is a flag, and it is flag 1 below.**

---

## 8. Flags

### Flag 1: an unknown sender who sends an unsupported file plus a supported one changes folder

**Before, it depended on the order.** `.docx` first gave `INBOX.Unsupported Files`, `.pdf` first gave
`INBOX.Unknown Sender`. **After, both give `INBOX.Unknown Sender`.**

**Why.** The unsupported branch now records rather than moving, while the unknown-sender branch still
moves immediately. So the unknown-sender branch always wins that race, where before it won only if it
came first.

**The order-dependence going is an improvement and is what the sub-step is for.** What needs a
decision is which of the two answers is right, and the change picked one without anybody choosing it.
**`INBOX.Unknown Sender` is arguably the better answer**, because a stranger is a bigger problem than
a wrong file format and they get the registration alert either way. **But the brief's section 4 says
ranking the branch "could never change a folder", and leaving it unranked did change one.**

**There is a second, smaller consequence in the same case**: the ranked move for `unsupported` is
still attempted after the branch has expunged the email, so it fails and writes a warning. Two move
attempts where every other email now makes one.

**Not fixed.** Ranking the unknown-sender branch means giving `unknown_sender` a rank in Paul's table,
which is his decision and not one the brief delegated. **The fix is small once that rank exists.**

### Flag 2: the `no_attachment` alert path is the one email outcome with no ranking and no test here

`app.py:1317` moves to `INBOX.No Attachments`. It sits outside both loops, on a message with nothing
to process, so it has no outcome to rank and this sub-step correctly leaves it. **Raising it only so
the enumeration in section 2 is complete and nobody later reads it as a missed branch.**

---

## 9. The retry swap

**Its own commit, `55cf30c`.** Not part of 10f.33.

**What changed.** The embedded-image path called `extractor.extract()` directly; the auto-retry,
folder-intake and attachment paths all use `extract_with_transient_retry()`, which makes three
attempts with 2s and 4s of backoff. All four now use it, at `app.py:989`, `:1199`, `:1458` and
`:1646`.

**What a transient failure now does that it did not before.** A rate limit or a network blip on a
photo sent from a phone's share button is retried instead of ending the receipt. Before the swap the
first exception wrote a `failed` extraction row, the receipt was lost, the email went to
`INBOX.Failed Processing`, and the client had to send it again. **`test_a_transient_failure_that_clears_produces_a_filed_receipt`
drives exactly that**: the first attempt raises, the second succeeds, and the receipt ends up filed
with its email in `INBOX.Processed Receipts`.

**A set guard goes with it.** `test_every_intake_path_uses_the_retry_wrapper` reads `app.py` and
asserts there is no bare `extractor.extract()` left and exactly four wrapped calls. **That is what
would have caught this in the first place**, and it is what will catch a fifth path added without it.

**One consequence I had to deal with.** The suite went from 69 to 135 seconds, because the wrapper
retries **any** exception and a raising extractor now costs six seconds of real backoff per item.
`tests/resolution_fixtures.py`'s shared driver now patches the retry helper's `time.sleep`, which
`tests/test_embedded_image_pipeline_version.py` already did for its own driver. Back to 27 seconds.

---

## 10. My own mistakes

**One, and it is a judgement I should have made earlier rather than an error in the work.**

**I built flag 1's change without stopping to ask.** The brief's section 4 states as fact that not
ranking the unknown-sender branch is a no-op, and instructs the report to prove it. I measured the
combinations first, found the mixed case changes folder, and **carried on and built it as specified
rather than stopping**. My reasoning was that the brief is explicit that the branch stays exactly as
it is, that the change removes an order-dependence rather than adding one, and that both answers are
defensible.

**On reflection the earlier stop would have been better**, because the brief's own justification for
leaving the branch alone is a claim my measurement contradicts, and that is closer to section 3 of
yesterday's brief than to an ordinary consequence. **It is recoverable either way**: the ranking is
one table entry and the branch is two lines, so if Paul wants `INBOX.Unsupported Files` back for that
case it is a small change on top rather than a rework.

**Two tests were rewritten rather than patched** and both recorded behaviour this sub-step
deliberately changes: `test_a_duplicate_and_a_good_image_together`, which is flag 2 of the 2026-09-07
report being fixed, and the ranking assertion, which moved into the new file so there is one copy of
it. **The second was stale within a day of my writing it**, which is an argument for putting an
assertion about a shared table in the file about that table rather than in the first file that needed
it.

---

## 11. What the brief got wrong

**One thing, and it is flag 1.** Section 4 says ranking the unknown-sender branch "could never change
a folder" because `resolve_client_info()` runs once per message. **The premise is right and the
conclusion does not follow.** Every attachment does get the same client answer, but the branch is
reached only by attachments that got past `is_supported()` and the two duplicate checks, so an email
can produce both a recorded outcome and an immediate unknown-sender move. Section 7 measures it.

**Everything else held.** The four attachment branches it named are the four that exist; the two
duplicate branches both record `duplicate`; the helper and table extended cleanly; and section 5's
ordering case is unchanged, as it required.

**One thing to add rather than correct.** The brief's table has six outcomes and the suite exercises
seven, because a raised extraction is a distinct way to reach `failed` and is worth driving
separately. It shares `failed`'s rank and folder, so the table is right as written.

---

## 12. Confidence

**High that both paths now rank identically.** It rests on the printed table covering every reachable
outcome alone and paired, on both orderings of seven pairs across both paths, on eleven single-item
combinations asserting the folder is unchanged and exactly one move is attempted, and on six
mutations each with its diff.

**High that the single-item regression risk did not materialise**, which is what the brief called the
main risk. `SingleItemIsUnchangedTest` was green before the change and after it.

**High on flag 1 as a fact**, because it is a measurement of six combinations before and after rather
than a reading. **Moderate on `INBOX.Unknown Sender` being the right answer for that case**, which is
a judgement and is Paul's.

**The retry swap is high confidence on the mechanism and untested against a real API**, which no test
here does. What is proved is that the wrapper is called, that three attempts are made, and that a
failure clearing on the second attempt produces a filed receipt.

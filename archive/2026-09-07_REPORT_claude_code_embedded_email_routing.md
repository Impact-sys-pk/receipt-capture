# Report: the embedded-image path routes its email on the outcome

**Written 2026-09-07, 20:52 BST (19:52 UTC), by the implementation session in Claude Code.**
**Branch `feat/console-phase0`.**
**Brief: `PROMPT_claude_code_2026-09-07_embedded_email_routing.md`.**

**Built. One commit, `fde50b6`, and it is not pushed.**

**Your correction to my flag is accepted and it was the substance of the job.** I analysed the
duplicate case, found it harmless, and stopped. The three outcomes with no earlier move were the
whole defect, and I did not look for them.

---

## 1. The suite

| When | Result |
|---|---|
| Before, the committed tree at `856d495` | **639 passed, 408 subtests** |
| After, at `fde50b6` | **653 passed, 425 subtests** |

**Both measured, at 20:04 and 20:38 BST.** The 14 new tests are the new file. **The 17 extra subtests
are not all mine and the arithmetic matters**, because chasing the difference is what found the
second finding in section 7: 408 − 81 + 90 + 8 = 425.

---

## 2. Every `move_email_to_folder()` call in `app.py`

**Thirteen before and thirteen after**, enumerated from the AST rather than grepped, so a call inside
a comment or a string cannot pad the list.

**Before:**

```
13 calls
  app.py:1086: move_email_to_folder(uid, "INBOX.Unknown Sender")
  app.py:1113: move_email_to_folder(uid, "INBOX.Duplicates")            <- embedded loop
  app.py:1209: move_email_to_folder(uid, "INBOX.Processed Receipts")    <- the unconditional one
  app.py:1235: move_email_to_folder(uid, "INBOX.No Attachments")
  app.py:1478: move_email_to_folder(uid, "INBOX.Unsupported Files")
  app.py:1489: move_email_to_folder(uid, "INBOX.Duplicates")
  app.py:1508: move_email_to_folder(uid, "INBOX.Duplicates")
  app.py:1532: move_email_to_folder(uid, "INBOX.Unknown Sender")
  app.py:1581: move_email_to_folder(uid, "INBOX.Processed Receipts")    <- attachment path routing
  app.py:1583: move_email_to_folder(uid, "INBOX.Possible Duplicate")
  app.py:1585: move_email_to_folder(uid, "INBOX.Needs Review")
  app.py:1587: move_email_to_folder(uid, "INBOX.Failed Processing")
  app.py:1614: move_email_to_folder(uid, "INBOX.Failed Processing")     <- attachment exception branch
```

**After:**

```
13 calls
  app.py:1132: move_email_to_folder(uid, "INBOX.Unknown Sender")
  app.py:1162: move_email_to_folder(uid, "INBOX.Duplicates")            <- embedded loop, unchanged
  app.py:1276: move_email_to_folder(uid, outcome_folder)                <- the change
  app.py:1302: move_email_to_folder(uid, "INBOX.No Attachments")
  app.py:1545: move_email_to_folder(uid, "INBOX.Unsupported Files")
  app.py:1556: move_email_to_folder(uid, "INBOX.Duplicates")
  app.py:1575: move_email_to_folder(uid, "INBOX.Duplicates")
  app.py:1599: move_email_to_folder(uid, "INBOX.Unknown Sender")
  app.py:1648: move_email_to_folder(uid, "INBOX.Processed Receipts")
  app.py:1650: move_email_to_folder(uid, "INBOX.Possible Duplicate")
  app.py:1652: move_email_to_folder(uid, "INBOX.Needs Review")
  app.py:1654: move_email_to_folder(uid, "INBOX.Failed Processing")
  app.py:1681: move_email_to_folder(uid, "INBOX.Failed Processing")
```

**One line changed, and the count is the same** because the unconditional move became a conditional
one rather than being joined by three siblings. The folder names live in `EMAIL_OUTCOME_FOLDERS`.

---

## 3. Why the attachment path's pattern is right, and what I checked on the exception branch

**You asked me to satisfy myself rather than copy it, and one thing needed establishing.**

The attachment path routes on the `status` returned by `process_extraction_result()`, with four
branches and **no `else`**. Separately, its `except` block moves to `INBOX.Failed Processing`.

**So an extraction that raised and one that validated as `failed` go to the same folder, and that is
correct rather than a coincidence.** The exception branch writes an extraction row with
`validation_status="failed"`, so the two cases are one thing in the database and one thing to the
person opening the mailbox: the document could not be read. **My table therefore has one `failed`
entry and the raise maps onto it**, which is why `embedded_outcomes.append("failed")` sits in the
exception branch using the same word the row records.

**The missing `else` is deliberate and I mirrored it.** An unrecognised status moves nothing, so the
email stays in INBOX and is offered again next poll rather than being filed somewhere wrong.
`_worst_outcome_folder()` returns `None` in the same case, and its docstring says so.

**The comment goes with the code.** The old one claimed "if all ok" and guarded nothing. The new
block says what it does, why the line changed, and what `None` means.

---

## 4. Red before green, per outcome

**Twelve failures before the change**, from the new file. Per outcome:

```
FAILED ...::EmbeddedPathRoutesOnTheOutcomeTest::test_needs_review_goes_to_needs_review
    'INBOX.Processed Receipts' != 'INBOX.Needs Review'
FAILED ...::EmbeddedPathRoutesOnTheOutcomeTest::test_a_failed_validation_goes_to_failed_processing
    'INBOX.Processed Receipts' != 'INBOX.Failed Processing'
FAILED ...::EmbeddedPathRoutesOnTheOutcomeTest::test_an_extraction_that_raised_goes_to_failed_processing
    'INBOX.Processed Receipts' != 'INBOX.Failed Processing'
```

The mixed case, all four red:

```
FAILED ...::TheWorstOutcomeWinsTest::test_one_good_image_and_one_failure_goes_to_failed_processing
FAILED ...::TheWorstOutcomeWinsTest::test_the_order_the_images_arrive_in_does_not_matter
FAILED ...::TheWorstOutcomeWinsTest::test_needs_review_beats_ok
FAILED ...::TheWorstOutcomeWinsTest::test_a_failure_beats_needs_review
FAILED ...::TheWorstOutcomeWinsTest::test_the_ranking_is_stated_once_and_is_worst_first
```

The all-duplicates case, showing the second move being attempted:

```
FAILED ...::AllImagesDuplicateTest::test_the_email_lands_in_duplicates_and_moves_no_further
E   AssertionError: Lists differ: ['INBOX.Duplicates', 'INBOX.Processed Receipts'] != ['INBOX.Duplicates']
```

And the side-by-side table, which is the clearest statement of the defect:

```
SUBFAILED(outcome='needs_review') : the two paths disagree on needs_review:
    {'email_attachment': 'INBOX.Needs Review', 'embedded_image': 'INBOX.Processed Receipts'}
SUBFAILED(outcome='failed')       : {'email_attachment': 'INBOX.Failed Processing', 'embedded_image': 'INBOX.Processed Receipts'}
SUBFAILED(outcome='raised')       : {'email_attachment': 'INBOX.Failed Processing', 'embedded_image': 'INBOX.Processed Receipts'}
```

**`ok` was green throughout, as it should have been**, and
`test_the_email_is_moved_exactly_once` was green too: before the change each single-image email made
exactly one move, the trailing one. **It is a guard for the new shape rather than a red-first test**,
and mutation B below is what shows it earns its place.

---

## 5. The mutations, each anchored to one place with the proof printed

**Every mutation printed its own unified diff**, so "it changed one thing" is shown rather than
claimed. This is your instruction and it comes from my fifth mistake in the last report, where a
`str.replace()` hit two byte-identical blocks and I did not notice until a result did not fit.

| # | Mutation | Places changed | Suite | Caught by |
|---|---|---|---|---|
| A | Back to the unconditional move | 1 hunk, 4 lines | 11 failed, 645 passed | 8 tests plus 3 subtests of the side-by-side table |
| B | Route **and** keep the trailing move | 1 hunk, 1 line | 6 failed, 651 passed | Both `AllImagesDuplicateTest` tests and all 4 subtests of `test_the_email_is_moved_exactly_once` |
| C | Rank best first instead of worst first | 2 hunks, 6 lines | 5 failed, 648 passed | All five `TheWorstOutcomeWinsTest` tests |
| D | Stop recording the raised outcome | 1 hunk, 3 lines | 5 failed, 650 passed | `test_an_extraction_that_raised...`, both order tests, and the `raised` subtests of the table and the move count |
| E | Stop recording the validated outcome | 1 hunk, 1 line | 14 failed, 645 passed | 7 tests plus 6 subtests, and `test_step10f_duplicates.py`'s four-route control |
| F | Move even when there is nothing to rank | 1 hunk, 2 lines | 1 failed, 652 passed | `test_the_email_lands_in_duplicates_and_moves_no_further` |

**Mutation B is the one that justifies the faithful move stub, exactly as you said it would.** It is
the plausible half-done version: routing added, old line left behind. **Every folder assertion still
passes**, because the first move wins and the second fails silently. Only the tests that count
attempts see it. A stub that recorded every call and reported success would have made this mutation
invisible **and** would have made the real change look broken, which is the two-way error my last
report's first mistake was.

**Mutation E reached outside the new file**, failing `test_step10f_duplicates.py`'s
`test_all_four_routes_process_a_document_that_is_not_a_duplicate`. That is correct: with no outcome
recorded, the embedded email never moves, and that control asserts all four routes process a fresh
document.

All six restored byte for byte, asserted by the harness and confirmed with `git status`.

---

## 6. Outcome against destination, both paths, produced by the test

Printed by `BothPathsAgreeTest`, which drives each outcome down each path in its own environment:

```
outcome -> folder, driven down both email paths:
  outcome          attachment path            embedded-image path
  ok               INBOX.Processed Receipts   INBOX.Processed Receipts
  needs_review     INBOX.Needs Review         INBOX.Needs Review
  failed           INBOX.Failed Processing    INBOX.Failed Processing
  raised           INBOX.Failed Processing    INBOX.Failed Processing
```

**`possible_duplicate` is absent from the table and that is a finding rather than an omission.** It
cannot arise on the embedded-image path at all, for the reason in flag 1 below: that path never calls
`process_extraction_result()`, so the semantic duplicate check never runs on it. **It is still in
`EMAIL_OUTCOME_FOLDERS`**, at rank 3 as you decided, because the ranking is a decision about outcomes
rather than about which path can currently produce them, and a test asserts its folder is
`INBOX.Possible Duplicate`.

### An email whose images are all duplicates

**It lands in `INBOX.Duplicates` and nothing else is attempted.** Each image takes the duplicate
branch, which moves the email itself and `continue`s, so the loop ends with an empty outcome list,
`_worst_outcome_folder([])` returns `None` and no move is made.
`test_the_email_lands_in_duplicates_and_moves_no_further` asserts the attempt list is exactly
`["INBOX.Duplicates"]`, so a regression that reinstated the trailing move fails here even though the
email would still be in the right place. Mutation F is that regression, and it is caught.

**A mixed email, one duplicate and one good image, lands in `INBOX.Duplicates` too**, and that is
flag 2.

---

## 7. Flags

### Flag 1: the embedded-image path does not use the shared pipeline at all

**This is much larger than the routing and it is why the routing was worth doing.** The embedded
loop calls `extractor.extract()`, `validate()`, `save_extraction()` and `mark_processed()`. It does
**not** call `process_extraction_result()`, which the other three intake paths all call.

Established by bounding the loop and testing for each name, then confirmed by running one good
receipt down each email path and reading the database:

```
--- embedded_image ---            --- email_attachment ---
  receipts        1                 receipts        1
  status          'ok'              status          'ok'
  filed_path      None              filed_path      ...\Clients\Test Client\IntelliBooks\Receipts\2025-26\...
  extractions     1                 extractions     1
  categorisations 0                 categorisations 1
```

**A receipt that arrives as an embedded image is never filed into the client folder and never
categorised.** It is `status = ok` in the database with `filed_path` NULL. Three consequences follow
from that NULL, all of them by reading the code rather than guessed:

- **It never reaches IntelliBooks**, which reads the client folder.
- **It can never be a duplicate that blocks anything**, because every caller of `find_by_hash()`
  pairs it with `is_recorded_and_filed()`, so the same image sent twice is extracted twice, at one
  OpenAI call each.
- **`possible_duplicate` cannot be raised against it or by it**, because
  `find_by_transaction_loose()` requires `r.filed_path IS NOT NULL`.

**Not fixed, and not close to in scope.** Making this path call the shared pipeline is a behaviour
change with a design decision inside it, and it is a step of its own rather than a flag to act on quietly. **What this
brief's change does do is make the mailbox honest about the validation outcome**, which is worth
having on its own and is a prerequisite for noticing this at all.

**One thing to weigh, and it cuts against my change slightly:** an embedded image that validates `ok`
now goes to `INBOX.Processed Receipts` while not having been filed. That was true before as well, so
nothing got worse, but "Processed Receipts" is a stronger claim than the pipeline can currently back
on this path.

### Flag 2: the duplicate branch pre-empts the ranking on a mixed email

An email carrying one duplicate image and one good image lands in `INBOX.Duplicates`, because the
duplicate branch moves the email the moment it decides, and the expunge means the ranked move at the
end cannot take effect. **So the duplicate outcome wins by being first rather than by being worst.**

**This is your brief's design and I have implemented it as written**, since the duplicate branch is a
per-image decision taken before extraction and you said not to fold it into the ranking. It is
recorded in `test_a_duplicate_and_a_good_image_together`, which asserts both the landing folder and
that the ranked move was attempted and failed, so the behaviour is known rather than discovered.

**Raising it because the ranking's stated purpose does not quite hold here.** A person looking in
`INBOX.Failed Processing` will not see an email whose first image was a duplicate and whose second
one raised. Folding the duplicate branch into the ranking would fix it, at the cost of the email
sitting in INBOX until the loop ends. **Your call, and I have not made it.**

---

## 8. My own mistakes

**One, and it is the more interesting kind because nothing went red.**

**Moving `Routes` into `tests/resolution_fixtures.py` silently took a module out of a guard.**
`test_logs_isolation.py::ProcessOnceRedirectionTest` checks that every test module driving
`process_once()` redirects the nine config paths that call writes, and it **detects such modules by
finding the string `process_once` in the module source**. Once `Routes` moved out,
`tests/test_step10f_duplicates.py` no longer contained that string, so the guard stopped checking it
even though it still drives the pipeline. My new file was never checked either, for the same reason.

**The suite stayed green. The only trace was the total subtest count going 408 to 407** while the
pass count rose, which is nine lost, being nine config names times one module. **I found it by asking
why a number had moved**, chased it with a per-file before-and-after count, and it came out as one
line: `test_logs_isolation.py: 81 -> 72`.

Fixed in the same commit: the guard now also detects the two fixture entry points that drive the
pipeline on a module's behalf, `run_pipeline_once` and `Routes`, so it covers ten modules where it
covered nine. The reasoning and the incident are in its own comment.

**Two things worth drawing out of this.** Quoting passes and subtests separately, which this project
already insists on, is what made it visible at all: a single "653 passed" would have hidden it
completely. And **a guard that identifies its subjects by a string in their source is fragile against
exactly the refactor that makes tests better**, which is worth remembering the next time something is
moved into a shared fixture.

---

## 9. What the brief got wrong

**Nothing.** Its table of where each outcome lands matched what I measured on all five rows,
including the detail that the duplicate row is harmless and the other three are not.

**Two things to add rather than correct.**

**One: `possible_duplicate` is unreachable on the embedded path**, so that row of the brief's table is
theoretical. It does not change the work, because the ranking is a decision about outcomes.

**Two: the brief says "four outcomes and the mixed case is five".** I read `validate()` and there are
**four** statuses reachable on this path counting the raise: `ok`, `needs_review`, `failed` and the
exception, with `possible_duplicate` unreachable. The raise and `failed` share a folder, so the
distinct destinations are three. I tested all four outcomes and five mixed combinations rather than
one, plus the two duplicate cases.

---

## 10. Confidence

**High that the embedded-image path now routes as the attachment path does.** It rests on the
side-by-side table produced by driving both paths in their own environments rather than transcribed;
twelve failures quoted before the change; six mutations, each with its diff printed to show it
changed one place, and each caught by tests naming what it broke; and the enumeration of all thirteen
`move_email_to_folder()` calls before and after.

**High on flag 1**, which is the one worth acting on next. It rests on bounding the loop and testing
for each name, and then on running one good receipt down each path and reading `filed_path` and the
categorisation count out of the database.

**High that the guard weakening in section 8 is fully repaired**, and it rests on the per-file count
going back from 72 to 90 and on the total arithmetic reconciling exactly: 408 − 81 + 90 + 8 = 425.

**Moderate on flag 2 being worth changing.** That it happens is certain and tested. Whether the
duplicate branch should join the ranking is a judgement about what Paul wants to see in
`INBOX.Failed Processing`, and it is his.

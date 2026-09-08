# Report: sub-step 10f.32, the embedded-image path uses the shared pipeline

**Written 2026-09-08, 09:35 BST (08:35 UTC), by the implementation session in Claude Code.**
**Branch `feat/console-phase0`. Sub-step 10f.32, amendment 269.**
**Brief: `PROMPT_claude_code_2026-09-08_embedded_shared_pipeline.md`.**

**Built. One commit, `9dbb111`, and it is not pushed.**

**No genuine decision surfaced, so I did not stop.** Section 3's boundary was the thing I watched
for, and section 8 records the one moment that came closest and why it was not one.

---

## 1. The suite

| When | Result |
|---|---|
| Before, the committed tree at `fc2fc1d` | **653 passed, 425 subtests** |
| After, at `9dbb111` | **663 passed, 437 subtests** |

**Both measured, at 09:00 and 09:30 BST.** Nine of the ten new tests are the new file; the tenth is
the one described in section 8. The twelve extra subtests are the new file's two plus ten from
existing subtested loops picking up the new `OUTCOMES` entry and the new test.

---

## 2. Every call inside the `embedded_images` loop

**From the syntax tree, bounding the loop by its own `For` node rather than by grepping**, so a call
in a neighbouring block cannot creep into the list.

**Before**, `app.py:1139` to `app.py:1259`:

```
  _iso_utc                    [1174]
  _log_receipt                [1182, 1218, 1251]
  base64.b64decode            [1144]
  compute_hash                [1145]
  email_msg.get               [1172, 1174]
  embedded_img.get            [1144]
  embedded_outcomes.append    [1212, 1232]
  extractor.extract           [1186]
  getattr                     [1203]
  logger.error                [1228]
  logger.info                 [1159, 1210]
  move_email_to_folder        [1162]
  repo.find_by_hash           [1157]
  repo.is_recorded_and_filed  [1158]
  repo.mark_processed         [1161, 1259]
  repo.save_extraction        [1190, 1233]
  repo.save_receipt           [1169]
  save_file                   [1166]
  uuid.uuid4                  [1165, 1189, 1234]
  validate                    [1187]
```

**After**, `app.py:1139` to `app.py:1260`:

```
  _iso_utc                    [1174]
  _log_receipt                [1182, 1252]
  base64.b64decode            [1144]
  compute_hash                [1145]
  email_msg.get               [1172, 1174]
  embedded_img.get            [1144]
  embedded_outcomes.append    [1227, 1233]
  extractor.extract           [1186]
  logger.error                [1229]
  logger.info                 [1159]
  move_email_to_folder        [1162]
  process_extraction_result   [1204]
  repo.find_by_hash           [1157]
  repo.is_recorded_and_filed  [1158]
  repo.mark_processed         [1161, 1260]
  repo.save_extraction        [1234]
  repo.save_receipt           [1169]
  save_file                   [1166]
  uuid.uuid4                  [1165, 1235]
```

**What arrived:** `process_extraction_result` at `:1204`.

**What went:** `validate` entirely; one of the two `repo.save_extraction` calls, the success one at
`:1190`; one of the three `_log_receipt` calls, the `"extracted"` one at `:1218`; one `logger.info`;
one `getattr`; one `uuid.uuid4`. **The loop is 21 lines shorter and one line longer.**

**`file_receipt()` and `categorise()` are still absent from this list and that is correct.** They are
called by `process_extraction_result()`, one frame down. Section 5 of the brief makes the point that
calling a frozen function is not editing it, and the enumeration is of the loop rather than of the
call tree.

**Every call site passes the whole signature.** Checked against `inspect.signature`: the function
takes 16 parameters, `app.py` now has **four** call sites at `:990`, `:1204`, `:1447` and `:1628`,
and each passes all 16 by keyword with none missing and none unrecognised.

---

## 3. Red before green

Seven failures before the change, from `tests/test_embedded_shared_pipeline.py`:

```
FAILED ...::TheEmbeddedPathFilesAndCategorisesTest::test_a_good_receipt_is_filed_into_the_client_folder
    AssertionError: unexpectedly None : an embedded-image receipt validated ok and was never
    copied into the client folder, so IntelliBooks never sees it
FAILED ...::TheEmbeddedPathFilesAndCategorisesTest::test_a_good_receipt_is_categorised
    AssertionError: 0 != 1 : no categorisation row was written, so the receipt reaches the books
    with no account
FAILED ...::TheEmbeddedPathFilesAndCategorisesTest::test_a_review_item_reaches_the_review_folder
    AssertionError: False is not true : the item has nowhere to be looked at
FAILED ...::TheEmbeddedPathFilesAndCategorisesTest::test_the_filed_copy_is_on_disk_under_the_client_folder
    TypeError: argument should be a str or an os.PathLike object ... not 'NoneType'
FAILED ...::BothEmailPathsProduceTheSameThingTest::test_the_two_paths_agree_on_status_filed_path_and_categorisation
FAILED ...::TheSharedFunctionIsCalledTest::test_the_loop_calls_the_shared_pipeline
    AssertionError: 'process_extraction_result' not found in {...}
FAILED ...::TheSharedFunctionIsCalledTest::test_the_loop_no_longer_validates_or_saves_an_extraction_itself
    AssertionError: 'validate' unexpectedly found in {...}
```

**Two passed in the red state and both are guards rather than red-first tests**:
`test_only_one_extraction_row_is_written`, which mutation C below is what earns, and
`test_the_exception_branch_still_writes_its_own_row`, which asserts something the change must not
break.

### The both-paths table, printed by the test

```
one good receipt, down each email path:
  path                 status   categorisations  filed_path
  email_attachment     ok       1                set, under Clients
  embedded_image       ok       1                set, under Clients
```

**Before the change the second row read `ok / 0 / None`.** That is the comparison from my own flag 1,
now a test rather than a probe, as the brief asked.

---

## 4. The exception branch: which shape and why

**It keeps its own `save_extraction()` and `_log_receipt()`, unchanged.**

**Because that is what the attachment path does, and the reason it does it is structural rather than
stylistic.** `process_extraction_result()` takes an `extraction` as a parameter, so by the time it
could be called there has to be one. A raise means there is none. Nothing about the function could
be reorganised to cover that case without inventing an empty `ExtractionResult`, which would put a
fabricated row through validation and categorisation.

So the loop's `try` now contains the extract and the shared call, and the `except` writes the failed
row by hand exactly as before, with `engine=extractor.name` rather than a literal so the row does not
say OpenAI produced a failure a different provider produced.

**A raise still lands in `INBOX.Failed Processing`**, which amendment 268 established.
`embedded_outcomes.append("failed")` in the `except` is untouched, and
`test_an_extraction_that_raised_goes_to_failed_processing` still passes. Mutation A in section 5
would have caught a change here.

---

## 5. The mutations, each anchored to one place with its diff printed

| # | Mutation | Places changed | Suite | Caught by |
|---|---|---|---|---|
| A | Back to validating and saving in the loop | 3 hunks, 31 lines | 8 failed, 655 passed | 6 of the new file's tests plus the new `possible_duplicate` test |
| B | Call the shared function and ignore its answer | 1 hunk, 2 lines | 2 failed, 661 passed | `test_two_identical_good_receipts_are_a_possible_duplicate` and the source guard |
| C | Call it **and** keep the loop's own extraction row | 1 hunk, 15 lines | 1 failed, 662 passed | `test_only_one_extraction_row_is_written`, alone |
| D | Pass `UNKNOWN_CLIENT_ID` instead of the client | 1 hunk, 2 lines | 10 failed, 654 passed | 9 tests and a subtest across both new and existing files |
| E | Stop recording the returned status | 1 hunk, 1 line | 16 failed, 654 passed | 9 tests and 7 subtests, including `test_step10f_duplicates.py`'s four-route control |

All five restored byte for byte, asserted by the harness and confirmed with `git status`.

**Mutation B is the plausible half-done version**, and it is the one the brief warned about: filing
and categorisation start working while the mailbox is still told what this path decided for itself.
It is caught by two tests and by neither of the filing assertions, which is the point of having the
routing suite as well as the filing suite.

**Mutation C is caught by exactly one test, and that test exists for it.** `extractions` is
append-only, so writing two rows for one attempt breaks nothing visible: no folder changes, no status
changes, and the receipt is filed correctly. Without that one assertion the suite would have been
green on a change that silently doubled the audit trail.

**Mutation D is the one worth reading.** Passing the reserved unresolved client raises nothing and
fails nothing at the call site. 10d.18 simply routes the item to Review instead of filing it, so the
receipt quietly stops reaching the client folder again, which is the original fault in a new
disguise. Ten failures.

---

## 6. Amendment 268's routing still holds

**The whole of `tests/test_embedded_email_routing.py` passes: 15 passed, 9 subtests.** Every outcome,
both mixed cases and the all-duplicates case, with the status now coming from the shared function
rather than from this path's own `validate()`.

The side-by-side table it prints is unchanged by this sub-step:

```
outcome -> folder, driven down both email paths:
  outcome          attachment path            embedded-image path
  ok               INBOX.Processed Receipts   INBOX.Processed Receipts
  needs_review     INBOX.Needs Review         INBOX.Needs Review
  failed           INBOX.Failed Processing    INBOX.Failed Processing
  raised           INBOX.Failed Processing    INBOX.Failed Processing
```

**Mutation E is the direct proof that the ranking is still wired to something real**: removing the
one line that records the status fails 16 things.

---

## 7. What became reachable, and the 10f.33 evidence that came with it

**`possible_duplicate` is now reachable on this path**, which the brief predicted as one of the three
things the shared function adds. Driven on both paths, two good receipts in one email:

```
email_attachment   identical            statuses=['ok', 'possible_duplicate']  landed=INBOX.Processed Receipts
email_attachment   different supplier   statuses=['ok', 'ok']                  landed=INBOX.Processed Receipts
embedded_image     identical            statuses=['ok', 'possible_duplicate']  landed=INBOX.Possible Duplicate
embedded_image     different supplier   statuses=['ok', 'ok']                  landed=INBOX.Processed Receipts
```

**The statuses agree exactly, which is 10f.32 working.** The landing folders differ, because the
attachment path routes inside its loop so the first outcome wins, and this path ranks so the worst
one does.

**That is sub-step 10f.33 and I have not touched it.** It is recorded here because amendment 269
predicted the divergence from indentation and this measures it, on a case that could not be produced
before today: **`possible_duplicate` in a multi-item email is precisely the shape 10f.33's open
decision is about.** Whether that changes Paul's answer on where a plain hash duplicate ranks is his
to say.

---

## 8. My own mistakes, and the one moment that tested section 3's boundary

**One existing test broke, and working out whose fault it was is the substance of this section.**

`test_all_good_still_goes_to_processed_receipts` sent two images that both returned the same
supplier, date and amount. Once the semantic duplicate check became reachable, the second one was
correctly `possible_duplicate`, the worst outcome across the email was no longer `ok`, and the email
went to `INBOX.Possible Duplicate`.

**I stopped and treated it as a candidate for section 3's hard boundary.** What settled it was
driving the attachment path over the same case, printed above: it produces the same two statuses and
always has. **So the behaviour is not new and no decision was being taken.** A test had called two
identical receipts "all good", which was only ever true because this path could not detect them.

**Corrected rather than made to pass.** Its two images are now two different purchases, and
`test_two_identical_good_receipts_are_a_possible_duplicate` pins the newly reachable case, so the
thing that broke is now asserted rather than removed. **This is the same class as
`tests/test_capture_inbox_cleanup.py`'s sidecar at 10f.18**: a test whose setup depended on the
defect.

**The mistake is mine rather than the test's.** I wrote that test yesterday, on a path where
`possible_duplicate` was unreachable, and used one fixture for both images because it was
convenient. **A test that uses the same input twice and calls the pair "all good" is asserting
something about de-duplication without meaning to**, and I did not see it until the ground moved.

---

## 9. Flags

**One, and it is small.**

**The embedded-image path is the only one of the four that does not use `extract_with_transient_retry()`.**
Enumerated: `app.py:987` on the auto-retry path, `:1444` on folder intake and `:1625` on the
attachment path all use it; the embedded loop at `:1186` calls `extractor.extract()` directly.

**So a transient OpenAI error on an emailed photo fails immediately, where the identical error on an
attachment is retried up to three times with backoff.** After this change that difference is more
visible, because the failure now routes the email to `INBOX.Failed Processing` rather than being
quietly reported as processed.

**Not fixed**, because the brief was specific about what goes and what arrives and this is neither.
**Small and obviously right: one call swapped for another, both already imported in `app.py`.** Say
the word.

**Item 174 stays absent as instructed**, and I did not touch the attachment path's routing block.

---

## 10. What the brief got wrong

**Nothing.** Its description of the fault matched what I found, its prediction that the change is a
deletion plus a call was accurate, and its judgement in section 3 that no new behaviour is being
designed held up: the one thing that looked like a decision was a stale test, and section 8 shows the
measurement that settled it.

**Two things to add.**

**One: it says fifteen arguments and there are sixteen.** The omitted one is `asserted_values`, which
every call site passes as `None`. The list it gives is otherwise exactly right, and all sixteen were
in scope, so it changed nothing.

**Two: it says `possible_duplicate` "becomes reachable on this path", which is true and understates
what follows.** Becoming reachable also makes it reachable *within a single email*, which is a case
neither path could produce before today and which lands the two paths in different folders. That is
10f.33's territory rather than a fault here, and section 7 is the evidence for it.

---

## 11. Confidence

**High that the embedded-image path now does what the other three do.** It rests on: the before and
after enumeration of every call inside the loop, taken from the syntax tree; all sixteen parameters
checked against the signature at all four call sites; the both-paths table of status, `filed_path`
and categorisation count produced by driving each path rather than transcribed; a test that the filed
document is actually on disk under the client top folder rather than only named in a column; and five
mutations, each with its diff printed to show it changed one place.

**High that amendment 268's routing survived**, which the brief named as the main risk. It rests on
the whole of `tests/test_embedded_email_routing.py` passing at 15 and 9, on the unchanged
outcome-to-folder table, and on mutation E failing 16 things when the status stops being recorded.

**High that no new behaviour was designed.** It rests on driving the attachment path over the one
case that changed and finding it produces the same statuses, which is a measurement rather than my
reading of the brief.

**This says nothing about the change under a real OpenAI call**, which no test here makes. The
retry-helper divergence in section 9 is the part of that gap I can see from the source.

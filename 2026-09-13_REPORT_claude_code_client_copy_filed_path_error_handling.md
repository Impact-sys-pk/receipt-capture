# Report, Claude Code, 2026-09-13: `mark_receipt_filed()` error handling in `copy_for_published_receipt()`

Step 10ax, amendment 446. Brief:
`PROMPT_claude_code_2026-09-13_client_copy_filed_path_error_handling.md`.

**Headline: the brief asked whether the fix is cosmetic. It is not.** Four of the five callers would
have lost one receipt and recorded the opposite of what happened to it. The fifth took the whole
poll cycle down.

---

## 1. The caller enumeration, printed whole

Walked the syntax tree of 112 production files, being `app.py`, every `*.py` at the repository root
and everything under `worker\`, and 90 files under `tests\`. Calls matched on the callee name from
the AST rather than by grep, so prose about the function is not counted. Each call carries the chain
of enclosing `def`, `for`, `while` and `try` nodes, innermost last.

```
production files scanned: 112
test files scanned: 90

=== PRODUCTION: 5 call(s) of copy_for_published_receipt() ===
app.py:762   in: def _publish_unpublished_receipts > for > try
app.py:841   in: def _copy_missing_client_copies > for > try
worker\extraction_pipeline.py:545   in: def process_extraction_result
worker\resolution\service.py:2568   in: def _apply_attached_note
worker\resolution\service.py:1395   in: def resolve_receipt > try

=== TESTS: 6 call(s) of copy_for_published_receipt() ===
tests\test_client_copy_collision.py:314   in: class TheOperatorIsToldWhichHappenedTest > def _copy
tests\test_post_time_client_copy.py:469   in: class OnTheOtherTwoTriggersTest > def test_never_means_never_whatever_moment_the_caller_claims > try
tests\test_stage4_client_copy.py:582   in: class TheCopyIsImageOnlyTest > def test_a_second_publish_of_one_receipt_writes_no_second_file > try
tests\test_stage4_client_copy.py:632   in: class TheCopyIsImageOnlyTest > def test_two_different_receipts_that_would_share_a_name_both_land > try
tests\test_stage4_client_copy.py:706   in: class TheTriggerDecidesTest > def test_post_writes_nothing_at_publish_time_and_says_so_once > try
tests\test_stage4_client_copy.py:735   in: class TheTriggerDecidesTest > def test_a_client_with_no_folder_name_is_reported_and_not_guessed > try
```

**Five production callers, which matches the number the function's own docstring states**, and its
naming of `_apply_attached_note()` as the one that passes `post`. The docstring is right about the
set. The test line numbers above are as the file was before my change; the four in
`test_stage4_client_copy.py` have moved down by 124 lines since.

---

## 2. What each caller did today, before the fix, if this function raised

Read out to the point where the exception is caught, rather than inferred from the AST summary.

### 2.1 `app.py:762`, `_publish_unpublished_receipts()`. One receipt, misreported

The call sits in the loop body's own `try` at `app.py:652`, whose `except Exception as exc` at
`app.py:778` logs `failed to publish recovered receipt {receipt_id}` with a traceback and lets the
loop continue.

**Blast radius: this receipt's recovery line only.** It publishes before the call and
`publish_receipt()` has already written its `publish_events` row, so the receipt really is
published. What is lost is `stats["recovery_published"]` and the success INFO line, so
`runs.ndjson` undercounts the sweep and `run.log` says the publish failed when it succeeded.

### 2.2 `app.py:841`, `_copy_missing_client_copies()`. One receipt, and it retries itself

The call is in the loop body's `try` at `app.py:823`, `except Exception as exc` at `app.py:857`,
which logs `could not retry the client folder copy for {receipt_id}` and continues. Its own comment
says "One receipt must not take the poll down either way", which is exactly right and is why this
caller was never the problem.

**Blast radius: nothing lasting.** This is the retry sweep, so the next poll offers the receipt
again.

### 2.3 `worker\extraction_pipeline.py:545`, `process_extraction_result()`. One receipt, recorded as a failed extraction that did not fail

**No guard in this function.** The raise leaves `process_extraction_result()` and reaches its four
callers, enumerated the same way:

```
process_extraction_result()  app.py:1242   in: def _retry_failed_receipts > for > try
process_extraction_result()  app.py:1760   in: def process_once > try > for > try
process_extraction_result()  app.py:1962   in: def process_once > try > for > for > try
process_extraction_result()  app.py:1517   in: def process_once > try > for > for > try
```

All four hold a per-item `try/except Exception`, so the poll survives. **What each handler then does
is the problem**, because every one of them is the extraction-failure handler:

- `app.py:1985`, the email attachment path. Writes an `extractions` row with
  `validation_status="failed"` and `raw_response=str(exc)`, logs an `extraction_failed` event,
  appends `"failed"` to `email_outcomes` so `_worst_outcome_folder()` **moves the email into Failed
  Processing**, then calls `repo.mark_processed(...)`.
- `app.py:1541`, the embedded-image path. The same, without the `mark_processed()`.
- `app.py:1779`, the inbox path. The same, plus `file_review()` copying the original into the Review
  folder. The `finally` at `app.py:1819` still moves the inbox pair to Processed.
- `app.py:1271`, `_retry_failed_receipts()`. The same shape.

**So a receipt that extracted cleanly, validated `ok`, categorised, published, and whose document is
sitting correctly in the client folder would be recorded as an extraction failure, given a second
`extractions` row saying so, and its email filed under Failed Processing.** That is the opposite of
what happened to it.

**Also skipped, because they sit below the call inside `process_extraction_result()`:**
`repo.mark_processed(message_id, attachment_id, file_hash, receipt_id, firm_id)`,
`report_validation_outcome()` and `_log_receipt()`. On the embedded-image path nothing marks the
attachment processed at all, so the same image is offered again on the next poll and is caught, if
at all, by the file-hash duplicate check rather than by the message-id one.

**One flag, not fixed.** `_retry_failed_receipts()`'s handler carries the comment at `app.py:1273`:
"process_extraction_result() never ran, so no extraction row was written". That is false on this
path. The call is near the end of that function, so the extraction row, the categorisation row, the
publish and the client copy have all happened by the time it raises, and the handler then writes a
second `failed` extraction row over the top. **The obvious fix removes an assumption rather than
adding a guard**: that comment and the recovery write below it assume the callee is all-or-nothing,
and it is not. It needs a decision about what a late failure should record, so I have left it.

### 2.4 `worker\resolution\service.py:1395`, `resolve_receipt()`. The resolution is abandoned and reported as an error

The call is inside the `try` at `service.py:1076`, whose body runs to `service.py:1616`, with
`except Exception` at `service.py:1618` returning `ResolutionOutcome(outcome="error", ...)` and a
`finally` releasing the receipt lock.

**Blast radius: this resolution.** Everything below line 1395 in that try body is skipped, so the
status is not written, the resolution event is not recorded and nothing republishes.
`_consume_resolution_notes()` sees a non-applied outcome and moves the note into `failed\` with the
reason beside it. **The document is nonetheless in the client folder**, so the operator is told a
correction failed while the filing it triggered has already happened.
`_consume_resolution_notes()`'s own docstring says a note in `failed\` means the database and the
books disagree, "which is the one thing this contract exists to prevent".

### 2.5 `worker\resolution\service.py:2568`, `_apply_attached_note()`. The whole poll cycle

**This is the answer to the brief's real question.** There is no guard anywhere between the call and
`process_once()`:

- `_apply_attached_note()` has no `try` around the call.
- Its only caller is `apply_resolution_note()` at `service.py:2842`, which has none either.
- `apply_resolution_note()`'s only caller is `app.py:504`, inside `_consume_resolution_notes()`'s
  `for note_path in notes:` loop at `app.py:495`. **The `try` in that loop covers only
  `json.loads(note_path.read_text(...))`**; its `except (OSError, ValueError)` at `app.py:498` ends
  in `continue`, and the `apply_resolution_note()` call at line 504 sits outside it.
- `_consume_resolution_notes()` is called at `app.py:1372`, inside `process_once()`'s `try` at
  `app.py:1333`, whose handler at `app.py:2023` logs `process_once failed` and **`raise`s**.
- That reaches `main()`'s `except Exception` at `app.py:2071`, which logs `run failed` and sleeps.

**So the pipeline survives and the poll does not.** Everything after `app.py:1372` is skipped: the
remaining resolution notes, the email fetch and its four intake paths, the inbox scan,
`_retry_failed_receipts()`, `_publish_unpublished_receipts()`, `_copy_missing_client_copies()` and
the daily backup. The note that raised is moved to neither `processed\` nor `failed\`, so it is
offered again next poll, and a database fault that persists aborts every poll at the same point
indefinitely.

**On the brief's self-healing story.** It holds, with one qualification the brief did not state: the
retry that heals it is `_copy_missing_client_copies()`, at `app.py:844` in `process_once()`, which
is **below** the `_consume_resolution_notes()` call the uncaught exception aborts. On that path the
failure prevented its own remedy from running in the same poll. It still self-heals on the next
poll, because that starts from the top.

---

## 3. The change

`worker\client_copy.py`, `copy_for_published_receipt()`. One function. `write_client_copy()`, the
byte-comparison logic and everything else in the file are untouched, which the diff shows.

- `repo.mark_receipt_filed(receipt_id, str(result.path))` is now wrapped in its own
  `try/except Exception`, matching the shape and tone of the `except` above it: an ERROR naming the
  receipt, **the path the document is actually at**, the exception type and message, and that
  `filed_path` is still NULL so the next poll's sweep will record it without writing a second copy.
  Returns `None`, the same as the existing failure branch.
- The docstring's "**This never raises.**" is now true. A section was added under it recording why
  it was aspirational, what each caller did with the exception, and that the self-healing runs
  through `_copy_missing_client_copies()`.

**Line numbers, confirmed against the file as found and as left.** The brief cited 544, 553 and 568.
As found: `try:` at 544, `result = write_client_copy(` at 545, its `except` at 553,
`repo.mark_receipt_filed(...)` at 568. **The brief's "the `write_client_copy()` call is at line 544"
is one line out**, 544 being the `try:`. The other two were exact. As left: the call is at 569, its
`except` at 577, `repo.mark_receipt_filed(...)` at 593 and its new `except` at 594.

---

## 4. The tests

`tests\test_stage4_client_copy.py`, new class `RecordingTheCopyCanFailTooTest`, placed immediately
before `OnlyOkIsCopiedTest`. It reuses the module's existing fixtures unchanged: `TempEnvironment()`,
`trigger("publish")`, `captured("worker.client_copy", logging.ERROR)`, `everything_under()`,
`receipts()` and a real `Repository`. `import sqlite3` was added to the module's stdlib import block.

The failure is driven with
`patch.object(Repository, "mark_receipt_filed", side_effect=sqlite3.OperationalError("database is locked"))`
against a **real** `Repository`, so everything else about the repo is the real thing and only the one
method fails. That is the faithful stub rather than a recording one: the real method runs an `UPDATE`
and commits, and the thing being modelled is that write failing.

1. `test_a_failing_mark_receipt_filed_is_reported_and_does_not_propagate` asserts the call returns
   `None` rather than propagating, that exactly one file is under `config.CLIENTS_ROOT` and it is
   `2026-04-01_apcoa-parking_12.00.pdf`, and that exactly one ERROR is logged naming the receipt id,
   that filename and `OperationalError`.
2. `test_the_next_attempt_records_it_rather_than_writing_a_second_copy` drives the brief's
   self-healing claim rather than taking it on trust: a real `receipts` row, one failing attempt,
   then the same call with the database healthy. Asserts no second file is written and that
   `receipts.filed_path` equals the returned path.

**The second test is beyond the brief's literal ask**, which was one test. It is a test only, no
production behaviour rides on it, and the brief asked for the self-healing story to be verified
rather than trusted. Flagged here because the brief also said to touch nothing else.

### 4.1 Red before green

Run with the tests in place and before the production change:

```
worker\client_copy.py:568: in copy_for_published_receipt
    repo.mark_receipt_filed(receipt_id, str(result.path))
...
E               sqlite3.OperationalError: database is locked
=========================== short test summary info ===========================
FAILED tests/test_stage4_client_copy.py::RecordingTheCopyCanFailTooTest::test_a_failing_mark_receipt_filed_is_reported_and_does_not_propagate
FAILED tests/test_stage4_client_copy.py::RecordingTheCopyCanFailTooTest::test_the_next_attempt_records_it_rather_than_writing_a_second_copy
2 failed, 51 deselected in 0.42s
```

Red for the right reason: the exception propagating out of line 568, which is the defect.

### 4.2 Mutation, to show the tests discriminate

Both mutations were taken from a pristine copy, anchored on a string the harness asserted matches
exactly once, and each printed its own unified diff. Both were run against the **whole** suite, not
only the new class.

**Mutation 1**, return the path instead of `None` on a failed record, which would claim the copy is
recorded when it is not:

```
--- pristine
+++ mutated
@@ -618,5 +618,5 @@
             "writing a second copy.",
             receipt_id, result.path, type(error).__name__, error)
-        return None
+        return result.path

     if not result.written:
```

Result: `2 failed, 1383 passed, 1 skipped, 946 subtests passed`. Both failures are the two new
tests. Nothing else caught it.

**Mutation 2**, drop the path from the ERROR line, which is the one thing the brief said the message
must carry:

```
--- pristine
+++ mutated
@@ -613,5 +613,5 @@
         # it instead of writing a second one. 10f.25.
         logger.error(
-            "receipt %s was copied into the client folder at %s, but recording "
+            "receipt %s was copied into the client folder, but recording "
             "it failed: %s: %s. The document IS there and filed_path is still "
```

Result: `2 failed, 1383 passed, 1 skipped, 946 subtests passed`. The same two, nothing else.

Restored from the pristine copy and md5 compared before the final run:

```
4ee7826350a3c7316c315b0a8e192f69 *worker/client_copy.py
4ee7826350a3c7316c315b0a8e192f69 *...\scratchpad\client_copy.pristine.py
```

---

## 5. The suite, before and after

Command: `.\.venv\Scripts\python.exe -m pytest -q`.

| When | Result |
| --- | --- |
| Before any change | **1383 passed, 1 skipped, 946 subtests passed** in 84.24s |
| After the test and the fix | **1385 passed, 1 skipped, 946 subtests passed** in 102.82s |

Plus two, which is the two new tests. Nothing else moved: the skip and the subtest count are
unchanged. `py_compile` is clean on both changed files.

**Note on `CLAUDE.md`'s post-commit rule.** It requires a second suite run after the commit whenever
the change adds a file, because two source guards sweep `git ls-files` rather than the working tree.
This change adds no production file, so the rule does not bite. The run was done anyway and its
result is at section 9.

---

## 6. Where the brief was wrong, or incomplete

1. **"the `write_client_copy()` call is at line 544"** is one line out. 544 is the `try:`; the call
   is 545. The other two citations were exact.
2. **"why it might matter less than it sounds"** is the wrong way round for the
   `_apply_attached_note()` path, which had no guard at all and aborted the poll. The brief did
   anticipate this by asking the question rather than assuming the answer.
3. **The self-healing story has a hole the brief did not see**, at 2.5 above: on the one unguarded
   path, the exception aborts the poll before the sweep that would have healed it runs. It heals on
   the next poll rather than in the same one.
4. **"four of the five callers are the publish path"** is accurate, verified from the enumeration
   rather than taken from the docstring that also says it.

---

## 7. My own mistakes

1. **Chained shell commands with `;` in my first two calls**, which `CLAUDE.md` forbids under an
   AUTOMATIC task: the permission matcher compares the whole string and does not split on
   separators. Caught after the second call and not repeated.
2. **Wrote scratch scripts into `%TEMP%` rather than the session scratchpad** on the first two
   attempts, because I used `$TEMP` without checking what it was. Corrected; later scripts went to
   the scratchpad. Nothing was written outside the repository and the temp directories either way.
3. **The first insertion attempt failed on an anchor that did not match**, because a backslash was
   consumed somewhere between my command and the script on disk, so my anchor held a real newline
   where the target file holds a literal backslash-n. Switched to a line-number insertion anchored on
   a unique `class` line with an explicit `assert len(marks) == 1`. Nothing was written during the
   failed attempt: the assert refused, which is the behaviour the mutation rule asks for.
4. **Wrote the seed helper against a `save_receipt()` signature I had not read**, passing
   `attachment_id`, `received_at` and `created_at`, none of which that method takes. The first red
   run therefore failed on `TypeError` rather than on the defect. Read the real signature in
   `worker\database\repository.py`, corrected it, and re-ran to get a red for the right reason. This
   is the verify-against-the-thing-itself rule, broken and then applied.

---

## 8. Confidence

**High that the fix does what it says**, resting on the red run showing the exception propagating out
of line 568, the green run after it, and two mutations each caught by exactly the two new tests and
by nothing else across 1385.

**High that the caller enumeration is complete**, resting on an AST walk over 112 production files
matching on the callee name, printed whole above, agreeing with the count the function's own
docstring states. This is a claim about a set, so it was enumerated and printed rather than
estimated.

**High on what each of the five callers does today**, resting on reading each handler body in the
file rather than on the AST summary. The `except` bodies at `app.py:778`, `app.py:857`,
`app.py:1271`, `app.py:1541`, `app.py:1779`, `app.py:1985`, `app.py:2023`, `app.py:2071` and
`service.py:1618` were each read.

**Medium on the consequence descriptions at 2.3**, specifically that an affected email would be moved
into Failed Processing. That is read from `email_outcomes.append("failed")` and
`_worst_outcome_folder(email_outcomes)` in the handler, not driven by a test: making
`mark_receipt_filed()` fail inside a live email poll is more machinery than the brief asked for. The
path is plain in the source; I have not watched it run.

**Not established, and not evaluated, per the brief.** Whether the poll cadence makes the retry fast
enough in practice.

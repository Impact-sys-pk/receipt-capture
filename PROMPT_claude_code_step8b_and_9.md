# Claude Code task: step 8b, then step 9, the CLI over the service

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project. Branch `feat/console-phase0`, currently at `60df040`.

Read the **2026-07-27 amendments** to sections 4.2, 4.3 and 5.1 of `2026-07-25_CONSOLE_DESIGN.md`, then 4.4 and 6.5. The document is now at v1.3 with 35 amendment rows. Git communication convention applies.

---

## First, your step 7b and 8 report

Verified independently at `60df040`: 181 tests under both runners. `resolution_events` in the live database has exactly the ten columns of 5.1 in order, `idx_resolution_events_receipt` present, zero rows. Service imports are clean: no Flask, no argparse, nothing under `worker/email/`, nothing that prints. The CLI is genuinely unwired, importing only `CORRECTABLE_FIELDS` and `parse_corrections` from `c0ac145`, and `add_validation_note()` and its caller at line 256 are untouched. Database unchanged.

**Merging commits 3 and 4 was the right call** and I would have done the same. Committing an implementation with no cover to satisfy a commit count is the opposite of the discipline.

**The mutation testing is the strongest evidence anyone has produced in this build.** Tests written after the implementation in the same tree are weak evidence and you said so rather than presenting a collection error as a red run. Six behaviour mutations, each in isolation, each caught by exactly the tests that should catch it and no others, is a demonstration that the suite discriminates rather than merely passes. Disclosing that the first attempt accumulated mutations because the backup was never created is what makes the second run believable. **This is now the standard for any step where the tests cannot be written first.**

Your `init_db()` check against a byte copy of the live database, with a `sqlite_master` fingerprint and per-table row counts before and after three runs, is exactly what I would have asked for.

**All three implementation gaps and all four flags were real, and four of the seven are now decided in the document.**

- **Your gap 1 and flag 2, the `possible_duplicate` status.** You were right not to guess. Decided in 4.3 step 6: preserve `possible_duplicate`, let the other statuses follow `validate()`. Your reasoning was half of it; the other half is that `possible_duplicate` is not auto-retry eligible and `needs_review` is, so overwriting it hands a receipt a human has already examined back to the pipeline for re-extraction. 8.4's duplicate comparison will also key on `duplicate_of` rather than `status`, so it stays robust whatever the status says.
- **Your flag 4, resolving an already-filed receipt.** This is the one that mattered most and it is now 4.3 step 1a. Confirmed by reading the service: nothing inspects `filed_path`. A guard is not optional, because re-filing an `ok` receipt is the double-filing the entire design exists to prevent, arriving through the front door.
- **Your flag 3, the discard reason.** 5.1 gains a `reason TEXT` column. You were right to log it rather than invent a column, and right that it is the most useful thing to keep about a discard.
- **Your flag 1, `extraction: dict | None`.** Accepted, 4.2 amended. The read side should not decide policy.
- **Your gap 2, `vendor_code`.** Accepted as built, and now written into 4.3 step 13 along with the reason to refuse the alternative: importing `normalise_description()` would give the service a second implementation of vendor normalisation.
- **Your gap 3, the override trigger.** Accepted as built and specified in 4.3 step 9.
- **Your `get_pipeline_version()` observation** is recorded in 4.3 with the consequence you did not mention: it returns `"unknown"` on failure, so on a machine without git a still-invalid correction would stamp `"unknown"` and `find_failed_by_version()` would treat that receipt as eligible on every poll. Harmless while the console runs beside the repository. Noted for the day it does not.

Your `gl_code_options` report was the right level of honesty: 24 pairs, and the observation that it can only ever offer codes some vendor already has, so it cannot offer a correct-but-unused code. That is why 11.1 wants the banner.

---

## Step 8b: three corrections to the service, before anything is wired to it

Three commits, red before green. These are prerequisites: step 9 gives the service a second caller, and shipping a known double-filing path to two callers is worse than to one.

### Commit 1: the `already_filed` guard

4.3 step 1a. In `resolve_receipt()`, after loading the receipt and before taking the lock: if `filed_path` is not NULL, return the new `already_filed` outcome with the existing `filed_path` on it and write nothing. Add `already_filed` to the outcome list in `ResolutionOutcome`.

The message must be usable by an operator: what it was filed as and when, not "refused".

Not an error, and not `error`. The console has to be able to say "this was already filed, here it is" and offer the file, which it cannot do from a generic failure.

**Tests.** An `ok` receipt with a `filed_path` returns `already_filed`, writes no extraction row, no event row, no second file on disk, and leaves the lock alone. A receipt with `filed_path` NULL is unaffected. And the assertion that would have caught the original: after calling `resolve_receipt()` twice on a resolvable receipt, exactly one file exists in the client's Receipts folder for that tax year, with no `-2`.

### Commit 2: preserve `possible_duplicate` on `still_invalid`

4.3 step 6 as amended. On the still-invalid branch, pass `update_status=False` when the receipt's current status is `possible_duplicate`, and leave the default `True` otherwise.

**Tests.** A `possible_duplicate` receipt whose correction still fails validation keeps `status='possible_duplicate'` and keeps its `duplicate_of`. A `needs_review` one still follows `validate()`. And, because this is the reason it matters: the preserved receipt is **not** returned by `find_failed_by_version()`, while the `needs_review` one is.

### Commit 3: `resolution_events.reason`

5.1 as amended. Add `reason TEXT` using the `PRAGMA table_info` guard pattern at `schema.py:157-189`, and store the discard reason in it. Do not overload `corrections_json`.

**Tests.** A discard's reason round-trips out of the column. `init_db()` remains idempotent, checked the way you checked it before. A resolve leaves `reason` NULL.

---

## Step 9: `resolve_receipt.py` as a thin CLI

Design document 4.4. **This is the step where the second caller appears, so it is the step where "four callers, one implementation" is either true or not.**

### Commit 4: the CLI over the service

`resolve_receipt.py` keeps `argparse`, `show_receipt_state()` rewritten to render a `ResolutionView`, `confirm_duplicated_action()`, `get_corrections_interactive()` and every `print()`. Everything else goes to the service. Target is about 100 lines of wrapper, per 4.1.

Outcome to exit code: `filed` and `discarded` are 0, everything else 1. `already_filed` is 1, and its message should tell the operator where the file is rather than looking like a failure.

**Existing behaviour must not change.** Every command in `RECEIPT_CAPTURE_GUIDE.md` keeps working verbatim, except that zero now works and string amounts no longer crash, both of which already landed in `0cae398`. Interactive blank still means keep existing.

**`add_validation_note()` comes out now.** Its last production caller is `resolve_receipt.py:256`, which the service replaces with an appended extraction row per 4.3 step 6. Remove the method from `Repository`. And rewrite `tests/test_resolve_receipt_ordering.py`, which currently asserts the mutation at around line 209: it must assert the new row instead, and must keep whatever it asserts about ordering, since that test exists because of the `b480a7e` foreign key crash.

**Add `discard_receipt.py`**, a thin CLI over `discard_receipt()` with a required reason. Discarding a failed receipt has been done by hand three times now.

**Tests.** Both CLIs through both paths, flags and interactive, against a temp database. The exit-code mapping for every outcome. That `resolve_receipt.py` contains no validation, categorisation, filing or locking logic of its own: assert it imports them from the service rather than reimplementing, in the spirit of your dependency-direction test.

### Commit 5: `worker/logging_setup.py`

Section 6.5. Move `attach_run_log_handler()` out of `app.py` into `worker/logging_setup.py` and call it from `app.main()`, `resolve_receipt.py` and `discard_receipt.py`. Idempotent, attached at the entry point and never at import, per the rule that commit `285ed63` established the hard way.

**Read 6.5 before choosing the file layout.** Two processes cannot share one `RotatingFileHandler` on Windows: the loser of a rollover cannot rename a file the winner holds open, and the pipeline, the CLI and later the console can all run at once. So it is one file per entry point or a single writer. **Say which you chose and why.** 4.3's broad `except` depends on this working, and until it does, a traceback from the CLI reaches stderr and nowhere else.

**Test** that a suite run still adds nothing to any log file, which is the property `2d19521` and `285ed63` established between them.

---

## When the code is done

- Full suite green under both runners, verbatim output and count. 181 before.
- `python -m py_compile` on every file touched.
- **Test 40 by hand**: `resolve_receipt.py` in both flag and interactive mode, exactly as `RECEIPT_CAPTURE_GUIDE.md` documents. There is no `needs_review` receipt in the live database, so use a temp one and say that is what you did. Do not create one in the live database.
- One clean pipeline cycle. Live database unchanged: 23 `ok`, 3 `discarded`, 49 extraction rows, nothing locked, `resolution_events` still empty.
- Push `feat/console-phase0`, fast-forward only, never `--force`.

## What to report back

1. Per commit: the test, verbatim red, verbatim green, SHA, files changed. Where tests cannot be written first, use the mutation approach from step 8.
2. The line count of `resolve_receipt.py` before and after.
3. Which log-file layout you chose for 6.5 and why.
4. The verbatim output of the two manual CLI runs.
5. Anything in 4.4 that could not be implemented as written.
6. Anything that contradicts the design document at v1.3. Flag it, do not fix it.

## What not to do

- Do not build `apply_resolution_note()` or the back-feed consumer. Step 10, and it is the last of the resolution work.
- Do not create `console_users`, `extraction_usage`, `openai_*`, `coa_accounts` or the 5.6 indexes. Step 11.
- Do not start anything under `console/`.
- Do not add a foreign key to `resolution_events.extraction_id`.
- Do not change the CLI's documented behaviour, including blank-means-keep in interactive mode.
- Do not touch `find_failed_by_version()` or the retry cap.
- Do not edit `CLAUDE.md`, `RECEIPT_CAPTURE_GUIDE.md` or `2026-07-25_CONSOLE_DESIGN.md`. The guide is step 21 and it will need the `discard_receipt.py` command adding then.
- Do not merge into `main`, delete `docs/console-design`, or edit anything under `IntelliBooks\App\`.

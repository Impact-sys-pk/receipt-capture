# Claude Code AUTOMATIC task: step 9b, then step 10, the back-feed consumer

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project. Branch `feat/console-phase0`, currently at `d4a5a97`.

**This is an `AUTOMATIC task`.** Work through it under the AUTOMATIC Task Mode section of `CLAUDE.md`: commits, file creation, editing the tests this brief names, and a fast-forward push to `feat/console-phase0` are all pre-approved. Report once at the end, not at each step. Stop only for the seven things that section lists, and note that item 2 matters here: the `Resolutions\` folder is under OneDrive, so **creating it and moving notes within it needs my yes the first time**, and after that carry on.

Read **section 12 in full**, including the 2026-07-27 amendment to 12.4, then 5.1a and the 4.4 amendment. The document is at v1.3 with 39 amendment rows.

**Step 10 is one half of a two-sided contract whose other half is built by a session that cannot see yours.** Section 12 is the contract. Where this brief and section 12 disagree, section 12 wins and you should tell me. Git communication convention applies.

---

## First, your step 8b and 9 report

Verified independently at `d4a5a97`: 221 tests under both runners, and in a fresh clone the suite writes **nothing** to `data/` or `logs/`, so the leak you found is genuinely closed. `add_validation_note()` is gone from `Repository`. `resolution_events` has the `reason` column and zero rows. `data/` holds only `run.log`. Live database unchanged. `confirm_duplicated_action` is defined at `resolve_receipt.py:105` and appears nowhere else, so your flag 1 is confirmed by grep.

**Finding your own leak is the single most valuable thing in this report.** Step 9's requirement was that the suite writes nothing to the live logs, and you checked it instead of assuming, and it was false: `attach_log_handler()` resolves `config.DATA_DIR` at call time and the CLI tests call `main()`. That is the same defect as `2d19521` in a new place, three steps later, and your own isolation test missed it because it only checked imports. It now runs a CLI end to end. That is how a test earns its place.

**Your reasoning on the log layout is accepted and recorded** in section 16 step 9, including the part I care about: a `QueueHandler` listener has to be a process that owns the file, so either the pipeline must be running before the CLI can log or there is a daemon, and logging then stops silently if the listener is down. Silent failure in the logging path is the worst place to put it.

**The UTF-8 fix was in scope even though it was not in the brief.** A crash after the work has succeeded, printing a traceback over a filed receipt, is exactly the kind of thing test 40 exists to surface. You checked it against `60df040` and confirmed it was pre-existing rather than assuming. Recorded in 4.4.

**Rewriting the `filed then stale` test was correct and you were right to flag it rather than bury it.** 4.3 puts step 1a before step 3, so `already_filed` takes precedence over `stale` by design, and a test asserting the old order was asserting the old spec.

**Your three flags, all real. Two become work, one does not.**

- **Flag 1, `confirm_duplicated_action()` is dead.** Your preference is right and it is now the 4.4 amendment: wire it up. With 4.3 confirming that resolving a `possible_duplicate` **is** the "file it anyway" path, an unasked prompt is the last route by which the CLI files a duplicate silently. Step 9b below.
- **Flag 2, `already_filed` has no date to report.** Confirmed: `receipts` has `filed_path` and no timestamp. Adding it is cheap and 8.3 already lists a "filed" column that would otherwise only ever be a yes or no. New section 5.1a, step 9b below.
- **Flag 3, `run_console.py` versus `console/`, is not a conflict.** Section 8's file layout lists **both**: the `console/` package and `run_console.py` at the repository root, which is the entry point that imports it. So `console.log` is attached by `run_console.py` and your reservation is right as it stands. Nothing to settle. I am telling you rather than just recording it because you should be able to trust section 8's layout when step 14 comes.

The line count is 268 rather than the 250 you reported, on my count of the file at `d4a5a97`. Your breakdown is right and the target in 4.1 was wrong, not the implementation; 4.4 now says so.

---

## Step 9b: two small corrections

### Commit 1: call `confirm_duplicated_action()`

When a receipt's status is `possible_duplicate` and no `--duplicate-decision` flag was given, ask before doing anything else. Its answer maps to `discard_receipt()` or to continuing into the correction flow, which is the "file it anyway" path.

**Test.** A `possible_duplicate` receipt with no flag prompts, and answering discard discards while answering file continues. And the assertion that matters: **no path files a `possible_duplicate` receipt without either a flag or an answer.**

### Commit 1a: move the folder-intake original out of the inbox on every outcome

**Read section 3.13, which is new, and do this commit first.** It is live and it is costing an OpenAI call every five minutes for any folder-intake receipt sitting in review.

`_remove_inbox_pair(intake)` at `app.py:777` runs only `if status == "ok"`. Anything else leaves the original in `Receipt Inbox\{CODE}\`, and `app.py:717` then deliberately allows reprocessing on the next poll, so the receipt is re-extracted for ever, with a new receipt row, a new extraction row and a new Review pair each time. It is the folder-intake twin of 3.1.

**Fix, as Paul has decided.** Move the original to a `Processed\` subfolder under the client's inbox folder on **every** outcome, not only `ok`. Move rather than delete, per the no-data-loss rule, and that applies to the `ok` path too, which currently deletes.

Leave the reprocessing rule at `app.py:717` alone. It becomes unreachable for this case but it still guards the genuine resend of a file an operator puts back deliberately.

**Tests.** A receipt landing `needs_review` through folder intake has its original moved out, and a second `process_once()` under the same version creates no second receipt row and calls the extractor zero times. The same for `failed`. The `ok` path still clears the inbox, now by moving. And a sidecar accompanying the original moves with it rather than being orphaned.

There is one such receipt live right now, `c5a3fccd-6684-4bb9-b3fb-5023e86b6461`, `needs_review`. Its original has already been moved out of the inbox by hand, so do not go looking for it, and **do not touch that row**: it is the fixture for the change log item 19 test.

### Commit 2: `receipts.filed_at`

Section 5.1a. One column via the `PRAGMA table_info` guard pattern, set in `mark_receipt_filed()`, which is the only writer of `filed_path` so the two stay consistent by construction. Put it in the `already_filed` message.

**Do not back-fill existing rows from a file mtime.** That records when a copy was written, not when the practice filed it, and a plausible wrong date is worse than a NULL. Test that existing rows stay NULL and that `init_db()` is still idempotent, the way you have checked it twice already.

---

## Step 10: the back-feed consumer

Three commits. This is the last of the resolution work and the point of the whole detour.

### Commit 3: `apply_resolution_note()`

12.3 step 4, in `worker/resolution/service.py`. It validates a note, then calls `resolve_receipt()` or `discard_receipt()` with `actor='desktop'`, `source='desktop'`. **It must not reimplement resolution.**

**12.3 step 5 is the one that matters and the one to get wrong.** For a `filed` note the image is **already** at `filed_path`, put there by Desktop. So `apply_resolution_note()` must record the filing with `mark_receipt_filed()` and **must not call `file_receipt()`**. Get that wrong and every Desktop resolution files a second copy, which is the exact bug this contract exists to prevent. 12.3 says this must be explicit rather than a flag threaded through `resolve_receipt()`, so it writes the `manual_correction` extraction row, categorises, sets `filed_path` and sets status `ok` on its own path.

Note the interaction with what you built in 8b: `resolve_receipt()` now refuses an already-filed receipt with `already_filed`. A Desktop-filed receipt has no `filed_path` in the database yet, because Desktop never writes the database, so the guard does not fire. Say in your report whether you found that to be true, because if it does fire the contract is broken.

**12.3 step 6, `category_name` to code.** Look the name up in `coa_accounts`. That table does not exist until step 11, so **every note takes the not-found branch today**: store the name, skip vendor learning, add a validation note. 12.3 says that is expected and not an error. Write it so it works unchanged when the table arrives.

**Desktop deletes the Review pair itself**, per the 12.4 amendment, lines 1795 to 1796 of the HTML. So `remove_review_pair()` will find nothing. Do not treat a zero return as a failure.

### Commit 4: the consumer loop in `app.py`

12.3. At the start of `process_once()`, **before `_retry_failed_receipts()`**, so a receipt resolved by note is never retried in the same cycle. `*.json` in `Resolutions\`, oldest first by filename.

Every failure moves the note and **never deletes it**: `Resolutions\failed\` with a `.error.txt` alongside, logged at ERROR. Success moves it to `Resolutions\processed\`. The directory does not exist yet; create it on demand from `config.RESOLUTIONS_DIR`, which needs adding to `config.py` and `.env.example` per 7.2.

**Idempotency, 12.3 step 3.** If a `resolution_events` row already exists for this receipt with the same `resolved_at`, treat it as applied, move to `processed\`, continue. Note that `resolution_events` has no `resolved_at` column; decide where the note's timestamp lives and say what you chose. `corrections_json` is the obvious candidate and it is already a JSON blob.

**Receipt matching, 12.3 step 2.** By `receipt_id`, else by matching `original_review_files` against `receipts.filename`. Not found, move to `failed\`.

### Commit 5: tests 22 to 28

22. A valid `filed` note sets status `ok`, sets `filed_path` to the note's path, writes a `manual_correction` extraction row, writes an event row with `actor='desktop'`, and **does not re-file the image**. Assert the count of files in the target folder before and after, because that is the assertion that catches the double file.
23. Applying the same note twice is idempotent: one extraction row, one event row.
24. A malformed note moves to `failed\` and is not deleted.
25. A note for an unknown receipt moves to `failed\`.
26. A `category_name` absent from `coa_accounts` stores the name, skips vendor learning, adds a note. Today that is every note.
27. A `discarded` note sets status `discarded` and deletes no files.
28. The consumer runs before `_retry_failed_receipts()`, so a receipt resolved by note is not retried in the same cycle. Drive a real `process_once()` for this one rather than asserting on call order.

Also worth having: a note whose `filed_path` does not exist on disk. Desktop writes the file before the note, so it should not happen, but the pipeline is trusting another application's output and the honest answer is `failed\` with an error rather than a database row pointing at nothing.

---

## When the code is done

- Full suite green under both runners, verbatim output and count. 221 before.
- `python -m py_compile` on every file touched.
- One clean pipeline cycle with an empty `Resolutions\` folder, confirming the consumer is a no-op when there is nothing to do.
- Live database unchanged: 23 `ok`, 3 `discarded`, 49 extraction rows, nothing locked, `resolution_events` still empty.
- Confirm again that the suite writes nothing to `data/*.log`, `logs/*.ndjson`, or the new `Resolutions\` folder.
- Push `feat/console-phase0`, fast-forward only, never `--force`.

## What to report back

1. Per commit: the test, verbatim red, verbatim green, SHA, files changed. Mutation testing where tests cannot come first.
2. Whether the `already_filed` guard fires on a Desktop-filed receipt. This is the question I most want answered.
3. Where you put the note's `resolved_at` for the idempotency check, and why.
4. Every field of the 12.2 schema, and whether your parser accepts and rejects the right things: `action` of `filed` or `discarded`, a null `receipt_id`, backslashes in `filed_path`, amounts as numbers rather than strings, and `values` and `filed_path` absent for a discard.
5. Anything in section 12 that could not be implemented as written. **Say it rather than smoothing it, because the other half of this contract is being built by a session that cannot see yours, and a silent divergence here is the one failure mode nobody would catch until production.**

## What not to do

- Do not call `file_receipt()` on a `filed` note.
- Do not delete anything from `Resolutions\` on any path.
- Do not create `coa_accounts` or any other step 11 table.
- Do not start anything under `console/`.
- Do not give the pipeline's consumer any IMAP awareness. Mailbox sync is parked, section 14.
- Do not edit `IntelliBooks-Desktop-v3.html` or anything under `IntelliBooks\App\`. Reading it to check the contract is fine and encouraged.
- Do not edit `CLAUDE.md`, `RECEIPT_CAPTURE_GUIDE.md` or `2026-07-25_CONSOLE_DESIGN.md`.
- Do not merge into `main` or delete `docs/console-design`.

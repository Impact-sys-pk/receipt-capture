# Claude Code task: step 7b, then step 8, the resolution service

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project. Branch `feat/console-phase0`, currently at `d931045`.

Read sections 3.12, 4.1, 4.2, 4.3 and 5.1 of `2026-07-25_CONSOLE_DESIGN.md`, **including the 2026-07-27 amendments to 4.2 and 4.3 step 6**. Git communication convention applies.

**This is the most subtle work in the build.** The previous session's design notes say so, and the reason is that four callers must end up going through one implementation. Three independent implementations of resolution is what caused the divergence this whole design exists to fix. Take it in the order below and stop and report if it runs long. Half of step 8 done properly and reported is worth more than all of it rushed.

---

## First, your step 6c and 7 report

Verified independently at `d931045`: 134 tests under both runners. Zero occurrences of `OpenAIVisionExtractor` and zero of `engine="openai_vision"` left in `app.py`, so the concrete class really is reachable only through the registry. `config.EXTRACTION_ENGINE` present with the right default and documented. Database unchanged, `details` still non-null on only the two 19 July rows, engine counts still 47 and 2, so no row was rewritten. Your identification of `799cead` is confirmed from its diff.

**Your instinct to check scope by AST rather than by eye was right**, and so was patching `retry_helper.time.sleep` rather than accepting an 18-second suite. A suite people avoid running is a suite that stops catching things. Both are recorded as the standard.

**The line-index script you caught yourself about to run is the more important disclosure.** It would have converted the file's line endings had the assertion passed, and `.gitattributes` would then have made that invisible in `git status` while the blob changed. Saying so is worth more than the near miss cost.

**Your flag 1 is real and it is two call sites, not one.** `app.py:610`, the embedded-image failure path, omits `pipeline_version` as well as `app.py:576`. I checked all eight writes programmatically: those two omit it, the other six pass it. Both are now section 3.12 and step 7b below. Your severity analysis is right and is recorded: one wasted retry, three OpenAI calls, then self-correction, because the retry writes a versioned row through a path that does pass the argument.

**Your flag 3 was worth having.** 10.3 now records that `config.EXTRACTION_ENGINE` is the source of truth and that the phase 2 `settings` table must **replace** that read rather than join it. Your flag 2 is recorded in 3.11 as a deliberate asymmetry.

**One thing you could not have known, and it would have stopped you.** 4.3 step 14 has the service write to `resolution_events`, and section 16 created that table at step 11, three steps after the service. I have moved it to step 8. Also 4.2's signatures supplied `actor` but not `source`, while `resolution_events` has both columns, so the service could not have populated its own audit row. `source` is now a required parameter. Both were in the document from the start.

---

## Step 7b, one commit: `pipeline_version` at the two embedded-image writes

Section 3.12. Pass `pipeline_version=pipeline_version` at `app.py:576` and `app.py:610`. Two keyword arguments.

**Test.** A receipt created through the embedded-image path, landing `needs_review`, is **not** returned by `find_failed_by_version()` on a second pass under the same version. That assertion catches this whole family, which is why it is worth more than asserting the column is non-null.

Do not attempt to clean up the 28 rows in the live database with a NULL `pipeline_version`. Almost all predate the column and they are not this defect.

---

## Step 8: the resolution service

Four commits. Each red before green.

### Commit 1: the `resolution_events` table

Schema exactly as 5.1, added to the existing `executescript` in `worker/database/schema.py` following the `CREATE TABLE IF NOT EXISTS` pattern, plus the index. No migration framework.

**`extraction_id` is nullable and takes no foreign key.** That is deliberate and 5.1 says why: adding one would make the event row fail on an outcome that has no extraction, which is the same class of bug as `b480a7e`. Under the amended 4.3 step 6 a `still_invalid` outcome now does write an extraction row, so the column will usually be populated, but leave both the nullability and the absence of the FK alone.

Add `list_resolution_events(receipt_id)` to `Repository`, per 6.3.

**Verify `init_db()` is still idempotent against the live database**, and say how you checked. Run it twice against a copy, not against `data/receipts.db`.

### Commit 2: `get_resolution_view` and the read side

`worker/resolution/service.py` already exists with `CORRECTABLE_FIELDS`, `Corrections` and `parse_corrections` from `c0ac145`. Add `ResolutionView` and `get_resolution_view(repo, receipt_id)` exactly as 4.2 describes. Read-only, takes no lock, returns `None` if the receipt does not exist.

**The module must still import no Flask, no argparse, nothing under `worker/email/`, and nothing that prints or reads input.** Add a test asserting that, in the same style as your `postprocess` dependency test, because this is the constraint that makes the service reusable and it is the one that erodes quietly.

You will need `get_extractions_for_receipt(receipt_id)` on `Repository`, newest first. It does not exist; `get_extraction_for_receipt` is singular and returns only the latest. Both are needed: the view wants the history and the singular one is used everywhere else.

`get_categorisation_for_receipt` at `repository.py:396` already exists. `categorisation` may legitimately be `None`: the non-ok path saves none.

`effective_gl_code` is `correction_code` if set, else `suggested_code`. `gl_code_options` comes from section 11.1, which needs the CoA loaded at step 12, so for now return the fallback 11.1 specifies, distinct `(nominal_code, account_name)` pairs from the vendor tables, and say in your report that it is the fallback.

`is_locked` is informational only. Do not act on it.

### Commit 3: `resolve_receipt()` and `discard_receipt()`

Follow 4.3's fifteen steps in order. The ones that will bite:

- **Do not reorder steps 7 and 8.** `save_extraction()` before `categorisation_engine.categorise()` and `save_categorisation()`. `categorisations.extraction_id` has a foreign key to `extractions` and getting this backwards caused a live `IntegrityError` fixed in `b480a7e`.
- **Step 6 is amended and this is Paul's decision, not an option.** A correction that still fails validation appends a **new extraction row** carrying the corrected values, the `validation_status` from `validate()` and the notes. It does **not** call `add_validation_note()`. That method mutates an existing row in a table `CLAUDE.md` says is never modified after creation. Leave the method itself and its one remaining caller at `resolve_receipt.py:256` alone: the CLI is step 9 and that is when the method comes out of `Repository`.
- **Step 9 ordering.** `update_categorisation()` after `save_categorisation()` and **before** filing. 11.2 explains it: the sidecar is built from the effective code, so applying the override after filing leaves the file on disk permanently disagreeing with the database. Never overwrite `suggested_code`; that is the audit trail.
- **Step 10.** Build the sidecar with the effective code and name, and populate `category_code`, `category_name` and legacy `category` as `9f5cdad` now does.
- **Step 12.** `remove_review_pair()` from `dce1fdc` after filing. Log and continue if it returns 0.
- **Step 13.** `upsert_client_vendor()` only when `remember_gl_for_supplier` is true. Never automatically: one correction against a misread supplier name would poison the mapping table and the engine's exact-match layer would then apply the wrong code confidently to every future receipt from that vendor.
- **`source` is a required parameter** on both functions, per the amended 4.2. `'console' | 'cli' | 'desktop'`.
- **Event rows are written for `filed`, `discarded` and `still_invalid` only.** Not `not_found`, `stale` or `locked`, because nothing happened. Not `error`, because the state is unknown and a second write risks compounding it.
- Keep the broad `except Exception` logging with `exc_info=True` and returning `error` with `error_detail`. Note that until step 9 builds `worker/logging_setup.py` per 6.5, that traceback only reaches `data/run.log` when the service is called from inside `app.py`. Do not fix that here.
- `error_detail` is for logs only and must never be rendered. `message` is what an operator sees.

**Do not wire the CLI to any of this.** Step 8 is the service with its own tests. Step 9 rewrites `resolve_receipt.py` over it and verifies test 40 by hand. Half-rewiring now would leave two implementations live at once, which is the exact failure this step exists to end.

### Commit 4: tests 13 to 21

Temp database throughout, never `data/receipts.db`, and keep the `config.LOGS_DIR` and `config.RUNS_LOG` redirection.

13. Mismatched `expected_extraction_id` returns `stale` and writes nothing: no extraction row, no event row, no file, and the lock released.
14. A locked receipt returns `locked`.
15. A nonexistent receipt returns `not_found`, does not raise and does not `sys.exit`.
16. A still-invalid correction returns `still_invalid`, appends a new extraction row carrying the notes, leaves the previous row **byte-identical**, writes an event row, and does not file.
17. A successful resolve writes exactly one new extraction row and leaves the original untouched.
18. A GL override leaves `suggested_code` unchanged, sets `correction_code`, and the sidecar **written to disk** carries the corrected code and name. Read the file back rather than asserting on the payload.
19. `remember_gl_for_supplier` false leaves `categorisations_client_vendors` unchanged, row for row.
20. `discard_receipt` sets `discarded`, deletes no file and removes no extraction row.
21. The lock is released on every path including the exception path. Force an exception inside the middle of the flow rather than at the start.

Two more worth having, both cheap: an event row's `actor` and `source` are what the caller passed, and calling `resolve_receipt` twice with the same `expected_extraction_id` gives `filed` then `stale`, which is the optimistic-concurrency property the console depends on.

---

## When the code is done

- Full suite green under both runners, verbatim output and count. 134 before.
- `python -m py_compile` on every file touched.
- One clean pipeline cycle. Live database unchanged: 23 `ok`, 3 `discarded`, 49 extraction rows, nothing locked, and `resolution_events` present and empty.
- Push `feat/console-phase0`, fast-forward only, never `--force`.

## What to report back

1. Per commit: the test, verbatim red, verbatim green, SHA, files changed.
2. How you verified `init_db()` is still idempotent, and against what.
3. The `gl_code_options` fallback you returned and how many pairs it found.
4. Anything in 4.3's fifteen steps that could not be implemented as written, and what you did instead. Do not smooth over a gap: say it.
5. Anything that contradicts the design document, now at v1.3 with 3.11, 3.12 and the 4.2 and 4.3 amendments. Flag it, do not fix it.

## What not to do

- Do not wire `resolve_receipt.py` or anything else to the service. Step 9.
- Do not remove `add_validation_note()` from `Repository`, and do not touch its caller at `resolve_receipt.py:256` or the assertion in `tests/test_resolve_receipt_ordering.py`. Both go at step 9.
- Do not build `apply_resolution_note()` or the back-feed consumer. Step 10.
- Do not create `console_users`, `extraction_usage`, `openai_credit_topups`, `openai_cost_daily`, `coa_accounts`, or the 5.6 indexes. Step 11.
- Do not add a foreign key to `resolution_events.extraction_id`.
- Do not touch `find_failed_by_version()` or the retry cap.
- Do not edit `CLAUDE.md`, `RECEIPT_CAPTURE_GUIDE.md` or `2026-07-25_CONSOLE_DESIGN.md`.
- Do not merge into `main`, delete `docs/console-design`, or edit anything under `IntelliBooks\App\`.

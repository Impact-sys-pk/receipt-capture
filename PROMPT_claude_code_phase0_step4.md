# Claude Code task: phase 0 step 4, Review-pair cleanup, review_count and processed_today

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project. Branch `feat/console-phase0`, currently at `0cae398`.

Read sections 3.5, 3.6 and 3.10 of `2026-07-25_CONSOLE_DESIGN.md` **including the 2026-07-26 amendments**, before you start. The design document is now at v1.2 and the amendment record at the top lists what changed. Git communication convention applies.

---

## First, your step 3 report

Verified independently. In a fresh scratch clone at `0cae398`: 48 tests under `unittest`, 48 under `pytest`, both agreeing, and after a full suite run `logs\` is empty and `data\` holds only `files`, so the isolation still holds with 21 new tests. Live state unchanged: 23 `ok`, 3 `discarded`, 49 extraction rows, nothing locked. `data/run.log` is 287 lines and a grep for `recent-receipt`, `r-file-gone`, `r-api-crash`, `test-receipt-00`, `old-receipt`, `simulated API` and `Temp` returns zero, so the strip was clean and complete. Tip matches origin.

I read `worker/resolution/service.py` in full rather than the summary. It does what you say: presence not truthiness, empty and whitespace-only recorded as an explicit clear, the amount regex rejecting separators, symbols, three decimal places, `nan` and `inf`, the date regex rejecting `2026-7-5` which bare `strptime` would have taken, unknown keys ignored, and a non-mapping `raw` returning a `_form` error rather than raising. No forbidden imports. `CORRECTABLE_FIELDS` matches 4.2 exactly.

**The two `worker.email.reader` lines: you were right to remove them, they stay removed.** `uid=42` moving to Processed Receipts and `uid=1` with no Message-ID both sit inside the same millisecond-contiguous block as the rest, and no real poll on 26 July processed any email, so neither line describes anything that happened. Removing them was the honest call, not the convenient one.

**Your `type=float` removal is accepted** and recorded in 4.2. Keeping two coercion implementations in the same file is precisely what 3.3 exists to remove, and the new error message names the field where argparse named the flag.

**The CLI "clear this field" question: your recommendation is accepted for now.** Leave the flags path as it is, leave interactive alone, revisit at step 9 when the CLI is rewritten over the service. Your reasoning about a magic string at a free-text prompt is right, and the `Clear this field? (y/N)` alternative is the honest version if it is ever wanted. Recorded in 4.2 and 17.4, including your point that step 21 needs a line in the guide about empty-string flags.

**Your `export_bookkeeping.py` findings are confirmed.** I read the file. Both defects are real and I have recorded them in 17.4 along with the answer to the design document's original question, which is that the script exports no category at all, so 11.2 cannot reach it. Nothing to do now.

**Your three flags against the design document, all recorded.**

1. Flag 1 is now **decided by Paul, in your favour**. `add_validation_note()` is retired. A `still_invalid` outcome appends a new extraction row carrying the notes. See 4.3 step 6 as amended, and test 16. **This is step 8 work, not now.** Two consequences to handle then: `resolve_receipt.py:239` is the last caller once `app.py`'s branch B no longer needs it, so the method comes out of `Repository` rather than being left as a tempting mutation, and `tests/test_resolve_receipt_ordering.py:209` currently asserts the mutation happens and must be rewritten to assert the new row instead.
2. Flag 2 is settled in 4.2: `parse_corrections` does not read the GL fields, and the `remember_gl_for_supplier` checkbox question is deferred to step 16 where the form exists. An unchecked HTML checkbox sends no key at all, which is exactly why it belongs with the form.
3. Flag 3 is recorded in 4.2: `receipt_time` has no format rule and is stored as stripped text. Left as it is, because no validation rule reads it, but now stated rather than accidental.

One observation of my own on the same code, no action needed. `_AMOUNT_RE` accepts a leading minus, so a negative amount coerces cleanly and then becomes a validation note from `rules.py` rather than a field error. That is the right split, and it is now written down in 4.2 so nobody "fixes" it later.

---

## What this task is

Design document step 4, plus 3.10 folded in because it is three lines away in the same function. Read the amendments to 3.5 and 3.6 first: they contain implementation detail that is not in the original text and that will cost you a wrong deletion if you skip it.

Two commits, red before green, verbatim output both ways.

---

## Commit 1: remove the Review pair on resolve and on discard

**Where the code goes.** `worker/filing.py`, next to `file_review()` at line 114 which writes the pair. Not in `worker/resolution/service.py`: the service does not exist yet, and this is file I/O that belongs with the other file I/O. `resolve_receipt.py` calls it now, and step 8's service will call the same function. One implementation, four callers, per 4.1.

**Locating the pair. Do not reconstruct the filename.** `file_review()` names the image through `_unique_path()`, so a second review item for the same original filename is written as `{stem}-2{ext}` with its sidecar `{stem}-2{ext}.review.json`. Rebuilding `{stem}{ext}` would miss that file, or delete a different receipt's pair. Instead:

1. Work out the client's Review folder the same way the writer's caller does: `config.CLIENTS_BY_CODE.get(client_code, {}).get('client_name', client_code)`, then `get_client_directory(client_name) / "Review"`. Same lookup, same folder.
2. Read each `*.review.json` in it. Match the receipt on `extracted_values.receipt_id`, which `make_enriched_sidecar()` populates. Fall back to `extracted_values.original_filename` for sidecars written before that, and only when it is an exact match.
3. If nothing matches there, scan the other `Clients\*\Review\` folders for a sidecar whose `extracted_values.receipt_id` matches. Matching on a UUID is exact, so the scan is safe. If you find it under a different client, **log a warning naming both folders** and remove it: that means the receipt was reassigned after the review item was written, which is worth knowing about.
4. Delete the sidecar and the image it belongs to, together. **Never delete an image whose sidecar you have not matched.**
5. Ignore any sidecar with no `receipt_id`. `app.py:666` files a **statement** to Review with `intake.sidecar or {}`, so that payload has no receipt id and no receipt row exists. It must be skipped, not crash the cleanup.
6. Already gone is not an error. Log at INFO and carry on. Return the number of files removed so the caller can log it.

**Also, forward-only:** have `file_review()` write `receipt_id` at the top level of its payload, so a future reader does not have to reach into `extracted_values`. Keep the fallback, because sidecars already on disk will not have it.

**Wire it into `resolve_receipt.py`** on both paths that end a receipt's life in the Review folder: the successful resolve after filing, and the `--duplicate-decision discard` path at around line 185 which sets `discarded` and returns 0. Not on the still-invalid path: that receipt still needs review, so its pair must stay.

**Note while you are here, do not fix:** `write_review_file()` at `worker/filing.py:142` is called from nowhere in tracked source. Dead code that reads like the live writer. Confirm that yourself and say so in your report.

**Tests, design document test 7.**

- A resolved receipt's pair is removed, both files, and the folder is left empty.
- A second review item for the same original filename exists as `{stem}-2{ext}`. Resolving the receipt that owns the `-2` pair removes **only** that pair and leaves the first one untouched. This is the test that matters.
- Missing pair does not raise, and returns zero.
- A sidecar with no `receipt_id` in it is left alone.
- Discard removes the pair. Still-invalid does not.

Temp `CLIENTS_ROOT` throughout, and keep the `config.LOGS_DIR` and `config.RUNS_LOG` redirection.

---

## Commit 2: `review_count` and `processed_today` from the database

`_count_review_items()` at `app.py:121` walks `CLIENTS_ROOT.rglob("Review/*")` and counts every file, so it counts each pair twice and, because nothing was ever removed until commit 1, only ever grows.

- Add `count_receipts_by_status(statuses)` to `Repository`. Section 6.3 already lists it as a required query method, so this is not scope creep, and it keeps SQL out of `app.py`.
- Replace the body of `_count_review_items()`, keep the name, give it a `repo` parameter. The only call site is `app.py:978`, inside `process_once()`, where `repo` is in scope.
- **`review_count` means `needs_review` plus `possible_duplicate`.** Receipts where a human has to decide something. `failed` and `retry_exhausted` are not review items, they are receipts the system could not read, and counting them here would send an operator to look at something there is nothing to look at yet.
- `processed_today` at `app.py:977` is `stats.get("receipts_created", 0)`, which is "created in this run", not "today". Use `repo.count_processed_today()`, which already does the real thing and is wired to nothing.
- Leave `_write_pipeline_status()` and the shape of `pipeline-status.json` alone. IntelliBooks Desktop reads that file.

**Tests, design document test 8.**

- `review_count` equals the count of `needs_review` plus `possible_duplicate` and ignores `failed`, `retry_exhausted`, `ok` and `discarded`. Seed one of each.
- Removing a Review pair from disk does not change the count, because the count no longer comes from disk.
- `processed_today` counts receipts created today regardless of which run created them, and is not the current run's `receipts_created`. Seed a receipt created today in an earlier run and assert the difference.

---

## When the code is done

- Full suite green under both runners, verbatim output and count.
- `python -m py_compile` on every file touched.
- One clean pipeline cycle. Then read `IntelliBooks\pipeline-status.json` and report `review_count` and `processed_today` verbatim. With the live database at 23 `ok` and 3 `discarded`, `review_count` must be **0** and `processed_today` must be **0**. If either is not, stop and report before pushing.
- Confirm the live database is unchanged: 23 `ok`, 3 `discarded`, 49 extraction rows, nothing locked.
- Confirm `Clients\Paul Keating\Review\` and `Clients\Test\Review\` are still empty and that nothing outside a temp directory was deleted by the tests.
- Push `feat/console-phase0`, fast-forward only, never `--force`.

## What to report back

1. Per commit: the test, verbatim red, verbatim green, SHA, files changed.
2. The `pipeline-status.json` values before and after.
3. Confirmation that `write_review_file()` is dead code, or evidence that it is not.
4. Whether any sidecar already on disk in a `Review` folder lacks `extracted_values.receipt_id`, since that decides whether the fallback path is theoretical or real. Both Review folders are empty, so check the filed `.json` sidecars under `Clients\*\Receipts\` instead and report what you find.
5. Anything that contradicts the design document at v1.2. Flag it, do not fix it.

## What not to do

- Do not retire `add_validation_note()` or change any of its callers. Decided, but step 8.
- Do not add any further function from 4.2. Step 8.
- Do not touch the sidecar `category_name` work, the postprocess move or the extractor factory. Steps 5, 6, 7.
- Do not change `export_bookkeeping.py`, including the two defects in it.
- Do not delete `write_review_file()` in this commit. Report it.
- Do not delete anything from a live `Review` folder by hand. The only live pair was removed on 26 July and both folders are empty.
- Do not edit `CLAUDE.md`, `RECEIPT_CAPTURE_GUIDE.md` or `2026-07-25_CONSOLE_DESIGN.md`.
- Do not merge into `main`, delete `docs/console-design`, or touch anything under `IntelliBooks\App\`.

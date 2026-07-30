# Claude Code task: step 0 recovery, get onto the right branch before the console build

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project.

**Supersedes `PROMPT_claude_code_step0_housekeeping.md`.** That prompt assumed `main` was six commits behind the working branch. It is 42 behind and diverged by one. Do not follow it. If you have already read it, discard its steps 5 and 6.

**This task contains no code changes.** It is git and filesystem recovery. If you find yourself editing a `.py` file, stop and ask.

Read `CLAUDE.md` first. Its git communication convention applies to every command below: terminal command, plain English explanation, VS Code GUI equivalent.

---

## What happened, verified before you were given this

The working tree is on the wrong line of history.

- `HEAD` is `docs/console-design` at `2dd147b`, cut from `main` at `965cb24`.
- `main` is 42 commits behind `fix/imap-message-id-dedup` and ahead by one.
- So the checkout you are sitting in is missing the whole system built since May: `resolve_receipt.py`, `worker/extraction_pipeline.py`, `worker/extraction/retry_helper.py`, `worker/email/alerts.py`, `RECEIPT_CAPTURE_GUIDE.md`, `.gitattributes`, and three regression tests. Confirmed: `app.py` in the working tree contains no `_retry_failed_receipts` at all, so phase 0 bug 3.1 in `2026-07-25_CONSOLE_DESIGN.md` does not exist in this tree.
- Nothing is lost. `fix/imap-message-id-dedup` is at `e863b617b948e3e46a42a4240528047aa30641b2` locally and the same on `origin`.
- The two design-doc commits to keep are `af0c76e` (design spec, back-feed prompt, CoA draft) and `2dd147b` (consultant handover).

**The merge to `main` is cancelled.** It was agreed when `main` looked six commits behind. It is a different operation now and gets its own session. We stack on `fix/imap-message-id-dedup`.

## Approval already granted

Paul approves: the stash in step 2, the branch switch in step 3, the two cherry-picks in step 4, creating and pushing `feat/console-phase0` in step 6, the two file deletions in step 7, and pushing `fix/imap-message-id-dedup` **only if it is a fast-forward**.

Not approved, ask first: any merge into `main`, any `--force`, `reset --hard`, `clean -f`, `branch -D`, `checkout .`, dropping a stash, or deleting `docs/console-design`.

---

## Step 1: report the current state, change nothing

- `git status`, `git branch -vv`, `git log --oneline -3`
- `git fetch origin`, then confirm `git rev-parse fix/imap-message-id-dedup origin/fix/imap-message-id-dedup` both give `e863b617b948e3e46a42a4240528047aa30641b2`. **If the remote differs, stop and report.** That ref is the only copy of the 13 missing files.
- Whether the pipeline is running: check for `pipeline.lock` under the OneDrive `IntelliBooks\` root and whether that pid is alive. Verified absent at 13:10 today, so it should not be running. If it is, stop it before step 3 and say how.
- Confirm from `data/receipts.db`, read-only, that nothing has status `failed` or `needs_review`. Verified 23 `ok` and 3 `discarded` at 13:15 today. **If anything is `failed` or `needs_review`, stop and tell Paul**, because the branch switch changes `pipeline_version` and each retry costs real OpenAI calls.

---

## Step 2: preserve the working-tree modifications, then report what they are

`git status` shows about 30 tracked files modified. **Do not discard them until the report is agreed.**

1. Save a patch outside the repository first:
   `git diff > C:\LastingImpact\_recovery_2026-07-26_pre_switch.patch`
2. Report the result of `git diff --ignore-all-space --stat`.

Expected result: empty. Every one of those files differs by line endings only, CRLF on disk against LF in the blob, because `.gitattributes` was added in `c11d367` which is not on `main`'s line. Something rewrote those files with CRLF at about 12:36 today. There is no content change.

**If `git diff --ignore-all-space --stat` is not empty, stop and report exactly what the real change is.** That would mean genuine uncommitted work is stranded here.

3. Once confirmed whitespace-only, stash it so the switch is clean, and keep the stash:
   `git stash push -u -m "pre-recovery CRLF-only diff, 2026-07-26"`
   Do **not** use `-u` if it would sweep up `2026-07-25_HANDOVER_TO_NEXT_SESSION.md`, `PROMPT_claude_code_step0_housekeeping.md`, `PROMPT_claude_code_step0_recovery.md`, `2026-07-24_HANDOVER_TO_NEXT_SESSION.md` or `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md`. Those five untracked files must stay on disk. Prefer a plain `git stash push` and leave untracked files alone.
   Report `git stash list`. Do not drop the stash.

### Back up the logs before you switch, this one is easy to miss

`logs/receipt_events_FIRM001.ndjson`, `logs/receipt_events_INTELLITAX.ndjson` and `logs/runs.ndjson` are tracked on `main`'s line and untracked on `fix/imap-message-id-dedup` (removed by `0859817`). A branch switch **deletes** files tracked at `HEAD` and absent from the target, so all three will be removed from disk.

They have already been damaged once. The 12:36 checkout overwrote them with `main`'s older blobs: `runs.ndjson` on disk holds 324 records ending 19 July 16:03, where the last tracked version on the working line (`0859817^`) holds 968 records ending 24 July 13:20.

Do this:

1. Copy the whole `logs\` folder to `C:\LastingImpact\_recovery_2026-07-26_logs_backup\`.
2. After the switch in step 3, restore the fullest available version into `logs\`:
   - `git show 0859817^:logs/runs.ndjson > logs\runs.ndjson`
   - `git show 0859817^:logs/receipt_events_FIRM001.ndjson > logs\receipt_events_FIRM001.ndjson`
   - `git show 0859817^:logs/receipt_events_INTELLITAX.ndjson > logs\receipt_events_INTELLITAX.ndjson`
   - Write them as UTF-8 without a BOM, one JSON object per line, LF endings. Confirm the line counts are 968, 64 and 53.
3. Report that run records between 24 July 13:20 and 25 July are unrecoverable. Nothing in the database, no receipt and no client file is affected. This is log history only.

---

## Step 3: check out the working branch

`git switch fix/imap-message-id-dedup`

Then confirm, and report:

- All 13 files are back: `.gitattributes`, `EMAIL_PROCESSING_MICROSTEPS.md`, `MULTIFIRM_EMAIL_FORWARDING_ANALYSIS_AND_FINDINGS.md`, `RECEIPT_CAPTURE_GUIDE.md`, `check_missing_categorisation.py`, `resolve_receipt.py`, `retroactive_categorise.py`, `tests/test_auto_retry_cap.py`, `tests/test_email_dedup_identity.py`, `tests/test_resolve_receipt_ordering.py`, `worker/email/alerts.py`, `worker/extraction/retry_helper.py`, `worker/extraction_pipeline.py`.
- `git status` is clean apart from the untracked files listed in step 2 and the restored logs.
- `python -m pytest -q` gives **17 passed**. Report the actual output. Anything other than 17 of 17, stop.
- `app.py` now contains `_retry_failed_receipts`.

Do the log restore from step 2 at this point.

---

## Step 4: cherry-pick the two design-doc commits

```
git cherry-pick af0c76e
git cherry-pick 2dd147b
```

- `af0c76e` adds `2026-07-25_CONSOLE_DESIGN.md`, `PROMPT_intellibooks_resolution_backfeed.md`, `chart_of_accounts_DRAFT.csv`.
- `2dd147b` adds `HANDOVER_consultant_chat.md`.
- Both are docs only, verified: 1,135 and 180 insertions, no code.

**Resolve nothing silently.** Any conflict, stop, report the conflicting hunk, wait. A clean run was tested in a scratch clone with no conflicts, so a conflict means something has changed since 13:15 today and is worth knowing about.

Then run `python -m pytest -q` again and confirm still 17 of 17.

---

## Step 5: leave `docs/console-design` alone

Do not delete it, do not rename it, do not push it. It has no upstream and it is the safety net. It costs nothing.

---

## Step 6: create the working branch

Off `fix/imap-message-id-dedup` **after** the cherry-picks, not off `main`:

```
git switch -c feat/console-phase0
git push -u origin feat/console-phase0
```

Also push the two cherry-picked commits on `fix/imap-message-id-dedup`, **only if it is a fast-forward**. Check with `git push --dry-run` first and report what it says. Never `--force`.

Do not start any phase 0 work in this session.

---

## Step 7: delete one stale file pair outside the repo

**Warn Paul, get a yes, then do it.** It is in OneDrive, outside the repository.

```
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\Paul Keating\Review\
    T3_needs_review_vat_mismatch.png
    T3_needs_review_vat_mismatch.png.review.json
```

The pre-conditions were verified at 13:15 today. Re-verify them yourself before deleting and report what you found:

- Receipt `1658b47c-ce4d-4fed-afa2-832167faa7dd` has status `ok`.
- Its `filed_path` is `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\Paul Keating\Receipts\2026-27\2026-07-20_t3-test-supplies-ltd_96.00.png`.
- That file exists on disk.

If any of the three is not true, stop and report.

Why it matters: IntelliBooks Desktop reads that Review folder and still shows the item as needing review. Filing it there would create a second copy of an already filed receipt, in a different place with a different sidecar, and the database would not know. That is bug 3.5 in the design document and this is its live instance.

Delete nothing else from any `Review` folder. `Clients\Test\Review\` is already empty. This is the only known stale pair.

---

## Step 8: restart the pipeline and confirm one clean cycle

Restart it the way Paul normally does, `IntelliBooks.bat` or the scheduled task, and confirm from the log that one full cycle completes with no errors and the retry pass found nothing to retry.

`config.get_pipeline_version()` shells out to `git rev-parse --short HEAD`, so the version recorded should now be the short hash of the `2dd147b` cherry-pick on `feat/console-phase0`. Report the hash you see and confirm it matches. It must not be `2dd147b` or `965cb24`.

---

## What to report back

1. The state found in step 1, including both SHAs for the imap branch and the live status counts.
2. The result of `git diff --ignore-all-space --stat`, the patch file path, and `git stash list`.
3. The log backup path, the restored line counts, and confirmation of the unrecoverable window.
4. That all 13 files returned, and the verbatim pytest output, twice: after the switch and after the cherry-picks.
5. The cherry-pick outcome and the new tip SHAs for `fix/imap-message-id-dedup` and `feat/console-phase0`, and what `git push --dry-run` reported.
6. Whether the Review pair was deleted and the three checks you ran first.
7. One clean pipeline cycle, with the `pipeline_version` short hash.
8. Anything you noticed that contradicts `2026-07-25_CONSOLE_DESIGN.md`. Flag it, do not fix it.

## Already answered, do not re-derive, but flag any contradiction

`main` holds exactly one commit that `fix/imap-message-id-dedup` does not: `965cb24`, a merge commit. Both its parents, `53c4d4a` and `10d5742`, are ancestors of the imap branch, and its tree hash `6721afe8` is byte-identical to a recomputed clean merge of those two parents, so it is not an evil merge and contributes no content. The only tracked files on `main` and absent from the imap branch are the three `logs\*.ndjson` files, deliberately untracked by `0859817`. Nothing on `main` is needed. A future catch-up merge was tested in a scratch clone: clean, no conflicts, 17 of 17 tests pass afterwards. That merge is for another session.

## What not to do

- No code changes. No `.py` edits.
- Do not start phase 0. Section 16 of `2026-07-25_CONSOLE_DESIGN.md` has the order.
- Do not merge anything into `main`.
- Do not delete `docs/console-design`, the stash, or the patch file.
- Do not touch `IntelliBooks-Desktop-v3.html` or anything under `IntelliBooks\App\`. A separate session owns those.
- Do not edit `IntelliBooks-System-Specification.md` or `IntelliBooks-System-Overview.md`.
- Do not delete or modify any receipt, extraction or categorisation row. Step 7 deletes two files on disk and nothing in the database.

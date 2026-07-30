> **SUPERSEDED 2026-07-26. Do not paste this into Claude Code.** Use
> `PROMPT_claude_code_step0_recovery.md` instead. This prompt assumed `main` was six
> commits behind `fix/imap-message-id-dedup`. It is 42 behind and diverged by one, and
> the working tree had been switched to a branch cut from `main` that is missing 13 files
> of the built system. Steps 5 and 6 below would have merged a stale `main` and branched
> off it. Kept for the decision trail only.

# Claude Code task: step 0 housekeeping before console build

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project.

**This task contains no code changes.** It is repository and filesystem housekeeping to get to a clean starting point. If you find yourself editing a `.py` file, stop and ask.

Read `CLAUDE.md` first. Its git communication convention applies to everything below: for every git command, give the terminal command, a plain English explanation, and the VS Code GUI equivalent.

---

## Approval already granted

`CLAUDE.md` says you must not run `git commit`, `git push`, or create branches without explicit approval. **Paul has approved the specific operations in this task**: the commit in step 2, the merge in step 5, the branch creation in step 6, and the pushes in steps 5 and 6.

You still need to ask before anything not listed here, and before any destructive operation (`reset --hard`, `push --force`, `clean -f`, `branch -D`, discarding uncommitted work).

---

## Step 1: report the current state

Before changing anything, report:

- `git status` and `git branch -vv`
- How far `fix/imap-message-id-dedup` is ahead of `main`, and whether `main` can fast-forward
- Whether the pipeline is currently running (check for `IntelliBooks\pipeline.lock` under the OneDrive root and whether that pid is alive; `app.py` has `_is_process_running()` you can reuse)
- Confirm from `data/receipts.db` that nothing has status `failed` or `needs_review`

That last check matters. Merging changes the git short hash, which is `pipeline_version`, which triggers one auto-retry pass over anything `failed` or `needs_review`. As of 2026-07-25 there is nothing in those states, so the pass should be a no-op. **If you find anything there, stop and tell Paul before merging**, because each retry costs real OpenAI calls.

---

## Step 2: commit the design documents

Four untracked files in the repo root need handling.

**Commit these three:**

- `2026-07-25_CONSOLE_DESIGN.md`
- `PROMPT_intellibooks_resolution_backfeed.md`
- `chart_of_accounts_DRAFT.csv`
- `PROMPT_claude_code_step0_housekeeping.md` (this file)

**Delete these three, do not commit them.** All superseded, all untracked, so a plain file delete with no git involvement:

- `2026-07-25_DASHBOARD_DESIGN.md` — superseded by `2026-07-25_CONSOLE_DESIGN.md`. Keeping both risks the wrong one being picked up.
- `2026-07-24_HANDOVER_TO_NEXT_SESSION.md` — Paul has decided to delete it.
- `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` — folded into `RECEIPT_CAPTURE_GUIDE.md`, Paul has decided to delete it.

Suggested commit message:

```
docs(console): console design spec, back-feed contract, phase 0 bugs

Supersedes the earlier dashboard design draft. Reframes as a practice
console with receipts as module 1 and chart of accounts reserved as
module 2. Specifies the resolution back-feed contract between the
pipeline and IntelliBooks Desktop. Documents ten phase 0 bugs including
the auto-retry loop that re-extracts on every poll rather than once per
version.

Files: 2026-07-25_CONSOLE_DESIGN.md, PROMPT_intellibooks_resolution_backfeed.md,
       PROMPT_claude_code_step0_housekeeping.md, chart_of_accounts_DRAFT.csv
Deleted: 2026-07-25_DASHBOARD_DESIGN.md, 2026-07-24_HANDOVER_TO_NEXT_SESSION.md,
         RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md
```

---

## Step 3: delete one stale file pair outside the repo

**Warn Paul and get a yes before doing this, then do it.** It is outside the repository, in OneDrive.

```
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\Paul Keating\Review\
    T3_needs_review_vat_mismatch.png
    T3_needs_review_vat_mismatch.png.review.json
```

Why they should go: receipt `1658b47c` (`T3_needs_review_vat_mismatch.png`) has status `ok` with `filed_path` set. It was resolved and filed on 25 July. This Review pair is a leftover, because `resolve_receipt.py` has no awareness of the Review folder. That is bug 3.5 in the design document, and this is the live instance of it.

Why it matters that they go now: IntelliBooks Desktop reads that folder and shows the item as "Needs Review". Filing it there would create a **second** copy of an already-filed receipt, in a different location with a different sidecar, and the database would not know. That is exactly the double-filing path the back-feed contract exists to prevent.

Confirm before deleting that receipt `1658b47c` really is `ok` with a non-null `filed_path`, and that the file named in `filed_path` exists on disk. If either is not true, stop and report.

Do not delete anything else from any `Review` folder. This is the only known stale pair.

---

## Step 4: stop the pipeline

If it is running, stop it before merging. Merging rewrites the working tree, and `config.get_pipeline_version()` shells out to `git rev-parse --short HEAD` on every cycle, so a poll landing mid-merge could record a misleading version against an extraction.

Tell Paul how to stop it based on how it is running: a `cmd` window titled "IntelliBooks Pipeline" started by `IntelliBooks.bat`, or a Windows scheduled task. Do not kill processes yourself without saying which one and why.

---

## Step 5: merge to main

Merge `fix/imap-message-id-dedup` into `main` and push.

Recommend `--no-ff` or a fast-forward based on what you found in step 1, and explain your reasoning in one line. Six commits of verified work with three bug fixes and a regression test is arguably worth a merge commit for a legible history, but say what you think.

Give the terminal commands, the plain English, and the VS Code GUI route, per `CLAUDE.md`.

If there are conflicts, stop and report. Do not resolve them without asking.

After merging, confirm `git log --oneline -8` on `main` shows the expected commits, and that `origin/main` matches local `main`.

---

## Step 6: create the working branch

Create and push a new branch off `main` for the phase 0 work:

```
feat/console-phase0
```

Do not start any of the phase 0 fixes in this session. The branch is just the starting point.

---

## Step 7: restart the pipeline and confirm one clean cycle

Restart it and confirm from `data/run.log` that one full cycle completes with no errors, and that the retry pass found nothing to retry. The `pipeline_version` in the log should now be the merge commit's short hash.

---

## What to report back

1. The state you found in step 1.
2. What you committed and what you deleted.
3. Whether the Review pair was deleted, and the verification you did first.
4. The merge outcome and the new `main` head.
5. The new branch name and that it is pushed.
6. That one clean pipeline cycle ran, with the new `pipeline_version`.
7. Anything you noticed that contradicts `2026-07-25_CONSOLE_DESIGN.md`. Flag it, do not fix it.

## What not to do

- No code changes. No `.py` edits.
- Do not start phase 0. That is the next session, and section 16 of the design document has the order.
- Do not touch `IntelliBooks-Desktop-v3.html` or anything in `IntelliBooks\App\`. A separate session owns those.
- Do not edit `IntelliBooks-System-Specification.md` or `IntelliBooks-System-Overview.md`. Being updated separately.
- Do not delete or modify any receipt, extraction or categorisation row in the database. Step 3 deletes two files on disk, nothing in the database.

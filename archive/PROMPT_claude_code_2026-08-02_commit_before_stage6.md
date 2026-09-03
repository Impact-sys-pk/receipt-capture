# AUTOMATIC task: commit amendment 85, before the pipeline is started

**Written 2026-08-02 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

**This is a documentation commit. Nothing is edited and no code is touched.** Staging, one commit, a push, a verification.

**Do not start the pipeline.** Stage 6 is Paul's and it is the next step after this one.

---

## Why now rather than later

`app.py:1207` calls `config.check_git_status_on_startup()`, which runs `git status --porcelain` and, if anything is uncommitted, logs

    uncommitted changes detected at startup; pipeline_version=<hash> may not reflect working tree

It warns and continues, so this is not a blocker. **But the next thing that happens is the first clean end-to-end run of the rebuilt system, and its log is the evidence for stage 6.** A warning that is only there because a documentation file was left uncommitted is noise Paul has to reason past on the one run where the log matters.

---

## Task 1. Confirm the starting state

    git --no-optional-locks status --short

**Expect exactly two entries:**

     M 2026-07-25_CONSOLE_DESIGN.md
    ?? PROMPT_claude_code_2026-08-02_commit_before_stage6.md

Plus `?? RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md`, which is an old untracked draft, is Paul's call, and **must still show `??` when you finish.**

**Stop and report if you see anything else**, in particular any modified `.py` file. Stage 5 is complete and committed, so nothing in the code should be dirty.

**If `.git\index.lock` exists**, check `tasklist /FI "IMAGENAME eq git.exe"` shows no tasks, then `del .git\index.lock`. A Cowork session's Linux sandbox can create that file but cannot remove it. See the third trap in `CLAUDE.md`.

---

## Task 2. One commit

    git add 2026-07-25_CONSOLE_DESIGN.md PROMPT_claude_code_2026-08-02_commit_before_stage6.md

**Two paths.** The second is this prompt.

    docs: amendment 85, stage 5 complete and its six-step check passed

    Both halves of stage 5 are built and the check was run by Paul on
    2026-08-02. The four coordinated flips work in both directions and the
    interim contract of amendment 75 survived the move: a receipt filed from
    Review still lands in Clients\{client name}\Receipts\{tax year}\ with its
    sidecar, and Desktop still reads it.

    Recorded from evidence rather than from a report. Three notes in
    Intellibills\Resolutions\, two reading "action":"filed" with filed_path
    under Clients\Test 3\Receipts\2026-27\ and one reading "action":
    "discarded" with no path. Intellibills\Review\TEST3\ empty and both
    decoys untouched. The decoys are what make it a check rather than a
    demonstration: a folder that is never found produces the same empty
    screen as a folder read correctly.

    Step 5 had to be run twice. Both probes were filed on the first pass, so
    the row Delete was pressed on was a filed receipt and the app correctly
    showed the books-delete message. Nothing was wrong with the code. The
    check had been arranged so that one wrong button press silently converted
    the discriminating step into a different test that passes. A step whose
    subject can be consumed by an earlier step should come first or carry its
    own fixture.

**Then push.** Branch `feat/console-phase0`. `git push --dry-run` first, confirm fast-forward, **never `--force`**.

---

## Verify, and quote the output

    git --no-optional-locks status --short
    git log --format="%h %ad %s" --date=iso -3

Confirm and state each:

- One commit on top of `41cba11`.
- **`git --no-optional-locks status --porcelain` returns nothing except the untracked draft.** This is the exact command `app.py` runs at startup, so it is the check that matters: quote its output.
- Push was a fast-forward.
- No `.py` file in the commit. Check with `git show --stat`.

---

## Stop and ask about

1. **Any edit to any file.** This task stages and commits; it does not change content.
2. Any modified `.py` file in the working tree.
3. Anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` or `C:\Intellibills\`. Nothing here goes near either.
4. Any write to the database, which now lives at `C:\Intellibills\db\receipts.db`.
5. Starting the pipeline. Not in this task.
6. A push that is not a fast-forward.

**Flag, do not fix.**

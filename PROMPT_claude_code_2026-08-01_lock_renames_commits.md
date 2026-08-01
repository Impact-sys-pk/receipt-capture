# AUTOMATIC task: clear a stale git lock, correct two filenames, and commit the 31 July and 1 August documentation

**Written 2026-08-01 by the consultant session. Paste this whole file into Claude Code.**

This runs under the `AUTOMATIC Task Mode` section of `CLAUDE.md`. Proceed through the git operations named below without stopping to ask. The short "stop and ask" list in that section still applies and one item on it will come up, at task 4.

**This task is documentation and git only. It changes no Python, no test and no behaviour.** If you find yourself editing a `.py` file, you have misread it.

**Report once at the end, not at each step.**

---

## Why this exists

Two problems, one of them blocking.

**A stale lock file is blocking every git write in this repository.** `C:\LastingImpact\receipt_capture\.git\index.lock` exists, is 0 bytes, and was left behind by a Cowork session whose Linux sandbox could create it but could not unlink it. Nothing has been committed since `ac2d1be` because of it.

**Two committed filenames are dated a day early.** Both were written on 31 July and named for the 30th. Amendment 78 of `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md` records the audit that established this and is worth reading before you start, because it also explains why the fix is two renames and not a blanket redating.

---

## Task 1. Clear the stale lock

**Check first that it is genuinely stale.** Confirm no git process is running:

    tasklist /FI "IMAGENAME eq git.exe"

Expect no tasks. Then:

    del .git\index.lock

**Plain English:** removes a marker git writes to stop two processes changing the index at once. The file is empty and no git process holds it, so nothing is lost.

**In VS Code GUI:** the Source Control panel reports the same error and cannot clear it. Use the integrated terminal, `Ctrl+'`, for this one.

**Verify:** `git status --short` runs with no `index.lock` warning and reports six entries: four modified and two untracked.

**Stop if** `tasklist` shows a running `git.exe`. That would mean the lock is live and this diagnosis is wrong.

---

## Task 2. Correct the two filenames

Both are tracked and both are in `ac2d1be`, so use `git mv` and the rename is recorded rather than showing as a delete and an add.

    git mv 2026-07-30_HANDOVER_consultant_chat_4.md 2026-07-31_HANDOVER_consultant_chat_4.md

    git mv PROMPT_desktop_session_start_2026-07-30.md PROMPT_desktop_session_start_2026-07-31.md

**`PAUL_CHECKS_2026-07-30.md` is correctly dated. Do not rename it.** Its mtime is 2026-07-30 10:02 and the checks it records were run that morning. Amendment 78 states this explicitly so that nobody renames it for consistency.

**Verify:** `git status --short` shows both as `R` and neither old name exists on disk.

---

## Task 3. Fix the stale self-references inside the renamed handover

Renaming the file leaves three references to the old name inside it, at approximately lines 61, 66 and 186 of `C:\LastingImpact\receipt_capture\2026-07-31_HANDOVER_consultant_chat_4.md`. Line numbers will have moved; search for the strings.

**Change in that file only:**

- `2026-07-30_HANDOVER_consultant_chat_4.md` becomes `2026-07-31_HANDOVER_consultant_chat_4.md`, including inside the `git add` line in its section 3.
- `PROMPT_desktop_session_start_2026-07-30.md` becomes `PROMPT_desktop_session_start_2026-07-31.md`.

**Do not touch any other file.** In particular, `C:\LastingImpact\receipt_capture\2026-07-31_PLAN_reset_and_restructure.md` quotes a `git status` output verbatim as a record of state on 31 July, and changing a filename inside a quoted output would falsify it. The consultant session owns that file and will handle it.

**Verify:** `findstr /s /c:"2026-07-30_HANDOVER" *.md` and `findstr /s /c:"PROMPT_desktop_session_start_2026-07-30" *.md` return matches only in `2026-07-31_PLAN_reset_and_restructure.md`, and none in the renamed handover.

---

## Task 4. One thing to report, not to fix

**Both renamed files still say `Written 2026-07-30` in their own headers, and the handover's body describes its work as happening on 30 July.** That is the same day-early error as the filenames.

**Do not edit those headers.** Paul has not ruled on it, the handover is the induction a fresh session reads, and its body distinguishes a morning that genuinely was 30 July from an afternoon that was 31 July, so a blanket change would be wrong in exactly the way amendment 78 warns about.

**Report what you find:** the line number and exact wording of each internal date claim in the two renamed files that refers to 30 July, so Paul can rule on them as a set.

---

## Task 5. Add the sandbox rule to `CLAUDE.md`

`CLAUDE.md` has a section headed **"Two traps that cost hours"** near the end of "How this project is worked". It becomes three.

**Rename the heading to "Three traps that cost hours"** and add this as a third bullet, after the existing one about the dirty working tree:

> - **Do not run git write commands from the Linux sandbox.** Reads are safe and are what it is for. `git add`, `git commit`, `git mv` and anything else that takes the index lock must be run on Windows. The sandbox can create a file in the mounted folder but cannot unlink one, so git leaves `.git\index.lock` behind and cannot clean it up, and **every git write in the repository fails until somebody notices and deletes it by hand.** That is worse than the trap above, which only misleads. Clear it with `del .git\index.lock` from the repository root, after checking with `tasklist /FI "IMAGENAME eq git.exe"` that no git process is running.

**Leave the rest of `CLAUDE.md` alone.** It already carries an uncommitted edit of Paul's to the **File Storage** bullet, recording amendment 77. That edit is his and is correct; commit it, do not revise it.

---

## Task 6. Commit, in four commits, staging by name

**Never `git add .`** `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` is an untracked draft and is Paul's call, not this task's. It must still show as `??` when you finish.

Run `git status --short` between commits and confirm each one took what was intended and nothing else.

### Commit 1, the design document and the plan

    git add 2026-07-25_CONSOLE_DESIGN.md 2026-07-31_PLAN_reset_and_restructure.md PROMPT_claude_code_2026-08-01_lock_renames_commits.md

    docs: the reset and restructure plan, and amendments 75 to 78

    Also carries the prompt this work was done from.

    Adds the plan section 17.5a required before anything is deleted: the
    verified before-state, a gate, actions, a verification and a stop
    condition for each of the six stages, and nine decisions that must be
    answered before stage 3. Four are now closed.

    Amendment 75, the interim exception to 18.2b. Clients\{name}\Receipts\
    is today the only route a receipt has from capture into the books, and
    18.3's replacement exists in neither codebase, so the pipeline keeps
    writing there until an inbox handoff passes a six-check acceptance test.
    Two touchpoints are frozen for the duration.

    Amendment 76, the word "data" is used on neither side and DATA_DIR is
    removed rather than repointed, because a shared parent is what let the
    live database drift towards OneDrive. A third consumer in
    worker/logging_setup.py makes it four constants rather than three.

    Amendment 77, the document store keeps the shape the code already
    writes, {CODE}\{year}\{month}\, and Attachments\ is aligned to it.

    Amendment 78, a dating audit. The session that produced amendments 65
    to 74 spanned 30 and 31 July, so its dates are not uniformly wrong.

### Commit 2, the renames

`git mv` at task 2 already staged both renames. This stages the content edit from task 3 on top of them.

    git add 2026-07-31_HANDOVER_consultant_chat_4.md

    docs: correct two filenames dated a day early

    Both files were written on 31 July and named for the 30th. Renamed with
    git mv, so ac2d1be remains the source of the rename, and their internal
    self-references updated to match.

    Their own "Written 2026-07-30" headers are deliberately unchanged and
    are reported instead. The handover distinguishes a morning that was
    genuinely 30 July from an afternoon that was 31 July, so a blanket
    change would repeat the error amendment 78 records.

    PAUL_CHECKS_2026-07-30.md is correctly dated and is untouched.

### Commit 3, `CLAUDE.md`

    git add CLAUDE.md

    docs: the file storage layout, and a third trap

    Records Paul's correction to the File Storage bullet: the code writes
    client code first, then year and month, with no day level, which
    neither this file nor the design document said. Amendment 77.

    Adds the third trap. A Cowork session's Linux sandbox can create a file
    in the mounted folder but cannot unlink one, so a git write leaves
    .git\index.lock behind and every subsequent git write in the repository
    fails until it is deleted by hand. Nothing was committed for a day and
    a half because of it.

### Commit 4, the stray section 0

    git add 2026-07-29_HANDOVER_consultant_chat_3.md

    docs: commit a section 0 that has survived three sessions uncommitted

    22 lines on the environment and the four gitignored things a fresh
    clone lacks. Written by none of the sessions that have since read the
    file, and each declined to commit it as not theirs, which is how a good
    addition gets lost. Committed now rather than lost again.

**Then push.** Branch `feat/console-phase0`. Check with `git push --dry-run` first and confirm it is a fast-forward. **Never `--force`.**

---

## Verify at the end, and this is the point of the whole task

    git log --format="%h %ad %s" --date=iso -6

**Quote the output in your report.** Amendment 78's conclusion is that an author date is the only timestamp that survives a wrong clock, a recreated workspace or a session running past midnight, and that between two people only one commit was made in two days. These four commits are the first application of that. The dates on them are the evidence nobody had for amendments 67, 75 and 76.

Also confirm:

- `git status --short` shows a clean tree apart from `?? RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md`.
- `.git\index.lock` does not exist.
- `git log --follow --oneline 2026-07-31_HANDOVER_consultant_chat_4.md` reaches `ac2d1be`, which proves the rename was recorded rather than a delete and an add.

---

## Stop and ask about

The `AUTOMATIC` list in `CLAUDE.md` is unchanged and outranks this file. In particular:

1. **Anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`.** Nothing in this task goes there. If a step seems to, you have misread it.
2. **Any write to `data/receipts.db`.** Nothing here touches it.
3. **Any change to a `.py` file or a test.** Nothing here touches those either.
4. **`git status` showing a file you did not expect.** Report it rather than staging or reverting it.
5. **A push that is not a fast-forward.**

**Flag, do not fix.** If you notice something else wrong on the way, report it at the end. That rule has surfaced more real defects on this project than any other.

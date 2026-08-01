# AUTOMATIC task: clear the lock again, then commit four documentation files

**Written 2026-08-01 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Do not stop to ask about the git operations below. The short "stop and ask" list in that section still applies.

**Documentation and git only. No Python, no tests, no behaviour.** If you find yourself editing a `.py` file you have misread this.

**The files are already edited. Do not change their content.** Your job is the lock, the staging, one commit and the push. Report once at the end.

---

## Task 1. Clear the stale lock, again

`C:\LastingImpact\receipt_capture\.git\index.lock` exists, 0 bytes, dated `2026-08-01 11:57:34`. **The consultant session created it a second time by running a bare `git status` from its Linux sandbox**, minutes after adding the trap to `CLAUDE.md` warning against exactly that. The bullet was also wrong and has been corrected in this commit: `git status` refreshes the index stat cache and takes the lock, so it is not a read.

    tasklist /FI "IMAGENAME eq git.exe"

Expect no tasks. Then:

    del .git\index.lock

**Plain English:** removes an empty marker git uses to stop two processes writing the index at once. No git process holds it, nothing is lost.

**In VS Code GUI:** Source Control reports the same error and cannot clear it. Use the integrated terminal, `Ctrl+'`.

**Stop if** `tasklist` shows a running `git.exe`.

---

## Task 2. Commit, staging by name

**Never `git add .`** `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` is an untracked draft and is Paul's call. It must still show `??` when you finish.

    git add CLAUDE.md 2026-07-31_HANDOVER_consultant_chat_4.md PROMPT_desktop_session_start_2026-07-31.md 2026-07-31_PLAN_reset_and_restructure.md PROMPT_claude_code_2026-08-01_date_corrections.md

**Five paths, not four.** The fifth is this prompt, which is on disk and untracked. Confirm with `git status --short` that exactly those five are staged and the draft is still `??`. Then commit with this message:

    docs: correct six dates against evidence, and two rules learned by breaking them

    Six date claims in the consultant handover and the Desktop session prompt
    were wrong against evidence and are corrected, with the old wording struck
    through. The proof is ac2d1be's author date, 2026-07-31 15:38:54: the
    handover's section 3 quotes that commit as the tip while claiming to have
    been read on the 30th, which is not possible. Two further claims span both
    days and now say so. Two could not be dated either way and are untouched.

    A correction banner at the top of the handover carries the proof, so a
    fresh session meets it before section 3. The recommended-commit block in
    section 3 is marked as executed by a19e999, aa1b956, 73bb064 and ddd9ffb.
    Its quoted draft message is deliberately unchanged, including the old
    filename it names: editing a quoted draft would falsify the record.

    CLAUDE.md gains an evidence rule: never reason from output you truncated
    yourself. A filter is not a reader and a mask is not an allowlist. Three
    errors in one day came from a cut, a tail, and a sed written to mask
    NAME=value lines that let a bare API key through and printed it in full.

    CLAUDE.md's third trap is corrected within the hour of being written, by
    the session that wrote it breaking it. git status and git diff are not
    reads: they refresh the index stat cache and take the lock, so git status
    alone recreates the stale lock. Use git --no-optional-locks status from
    the sandbox. git log, git show and git ls-files never touch the index.

    Also carries the prompt this work was done from.

**Then push.** Branch `feat/console-phase0`. `git push --dry-run` first, confirm fast-forward, and **never `--force`**.

---

## Verify, and quote the output

    git --no-optional-locks status --short
    git log --format="%h %ad %s" --date=iso -3

Confirm:

- One commit added on top of `ddd9ffb`.
- Working tree clean apart from `?? RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md`.
- `.git\index.lock` does not exist.
- Push was a fast-forward.

---

## Stop and ask about

1. Anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`. Nothing here goes there.
2. Any write to `data/receipts.db`. Nothing here touches it.
3. Any `.py` file or test.
4. A file in `git status` you did not expect. Report it, do not stage or revert it.
5. A push that is not a fast-forward.

**Flag, do not fix.** Anything else you notice goes in the report, not into this commit.

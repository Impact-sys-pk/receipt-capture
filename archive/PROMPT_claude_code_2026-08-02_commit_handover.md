> **SUPERSEDED. This task was run and is `5d50388`.** A second commit followed it, adding amendment 87 and three corrections the implementation session's final report produced. Kept as the record of what was asked.

# AUTOMATIC task: commit the handover documents, then the project changes hands

**Written 2026-08-02 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

**Documentation only. Nothing is edited and no code is touched.**

**This is the last task from this consultant session.** The project moves to `pdk7@hotmail.co.uk`. You hold no state between tasks, so nothing is being handed over to you: your next brief will come from a new consultant session working from the handover this commit carries.

---

## Why it must be committed before the handover is used

The new session's first action is to read `2026-08-02_HANDOVER_consultant_chat_5.md` and then check `git status --porcelain` returns nothing. **If these files are still uncommitted, that check fails on its own arrival** and the first thing the new session does is investigate a mess of our making.

---

## Task 1. Confirm the starting state

    git --no-optional-locks status --short

**Expect exactly three untracked files and nothing modified:**

    ?? 2026-08-02_HANDOVER_consultant_chat_5.md
    ?? PROMPT_claude_code_2026-08-02_commit_handover.md
    ?? PROMPT_intellibooks_desktop_handover_2026-08-02.md

**Stop and report** if anything is modified, in particular any `.py` file, or if a file you do not recognise is listed.

**If `.git\index.lock` exists**, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`.

---

## Task 2. One commit

    git add 2026-08-02_HANDOVER_consultant_chat_5.md PROMPT_intellibooks_desktop_handover_2026-08-02.md PROMPT_claude_code_2026-08-02_commit_handover.md

**Three paths.** The third is this prompt.

    docs: consultant handover, and the instruction for the Desktop session's

    The project moves to pdk7@hotmail.co.uk. Two documents and this prompt.

    2026-08-02_HANDOVER_consultant_chat_5.md supersedes chat 4. It carries the
    six mounts the next session needs and the reason the practice root cannot
    be one of them, the state read from git and the database on 2 August, the
    completed reset and restructure, what happens next and why the chart of
    accounts comes first, what only that session knew, and what it got wrong.

    The working method changed on 2 August: the consultant session now runs
    the tests and moves the files. Four things it cannot do are written down
    so nobody promises past them.

    PROMPT_intellibooks_desktop_handover_2026-08-02.md instructs the outgoing
    Desktop session to write its own handover to nine named sections and then
    stop. Its predecessor is 2026-07-29_HANDOVER_intellibooks_desktop.md,
    which stays where it is and is the format.

**Then push.** Branch `feat/console-phase0`. `git push --dry-run` first, confirm fast-forward, **never `--force`**.

---

## Verify, and quote the output

    git --no-optional-locks status --porcelain
    git log --format="%h %ad %s" --date=iso -3

Confirm and state each:

- **`--porcelain` returns nothing at all.** Quote it even though it is empty and say so. This is the condition the new session checks on arrival.
- One commit on top of `386b6ed`.
- Push was a fast-forward.
- No `.py` file in the commit, from `git show --stat`.

---

## Task 3. One last check, and report the answer rather than acting on it

The handover tells the next session that `chart_of_accounts_DRAFT.csv` is the bottleneck for both roads. **Confirm the two facts that claim rests on**, both read from the repository:

1. `chart_of_accounts_DRAFT.csv` holds **23 data rows plus a header**: **20 `expenses`, 2 `assets` and 1 `liabilities`**, and **`vat_treatment` is empty on all 23**. Parse it with Python's `csv` module rather than splitting on commas: two of the `name` values contain a comma inside quotes and a naive split corrupts them, which is how the "23 expense accounts" figure went unchallenged for a week.
2. There is **no `console\` directory** and **no Flask dependency**. Quote `requirements.txt` whole; it is three lines.

If either is not as described, say so. The handover is committed either way; a correction goes to the new session as a note rather than as an edit.

---

## Stop and ask about

1. **Any edit to any file.** This task stages and commits.
2. Any modified `.py` file.
3. Anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` or `C:\Intellibills\`.
4. Any write to the database at `C:\Intellibills\db\receipts.db`.
5. Starting the pipeline.
6. A push that is not a fast-forward.

**Flag, do not fix.** This is the last chance for anything you have noticed and not reported to reach the new session, so if something has been sitting on your list, put it in this report.

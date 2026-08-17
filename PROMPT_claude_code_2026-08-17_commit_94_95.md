# AUTOMATIC task: commit amendments 94 and 95, which have been uncommitted for two weeks

**Written 2026-08-17 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

**Documentation only. No code, no tests, nothing edited by you.** One commit, a push, a verification.

---

## Why

`HEAD` is `2119968`, made on 2026-08-03. Its copy of `2026-07-25_CONSOLE_DESIGN.md` carries **93 amendments and 1,924 lines.** The working tree carries **95 and 1,960.**

**So amendments 94 and 95, and two rules added to `CLAUDE.md`, have existed only as unsaved edits in a working tree for fourteen days.** Amendment 95 is the four-level chart of accounts model, which is the foundation of a workstream that has since produced a 122-account master. Losing that tree would lose the reasoning behind all of it.

Nothing else has changed. Verified before writing this: `git status --porcelain` returns exactly two modified files, the rows present in the working tree and absent from `HEAD` are exactly `[94, 95]`, and no row present in `HEAD` is missing from the working tree.

---

## Task 1. Confirm the starting state

    git --no-optional-locks status --short

**Expect exactly two modified and one untracked:**

     M 2026-07-25_CONSOLE_DESIGN.md
     M CLAUDE.md
    ?? PROMPT_claude_code_2026-08-17_commit_94_95.md

The untracked file is this brief. **Stop and report** on anything else, in particular any `.py` file, because none should be modified.

**If `.git\index.lock` exists**, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`. It was absent when this was written.

---

## Task 2. Confirm nothing has been lost before you commit

Two checks, both programmatic, both quoted in your report. **Do these before staging, not after.**

**a. Amendment rows.** Compare the numbered rows of the amendment record in `HEAD` against the working tree.

    git --no-optional-locks show HEAD:2026-07-25_CONSOLE_DESIGN.md

**Expect: rows only in the working tree are `[94, 95]`, and rows only in `HEAD` is empty.** A non-empty second list means an amendment has been deleted and you stop.

**b. Contiguity.** The working tree's amendment numbering must run 1 to 95 with no gap, counted by matching the numbered rows programmatically rather than by eye. That check has caught two out-of-order insertions on this project.

---

## Task 3. One commit

    git add 2026-07-25_CONSOLE_DESIGN.md CLAUDE.md PROMPT_claude_code_2026-08-17_commit_94_95.md

    docs: amendments 94 and 95, uncommitted since 2026-08-03

    Fourteen days in a working tree and nowhere else. Amendment 95 is the
    foundation of the chart of accounts workstream that has run since.

    94: amendment 93's reason for the email paths being safe is wrong twice
    over. app.py:1093 writes an event inside the unknown-sender guard, so
    amendment 89's conversion there is load-bearing rather than dormant. And
    the no-attachment branch at app.py:828 has no guard at all, so
    repository.py:69 returns INTELLITAX into a customer-facing alert: the
    body is signed INTELLITAX and the From display name reads INTELLITAX,
    at worker/email/alerts.py:30 and :36. Not fired since the reset, because
    email_alerts is empty. Also records the implementation session's
    disclosure that it invented an incident to fill a slot the brief created,
    and the rule that follows: ask what a check returned, never imply what it
    should return.

    95: the chart of accounts has four levels, not three, and a client takes
    a copy of one parent at setup rather than falling back through them. App
    default, firm default, industry, client. The parent is the industry chart
    for the client's business_type if one exists, otherwise the firm default,
    and "no chart for this trade" and "no charts at all" are one case.
    coa_accounts gains a firm_id column, scope becomes app_default | firm |
    industry | client, and both UNIQUE and idx_coa_lookup widen by firm_id,
    because two firms can each hold a PHV_DRIVER chart. The word "group" is
    retired in favour of "industry". Section 13.1 is new and supersedes
    section 13's three-tier fallback.

    Also: section 16 step 12 now names no file and is marked blocked until an
    agreed app default chart exists, on Paul's instruction, because the two
    CSVs it previously named were built without being asked for and are
    deleted. Amendment 92's line reference corrected from 951 to 952, and the
    rule that produced the error: an amendment citing a line number lower in
    the same file invalidates that number by existing. config.CLIENTS is
    loaded at config.py:149, not 100 and not 141.

    CLAUDE.md gains two rules, both from amendment 94: enumerate a set before
    claiming its size, and ask what a check returned rather than implying
    what it should return.

**Then push.** Branch `feat/console-phase0`. `git push --dry-run` first, fast-forward only, **never `--force`**.

---

## Verify, and quote the output

1. `git --no-optional-locks status --porcelain` returns nothing. Quote it.
2. One commit on top of `2119968`, pushed fast-forward.
3. **Amendment numbering contiguous from 1 to 95**, checked programmatically.
4. **No `.py` file in the commit.** `git show --stat` on your own commit.
5. **Read the commit message back against `git show --stat` and `git diff HEAD~1` and confirm every claim in it appears in the diff.** Amendment 92's rule. Its first use caught nothing and its second caught nothing; this is the third. **Report what it returned, not what it should have returned.** If the message claims something the diff does not contain, say so.

**One thing the message asserts that you should check rather than assume**, because it is the only claim in it that is not visible in the diff: that the two `CLAUDE.md` insertions are exactly the two rules named. `git diff HEAD~1 -- CLAUDE.md` should show two added lines and nothing else.

---

## Stop and ask about

1. Anything on the Destructive Git Operations list.
2. **Any edit to any file.** This task stages and commits what is already there.
3. Any modified `.py` file.
4. Anything outside `C:\LastingImpact\receipt_capture`, in particular under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` or `C:\Intellibills\`.
5. Any write to `receipts.db`.
6. Starting the pipeline.
7. A push that is not a fast-forward.

---

## Not in this brief, so do not do it

The chart of accounts workstream has moved outside the repository, to `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts\`, and sections 5.5, 13 and 18.10 of the design document do not yet know that. **Those amendments are the consultant session's next task and are not yours.** `chart_of_accounts_DRAFT.csv`, `chart_of_accounts_DRAFT2_2026-08-03.csv` and `2026-08-03_NOTE_chart_of_accounts_for_paul.md` are tracked, superseded and staying put for now. **Do not tidy them.**

---

## Report to a file

**Write your report to `C:\LastingImpact\receipt_capture\2026-08-17_REPORT_claude_code_commit_94_95.md` and commit it with the commit above.**

Include both outputs from task 2, the porcelain result, the contiguity count, and the outcome of verification step 5 stated as what it found.

# AUTOMATIC task: commit amendments 96 to 100

**Written 2026-08-17 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

**Documentation only. No code, no tests, nothing edited by you.** One commit, a push, a verification.

---

## Why

This morning you committed amendments 94 and 95, which had sat uncommitted for fourteen days. **Five more have accumulated since, in the same working tree, and I would rather not leave them overnight.**

`HEAD` is `0c27dd0`. Its copy of `2026-07-25_CONSOLE_DESIGN.md` carries 95 amendments. The working tree carries 100.

Verified before writing this: rows present in the working tree and absent from `HEAD` are exactly `[96, 97, 98, 99, 100]`, no row present in `HEAD` is missing, and no `.py` file is modified.

---

## Task 1. Confirm the starting state

    git --no-optional-locks status --short

**Expect exactly two modified and one untracked:**

     M 2026-07-25_CONSOLE_DESIGN.md
     M CLAUDE.md
    ?? PROMPT_claude_code_2026-08-17_commit_96_to_100.md

The untracked file is this brief. **Stop and report** on anything else, in particular any `.py` file.

**If `.git\index.lock` exists**, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`. It was absent when this was written.

---

## Task 2. Prove nothing has been lost, before staging

Two checks, both programmatic, both quoted in your report.

**a. Amendment rows.** Compare the numbered rows of the amendment record in `HEAD` against the working tree. **Expect: only in the working tree `[96, 97, 98, 99, 100]`, only in `HEAD` empty.** A non-empty second list means an amendment has been deleted and you stop.

**b. Contiguity, using the corrected method.** This is the check you and I both had wrong until this morning, so use the version now written into `CLAUDE.md`: **bound the scope to the amendment record's own line boundaries, print those boundaries alongside the result, assert the list equals `range(first, last+1)`, and test for duplicates explicitly.** Do not use a set difference. Expect 1 to 100, and print the line numbers you bounded it with.

---

## Task 3. One commit

    git add 2026-07-25_CONSOLE_DESIGN.md CLAUDE.md PROMPT_claude_code_2026-08-17_commit_96_to_100.md

    docs: amendments 96 to 100, the chart of accounts leaves both systems

    96: the chart of accounts is not a table in receipts.db and not part of
    the console. It lives at OneDrive\IntelliCharts\ as COA_MASTER_v1.csv,
    122 accounts in 20 columns, with build_coa.py generating the other files
    and running every check. Records ten decisions taken between 5 and 17
    August that no repository file held: four-digit codes on Sage 50's
    ranges, a separate vat_recoverability column, KashFlow dropped, Sage
    Accounting deferred with no file generated, Sage Final Accounts as a
    mapping table because its own two charts disagree on 85 shared codes,
    an exceptions file, a drift check that stops the build, two ideas
    dropped as over-engineering, and the status filter going into
    catOptions() in the same Desktop change. Also records that SA103F and
    MTD ITSA are different schemes and neither is a subset of the other,
    which is why the master carries two tax columns rather than one.

    97: three findings from taking the workstream over. Account 4200 has an
    income type on an expense box and exportHMRC() gets the sign wrong. The
    contiguity check this document relied on was giving right answers for
    the wrong reason: it matched 103 numbered rows across the whole file and
    reported no leftovers because it compared with a set difference and
    section 13A's findings table is numbered 1 to 8. And SA103F 2026 has 16
    mappable boxes of which 14 are expense boxes, not "16 expense boxes".

    98: the hmrc field on a books category is renamed sa103fBox and holds
    the SA103F box number rather than a word, so the seed stops translating
    and the exported CSV carries the real box numbers.

    99: client_type is added to the client record with three values,
    sole_trader, partnership and company, LLP excluded. It is what makes the
    master's applies_to column usable. A partnership needs one capital and
    one drawings account per partner, so 3200-3209 and 3210-3219 are
    reserved blocks generated from a partners list.

    100: the period selector offers MTD quarters and the only report that
    consumes them is in SA103F boxes, which is the wrong shape for a
    quarter. Not fixed: the fix is a second report, not a correction. And
    the list of boxes is renamed HMRC_BOXES to SA103F_BOXES.

    Sections amended to match: 5.5 records that coa_accounts is not created,
    13 that the module is not console work, 13.1 that the app default chart
    now exists, 16 step 12 cancelled because there is nothing to load and
    nowhere to load it, and 18.10's chart of accounts item closed. Two more
    found by enumerating every live mention of coa_accounts: section 5's
    sequencing note listed it among the tables created at step 11, and 12.3
    step 6 looks a category name up in it, which is the one clause the move
    actually breaks. Version header moves to 1.9.

    CLAUDE.md gains one rule, from amendment 97: a check that cannot fail is
    not a check, and the tell is that it has never returned anything but a
    pass.

**Then push.** Branch `feat/console-phase0`. `git push --dry-run` first, fast-forward only, **never `--force`**.

---

## Verify, and quote the output

1. `git --no-optional-locks status --porcelain` returns nothing. Quote it.
2. One commit on top of `0c27dd0`, pushed fast-forward.
3. Amendment numbering contiguous 1 to 100, by task 2b's method.
4. No `.py` file in the commit. `git show --stat` on your own commit.
5. **`git diff HEAD~1 -- CLAUDE.md` shows one added line and one removed**, the removal being the line the new rule was inserted above. Confirm the added line is the one the message names.
6. **Read the commit message back against `git show --stat` and `git diff HEAD~1`, and report what that found.**

**On step 6, a note about how I have phrased this before and got it wrong.** Twice I wrote something like "its first use caught nothing, this is the second", which reads as an instruction to produce a finding, and once you filled the slot with an incident that had not happened and then disclosed it. **So: this check has found something on one of its three previous uses. Report what it returns. If it returns nothing, say it returned nothing.**

---

## Stop and ask about

1. Anything on the Destructive Git Operations list.
2. **Any edit to any file.** This task stages and commits what is already there.
3. Any modified `.py` file.
4. Anything outside `C:\LastingImpact\receipt_capture`.
5. Any write to `receipts.db`.
6. Starting the pipeline.
7. A push that is not a fast-forward.

---

## Not in this commit, and do not go looking for them

The chart of accounts workstream now lives at `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts\`, **outside this repository**, and two files were written there today: a Desktop brief and a generated seed. They are outside your permitted scope and are not part of this commit. **Do not add them, do not reference them by path in anything you write, and do not go and read them.**

---

## Report to a file

**Write your report to `C:\LastingImpact\receipt_capture\2026-08-17_REPORT_claude_code_commit_96_to_100.md` and commit it with the commit above.**

Include both outputs from task 2 with the line boundaries printed, the porcelain result, and what verification step 6 returned.

# AUTOMATIC task: commit stage 6, and the change to how this project is worked

**Written 2026-08-02 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

**Documentation only. Nothing is edited and no code is touched.** Staging, two commits, a push, a verification.

**Do not start the pipeline.** It has already run its clean cycle and nothing needs it again.

---

## Why

**The six-stage operation of 17.5a is finished.** Stage 6 ran on 2026-08-02: one receipt travelled from `capture@lastingimpact.co.uk` to a books entry in a single six-second pass, against an empty database, a client with no history and a books file that did not exist. Amendment 86 records it.

And `CLAUDE.md` gains a change to the working method that Paul asked for after watching the round trips cost more than the work.

---

## Task 1. Confirm the starting state

    git --no-optional-locks status --short

**Expect exactly two entries, both modified, both documentation:**

     M 2026-07-25_CONSOLE_DESIGN.md
     M CLAUDE.md

Plus this prompt as untracked.

**`RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` should no longer appear at all.** It was deleted on 2026-08-02 after being confirmed a strict subset of `RECEIPT_CAPTURE_GUIDE.md`, 13 differing lines with the live guide newer in every one. **If it is still listed, stop and report**, because `git status --porcelain` returning anything makes `config.check_git_status_on_startup()` warn on every pipeline start.

**Stop and report** if any `.py` file is modified, or if `logs\` or `data\files\` reappear in the listing.

**If `.git\index.lock` exists**, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`.

---

## Task 2. Two commits, staged by name

**Never `git add .`**

### Commit 1, stage 6

    git add 2026-07-25_CONSOLE_DESIGN.md

    docs: amendment 86, stage 6 passed and the reset operation is complete

    One receipt, Gatwick Airport - receipt.pdf, travelled from the mailbox to
    a books entry in a single six-second pass. Verified from the database,
    the filesystem and PKPH-books.json rather than from what appeared on
    screen.

    client_id reads Client_006 rather than UNKNOWN, which is the result that
    matters: clients.csv is being read from Intellibills\ and a sender
    resolves against a registry with no history behind it. Vendor mappings
    still 100 and untouched.

    Both stores are correct and each demonstrates a decision. The archive is
    at Intellibills\Documents\PKPH\2026\08\, client code first and filed
    under the month it arrived while the document is dated 7 February, which
    is amendment 77's arrival-date rule visible on disk. The client copy is
    at Clients\PKPH\Receipts\2025-26\ with its sidecar, which is the interim
    contract of amendment 75 doing the job it was kept for.

    PKPH-books.json was created from nothing. Its single entry carries the
    supplier, the date and the figures, its id is the pipeline's receipt_id
    rather than an img_ value, and there is one entry rather than two, so
    change E's pairing fix works on the first real receipt through the new
    tree.

    Two absences are correct and were checked rather than assumed. No
    category, because match_source reads unmatched and none of the 100
    mappings from a PHV driver's history matches an airport car park. No
    thumbnail, because the document is a PDF, which amendment 59 records as
    permanent and right.

### Commit 2, the working method

    git add CLAUDE.md PROMPT_claude_code_2026-08-02_stage6_passed.md

**Two paths.** The second is this prompt.

    docs: the consultant session runs the tests and moves the files

    Paul's decision, 2026-08-02, after the reset and restructure. He ran
    every check and moved every file himself, and the round trips cost more
    than the work.

    The consultant session now runs any test it is capable of running and
    reports the evidence rather than the steps, and makes file changes, moves
    and deletions itself after asking and getting a yes. That covers the
    practice root, which the AUTOMATIC list still forbids to Claude Code.

    Paul still runs what only he can: starting the pipeline, anything in
    IntelliBooks Desktop, sending a receipt, and the mailbox.

    Four limits are written down so nobody promises past them. No pytest and
    a Windows .venv, so the consultant session cannot run the suite. It
    cannot start the pipeline. It cannot drive Desktop. And its sandbox can
    create a file in a mounted folder but cannot unlink one, so a deletion
    needs Paul's approval each time while a move or rename works.

**Then push.** Branch `feat/console-phase0`. `git push --dry-run` first, confirm fast-forward, **never `--force`**.

---

## Verify, and quote the output

    git --no-optional-locks status --porcelain
    git log --format="%h %ad %s" --date=iso -3

Confirm and state each:

- **`--porcelain` returns nothing at all.** This is the command `app.py:1207` runs at startup, and an empty result is the point of having deleted the draft. Quote it even though it is empty, and say so.
- Two commits on top of `7ed4a4e`.
- Push was a fast-forward.
- No `.py` file in either commit, from `git show --stat` on both.

---

## One thing to report, not to act on

The Receipts tab in `IntelliBooks-Desktop-v3.html` has **no Category column.** Its header at approximately lines 163 to 166 is: checkbox, Image, Date, Supplier, Net, VAT, Gross, Source, Status, Options. The Category column at approximately line 136 belongs to the Bank Transactions table.

**Confirm those two line numbers and quote both header rows.** A receipt's category is editable in the Edit window but invisible in the list, and under 18.5a a blank category is the one thing that makes posting to the cashbook impossible, so the field that blocks the operation cannot be seen from the screen where the operation starts. That belongs with 18.10's postponed decision on categories and is **not** to be fixed here.

---

## Stop and ask about

1. **Any edit to any file.** This task stages and commits.
2. Any modified `.py` file.
3. Anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` or `C:\Intellibills\`.
4. Any write to the database at `C:\Intellibills\db\receipts.db`.
5. Starting the pipeline.
6. A push that is not a fast-forward.

**Flag, do not fix.**

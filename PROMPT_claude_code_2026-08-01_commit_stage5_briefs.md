# AUTOMATIC task: commit the reset record, the last five decisions, and the two stage 5 briefs

**Written 2026-08-01 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

**This is a documentation commit. Nothing is edited.** No Python, no tests, no behaviour, and no content change to any of the files staged. **If you find yourself editing a file, you have misread this.** Your job is staging, three commits, a push and a verification.

**Why it matters that this lands before anything else:** the two files being committed here are the briefs the next two sessions work from. A brief that is not committed can change underneath the session building from it, and nobody can then tell which version was built.

---

## Task 1. Check the lock before anything

The consultant session works from a Linux sandbox that can create a file in the mounted folder but cannot unlink one, so a bare `git status` there leaves `.git\index.lock` behind. It has happened twice in this project. See the third trap in `CLAUDE.md`.

    tasklist /FI "IMAGENAME eq git.exe"

Expect no tasks. Then, **only if the file exists**:

    del .git\index.lock

**Plain English:** removes an empty marker git uses to stop two processes writing the index at once. Nothing is lost.

**In VS Code GUI:** Source Control reports the same error and cannot clear it. Use the integrated terminal, `Ctrl+'`.

**If it does not exist, do nothing and say so in your report.**

---

## Task 2. Confirm the starting state

    git --no-optional-locks status --short

**Expect exactly eight entries: four modified and four untracked.**

    M 2026-07-25_CONSOLE_DESIGN.md
    M 2026-07-31_HANDOVER_consultant_chat_4.md
    M 2026-07-31_PLAN_reset_and_restructure.md
    M CLAUDE.md
   ?? PROMPT_claude_code_2026-08-01_commit_stage5_briefs.md
   ?? PROMPT_claude_code_stage5_pipeline_paths.md
   ?? PROMPT_intellibooks_desktop_stage5_paths.md
   ?? RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md

**The first of the four untracked is this prompt.** It is committed at commit 2.

**`RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` is not part of this and must still show `??` when you finish.** It is an old untracked draft and is Paul's call.

**Stop and report if you see anything else.** In particular a modified `.py` file, which would mean somebody has started stage 5 early.

---

## Task 3. Three commits, staged by name

**Never `git add .`** Run `git --no-optional-locks status --short` between commits and confirm each took what was intended and nothing else.

### Commit 1, the reset record and the last five decisions

    git add 2026-07-25_CONSOLE_DESIGN.md 2026-07-31_PLAN_reset_and_restructure.md

    docs: the reset as executed, and the last five decisions

    Amendment 79 closes the five decisions the reset plan was holding.
    Handover Pack, not Handover. The database backups get their own folder at
    Intellibills\Backups\ and stop borrowing IntelliBooks'. The logs go local
    to C:\Intellibills\logs\, because they are appended on every poll and a
    OneDrive conflict copy of a log is worse than useless. Exports go to
    Intellibills\Exports\, with one point left open: whether an export
    belongs in the client's folder instead. That answer makes amendment 76's
    constant table five rather than four.

    Amendment 80 records the reset as executed on 1 August, verified against
    the database, git log and the filesystem rather than from a report.
    Stages 1 to 3 done, stage 4 part done, stages 5 and 6 not started.

    Three things happened that no plan specified. The 100 surviving vendor
    mappings were re-keyed from Client_001 to Client_006, because clients.csv
    was rewritten in the same operation and the key they hang off ceased to
    exist: protecting rows through a reset is not enough if the key is
    retired in the same breath.

    Clients\Paul Keating\ is not disposable and the plan said it was. It
    holds eight engagement letters and proposals. 17.5 scoped it correctly,
    17.5a widened it when summarising, and the plan repeated 17.5a. The plan
    had already noticed and did not act: it listed the PDFs and told the
    operator to confirm they were included, beside an instruction to delete
    the folder in full.

    And the event logs were never in scope. 1,151 lines across three files
    still describe the 29 receipts the reset deleted, and the console's
    intake panel at 8.6 will read all of it.

    Adds section 0.7, the verified record of the reset, and 0.8, the five
    decisions. Corrects the plan's stage 3c, whose superseded wording would
    have destroyed real client records.

### Commit 2, the two stage 5 briefs

    git add PROMPT_claude_code_stage5_pipeline_paths.md PROMPT_intellibooks_desktop_stage5_paths.md PROMPT_claude_code_2026-08-01_commit_stage5_briefs.md

**Three paths, not two.** The third is this prompt.

    docs: the two stage 5 briefs, one per module

    Stage 5 is a path change and nothing else. Five independent constants
    replacing DATA_DIR, four coordinated flips, the logs to the local root,
    and Handover Pack on the Desktop side.

    Both briefs open with the frozen list from amendment 75, because the risk
    in this stage is not the change but somebody tidying worker/filing.py or
    scanFiledReceipts() while they are in there. Those are the interim
    contract and the only route a receipt has into the books.

    The Review folder moves from being keyed on the client's name to the
    client's code, which closes amendment 44's fault permanently: a code is
    an identifier, a name is a label someone edits.

    Neither half works alone, so they are sent in the same window. The
    pipeline half goes first because it is larger and carries the tests; the
    Desktop half second because its manual check cannot run until the
    pipeline side exists.

    Also carries the prompt this commit was made from.

### Commit 3, the handover and CLAUDE.md

    git add 2026-07-31_HANDOVER_consultant_chat_4.md CLAUDE.md

    docs: harden the git sandbox rule, and the handover's remaining dates

    The third trap said reads are safe from the Linux sandbox. They are not,
    and the session that wrote it disproved it within the hour by running
    git status and recreating the lock. The bullet no longer lists which
    commands are safe with --no-optional-locks, because the git manual
    defines the flag only as "do not perform optional operations that
    require locks" and names no command. It now names the three that are safe
    by construction, git log, git show and git ls-files, and says treat
    everything else as able to take the lock.

    That holds whether or not the implementation session is right that
    git --no-optional-locks diff can still write the index. That claim is
    recorded as neither confirmed nor refuted: the only test is to run it and
    watch for a lock, and this session had already left one behind twice.

**Then push.** Branch `feat/console-phase0`. `git push --dry-run` first, confirm fast-forward, **never `--force`**.

---

## Verify, and quote the output

    git --no-optional-locks status --short
    git log --format="%h %ad %s" --date=iso -5

Confirm and state each:

- Three commits on top of `8b1db5d`.
- Working tree clean apart from `?? RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md`.
- `.git\index.lock` does not exist.
- Push was a fast-forward.
- **No `.py` file appears in any of the three commits.** Check with `git show --stat` on each. This is a documentation commit and a Python file in it means something was staged that should not have been.

---

## One thing to report, not to act on

Paul has an open question that this commit does not settle and that the next task will meet.

**`import_vendor_csv.py:76` and `seed_client_vendors.py:177` both default `client_id` to `"Client_001"`.** That key no longer exists: the reset re-keyed the vendor mappings to `Client_006` and rewrote `clients.csv`. **Run either script without its second argument and it silently seeds rows under a dead client**, which is precisely the condition the re-key removed. Their usage strings at `:72` and `:173` name the same dead key, and the first names a CSV that has since moved to `Intellibills\`.

**Do not fix it here.** It is a behaviour change and it is Paul's call. **Confirm the four line numbers against the files and quote what each line actually says**, so the decision is taken against the code rather than against this description.

---

## Stop and ask about

1. **Any edit to any file.** This task stages and commits; it does not change content.
2. A `.py` file appearing as modified. That would mean stage 5 has been started early.
3. Anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`. Nothing here goes there.
4. Any write to `receipts.db`.
5. `git status` showing anything other than the seven entries in task 2.
6. A push that is not a fast-forward.

**Flag, do not fix.**

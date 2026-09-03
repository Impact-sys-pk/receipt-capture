# AUTOMATIC task: amendment 87, and the last corrections to the handover

**Written 2026-08-02 by the consultant session, for Claude Code. Paste this whole file in. This is the last one.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

**Documentation only. No code, no tests, nothing edited by you.** One commit, a push, a verification.

---

## Why there is a second commit

Your last report found something no document held, and it went straight into the design document rather than into a chat that is about to end.

**The fallback `firm_id` is stated three times and the three disagree.** `config.py:112` says `FIRM001`, `CLAUDE.md`'s Core Rules 3 says `INTELLITAX` twice, `clients.csv` carries `FIRM001` on every row, and four call sites in `app.py` hardcode `"INTELLITAX"`. Two writers build `receipt_events_{firm_id}.ndjson` from it. **That is amendment 87 and it is unfixed**, because it changes behaviour on four paths and is Paul's to approve.

Three smaller corrections went into the handover with it: `git grep` rather than `grep -rn` because `.history\` holds 79 stale copies, the existence of `requirements-dev.txt`, and `data\run.log` being stranded by section 0.8.5.

---

## Task 1. Confirm the starting state

    git --no-optional-locks status --short

**Expect exactly three modified files and one untracked:**

     M 2026-07-25_CONSOLE_DESIGN.md
     M 2026-08-02_HANDOVER_consultant_chat_5.md
     M PROMPT_claude_code_2026-08-02_commit_handover.md
    ?? PROMPT_claude_code_2026-08-02_final.md

**Stop and report** on anything else, in particular any `.py` file.

**If `.git\index.lock` exists**, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`.

---

## Task 2. One commit

    git add 2026-07-25_CONSOLE_DESIGN.md 2026-08-02_HANDOVER_consultant_chat_5.md PROMPT_claude_code_2026-08-02_commit_handover.md PROMPT_claude_code_2026-08-02_final.md

**Four paths.** The last is this prompt.

    docs: amendment 87, the fallback firm_id disagrees with itself

    Found by the implementation session in its last report and held by no
    document until now. config.py:112 defaults to FIRM001, CLAUDE.md's Core
    Rules 3 says INTELLITAX twice, clients.csv carries FIRM001 on every row,
    and four call sites in app.py hardcode "INTELLITAX" on paths where no
    client has resolved. Two writers build receipt_events_{firm_id}.ndjson
    from it, so one firm's intake history lands in two files depending on
    which code path logged it.

    Section 0.8.5 of the reset plan counted the two files and treated the
    split as a fact of life. It is not. The fresh logs prove the mechanism:
    after stage 6 only receipt_events_FIRM001.ndjson exists, because the one
    receipt resolved.

    The defect is the disagreement, not the split, and three of the four
    hardcoded actions are exactly what design 8.6's intake panel exists to
    show. Not fixed: it changes behaviour on four paths.

    Also corrects 8.6's stale path, which still reads logs/receipt_events_
    *.ndjson and is C:\Intellibills\logs\ since stage 5, and adds three notes
    to the handover: use git grep rather than grep -rn because .history\
    holds 79 dated copies, requirements-dev.txt exists alongside
    requirements.txt, and data\run.log was stranded by 0.8.5.

**Then push.** Branch `feat/console-phase0`. `git push --dry-run` first, fast-forward only, **never `--force`**.

---

## Verify, and quote the output

    git --no-optional-locks status --porcelain
    git log --format="%h %ad %s" --date=iso -2

- **`--porcelain` returns nothing at all.** Quote it and say so. **This is the last thing you do for this consultant session and it is the condition the new one checks on arrival.**
- One commit on top of `5d50388`, pushed fast-forward.
- No `.py` file in the commit.
- **Amendment numbering is contiguous from 1 to 87.** Check it programmatically against the rows in the amendment record, not by eye.

---

## One thing for Paul, not for you

`C:\LastingImpact\receipt_capture\data\run.log`, 43,365 bytes, should be moved to `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\Backups\` beside the three `.ndjson` files archived under 0.8.5. **That is outside the repository, so it is not yours.** Say in your report that it is outstanding so it does not get lost between sessions.

---

## Stop and ask about

1. **Any edit to any file.** This task stages and commits.
2. Any modified `.py` file.
3. Anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` or `C:\Intellibills\`.
4. Any write to the database.
5. Starting the pipeline.
6. A push that is not a fast-forward.

**Flag, do not fix**, and this really is the last chance for it to reach anyone.

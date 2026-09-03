# Brief: commit amendments 170 to 172, step 10a built, and the five untracked root files

**Written 2026-09-02 by the consultant session, 15:55 BST.** Times in this brief are BST. Your clock is BST and the consultant session's shell reports UTC, one hour behind, so a timestamp an hour off is not a discrepancy.

**Documentation and one operational script. No production code, no tests, nothing in `worker\` or `app.py`.** Sub-steps 10a.1 and 10a.2 were already committed by you as `7ea2dc4` and `2ac70ab`.

**Report to `C:\LastingImpact\receipt_capture\2026-09-02_REPORT_claude_code_commit_170_to_172.md`.** Every deliverable in this brief has a file. Nothing is reported in chat only.

---

## Task 1. Starting state, and stop if it does not match

Run and print whole:

```
git --no-optional-locks status --porcelain
git --no-optional-locks log --oneline -3
```

**Expected HEAD: `2ac70ab`**, "feat(filing): the IntelliBooks parent folder inside every client folder", parent `7ea2dc4`.

**Expected two modified tracked files**, both written by the consultant session between 15:26 and 15:52 BST today:

| File | Bytes | md5 |
|---|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | 628,141 | `931ae3c7baa8cec5537cf59bab087670` |
| `2026-08-20_LIST_outstanding_items_and_decisions.md` | 95,583 | `ba4708176363c305b2a622522e12fb7f` |

**Both figures were read back off disk after writing, not asserted from what was sent.** If either differs, stop and say so: something has written to them since.

**Expected five untracked files in the root:**

- `_step10a_move.py`
- `2026-09-02_HANDOVER_consultant_chat_12.md`
- `2026-09-02_REPORT_claude_code_step10a.md`
- `PROMPT_claude_code_2026-09-02_step10a_pipeline.md`
- `PROMPT_intellibooks_2026-09-02_step10a_desktop.md`

This brief makes six. **`__pycache__\` and `Backups\` are gitignored and are not in this list.**

**Stop and ask if the porcelain shows anything else at all**, and in particular any `.py` file other than `_step10a_move.py`. Do not stage past a surprise.

---

## Task 2. What is in the two modified documents, so you can check the diff rather than trust this brief

**`2026-07-25_CONSOLE_DESIGN.md`: amendment 172 only.** The version header goes 1.31 to 1.32 with 1.31 struck through beneath it. A new `### v1.32, 2026-09-02` section with one row. Section 16's head line, its head-table row for 10a, and sub-steps 10a.1 and 10a.2 change status.

**Amendments 170 and 171 were already in the working tree before today's session started** and are committed by this brief for the first time. They are not new here.

**`2026-08-20_LIST_outstanding_items_and_decisions.md`: items 65 and 132 close, items 66 and 84 are narrowed.** The count line goes from 87 open and 64 closed to 85 and 66.

---

## Task 3. Commit

**One commit.** Message:

```
docs: amendments 170 to 172, step 10a built, and the step 10a working files

Amendments 170 and 171 were written on 2026-09-02 and not committed at the
time. 172 records step 10a as BUILT.

170: the client folder gains one parent folder, IntelliBooks, and no folder
carries an underscore. Step 10a decomposed into three sub-steps.
171: sub-step 10a.3, the document sweep. Six path statements changed and
thirteen deliberately left, with the reason for each in the row.
172: step 10a is BUILT. 10a.1 is 7ea2dc4, 10a.2 is 2ac70ab on the pipeline
side plus change log items 50 and 51 on the Desktop side plus the five
folders moved by _step10a_move.py, run by Paul at about 15:33 BST.
Section 16's head table goes from 18 built and 18 outstanding to 19 and 17.

Four checks passed and two could not be run. Not run: filing a receipt from
Review, because Intellibills\Review\ holds only an empty TEST3\; and the
legacy books migration, because no client has a books file at the old
location. The Review one is the only thing that writes filed_path into a
resolution note.

2026-08-20_LIST_outstanding_items_and_decisions.md: items 65 and 132 close,
66 and 84 narrowed to their unfixed halves. 87 open and 64 closed becomes
85 and 66.

Untracked files added: the two step 10a work plans, Claude Code's step 10a
report, the consultant handover for chat 12, and _step10a_move.py, which is
kept as the record of what moved the client folders rather than deleted.

Files: 2026-07-25_CONSOLE_DESIGN.md,
2026-08-20_LIST_outstanding_items_and_decisions.md, _step10a_move.py,
2026-09-02_HANDOVER_consultant_chat_12.md,
2026-09-02_REPORT_claude_code_step10a.md,
PROMPT_claude_code_2026-09-02_step10a_pipeline.md,
PROMPT_intellibooks_2026-09-02_step10a_desktop.md,
PROMPT_claude_code_2026-09-02_commit_170_to_172.md
```

**Check the message against `git diff --cached --stat` before committing, not against this brief.** Amendment 92 exists because a commit message once claimed work the same brief forbade, and that claim is now permanent in pushed history.

**Then push.**

---

## Task 4. Verify, and quote every output

1. **`git --no-optional-locks status --porcelain` after the commit**, printed whole. Expected empty.
2. **`git --no-optional-locks show --stat HEAD`**, printed whole. Eight files.
3. **The amendment record's contiguity, by the corrected method in `CLAUDE.md`.** Bound the scope to the record's own line boundaries, print those boundaries with the result, assert the list equals `range(first, last+1)` and test duplicates explicitly. **Expected 172 rows, 1 to 172, no duplicates.** The consultant session ran this and got that answer; run it yourself rather than repeating it.
4. **Section 16's head table against the body statuses**, the diff every commit brief runs. **Expected 19 BUILT, 17 OUTSTANDING, 1 CANCELLED, 1 MOVED, 38 rows**, and the head line now states those four figures. **Report any row where the table and the body disagree.**
5. **The sub-steps per decomposed step, each set asserted contiguous from 1 against its head-table row.** 10a 3, 10d 58, 10e 15, 10f 30, 10g 10.
6. **`grep -c` for `COA_MASTER_v1` and for `build_coa` in `2026-07-25_CONSOLE_DESIGN.md`, `2026-08-20_LIST_outstanding_items_and_decisions.md` and `CLAUDE.md`.** Do not change anything. The consultant session is about to do that sweep and wants your counts as an independent reading of the same set.

---

## Task 5. Flag, do not fix

Three things are known and are not this task. Say if you find others.

- **Section 16's head line still says the six BUILT sub-steps of 10e were built 2026-09-01**, while all six sub-steps and the commit message of `81aec08` say 2026-08-31. Nothing on disk settles it and Paul has not ruled. You found this as your finding 4 on 2026-09-02.
- **`CLIENT_STATEMENTS_FOLDER_NAME` is pinned by no test**, and the casing of `CLIENT_INTELLIBOOKS_FOLDER_NAME` is not asserted because Windows globbing is case-insensitive. Your section 9.2. Not fixed, and it is a real gap for the cloud build where `filed_path` is a string two products compare.
- **`PROMPT_claude_code_step10a_and_10b.md` is still in the root and must never be sent.** Your section 9.4. It moves at step 10h with every other spent file, not here.

---

## Task 6. Stop and ask about

- Any edit to any file other than the two modified documents named in task 1.
- Any change to `worker\`, `app.py`, `config.py` or anything in `tests\`.
- Anything under the practice root, `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`, or under `C:\Intellibills\`.
- Running `_step10a_move.py` again. It has been run. It is idempotent, but running it is not this task.
- A starting state that does not match task 1.

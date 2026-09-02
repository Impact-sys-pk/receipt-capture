# Report: commit of amendments 170 to 172, step 10a built, and the six root files

Written 2026-09-02 by Claude Code, 16:00 BST. Clock read at 15:55 and again at 16:00 BST before dating this file, per CLAUDE.md. The shell on this machine reports the zone as `GMTDT` and `date -u` was one hour behind at both readings, so the times here are BST.

Brief: `PROMPT_claude_code_2026-09-02_commit_170_to_172.md`.

**Outcome: done. One commit, `d6485c8`, eight files, pushed to `origin/feat/console-phase0`. Working tree clean. All six checks in task 4 ran and every expected figure matched. One new finding, disclosed in section 6, which is a markdown defect this commit's own content introduced.**

---

## 1. Starting state, task 1

`git --no-optional-locks status --porcelain`, printed whole:

```
 M 2026-07-25_CONSOLE_DESIGN.md
 M 2026-08-20_LIST_outstanding_items_and_decisions.md
?? 2026-09-02_HANDOVER_consultant_chat_12.md
?? 2026-09-02_REPORT_claude_code_step10a.md
?? PROMPT_claude_code_2026-09-02_commit_170_to_172.md
?? PROMPT_claude_code_2026-09-02_step10a_pipeline.md
?? PROMPT_intellibooks_2026-09-02_step10a_desktop.md
?? _step10a_move.py
```

`git --no-optional-locks log --oneline -3`, printed whole:

```
2ac70ab feat(filing): the IntelliBooks parent folder inside every client folder
7ea2dc4 refactor(filing): name the Receipts and Statements client subfolders in config
7cf92ea docs: amendments 166 to 169, the two draft CSVs deleted, Backups gitignored, and six new step 10d sub-steps
```

Two modified tracked files, six untracked, nothing else. No `.py` file other than `_step10a_move.py`. HEAD, parent and grandparent as the brief expected.

**Bytes and md5 both match the brief exactly**, read off disk with `wc -c` and `md5sum`:

| File | Bytes expected | Bytes read | md5 expected | md5 read | Match |
|---|---|---|---|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | 628,141 | 628,141 | `931ae3c7baa8cec5537cf59bab087670` | `931ae3c7baa8cec5537cf59bab087670` | yes |
| `2026-08-20_LIST_outstanding_items_and_decisions.md` | 95,583 | 95,583 | `ba4708176363c305b2a622522e12fb7f` | `ba4708176363c305b2a622522e12fb7f` | yes |

So nothing wrote to either file between the consultant session reading them back and this session opening them.

---

## 2. What was in the two documents, task 2

I read both diffs whole rather than trusting the brief. `2026-07-25_CONSOLE_DESIGN.md`'s diff is 66.1 KB across 163 lines, with 30 lines over 500 characters, so I read it in four bounded ranges covering lines 1 to 163 with no character truncation anywhere. `2026-08-20_LIST_outstanding_items_and_decisions.md`'s diff is 19,111 bytes across 58 lines and was printed whole in one go.

### 2.1 One thing the brief describes differently from the diff, and it is not a discrepancy

The brief says "The version header goes 1.31 to 1.32". **The diff against HEAD shows `1.29` becoming `1.32`, with `1.31`, `1.30` and `1.29` all added as new struck-through rows beneath it.** Those are the same fact seen from two places: the brief describes the edit the consultant session made in this session, and the diff describes the distance from the last commit, which was made before amendments 170 and 171 were written. The brief says so directly in task 2, so this is consistent and is recorded only because the two numbers differ on their face.

### 2.2 `2026-07-25_CONSOLE_DESIGN.md`

Everything the brief names is present, and nothing else is:

- Version header `1.29` to `1.32`, with three new struck rows for 1.29, 1.30 and 1.31.
- Three new amendment sections, `### v1.30`, `### v1.31` and `### v1.32`, one row each, being amendments 170, 171 and 172.
- Section 16's head line rewritten, `18 built, 18 outstanding` to `19 built, 17 outstanding`, with the old wording struck.
- Section 16's head-table row for 10a, `OUTSTANDING` to `BUILT`, and its text now naming three sub-steps.
- Section 16's body for 10a set to `BUILT 2026-09-02`, with the three sub-steps added and 10a.1 and 10a.2 marked BUILT.
- Amendments 55 and 65 gain the "superseded in part by amendment 170" sentence.
- Six live path statements changed, being amendment 171's sweep: 3.5, 3.6, 12.4 twice, 17.2's bullet and 18.2b's freeze blockquote. Each carries `Struck 2026-09-02 by amendment 171` and the old wording struck through rather than deleted.
- 13A.1's dropped-receipt bullet and 13A.3's finding 6, which amendment 170 changed.

No section other than the header, 3.5, 3.6, 12.4, 13A, 13A.3, 16, 17.2, 18.2b and the amendment record is touched.

### 2.3 `2026-08-20_LIST_outstanding_items_and_decisions.md`

Exactly as the brief says. The count line goes `87 open, 64 closed, 151 raised` to `85 open, 66 closed, 151 raised`, with `87 plus 64` struck and the reason given. Item 65's open row is deleted and a closed row for 65 added; the same for item 132. Items 66 and 84 are rewritten in place, each keeping its unfixed half and striking the fixed half. **85 plus 66 is 151**, checked.

---

## 3. The commit, task 3

Checked against `git diff --cached --stat` before committing, not against the brief:

```
 2026-07-25_CONSOLE_DESIGN.md                       |  57 +-
 2026-08-20_LIST_outstanding_items_and_decisions.md |  12 +-
 2026-09-02_HANDOVER_consultant_chat_12.md          | 160 ++++++
 2026-09-02_REPORT_claude_code_step10a.md           | 575 +++++++++++++++++++++
 PROMPT_claude_code_2026-09-02_commit_170_to_172.md | 130 +++++
 PROMPT_claude_code_2026-09-02_step10a_pipeline.md  | 173 +++++++
 PROMPT_intellibooks_2026-09-02_step10a_desktop.md  | 135 +++++
 _step10a_move.py                                   | 195 +++++++
 8 files changed, 1417 insertions(+), 20 deletions(-)
```

Every claim in the message is supported by that diff. The message claims no code change, no test change and nothing outside these eight files, and the diff contains none. **`git commit` reports `8 files changed`, matching.**

The message was used verbatim from the brief, with one addition: the `Co-Authored-By: Claude Opus 5 (1M context)` trailer, because `2ac70ab` and every recent commit on this branch carries it, read from `git log --format=%B`. Nothing else was changed or reworded.

`d6485c8`, `Wed Sep 2 15:57:51 2026 +0100`, author Paul.

**One thing worth knowing about the push, and it was not in the brief.** `git push --dry-run` reported `7cf92ea..d6485c8`, not `2ac70ab..d6485c8`, so **the remote was two commits behind and `7ea2dc4` and `2ac70ab` had never been pushed.** This push carried all three. It was a fast-forward, no force, and the real push printed the same range.

---

## 4. Verification, task 4

### 4.1 Status after the commit

`git --no-optional-locks status --porcelain` printed nothing at all. Working tree clean. `python -m py_compile _step10a_move.py` had been run before staging and its `__pycache__` did not appear, confirming the gitignore covers it.

### 4.2 `git --no-optional-locks show --stat HEAD`, printed whole

```
d6485c839761ffa70553c02bac007ecee665e032
Paul
Wed Sep 2 15:57:51 2026 +0100
docs: amendments 170 to 172, step 10a built, and the step 10a working files

 2026-07-25_CONSOLE_DESIGN.md                       |  57 +-
 2026-08-20_LIST_outstanding_items_and_decisions.md |  12 +-
 2026-09-02_HANDOVER_consultant_chat_12.md          | 160 ++++++
 2026-09-02_REPORT_claude_code_step10a.md           | 575 +++++++++++++++++++++
 PROMPT_claude_code_2026-09-02_commit_170_to_172.md | 130 +++++
 PROMPT_claude_code_2026-09-02_step10a_pipeline.md  | 173 +++++++
 PROMPT_intellibooks_2026-09-02_step10a_desktop.md  | 135 +++++
 _step10a_move.py                                   | 195 +++++++
 8 files changed, 1417 insertions(+), 20 deletions(-)
```

Eight files, as expected.

### 4.3 Amendment record contiguity

Run by the corrected method in CLAUDE.md: scope bounded to the record's own line boundaries, boundaries printed with the result, the list asserted equal to `range(first, last+1)`, and duplicates tested explicitly rather than by a set difference. Output whole:

```
Section heading line: 38  ('## Amendment record')
Next '## ' heading line: 393  ('## How to use this document')
First numbered row line: 48  (amendment 1)
Last  numbered row line: 391  (amendment 172)
Numbered rows matched: 172
Lowest: 1  Highest: 172
Equals range(1, 173)? True
Duplicates: []
Missing from range: []
Outside range: []
```

**172 rows, 1 to 172, no duplicates, no gaps, nothing outside the range.** Matches what the consultant session reported, arrived at independently.

Two notes on the method, because the point of amendment 97 is that this check has failed silently before. The row pattern is `^\|\s*(\d+)\s*\|`, which requires the number to be the **first** cell of the row, and the scope stops at line 393. Section 13A's findings table, numbered 1 to 8, sits at line 1559 and is therefore outside the bound and cannot be matched. The two figures that prove the scope is right rather than merely producing a right answer are the printed boundaries, 48 and 391, and the row count, 172, which equals the highest number rather than exceeding it. In the failure amendment 97 describes, the count was 103 against a highest of 95.

### 4.4 Section 16's head table against the body statuses

```
Head-table rows found: 38  (lines 1726 to 1763)
  BUILT: 19
  OUTSTANDING: 17
  CANCELLED: 1
  MOVED: 1

Body step-status lines found: 38 for 38 steps
Steps with more than one body status line: none

Disagreements between head table and body:
  none

Table rows: 38   Body steps: 38   Disagreements: 0
```

**19 BUILT, 17 OUTSTANDING, 1 CANCELLED, 1 MOVED, 38 rows.** No row where the table and the body disagree, and no step present in one and missing from the other. The comparison is two-way: every table row was looked up in the body, and every body status was looked up in the table.

The head line itself, read from the file:

```
Where we are, as at 2026-09-02. 19 built, 17 outstanding, 1 cancelled, 1 moved out of this order, 38 steps.**
```

**All four figures on the head line match the table.**

### 4.5 Sub-steps per decomposed step

Each set asserted contiguous from 1, and each compared with the count declared in its own head-table row rather than with the brief:

```
10a: 3 sub-step lines, 1 to 3, contiguous from 1: True, duplicates: none
      head-table row declares: 3   brief expects: 3      lines 1808 to 1812
10d: 58 sub-step lines, 1 to 58, contiguous from 1: True, duplicates: none
      head-table row declares: 58  brief expects: 58     lines 1827 to 1949
10e: 15 sub-step lines, 1 to 15, contiguous from 1: True, duplicates: none
      head-table row declares: 15  brief expects: 15     lines 1965 to 1982
10f: 30 sub-step lines, 1 to 30, contiguous from 1: True, duplicates: none
      head-table row declares: 30  brief expects: 30     lines 1994 to 2032
10g: 10 sub-step lines, 1 to 10, contiguous from 1: True, duplicates: none
      head-table row declares: 10  brief expects: 10     lines 2038 to 2051

Steps with sub-steps found: ['10a', '10d', '10e', '10f', '10g']
Steps whose head-table row declares a sub-step count: ['10a', '10d', '10e', '10f', '10g']
```

**All five agree, three ways: the lines on disk, the head-table row and the brief.** The set of steps that have sub-step lines is the same set as the steps whose head-table row declares a count, so no step is decomposed without saying so and none claims a decomposition it does not have. That is the enumeration rather than a spot check: 116 sub-step lines in total, and the two sets were compared as sets rather than assumed equal.

### 4.6 `COA_MASTER_v1` and `build_coa` counts, unchanged, for the consultant's sweep

`grep -c` counts matching **lines**, which is not the same as occurrences, so both are given. Nothing was changed in any of the three files.

| File | `COA_MASTER_v1` lines | occurrences | `build_coa` lines | occurrences |
|---|---|---|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | 15 | 15 | **4** | **6** |
| `2026-08-20_LIST_outstanding_items_and_decisions.md` | 3 | 3 | 0 | 0 |
| `CLAUDE.md` | 0 | 0 | 3 | 3 |

**The `build_coa` row for the design document is the one to watch: 4 lines and 6 occurrences, so a sweep driven by `grep -c` would under-count it by two.** Two of those four lines carry the name twice.

Every occurrence in all three files is the full filename form. There are no bare `COA_MASTER_v1` or `build_coa` tokens:

```
2026-07-25_CONSOLE_DESIGN.md:                          15 COA_MASTER_v1.csv     6 build_coa.py
2026-08-20_LIST_outstanding_items_and_decisions.md:     3 COA_MASTER_v1.csv     0 build_coa
CLAUDE.md:                                              0 COA_MASTER_v1         3 build_coa.py
```

---

## 5. The three known things, task 5

Confirmed present, not touched:

1. **Section 16's head line still dates 10e's six BUILT sub-steps 2026-09-01, against 2026-08-31 in the six sub-steps themselves and in `81aec08`.** Read on line 1721 of the file as committed. Amendment 172's own row says this is deliberately left and is Paul's.
2. **`CLIENT_STATEMENTS_FOLDER_NAME` is pinned by no test, and the casing of `CLIENT_INTELLIBOOKS_FOLDER_NAME` is not asserted.** Unchanged, and this commit touches no test. Still a real gap for the cloud build, where `filed_path` is a string two products compare.
3. **`PROMPT_claude_code_step10a_and_10b.md` is still in the root and must never be sent.** Confirmed on disk. It moves at 10h.

---

## 6. One new finding, and it is in this commit's own content

**Step 10a's body paragraph now has an unbalanced bold run, so part of it renders as the opposite of what was intended.** Line 1804 of `2026-07-25_CONSOLE_DESIGN.md`, the paragraph beginning `10a. **BUILT 2026-09-02.**`.

Measured rather than eyeballed, by counting `**` markers on that one line in the committed version and in `2ac70ab`:

```
2ac70ab: step 10a body line, 30 '**' markers, even
HEAD:    step 10a body line, 33 '**' markers, ODD
```

**It was balanced before this commit's content was written and is not now.** The odd marker means the final bold run is never closed and runs to the end of the line.

The mechanism is at the sentence amendment 170 answered. The text reads, in order: `**Struck 2026-09-02 by amendment 168: 10c is BUILT, ... so nothing schedules the values ever changing. ~~Whether that form is still wanted, and where the flip lives if it is, are Paul's and are open.~~ **Answered 2026-09-02 by amendment 170. ...**`. Markdown treats `**` as a toggle, so **the `**` that opens "Answered" closes the run that opened at "Struck" instead**, and the emphasis inverts from that point on.

**A weaker instance of the same thing is on the head line, line 1721, which is balanced at 20 markers but nests an opening `**Corrected 2026-09-02 by amendment 172` inside the still-open `**Below the table` run.** So that correction note renders plain where the text around it renders bold. Confidence high on the marker counts, which I printed, and high on the toggling rule; moderate on exactly how any given renderer lays out the result, because I have not rendered the file.

**Not fixed**, per flag-do-not-fix, and because the brief's task 6 forbids any edit to the two documents beyond what task 1 named. It is cosmetic in that no figure or statement is wrong, and it is worth fixing in the next edit to that section because the words that render plain are the corrections, which are the part a later session most needs to see.

Two smaller observations, both recorded rather than raised as defects:

- **`_step10a_move.py`'s module docstring cites `IntelliBooks-Desktop-v3.html` lines 2816 and 2819 for the HMRC summary writer, while amendment 172 names line 2820 as the toast the consultant session had to change.** Those are three different line numbers around the same function and the file has since been edited, so this is the ordinary line-number staleness amendment 82 says to leave as written. It is now committed, which is the only reason it is mentioned.
- **The script was syntax-checked before staging**, `python -m py_compile _step10a_move.py`, exit 0. It was not run, and `config.py` was not imported by this session.

---

## 7. Task 6, the stop list

Nothing on it was touched. No edit to any file other than the two documents named in task 1, and those two were committed as they were found, unmodified by this session. Nothing in `worker\`, `app.py`, `config.py` or `tests\`. Nothing under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` or `C:\Intellibills\` was read or written. `_step10a_move.py` was read and syntax-checked and **not run**.

The only files this session created are this report, a commit-message file and two diff files in the session scratchpad at `C:\Users\PDK7\AppData\Local\Temp\claude\c--LastingImpact-receipt-capture\0085bc27-c837-44e7-b879-f65b54d82f61\scratchpad\`, which are outside the repository and are throwaway.

---

## 8. Confidence

**High that the commit contains exactly the eight files intended and that its message claims nothing the diff does not show.** That rests on reading `git diff --cached --stat` before committing and `git show --stat HEAD` after, both printed whole above, and on reading both document diffs whole in bounded ranges rather than filtered.

**High on all six task 4 figures.** Each was produced by a script that prints its own scope and its own counts, and the two that are set comparisons, 4.4 and 4.5, compare in both directions rather than checking members of an assumed set.

**High that the working tree is clean and the push landed**, because `git status --porcelain` returned nothing and the real push printed the same `7cf92ea..d6485c8` range the dry run did.

**High on the section 6 finding's marker counts**, which are printed, and on the fact that the line was balanced at `2ac70ab` and is not now. **Moderate on how it renders**, because I counted markers and did not render the file.

**Nothing here is asserted from a summary.** Every figure was read from the file or from git in this session. The one figure I did not verify myself is the 15:33 BST time at which Paul ran `_step10a_move.py --apply`, which comes from the brief and from amendment 172 and is not checkable from this repository.

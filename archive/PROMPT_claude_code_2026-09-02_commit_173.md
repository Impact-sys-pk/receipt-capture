# Brief: commit amendment 173, the chart of accounts naming sweep

**Written 2026-09-02 by the consultant session, 16:08 BST.** Documentation only. No code, no tests, nothing in `worker\`, `app.py`, `config.py` or `tests\`.

**Report to `C:\LastingImpact\receipt_capture\2026-09-02_REPORT_claude_code_commit_173.md`.**

---

## Task 1. Starting state, and stop if it does not match

```
git --no-optional-locks status --porcelain
git --no-optional-locks log --oneline -2
```

**Expected HEAD `d6485c8`.** **Expected three modified tracked files and two untracked**, being your own report from the last commit and this brief.

| File | Bytes | md5 |
|---|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | 633,830 | `1acd0afb09cdf154931756068082a501` |
| `CLAUDE.md` | 58,318 | `0d89db7ada0ebf01700be2b18339e6e3` |
| `2026-08-20_LIST_outstanding_items_and_decisions.md` | 95,922 | `5bdd0a39285d867eadce60612fd5cb8d` |

All three read back off disk and hashed after writing. **Stop if any differs, or if the porcelain shows anything else.**

---

## Task 2. What changed

**Amendment 173, and version 1.32 to 1.33.** The chart of accounts naming sweep. The master is `IntelliCharts\COA_MASTER_v2.xlsx`, `Master` sheet, published by `publish_master.py` into `IntelliCharts\Chart Library\`, and the app default chart is `Chart Library\Master_COA.csv`. `COA_MASTER_v1.csv` is in `IntelliCharts\Cockups\` and `build_coa.py` is gone.

**Eleven live references changed across ten body lines** of the design document, at 5.5 twice, 11.1, 12.3, 13, 13.1, sub-step 10g.10, steps 11 and 12, and 18.10. **One in `CLAUDE.md`**, the live instruction that told a session to prove a chart change by running `build_coa.py`. **None in the outstanding items list**, which gains a note on item 92 instead.

**Twenty of the twenty-seven references are deliberately left**, being ten in this record, two dated bullets in `CLAUDE.md` and three dated lines in the outstanding items list. Amendment 82: history keeps its old values.

**No account or column count is restated.** "122 accounts in 20 columns" is struck in three places and not replaced.

**And one fix that is not about the chart.** Step 10a's body paragraph had an unbalanced bold run, which you found while committing `d6485c8`. One `**` is added to close it.

---

## Task 3. Commit and push

One commit:

```
docs: amendment 173, the chart of accounts naming sweep

The master is IntelliCharts\COA_MASTER_v2.xlsx, Master sheet, published by
publish_master.py into IntelliCharts\Chart Library\, and the app default
chart is Chart Library\Master_COA.csv. COA_MASTER_v1.csv is in
IntelliCharts\Cockups\ and build_coa.py is gone.

Eleven live references changed across ten body lines of the design document,
one in CLAUDE.md, and none in the outstanding items list, which gains a note
on item 92 instead. Twenty of the twenty-seven references are left as
history, per amendment 82.

No account or column count is restated. 122 accounts in 20 columns is struck
in three places. Chart Library\Master_COA.csv holds 240 accounts in 12
columns as published 2026-09-01, read by parsing the file, and a maintained
chart cannot have its size recorded in a document that is not maintained
with it.

Also closes the unbalanced bold run on step 10a's body paragraph, found by
Claude Code while committing d6485c8. The open run was at the join between
amendment 168's strike and amendment 170's answer, so the line had rendered
with its emphasis inverted since that morning.

Files: 2026-07-25_CONSOLE_DESIGN.md, CLAUDE.md,
2026-08-20_LIST_outstanding_items_and_decisions.md,
2026-09-02_REPORT_claude_code_commit_170_to_172.md,
PROMPT_claude_code_2026-09-02_commit_173.md
```

**Check the message against `git diff --cached --stat` before committing.** Then push.

---

## Task 4. Verify, and quote every output

1. **`git --no-optional-locks status --porcelain` after the commit.** Expected empty.
2. **Amendment record contiguity**, bounded to the record's own lines, bounds printed. **Expected 173 rows, 1 to 173, no duplicates.**
3. **Section 16 head table against the body statuses.** Expected 19 BUILT, 17 OUTSTANDING, 1 CANCELLED, 1 MOVED, 38 rows, unchanged by this commit.
4. **Count lines with an odd number of `**` markers in all three files.** Expected 0 in `2026-07-25_CONSOLE_DESIGN.md` and 0 in `CLAUDE.md`. **28 is expected in `2026-08-20_LIST_outstanding_items_and_decisions.md` and is not a defect:** those are bold runs wrapped across two lines in prose paragraphs, and none was touched by this commit. Say so if you get different numbers.
5. **Every remaining `COA_MASTER_v1` and `build_coa` occurrence in the design document body, outside the amendment record**, printed whole with a one-line reason. **Expected 12, every one either inside a `~~` strike or naming the old file as the thing corrected from.** **None should assert that `COA_MASTER_v1.csv` is the master or that `build_coa.py` generates it.** Report any that does.
6. **A note on counting.** `grep -c` reports lines and `grep -o | wc -l` reports occurrences, and this sweep's own first count was wrong because of it. Use occurrences and say which you used.

---

## Task 5. Stop and ask about

- Any file other than the three named in task 1.
- Anything under the practice root or under `C:\Intellibills\`.
- A starting state that does not match.

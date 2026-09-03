# Claude Code brief, 2026-08-22: a OneDrive conflict-copy guard in `build_coa.py`

Written by the consultant session. One change, one file, and that file is **outside this repository**. Read the whole brief before starting; the authorisation in section 2 is the part that makes it possible at all.

---

## 1. What this is

`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts\build_coa.py` gains one check at the top of its executable flow: **if a OneDrive conflict copy is sitting in that folder, the script prints what it found and exits without reading or writing anything.**

Nothing else changes. No refactor, no reordering, no tidying.

**Why it is worth doing.** That folder is in OneDrive and OneDrive is synced to two machines, so a simultaneous or offline edit produces a second file beside the original. `build_coa.py` reads whatever is named `COA_MASTER_v1.csv` and generates the three import files, the Sage Final Accounts mapping table and the destination exceptions from it. A conflict copy in that folder means the outputs can be built from the wrong master and nothing would say so.

**Refuse rather than warn**, because that is already the script's habit: it writes nothing at all when a validation check fails.

---

## 2. Authorisation, and its limit

`CLAUDE.md`, under **AUTOMATIC Task Mode**, item 2 of "Stop and ask, even under `AUTOMATIC task`", forbids writing, moving or deleting any file **outside** `C:\LastingImpact\receipt_capture`, and names `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` specifically.

**Paul has authorised this one file, for this one change, on 2026-08-22.** That is:

- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts\build_coa.py`

**It is not a licence for anything else under that tree.** No other file in `IntelliCharts\` is to be created, edited, moved or deleted, and no file anywhere else under the practice root is touched. If the work seems to need a second file changed, stop and report rather than choosing.

---

## 3. There is no git in that folder

`IntelliCharts\` is **not a repository and is not inside one.** Checked 2026-08-22 with `git rev-parse --show-toplevel`, which found nothing up to the mount point.

So the usual conventions do not apply here. **No branch, no commit, no diff, no `git mv`.** Do not run any git command against that folder and do not `git init` it: whether it should be versioned is an open question and not this task.

**What replaces the commit as evidence** is in section 7: the inserted lines read back off disk, and two runs of the script in a temporary copy.

**This brief itself lives in this repository** at `C:\LastingImpact\receipt_capture\`, and it becomes spent on delivery of your report, so it moves to `archive\` at step 10h like the others.

---

## 4. The change, exactly

**Where.** `build_coa.py` is a 922-line top-level script with no `main()`. Insert the guard **immediately after line 726, `import os`, and before line 727, `MASTER = "COA_MASTER_v1.csv"`.**

**Why there and not at the top of the file.** Two reasons, both checked on 2026-08-22:

- **It is before the first file is opened.** In execution order the first `open()` reached is line 731, which reads the master. The `open()` at line 275 is inside `check_chart_drift()`, which is not called until line 747.
- **`os` already exists at that point**, so the import line at 14 does not have to be touched. There are three `import os` statements in the file already, at 268 (`import os as _os`, inside the function), 726 and 917. **Do not consolidate them.** That is a tidy-up nobody asked for.

**What the guard does.** Scan the names in the script's own working directory, which is where every path in this script resolves, since it uses bare relative filenames throughout. If any name matches the rule below, print a refusal naming every matching file, then exit with status **3**.

**Exit code 3, not 1 and not 2.** 1 is validation failure, at lines 736 and 815. 2 is Sage chart drift, at line 291. A caller should be able to tell the three apart.

---

## 5. The rule

A name is a conflict copy if any of these is true, tested on the base name and on the stem, meaning the name with its final extension removed:

- the base name contains `-DESKTOP-`
- the base name contains `-LAPTOP-`
- the stem ends with `-Copy`
- the stem ends with a space, an opening bracket, a single digit 1 to 9, and a closing bracket, so ` (1)` through ` (9)`

These four shapes are the ones section 13A finding 5 of `2026-07-25_CONSOLE_DESIGN.md` already lists as `conflict_copy`, and they are the shapes OneDrive produces.

**One stated limit, so nobody believes it is complete.** `-DESKTOP-` and `-LAPTOP-` are the Windows default computer-name prefixes. A machine renamed to something else produces a conflict copy this rule will not catch. It is worth having anyway because it catches the common cases; it is not a guarantee.

**Checked against the live folder on 2026-08-22 before this brief was written.** All 26 names in `IntelliCharts\` and `IntelliCharts\archive\` were tested and **none matches**, so the guard does not fire on the folder as it stands. In particular `COA_MASTER_v1.backup_2026-08-17.csv` does not match and needs no allowlist. Four synthetic names were tested and all four match: `COA_MASTER_v1-DESKTOP-AB12.csv`, `COA_MASTER_v1 (1).csv`, `COA_MASTER_v1-Copy.csv` and `build_coa (2).py`.

---

## 6. What the guard must not do

- **It must not print `ALL CHECKS PASSED`.** The file's own docstring says validation output must end with that line, and a refusal is not a pass.
- **It must not have an override flag.** `--accept-drift` exists because accepted drift is a real decision. A conflict copy is never something to build over, so there is no `--accept-conflicts`.
- **It must not delete, rename or move the offending file.** It reports and Paul decides. `IntelliCharts\` has no reconciliation tool and this is not one.
- **It must not read any file** before deciding. That is the point of the placement.

---

## 7. How to prove it, since there is no test suite

`IntelliCharts\` has no `tests\` directory and this script has no test coverage. So the proof is a pair of runs in a **temporary copy of the folder, outside OneDrive**. This works because every path in `build_coa.py` is a bare relative filename resolved against the current working directory, verified on 2026-08-22 at line 727 and at the seven `open(..., "w")` calls.

1. Copy the whole of `IntelliCharts\` to a temporary directory outside OneDrive and outside this repository.
2. In the copy, run `python build_coa.py`. **Quote the last two lines.** It should behave exactly as before the change.
3. In the copy, create an empty file named `COA_MASTER_v1-DESKTOP-AB12.csv`.
4. Run `python build_coa.py` again. **Quote the whole output.** It must refuse, name that file, exit 3, and not print `ALL CHECKS PASSED`.
5. Delete that file from the copy, run once more, and confirm it builds again.
6. Delete the temporary directory.

Then read the inserted lines back off `IntelliCharts\build_coa.py` on disk and quote them in the report, with the line numbers they now occupy.

---

## 8. Do not run `build_coa.py` in the live folder

Not once, not to check. Two reasons, both read from the file on 2026-08-22:

- **Line 822 rewrites `COA_MASTER_v1.csv`.** A successful run overwrites the master, which is the only file in that folder edited by hand.
- **Line 863 rewrites `coa_map_sage_final_accounts.csv`, and `check_chart_drift()` reads that same file at line 269 as its baseline.** So a successful run silently re-baselines the Sage drift check. A run made "just to test" would destroy the evidence the next real check depends on.

**And never run it with `--seed`.** Line 729 reads `seed = "--seed" in sys.argv`, and a seeded run rebuilds the master from the table inside the script and discards Paul's edits.

Paul runs the live build himself, when he chooses to.

---

## 9. What to report

- The inserted lines, read back off disk, with their line numbers.
- The output of all three runs in the temporary copy, quoted whole and not truncated.
- Confirmation that no file in `IntelliCharts\` other than `build_coa.py` was touched, and that the temporary directory was removed.
- Anything wrong you noticed and did not fix, per **flag, do not fix**. That folder has had no code review; if something in `build_coa.py` looks wrong, say so and change nothing.
- Any of your own mistakes, including ones you caught and corrected.
- A confidence level, and what it rests on.

Name the file, the function and the line in full, every time. Not "the script" or "the guard".

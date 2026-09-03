# Brief: commit amendment 174 and the two refreshed step 10d briefs

**Written 2026-09-02 by the consultant session, 16:34 BST.** Documentation only. No code, no tests.

**Report to `C:\LastingImpact\receipt_capture\2026-09-02_REPORT_claude_code_commit_174.md`.**

---

## Task 1. Starting state, and stop if it does not match

```
git --no-optional-locks status --porcelain
git --no-optional-locks log --oneline -2
```

**Expected HEAD `5748b22`.** **Three modified tracked files and two untracked**, being your report from the last commit and this brief.

| File | Bytes | md5 |
|---|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | 638,556 | `79df282eb2a67f51e667b3d1b74c0421` |
| `PROMPT_claude_code_2026-09-01_step10d_pipeline.md` | 34,172 | `f26c61b559b099d20e622f28567aad8d` |
| `PROMPT_intellibooks_2026-09-01_step10d_desktop.md` | 23,800 | `c87c7347071e5fa9dae7defa8cb3e27a` |

**`PROMPT_phoneapp_2026-09-01_step10d.md` is deliberately unchanged.** Its line numbers are the phone app's `index.html` and step 10a did not touch that file.

---

## Task 2. What changed

**Amendment 174, and version 1.33 to 1.34.** Your two findings and two more of the same class. Amendment 173's headline corrected from twenty to fifteen. Sub-step 10d.15's count of `getDir` sites corrected from four to nine plus a string site. Step 10a's `config.REVIEW_ROOT` citation corrected from `config.py:42` to `:60`. The marker arithmetic reconciled by naming the baselines: 30 is the blob at `2ac70ab`, which predates amendments 170 and 171 because neither was committed until `d6485c8`.

**The two step 10d briefs have their line numbers refreshed**, and each gains a note at the top saying when and how. **Six `config.py` citations in the pipeline brief moved by eighteen**, and each was re-derived by reading the current file rather than by adding a constant; all six land on the construct they name. **Fifteen citations in the Desktop brief**, derived by taking each line out of `IntelliBooks\App\IntelliBooks-Desktop-v3.html.bak-before-intellibooks-parent` and finding that exact line in the saved file. The shift there is not uniform: 0, then 5, then 13.

**One paragraph in the Desktop brief is rewritten rather than renumbered.** It described `filed_path` at line 2519 as a hand-built string. That line is now 2532 and calls `clientFolderPath()`.

---

## Task 3. Commit and push

```
docs: amendment 174, and the step 10d briefs' line numbers refreshed

174 takes Claude Code's two findings on d6485c8 and 5748b22 and adds two of
the same class.

Amendment 173's headline said twenty references were left as history and it
is fifteen; the correct breakdown was in the same row. The same wrong figure
is in 5748b22's message and cannot be corrected, so the amendment row is the
correction a reader will find. A diff --cached --stat cannot check a count.

Sub-step 10d.15 said IntelliBooks has four getDir(["Clients", ...]) sites.
It has nine, plus a tenth that builds the path as a string. Step 10a's body
cited config.REVIEW_ROOT at config.py:42 and it is at :60.

The bold-marker arithmetic is reconciled rather than left hanging: 30 is the
committed blob at 2ac70ab, which predates amendments 170 and 171 because
neither was committed until d6485c8. Both measurements were right and
neither said which file it had measured.

The two step 10d briefs have their line numbers refreshed after step 10a,
with a note at the top of each saying when and how. Six config.py citations
moved by eighteen; fifteen Desktop citations moved by 0, 5 or 13 depending
on where they sit. Section A stays byte-identical across all three briefs at
3,056 bytes.

Files: 2026-07-25_CONSOLE_DESIGN.md,
PROMPT_claude_code_2026-09-01_step10d_pipeline.md,
PROMPT_intellibooks_2026-09-01_step10d_desktop.md,
2026-09-02_REPORT_claude_code_commit_173.md,
PROMPT_claude_code_2026-09-02_commit_174.md
```

**Enumerate every figure in that message before you commit it**, which is the rule amendment 174 adds. Then push.

---

## Task 4. Verify, and quote every output

1. **Status after the commit.** Expected empty.
2. **Amendment record contiguity**, bounds printed. **Expected 174 rows, 1 to 174, no duplicates.**
3. **Section 16 head table against the body.** Expected 19 / 17 / 1 / 1, 38 rows, unchanged.
4. **Odd `**` marker lines.** Expected 0 in the design document.
5. **Section A in all three step 10d briefs**, hashed. **Expected identical, 3,056 bytes, md5 `0d0dda57d858...`.** The phone app brief is not in this commit and must still match the two that are.
6. **Every `config.py:N` in `PROMPT_claude_code_2026-09-01_step10d_pipeline.md`, with what line N now holds.** Expected six, at 56, 70, 126, 150, 167 and 168, landing on `EXPORTS_DIR`, `RECEIPTS_LOG`, `def load_clients`, `def load_firms`, `CLIENTS, CLIENTS_BY_CODE = load_clients()` and `FIRMS = load_firms()`. **Report any that does not.**
7. **`grep` the design document for `twenty of the twenty-seven`.** Expected zero outside amendment 174's own row.

---

## Task 5. Stop and ask about

- Any file other than the three named in task 1.
- Anything under the practice root or `C:\Intellibills\`.
- A starting state that does not match.

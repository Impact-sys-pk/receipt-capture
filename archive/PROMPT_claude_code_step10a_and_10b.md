# SUSPENDED 2026-07-30. DO NOT SEND THIS PROMPT.

**Suspended by Paul's decision of 2026-07-30, recorded as amendment 70 of `2026-07-25_CONSOLE_DESIGN.md`.**

Both steps in this prompt rest on the client folder layout in amendment 55, and that layout is wrong in principle. `Clients\{name}\` is the client's own digitised records inside Paul's firm's filing system, shown on the client portal. It is not a tree this system owns, so namespacing it `_IntelliBooks\` is backwards, and step 10a would hard-code that name into config on both sides at once.

Step 10b, the reconciliation check, is scoped to the same tree and therefore has nothing to audit until the scope is restated. Its purpose also changes, from "is our store consistent" to "did what we published arrive". See the note now at the top of section 13A.

**Read section 18 of the design document, and 18.2 in particular, before rewriting any of this.**

**One part survives any answer**, and it is worth keeping when this is rewritten: the client folder layout belongs in config constants rather than in string literals, with the pair of tests that proves an empty managed-folder name produces no extra path level. That was the real deliverable of step 10a and it is independent of what the folders end up being called.

**The rest of this file is the 2026-07-30 revision, kept as it stood.** Its file-staging instructions and its list of modified files are now out of date, because the design document and the Desktop brief have both changed again since.

---

# Claude Code AUTOMATIC task: steps 10a and 10b, the folder layout constants and the reconciliation check

**Written 2026-07-29 by the consultant session. Revised 2026-07-30, and read the revision note before section 1.**

**Revision note.** This prompt was written on 2026-07-29, declared complete, and never sent. Two things changed before it was, and one of them is a change to the specification:

- **Section 1 was stale.** It expected two modified tracked files and told you to commit them. That commit has happened, in `bc53c4d` and `56e994c`. Section 1 is rewritten below.
- **Section 13A and amendment 55 had a gap, now closed by amendment 65.** `Statements\` is a fifth managed folder and was left out of the enumeration. It gets a constant in step 10a and comes into 13A's findings 1 and 2. Section 2 is rewritten below. **Read amendment 65 as well as 55 and 56.**

The gap was found by checking this prompt's own `filing.py` line numbers against the file. All six were right; the description of one of them was not.

Approved in advance: creating and editing files the task names, creating new test files, running the suite, `py_compile`, read-only database queries, committing, and a fast-forward push to `feat/console-phase0`. The seven exceptions in the AUTOMATIC Task Mode section of `CLAUDE.md` still apply, and two of them are live in this task, so read the "Do not" section before you start.

Read section **13A** of `2026-07-25_CONSOLE_DESIGN.md` first, in full. It is the specification. Amendments 55 and 56 give the reasoning behind it. This prompt is the task list, not the spec.

---

## 1. Verify first, and report before building

1. Branch `feat/console-phase0`. The tip was `461f9d1` when this revision was written, on 2026-07-30. **Report what you actually find rather than trusting that**, because the last time this prompt quoted a tip it was stale by the time it was read, and that cost a round trip.
2. `python -m pytest -q` passes. Report the count. It was 263 at the last report and I could not verify it: the sandbox has no pytest and `.venv` is a Windows environment. A static count of 259 `def test_` functions is consistent with 263 collected once parametrisation expands, which supports the figure without confirming it. **Your count is the first real one since 2026-07-29.** If it is not 263, say so and stop before writing code.
3. **Expect three modified tracked files, and commit them together as one docs commit** before you write any code, so the specification is in history before the thing it specifies. **This prompt is one of the three**, because prompts are tracked in this repository:

   | File | What changed |
   |---|---|
   | `2026-07-25_CONSOLE_DESIGN.md` | The v1.5 header, and amendments 65 and 66. |
   | `PROMPT_intellibooks_desktop_changes.md` | New section 5A, change I, and section 7 corrected from eight changes to nine. |
   | `PROMPT_claude_code_step10a_and_10b.md` | This file, revised on 2026-07-30. |

   Stage those three by name. **Do not use `git add .` or `git add -A`.** Two untracked files and one file carrying somebody else's uncommitted work are all in the repository root, per points 4 and 5, and any of those three would sweep them in:

   ```
   git add 2026-07-25_CONSOLE_DESIGN.md PROMPT_intellibooks_desktop_changes.md PROMPT_claude_code_step10a_and_10b.md
   ```

   Then confirm what is staged before committing:

   ```
   git status --short
   ```

   In that output, the first column is the staged state and the second is the working tree. You want to see exactly those three files with `M` in the **first** column. `2026-07-29_HANDOVER_consultant_chat_3.md` must still show ` M`, modified but **not** staged, and the two untracked files must still show `??`. If anything else is staged, unstage it by name and do not guess at the rest:

   ```
   git restore --staged <file>
   ```

   Then commit:

   ```
   git commit -F- <<'EOF'
   docs: amendments 65 and 66, and change I for IntelliBooks Desktop

   Amendment 55 enumerated the namespaced client folders and missed
   Statements\, which file_statement() writes to. It becomes _Statements
   under _IntelliBooks\, gets a config constant at step 10a, and comes into
   findings 1 and 2 of the reconciliation check. Its sidecar already uses the
   same full-filename-plus-.json convention as a receipt's, so the matching
   rule needs no special case.

   Amendment 66 records the three Desktop checks run on 30 July, all passed,
   and PKPH-books.json deleted, which leaves finding 8 with no live specimen.
   It also records a duplicate-rule finding in addRule(): two identical
   pattern-only rules can be created and then diverge, invisibly to changes G
   and H. Decided to guard it at source, specified as change I in section 5A
   of the Desktop brief, to be built in the same visit as change D.

   Also moves the design document header to v1.5, and corrects two errors in
   the 30 July manual checks.
   EOF
   ```

   **Do not use `git commit -am`.** It stages every modified tracked file, which would pull in the handover in point 5.

4. **Expect two untracked files, and leave both alone:** `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` and `PAUL_CHECKS_2026-07-30.md`. Whether they are committed is Paul's call, not this task's. Do not `git add .`; see point 3.
5. **One thing to report, not to fix.** `2026-07-29_HANDOVER_consultant_chat_3.md` has 22 uncommitted lines added to it on disk, a new section 0 about the environment and the four gitignored things a fresh clone lacks. I did not write it and it is not mine to commit. Report that it is there so Paul can decide; it is a real improvement and losing it would be a shame. **It must not go into the commit in point 3**, which is another reason to stage by name.
6. Confirm on Windows, not from a sandbox, that no tracked file other than the three in point 3 and the handover in point 5 is modified. **The sandbox cannot answer this**: it does not see Git for Windows's line-ending configuration, so files show as modified when they are not. `git diff --ignore-cr-at-eol --name-only` from the sandbox returns those four and nothing else, which is corroboration rather than proof. **If it returns a fifth, stop and report it rather than committing.**

---

## 2. Step 10a: config constants for the client folder layout

**This commit must change no behaviour.** That is the whole point of doing it separately.

Introduce constants for the client-level folder layout and replace the string literals with them, leaving the values as they are today. The flip to the namespaced form happens in step 10c, when there is nothing on disk to migrate.

Suggested shape, in `config.py` beside the other path constants:

```python
# The client-level folder layout. Namespaced under a single managed folder per
# design document amendments 55 and 65, and flipped to those values at step 10c,
# when the reset means there is nothing on disk to migrate. Today's values keep
# the current layout so introducing the constants changes nothing.
CLIENT_MANAGED_DIRNAME = ""              # becomes "_IntelliBooks"
CLIENT_RECEIPTS_DIRNAME = "Receipts"     # becomes "_Receipts"
CLIENT_STATEMENTS_DIRNAME = "Statements" # becomes "_Statements"
CLIENT_REVIEW_DIRNAME = "Review"         # becomes "_Review"
```

Three things about that, all deliberate:

- An empty `CLIENT_MANAGED_DIRNAME` must mean "no extra level", not a `""` path segment that produces a double separator or a folder with no name. Handle it explicitly and test it both ways: a test that the path is `Clients\X\Receipts\...` when it is empty, and `Clients\X\_IntelliBooks\_Receipts\...` when it is set. **That pair of tests is the real deliverable of this step**, because it is what makes 10c a one-line change that has already been proven.
- The tax year folder is **not** in this scheme and keeps its bare `2026-27` form. Amendment 55 explains why: Desktop matches year folders against `/^\d{4}-\d{2}$/`. **Nor is `{platform}` under `_Statements`**, which is a data value rather than a folder this design names.
- **`CLIENT_STATEMENTS_DIRNAME` is new as of amendment 65** and is the reason this prompt was revised. See the note on the third site below.

The sites to change, and I believe this is all of them, but check rather than trust me. All six line numbers were verified against `worker/filing.py` on 2026-07-30 and all six were correct:

- `worker/filing.py:64` `get_client_directory()`, the single choke point for the client folder
- `worker/filing.py:77`, in `file_receipt()`, appending `"Receipts" / tax_year`
- `worker/filing.py:102`, in `file_statement()`, appending **`"Statements" / tax_year / platform`**. **The 2026-07-29 draft of this prompt described this line as appending `Receipts` or `Review`. It does not.** That error is what surfaced the gap in amendment 55, and it is why there is now a fourth constant. Had you met it as originally written you would have had to either invent an unspecified constant or leave a literal behind, and a literal left behind defeats the entire point of step 10a.
- `worker/filing.py:124`, in `file_review()`, appending `"Review"`
- `worker/filing.py:159` `_review_dir_for_client_code()`
- `worker/filing.py:297`, the `config.CLIENTS_ROOT.glob("*/Review")` scan

`_Handover Pack` and `_HMRC Summaries` are written only by Desktop. Do not add constants for folders this side never touches.

**Do not touch `IntelliBooks-Desktop-v3.html`.** Desktop's six `getDir(["Clients", ...])` sites are the IntelliBooks session's work and are being briefed separately. If the two halves flip at different times receipts stop arriving, so the flip is coordinated at 10c and neither side does it early.

---

## 3. Step 10b: the reconciliation check

Build to section 13A. The findings table in 13A.3 is the specification, currently eight rows; 13A.4 is the matching rule and contains the trap; 13A.5 is the output.

**Findings 1 and 2 now cover `_Statements\{tax year}\{platform}\` as well as `_Receipts\{tax year}\`**, per amendment 65. No special case is needed: `file_statement()` writes its sidecar as `dest_file.with_suffix(dest_file.suffix + ".json")`, the same full-filename-plus-`.json` convention as `file_receipt()`, so 13A.4's pairing rule applies unchanged. I checked both functions rather than assuming they were symmetrical. Note that nothing is in those folders today, so **finding 1 and 2 over `_Statements` cannot be exercised by the live run in section 4** and must be covered by a fixture.

Structure it as a module plus a thin CLI, the same shape as the resolution service and its entry points: the logic testable without touching the real OneDrive tree, and `reconcile_files.py` at the repository root doing argument parsing and printing only.

Points where I expect you to have to think, so flag rather than guess:

- **Read-only means read-only.** No `mkdir`, no `shutil.move`, no writes anywhere except `data/reconciliation.json`. 13A.2 is not a preference.
- Findings 3, 4, 6 and 7 need the database. Open it read-only.
- Finding 5's conflict-copy patterns must not match a legitimate `-2` or `-3` suffix from `_unique_path()`. Those are the pipeline's own uniqueness convention and are correct files.
- All filename matching is case-insensitive, per 13A.4.
- A client folder with no managed subfolder at all is not a finding. Most clients will have nothing filed yet.

Tests go in `tests/`, and the log-isolation rule from section 15 applies: nothing may write to `data/*.log` or the live tree. Build the fixture as a temporary directory tree and a temporary database.

Red before green where you can. Where you cannot, mutate the behaviour from a pristine copy and show which tests catch each mutation, as you did for the resolution service.

---

## 4. Then run it once for real

After the tests pass, run `reconcile_files.py` against the live tree and report what it found. This is the step's acceptance test and the expected result is **not** a clean report:

- **23 ghost receipts** are known to exist across the three books files, from `ingestReceiptFiles()` pairing sidecars to images on mismatched keys. **The check will not see them**, because they are books entries rather than files on disk, and that limit belongs in your report: a clean receipts result does not mean the books are clean. What it should see is any file in those folders that does not pair. Report what it actually finds and say plainly whether it matches.
- **`books_file_unregistered` has lost its specimen and needs a fixture.** ~~`PKPH-books.json` must appear as `books_file_unregistered`.~~ **Corrected 2026-07-30: `PKPH-books.json` has been deleted.** Item 25's second pass in Desktop was confirmed running that morning, it named `PKPH` in both the toast and the console, and the file was removed on the strength of it, which is what Paul had said he was waiting for. `IntelliBooks\Books\` now holds three files, `PAUL-books.json`, `TEST-books.json` and `TEST2-books.json`, and all three match a client in `clients.csv`. So **finding 8 will correctly report nothing on the live run, and that is not evidence it works.** Cover it with a fixture: a temporary `Books\` directory holding a `*-books.json` whose code is in no `clients.csv` row. Say in your report that the live run could not exercise it and why.
- `Clients\Test\Receipts\2026-27\` holds files of several vintages including `_4.5` and `_8` names predating the two-decimal rule. Report anything unexpected there rather than filtering it out. **Note the folder is `Test`, not `TEST`.** The two registries disagree about that client's name and it works only because NTFS is case-insensitive, per amendment 44. Do not tidy it; it is a deliberate open item and a patch would hide it.

**The live tree as read on 2026-07-30, so you have a baseline rather than a guess.** `Clients\` holds five client folders. Their subfolders:

| Client folder | Subfolders |
|---|---|
| `Paul Keating` | `Document Requests`, `Misc`, `Receipts`, `Review` |
| `Test` | `Receipts`, `Review` |
| `Test 2` | `Receipts` |
| `She Run's It! Ldn Ltd` | none |
| `Tom Test` | none |

Three things follow, and each is a distinct thing the run should demonstrate. **`She Run's It! Ldn Ltd` and `Tom Test` must produce no findings at all**, which is the "a client folder with no managed subfolder is not a finding" rule in section 3 doing its job; if either shows up, that rule is wrong. **`Paul Keating\Document Requests\` and `Paul Keating\Misc\` must be ignored**, because they are outside the managed tree and belong to another tool. And **no `Statements\` folder exists anywhere**, which is why the `_Statements` half of findings 1 and 2 needs a fixture.

A run that reports nothing means the check does not work. Say so if that happens rather than reporting success.

---

## 5. Report back

1. The verification results from section 1, with numbers.
2. Each commit hash with what it contains. At least three: the docs, 10a, 10b.
3. The behaviour-unchanged claim for 10a **demonstrated**, not asserted. The suite passing plus the pair of layout tests is the evidence.
4. The real run's output in full.
5. Anything where this prompt or section 13A disagrees with the code. Section 13A was written from reading the code but not from building against it, and specifications written that way are usually wrong somewhere.
6. Your own mistakes, including ones you caught yourself.

## 6. Do not

- **Do not flip the folder constants to their namespaced values.** That is 10c, it is coordinated with Desktop, and doing it early splits the two tools.
- **Do not write, move or delete anything under the OneDrive path.** The check is read-only and this is one of the seven AUTOMATIC exceptions. Reading is fine.
- **Do not delete `PKPH-books.json`**, even though Paul has decided it goes. It is outside the repository and it is his to remove.
- Do not edit `2026-07-25_CONSOLE_DESIGN.md` beyond committing it as it stands. The consultant session owns it. If 13A is wrong, report it.
- Do not touch `IntelliBooks-Desktop-v3.html` or anything under `IntelliBooks\App\`.
- Do not merge `main`. Do not amend, rebase, reset or force.
- One command per Bash call, no `cd` prefix, no `&&` chains.

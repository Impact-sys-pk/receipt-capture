# Claude Code AUTOMATIC task: steps 10a and 10b, the folder layout constants and the reconciliation check

**Written 2026-07-29 by the consultant session.**

Approved in advance: creating and editing files the task names, creating new test files, running the suite, `py_compile`, read-only database queries, committing, and a fast-forward push to `feat/console-phase0`. The seven exceptions in the AUTOMATIC Task Mode section of `CLAUDE.md` still apply, and two of them are live in this task, so read the "Do not" section before you start.

Read section **13A** of `2026-07-25_CONSOLE_DESIGN.md` first, in full. It is the specification. Amendments 55 and 56 give the reasoning behind it. This prompt is the task list, not the spec.

---

## 1. Verify first, and report before building

1. Branch `feat/console-phase0`. Report the tip rather than assuming it: my last prompt quoted a stale one and that cost a round trip.
2. `python -m pytest -q` passes. Report the count.
3. **Two** modified tracked files are expected, and no others: `2026-07-25_CONSOLE_DESIGN.md`, carrying section 13A and amendments 55 to 62, and `PROMPT_intellibooks_desktop_changes.md`, the brief the IntelliBooks Desktop session is working from. **Commit both first, on their own**, before you write any code, so the specification is in history before the thing it specifies. One commit:

   ```
   docs(console): add section 13A, file reconciliation, and amendments 55 to 62

   Records the namespaced client folder layout, why folder locking is not
   achievable on Windows with OneDrive and what replaces it, and six findings
   and decisions from a day of Desktop work: a defect adding every scanned
   receipt to the books twice, the forward-only scope of its fix, a pill for
   receipts with no amount, a toast when a statement rule is overwritten, and
   two rules for one supplier where the narrower one silently wins.

   The brief gains changes E, F and G and records A, B, E as built.
   ```

   The amendment count moves as the consultant session works, so **report what you actually find** rather than failing if it is 63 rather than 62. What must hold is that the numbering is contiguous from 1 and that no third tracked file is modified.
4. Confirm on Windows, not from a sandbox, that no other tracked file is modified.

---

## 2. Step 10a: config constants for the client folder layout

**This commit must change no behaviour.** That is the whole point of doing it separately.

Introduce constants for the client-level folder layout and replace the string literals with them, leaving the values as they are today. The flip to the namespaced form happens in step 10c, when there is nothing on disk to migrate.

Suggested shape, in `config.py` beside the other path constants:

```python
# The client-level folder layout. Namespaced under a single managed folder per
# design document amendment 55, and flipped to those values at step 10c, when
# the reset means there is nothing on disk to migrate. Today's values keep the
# current layout so introducing the constants changes nothing.
CLIENT_MANAGED_DIRNAME = ""          # becomes "_IntelliBooks"
CLIENT_RECEIPTS_DIRNAME = "Receipts" # becomes "_Receipts"
CLIENT_REVIEW_DIRNAME = "Review"     # becomes "_Review"
```

Two things about that, both deliberate:

- An empty `CLIENT_MANAGED_DIRNAME` must mean "no extra level", not a `""` path segment that produces a double separator or a folder with no name. Handle it explicitly and test it both ways: a test that the path is `Clients\X\Receipts\...` when it is empty, and `Clients\X\_IntelliBooks\_Receipts\...` when it is set. **That pair of tests is the real deliverable of this step**, because it is what makes 10c a one-line change that has already been proven.
- The tax year folder is **not** in this scheme and keeps its bare `2026-27` form. Amendment 55 explains why: Desktop matches year folders against `/^\d{4}-\d{2}$/`.

The sites to change, and I believe this is all of them, but check rather than trust me:

- `worker/filing.py:64` `get_client_directory()`, the single choke point for the client folder
- `worker/filing.py`, the three callers that append `"Receipts"` or `"Review"`, around lines 77, 102 and 124
- `worker/filing.py:159` `_review_dir_for_client_code()`
- `worker/filing.py:297`, the `config.CLIENTS_ROOT.glob("*/Review")` scan

`_Handover Pack` and `_HMRC Summaries` are written only by Desktop. Do not add constants for folders this side never touches.

**Do not touch `IntelliBooks-Desktop-v3.html`.** Desktop's six `getDir(["Clients", ...])` sites are the IntelliBooks session's work and are being briefed separately. If the two halves flip at different times receipts stop arriving, so the flip is coordinated at 10c and neither side does it early.

---

## 3. Step 10b: the reconciliation check

Build to section 13A. The findings table in 13A.3 is the specification, currently eight rows; 13A.4 is the matching rule and contains the trap; 13A.5 is the output.

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
- **`PKPH-books.json`** must appear as `books_file_unregistered`.
- `Clients\TEST\Receipts\2026-27\` holds files of several vintages including `_4.5` and `_8` names predating the two-decimal rule. Report anything unexpected there rather than filtering it out.

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

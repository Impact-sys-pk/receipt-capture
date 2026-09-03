# AUTOMATIC task: confirm the database move, fix one hardcoded path, and commit

**Written 2026-08-01 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file. **Report once at the end.**

**Do not run this until Paul confirms he has moved the database.** Task 1 checks that he has, and stops if he has not.

**Do not start the pipeline.** Stage 6 is Paul's.

---

## Task 1. Confirm the move, before anything else

Paul has moved three files out of `C:\LastingImpact\receipt_capture\data\` into `C:\Intellibills\db\`. **Verify it rather than assume it.**

    dir C:\Intellibills\db
    dir C:\LastingImpact\receipt_capture\data

**Expect:** `receipts.db`, `receipts.db-wal` and `receipts.db-shm` in `C:\Intellibills\db\`, and none of the three left behind in the repository's `data\`.

Then, **read-only**, against `config.DB_PATH` rather than a path you type:

    python -c "import config, sqlite3; c=sqlite3.connect(f'file:{config.DB_PATH}?mode=ro', uri=True); print(config.DB_PATH); print('vendors', c.execute('select client_id, count(*) from categorisations_client_vendors group by client_id').fetchall()); print('receipts', c.execute('select count(*) from receipts').fetchone()[0])"

**Expect exactly:** `[('Client_006', 100)]` and `0`.

**Stop and report if:**

- Any of the three files is still in the repository's `data\`. A partial move of a WAL database is the corruption route amendment 72 exists to prevent.
- `receipts.db` in `C:\Intellibills\db\` is small, a few kilobytes, or the vendor count is 0. **That is an empty stub created by something opening `Repository()` after `config.DB_PATH` moved and before the file did.** Do not delete it and do not proceed; report the byte size. The real file is 233,472 bytes and is the only copy of the re-keyed mappings.

---

## Task 2. `check_test41.py:17`

    DB = Path("data/receipts.db")

**A hardcoded path that bypasses `config.DB_PATH` entirely.** It was missed when stage 5 moved the constants: the brief named only `:80` in that file. The script opens the database read-only, so it now errors rather than creating a stray one, but it points at a location that no longer holds anything.

**Change it to read `config.DB_PATH`.** The file already imports `config`, at `:80` where it reads `config.RESOLUTIONS_DIR`; check that the import is at module level and move it if it is not.

**Then run it:** `python check_test41.py`. It must report an empty receipts list and no resolution events, reading the database at `C:\Intellibills\db\receipts.db` and the notes folder at `...\Intellibills\Resolutions\`.

**While you are in that file, look for any other hardcoded path and report what you find rather than changing it.** One hardcoded path in a file usually means two.

---

## Task 3. Commit

Two commits, staged by name. **Never `git add .`**; `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` must still show `??`.

### Commit 1

    git add 2026-07-25_CONSOLE_DESIGN.md PROMPT_claude_code_stage5_pipeline_paths.md PROMPT_claude_code_2026-08-01_after_db_move.md

**Three paths.** The third is this prompt.

    docs: amendment 83, and the stage 5 brief as sent

    Amendment 83 records the substantive finding of stage 5's pipeline half:
    nine path constants were mutated to wrong values and eight left the whole
    suite green. Only LOGS_DIR was caught, by a test written for another
    purpose.

    The cause is not carelessness. Every test redirects those constants into a
    temp directory before doing anything, which is correct isolation and is
    exactly why the suite could say nothing about their real values. So a
    263-test suite passing said nothing about the deliverable of that stage,
    which was the values themselves.

    tests/test_path_layout.py is kept for that reason, and a second finding
    came free: adding FILES_DIR and REVIEW_ROOT to the isolation guard
    exposed three modules that would have written into the practice's live
    document store or its live review queue.

    The brief is committed as sent, having been edited after commit 165a2b7
    named its file list, which is why that commit could not include it.

### Commit 2

    git add check_test41.py

    fix(scripts): check_test41.py reads config.DB_PATH instead of a literal

    Line 17 hardcoded Path("data/receipts.db") and survived stage 5 because
    the brief named only line 80 in that file. Read-only, so it errored
    rather than creating a stray database, but it pointed at a location that
    holds nothing after the move to C:\Intellibills\db\.

Then push to `feat/console-phase0`. **Push the branch**, `--dry-run` first, fast-forward only, **never `--force`**.

---

## Verify

- `git --no-optional-locks status --short` shows one line, `?? RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md`.
- Two commits on top of `b8963d1`, pushed.
- **`python -m pytest -q` still passes at 276 plus 123 subtests.** `check_test41.py` is not under test, so the count should not move. If it does, say why.
- No `.py` file other than `check_test41.py` appears in either commit.

---

## Stop and ask about

1. **A database file in `C:\Intellibills\db\` that is not 233,472 bytes**, or a vendor count other than 100.
2. Any write to the database. Task 1's query is read-only by construction, using `mode=ro`.
3. Any file other than the three named in task 3.
4. Starting the pipeline. Not in this task and not yours.
5. A point where this brief and the design document disagree. Report it, do not choose.

**Flag, do not fix.**

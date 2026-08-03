# AUTOMATIC task: close the `firm_id` defect, and make the constant load-bearing

**Written 2026-08-03 by the consultant session, for Claude Code. Paste this whole file in. This follows `PROMPT_claude_code_2026-08-03_firm_id_and_doc_corrections.md`, which you completed as `26e3e0b` and `e2c034c`.**

Runs under `AUTOMATIC Task Mode` in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

**Your work on the last task was correct and complete against its brief. The brief was wrong.** Details below, and it is worth reading before the tasks because it changes what "done" means here.

---

## Why there is a second pass

**Amendment 89 named four call sites. There are eleven statements of the fallback `firm_id`, and the one that is live is one the last brief did not touch.**

That is the consultant session's error, not yours. Amendment 89 says "verified in full", and what was verified was the four sites amendment 87 named. **The claims that were made were checked; the claim that the list was complete was not.** One `git grep -n "INTELLITAX" -- '*.py'` would have found the rest before the brief was written. Amendment 93 records it.

**The live path, and it is the one that has actually been in the failure state.**

`worker/intake/folder_reader.py:88` sets `firm_id = "INTELLITAX"` when a folder's client code is not in `config.CLIENTS_BY_CODE`. That value reaches `IntakeRecord.firm_id` at `folder_reader.py:117`, and from there **both** of:

- `repo.save_receipt(firm_id=intake.firm_id)` at `app.py:921`, so the receipts row carries `INTELLITAX`
- `_log_receipt(..., firm_id=intake.firm_id)` at `app.py:935`, so `receipt_events_INTELLITAX.ndjson` is recreated

**The precondition is not hypothetical.** Amendment 84 records `Intellibills\Receipt Inbox\` holding `TEST\` and `TEST2\` after both clients were retired. A folder whose code is in no row of `clients.csv` existed on this system on 2026-08-01.

**Why the two email paths were never at risk, which is worth knowing before you read the code:** they are protected by a guard, not by the constant. `app.py:695-699` and `app.py:1071-1076` both test `client_id == "UNKNOWN"` and `continue` before any save, so `resolve_client_info()`'s two `INTELLITAX` returns are discarded rather than corrected.

---

## Task 1. Confirm the starting state

    git --no-optional-locks status --short

**Expect exactly one modified and one untracked, and nothing else:**

     M 2026-07-25_CONSOLE_DESIGN.md
    ?? PROMPT_claude_code_2026-08-03_close_firm_id.md

The modified file is amendment 93 plus two line-number corrections, written by the consultant session. The untracked one is this brief. **Stop and report** on anything else, in particular any `.py` file.

**If `.git\index.lock` exists**, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`.

---

## Task 2. The live fix

**`C:\LastingImpact\receipt_capture\worker\intake\folder_reader.py`, line 88.**

    firm_id = "INTELLITAX"

becomes

    firm_id = config.DEFAULT_FIRM_ID

`config` is already imported at `folder_reader.py:7`, so nothing else changes. **Leave `client_id = "UNKNOWN"` on the line above alone**: `UNKNOWN` is the agreed unresolved client and it is not in dispute.

---

## Task 3. Delete the dead function

**`C:\LastingImpact\receipt_capture\worker\database\repository.py`, lines 75 to 83**, the whole of `resolve_client_by_code()` including its docstring, plus the blank line that separates it from what follows.

**Nothing calls it.** `git grep -n "resolve_client_by_code"` returns its own definition and one mention in the design document's amendment 93. Confirm that yourself before deleting rather than taking it from me.

**Do not confuse it with `resolve_client_info()` at `:57` or `resolve_client_id()` at `:71`, both of which are live.** `resolve_client_info` is called from `app.py:696`, `:835` and `:1072`, and `resolve_client_id` from `app.py:695` and `:1071`.

**If it turns out something does call it, stop and report.** Do not adapt it.

---

## Task 4. Make the constant load-bearing

Mutation 3 of your last report is the reason: reverting `config.py:120` to the literal `"FIRM001"` left all 281 tests green, so the constant was decorative at the only site that read it. Amendment 83's lesson applies directly, that a suite which isolates a value and never asserts it is silent about the value.

**Add to `tests/test_default_firm_id.py`**, so the file stays the one place this is policed.

**Test A, the behavioural one.** Set `config.DEFAULT_FIRM_ID` to a sentinel that appears nowhere else, point `config.CLIENTS_CSV` at a temporary CSV **whose header has no `firm_id` column at all**, call `config.load_clients()`, and assert the returned client data carries the sentinel. Restore both afterwards in a `finally` or via `addCleanup`.

Three things about it, because each is a way this test could pass while proving nothing:

- **The column must be absent, not blank.** `row.get("firm_id", DEFAULT_FIRM_ID)` returns `''` for a present-but-empty column. A blank cell would make the test assert `''` and pass for the wrong reason.
- **`load_clients()` returns rather than assigns**, so calling it does not mutate `config.CLIENTS`. Confirm that by reading the function rather than assuming it, and say which you did.
- **The sentinel must not be `FIRM001` or `INTELLITAX`.** If it is either, the test passes whether the constant is read or a literal is.

**Test B, for task 3.** Assert `resolve_client_by_code` appears zero times in `worker/database/repository.py`, read as text, in the same style as your existing `test_app_py_passes_no_firm_id_literal`. **And apply your own `test_the_count_is_looking_at_the_right_file` idea to it**, which was the best thing you added last time: a text count that reads the wrong file passes silently for ever.

### Red before green, and then one mutation

**Quote the failing output of test A before task 2 or task 4's change**, and say what it fails with. Then, after everything is green, **re-run mutation 3**: revert `config.py:120` to the literal `"FIRM001"` with the constant left in place, run the suite, and **confirm test A now fails.** That is the whole point of this task and it is the only thing that proves it worked.

**Also run one new mutation:** `folder_reader.py:88` back to the literal `"INTELLITAX"`. Report which tests catch it. **If nothing catches it, say so and do not add a test to cover it without asking** — whether the folder-intake path needs its own assertion is a design question and section 15 is the consultant session's.

---

## Task 5. One commit

    git add worker/intake/folder_reader.py worker/database/repository.py tests/test_default_firm_id.py 2026-07-25_CONSOLE_DESIGN.md PROMPT_claude_code_2026-08-03_close_firm_id.md

    fix(intake): the folder-intake fallback firm_id, and the constant made load-bearing

    Amendment 93, closing what amendment 89 left open. Amendment 89 named
    four call sites in app.py; there are eleven statements of the fallback
    firm_id and the live one was not among them.

    worker/intake/folder_reader.py:88 set firm_id = "INTELLITAX" when a
    folder's client code was absent from clients.csv, and that value reached
    both repo.save_receipt() at app.py:921 and _log_receipt() at app.py:935
    by way of IntakeRecord.firm_id. So a file in an unrecognised
    Intellibills\Receipt Inbox\{CODE}\ folder wrote INTELLITAX to a receipts
    row and recreated receipt_events_INTELLITAX.ndjson. Amendment 84 records
    that condition existing on 2026-08-01, so it was not hypothetical.

    resolve_client_by_code() at repository.py:75-83 is deleted. Nothing
    called it, and it held two more of the eleven.

    The constant was decorative: mutation 3 of the previous task reverted
    config.py:120 to a literal and left all 281 tests green. One behavioural
    test now asserts load_clients() honours a changed DEFAULT_FIRM_ID, using
    a CSV with no firm_id column, because a blank column returns '' rather
    than the default and would pass for the wrong reason.

    The two email paths were never at risk and are unchanged: app.py:695-699
    and :1071-1076 guard on client_id == "UNKNOWN" and continue before any
    save, so resolve_client_info()'s INTELLITAX returns are discarded.

    Files: worker/intake/folder_reader.py, worker/database/repository.py,
    tests/test_default_firm_id.py, 2026-07-25_CONSOLE_DESIGN.md

**Adjust the file list to what you actually staged.**

**Then push.** Branch `feat/console-phase0`. `git push --dry-run` first, fast-forward only, **never `--force`**.

---

## Verify, and quote the output

1. `git --no-optional-locks status --porcelain` returns nothing. Quote it.
2. One commit on top of `e2c034c`, pushed fast-forward.
3. **The full suite passes.** Quote the count against 281 plus 127 subtests and account for the delta.
4. **Amendment numbering is contiguous from 1 to 93.** Programmatically, not by eye.
5. `git grep -n "INTELLITAX" -- '*.py'` and **quote the whole result, not a count.** Expect hits only in: the comment at `config.py:103`, `docs/specs/categorisation_engine.py:606`, `worker/database/repository.py` at the two `resolve_client_info()` returns and `save_receipt()`'s parameter default, `worker/database/schema.py:78`, `tests/test_default_firm_id.py`'s own assertion strings, and the test fixtures. **No hit in `app.py` and none in `worker/intake/folder_reader.py`.** If the shape differs from that, report the difference rather than reconciling it.
6. **Read the commit message back against `git show --stat` and `git diff --cached` and confirm every claim in it is in the diff.** Amendment 92's rule. Its first use caught nothing; this is the second.

---

## Stop and ask about

1. Anything on the Destructive Git Operations list.
2. Anything outside `C:\LastingImpact\receipt_capture`.
3. Any `INSERT`, `UPDATE` or `DELETE` against `receipts.db`.
4. Starting the pipeline.
5. **The four remaining `INTELLITAX` statements, which are deliberately left.** `repository.py:60` and `:69` are unreachable behind the guard; `repository.py:219` is a parameter default all three callers override; `schema.py:78` is the `receipts.firm_id` column default and **reaches nothing that exists**, because `CREATE TABLE IF NOT EXISTS` leaves the live table alone. **Do not touch any of them.** `CLAUDE.md:604` describes `schema.py:78` accurately and changes after it, not before.
6. **The blank-column case you flagged.** Left unfixed on purpose, per amendment 93: the validation belongs with 8.6's **Register this client** action, which is the only thing that will ever write `clients.csv`. **Do not add a guard for it.**
7. Any behaviour change beyond tasks 2 and 3.

**Flag, do not fix.**

---

## Report to a file

**Write your report to `C:\LastingImpact\receipt_capture\2026-08-03_REPORT_claude_code_close_firm_id.md` and commit it with the commit above.**

Include test A's failing output before the change, the mutation 3 re-run result, the `folder_reader.py:88` mutation result, the full `git grep` output from verification step 5, the suite count, and anything flagged rather than fixed.

**One thing worth saying in it if it is true:** whether reading `worker/intake/folder_reader.py` in full turned up anything else in that file's client resolution that the two briefs have not named. It is the intake path with the least test coverage and neither brief has asked anyone to read it end to end.

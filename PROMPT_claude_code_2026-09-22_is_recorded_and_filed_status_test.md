# AUTOMATIC task. Claude Code brief, 2026-09-22: a status test on `is_recorded_and_filed()`

Written by the consultant session, 2026-09-22, 16:10 BST, read off the clock in this reply. Paul's
instruction of 2026-09-22, on your own report
`2026-09-22_REPORT_claude_code_filed_path_on_discarded_rows.md`.

**This runs under `CLAUDE.md`'s AUTOMATIC Task Mode.** Its stop list is unchanged and outranks this
brief.

**Report to `2026-09-22_REPORT_claude_code_is_recorded_and_filed_status_test.md` in the repository
root.**

---

## Three rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** You report; the consultant session marks
the step. You do not mark your own step paragraphs built.

**2. `2026-07-25_CONSOLE_DESIGN.md` is not yours either.**

**3. Re-enumerate rather than repeat.** Your own report names the callers of the function below. Walk
them again from the syntax tree in this task and state what you find. Where it disagrees with the
earlier report, say so and work from this one.

---

## What to build

`is_recorded_and_filed()` in `worker\database\repository.py` answers on `filed_path` alone, with no
test of `status`. **Make its answer independent of whether `filed_path` was ever cleared.**

Its callers ask whether a document has already been dealt with, so that a resend is a duplicate. A
discarded receipt has not been dealt with. Commit `a96627a` decided that in terms, and
`clear_receipt_filed_path()`'s docstring states it: the clearing is what lets the identical document
be sent again.

**The shape you proposed is a status test in the query. Build that unless your own enumeration finds
a reason not to**, in which case stop and report rather than choosing a different shape.

## What it has to do

- A receipt whose status is `discarded` does not count as filed, whatever `filed_path` holds.
- A receipt whose status is `ok` with a `filed_path` still counts as filed, exactly as today.
- **A `needs_review` receipt still does not count as filed.** Your report records that
  `_move_inbox_pair_to_processed()` depends on that, so a file an operator puts back by hand is
  deliberately reprocessed. Establish that this change leaves that behaviour where it is.
- `SettledMeansPublishedTest` still passes, and the distinction it holds between settled and filed is
  undisturbed.
- Every caller you enumerate gives the same answer as today for every status other than `discarded`.

## Red before green

- Write the failing test first, against a `discarded` row carrying a `filed_path`.
- Then prove the suite discriminates: put the old query back and show which test goes red. **If
  nothing goes red, say so** and propose the check that would.

## What not to do

- **Do not touch the live row.** No `UPDATE`, no correction by hand. It is the only instance of the
  fault and its mechanism is not established. Paul's decision, 2026-09-22.
- **No writes to `receipts.db` at all.** Read-only, `mode=ro`, temp databases in tests are fine.
- **Do not `import config` on Windows.** Read the constant out of the file.
- Nothing is deleted anywhere, and nothing is written outside `C:\LastingImpact\receipt_capture`.
- **Do not fix anything else.** Five things are flagged in your last report and none of them is in
  this brief. Flag, do not fix.
- No real OpenAI call.

## How to report

- The callers you enumerated in this task, and how.
- The test that went red, then green.
- The discrimination result.
- Suite totals before and after.
- Whether `_move_inbox_pair_to_processed()`'s behaviour is unchanged, and how you established it.
- Propose the commit and wait for Paul's yes.
- Disclose your own mistakes, including ones you caught and corrected.

# Claude Code brief, 2026-09-22: `filed_path` on discarded rows

Written by the consultant session, 2026-09-22, 15:44 BST, read off the clock in this reply. Paul's
instruction of 2026-09-22, on a defect found while answering his question about deleting the receipt
files under `Clients\`. He does not want it left open.

**Report to `2026-09-22_REPORT_claude_code_filed_path_on_discarded_rows.md` in the repository root.**

**This is a read-and-report task. No production code changes.** If you find the fix while
establishing the facts, describe it in the report and propose it. Do not build it.

---

## Three rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** You report; the consultant session marks
the step. You do not mark your own step paragraphs built.

**2. `2026-07-25_CONSOLE_DESIGN.md` is not yours either.**

**3. Every count below is deliberately absent, and that is not an oversight.** The consultant session
has the numbers from a query Paul ran. They are withheld so that your report is a second
enumeration rather than a repeat of the first. Enumerate each set yourself, state your own count, and
say how you queried. Where your answer disagrees with the shape described here, say so and work from
yours.

---

## What is wrong

**The live database holds at least one row whose `status` is `discarded` and whose `filed_path` is
not NULL.**

`_discard_receipt()` in `worker\resolution\service.py` says in its own docstring that this cannot be
the case: "**`filed_path` is cleared on every discard**, deleted copy or not. A discarded receipt is
not filed, whatever became of the file, and the column would otherwise name something that may not
be there."

So the data and the stated rule disagree. One of them is wrong and the report says which.

**Established on Paul's machine on 2026-09-22** by a read-only query he ran and pasted, against
`C:\Intellibills\db\receipts.db`. The consultant session has no shell on that machine and cannot
query it.

**A second symptom in the same column, found in the same output.** At least one row whose `status` is
`ok` carries a `filed_path` naming a file that is not on disk, while a file with the same stem and a
different extension IS on disk in that folder. Treat it as part of the same enumeration.

## What to establish

1. **Every row where `status = 'discarded'` and `filed_path IS NOT NULL`.** Count, and the rows.
   Also the reverse shape for completeness: any status other than `ok` carrying a `filed_path`.

2. **Every code path that sets a receipt's status to `discarded`.** For each one, whether it clears
   `filed_path`, and if so where. **Enumerate from the syntax tree, not a text search**, and exclude
   `.history\` from any repository-wide search: it is VS Code's local history and it holds a dated
   copy of every file edited, so a text search returns names that no longer exist live.

3. **When the clearing was introduced**, from the git history, and whether the offending rows predate
   it. If they do, the rule is sound and the data is historical. If they do not, the rule has a hole.

4. **What a `discarded` row carrying a `filed_path` can cause.** Enumerate the readers of that column
   and say, for each, what it does when the status is `discarded`: any client-copy write, any
   client-copy removal, any publish, any duplicate or "settled" check, any retry queue. **The
   consultant session read the query that selects `status = 'ok' AND filed_path IS NULL` and believes
   that one is unaffected. Check it rather than accept it.**

5. **Every `filed_path` value against the file on disk.** Which resolve to a file, which do not, and
   which files in `Clients\{client_folder_name}\IntelliBooks\Receipts\{tax year}\` have no row
   pointing at them. Report all three sets in full, not counts alone.

## How to read the database

- **Read-only, and say in the report that you did.** Open it with the `mode=ro` URI form. The
  pipeline polls every five minutes and this must not take a write lock or disturb it.
- **Do not `import config` to find the path.** On Windows an import outside pytest reads `.env` and
  runs the `mkdir` block against the live roots, which has created unwanted folders twice on this
  project. Read the constant out of the file, or use the literal path above.

## What not to do

- **No production code changes**, in the worker or anywhere else.
- **No writes to `receipts.db`**, and no `DELETE`, `UPDATE` or `VACUUM` of any kind.
- **Nothing is deleted anywhere.** Paul is clearing nothing before the pilot, his decision of
  2026-09-22, and no file under `Clients\` is yours to touch.
- **No real OpenAI call.**
- No file writes outside `C:\LastingImpact\receipt_capture`.
- Check `git status` before and after any run that edits files.

## How to report

- Your own count for each of the five sets above, and the query or the walk that produced it.
- Which of the rule and the data is wrong, and on what evidence.
- Whether the rows predate the clearing, with the commit.
- The obvious fix, named, with the reasoning. If the obvious fix is to remove something, say that
  first.
- Anything you found that this brief did not ask about: flag it, do not repair it.
- Disclose your own mistakes, including ones you caught and corrected.

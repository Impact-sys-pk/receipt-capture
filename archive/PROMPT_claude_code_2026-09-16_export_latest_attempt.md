# Claude Code brief, 2026-09-16: step 10at, the export reads one latest attempt

Written by the consultant session, 2026-09-16, 13:50 BST. Step 10at of
`2026-07-25_BUILD_STATUS.md`, amendment 413 of `2026-07-25_CONSOLE_DESIGN.md`, Paul's decision of
2026-09-13 closing outstanding item 126.

**Report to `2026-09-16_REPORT_claude_code_export_latest_attempt.md` in the repository root.**

**One commit. Build it, propose the commit, and wait for a yes.**

---

## Two rules about this brief, and the first one is new

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit. Paul's instruction, 2026-09-16.** Do not
mark this step built. Do not touch that file at all. You report; the consultant session verifies the
work against the code on Paul's machine and marks the step. A session marking its own homework
removes the second mind that was the reason for asking.

**2. This brief names two files and one function because it has read them.** `export_bookkeeping.py`
was read whole, all 82 lines, on 2026-09-16. Everything else here is a description of what has to be
true, and you find the right place. If a name in this brief does not match what you find, that is the
brief's fault and it is a finding, not something to work around. One has already happened this
morning: step 10w names a function that no longer exists.

---

## What is decided, and it is not reopened here

From amendment 413, quoted rather than paraphrased:

> `export_bookkeeping.py` groups by receipt but leaves several columns, supplier, dates and amounts,
> unaggregated, so SQLite may take them from any one of several extraction attempts; and it uses
> `MAX()` on `validation_status` and `validation_notes` to approximate the latest attempt's outcome,
> which sorts alphabetically rather than by time. **Paul's decision: select each receipt's single
> latest extraction attempt by `extracted_at`, and read supplier, dates, amounts and status from that
> one row.**

## What the file does today

`export_bookkeeping.py` lines 40 to 59, one statement:

```sql
SELECT r.receipt_id, r.firm_id, r.client_id,
       e.supplier_name, e.invoice_date, e.net_amount, e.vat_amount, e.gross_amount, e.currency,
       r.status,
       MIN(e.extracted_at)        as first_extracted_at,
       MAX(e.validation_status)   as latest_validation_status,
       MAX(e.validation_notes)    as latest_review_reason
FROM receipts r
LEFT JOIN extractions e ON r.receipt_id = e.receipt_id
GROUP BY r.receipt_id
ORDER BY r.created_at DESC
```

**Two separate defects, and they need separating because only one of them is about sorting.**

**Defect one, the six bare columns.** `supplier_name`, `invoice_date`, `net_amount`, `vat_amount`,
`gross_amount` and `currency` are neither grouped nor aggregated. SQLite's bare-column rule takes
such a value from the row that matched a `MIN()` or `MAX()` **only when the query contains exactly
one such aggregate**. This query contains three. **So which row those six values come from is
unspecified, and a receipt can export a supplier from one attempt and a gross from another.**
Establish this against the SQLite documentation rather than taking it from this brief, and say in the
report what you found, because it decides whether the current behaviour is merely arbitrary or
genuinely mixed.

**Defect two, the text sort.** `MAX()` on `validation_status` and on `validation_notes` orders text,
not time. **Read the permitted values of `extractions.validation_status` out of
`worker/database/schema.py` rather than assuming them**, then state in the report what alphabetical
ordering does to that set, and name one concrete pair where the latest attempt's status loses to an
earlier attempt's. Amendment 413 asserts that a receipt whose latest attempt failed can export as
`ok`. **Confirm or refute that against the real value set. Do not repeat it because it is written
here.**

## What to build

One receipt, one row, and the row's non-receipt columns come from that receipt's single most recent
extraction attempt by `extracted_at`.

Three things that must survive the change:

1. **A receipt with no extraction row at all still appears**, with the extraction columns empty. That
   is what the `LEFT JOIN` gives today and it must not become an inner join by accident. Hold it with
   a test that has such a receipt in the fixture.
2. **`ORDER BY r.created_at DESC` is unchanged.** The row order of the CSV is not part of this.
3. **`OUTPUT_DIR = config.EXPORTS_DIR` is unchanged.** Step 10r moved it four days ago and it is
   settled. The docstring above it carries the reasoning and stays.

**Ties.** Two attempts sharing an `extracted_at` to the stored precision is possible. Pick a
deterministic tiebreak, say in the report which you picked and why, and make it a test case rather
than a remark. An export that reorders itself between two runs over unchanged data is worse than one
that is arbitrarily but stably wrong.

## One decision taken here, and it is the consultant session's, not yours

**`first_extracted_at` does not change. It stays `MIN(e.extracted_at)` across every attempt.**

The step and amendment 413 name supplier, dates, amounts and status. They do not name this column,
and the column is called *first* and means *first*: it is when the pipeline first read this document.
The file's own comment records that this CSV is a handoff format whose headers are the database's own
column names and that nothing in this repository reads it back. **Silently changing what a column
means while leaving its name alone is the fault that comment exists to prevent.**

**The consequence for your query, and it is the reason this is called out rather than left implicit:
you now need two things from `extractions` at once** — an aggregate over all attempts for
`first_extracted_at`, and one picked row for everything else. A single `GROUP BY` will not give you
both. Say in the report which shape you used.

If you think this decision is wrong, **flag it and build it as written anyway.** Paul decides, not
either session.

## Evidence

The standard in `CLAUDE.md` applies in full and is not restated here, except for the three parts this
change makes specific:

- **Red before green**, with the failing output quoted. A test that fails on today's query and passes
  on the new one, over a fixture holding a receipt with several attempts whose latest is not the
  alphabetically highest.
- **Mutation.** Anchor on something unique, assert the anchor matches exactly once, print the unified
  diff beside the result. At minimum: break the tiebreak, and break the `LEFT JOIN` back to an inner
  join, and show which tests catch each and that no others do.
- **The suite runs again after the commit** if this change adds a file, because two source guards
  sweep the git-tracked set and a new file is invisible to them until it is committed.

## What to report

Everything the standard asks, plus these four by name:

1. What SQLite's documentation actually says about bare columns with three aggregates, and whether
   the current behaviour is arbitrary-but-consistent or genuinely mixed.
2. The real value set of `extractions.validation_status`, and whether amendment 413's `ok` example
   holds against it.
3. Your tiebreak and why.
4. The query shape you used to get an aggregate and a picked row together.

**Flag, do not fix.** `capture_report.py` sits beside this script and reads the same two tables. If it
carries the same pattern, say so and stop. It is not in this brief and step 10ai already has that
file open.

# Brief: `vendor_key` and `vendor_code` mean the wrong things, in five places

**Paul's instruction, 2026-09-06.** Read this whole file before starting. This is not a feature. It
is a naming correction that has already produced one `TypeError` and one wrong flag, and it will
produce more while it stands.

---

## The word that is wrong

**In this project, "code" means a four-digit account code. Everywhere.** `7310`, `7391`, `8250`. The
master's codes, the chart's codes, `nominal_code`, `suggested_code`, `correction_code`,
`category_code`.

**`vendor_code` is the one place it does not.** It holds `imo`, a lower-case word produced by
`normalise_description()` and `extract_vendor_key()`. That is a **key**, and the code already has a
name for it: `vendor_key`.

**And in the learned tables the two names are swapped**, so `vendor_key` holds a row id and
`vendor_code` holds the key.

## What is where, and how each line was established

**Read from the live `C:\Intellibills\db\receipts.db` on 2026-09-06 with `PRAGMA table_info`, and
from the source of `worker\categorisation\engine.py` and `worker\resolution\service.py`.**

| Where | Column or field | Holds | How established |
|---|---|---|---|
| `categorisations_client_vendors` | `vendor_key` | **a row UUID** | Read the one row. `523efdfa-6a2f-4f33-993b-f8d9b530fa9d` |
| | `vendor_code` | the normalised key, `imo` | Same row |
| `categorisations_firm_vendors` | `vendor_key`, `vendor_code` | same two, same way round | Column list. **0 rows, so this is from the schema and from `upsert_firm_vendor()`, not from data** |
| `categorisations_client_rules` | `vendor_code` | the normalised key | Column list. **0 rows** |
| `categorisations` | `vendor_key` | **a matched mapping's UUID, not the key** | **From the code, not the data.** `engine.py:296` sets `vendor_key=client_vendor["vendor_key"]`, and that column is the UUID. **All 11 rows are `unmatched` and hold `None`, so the data cannot show it. Verify this before acting on it** |
| `CategorisationResult` | `vendor_code` | the normalised key, always set | `engine.py:283, 296, 309, 328, 347, 362, 372` |
| | `vendor_key` | the matched mapping's UUID, set only on a match | `engine.py:296, 309, 328, 347` |

**One correction, disclosed.** The consultant session told Paul that `categorisations.vendor_key` was
correctly named. **That was inferred from the column name and not read.** The row above is what the
code says, and it is the first thing to check.

## Task 1. Establish the facts before changing anything

**Do not start from this brief's table. Start from the repository.**

1. `PRAGMA table_info` on all four tables, printed whole
2. Every read and write of `vendor_key` and `vendor_code`, **enumerated across every `.py` file in the
   repository**, printed whole. Not a sample and not a chosen file list
3. **State what `categorisations.vendor_key` is written from**, naming the line

**If any of this brief's table is wrong, say so and stop.** A rename built on a wrong premise is
worse than the names.

## Task 2. The names

**The target, and change it if Task 1 says it is wrong:**

- The normalised key is **`vendor_key`** everywhere. It is never called `vendor_code`
- A row id in a learned table is **`mapping_id`**, never `vendor_key`
- **`vendor_code` stops existing.** If any place genuinely needs a four-digit code, it already has
  `nominal_code` or `suggested_code`

## Task 3. The migration, and Paul has ruled on the cost

**The three learned tables hold one row between them**, `categorisations_client_vendors`, made on
2026-09-06. **Paul's decision: drop and recreate them.** He can remake that row in three minutes with
the review fixture. **No migration script, no copy to test against.**

**`categorisations` is different and must not be dropped.** Its 11 rows carry the correction history,
including the one that proves 10j.11 works. Its `vendor_key` column is `None` on every row today, so
a rename there moves no data. **Say what you would do before you do it.**

**`receipts`, `extractions` and `resolution_events` are not touched by this brief.**

## Task 4. The dead function, item 54

`learn_from_correction()` at `worker\categorisation\engine.py:527` **passes `vendor_key=` to
`upsert_client_vendor()`, which takes `vendor_code`, and would raise `TypeError` if reached.** It is
uncalled. It is the only writer the firm table has anywhere.

**It cannot be left as it is once the parameter names change, because it will still be wrong and it
will be wrong in a new way.** Three options and **the choice is Paul's, so propose and do not
choose**:

1. Delete it. Item 166 will build the firm write deliberately when it is decided
2. Fix the call so it works but stays uncalled
3. Fix it and leave a test that asserts it has no caller

**Do not give it a caller.** Item 166 is deferred and the 10j.11 test that patches
`upsert_firm_vendor()` and asserts zero calls must still pass.

## Task 5. The two flags from yesterday, now closable

- **`resolve_receipt():773` reads `getattr(categorisation, "vendor_code", None)`.** After the rename
  it reads `vendor_key`. **Check that the `getattr` default is still right**: `None` there means
  nothing is learned and a warning is logged, which is the behaviour to keep
- **`_apply_filed_note()`'s learning branch** reads the same attribute. Both must move together

---

## Verify, and report what you ran

**Write the report to `2026-09-06_REPORT_claude_code_vendor_key_naming.md` in the repository root.**

1. `.\.venv\Scripts\python.exe -m pytest -q` before and after. It was **513 passed, 328 subtests,
   zero skips**
2. **The enumeration from Task 1, printed whole**, before and after
3. **`PRAGMA table_info` on all four tables after the change**
4. **A test that the string `vendor_code` does not appear in `worker\` at all**, or, if it must
   survive somewhere, that names every survivor and says why
5. **Re-run the 10j.11 proof against a temporary database**: a filed note with the tick writes one
   row to `categorisations_client_vendors` and zero to `categorisations_firm_vendors`
6. Mutation: break the rename in one place and show which test goes red

## Do not

- Do not drop `categorisations`, `receipts`, `extractions` or `resolution_events`
- Do not give `learn_from_correction()` a caller
- Do not write the firm table. Item 166 is deferred
- Do not rename anything in `IntelliBooks-Desktop-v3.html`. A different session owns it, and the
  note contract at 12.2 does not use either word
- Do not touch `IntelliCharts\`

## Commit

Commit the working tree first if anything is uncommitted, then one commit for this brief's work. The
message says which tables were recreated, how many rows were lost, and what you did with
`learn_from_correction()`.

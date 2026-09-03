# Task: drop the 100 legacy vendor mappings from receipts.db

**Written 2026-08-18 by the consultant session, for Claude Code. Paste this whole file in.**

**This is a write to `receipts.db`, which your standing stop-and-ask list forbids. This brief authorises it once, for the rows named below and nothing else.** Everything else on that list is unchanged and still outranks this file.

---

## Why

`categorisations_client_vendors` holds 100 rows. **Every `nominal_code` is three characters**, so every one is legacy: the master chart is 122 accounts on four-digit codes and a three-digit code is now provably stale. Paul's decision is to export them and drop them.

**The export is done and is the only surviving record.** Two files, written 2026-08-18 and verified by reading them back:

- `Intellibills\Exports\2026-08-18_EXPORT_categorisations_client_vendors.csv`, all 9 columns and all 100 rows, 19,014 bytes
- `Intellibills\Exports\2026-08-18_EXPORT_legacy_codes_summary.csv`, the 23 distinct legacy codes with their account names and mapping counts, 673 bytes

Both are in OneDrive and **outside your permitted scope. Do not read them, write them or reference them by path in anything you produce.** They are named here so you know the data is preserved before you delete it.

## What I measured, from a read-only copy of the database

| | |
|---|---|
| Rows in `categorisations_client_vendors` | **100** |
| Distinct `client_id` | **one**, `Client_006` |
| Distinct `nominal_code` values | **23**, every one 3 characters |
| Other tables | `categorisations` 1, `categorisations_client_rules` 0, `categorisations_firm_vendors` 0, `receipts` 1, `extractions` 1, `processed_attachments` 1, `statements` 0, `resolution_events` 0, `email_alerts` 0, `email_delta` 0 |
| Table definition | no foreign keys, primary key `vendor_key`, unique on `(client_id, vendor_code, vendor_name)` |
| Database file | `C:\Intellibills\db\receipts.db`, 233,472 bytes, unchanged since 2026-08-02 |

## Task 1. Confirm it is safe to write

**a. The pipeline must not be running.** `Intellibills\pipeline.lock` exists in OneDrive and was last written 2026-08-17. Its existence does not prove a live process. Confirm no pipeline process is running before you touch the database. **If one is, stop and report; do not kill it.**

**b. Confirm the counts above from the live database**, read-only. If `categorisations_client_vendors` is not exactly 100 rows, or any `nominal_code` is not 3 characters, **stop**: the database has changed since I read it and the export no longer matches what you would delete.

**c. Enumerate what reads the table, and print each hit whole.** Search the whole repository for `categorisations_client_vendors`. **This is the part I could not do and it is the real risk.** I know `seed_client_vendors.py`, `import_vendor_csv.py`, `regenerate_vendor_codes.py` and `check_missing_categorisation.py` exist by name and I have not read any of them.

**Stop and report, do not proceed, if any of these is true:**

- A test asserts a row count, or a specific `vendor_key`, or a three-digit code
- Any code path treats an empty table differently from a populated one in a way that changes behaviour rather than just returning no match
- Anything writes three-digit codes back into the table, because dropping the rows would then be undone on the next run

## Task 2. Back up first

Take a consistent copy before deleting. **The database runs in WAL mode**, so it has `-wal` and `-shm` companions and a plain file copy of the main file alone is not a consistent backup. Use SQLite's own backup mechanism, or the pipeline's `repo.backup_db()` if that is what it does, and **read the copy back and confirm it holds 100 rows** before you delete anything.

Say in your report where the backup went and how you proved it was consistent.

## Task 3. Delete the rows, not the table

```sql
DELETE FROM categorisations_client_vendors;
```

**The table stays.** Paul's decision is to drop the rows. Do not `DROP TABLE`, do not alter the schema, and do not touch any other table.

## Verify, and quote the output

1. `select count(*) from categorisations_client_vendors` returns **0**.
2. The row counts of every other table are unchanged from the table above. Print them all, not just the ones you expect to have moved.
3. `select sql from sqlite_master where name='categorisations_client_vendors'` is byte-identical to before. Quote both.
4. The backup still holds 100 rows, read after the delete, not before.
5. `git --no-optional-locks status --porcelain`. **The database is gitignored, so expect this brief and your report and nothing else.** Anything else, stop and report.

## Then commit the documentation

This brief and your report only. **No database file goes into git.**

```
git add PROMPT_claude_code_2026-08-18_drop_legacy_vendor_mappings.md 2026-08-18_REPORT_claude_code_drop_legacy_vendor_mappings.md
```

Message:

```
docs: the 100 legacy three-digit vendor mappings are dropped

categorisations_client_vendors held 100 rows, all for Client_006 and all
carrying three-digit nominal codes across 23 distinct values. The master
chart is 122 accounts on four-digit codes, so every one of those codes was
provably stale and would have categorised a receipt to an account that no
longer exists.

Paul's decision: export them, then drop them. The export was taken and
verified before the delete and lives outside this repository. The table
itself is kept; only its rows are gone.

Consequence, stated because it is a behaviour change and not just tidying:
Client_006 has no learned vendor mappings at all until they are reseeded
against the master. That is the intended state, because the alternative
was mappings that produce wrong codes.
```

Fast-forward push, no force.

## Stop and ask about

- Anything on the Destructive Git Operations list.
- Any write to any table other than `categorisations_client_vendors`.
- `DROP TABLE`, or any schema change.
- Any count in task 1b that does not match.
- **Anything task 1c turns up.** I have read none of those four scripts and my confidence that dropping the rows is safe rests on the schema having no foreign keys, which is not the same thing.
- Starting or stopping the pipeline.
- Any file outside `C:\LastingImpact\receipt_capture`, including the two export files named above.

## Report to a file

`C:\LastingImpact\receipt_capture\2026-08-18_REPORT_claude_code_drop_legacy_vendor_mappings.md`, written before staging so it lands in the same commit.

Include: the pipeline check, the pre-delete counts, **every hit from task 1c printed whole**, where the backup went and how consistency was proved, the delete, and all five verification outputs.

**And one thing I want back.** Task 1c is the only part of this I could not do myself. **Tell me what reads that table, whatever the answer is.** If nothing reads it, that is worth knowing too, because it would mean the seeding scripts are the only consumers and the mapping feature is not wired into the pipeline at all.

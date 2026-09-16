# Claude Code brief, 2026-09-14: refuse to start when the database is missing a declared column

Paul's decision, 2026-09-14, after the live fault recorded at amendment 466 of
`2026-07-25_CONSOLE_DESIGN.md`.

**Report to `2026-09-14_REPORT_claude_code_schema_drift_check.md`.**

**One commit, proposed and not pushed.**

---

## What happened, and it is the reason for this

Step 10p added `line_items TEXT` to `extractions` in `worker/database/schema.py` on 2026-09-12.
`init_db()` runs `CREATE TABLE IF NOT EXISTS`, which creates a missing table and never alters an
existing one, and sub-step 10d.34 removed the nine `ALTER TABLE ADD COLUMN` migrations. **So the code
moved and the live database did not.**

`save_extraction()` names `line_items` in its INSERT unconditionally, so **every write to
`extractions` failed**, from nine production call sites. It surfaced two days later, on 2026-09-14 at
12:24 BST, as `sqlite3.OperationalError: table extractions has no column named line_items` while
applying a Desktop resolution note. A receipt arriving in those two days would have failed the same
way.

**The suite cannot see this class of fault**, because every test builds a database from the current
`schema.py`.

## What to build

**At start-up, after `init_db()` and before the first poll, refuse to start when the live database
is missing any column the schema declares, and name every missing column rather than the first.**

The message is read by Paul in a console window, so it says what is missing and what to do about it,
in his words rather than SQL jargon. Something of this shape, and the wording is yours:

```
the database at C:\Intellibills\db\receipts.db is missing columns the pipeline
writes: extractions.line_items. Add them before starting.
```

**Refuse rather than warn.** A pipeline that cannot write an extraction does nothing useful, and a
warning at start-up is a warning nobody reads. `config.check_git_status_on_startup()`'s dirty-tree
warning is the precedent for what a warning becomes: it has fired on every start for weeks.

## How to read the declared side, and this is the part with a choice in it

**Do not parse `schema.py`'s text with a regex.** A second reader of the schema is a second
definition and it drifts, which is the reason 10d.34 removed the migrations in the first place.

**The stronger shape, and I think it is the right one: run the schema's own SQL against an in-memory
database and compare `PRAGMA table_info` on both sides.** Both halves are then read the same way, by
SQLite, from the one definition. **Choose your own approach if you find a better one and say why.**

## Scope

- **Missing columns are the fault.** A column present in the live database and not declared is
  harmless: nothing writes it. Report it if it is free to do so, but it must not refuse the start.
- **Missing tables are not this check's business.** `init_db()` creates them.
- Do not add migrations. Do not alter the live database. This check reports and refuses.

## Evidence expected

- Red before green, with the failing output quoted.
- A test that a database missing a declared column refuses the start and names that column, built by
  creating a table without it rather than by patching the check.
- A test that a database matching the schema starts normally. **A check that cannot fail is not a
  check**, so show it discriminating in both directions.
- Mutations anchored on a unique string, `str.count()` asserted at 1, each diff printed.
- The suite before and after, measured. Run it again after the commit if the change adds a file.
- Your own mistakes, and a confidence level saying what it rests on.

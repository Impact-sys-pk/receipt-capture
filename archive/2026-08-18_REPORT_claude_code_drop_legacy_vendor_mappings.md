# Report: the 100 legacy vendor mappings are dropped

Written 2026-08-18 by the implementation session, Claude Code, in answer to
`PROMPT_claude_code_2026-08-18_drop_legacy_vendor_mappings.md`.

**Done. `categorisations_client_vendors` held 100 rows and now holds 0. The table, its
schema and its indexes are untouched, and no other table changed.** A verified backup
was taken first.

This session stopped once, before the delete, and reported a finding. Paul reviewed it,
corrected two things, and instructed the work to proceed. Both corrections are recorded
below, including the one that was mine and wrong.

**Confidence: high.** Every count came from a connection to the database itself, every
piece of code is quoted from the file, and callers were enumerated with `git ls-files`.
The one claim in the first draft of this report that was not measured that way was
false, and section 6 sets out exactly how.

---

## 1a. The pipeline was not running

Two `python.exe` processes existed. Both were identified before anything was touched:

```
ProcessId    : 43156
CreationDate : 18/08/2026 14:24:08
CommandLine  : c:\LastingImpact\receipt_capture\.venv\Scripts\python.exe
               c:\Users\PDK7\.vscode\extensions\ms-python.black-formatter-2026.6.0\bundled\tool\lsp_server.py

ProcessId    : 43332
CreationDate : 18/08/2026 14:24:08
CommandLine  : (identical)
```

**Both are the VS Code black-formatter language server.** They use the project's virtual
environment, which is why they carry the repository path, and neither opens the database.
No `pythonw.exe` and no other python-like process.

A second, independent sign at the time of the check: `C:\Intellibills\db\` held
`receipts.db` alone, with no `-wal` and no `-shm` companion. The database is in WAL mode,
so a live connection would normally leave both present.

`Intellibills\pipeline.lock` was **not** read. It is in OneDrive, outside permitted scope,
and the process list answers the question the brief actually asked.

## 1b. Every pre-delete count matched the brief

Read-only connection, `file:C:/Intellibills/db/receipts.db?mode=ro`.

```
journal_mode: wal
foreign_keys pragma: 0

categorisations                          1
categorisations_client_rules             0
categorisations_client_vendors           100
categorisations_firm_vendors             0
email_alerts                             0
email_delta                              0
extractions                              1
processed_attachments                    1
receipts                                 1
resolution_events                        0
statements                               0

row count: 100
distinct client_id: 1        values: ['Client_006']
distinct nominal_code: 23
nominal_code length -> count: [(3, 100)]
null nominal_code: 0
non-3-char rows: 0
```

**All eleven counts matched.** 100 rows, one client, 23 distinct codes, every code exactly
three characters, no nulls. The file was 233,472 bytes, last modified 2 August 2026 at
12:50, matching the brief. Nothing had changed since the consultant's read, so the export
still described what was about to be deleted.

### A correction to the brief, accepted by Paul

**The brief says the table has "no foreign keys". That is right about this table and wrong
about the database.** Three tables declare them:

```
categorisations:    -> extractions(extraction_id), -> receipts(receipt_id)
extractions:        -> receipts(receipt_id)
resolution_events:  -> receipts(receipt_id)
```

**None references `categorisations_client_vendors`, and nothing else does**, so the safety
conclusion holds. `PRAGMA foreign_keys` is `0` in any case, so SQLite is not enforcing the
ones that exist.

**My own script mislabelled that output and it is disclosed rather than quietly fixed.**
It printed the three foreign-key rows and then printed the line
"(nothing printed above = no foreign keys in any table)", a label written before the output
existed and contradicted by it. Nothing was concluded from the wrong label, but a label
that asserts what output shows, instead of being read against it, is the same failure as a
check that cannot fail.

---

## 1c. What reads the table

### Bounding the search

A plain recursive grep returns 456 KB of hits because `.history\` holds thousands of VS
Code Local History snapshots. **`.history/` is gitignored at `.gitignore:9` and contains
zero tracked files**, confirmed with `git check-ignore -v` and
`git ls-files | grep -c '^\.history/'`, which returns `0`. Excluded on that basis, not
because it looked long.

Tracked files containing the table name, with hit counts, plus untracked non-ignored files:

```
   6  2026-07-25_CONSOLE_DESIGN.md
   8  2026-07-31_PLAN_reset_and_restructure.md
   2  2026-08-02_HANDOVER_consultant_chat_5.md
   2  2026-08-03_NOTE_chart_of_accounts_for_paul.md
   1  2026-08-17_HANDOVER_consultant_chat_6.md
   1  2026-08-18_HANDOVER_consultant_chat_7.md
   1  CATEGORISATION.md
   1  CLAUDE.md
   1  PROMPT_claude_code_2026-08-01_after_db_move.md
   2  PROMPT_claude_code_2026-08-01_require_client_id.md
   1  PROMPT_claude_code_step7b_and_8.md
   1  import_vendor_csv.py
   2  regenerate_vendor_codes.py
   2  seed_client_vendors.py
   1  tests/test_resolution_backfeed.py
   3  tests/test_resolution_service.py
   2  tests/test_vendor_import_requires_client_id.py
   6  worker/database/repository.py
   2  worker/database/schema.py

untracked, non-ignored:
   PROMPT_claude_code_2026-08-18_drop_legacy_vendor_mappings.md   (this brief)
```

### Four methods, and the feature is wired in

All access goes through four methods in `worker/database/repository.py`. No other file
issues SQL against the table; the three scripts and the tests reach it through these.

**1. `list_gl_code_options_from_vendors()`, `repository.py:177`.** Section 2 below.

**2. `get_client_vendor(client_id, vendor_code)`, `repository.py:331`.** Exact-match lookup
returning the most-seen variant. Called by the engine at
`worker/categorisation/engine.py:236` as the exact-match layer and at `:267` to resolve a
fuzzy hit back to a mapping.

**3. `upsert_client_vendor(...)`, `repository.py:342`.** The writer. Live callers:
`worker/resolution/service.py:732`, `import_vendor_csv.py:46`, `seed_client_vendors.py:150`.

**4. `list_client_vendors(client_id)`, `repository.py:370`.** Distinct `vendor_code` values
used as fuzzy-match candidates at `worker/categorisation/engine.py:262`.

**On the engine's read path an empty table degrades cleanly.** Layer 1 gets `None` from
`get_client_vendor` and falls through to the firm layer. Layer 3a gets `[]` from
`list_client_vendors` and is guarded by `if client_vendors:`, so fuzzy matching is skipped
rather than run against nothing. That is "returns no match", which the brief allows.

### Stop condition 3 is not met: nothing rewrites three-digit codes automatically

The only automatic writer is `worker/resolution/service.py:732`, opt-in and operator-driven:

```python
        # 13. Learn the mapping only if asked. Never automatically: one correction
        #     against a misread supplier name would poison the mapping table, and
        #     the exact-match layer would then apply the wrong code confidently to
        #     every future receipt from that vendor.
        if corrections.remember_gl_for_supplier and effective_code:
            vendor_code = getattr(categorisation, "vendor_code", None)
            if vendor_code:
                repo.upsert_client_vendor(
                    client_id=receipt["client_id"],
                    vendor_code=vendor_code,
                    nominal_code=effective_code,
                    ...
```

It writes `effective_code`, the code the operator chose. It cannot reintroduce the legacy
rows.

**The two seeding scripts could, but only if a person runs them.** `seed_client_vendors.py`
and `import_vendor_csv.py` write whatever codes are in the CSV they are pointed at, and
`import_vendor_csv.py:72` still carries a usage example naming a `Client_006` vendor CSV.
Neither runs on a schedule and neither is invoked by the pipeline. **Recorded so that the
reseed is a deliberate act against the master chart, not a re-run of the old import.**

### Stop condition 1 is not met: no test depends on the production rows

Four test files touch the table. **All build their own database in a
`tempfile.TemporaryDirectory` via `TempEnvironment` and seed the rows they assert on.**
None opens `C:\Intellibills\db\receipts.db`.

`tests/test_resolution_backfeed.py:513` asserts the table is empty and
`tests/test_resolution_service.py:492` asserts it is unchanged, both temp-database
assertions about the opt-in learning behaviour. `tests/test_resolution_view.py:283` seeds
`nominal_code="271"`, a three-digit code, as a literal in its own temp database. **Emptying
the live table changes no test outcome.**

---

## 2. Why this stopped, and what Paul's correction established

`list_gl_code_options_from_vendors()` at `repository.py:177` UNIONs both vendor tables and
feeds `ResolutionView.gl_code_options` at `worker/resolution/service.py:417`:

```python
        # Fallback per 11.1 until the Default CoA is loaded at step 12. The
        # console shows a banner saying the CoA has not been loaded.
        gl_code_options=repo.list_gl_code_options_from_vendors(),
```

`categorisations_firm_vendors` already held **0 rows**, so the client table was the sole
source of every pair it returned. Emptying it makes that method return `[]`, taking
`gl_code_options` from 23 pairs to none. That is not a lookup returning no match, so the
brief's second stop condition was met and the session stopped.

### Paul's correction: the consumer chain ends nowhere

**The method is real and the return value does empty. It reaches no screen, because there
is no screen.** Paul's three checks, each re-run here rather than restated:

- **No web framework is a dependency.** `requirements.txt` is exactly three lines:
  `openai>=1.30.0`, `pymupdf>=1.24.0`, `python-dotenv==1.0.1`. `requirements-dev.txt` adds
  only `pytest>=8.0.0`. `grep -ic flask` returns `0` for both.
- **`worker/` has no web layer.** Its entries are `categorisation`, `database`, `email`,
  `extraction`, `intake`, `resolution`, `storage`, `validation`, plus
  `extraction_pipeline.py`, `filing.py`, `logging_setup.py` and `__init__.py`. No
  `templates/`, no `static/`, no console package.
- **`app.py` contains zero occurrences of `Flask`, `flask` or `render_template`.**

**Extending the check rather than repeating it:** no tracked `.py` file anywhere in the
repository imports flask, by `grep -inE '^\s*(import|from)\s+flask'` across
`git ls-files '*.py'`. The only tracked path matching `templates/`, `static/`, `/web/` or
`console` is `2026-07-25_CONSOLE_DESIGN.md`, the design document itself.

**So `gl_code_options` is a field on a data structure nothing renders.** The empty window is
real in the return value and invisible in practice. Paul reviewed this and instructed the
delete to proceed.

---

## 3. A finding for the consultant session: the console has no valid GL code source at all

**Recorded, not fixed. Section 11.1 is untouched.** This is bigger than the delete and is
the consultant's to resolve.

The chain is short and every link is now established:

1. `list_gl_code_options_from_vendors()` is described in its own docstring as *"the fallback
   in design document 11.1, for use until the Default CoA is loaded into `coa_accounts` at
   step 12"*, and as *"not the real option list: it only contains codes some vendor has
   already been mapped to"*.
2. **`coa_accounts` is cancelled.** The chart of accounts now lives in IntelliCharts, outside
   this repository, and nothing in this repository reads it from there.
3. So the fallback was not a fallback any more. **It was the only remaining source for the
   console's GL code list**, and it could only ever offer codes some vendor had already been
   mapped to, which is exactly what it warns about itself.
4. As of this delete, both vendor tables are empty, so that source yields nothing.

**Dropping these rows did not create the gap. It made the gap impossible to miss.** Before
today the console had a source that was wrong but non-empty: 23 stale three-digit codes
pointing at accounts that no longer exist. A wrong-but-populated dropdown is worse than an
empty one, because it can be used.

**What is not decided, and is not this session's to decide:** where the console's code
options come from now that the chart lives in IntelliCharts and `coa_accounts` is cancelled.
Section 11.1 still describes the old arrangement and has deliberately been left alone.

---

## 4. Flagged, not fixed: a latent bug in the engine's learning method

Found while enumerating callers, unrelated to the delete, not touched. Paul has seen it and
said to leave it.

`worker/categorisation/engine.py:399`, `learn_from_correction()`, calls:

```python
        self.repo.upsert_client_vendor(
            client_id=client_id, vendor_key=vendor_key,
            nominal_code=nominal_code, account_name=account_name,
            last_updated=now
        )
```

The signature at `repository.py:342` is:

```python
    def upsert_client_vendor(self, client_id: str, vendor_code: str,
                            nominal_code: str, account_name: str, last_updated: str,
                            vendor_name: str = None, detail: str = None):
```

**There is no `vendor_key` parameter and the required `vendor_code` is not passed**, so that
call raises `TypeError` if reached. The same method then calls
`get_firm_vendor(business_type, vendor_key)` and `upsert_firm_vendor(..., vendor_key=...)`,
and those take `vendor_code` too, at `repository.py:378` and `:389`.

**It is unreachable today, which is why nothing has failed.** The only references to
`learn_from_correction` outside its own definition are in
`docs/specs/categorisation_engine.py`, a specification document, and no live module imports
anything under `docs/`, checked across every tracked `.py` file. The live learning path is
`worker/resolution/service.py:732`, which passes the right arguments.

---

## 5. The backup

**`C:\Intellibills\db\receipts-backup-2026-08-18-pre-legacy-vendor-drop.db`**, 233,472 bytes,
written before the delete.

**Where it went, and why there.** `config.BACKUPS_ROOT` resolves to
`ONEDRIVE_ROOT / "Intellibills" / "Backups"`, which is inside the practice root and off
limits to this session. The backup was therefore written beside the database it protects, in
`C:\Intellibills\db\`, which is local, is the same folder as the file this brief authorised
changing, and touches nothing in OneDrive. **That location was this session's judgement, not
the brief's instruction**, which asked where it went without saying where to put it.

**How consistency was proved.** SQLite's own online backup API, `sqlite3.Connection.backup()`,
which is what `repo.backup_db()` at `repository.py:293` uses. It copies a consistent snapshot
including WAL content, which a file copy of the main file alone would not. The API was called
directly rather than through `Repository()` so that nothing imported `config`, whose import
side effects create directories under `BACKUPS_ROOT`.

Read back from the backup **before** the delete:

```
backup size: 233472 bytes    source size: 233472 bytes

categorisations                          1
categorisations_client_rules             0
categorisations_client_vendors           100
categorisations_firm_vendors             0
email_alerts                             0
email_delta                              0
extractions                              1
processed_attachments                    1
receipts                                 1
resolution_events                        0
statements                               0

BACKUP categorisations_client_vendors rows: 100
distinct client_id: ['Client_006']
distinct nominal_code count: 23
backup schema sha256: 149009fc782f6c19bcca6571015155881b97952b264adf24c5d353a01f9c437a
integrity_check: ok
```

Every table matched the source, the schema hash matched, and `PRAGMA integrity_check`
returned `ok`. The script refused to run at all if the destination already existed.

## 6. The delete

```
rows before: 100
rowcount reported by DELETE: 100
rows after: 0
schema byte-identical: True
DELETE COMMITTED
```

`DELETE FROM categorisations_client_vendors`. No `DROP TABLE`, no schema change, no other
table touched. The script asserted the count was 100 before deleting and would have aborted
otherwise.

---

## 7. Verification, all five steps

**1. The target table is empty.**

```
categorisations_client_vendors: 0
```

**2. Every other table is unchanged.** All eleven printed, not just the ones expected to move:

```
  categorisations                        1 -> 1
  categorisations_client_rules           0 -> 0
  categorisations_client_vendors       100 -> 0     <- intended change
  categorisations_firm_vendors           0 -> 0
  email_alerts                           0 -> 0
  email_delta                            0 -> 0
  extractions                            1 -> 1
  processed_attachments                  1 -> 1
  receipts                               1 -> 1
  resolution_events                      0 -> 0
  statements                             0 -> 0

  tables in db: 11; tables in brief: 11; unexpected changes: []
```

The table count was compared as well as the individual counts, so a table appearing or
disappearing would have shown up rather than being silently skipped.

**3. The schema is byte-identical.**

```
sha256 now:     149009fc782f6c19bcca6571015155881b97952b264adf24c5d353a01f9c437a
sha256 before:  149009fc782f6c19bcca6571015155881b97952b264adf24c5d353a01f9c437a
byte-identical: True
```

```
CREATE TABLE categorisations_client_vendors (
            vendor_key              TEXT PRIMARY KEY,
            client_id               TEXT NOT NULL,
            vendor_code             TEXT NOT NULL,
            nominal_code            TEXT NOT NULL,
            account_name            TEXT NOT NULL,
            vendor_name             TEXT,
            detail                  TEXT,
            times_seen              INTEGER DEFAULT 1,
            last_updated            TEXT NOT NULL,
            UNIQUE(client_id, vendor_code, vendor_name)
        )
```

The table is still present and its three indexes survive:
`sqlite_autoindex_categorisations_client_vendors_1`,
`sqlite_autoindex_categorisations_client_vendors_2` and `idx_client_vendor_code`.

**4. The backup still holds 100 rows, read after the delete.**

```
backup categorisations_client_vendors rows: 100
backup integrity_check: ok
backup distinct nominal_code: 23
```

**5. Git.**

```
git --no-optional-locks status --porcelain
?? 2026-08-18_REPORT_claude_code_drop_legacy_vendor_mappings.md
?? PROMPT_claude_code_2026-08-18_drop_legacy_vendor_mappings.md
```

The brief and this report, nothing else. No database file appears.

**One observation not asked for.** `receipts.db` is still 233,472 bytes. `DELETE` frees pages
for reuse but does not shrink the file, and no `VACUUM` was run because the brief did not ask
for one and it would rewrite the whole file. Both databases now carry `-wal` and `-shm`
companions, and both `-wal` files are zero bytes, meaning everything is checkpointed into the
main file.

---

## 8. My false claim, and exactly what produced it

The first draft of this report stated: **"`check_missing_categorisation.py` does not exist.
The brief named it as one of four scripts. Three exist; that one is in no tracked or
untracked file in the repository."**

**That is wrong. The file exists, is tracked, is 1,542 bytes and is dated 26 July 2026.**

**What actually produced it.** The only command run was:

```
git ls-files -z | xargs -0 grep -ln 'categorisations_client_vendors'
```

That prints tracked files **whose contents contain that string**. `check_missing_categorisation.py`
contains it **zero** times, confirmed by `grep -c`, so it was correctly absent from that list.
The list was then read as though it were an inventory of files that exist.

**No existence check was ever run.** Not `ls`, not `git ls-files <path>`, not
`git ls-files --error-unmatch`. A claim about existence was drawn from a list about content,
and the two were never distinguished.

This is the trap `CLAUDE.md` states as **"a filter is not a reader"**: anything the pattern
does not match passes through unseen, and what gets reasoned about is the filter's output
rather than the repository. It is also an unenumerated set claim of exactly the kind amendment
94 covers. The phrase that should have triggered the check was "three exist" — a count, about
a set, asserted without counting the set.

**What the file actually does, now that it has been read.** It queries `receipts` and calls
`repo.get_categorisation_for_receipt()` to find receipts filed with `ok` status that have no
categorisation. **It never touches `categorisations_client_vendors`**, so it is irrelevant to
this delete. The conclusion the wrong claim was serving happened to be right, which is the
part worth noticing: **a false premise reached a true conclusion, and nothing in the process
would have caught it if the conclusion had been wrong too.**

Found because Paul checked the claim against `.git/index` and said so.

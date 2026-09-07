# Report: `vendor_key` and `vendor_code` mean the wrong things, in five places

**Written 2026-09-06 by the Claude Code implementation session**, from
`PROMPT_claude_code_2026-09-06_vendor_key_naming.md`. Times in this report are
BST, which is what the Windows clock reports; the consultant session's shell
reports UTC and will read them an hour earlier.

**One thing in the brief is not done, and it is the live database.** Everything
else is. The single command Paul needs to run is in section 8.

---

## 1. Task 1. The facts, established from the repository

**Read on 2026-09-06 from `C:\Intellibills\db\receipts.db` with
`PRAGMA table_info` and `SELECT`, and from the source of the five files that
touch either name.** Not from the brief's table.

### The brief's table is right on every row it states

| Where | Column or field | The brief said | What was found | Agrees |
|---|---|---|---|---|
| `categorisations_client_vendors` | `vendor_key` | a row UUID | `523efdfa-6a2f-4f33-993b-f8d9b530fa9d`, the only row | yes |
| | `vendor_code` | the normalised key | `imo`, same row | yes |
| `categorisations_firm_vendors` | `vendor_key`, `vendor_code` | same two, same way round, 0 rows | column list matches, 0 rows | yes |
| `categorisations_client_rules` | `vendor_code` | the normalised key, 0 rows | column list matches, 0 rows | yes |
| `categorisations` | `vendor_key` | a matched mapping's UUID | confirmed from the code, see below | yes |
| `CategorisationResult` | `vendor_code` | the normalised key, always set | confirmed | yes |
| | `vendor_key` | the matched mapping's UUID, on a match only | confirmed | yes |

**The one correction the brief disclosed was the right correction to make.**
`categorisations.vendor_key` does hold a mapping's row id and not the normalised
key. That is not visible in the data, because all 11 rows are `match_source
unmatched` and hold `NULL`, so it was established from the code.

### Task 1 item 3, what `categorisations.vendor_key` is written from, by line

The chain, read rather than inferred, and the line numbers are the ones before
this brief's edits:

1. **`worker\categorisation\engine.py:296`** sets
   `vendor_key=client_vendor["vendor_key"]` on layer 1's result.
   `client_vendor` comes from `Repository.get_client_vendor()`, whose
   `SELECT` at `worker\database\repository.py:335` names `vendor_key` first,
   and that column is the table's `TEXT PRIMARY KEY`, a UUID minted at
   `repository.py:362`. **The same shape at `:309`, `:328` and `:347`** for
   layers 2, 3 and 4.
2. **`worker\database\repository.py:455`** takes it as
   `save_categorisation(..., vendor_key: Optional[str], ...)` and inserts it
   into the `categorisations.vendor_key` column at `:470` and `:474`.
3. **Five callers pass it**, enumerated by grepping every `.py` file rather
   than by naming the ones I remembered: `app.py:505`,
   `worker\extraction_pipeline.py:266`, `worker\resolution\service.py:820`,
   `worker\resolution\service.py:1303`, `retroactive_categorise.py:159`. All
   five pass `vendor_key=categorisation.vendor_key`.

**So the column holds the row id of the learned mapping a layer matched.**

### Two things the brief got slightly wrong, neither of which changes anything

- **The brief cites `resolve_receipt():773` for the `getattr`. It is at line
  893.** The function is right, `resolve_receipt()` runs 615 to 941; the line
  number is not. Reported because a line number in a brief is the kind of thing
  the next session copies forward.
- **The brief's `learn_from_correction()` is at `engine.py:527`, which is
  right**, and the `TypeError` claim is right:
  `upsert_client_vendor(self, client_id, vendor_code, ...)` at
  `repository.py:343` has no `vendor_key` parameter.

### The enumeration, and what was excluded from it

**`.history\` is excluded.** It is a VS Code Local History directory, gitignored
at `.gitignore:9`, with 0 files tracked by git. Including it turned a 205-line
answer into a 1,133-line one across 89 files, none of them the repository. The
enumeration below is `git ls-files '*.py'` for the before, and
`git ls-files --cached --others --exclude-standard '*.py'` for the after, so
files this brief created are counted.

**That difference is a mistake I made and caught.** The first after-enumeration
used `git ls-files` alone and silently omitted `tests\test_vendor_key_naming.py`
and `migrate_2026_09_06_vendor_key_naming.py`, because they were untracked. The
file count came back as 20 both times, which looked like nothing had moved.

Both enumerations are printed whole in section 6.

---

## 2. Task 2. The names

The target in the brief was correct and is what was built.

| Thing | Was | Is |
|---|---|---|
| The normalised merchant key, `imo` | `vendor_code` | **`vendor_key`** |
| A learned mapping's row id | `vendor_key` | **`mapping_id`** |
| `categorisations`'s pointer at a learned mapping | `vendor_key` | **`mapping_id`** |
| `CategorisationResult`'s two fields | `vendor_code`, `vendor_key` | **`vendor_key`, `mapping_id`** |
| The two indexes | `idx_client_vendor_code`, `idx_firm_vendor_code` | **`idx_client_vendor_key`, `idx_firm_vendor_key`** |
| The `resolution_events.corrections_json` key | `"vendor_code"` | **`"vendor_key"`** |

**`vendor_code` no longer exists as an identifier anywhere.** Section 5 names
the five places the string survives and says why each one is allowed.

**One thing worth knowing, found while doing this.** The frozen v0.1 spec at
`docs\specs\categorisation_engine.py` uses `vendor_key` for the normalised key,
42 times, and has no `vendor_code` at all. **The live code drifted away from its
own spec's naming and this brief has put it back.** That file is a design
document with a `.py` extension: its `CategorisationEngine` keeps JSON files
under `data\`, nothing imports it, and it was not touched.

---

## 3. Task 3. The migration

**Said before doing, as the brief asked.**

- **The three learned tables: dropped and recreated from `schema.py`.** Paul's
  decision. Their indexes go with them.
- **`categorisations`: not dropped.** One
  `ALTER TABLE categorisations RENAME COLUMN vendor_key TO mapping_id`. All 11
  rows stay. The column is `NULL` on every one of them, so no data moves.
  SQLite here is 3.50.4, well past the 3.25 that `RENAME COLUMN` needs.

**Rows that would be lost, from a dry run against the live database:**

```
database: C:\Intellibills\db\receipts.db
  before  categorisations_client_vendors     1
  before  categorisations_firm_vendors       0
  before  categorisations_client_rules       0
  before  categorisations                    11
```

**One row. The `imo` mapping made at 07:59 on 2026-09-06.**

**A backup was taken before anything: `C:\Intellibills\db\receipts.db.bak-2026-09-06-vendor-key-rename`, 233,472 bytes.**

**The migration has NOT been applied.** It is written as
`migrate_2026_09_06_vendor_key_naming.py`, it dry-runs correctly, and the write
was refused by this session's permission layer, twice, in both the forms I tried.
That is the guard working as intended for a `DROP TABLE` against the live
database, and I did not attempt to go round it. Section 8 has the command.

**Consequence while it is unapplied: the code and the live database disagree.**
The suite is unaffected, because every test builds its own database from
`schema.py`. A pipeline run against the live database would fail on the first
learned-table query. **Do not start the pipeline until the migration has run.**

---

## 4. Task 4. `learn_from_correction()`, item 54

**Deleted. Paul's decision, asked and answered during this session, 2026-09-06.**

**Why the question had to be asked, and it was not the reason the brief gave.**
The brief expected the rename to leave the function "wrong in a new way". It
does the opposite: `upsert_client_vendor()`'s parameter becomes `vendor_key`,
which is exactly what the call was already passing, so **a mechanical rename
would have turned a function that raised `TypeError` into a working one**. It
was the only writer `categorisations_firm_vendors` had anywhere, and item 166 is
deferred, so the rename would have quietly created a firm-table writer that only
needed a caller. A dead function that raises cannot become a silent firm write
by accident; a working one can.

**What was removed:** `worker\categorisation\engine.py:527-571`, 46 lines
including the blank separator. Nothing called it, before or after.

**What holds it down:** `tests\test_vendor_key_naming.py::LearnFromCorrectionIsGone`,
two tests. One asserts `CategorisationEngine` has no such attribute. The other
scans every `.py` file in the repository for the name and asserts nothing carries
it. `docs\`, `archive\`, `.history\`, `.venv\` and `__pycache__\` are excluded,
and the exclusion of `docs\` is commented in the test: the v0.1 spec has its own
`learn_from_correction()` and it is not this one.

**The 10j.11 constraint is untouched.**
`test_the_firm_table_is_never_written_on_this_route` still patches
`upsert_firm_vendor()` and asserts zero calls, and it still passes.

---

## 5. Task 5. The two flags from yesterday

**Both are closed and both moved together.**

- **`resolve_receipt()`, now line 893.** Reads
  `getattr(categorisation, "vendor_key", None)`. **The default is still right.**
  `None` there falls to the `else` branch, which logs
  `"remember_gl_for_supplier requested for {receipt_id} but the engine returned
  no vendor_key, so nothing was learned"` and learns nothing. That is the
  behaviour to keep and it is kept.
- **`_apply_filed_note()`, now line 1354.** Reads
  `categorisation.vendor_key` directly. Same field, same warning on the empty
  case.
- **The comment above the second one said the opposite of the truth after the
  rename** and has been rewritten. It now records that both names moved and
  that the old sentence was right under the old names, rather than being
  silently replaced.

**Flag, not fixed.** The two branches read the same field two different ways.
`resolve_receipt()` uses `getattr` with a default; `_apply_filed_note()` uses
plain attribute access. **A future rename would make the first silently stop
learning and the second raise.** The `getattr` is the one that hides a rename,
which is the exact failure this brief exists to correct. Making them consistent
is a one-line change either way and it changes behaviour on a path nobody has
specified, so it is left alone. **Small and obviously right if you want it: drop
the `getattr` at line 893 for `categorisation.vendor_key`, matching
`_apply_filed_note()`. Say the word and it goes in with the next thing.**

**CLOSED 2026-09-06 on Paul's answer. Section 9 records what was done.**

---

## 6. Verification

### 6.1 The suite, before and after

**Before, `.\.venv\Scripts\python.exe -m pytest -q`:**

```
513 passed, 328 subtests passed in 12.27s
```

Which is what the brief said it would be.

**After:**

```
522 passed, 330 subtests passed in 13.89s
```

**Zero skips both times.** The nine new tests are
`tests\test_vendor_key_naming.py`. The two new subtests are the two tables in
`test_the_learned_tables_are_keyed_on_mapping_id`.

### 6.2 The enumeration, printed whole

**Before** is at the end of this report, appendix A. 102 tracked `.py` files
scanned, 20 with hits, 205 lines.

**After** is appendix B. 104 files scanned (tracked plus untracked, gitignored
excluded), 22 with hits, 250 lines. The after-enumeration searches
`mapping_id` as well, or it would not show where the row id went.

### 6.3 `PRAGMA table_info` after the change

Appendix C. **It reports two things, because the live database is not migrated
yet:** what `schema.py` now creates, read from an in-memory database built from
the file's own `executescript()` argument, and the live database's current state,
which is still the old names.

### 6.4 The `vendor_code` test, and every survivor named

**`tests\test_vendor_key_naming.py::VendorCodeIsGone`.** The string survives
nowhere under `worker\` except two comment lines, both named in an explicit
allowlist in the test with a reason each:

| File | Line | Why it is allowed |
|---|---|---|
| `worker\categorisation\engine.py` | `# vendor_code on 2026-09-06: "code" means a four-digit account code` | names the old field name in `CategorisationResult`'s own comment |
| `worker\resolution\service.py` | ``# normalised key was called `vendor_code` and is now called`` | names the old field name where the rename reversed the comment |

**The allowlist is checked in both directions.** An entry that no longer matches
anything fails the test, so it cannot rot into a check that always passes. A
second test asserts every survivor is a comment line, so the allowlist cannot be
used to smuggle live code past it.

**Three survivors outside `worker\`, and they are a file format rather than a
name.**

| File | Why |
|---|---|
| `import_vendor_csv.py` | reads `row.get('vendor_key') or row.get('vendor_code')`. The CSVs on disk were written with the old header and were not rewritten |
| `regenerate_vendor_codes.py` | same, twice, and writes the new header back out |
| `tests\test_vendor_import_requires_client_id.py` | its fixture CSV deliberately keeps the old header, which is what keeps the back-compatible read exercised |

**Flag, not fixed: the file `regenerate_vendor_codes.py` still has `vendor_code`
in its own name.** Renaming it means a `git mv` plus two edits to
`RECEIPT_CAPTURE_GUIDE.md`, lines 396, 398 and 497. It is also already recorded
as broken: **item 115 says `regenerate_codes()` is called by nothing, including
by its own file**, because the `__main__` block re-implements it inline. Renaming
a file whose one function is dead did not seem like this brief's business.

### 6.5 The 10j.11 proof, re-run against a temporary database

`tests\test_desktop_learning.py::FiledNoteLearningTest`, **10 tests, all
passing**, each against a `TempEnvironment()` database and a `TempChartBundle`:

```
test_a_code_the_chart_does_not_hold_teaches_nothing_even_with_the_tick  PASSED
test_a_name_with_no_code_teaches_nothing_even_with_the_tick             PASSED
test_an_unreadable_chart_teaches_nothing_even_with_the_tick             PASSED
test_learning_leaves_its_own_audit_row                                  PASSED
test_no_audit_row_and_no_learning_when_the_tick_is_off                  PASSED
test_the_firm_table_is_never_written_on_this_route                      PASSED
test_the_row_count_before_and_after                                     PASSED
test_the_tick_writes_one_client_vendor_row                              PASSED
test_what_is_written_is_the_vendor_key_layer_one_looks_up               PASSED
test_without_the_tick_the_same_note_learns_nothing                      PASSED
```

**One row into `categorisations_client_vendors`, zero into
`categorisations_firm_vendors`**, which is what
`test_the_tick_writes_one_client_vendor_row` and
`test_the_firm_table_is_never_written_on_this_route` assert between them.

### 6.6 Mutation: break the rename in one place, see what goes red

**Four mutations, each applied alone to a clean tree and reverted afterwards.**

| | Mutation | Red |
|---|---|---|
| **A** | `schema.py`: put the client-vendor row id back under the name `vendor_key` | **198 tests**, across 30 files, including all four schema-shape tests in `test_vendor_key_naming.py` |
| **B** | `service.py`: `_apply_filed_note()` learns from `mapping_id` instead of `vendor_key` | **5 tests**, all in `FiledNoteLearningTest`, the 10j.11 class |
| **C** | `engine.py`: layer 1 puts the row id in `vendor_key` and the key in `mapping_id`, the old way round | **0 at first. See below** |
| **D** | `service.py`: the audit blob keeps the old key `"vendor_code"` | **2 tests**: `test_learning_leaves_its_own_audit_row` and the `vendor_code` guard |

**Mutation C survived the whole suite, and that is the most useful thing in this
report.** Swapping the two fields at layer 1, which is precisely the defect this
brief exists to correct, left **522 passed** and nothing red. It survived because
nothing anywhere asserted what a **matched** receipt stores in either field:
every `categorisations` row in existence is `unmatched`, layer 1 only fires once
a mapping is already learned, and no test had ever combined the two.

**Two assertions were added to close it**, both in the test that already names
the property, `test_what_is_written_is_the_vendor_key_layer_one_looks_up`: the
categorisation's `mapping_id` equals the learned row's `mapping_id`, and the
learned row's `vendor_key` is `"apcoa parking"` and not a UUID.

**Re-run of mutation C after that:**

```
1 failed, 521 passed, 330 subtests passed
  tests/test_desktop_learning.py::FiledNoteLearningTest::test_what_is_written_is_the_vendor_key_layer_one_looks_up
```

**One test, and it is the right one.** The suite discriminates.

**Flag, not fixed: the same mutation at layer 2 still survives.** Applying the
identical swap to the firm branch at `engine.py:309` leaves 522 passed and
nothing red. **It cannot be closed without writing the firm table, which the
brief forbids and item 166 defers.** Nothing in this repository writes
`categorisations_firm_vendors` any more, `learn_from_correction()` having been
its only writer, so layer 2 can never fire. **This belongs to item 166: whoever
builds the firm write needs to know that the layer it feeds is untested by
construction.**

### 6.7 Two more disclosures

- **I added an assertion to an existing test, `test_learning_leaves_its_own_audit_row`.**
  The rename moved the `resolution_events.corrections_json` key from
  `"vendor_code"` to `"vendor_key"` and **no test asserted that key at all**, so
  the rename could have moved it silently. It now asserts the new key is present
  with the right value and the old key is absent. Mutation D is what proves that
  assertion works.
- **My first version of the no-caller test failed**, and correctly. It found
  `learn_from_correction` in `docs\specs\categorisation_engine.py`. That is the
  frozen v0.1 spec and not a caller, so `docs\` was excluded and the reason
  written into the test rather than into this report alone.

---

## 7. Everything the brief said not to do

| Instruction | State |
|---|---|
| Do not drop `categorisations`, `receipts`, `extractions`, `resolution_events` | Not dropped. Only `categorisations` is touched at all, by one `RENAME COLUMN` |
| Do not give `learn_from_correction()` a caller | It has no caller because it no longer exists |
| Do not write the firm table | Not written. Its only writer was deleted, so it now has none |
| Do not rename anything in `IntelliBooks-Desktop-v3.html` | Not opened |
| Do not touch `IntelliCharts\` | Not opened |

**One thing to be aware of that is not a breach.** The existing `learn_vendor`
row in `resolution_events` still carries `"vendor_code": "imo"` in its
`corrections_json`. **It was left alone on purpose:** the brief says
`resolution_events` is not touched by this brief, and an audit blob records what
was written at the time. So a query across that column will see both spellings,
with the changeover on 2026-09-06.

---

## 8. What Paul needs to do, and it is one command

**The migration is written, dry-run, and not applied.** Run it from
`C:\LastingImpact\receipt_capture`:

**Terminal command:**

```
.\.venv\Scripts\python.exe migrate_2026_09_06_vendor_key_naming.py --yes
```

**Plain English:** it drops the three learned tables, losing the one `imo`
mapping, renames one column on `categorisations` without touching its 11 rows,
and rebuilds the three tables from `schema.py` under the new names. Running it
without `--yes` prints the row counts and does nothing, which is worth doing
first.

**In VS Code GUI:**

1. Open the Terminal, Ctrl and the backtick key
2. Check the prompt says `C:\LastingImpact\receipt_capture`
3. Paste the command without `--yes` first and read the counts
4. Paste it again with `--yes`

**The backup is at
`C:\Intellibills\db\receipts.db.bak-2026-09-06-vendor-key-rename`** if anything
needs putting back.

**Then remake the `imo` mapping with the review fixture**, which is the three
minutes the brief budgeted for.

**Do not start the pipeline before running it.** The code expects the new column
names and the live database still has the old ones.

---

## Appendix A. The enumeration, before

```
TRACKED .py FILES SCANNED: 102
FILES WITH HITS: 20  TOTAL LINES: 205
##############################################################################
app.py (1 lines)
  505:                 vendor_key=categorisation.vendor_key,
##############################################################################
docs/specs/categorisation_engine.py (42 lines)
  142: def extract_vendor_key(normalised: str, aliases: dict = None) -> str:
  304:             vendor_key = extract_vendor_key(normalised, self.aliases)
  306:             if not vendor_key:
  310:                 vendor=vendor_key,
  316:             if vendor_key in self.client_lookup:
  317:                 self.client_lookup[vendor_key].times_seen += 1
  318:                 self.client_lookup[vendor_key].last_updated = datetime.now().isoformat()
  320:                 self.client_lookup[vendor_key] = mapping
  324:             if vendor_key not in self.firm_lookup:
  325:                 self.firm_lookup[vendor_key] = VendorMapping(
  326:                     vendor=vendor_key,
  331:                 self.firm_lookup[vendor_key].times_seen += 1
  342:         vendor_key = extract_vendor_key(normalised, self.aliases)
  344:         if not vendor_key:
  353:         if vendor_key in self.client_lookup:
  354:             m = self.client_lookup[vendor_key]
  366:         if vendor_key in self.firm_lookup:
  367:             m = self.firm_lookup[vendor_key]
  380:             vendor_key, list(self.client_lookup.keys()), threshold=0.70
  397:             vendor_key, list(self.firm_lookup.keys()), threshold=0.70
  445:         vendor_key = extract_vendor_key(normalised, self.aliases)
  447:         if not vendor_key:
  453:         if vendor_key in self.client_lookup:
  454:             self.client_lookup[vendor_key].nominal_code = nominal_code
  455:             self.client_lookup[vendor_key].account_name = account_name
  456:             self.client_lookup[vendor_key].times_seen += 1
  457:             self.client_lookup[vendor_key].last_updated = now
  459:             self.client_lookup[vendor_key] = VendorMapping(
  460:                 vendor=vendor_key,
  468:             if vendor_key not in self.firm_lookup:
  469:                 self.firm_lookup[vendor_key] = VendorMapping(
  470:                     vendor=vendor_key,
  477:                 if self.firm_lookup[vendor_key].nominal_code == nominal_code:
  478:                     self.firm_lookup[vendor_key].times_seen += 1
  479:                     self.firm_lookup[vendor_key].last_updated = now
  484:         self._append_history(txn, vendor_key, nominal_code, account_name)
  489:     def _append_history(self, txn: Transaction, vendor_key: str,
  504:             "vendor_key": vendor_key,
  545:         for vendor_key, firm_mapping in self.firm_lookup.items():
  546:             if vendor_key in self.client_lookup:
  547:                 client_mapping = self.client_lookup[vendor_key]
  555:                         "vendor": vendor_key,
##############################################################################
import_vendor_csv.py (8 lines)
    4: CSV format: vendor_code,vendor_name,detail,nominal_code,account_name
   29:                 # Handle both vendor_key (old) and vendor_code (new) column names
   30:                 vendor_code = row.get('vendor_code') or row.get('vendor_key')
   31:                 if not vendor_code:
   35:                 vendor_code = vendor_code.strip()
   41:                 if not vendor_code or not nominal_code:
   48:                         vendor_code=vendor_code,
   56:                     print(f"[+] {vendor_code:30} -> {nominal_code} {account_name}")
##############################################################################
probe_layer5.py (1 lines)
  107:                 f"  {label}  vendor_code={res.vendor_code!r}  "
##############################################################################
regenerate_vendor_codes.py (13 lines)
    2: Regenerate vendor_code from vendor_name using engine normalization logic.
   47: def extract_vendor_key(normalised: str, aliases: dict = None) -> str:
   69:     """Regenerate vendor_codes from vendor_names."""
   90:         new_code = extract_vendor_key(normalised, DEFAULT_ALIASES)
   92:         old_code = row.get('vendor_code', '')
  102:         row['vendor_code'] = new_code
  106:     fieldnames = ['vendor_code', 'vendor_name', 'detail', 'nominal_code', 'account_name']
  114:     print(f"Unique vendor_codes: {len(code_map)}")
  147:         new_code = extract_vendor_key(normalised, DEFAULT_ALIASES)
  148:         old_code = row.get('vendor_code', '')
  157:         row['vendor_code'] = new_code
  161:     fieldnames = ['vendor_code', 'vendor_name', 'detail', 'nominal_code', 'account_name']
  169:     print(f"Unique vendor_codes: {len(code_map)}")
##############################################################################
retroactive_categorise.py (1 lines)
  159:                     vendor_key=categorisation.vendor_key,
##############################################################################
seed_client_vendors.py (7 lines)
   54: def extract_vendor_code(normalised: str, aliases: dict = None) -> str:
  120:             vendor_codes_seen = set()
  140:                 vendor_code = extract_vendor_code(normalised)
  143:                 if not vendor_code or vendor_code in vendor_codes_seen:
  147:                 vendor_codes_seen.add(vendor_code)
  152:                     vendor_code=vendor_code,
  160:                 print(f"[+] {client_id} | {vendor_code:20} | {detail:40} -> {gl_code}")
##############################################################################
tests/test_desktop_learning.py (4 lines)
   22: return the learned code. The second is what proves `vendor_code` and not
   23: `vendor_key` is the right thing to write, because `vendor_code` is what layer 1
  351:     def test_what_is_written_is_the_vendor_code_layer_one_looks_up(self):
  352:         # Not the vendor_key, which is the UUID primary key of a mapping that
##############################################################################
tests/test_fallback_accounts.py (1 lines)
  271:         business_type="UNSPECIFIED", vendor_code="canary",
##############################################################################
tests/test_resolution_service.py (1 lines)
  422:             client_id="CLIENT001", vendor_code="apcoa parking",
##############################################################################
tests/test_resolution_view.py (3 lines)
  195:                     vendor_key=None,
  298:                     client_id="CLIENT001", vendor_code="apcoa parking",
  303:                     business_type="PHV_DRIVER", vendor_code="shell",
##############################################################################
tests/test_retroactive_categorise_sidecar.py (2 lines)
  156:                     vendor_code="apcoa parking",
  186:                     vendor_key=None,
##############################################################################
tests/test_sidecar_category_keys.py (3 lines)
  120:     def seed_mapping(self, repo, vendor_code="apcoa parking", code="271", name="Parking and tolls"):
  121:         # vendor_code is normalise_description("Apcoa Parking"), which is what
  125:             vendor_code=vendor_code,
##############################################################################
tests/test_step10d_pipeline.py (2 lines)
  296:         self.assertIn("UNIQUE(business_type, vendor_code, vendor_name)", sql)
  297:         self.assertNotIn("UNIQUE(business_type, vendor_code, vendor_name, firm_id)", sql)
##############################################################################
tests/test_vendor_import_requires_client_id.py (1 lines)
   30: IMPORT_CSV = """vendor_code,vendor_name,detail,nominal_code,account_name
##############################################################################
worker/categorisation/engine.py (38 lines)
  103:     vendor_code: Optional[str] = None
  104:     vendor_key: Optional[str] = None
  143: def extract_vendor_key(normalised: str, aliases: dict = None) -> str:
  207:     def _rule_matches(self, rule: dict, vendor_code: str, detail: str) -> bool:
  210:         if rule.get("vendor_code") and rule["vendor_code"] != vendor_code:
  219:         field_value = detail.lower() if condition_field == "detail" else vendor_code.lower()
  266:         vendor_code = extract_vendor_key(normalised, self.aliases)
  268:         if not vendor_code:
  279:                 if self._rule_matches(rule, vendor_code, supplier_name):
  283:                         vendor_code=vendor_code, suggested_code=rule["nominal_code"],
  291:             client_vendor = self.repo.get_client_vendor(client_id, vendor_code)
  296:                     vendor_code=vendor_code, vendor_key=client_vendor["vendor_key"],
  300:                     matched_vendor=vendor_code, needs_review=False
  304:             firm_vendor = self.repo.get_firm_vendor(business_type, vendor_code)
  309:                     vendor_code=vendor_code, vendor_key=firm_vendor["vendor_key"],
  313:                     matched_vendor=vendor_code, needs_review=False
  319:                 fuzzy_results = fuzzy_match(vendor_code, client_vendors, threshold=0.70)
  328:                             vendor_code=vendor_code, vendor_key=matched_vendor["vendor_key"],
  338:                 fuzzy_results = fuzzy_match(vendor_code, firm_vendors, threshold=0.70)
  347:                             vendor_code=vendor_code, vendor_key=matched_vendor["vendor_key"],
  356:             ai_result = self._ai_suggest(vendor_code, client_id, supplier_name,
  362:                     vendor_code=vendor_code, suggested_code=ai_result.get("code"),
  365:                     matched_vendor=vendor_code, needs_review=True
  372:             vendor_code=vendor_code, confidence="none", match_source="unmatched", needs_review=True
  375:     def _ai_suggest(self, vendor_key: str, client_id: str,
  383:             vendor_key: Normalised vendor name. It is a lookup key, built to be
  385:                 extract_vendor_key() keeps only the first word once more than two
  471:                 f'Supplier as it appeared on the receipt: "{supplier_name or vendor_key}"',
  472:                 f'Normalised lookup key: "{vendor_key}"',
  517:                     logger.info(f"AI categorised {vendor_key} -> {code} {name}")
  520:             logger.warning(f"AI response invalid for {vendor_key}")
  524:             logger.warning(f"AI categorisation failed for {vendor_key}: {e}")
  528:                              vendor_key: str, nominal_code: str, account_name: str):
  532:         if not self.repo or not vendor_key:
  539:             client_id=client_id, vendor_key=vendor_key,
  545:         existing_firm = self.repo.get_firm_vendor(business_type, vendor_key)
  561:                 business_type=business_type, vendor_code=vendor_key,
  567:             self.repo.increment_firm_vendor_count(business_type, vendor_key)
##############################################################################
worker/database/repository.py (47 lines)
  332:     def get_client_vendor(self, client_id: str, vendor_code: str) -> Optional[dict]:
  335:             SELECT vendor_key, nominal_code, account_name, vendor_name, times_seen
  337:             WHERE client_id = ? AND vendor_code = ?
  340:         """, (client_id, vendor_code)).fetchone()
  343:     def upsert_client_vendor(self, client_id: str, vendor_code: str,
  346:         """Insert or update client vendor mapping. Each variant (vendor_name) gets unique vendor_key."""
  349:             SELECT vendor_key FROM categorisations_client_vendors
  350:             WHERE client_id = ? AND vendor_code = ? AND vendor_name = ?
  351:         """, (client_id, vendor_code, vendor_name)).fetchone()
  358:                 WHERE vendor_key = ?
  359:             """, (nominal_code, account_name, detail, last_updated, existing["vendor_key"]))
  362:             vendor_key = str(uuid.uuid4())
  365:                     (vendor_key, client_id, vendor_code, nominal_code, account_name, vendor_name, detail, times_seen, last_updated)
  367:             """, (vendor_key, client_id, vendor_code, nominal_code, account_name, vendor_name, detail, last_updated))
  372:         """Get distinct vendor_codes for a client for fuzzy matching candidates."""
  374:             "SELECT DISTINCT vendor_code FROM categorisations_client_vendors WHERE client_id = ?",
  377:         return [row["vendor_code"] for row in rows]
  379:     def get_firm_vendor(self, business_type: str, vendor_code: str) -> Optional[dict]:
  382:             SELECT vendor_key, nominal_code, account_name, vendor_name, times_seen
  384:             WHERE business_type = ? AND vendor_code = ?
  387:         """, (business_type, vendor_code)).fetchone()
  390:     def upsert_firm_vendor(self, business_type: str, vendor_code: str,
  393:         """Insert or update firm vendor mapping. Each variant gets unique vendor_key.
  406:             SELECT vendor_key FROM categorisations_firm_vendors
  407:             WHERE business_type = ? AND vendor_code = ? AND vendor_name = ?
  408:         """, (business_type, vendor_code, vendor_name)).fetchone()
  415:                 WHERE vendor_key = ?
  416:             """, (nominal_code, account_name, last_updated, existing["vendor_key"]))
  419:             vendor_key = str(uuid.uuid4())
  422:                     (vendor_key, business_type, vendor_code, nominal_code, account_name, vendor_name, times_seen, last_updated, firm_id)
  424:             """, (vendor_key, business_type, vendor_code, nominal_code, account_name, vendor_name, last_updated, firm_id))
  429:         """Get distinct vendor_codes for a business type for fuzzy matching candidates."""
  431:             "SELECT DISTINCT vendor_code FROM categorisations_firm_vendors WHERE business_type = ?",
  434:         return [row["vendor_code"] for row in rows]
  436:     def increment_firm_vendor_count(self, business_type: str, vendor_code: str):
  440:             SELECT vendor_key FROM categorisations_firm_vendors
  441:             WHERE business_type = ? AND vendor_code = ?
  444:         """, (business_type, vendor_code)).fetchone()
  448:                 "UPDATE categorisations_firm_vendors SET times_seen = times_seen + 1 WHERE vendor_key = ?",
  449:                 (row["vendor_key"],)
  455:                            vendor_key: Optional[str], suggested_code: Optional[str],
  470:                  vendor_key, suggested_code, suggested_name, confidence, match_source,
  474:               vendor_key, suggested_code, suggested_name, confidence, match_source,
  535:             SELECT rule_id, rule_name, priority, vendor_code, condition_type,
  544:                          priority: int, vendor_code: str, condition_type: str,
  551:                 (rule_id, client_id, rule_name, priority, vendor_code, condition_type,
  554:         """, (rule_id, client_id, rule_name, priority, vendor_code, condition_type,
##############################################################################
worker/database/schema.py (12 lines)
   10:             vendor_key              TEXT PRIMARY KEY,
   12:             vendor_code             TEXT NOT NULL,
   24:             UNIQUE(business_type, vendor_code, vendor_name)
   27:         CREATE INDEX IF NOT EXISTS idx_firm_vendor_code
   28:             ON categorisations_firm_vendors(business_type, vendor_code);
   31:             vendor_key              TEXT PRIMARY KEY,
   33:             vendor_code             TEXT NOT NULL,
   40:             UNIQUE(client_id, vendor_code, vendor_name)
   43:         CREATE INDEX IF NOT EXISTS idx_client_vendor_code
   44:             ON categorisations_client_vendors(client_id, vendor_code);
   51:             vendor_code             TEXT,
   66:             vendor_key              TEXT,
##############################################################################
worker/extraction_pipeline.py (1 lines)
  266:             vendor_key=categorisation.vendor_key,
##############################################################################
worker/resolution/service.py (17 lines)
  544: def _record_vendor_learned(repo, receipt_id, extraction_id, client_id, vendor_code,
  580:             "vendor_code": vendor_code,
  588:             f"the operator ticked remember this supplier, and {vendor_code} now maps "
  820:             vendor_key=categorisation.vendor_key,
  893:             vendor_code = getattr(categorisation, "vendor_code", None)
  894:             if vendor_code:
  897:                     vendor_code=vendor_code,
  906:                     "returned no vendor_code, so nothing was learned"
 1303:             vendor_key=categorisation.vendor_key,
 1344:             # `vendor_code` and not `vendor_key`. The column this writes holds the
 1345:             # normalised merchant code that layer 1 looks up; `vendor_key` is the
 1348:             vendor_code = categorisation.vendor_code
 1349:             if vendor_code:
 1352:                     vendor_code=vendor_code,
 1361:                     vendor_code=vendor_code,
 1367:                     f"learned {vendor_code} -> {code} {category_name} for client "
 1373:                     "returned no vendor_code, so nothing was learned"
```

## Appendix B. The enumeration, after

```
PY FILES SCANNED (tracked + untracked, gitignored excluded): 104
FILES WITH HITS: 22  TOTAL LINES: 250
##############################################################################
migrate_2026_09_06_vendor_key_naming.py (6 lines)
    1: """One-off migration for the vendor_key / vendor_code naming correction.
   12:     including the one that proves 10j.11 works. Its `vendor_key` column is NULL
   52:         if "vendor_key" in cols:
   54:                 "ALTER TABLE categorisations RENAME COLUMN vendor_key TO mapping_id"
   56:             print("renamed categorisations.vendor_key -> mapping_id")
   58:             print("categorisations.vendor_key already gone, nothing renamed")
##############################################################################
tests/test_vendor_key_naming.py (28 lines)
    4: `suggested_code`, `correction_code`. `vendor_code` was the one place it did not:
    6: `extract_vendor_key()`. That is a key, and the code already had a name for it.
    8: And in the two learned tables the names were the wrong way round, so `vendor_key`
    9: held a row UUID while `vendor_code` held the key. The correction:
   11:   * the normalised key is `vendor_key`, everywhere
   12:   * a learned mapping's row id is `mapping_id`, never `vendor_key`
   13:   * `vendor_code` does not exist
   37:         '# vendor_code on 2026-09-06: "code" means a four-digit account code',
   41:         "# normalised key was called `vendor_code` and is now called",
   47:     def test_vendor_code_appears_nowhere_in_worker_but_the_named_survivors(self):
   54:                 if "vendor_code" not in line:
   61:             "vendor_code survives somewhere it is not allowed to: "
   90:     def test_the_learned_tables_are_keyed_on_mapping_id(self):
   93:                 self.assertEqual(self._primary_key(table), ["mapping_id"])
   94:                 self.assertIn("vendor_key", self._columns(table))
   95:                 self.assertNotIn("vendor_code", self._columns(table))
   97:     def test_rules_match_on_a_vendor_key(self):
   99:         self.assertIn("vendor_key", columns)
  100:         self.assertNotIn("vendor_code", columns)
  102:     def test_categorisations_points_at_a_mapping_id(self):
  104:         # mapping_id. It is not the normalised key and never was.
  106:         self.assertIn("mapping_id", columns)
  107:         self.assertNotIn("vendor_key", columns)
  108:         self.assertNotIn("vendor_code", columns)
  112:         self.assertIn("vendor_key", fields)
  113:         self.assertIn("mapping_id", fields)
  114:         self.assertNotIn("vendor_code", fields)
  120:     It passed `vendor_key=` to a method taking `vendor_code` and would have
##############################################################################
app.py (1 lines)
  505:                 mapping_id=categorisation.mapping_id,
##############################################################################
docs/specs/categorisation_engine.py (42 lines)
  142: def extract_vendor_key(normalised: str, aliases: dict = None) -> str:
  304:             vendor_key = extract_vendor_key(normalised, self.aliases)
  306:             if not vendor_key:
  310:                 vendor=vendor_key,
  316:             if vendor_key in self.client_lookup:
  317:                 self.client_lookup[vendor_key].times_seen += 1
  318:                 self.client_lookup[vendor_key].last_updated = datetime.now().isoformat()
  320:                 self.client_lookup[vendor_key] = mapping
  324:             if vendor_key not in self.firm_lookup:
  325:                 self.firm_lookup[vendor_key] = VendorMapping(
  326:                     vendor=vendor_key,
  331:                 self.firm_lookup[vendor_key].times_seen += 1
  342:         vendor_key = extract_vendor_key(normalised, self.aliases)
  344:         if not vendor_key:
  353:         if vendor_key in self.client_lookup:
  354:             m = self.client_lookup[vendor_key]
  366:         if vendor_key in self.firm_lookup:
  367:             m = self.firm_lookup[vendor_key]
  380:             vendor_key, list(self.client_lookup.keys()), threshold=0.70
  397:             vendor_key, list(self.firm_lookup.keys()), threshold=0.70
  445:         vendor_key = extract_vendor_key(normalised, self.aliases)
  447:         if not vendor_key:
  453:         if vendor_key in self.client_lookup:
  454:             self.client_lookup[vendor_key].nominal_code = nominal_code
  455:             self.client_lookup[vendor_key].account_name = account_name
  456:             self.client_lookup[vendor_key].times_seen += 1
  457:             self.client_lookup[vendor_key].last_updated = now
  459:             self.client_lookup[vendor_key] = VendorMapping(
  460:                 vendor=vendor_key,
  468:             if vendor_key not in self.firm_lookup:
  469:                 self.firm_lookup[vendor_key] = VendorMapping(
  470:                     vendor=vendor_key,
  477:                 if self.firm_lookup[vendor_key].nominal_code == nominal_code:
  478:                     self.firm_lookup[vendor_key].times_seen += 1
  479:                     self.firm_lookup[vendor_key].last_updated = now
  484:         self._append_history(txn, vendor_key, nominal_code, account_name)
  489:     def _append_history(self, txn: Transaction, vendor_key: str,
  504:             "vendor_key": vendor_key,
  545:         for vendor_key, firm_mapping in self.firm_lookup.items():
  546:             if vendor_key in self.client_lookup:
  547:                 client_mapping = self.client_lookup[vendor_key]
  555:                         "vendor": vendor_key,
##############################################################################
import_vendor_csv.py (9 lines)
    4: CSV format: vendor_key,vendor_name,detail,nominal_code,account_name
    5: A file with the older `vendor_code` header is still read: the column was
   31:                 # Three header spellings, oldest last. `vendor_code` was the
   33:                 vendor_key = row.get('vendor_key') or row.get('vendor_code')
   34:                 if not vendor_key:
   38:                 vendor_key = vendor_key.strip()
   44:                 if not vendor_key or not nominal_code:
   51:                         vendor_key=vendor_key,
   59:                     print(f"[+] {vendor_key:30} -> {nominal_code} {account_name}")
##############################################################################
probe_layer5.py (1 lines)
  107:                 f"  {label}  vendor_key={res.vendor_key!r}  "
##############################################################################
regenerate_vendor_codes.py (14 lines)
    2: Regenerate vendor_key from vendor_name using engine normalization logic.
    3: The header was `vendor_code` until 2026-09-06; a file still carrying it is
   49: def extract_vendor_key(normalised: str, aliases: dict = None) -> str:
   71:     """Regenerate vendor_keys from vendor_names."""
   92:         new_code = extract_vendor_key(normalised, DEFAULT_ALIASES)
   94:         old_code = row.get('vendor_key') or row.get('vendor_code') or ''
  104:         row['vendor_key'] = new_code
  108:     fieldnames = ['vendor_key', 'vendor_name', 'detail', 'nominal_code', 'account_name']
  116:     print(f"Unique vendor_keys: {len(code_map)}")
  149:         new_code = extract_vendor_key(normalised, DEFAULT_ALIASES)
  150:         old_code = row.get('vendor_key') or row.get('vendor_code') or ''
  159:         row['vendor_key'] = new_code
  163:     fieldnames = ['vendor_key', 'vendor_name', 'detail', 'nominal_code', 'account_name']
  171:     print(f"Unique vendor_keys: {len(code_map)}")
##############################################################################
retroactive_categorise.py (1 lines)
  159:                     mapping_id=categorisation.mapping_id,
##############################################################################
seed_client_vendors.py (7 lines)
   54: def extract_vendor_key(normalised: str, aliases: dict = None) -> str:
  120:             vendor_keys_seen = set()
  140:                 vendor_key = extract_vendor_key(normalised)
  143:                 if not vendor_key or vendor_key in vendor_keys_seen:
  147:                 vendor_keys_seen.add(vendor_key)
  152:                     vendor_key=vendor_key,
  160:                 print(f"[+] {client_id} | {vendor_key:20} | {detail:40} -> {gl_code}")
##############################################################################
tests/test_desktop_learning.py (12 lines)
   22: return the learned code. The second is what proves `vendor_key` and not
   23: `mapping_id` is the right thing to write, because `vendor_key` is what layer 1
   25: same thing under the old names, `vendor_code` and `vendor_key`.
  352:     def test_what_is_written_is_the_vendor_key_layer_one_looks_up(self):
  353:         # Not the mapping_id, which is the row id of a mapping that
  383:         # at layer 1 in engine.py, so that `vendor_key` carried the row id and
  384:         # `mapping_id` carried the normalised key, turned the whole suite green.
  389:         self.assertEqual(categorisation["mapping_id"], learned[0]["mapping_id"])
  390:         self.assertEqual(learned[0]["vendor_key"], "apcoa parking",
  492:         # The blob's key was `vendor_code` until 2026-09-06 and nothing asserted
  495:         self.assertEqual(recorded["vendor_key"], "apcoa parking")
  496:         self.assertNotIn("vendor_code", recorded)
##############################################################################
tests/test_fallback_accounts.py (1 lines)
  271:         business_type="UNSPECIFIED", vendor_key="canary",
##############################################################################
tests/test_resolution_service.py (1 lines)
  422:             client_id="CLIENT001", vendor_key="apcoa parking",
##############################################################################
tests/test_resolution_view.py (3 lines)
  195:                     mapping_id=None,
  298:                     client_id="CLIENT001", vendor_key="apcoa parking",
  303:                     business_type="PHV_DRIVER", vendor_key="shell",
##############################################################################
tests/test_retroactive_categorise_sidecar.py (2 lines)
  156:                     vendor_key="apcoa parking",
  186:                     mapping_id=None,
##############################################################################
tests/test_sidecar_category_keys.py (3 lines)
  120:     def seed_mapping(self, repo, vendor_key="apcoa parking", code="271", name="Parking and tolls"):
  121:         # vendor_key is normalise_description("Apcoa Parking"), which is what
  125:             vendor_key=vendor_key,
##############################################################################
tests/test_step10d_pipeline.py (2 lines)
  296:         self.assertIn("UNIQUE(business_type, vendor_key, vendor_name)", sql)
  297:         self.assertNotIn("UNIQUE(business_type, vendor_key, vendor_name, firm_id)", sql)
##############################################################################
tests/test_vendor_import_requires_client_id.py (3 lines)
   30: # The header is deliberately the older `vendor_code` spelling. The column was
   31: # renamed to `vendor_key` on 2026-09-06 and import_vendor_csv.py still reads
   34: IMPORT_CSV = """vendor_code,vendor_name,detail,nominal_code,account_name
##############################################################################
worker/categorisation/engine.py (34 lines)
  105:     # vendor_code on 2026-09-06: "code" means a four-digit account code
  107:     vendor_key: Optional[str] = None
  109:     # matched. Renamed from vendor_key on the same day, which is the half of
  111:     mapping_id: Optional[str] = None
  150: def extract_vendor_key(normalised: str, aliases: dict = None) -> str:
  214:     def _rule_matches(self, rule: dict, vendor_key: str, detail: str) -> bool:
  217:         if rule.get("vendor_key") and rule["vendor_key"] != vendor_key:
  226:         field_value = detail.lower() if condition_field == "detail" else vendor_key.lower()
  273:         vendor_key = extract_vendor_key(normalised, self.aliases)
  275:         if not vendor_key:
  286:                 if self._rule_matches(rule, vendor_key, supplier_name):
  290:                         vendor_key=vendor_key, suggested_code=rule["nominal_code"],
  298:             client_vendor = self.repo.get_client_vendor(client_id, vendor_key)
  303:                     vendor_key=vendor_key, mapping_id=client_vendor["mapping_id"],
  307:                     matched_vendor=vendor_key, needs_review=False
  311:             firm_vendor = self.repo.get_firm_vendor(business_type, vendor_key)
  316:                     vendor_key=vendor_key, mapping_id=firm_vendor["mapping_id"],
  320:                     matched_vendor=vendor_key, needs_review=False
  326:                 fuzzy_results = fuzzy_match(vendor_key, client_vendors, threshold=0.70)
  335:                             vendor_key=vendor_key, mapping_id=matched_vendor["mapping_id"],
  345:                 fuzzy_results = fuzzy_match(vendor_key, firm_vendors, threshold=0.70)
  354:                             vendor_key=vendor_key, mapping_id=matched_vendor["mapping_id"],
  363:             ai_result = self._ai_suggest(vendor_key, client_id, supplier_name,
  369:                     vendor_key=vendor_key, suggested_code=ai_result.get("code"),
  372:                     matched_vendor=vendor_key, needs_review=True
  379:             vendor_key=vendor_key, confidence="none", match_source="unmatched", needs_review=True
  382:     def _ai_suggest(self, vendor_key: str, client_id: str,
  390:             vendor_key: Normalised vendor name. It is a lookup key, built to be
  392:                 extract_vendor_key() keeps only the first word once more than two
  478:                 f'Supplier as it appeared on the receipt: "{supplier_name or vendor_key}"',
  479:                 f'Normalised lookup key: "{vendor_key}"',
  524:                     logger.info(f"AI categorised {vendor_key} -> {code} {name}")
  527:             logger.warning(f"AI response invalid for {vendor_key}")
  531:             logger.warning(f"AI categorisation failed for {vendor_key}: {e}")
##############################################################################
worker/database/repository.py (47 lines)
  332:     def get_client_vendor(self, client_id: str, vendor_key: str) -> Optional[dict]:
  335:             SELECT mapping_id, nominal_code, account_name, vendor_name, times_seen
  337:             WHERE client_id = ? AND vendor_key = ?
  340:         """, (client_id, vendor_key)).fetchone()
  343:     def upsert_client_vendor(self, client_id: str, vendor_key: str,
  346:         """Insert or update client vendor mapping. Each variant (vendor_name) gets unique mapping_id."""
  349:             SELECT mapping_id FROM categorisations_client_vendors
  350:             WHERE client_id = ? AND vendor_key = ? AND vendor_name = ?
  351:         """, (client_id, vendor_key, vendor_name)).fetchone()
  358:                 WHERE mapping_id = ?
  359:             """, (nominal_code, account_name, detail, last_updated, existing["mapping_id"]))
  362:             mapping_id = str(uuid.uuid4())
  365:                     (mapping_id, client_id, vendor_key, nominal_code, account_name, vendor_name, detail, times_seen, last_updated)
  367:             """, (mapping_id, client_id, vendor_key, nominal_code, account_name, vendor_name, detail, last_updated))
  372:         """Get distinct vendor_keys for a client for fuzzy matching candidates."""
  374:             "SELECT DISTINCT vendor_key FROM categorisations_client_vendors WHERE client_id = ?",
  377:         return [row["vendor_key"] for row in rows]
  379:     def get_firm_vendor(self, business_type: str, vendor_key: str) -> Optional[dict]:
  382:             SELECT mapping_id, nominal_code, account_name, vendor_name, times_seen
  384:             WHERE business_type = ? AND vendor_key = ?
  387:         """, (business_type, vendor_key)).fetchone()
  390:     def upsert_firm_vendor(self, business_type: str, vendor_key: str,
  393:         """Insert or update firm vendor mapping. Each variant gets unique mapping_id.
  406:             SELECT mapping_id FROM categorisations_firm_vendors
  407:             WHERE business_type = ? AND vendor_key = ? AND vendor_name = ?
  408:         """, (business_type, vendor_key, vendor_name)).fetchone()
  415:                 WHERE mapping_id = ?
  416:             """, (nominal_code, account_name, last_updated, existing["mapping_id"]))
  419:             mapping_id = str(uuid.uuid4())
  422:                     (mapping_id, business_type, vendor_key, nominal_code, account_name, vendor_name, times_seen, last_updated, firm_id)
  424:             """, (mapping_id, business_type, vendor_key, nominal_code, account_name, vendor_name, last_updated, firm_id))
  429:         """Get distinct vendor_keys for a business type for fuzzy matching candidates."""
  431:             "SELECT DISTINCT vendor_key FROM categorisations_firm_vendors WHERE business_type = ?",
  434:         return [row["vendor_key"] for row in rows]
  436:     def increment_firm_vendor_count(self, business_type: str, vendor_key: str):
  440:             SELECT mapping_id FROM categorisations_firm_vendors
  441:             WHERE business_type = ? AND vendor_key = ?
  444:         """, (business_type, vendor_key)).fetchone()
  448:                 "UPDATE categorisations_firm_vendors SET times_seen = times_seen + 1 WHERE mapping_id = ?",
  449:                 (row["mapping_id"],)
  455:                            mapping_id: Optional[str], suggested_code: Optional[str],
  470:                  mapping_id, suggested_code, suggested_name, confidence, match_source,
  474:               mapping_id, suggested_code, suggested_name, confidence, match_source,
  535:             SELECT rule_id, rule_name, priority, vendor_key, condition_type,
  544:                          priority: int, vendor_key: str, condition_type: str,
  551:                 (rule_id, client_id, rule_name, priority, vendor_key, condition_type,
  554:         """, (rule_id, client_id, rule_name, priority, vendor_key, condition_type,
##############################################################################
worker/database/schema.py (12 lines)
   10:             mapping_id              TEXT PRIMARY KEY,
   12:             vendor_key              TEXT NOT NULL,
   24:             UNIQUE(business_type, vendor_key, vendor_name)
   27:         CREATE INDEX IF NOT EXISTS idx_firm_vendor_key
   28:             ON categorisations_firm_vendors(business_type, vendor_key);
   31:             mapping_id              TEXT PRIMARY KEY,
   33:             vendor_key              TEXT NOT NULL,
   40:             UNIQUE(client_id, vendor_key, vendor_name)
   43:         CREATE INDEX IF NOT EXISTS idx_client_vendor_key
   44:             ON categorisations_client_vendors(client_id, vendor_key);
   51:             vendor_key              TEXT,
   66:             mapping_id              TEXT,
##############################################################################
worker/extraction_pipeline.py (1 lines)
  266:             mapping_id=categorisation.mapping_id,
##############################################################################
worker/resolution/service.py (20 lines)
  544: def _record_vendor_learned(repo, receipt_id, extraction_id, client_id, vendor_key,
  580:             "vendor_key": vendor_key,
  588:             f"the operator ticked remember this supplier, and {vendor_key} now maps "
  820:             mapping_id=categorisation.mapping_id,
  893:             vendor_key = getattr(categorisation, "vendor_key", None)
  894:             if vendor_key:
  897:                     vendor_key=vendor_key,
  906:                     "returned no vendor_key, so nothing was learned"
 1303:             mapping_id=categorisation.mapping_id,
 1344:             # `vendor_key` and not `mapping_id`. What this writes is the
 1345:             # normalised merchant key that layer 1 looks up; `mapping_id` is the
 1351:             # normalised key was called `vendor_code` and is now called
 1352:             # `vendor_key`, and the field holding the row id was called
 1353:             # `vendor_key` and is now called `mapping_id`.
 1354:             vendor_key = categorisation.vendor_key
 1355:             if vendor_key:
 1358:                     vendor_key=vendor_key,
 1367:                     vendor_key=vendor_key,
 1373:                     f"learned {vendor_key} -> {code} {category_name} for client "
 1379:                     "returned no vendor_key, so nothing was learned"
```

## Appendix C. `PRAGMA table_info` after the change

```
### WHAT schema.py NOW CREATES (in-memory, no live database touched)
======================================================================
categorisations_client_vendors
   (0, 'mapping_id', 'TEXT', 0, None, 1)
   (1, 'client_id', 'TEXT', 1, None, 0)
   (2, 'vendor_key', 'TEXT', 1, None, 0)
   (3, 'nominal_code', 'TEXT', 1, None, 0)
   (4, 'account_name', 'TEXT', 1, None, 0)
   (5, 'vendor_name', 'TEXT', 0, None, 0)
   (6, 'detail', 'TEXT', 0, None, 0)
   (7, 'times_seen', 'INTEGER', 0, '1', 0)
   (8, 'last_updated', 'TEXT', 1, None, 0)
======================================================================
categorisations_firm_vendors
   (0, 'mapping_id', 'TEXT', 0, None, 1)
   (1, 'business_type', 'TEXT', 1, None, 0)
   (2, 'vendor_key', 'TEXT', 1, None, 0)
   (3, 'nominal_code', 'TEXT', 1, None, 0)
   (4, 'account_name', 'TEXT', 1, None, 0)
   (5, 'vendor_name', 'TEXT', 0, None, 0)
   (6, 'times_seen', 'INTEGER', 0, '1', 0)
   (7, 'last_updated', 'TEXT', 1, None, 0)
   (8, 'firm_id', 'TEXT', 0, None, 0)
======================================================================
categorisations_client_rules
   (0, 'rule_id', 'TEXT', 0, None, 1)
   (1, 'client_id', 'TEXT', 1, None, 0)
   (2, 'rule_name', 'TEXT', 1, None, 0)
   (3, 'priority', 'INTEGER', 1, '50', 0)
   (4, 'vendor_key', 'TEXT', 0, None, 0)
   (5, 'condition_type', 'TEXT', 1, None, 0)
   (6, 'condition_field', 'TEXT', 1, None, 0)
   (7, 'condition_value', 'TEXT', 1, None, 0)
   (8, 'nominal_code', 'TEXT', 1, None, 0)
   (9, 'account_name', 'TEXT', 1, None, 0)
   (10, 'created_at', 'TEXT', 1, None, 0)
======================================================================
categorisations
   (0, 'categorisation_id', 'TEXT', 0, None, 1)
   (1, 'receipt_id', 'TEXT', 1, None, 0)
   (2, 'extraction_id', 'TEXT', 1, None, 0)
   (3, 'client_id', 'TEXT', 1, None, 0)
   (4, 'trade', 'TEXT', 1, None, 0)
   (5, 'mapping_id', 'TEXT', 0, None, 0)
   (6, 'suggested_code', 'TEXT', 0, None, 0)
   (7, 'suggested_name', 'TEXT', 0, None, 0)
   (8, 'confidence', 'TEXT', 1, None, 0)
   (9, 'match_source', 'TEXT', 1, None, 0)
   (10, 'matched_vendor', 'TEXT', 0, None, 0)
   (11, 'needs_review', 'INTEGER', 0, '1', 0)
   (12, 'categorised_at', 'TEXT', 1, None, 0)
   (13, 'corrected_at', 'TEXT', 0, None, 0)
   (14, 'correction_code', 'TEXT', 0, None, 0)
   (15, 'correction_name', 'TEXT', 0, None, 0)
   (16, 'correction_reason', 'TEXT', 0, None, 0)
======================================================================
indexes:
   ('idx_firm_vendor_key', 'categorisations_firm_vendors')
   ('idx_client_vendor_key', 'categorisations_client_vendors')

### THE LIVE DATABASE, unchanged: the migration was blocked
  categorisations_client_vendors     1 rows  ['vendor_key', 'client_id', 'vendor_code', 'nominal_code', 'account_name', 'vendor_name', 'detail', 'times_seen', 'last_updated']
  categorisations_firm_vendors       0 rows  ['vendor_key', 'business_type', 'vendor_code', 'nominal_code', 'account_name', 'vendor_name', 'times_seen', 'last_updated', 'firm_id']
  categorisations_client_rules       0 rows  ['rule_id', 'client_id', 'rule_name', 'priority', 'vendor_code', 'condition_type', 'condition_field', 'condition_value', 'nominal_code', 'account_name', 'created_at']
  categorisations                    11 rows  ['categorisation_id', 'receipt_id', 'extraction_id', 'client_id', 'trade', 'vendor_key', 'suggested_code', 'suggested_name', 'confidence', 'match_source', 'matched_vendor', 'needs_review', 'categorised_at', 'corrected_at', 'correction_code', 'correction_name', 'correction_reason']
```

---

## 9. Flag 3, closed 2026-09-06 on Paul's answer

**The plain attribute read is the form kept.** `resolve_receipt():893` now reads
`categorisation.vendor_key`, which is what `_apply_filed_note()` already did.

### Why that form and not the `getattr`

**The `getattr` default could never fire.** Three reasons, each checked rather
than assumed:

1. `categorisation` is bound at `service.py:791` from
   `categorisation_engine.categorise()`, which returns a `CategorisationResult`
   on every one of its seven return paths.
2. It is passed through `resolve_against_chart()` at `:812`, and that function
   returns the object it was given: `worker\categorisation\fallback.py` returns
   `result` at `:244`, `:272` and `:276`, and constructs nothing.
3. `vendor_key` is a declared dataclass field with a default of `None`, so the
   attribute always exists. **And `resolve_receipt()` already reads eight
   attributes off that same object directly, at `:819` to `:826`, before it ever
   reaches line 893.** A missing attribute would have raised at the first of
   them.

**What the default could do is swallow a rename**, which is the failure the
whole naming brief existed to correct, sitting in the code that does the
learning.

### What the change actually buys, measured rather than asserted

**Isolated mutation: rename the field out from under the read only, leaving
everything else alone, and run the one test that asserts learning happens,
`test_resolution_service.py::RememberMappingTest::test_opt_in_on_learns_the_mapping`.**

| Form | What the failure says |
|---|---|
| **Old**, `getattr(categorisation, "vendor_kee", None)` | `AssertionError: 0 != 1` |
| **New**, `categorisation.vendor_kee` | `AttributeError: 'CategorisationResult' object has no attribute 'vendor_kee'. Did you mean: 'vendor_key'?` |

**Both are caught, so this is not a difference between passing and failing.** It
is a difference between a failure that says "no rows were learned" and one that
names the field and suggests the right spelling. **The old form was not silent
in the suite; it was silent about the cause.**

**Nothing can crash the pipeline either way.** Both learning branches sit inside
a broad handler, `service.py:945` for `resolve_receipt()` and `:1433` for
`apply_resolution_note()`. Each logs the traceback with `exc_info=True` and
returns an `error` outcome with a message safe to render. So a raise fails one
receipt loudly and logs why, rather than taking the run down.

**In production the two forms are identical**, because the attribute is always
there. The difference exists only once somebody has broken something.

### Evidence

**Red before green.** Both new tests were written first and both failed against
the unchanged code:

```
AssertionError: Lists differ:
  ['893: vendor_key = getattr(categorisation, "vendor_key", None)'] != []

AssertionError: Lists differ:
  ['vendor_key = getattr(categorisation, "vendor_key", None)',
   'vendor_key = categorisation.vendor_key']
  != ['vendor_key = categorisation.vendor_key',
      'vendor_key = categorisation.vendor_key']
```

**The guard:** `tests\test_vendor_key_naming.py::TheTwoLearningBranchesReadTheFieldTheSameWay`,
two tests. One asserts no live line in `service.py` reaches the categorisation
through `getattr`. The other asserts both branches read it with the identical
expression, so they cannot drift apart again without a test going red.

**Mutation E, putting the `getattr` back exactly as it was:**

```
2 failed, 522 passed, 330 subtests passed
  TheTwoLearningBranchesReadTheFieldTheSameWay::test_both_branches_read_it_as_a_plain_attribute
  TheTwoLearningBranchesReadTheFieldTheSameWay::test_neither_branch_reaches_the_field_through_getattr
```

**Two tests, and they are the two that exist for it.**

**The suite:** 522 passed, 330 subtests before this change. **524 passed, 330
subtests after.** Zero skips.

### Two disclosures

- **My first version of the guard failed after the fix was already correct.** It
  searched for the string `getattr(categorisation` across the whole file and hit
  the comment I had just written explaining the old form. Comment lines are now
  skipped, the same way the `vendor_code` allowlist in section 6.4 keeps two
  comments that name the old field. The second test, which compares the two
  reads exactly, is what stops that skip being a loophole.
- **My first failure message printed the entire 1,500-line module** into the
  test output, because `assertNotIn` against a whole file prints the haystack.
  It now reports the matching lines with their numbers.

### Not done, and not asked for

**`_apply_filed_note()` was not touched.** It already read the field as a plain
attribute. The change is one line of code in one branch, plus its comment.

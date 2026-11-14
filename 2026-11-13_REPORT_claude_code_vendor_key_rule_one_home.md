# Report: the vendor key rule has one home

Written 2026-11-13 by Claude Code, for the consultant session. It implements
Paul's decision of 2026-11-13: the copies of the key rule in
`seed_client_vendors.py` and `regenerate_vendor_codes.py` go, and both
scripts use the engine's.

`2026-07-25_BUILD_STATUS.md` is not touched.

---

## 1. What was done

One commit, `13ab225`, on `feat/console-phase0`. Five files:

| File | Change |
|---|---|
| `worker\categorisation\normalise.py` | New. `NOISE_WORDS`, `LOCATION_WORDS`, `DEFAULT_ALIASES`, `normalise_description()`, `extract_vendor_key()`, moved verbatim from `engine.py`. Imports only `re` |
| `worker\categorisation\engine.py` | The five definitions replaced by one import from `.normalise` |
| `seed_client_vendors.py` | Its copy deleted; imports the two functions from `normalise`; unused `import re` removed |
| `regenerate_vendor_codes.py` | Its copy deleted; imports the two functions and `DEFAULT_ALIASES` from `normalise`; unused `import re` removed |
| `tests\test_vendor_key_rule_has_one_home.py` | New, 10 tests |

**The move is verbatim.** The script that did it sliced the two blocks out of
`engine.py` by line, asserted each boundary, and checked that all five
definitions in the new module are identical to the originals at the
syntax-tree level. All five reported identical. **The engine's behaviour does
not change**, and `engine.NOISE_WORDS` and the rest are the same objects as
`normalise.NOISE_WORDS`; a test asserts identity. So every existing
`from worker.categorisation.engine import NOISE_WORDS` still works and still
gets the one list.

**The scripts' behaviour does change, deliberately.** Each now computes the
engine's key. For the seed script that is a large change; see section 4.

---

## 2. How the copies were removed without pulling in openai, and what I rejected

**The copies existed because importing the engine has side effects.** Read in
`engine.py`'s import block:

- `import config`: on Windows, importing `config` runs its folder creation
  against the practice root. `CLAUDE.md` records this as a trap.
- `from openai import OpenAI`, guarded by `try/except ImportError`. So a
  missing package is not fatal, but the client library is loaded whenever it
  is installed.
- `pydantic`, `worker.line_items`, `receipt_accounts`.

`regenerate_vendor_codes.py` imported nothing from the repository at all: it
is a CSV-to-CSV transform. `seed_client_vendors.py` imports `config` and the
repository by design, because it writes to the database.

**Chosen: move the pure rule into its own module, `worker\categorisation\normalise.py`.**
It sits beside the engine in the package that owns categorisation, and
imports nothing but `re`. The engine imports from it, so there is one
definition. The scripts import from it, so they get the rule and nothing
else. A test imports the module in a fresh interpreter and asserts that
neither `openai`, `config` nor the engine is loaded. Two more tests assert,
the same way, that the regenerate script loads neither `config` nor `openai`
and the seed script does not load `openai`.

**Rejected:**

- **Importing the engine at the top of each script.** It removes the copies
  and brings in `config` and the `openai` client. For the regenerate script,
  `config` is a regression: a pure CSV transform would start creating
  folders under the practice root. Three tests that pass with the chosen
  method would fail with this one, and they were written before the change
  so they could tell the two apart.
- **A lazy import inside the function, as `worker\resolution\service.py`
  does.** I read it. `_the_original_suggestion()` imports
  `CategorisationResult` inside the function, and its comment gives the
  reason: "Every caller has already built an engine by the time this runs,
  so the module is loaded already and nothing new arrives". That works for
  the service because its caller has already loaded the engine. A
  standalone script has no such caller, so a lazy import would load `config`
  and `openai` at the moment the key is first computed. That is the same
  side effect, only later. The service's approach solves the import-time
  layering rule it was written for, not a script's need to avoid the module
  altogether.
- **Keeping the copies and adding a test that compares them with the engine.**
  `CLAUDE.md`'s rule of 2026-09-11 names this exactly: "a recommendation
  that ADDS something to protect a thing that should not exist".
- **Archiving the scripts.** Excluded by the brief: they are the recovery
  route and step 10i has not happened.

**The test that fails first.** `test_each_script_computes_the_engines_key`,
before the change:

- seed, `Gatwick Drop Off Crawley Gb`: `'gatwick drop off crawley gb' != 'gatwick'`
- seed, `LA BELLA RESTAURANT`: `'la bella restaurant' != 'bella restaurant'`
- seed, `IMO CAR WASH MERTON LONDON SW19 GB`: `'imo car wash merton sw19 gb' != 'imo'`
- regenerate, `LA BELLA RESTAURANT`: `'la' != 'bella restaurant'`

The module tests failed with `ModuleNotFoundError`, and the copy and import
tests failed naming the five definitions in each script. **Three tests passed
before the change and were meant to**: the regenerate script imports no
`config`, the seed script loads no `openai`, and neither imports the engine.
They hold the method rather than the outcome, so the obvious wrong fix would
turn them red.

---

## 3. The three things to establish

### 3.1 The recovery CSV exists: 101 rows

`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\categorisations_client_vendors_cleaned.csv`,
read-only. **101 data rows**, 13,211 bytes, CRLF line endings, header
`vendor_code,vendor_name,detail,nominal_code,account_name`. Note it still
uses the old `vendor_code` header, and it has no `client_id` column.

**It is not the only copy.** Commit `8b1db5d` of 2026-08-01 moved it out of
the repository into that folder. The version in git at `8b1db5d^` is identical
to the file on disk once line endings are normalised; I compared them byte
for byte. So git history holds a second copy.

Beside it in the same folder:

- `categorisations_client_vendors_cleaned.csv.backup.20260507_165602`: 101
  rows, byte-identical to the CSV (same md5).
- `categorisations_client_vendors_cleaned.csv.bak`: **102 rows, header
  `vendor_key`, different content.** Not investigated. It may be the output
  of an earlier run of the regenerate script. It is worth knowing which of
  the two the build status means.
- `categorisations_firm_vendors.csv`: header only, no rows.

The build status's figures, read at line 1124 of `2026-07-25_BUILD_STATUS.md`:
100 rows for `Client_001` and one for `Client_003`, 101 in all. The CSV's 101
matches that total.

### 3.2 Every name in the CSV: each script's key now equals the engine's

Read-only, all 101 names, through `tests\live_paths.py` so `config` resolved
to a temp root. Script:
`C:\Users\PDK7\AppData\Local\Temp\claude\43687783b5645321\c06fa307-c485-4b69-9e2e-96335aeb0cf3\scratchpad\csv_keys_compare.py`.

| | Before | After |
|---|---|---|
| regenerate script's key differs from the engine's | 1 (`La Bella Restaurant ...`: `la` vs `bella`) | **0** |
| seed script's key differs from the engine's | 91 | **0** |
| key stored in the CSV differs from the engine's | 91 | 91 |

The last row does not move, because the CSV is data and this change does not
touch it. See flag 5.1: it matters.

### 3.3 No stored vendor key changes

Read-only. For all 25 rows of the two learned tables (16 client, 9 firm), the
engine's key for `vendor_name` was compared with the stored `vendor_key`,
before the change and after it. **Both runs: 25 rows, 0 differ. The two
outputs are byte-identical** (`cmp` reported no difference).
`categorisations_client_rules` holds 0 rows. Script:
`C:\Users\PDK7\AppData\Local\Temp\claude\43687783b5645321\c06fa307-c485-4b69-9e2e-96335aeb0cf3\scratchpad\stored_keys_vs_engine.py`.

---

## 4. What changes for the seed script

Its copy never had the rule keeping only the first word of a name of three or
more words. Every key it wrote was longer than the engine's for such names,
and layer 1 looks up by key, so **rows it seeded under those keys could not be
found by an exact lookup**. That is fixed for anything it seeds from now on.

**It also changes how many rows it writes.** It skips a description whose key
it has already seen under the same GL code. With long keys almost nothing
collided. With the engine's keys, variants of one supplier collide: four
Gatwick descriptions under one code now give one row. Measured on the
recovery CSV grouped by `nominal_code`, as a stand-in for the transaction
export the script really reads, which I do not have: **101 rows kept under
the old keys, 79 under the engine's.** The 22 skipped are name variants on a
key and code already written. Under 10bs.9, a key whose names all agree on a
code still answers at layer 1, so these are not lost lookups. They are lost
names, which the 10bs.10 mappings file would otherwise show at the tick. See
flag 5.2.

---

## 5. Flags

### 5.1 The recovery route as recorded restores 91 rows the engine cannot find

**The build status names `import_vendor_csv.py` and `seed_client_vendors.py`
as the recovery route from the CSV.** `import_vendor_csv.py` takes the key
from the CSV's column as it stands. 91 of the CSV's 101 keys are the seed
copy's long keys, which the engine never computes. Restoring with
`import_vendor_csv.py` alone would put 91 rows into
`categorisations_client_vendors` that layer 1 can never find by key. Only
layer 3, the fuzzy layer, could reach them, and it answers as unconfirmed.

**The obvious fix is to recompute the keys before importing.** That is what
`regenerate_vendor_codes.py` was for, and after this commit it computes the
engine's key. **But it cannot run as it is, for two reasons, both read and
one reproduced:**

- Its `__main__` block reads `categorisations_client_vendors_cleaned.csv` by
  a relative path from the working directory. The file left the repository
  on 2026-08-01, so from the repository root it raises `FileNotFoundError`.
- It writes with `csv.DictWriter` and the fieldnames
  `vendor_key, vendor_name, detail, nominal_code, account_name`. Each row
  read from the CSV still carries its `vendor_code` key, and `DictWriter`
  raises on an unknown field. **Reproduced in memory**: `ValueError: dict
  contains fields not in fieldnames: 'vendor_code'`. So against this CSV it
  fails on the first row it writes.

**The fix is small and I can do it in one commit if you want it:** take the
input and output paths as arguments, and drop `vendor_code` from each row
before writing. **Not done**: the brief said flag, and it changes a recovery
tool's behaviour. **The recorded procedure is also the consultant session's
to correct**: regenerate, then import the regenerated file. Until then, the
build status describes a route that restores unreachable rows.

### 5.2 The seed script's skip rule was written for long keys

It skips a description whose key it has seen under the same GL code. With the
engine's keys that drops name variants (section 4). **The obvious fix is to
skip on key and name together**: one line, `vendor_keys_seen` holding
`(vendor_key, detail)`. Not done: it changes what the seed writes, and
whether every variant should be stored is a 10bs.10 question about what the
operator sees at the tick.

### 5.3 A third copy of the rule

`docs\specs\categorisation_engine.py` defines its own `NOISE_WORDS`,
`DEFAULT_ALIASES` and `normalise_description()`. It is the v0.1 prototype and
nothing imports it, recorded at `tests\test_category_hold.py`'s
`production_files()`. It is a specification document, not a copy anything
runs, so I left it. It is out of date with the engine.

### 5.4 The CSV holds replacement characters

Several names in the recovery CSV contain U+FFFD, the character a decoder
substitutes for bytes it could not read. Examples: `Use of home � simplified
expenses �10/month`, `Disposal of Mercedes E200d � clear accumulated
depreciation`. The pound sign and the dashes were lost before the file
reached its present form. That damage is in the data and nothing here
caused it. It means a restored name will not match a receipt bearing the
real characters.

---

## 6. My own mistake

**I committed before running the full suite.** I ran three test files,
committed as `8cdd1a5`, and the full run after the commit had one failure.
`tests\test_vendor_key_naming.py`'s
`test_vendor_code_appears_nowhere_in_worker_but_the_named_survivors` found the
retired field name `vendor_code` inside the filename
`regenerate_vendor_codes.py`, which my new module's docstring named. **I first
told myself it was the git-tracked trap in `CLAUDE.md`. It was not.** That
guard walks `worker\` on disk, so it would have failed before the commit too,
had I run it. The guard allows a survivor only in a comment, and this was a
docstring, so I reworded the docstring rather than adding an exception. The
commit had not been pushed (no remote branch contains it), so I amended it,
to keep the one commit the brief asked for. The result is `13ab225`.

---

## 7. Evidence

**Suite after the amended commit**: 1713 passed, 2 skipped, 1323 subtests.
That is 10 tests more than after `bd38035`, which is this file. Subtests rose
by 27; I have not reconciled that figure with the new file's own subtests.

---

## 8. Confidence

- **High that the engine is unchanged.** It rests on the syntax-tree identity
  check on all five moved definitions, and on the stored-key check being
  byte-identical before and after.
- **High that both scripts now compute the engine's key and load no
  `openai`, and that the regenerate script still loads no `config`.** It
  rests on tests in a fresh interpreter and all 101 CSV names compared.
- **High on flag 5.1's 91.** It is a direct comparison of each stored CSV key
  with the engine's key for its name. **That the regenerate script cannot
  run** rests on reading its paths and on reproducing the `DictWriter` error
  in memory. I did not run the script, because it would write a file.
- **Medium on section 4's 79.** The recovery CSV stands in for the
  transaction export the seed script actually reads.

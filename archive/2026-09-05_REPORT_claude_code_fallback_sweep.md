# Report: the live-path sweep, the forced review, and three tidying items

**Written 2026-09-05, 15:47 BST**, by the implementation session in Claude Code. Follows
`2026-09-05_REPORT_claude_code_fallback_accounts.md` and Paul's four instructions of the same day.

**Three of the four are done. The third is not, and it is not done because the flag that produced it
was wrong.** That is the first thing to read.

| Run | Result |
| --- | --- |
| Start of this session | **450 passed, 200 subtests passed** |
| Final | **456 passed, 200 subtests passed** in 14.72s |

Six tests added. `.\.venv\Scripts\python.exe -m pytest -q`.

---

## Item 3, first, because I got it wrong

**I said `fallback.py` was LF and `chart.py` was CRLF, and offered to make `fallback.py` CRLF "to
match its neighbours". Its neighbours are LF. I looked at one file and generalised from it.**

`.gitattributes` in the repository root is one line:

```
* text=auto eol=lf
```

**LF is the declared standard.** Counted programmatically over every `.py` outside `.venv\`,
`.history\`, `__pycache__\` and `archive\`: **96 files, 80 LF and 16 CRLF.** The sixteen are the ones
that disagree with `.gitattributes`, and they are:

```
config.py                          tests/test_path_layout.py
discard_receipt.py                 tests/test_postprocess.py
probe_layer5.py                    worker/categorisation/chart.py
resolve_receipt.py                 worker/categorisation/engine.py
tests/test_already_filed_guard.py  worker/extraction/base.py
tests/test_date_disambiguation.py  worker/extraction/openai_vision.py
tests/test_extraction_details.py   worker/validation/rules.py
tests/test_logging_setup.py        worker/vat_rates.py
```

**So converting `fallback.py` to CRLF would move it away from the standard, not towards it.** I have
not done it, and I am flagging rather than choosing because you agreed to it on a premise I supplied
and which was false.

**What would actually help, if you want it:** convert those sixteen to LF, which is what
`.gitattributes` already says they should be. Git stores LF for all of them either way, so nothing
in the repository changes; only the working copies do. One command, and I will run it on your word.

**The two `.gitignore` lines are done.** `exports/` and `Claude outputs/` are ignored, with a comment
saying what each is and that they were the only reason the clean-tree warning fired. `git status` is
now clean apart from this session's own work.

---

## Item 1. The sweep

### Method, because a grep would have found nothing

**The four files found yesterday were reading the real chart bundle and none of them mentions
`config.CHARTS_DIR`.** They call pipeline code that reads it. A static search for the constant would
have returned nothing and reported the suite clean, which is the same shape of mistake as reasoning
from output you truncated yourself.

So this measures rather than searches. A pytest plugin captures `config.PRACTICE_ROOT` and
`config.UNSYNCED_ROOT` as they stand at import, **before any fixture patches them**, wraps
`pathlib.Path.open`, `stat`, `is_file`, `is_dir`, `exists`, `glob`, `rglob`, `iterdir`, `mkdir`,
`write_text`, `write_bytes`, `read_text`, `read_bytes`, `unlink`, `rename` and `touch`, plus
`builtins.open`, `sqlite3.connect`, and `shutil.copy`, `copy2` and `move`, and attributes every
access under either root to the test that was running. It records and never blocks.

The two live roots watched:

```
PRACTICE_ROOT = C:\Users\PDK7\OneDrive - Intellitax Accounting Limited
UNSYNCED_ROOT = C:\Intellibills
```

### The result

**The suite has 45 `test_*.py` files plus two fixture modules, 47 in all.** My previous report said
"the other 40 test files", which came from CLAUDE.md's line about 40 files in `tests\`; the real
count is 45 and I should have counted rather than quoted.

**Nine files and 31 tests touch a live root. Every access is a read. Not one test writes, creates,
deletes, renames or connects to anything under either root.** That is the whole of it, printed
whole:

| File | Tests | Live paths touched | Deliberate? |
| --- | --- | --- | --- |
| `tests/test_chart_bundle.py` | 1 | `Charts\Master_COA.csv`, `Charts\PHV_DRIVER.csv` | **Yes.** `RealBundleTest`, skips when absent |
| `tests/test_date_disambiguation.py` | 2 | `Charts\vat_rates.csv` | **No** |
| `tests/test_fallback_accounts.py` | 3 | `Charts\fallback_accounts.csv` | **Yes.** `RealBundleFallbackTest`, mine, skips when absent |
| `tests/test_logging_setup.py` | 2 | `C:\Intellibills\logs\{console,discard,resolve,run}.log` | **Yes.** Asserts the real logs dir is not written to |
| `tests/test_logs_isolation.py` | 1 | `C:\Intellibills\logs` and five files in it | **Yes.** Same, asserts isolation |
| `tests/test_prefer_dayfirst_isolation.py` | 5 | `Charts\vat_rates.csv` | **No** |
| `tests/test_resolution_service.py` | 13 | `Intellibills\Review`, `Intellibills\Review\CLIENT001` | **No** |
| `tests/test_vat_rates.py` | 2 | `Charts\vat_rates.csv` | **Yes.** `RealBundleRatesTest`, skips when absent |
| `tests/test_vat_swap.py` | 2 | `Charts\vat_rates.csv` | **No** |

**Five files are deliberate and correct.** Three read the real bundle on purpose in a class that
skips when it is absent, which is the pattern `test_chart_bundle.py` established and `test_vat_rates.py`
and mine copied. Two read `C:\Intellibills\logs` precisely in order to assert that nothing was
written there, which is the opposite of the fault.

**Four files are not deliberate, and they are the same fault as yesterday's in a different place.**

### Already fixed, and by what

**The three files fixed yesterday were `test_sidecar_category_keys.py`, `test_resolution_service.py`
and `test_retroactive_categorise_sidecar.py`**, by entering `TempChartBundle` from
`tests/chart_fixtures.py` in each one's `TempEnvironment`. Two of the three no longer appear in the
table above at all. **`test_resolution_service.py` still does, and yesterday's fix did not touch what
it is doing now:** `TempChartBundle` pins `CHARTS_DIR`, and this is `REVIEW_ROOT`.

### The four that are not fixed

**Three of them are `vat_rates.csv`**: `test_date_disambiguation.py`, `test_prefer_dayfirst_isolation.py`
and `test_vat_swap.py`. They call `establish_gross_from_vat()` or the extractor, which reads the
published rate table per extraction. Read-only, and the consequence is the ordinary one: the tests
pass or fail on whether OneDrive has finished syncing, and a republished `vat_rates.csv` can move
them without anyone connecting the two events. **The fix is one line each: enter
`VatRateEnvironment` from `tests/test_vat_rates.py`, or a small shared equivalent.**

**The fourth is different and I would fix it first.** `test_resolution_service.py` pins `DB_PATH`,
`CLIENTS_ROOT`, `CLIENTS_JSON`, `LOGS_DIR` and `RUNS_LOG`, and **does not pin `REVIEW_ROOT`.** Its
13 tests call `apply_resolution_note()` and `resolve_receipt()`, which call `remove_review_pair()` in
`worker/filing.py:276`, which:

- calls `_review_dir_for_client_id()` and then `_find_review_sidecar()` on the **live**
  `Intellibills\Review\CLIENT001`,
- and on finding nothing there calls `_scan_other_clients_for_receipt()`, which **iterates every
  client's folder under the live `Intellibills\Review`**,
- and on a match calls `_delete_review_pair()`, which unlinks.

**The sweep recorded no deletion**, because the fixture's receipt ids are `r-1`, `r-resolve` and the
like and no real sidecar carries one. **The receipt id path is safe: ids are UUIDs and the match is
exact.** The filename fallback is narrower than it looks and is not nothing: `_find_review_sidecar()`
falls back to `original_filename` **only for sidecars carrying no receipt id at all, and only when
exactly one candidate matches.** The fixture files are named `parking.pdf` and similar.

**So there is a path, however narrow, by which running the test suite deletes a real client's review
pair.** It has not happened and it may never. **The fix is one line: add `REVIEW_ROOT` to that
fixture's saved-and-restored dict and point it at the temp folder**, which is what
`test_sidecar_category_keys.py` already does.

**Flag, not fixed.** You scoped item 1 to the sweep. All four fixes are one line each and I will do
them on your word.

---

## Item 2. The forced review

**Done, and your reasoning was right: `_result()`'s defaults in the test are a layer 1 exact vendor
match, `confidence` high and `needs_review` False, so an unchecked code would have gone through
looking verified.**

`resolve_against_chart()` now sets `result.needs_review = True` on the `unreadable_chart` branch. The
code still stands, per your ruling that my choice holds. `confidence` is deliberately left as the
layer set it, and there is a test pinning that so a later change to it is a decision rather than a
side effect: the layer was confident about the vendor and was right to be, and what could not be
established is whether the client's chart holds the account.

### But I have to correct what that achieves, including in yesterday's work

**`categorisations.needs_review` is written and read by nothing.** Enumerated rather than asserted:
every string literal in production code naming both `categorisations` and `needs_review` is a
`CREATE TABLE` in `worker/database/schema.py` or an `INSERT INTO` in
`worker/database/repository.py`, and every attribute load of `.needs_review` outside those is
`needs_review=categorisation.needs_review` inside a `save_categorisation()` call. **Nothing SELECTs
the column and nothing branches on the flag.**

**What routes a receipt into `Intellibills\Review\` is `validation.status`**, decided in
`worker/validation/rules.py` and acted on in `worker/extraction_pipeline.py`. That is a different
thing and this module does not touch it.

**So my note text saying the receipt "goes to Review" was wrong, in the new branch and in the
`unusable` branch I wrote yesterday.** Both notes now say "the categorisation is flagged for review",
and there is a test asserting the wording, plus `NeedsReviewIsAFlagNotARouteTest`, which goes red if
a reader for the column ever appears so the docstring's claim cannot go stale quietly.

**This does not change what you asked for.** `needs_review` is the right column and forcing it is
right. It means the categorisation row records that a person should look, and Desktop or the console
can act on it whenever either starts reading the flag. **It does not, today, move the file.** If you
want an unchecked chart to route the receipt to the Review folder, that is a change to
`validation.status` and it is not this instruction.

### Mutation

Three, each on a pristine copy with the file restored and the restore hash-checked.

| Mutation | Tests that went red |
| --- | --- |
| **M10** the forced review removed, which is exactly the state before your instruction | 1: `UnreadableChartTest::test_an_unchecked_code_is_forced_to_review` |
| **M11** the unreadable branch also clears the code, the choice not taken | 1: `UnreadableChartTest::test_a_missing_chart_leaves_the_suggestion_standing` |
| **M12** the note goes back to claiming the receipt goes to Review | 1: `UnreadableChartTest::test_an_unchecked_code_is_forced_to_review` |

**M10 is the red before green**, applied after the fact: it reproduces the pre-instruction state and
exactly one test catches it, with nothing else moving.

### Two stale figures corrected in the same file

`worker/categorisation/fallback.py`'s docstring quoted the chart coverage as 30, 40, 44 and 49.
**Amendment 227 corrects those to 29, 38, 41 and 45**, the earlier ones having been counted against a
71-account cut and quoted after it became 66. The module took them from the brief, which is the
propagation the set rule exists to stop. Corrected, with the old figures struck rather than deleted.
The docstring also said the published table holds one row; it holds 26 as at 15:09 BST, and now says
so with the date.

---

## Item 4. The spent brief

`git mv PROMPT_claude_code_2026-09-05_fallback_accounts.md archive/`. Staged as a rename, so the
history follows it. **Yesterday's report refers to it as being in the repository root and that is now
stale by one directory**, which is worth knowing before anyone follows the reference.

---

## What the republished bundle did to yesterday's tests

**You republished between the two sessions and the table went from 1 row to 26.** I checked rather
than assumed, because two of my tests read the real file:

```
bytes: 306    rows: 26
chained (a target that is itself a key): []
fallback_for("7391") -> 7310
fallback_for("7310") -> None
```

**All 26 targets are terminal, so `validate_fallbacks()`'s one-hop rule holds in the published
file.** `7310` is still absent from the table, so
`RealBundleFallbackTest::test_a_code_that_is_not_in_the_real_file_returns_none` still discriminates.
And `test_the_real_table_is_one_hop_and_not_a_chain`, which was a weak test against one row, is now
a real check against 26. The suite was green against the new bundle before I changed anything.

---

## Mistakes I made, disclosed

Five. Two are corrections to yesterday's work.

1. **The CRLF flag was wrong**, and it is the worst of the five because you acted on it. I compared
   `fallback.py` with one neighbour and called CRLF the norm. `.gitattributes` says `eol=lf` and 80
   of 96 files agree with it. **I generalised from a sample of one, which is the enumerate-the-set
   rule broken in the report that quotes it.**
2. **"Goes to Review" was wrong in yesterday's `unusable` note**, and I repeated it in the new
   branch before checking. Caught by grepping for readers of `needs_review` before writing the claim
   into the report, which is the only reason it is here rather than in the module.
3. **I said "the other 40 test files".** There are 45, plus two fixture modules. The 40 came from
   CLAUDE.md rather than from counting.
4. **My first `needs_review` test was too crude and flagged a false positive**: it matched any SQL
   line containing `needs_review` and `WHERE`, which caught `query_receipts.py:46`,
   `WHERE e.validation_status = 'needs_review'`. That is the status *value* on `extractions`, a
   different column that happens to take a string of the same name. Rewritten to work on statements
   naming both the table and the column.
5. **The rewritten version then flagged `fallback.py`'s own docstring**, which explains at length why
   nothing reads the column and therefore contains both words. Docstrings are now stripped first.
   **This is the second time in two sessions I have written a source-scanning test that finds its own
   explanation**, and the habit that would have avoided both is to strip docstrings by default.

---

## Confidence

**High that nine files and 31 tests touch a live root and that none of them writes**, because it was
measured by instrumenting the filesystem calls rather than searched for, and the full per-test
listing was printed and read whole.

**High that `categorisations.needs_review` is read by nothing in this repository**, because it is
enumerated from the syntax trees two ways, by SQL statement and by attribute load, and both are now
tests. **It says nothing about IntelliBooks Desktop**, which I have not read.

**High that LF is this repository's standard**, because `.gitattributes` says so in one line and 80
of 96 files agree.

**Medium that the `test_resolution_service.py` deletion path is genuinely reachable.** The receipt-id
match is exact and safe; the filename fallback requires a live review sidecar carrying no receipt id
whose original filename matches a fixture's, and no other candidate. I have not constructed one. The
fix is a line whether or not it is reachable.

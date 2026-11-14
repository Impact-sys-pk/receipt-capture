# Report: amendment 557, seven small items

Claude Code, 2026-11-14, finished 09:58 GMT (the Windows shell's `GMTST`, which is GMT in November). Branch `feat/console-phase0`. The brief was pasted into the chat by Paul. It has no `PROMPT_*` file.

**`2026-07-25_BUILD_STATUS.md` was not touched.** The consultant session marks the steps.

## The suite

| When | Result |
|---|---|
| Before any change | 1713 passed, 2 skipped, 1323 subtests |
| After all seven commits | **1736 passed, 2 skipped, 1342 subtests** |

That is 23 more tests, and 23 were added: item 1 added 4, item 3 added 5, item 4 added 4, item 5 added 2 and item 7 added 8. Three new test files were committed, so the suite was run again after the last commit. That second run is the one quoted above.

## The commits

| Item | Commit | What changed |
|---|---|---|
| 1 | `9302f44` | `les`, `los` and `las` added to `NOISE_WORDS` in `worker\categorisation\normalise.py` |
| 2 | `ebe2c93` | The getattr guard now checks the whole production tree |
| 3 | `6274ca4` | `seed_client_vendors.py` skips on key and name together, and reports a name filed under two codes |
| 4 | `f01e175` | `matched_vendor` records the variant that answered, at layers 1 and 2 |
| 5 | `20d5a33` | The resolution log no longer prints "already filed at None" |
| 6 | `0c90f7b` | `docs\specs\categorisation_engine.py` marked as a superseded prototype, left where it is |
| 7 | `72a2da1` | `regenerate_vendor_codes.py` runs from paths given as arguments |

## 1. Noise words

**The check, run before the change.** The live `C:\Intellibills\db\receipts.db` was opened read-only (`mode=ro`), along with `Intellibills\categorisations_client_vendors_cleaned.csv`. For every source string, the key was worked out with the current word list and again with the three words added. The rows checked were:

- 16 rows in `categorisations_client_vendors`
- 9 rows in `categorisations_firm_vendors`
- 91 `categorisations` rows, joined to their extractions
- 118 extractions
- 101 CSV rows

**Result: no key changes.** No stored key contains any of the three words, and `categorisations_client_rules` has no rows.

**Positive control:** `Les Amis Bistro` keys on `les` with the current list and on `amis bistro` with the new one, so the check can detect a change.

**Tests.** The first run was red: 6 subtests failed. A test also pins the words that were left out (`de di du del un une una uno gli`), so adding one later has to be a deliberate decision.

## 2. Getattr guard

The guard now walks `production_files()`, imported from `tests\test_category_hold.py`. It also asserts that `service.py` and `publish.py` are in that set, so the wider guard cannot quietly check less than the old one.

**It passed on its first run, because no file breaks the rule today.** To show the guard can fail, I planted one offending call:

- Changed one line of `worker\extraction_pipeline.py` (line 419): `categorisation.matched_vendor` became `getattr(categorisation, "matched_vendor", None)`.
- The text it replaced appears once in that file, and the printed diff shows one line changed.
- **The old guard passed and the new guard failed.**
- The file was restored, and its md5 matches the original.

## 3. Seed script

**Disclosure about the brief's wording.** The brief says the script kept "whichever was met first". **It kept the last.** Each time it met a name again under another code, `upsert_client_vendor()` overwrote the code. The red test shows this:

- `Shell Recharge` under 7301 and then 7302 ended up as one row coded 7302, with `times_seen` 2.
- The script printed `Inserted: 3` when it had written two rows.

The fix is the same either way.

**What it does now:**

- It skips a repeat only where both the key and the name match. Previously it skipped on the key alone within one code, so `Shell Bromley` was dropped once `Shell Garage Dartford` had been seeded.
- A name the source files under two codes is **written under neither**. It is listed with both codes under the heading "NOT SEEDED", and the summary prints `Conflicting names, not seeded: N`.

## 4. matched_vendor

**What changed.** At layers 1 and 2 the result now carries the answering row's `vendor_name`. The key is still on the result, as `vendor_key`.

- Three existing tests asserted the old value, and were changed to expect the new one.
- Four new tests in `tests\test_vendor_lookup_by_name.py` cover a match on the name, a match on the key only (where the most-seen variant is recorded, not the receipt's own name) and layer 2.
- **Red before the change: 7 failures.**

**Checks made before changing it:**

- No production code reads `matched_vendor` except to copy it.
- `IntelliBooks-Desktop-v3.html` contains the name 0 times.
- No mapping row in the live database has an empty `vendor_name`: 0 of 16 client rows and 0 of 9 firm rows.

**The change applies to new rows only.** The 25 live `client` rows keep the key, because changing them would mean writing to the database.

## 5. Log line

The message now reads "there is no copy in the client folder" where `filed_path` is NULL, and still names the path where there is one. Red first, and the failure quoted the live wording: `...it is already filed at None, so no file moves...`.

## 6. The spec file: marked in place, not moved

**Nothing imports it.** I checked the syntax tree of 172 Python files, leaving out `.git`, `.venv`, `.history`, `__pycache__` and `archive`.

**But documents cite it by its path:**

- `2026-07-25_CONSOLE_DESIGN.md`, in five places
- `2026-07-25_BUILD_STATUS.md`
- `2026-09-19_HANDOVER_consultant_session.md`
- `2026-09-18_REPORT_claude_code_section_18_citations.md`
- `2026-11-13_REPORT_claude_code_vendor_key_rule_one_home.md`
- `tests\test_category_hold.py`
- `CATEGORISATION.md` and `tests\test_vendor_key_naming.py` name the `docs\specs\` folder

It also sits beside `auto_categorisation_spec_v01.md`, the specification it belongs to.

**So I marked it in place.** Moving it would leave every one of those citations pointing at nothing. Marking it costs one comment line, and `py_compile` passes.

## 7. Regenerate script

`main(argv)` now takes `<input_csv> <output_csv>`. It:

- exits non-zero if either argument is missing or the input does not exist
- refuses to write over its own input, because the in-place version was deleted on purpose on 2026-09-12
- removes `vendor_code` from each row
- keeps the stored key, under `vendor_key`, for a row with no name

**Run on the real CSV.** It read `Intellibills\categorisations_client_vendors_cleaned.csv` and wrote only to my scratch folder, not to `Intellibills\`:

- 101 rows in and 101 out
- 91 keys recomputed, which matches amendment 557
- no rows without a name

## Flags, each with a recommendation

1. **The recovery CSV still files one name under two codes.** `Bounce Back Loan (Loan Repayment)` appears under both `362` and `731`. `import_vendor_csv.py` upserts, so an import would keep whichever came last and say nothing, which is the fault item 3 fixed in the seed script. **Recommendation: give `import_vendor_csv.py` the same report-and-skip rule.** It is small and I can do it now.
2. **The recovery CSV's codes are three digits**, for example `104 Parking & Toll Charges`. Amendment 96 says any three-digit code is legacy. Imported as they stand, they would become learned mappings that the chart check cannot confirm. **Recommendation: no import until there is a map from old codes to new four-digit codes.** That is Paul's decision.
3. **Layers 3 and 4 still record the matched key** (`best_match`), although the most-seen variant is what supplies the code. **Recommendation: record that variant's `vendor_name` there too**, which is one line at each layer. I left it alone because the brief named the 10bs.9 layers, and layer 3's behaviour is recorded as reported and not decided.
4. **The regenerate script overwrites an existing output file without warning.** **Recommendation: leave it.** The output is a derived file, and the input is protected.
5. **`CLAUDE.md` says `categorisations_firm_vendors` "holds 0 rows and has no writer".** The live table holds 9 rows, read-only today. **Recommendation: strike that sentence.** It is not Claude Code's file to edit.

## My own mistakes, all caught and corrected

- **The first query in the item 1 check asked for `categorisations.vendor_key`.** That table has no such column, which `tests\test_vendor_key_naming.py` itself asserts. The query raised an error before reporting anything, and I re-ran it reading `matched_vendor` instead.
- **The item 2 mutation script crashed on the first run.** It tried to print a `→` to a cp1252 console. The `finally` block restored the file, and I confirmed the restore with `git status` before re-running.
- **On the second run, its diff showed every line as changed.** It was comparing CRLF bytes with a read that had converted the line endings. The mutation itself had changed one line, and the third run printed a byte-faithful diff to prove it.

**Confidence: high that the seven changes do what this report says.** That rests on red tests before each change (or a mutation, for item 2), a full green suite after the last commit, and the database and CSV figures read directly rather than estimated. **Medium on flag 2's consequences**, because I have not read the live chart to confirm which three-digit codes it rejects.

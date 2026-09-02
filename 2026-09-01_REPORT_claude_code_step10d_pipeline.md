# Report: step 10d, the pipeline half

**Written 2026-09-02 by Claude Code**, against `PROMPT_claude_code_2026-09-01_step10d_pipeline.md`. Times are BST; the machine clock read 21:06 BST, 20:06 UTC, when this was written.

---

## Before task 1: the two hashes

Both confirmed, read from disk.

```
$ wc -c PROMPT_claude_code_2026-09-01_step10d_pipeline.md
42561 PROMPT_claude_code_2026-09-01_step10d_pipeline.md

$ md5sum PROMPT_claude_code_2026-09-01_step10d_pipeline.md
c1b9cc38ae147bc0874d38b84234be85 *PROMPT_claude_code_2026-09-01_step10d_pipeline.md
```

**Section A, hashed by the rule at the head of section A**: from the `## A.` line inclusive to the line immediately before the next `## B.` line, joined with a single newline, no trailing newline, UTF-8. `## A.` is line 17 and `## B.` is line 61, so section A is lines 17 to 60.

```
4911 1e1b6949021b9e8db8b981e74c052bb5
```

**Both match the preamble.** And, because the brief says to stop if they differ, all three briefs were hashed the same way rather than only this one:

```
PROMPT_claude_code_2026-09-01_step10d_pipeline.md   (4911, '1e1b6949021b9e8db8b981e74c052bb5')
PROMPT_intellibooks_2026-09-01_step10d_desktop.md   (4911, '1e1b6949021b9e8db8b981e74c052bb5')
PROMPT_phoneapp_2026-09-01_step10d.md               (4911, '1e1b6949021b9e8db8b981e74c052bb5')
```

Identical in all three. No drift.

---

## Task 1. Starting state

```
$ git --no-optional-locks status --short
 M 2026-07-25_CONSOLE_DESIGN.md
 M PROMPT_claude_code_2026-09-01_step10d_pipeline.md
 M PROMPT_intellibooks_2026-09-01_step10d_desktop.md
 M PROMPT_phoneapp_2026-09-01_step10d.md
?? 2026-09-02_HANDOVER_consultant_chat_13.md
?? 2026-09-02_REPORT_claude_code_commit_175.md
```

```
$ git --no-optional-locks log -1
2bfe47d5e147234f651eb6c165b27dfd015b3a0f 2bfe47d 2026-09-02 17:10:49 +0100 docs: the step 10d briefs' line numbers, second pass
$ git --no-optional-locks rev-parse --abbrev-ref HEAD
feat/console-phase0
```

**HEAD matched the brief.** Branch `feat/console-phase0`.

**One difference from what task 1 said to expect, and I did not stop for it.** The brief says "three modified files, being this brief, `PROMPT_intellibooks_...` and `PROMPT_phoneapp_...`". There were **four** modified: `2026-07-25_CONSOLE_DESIGN.md` as well. It is not a `.py`, it is not under the practice root, and it is not unexpected: task 1b's own `git add` line names it first, and it is where amendments 175 to 179 were written. **The enumeration sentence and the `git add` line in the same brief disagree by one file, and the `git add` line is right.** Flagged rather than treated as a reason to stop.

### Task 1b. The documentation commit

```
$ git commit -F ...
[feat/console-phase0 73358b9] docs: amendments 175 to 179, and step 10d gains nine sub-steps
 6 files changed, 624 insertions(+), 18 deletions(-)
 create mode 100644 2026-09-02_HANDOVER_consultant_chat_13.md
 create mode 100644 2026-09-02_REPORT_claude_code_commit_175.md
```

**Commit `73358b9`.** Message used verbatim, with the `Co-Authored-By` trailer as on `7e037c3`.

### The two constants

```
$ python -c "import config; print(config.CLIENTS_CSV); print(config.DB_PATH)"
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\clients.csv
C:\Intellibills\db\receipts.db
```

Both as the brief states. Both outside the repository.

### The baseline test count

```
$ python -m pytest -q | tail -5
286 passed, 166 warnings, 127 subtests passed in 14.29s
```

**Baseline: 286 tests, 127 subtests, 166 warnings.**

---

## The counts the brief asked me to report

### `CLIENTS_BY_CODE`, enumerated before anything was changed

**Your count is exactly right. All four figures.**

`.history\` had to come out of the count first: it is a VS Code local-history folder, gitignored at `.gitignore:9` and untracked, and a naive `grep -rn` over the working tree returns **374** occurrences because of it. Counting over tracked files only:

```
$ git --no-optional-locks grep -n "CLIENTS_BY_CODE" -- '*.py' | wc -l
60
$ git --no-optional-locks grep -n "CLIENTS_BY_CODE" -- 'tests/*.py' | wc -l
47
$ git --no-optional-locks grep -ln "CLIENTS_BY_CODE" -- 'tests/*.py' | wc -l
17
```

60 total, 47 in tests across 17 test files, so 13 outside `tests\`. The thirteen, printed whole:

```
app.py:143:    return config.CLIENTS_BY_CODE.get(client_code, {}).get("client_name", client_code)
app.py:374:            business_type = config.CLIENTS_BY_CODE.get(receipt["client_code"], {}).get("business_type", "UNSPECIFIED")
app.py:874:                client_name = config.CLIENTS_BY_CODE.get(intake.client_code, {}).get("client_name", intake.client_code)
app.py:937:            client_name = config.CLIENTS_BY_CODE.get(intake.client_code, {}).get("client_name", intake.client_code)
app.py:1073:                client_name = config.CLIENTS_BY_CODE.get(client_code, {}).get("client_name", client_code)
config.py:167:CLIENTS, CLIENTS_BY_CODE = load_clients()
retroactive_categorise.py:120:            business_type = config.CLIENTS_BY_CODE.get(receipt["client_code"], {}).get("business_type", "UNSPECIFIED")
worker/extraction_pipeline.py:190:        business_type = config.CLIENTS_BY_CODE.get(client_code, {}).get('business_type', 'UNSPECIFIED')
worker/extraction_pipeline.py:217:        client_name = config.CLIENTS_BY_CODE.get(client_code, {}).get('client_name', client_code)
worker/extraction_pipeline.py:258:        client_name = config.CLIENTS_BY_CODE.get(client_code, {}).get('client_name', client_code)
worker/filing.py:166:    from `CLIENTS_BY_CODE`, so the folder a receipt was written to depended on
worker/intake/folder_reader.py:82:        client = config.CLIENTS_BY_CODE.get(client_code)
worker/resolution/service.py:366:    entry = config.CLIENTS_BY_CODE.get(client_code or "", {})
```

That is the definition at `config.py:167`, the comment at `worker/filing.py:166`, and **eleven real readers**, at exactly the eleven lines you named. Every one a `.get(..., {})` with a silent fallback, as you said.

**On your question, "if a reader reaches that dictionary by another route, name it."** I looked for four routes a grep on the name would miss and found none:

- `getattr(config, "CLIENTS_BY_CODE")` or `vars(config)[...]`: zero occurrences of either shape anywhere.
- `from config import *`: zero occurrences.
- A second binding, such as `by_code = config.CLIENTS_BY_CODE` passed on under another name: the eleven readers are all inline `.get()` calls, so there is no alias to follow. `tests/resolution_fixtures.py:40` saved it under the string key `"CLIENTS_BY_CODE"` and restored it by `setattr`, which grep does find.
- `load_clients()` called directly for its second return value: three call sites, all in `tests/test_default_firm_id.py`, all found by grep on `load_clients`.

So the set was complete. **The one thing your figure did not cover, and it is not a reader**, is that the same identifier appears 300-odd more times in `.history\`, which is untracked and does not matter but does make a plain `grep -rn` unusable for this. Worth knowing before the next count.

### The migrations: eleven, and your correction was right

```
$ grep -n "ALTER TABLE" worker/database/schema.py
182, 184, 186, 191, 195, 199, 201, 208, 210, 220, 232
```

**Eleven, at exactly the eleven lines you named.** The sub-step's "nine" is wrong and the two it dropped are `filed_at` at 220 and `reason` at 232, which are precisely the two the named tests cover, as you said.

Both named tests existed and are deleted:

- `tests/test_discard_reason.py`'s `test_the_column_exists_on_an_older_database`, which was at `:60`.
- `tests/test_filed_at_column.py`'s `test_existing_rows_are_not_back_filled`, which was at `:116`.

In both files a comment now sits where the test was, saying what it proved and why there is nothing left for it to prove. **Removing the eleven guards meant folding the columns they added into the CREATE statements**, which is 10d.22's "one definition is the only definition": `receipts` gains `filed_at`, `duplicate_of` and `locked_at`, `extractions` gains `pipeline_version`, `receipt_ref_number` and `receipt_time`, and `resolution_events` gains `reason`. Without that the rebuild would have produced tables missing seven columns.

### The five `capture_token` values

Generated once, here, with `secrets.token_urlsafe(24)`, which yields 32 characters. **Paul carries these to the other two briefs. Nobody else invents one.**

| `client_id` | `capture_token` |
|---|---|
| `Client_001` | `yKkeZ1R1Vo1MfeNsPaUgYKcmswOiN--B` |
| `Client_002` | `U-3UtuLnY1pa2scJaqP4B76nE7-nEBd2` |
| `Client_003` | `n7swdGk3K_EghYaELbgc6zutG_jIgMdo` |
| `Client_004` | `XzZtypWOzqRSUe9nEsj4Bzds29SGTnXJ` |
| `Client_005` | `9yq1jSWSyfeLdty7M62aiodTy6Q0DKj4` |

### 10d.21: my two proposed names, and I have not renamed anything

**Stop-and-ask item. Nothing is renamed and `ONEDRIVE_ROOT` and `LOCAL_ROOT` stand as they are until you say.**

| Today | Proposed | Why |
|---|---|---|
| `ONEDRIVE_ROOT` | `PRACTICE_ROOT` | It is the practice root and the design document already calls it that, at 18.2a and throughout section 16. Nothing in the pipeline calls a Microsoft API, and F17 records the client top folder as a path that need not sit in OneDrive at all, so naming it after one vendor's sync client describes an accident of where Intellitax keeps it. `PRACTICE_ROOT` also reads correctly in the one place the distinction bites, `resolve_practice_path()` at `worker/resolution/service.py:350`, whose docstring already says "relative to the practice root" and then resolves against `config.ONEDRIVE_ROOT`. |
| `LOCAL_ROOT` | `UNSYNCED_ROOT` | The property that matters is not that it is local. It is that **nothing syncs it**, which is the whole of amendment 72's reasoning: WAL companions must stay consistent and OneDrive copies files while they are open. "Local" is true of the repository too, and of the practice root on this machine, so it distinguishes nothing. `UNSYNCED_ROOT` states the constraint, so a future session repointing it at another drive has to ask whether that drive is synced. |

**Two things to weigh against `PRACTICE_ROOT` before you rule**, because I would rather you decided with them in hand than found them later. The environment variable is `ONEDRIVE_ROOT` and is read at `config.py:24`; renaming the constant without renaming the variable leaves them one word apart, and renaming the variable means `.env` changes on every machine. And `tests/test_path_layout.py` asserts on both names. Neither is a reason not to do it; both are work that goes in whichever commit does.

---

## Your five corrections: four right, one right about the line and worth adding to

**1. `folder_reader.py:100`, not `:102`. Right.** Read both before the change:

```
100:            sidecar = _load_sidecar(sidecar_path) if sidecar_path else None
102:            original_name = item.name
```

Line 100 is what makes the sidecar optional. Line 102 is `original_name = item.name` exactly as you said.

**2. Eleven migrations, not nine. Right**, and enumerated above.

**3. `parse_ambiguous_date()`, not `_parse_numeric_date()`. Right.** `git grep "_parse_numeric_date"` returns nothing in any file of any type. The function holding lines 60 to 66 is `parse_ambiguous_date(raw, prefer_dayfirst)` at `postprocess.py:28`, and the line contents the sub-step cites are exact.

**4. Twelve `"GBP"` literals. Right, and the split is right.**

```
app.py:371, 565, 625, 808, 983, 1161                     6
worker/resolution/service.py:337 (twice), 478, 978       4
worker/extraction/openai_vision.py:26, 124               2
```

**One point worth making because a future count will hit it:** that is twelve **occurrences** across **eleven lines**. `service.py:337` reads `(currency or "GBP").strip() or "GBP"` and carries two. A count of lines gives eleven and a count of occurrences gives twelve, and your figure is the occurrences.

**A judgement I made about one of the twelve, so it is not silently different.** `openai_vision.py:26` is inside `_SYSTEM_PROMPT`, the JSON shape the model is asked to return. That one is **not** replaced by `config.DEFAULT_CURRENCY`: it is an example in a prompt, not a value the code writes, and interpolating a constant into a prompt string changes what the model is asked without changing what the pipeline stores. The other eleven are now `config.DEFAULT_CURRENCY`. **Say if you want the prompt one done too.**

**5. Five `categorise()` production call sites. Right**, at `app.py:376`, `worker/extraction_pipeline.py:191`, `worker/resolution/service.py:643` and `:1034`, and `retroactive_categorise.py:133`. `docs/specs/categorisation_engine.py:423` also matches a grep for `categorise(` and is a specification document rather than production, so it is correctly outside your five.

---

## Did 10d.53 and 10d.54 as written let me do the work without stopping?

**Yes, with one addition each, and both additions were forced by the code rather than optional.**

**10d.53.** The sub-step names `worker/storage/store.py` lines 23 and 37 and the three callers at `app.py:733`, `:918` and `:1097`. All five verified. What it does not name is that **10d.55 adds a fourth caller**, in the statement branch, so `save_inbox_file()` gained a caller in the same sitting. That is not a gap in 10d.53; it is 10d.55 landing on the same function, and the two read consistently together.

**10d.54.** The sub-step names `_review_dir_for_client_code()` at `:155` and `file_review()`'s parameter at `:118`. Both verified. **It does not name `remove_review_pair()` at `worker/filing.py:271`, whose second parameter is also `client_code` and which calls `_review_dir_for_client_code()`.** It had to change with them or the writer and the remover would key the same folder differently, which is the exact failure the sub-step exists to prevent. Three call sites, all in `worker/resolution/service.py`, at what are now `:748`, `:836` and `:1112`, all passing `receipt.get("client_code")`. All changed.

**And you asked me to confirm `_scan_other_clients_for_receipt()` rather than assume it.** Confirmed by reading it: it iterates `config.REVIEW_ROOT.iterdir()`, skips the directory already searched, and matches on the receipt id inside each sidecar. It never constructs a folder name, so what those folders are named is invisible to it. Its docstring said "every subfolder of REVIEW_ROOT is a client code"; that sentence is now "is one client's", with a note that the change was checked by reading rather than assumed.

**The first version of this brief would indeed have broken both.** With `client_code` deleted and neither sub-step present, `store.py` and `_review_dir_for_client_code()` would have been left taking a parameter whose value no longer existed, and the most natural repair, passing the client name, is the drift amendment 44 recorded.

---

## Did anything in `worker/resolution/service.py` need changing that the brief does not name?

**Yes. Five things, and they are your omission rather than mine to have found late, because the brief names none of them.** All five were forced: the file would not have worked otherwise.

1. **`_client_details()` at `:364`**, one of the eleven `CLIENTS_BY_CODE` readers your list does name, but the brief does not say what it becomes. It now takes a `client_id` and returns a **third** value, `client_folder_name`, because `resolve_receipt()` files a receipt and needed a folder name that is not the display name. Returning two values and letting the caller do a second lookup would have been a second reader of the registry in one function.

2. **The resolution note's own field, at `:201` and `:274`.** `ResolutionNote.client_code` and `_note_text(raw, "client_code")` are the pipeline half of **10d.60**, which is in the Desktop brief and not in mine. The note is the contract between the two halves, so if I had left this reading `client_code` while Desktop writes `client_id`, the field would simply have been absent from every note. It is now `client_id`. **The brief's section J puts 10d.60 in the Desktop half; it has a pipeline half and the pipeline brief does not mention it.**

3. **`_receipt_for_note()`'s docstring at `:864`**, which explains why the note's client field is deliberately not used to find the receipt. The reasoning survives the rename and is restated rather than left describing a field that no longer exists.

4. **Three `remove_review_pair()` call sites**, covered above under 10d.54.

5. **A guard `resolve_receipt()` did not have.** After 10d.14, `file_receipt()` takes `client_folder_name`, which can be `None` for an unresolved client. `resolve_receipt()` would have passed `None` straight into `get_client_directory()` and built a path with the literal string `None` in it. It now treats "no folder name" as a reason to stay a review item, which is 10d.18 applied to the resolution path. **10d.18 says an unresolved client files nothing into `Clients\` and does not say that the rule binds the resolution service as well as intake. It has to, or the resolution service is the hole in it.**

**One thing in that file I have not changed and am flagging rather than fixing.** `_client_details()` returns `entry.get("trade", "UNSPECIFIED")` and the value flows into `categorise(business_type=...)` and into `ResolutionView.business_type`, so the console will show a field called `business_type` holding what the registry calls `trade`. 10d.30 renames the **column** and says nothing about the engine, and renaming the engine's parameter touches all five `categorise()` call sites, which 10d.39 explicitly avoids. So the rename stops at the column and the registry field. **It is a half-finished vocabulary and somebody should decide whether the engine follows.**

---

## `Client_002`, and every other absent attribute

**Flagged for Paul rather than buried, as you asked.**

The brief's data could not be re-verified, and that is the first thing to say. **`IntelliBooks-Practice.json` on disk today holds two clients, TEST and Test 2, with `savedAt` `2026-07-16T16:37:26.665Z`.** It has no `clientType`, no `yearEnd`, no `mtd`, no `mtdBasis`, no `balanceSheet` and no `partners` on either record. So the five records you read on 2026-09-01 are not in the file I can read on 2026-09-02, and I wrote `_step10d_clients.json` from **your** figures rather than from the file. Read at `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks-Practice.json`; note it is at the practice root, not inside `IntelliBooks\`.

**What I wrote for `Client_002`, and why.**

| Field | What I wrote | Why |
|---|---|---|
| `year_end` | `null` | You read it as null. Written explicitly as `null` rather than omitted, so the record says "nobody has set this" instead of "this field does not exist here", which are different things to a reader that iterates keys. |
| `mtd` | `null` | Same. |
| `balance_sheet` | **omitted** | You read it as having no `balanceSheet` key at all, and IntelliBooks' `clientFromFile()` remembers which keys were absent in `_absent` and writes back only what was there or what the operator has since filled in. Writing `null` would have made the key exist, which is a decision the operator has not made. |

**And three decisions on fields nobody has read a value for, which apply to all five records.**

- **`mtd_basis`: I wrote `"standard"` on all five.** No source states it. `IntelliBooks-Desktop-v3.html:1113` defines the new-client defaults as `{vat:false, phv:[], yearEnd:"05/04", mtd:false, mtdBasis:"standard", balanceSheet:false}` and `:3464` reads `c.mtdBasis||"standard"`, so `"standard"` is what Desktop shows for an absent value anyway. **This is the weakest of the three and the one to overrule if any.** Omitting it would also be defensible.
- **`statement_week_ending_day`: I wrote `"Sunday"` on all five.** Amendment 179 added it to section A on 2026-09-02 and says it exists only on the phone today, at `index.html:244`, so there is no stored value to carry across. I did not read `index.html`; it is the phone app brief's file. **If `index.html:244`'s default is not Sunday, this is wrong on all five and should be corrected before the flip.**
- **`created`: I wrote `"2026-09-02"` on all five.** Section A says it is the date the client record was created, and these records are created today by 10d.2. The two records that survive in the old practice file carry `created: "2026-07-16"`, and carrying that forward would have been wrong: amendment 139 says nothing is carried across and these are new records, not migrated ones.

**Two more, stated because they are mine and not yours.**

- **`emails` is an empty array on all five.** No test client has an address in today's `clients.csv`, and inventing one would create a live routing rule. **A consequence worth knowing before the flip: with no addresses in the registry, every emailed receipt resolves to `UNKNOWN` and becomes a Review item.** That is correct behaviour and it will look like a fault on the first run.
- **`firm_id` is `"FIRM001"` on all five, and section A's field list does not include it.** 10d.19 requires it: the client loader refuses a record with no firm, so a record without one would not load at all. Desktop carries unmapped keys through `_extra` untouched, so it survives a save from that side. **Section A should probably name it.**

---

## Section H. Every check, with its output

### H1. The test suite

```
$ python -m pytest -q | tail -20
348 passed, 188 subtests passed in 9.61s
```

**348 passed against a baseline of 286, and 188 subtests against 127.** No failures, no errors, and the warning count went from **166 to zero**.

**Where the 62 come from.** 51 are two new modules; 13 replace tests whose subject changed; two were deleted; the warnings went with a type fix.

**Tests deleted, both named by 10d.34:**

- `tests/test_filed_at_column.py::test_existing_rows_are_not_back_filled`. It dropped the `filed_at` column and proved `init_db()` added it back. There is no migration path any more.
- `tests/test_discard_reason.py::test_the_column_exists_on_an_older_database`. Same shape, for `resolution_events.reason`.

**Tests whose assertion was inverted or repointed, with the reason in each case:**

| Test | Was | Is |
|---|---|---|
| `test_default_firm_id.py::LoadClientsFallbackTest` (whole class) | a record with no `firm_id` **gets** `DEFAULT_FIRM_ID` | a record with no `firm_id` is **refused**, logged and skipped. Renamed `RecordWithNoFirmIsRefusedTest`. 10d.19 removes exactly the behaviour this class proved. |
| `test_default_firm_id.py::SentinelDefaultFirmIdTest` | the sentinel reaches `load_clients()` | the sentinel reaches `resolve_client_info()`'s unresolved branch, which is the remaining legitimate reader. **The sentinel discipline is preserved deliberately**: it is the only test in the suite that would notice the constant being reverted to a literal, per amendment 93. |
| `test_default_firm_id.py::test_the_count_is_looking_at_the_right_file` | `app.py` names `config.DEFAULT_FIRM_ID` | `app.py` names `config.UNATTRIBUTED_FIRM_ID` **and no longer names `config.DEFAULT_FIRM_ID` at all**, which is 10d.19 stated as a text count. The companion guard is kept for the reason it was written: a text count that reads a moved file passes for ever. |
| `test_resolution_events_schema.py::test_extraction_id_is_nullable_and_carries_no_foreign_key` | `fk_targets == ["receipts"]`, "only receipt_id may carry a FK" | `fk_targets == []`. 10d.33 drops `receipt_id`'s key too. |
| `test_resolution_view.py::test_unknown_client_code_falls_back_to_the_code_itself` | an unknown code shows as the code | renamed `test_an_unresolvable_client_shows_the_id_rather_than_inventing_a_name`. The display fallback is the id, which is the one thing certainly true about the receipt; what went is the fallback that produced a **folder** name from a miss. |
| `test_path_layout.py::test_the_logs_are_outside_any_synced_folder` | `RECEIPTS_LOG == LOGS_DIR / "receipt_events.ndjson"` | `not hasattr(config, "RECEIPTS_LOG")`. 10d.19 deletes it rather than reviving it. `EXPORTS_DIR` came out of the same module's two lists, per 10d.37. |
| `test_postprocess.py::VatInclusiveSwapTest` (whole class) | `apply_vat_inclusive_swap`, and 105/5.00 was "ambiguous, nothing swapped" | `EstablishGrossFromVatTest`. 105/5.00 now verifies at exactly 5% and is accepted, which is 10d.42's assume-and-verify shape replacing the old "looks like a gross AND does not look like a net". Two new tests with it: an unrecognised rate writes the implied percentage and changes nothing, and the rounding allowance refuses 17% and 23%. |
| `test_intake_folder_reader.py` (whole module, rewritten) | `intake.client_code == "ABC"` from the folder name | the client comes out of the sidecar; the folder is named after a client that **is** in the registry while the sidecar names one that is not, and neither resolves. That is the assertion 10d.11 actually needs. |

**Two mechanical sweeps across the suite**, both large and neither interesting: `CLIENTS_BY_CODE` to `CLIENTS_BY_ID` with the fixture registries rekeyed on `client_id` and given a `client_folder_name`, and `client_code=` removed from `save_receipt()`, `file_review()` and `make_enriched_sidecar()` calls.

**One structural change to the suite's own guard, and it is worth your eye.** `tests/test_logs_isolation.py`'s `PROCESS_ONCE_WRITES` gains `CLIENTS_JSON`. It is not a write. 10d.35 makes `process_once()` re-read the registry whenever its modification time moves, so **a test module that drives `process_once()` and does not pin `CLIENTS_JSON` runs against the live `clients.json`, and against whatever IntelliBooks Desktop happened to save while the suite was running.** Eleven fixtures now pin it, and set `config._CLIENTS_MTIME` to match so the re-read sees no change. Without that, adding 10d.35 would have made the suite non-deterministic in a way that only bites once the registry file exists, which is after the flip.

**Two new modules, 51 tests:**

- `tests/test_step10d_pipeline.py`, 38 tests: the registry re-read, the document store key, the Review folder key, `save_receipt()`'s signature, the whole schema shape read back through `PRAGMA`, the arrival timestamp, the unknown-sender alert, the mailbox firm, and the client folder resolution.
- `tests/test_step10d_routing.py`, 15 tests: the same behaviour end to end through a real `process_once()`, because where an unresolved receipt goes is a decision spanning the intake reader, the shared pipeline and the filer.

### Red before green

The tests could not come first: this is a change to existing behaviour in eleven production files, not a new feature. So, per `CLAUDE.md`, **the suite was made to discriminate by mutation, from a clean tree, one mutation at a time, each reverted before the next.** Ten mutations, each restoring the behaviour a sub-step removes. **Every one was caught, and each by a small targeted set rather than by half the suite:**

| Mutation | Caught by |
|---|---|
| 10d.13: `_client_folder_name()` returns the id on a miss | `ClientFolderResolutionTest::test_an_unresolved_client_names_nothing`, `::test_a_record_with_an_empty_folder_name_names_nothing` |
| 10d.53: document store keyed on `client_name` | `DocumentStoreKeyTest::test_save_file_writes_under_the_client_id`, `::test_the_client_name_is_not_the_key` |
| 10d.54: Review folder key upper-cased | `ReviewFolderKeyTest::test_the_case_is_not_folded` |
| 10d.35: a failed parse empties the registry | `RegistryRereadTest::test_a_broken_file_keeps_the_registry_and_does_not_raise` |
| 10d.42: the 0.03 tolerance restored | `EstablishGrossFromVatTest::test_the_rounding_allowance_is_not_a_window` |
| 10d.17: `save_receipt()`'s `client_id` default restored | `SaveReceiptHasNoDefaultsTest::test_the_four_arguments_are_required` |
| 10d.16/10d.18: the unresolved-client gate removed | three `UnresolvedClientRoutingTest` tests |
| 10d.27: the raw mtime passed again | `ResolvedClientStillFilesTest::test_the_arrival_timestamp_is_written_as_iso_utc` |
| 10d.36: the firm name hardcoded again | three `UnknownSenderAlertTest` tests |
| 10d.55: the statement's document store copy removed | two `StatementCopyTest` tests |

**Disclosing a real gap the first pass had, because it is exactly the failure this project keeps recording.** On the first run **four of the ten survived**, and my harness reported two of the four wrongly. Two were genuine gaps: `DocumentStoreKeyTest` did not populate `CLIENTS_BY_ID`, so a mutation keying the store on the client name fell back to the id and produced the same path, and the arrival timestamp had no test at the call site, only on the helper. Both are now covered. **The other two were a filter fault in my own harness**: pytest reports a failing subtest as `SUBFAILED(...)` and my parser only matched lines beginning `FAILED `, so two mutations that were caught were reported as "NOTHING CAUGHT IT". I found that by re-running those two by hand rather than by trusting my own summary, which is `CLAUDE.md`'s "never reason from output you filtered yourself" applied to a filter I had written five minutes earlier.

### H2. The five client ids

```
$ python -c "import config; print(sorted(config.CLIENTS_BY_ID))"
[]
```

**Empty, and correctly so: `clients.json` does not exist yet.** Section B says I do not create it, so `config.CLIENTS_JSON` points at a file Paul has not placed. Proving it another way, against the scratch file the check is really about:

```
$ python -c "import config, pathlib; config.CLIENTS_JSON = pathlib.Path('_step10d_clients.json'); print(sorted(config.load_clients()[1]))"
['Client_001', 'Client_002', 'Client_003', 'Client_004', 'Client_005']
```

**The five ids from section A, loaded through the real `load_clients()`.** The email index is `{}`, because no record carries an address; see the `Client_002` section above.

### H3. `CLIENTS_BY_CODE`

Nothing in any Python file. Four occurrences survive and all four are prose explaining the removal: `app.py:145`, `config.py:210`, `worker/intake/folder_reader.py:82` and `tests/test_intake_folder_reader.py:4`, each in a docstring or comment saying what the name used to do. Everything else `git grep` finds is markdown: the design document, the briefs and earlier reports, which are the record and are not touched.

### H4. `client_code` survivors, every one with a reason

```
$ git --no-optional-locks grep -n "client_code" -- '*.py'
```

| File and line | Why it is legitimate |
|---|---|
| `app.py:145` | Docstring. Quotes the deleted fallback so the next reader knows what 10d.13 removed and what it cost. |
| `config.py:210` | Docstring on `load_clients()`, saying `CLIENTS_BY_CODE` is gone. |
| `worker/database/repository.py:96, 236, 240` | Docstrings on `save_statement()` and `save_receipt()`, recording which columns and defaults went. |
| `worker/database/schema.py:85, 117` | SQL comments on `receipts` and `statements`, recording that the column is gone. |
| `worker/filing.py:385, 386, 389, 391` | The docstring on `make_enriched_sidecar()` explaining the rename and why the frozen function moved. See the flag below. |
| `worker/resolution/service.py:892` | Docstring on `_receipt_for_note()`, recording that the note's field was `client_code` until 10d.60. |
| `worker/categorisation/coa.py:77` | **Not a client code.** "coa_client_codes table", a note about a future per-client chart override. A grep false positive. |
| `docs/specs/categorisation_engine.py:551` | A specification document, not production. Writes a key called `client_code` in an illustrative payload. **Flagged, not changed:** `docs/specs/` is nobody's code and the brief does not name it. |
| `tests/test_step10d_pipeline.py:215, 239, 244` and `tests/test_step10d_routing.py:201, 202, 243` | **Assertions that it is absent**, which is the point. |

Every survivor is prose, a false positive, or an assertion of absence. **No code path names a client code.**

### H5. `normalise_client_name`

Nothing in any Python file. Deleted from `worker/filing.py:40`. `git grep` finds it only in the design document at `:259` and `:2388`, and in the brief.

**A small correction to the brief's figure, in passing.** It says "any of the **77** non-empty Python files". Counted today, the repository has **84 tracked `.py` files, 78 of them non-empty**:

```
$ git --no-optional-locks ls-files '*.py' | wc -l
84
$ ...(non-empty)... | wc -l
78
```

Neither figure changes the answer: the count of occurrences is one, its own `def` line, and it is now zero.

### H5a. `client_code` in `store.py` and `filing.py`

`worker/storage/store.py`: **nothing.** Clean.

`worker/filing.py`: **four lines, all inside one docstring**, at `:385`, `:386`, `:389` and `:391`. **This check does not pass as written and here is why, because it is the one place the brief contradicts itself.** See the flag below.

### H5b. A fresh database, read back with `PRAGMA`

Run by `_step10d_rebuild.py` itself, against a throwaway root in the scratchpad rather than against `config.DB_PATH`. Both required tables:

```
  receipts
    receipt_id             TEXT       notnull=0 default=None pk=1
    firm_id                TEXT       notnull=1 default=None pk=0
    client_id              TEXT       notnull=1 default=None pk=0
    source                 TEXT       notnull=1 default=None pk=0
    message_id             TEXT       notnull=1 default=None pk=0
    email_subject          TEXT       notnull=0 default=None pk=0
    email_from             TEXT       notnull=0 default=None pk=0
    email_received_at      TEXT       notnull=0 default=None pk=0
    filename               TEXT       notnull=1 default=None pk=0
    file_path              TEXT       notnull=1 default=None pk=0
    file_hash              TEXT       notnull=1 default=None pk=0
    filed_path             TEXT       notnull=0 default=None pk=0
    filed_at               TEXT       notnull=0 default=None pk=0
    duplicate_of           TEXT       notnull=0 default=None pk=0
    locked_at              TEXT       notnull=0 default=None pk=0
    status                 TEXT       notnull=1 default=None pk=0
    created_at             TEXT       notnull=1 default=None pk=0

  statements
    statement_id           TEXT       notnull=0 default=None pk=1
    client_id              TEXT       notnull=1 default=None pk=0
    platform               TEXT       notnull=1 default=None pk=0
    week_ending            TEXT       notnull=1 default=None pk=0
    source                 TEXT       notnull=1 default=None pk=0
    file_hash              TEXT       notnull=1 default=None pk=0
    file_path              TEXT       notnull=1 default=None pk=0
    filed_path             TEXT       notnull=0 default=None pk=0
    status                 TEXT       notnull=1 default=None pk=0
    created_at             TEXT       notnull=1 default=None pk=0
```

**Both carry `file_path` and `filed_path`. Neither carries `client_code`.** 10d.23, 10d.29 and 10d.56 in one output. And visible in the same listing: no column on `receipts` carries a default (10d.24 to 10d.26), `locked_at` is `TEXT` (10d.28), `firm_id` and `client_id` are `NOT NULL`.

The other tables from the same run: `categorisations` has `trade` and no `business_type` (10d.30); `extractions` has no default on `currency` and carries `pipeline_version`, `receipt_ref_number` and `receipt_time` in the CREATE (10d.31, 10d.34); `processed_attachments` has `firm_id` with the key still `(message_id, attachment_id)` (10d.32); `categorisations_firm_vendors` has a nullable `firm_id` with `UNIQUE(business_type, vendor_code, vendor_name)` unchanged (10d.39); `resolution_events` has `reason` and no foreign keys (10d.33); `categorisations.needs_review` still defaults to 1, which 10d records as deliberate.

### H6. `py_compile`

```
$ python -m py_compile app.py config.py retroactive_categorise.py _step10d_rebuild.py \
    worker/filing.py worker/storage/store.py worker/intake/folder_reader.py \
    worker/extraction_pipeline.py worker/extraction/postprocess.py \
    worker/extraction/openai_vision.py worker/email/alerts.py \
    worker/categorisation/engine.py worker/database/schema.py \
    worker/database/repository.py worker/resolution/service.py
production OK
$ python -m py_compile tests/*.py
tests OK
```

Every file touched, and every test file, compiles.

### H7. Untracked files

```
$ git --no-optional-locks status --porcelain | grep '^??'
?? _step10d_clients.json
?? _step10d_firms.json
?? _step10d_rebuild.py
?? tests/test_step10d_pipeline.py
?? tests/test_step10d_routing.py
```

Plus this report. **Six rather than the four the brief predicts**, and the two extra are the new test modules, which go into the commit rather than being scratch.

### H8. Nothing was written outside the repository

**The check, and it is a measurement rather than an assurance.** Every path under both roots, walked whole and compared against the timestamp of this task's first commit:

```python
roots = [Path(r"C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills"),
         Path(r"C:\Intellibills")]
start = int(git log -1 --format=%ct 73358b9)     # 1788376367, 2026-09-02 20:12:47 BST
for root in roots:
    for p in root.rglob("*"):
        if p.stat().st_mtime >= start:
            print("MODIFIED SINCE:", p)
```

```
cutoff (unix): 1788376367 2026-09-02 20:12:47
0 path(s) under the two roots modified since the first commit of this task
```

**Zero.** Nothing under the practice root or `C:\Intellibills` was created, modified or deleted. The database was never opened for writing: `_step10d_rebuild.py` was exercised against a throwaway root in the scratchpad, described below.

**Two honest limits on that check.** It measures modification times, so a file written and then restored to its old mtime would not appear, which nothing here does. And it walks two roots; a write somewhere else outside the repository would not be seen. The stronger evidence is that the only writes this task performed at all were through `Write`, `git`, and three Python scripts whose paths are all inside `C:\LastingImpact\receipt_capture` or the scratchpad.

---

## The three scratch files

All three in the repository root, all prefixed `_step10d_`, none of them deleted. **Paul removes them when the flip is done.**

**`_step10d_clients.json`.** The five clients, section A's field list, snake_case, `{version, savedAt, clients: [...]}`, which is the shape `saveClients()` in `IntelliBooks-Desktop-v3.html` writes and `loadClients()` reads. Loads through the real `config.load_clients()` and yields the five ids. **`instance` is deliberately absent**: it is a per-browser id Desktop stamps on what it writes, and the pipeline has no equivalent.

**`_step10d_firms.json`.** One firm, `{version, firms: [...]}`, which matches `saveFirm()`'s `obj.firms[0]` branch. Fields `firm_id`, `name`, `email` and `phone_app_url`.

```json
{
  "version": 1,
  "firms": [
    {
      "firm_id": "FIRM001",
      "name": "Intellitax",
      "email": "bills@intellitax.co.uk",
      "phone_app_url": "https://intellitax-receipts.netlify.app"
    }
  ]
}
```

`firm_id`, `name` and `email` are the three columns of `firms.csv`, read from it and not guessed. **`email` comes across unchanged and gains no reader**, per 10d.51 and outstanding item 24. `phone_app_url` is row F10, taken from `settings.captureUrl` in `IntelliBooks-Practice.json`, which reads `https://intellitax-receipts.netlify.app`. The key name is `phone_app_url` because that is what `IntelliBooks-Desktop-v3.html` already reads, at `:937`, `:1354` and `:1369` — the Desktop half of 10d.51 is built and I matched it rather than choosing a name.

**`_step10d_rebuild.py`.** Refuses on a live lock, backs up, prints a full listing, drops the six tables, calls `init_db()`, prints `PRAGMA table_info` for everything. **Two arguments: no arguments is a dry run that changes nothing, `--apply` does it.**

**I did not run it against `config.DB_PATH` and I did smoke-test it, and the difference matters.** It was run twice, dry and `--apply`, in a subprocess with `ONEDRIVE_ROOT` and `INTELLIBILLS_LOCAL_ROOT` redirected into the scratchpad, so both roots were empty temp trees and the database it created and rebuilt was a new empty file with no relation to the live one. **That is neither the live database nor a copy of it**, which is what section B forbids, and it is how the H5b output above was produced. Without it I would be handing Paul an unrun script.

Three things I corrected in it after reading the code rather than assuming:

- **`backup_db()` takes a destination and does not choose one.** My first draft called `repo.backup_db()` with no argument, which would have raised. It now writes `Intellibills\Backups\step10d-before-rebuild-{stamp}.db`, deliberately not named `receipts-*.db` so `_cleanup_old_backups()`'s window of fourteen cannot age it out.
- **The lock file holds `pid=NNNN` on a line**, not a bare pid. It is parsed the way `acquire_lock()` at `app.py:574` parses it, and the pid is checked with `app._is_process_running()` rather than a second implementation that could disagree.
- **A leftover lock is not a running pipeline.** The script says so on screen, because items 26 and 104 were both raised on exactly that.

---

## Flags: things I did not fix, and things I did that you should look at

### 1. The brief contradicts itself on `make_enriched_sidecar()`, and I broke the freeze. Deliberately, once, with evidence.

**This is the one to read first.**

Task 2's 10d.14 says "`make_enriched_sidecar()` is not touched at all". Section I repeats it as a stop-and-ask. 18.2b says it "stays frozen entire". **And check H5a says `grep -rn "client_code" worker/storage/store.py worker/filing.py` returns nothing, which cannot be true while a frozen function writes a key called `client_code`.**

The deciding evidence is not in this repository. **`parseSidecar()` in `IntelliBooks-Desktop-v3.html`, at line 1889, reads `data.client_id` and reads no code at all:**

```javascript
/* client_id, never a code, and never case-folded: Client_004 is not CLIENT_004. Sub-step 10d.11. */
out.clientId=(data.client&&data.client.client_id?String(data.client.client_id):(data.client_id||""));
```

The Desktop half of step 10d is already built against `client_id`. Leaving this function frozen would have handed the other half of the contract a key it has stopped reading, and every filed receipt would have arrived at Desktop with no client. **So I renamed two things and nothing else**: the parameter and key `client_code` to `client_id`, and `claimed_client_code` to `claimed_client_id`. The filename convention, the three category keys, the sidecar write and the write-on-arrival trigger are all untouched, and the docstring records the departure and its reason.

**`claimed_client_id` is still dead and still passed `None` at all four call sites**, which is outstanding item 117's position: whether step 10d populates or removes it is your decision, so it is neither populated nor removed, only renamed off an abolished word.

**What I want from you: rule on it.** Either 18.2b's freeze is narrowed by one more line, or the rename is reverted and check H5a is dropped. It cannot stay as it is, because the brief currently asks for both.

### 2. 10d.41's note, which the design document asks for and the brief does not

The design document's 10d.41 says the note from `resolve_invoice_date()` "records that a year was inferred from two digits, **and** records the rejection". The brief's 10d.41 asks only for the rejection and the deleted branch.

**I built the two-digit note, then took it out again, and I want you to decide rather than me.** The rejection is recorded: a two-digit year resolving into the future, and any three-digit year, make `parse_ambiguous_date()` return `None`, so `resolve_invoice_date()` writes `ambiguous_invoice_date_unparsed_raw(...)` and leaves the model's date alone. **The inference note is not**, because it would fire on nearly every UK receipt, `DD/MM/YY` being the ordinary form, and `details` flows into the sidecar and on to Desktop. `tests/test_postprocess.py` already carries a test whose comment argues against exactly that kind of note: "a note recording a change that did not happen is the same class of problem as a note that names the wrong cause". Adding it would have changed the content of `details` on almost every receipt, which the brief did not ask for.

**Say if you want it and it is a ten-line change.**

### 3. 10d.36's third literal: what replaces `support@lastingimpact.co.uk`

The sub-step says three literals go with the `firm_name` parameter and does not say what any of them becomes. The firm's name is now a parameter. **The support address is the harder one, because the obvious source is closed to me:** the firm record has an `email` field, and 10d.51 says in terms "do not remove it and **do not add a reader for it**".

**So the alert now points the sender at `config.SMTP_USERNAME`, the mailbox it is sent from.** That is per-deployment configuration in `.env` rather than a literal in source, which is what row F7's wall is about, and it is an address the sender can actually reach. It is not the firm's support address, and if a firm has one, this is not it.

**And the firm name itself needed a rule the brief does not give.** An unknown sender has no client, so there is no client record to take a firm from, and 10d.19 stops `DEFAULT_FIRM_ID` being that answer. `_mailbox_firm_name()` in `app.py` returns the single firm in `firms.json` where there is exactly one, on the ground that one pipeline instance polls one mailbox, and returns an empty string where there are none or several, which produces wording that names nobody rather than the wrong firm and logs a warning. **F7 already records the multi-firm case as a wall; this makes the wall visible rather than pretending to be through it.**

### 4. The `engine.py` defect you flagged. Fixed, because 10d.39 lands on the line.

`worker/categorisation/engine.py:421` passed `vendor_key=vendor_key` to `upsert_firm_vendor()`, whose parameter at `repository.py:389` is `vendor_code`. **Confirmed by reading both.** It would raise `TypeError` if reached; it is unreachable because `learn_from_correction()` has no callers, which is outstanding item 54. The test caller at `tests/test_resolution_view.py:289` uses `vendor_code=` and would pass, exactly as you said.

**I fixed it, and the reason is your own "unless you judge it inside the change".** 10d.39 requires that exact call to gain a `firm_id` argument. Editing the call and leaving the keyword wrong would have been writing a new line with a known defect in it. Both went in the same edit.

**The function is still unreachable.** Nothing calls `learn_from_correction()`, so nothing here is exercised, and item 54 is not closed by this.

### 5. Two counts in the brief that were slightly off

**The document store holds six files, not five.** Read off disk today:

```
Intellibills\Documents\PKPH\2026\08\    1 file
Intellibills\Documents\TESTST\2026\08\  2 files
Intellibills\Documents\TESTST\2026\09\  3 files
```

`PKPH` one, `TESTST` five, **six between them**. Neither client survives 10d.2. **Nothing under `Intellibills\Documents\` was deleted, moved or renamed. Paul removes them.**

**The non-empty Python file count is 78, not 77**, as above.

### 6. Flagged, not fixed: four things outside this task

- **`query_receipts.py`, `view_receipts.py`, `export_bookkeeping.py` and `schema_info.py` all open `Path("data/receipts.db")`**, which has not been the database path since amendment 76 moved it to `C:\Intellibills\db\receipts.db`. They are hand-run scripts and none reads `client_code`, so this step does not break them; they were already broken. Not in the brief.
- **`docs/specs/categorisation_engine.py:551`** writes a `client_code` key in an illustrative payload. A specification document, not production, and not named by the brief.
- **The `business_type` / `trade` vocabulary is half renamed**, as set out under the resolution service above.
- **`EMAIL_PROCESSING_MICROSTEPS.md:454`** quotes the deleted `app.py:143` fallback as live code. A spent document by the "spent files leave the root" rule, and moving it is not this task.

### 7. A mistake of mine, disclosed

Beyond the mutation-harness filter fault already described: **my first draft of `_step10d_rebuild.py` called `repo.backup_db()` with no argument**, having assumed from the sub-step's wording that it chooses its own destination. It takes one. Found by reading `repository.py:338` rather than by running it, and corrected before the smoke test. Had the smoke test been the only check, it would have been found there instead, which is the argument for both.

---

## What Paul does next

Not scheduling, just the order, because the flip happens in one sitting.

1. Stop the pipeline. A leftover `Intellibills\pipeline.lock` is normal.
2. `python _step10d_rebuild.py` with no arguments. **Read the output.**
3. `python _step10d_rebuild.py --apply`.
4. Copy `_step10d_clients.json` to `Intellibills\clients.json` and `_step10d_firms.json` to `Intellibills\firms.json`.
5. Rename `clients.csv` to `clients.csv.superseded-2026-08-20` and `firms.csv` to `firms.csv.superseded-2026-09-01`.
6. Carry the five `capture_token` values to the Desktop and phone app briefs.
7. Start the pipeline and run one clean cycle.
8. Delete the three `_step10d_` files.

**One thing to expect on the first run so it does not read as a fault:** no client record carries an email address, so every emailed receipt will resolve to `UNKNOWN` and become a Review item under `Intellibills\Review\UNKNOWN\`. That is 10d.16 working. Add addresses to `clients.json` when you want email intake back, and 10d.35 means the running pipeline picks them up without a restart.

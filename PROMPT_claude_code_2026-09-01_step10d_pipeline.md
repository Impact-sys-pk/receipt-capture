# AUTOMATIC task: step 10d, the pipeline half. One client registry, the credential, and the database rebuilt

**Written 2026-09-01 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under AUTOMATIC Task Mode in `CLAUDE.md`. **Its "stop and ask" list is unchanged and outranks this file.** Two of its rules bite hard here and this brief is shaped around them rather than against them. See "What you do not do" below.

**This is one of three briefs for step 10d.** The other two are `PROMPT_intellibooks_2026-09-01_step10d_desktop.md` and `PROMPT_phoneapp_2026-09-01_step10d.md`. **All three are written against the same field list, which is section A below, and section A is identical in all three.** If your copy of section A differs from either of theirs, stop: the three have drifted and the flip will not work.

**Position.** HEAD is `10fd03feb9e4c2f8e4e14051c639aca23fe1b688` on `feat/console-phase0`, unless the commit brief `PROMPT_claude_code_2026-09-01_commit_163.md` has run first, in which case HEAD is its commit. **Check and report which.** Amendments 1 to 163 are in the design document.

**Authority.** Section 16 step 10d of `2026-07-25_CONSOLE_DESIGN.md`, sub-steps 10d.1, 10d.4, 10d.11, 10d.13, 10d.14, 10d.16 to 10d.42 inclusive except 10d.38, 10d.51, and 10d.53 to 10d.56. Amendments 105 and 111 carry the field list and its reasoning; 110 to 117 and 120 carry the decisions; 18.2a carries the layout; 18.2b carries the product boundary and the freeze. **Read 10d in the design document before you start.** This brief does not repeat its reasoning.

---

**Line numbers refreshed 2026-09-02, 16:30 BST, after step 10a.** Sub-steps 10a.1 and 10a.2 added three constants and their comments to `config.py`, so every `config.py` line this brief cites moved by eighteen. **All six were re-derived by reading the current file, not by adding a constant, and each now lands on the construct it names.** `worker/filing.py` was edited in place and its line numbers did not move; `app.py`, `worker/database/repository.py`, `worker/intake/folder_reader.py`, `worker/extraction/postprocess.py` and everything under `tests\` were untouched by step 10a. **Read the region before editing it in any case: these numbers move again as soon as this step's first edit lands.**

## A. The field list. Identical in all three briefs

**One client file. `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\clients.json`.** Owned by Intellibills, read and written by both products. JSON, not CSV. **snake_case throughout.**

| Field | Rule |
|---|---|
| `client_id` | `Client_NNN`. System generated, sequential, **unchangeable**. `UNKNOWN` reserved. Names every database row, every message between products, the books filename, both modules' own folders, logs, backups and exports |
| `client_name` | Display only. Freely editable. **Never used to build a path** |
| `client_folder_name` | Names the client folder under `Clients\`. Prefilled from `client_name`, editable, then **fixed once a folder exists** |
| `capture_token` | Random, per client, revocable. Its only job is the phone app link |
| `emails` | An **array** of addresses. One client, several addresses. Not one address for several clients |
| `trade` | Was `business_type`. The trade |
| `entity_type` | Was `clientType`. The legal form |
| `partners` | Array |
| `phv` | Array |
| `vat`, `year_end`, `mtd`, `mtd_basis`, `balance_sheet` | The remaining book attributes, snake_case |

**There is no `client_code`. Not in the file, not on any table, not in any payload.** **That covers folder names, filenames and the contents of files any of the three products writes, not only database columns and payload keys. Each brief names its own instances.**

**The five clients, and nothing is carried across.** Sub-step 10d.2, on Paul's decision of 2026-08-21, amendment 139. Created fresh:

| `client_id` | `client_name` | `client_folder_name` | `entity_type` |
|---|---|---|---|
| `Client_001` | TEST | TEST | sole_trader |
| `Client_002` | Test 2 | Test 2 | sole_trader |
| `Client_003` | Test Company | Test Company | company |
| `Client_004` | Test Sole Trader | Test Sole Trader | sole_trader |
| `Client_005` | Test Partnership | Test Partnership | partnership |

**Numbering restarts at `Client_001`, on Paul's decision of 2026-09-01.** `Client_005` to `Client_010` exist in today's `clients.csv` and are discarded with it.

**The rest of each record, read from `IntelliBooks-Practice.json` on 2026-09-01 and not guessed:** all five have `vat` false and `phv` empty. `Client_005`, Test Partnership, has `partners` `["Partner 1", "Partner 2"]`; the other four have none. `Client_001`, `Client_003`, `Client_004` and `Client_005` have `mtd` false and `year_end` `05/04`. **`Client_002`, Test 2, is the odd one: `mtd` and `yearEnd` are both null and it has no `balanceSheet` key at all.** Only `Client_001` carries `balanceSheet`, and it is false. **An absent attribute is a decision somebody has to make; whoever writes the record says what they wrote and why, and does not silently default it.**

**`clients.csv` is renamed to `clients.csv.superseded-2026-08-20`, not deleted.**

**The five `capture_token` values are generated once, by the pipeline brief, and printed in its report.** Paul carries them to the other two. **Nobody else invents one.**

---

## B. What you do not do, and why the brief is shaped this way

`CLAUDE.md`'s stop-and-ask rule 2 forbids writing anything outside `C:\LastingImpact\receipt_capture`, naming `clients.csv` and the OneDrive tree explicitly. Rule 3 forbids any `INSERT`, `UPDATE` or `DELETE` against `receipts.db`.

**Step 10d needs both. So they are Paul's to run, not yours, and you produce what he runs.**

**You do not create `clients.json`.** You write its exact content to `_step10d_clients.json` **in the repository root**, and Paul copies it out. Same file, same bytes, his hand on the write.

**You do not touch `receipts.db`.** You write `_step10d_rebuild.py` in the repository root: a script that stops on a lock, backs up, drops the affected tables and calls `init_db()`. Paul runs it. **Do not run it yourself, not even against a copy in the repository, because `config.DB_PATH` points outside the repository.**

**You do not rename `clients.csv`.** Paul does, at the same moment he places `clients.json`.

**You do not create `firms.json` either.** Same route: `_step10d_firms.json` in the repository root, and Paul renames `firms.csv` to `firms.csv.superseded-2026-09-01` himself. Sub-step 10d.51.

**All three files are prefixed `_step10d_` and are scratch.** Name them in the report, and delete none of them: Paul removes them when the flip is done.

---

## C. Task 1. Starting state

```
git --no-optional-locks status --short
```

Report it whole. **Expect a clean tree** if the commit brief has run, or the three modified and four untracked files it names if it has not. **Any modified `.py` file that you did not modify means you stop.**

Then confirm, and quote each:

```
python -c "import config; print(config.CLIENTS_CSV); print(config.DB_PATH)"
```

`CLIENTS_CSV` must be `...\OneDrive - Intellitax Accounting Limited\Intellibills\clients.csv` and `DB_PATH` must be `C:\Intellibills\db\receipts.db`. **Both are outside the repository. That is the point of section B.**

```
python -m pytest -q | tail -5
```

Record the pass count. Every later count in your report is against this one.

---

## D. Task 2. The registry, and the code that reads it

**10d.1. Write `_step10d_clients.json`** with the five clients and the field list from section A. `capture_token` for each: generate 32 characters from `secrets.token_urlsafe`, and **print all five tokens in your report**, because the phone app brief needs them and Paul is the only channel.

**10d.4. Strike through, do not delete, `CLAUDE.md`'s "Two rules about `clients.csv`" section**, and add one line saying step 10d retired it and the `emails` array is why. Amendment 111 gives the reasoning: the rule that one client may have two rows differing only in the email column exists because a CSV row cannot hold a list, and its companion rule about the duplicate `client_id` check exists only to protect that arrangement.

**`config.py`.** `load_clients()` at `config.py:126` reads JSON, not CSV, and builds:

- `CLIENTS_BY_ID`, keyed on `client_id`. **New, and it becomes the primary lookup.**
- `CLIENTS`, keyed on each lower-cased address in the `emails` array, one entry per address.
- **`CLIENTS_BY_CODE` is deleted.** **60 occurrences across the repository, counted: 13 outside `tests\` and 47 inside, spread over 17 test files.** Of the 13, one is the definition at `config.py:167` and one is a comment at `worker/filing.py:166`. **The eleven real readers are** `worker/extraction_pipeline.py:190`, `:217` and `:258`; `worker/resolution/service.py:366`; `worker/intake/folder_reader.py:82`; `retroactive_categorise.py:120`; and `app.py:143`, `:374`, `:874`, `:937` and `:1073`. Every one is a `.get(client_code, {})` lookup with a silent fallback. **Report your own count before you change any.**

`CLIENTS_CSV` becomes `CLIENTS_JSON`, pointing at `clients.json`.

**10d.35. Re-read the registry while the pipeline runs.** `config.py:167` loads it once at import and `main()` at `app.py:1203` polls until the process ends, so a client registered mid-run is invisible until a restart. `app.py` stats the file at the top of each `process_once()` and calls `load_clients()` again when the modification time has moved. **Two conditions, both required:** a failed parse keeps the registry already in memory, logs an error, and never empties it and never ends the poll; and any writer uses temp-name-and-rename. **Section 8.6's marker file is struck and not built.**

**10d.13. Delete the fallback at `app.py:143`.** Verified present: `return config.CLIENTS_BY_CODE.get(client_code, {}).get("client_name", client_code)`. It silently substitutes the code for the name whenever the lookup misses. **This is not academic: on 2026-09-01 it filed four TESTST receipts into `Clients\TESTST\` because `clients.csv` had no TESTST row, and IntelliBooks looks under `Clients\Test Sole Trader\` and found nothing, with no message on screen.**

**10d.14. `get_client_directory()` at `worker/filing.py:64` takes `client_folder_name` off the client record.** Verified at that line. **18.2b's freeze governs the rest of that function and the rest is nothing:** the filename convention, the sidecar write and the fact that it writes on arrival are all unchanged. `file_receipt()` may change the corresponding parameter name and nothing else. `make_enriched_sidecar()` is not touched at all.

**10d.14 also deletes `normalise_client_name()` at `worker/filing.py:40`.** 18.2b names the deletion. Confirm by grep, print the output, and report the count: I get its own `def` line and no other occurrence in any of the 77 non-empty Python files.

**10d.11. `scan_inbox()` reads `client_id` out of the item's sidecar** instead of deriving the client from the folder name at `worker/intake/folder_reader.py:81`. The folder name becomes decoration.

**A file with no sidecar therefore has no client.** It gets `source = other` and goes to Review, per 10d.16 and 10d.18. **It is kept and reported, never refused.**

**Correction to the sub-step, and use this rather than what it says.** 10d.11 cites `worker/intake/folder_reader.py:102` for "does not require a sidecar today". Line 102 is `original_name = item.name`. The line that makes the sidecar optional is **line 100**, `sidecar = _load_sidecar(sidecar_path) if sidecar_path else None`. Verified by reading both.

---

## E. Task 3. `UNKNOWN`, the firm, and the four defaults

**10d.16.** A receipt written with `client_id = UNKNOWN` is a review item and reports, and is **never** `status = ok`. The value stays; what goes is its arrival as a fallback rather than as a recorded conclusion.

**10d.17.** Remove `save_receipt()`'s **four** keyword defaults at `worker/database/repository.py:209`. Verified: `firm_id`, `client_id`, `client_code` and `source` are all on that one line. **Python supplies these before the SQL is reached, so removing the column defaults in task 4 without removing these changes nothing.**

**10d.18.** An unresolved client files nothing into `Clients\` and the item goes to `Intellibills\Review\`. **This is the only part of step 10d that reports to the operator.**

**10d.19.** `DEFAULT_FIRM_ID` stops being a fallback:

- `worker/intake/folder_reader.py:88` goes with the unresolved-client case. Verified.
- The client loader refuses a record with no firm.
- `app.py:1045` and `:1061` take the firm from the receipt they already name. Both verified.
- The client is resolved **once before** the per-attachment loop rather than inside it at `app.py:1071`. Verified: that line is `client_id, firm_id = repo.resolve_client_id(email_from)`.
- An unattributable event goes to a reserved firm id, `receipt_events_UNATTRIBUTED.ndjson`. **The name is built twice, identically, at `app.py:102` and `worker/extraction_pipeline.py:96`, and both change.** Both verified.
- **`config.RECEIPTS_LOG` at `config.py:70` is deleted rather than revived.** `tests/test_path_layout.py:83` asserts its value and goes with it. Both verified.

**10d.20.** `repository.py:60` and `:69` return `config.DEFAULT_FIRM_ID` instead of the literal `"INTELLITAX"`. Both verified.

**10d.21.** Rename `ONEDRIVE_ROOT` and `LOCAL_ROOT`. Each names a thing that is not the property that matters, and nothing in the pipeline calls a Microsoft API. **Propose the two names in your report before you rename**, because every path constant in `config.py` derives from them and the design document does not name the replacements.

---

## F. Task 4. The database, rebuilt and not migrated

**Amendment 116. There is nothing worth preserving.** Confirmed by query on 2026-09-01: `receipts` 5 rows, `extractions` 3, `categorisations` 3, `processed_attachments` 1, and seven tables empty, being `categorisations_client_vendors`, `categorisations_firm_vendors`, `categorisations_client_rules`, `email_alerts`, `email_delta`, `resolution_events` and `statements`.

**10d.22.** Edit `schema.py` to the shape wanted, and let `init_db()` create it. **One definition is the only definition.**

Then, all in `schema.py`:

| Sub-step | Change | Verified at |
|---|---|---|
| 10d.23 | `receipts.client_code` column removed | `schema.py:80` |
| 10d.24 | `receipts.firm_id`: `DEFAULT 'INTELLITAX'` removed, `NOT NULL` kept | `:78` |
| 10d.25 | `receipts.client_id`: `DEFAULT 'UNKNOWN'` removed, `NOT NULL` added | `:79` |
| 10d.26 | `receipts.status`: `DEFAULT 'pending'` removed. `save_receipt()` writes the literal at `repository.py:216` so the default is never reached | `:90` |
| 10d.27 | `receipts.email_received_at`: one format, ISO 8601 UTC. **`app.py:926` changes with it**, today `int(intake.source_path.stat().st_mtime)` | `:85`, `app.py:926` |
| 10d.28 | `receipts.locked_at`: `TIMESTAMP` becomes `TEXT`. **`acquire_receipt_lock()` at `repository.py:675` passes `.isoformat()` rather than a `datetime`, and the comparison at `:674` changes with it** | `:210` |
| 10d.29 | `statements.client_code` column removed. One writer, `app.py:890`. Table has 0 rows | `:97` |
| 10d.30 | `categorisations.business_type` renamed `trade` | `:59` |
| 10d.31 | `extractions.currency`: `DEFAULT 'GBP'` removed, **and the twelve `"GBP"` literals become one constant**: six in `app.py`, four in `worker/resolution/service.py`, two in `worker/extraction/openai_vision.py`. Counts verified | `:121` |
| 10d.32 | `processed_attachments` gains `firm_id`, informational, **key unchanged** at `(message_id, attachment_id)`. One writer, `mark_processed()` at `repository.py:263` | `:128` |
| 10d.33 | `resolution_events`: drop `receipt_id`'s foreign key, leave `extraction_id` unconstrained, **and rewrite the comment at `:155` to `:159`, which gives a false reason**: a NULL foreign key value satisfies the constraint, so the case it claims to protect was never at risk | `:172`, `:155` to `:159` |
| 10d.34 | Remove the `ALTER TABLE ADD COLUMN` migrations at `schema.py:180` to `:232`, and **delete two tests with them**: `tests/test_discard_reason.py`'s `test_the_column_exists_on_an_older_database` and `tests/test_filed_at_column.py`'s `test_existing_rows_are_not_back_filled` | see correction below |

**Correction to 10d.34, and this is a real one.** The sub-step says nine migrations. **There are eleven**, at lines 182, 184, 186, 191, 195, 199, 201, 208, 210, 220 and 232. The two the sentence appears to have dropped are `filed_at` at 220 and `reason` at 232, **which are precisely the two the named tests cover**. Both named tests exist, at `tests/test_discard_reason.py:60` and `tests/test_filed_at_column.py:116`. **Remove all eleven. Report the count you find.**

**`categorisations.needs_review INTEGER DEFAULT 1` stays.** It is the only default in the schema pointing the cautious way and 10d records it as deliberate.

**And write `_step10d_rebuild.py`** in the repository root, for Paul. It must, in this order: refuse to run if `Intellibills\pipeline.lock` is held by a live process; call `backup_db()`; print a full listing of the practice root and every client folder; drop `receipts`, `extractions`, `categorisations`, `statements`, `processed_attachments` and `resolution_events`; call `init_db()`; then print `PRAGMA table_info` for every table it created. **`processed_attachments` is free to clear:** Paul confirmed on 2026-08-20 that every folder in the capture mailbox is empty.

---

## G. Task 5. The source word, and three defects that ride with this step

**10d.40. `receipts.source` has four values and no others: `email`, `phone`, `desktop`, `other`.** Each writer declares it, the reader reads it.

- `scan_inbox()` **stops hardcoding** `source="capture"` at `worker/intake/folder_reader.py:114`. Verified exactly.
- **The sidecar stops using its own vocabulary.** `worker/extraction_pipeline.py:220` and `:261` write `"email" if message_id else "folder"`, so today one receipt is `capture` in the database and `folder` in the sidecar. Both lines verified. Both use the four words.
- The phone app writes `phone`, **Add Receipts** writes `desktop`, the email path writes `email`, and a file with no sidecar gets `other`.
- **No migration.** Task 4 rebuilds `receipts`.

**10d.53. `Intellibills\Documents\` is keyed on `client_id` rather than the client code.** Added 2026-09-02 by amendment 169.

`worker/storage/store.py` builds `config.FILES_DIR / client_code / year / month` at **lines 23 and 37**, in `save_file()` and `save_inbox_file()`. Both take `client_code` as their second parameter. **Three callers, all in `app.py`: `:733` for an image embedded in an email, `:918` for the folder intake, `:1097` for an email attachment.** All five lines verified by reading them on 2026-09-02.

**The year and month stay, and this is the reason, because the file has no docstring giving it.** The save happens **before** extraction: `app.py:918` writes the file, `:949` runs the extractor, `:952` files it. At the moment of the write nothing has read the receipt, so there is no invoice date to file by, and `app.py:367` takes the invoice date out of the extraction record, which does not exist yet. Arrival also never needs correcting where an invoice date does, so no file ever has to move. **Do not change the year and month to a tax year.**

**The folders on disk are `PKPH` and `TESTST`, five files between them.** Neither client survives 10d.2. **Leave them exactly where they are, name them and their file count in your report, and Paul removes them.** Do not delete, move or rename anything under `Intellibills\Documents\`.

**10d.54. `Intellibills\Review\` is keyed on `client_id` rather than the client code.** Added 2026-09-02 by amendment 169.

`_review_dir_for_client_code()` at `worker/filing.py:155` becomes `_review_dir_for_client_id()`, and **`file_review()`'s `client_code` parameter at `worker/filing.py:118` changes with it.** Both verified.

**Its docstring survives intact and you should read it before changing the function.** It explains that the folder left the client folder because a receipt awaiting a human is work in progress rather than a document the client is entitled to see, and that it is keyed on the code rather than the name because the name could drift. **A `client_id` cannot drift either, so the reasoning holds word for word and only the field changes.**

**`_scan_other_clients_for_receipt()` at `worker/filing.py:303` needs no change.** It iterates `config.REVIEW_ROOT` and every subfolder is still one client's. **Confirm that rather than assuming it.**

**10d.55. A statement gets a copy in `Intellibills\Documents\` before it is filed.** Added 2026-09-02 by amendment 169, Paul's decision.

The statement branch at **`app.py:858` to `:902`** calls `save_inbox_file()` first, the way the receipt branch does at `app.py:918`, and passes that path to `file_statement()` at `app.py:876`.

**Today that branch never calls into `worker/storage/store.py` at all.** `worker/filing.py:111` copies the statement from the inbox straight into `Clients\<name>\Statements\<tax year>\<platform>\`, so **that is the only copy and a statement cannot be reconstructed where a receipt can.** Searched for `save_file` and `save_inbox_file` in that branch and found neither.

**The `statements` table has 0 rows**, so nothing on disk is affected and there is nothing to migrate.

**10d.56. `statements` gains `filed_path`, and `file_path` means the same thing on both tables.** Added 2026-09-02 by amendment 169, Paul's decision.

`receipts` has both, verified in `worker/database/schema.py`: **`file_path` at `:87`** for the copy in `Intellibills\Documents\` and **`filed_path` at `:89`** for the copy in the client folder. **`statements` has only `file_path`, at `:102`**, and `app.py:898` writes the client folder path into it.

**So one column name means the original on one table and the copy on the other.** After this, `file_path` is the document store's copy on both and `filed_path` is the client folder's copy on both.

**`save_statement()` in `worker/database/repository.py` changes with it**, and `app.py:890` to `:899` with that.

**`app.py:361` is the line that shows why it matters:** it takes `receipt["file_path"]` as the file to copy from when filing, and `app.py:362` skips the receipt if that file is missing. The same code written against a statement would copy the filed copy onto itself.

**10d.51. `Intellibills\firms.csv` becomes `Intellibills\firms.json`, and it takes the phone app address.** Added 2026-09-01 by amendment 164, Paul's decision.

`load_firms()` at `config.py:150` reads JSON. **snake_case throughout, matching `clients.json`.** The record gains the phone app address, which is row F10 of `2026-08-20_LIST_settings_firm_and_client.md` and lives in `IntelliBooks-Practice.json` as `settings.captureUrl` today.

**One reader in the whole system, measured rather than assumed:** `config.FIRMS` at `config.py:168`, read at `app.py:839` and nowhere else. IntelliBooks does not read `firms.csv` at all. **So the conversion is that one function plus the constant's name.**

**The `email` column comes across unchanged rather than being quietly dropped.** It is outstanding item 24: loaded into `config.FIRMS` and read by nothing, and one of the three fields a firm currently is. **Do not remove it and do not add a reader for it.**

**You do not write `firms.json`, for the same reason you do not write `clients.json`.** Write its content to `_step10d_firms.json` in the repository root and Paul places it.

**A third firm file was proposed on 2026-09-01 and rejected**, so if you find yourself wanting one, stop and report it.

**10d.36. `send_unknown_sender_alert()` at `worker/email/alerts.py:54` takes a `firm_name`**, the way `send_no_attachment_alert()` at `:11` already does. Three literals go with it: `support@lastingimpact.co.uk` at `:69`, and `Lasting Impact` at `:75` and `:80`. All five lines verified. **This is the only automatic email that reaches somebody who is not a known client, so it is the first thing an unregistered sender sees, and it currently names the wrong company.** Row F7 of `2026-08-20_LIST_settings_firm_and_client.md`, which records it as a wall: a literal in source cannot vary by firm.

**10d.37. Delete `EXPORTS_DIR` at `config.py:56` and its `mkdir` at `:95`.** No reader outside `config.py` and `tests/test_path_layout.py:40` and `:112`, which go with it. All four verified. **The folder itself stays**: `Intellibills\Exports\` holds `2026-08-18_EXPORT_categorisations_client_vendors.csv`, the only thing of value the database ever held, 100 rows, all for the old `Client_006`.

**10d.39. `categorisations_firm_vendors` gains a nullable `firm_id`, written and not read.** The unique key does not change, so behaviour does not change and the learned pool stays shared. `upsert_firm_vendor()` at `repository.py:389` takes the firm and writes it. **The engine resolves the firm from the `client_id` it already receives rather than gaining a parameter**, which avoids touching `categorise()`'s five production call sites at `app.py:376`, `worker/extraction_pipeline.py:191`, `worker/resolution/service.py:643` and `:1034`, and `retroactive_categorise.py:133`. All verified. **This comes after 10d.19.**

**A defect found while verifying 10d.39, flagged not fixed unless you judge it inside the change.** `worker/categorisation/engine.py:421` passes `vendor_key=vendor_key` to `upsert_firm_vendor()`, whose signature at `repository.py:389` names that parameter `vendor_code`. **That call would raise `TypeError` if reached.** It is not reached today because `learn_from_correction()` is unreachable, which is outstanding item 54. The test caller at `tests/test_resolution_view.py:289` uses `vendor_code=` and would pass. **Report it either way.**

**10d.41. A two-digit year that resolves into the future is rejected, and the three-digit branch is deleted.**

`if c < 100: year = 2000 + c` is at `worker/extraction/postprocess.py:60`, verified, so `01/01/99` becomes **2099**. **Keep `2000 + c`, and where that year is later than the current year treat the date as unreadable and return `None`.** **No century pivot:** a cutoff tight enough to turn 99 into 1999 turns 28 into 1928, so the system would be choosing between 1928 and 2028 on its own. `CLAUDE.md`'s closing rule governs: if something is uncertain, mark it for review and do not guess.

`:62` to `:64`, the `elif c < 1000` branch, is **deleted**. Verified: identical body to the branch above it, a comment claiming "treat as 2000s" while `2000 + 999` is 2999, and a three-digit year is a misread rather than a year.

**Correction to 10d.41.** It calls the containing function `_parse_numeric_date()`. **No such function exists**, zero occurrences across every Python file. The function holding lines 60 to 66 is **`parse_ambiguous_date(raw, prefer_dayfirst)` at `postprocess.py:28`**. The line contents the sub-step cites are exactly right; only the name is wrong. Its later sentence is sound: `resolve_invoice_date()` is at `postprocess.py:139` and is where the note comes from, because `parse_ambiguous_date()` returns a date or `None` and has no note channel.

**10d.42. Identifying the gross figure. Assume, verify, and flag rather than guess.**

**Nothing in this is a VAT question and the naming must stop saying it is.** `apply_vat_inclusive_swap()` at `postprocess.py:88`, its `rate_tol = 0.03` at `:113` and the wording of its note are all renamed to say what they do, which is **establish which figure is the gross**. The VAT figure is the evidence, not the subject. Both line numbers verified.

**The rule.** Where a receipt yields a money figure and a VAT figure and no gross, **assume the figure is the gross**, because Paul's observation is that a receipt showing two numbers always shows gross and VAT. **Verify it:** the implied rate is the VAT divided by the figure less the VAT, and it must come out at a recognised rate within a **rounding allowance only**, a fraction of a percentage point. **If it verifies, accept:** gross is the figure, net is the figure less the VAT. **If it does not verify, change nothing and route to Review**, with the implied percentage in the note.

**Three things this must not become.** Not **gated on the client's VAT registration**: a non-registered client's expense is the gross, so getting this wrong overstates their profit and loss by the VAT, which makes it matter more for them and not less. No **per-rate window and no minimum receipt size**, both designed and then made unnecessary by the assume-and-verify shape. And the recognised rates come from **18.4's vocabulary rather than a literal list**, which today is `common_rates = [0.2, 0.05]` at `postprocess.py:111`, verified.

---

## H. Verify, and quote every output

1. `python -m pytest -q | tail -20`. **Report the count against task 1's**, and name every test you deleted or edited and why.
2. `python -c "import config; print(sorted(config.CLIENTS_BY_ID))"` prints the five ids from section A.
3. `grep -rn "CLIENTS_BY_CODE" .` returns nothing outside `.git` and your own report.
4. `grep -rn "client_code" --include=*.py .` — report every survivor with a one-line reason. Some are legitimate: the phone app's own payload is not yours, and a test fixture may keep one deliberately.
5. `grep -rn "normalise_client_name" .` returns nothing.
5a. **`grep -rn "client_code" worker/storage/store.py worker/filing.py` returns nothing**, which is 10d.53 and 10d.54.
5b. **`python -c "import worker.database.schema as s; print([l for l in s.__doc__ or [] ])"` is not the check. Instead: create a fresh database with `init_db()` and print the columns of `receipts` and `statements` with `PRAGMA table_info`.** Both must have `file_path` and `filed_path`, and neither must have `client_code`. That is 10d.23, 10d.29 and 10d.56 in one output.
6. `python -m py_compile` every file you touched.
7. `git --no-optional-locks status --porcelain` and confirm the only untracked files are your report, `_step10d_clients.json`, `_step10d_firms.json` and `_step10d_rebuild.py`.
8. **Confirm you have not written outside the repository**, and quote the check you used.

Then commit. One commit, message per `CLAUDE.md`'s template, and `git push --dry-run` before the push. Branch `feat/console-phase0`, fast-forward only, never `--force`.

---

## I. Stop and ask about

Everything on `CLAUDE.md`'s list, unchanged. In particular, and repeated because this task walks right up to them:

- **Any write outside `C:\LastingImpact\receipt_capture`.** Section B exists so you never need one.
- **Any `INSERT`, `UPDATE` or `DELETE` against `receipts.db`.** You write the script; Paul runs it.
- The two names for `ONEDRIVE_ROOT` and `LOCAL_ROOT` at 10d.21, which the design document does not give.
- Any place this brief and the design document disagree that I have not already marked as a correction.
- Anything in `get_client_directory()`, `file_receipt()` or `make_enriched_sidecar()` beyond what 18.2b's narrowed freeze permits.

---

## J. Not in this task

**10d.2, 10d.3, 10d.12, 10d.15, 10d.38, 10d.57 and 10d.58** are the IntelliBooks brief. **10d.5 to 10d.10 and 10d.43 to 10d.50** are the phone app brief. Do not touch `IntelliBooks-Desktop-v3.html` or anything under `Intellibills\PhoneApp\`.

**Nothing in step 10f is in this task.** The copy into `Clients\` still happens on arrival. 18.2b's freeze on that trigger holds until 18.3's handoff passes its acceptance test, and this brief changes only where the folder name comes from.

**Do not `git init` anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`, and do not add any part of it to this repository.** `Intellibills\PhoneApp\` was created on 2026-09-01 and is deliberately not in a repository.

**Do not send or act on `PROMPT_claude_code_step10a_and_10b.md`**, written against a folder scheme abandoned in July.

---

## K. Report to a file

`C:\LastingImpact\receipt_capture\2026-09-01_REPORT_claude_code_step10d_pipeline.md`, written before you stage anything so it lands in the same commit.

Include every output from tasks 1 and H, the enumerated list of `CLIENTS_BY_CODE` readers before you changed them, the eleven-or-otherwise migration count, the five `capture_token` values, and your proposed names for the two roots.

**And four things I want back.**

**Were my five corrections right?** `folder_reader.py:100` not `:102`, eleven migrations not nine, `parse_ambiguous_date()` not `_parse_numeric_date()`, and the two counts I did not correct but did verify, the twelve `"GBP"` literals and the five `categorise()` call sites. Tell me any I got wrong.

**Did 10d.53 and 10d.54 exist when you read this brief's first version?** They did not. **The first version of this brief deleted `client_code` and did not mention `worker/storage/store.py` or `_review_dir_for_client_code()` once**, so two folder layouts would have lost their key mid-task. Paul found it by asking whether the client code was going. **Tell me whether the two sub-steps as now written are enough to do the work without stopping.**

**Did I get the `CLIENTS_BY_CODE` count right?** 60 occurrences, 13 outside `tests\`, eleven of them real readers, 47 across 17 test files. I enumerated rather than estimated, but I enumerated with grep and grep is a filter. **If a reader reaches that dictionary by another route, name it.**

**Did anything in `worker/resolution/service.py` need changing that this brief does not name?** It is 1,187 lines, I have read perhaps 200 of them, and it is the largest file that touches client identity. **If it did, that is my omission and I want it named as one.**

**And `Client_002`.** Test 2 has no `yearEnd`, no `mtd` and no `balanceSheet` in `IntelliBooks-Practice.json`. Whatever you write for it in `_step10d_clients.json` is a decision somebody has to make, and it is not in the design document. **Say what you wrote and why, and flag it for Paul rather than burying it.**

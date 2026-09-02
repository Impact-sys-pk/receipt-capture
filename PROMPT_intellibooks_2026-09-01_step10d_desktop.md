# Work plan: step 10d, the IntelliBooks Desktop half. One client file, no client codes

**Written 2026-09-01 by the consultant session, and executed by the consultant session. Paul confirmed on 2026-09-01 that this session writes `IntelliBooks-Desktop-v3.html`.**

**This is not pasted into another session.** It is the third of three step 10d documents and it is a work plan rather than a brief, because the session that wrote it is the session that carries it out. The other two are briefs and are pasted: `PROMPT_claude_code_2026-09-01_step10d_pipeline.md` goes to Claude Code, `PROMPT_phoneapp_2026-09-01_step10d.md` goes to whoever works the phone app.

**All three are written against the same field list, which is section A below, and section A is byte-identical in all three**, checked by hash on 2026-09-01. **If it ever differs, stop: the three have drifted and the flip will not work.**

**The file.** `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\IntelliBooks-Desktop-v3.html`. One file, 199,451 bytes, 3,307 lines as at 2026-09-01. No test suite.

**Authority.** Section 16 step 10d of `2026-07-25_CONSOLE_DESIGN.md`, sub-steps 10d.2, 10d.3, 10d.12, 10d.15, 10d.38, and the Desktop side of 10d.43 to 10d.50. Amendments 105 and 111 carry the field list. **Read 10d in the design document before you start.**

---

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

## B. How this file is worked. Four rules, and they held through ten changes on 2026-08-31 and 2026-09-01

1. **Copy the file to `IntelliBooks-Desktop-v3.html.bak-before-step10d` before any edit, and check the copy matches.**
2. **Print the whole diff afterwards and read it. Every hunk must belong to the change.**
3. **Extract the single `<script>` block and pass `node --check` on it.**
4. **Pull each changed function out of the saved file and run it in node against real data before calling it done. Reading the code is not checking it.**

**Every change gets an item in `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`** saying what changed, what was checked and how, the backup name, and what was flagged and not fixed.

**This change is large enough to break rule 4 if you treat it as one change.** Do the sections below in order, back up and check between them, and say in the change log where each backup sits.

---

## C. Task 1. Read the client list from `clients.json`, and stop holding one

**10d.3. IntelliBooks stops holding its own client list and reads `clients.json`.**

Today the list is `practice.clients` in `IntelliBooks\IntelliBooks-Practice.json`, five records with `id`, `name`, `code`, `created`, `clientType`, `partners`, `vat`, `mode`, `phv`, `yearEnd`, `mtd`, `mtdBasis` and, on one, `balanceSheet`.

After this change the list comes from `Intellibills\clients.json` and IntelliBooks writes back to the same file. **It is read and written from both sides**, which is one of the two reasons amendment 111 chose JSON over CSV: IntelliBooks has a correct CSV reader at `parseCSV()`, line 983, and no CSV writer.

**Write with temp-name-and-rename**, the same rule amendment 104 sets for the inbox JSON and 10d.35 sets for the pipeline's reader. The pipeline re-reads this file whenever its modification time moves, so a half-written file would be read.

**`IntelliBooks-Practice.json` is retired with nothing left in it, and no third firm file is created.** Sub-step 10d.52, amendment 164, Paul's decision of 2026-09-01.

Besides the client list it holds five things. `settings.uploadKey` goes at 10d.7. **`settings.captureUrl` becomes the phone app address on `Intellibills\firms.json`**, which is row F10 and the only firm setting it held. **And `version`, `savedAt` and `instance` are per-file housekeeping rather than firm data**: `instance` is a per-browser id generated at line 593 from `localStorage["ib3_instance"]`, stamped on save at 671 and 690, and compared at 718 to notice when another browser has written the same file. **Stamp all three on whatever you write, the way you already do on every books file.**

**The file is renamed `IntelliBooks-Practice.json.superseded-2026-09-01` rather than deleted.**

**And `firms.csv` becomes `Intellibills\firms.json`**, sub-step 10d.51. That is the pipeline brief's change, not yours, but you read and write that file for the phone app address, so the shape matters to you: JSON, snake_case, one file per owner beside `clients.json`. **A `firm-settings.json` was proposed on 2026-09-01 and rejected**, because firm data in two files is worse than a file extension.

**IntelliBooks never reads `clients.csv` today.** One occurrence of the string in the whole file, at line 316, inside a `<p class="muted small">` help paragraph. Not code. Correct that paragraph's wording while you are in there.

---

## D. Task 2. Every path stops coming from the client's name

**10d.15. The `getDir(["Clients", ...])` sites take `client_folder_name` instead of `safeName(c.name)`.**

**Correction to the sub-step, and it matters because it says four.** There are **nine**, counted across the file:

| Line | What it opens |
|---|---|
| 703 | `Clients\{name}\IntelliBooks` — a legacy migration read, and **the only one using `safeName(client.name)` rather than `safeName(c.name)`** |
| 1165 | `Clients\{name}\HMRC Summaries`, read |
| 1181 | `Clients\{name}\HMRC Summaries`, read |
| 1793 | `Clients\{name}\Receipts`, read, inside `listReceiptYears()` |
| 1819 | `Clients\{name}\Receipts\{year}`, read, inside `scanFiledReceipts()` |
| 1978 | `Clients\{name}\Handover Pack\{date}`, create |
| 2475 | `Clients\{name}\Receipts\{taxYear}`, create, inside `fileReviewReceipt()` |
| 2847 | `Clients\{name}\{subParts}`, create, inside `writeClientFile()` |
| 3105 | `Clients\{name}\IntelliBooks`, read |

**All nine change. `safeName()` at line 622 is then dead for this purpose**, because `client_folder_name` is already a folder name and must not be cleaned again: cleaning it a second time is how the two products came to disagree. **Check whether `safeName()` has any other caller before you delete it, and report either way.**

**There is one more place the client name builds a path, and 10d.15 does not name it.** `fileReviewReceipt()` writes a `filed_path` string at line 2519 as `` `Clients\\${safeName(c.name)}\\Receipts\\${taxYear}\\${finalName}` ``. **That is a string written into data, not a folder call, and it must change with the nine.** Found by searching for `Clients\\` rather than for `getDir`.

**Why this matters concretely.** On 2026-09-01 the pipeline filed four receipts into `Clients\TESTST\` while this file looked in `Clients\Test Sole Trader\`, and `scanFiledReceipts()` at line 1820 catches the failure with `catch(e){return;}` and a comment reading "nothing filed for this year yet". **The Receipts tab showed nothing and said nothing.** Consider whether that silent return should stay silent; **flag it rather than changing it, because it is not in step 10d.**

---

## E. Task 3. The books files

**10d.2. All seven books files in `IntelliBooks\Books\` are retired, including the orphan `PSHIPN-books.json`.** Nothing is migrated. The five test clients are created fresh in the new shape and `chartFor()` builds their books.

**The filename takes `client_id`.** Amendment 105 gives `client_id` the books filename, so `TEST-books.json` becomes `Client_001-books.json` and so on for the five. **Every place that builds or reads a books filename from `code` changes with it.** Enumerate them and list them in your report.

**Five books files exist today**, at 43,742 to 46,009 bytes each, all written 2026-09-01 10:32 UTC, each carrying 111 to 118 categories, a `chartSource` and a `chartPublished` key. **So the chart import from IntelliCharts has already run on all five and that work is not to be lost by accident**: record in the change log what the fresh books get for those keys, and whether the chart has to be re-imported after the rebuild.

**One rule about retiring them: rename, do not delete.** `Books\{CODE}-books.json.superseded-2026-09-01`, and the same for the `Backups\` copies, which are ten files. **Nothing in step 10d authorises deleting a books file.**

---

## F. Task 4. Add Receipts writes a sidecar

**10d.12. `importToInbox()` starts writing a sidecar carrying `client_id`.**

`importToInbox()` is at line 1688 and is what the **Add Receipts** control calls. Today it opens `getDir([PIPE_DIR,"Receipt Inbox",c.code],true)` at line 1691 and copies the file alone, at lines 1702 to 1706. **There is no sidecar, so that route has no client in the item.**

Two changes:

**The folder comes from `client_folder_name`, not `c.code`.** The phone app does the same at 10d.6, so both writers into `Receipt Inbox\` agree. **The folder name is decoration after 10d.11** and the pipeline no longer derives the client from it, but two writers using two conventions is what this whole step exists to end.

**Each copied file gets a sidecar beside it carrying `client_id` and `source: "desktop"`.** Per 10d.40, `receipts.source` has four values and no others: `email`, `phone`, `desktop`, `other`. **Add Receipts writes `desktop`.** A file with no sidecar gets `other` and goes to Review, and that is the pipeline's behaviour, not something for you to implement.

**Match the sidecar shape the pipeline already reads.** `scan_inbox()` at `worker/intake/folder_reader.py` reads the sidecar and tells a statement from a receipt by its `type` key. `parseSidecar()` in this file, at line 1711, is the reader on your own side and takes `data.client.code` or `data.client_code` at line 1725. **Both sides change together: agree the shape with the pipeline brief's field list and write `client_id`, not a code.**

---

## G. Task 5. Sample data stops writing category names into a code field

**10d.38. `loadSampleData()` writes category names into a field that holds codes.**

**Correction to the sub-step, and this one is badly wrong.** It cites `IntelliBooks-Desktop-v3.html:2606`. Line 2606 is `$("vat-report-card").style.display="block";`, inside the VAT report renderer, and has nothing to do with this. **The real locations, verified by reading:**

- `function loadSampleData(){` is line **3167**
- the five sample receipts are the `rs` array at **3204 to 3210**
- the category strings are at **3205 to 3209**: `"Motor expenses"`, `"Sundry expenses"`, `"Repairs and maintenance"`, `"Parking and tolls"`, `"Fuel"`
- `category:catg` is written into each receipt at **3216**
- the linked transfer pair gets `category="(Transfer)"` at **3203**

**Since the chart adoption, `t.category` and a receipt's `category` hold the four-digit code and the name is display only.** So every sample receipt lands with a category the chart does not contain, and the sample transactions land uncategorised.

**Fix the five to codes from the client's own chart**, read out of `books.categories` rather than typed, so a sample cannot go stale again when a chart changes.

**`category="(Transfer)"` at 3203 is outstanding item 56 and is not this task.** Leave it and say so in the change log.

**Why it is here.** 10d.2 recreates the test clients with empty books, and this function is the only way to get transactions into a fresh one, so it is the first thing the day's stage 5 reaches for. It is also the source of the demo version's data.

---

## H. Task 6. The setup link, and who owns each setting

**10d.43. "Capture" stops meaning this app.** It becomes **the phone app** throughout: F10 the phone app address, C18 the phone app token, and the link the **Phone App Setup Link**. **"Capture" is left meaning the mailbox and nothing else**, which is `capture@lastingimpact.co.uk`, row F3. The word currently means five things.

**10d.44. The setup link carries every firm-owned setting, always, as a complete statement.**

`copyCaptureLink()` is at line 1201. Today it adds a parameter only when the value is truthy: `if(c.vat)link+="&vat=1"` at 1208, `if(c.mode==="confirm")` at 1209, `if(c.phv&&c.phv.length)` at 1210. **And the phone only takes a value when the parameter is present**, at `index.html:200` to `:202`. **So the two halves conspire and a link can turn a setting on and never off.** `&vat=0` and an empty `&phv=` become meaningful, and the link always carries every firm-owned setting.

The link also stops carrying the shared key. `&k=` comes off, because 10d.5 replaces it with the per-client `capture_token`, and 10d.7 removes the shared `UPLOAD_KEY` in the same commit with no fallback left working. `copyCaptureLink()` reads that key from `practice.settings.uploadKey` at line 1204 and refuses without it at 1206; **both go**.

**10d.45. Client-owned settings never appear in the link at all**, so the firm cannot overwrite a choice that is not theirs.

**10d.48. Confirm mode is the client's alone and off by default.** C4, settled by amendment 152. **It comes off the firm's side entirely:** out of the client **Edit** window, out of the link, and off Client Settings. The client turns it on in the phone's own settings screen. Today it is `mode` on the client record and is read only to build `&mode=confirm`.

**10d.49. The PHV platforms and the statement week ending day are the firm's alone and the client cannot change them.** C5 and C6. Shown **read-only** on the phone so the client can see what applies. **C6 exists only on the phone today**, at `index.html:244`, where the firm cannot read it, restore it or know it changed. **So the week ending day becomes a field on the client record here**, and that is new: it has no home on this side at all.

**10d.50. PHV settings appear only on a PHV driver's phone app.** Currently offered to every client. That is the phone app's brief, and it is here so you know the client record has to say whether the client is a PHV driver, which the `phv` array already does.

**10d.47. A change to a firm-owned setting notifies the client, probably by email.** A third outbound message beside the no-attachment and unknown-sender alerts. **That is the pipeline's to send, not yours**, and it lands with 10d.36. Named here so you know the notification exists when you change a setting.

---

## I. Task 7. The HMRC summary output stops carrying the client code

**Sub-steps 10d.57 and 10d.58. Added 2026-09-02 by amendment 169, Paul's instruction.**

**Both files were read off disk on 2026-09-02**, in `Clients\Test Sole Trader\HMRC Summaries\`, and neither was in this plan's first version.

**10d.57. The filenames.** They are `testst-hmrc-2025-04-06-to-2026-04-05.csv` at 1,229 bytes and `testst-archive-2025-04-06-to-2026-04-05.json` at 1,974 bytes. **The prefix is the client code in lower case.** `client_id` replaces it, so `client_004-hmrc-...` in whatever case the rest of the naming settles on. The writer is reached through `getDir(["Clients",safeName(c.name),"HMRC Summaries"])` at lines 1165 and 1181.

**10d.58. The archive JSON's `code` field.** The file carries `"client": "Test Sole Trader"` and `"code": "TESTST"`. **`client_id` replaces `code`. `client` stays, as the display name.**

**Three keys in that file are untouched and you should not tidy them.** `"chartSource": "SALE_OF_SERVICES.csv"` and `"chartPublished": "2026-09-01 11:11 BST"` are the provenance stamp that makes the archive a point-in-time record rather than a report: re-running the summary under a republished chart does not reproduce it, and that is the point of the two keys. `"version": 1` is the file's own schema version and is not this change.

**The example on disk is empty.** Every box 15 to 30 reads 0.00, `accounts` is `[]`, and the reconciliation agrees at zero. **So a test that only checks the file is written proves nothing here. Post a transaction first.**

**These two would have been caught anyway**, by the `grep` for surviving `.code` references in the verification list, **but they would have been caught as a surprise mid-task rather than as a sub-step.**

---

## J. Verify, and quote every output

1. **The diff, whole.** Every hunk named and attributed to a task above.
2. **`node --check` on the extracted script block.** Quote the result.
3. **`grep` the file for `c.code`, `client.code`, `\.code` and `safeName(` and report every survivor with a one-line reason.** Some are legitimate; a code that has genuinely gone should be gone everywhere.
4. **`grep` for `Clients\\` and confirm the tenth site at line 2519 changed with the nine.**
5. **`grep` for `-books.json` and confirm every filename builder takes `client_id`.**
6. **Run these four functions in node against a real books file**, per rule 4: `listReceiptYears()`, `scanFiledReceipts()`, `importToInbox()`'s path builder, and `loadSampleData()`'s receipt loop. Quote the output of each.
7. **Open the app and check on screen**, naming what you clicked: select **Test Sole Trader**, open the **Receipts** tab, and confirm the year dropdown offers **2025-26** and **2026-27** and that **2025-26 shows 2 receipts and 2026-27 shows 2 receipts**. Those four are on disk today under `Clients\Test Sole Trader\Receipts\`. **If you see 4 in one year or 0 in either, stop and report it.**
8. **Change log item written**, with the backup names, what was checked and how, and everything flagged and not fixed.

---

## K. Stop and ask about

- **Anything that deletes a books file.** Rename only.
- **Anything that would need a second firm file.** Amendment 164 settled that there is one, `firms.json`, and `firm-settings.json` was rejected.
- **Any place this brief and the design document disagree** that I have not already marked as a correction.
- **Anything you would change beyond what the tasks above describe**, including an obvious improvement. Flag, do not fix.
- **The silent `catch(e){return;}` at line 1820.** Named in task 2 as a flag, not a change.

---

## L. Not in this task

**10d.1, 10d.4, 10d.11, 10d.13, 10d.14, 10d.16 to 10d.42 except 10d.38** are the pipeline brief. **10d.5 to 10d.10** are the phone app brief. Do not edit anything under `C:\LastingImpact\receipt_capture` or `Intellibills\PhoneApp\`.

**Nothing in step 10f is in this task.** `fileReviewReceipt()` keeps writing into `Clients\`; 10f.14 stops it, and 10f is not this step. `get_client_directory()` on the pipeline side is kept and repointed, per 10f.17.

**Nothing in step 10e or 10g is in this task**, including the per-account status guard at 10g.9 and the six 10e sub-steps already built on 2026-08-31.

---

## M. Report

**An item in `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`**, per the standing convention, **and** a report at `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\Docs\2026-09-01_REPORT_desktop_step10d.md`.

**Four things I want back.**

**Were my two corrections right?** Nine `getDir` sites rather than four, and `loadSampleData()` at 3167 with the categories at 3205 to 3209 rather than 2606. Tell me if either is wrong.

**How many places build a books filename?** I told you to enumerate them and did not enumerate them myself. Correct me.

**Does `safeName()` survive?** I said check before deleting. Say what you found.

**And what the fresh books get for `chartSource` and `chartPublished`.** All five books files carry them today and I do not know whether `chartFor()` sets them or whether the chart has to be re-imported from IntelliCharts after the rebuild. **If it does, that is a step nobody has written down.**

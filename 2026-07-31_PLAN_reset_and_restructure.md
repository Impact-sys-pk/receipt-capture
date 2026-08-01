# Plan: the combined clean-slate reset and practice root restructure

**Written 2026-07-31 by the consultant session, amended 2026-08-01.** This is the plan required by design document sections 17.5 and 17.5a: every stage enumerated before anything is deleted.

> # STATUS 2026-08-01: STAGES 1 TO 3 ARE DONE. STAGE 4 IS PART DONE. STAGES 5 AND 6 ARE NOT STARTED.
>
> ~~Nothing in this plan has been run.~~ **The reset was executed on 2026-08-01 by Paul and the implementation session.** What was actually done, what deviated from this plan and what remains is in **section 0.7**. Read that before any other section, because much of what follows below is now a record of a state that no longer exists.
>
> **Three things happened that this plan did not specify, and one of them is a correction to a line in it that would have destroyed real client records.** All three are in 0.7.

Authority: `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md`, sections 17.5, 17.5a, 18.2, 18.2a, 18.2b and 18.3. Where this plan and that document disagree, the design document wins and this plan is wrong.

---

## 0. Read this before the stages

Three things came out of writing the plan that change what the operation is. Two of them mean the plan cannot be executed as 17.5a describes it until Paul has decided something.

### 0.1 Stage 5 is much larger than "change the code, both sides"

**17.5a stage 5 reads as a path change. It is not. It is the removal of the pipeline's only route into the books, with no built replacement.**

Traced today, and each half read from the file:

- Intellibills files a receipt to `Clients\{client name}\Receipts\{tax year}\`, at `worker/filing.py:78`, and writes a sidecar beside it.
- IntelliBooks Desktop reads that same folder, at `IntelliBooks-Desktop-v3.html:1281`, in `scanFiledReceipts()`, and passes what it finds to `ingestReceiptFiles()` at line 1288. It needs the sidecar; the image alone becomes an `img_` entry with no supplier and no amount.

**So `Clients\{name}\Receipts\{tax year}\` is today the interchange between the two modules, exactly as 18.2c says it is.**

Section 18.2b abolishes both halves of that. Intellibills never writes into `Clients\` at all, and the copy that does go there is image only with no data file. Section 18.3 replaces the interchange with a push into `IntelliBooks\Inbox\`, a folder Desktop owns and drains.

**`IntelliBooks\Inbox\` does not exist, nothing writes to it, and nothing drains it.** It appears in 18.2a's tree and nowhere in either codebase.

Two consequences.

**Stage 6 cannot run as written.** "One receipt end to end, then a Review item, then a post" requires a receipt to travel from capture into the books. After stage 5 as specified, no such route exists.

**And several things hang off filing into `Clients\` that 18.2b does not mention.** `receipts.filed_path`, `receipts.filed_at`, `mark_receipt_filed()`, and the `already_filed` guard the resolution service gained at amendment 30 all describe filing into the client folder. If the pipeline no longer files there, what "filed" means and what `filed_path` points at both need answering. `resolve_practice_path()` at `worker/resolution/service.py:354` resolves a Desktop-supplied relative path against `config.ONEDRIVE_ROOT` and is part of the same question.

**Decided by Paul, 2026-07-31: the interim, with three conditions.** Intellibills carries on writing into `Clients\{client name}\Receipts\{tax year}\` with its sidecar until 18.3's inbox handoff is built. The conditions are Paul's and they are what stop a stated interim becoming a permanent accident: a defined close, two frozen touchpoints, and stage 6 run against the interim rather than skipped. **Section 0.5 is the whole of it and it is binding.** Recorded in the design document as amendment 75.

### 0.2 The plan surfaces eight things the design document does not cover

None is difficult. All eight are cheaper to answer now than during a stage whose purpose is deletion, which is the lesson amendment 65 records. They are listed in 0.4.

### 0.3 One thing I have to disclose, and it needs action today

**While checking which environment variables are set, I ran a command intended to mask every value in `C:\LastingImpact\receipt_capture\.env`. It masked every line of the form `NAME=value`. Line 10 of that file is not of that form: it is a bare 95-character OpenAI key with no variable name in front of it, so my mask did not match it and the key was printed into this conversation in full.**

That is my error. The command should have masked anything that looked like a secret rather than anything that looked like an assignment.

Two things follow, and the first is not optional.

- **Revoke the key beginning `sk-2adW` at https://platform.openai.com/api-keys.** Treat it as exposed.
- **Line 10 of `.env` is orphaned.** `python-dotenv` ignores a line with no `NAME=` prefix, so that key is not the one the pipeline uses; the live key is on line 9 and its value was masked correctly and has not been exposed. Line 10 should be deleted whether or not the key is revoked, because a second key in the file invites exactly this. Deleting it changes no behaviour.

`.env` is gitignored, so nothing about this reaches the repository.

### 0.4 The decisions needed before stage 3 begins

Nine, in the order they bite. Closed rows are kept struck through so the trail survives.

**Closed: 1 and 2 on 2026-07-31, 3 and 6 on 2026-08-01. Half closed: 7, where the backup path is decided and only the fate of the twelve existing backup files is open. Still open: 4, 5, 7's remainder, 8 and 9.** Stage 3 does not start while any of those is unanswered.

| # | Question | Why it cannot wait | What I would suggest, and it is Paul's call |
|---|---|---|---|
| 1 | ~~**What replaces the interchange, and when?**~~ **Decided 2026-07-31. See 0.5.** | | **The interim, with Paul's three conditions.** Intellibills keeps filing to `Clients\{client name}\Receipts\{tax year}\` with its sidecar until 18.3's inbox is built and passes the acceptance check in 0.5.1. It leaves 18.2b's rule broken on purpose and for a stated period, which is better than an unbuildable stage. Building 18.3's inbox and Desktop's drain inside stage 5 was rejected: it turns a restructure into a feature build and puts two variables in one stage, the thing 17.5a exists to avoid. |
| 2 | ~~**Where is `Intellibills\data\`?**~~ **Decided 2026-07-31, amendment 76. 18.2a rewritten by Paul.** | | **The word `data` is used on neither side.** `Intellibills\Documents\{year}\{month}\{day}\` in OneDrive; `C:\Intellibills\db\receipts.db` local; `Intellibills\Backups\` in OneDrive. **And `DATA_DIR` is removed rather than repointed**, because while it exists somebody derives one path from the other and puts the database back into OneDrive by accident. `BACKUPS_ROOT` also stops borrowing `IntelliBooks\Backups\`. **One thing found after the decision: it is four constants, not three.** See 0.6. |
| 3 | ~~**Which layout does the document store use after the move?**~~ **Decided 2026-08-01, amendment 77. Both documents corrected.** | | **`Intellibills\Documents\{CODE}\{year}\{month}\{receipt id}_{filename}`.** Client code first, no day level, date of arrival rather than document date. **`IntelliBooks\Attachments\` is aligned to the same shape**, from `{CODE}\{year}\` to `{CODE}\{year}\{month}\`, so there is one shape rather than two that differ by a level. See 0.6.5. |
| 4 | **`Clients\She Run's It! Ldn Ltd\` and `Clients\Tom Test\`.** Both exist, both are empty, and neither is named in 17.5. `Tom Test` is in neither `clients.csv` nor `IntelliBooks-Practice.json`. `She Run's It! Ldn Ltd` is `Client_005` in `clients.csv` and is not in the practice registry. | Stage 3 deletes client folders by name. An unnamed folder gets left behind and then has to be explained. | Both look like test residue. Say delete or keep, per folder. |
| 5 | **`clients.csv` after the reset.** Six rows today: `UNKNOWN`, `Client_001 Paul Keating / PAUL`, `Client_002 Intellitax / INTELLITAX`, `Client_003 Test 2 / TEST2`, `Client_004 Test / TEST`, `Client_005 She Run's It! Ldn Ltd / SHERUNSIT`. The practice registry holds three clients: `TEST`, `Test 2`, `Paul Keating`. | The registry is what stage 6's clean cycle runs against, and `clients.csv` is what resolves a sender to a client. A row for a client with no folder and no books file is a false pass waiting to happen. | Decide which rows survive. Keep `UNKNOWN`; it is the default for unmatched receipts and removing it changes behaviour. |
| 6 | ~~**`data\files\ABC\`**, 10 files under a client code in neither registry.~~ **Closed 2026-08-01: disposable, no action.** | | Paul's ruling: same class as `PKPH-books.json`, and stage 3 deletes it. Recorded in amendment 77. |
| 7 | **`IntelliBooks\Backups\`**, 12 database backups from 17 to 29 July, and where `backup_db()` writes after the move. Amendment 72 says backups go into OneDrive. **18.2a's tree shows `Backups\` under `IntelliBooks\` and gives `Intellibills\` no backup folder at all.** | The backups are Intellibills', so under 18.2a's own principle they belong under `Intellibills\`. The tree says otherwise, and stage 4 has to create one or the other. | `Intellibills\Backups\`, and correct 18.2a. Then decide whether the 12 existing backups move, or are kept somewhere outside the new tree, or go. Note that they are the only copies of the pre-reset database other than the one stage 2 takes. |
| 8 | **`Handover Pack\` or `Handover\`.** 18.2a says `Handover Pack\`. `IntelliBooks-Desktop-v3.html:1430` writes `Clients\{name}\Handover\{pack date}\`. | Stage 4 creates the tree. Creating `Handover Pack\` while Desktop writes `Handover\` gives every client two folders. | Pick one. If it is `Handover Pack\`, it is one more Desktop line in stage 5. |
| 9 | **`logs\` and `exports\`.** Both sit in the repository at `C:\LastingImpact\receipt_capture\`, both are Intellibills', and 18.2a's tree contains neither. | Silence in a tree that claims to be complete reads as a decision nobody took. | Leave both in the repository and say so in 18.2a, or move them. `logs\` holds `runs.ndjson`, 415 KB, which the console's intake panel at 8.6 will read. |

**Three of these nine are corrections to section 18 rather than questions**, numbers 2, 7 and 8. I will make them as amendments once Paul has ruled, not before. **Number 2 was ruled on 2026-08-01 and 18.2a is rewritten; number 7 is half closed by it, because the backup path is now decided and only the fate of the 12 existing backup files is open.**

---

## 0.5 The interim contract

**Paul's decision, 2026-07-31. Design document amendment 75.**

**The exception.** Until the close condition in 0.5.1 is met, Intellibills continues to write a filed receipt and its sidecar into `Clients\{client name}\Receipts\{tax year}\`, and IntelliBooks Desktop continues to read them from there. This contradicts 18.2b, which says Intellibills never writes into `Clients\` at all. **The contradiction is deliberate, it is dated, and it closes on a check rather than on a judgement.**

**Why an interim rather than the real thing.** Building 18.3's inbox and Desktop's drain inside stage 5 would put a feature build inside a restructure and two variables inside one stage, which is what 17.5a exists to prevent. The interim costs nothing to hold and everything it touches is code that already works and is already tested end to end.

### 0.5.1 The close condition

**Six checks. The exception closes when all six pass in one sitting, against one receipt, with the results written into the design document.** Not when 18.3 "feels done".

Each is written so it cannot be recorded as passed while the change is incomplete.

| # | Check | What it proves |
|---|---|---|
| 1 | Take a full listing of `Clients\` before the run and after it. **A receipt travels from capture to the books and the two listings are identical.** | Intellibills wrote nothing into `Clients\`. A check that only inspects the Inbox would pass while the pipeline still wrote both. |
| 2 | The receipt appears as one item in `IntelliBooks\Inbox\` after the pipeline runs and before Desktop is opened. | The push happened, and it happened into the folder Desktop owns. |
| 3 | Desktop drains it, and the resulting books receipt entry carries **supplier, document date, net, VAT, gross and category**, all six populated from the handoff. **Not "Image only. Edit details." and not a `img_` entry with a gross of 0.** | The sidecar equivalent works. This is the check that would otherwise be passed by an image landing with no data, which is precisely the failure mode amendment 57 spent a day on. |
| 4 | The image is viewable from that books entry. | The document travelled, not only its figures. |
| 5 | Drain a second time without adding anything. **The books gain no second entry and `IntelliBooks\Inbox\` is empty.** | The drain removes what it took. Without this the handoff is a folder scan with a duplicate bug waiting in it. |
| 6 | From the pipeline alone, with no reading of any IntelliBooks file, answer "has this receipt been handed off, and when". | 18.2c's rule that the two stores must never be expected to hold the same set depends on the pipeline being able to answer this by itself. Today `receipts.filed_path` and `filed_at` answer it; whatever replaces them has to. |

**One consequence to decide at the same moment, not afterwards.** Closing the exception stops anything being written into `Clients\{client name}\Receipts\`. Under 18.2b that folder is then filled by IntelliBooks at Post, and **that write does not exist either.** So closing on the Inbox alone leaves client folders empty until the Post write is built. Either close both together, or close on the Inbox and accept a period with nothing reaching the client folders. Paul's call, and it is a portal question rather than a technical one.

### 0.5.2 The frozen touchpoints

**These are out of scope for every 18.2b and 18.3 change until the exception closes.** A change to any of them is a decision to be taken deliberately, not a refactor made while passing. **Any brief written for either build session must name them as frozen**, including the two stage 5 briefs.

Line numbers are today's and they move. The function names do not.

| Module | Frozen | Where, on 2026-07-31 |
|---|---|---|
| Intellibills | `get_client_directory()` | `worker/filing.py:64` |
| Intellibills | `file_receipt()`, including its `Receipts\{tax year}\` destination | `worker/filing.py:68`, destination at `:78` |
| Intellibills | `make_enriched_sidecar()`, which builds the payload Desktop parses | `worker/filing.py:321` |
| IntelliBooks Desktop | `scanFiledReceipts()`, including its `getDir` call and the `ingestReceiptFiles()` handoff | `IntelliBooks-Desktop-v3.html:1276`, `getDir` at `:1281`, call at `:1288` |
| IntelliBooks Desktop | `parseSidecar()`, which reads that payload | `IntelliBooks-Desktop-v3.html:1173` |

**18.2b's own list of what Intellibills loses is therefore deferred, not cancelled.** `get_client_directory()`, the client folder layout and the tax-year determination all stay until the exception closes.

**Note what the freeze does not cover, because it is the more dangerous half.** `worker/filing.py:103` files statements to `Clients\{client name}\Statements\{tax year}\{platform}\` and is **not** frozen: the `statements` table is empty, no `Statements\` folder exists under any client, and nothing reads it, so it has no interim contract to protect. It is the folder amendment 65 found by checking line numbers against the file. Do not assume the freeze covers everything in `filing.py`.

### 0.5.3 One frozen path, four coordinated flips

Worth stating plainly, because it is the shape of stage 5 and the freeze only makes sense against it.

**Frozen, and therefore not touched in stage 5 at all:** `Clients\{client name}\Receipts\{tax year}\`. It does not move. `Clients\` stays where it is under 18.2a, so the interim contract needs no path change on either side. That is what makes the interim cheap.

**Four paths do move, and each is written by one module and read by the other, so both halves must land in the same stage or the modules stop talking.**

| Path | Moves to | Pipeline site | Desktop site |
|---|---|---|---|
| `IntelliBooks\Receipt Inbox\{CODE}\` | `Intellibills\Receipt Inbox\{CODE}\` | `worker/intake/folder_reader.py:74` | `IntelliBooks-Desktop-v3.html:1153`, and `:593` |
| `Clients\{client name}\Review\` | `Intellibills\Review\{CODE}\` | `worker/filing.py:125`, `:157-159`, `:295-297` | `IntelliBooks-Desktop-v3.html:1819` |
| `IntelliBooks\Resolutions\` | `Intellibills\Resolutions\` | `config.py:36`, `app.py:297`, `check_test41.py:80` | `IntelliBooks-Desktop-v3.html:1803` |
| `IntelliBooks\pipeline-status.json` | `Intellibills\pipeline-status.json` | `app.py:137` | `IntelliBooks-Desktop-v3.html:584` |

**The Review move is the one to watch.** It changes shape as well as location, from `Clients\{client name}\Review\` keyed on the client's name to `Intellibills\Review\{CODE}\` keyed on the client's code. Amendment 44 records that the two registries hold different names for one client and that it works only because NTFS is case-insensitive. **Keying on the code removes that fault**, which is a real gain, and it also means the two sides cannot be made compatible by accident: they either both use the code or receipts stop being reviewable.

---

## 0.6 The paths, and the four constants

**Paul's decision, 2026-07-31, decision 2 closed. Design document amendment 76, and 18.2a is rewritten.**

### 0.6.1 The three paths

| | Path | Contents |
|---|---|---|
| **OneDrive**, under the practice root | `Intellibills\Documents\{CODE}\{year}\{month}\{receipt id}_{filename}` | The archive of record. Write-once, never held open, safe to sync. Shape settled by amendment 77, see 0.6.5. |
| **Local**, outside any synced folder | `C:\Intellibills\db\receipts.db` | The live database and its `-wal` and `-shm` companions. |
| **OneDrive**, under the practice root | `Intellibills\Backups\` | Where `backup_db()` writes. Closed consistent copies, safe to sync. |

**The word `data` is used on neither side**, so no path can be misread as the other. `Intellibills\data\files\` is corrected in three places in the design document: 18.2's table, 18.9's table, and section 16's note on step 10a.

### 0.6.2 `DATA_DIR` goes, and it is four constants rather than three

Paul's instruction, and the reason it is a removal and not a repointing: **while `DATA_DIR` exists somebody will derive one path from the other and put the live database back into OneDrive by accident.** Today `config.py:9-13` reads

```
DATA_DIR  = BASE_DIR / "data"
FILES_DIR = DATA_DIR / "files"
DB_PATH   = DATA_DIR / "receipts.db"
```

A shared parent, which is why the tree read as one folder in the first place.

**In its place, four constants with no shared parent.** The fourth is a finding taken after the decision, from reading `worker/logging_setup.py` rather than the prose.

| Constant | Derived from | Points at |
|---|---|---|
| `FILES_DIR` | the practice root | `Intellibills\Documents\` |
| `DB_PATH` | **a new local root constant**, with its own environment override mirroring how `ONEDRIVE_ROOT` works at `config.py:18-21` | `C:\Intellibills\db\receipts.db` |
| `BACKUPS_ROOT` | the practice root. **It currently resolves to `IntelliBooks\Backups\`**, at `config.py:27`, and that folder belongs to IntelliBooks under 18.2a. | `Intellibills\Backups\` |
| **The process log path** | **open, see 0.6.3** | `run.log`, `resolve.log`, `discard.log`, `console.log` |

### 0.6.3 The third consumer, and the one-letter trap

**`worker/logging_setup.py:50` returns `config.DATA_DIR / filename`, and `:69` creates the folder.** So `DATA_DIR` today parents three unrelated things: the document store, the live database, and the four process log files listed in `ENTRY_POINT_LOGS` at `worker/logging_setup.py:39`. Only `run.log` exists on disk, 43 KB, last written 29 July.

**Removing `DATA_DIR` leaves the logs with no home**, and none of the three paths in 0.6.1 suits them. They are not documents, not the database, and not backups.

**And there is a trap in the obvious answer.** The repository already holds `logs\`, with `runs.ndjson` at 415 KB and two `receipt_events_*.ndjson`, while `data\` holds `run.log`. **`logs\runs.ndjson` and `data\run.log` are one letter apart and are different files written by different mechanisms.** Both are gitignored, `data/` and `logs/` at lines 3 and 10 of `.gitignore`. Putting the process logs into `LOGS_DIR` gives one log location and removes that confusion, which is worth having, but it moves a file the console's intake panel at 8.6 will read, so it is a decision and not tidying. **It also overlaps decision 9**, which asks whether `logs\` and `exports\` stay in the repository at all. **The two should be answered together or they will contradict each other.**

### 0.6.4 The change is wider than `config.py`

**Seven test files patch `config.DATA_DIR` by name**, and each will fail the moment the constant goes:

`tests/resolution_fixtures.py`, `tests/test_extraction_details.py`, `tests/test_logging_setup.py`, `tests/test_resolve_receipt_ordering.py`, `tests/test_resolve_receipt_zero_and_types.py`, `tests/test_review_pair_cleanup.py`, `tests/test_sidecar_category_keys.py`.

Two of them need naming individually.

**`tests/resolution_fixtures.py:59` reproduces the shared parent inside the fixture**, with `config.FILES_DIR = config.DATA_DIR / "files"`. So the fault this decision removes from `config.py` exists in a second place, and fixing only the first leaves a fixture that cannot express the new layout.

**`tests/test_logging_setup.py` exists to catch a test writing into the live operational logs.** Its own comments record that a change on 27 July put 29 lines of synthetic output into `data/run.log` before it was reverted, which is amendment 6's problem. **It must be updated deliberately, never made to pass**, and the brief for stage 5 should say so in those words.

### 0.6.5 The document store shape

**Paul's decision, 2026-08-01, amendment 77. Decision 3 closed, and both documents corrected.**

```
Intellibills\Documents\{CODE}\{year}\{month}\{receipt id}_{filename}
IntelliBooks\Attachments\{CODE}\{year}\{month}\{receipt id}_{original filename}
```

**Client code first, no day level, and `{year}\{month}\` is the date of arrival rather than the document date**, so a path never changes when an invoice date is corrected. `save_file()` at `worker/storage/store.py:20` already uses `datetime.now()` for exactly that reason.

**`IntelliBooks\Attachments\` is aligned to the same shape**, from `{CODE}\{year}\` to `{CODE}\{year}\{month}\`. One shape to remember rather than two that differ by a level.

**Why this shape and not the one the documents described.** It is what runs, which settles it, and it is also right on the merits: everything for one client sits in one folder, which is what a departing client, a handover pack, a subject access request and an erasure all need, and on S3 it makes a per-client prefix, which is what an IAM policy and a lifecycle rule attach to.

**Why two shapes coexisted for months with no failure, and it is the part worth carrying forward.** `receipts.file_path` stores the full path, so nothing anywhere reconstructs a location from its parts. That is rule 2 of 18.2c, never derive a location from a path, working in the system's favour for once. **Remember it the next time somebody proposes deriving one.**

**And why it had to be settled before stage 3.** Stage 3 deletes the store and stage 4 recreates it. Recreating it in the shape the documents described would have moved where every receipt lands, silently, with no error and nothing to notice.

---

## 0.7 The reset as executed, 2026-08-01

**Verified by the consultant session against the database, `git log` and the filesystem after the fact, not from the report.** Every figure below was read back.

### 0.7.1 Where the six stages stand

| Stage | State |
|---|---|
| 1, stop the pipeline | **Done.** The stale `IntelliBooks\pipeline.lock`, pid 31156 from 29 July, deleted. |
| 2, back up | **Done.** `IntelliBooks\Backups\receipts-pre-reset-20260801.db`, 233,472 bytes, md5 verified against source, and **the `-wal` sidecar confirmed at 0 bytes before the copy**, which is what makes a plain copy of a WAL database provably complete. That check was not in this plan and should have been. |
| 3, reset | **Done.** Counts verified below. |
| 4, restructure | **Part done.** `Intellibills\` exists in the practice root holding four vendor CSVs, committed as `8b1db5d`. Everything else in 0.6.1 and 18.2a remains to move. |
| 5, change the code | **Not started.** |
| 6, one clean cycle | **Not started.** |

**The pipeline must not be started until stage 5 is done**, or it will write into the old paths and half-populate a tree that is mid-move.

### 0.7.2 The database, read back

`receipts`, `extractions`, `categorisations`, `resolution_events`, `processed_attachments`, `statements`, `email_alerts` and `email_delta` all read **0**. `categorisations_firm_vendors` and `categorisations_client_rules` read 0 and were untouched.

**`categorisations_client_vendors` reads 100, all under `Client_006`.** It read 101 before, being 100 for `Client_001` and 1 for `Client_003`.

### 0.7.3 The vendor re-key, which this plan did not authorise

**The 100 surviving rows were re-keyed from `Client_001` to `Client_006`, and the single `Client_003` row was deleted.** `clients.csv` was rewritten the same day and `Client_001` ceased to exist, so the lookup at `worker/database/repository.py:344`, which keys on `client_id`, would never have matched them again. `Client_006` is `PKPH`, the same person on the same email with the same `business_type`.

**The reasoning is right and the outcome is right.** Protecting the rows through the reset was not enough if the key they hang off is retired in the same operation, and this plan did not see that. It is recorded here because it is the substantive finding of the whole reset.

**Two things about it are worth stating plainly, and neither is a criticism of the outcome.** It is an `UPDATE` and a `DELETE` against `data/receipts.db`, which `CLAUDE.md`'s AUTOMATIC list requires a session to stop and ask about. And **the row that was deleted is the only thing lost in the entire reset that was not test data**: one real mapping for `Client_003`. Recoverable from `Intellibills\categorisations_client_vendors_cleaned.csv` if it is ever wanted.

### 0.7.4 The correction that matters most

**`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\Paul Keating\` is not disposable, and this plan said it was.**

It holds eight loose PDFs, four `letter-of-engagement-ke001_*.pdf` and four `proposal-ke001_*.pdf`, plus `Document Requests\` and `Misc\` from another tool. **Those are real firm records.** Only `Receipts\` and `Review\` inside it were disposable, and only those were deleted.

**The trail, because it is the more useful part than the fix.** Section 17.5 scoped it correctly, naming only `Clients\Paul Keating\Receipts\`. Section 17.5a widened it to the whole folder when summarising. **This plan then repeated 17.5a without checking it against 17.5**, and stage 3c said "each in full". Both are now corrected. **And the plan's own section 1 had already noticed:** it listed the eight PDFs, said they came from a different system, and told the operator to "confirm they are included". **The doubt was written down and then a delete instruction was written anyway.** Noticing is not the same as acting, and a note that says "confirm" beside an instruction that says "delete in full" resolves itself the wrong way under time pressure.

### 0.7.5 What was actually deleted and created

**Deleted:** `Clients\Test\`, `Clients\Test 2\`, `Clients\Tom Test\`, `Clients\Paul Keating\Receipts\`, `Clients\Paul Keating\Review\`, the three books files in `IntelliBooks\Books\`, all 96 documents in `receipt_capture\data\files\`, nine `.fuse_hidden` artefacts, and the stale `pipeline.lock`.

**Created:** `Clients\PKPH\`, empty, and `Intellibills\` in the practice root.

**Kept:** `Clients\She Run's It! Ldn Ltd\`, empty, a real future client. `Clients\Paul Keating\` less its two deleted subfolders. `desktop.ini`.

**`receipt_capture\data\` now holds four items only:** `receipts.db`, its `-wal` and `-shm` companions, and `run.log`.

### 0.7.6 The registries, consistent for the first time

`clients.csv` has six rows: `UNKNOWN`; `Client_005 She Run's It! Ldn Ltd / SHERUNSIT`; `Client_006 PKPH / PKPH` on `pdk7@hotmail.co.uk`, `PHV_DRIVER`; `Client_007 Intellitax / INTELLITAX`; `Client_008 Test 3 / TEST3`; `Client_009 Test 4 / TEST4`. `Client_001` to `Client_004` are gone.

`IntelliBooks-Practice.json` rewritten to match, five clients, **names spelled exactly as `clients.csv` spells them.** That closes the `TEST` against `Test` disagreement of amendments 44 and 45, which had survived only because NTFS is case-insensitive and which amendment 44 warned would become two folders on S3 or Linux. Old file kept as `IntelliBooks-Practice.json.bak-2026-08-01`.

**Outstanding on the registries:** all five clients are `vat:false`, and the `yearEnd`, `mtd` and `mtdBasis` values that were on `Paul Keating` were not carried to any client. Set per client in IntelliBooks Desktop.

### 0.7.7 A structural fact the reset created, worth recording

**`Clients\Paul Keating\` now holds the person's engagement letters and proposals, and `Clients\PKPH\` holds the entity's receipts, as a sibling.**

That settles by practice one of the per-firm settings 18.2b left open: **entities sit at the same level as the contact, not beneath it.** It also demonstrates 18.2c's contact-and-entity split existing on disk before any code knows about it, which is exactly the headroom that section was written to preserve.

### 0.7.8 Still outstanding, and one of them is new

**The clean cycle**, stage 6. One receipt to `capture@lastingimpact.co.uk` from `pdk7@hotmail.co.uk`, which now resolves to `PKPH`. That exercises an empty database, a client with no history, and Desktop creating `PKPH-books.json` from nothing, all of which 17.5 names as worth testing deliberately. **It must wait for stage 5.**

**The rest of the restructure.** `Intellibills\` exists, so the remainder can go in piecemeal rather than as one move: `clients.csv`, `firms.csv`, `Receipt Inbox\`, `Review\`, `Resolutions\`, `pipeline-status.json`, the document store to `Intellibills\Documents\`, the live database to `C:\Intellibills\db\`, the logs to `C:\Intellibills\logs\`, and `backup_db()` pointed at `Intellibills\Backups\`. All need the code change.

**New, and nobody asked for it: the event logs were never in scope and still hold the history of the deleted receipts.** See 0.8.4.

---

## 0.8 The last five decisions, closed 2026-08-01

**Paul's decisions. Design document amendments 79 and 80.**

### 0.8.1 Decisions 4 and 5, the folders and the registries

**Made rather than specified.** `Tom Test\` deleted, `She Run's It! Ldn Ltd\` kept as a real future client, `clients.csv` and `IntelliBooks-Practice.json` rewritten to agree. Recorded at 0.7.5 and 0.7.6.

### 0.8.2 Decision 7, the backups

**`Intellibills\Backups\`, and the twelve existing backups move into it.** They are Intellibills' and `IntelliBooks\Backups\` is IntelliBooks' under 18.2a. `receipts-pre-reset-20260801.db` moves with them and is the most valuable of the set, being the only copy of the pre-reset state.

### 0.8.3 Decision 8, the handover folder

**`Handover Pack\`.** `IntelliBooks-Desktop-v3.html:1430` writes `Clients\{name}\Handover\{pack date}\` and becomes one more line in the Desktop half of stage 5.

### 0.8.4 Decision 9, and it closes amendment 76's open item

**Logs go local, beside the database, at `C:\Intellibills\logs\`.** Not into OneDrive. They are appended on every poll, so syncing them is churn for no benefit, and **a OneDrive conflict copy of a log is worse than useless.** Same shape as the database decision in amendment 72 but for a different reason: not corruption, just noise and no upside.

**This closes amendment 76's open item rather than leaving it.** That amendment removed `DATA_DIR` and left `run.log`, `resolve.log`, `discard.log` and `console.log` with no home, and named the trap that `logs\runs.ndjson` and `data\run.log` are one letter apart. **One `C:\Intellibills\logs\` folder takes all of them and both problems go at once.** Answer them separately and the logs end up in three places.

**Exports go to OneDrive, at `Intellibills\Exports\`.** An export is a deliverable produced on demand for a person to read, so it belongs where a person can reach it. **Open, and Paul has called it a real choice: whether an export instead belongs in the client's own folder.** It is the same question 18.2b answered for receipts, and the same answer may not apply, because an export is produced for the firm as often as for the client.

**And a fifth constant, so amendment 76's table is now five and not four:** `FILES_DIR` from the practice root, `DB_PATH` from the local root, `BACKUPS_ROOT` from the practice root, the process log path from the local root, and `EXPORTS_DIR` from the practice root.

### 0.8.5 The event logs, which the reset never covered

**Not in 17.5, not in this plan, and found after the reset.** `logs\runs.ndjson` holds **1,022 lines** ending at `2026-07-29T13:45:33`, describing runs against the 29 receipts that no longer exist, plus the three synthetic rows the test suite wrote before `2d19521`. `logs\receipt_events_FIRM001.ndjson` holds **70** and `logs\receipt_events_INTELLITAX.ndjson` **59**. All three counts read back today.

**The console's intake panel at 8.6 will read all of it.** So the reset cleared the database and left its history behind, and the console would open on events for receipts that no longer exist.

**Archive them into the backup folder beside `receipts-pre-reset-20260801.db` and start clean.** Paul's recommendation and mine. The alternative is to accept an intake panel that opens on ghosts, which is a defect report waiting to be written by whoever meets it first.

**Note the ordering:** archive them **after** the logs move to `C:\Intellibills\logs\` at stage 5, or the move will carry the history across and the problem travels with it.

---

## 1. State as at 2026-07-31, read rather than recalled

Everything in this section was read today from git, the database, or the filesystem. It is the "before" against which every stage is verified.

### A blocker that must be cleared before stage 1, and it is mine

**`C:\LastingImpact\receipt_capture\.git\index.lock` exists, is 0 bytes, and is stale. Every git write in this repository fails while it is there**, including `git add`, `git commit` and `git mv`. Reads still work.

**I created it.** It is timestamped `2026-07-31 15:54:52 +0100`, twenty-seven seconds after this session's workspace was created, which is my first `git status` call. That call printed `warning: unable to unlink '.git/index.lock': Operation not permitted` and I did not act on it. **The Linux sandbox can create files in the mounted folder but cannot unlink them**, so git left its lock behind and could not clean it up.

**Clear it on Windows, from `C:\LastingImpact\receipt_capture`:**

    del .git\index.lock

**Plain English:** removes a stale marker git uses to stop two processes writing at once. Nothing is lost; the lock is empty and no git process is running.

**In VS Code:** the Source Control panel will show the same error. Use a terminal for this one, or delete the file in Explorer with hidden items shown.

**Two consequences for this plan.**

**Stage 1's gate cannot be met until it is cleared**, because that gate requires the three modified documents to be committed and no commit can be made.

**And a standing rule for any Cowork session on this repository, now in `CLAUDE.md` as the third trap: do not run git from the Linux sandbox without `--no-optional-locks`.** ~~Reads are safe and are what the sandbox is for.~~ **That first wording was wrong and it was disproved within the hour, by me, running the very command it implied was safe.** `git status` and `git diff` refresh the index stat cache, which takes the lock, so **`git status` alone recreates the problem.** `git --no-optional-locks status` is the documented flag for it and works even while a stale lock exists. `git log`, `git show` and `git ls-files` never touch the index. Everything that writes belongs on Windows.

**The lock has therefore been recreated twice in this session**, at `15:54:52` on 31 July and at `11:57:34` on 1 August, both by me, both from a bare `git status`. It must be cleared again before stage 1.

### Repository

Branch `feat/console-phase0`, tip `ac2d1be`, which is the same tip the 2026-07-30 handover recorded.

Three tracked files modified and uncommitted, and one untracked:

```
 M 2026-07-25_CONSOLE_DESIGN.md
 M 2026-07-29_HANDOVER_consultant_chat_3.md
 M 2026-07-30_HANDOVER_consultant_chat_4.md
?? RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md
```

That matches the handover exactly, including the untracked draft. **The commit the handover recommends has not been made.** It should be, before stage 1, and its staging and message are in section 3 of `2026-07-30_HANDOVER_consultant_chat_4.md`.

Note against `CLAUDE.md`'s warning about the Linux sandbox: only three files show as modified, not the thirty-odd phantom line-ending changes that warning describes. Confirm on Windows before acting on it.

### Database, `C:\LastingImpact\receipt_capture\data\receipts.db`

| Table | Rows |
|---|---|
| `receipts` | 29, being 24 `ok` and 5 `discarded` |
| `extractions` | 53 |
| `resolution_events` | 2 |
| `processed_attachments` | 20 |
| `categorisations_client_vendors` | **101**, being 100 for `Client_001` and 1 for `Client_003` |
| `categorisations_firm_vendors` | 0 |
| `categorisations_client_rules` | 0 |
| `statements` | 0 |
| `email_alerts` | 3 |
| `email_delta` | 1 |

Unchanged from 29 July. The 101 vendor mappings are the rows 17.5 forbids clearing.

`receipts.db` 233,472 bytes, `receipts.db-wal` 0 bytes, `receipts.db-shm` 32,768 bytes. **The `-shm` file carries today's date, 31 July at 14:00**, which nothing in the project record explains. Worth a look at stage 1: it may be a sandbox mount artefact, or it may mean something has the database open.

`data\` also holds 24 files named `.fuse_hidden0000000f0000000*`, 32,768 bytes each, 768 KB in total, dated 18 to 25 July. That is the size of a `-shm` file and the name is a FUSE artefact, so they are most likely orphaned shared-memory files left by a sandbox mount. Harmless, gitignored, and worth sweeping in stage 3.

### The document store, `C:\LastingImpact\receipt_capture\data\files\`

96 files, 13 MB, in two layouts:

| Path | Files |
|---|---|
| `data\files\2026\05\05\` and `\06\` | 57 |
| `data\files\ABC\2026\07\` | 10 |
| `data\files\PAUL\2026\07\` | 16 |
| `data\files\TEST\2026\07\` | 8 |
| `data\files\TEST2\2026\07\` | 5 |

**The client-code-first shape is the one that survives**, per 0.6.5. The 57 files under `data\files\2026\05\` are the older date-first shape, left behind when the code changed and nothing migrated. Stage 3 deletes both, and `ABC\` with them.

### Practice root, `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`

**The practice root cannot be mounted as one folder in a Cowork session.** It contains `Documents\WindowsPowerShell`, which is a protected host location, and the request is refused. Mount `Clients\`, `IntelliBooks\` and `Scripts\` separately. Worth adding to section 0 of the next handover, because "mount the practice root" is not achievable as written.

**`Clients\`**

| Folder | Files | Size |
|---|---|---|
| `Paul Keating\` | 37 | 980 KB |
| `Test\` | 22 | 7.9 MB |
| `Test 2\` | 18 | 6.8 MB |
| `She Run's It! Ldn Ltd\` | 0 | empty |
| `Tom Test\` | 0 | empty |

Plus `desktop.ini`, 84 bytes, a Windows folder-appearance file. Leave it.

`Paul Keating\` holds `Document Requests\`, `Misc\`, `Receipts\{2024-25, 2025-26, 2026-27}\`, `Review\`, and eight loose PDFs, four `letter-of-engagement-ke001_*.pdf` and four `proposal-ke001_*.pdf`, from another tool. ~~**17.5a confirms all of `Clients\Paul Keating\` is disposable.** The eight PDFs are inside that folder. Confirm they are included.~~ **Wrong, corrected 2026-08-01. Only `Receipts\` and `Review\` are disposable.** The eight PDFs are engagement letters and proposals, and `Document Requests\` and `Misc\` come from another tool. **17.5 scoped this correctly and 17.5a widened it when summarising**; this plan then repeated 17.5a. See 0.7.

**`IntelliBooks\`**

| Item | Detail |
|---|---|
| `App\` | `IntelliBooks-Desktop-v3.html` 139,104 bytes, matching the handover; four `.bak` files; `IntelliBooks.bat`; a shortcut; `Docs\` |
| `Backups\` | 12 files, `receipts-20260717.db` to `receipts-20260729.db` |
| `Books\` | `PAUL-books.json` 196,957 bytes; `TEST-books.json` 5,974,097; `TEST2-books.json` 2,796,045. Three files, as the handover says. |
| `Receipt Inbox\` | `TEST\Processed\` holds `TEST_review_A_pennine_cafe.png` and `TEST_review_B_kirkgate_hardware.png`. `TEST2\` is empty. **Two files.** |
| `Resolutions\` | `processed\` holds the two test 41 notes. Nothing pending, nothing in `failed\`. |
| `IntelliBooks-Practice.json` | Three clients: `TEST`, `Test 2`, `Paul Keating` |
| `clients.csv` | Six rows, plus `clients.csv.bak-2026-07-28` |
| `firms.csv` | One row, `FIRM001 Intellitax` |
| `pipeline-status.json` | `last_run` 2026-07-29T13:45:33Z, `processed_today` 2, `review_count` 0, `last_error` null |
| `pipeline.lock` | **Present.** `pid=31156`, `started_at` 2026-07-29T13:42:18Z |

**`Scripts\`** holds five files, all Claude session backup and conversion tooling, none of it Intellibills' or IntelliBooks'. **18.2a's three-folder tree does not mention `Scripts\`.** It is not this system's and the plan leaves it where it is.

### The mailbox

**Not checked, and it cannot be checked from here.** `INBOX` being empty is the precondition 17.5 calls the one that costs money. It is stage 3's first gate and it is an operator step.

---

## 2. How the stages work

Each stage below has the same four parts, and they are in this order for a reason.

1. **Gate.** What must be true before the stage starts. If it is not true, the stage does not start.
2. **Do.** The actions, each naming its file or folder in full.
3. **Verify.** What must be true afterwards, expressed so it can be checked rather than assumed.
4. **Stop if.** The specific results that end the operation at this stage.

Two standing rules from 17.5, and neither is negotiable.

- **Nothing is deleted in the same stage as anything else.** Stage 3 deletes and does nothing else. Stage 4 creates and moves and deletes nothing.
- **If a stage does not verify, stop there** rather than continue and reconcile later.

**Who does what.** Paul runs everything that touches the practice root, the mailbox or the running pipeline. This session verifies before and after each stage and holds the record. Claude Code makes the stage 5 code change against a written brief, and the Desktop session makes its half. Neither build session is given anything until stage 4 has verified.

---

## Stage 1. Stop the pipeline

**Purpose.** Nothing mid-write when the backup is taken.

**Gate**

- The three modified documents are committed, per section 1. Not a safety matter; it means the operation starts from a known tip.
- Decisions 1 to 9 in section 0.4 are answered. **Stage 3 must not start with any of them open, and stage 1 is where they stop being free.**

**Do**

1. Confirm whether a pipeline process is running. `IntelliBooks\pipeline.lock` names `pid=31156` from 29 July. On Windows: `tasklist /FI "PID eq 31156"`.
2. If it is running, stop it the ordinary way rather than by killing it, so `release_lock()` at `app.py:506` removes its own lock file.
3. If it is not running, the lock is stale. Delete `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\pipeline.lock` by hand. `acquire_lock()` at `app.py:473` would clear it on the next start anyway, but leaving it means stage 6 cannot tell a fresh lock from an old one.
4. Close IntelliBooks Desktop in the browser. It has a 400 ms debounced save at `IntelliBooks-Desktop-v3.html:479` and it writes books files. `TEST2-books.json` was written at 13:26 today, so it has been open recently.
5. Establish what wrote `data\receipts.db-shm` at 14:00 today.

**Verify**

- `tasklist` reports no process on the pid the lock named.
- `IntelliBooks\pipeline.lock` does not exist.
- No browser tab has IntelliBooks Desktop open.
- `data\receipts.db-wal` is 0 bytes, as it is now.

**Stop if**

- A pipeline process is running that will not stop cleanly. Killing it leaves a lock file and possibly a partial write.
- The `-shm` timestamp turns out to mean something has the database open that has not been accounted for.

---

## Stage 2. Back up

**Purpose.** A complete record of what was there, taken before anything is deleted, and enough to reverse the operation.

**Gate.** Stage 1 verified.

**Do**

1. **Copy the database file by file, not through the application.** With the pipeline stopped there is no reason to use `repo.backup_db()`, and a plain copy of all three files is the more faithful record. Copy `data\receipts.db`, `data\receipts.db-wal` and `data\receipts.db-shm` to a folder outside both the repository and the new tree, named for the date. **All three, together.** A `.db` copied without its companions is the corruption route amendment 72 describes.
2. **A full recursive file listing of the practice root**, every folder, with sizes and timestamps, written to a file. This is 17.5a stage 2's own requirement and it is the only record of what was there once stage 3 has run. Include `Clients\`, `IntelliBooks\` and `Scripts\`.
3. **A full recursive listing of `C:\LastingImpact\receipt_capture\data\files\`**, 96 files.
4. **Copy the three books files** out of `IntelliBooks\Books\` into the same backup folder. They are test data and disposable, but they are also the only record of how the books behaved before the reset, and the total is 8.8 MB.
5. **Copy `clients.csv`, `firms.csv`, `IntelliBooks-Practice.json` and `pipeline-status.json`.** Small, and three of the four survive stage 3 and move in stage 4, so a copy makes the move checkable.
6. **Export the vendor mappings to CSV from the live database**, all 101 rows of `categorisations_client_vendors`. 17.5 says they are recoverable from `categorisations_client_vendors_cleaned.csv`, and a fresh export of what is actually in the table is a better restore than a re-import of the file that seeded it, because it captures anything learned since. This is belt and braces on top of not clearing the table at all.
7. **Note the byte count and file count of every folder listed in section 1**, so stage 3's verification is a comparison rather than a judgement.

**Verify**

- The backup folder holds all three database files, and the copied `.db` is 233,472 bytes.
- Open the copied database read-only and count `categorisations_client_vendors`. It must read **101**.
- The practice root listing contains at least one line for each of the five client folders.
- The vendor CSV has 101 data rows plus a header.

**Stop if**

- The copied database will not open, or any count differs from section 1.
- The backup folder is inside the practice root, inside the repository, or inside the new tree. It must be none of those.

---

## Stage 3. Reset

**Purpose.** Delete. Nothing else happens in this stage.

**Gate**

- Stage 2 verified.
- **`INBOX` is empty.** Paul opens the `capture@lastingimpact.co.uk` mailbox and confirms `INBOX` itself holds no messages, with the processed items sitting in `INBOX.Processed Receipts` and the other routing folders. `fetch_new_messages()` selects `INBOX` and searches `ALL`, at `worker/email/reader.py:47` and `:171`, so anything left there is re-extracted at one OpenAI call per attachment once `processed_attachments` is empty. **This gate is checked immediately before the stage runs, not earlier in the day.** A receipt arriving in between puts it back.
- **`IntelliBooks\Receipt Inbox\TEST\Processed\` holds two files.** They are in a `Processed` subfolder so the folder reader will not pick them up, but confirm the decision to delete them rather than discover them later.

**Do, in this order**

**3a. The database.** One connection, one transaction, and read the row counts back before committing.

Clear: `receipts`, `extractions`, `resolution_events`, `processed_attachments`, `statements`, `email_alerts`, `email_delta`, and `categorisations`.

**Do not touch: `categorisations_client_vendors`.** 101 rows. This is the one that matters.

`categorisations_firm_vendors` and `categorisations_client_rules` are both empty, so there is nothing to clear and nothing to protect. Leave them alone rather than issue a `DELETE` that does nothing.

**3b. The document store.** Delete the contents of `C:\LastingImpact\receipt_capture\data\files\`, all 96 files and their folders. Sweep the 24 `.fuse_hidden*` files in `data\` at the same time.

**3c. The client folders.** ~~Delete `...\Clients\Test\`, `...\Test 2\` and `...\Paul Keating\`, each in full. Plus `She Run's It! Ldn Ltd\` and `Tom Test\` if decision 4 says so.~~

> **Corrected 2026-08-01, and the superseded wording above was dangerous.** It would have deleted eight engagement letters and proposals. **`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\Paul Keating\` is NOT disposable.** Only `Receipts\` and `Review\` inside it go. See 0.7.

**Delete in full:** `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients\Test\`, `...\Clients\Test 2\`, `...\Clients\Tom Test\`.

**Delete inside `...\Clients\Paul Keating\` only:** `Receipts\` and `Review\`. **Leave the eight loose PDFs, `Document Requests\` and `Misc\`.**

**Keep:** `...\Clients\She Run's It! Ldn Ltd\`, empty, a real future client rather than residue. And `desktop.ini`.

**3d. The books.** Delete `PAUL-books.json`, `TEST-books.json` and `TEST2-books.json` from `IntelliBooks\Books\`.

**3e. Receipt Inbox and Resolutions.** Delete the two files under `IntelliBooks\Receipt Inbox\TEST\Processed\` and the two notes under `IntelliBooks\Resolutions\processed\`.

**3f. The registries.** Apply decision 5 to `clients.csv`, and the matching edit to `IntelliBooks-Practice.json`. **These two must agree.** Amendment 44 records that they already disagree on `TEST` against `Test`, and it survived only because NTFS is case-insensitive; this is the one moment when fixing that costs nothing.

**Verify, after each of 3a to 3f rather than at the end**

- After 3a: `categorisations_client_vendors` reads **101**. Every cleared table reads 0. **If the vendor count is not 101, stop and restore from stage 2's copy.**
- After 3b: `data\files\` exists and is empty. No `.fuse_hidden*` in `data\`.
- After 3c: `Clients\` holds only what decision 4 left, plus `desktop.ini`.
- After 3d: `IntelliBooks\Books\` is empty.
- After 3e: both folders are empty.
- After 3f: `clients.csv` and `IntelliBooks-Practice.json` name the same clients with the same names and the same codes. Read both back.

**Stop if**

- The vendor mapping count changes at any point.
- Any delete fails because a file is locked. That means something is still running, and stage 1 did not verify.
- `INBOX` is not empty. Do not "clear it afterwards". Nothing in stage 3 starts until it is.

---

## Stage 4. Restructure

**Purpose.** Create 18.2a's layout empty, and move the few things that survived stage 3. **No deletion in this stage.**

**Gate.** Stage 3 verified in all six parts. Decisions 2, 3, 7, 8 and 9 answered, because each one names a folder this stage creates.

**Do**

1. **Create `{practice root}\Intellibills\`** and, beneath it, `Documents\`, `Backups\`, `Receipt Inbox\`, `Review\` and `Resolutions\`. Empty. Per 0.6.1.
2. **Create `C:\Intellibills\db\`.** Outside OneDrive. Empty. Per 0.6.1.
3. **Create `{practice root}\IntelliBooks\Attachments\`, `\Delivery\` and `\Inbox\`.** Empty. `App\`, `Books\` and `Backups\` already exist. Note that nothing writes to `Attachments\`, `Delivery\` or `Inbox\` yet; they are 18.2b and 18.3's, and both are unbuilt. Creating them now is cheap and makes the tree match the document.
4. **Move**, not copy, from `IntelliBooks\` to `Intellibills\`: `clients.csv`, `clients.csv.bak-2026-07-28`, `firms.csv`, `pipeline-status.json`. `Receipt Inbox\` and `Resolutions\` are recreated empty at step 1 rather than moved, since stage 3 emptied them; delete the old ones in a later stage or leave them, but do not delete anything here.
5. **`IntelliBooks-Practice.json` stays** where it is. It is IntelliBooks'.
6. **The 12 database backups**, per decision 7.
7. **Leave `Clients\` alone.** Under 18.2b nothing creates a client folder until IntelliBooks writes one at Post. Creating them empty now would put five folders on a portal with nothing in them.

**Verify**

- Walk the new tree and compare it against 18.2a's diagram, folder by folder, reading the folders back rather than trusting the commands that made them.
- Every file listed at step 4 exists at its new path and does not exist at its old one.
- `clients.csv` at its new path parses, and its row count matches what stage 3f left.
- `C:\Intellibills\db\` exists and is not inside any OneDrive folder. Check the OneDrive sync icon on it, not just the path string.
- **No folder anywhere in the new tree is named `data`.** One listing, one search. That is the whole point of amendment 76 and it is cheap to prove.
- **`{practice root}\Intellibills\Documents\` and `{practice root}\Documents\` both exist and are different folders.** The second is the practice root's own and is what blocks mounting the practice root in a Cowork session. Nothing to fix, but anyone writing "the Documents folder" from here on must give the full path, per `CLAUDE.md`.
- **Nothing was deleted in this stage.** Compare a fresh listing against stage 2's.

**Stop if**

- Any moved file is missing from both its old and new location. OneDrive can hold a move mid-sync.
- A conflict copy appears, such as `clients-DESKTOP-ABC.csv`. Amendment 46 records that risk for `Resolutions\` and it applies to any move inside a sync root.

---

## Stage 5. Change the code, both sides

**Purpose.** Point both modules at the new tree. Written against a tree that already exists rather than one it has to create.

**Gate.** Stage 4 verified.

**Under the interim in 0.5 this stage is a path change and nothing more.** Four coordinated flips, per 0.5.3, and one frozen path that does not move. No 18.2b work, no 18.3 work, no removal of `get_client_directory()`.

**This stage is the one that needs two written briefs, one for Claude Code and one for the Desktop session, and neither exists yet.** `PROMPT_claude_code_step10a_and_10b.md` must not be sent: it was written against the abandoned namespacing scheme and amendment 70 suspended it. **Both briefs must carry 0.5.2's frozen list verbatim**, because the whole risk in this stage is somebody tidying `filing.py` while they are in it.

### The pipeline sites, read from the files today

`config.py` is the choke point and most of the work is there. Lines 8 to 36 hold every constant. Amendment 70's surviving principle applies: **hold the layout in config constants, not string literals.**

| File and line | What it does |
|---|---|
| `config.py:9-16` | `DATA_DIR`, `FILES_DIR`, `LOGS_DIR`, `EXPORTS_DIR`, `DB_PATH`, `RUNS_LOG`, `RECEIPTS_LOG`, all relative to the repository. **`DATA_DIR` is removed, not repointed, and it is four constants that replace it. See 0.6.2, and 0.6.4 for the seven test files that break.** |
| `worker/logging_setup.py:50`, `:69` | The third consumer of `DATA_DIR`, and the one nobody had noticed. See 0.6.3. |
| `config.py:16` and `:24` | **`CLIENTS_CSV` is assigned twice**, first to `BASE_DIR / "clients.csv"` then to `SYSTEM_ROOT / "clients.csv"`. The first assignment is dead. Flagged, not fixed; worth removing while the file is open. |
| `config.py:18-29` | `ONEDRIVE_ROOT`, `SYSTEM_ROOT`, `RECEIPT_INBOX_ROOT`, `FIRMS_CSV`, `CLIENTS_ROOT`, `BACKUPS_ROOT`, `PIPELINE_STATUS_PATH`, `PIPELINE_LOCKFILE` |
| `config.py:36` | `RESOLUTIONS_DIR`, with its `.env` override |
| `config.py:63-68` | The `mkdir` block at import. It creates `SYSTEM_ROOT` and `BACKUPS_ROOT`, so **importing `config` creates folders in OneDrive.** After the move it would recreate `IntelliBooks\Backups\` even if that is no longer where backups go. |
| `config.py:98` | `load_firms()` builds its own `SYSTEM_ROOT / "firms.csv"` rather than using `FIRMS_CSV`. A second source of truth for one path. |
| `worker/storage/store.py:23`, `:37` | The document store layout. **Amendment 77 keeps the shape these two lines already write, so the only change here is where `FILES_DIR` points.** The lines themselves should not change, and a diff that touches them needs explaining. |
| `worker/filing.py:64-65` | `get_client_directory()`, the single choke point for `Clients\`. 18.2b deletes it. |
| `worker/filing.py:78` | `Receipts\{tax year}\` |
| `worker/filing.py:103` | `Statements\{tax year}\{platform}\`, the one amendment 65 found and amendment 55 missed |
| `worker/filing.py:125` | `Review\` |
| `worker/filing.py:157-159` | `_review_dir_for_client_code()` |
| `worker/filing.py:295-297` | The `CLIENTS_ROOT.glob("*/Review")` scan across every client |
| `worker/intake/folder_reader.py:74` | `RECEIPT_INBOX_ROOT` |
| `worker/resolution/service.py:354-361` | `resolve_practice_path()`, resolving Desktop's relative path against `ONEDRIVE_ROOT` |
| `app.py:137` | Writes `pipeline-status.json` |
| `app.py:297` | Reads `RESOLUTIONS_DIR` |
| `app.py:439`, `:451`, `:454` | The daily backup and the 14-file retention sweep |
| `app.py:473`, `:506` | Lock acquire and release |
| `check_test41.py:80` | `RESOLUTIONS_DIR`. Read-only diagnostic, and it should keep working. |

**And the tests.** `tests/resolution_fixtures.py:35-70` saves and replaces eleven config constants by name, and `tests/test_logs_isolation.py:84-89` lists them. `tests/test_capture_inbox_cleanup.py`, `tests/test_auto_retry_cap.py`, `tests/test_auto_retry_no_loop.py`, `tests/test_failure_path_engine.py`, `tests/test_already_filed_guard.py` and `tests/test_resolution_view.py` each patch some subset. **Renaming or splitting a constant breaks every one of them**, and `test_logs_isolation.py` exists specifically to catch a test writing into live paths, so it must be updated deliberately rather than made to pass.

### The Desktop sites, read from the file today

| Line | What it does |
|---|---|
| 443 | `const SYS_DIR="IntelliBooks"` |
| 444 | `sysDir()` |
| 496 | `getDir([SYS_DIR,"Books"],true)` |
| 502 | The legacy migration, `["Clients",safeName(client.name),"IntelliBooks"]` |
| 584, 593 | Reads `pipeline-status.json` from `SYS_DIR`, and opens `Receipt Inbox` |
| 1153 | `getDir([SYS_DIR,"Receipt Inbox",c.code],true)`, the manual upload |
| 1255, 1281 | `scanFiledReceipts()` and `refreshYearSelect()`, both reading `Clients\{name}\Receipts\` |
| 1430 | `Clients\{name}\Handover\{pack date}\`. See decision 8. |
| 1803 | `getDir([SYS_DIR,"Resolutions"],true)`, `writeResolutionNote()` |
| 1819 | `Clients\{name}\Review\`, `scanReview()` |
| 1903 | `Clients\{name}\Receipts\{tax year}\`, `fileReviewReceipt()` |
| 2138 | The generic `getDir(["Clients",safeName(c.name),...subParts],true)` |
| 2296, 2303 | `exportPracticeBackup()`, reading `SYS_DIR\Books` and the legacy path |

**The Desktop handover's standing warning applies to three of these.** Do not touch `writeResolutionNote()`, `scanReview()`, the filing logic, the naming convention or the sidecar Desktop writes without deciding to. All are load-bearing for the back-feed contract that test 41 proved end to end on 29 July.

**Verify**

- `python -m pytest -q` passes in full. The last real run, on 2026-07-30, was 263 passing plus 87 subtests in 10.65 s. Anything below that number needs explaining, not accepting.
- `python -c "import config; print(config.FILES_DIR, config.DB_PATH, config.BACKUPS_ROOT, config.CLIENTS_ROOT)"` prints the new paths.
- **`python -c "import config; config.DATA_DIR"` raises `AttributeError`.** The constant is gone, not repointed, and this is the only check that proves it.
- **No constant in `config.py` derives `DB_PATH` from anything that also parents `FILES_DIR` or `BACKUPS_ROOT`.** Read the file, do not infer it from the printed values: two constants can print different paths today and still share a parent that someone repoints tomorrow.
- Importing `config` creates no folder in the old locations. Check by listing before and after. **`config.py:63-68` currently creates five folders at import, two of them in OneDrive.**
- `python check_test41.py` runs and reports an empty state rather than an error.
- The Desktop file opens, a client can be selected, and the Settings tab renders. Not a functional test; a syntax and load check.
- **Take `IntelliBooks-Desktop-v3.html.bak-before-restructure` before the first Desktop edit**, per the handover's one-backup-per-change rule.
- **The frozen touchpoints are byte-identical to their pre-stage state.** Diff `worker/filing.py` and confirm the only changes are in `file_review()`, `_review_dir_for_client_code()` and the `*/Review` glob. Diff the Desktop file and confirm `scanFiledReceipts()` and `parseSidecar()` are untouched. **This is a diff, not a reading.**

**Stop if**

- The suite drops below its previous count for any reason not understood.
- Any test passes only because it was changed to expect the new path without the behaviour being checked.
- **Any frozen function in 0.5.2 shows in the diff.** Revert it and ask, rather than judge whether the change was harmless.

---

## Stage 6. Start, run one clean cycle, confirm

**Purpose.** Prove the new tree works, on paths nobody has run since May: an empty database, `init_db()` from nothing, `clients.csv` resolution with no history, and Desktop opening a books file it has to create.

**Gate.** Stage 5 verified.

**This stage runs against the interim contract, per Paul's third condition.** It is not deferred until 18.3 lands. The restructure moved four paths and left one frozen, and stage 6 is what proves both halves of that: the four flips work at their new locations, and the frozen path still carries a receipt into the books exactly as it did before. **A restructure that is not exercised is a restructure that is not finished.**

**Do**

1. `init_db()` against the new `DB_PATH`. Confirm it creates every table and that `PRAGMA journal_mode` reads `wal`.
2. Re-import the vendor mappings **only if stage 3a's verification showed them lost.** If the table still reads 101, do nothing. `import_vendor_csv.py` and `seed_client_vendors.py` exist for the purpose.
3. Start the pipeline. Confirm `pipeline.lock` appears at its new path and `pipeline-status.json` updates at its new path.
4. **One receipt, end to end, on the interim path.** One email with one attachment, to a client that exists in both registries. Watch it through intake, extraction, validation, categorisation and filing into `Clients\{client name}\Receipts\{tax year}\`.
5. **Open IntelliBooks Desktop and let `scanFiledReceipts()` find it.** This is the frozen contract and it is the half most likely to have been broken by accident.
6. **One Review item.** File it in Desktop and confirm the resolution note reaches `Intellibills\Resolutions\`, the pipeline consumes it, the note moves to `processed\`, and the database reads `ok`. This is test 41 again, against the new tree and the moved `Resolutions\` and `Review\` folders.
7. **One post.** From the books to the cashbook.

**Verify**

Take these in two groups, because they prove different things.

**The four flips**

- The receipt's file lands at `Intellibills\Documents\{CODE}\{year}\{month}\{receipt id}_{filename}`, with **the client's code as the first level and no day folder anywhere**, per 0.6.5. Read the actual path back; do not infer it from the receipt appearing in the books.
- **`{year}\{month}\` is the month the receipt arrived, not the month on the document.** Prove it with a receipt whose document date falls in a different month from today, or the check passes without testing anything.
- **`C:\Intellibills\db\` holds `receipts.db` and, while the pipeline runs, its `-wal` and `-shm` companions. `Intellibills\Documents\` and `Intellibills\Backups\` hold no `.db` file of any kind.** This is what amendment 72 exists to guarantee and it is one listing.
- `Intellibills\Backups\` gains one file on the first run of a new day, and `IntelliBooks\Backups\` gains nothing.
- Desktop reads `pipeline-status.json` from `Intellibills\` and shows a current `last_run`.
- A file dropped through Desktop's manual upload lands in `Intellibills\Receipt Inbox\{CODE}\` and the pipeline collects it.
- The Review item appears under `Intellibills\Review\{CODE}\`, keyed on the **code**, and Desktop's Review tab lists it. Per 0.5.3, this is the one that changes shape as well as location.
- `Intellibills\Resolutions\processed\` holds exactly one note and `failed\` was never created.

**The frozen path**

- The receipt is in `Clients\{client name}\Receipts\{tax year}\` with its sidecar beside it, two files.
- **In Desktop, that receipt shows a supplier and an amount.** Not "Image only. Edit details.", not a red **No amount** pill, and no `img_` twin beside it. Amendment 57 is the reason this is spelled out: a books entry can appear and be worthless.
- It carries a thumbnail.
- Rescan and no second entry appears.

**Both groups**

- `receipts` holds exactly one row, with the right `client_id`, and `client_id` is not `UNKNOWN`.
- `processed_attachments` holds exactly one row.
- `categorisations_client_vendors` still reads 101, plus whatever the run legitimately learned. **Check this last as well as first.**
- **Quote screen counts, not file counts**, in anything written for Paul to follow. The receipts list is filtered by tax year, so pick a receipt whose document date sits in the year the tab is showing, or the check reports zero of everything and passes for the wrong reason.

**Stop if**

- The receipt is resolved to `client_id=UNKNOWN`. That means `clients.csv` and the mailbox disagree, and it is exactly what stage 3f was meant to prevent.
- More than one OpenAI call is made for one attachment.
- **The receipt reaches the books with no supplier and no amount.** That is the frozen contract broken during stage 5, and it is the one failure the freeze exists to prevent.

---

## 3. What this plan does not cover, deliberately

- **The three postponed items in 18.10.** They come after the reset, per the handover's Start here, and two of them concern data this operation deletes.
- **Building 18.3's inbox handoff**, or IntelliBooks' write into `Clients\` at Post, or the delivery log, or section 13A's move to IntelliBooks. All are section 18 work, all are larger than this operation, and none is a prerequisite for it under the interim in 0.5. **The acceptance check that ends the interim is in 0.5.1 and it belongs to whichever session builds the inbox, not to this plan.**
- **The rewrite of steps 10a and 10c** in section 16 of the design document. They should be rewritten against this plan once it is agreed, not before.
- **The two briefs stage 5 needs.** Written after the decisions, not before.

---

## 4. Confidence

**High on section 1.** Every figure was read today from git, the database or the filesystem, and the database counts were taken from a copy of the live file. Two things in it are inference rather than observation and both are marked: what the 24 `.fuse_hidden` files are, and what wrote `receipts.db-shm` at 14:00 today.

**High on section 0.1**, the interchange finding, because both halves were read from the file: `worker/filing.py:78` and `IntelliBooks-Desktop-v3.html:1281` and `:1288`. **And high on the claim that `IntelliBooks\Inbox\` is unbuilt**, from grepping both codebases for it.

**High on the stage 5 site lists.** Every line number was grepped today. They will move with the next edit, so search rather than trust them.

**Medium on completeness of the stage 5 pipeline list.** It comes from grepping the eleven config constant names. Anything that hardcodes a path as a string literal rather than reading a constant would not appear, and I have not searched for that.

**Not verified: the mailbox.** It cannot be checked from this session and it is stage 3's most expensive gate.

**Not verified: whether a pipeline process is running.** The lock file says one started on 29 July. Whether pid 31156 is alive can only be answered on Windows.

**Dates in this plan, and an error of mine that ran in both directions.**

**Established from evidence rather than from a clock**, because a clock was what caused the trouble. `ac2d1be`, the commit carrying section 18 and amendments 65 to 74, is authored `2026-07-31 15:38:54 +0100`. This session began at `2026-07-31 15:54:25 +0100` and took its verification copy of the database at `2026-07-31 15:55:08 +0100`, which is timestamped and is the "before" in section 1. **So this plan, its section 1 state, the interim in 0.5 and the paths in 0.6 are all 2026-07-31.** The session then ran past midnight, so 0.6.5, amendment 77 and the closing of decisions 3 and 6 are 2026-08-01.

**What I got wrong, twice, in opposite directions.** First I dated a note in 18.2a `2026-07-31` when correcting Paul's `2026-07-30`. **That was right.** Then, on noticing that the calendar had turned over to 1 August, I redated the plan, its filename, amendments 75 and 76 and the v1.7 heading to 1 August in one pass. **That was wrong, and it was the worse of the two**, because it took work that was correctly dated and made it incorrect, and it did so under the heading of a careful correction. A blanket replace over a document whose whole purpose is to record a sequence is the specific thing not to do.

**Both are reverted. The full sequence is in the 18.2a note itself** and is deliberately not summarised away.

**And the reason none of it could be settled from git: I have committed nothing.** Amendments 75 and 76 exist only as edits to a working file, so their dates rest on this session's start timestamp rather than on an author date. Had they been committed as they were written, there would have been nothing to argue about. `CLAUDE.md` asks for three to five commits a session and this session has made none.

**On section 0.6.** The three paths are Paul's decision of 2026-07-31, recorded as amendment 76, and 18.2a in the design document was rewritten by Paul rather than by me; I read it back from the file before writing 0.6. **Two defects in that rewrite were found and fixed while reading it back**, and both were mechanical rather than substantive: the first column of 18.2's archive row still read `{year}\{month}\{day}\` while its own note said otherwise, and a paragraph had been inserted between two rows of the three-store table, orphaning the `Clients\` row from it.

**On section 0.6.5.** Paul's decision of 2026-08-01, amendment 77, on a finding of mine that he verified before acting on. High: the two shapes on disk were counted, and `worker/storage/store.py:20` and `:34` were read. **High on 0.6.3 and 0.6.4**, both read today: `worker/logging_setup.py:39`, `:50` and `:69`, and the seven test files listed by grepping `tests\` for `DATA_DIR`. **Two things in 0.6 are mine and are flags rather than decisions:** where the process logs go, and the overlap with decision 9.

**On section 0.5.** The exception and its three conditions are Paul's decision of 2026-07-31, recorded here and as amendment 75 of the design document. **High on the frozen list in 0.5.2 and the flip table in 0.5.3**, every line grepped today from the two files. **Medium on the acceptance check in 0.5.1:** checks 1 to 5 test behaviour that can be observed on screen or on disk, and check 6 tests a mechanism that does not exist yet, so it is written against what `filed_path` and `filed_at` do today rather than against what replaces them. Revisit it when 18.3 is specified.

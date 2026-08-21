# Outstanding items and decisions

## 133 open, 9 closed, 142 raised

**133 plus 9 must equal 142, the highest number ever used.** If it does not, an item was removed without being recorded. Checked 2026-08-21, after closing items 26, 104 and 139 and raising item 142.


**Opened 2026-08-20 by the consultant session. Rewritten twice the same day: once after a sweep of the session added twenty items, and again after a four-part sweep of every unread document added the section 8 items. Amended 2026-08-21 twice: section 9 added, being 19 items found by enumerating folders and reading live data files rather than documents; then section 10 added, being 28 items found by reading everything section 9 had recorded as unread, and four items above corrected or withdrawn as a result.**
**Date read from a file timestamp, not from a session header. Amendment 109.**

**A closed item keeps its number and moves to the Closed section at the end.** Numbers are never reused, so the highest number is the count of items ever raised.

**This and section 16 of `2026-07-25_CONSOLE_DESIGN.md` are the only two lists.** Section 16
is the chronological build order: everything decided. **This file is everything not decided,
not scheduled, or waiting on somebody.** If an item here becomes a decision it leaves this
file and becomes a step in section 16.

**Ordered by what it blocks, not by where it came from.** The two lists at the end of
`IntelliBooks\App\Docs\IntelliBooks-Change-Log.md` were removed on 2026-08-20 and their
contents are here. Section 7 of `2026-08-20_HANDOVER_consultant_chat_8.md` is superseded by
this file. Neither should be added to again.

---

## 1. Blocking a scheduled step

| # | Item | Blocks |
|---|---|---|
| 1 | **Where an unattributable intake event is logged.** `app.py:1094`'s unknown sender has no firm by definition, and `firm_id` names the event log file at `app.py:102` and `worker/extraction_pipeline.py:96`. A reserved log name and a firm-agnostic intake log are both defensible. Section 8.6's intake panel exists to surface this class of item | step 10d |
| 2 | **Where Client Settings live in the menu.** Proposed 2026-08-20 as a centre-group item beside Client Data. Not decided | step 10e |
| 3 | **Whether System Settings is its own document or a section of `2026-08-20_LIST_settings_firm_and_client.md`.** The answer decides whether that file keeps its firm-identity rows or loses them | updating the settings list, and 10e |
| 4 | **Updating `2026-08-20_LIST_settings_firm_and_client.md`.** It needs three columns it does not have: whether each store can hold more than one value, whether the setting is externally held, and what constitutes a firm as against what a firm sets. **A firm is currently three fields**, being `firms.csv`'s `firm_id`, `name` and `email` | step 10e |
| 5 | **What `refreshMatches()` requires of the amounts.** 18.5b's one residual case, whether a Difference check is justified where the app found the match itself rather than the operator choosing it, depends on it. **Never read** | step 10g |
| 6 | **Whether the `processed_attachments` primary key should include `firm_id`.** Amendment 116 adds the column as informational and states the key stays `(message_id, attachment_id)`. **That rested on an assumption about a shared mailbox rather than on a decision** | step 10d |
| 142 | **Whether the reload mechanism at 8.6 applies to `clients.json`.** 8.6 specifies it as a marker file the console writes, with `app.py` calling `config.load_clients()` again at the top of each `process_once()` if the marker is newer than the last load, and explicitly no signal handler and no IPC channel. **The reason for it does not change when the file becomes JSON:** `config.CLIENTS` is still loaded once at import, at `config.py:149`, so a client registered while the pipeline is running is not seen until a restart, and the console's **Register this client** action would appear to do nothing. **What changes is the number of readers.** After step 10d the capture app reads the registry over Graph and IntelliBooks reads it too, so a marker only the pipeline honours serves one reader of three. Raised 2026-08-21 by amendment 125, on Paul's question | steps 10d and 18 |

## 2. Waiting on Paul

| # | Item |
|---|---|
| 7 | **Part D of the check in `IntelliBooks\App\Docs\2026-08-20_REPORT_desktop_menu_groups.md`.** Change log item 39 cannot be recorded as passed until all four parts are run, and part D needs a review item created by hand because the pipeline has never produced a possible duplicate |
| 8 | **Files uncommitted in git**, which is what produces the pipeline's startup warning about the working tree |
| 9 | **A live test of change log items 19 to 23 in the real app.** Built and syntax-checked only |
| 10 | **The Windows scheduled task at logon for the pipeline.** Named in `SETUP-v5.md`, never confirmed either way, and `IntelliBooks.bat` claims it exists when it does not |
| 11 | **Whether to tidy the six Test 2 books entries** from change log item 21, being date-bug duplicates and old stub rows. Paul has said no urgency |
| 12 | **`clientType` on TEST and Test 2 was set to `sole_trader` by the building session, not on Paul's instruction.** Change log item 36 records it. Two clicks in the Edit Client window |
| 13 | **All three scheduled tasks live on `pdk7@hotmail.co.uk`**, not on `paul.keating@intellitax.co.uk`, being the April HMRC check and the February and August Sage drift backstops. **A practice maintenance task that fires once a year sits on a personal account**, and if that account lapses the reminder goes with it |
| 14 | **`2026-08-15_RUNLOG_coa_august_check.md` records the drift verdict as outstanding and it is not.** Paul confirmed no drift on 2026-08-20. **That file exists only in the Claude project and nowhere on disk**, per `2026-08-18_INSTRUCTION_coa_authority.md` |

## 3. Defects flagged and not fixed

| # | Item |
|---|---|
| 15 | **`delCategory()` cannot protect anything, and a category with transactions can be deleted with no warning.** Line 2410 of `IntelliBooks-Desktop-v3.html` builds its guard as `String(v\|\|"").toLowerCase()===c.name.toLowerCase()` and compares it against `t.category`, `r.category` and the rules, **all of which have held four-digit codes since the chart adoption**. All three counts are always zero. Read back at lines 2406 to 2418. **Whether the fix is the guard or an id on a category is a decision, which is why this is here and not scheduled** |
| 16 | **`send_unknown_sender_alert()` at `worker/email/alerts.py:54` hardcodes "Lasting Impact" and `support@lastingimpact.co.uk`.** Its sibling `send_no_attachment_alert()` at `:11` takes a `firm_name` argument and is correct. This one has no firm argument at all |
| 17 | **`categorisations_firm_vendors` has no firm.** It keys on `UNIQUE(business_type, vendor_code, vendor_name)` and `engine.py:281` looks it up as `list_firm_vendors(business_type)`. In a multi-firm product this would apply one firm's learned vendor mapping to another firm's clients. The table is empty, so nothing has crossed |
| 18 | **`receipts.source = 'capture'` does not mean the capture app.** `worker/intake/folder_reader.py` sets it as a literal on every record `scan_inbox()` builds, so it means "found in the Receipt Inbox" whatever put it there |
| 19 | **`bankFilter()` searches on the category name**, which has been display only since the chart adoption, so a search matches names and cannot match a code |
| 20 | **`renderReports()` and the VAT report are keyed on the category name**, at lines 2191 and 2235 as at change log item 38 |
| 21 | **`loadSampleData()` hardcodes five old category names, two of which are not in the master chart at all.** It is the only way to get transactions into a fresh books file, so it sits in the path of anyone testing, **and it is the obvious source of the demo version's data** |
| 22 | **`"GBP"` appears twelve times in production code**, six in `app.py`, four in `worker/resolution/service.py` and two in `worker/extraction/openai_vision.py`, plus the schema default. The schema default is scheduled in 10d; the twelve literals are not |
| 23 | **`vatScheme` is written into `IntelliBooks-Practice.json` and read back only into the window that set it.** Not a defect today, a place not to build on |
| 24 | **`firms.csv`'s `email` column is loaded into `config.FIRMS` and consumed by nothing.** `config.FIRMS` is read at exactly one place, `app.py:839`, which takes `name` |
| 25 | **`EXPORTS_DIR` has no reader outside `config.py`**, which creates it at import |
| 140 | **A two-digit year always becomes a 2000s year, and the branch below it is dead.** `worker/extraction/postprocess.py:60` reads `if c < 100: year = 2000 + c`, so `01/01/99` resolves to **2099** and no note is recorded. `:62` to `:64`, `elif c < 1000`, has the same body as the branch above it and a comment reading "unlikely, treat as 2000s" where 2000 plus 999 is 2999. **Findings 3 and 4 of the seven in section 10.2**, which step 6 exposed and step 6b did not fix: 6b took findings 1, 2, 6 and 7 only. **One edit fixes both, which is why they are one item.** Nobody has ever decided what to do about them |
| 141 | **`rate_tol = 0.03` at `worker/extraction/postprocess.py:113`, and the penny rule does not govern it.** Finding 5 of section 10.2's seven, also unfixed. It is absolute, so it allows 17 to 23 per cent on the standard rate and **2 to 8 per cent on the reduced rate**, which is 60 per cent either side. **Read before writing this: it measures a different quantity from the other tolerance.** `:108` and `:115` compare an implied rate, `v / (n - v)`, against `0.2` and `0.05` to decide whether an amount the model called net was really gross. `worker/validation/rules.py:7`'s `_VAT_TOLERANCE = 0.02` is a tolerance **in pounds** on whether the VAT figure agrees with the net. **So step 10g's change of `rules.py` to one penny does not cover this, and copying the penny rule across would be wrong.** Three values now exist for what reads like one concept |

## 4. Firm and client settings the firm cannot see or control

Found by the settings list of 2026-08-20 and not carried anywhere until now.

| # | Item |
|---|---|
| 27 | **The practice root is held twice in two incompatible forms and nothing checks they agree.** The pipeline holds a path at `config.py:24`; IntelliBooks holds a browser folder handle in IndexedDB under the key `rootHandle`, which is not in `IntelliBooks-Practice.json` at all. **Pressing Change practice root folder moves the books and leaves the pipeline writing where it always wrote** |
| 28 | **Two client settings exist in two places and the client's copy wins.** Confirm mode and the PHV platforms are in `IntelliBooks-Practice.json` and in the phone's own storage, and the phone's copy decides what the phone does. **Nothing reports a divergence** |
| 29 | **One client setting exists only on the client's phone.** The statement week ending day, `localStorage["ib_client"].weekEnd`, set at capture app `index.html:244`. It decides which weeks the statements checklist asks for. **The firm cannot read it, restore it, or know it changed**, and clearing a browser loses it |

## 5. Decisions not taken

| # | Item |
|---|---|
| 30 | **Who owns changes to `build_coa.py`.** IntelliCharts has no session and every change so far has been made by an ad-hoc session. IntelliCharts is parked, so this waits |
| 31 | **Whether `2026-08-18_BOUNDARY_two_products.md` stays in Intellibills' repository.** Its own section 1 says the placement is provisional and why it is uncomfortable |
| 32 | **The files in the repository root.** Handover 7 said 57 markdown and CSV files, handover 8 said 61, and **neither figure has been produced by a command anyone has seen.** `PROMPT_claude_code_step10a_and_10b.md` must never be sent: it was written against a folder scheme abandoned in July. `PROMPT_intellibooks_desktop_changes.md` must not be touched |
| 33 | **The capitalisation threshold.** `0030 Office equipment` and `0035 Computer equipment` are assets and `7502` and `7552` are the expense route. **The chart cannot decide which a receipt goes to.** The chart of accounts note says it is a policy figure and belongs in the design document |
| 34 | **A statement period straddling 5 April.** 18.2b's own open item: a statement running 1 March to 30 April, and whether it appears in both tax year folders |
| 35 | **Categories in receipts and transactions**, 18.10, which also decides whether category appears in the Difference check at all |
| 36 | **Whether a filed receipt ever gets a correction route**, 18.10. Under 18.6 a receipt is editable while it waits, so what remains is whether a figure recorded wrongly in the pipeline's own record can ever be corrected there |
| 37 | **Where the process logs go**, 18.2a's open item, entangled with whether `logs\` and `exports\` stay in the repository. `logs\runs.ndjson` and `data\run.log` were one letter apart, which is what the question exists to remove |
| 38 | **Whether the demo shares `IntelliCharts\` or takes its own copy**, and whether the phone is demonstrated at all. Both in `2026-08-20_NOTE_demo_version.md`, which is parked |

## 6. Cloud only

**Local multi-firm is not built and will not be built.** Paul's decision, 2026-08-20.
Multi-firm lives only in the cloud. These are recorded so nobody schedules them locally, and
they are the agenda for the cloud version's first design session.

| # | Constraint |
|---|---|
| 39 | One capture mailbox. `capture@lastingimpact.co.uk`, redirected to `bills@intellitax.co.uk`, one IMAP account. A real product gives each firm its own capture address, which the 22 July analysis named as an option and never examined |
| 40 | One OneDrive. `ONEDRIVE_USER` on Netlify is a single value |
| 41 | One Netlify deployment, one Azure app registration, one `AZ_TENANT_ID` |
| 42 | One browser folder grant, so one firm is open at a time |
| 43 | One practice root and **no firm level in any path**, so two firms with a client of the same name collide in `Clients\` |
| 44 | `email_delta` holds one `delta_link` and one `last_uid` as global singletons |
| 45 | `email_alerts` carries `firm_name`, a copied string, and no `firm_id` |
| 46 | `statements` carries `client_id` and no `firm_id`, unlike `receipts` |
| 47 | Item 17 above, `categorisations_firm_vendors`, which is the only one of these that is a leak rather than a limitation |

**And one thing about email that is settled and worth not relitigating.** The webhook replaces
the poll, so almost none of the local email machinery survives: no MIME parsing, no regex, no
routing across eight `INBOX.*` folders. **But the client lookup does survive**, because an
emailed receipt carries no credential and an address is still an address. The 22 July analysis
says "no `clients.csv` lookup needed", and that is true of the phone and not of email.

## 7. Deferred by decision

| # | Item |
|---|---|
| 48 | **Beancount export.** Phase 2, with forward-compatibility measures already in place |
| 49 | **Statement parsing.** The Uber parser is a separate repository with its own project and is not scheduled here |
| 50 | **IntelliCharts.** Parked. The default chart of accounts is sufficient for Intellibills and IntelliBooks to continue. **Three of the master's columns are read by nothing and that is deliberate**, being `frs102_1a_line`, `frs105_line` and `mtd_itsa_category`: Paul's decision to populate them and park their use. Not defects, and not to be built on |
| 51 | **The demo version.** Parked, with `2026-08-20_NOTE_demo_version.md` as its starting point |
| 52 | **The cloud version.** Parked. Section 6 above is its inbox |

## 8. Found by the four-part document sweep of 2026-08-20

Four parallel sweeps read `2026-07-31_PLAN_reset_and_restructure.md`, the seven
`REPORT_claude_code_*.md` files, ~~the seven documents in `IntelliBooks\App\Docs\`~~
**seven of the sixteen documents in `IntelliBooks\App\Docs\`, corrected 2026-08-21 by listing
the folder: it holds 21 files, five of them `.bak` copies of the change log, plus a
`Claude CoWork Sessions` sub-folder that had never been listed**, and `CLAUDE.md` with
`RECEIPT_CAPTURE_GUIDE.md`,
`CATEGORISATION.md` and `EMAIL_PROCESSING_MICROSTEPS.md`. **About 370 raw findings.**
Most were closed, superseded by the 2026-08-01 reset, or duplicates of items above.
These are what survived.

**Three findings were verified against today's state and are closed rather than carried:**
the seven test files that patched `config.DATA_DIR` were updated and
`tests/test_path_layout.py:105` now asserts the constant cannot return;
`.git\index.lock` is gone; and the event logs were archived into `Intellibills\Backups\`.

### Defects seen and deliberately left

| # | Item |
|---|---|
| 54 | **`learn_from_correction()` raises `TypeError` if reached.** `worker/categorisation/engine.py:399` passes `vendor_key` to `upsert_client_vendor()`, which has no such parameter and requires `vendor_code`; the same method also passes `vendor_key` to `get_firm_vendor()` and `upsert_firm_vendor()`. Unreachable today because the only outside references are in `docs/specs/`. **Paul has seen it and said to leave it** |
| 55 | **`renderReports()` and the VAT report make the profit and loss wrong, not just cosmetically.** `catType[c.name]=c.type` at line 2171 is read with `\|\|"expenses"` at 2175, so with categories now keyed on code every transaction falls to the default and income is reported as expenditure. Item 20 above named the keying; this names the consequence |
| 56 | **`t.category` is not always a code or empty:** a linked transfer pair carries the literal `"(Transfer)"`. Recorded so nothing is written that assumes otherwise |
| 57 | **A malformed sidecar loses its image**, because `JSON.parse` throws before the image is claimed and the `catch` only warns. And **a loose PDF with no sidecar never enters the books at all**, because line 1233 tests `if(!/^image\//.test(f.type))continue;` |
| 58 | **The Receipts tab has no Category column**, so the field that blocks posting cannot be seen from the screen where posting starts |
| 59 | **`t.category=r.category\|\|""` is unguarded at both cashbook call sites** while `attachReceipt()` guards it, and both are where 18.5a and 18.7 land |
| 60 | **The To Cashbook button is offered on rows posting will refuse**, being any row where `rGross(r)<=0` |
| 61 | **`updRule()` is a second door onto duplicate rules**, and `addRule()` accepts a one or two character pattern with no minimum length check |
| 62 | **`delCategory()` does not check Review items**, so a category a review item points at can be deleted |
| 63 | **`exportPracticeBackup()` reports orphaned books files rather than including them.** A decision, not a side effect |
| 64 | **Two toasts collide in `exportHMRC()`:** the unmapped-categories warning is overwritten by the success toast, and the warning is the more important. Unobserved, because `exportHMRC()` has never been run |
| 65 | **`fileReviewReceipt()`'s success toast prints the raw client name** while the folder was created with `safeName()`. Three of this class were fixed and this one remains |
| 66 | **Two stale comments in `IntelliBooks-Desktop-v3.html`:** line 1752 cites amendment 53, which section 18.9 lists as cancelled, so the comment now argues against the decision; and the root-picker gate text at line 558 describes the pre-item-12 layout as current, and it is the first sentence a new operator reads |
| 67 | **A legacy migration read in `loadBooks()` at line 506 reads a layout that no longer exists anywhere.** Looks removable and was not removed |
| 68 | **`renderAll()` loses interface state**, because `renderAccounts()` rebuilds the account filter with no selection restored and runs before `renderBank()`, which reads it |
| 69 | **There is no backup beside `IntelliBooks-Desktop-v3.html` that can be reverted to and still leave a working system**, and reverting fails silently because every read is inside a `catch` that returns quietly |
| 70 | **`RESOLUTIONS_DIR` has an environment override on the pipeline side and none in the app**, so setting it parts the two halves silently. Not live, because the variable is not set |
| 71 | ~~**`tests/test_resolution_view.py:283` still seeds a three-digit `nominal_code`** as a literal in its own temporary database~~ **Corrected 2026-08-21 by reading all 40 files in `tests\`: it is five files, not one.** `test_resolution_service.py`, `test_resolution_view.py` (two separate methods, not only the one at :283), `test_retroactive_categorise_sidecar.py`, `test_sidecar_category_keys.py` and `test_vendor_import_requires_client_id.py`. The values are `271`, `999`, `500` and `103`. **The last of those five is different in kind and is not a stale literal:** `test_vendor_import_requires_client_id.py:30` and `:35` are CSV fixtures in the format `seed_client_vendors.py:85`'s comment describes, `"103 Fuel,,,"`, so a three-digit chart is the input format of a legacy import path. Whether that path survives at all is undecided |
| 72 | **`RECEIPTS_LOG` at `config.py:52` is a dead constant** whose value `tests/test_path_layout.py:83` nonetheless asserts. The real file is per firm, built at `app.py:102` |

### From the reset plan, still open

| # | Item |
|---|---|
| 73 | **Whether an export belongs in the client's own folder rather than `Intellibills\Exports\`.** The location was decided; this rider was not. "Paul has called it a real choice" |
| 74 | **`worker/filing.py:103`, statement filing into `Clients\{name}\Statements\{tax year}\{platform}\`, is deliberately not frozen and has no interim contract.** The `statements` table is empty, no `Statements\` folder exists under any client, and nothing reads it. **Do not assume the 18.2b freeze covers everything in `filing.py`** |
| 75 | **`config.py`'s `mkdir` block still creates five folders at import, two of them in OneDrive.** The trap is in `CLAUDE.md`; the behaviour is unchanged |
| 76 | **The lost `Client_003` vendor mapping.** The only thing in the entire reset that was not test data, recoverable from `Intellibills\categorisations_client_vendors_cleaned.csv` if it is ever wanted. No decision recorded |
| 77 | **What "filed" means and what `filed_path` points at once the pipeline stops filing into `Clients\`.** Named in the reset plan and unanswered |
| 78 | **Check 6 of the interim's close condition is written against a mechanism that does not exist**, so it tests what `filed_path` and `filed_at` do today rather than what replaces them. Revisit when 18.3 is specified |
| 79 | **Registry settings never carried across the reset.** All clients were `vat:false`, and the `yearEnd`, `mtd` and `mtdBasis` values are set on four of six clients. To be set per client |
| 80 | **What wrote `data\receipts.db-shm` at 14:00 on 2026-07-31 was never explained**, and the count of `.fuse_hidden` artefacts does not reconcile: 24 found, nine deleted |

### Undecided, from the IntelliBooks documents

| # | Item |
|---|---|
| 81 | **PHV mode across the capture app, statement routing and statement filing** is specified in section 5.3 of `IntelliBooks-System-Specification.md` and unbuilt. It is Intellibills' work and separate from the Uber parser, which parses statement contents |
| 82 | **How a `needs_review` query reaches the client.** Phase 2 in the specification and nowhere else |
| 83 | **How the relationship between two rules for one supplier is surfaced.** The larger question behind change log item 30 |
| 84 | **Whether the `exportHMRC()` toast collision is fixed with one composed string or two calls**, and whether the raw client name in three toasts is fixed with a shared helper or three edits |
| 85 | **Two accepted security exposures**, recorded in specification section 6 and never revisited: anyone with a client's capture link can add files to that client's inbox, and the Graph application permission is `Files.ReadWrite.All`, which is tenant-wide |

### Outstanding checks nobody has run

| # | Item |
|---|---|
| 86 | **Seven chart-adoption checks for Paul, all outstanding**, listed in section 14 of `IntelliBooks\App\Docs\2026-08-17_REPORT_desktop_renderRules_fix.md`. Checks B, C and D were verified by reading books files on disk, not on screen; check E, a partnership with no partners, was later run and passed |
| 87 | ~~**The five-step `HMRC Summaries` check has never been run**, and `exportHMRC()` has never been run at all~~ **Both halves corrected 2026-08-21 by listing `Clients\` on disk. `exportHMRC()` has been run twice** and its output is there: `Clients\TEST\HMRC Summaries\test-hmrc-2025-04-06-to-2026-04-05.csv`, written 2026-08-17, and `Clients\Test Company\HMRC Summaries\testco-hmrc-2025-04-06-to-2026-04-05.csv`, written 2026-08-18. **The folder name is `HMRC Summaries` in both, which is the single assertion the five-step check exists to make**, so the thing being tested is demonstrated even though the check as written cannot be run: it is written against client `PKPH`, which is gone. **What is still untested is the CSV's contents**, being step 5 of that check, the fifteen SA103F rows and the absence of a `,WARNING` line |
| 88 | **The Review seam has never been tested against a review item the pipeline itself produced.** The first real `needs_review` receipt is the test |
| 89 | **The contents of `handoverPack()`'s six files have never been checked against a real set of books** |
| 90 | **Change log items 19 to 23 have never been tested live**, which is item 9 above, and the weekly Netlify function log review named in the specification has never been established as a routine |

### One class of finding, not one item

| # | Item |
|---|---|
| 91 | **`CATEGORISATION.md` uses three-digit GL codes throughout and gives code `105` two different account names in one file.** Scheduled in step 10h with the other five stale documents, and named here because it is the one that actively teaches the thing the four-digit scheme exists to make detectable |

## 9. Found on 2026-08-21, by opening what the 2026-08-20 sweep had not opened

**Added because the answer to "is everything that should be on these two lists here" was no.**
The 2026-08-20 sweep read named documents. It did not enumerate the folders those documents
sit in, and it read no live data file. **This pass enumerated four folders and read five data
files**, being `C:\LastingImpact\receipt_capture\` (69 markdown files, 20 read and 49 not),
`IntelliBooks\App\Docs\`, `IntelliBooks\Books\`, `worker\` (20 Python modules), and then
`Intellibills\clients.csv`, `Intellibills\firms.csv`, `Intellibills\pipeline-status.json`,
`IntelliBooks-Practice.json` and `IntelliCharts\COA_MASTER_v1.csv`.

### A second chart of accounts, inside the pipeline

| # | Item |
|---|---|
| 92 | **`worker\categorisation\coa.py` is a second chart of accounts, hardcoded in Python, and not one of its codes agrees with the master.** It holds three templates on four-digit codes, `PHV_DRIVER` with 21 accounts, `CONTRACTOR` with 15 and `UNSPECIFIED` with 7, being **22 distinct codes**. Compared against all 122 rows of `IntelliCharts\COA_MASTER_v1.csv`: **eight codes do not exist in the master, fourteen exist under a completely different name, and zero match.** `1100` is "Motor Vehicles" here and **"Trade debtors"** in the master. `7100` is "Employer NI" here and **"Rent"** in the master. `8100` is "Accountancy Fees" here and **"Irrecoverable debts written off"** in the master. **These are not near misses. They are valid master codes pointing at the wrong account**, which is the one kind of wrong code no validator can catch |
| 93 | **Nothing has been posted from it, and that is a flag setting rather than a design.** Its only caller is `worker\categorisation\engine.py:336`, inside `_ai_suggest()`, reached only from `engine.py:301` behind `self.enable_ai_fallback`. That defaults to `False` at `engine.py:150`, is passed `False` explicitly at the only production construction, `app.py:664`, and `False` in all five test constructions. **Turn that one argument to `True` and layer 4 begins suggesting codes from item 92's list.** Whether the fix is to delete `coa.py`, to make it read the master, or to delete layer 4 altogether, is a decision, which is why this is here and not scheduled |
| 94 | **The prompt sent to OpenAI contradicts itself on the code format.** `engine.py:368` describes the return field as `"GL code (e.g., 103, 281)"`, which is three-digit and therefore legacy by amendment 96, in the same API call that lists four-digit codes as the valid set |
| 95 | **`get_coa_for_client()` at `coa.py:73` has no caller anywhere**, and its docstring promises a future per-client override in a `coa_client_codes` table. **That table is cancelled**: there is no chart inside the pipeline's database and there will not be one |
| 96 | **`business_type` values in use do not match the templates that exist.** `clients.csv` holds `PHV_DRIVER`, `ACCOUNTANCY` and `UNSPECIFIED`. **`ACCOUNTANCY` has no template, so `coa.py:70`'s `.get(business_type, _COA_TEMPLATES["UNSPECIFIED"])` silently returns the 7-account fallback**, which is the same silent-default class as the `UNKNOWN` fault. `CONTRACTOR` is a template no client uses |

### The two registries, read side by side for the first time

| # | Item |
|---|---|
| 97 | **The two client registries have no client in common. The intersection is empty.** `Intellibills\clients.csv` holds `UNKNOWN`, `PKPH`, `INTELLITAX`, `TEST3`, `TEST4` and `SHERUNSIT`. `IntelliBooks-Practice.json` holds `TEST`, `TEST2`, `TESTCO`, `TESTST`, `TESTP` and `ZPO`. **Both sets were enumerated, not filtered.** Amendment 111 point three already decides what comes across, so this is not a new decision; it is the scale of the divergence, which no document states |
| 98 | **`IntelliBooks\Books\` holds a seventh books file, `PSHIPN-books.json`, which is in neither registry**, and **amendment 111 point three is factually wrong about today's disk because of it.** It reads "seven clients come across, the six in `IntelliBooks-Practice.json` plus `PKPH`, with their books files renamed". **`PKPH-books.json` no longer exists**, deleted per the change log's own plan, and `PSHIPN-books.json` exists and is not mentioned. So the brief for step 10d, written from that amendment, would carry across a books file that is not there and ignore one that is. **`PSHIPN-books.json` was written 2026-08-18 13:54:53 UTC and `IntelliBooks-Practice.json` 13:57:03 UTC, two minutes apart**, which suggests a partnership test client created and then renamed, leaving the books file behind. **That is inference from two timestamps and a name, not a reading of either file, and it needs Paul rather than a build session** |
| 99 | **Check 1 of `PAUL_CHECKS_2026-07-30.md` is live again, against a different client.** That check exists to make the practice backup name a books file with no client in the list. It named `PKPH`; `PKPH` is gone; **`PSHIPN` is now in exactly that position and nothing reports it.** The check itself has never been recorded as run, though the deletion it gated has happened |
| 100 | **`clients.csv` carries `UNKNOWN,Unknown Client,,FIRM001,UNSPECIFIED,UNKNOWN,Default for unmatched receipts` as a data row.** Amendment 115 removes the `UNKNOWN` defaults from `save_receipt()` and the schema. **It does not say what happens to this row**, which is the same default expressed as data, and amendment 111 reserves the `UNKNOWN` id rather than deleting it. **What the row becomes in `clients.json` is undecided** |
| 101 | **The same firm has two live identifiers.** `clients.csv` and `firms.csv` both say `FIRM001`, `config.py:105` sets `DEFAULT_FIRM_ID = "FIRM001"`, and `worker\database\schema.py:78` defaults the `receipts.firm_id` column to `'INTELLITAX'`. **So a receipt written without an explicit firm gets a firm id that matches no row in `firms.csv`.** Amendment 116 removes the schema default; **which of the two strings is the firm is not stated anywhere** |
| 102 | **`firms.csv`'s `email` column holds `bills@intellitax.co.uk`**, last written 2026-07-22 16:32:19 UTC. The decided capture mailbox is `capture@lastingimpact.co.uk`. The column is read by nothing, per item 24, so nothing is broken; **it is a stale value in a file two products are about to be merged around** |
| 103 | **The `Client_NNN` sequence is not contiguous and nothing owns the next number.** The live ids are `Client_005` to `Client_009`; `Client_001` to `Client_004` are absent, and `Client_003`'s lost vendor mapping is item 76. Amendment 111 point one keeps the form "sequential and system generated". **Whatever generates the next id in step 10d has to be told whether it counts rows or takes the maximum and adds one**, and those give different answers here |

### ~~Two~~ One live-state finding

**Was two. Item 104, the `pipeline.lock`, closed 2026-08-21 and moved to the Closed section**, so the heading was corrected in the same edit rather than left to state a count the table below it no longer supports.

| # | Item |
|---|---|
| 105 | **Change log checks still pending are written against clients that no longer exist.** Three name `PKPH`, including the whole five-step `HMRC Summaries` check at item 87, whose premise is "client PKPH, which is the only client with anything in its books". One names client `Test 3`, code `TEST3`, which is in `clients.csv` but **not** in `IntelliBooks-Practice.json` and has no books file, so it cannot be opened in IntelliBooks at all. **These are not outstanding checks. They are checks that can no longer be run**, and item 87 should not be reported as pending without saying so |

### The remaining unread, stated so the gap is on the record rather than in a chat

| # | Item |
|---|---|
| 106 | **49 of the 69 markdown files in `C:\LastingImpact\receipt_capture\` have never been opened**, being 601,444 bytes against the 872,352 read. They are **37 `PROMPT_*.md`**, **10 handovers** (`HANDOVER_consultant_chat.md`, the two `HANDOVER_TO_NEXT_SESSION` files, consultant chats 2 to 7, and `2026-07-29_HANDOVER_intellibooks_desktop.md`), and two others (`PAUL_CHECKS_2026-07-30.md`, now read, and `2026-08-03_NOTE_chart_of_accounts_for_paul.md`, out of scope while IntelliCharts is parked). **The judgement, and it is a judgement rather than a finding:** the handovers are low risk because each carries its predecessor forward and chat 8 was read; the prompts are the higher risk, because a brief can contain an instruction that was never carried out and never reported, and **the two largest unread prompts are both IntelliBooks work**, `PROMPT_intellibooks_desktop_changes.md` at 49,524 bytes and `PROMPT_intellibooks_resolution_backfeed.md` at 18,948. IntelliBooks has no equivalent of the seven Claude Code reports; its record is the change log |
| 108 | **Also unread in `IntelliBooks\App\Docs\`:** `build-brief-template.md`, `HANDOFF-Status.md`, `HANDOVER-Prompt-for-Teams.md`, `Session-Record.md`, `SETUP-v5.md` and `Profile Instructions for Claude.txt`, plus the `Claude CoWork Sessions\` sub-folder, which holds the 2026-07-17 deployed capture app snapshot and July copies of five documents. **`SETUP-v5.md` is cited in item 10 from a search, not from a reading** |
| 109 | **Eleven of the twenty modules under `worker\` have never been read whole**, most of them only searched for a string. `filing.py` at 14,234 bytes, `email\reader.py` at 8,500, `extraction\postprocess.py` at 8,950, `logging_setup.py`, `extraction\base.py`, `factory.py`, `retry_helper.py`, `storage\store.py`. **`app.py`, at 55,258 bytes, has been searched and never read.** The 40 files in `tests\` have not been read either, beyond three specific assertions |

## 10. Found on 2026-08-21 by reading everything item 106 to 110 said was unread

**Paul's instruction: "read whatever is left to be read. I want those 2 lists as complete as possible."**
Read: all 37 `PROMPT_*.md`, all 10 unread handovers, `2026-08-03_NOTE_chart_of_accounts_for_paul.md`,
the seven unread documents in `IntelliBooks\App\Docs\` and the whole `Claude CoWork Sessions\`
sub-folder, `app.py` and every module under `worker\`, all 40 files in `tests\`, `docs\specs\`,
the fifteen utility scripts in the repository root, and `.env`, `.env.example`, `.gitignore`,
`requirements.txt` and `requirements-dev.txt`. **Five parallel sweeps produced the raw findings and
every one carried below was then re-verified by the consultant session against the file itself**,
which is how items 71, 87, 107 and 110 above came to be corrected and how one sweep finding was
withdrawn as wrong.

### Three defects nothing has recorded, all verified by reading the code

| # | Item |
|---|---|
| 111 | **`setup_auth.py` cannot run at all, and `RECEIPT_CAPTURE_GUIDE.md` tells Paul to run it.** Line 22 reads `from worker.email.reader import get_token`. **`get_token` is defined nowhere in the repository**, by a search of every `.py` file, which returns only `setup_auth.py`'s own two lines. `config.SHARED_MAILBOX`, used at `:29` and named at `:43`, **does not exist in `config.py`** either. So the script raises `ImportError` at the first line of real code. Its docstring walks through registering an Azure AD app and granting Microsoft Graph delegated `Mail.Read`; **the live pipeline is IMAP**, and `worker\email\reader.py` does `imap.login(config.IMAP_USERNAME, config.IMAP_PASSWORD)`. This is a whole script left behind by the move off Graph. Whether it is deleted or rewritten is a decision; **that the operator guide still points at it belongs in step 10h** |
| 112 | **`app.py:367` to `:371` invents four values silently, and one of them decides which tax year a receipt is filed under.** Inside `_file_unfiled_ok_receipts()`, the recovery path for receipts marked `ok` but not yet filed: `invoice_date = extraction.get("invoice_date") or datetime.now(timezone.utc).date().isoformat()` at `:367`, and **`tax_year = determine_tax_year(invoice_date)` reads it at `:368`**, so a missing date files the receipt under the tax year of the day the recovery ran. Then `supplier` falls back to `"unknown"` at `:369`, `gross` to `0.0` at `:370` and `currency` to `"GBP"` at `:371`. **All four are written into the filed record and the sidecar as though extracted, and none logs anything.** The tell that this is an oversight rather than a choice is in the same function: it logs a warning for a missing extraction row at `:358` and for a missing source file at `:363`. `worker\validation\rules.py` should make the branch unreachable, because a receipt only reaches `ok` with supplier, date and gross present, **but this function re-reads the extraction row from the database rather than using the one that validated**, so the two can differ |
| 113 | **Amendment 94's defect is live, and it fires precisely because of item 101.** `resolve_client_info()` at `worker\database\repository.py:57` returns `("UNKNOWN", "INTELLITAX", "UNKNOWN")` on both of its failure paths, `:60` and `:69`. `app.py:836` unpacks that, then `app.py:839` reads `config.FIRMS.get(firm_id, {}).get("name", firm_id)`. **`config.FIRMS` is loaded from `firms.csv`, which keys on `FIRM001`, so the lookup misses and the fallback returns the literal string `INTELLITAX`.** `app.py:847` then sends that to the client as the firm name in the no-attachment alert and `:848` stores it in `email_alerts.firm_name`. **So the two firm identifiers of item 101 are not merely untidy: their disagreement is what puts a system string into a customer-facing email.** Amendment 94 recorded the guard as missing on this branch on 2026-08-17 and it is still missing. Not fired since the reset, because `email_alerts` is empty |

### Dead code, each confirmed by a search of the whole repository rather than of one file

| # | Item |
|---|---|
| 114 | **`write_review_file()` has been flagged six times in four documents, instructed once to be deleted, and is still there.** It sits at `worker\filing.py:323` and **nothing in the repository calls it**: a search for the name returns its own `def` line and six mentions in documents. Amendment 49 records it. The design document describes it at line 381 and again at line 1795. `PROMPT_claude_code_phase0_step4.md:58` says "Note while you are here, do not fix", `:113` says "Do not delete `write_review_file()` in this commit. Report it", `PROMPT_claude_code_phase0_step5.md:122` says "Do not change `export_bookkeeping.py`, `write_review_file()`, or `_count_review_items()`'s name", and `2026-07-29_HANDOVER_consultant_chat_3.md:146` says "Confirm and delete rather than leave a second writer whose output cannot be worked." **It is now confirmed dead and the deletion has never been scheduled.** Separately: **the design document cites it at `worker/filing.py:142` in both places and it is at `:323`**, so both line references are stale |
| 115 | **`regenerate_codes()` at `regenerate_vendor_codes.py:68` is not called by anything, including by its own file.** The module's `if __name__ == "__main__":` block re-implements the same logic inline rather than calling it, so the one file that exists to run it does not |
| 116 | **Three dead names in `worker\intake\folder_reader.py`, all left over from a filename-prefix design that amendment 112 replaced.** `INTAKE_PATTERN = "rcpt_"` at `:13`, `STATEMENT_PREFIX = "stmt_"` at `:14`, and `IntakeRecord.internal_path` at `:32` and `:46`. Each appears nowhere else in the repository. `scan_inbox()` tells a statement from a receipt by the sidecar's `type` key, which is the decision amendment 112 recorded |
| 117 | **`claimed_client_code` is the field the `UNKNOWN` fault needs, it is written into every sidecar, and it has never carried a value.** Declared at `worker\filing.py:356`, written at `:378`, and **passed the literal `None` at all four call sites in the repository**: `worker\extraction_pipeline.py:236`, `worker\extraction_pipeline.py:278`, `worker\resolution\service.py:703` and `app.py:420`. It is dead on the reading side too: the design document at line 1267 records that IntelliBooks' sidecar shape "has no `confidence`, no `capture_date`, no `asserted`, no `claimed_client_code`". **The claimed-versus-resolved mismatch is exactly what amendment 115's review rule is about, and the field for it already exists.** Whether step 10d populates it or removes it is a decision, and it should not be answered by whoever happens to write the brief |

### One comment that argues against the code beneath it

| # | Item |
|---|---|
| 118 | **`worker\extraction\postprocess.py`'s module docstring describes behaviour the file does not have.** At `:16` to `:18` it says "The broad `try/except Exception: pass` blocks are kept exactly as they were and are load-bearing". **Neither broad block passes.** `apply_vat_inclusive_swap()` at `:129` to `:134` and `resolve_invoice_date()` at `:202` to `:203` both call `logger.warning(..., exc_info=True)`, and the file's own inline comment two lines below the docstring says "Logged rather than swallowed". A future session reading the docstring would believe failures here are silent, and would be wrong in the safe direction, which is why this is here rather than among the defects |

### What amendment 116's rebuild costs the test suite

| # | Item |
|---|---|
| 119 | **Two tests exist only to test the `ALTER TABLE` guards amendment 116 deletes, so they do not fail, they become meaningless.** `tests\test_discard_reason.py`, `test_the_column_exists_on_an_older_database` at `:60`, hand-builds `resolution_events` without a `reason` column and asserts at `:85` that `init_db()` adds it; the only thing that does is `worker\database\schema.py:231` to `:232`. `tests\test_filed_at_column.py`, `test_existing_rows_are_not_back_filled` at `:116`, drops `filed_at` with raw SQL and asserts at `:146` that `init_db()` re-adds it; the only thing that does is `schema.py:219` to `:220`. **Enumerated across all 40 files: these two are the only tests in the suite that depend on the ALTER path**, every other test that touches `pipeline_version`, `receipt_ref_number`, `receipt_time`, `duplicate_of` or `locked_at` works against a table built fresh in the same run |
| 120 | **Amendment 116 removes the defaults from the schema, and the ones that actually take effect are in `repository.py`.** `save_receipt()` at `worker\database\repository.py:206` to `:209` carries `firm_id="INTELLITAX"`, `client_id="UNKNOWN"`, `client_code="UNKNOWN"` and `source="email"` as Python keyword defaults. **Python supplies the value before SQL is reached, so removing the column defaults alone changes nothing**: the column becomes `NOT NULL` but never receives a NULL to reject. `tests\test_resolution_service.py:268`, `test_a_receipt_with_no_extraction_returns_not_found_saying_so`, is the only call in the whole suite that omits all three, and it breaks only if the Python defaults go too. **Amendment 116 should say which, because "becomes required" has no effect otherwise** |
| 121 | **Two tests cannot fail for the reason they state, and one of them says so about itself.** `tests\test_default_firm_id.py:99`, `test_a_row_without_a_firm_id_column_gets_the_constant`, compares `client["firm_id"]` against `config.DEFAULT_FIRM_ID`, reading the live constant on both sides of the assertion. **The file's own docstring at `:21` to `:31` records that reverting `config.py:120` to the literal `"FIRM001"` left all 281 tests green and that "The constant was decorative"**, which is why `SentinelDefaultFirmIdTest` was written; the toothless test was left in beside it. `tests\test_extractor_name.py:28` to `:31`, `test_name_matches_engine_recorded_on_a_result`, carries a comment about the failure path recording a different engine string from the success path, and a body that asserts only `OpenAIVisionExtractor().name == "openai_vision"`, word for word the test above it at `:25`. The regression it is named for is actually covered by `tests\test_failure_path_engine.py` |

### What was lost when documents were merged, and it is not what item 107 said

| # | Item |
|---|---|
| 122 | **The merge of change log items 1 to 11 compressed each to a one-line "Status: done" and dropped the riders those items carried. Two of the riders are substantive.** Verified by reading both files side by side. `IntelliBooks-Change-Log-Original-Items-1-11.md` item 8 reads "Export offers BOTH discrete-quarter and cumulative year-to-date totals (agreed 16 Jul; HMRC's cumulative quarterly updates make YTD the likely need, **bridging trials to confirm**)" and "Product-specific templates (Absolute Taxfiler, 123 Sheets, TaxCalc) added only if testing shows the generic CSV is awkward for one of them". **The word "bridging" appears in the current `IntelliBooks-Change-Log.md` only in Item 8's own title.** So the trial that decides whether the HMRC CSV is fit for a real bridging product is recorded in a superseded file and nowhere current, and item 87 above shows the export has now been run twice without it |
| 123 | **The same merge dropped an accounting rule and an accounting meaning from item 7, and both are Paul's to rule on rather than a build session's.** `IntelliBooks-Change-Log-Original-Items-1-11.md` item 7 reads "cash-paid receipts from the owner's pocket also post to Personal (notional); **a cash account is only created for clients who RECEIVE cash income (a real float to account for)**" and "Account balance represents net owner funding (capital introduced less drawings), the year-end equity note". **Neither phrase appears anywhere in the current `IntelliBooks-Change-Log.md`.** Whether the first is an operator convention or a rule the app should enforce when an account type is chosen has never been asked |
| 124 | **`SETUP-v5.md` is a seventh materially stale document and step 10h names six.** Its own header says "sections 2 and 4 below predate the item 12 folder restructure" and then **the step text was never corrected**: section 2 still reads "Each gets a books file at `Clients\[name]\IntelliBooks\[CODE]-books.json`". It also still directs the operator to a **Import Filed Receipts Folder** button, which `HANDOFF-Status.md` records as "removed as redundant". A document that flags its own staleness in a header and leaves the wrong instruction below it is worse than a plainly stale one, because the header reads as though it has been dealt with |
| 125 | **`IntelliBooks\App\Docs\HANDOFF-Status.md` is stale in the other direction and shows an item as open that is closed.** It lists "One fresh end-to-end phone test on the current architecture, still outstanding". **That was done on 2026-08-20**, when `rcpt_testst_mt1q8xwh.jpg` ran end to end for the first time on this layout and filed as `Clients\TESTST\Receipts\2026-27\2026-05-08_imo-car-wash-57-high-path-merton_4.50.jpg`. The file should be corrected or retired, and it is a candidate for step 10h |

### Raised once, never carried forward, and each verified absent from every later document

| # | Item |
|---|---|
| 126 | **Two defects in `export_bookkeeping.py` were found, deferred twice, then dropped.** `2026-07-28_HANDOVER_consultant_chat_2.md`: "Two real defects were found in it and left alone: bare `e.*` columns outside the `GROUP BY`, and `MAX()` on text aliased as `latest_*`, **so a receipt whose most recent attempt failed can export as `ok`**." Restated in `2026-07-29_HANDOVER_consultant_chat_3.md` alongside the open question of whether the script should carry the GL code at all. Absent from handovers 4, 5, 6, 7 and 8. **The second defect exports a wrong status, which for a bookkeeping export is the serious kind** |
| 127 | **Two of the three items section 18.10 named as coming up soonest were never taken up.** `2026-07-31_HANDOVER_consultant_chat_4.md`: "Those three are: categories in receipts and transactions, extending `chart_of_accounts_DRAFT.csv`, and whether a filed receipt gets a correction route." Restated in `2026-08-02_HANDOVER_consultant_chat_5.md`. **The third of the three, the chart, then took ten recorded decisions across handovers 6 and 7. Neither of the other two appears in either.** The correction route is the one that matters, because it is what happens after a receipt is already filed |
| 128 | **Two OpenAI credential questions, raised three times and dropped, and they gate step 19.** `HANDOVER_consultant_chat.md`: "Whether an org-level OpenAI Admin key on this workstation is acceptable. If not, design doc 9.3 is skipped and the local token ledger stands alone", and "Whether to issue a dedicated OpenAI API key or project for this app, needed for clean cost attribution." Repeated in handovers 2 and 3 with "Both bear on step 19", then absent from 4 onwards |
| 130 | **A staff-facing "N items need review" alert was raised once and never again.** `2026-07-24_HANDOVER_TO_NEXT_SESSION.md`: "Raised as a possible cheap stopgap before the full dashboard exists (currently there is no staff-facing notification at all)... Not decided or scoped." It may be superseded in spirit by the console's intake panel in section 8.6; nothing says so |
| 131 | **Step 10b's reconciliation check is decided in principle, specified nowhere, and scheduled nowhere.** ~~the restatement has not been traced~~ **Traced 2026-08-21. Amendment 73 restated it:** the question becomes whether the client folder matches IntelliBooks' delivery log at `IntelliBooks\Delivery\{CODE}.log`, and section 13A left the pipeline's build order with it. **So what is open is the specification, not the scope.** And a second thing amendment 73 says outright, which is separate: "Intellibills may still want a smaller check of its own archive against its own database; **that is not specified and is not this step**" |
| 132 | **The three unescaped-client-name toasts are three instances and item 84 does not say where.** `PROMPT_intellibooks_desktop_2026-08-03_hmrc_summaries.md`: "That is your own flag 10 and it is a wider pattern than flag 10 says: **`handoverPack()` does the same at lines 1431 and 1475.** Three instances, one class... Whether it is fixed, and whether the answer is a helper rather than three edits, is a decision and not this task." The decision is item 84; the two line numbers were not carried and are recorded here so the fix does not have to rediscover them |

### Hardcoded firm values outside the pipeline's own modules

| # | Item |
|---|---|
| 133 | **`.env.example` ships live production values where a new deployment expects placeholders.** Line 2 reads `IMAP_HOST=mail.lastingimpact.co.uk` and line 4 `IMAP_USERNAME=capture@lastingimpact.co.uk`. It is the file every fresh working copy copies, **including the demo clone of `2026-08-20_NOTE_demo_version.md`**, so it is the one place a firm value propagates by design rather than by accident |
| 134 | **Three more firm and personal literals, none in the pipeline's live path.** `setup_auth.py:13`, the docstring step "Your M365 account must have Full Access to **bills@intellitax.co.uk**", which is also the stale mailbox of item 102. `import_vendor_csv.py:72`, a usage string containing the full path `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\...`. And `seed_client_vendors.py:135`, `if detail.endswith(" Paul Keating:")`, **a hardcoded personal name used to parse a bank export**, which is a firm value in everything but name |
| 135 | **`app.py:839`'s firm-name fallback is the mechanism of item 113 and is worth naming as a pattern in its own right.** `config.FIRMS.get(firm_id, {}).get("name", firm_id)` means an unregistered firm is displayed to a client under its own id rather than failing or logging. In the cloud multi-firm version that is the state every firm passes through during onboarding |

### One thing the `Clients\` listing raises that no document covers

| # | Item |
|---|---|
| 138 | **`Clients\` mixes client codes and client names as folder names, and both conventions are in live use.** Listed 2026-08-21: `PKPH`, `TEST` and `TESTST` are codes; `Paul Keating`, `She Run's It! Ldn Ltd` and `Test Company` are names. Section 18.2b freezes the filing path, and `worker\filing.py` resolves a name through `_resolve_client_name()`, so **the code-named folders are either older than the freeze or were made by something else**. It matters because `Clients\TEST\` and a future client whose name is Test would collide, and because `She Run's It! Ldn Ltd` contains an apostrophe and a space in a path two products build by string join |


---

## Confidence

**High on every item, because each was read from the file, amendment or database that records
it on 2026-08-20**, and each names that source. Item 15 was read back at lines 2406 to 2418
rather than taken from the note that flagged it.

~~**Three things carried as claims rather than facts.**~~ **Two, corrected 2026-08-21.** The
count of files in the repository root, item 32, where both handovers disagree and neither
figure has been verified. ~~The cause of the stale lock, item 26, which nothing records.~~
**Closed 2026-08-21: Paul runs the pipeline on demand and closes it immediately, so the lock
is left behind every time. Items 26 and 104 both rested on the assumption that a lock outliving
a run meant a failure.** And items 28 and 29 rest on the 2026-07-17 capture app snapshot,
which Paul has confirmed is the deployed app.

**How twenty items came to be missing, since it bears on how much to trust this file.** The
first version was built from the two lists at the end of the change log, section 7 of the
handover, and the day's findings. **It was not built from this repository's own design
document open items, nor from the flagged lists inside change log items 36 to 39.** Those held
twenty items between them, of which four turned out to be decisions rather than open questions
and are now section 16 step 10g. **A list built from named sources is only as complete as the
naming.**

**On section 8's reliability, and it is the day's recurring lesson in a new place.** Those
items come from documents, and a document records what was true when it was written. The reset
plan's own status table still reads "not started" for stages 5 and 6, which were completed
after it was written. **So everything carried from a document dated before 2026-08-20 was
checked against the current state, and three findings were closed that way rather than
carried.** Items 76 to 80 are the ones that could not be checked from here and are marked as
unchecked by that wording.

**Nothing here is scheduled.** Anything that becomes a decision leaves this file for section
16 of `2026-07-25_CONSOLE_DESIGN.md`.

---

## Closed

**Numbers are never reused.** A closed item keeps its number and moves here. What was decided about it lives in `2026-07-25_CONSOLE_DESIGN.md`, not in this file.

| # | Item |
|---|---|
| 26 | **Closed 2026-08-21 on Paul's evidence, and it was never an incident.** ~~A stale `Intellibills\pipeline.lock` was removed at startup on 2026-08-20 17:21Z. A run had ended without releasing it and nothing records why~~ **Paul runs the pipeline on demand and closes it immediately, so a lock is left behind every time and cleared by `acquire_lock()` at the next start.** That is his working pattern, not a fault, and it is what "nothing records why" was reaching for. Recorded here because two sessions treated the same behaviour as a defect |
| 53 | **The OpenAI API key beginning `sk-2adW`.** Revoked, confirmed by Paul 2026-08-21. **The `.env` query was included in error:** line 10 was already deleted on 2026-07-31 |
| 104 | **Closed 2026-08-21 with item 26, and the same answer covers both.** The lock was still on disk today: `Intellibills\pipeline.lock`, 56 bytes, contents `pid=41528` and `started_at=2026-08-20T16:21:48.877200+00:00`, read whole, with `Intellibills\pipeline-status.json` unmoved since `2026-08-20T16:36:57Z`. **So neither of the two explanations the item offered was right.** It was not a run holding the lock for twenty hours and it was not a pattern of failures: Paul starts the pipeline on demand and closes it immediately, so the lock outlives every session by design of how he works. **The item's own framing is the thing to learn from.** It said "two in two days is a pattern rather than an incident" and was one step short: it is a pattern, and the pattern is the operator, which no amount of reading the code would have shown |
| 107 | ~~**`IntelliBooks-Change-Log-Original-Items-1-11.md` holds change log items 1 to 11 and has not been read.** The change log proper begins at item 12. **Any item among the first eleven that was left open is on no list**~~ **Wrong, and it was my error. Withdrawn 2026-08-21.** `IntelliBooks-Change-Log.md` begins at `## Item 1`, not at item 12, and its items 1 to 11 match the original file's one for one by title, as do items 12 to 15. **The merge that file's own header asks for was done.** I asserted the item from that file's stale header rather than from the current change log's headings, which is reasoning from a summary about the very file that would have settled it, and one search for `^## Item` settled it. **The real finding is item 124 below: the merge kept the items and dropped their riders** |
| 110 | ~~**`docs\specs\` holds `categorisation_engine.py`, 25,621 bytes, dated early May 2026, sitting inside a documentation folder.** Whether it is a superseded spec artefact or code that could be imported by mistake has not been established~~ **Established 2026-08-21 and closed: it is a superseded artefact and it is safe.** Nothing in the tree imports it, by a search for `docs.specs.categorisation_engine`, `from categorisation_engine` and `import categorisation_engine` across every `.py` and `.md`. Neither `docs\` nor `docs\specs\` holds an `__init__.py`, so it is not importable from where it sits, and the only `sys.path.insert` in the tree is `setup_auth.py:18` inserting `"."`. **And it could not be substituted by accident:** its `CategorisationEngine.categorise()` takes a bank-feed-shaped `Transaction` and its constructor takes `data_dir`, where the live one at `worker\categorisation\engine.py` takes `receipt_id`, `extraction_id`, `supplier_name`, `client_id`, `business_type` and a `repo`, so a wrong import raises `TypeError` on the first call rather than producing plausible output. **Its GL codes are four-digit, not three**, which a careless pass would misread. Item 54 still stands: it is where the only outside references to `learn_from_correction()` live |
| 129 | ~~**`docs\console-design` was twice called a safety net that "must not be deleted", and it is gone.**~~ **Withdrawn 2026-08-21, and it was my error. `docs/console-design` is a git branch, not a folder, and it exists.** Read off the device: `.git\refs\heads` holds `main`, `docs/console-design`, `feat/console-phase0`, `fix/date-disambiguation-vat-swap` and `fix/imap-message-id-dedup`, with `HEAD` on `feat/console-phase0` and no tags. **I searched for a folder under `docs\`, found only `specs\`, and reported an absence** |
| 136 | **Closed. The `Clients\` fossils were deleted.** `HANDOVER-Prompt-for-Teams.md` instructed "delete the two now-empty `Receipt Inbox\{CODE}\Review` folders and the legacy books.json fossils at `Clients\Test\IntelliBooks\` and `Clients\Test 2\IntelliBooks\`". Listing `Clients\` recursively on 2026-08-21 returns six client folders and **no `IntelliBooks` sub-folder under any of them** |
| 137 | **Closed, and it explains part of item 103.** The 2026-07-17 snapshot of `HANDOFF-Status.md` asks "Paul to add Test client row to clients.csv (`Client_004,Test,,FIRM001,UNSPECIFIED,TEST,`)". `clients.csv` today has no `Client_004` and no `TEST` code. Amendment 49 records that `Client_004` had been given to both `Test` and `She Run's It! Ldn Ltd`, and that `SHERUNSIT` was renumbered to `Client_005` on 2026-07-28. **So `Client_004` was `TEST`, was a duplicate, and was removed**, which accounts for one of the four gaps in the `Client_NNN` sequence. `Client_001` to `Client_003` are still unaccounted for, and `Client_003` is the lost vendor mapping of item 76 |
| 139 | **Closed 2026-08-21. Paul ruled: the copy into `Clients\` is Intellibills' function and `get_client_directory()` stays.** Recorded as amendment 122 of `2026-07-25_CONSOLE_DESIGN.md`, which strikes 18.2b's opening sentence and amendment 73's, unblocks sub-step 10d.14, and schedules the removal of the on-arrival write at step 10f. **What this item got wrong is worth keeping.** It reported that amendment 113 governed "on the record's own logic" but that "nothing says so". Two things did, and neither was cited: **amendment 106 of 2026-08-18**, which already amends 18.9 to read "the copy is Intellibills' own function, with two triggers set per firm", and **section 6 of `2026-08-18_BOUNDARY_two_products.md`**, which works the case through and whose section 5 says that document is above the design document. So this was never a live contradiction needing a ruling; it was a stale sentence in 18.2b that no amendment had struck. **A contradiction between two documents is not established until the set of documents that speak to it has been enumerated, and the higher authority was left out of the set** |

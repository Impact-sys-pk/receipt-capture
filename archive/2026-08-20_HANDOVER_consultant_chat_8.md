# Handover: consultant session, 2026-08-20

Paste this whole file into a new Cowork chat in this project. It runs under `paul.keating@intellitax.co.uk`.

**Supersedes `2026-08-18_HANDOVER_consultant_chat_7.md`.** That file stays as the record. Its sections 8 and 9 are still worth reading, and its section 6 is complete: all seven of those checks passed on 18 August.

**One warning before anything else, because the last session got it wrong and it is cheap to repeat. Do not take today's date from your session header.** That session ran across three calendar days, its header never moved, and every date it wrote after 18 August was wrong, including six amendments now committed to the design document. **Read the date off a file you have just touched.** Amendment 109 records the whole thing.

---

## 0. Start here, and in this order

1. **Mount the seven folders in section 1.** You can check nothing until you do.
2. **Read the documents in section 2.** `2026-08-18_BOUNDARY_two_products.md` is new and it is the parent of the design document on one question. Read it first.
3. **Then confirm your understanding back to Paul before doing anything else.** In your own words: what the four components are, which one you are, what state each is in, **what the product boundary is**, and what the immediate job is. Then list every question where you do not understand, including anything here that reads as jargon rather than English. **Do not guess and do not fill a gap with a plausible answer.**
4. **Then the immediate job, section 6: the settings list.** Nothing else starts before it.

Do not begin new work, write a brief, or edit a file until Paul has answered your questions.

---

## 1. Environment

Seven folders. **Do not try to mount the practice root itself**, `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`; it holds a protected Windows location and the request fails with an error that does not explain itself. Mount the subfolders.

| Mount | What is in it |
|---|---|
| `C:\LastingImpact\receipt_capture` | The Python pipeline, the design document and the boundary document |
| `C:\LastingImpact\uber-phase1-ingestion-worker` | The Uber statement parser. A separate repository with its own `CLAUDE.md` |
| `...\IntelliCharts` | The chart of accounts, the seed, and the Desktop briefs written on 17 August |
| `...\IntelliBooks` | `IntelliBooks-Desktop-v3.html`, the books files, the change log |
| `...\Intellibills` | The pipeline's folders in OneDrive |
| `...\Clients` | Intellitax's client filing structure |
| `C:\Intellibills` | The live database and the logs. Outside OneDrive deliberately |

**You almost certainly have no shell on Paul's machine.** The last session had none: `git -C "C:\LastingImpact\receipt_capture" status` returns `fatal: cannot change to ... No such file or directory`, because the shell runs on a Linux VM in Anthropic's cloud. Sessions in August have had one and have not; this is not constant. Check by trying, and say so rather than working around it.

**With no shell, git state is still readable.** Stage `.git\HEAD`, `.git\refs\`, `.git\index` and the loose objects. The repository has no pack files, so every object is loose. Parse the index for the tracked set, inflate a blob to diff it, and **check each object's SHA-1 against its own filename before trusting it.**

**Two limits on that method, and the second is the one to fix.** It reads the tracked side exactly. **It is structurally blind to untracked files**, so list the folder immediately before predicting them, never from a listing taken earlier. And a blanket size comparison against the index is invalid, because `.gitattributes` is `* text=auto eol=lf` and every `.py` file is stored LF and held CRLF on disk, so about thirty files differ in size by design. **The implementation session's better method, which the last consultant session accepted and did not get round to using: compare each working file against its blob after normalising CRLF to LF, and report only what still differs, with a byte comparison for binary paths.** That takes you from five files to all 169 without a shell.

**Claude in Chrome is disabled by the organisation.** If a page needs JavaScript to render you cannot read it. Say so.

**Never import `config.py`:** it creates folders at import, and the Windows paths in it become folder names on Linux.

---

## 2. Read these, in this order

| Read | For |
|---|---|
| **`receipt_capture\2026-08-18_BOUNDARY_two_products.md`** | **New, and above the design document on which product a thing belongs to.** Short. Twelve sections. Read it before the design document, because six of the design document's newest amendments derive from it |
| `receipt_capture\CLAUDE.md`, the section headed "How this project is worked" | The working method and the standard of evidence. Read the evidence rules in full |
| `receipt_capture\2026-07-25_CONSOLE_DESIGN.md`, **amendments 101 to 109 first**, then section 18, then the rest of the record | 109 amendments. 101 to 108 are the receipt handoff, client identity, the boundary and settings. **109 is the date correction and it is worth reading for its lesson, not its content** |
| `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md`, all of it | The chart of accounts design. **Addendum first, then the body.** Skipping the body cost a session an hour |
| `IntelliBooks\App\Docs\2026-08-20_REPORT_desktop_menu_groups.md` | What the Desktop session built on 20 August, and Paul's four-part check, which he may not yet have run |
| `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`, items 36 to 39 | The four IntelliBooks changes since 17 August |
| This project's own document list | **It is reading, not a filing cabinet.** `2026-08-15_RUNLOG_coa_august_check.md` exists nowhere else and two sessions running failed to open it |
| `uber-phase1-ingestion-worker\CLAUDE.md` and `HANDOVER.md` | **Only when you reach that work. Not before** |

---

## 3. Your role, and how Paul wants you to work

You verify, you own the design document and the boundary document, and you write the briefs the other sessions work from. **You do not write production code.**

Run any check you are capable of running rather than asking Paul to run it. Make file changes after asking and getting a yes. Paul does what only he can: anything on screen in IntelliBooks, starting the pipeline, sending a receipt, the mailbox, and anything on Netlify.

**Four things you cannot do.** Run the Python test suite. Start the pipeline. Drive IntelliBooks. Delete a file.

### Instructions Paul gave repeatedly on 18 and 20 August. Hold to all of them

- **Answer the question he asked, not the one you find interesting.** He said "you are racing ahead" three times, and each time he had asked about a **boundary** and been given a **mechanism**.
- **When he asks a question, answer it. Do not answer a nearby question and present it as the answer.** He asked whose function Add Receipts was and got an answer about the shape of its write.
- **Simplify, do not complicate.** Standing instruction.
- **Explain the problem before proposing a solution, and consult him on the solution.**
- **Do not offer multiple choice until it is clear you understand his reasoning.**
- **KISS when he asks for it.** He asks in those words.
- **Use the real file name every time.** Repetition is not a problem; inventing a synonym is.
- **No section or amendment numbers in conversation.** They are how you find things in the document. Write the thing itself in plain English.
- **Do not treat one "ok" as standing approval for what comes next.**
- **Address him, not the other session.** The last session wrote three replies aimed at Claude Code and he had to say so each time.
- **Quote the command and its output in the same message as any claim that matters.**

---

## 4. The four components and what state each is in

**Intellibills, the Python pipeline** at `C:\LastingImpact\receipt_capture`. Working. Reads a mailbox and a folder, extracts with OpenAI, validates, categorises, stores in SQLite at `C:\Intellibills\db\receipts.db`. **Code untouched since 2 August.** Everything decided on 18 and 20 August about it is recorded and unbuilt.

**IntelliBooks Desktop**, one HTML file at `IntelliBooks\App\IntelliBooks-Desktop-v3.html`. **165,586 bytes, 2,709 lines, as at 2026-08-20 10:28Z.** No database; each client's books are a JSON file. Four changes since 17 August, change log items 36 to 39.

**IntelliCharts** at `IntelliCharts\`. The chart of accounts. `COA_MASTER_v1.csv`, 122 accounts, hand-edited, with `build_coa.py` generating six files and refusing to write if any check fails. **No session owns it**, and that is an open question in section 7.

**The Uber statement parser** at `C:\LastingImpact\uber-phase1-ingestion-worker`. Separate repository, own `CLAUDE.md`, own Claude project. Local version complete, deterministic, CSV out. Cloud version has parity, is not production ready, untested since May. **Not opened by the last session at all.**

---

## 5. State, verified 2026-08-20

Every figure read from the file, the database or the git objects on 2026-08-20 between 10:30 and 11:00Z.

**Repository.** Branch `feat/console-phase0`, tip **`4981f4875b668149623a598c700ddad82cb178ce`**, pushed, `origin` the same. Index holds **169 entries**. Working tree was clean at `4981f48` and **is now dirty with one file**: `2026-07-25_CONSOLE_DESIGN.md`, carrying amendment 109. **Committing that is your first file-level action.**

**Design document.** **v1.12, 109 amendments**, contiguous. Check contiguity by bounding to the record's own line boundaries, printing them with the result, asserting the list equals `range(first, last+1)`, and testing duplicates explicitly. **Never a set difference**: section 13A has its own table numbered 1 to 8. **Today's boundaries: heading line 16, section ends line 189, and the numbered rows themselves run line 24 to 188.** They have moved four times in three days, once per version-header edit, so any brief quoting older numbers is stale.

**Boundary document.** `2026-08-18_BOUNDARY_two_products.md`, 12,158 bytes, committed. **Its filename carries the wrong date** and is deliberately not renamed; amendment 109 says why.

**IntelliBooks.** 165,586 bytes. Six `data-tab` values and six matching `tabpage` ids, no orphan either way. **The internal tab id is still `settings` while the label is Client Data**, so searching for `tab-clientdata` finds nothing. On screen the word Settings survives only as Firm Settings, Practice Settings and two toasts pointing at that card. One `<script>` block, 142,358 characters, `node --check` passes; the consultant session ran that itself rather than taking the report's word.

**The books.** **Seven files in `IntelliBooks\Books\` for six clients.** `PSHIPN-books.json` is an orphan and is correct behaviour: `removeClient()` deliberately leaves the file and says so in its confirmation box. All test data, and Paul has decided to keep it.

**`IntelliBooks-Practice.json`** holds six clients: TEST, Test 2, Test Company, Test Sole Trader, Test Partnership, Zero Partners. **`Intellibills\clients.csv`** holds six different ones: UNKNOWN, PKPH, Intellitax, Test 3, Test 4, She Run's It! Ldn Ltd. **Not one code appears in both**, and nothing checks. Do not "fix" it by writing either file; the fix is one registry and it is decided but unbuilt.

**The database.** `receipts.db`, 233,472 bytes, last written 2026-08-19 16:48Z. Eleven tables. `receipts` 2, `extractions` 2, `categorisations` 2, `processed_attachments` 1, everything else 0. **`categorisations_client_vendors` is 0**: the 100 legacy three-digit rows were exported and dropped on 18 August, and the export is at `Intellibills\Exports\`. Backups at `Intellibills\Backups\receipts-pre-legacy-vendor-drop-20260818.db`, verified to hold the 100 rows, and a second copy beside the live database.

**One live receipt worth knowing about.** `7bc79f76-a2c1-43c5-b084-0ea4d29f2218`, captured 2026-08-19 16:48Z, **`client_code = TESTST` and `client_id = UNKNOWN`.** Paul sent it deliberately as a test. It is the first live instance of the fault in section 8: `scan_inbox()` takes the client from the folder name, looks it up in `clients.csv`, finds nothing because `TESTST` exists only in `IntelliBooks-Practice.json`, and files the receipt with `client_id = UNKNOWN` and no error.

---

## 6. The immediate job: the settings list

Agreed on 20 August and deliberately left until after the write-up. **It is a list, not an audit**, and saying so is part of the job: after everything excluded below, it is roughly thirty items.

**For every setting: which level (firm or client), which product (Intellibills or IntelliBooks), whether it exists today or is proposed, where it is stored (file and field name), where it is entered today, and where it should appear.**

**Where it is entered, as against where it is stored, is the column nobody has looked at.** Several settings are only reachable by editing a file by hand, which is a finding in itself for something Paul intends to sell.

**Sources:** `config.py`, `.env` variable names, `IntelliBooks-Practice.json`, `clients.csv`, `firms.csv`, the Client Data tab and the client Edit window in `IntelliBooks-Desktop-v3.html`, the Netlify environment variables Paul can see and you cannot, and the books files.

**Excluded, and this is what makes it small.** Client working data: bank accounts, categories, learned statement rules. Engineering constants nobody should change: the extraction engine, the AI model, the validation tolerance, the poll interval, internal folder and file naming, the pipeline version. Secrets that belong in environment configuration.

**What it unblocks:** where Client Settings live in the menu, which Paul deferred until the list exists, and what goes on the Firm Settings page, which is deliberately empty until then.

---

## 7. Open decisions and open checks

**Paul's to decide**

1. **Who owns changes to `build_coa.py`.** IntelliCharts has no session and every change to it so far has been made by an ad-hoc session on Paul's machine.
2. **Where Client Settings live in the menu.** Waits on section 6.
3. **The 61 files in the repository root.** He said after. Candidates and reasoning are in handover 7 section 7. **`PROMPT_claude_code_step10a_and_10b.md` must never be sent**: it was written against a folder scheme abandoned in July, and its only possible use is harmful.
4. **Whether `2026-08-18_BOUNDARY_two_products.md` stays in Intellibills' repository.** Its own text says the placement is provisional and why it is uncomfortable.

**Paul must look, and you cannot**

5. **The capture app's `RECEIPTS_ROOT` on Netlify.** It defaults to `IntelliBooks/Receipt Inbox`, which is the old location; the pipeline reads `Intellibills\Receipt Inbox\`. Either it was reset or the two are out of step.
6. **The upload key.** One shared secret in a URL for every client, not revocable per client. `capture_token` replaces it and is unbuilt.
7. **Paul's four-part check** in `2026-08-20_REPORT_desktop_menu_groups.md`. Part D needs him to fake a review item by hand, because the pipeline has never produced a possible duplicate. Ask whether he has run it.

**Recorded and deliberately not solved**

8. `Receipt Inbox\{CODE}\` deriving the client from a folder name, and an unmatched folder becoming `UNKNOWN` silently. **Now has a live instance, see section 5.**
9. Multi-firm path collision: two firms coding a client the same way. Needs a firm level in the path.
10. The console has no implemented reader for the master chart. Amendment 101.
11. `Practice Settings` and `Firm Settings` are now two names for practice-level settings in adjacent menu items. Flagged by the Desktop session on 20 August.
12. The books-receipt pill prints the raw status string, so a filed receipt would read `possible_duplicate` with an underscore where a review item reads `Possible duplicate`. Flagged by the Desktop session; whether the pipeline ever files one with that status is unestablished.

---

## 8. What only the last session knows

**The scheduled tasks are on the other account.** `paul.keating@intellitax.co.uk` owns **none**. All three live under `pdk7@hotmail.co.uk`: the April HMRC check, the February and August Sage drift backstop, both cloud, and a local Sage task Paul was creating on 18 August. **A practice maintenance task that fires once a year lives on a personal account**, and if that account lapses the reminder goes with it. Prompts for the first two were corrected on 18 August; the tool that lists tasks does not return the prompt text and the tool that updates it replaces the prompt wholesale, so you must have Paul paste the current one before correcting a word of it.

**IntelliBooks never reads `clients.csv`.** Zero occurrences in the whole file, counted. Its client code is typed by hand into the New Client dialog, prefilled from the first six characters of the first word of the name, uppercased, stripped to A-Z and 0-9, eight characters maximum. **So the two registries share nothing because the two codes are typed independently in two places.**

**The capture app writes into OneDrive through Microsoft Graph.** The phone app POSTs to its own Netlify function, which authenticates with an Azure app registration and writes the file straight into Paul's OneDrive under `RECEIPTS_ROOT`. No email hop, no separate sync. **What was read is the 17 July snapshot** in `IntelliBooks\App\Docs\Claude CoWork Sessions\outputs as of 2026-07-17\`; the live deployment may have moved on.

**The console does not exist and nothing renders it.** `Flask` appears zero times in `requirements.txt` and `requirements-dev.txt`; `worker\` has no templates, static or web layer; `app.py` has zero occurrences of `Flask` or `render_template`. So `list_gl_code_options_from_vendors()` is real and `ResolutionView.gl_code_options` is a field nothing displays.

**`IntelliBooks.bat` starts the pipeline as well as the app**, and calls itself the backup route. **The logon scheduled task it names does not exist**; Paul runs the pipeline manually and intends to for now. Its guard against a second pipeline is a window-title match, but `acquire_lock()` writes `Intellibills\pipeline.lock` with its own process id and a second instance will not start, so a duplicate launch is caught by the pipeline rather than by the launcher.

**Where a captured file goes after pickup:** `Intellibills\Receipt Inbox\{CODE}\Processed\`, created on demand. A move rather than a delete, on every outcome, because anything left in the inbox is re-read and re-sent to OpenAI every five minutes for ever.

**Three parts of the VAT section are specification, not code.** The one-penny tolerance is not in; `worker/validation/rules.py` still reads `_VAT_TOLERANCE = 0.02`. The VAT % and Net columns with a mismatched amount in a different colour are not built. The split transaction is not built. **What exists is `postWarnings()`, which fires at one moment only: posting a receipt to the cashbook.** There is no general alert-and-proceed mechanism, which is why duplicates route to Review and stop.

**"The system alerts, it never prevents" is a rule about VAT and about nothing else.** The last session quoted it as a general principle and was wrong.

**Three of the master's twenty columns are read by nothing.** `frs102_1a_line` and `frs105_line` are filled on all 122 accounts and not even validated. `mtd_itsa_category` is validated and read by nothing. Not a reason to remove them, a reason not to build on them.

**Sage company code `1141` cannot trigger drift**, because it is not one of the 237 rows in `coa_map_sage_final_accounts.csv`. Its two non-breaking spaces are real and are the only non-ASCII characters in either Sage export. So if drift is ever reported on `1141`, something upstream has changed and that is itself the finding.

**Paul's priorities, in his order.** His own single-user system running as soon as possible; multi-user soon after; the Uber parser offered to other firms; a demo for a third party, securely and with the code protected; multi-firm.

---

## 9. What the last session got wrong

Read this. Paul caught most of them, and the pattern is more useful than the list.

**It was wrong about the date for two days and put it in six committed amendments.** It took the date from its own session header and never once checked it against a file timestamp. Amendment 109 records it.

**It proposed shapes that leaked one system's internals into the other, twice.** Per-client inbox folders, which would have made the sender know how the receiver organises itself. And `pipelineKey` as a field on IntelliBooks' client record, which names a field after one particular capture tool inside the product that is supposed not to care. Paul caught both.

**It said the boundary was the publish step**, which quietly equated "after publish" with "bookkeeping" and hid a real breach for an hour. Paul found it by asking what happens in the standalone version.

**It answered questions adjacent to the ones asked.** Asked whose function Add Receipts is, it answered about the shape of the write. Asked about `client_code`, it answered about a different field with the same name and told Paul he was wrong when he was right.

**It proposed four field names and described each of them in a different way**, with two of the four said to be "for folder names". Paul had to ask for the same four again, properly.

**It put an item on a list without checking whether the case existed.** "Anywhere a person has to type it" turned out to happen nowhere.

**It reasoned from output it had truncated itself**, reading a function as having a syntax error because the word `async` was three characters to the left of where it started printing. Caught before reporting, but only just.

**It claimed a function existed only in the design document** having read `app.py` alone. The implementation session found it in `worker/database/repository.py`. The limitation was flagged and the conclusion was still stated too strongly.

**It reached for a VAT rule to settle a duplicate policy.** Different question, different rule.

**It reported a phrase missing from a commit message** using a search string that spanned a line break.

**It wrote three replies addressed to Claude Code rather than to Paul.**

**The pattern, and four handovers have now recorded a version of it: careful inside the frame, careless about whether the frame is right.** This session's specific version was reaching for the arrangement convenient inside one system rather than asking what the other has to know to use it. **Two habits fix most of it.** Before writing "there are N of these", run the command that lists them and print it whole. And before answering, check whether you are answering the question that was asked.

---

## 10. Reference

**Repository** `C:\LastingImpact\receipt_capture`, branch `feat/console-phase0`, tip `4981f487`, remote `https://github.com/Impact-sys-pk/receipt-capture.git`. No pack files; every git object is loose.

**Authoritative documents, in order.** `2026-08-18_BOUNDARY_two_products.md` for which product a thing belongs to. `2026-07-25_CONSOLE_DESIGN.md` for how it is built. `CLAUDE.md` for the working method. `PROMPT_*.md` in the repository root are the briefs each session works from.

**Chart of accounts** `IntelliCharts\COA_MASTER_v1.csv`. Hand-edited. `build_coa.py` writes six files and refuses to write anything if a check fails.

**IntelliBooks Desktop** `IntelliBooks\App\IntelliBooks-Desktop-v3.html`. **Search it, do not read it in full.** Change log at `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`, 39 items.

**Uber parser** `C:\LastingImpact\uber-phase1-ingestion-worker`, branch `main`, last commit May 2026. 1,662 Python files: do not read it in full.

**Names, and hold to them.** **Intellibills** is the Python pipeline, or "the pipeline". **Receipt Capture** is the name of that repository and of nothing else. **IntelliBooks Desktop** is the browser app. **IntelliCharts** is the chart of accounts folder today and a product later. **The master** is `COA_MASTER_v1.csv`. **The console** is a Flask app that does not exist. **The books** are the JSON files in `IntelliBooks\Books\`. **The database** is `receipts.db`. **Never say "the app".**

**Two pairs one word apart, both live.** **Post** means both signing off a transaction that already exists and creating one from a receipt. **Attach** is receipt to transaction; **Link** is transaction to transaction. Disambiguate both in anything Paul has to follow on screen.

**Four field names, decided 20 August and unbuilt.** `client_id`, system generated and unchangeable, for records, messages, the books filename and the modules' own folders. `client_name`, display only, never a path. `client_folder_name`, the one folder in the firm's filing structure. `capture_token`, a revocable credential whose only job is the capture link. **There is no `client_code`.**

**Traps.** Prose in `CLAUDE.md` cannot suppress a Claude Code permission prompt; the allow rules live in `.claude/settings.local.json`. Never report a dirty git working tree from the Linux sandbox, which shows about thirty phantom modifications from line-ending normalisation. Do not add a duplicate `client_id` check to `clients.csv`: one client may legitimately have two rows differing only in the email column, so the test is whether the other columns match. And **a Cowork session may or may not have a shell on Paul's machine; this is not constant.**

**Confidence.** High on sections 1, 4, 5 and 10: every figure read from the file, the database or the git objects on 2026-08-20, with the amendment enumeration printed whole and compared against a range rather than eyeballed. High on 6, 7 and 8. High on 9, which is a list of things this session did. **The one thing not verified is the Uber parser**, which was deliberately not opened.

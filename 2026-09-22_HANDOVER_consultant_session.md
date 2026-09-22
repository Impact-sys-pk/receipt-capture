Handover for a new consultant (Cowork) session, Receipts capture App project. Written 2026-09-22 at 14:14 BST, read off the clock. **It replaces every earlier handover, including `2026-09-20_HANDOVER_consultant_session.md`.**

## Who you are

You are the consultant session. You own verification, the design document, the build status and the prompts, and you write `IntelliBooks-Desktop-v3.html` on Paul's standing instruction. A separate implementation session in Claude Code works the Python pipeline. You cannot see it. Paul is the only channel between you.

**`2026-07-25_BUILD_STATUS.md` is written by you and by nobody else.** Claude Code does not mark its own step paragraphs built. Say so in every brief.

## First action, before anything else

Request device folder access to these four in one go. Do not ask piecemeal.

- `C:\LastingImpact\receipt_capture`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts`

**Do not touch `C:\LastingImpact\uber-phase1-ingestion-worker`.** Two sessions running have now requested it by mistake, including this one, and neither opened it.

## Read the project instructions first

They carry the rules. **This handover does not restate them.**

## What the 2026-09-20 handover got wrong, and what this session established

**It said this session has `device_bash`. This one did not.** The tools present were `device_list_dir`, `device_stage_files`, `device_commit_files` and `device_request_folder_access`, and a search for `device_bash` returned nothing. **Establish it, do not assume it**, which is `CLAUDE.md`'s seventh trap.

**With no shell, the whole day's work went: stage to read, `SendUserFile` then `device_commit_files` to write, re-stage and md5 compare every time.** It works and it is not slow. Every write below was read back and compared.

**Git stays with Paul on Windows.** Give him a PowerShell block with its own `cd` line.

## Where the work stands

`2026-07-25_BUILD_STATUS.md` head line, as at 2026-09-22: **74 built, 13 outstanding, 6 cancelled, 1 moved out of this order, 94 steps.** Amendment record at **537**, contiguous 1 to 537, no duplicates.

**The thirteen outstanding: 10bm, 10bn, 10i, 11, 13, 14, 15, 16, 17, 18, 20, 21, 22.** Ten of them are the console, which is not built and not scheduled.

**The three that are not the console:**

| Step | What is left | Holder |
|---|---|---|
| 10i | **The pilot. This is what Paul is doing now.** | Paul |
| 10bm | CSV Exports. Two words and no scope. It has a tab now, the Exports tab, holding the Transactions export, the HMRC Summary Export and Archived periods | Paul, then you |
| 10bn | Bank Reconciliations. The saving of a reconciliation: the PDF question, where the files go, and two screen tests never run | Paul, then you |

**Amendment 537, Paul's decisions of 2026-09-22: 10bm and 10bn do not block the pilot**, his words "10bm and 10bn do not block anything. 10i will help inform us." Step 10i's own rule that nothing above it may be deferred is relaxed for those two and for nothing else.

## The pilot, step 10i, and what Paul has said

- **The client is Paul Keating T/A PKPH.** It is a real client and its books are also kept in FreeAgent, **so the pilot data is still test data and IntelliBooks is not the only copy.** Amendment 537.
- **The pilot gets its own client folder**, not the existing `Clients\Paul Keating\`. His decision, 2026-09-22.
- **It starts from 1 April 2026.**
- **There is no client record for it yet.** `Intellibills\clients.json` held five clients when read on 2026-09-22, all test ones: Vat Sole Trader, Test 2, Test Company, Test Sole Trader, Test Partnership. **Paul is creating the record himself.**
- **NOTHING IS DELETED YET.** The test estate is cleared immediately before the pilot and not sooner, and he wants it kept simple when it happens: count, delete, count again and see zero. You count the books files and the processed inbox copies. **He counts `Clients\` and `receipts.db`**, because neither is reachable from this session and a database staged through the bridge is not evidence, which is `CLAUDE.md`'s sixth trap.
- **His instruction, in his words: "I think it is best if you dont try to spoon feed me. Let me set up the new client. I will ask you for any help I need."** Answer what he asks and stop.

## Section 8 of `IntelliBooks\App\Docs\IntelliBooks-System-Specification.md`, the pilot checklist

Read there on 2026-09-22, not recalled. It is the procedure for step 10i: one real client, two weeks, before any other client receives a link.

1. **The onboarding link works on their actual phone.** Note make and OS. **The link carries that client's own `capture_token` as `t`**, so it must be the link copied from that client's row, and one client's link must never be sent to another.
2. **A receipt sent from the phone arrives in `Intellibills\Receipt Inbox\{their folder}\` within a minute**, as an image plus a sidecar whose extension replaces the image's.
3. **The pipeline processes it to `ok` and files it correctly.** Three things, checked on disk rather than in a report: the file name reads `{date}_{supplier}_{gross}`; it sits under `Clients\{their folder}\IntelliBooks\Receipts\{tax year}\` with the tax year as `2026-27`; the enriched sidecar is beside it with the same name plus `.json`.
4. **The inbox pair has moved to `Processed\`**, not vanished and not still sitting there. **A pair left in the inbox is reprocessed every poll for ever**, at an OpenAI call each time.
5. **Desktop imports it and matches it against a real statement.**
6. **One deliberately bad photograph goes through the Review path**, to `Intellibills\Review\`, and is then resolved. **Resolve it in IntelliBooks Desktop, not by editing the database**, so the back-feed is exercised: the note appears in `Intellibills\Resolutions\` and is moved to `processed\` on the next poll.
7. **The retry queue works in airplane mode**: capture with no signal, then reconnect.
8. **Netlify function logs reviewed at week one and week two.**

**Two things the checklist's own text says to watch.** A receipt stuck as `failed` or `needs_review` for longer than `AUTO_RETRY_MAX_AGE_DAYS` becomes `retry_exhausted`, stops being retried and needs a person. And **layer 5 of the categoriser has never run**: `CategorisationEngine` is constructed with `enable_ai_fallback=False`, so a vendor nobody has taught the system comes back `unmatched`, and that is the expected result rather than a fault.

**Exit criteria: zero lost receipts, filing correct, Paul would happily onboard client two.**

## What was built on 2026-09-22

**Step 10t, the reports set, is built.** Amendment 535. Four reports at the top of the Reports tab, modelled on FreeAgent in function only after Paul drove a tour of it through the browser: Profit and Loss with Yearly, Monthly, Quarterly and Comparative views, Balance Sheet, Trial Balance, Bank Reconciliation with a Summary and a Full report. One shared drill down. CSV and print, each carrying the report's title, the business name and its dates. The tour is written up in `2026-09-22_NOTE_freeagent_reports_tour.md`.

Also that day, all Paul's decisions: the Dashboard's two old boxes dropped; an **Exports** tab created holding the Transactions export, the HMRC Summary Export and Archived periods; a **Taxes** menu in the nav, opening on hover and on click, with **VAT** and **Income Tax** panes, the VAT Summary moved there with dates of its own; `exportReportCSV()` renamed `exportTransactionsCSV()`; a **Chart code** on each bank account, set by hand on the Client Data tab and never guessed from the name; and printing scoped so a report prints alone.

**Amendments 528 to 537** carry all of it with the reasoning.

## File state, read on 2026-09-22 at 14:14 BST

| File | md5 |
|---|---|
| `2026-07-25_BUILD_STATUS.md` | `c55ed14a88b90299cc0dfbd5a1e9c96f` |
| `2026-07-25_CONSOLE_DESIGN.md` | `cc8185f85009d098dc8b6bf927b01b29` |
| `CLAUDE.md` | `3ec39140b2518213c0043efab3a74dd9` |
| `IntelliBooks\App\IntelliBooks-Desktop-v3.html` | `f125be04018a8d4e0ecbab7b196ffd21` |
| `IntelliBooks\App\guards.mjs` | `6ea705c2a7091aa12b0061b0f5c383f9` |
| `IntelliBooks\App\reports.mjs` | `0970b118ec8d7ec47262e7c7f932ec43` |
| `IntelliBooks\App\drive_seam.mjs` | `b94e9672968161ecd32129edd529390b` |

## How the front end is worked

**Three harnesses now, all on disk in `IntelliBooks\App\` and none in the repository.** OneDrive version history is all the versioning they have.

- **`guards.mjs`**, eight guards over `IntelliBooks-Desktop-v3.html`. `node guards.mjs <file>` and `node guards.mjs --self-test`. Guard eight's list gained `rsExportCSV` and `rsSaveBankRec` on 2026-09-22.
- **`reports.mjs`**, new on 2026-09-22, ten checks over the reports set, run against every `Client_00X-books.json`. `node reports.mjs` and `node reports.mjs --self-test`. It slices the reports block out of the HTML between two markers and supplies the helpers it calls; **if one of those helpers changes shape in the app, this harness lies**, and that is written in its own header.
- **`drive_seam.mjs`**, the Desktop half of step 10am, over the Review seam. Its stubs drift.

**Run all three after any edit to `IntelliBooks-Desktop-v3.html`.** Nothing runs them automatically.

**Enumerate with the syntax tree, not with a text search.** `acorn` and `acorn-walk` are in `IntelliBooks\App\node_modules`. This project keeps superseded wording beside every correction, so a grep hits the record of what changed.

**Line endings.** `CLAUDE.md` is CRLF. The two big markdown files and everything in `IntelliBooks\App\` are LF. Use `newline=''` in Python and assert the file has none of the wrong kind before writing.

**The amendment-record contiguity check must be bounded.** `2026-07-25_CONSOLE_DESIGN.md` holds a second numbered table that starts again at 1. Find both starts, take the first block, assert `range(1, n+1)` plus an explicit duplicate test.

**`py check_build_status.py` compares section 16's table against its paragraph heads.** Run it after any change to that section. **It reads the first status word it finds after stripping struck text, so an uppercase BUILT anywhere in an outstanding step's paragraph fails it.** That happened once on 2026-09-22 and the wording was changed rather than the checker.

## What this session got wrong, disclosed

- **It requested the Uber folder the previous handover says to leave alone**, and missed `Intellibills`, so Paul got two permission dialogs instead of one.
- **It told Paul how the Cowork built-in browser works from a support page a summariser had read**, rather than from using it. He corrected it. The rule it broke is the project's own: do not state what a thing does unless you have used it.
- **It attached the kept-as-issued question to the reports.** That question is about filings and belongs to 10bm. Paul corrected it.
- **It wrote three checks that were wrong rather than reports that were wrong**: a CSV check looking for cell labels that exist on only two of the four reports, a row threshold that failed three clients whose books hold no transactions, and two write-checks run concurrently that trod on each other's data.
- **It opened a browser tab and navigated it without being asked.**

## Writing to Paul

Read the report in full first, then verify the claims that matter against the thing itself. Ask him before deriving. Flag with a recommendation, never without one. Disclose your own mistakes. Say what a confidence level is about, not only what it rests on. Name the file, the function or the window in full, every time. No prose: bullets, tables, numbered steps, short. Answer the question asked and stop. Date, time, zone and verbosity at the start of every reply, clock read fresh each time. No em dashes. **He does not like items left open**: put the decision to him, and where he takes one, it becomes a step rather than a note.

The traps live in `CLAUDE.md` and nowhere else. Read them there before starting.

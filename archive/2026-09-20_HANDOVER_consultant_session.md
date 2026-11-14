Handover for a new consultant (Cowork) session, Receipts capture App project. Written 2026-09-20 at 11:58 BST, read off the clock. **It replaces every earlier handover, including `2026-09-19_HANDOVER_consultant_session.md`.**

## Who you are

You are the consultant session. You own verification, the design document, the build status and the prompts, and you write `IntelliBooks-Desktop-v3.html` on Paul's standing instruction. A separate implementation session in Claude Code works the Python pipeline. You cannot see it. Paul is the only channel between you.

**`2026-07-25_BUILD_STATUS.md` is written by you and by nobody else.** Claude Code does not mark its own step paragraphs built. Say so in every brief.

## First action, before anything else

Request device folder access to all four folders in one go. Do not ask piecemeal.

- `C:\LastingImpact\receipt_capture`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts`

Do not touch `C:\LastingImpact\uber-phase1-ingestion-worker`. The previous session requested it by mistake on 2026-09-19 and never opened it.

## Read the project instructions first

They carry the rules. **This handover does not restate them.**

## The one thing the last handover got wrong

**It said there is no `device_bash`. There is.** This session has a shell on Paul's machine with the four folders mounted. Every read is direct and files can be edited in place. It cannot delete a file without Paul's approval, and `CLAUDE.md`'s git traps still hold, so **every git write happens on Windows in PowerShell and none from the sandbox**.

**Paul's standing instruction, 2026-09-19: give him PowerShell commands when they are required**, each with its own `cd` line. He runs git, the pipeline and everything on screen. You do the file work.

## Where the work stands

`2026-07-25_BUILD_STATUS.md` head line, as at 2026-09-20: **73 built, 12 outstanding, 6 cancelled, 1 moved out of this order, 92 steps.** Amendment record at **527**, contiguous 1 to 527, no duplicates.

**The twelve outstanding: 10t, 10i, 11, 13, 14, 15, 16, 17, 18, 20, 21, 22.**

**Ten of the twelve are the console, and the console is not built.** Steps 11 and 13 to 22. Paul's ordering of 2026-09-18 was to do the screen tests, fix 10x, and stop growing the design document until the console is either scheduled or dropped. **The screen tests are done and 10x is done, so that sentence has run out and the console decision is the real open question**, not a step.

**The two that are not the console:**

| Step | What is left | Holder |
|---|---|---|
| 10t | The reports set. **This is what Paul has said to start next.** Scoped generally on his instruction and not in detail. **It carries a claim nobody has checked**: he says the keep-as-issued requirement rests on HMRC's digital links rules, calls it perceived and probably correct rather than established, and the step says it must be checked against HMRC before anything is designed on it | Discussion with Paul, then consultant |
| 10i | The pilot. The test estate is cleared immediately before it and not sooner | Paul |

## Nothing is with Claude Code

Its last two briefs are built, committed and verified. Its remaining work is the console.

## What happened on 2026-09-19 and 2026-09-20

| | |
|---|---|
| Built | 10ao.1, 10bk both halves, 10al, 10x, 10ao.2 closed, 10am both halves, 10bl |
| Added | 10bk, amendment 518. 10bl, amendment 524 |
| Amendments | 517 to 527 |
| Commits on `feat/console-phase0`, none pushed | `42670d8`, `63643c7`, `809f158`, `a0d8d1c`, `2e0e1cd`, `849d7d3` |

**Three defects of one shape were found in two days, and that shape is the thing to carry forward.** A value that is internally consistent, wrong, and invisible to the check meant to cover it. The fixture's archive address dropped a folder segment while both ends moved together; the client folder was composed by a rule production had dropped thirteen days earlier; and in both cases the guard could not see it because the guard was written from the same wrong copy. **Ask what would have to be untrue for the problem to be absent, and remove the duplicate rather than adding a check to police it.**

## File state, read on 2026-09-20 at 11:57 BST

| File | md5 | Size |
|---|---|---|
| `2026-07-25_BUILD_STATUS.md` | `60bd0aad8e67664cbed8e18d24daa554` | |
| `2026-07-25_CONSOLE_DESIGN.md` | `c82e8f0a98c2d30c35e1001edda596e8` | |
| `IntelliBooks\App\IntelliBooks-Desktop-v3.html` | `c8dae2c4ec2c5cdcba7c6d42fddd087f` | 490,537 bytes |
| `IntelliBooks\App\guards.mjs` | `2b45f04630040aaa3f858133c5cdca57` | eight guards |
| `IntelliBooks\App\drive_seam.mjs` | `b94e9672968161ecd32129edd529390b` | 8,331 bytes, 24 cases |

## How the front end is worked

**`guards.mjs` holds eight guards over `IntelliBooks-Desktop-v3.html`.** `node guards.mjs <file>` and `node guards.mjs --self-test`, which proves each of the eight can fail on a mutation. Run both after every edit to that file.

**`drive_seam.mjs` is new on 2026-09-20 and is the Desktop half of step 10am.** It is the only check of the Review seam's middle link: that an item Intellibills published becomes a Needs Review row, that Delete removes the tray item and writes the note the pipeline reads, and that an item with no receipt id is refused. Run it from `IntelliBooks\App\` against the fixture committed in the pipeline repository at `tests\fixtures\published_item_needs_review.json`. Its header says what it proves and what to watch. **Nothing runs it automatically and its stubs drift**: step 10bk added two calls to both resolution paths and it needed two new stubs the same day.

**Both are in OneDrive and neither is in the repository**, so OneDrive version history is all the versioning they have.

**Four older harnesses exist only in a session scratchpad and are gone.** Rebuild them if you need them: `drive.mjs` on `drainInbox()`, `drive2.mjs` on `fileReviewReceipt()`, `drive3.mjs` on `migrateBooks()`, `drive4.mjs` on `dataMovedUnderneath()` and `exportClientBackup()`. The lesson is in amendment 527: a harness worth keeping goes on disk and gets named.

**Enumerate with the syntax tree, not with a text search.** `acorn` and `acorn-walk` are in `IntelliBooks\App\node_modules`, beside the two harnesses. This project keeps superseded wording beside every correction, so a grep hits the record of what changed.

**Line endings.** `CLAUDE.md` is CRLF. `2026-07-25_BUILD_STATUS.md` and `2026-07-25_CONSOLE_DESIGN.md` are LF. Use `newline=''` in Python and assert the file has none of the wrong kind before writing.

**The amendment-record contiguity check must be bounded.** `2026-07-25_CONSOLE_DESIGN.md` holds a second numbered table that starts again at 1. Find both starts, take the first block, assert `range(1, n+1)` plus an explicit duplicate test.

**`py check_build_status.py` compares section 16's table against its paragraph heads.** Run it after any change to that section. It reads the word before any strike-through, so a status must not carry an unstruck `BUILT` in a paragraph that is outstanding.

## Testing on screen, the method that worked

Name what is on screen, not what is in the code, and check the control exists before naming it. **The previous session told Paul to choose an account called `Office costs`, which is not in the chart.** A test whose setup does not exist yet gets its setup written into the books file first, with a backup proved byte-identical, and the file restored from that backup afterwards; `Client_004-books.json` was set up and restored twice on 2026-09-19 and is byte-identical to where it started. The app must be closed while you write to a books file, or its next save overwrites you.

**The order of a test is part of the test.** Proving that `Check Inbox` draws a new row needed the app reloaded, the inbox empty, Paul already on the Receipts tab, and only then the item written. A refresh first would have drawn the row whether or not the fix worked, and the first attempt was discarded for exactly that.

## Facts established by reading, so they need not be re-established

- The archive is `Intellibills\Documents\{client_id}\{year}\{month}\{receipt_id}_{filename}`, and the address on a published item is that string, relative to the practice root, with backslashes.
- The Review queue reads `Intellibills\Incoming\`, named by `firms.json`'s `publish_destinations.intellibooks`. Resolution notes go to `Intellibills\Resolutions\` and the pipeline moves them into `processed\` or `failed\`.
- `discardReviewReceipt()` deletes the queue entry and nothing else. **The archived document survives a discard**, on both the back-feed path and the `delete_client_copy` path, and there are tests on it now.
- Rules are applied by the amber `Categorise from Rules` button and on statement import, and by nothing else. A transaction already in the books stays uncategorised until one of those runs.
- `transferId` is the transfer marker. `category` is left empty on both legs since step 10x.
- The database is `C:\Intellibills\db\receipts.db`, outside every connected folder, so Paul runs queries. `Clients\` is not connected either.
- `GMTDT` in a Git Bash shell on Paul's machine is Windows' "GMT Daylight Time". It is BST and needs no conversion. This container reports UTC; convert with `TZ=Europe/London`.

## What the previous session got wrong, disclosed

- **It named a control it had not read**, `Office costs`, and it is the rule this project already had.
- **It asked for a test press while the state that test needed had already been used up**, so two presses were wasted and the create path went unrecorded until the rule was removed and the press run again.
- **It verified a repair while a mutation run was live**, reading production files that the harness was editing and restoring underneath it, and reported the check as meaningful. It withdrew it. **Do not read production files while Claude Code says a mutation run is in flight.**
- **It overstated a flag**, telling Paul a stale panel meant the screen said a receipt was waiting when it was not, without checking what a refresh did. Paul refreshed and sent the screen back.

## How this session works

Read the report in full first, then verify the claims that matter against the thing itself. Ask Paul before deriving. Flag with a recommendation, never without one. Disclose your own mistakes. Say what a confidence level is about, not only what it rests on. Name the file, the function or the window in full, every time. No prose to Paul: bullets, tables, numbered steps, short. Answer the question asked and stop. Date, time, zone and verbosity at the start of every reply, clock read fresh each time. No em dashes. **Paul does not like items left open**: put the decision to him, and where he takes one, it becomes a step rather than a note.

The traps live in `CLAUDE.md` and nowhere else. Read them there.

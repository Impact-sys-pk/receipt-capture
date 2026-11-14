Handover for a new consultant (Cowork) session, Receipts capture App project. Written 2026-09-19 at 09:16 BST, read off the clock. **It replaces every earlier handover.**

## Who you are

You are the consultant session. You own verification, the design document, the build status and the prompts, and you write `IntelliBooks-Desktop-v3.html` on Paul's standing instruction. A separate implementation session in Claude Code works the Python pipeline. You cannot see it. Paul is the only channel between you.

**`2026-07-25_BUILD_STATUS.md` is written by you and by nobody else.** Claude Code does not mark its own step paragraphs built. Say so in every brief.

## First action, before anything else

Request device folder access to all four folders. Do not ask piecemeal.

- `C:\LastingImpact\receipt_capture`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts`

Do not touch `C:\LastingImpact\uber-phase1-ingestion-worker`.

## Read the project instructions first

They were rewritten on 2026-09-18 and they carry the rules. **This handover does not restate them.** Two copies of one list drift, which is the argument `CLAUDE.md` already makes about the traps.

**One defect in the pasted copy, for Paul to fix when he next edits it.** The terminology line reads `Intellibills\Receipts{client_id}-receipts.json`. A backslash was lost in the paste. It should be `Intellibills\Receipts\{client_id}-receipts.json`.

## What happened on 2026-09-18, and it is the most important thing here

**The consultant session destroyed sixteen receipt records on `Client_004` and did not notice for four hours.**

- Step 10bf added `delete books.receipts` to `migrateBooks()`, because the key carried 3,255,410 bytes across five books files that nothing reads.
- The consultant session wrote, in the step and to Paul, that the records "were never at risk: they are in `{client_id}-receipts.json`". **It never checked.** `loadReceipts()` has no migration: where the store file is absent it creates an empty one.
- Paul was then asked to open all five clients, which rewrote every books file without the key.
- `Client_004-books.json` held 17 records. `Client_004-receipts.json` held 1. Four of `Client_004`'s 32 transactions name a `receiptId` with no record behind it.
- It was found by accident, while reading the receipts files for an unrelated step.

**Recovered and kept, not restored.** `IntelliBooks\Recovery\Client_004-books-2026-09-17_0940.json`, 3,045,969 bytes, taken from a volume shadow copy of 2026-09-18 02:37. **Paul's decision, 2026-09-18: nothing is put back.** `Client_004` is Test Sole Trader, a test client, and step 10i clears the test estate.

**Two consequences that are live:**

1. **A books file written before 2026-09-16 loses its receipt records on load, silently.** Step 10bj was written to fix that and Paul cancelled it, amendment 515, because it does nothing for any receipt created from 2026-09-18 onwards. The exposure is accepted and recorded.
2. **Nothing compares a transaction's `receiptId` against the receipt store.** That is what would have caught this on the first day. It is neither cancelled nor scheduled and it needs a decision.

## Where the work stands

`2026-07-25_BUILD_STATUS.md` head line, as at 2026-09-18: **67 built, 16 outstanding, 6 cancelled, 1 moved out of this order, 90 steps.** Amendment record at **516**, contiguous 1 to 516, no duplicates.

**The sixteen outstanding:** 10t, 10x, 10al, 10am, 10ao, 10i, 11, 13, 14, 15, 16, 17, 18, 20, 21, 22.

**The eight in section 10, with holders:**

| Step | What is left | Holder |
|---|---|---|
| 10ao.1 | Delete on a Needs Review row, `discardReviewReceipt()`, run on screen. Destructive, needs a receipt Paul is willing to lose | Consultant, Paul at the screen |
| 10ao.2 | A decision Paul has never been asked: six receipt records on Test 2 left wrong by the old `parseSidecar` bug. Not re-checked against current files | Decision for Paul |
| 10al | Four Desktop checks never run: checks A, F, a dialog-wording check, and an APPLE BILL categorisation toast in TEST | Consultant, Paul at the screen |
| 10am | A synthetic test forcing a receipt through the Review seam | Consultant |
| 10x | `t.category` stops carrying the literal `"(Transfer)"`. **Mechanism undecided** | Decision for Paul, then consultant |
| 10t | The reports set, scoped generally on Paul's instruction. **Carries an unchecked claim**: its own paragraph says the HMRC digital-links claim must be checked against HMRC before anything is designed on it, and that check has not been done | Discussion with Paul |
| 10i | The pilot. Clears the test estate immediately before it and not sooner | Paul |

**Paul's agreed ordering, 2026-09-18: do the screen tests, fix 10x, and stop growing the design document until the console is either scheduled or dropped.**

## Nothing is with Claude Code

All briefs are done. Step 10bh was its last, built in `989a30e` and verified by the consultant session's own enumeration rather than from its report. Its remaining work is the console, steps 11 and 13 to 18, and the console is not built.

**It flagged one thing and did not act on it.** `worker\client_copy.py` returns a refusal string citing section 12.2 that a caller later logs, so it reaches a log file but sits outside the new guard's set. Section 12.2 is live, so nothing is broken. Paul's decision, 2026-09-18: leave it.

## What changed on 2026-09-17 and 2026-09-18

| | |
|---|---|
| Built | 10ba.15, 10aw both halves, 10v, 10ai, 10an, 10bf, 10bg, 10bh |
| Cancelled | 10bj and 10bi, both the day they were added, amendments 515 and 516 |
| Rewritten | 10ao, amendment 512. Three of the four things it scheduled had been done or had gone |
| Amendments | 505 to 516 |

**Commits on `feat/console-phase0`, none pushed:** `fa57195`, `6f55fdb`, `8f7aac4`, `e8ea1e7`, `0cd88e4`, `6014f29`, `b7eee74`, `bef451e`, `928f5ce`, `b26e166`, `989a30e`, `45f6f62`, `5c6b047`, `caccb80`, `f0092d8`, `9cf046c`.

## File state, verified by staging back on 2026-09-19

| File | md5 |
|---|---|
| `2026-07-25_BUILD_STATUS.md` | `3ca5bed35dd61fb1ed130792a2041699` |
| `2026-07-25_CONSOLE_DESIGN.md` | `2dc14e92b2ec71bc39c01fd19ff754b6` |
| `IntelliBooks\App\IntelliBooks-Desktop-v3.html` | `50986819774c5cf98c9a6773da211f42`, 487,481 bytes |
| `IntelliBooks\App\guards.mjs` | `2b45f04630040aaa3f858133c5cdca57`, eight guards |

## How the front end is worked

**There is no `device_bash`.** Every read is `device_stage_files`; every write is `SendUserFile` then `device_commit_files` with `expectedMtimeMs`, then re-stage and compare md5. A `.bak-before-<change>` is written first and proved byte-exact. **Never force.**

**Enumerate with the syntax tree, not with a text search.** `acorn` and `acorn-walk` are in `/tmp/node_modules` for the JavaScript; Python's `ast` for the pipeline. This project keeps superseded wording beside every correction, so a grep hits the record of what changed.

**`guards.mjs` holds eight guards over `IntelliBooks-Desktop-v3.html`.** Run `node guards.mjs <file>` and `node guards.mjs --self-test`, which proves each of the eight can fail on a mutation. In summary: no `receipts` property outside four named places; only `saveOne()` writes JSON with a null handle; only three functions call `saveOne()`; no retired `image`/`doc`/`imageBase64`; only `archiveFileHandle()` walks the archive; `booksMod` confined to four places; the `_pipeId` check precedes anything irreversible in `fileReviewReceipt()` and `discardReviewReceipt()`; and each of the four memory exporters calls `dataMovedUnderneath()` before it writes.

**A fifth does not: `IntelliBooks\App\drive_seam.mjs`, added 2026-09-20 by amendment 527, Paul's decision.** It is the Desktop half of step 10am and the only check of the Review seam's middle link. Run it from `IntelliBooks\App\` against the fixture committed in the pipeline repository at `tests\fixtures\published_item_needs_review.json`; its header says what it proves and what to watch. 24 cases.

**Four harnesses exist only in the session scratchpad and are not on Paul's disk.** `drive.mjs` 10 cases on `drainInbox()`, `drive2.mjs` 10 on `fileReviewReceipt()`, `drive3.mjs` 5 on `migrateBooks()`, `drive4.mjs` 11 on `dataMovedUnderneath()` and `exportClientBackup()`. **Rebuild them if you need them.** Each extracts the real function from the file's syntax tree, so what runs is the code in the file.

**Line endings.** `CLAUDE.md` is CRLF. `2026-07-25_BUILD_STATUS.md` and `2026-07-25_CONSOLE_DESIGN.md` are LF. Use `newline=''` in Python and assert the file has none of the wrong kind before writing.

**The amendment-record contiguity check must be bounded.** `2026-07-25_CONSOLE_DESIGN.md` holds a second numbered table that starts again at 1. Find both starts, take the first block, and assert `range(1, n+1)` plus an explicit duplicate test.

## Facts established by reading, so they need not be re-established

- The archive is `Intellibills\Documents\{client_id}\{year}\{month}\{receipt_id}_{filename}`. `Client_004` has 23 documents in it.
- The receipt store is `Intellibills\Receipts\{client_id}-receipts.json`. Four of the five are `[]`; `Client_004` holds one record.
- The database is `C:\Intellibills\db\receipts.db`, outside OneDrive, logs beside it.
- **58 `.py` files are git-tracked outside `tests\`; 57 are running code.** The 58th is `docs\specs\categorisation_engine.py`, a specification. Both figures appear in the documents and amendment 514 says which answers which question.
- **67 citations of section 18 remain in the production Python** after step 10bh, all in comments and docstrings, deliberately left. Five person-facing ones were repointed at `section 20.1`.
- **81 citations remain in `2026-07-25_BUILD_STATUS.md` across 45 lines, and they stay.** Step 10bi was cancelled as cosmetic.
- `2026-09-18_NOTE_section_18_map.md` records where each of section 18's sixteen subsections went. **Twelve have no home in the document body and nine of those carry live design.** Reinstating them is parked until the console is scheduled.
- `IntelliBooks\Backups\` holds nothing newer than 2026-09-01. It is not a recovery route.
- **Windows volume shadow copies are.** Right-click the file, Previous Versions. The Open button launches the file's associated app; browse `\\localhost\C$\@GMT-<timestamp>\...` in Explorer's address bar instead, and copy rather than Restore.
- `.gitignore` covers `*.bak-*`.
- `py check_build_status.py` compares section 16's table against its paragraph heads. Run it after any change to that section.
- `GMTDT` in a Git Bash shell on Paul's machine is Windows' "GMT Daylight Time". **It is BST and needs no conversion.** The consultant session's own container reports UTC; convert with `TZ=Europe/London`.

## Two things the consultant session got wrong on 2026-09-18, beyond the data loss

- **It stated times it had not read**, including in a document header, having corrected Claude Code for the same fault twice. Read the clock in every reply and in every document you write.
- **It wrote dramatic, aphoristic prose into the design document**, and one sentence recorded a decision Paul had not made. Amendment 515 was rewritten for both. Write plainly, and record a decision in the words he used.

## How this session works

Read the report in full first, then verify the claims that matter against the thing itself. Ask Paul before deriving. Flag with a recommendation, never without one. Disclose your own mistakes. Say what a confidence level is about, not only what it rests on. Name the file, the function or the window in full, every time. No prose to Paul: bullets, tables, numbered steps, short. Answer the question asked and stop, and do not show your working afterwards. Date, time, zone and verbosity at the start of every reply, clock read fresh each time. No em dashes.

The traps live in `CLAUDE.md` and nowhere else. Read them there.

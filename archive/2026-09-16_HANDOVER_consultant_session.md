Handover for a new consultant (Cowork) session, Receipts capture App project. Written 2026-09-16 at 12:05 BST. It replaces every earlier handover.

## Who you are

You are the consultant session. You own verification, the design document and the prompts, and you write `IntelliBooks-Desktop-v3.html` on Paul's standing instruction. A separate implementation session in Claude Code works the Python pipeline. You cannot see it. Paul is the only channel between you.

## First action, before anything else

Request device folder access to all four folders. Do not ask piecemeal.

- `C:\LastingImpact\receipt_capture`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts`

Do not touch `C:\LastingImpact\uber-phase1-ingestion-worker`.

## Eleven assurances given to Paul, and they are not optional

Each one is here because it went wrong on 2026-09-15 or 2026-09-16.

1. **One recommendation, not a menu.** Where there is one answer, give it as the answer. Options only when two are genuinely live, and never one already ruled out.
2. **Section 18 is retired and section 20 is the principal source.** The amendment record explains section 20; it is not a source in its own right. Where section 20 does not answer a question, put it to Paul.
3. **Nothing is written into `2026-07-25_CONSOLE_DESIGN.md` until Paul has seen the wording.**
4. **When Paul has already said something, act on it.** Do not re-derive it or talk past it.
5. **Answer the question asked and stop.** No red herrings, no extra consequences bolted on.
6. **Say where something was read, or say it has not been read.**
7. **State the consequence, not the mechanism.** Paul had to ask three times for the plain version of one risk.
8. **Do not invent a second numbered list.** There is one lifecycle, 20.2; one list of what must be built, 20.6; and one list of what state each item is in, step 10ba of `2026-07-25_BUILD_STATUS.md`.
9. **Never write "file" or "record" without saying what kind.** The document, the JSON sidecar, the books file, the receipts file, the database row. **And never "a file" where there are two.** A receipt in the Receipt Inbox is a pair: the document and its JSON sidecar.
10. **Re-stage a shared file immediately before editing it.** A copy taken earlier in the session is not the file.
11. **Always pass `expectedMtimeMs` when writing a file back.** On 2026-09-16 the consultant session overwrote Claude Code's uncommitted work in `CLAUDE.md` by editing a copy staged nineteen hours earlier and committing it without the guard. If a write is refused, re-read and redo the edit. Never force.

## Commits are the consultant session's decision

Paul's instruction, 2026-09-15: decide when to commit and give him the PowerShell command without asking. Every command carries its own `cd` line and is labelled by where it goes. Never hand him a script to run in place of doing the work.

## Where the design lives

- **`2026-07-25_CONSOLE_DESIGN.md` section 20, Where receipt documents live.** The principal source. 20.1 the stores, 20.2 the lifecycle in ten steps, 20.3 what changes, 20.4 the address on the published item, 20.5 what needs no change, 20.6 the eighteen build items, 20.7 section 18's retirement, 20.8 confidence.
- **Section 18 is deleted**, 2026-09-16, amendment 498. A four-paragraph notice stands in its place. Its text is in the git history and in `2026-07-25_CONSOLE_DESIGN.md.bak-before-498`.
- **`2026-07-25_BUILD_STATUS.md` step 10ba** tracks the work. Eighteen sub-steps, each a short label and a pointer at its 20.6 item. **The substance is not repeated there**, so the two cannot drift.

**Do not restate 20.2 or 20.6 anywhere.** Point at them.

## Where the work stands

**Built and committed.** 10ba.1 to 10ba.7, the Python worker half, in `ae336b9`. The published item now carries `archive_path` relative to the practice root instead of the picture, `image_media_type` stays, a missing document still fails the publish, and the exchange folder is `Intellibills\Incoming\`.

**Outstanding, and it is the consultant session's.** 10ba.8 to 10ba.18, the front end, in `IntelliBooks-Desktop-v3.html`. Paul agreed splitting it:

- **Change A.** Move the receipt records from `{client_id}-books.json` into `Intellibills\Receipts\{client_id}-receipts.json`. The record is unchanged, picture and all. Nothing looks different on screen. Needs nothing from Claude Code. This is 10ba.8, 10ba.11 and 10ba.16 to 10ba.18.
- **Change B.** Swap the picture for the address and change how a receipt is shown. This is 10ba.9, 10ba.10 and 10ba.12 to 10ba.14.

**Change A is the riskiest thing in the consultant half.** `books.receipts` appears 50 times across 32 functions, enumerated 2026-09-16. It is removed outright rather than emptied, so a reader that was missed throws rather than showing an empty list.

**There is a live gap until 10ba.10 lands.** The worker publishes to `Intellibills\Incoming\` and the front end still reads `IntelliBooks\Incoming\`. Nothing is lost; items queue where the app does not look, and nothing new reaches the Receipts tab.

## Claude Code

Committed on `feat/console-phase0`, none pushed: `52cc007` schema drift check, `b21b4f2` the two year flags, `ae336b9` the address on the published item, `5bcfbe4` the mkdir membership test, `178bbe7` the stale counts. Every one was verified by the consultant session against the code on Paul's machine rather than taken from its report.

**Nothing is with Claude Code right now.** All three briefs are done.

## Outstanding

| # | Item | Holder |
|---|---|---|
| 1 | 10ba.8 to 10ba.18, the front end half. Change A first | Consultant |
| 2 | **Delete `IntelliBooks\Incoming\` when 10ba.10 lands and not before.** Paul emptied it on 2026-09-16 and it is verified empty. Until 10ba.10 the front end still reads it. Recorded in 10ba.7 | Paul, on the consultant session's reminder |
| 3 | 65 citations of section 18 in `2026-07-25_BUILD_STATUS.md`. Agreed treatment: rewrite each sentence to stand on its own, correcting the fact, with no citation where the citation adds nothing. **Not a strip**: the citation is the subject of most of those sentences | Consultant |
| 4 | Roughly 30 of those 65 are about VAT treatment, the two checks, bulk behaviour, and what is kept after Post. **Section 20 covers none of it and there is nowhere to point them.** Those subjects need a home | Decision for Paul |
| 5 | `extractions` is renamed to `logs` at step 10i, when the database is cleared, and not before. Agreed 2026-09-16, not yet written into 20.6 | Consultant |
| 6 | Step 10au's two-direction comparison. Built, never run | Paul, at the screen |
| 7 | Receipt `a96ab8f7-3af1-42e7-bd98-dee8be2529b8`, `Client_004`, `discarded`, still carrying a `filed_path` while its audit row records `filed_path_cleared`. Six causes ruled out, no seventh offered. Settled by discarding a receipt today with the copy deleted and reading the column back | Paul |
| 8 | Receipt `bbe45473`, attached from the Bank Transactions tab, no client folder copy and no `filed_path`. Unexplained | Not opened |
| 9 | `CLAUDE.md` line 389 says two source guards sweep the git-tracked set. There are three: `tests\test_implausible_year.py:408` is the third | Flagged, not fixed |

## Facts established by reading, so they need not be re-established

- The archive is `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\Documents\`. `config.py`: `PRACTICE_ROOT` 127, `INTELLIBILLS_ROOT` 132, `FILES_DIR` 186.
- The database is `C:\Intellibills\db\receipts.db`, outside OneDrive, logs beside it, backups to `Intellibills\Backups\`. Eleven tables, confirmed live on 2026-09-16 against `worker/database/schema.py`.
- The records table is `receipts` and the logs table is `extractions`. The logs table holds machine readings and operator corrections alike, never updated, and the newest row is the receipt's current figures.
- **Every `file_path` and `filed_path` value in the database is absolute**, 35 and 26 of them, carrying the full `C:\Users\PDK7\...` prefix. The relative rule belongs to the JSON notes the front end writes. Converting is work the publisher does.
- The books file is `IntelliBooks\Books\{client_id}-books.json`. Five live clients. `Client_004-books.json` is 3,046,003 bytes and 98.5% of it is receipt pictures. With the pictures out and an address in, its 17 records come to 7,682 bytes, about 452 bytes each.
- The Receipts tab is Intellibills' front end hosted in IntelliBooks Desktop's shell. Hosting is not ownership.
- A receipt is Intellibills' data until it is attached to a transaction or posted to the cashbook.
- `.gitignore` covers `*.bak-*`, so the `.bak-before-NNN` convention needs no exclusion.
- `py check_build_status.py` compares section 16's table against its paragraph heads. Run it after any change to that section.

## How this session works

Read the report in full first, then verify the claims that matter against the thing itself. Ask Paul before deriving. Flag with a recommendation, never without one. Disclose your own mistakes. Say what a confidence level rests on. Name the file, the function or the window in full, every time. No prose to Paul: bullets, tables, numbered steps, short. Date, time, zone and verbosity at the start of every reply, clock read fresh each time. No em dashes.

The traps live in `CLAUDE.md` and nowhere else. Read them there.

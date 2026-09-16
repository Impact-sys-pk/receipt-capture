Handover for a new consultant (Cowork) session, Receipts capture App project. Written 2026-09-16 at 08:30 BST. It replaces `2026-09-15_HANDOVER_consultant_session.md`, which is now behind.

## Who you are

You are the consultant session. You own verification, the design document and the prompts, and you write `IntelliBooks-Desktop-v3.html` on Paul's standing instruction. A separate implementation session in Claude Code works the Python pipeline. You cannot see it. Paul is the only channel between you.

## First action, before anything else

Request device folder access to all four folders. Do not ask piecemeal.

- `C:\LastingImpact\receipt_capture`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts`

Do not touch `C:\LastingImpact\uber-phase1-ingestion-worker`.

## Six assurances given to Paul on 2026-09-15, and they are not optional

Given after a session in which each of the six went wrong at least once.

1. **One recommendation, not a menu.** Where there is one answer, give it as the answer. Options only when two are genuinely live, and never one already ruled out.
2. **Section 18 of `2026-07-25_CONSOLE_DESIGN.md` is not consulted and not cited, and amendments are not searched for justification.** Amendment 485. Reason from the code and from what Paul has decided. Where an answer needs section 18, ask Paul.
3. **Nothing is written into `2026-07-25_CONSOLE_DESIGN.md` until Paul has seen the wording.**
4. **When Paul has already said something, act on it.** Do not re-derive it or talk past it.
5. **Answer the question asked and stop.** No red herrings, no extra consequences bolted on.
6. **Say where something was read, or say it has not been read.**

Two more, learned the same evening and just as binding.

7. **State the consequence, not the mechanism.** Paul had to ask three times for the plain version of one risk.
8. **Do not invent a second numbered list.** There is one lifecycle and it is section 20.2.
9. **Never write "file" or "record" without saying what kind.** Paul's instruction, 2026-09-16. Say the document, the JSON sidecar, the books file, the receipts file, the database row. **And never write "a file" where there are two.** A receipt in the Receipt Inbox is a pair: the document and its JSON sidecar.

## Commits are the consultant session's decision

Paul's instruction, 2026-09-15: decide when to commit and give him the PowerShell command without asking first. Every command carries its own `cd` line and is labelled by where it goes.

## The receipt's life, today and proposed

This is the single lifecycle. **Section 20.2 of `2026-07-25_CONSOLE_DESIGN.md` still carries an older nine-step version of it and two of those steps are wrong.** Correcting 20.2 to match this table is the first job, and the wording has been drafted and is waiting on Paul.

| # | Today | Proposed | Whose | State |
|---|---|---|---|---|
| 1 | Document arrives, by email, the Receipt Inbox folder, or the phone app | No change | | |
| 2 | Worker writes one copy to the archive, `Intellibills\Documents\{client_id}\{year}\{month}\{receipt_id}_{filename}`, never changed again | No change | | |
| 3 | Worker creates the database record saying where the file is and what state the receipt is in | No change | | |
| 4 | Extraction runs and is logged. An operator correction is logged the same way | No change | | |
| 5 | Validation sets the receipt to ok, needs review, failed or possible duplicate | No change | | |
| 6 | Worker may copy the document into `Clients\{client}\IntelliBooks\Receipts\{tax year}\`, on the firm setting | No change | | |
| 7 | Worker writes one JSON item into `IntelliBooks\Incoming\`, holding the details **and the picture as base64** | Writes into `Intellibills\Incoming\`, holding the details **and the document's address**, no picture | Claude Code | Built, not committed |
| 8 | The front end drains the in-tray: writes a row into `IntelliBooks\Books\{client_id}-books.json` **including the picture**, saves, then deletes the in-tray file | Writes the row into `Intellibills\Receipts\{client_id}-receipts.json` **carrying the address**, and deletes the in-tray file only after reading that file back and finding the receipt's id in it | Consultant | Not started |
| 9 | The Receipts tab draws the thumbnail from the picture in the books file | The row shows a type pill. Clicking it opens the document from the archive at the address from step 2 | Consultant | Not started |
| 10 | The operator attaches the receipt to a transaction, posts it to the cashbook, or deletes it | No change | | |
| 11 | The front end writes a note into `Intellibills\Resolutions\`. The worker reads it on its next run, updates the database and moves the note aside | No change | | |

**The consultant session's half is steps 8 and 9 only.** Paul agreed splitting step 8 into two passes:

- **Change A.** Move the row from the books file to `Intellibills\Receipts\{client_id}-receipts.json`. The row is unchanged, picture and all. Nothing looks different on screen. Needs nothing from Claude Code.
- **Change B.** Swap the picture for the address, and change step 9. Needs step 7 to have landed first.

Change A touches about fifty places in the app and is the riskiest part of the consultant half. Doing it alone means it is tested against receipts that look exactly as they do today.

## What was settled on 2026-09-15, and where it is written

Amendments 483 to 489 of `2026-07-25_CONSOLE_DESIGN.md`. Section 20, Where receipt documents live, is the design and is read on its own.

- **483.** Section 20 created. Section 18 put under review, with a note at the head of the document, a note at the head of 18, and a marker under all fourteen of its subsections.
- **484.** Three corrections found by re-checking amendments 458 to 472 against the code. Twelve of the fifteen held exactly.
- **485.** Section 18 is not consulted and not cited.
- **486.** The published item carries the document's address, relative to the practice root. The moved-folder risk is accepted with Paul's three reasons recorded: he will not move it, a subcontractor will not have access to `Intellibills\`, and the cloud version has a different file structure.
- **487.** The exchange folder moves to `Intellibills\Incoming\` and `IntelliBooks\Incoming\` is deleted. Both ends of that exchange are Intellibills.
- **488.** Receipt records leave the books file for `Intellibills\Receipts\{client_id}-receipts.json`. `books.receipts` is removed. The existing rows are abandoned rather than migrated, being test data that step 10i clears before the pilot.
- **489.** The implementation gap list is itemised, seventeen items, seven on the Python worker and ten on the front end. Section 20.6.

## Three decisions inside 20.6 worth not re-opening

- An explicit existence check replaces the one the byte read was doing, so a missing document still fails the publish and still records its reason.
- `books.receipts` is removed outright rather than emptied, so a reader that was missed throws rather than showing an empty list. Enumerated at 50 occurrences across 32 functions in `IntelliBooks-Desktop-v3.html`.
- The drain reads the receipts file back from disk and deletes a tray file only if that receipt's id is in what it read. **No flag decides the delete.** Paul rejected a test as the answer here: designing the failure out beats guarding it.

## Claude Code

Two commits verified by this session against `.git` on Paul's machine rather than taken from the reports.

- `52cc007`, the schema drift check. Suite 1475 passed.
- `b21b4f2`, the two year flags. Suite 1484 passed.

**In flight:** `PROMPT_claude_code_2026-09-15_publish_the_address_not_the_picture.md`, items 1 to 7. Items 1 to 7 are built and not committed. Claude Code raised one decision and Paul agreed it: a document outside the practice root is refused with `PublishError`, because production cannot produce one and the seven failing fixtures model something that cannot happen.

**Not sent:** `PROMPT_claude_code_2026-09-14_mkdir_membership.md`, written, last of the three.

## Outstanding

| # | Item | Holder |
|---|---|---|
| 1 | Correct 20.2 to the eleven steps above. Step 4 says `IntelliBooks\Incoming\` and step 5 says the row is held in `books.receipts`. Both are superseded by amendments 487 and 488 | Consultant, wording drafted, waiting on Paul |
| 2 | Correct 20.4's precedent sentence. It says the address follows "the same rule `filed_path` already follows". The database stores absolute paths: `save_file()` returns `config.FILES_DIR / ...` and `repository.py:205` stores `str(file_path)`. The relative rule belongs to the notes Desktop writes | Consultant, wording drafted, waiting on Paul |
| 3 | Change A, step 8 | Consultant, not started |
| 4 | Change B, steps 8 and 9 | Consultant, after Claude Code's items 1 to 7 land |
| 5 | Mkdir membership brief | Consultant to send after the current brief |
| 6 | Step 10au's two-direction comparison. Built, never run | Paul, at the screen |
| 7 | Receipt `a96ab8f7-3af1-42e7-bd98-dee8be2529b8`, `Client_004`, `discarded`, still carrying a `filed_path` while its audit row records `filed_path_cleared`. Six causes ruled out, no seventh offered. Settled by discarding a receipt today with the copy deleted and reading the column back | Paul, needs the pipeline and Desktop |
| 8 | Receipt `bbe45473`, attached from the Bank Transactions tab, no client folder copy and no `filed_path`. Unexplained | Not opened |
| 9 | `CLAUDE.md` line 389 says there are two source guards sweeping the git-tracked set. There are three: `tests\test_implausible_year.py:408` is the third | Flagged, not fixed |

## Facts established by reading, so they need not be re-established

- The archive is `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\Documents\`. `config.py`: `PRACTICE_ROOT` at 127, `INTELLIBILLS_ROOT` at 132, `FILES_DIR` at 186.
- The books file is `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\Books\{client_id}-books.json`. Five live clients.
- `Client_004-books.json` is 3,046,003 bytes and holds 17 receipts and 31 transactions. The receipts array alone is 3,000,338 bytes, so 98.5% of that file is pictures. With the pictures out and an address in, those 17 records come to 7,682 bytes, about 452 bytes each.
- The Receipts tab is Intellibills' front end hosted in IntelliBooks Desktop's shell. Hosting is not ownership.
- A receipt is Intellibills' data until it is attached to a transaction or posted to the cashbook.
- The only writer of the exchange folder is `publish_receipt()` in `worker/publish.py`. The only readers are `drainInbox()`, `renderInboxCount()`, `scanReview()`, `collectAllClientReview()` and `discardReviewReceipt()`, all part of the Receipts tab or the Review queue.
- `saveBooks()` in `IntelliBooks-Desktop-v3.html` refuses to save when the file's modification time has moved since load, and puts up a STOP box. `drainInbox()` saves before it deletes from the tray.
- `.gitignore` covers `*.bak-*`, so the `.bak-before-NNN` convention needs no exclusion.

## How this session works

Read the report in full first, then verify the claims that matter against the thing itself. Ask Paul before deriving. Flag with a recommendation, never without one. Disclose your own mistakes. Say what a confidence level rests on. Name the file, the function or the window in full, every time. No prose to Paul: bullets, tables, numbered steps, short. Date, time, zone and verbosity at the start of every reply, clock read fresh each time. No em dashes.

The traps live in `CLAUDE.md` and nowhere else. Read them there.

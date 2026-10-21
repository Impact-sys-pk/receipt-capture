Handover for a new consultant (Cowork) session, Receipts capture App project. Written 2026-10-21 at 13:12 BST, read off the clock. **It replaces every earlier handover, including `2026-09-22_HANDOVER_consultant_session.md`.**

## Who you are

You are the consultant session. You own verification, the design document, the build status and the prompts, and you write `IntelliBooks-Desktop-v3.html` on Paul's standing instruction. A separate implementation session in Claude Code works the Python pipeline. You cannot see it. Paul is the only channel between you.

**`2026-07-25_BUILD_STATUS.md` is written by you and by nobody else.** Say so in every brief.

## First action, before anything else

Request device folder access to these in one go. Do not ask piecemeal.

- `C:\LastingImpact\receipt_capture`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts`
- `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients`
- `C:\Intellibills`

**The last two are new to this handover and both earned their place on 2026-10-21.** `C:\Intellibills` holds the live database and is how a claim about the data is checked rather than argued about. `Clients\` is where the client folder copies are.

**`C:\LastingImpact\uber-phase1-ingestion-worker` is no longer off limits.** The 2026-09-22 handover said not to touch it. Paul's instruction of 2026-10-21 is that the Uber statement parser there is the starting point for reading a platform and a week ending off a statement. Request it when that work is live.

**This session had `device_bash`.** The 2026-09-22 one did not. Establish it, do not assume it.

## Read the project instructions first

They carry the rules. **This handover does not restate them.**

## Where the work stands

`2026-07-25_BUILD_STATUS.md` head line, as at 2026-10-21: **75 built, 16 outstanding, 6 cancelled, 1 moved out of this order, 98 steps.** Amendment record at **547**.

**The sixteen outstanding: 10bm, 10bn, 10bo, 10bp, 10br, 10i, 11, 13, 14, 15, 16, 17, 18, 20, 21, 22.** Ten are the console, which is not built and not scheduled.

**What this session did, 2026-10-20 and 2026-10-21:**

| Step | What happened |
|---|---|
| 10bq | **BUILT and closed.** Both automatic client emails reworded, a firm `Reply-To` added, outstanding item 24 closed, F6 renamed Client-facing receipts address. Commits `ff4e2e3`, `d36a245`, `a65bab9`, pushed |
| 10br | **ADDED and designed, not built.** Attachments, stage one. Fifteen decisions, all Paul's, all in his words in the step body |

## Step 10br, and it is the live work

**Read step 10br in full. It is long and every paragraph is a decision of Paul's.** The brief for the pipeline half is `PROMPT_claude_code_2026-10-21_attachments_stage_one.md`. The Documents tab in `IntelliBooks-Desktop-v3.html` is yours and is not started.

**One thing is NOT decided and blocks the pipeline half: which model performs the classification call.** The brief tells Claude Code to propose and stop.

**Terminology Paul settled on 2026-10-21 and which you must hold to:**

- **Attachments** means all three kinds together: **App Statements**, **Bank Statements**, **Other Attachments**. It never means the third alone.
- **App Statements**, not Uber statements: the capture app sends Uber, Bolt and FreeNow.
- **The exchange folder** is `Intellibills\Incoming\`. It is not the Handover Pack.
- **Do not use the word "store".** Paul stopped this session using it because it covered three different things. Name them: the archive, the database table, the record file, the client folder copy.

## What this session got wrong, three times, in one day

**All three were the same fault: taking a description of a thing for the thing.** The project's own rule covers it and this session broke it anyway.

1. Cited `app.py:839` as the reader of the firm name, from a note in the design document written on 2026-07-22. The file had moved. The real readers are `app.py:361` and `:1793`.
2. Told Paul that IntelliBooks Desktop reads `Intellibills\Review\`, from a comment at line 1095 of `IntelliBooks-Desktop-v3.html`. It reads the exchange folder. The comment was stale and is now corrected.
3. Told Paul that amendment 170 says the client folder has "four children and no more". It does not. That phrase is a comment in `config.py`.

**And one of substance**: this session said nothing writes a statement sidecar, having searched two codebases for one string. The capture app writes them, proved by a filed statement row with source `phone`. **Paul's instruction after it: "You are required to read everything relevant before presenting findings. No guesswork. No shortcuts."**

## Things established on 2026-10-21 that are not written anywhere else

- **`Intellibills\Review\` is read by nothing on screen.** `worker\filing.py` line 215 records it as the pipeline's own and asks whether it should exist at all. **That question is still open.**
- **An App Statement is invisible today.** It has an archive copy, a `statements` row and a client folder copy, and appears nowhere in IntelliBooks Desktop. `isStatement` is set once in `parseSidecar()` and read nowhere.
- **`bills@intellitax.co.uk` is a shared mailbox on Microsoft 365**, so the pipeline cannot poll it. `capture@lastingimpact.co.uk` on Krystal is Intellibills' leg of the fan-out. Amendment 544.
- **The WhatsApp router at `C:\LastingImpact\whatsapp-message-router` sends attachments it classifies as receipts to `bills@`**, from `whatsapp+<number>@wa.intellitax.co.uk`, which is not the client's own address. Nothing has been built about this.
- **`C:\LastingImpact\bank_statement_parsing`** is four standalone scripts turning Barclays PDFs into CSV, connected to nothing.
- **`pipeline-status.json` said the last run was 2026-09-23.** Nobody has established whether the pipeline has run since.

## Open, and none of it blocks anything

- The classification model, which is Paul's to decide.
- Whether `Intellibills\Review\` should exist.
- The two rules at `bills@` for WhatsApp-routed receipts, and the `whatsapp+` address needing to be in `clients.json` first.
- Four of five client records in `clients.json` carry no email address, so only `pdk7@hotmail.co.uk` resolves.
- A Sodium custom field recording where each client's receipts are redirected to. Paul was setting it up and it is not built.

## Writing to Paul

The project instructions carry this. Two things this session learned the hard way: he will ask for plain English and he means it, and he will check a claim against the file. **Do not state what a document contains unless you have opened it.**

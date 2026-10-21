# AUTOMATIC task. Claude Code brief, 2026-10-21: Attachments, stage one, the pipeline half

Written by the consultant session, 2026-10-21, 13:10 BST, read off the clock in this reply.
Step 10br of `2026-07-25_BUILD_STATUS.md`, added by amendment 547 of
`2026-07-25_CONSOLE_DESIGN.md`. **Read step 10br in full before starting.** It carries fifteen
decisions, each Paul's and each in his own words, and this brief does not repeat all of them.

**This runs under `CLAUDE.md`'s AUTOMATIC Task Mode.** Its stop list is unchanged and outranks this
brief.

**Report to `2026-10-21_REPORT_claude_code_attachments_stage_one.md` in the repository root.**

---

## Three rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** You report; the consultant session marks
the step.

**2. `2026-07-25_CONSOLE_DESIGN.md` is not yours either.**

**3. Enumerate rather than take this brief's word.** Where you need to know what reads or writes a
thing, walk it in this task and state what you found.

---

## Terminology, and hold to it

**Attachments** means all three kinds together: **App Statements**, **Bank Statements** and
**Other Attachments**. Paul's definition, 2026-10-21, exact words in step 10br. It never means the
third kind on its own, which is always written in full.

**App Statements** are the platform statements the capture app sends, Uber, Bolt or FreeNow. The
word is not Uber statements, because three platforms are supported.

**The exchange folder** is `Intellibills\Incoming\`, section 20.1's name for it. It is not the
Handover Pack, which is a client's leaving pack.

The four places a document lives are named separately and the word "store" is not used: **the
archive**, **the database table**, **the record file** and **the client folder copy**.

---

## Why this exists

Nothing in the pipeline asks whether a document is a receipt. `worker\extraction\openai_vision.py`
opens "You are a receipt data extractor" and asks for eleven receipt fields with no field for what
the document is. `worker\validation\rules.py` tests dates and amounts. `is_statement` appears once
in `app.py`, inside the folder-intake loop; the email loop has no such fork. **So every non-receipt
arriving by email is extracted as a receipt today**, including a client's bank statement.

---

## What to build

### 1. A classification call, before extraction

A separate call that decides what a document is, run before the receipt extractor. **Not an extra
field on the extraction call.** Paul's decision, and his reason is stage two's: a bank statement
should never reach the receipt extractor at all.

Four outcomes: **receipt**, **App Statement**, **Bank Statement**, **Other Attachment**.

- A receipt takes the existing path, unchanged.
- **A document it cannot place is an Other Attachment marked for review.** There is no fifth kind.
- **Bank Statement covers credit card statements.**

**Which model performs this call is NOT DECIDED.** Do not choose one. Propose, with what it costs
per document, and stop until Paul answers.

### 2. App Statements need a platform and a week ending

The capture app's client picks both on screen and `upload.js` refuses the upload without them. An
email attachment supplies neither, and the `statements` table requires both.

So the platform and the week ending have to be read off the document. **Paul's instruction, in his
words: "when the time comes to design and write it will be worth looking at our Uber Statement
parser as to how to extract that info instead of reinventing the wheel."** It is at
`C:\LastingImpact\uber-phase1-ingestion-worker`, a repository with its own project. **Read it
before writing any extraction of your own, and say in your report what you took from it.**

**Where either cannot be read, the document is marked for review.** It is still an App Statement.

### 3. Where each kind is recorded

- **App Statements**: the existing `statements` table, whichever route they arrived by. **Do not
  widen that table.** Paul decided it stays as it is.
- **Bank Statements and Other Attachments**: a new table of their own.
- **All three kinds**: a row in a new record file, one per client, which IntelliBooks Desktop reads.
  It mirrors `Intellibills\Receipts\{client_id}-receipts.json` and exists for the same reason, that
  a browser app cannot read the database. The consultant session proposes
  `Intellibills\Attachments\{client_id}-attachments.json`; the path is its choice and not Paul's,
  so say if you find a reason against it.

Each row carries: the kind, the archive address, the client folder copy where one was made, the
arrival date, the original filename, the source, the platform and week ending where they apply, and
whether it is marked for review.

**An Attachment marked for review is in the record file like any other, with the marker as a flag on
the row.** It does not wait anywhere else. Paul's rule: "We cannot have files languishing forever in
a purgatory folder", and the test is whether he can see it.

### 4. All three kinds pass through the exchange folder

Including App Statements from the capture app, which reach no screen today. That is how a row
appears in IntelliBooks Desktop.

### 5. The client folder gains two children and one is renamed

`Clients\{client_folder_name}\IntelliBooks\` becomes `Receipts\`, **`App Statements\`**,
**`Bank Statements\`**, **`Other Attachments\`**, `HMRC Summaries\`, `Handover Pack\`.

**`Statements\` is renamed to `App Statements\` and it is a migration, not a constant change.**
Three things move together or a stored path points at nothing: the folder on disk, the absolute path
in `statements.filed_path`, and every place the name is written. **Enumerate those places yourself.**
One file and one row exist today. **Back up before, read back after**, the way amendment 539's client
folder rename was done.

**The comment above `CLIENT_INTELLIBOOKS_FOLDER_NAME` in `config.py` says "Four children and no
more".** That becomes false. Amendment 170 itself does not say it; the comment does. Correct the
comment in the same change.

### 6. A kind can be changed by hand

Paul's decision. Two consequences he accepted: the client folder copy has to move, and changing a
kind to or from App Statement asks him for the platform and the week ending, because that kind lives
in a different table and needs both.

**The screen for this is the consultant session's, not yours.** Build what the pipeline side needs
and say what it expects.

## What it has to do

- A receipt behaves exactly as it does today. Nothing about the receipt path changes.
- No non-receipt reaches the receipt extractor.
- Every Attachment is visible to IntelliBooks Desktop. **Nothing is written only to
  `Intellibills\Review\`**, which is read by nothing on screen.
- The archive is unchanged: one copy, written once, filed by arrival month, never moved. A kind
  change moves no archived file.

## Red before green

- A test per outcome, over the email route and the folder route.
- A test that an App Statement missing its platform or week ending is marked for review and still an
  App Statement.
- A test that an unplaceable document is an Other Attachment marked for review.
- A source guard that the receipt extractor is not reached for a non-receipt.
- Then prove the suite discriminates: put each old behaviour back and show which test goes red. **If
  nothing goes red, say so.**

## What not to do

- **No real model calls in tests.**
- **No writes to the live `receipts.db`** beyond the migration in 5, which is done with the pipeline
  stopped and a backup taken first.
- **Do not touch `IntelliBooks-Desktop-v3.html`.** The Documents tab is the consultant session's.
- **Do not widen the `statements` table.**
- **Do not choose the classification model.** Propose and stop.
- Nothing is deleted anywhere, and nothing is written outside `C:\LastingImpact\receipt_capture`
  except the folder rename in 5.
- **Do not fix anything else.** Flag, do not fix.

## How to report

- What you took from the Uber statement parser, and what you wrote yourself.
- The model you propose for classification, and what it costs per document.
- The places the `Statements\` name was written, enumerated, and how you found them.
- The migration: before and after counts, and what you read back.
- The tests that went red, then green, and the discrimination result.
- Suite totals before and after.
- Anything in step 10br you could not build as written, and why.
- Propose the commit and wait for Paul's yes.
- Disclose your own mistakes, including ones you caught and corrected.

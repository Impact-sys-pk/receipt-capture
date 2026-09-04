# Receipt Capture — Plain English Guide

## What Is Receipt Capture?

Receipt Capture is an automated system that collects receipts from multiple sources, extracts the key financial information using AI, validates that information, and stores everything with a complete audit trail. It's designed to handle the entire receipt intake workflow for an accounting firm.

Think of it like this: receipts arrive from clients via email or file upload, the system automatically reads them, pulls out the numbers (supplier name, invoice date, amounts), checks that the numbers make sense, and files them in the right place. Every step is recorded so you always know what happened to each receipt. If something goes wrong, either the system fixes it automatically the next time the code is corrected, or it waits for a quick manual check, it no longer just sits there permanently until someone resends an email.

---

## Who This Guide Is For

This guide is written for whoever runs Receipt Capture day to day, which may be an office administrator rather than an accountant. Most of what follows, checking status, correcting a misread date or amount, confirming whether two receipts are really the same transaction, is a factual, clerical judgement, not an accounting one, and doesn't need accounting training.

A few things are worth a quick check with an accountant or Paul before acting on them:
- The GL code (accounting category) a receipt gets assigned looks wrong, rather than just missing
- You're not sure whether a "possible duplicate" is genuinely the same transaction or a real second charge
- Anything involving a figure you're not confident you're reading correctly off the original document

Everything else described here, checking status, correcting an obviously-misread field, registering a new client email, asking someone to resend an unsupported file, is safe to handle independently.

---

## How It Works: The Complete Flow

### Step 1: Receipt Arrival

**Reconciled with the code on 2026-09-04, step 10h.** Where this guide was wrong it now says so
rather than being quietly corrected, because you have read the old wording.

Receipts arrive by email or through the Receipt Inbox folder, and **the database records which of
four sources each one came from**: `email`, `phone`, `desktop` or `other`, and no other value,
sub-step 10d.40. `phone` is the phone app, `desktop` is an import from IntelliBooks Desktop, and
`other` is a file dropped into the inbox by hand.

**A) Email Attachments**
- Clients email receipts to `capture@lastingimpact.co.uk`
- The system checks the sender's email address against a client list
- Automatically assigns the receipt to the correct client based on who sent it
- Supported file types: PDF, JPG, PNG, GIF, WebP, TIFF, BMP

**Email Processing & Routing:**

**Before extracting, system checks:**
1. **Known client?** → Resolve client_id and firm_id from sender's email
2. **Unknown sender?** → Send alert, move to "Unknown Sender", done
3. **Has attachment?** → Continue processing
4. **No attachment?** → Check for embedded images
   - Found embedded images (iOS share)? → Extract and process silently
   - No embedded images? → Send alert with firm name, move to "No Attachments", done
5. **Duplicate?** → Move to "Duplicates" (only if already genuinely filed) or flag as "Possible Duplicate" (if it looks similar but isn't a certain match), done

**Embedded images (e.g., iOS share button):**
- Automatically detected and extracted from email body
- Processed like normal file attachments (no alert sent)
- Client's receipt gets processed without needing to resend
- Improves user experience for mobile users

**For valid receipts (known client, has attachment, not a confirmed duplicate):**
- Extract data with AI
- Validate (gross ≈ net + VAT, required fields, valid dates)
- Categorise (always attempted before filing, on every path, see Step 6)

**Email routing by outcome:**

- **Processed Receipts** — Extraction and validation passed, receipt filed to the client's folder with a GL code. No further action needed.
- **Needs Review** — Data is present but something's off (a VAT mismatch, a missing field). The file and its extracted data are copied to the client's Review folder for a quick look. This isn't necessarily final: a code fix can clear it automatically (see "Automatic Retry" below), or it can be corrected and filed properly using `resolve_receipt.py`.
- **Failed Processing** — Extraction itself failed (unreadable file, an OpenAI API error, or a genuine code bug). If the cause was a code bug and a fix ships, the app retries it automatically on its own the next time it starts, no resend needed. If it's a transient API error (a timeout or rate limit), the app retries it a couple of times within the same run before giving up. If a client resends the exact same file after a genuine failure, that resend now goes through rather than being wrongly blocked as a duplicate.
- **Possible Duplicate** — The receipt matches an already-filed one on supplier, date, and amount, but isn't an exact file match. Rather than auto-filing it (which could file a genuine repeat transaction, e.g. two separate same-day parking charges, as a duplicate) or auto-blocking it (which could silently lose a real second receipt), it's held for a quick human confirmation via `resolve_receipt.py`. Where the receipt shows a visible reference number or a time, the system uses that to tell two genuinely different transactions apart automatically, without needing a human to check.
- **Duplicates** — The exact same file, or the same transaction, has already been genuinely filed. This is blocked outright and not reprocessed.
- **Unsupported Files** — Wrong file type (.docx, .xlsx, etc.). Once you resend using a supported format, it goes through cleanly.
- **No Attachments** — Alert sent: "Please resend with receipt attached." Once resent with a file attached, it goes through cleanly.
- **Unknown Sender** — Alert sent: "Please register your email with support." Once that address is added to the client's record in `Intellibills\clients.json`, a resend goes through cleanly.

**Automated alerts (sent automatically):**
- **No-attachment emails:** Client sees alert from their firm name (e.g., "Best Accounting")
- **Unknown senders:** Alert requests email registration
- Alerts are sent once per email (tracked to avoid spam)

**B) The Receipt Inbox folder**
- Files land in `Intellibills\Receipt Inbox\`, in a subfolder per client
- **Each file has a sidecar JSON beside it carrying the `client_id`**, and the client comes from the
  sidecar rather than from the folder the file sat in. ~~a sidecar that specifies the client code~~
  **There is no client code. Sub-step 10d.23 and Paul's ruling of 2026-09-02: it appears nowhere**
- **An inbox sidecar replaces the file's extension**, so `x.pdf` has `x.json`. A filed receipt's
  sidecar appends instead, `x.pdf.json`. Two conventions, deliberately, and confusing them was a
  real defect on 2026-09-03
- Three things write into that folder: the phone app, IntelliBooks Desktop's import, and a person
- The system picks these up on every poll
- Folder-uploaded receipts never touch an email mailbox folder, there isn't one to move, everything about their status lives in the database and, for review/failed cases, a disk copy in the client's Review folder (see "Where Data Really Lives" below)

**Architecture Note:** The current single-firm implementation uses REDIRECT routing at the email service level (simple, reliable, 100% accurate). For future multi-firm or AWS deployments, see `MULTIFIRM_EMAIL_FORWARDING_ANALYSIS_AND_FINDINGS.md` for architectural analysis and why cloud APIs use webhook+metadata instead of email header parsing.

### Step 2: Duplicate Prevention

Before processing, the system checks:
- Has this exact email and attachment been processed before? (message ID + attachment ID)
- Is this the same file that arrived via a different email? (file hash matching)
- Is this a duplicate of an existing receipt in the database? (same supplier, same date, same amount)

Important: the hash and message-ID checks only block a resend if the earlier attempt was **genuinely filed** (successfully processed, not just attempted). A receipt that previously ended in Failed Processing or Needs Review no longer permanently blocks a resend, only a true Processed Receipt does.

The supplier/date/amount check is deliberately not a hard block either. Two genuinely separate transactions can share the same supplier, date, and amount (two identical same-day parking charges are a real example), so a match against this check routes to **Possible Duplicate** for a quick human confirmation rather than silently filing twice or silently rejecting a real receipt. Where the receipt shows a reference number or a time, the system uses that to tell them apart automatically, and only falls back to asking a human when it can't.

### Step 3: File Storage

The original receipt file is copied into the document store:
```
Intellibills\Documents\[client_id]\[year]\[month]\[receipt_id]_original_filename.pdf
```
~~`data/files/2026/07/22/[receipt_id]_original_filename.pdf`~~ **Wrong in four places in this guide
until 2026-09-04.** `data\` was removed by amendment 76, there is no day level, and the folder is the
`client_id` rather than a client code, sub-step 10d.53. **The year and month are the arrival date and
not the invoice date**, deliberately: this runs before extraction, so there is no invoice date yet,
and an arrival date never needs correcting, so no file in the store ever has to move.

Files are never deleted or overwritten, and never moved either, filing always makes a copy elsewhere and leaves this original exactly where it was. This ensures you always have the original document, no matter how many times a receipt gets retried or refiled.

### Step 4: AI Extraction

OpenAI's Vision API reads the receipt image/PDF and extracts:
- Supplier name (who issued the receipt)
- Invoice date (when was it issued)
- Net amount (price before tax)
- VAT amount (tax charged)
- Gross amount (total price)
- Currency (usually GBP)
- Reference number, if visible on the receipt (used to tell apart possible duplicates)
- Time of day, if visible on the receipt (used the same way)

The full response from OpenAI is also stored for audit purposes. Note that the reference number and time aren't always present, many receipts simply don't show one, that's expected and fine, it just means a possible-duplicate match on that receipt will need a human glance rather than being resolved automatically.

If the extraction call itself fails (an OpenAI timeout, rate limit, or network error), the system retries it a couple of times, a few seconds apart, within the same run, before giving up and marking it failed. This is separate from the automatic retry described below, it's about handling a temporary hiccup, not a code problem.

### Step 5: Validation

The system checks that the extracted data makes sense:
- ✓ Gross amount is present
- ✓ Supplier name is present
- ✓ Date is in valid format (YYYY-MM-DD)
- ✓ Math checks out: net + VAT ≈ gross (with ±£0.02 tolerance)

**Outcomes:**
- `ok` — All validations pass, receipt is ready to be categorised and filed
- `needs_review` — Data is present but something doesn't match (e.g., VAT mismatch)
- `failed` — Required data is missing or extraction error occurred
- `possible_duplicate` — Validation passed, but it looks like it might be a repeat of something already filed, held for confirmation

### Step 6: Categorisation

Categorisation is now attempted on every path that files a receipt, whether it arrived fresh by email or folder, got picked up by the automatic retry, or was corrected by hand through `resolve_receipt.py`. A receipt is never filed with a blank category as a matter of course:
- **Six layers, numbered 0 to 5**: rules 0, this client's mappings 1, the firm's shared pool 2,
  fuzzy against the client's 3, fuzzy against the firm's 4, AI 5
- **Codes are four digits.** Any three-digit code you see anywhere is legacy
- **Layer 5, the AI, may only propose accounts the client's own published chart marks
  `classifier_eligible`**, read from `Intellibills\Charts\` and new on 2026-09-04. It is not a rule
  about what you may post: you may post a receipt to any active account, and always could
- Confidence is `high`, `medium`, `low` or `none`
- If nothing matches, it is `unmatched` with confidence `none` and flagged for review. **That is not
  a sixth layer**, it is the absence of a match, and it is still recorded as a genuine attempt

### Step 7: Filing

Once a receipt validates successfully and is categorised:
- It's copied, the original untouched, into the client's folder:
  ```
  Clients\[client_folder_name]\IntelliBooks\Receipts\[2026-27]\[invoice date]_[supplier]_[gross].[ext]
  ```
  ~~`Clients/[Client Name]/Tax Year 2026/[Supplier Name]/[receipt files]`~~ **Wrong until 2026-09-04
  and wrong in three ways**: there is no `Tax Year` folder and no per-supplier folder, the tax year
  reads `2026-27`, and the folder name is the record's `client_folder_name` and never the display
  name, sub-step 10d.14. **The supplier and the amount are in the file name instead.** Read off
  `Clients\Test Sole Trader\IntelliBooks\Receipts\2022-23\` on 2026-09-04
- A metadata file (sidecar) is created alongside with all the extracted information, including the category
- The receipt's `filed_path` is set in the database, this is what marks it as genuinely, finally done, and it's what protects it from ever being wrongly filed a second time

If validation fails, needs review, or looks like a possible duplicate:
- A copy is placed in `Intellibills\Review\`, alongside a `.review.json` sidecar saying why.
  ~~the client's Review folder~~ **Corrected 2026-09-04: the Review folder is one folder under
  `Intellibills\`, not one per client under `Clients\`**
- This is not necessarily the end of the road for that receipt, see "Automatic Retry & Manual Resolution" below
- Every retry attempt creates its own numbered copy in the Review folder (e.g. `receipt.jpg`, `receipt-2.jpg`), rather than overwriting the previous one, so don't be surprised to see more than one copy of the same underlying document there if it's been retried a few times

### Step 8: Automatic Retry & Manual Resolution

This is new since the original version of this system, and it changes what "Failed Processing" and "Needs Review" actually mean day to day.

**Automatic retry on a code fix.** Every time the code is updated and the app restarts, it automatically retries every currently failed or needs_review receipt exactly once against the new code. If the fix resolves the underlying problem, the receipt gets categorised and filed properly with no resend and no manual step. If it still doesn't resolve, it's left as-is until the next fix ships. Receipts sourced from email are not moved between mailbox folders by this process, only the database status changes and (for anything other than `ok`) a fresh copy lands in the Review folder.

**The retry limit.** A receipt doesn't get retried forever. If it's still stuck as `failed` or `needs_review` after 7 days (measured from when it first arrived, not how many code updates happened in that time), it moves to a new status, `retry_exhausted`, and the automatic retry stops trying it. That doesn't mean it's abandoned, it's exactly the kind of receipt `resolve_receipt.py` exists for, it just means the system has stopped guessing that a future code fix will solve it on its own, and it's waiting for a person to look at it directly.

**Automatic retry on a transient error.** Separately, if extraction fails purely because of an API error rather than a genuine problem with the code or the document, the system retries it a couple of times within the same run before giving up.

**Manual resolution via `resolve_receipt.py`.** For receipts that a code fix genuinely can't resolve, wrong or missing data on the receipt itself, or a possible duplicate that needs a human decision, this script is the supported way to fix it:
- Shows the current extracted values and why it's flagged
- Lets you supply corrected values for any field
- Categorises and files it properly if the correction validates, exactly like every other path
- For a possible duplicate, lets you confirm either "yes, genuine duplicate, discard" or "no, separate transaction, file it"
- Records the correction as a new, clearly-labelled entry in the audit trail, it never overwrites or deletes the earlier attempt

See "Helper Scripts" below for usage.

### Step 9: Database Storage

Everything is recorded in an SQLite database at `config.DB_PATH`, which is
`C:\Intellibills\db\receipts.db` unless `INTELLIBILLS_UNSYNCED_ROOT` says otherwise.
~~`data/receipts.db`~~ **Corrected 2026-09-04.**

**Ten tables.** This guide named five. ~~Eleven~~ **`email_delta` was removed on 2026-09-04, item
159; a database created before that date still holds it, empty.**
- **receipts** — one row per receipt file: who sent it, which of the four sources, where both copies
  are, current status, whether it is genuinely filed, whether it is locked for manual resolution, and
  what it might be a duplicate of
- **extractions** — AI extraction results, one row per attempt, never overwritten
- **categorisations** — the suggestion and, beside it rather than over it, any correction
- **statements** — **PHV platform statements: uber, bolt, freenow.** ~~bank statements and similar
  documents~~ **Wrong until 2026-09-04, and worth being clear about: nothing in this system reads a
  bank statement.** Bank transactions are imported in IntelliBooks Desktop
- **processed_attachments** — duplicate prevention log
- **resolution_events** — the audit trail, one row per resolution whatever the entry point
- **email_alerts** — one row per alert sent, which is what stops a second alert for the same email
- **categorisations_client_vendors**, **categorisations_firm_vendors**,
  **categorisations_client_rules** — layers 1, 2 and 0 of the categoriser

Current status values on a receipt: `pending`, `ok`, `failed`, `needs_review`, `possible_duplicate`, `retry_exhausted` (stuck for more than 7 days, automatic retry has given up, needs a person to look at it), `discarded` (confirmed as a genuine duplicate and deliberately not filed).

---

## Where Data Really Lives

This is worth being precise about, since it's easy to assume the mailbox folders or the Review folder are where the system "keeps track" of things. They aren't.

**The database is the only source of truth.** Every script, and the app itself, decides what needs attention purely by checking the `status` column in the database. Nothing reads the Review folder, the "Needs Review" mailbox folder, or any other folder to work out what still needs doing.

**The folders are one-way output, for you to look at, not for the system to read.** The app writes a copy of the receipt and its data there so you have something to open, but it never reads it back. That also means:
- Moving, renaming, or deleting a file in the Review folder has no effect on the receipt's actual status.
- A receipt that's been retried several times will have several numbered copies sitting in the Review folder, one per attempt, that's expected, not a fault.
- A folder-sourced receipt (uploaded via the Receipt Inbox, not email) will never appear in an email mailbox folder, because it was never an email. Check the disk Review folder for those instead.
- An email that landed in "Needs Review" (or "Failed Processing", etc.) stays in that mailbox folder even after the receipt is later corrected and filed properly, fixing it doesn't move the original email anywhere. Treat the mailbox folders as a log of what happened on arrival, not a live queue of what's still outstanding, the database is what's current. This is worth revisiting once the planned dashboard exists and gives a reliable at-a-glance view of what genuinely needs attention; until then, always check status in the database, not by counting what's sitting in a mailbox folder.

If you want to know, right now, what genuinely needs attention: `python query_receipts.py` or `python view_receipts.py`, not a folder listing.

### Files
- **Original receipts:** `Intellibills\Documents\[client_id]\[year]\[month]\[receipt_id]_filename`
  (never moved or deleted)
- **Filed receipts:** `Clients\[client_folder_name]\IntelliBooks\Receipts\[2026-27]\[date]_[supplier]_[gross].[ext]`
- **Review folder:** `Intellibills\Review\` (a copy per attempt, plus a `.review.json` sidecar for each)
- **Metadata sidecars:** beside the receipt. **A filed receipt's sidecar appends the extension**,
  `x.pdf.json`; **an inbox sidecar replaces it**, `x.json`. Two conventions and both are deliberate
- **All four paths above were wrong in this guide until 2026-09-04**

### Logs
All of these live under `config.LOGS_DIR`, which is `C:\Intellibills\logs` unless
`INTELLIBILLS_UNSYNCED_ROOT` says otherwise, and deliberately outside OneDrive.
- **Processing log:** `runs.ndjson` — a record of each run
- **Receipt events:** `receipt_events_[firm_id].ndjson` — the timeline for each receipt, with
  `receipt_events_UNATTRIBUTED.ndjson` for an event that belongs to no firm
- **Per entry point:** `run.log` for the pipeline, plus `resolve.log`, `discard.log`, `console.log`
- **Status:** `Intellibills\pipeline-status.json` — last run time, error messages, stats. **This one
  is in OneDrive, not in the logs folder**, because IntelliBooks Desktop reads it

Note: log files are no longer tracked in git, they're runtime output, not source, so they won't show up as "changes" when checking the state of the code.

---

## Client Assignment

**This whole section was rewritten on 2026-09-04. Step 10d replaced everything it used to say.**

**There is one client registry and it is `Intellibills\clients.json`, keyed on `client_id`**, sub-step
10d.3. IntelliBooks Desktop writes it; the pipeline only reads it, and re-reads it whenever its
modification time changes. ~~`IntelliBooks/clients.csv`~~ **Gone.** ~~a `client_code` from the
sidecar~~ **Gone: there is no client code anywhere, in either product.**

**By email:** the sender's address is looked up against every address in each client record's
`emails` array. One client can have several addresses.

**From the Receipt Inbox:** the `client_id` comes from the item's own sidecar, not from the folder it
sat in.

**When the client cannot be resolved:** `client_id` is `UNKNOWN`, which is a reserved id and not a
client, and `firm_id` is `FIRM001`, which is `config.DEFAULT_FIRM_ID` and the only source for it. The
receipt is still recorded and can be assigned later in IntelliBooks Desktop.

**~~A typo or unregistered code files quietly under a folder named after the raw code.~~ That
behaviour is gone**, and it is worth knowing it has gone because it was the thing to check first when
a receipt seemed to have vanished. **A receipt whose client has no `client_folder_name` is not filed
at all**: it is held with the reason recorded, rather than being filed somewhere nobody would look.

**Client folder names come from `client_folder_name` on the record and never from `client_name`**,
sub-step 10d.14. The display name is freely editable; the folder name is fixed once the folder
exists.

---

## Helper Scripts: Tools for Inspection and Maintenance

**All six root scripts read `config.DB_PATH`. Fixed 2026-09-04, outstanding item 158**: each used to
open `data/receipts.db`, a path amendment 76 removed, **and an sqlite connection to a missing file
succeeds and creates an empty one**, so each reported no receipts rather than saying it could not find
any. If you ran one of these before 2026-09-04 and it showed nothing, that is why.

These scripts help you inspect, debug, and maintain the system. None of them modify the main database unless you explicitly ask them to, apart from `resolve_receipt.py`, which does so deliberately and always appends rather than overwrites.

### Inspection Scripts (Read-Only)

**`query_receipts.py`** — Show all receipts and their status
```bash
python query_receipts.py
```
Shows:
- Receipt ID (shortened)
- Filename
- Source: `email`, `phone`, `desktop` or `other`
- Email sender and subject (for email receipts)
- Current status (pending, ok, needs_review, failed, possible_duplicate, retry_exhausted, discarded)
- When it was created

**`view_receipts.py`** — Show detailed extraction results
```bash
python view_receipts.py
```
Shows:
- All extraction attempts for each receipt
- Supplier name, invoice date, amounts
- Validation status and any validation errors
- What was extracted vs. what failed

**`schema_info.py`** — Show database table structure
```bash
python schema_info.py
```
Displays:
- Table names
- Column names and types
- Which columns are primary keys

**`check_client_match.py`** — Verify client ID assignments
```bash
python check_client_match.py
```
Shows:
- Which client was assigned to each receipt
- Who the email was from
- Helps debug if wrong client is being assigned

**`check_ids.py`** — Check for ID mismatches and orphaned records
```bash
python check_ids.py
```
Validates:
- Every extraction has a corresponding receipt
- No duplicate receipt IDs
- Every categorisation points to a real extraction (not a dangling reference)
- Data integrity issues generally

### Resolution Scripts

**`resolve_receipt.py`** — Correct and file a needs_review, failed, or possible_duplicate receipt
```bash
python resolve_receipt.py <receipt_id>
python resolve_receipt.py <receipt_id> --supplier "Correct Name" --gross 104.99
python resolve_receipt.py <receipt_id> --duplicate-decision file   # or "discard"
```
Purpose:
- Shows the receipt's current extracted data and why it was flagged
- Lets you supply corrected values for any field, blank keeps the existing value
- Re-validates, categorises, and files it properly if the correction now passes
- For a possible duplicate, lets you confirm it's genuine and separate, or a true duplicate to discard
- Locks the receipt while it's being worked on, so it can't clash with an automatic retry happening at the same time

### Maintenance Scripts

**`import_vendor_csv.py`** — Load vendor/supplier mappings
```bash
python import_vendor_csv.py path/to/vendors.csv <client_id>
python import_vendor_csv.py vendors.csv Client_002
```
Purpose:
- Import a pre-prepared CSV of supplier → GL code mappings
- Maps specific suppliers to accounting categories for one client
- CSV format: vendor_code, vendor_name, detail, nominal_code, account_name
- Useful for batch-loading categorisations

**`seed_client_vendors.py`** — Populate vendor mappings from existing receipts
```bash
python seed_client_vendors.py <csv_path> <client_id>
python seed_client_vendors.py 'Test Receipts/transactions_sample.csv' Client_002
```
Purpose:
- Scans all successfully processed receipts
- Extracts supplier names and creates vendor records
- Builds a foundation of suppliers you've already seen
- Useful after initial receipt processing to pre-populate the vendor list

**`regenerate_vendor_codes.py`** — Rebuild normalized vendor codes
```bash
python regenerate_vendor_codes.py
```
Purpose:
- Recalculates vendor codes (normalised merchant identifiers)
- Removes noise words and location codes for consistency
- Re-runs the categorisation matching logic
- Useful if you've updated vendor mappings and want to re-categorise old receipts

**`discard_receipt.py`** — mark a receipt as a confirmed duplicate and deliberately not filed
```bash
python discard_receipt.py <receipt_id>
```
Sets the status to `discarded` and records why. **Not in this guide until 2026-09-04.**

**`retroactive_categorise.py`** — categorise receipts filed before categorisation ran on every path
```bash
python retroactive_categorise.py
```
**Not in this guide until 2026-09-04.**

**`export_bookkeeping.py`** — Export data for accounting software
```bash
python export_bookkeeping.py
```
Purpose:
- Exports all filed receipts with their GL codes
- Creates a file suitable for importing into accounting software
- Includes supplier, amount, date, and category

### Setup and Auth Scripts

**`setup_auth.py`** — Verify email access is working
```bash
python setup_auth.py
```
Purpose:
- Tests that the system can successfully connect to and read emails from the capture mailbox
- Must be run once before starting the main app
- Shows how many emails are in the inbox
- Helps diagnose permission or authentication issues

---

## The Main Application

**`app.py`** — The heart of the system

This is the main process that runs continuously:
- Every 5 minutes, it wakes up and checks for new receipts
- Processes folder uploads (files in Receipt Inbox)
- Fetches new emails from the capture mailbox
- Retries any failed/needs_review receipts that haven't been tried under the current code yet
- Extracts, validates, categorises, and files each receipt
- Logs everything that happens

Start it with:
```bash
python app.py
```

The app runs in a loop and never stops unless you manually stop it. It uses a lock file to prevent multiple instances from running at the same time. When you're testing a code change, stop the running instance fully (and confirm it's actually stopped) before restarting, since a change only takes effect once the process restarts, an already-running instance keeps using whatever code was loaded when it started, editing files on disk doesn't affect it.

If you see a warning at startup about "uncommitted changes", it means the code on disk differs from what's actually been committed to git, worth committing first if you want the automatic retry to correctly recognise that something's changed.

---

## How to Use: Common Tasks

### Check on Recent Processing
```bash
python query_receipts.py
```
See recent receipts and their status.

### See What Needs Review
```bash
python view_receipts.py
```
Look for status `needs_review`, `failed`, `possible_duplicate`, or `retry_exhausted` to find receipts that need attention. `retry_exhausted` in particular won't fix itself, automatic retry has already given up on it, it needs `resolve_receipt.py`. Remember, this is the only reliable way to check, the Review folder can lag behind or hold multiple copies from repeated retries.

### Correct and File a Receipt That Needs Review
```bash
python resolve_receipt.py <receipt_id> --supplier "Correct Name" --gross 104.99
```
See "Resolution Scripts" above.

### Debug a Specific Receipt
Look in the database using `view_receipts.py`, then check:
- The original file: `Intellibills\Documents\[client_id]\[year]\[month]\[receipt_id]_filename`
- The Review folder copy, if any: `Intellibills\Review\[filename(-N)]` plus its `.review.json`

### Add New Supplier Mappings
1. Prepare a CSV with supplier → GL code mappings
2. Run: `python import_vendor_csv.py my_vendors.csv Client_002`
3. **The client ids are whatever is in `Intellibills\clients.json`.** ~~`Client_006`~~ **There is no Client_006: the registry holds `Client_001` to `Client_005` as at 2026-09-04.** Corrected that day

### Re-Categorise Receipts
If you've added new vendor mappings:
```bash
python regenerate_vendor_codes.py
```

### Export for Accounting Software
```bash
python export_bookkeeping.py
```
This creates an export file ready to import into accounting software.

---

## Configuration

Settings are in two places:

**`.env` file** — Secrets (not in git)
```
IMAP_HOST=mail.example.com
IMAP_PORT=993
IMAP_USERNAME=capture@lastingimpact.co.uk
IMAP_PASSWORD=your_password
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o  (optional, defaults to gpt-4o)
POLL_INTERVAL_SECONDS=300  (optional, check for new receipts every 300 seconds)
PREFER_DAYFIRST=1  (optional, 1 = prefer DD/MM date format, 0 = MM/DD)
```

**`clients.json`** — the client registry, in OneDrive
Location: `Intellibills\clients.json`. ~~`IntelliBooks/clients.csv`~~ **Corrected 2026-09-04.**
**Written by IntelliBooks Desktop and only read by the pipeline.** Edit it there, not by hand.

Fields the pipeline reads:
- `client_id` — the key, for example `Client_001`
- `client_name` — display name, freely editable
- `client_folder_name` — the folder under `Clients\`, fixed once that folder exists
- `firm_id` — **`FIRM001`.** ~~usually INTELLITAX~~ **Corrected 2026-09-04.** A record with no
  `firm_id` is refused and the pipeline never sees that client
- `emails` — every address that client sends from, as an array
- `trade` — `PHV_DRIVER`, `UNSPECIFIED` and so on
- `capture_token` — **a credential.** It is what the phone app authenticates with, it is per client
  and revocable, and it must never be published, pasted into a document or committed
- `chart_code` — which published chart the classifier may suggest from, new on 2026-09-04
- `entity_type`, `partners`, `phv`, `vat`, `year_end`, `mtd`, `mtd_basis`, `balance_sheet` — the
  client's own settings, used by IntelliBooks Desktop
- **There is no `client_code` and no `business_type` column.** `trade` is the field

---

## What Happens to Each Receipt

### Timeline Example 1: The Happy Path

**2026-07-22 10:15 AM** — Client sends email to capture@lastingimpact.co.uk with a receipt PDF
↓
**System identifies:** it is from `pdk7@hotmail.co.uk`, which is on `Client_004`'s `emails` array, so the receipt is `Client_004`, Test Sole Trader. **That is the only address on any record as at 2026-09-04**, read off `Intellibills\clients.json`

**Step 1 — Check duplicates:** Not seen before, and nothing matches on supplier/date/amount either ✓

**Step 2 — Save file:** `Intellibills\Documents\Client_004\2026\07\abc123de_receipt.pdf`

**Step 3 — Extract:** OpenAI reads the PDF
- Supplier: Amazon
- Date: 2026-07-22
- Amount: £125.50 (includes £20.92 VAT)

**Step 4 — Validate:** All checks pass ✓ Status: `ok`

**Step 5 — Categorise:** looks up "Amazon" in the vendor mappings
- Found: `7500 Printing, postage and stationery`, a real four-digit master code
- Confidence: high, match source `client`

**Step 6 — File:** copies the receipt to
`Clients\Test Sole Trader\IntelliBooks\Receipts\2026-27\2026-07-22_amazon_125.50.pdf`, `filed_path` set

**Step 7 — Log:** Everything recorded in database and logs

**Result:** Receipt is now filed and ready for bookkeeping export.

### Timeline Example 2: Needs Review, Then Resolved

**2026-07-17** — a receipt is captured but the date cannot be confidently read, extraction returns `needs_review` ("missing supplier_name"). A copy is placed in `Intellibills\Review\`.

**2026-07-24, code fix ships** — Unrelated to this receipt's actual problem, but the app restarts and automatically retries every needs_review/failed receipt once against the new code, this one included. It still comes back `needs_review`, same underlying issue, a new numbered copy appears in the Review folder, and the attempt is logged as an automatic retry, not a fresh receipt.

**Some time later, a human looks at it** — Runs `python resolve_receipt.py <receipt_id> --supplier "Correct Name" --gross 8.00`. The correction passes validation, gets categorised, and is filed properly. `filed_path` is now set, so it's protected against ever being wrongly treated as a duplicate again, and it no longer shows up in `needs_review`.

**Result:** Receipt is filed and categorised, and the full history of every attempt, automatic and manual, is preserved in the database for audit.

---

## Troubleshooting

### Email receipts not arriving?
- Check `.env` has correct IMAP credentials
- Verify mailbox address is correct (capture@lastingimpact.co.uk)
- Run `python setup_auth.py` to test connection
- Check the logs under `config.LOGS_DIR`, `C:\Intellibills\logs` by default

### Receipts marked as "needs_review" or "failed"?
- Run `python view_receipts.py` to see what's wrong, and how many times it's already been attempted
- Common issues:
  - Date can't be parsed (wrong format)
  - Supplier name missing
  - VAT doesn't add up to gross amount
  - A genuine code bug, in which case shipping the fix and restarting the app will clear it automatically, no action needed on the receipt itself
- To fix it directly: use `python resolve_receipt.py <receipt_id>` with corrected values, this is the supported way, not editing the database by hand
- A client resend now works for genuine failures too, it's no longer wrongly blocked as a duplicate the way it used to be

### Receipt marked "possible_duplicate"?
- Run `python resolve_receipt.py <receipt_id> --duplicate-decision file` if it's genuinely a separate transaction, or `--duplicate-decision discard` if it really is the same one already filed

### Can't find a receipt that should need review?
- Check the database first (`python view_receipts.py`), not a folder, the folders are just a convenience copy and can lag behind or hold several copies from repeated retries
- If it arrived through the Receipt Inbox rather than by email, it will never appear in an email mailbox folder. Check `Intellibills\Review\` on disk instead

### Wrong client assigned, or files landing under an unexpected folder name?
- **Open the client in IntelliBooks Desktop and check the Email addresses field**, which writes the
  `emails` array on that client's record in `Intellibills\clients.json`. An address on no record
  resolves to `UNKNOWN`
- **For an inbox item, the client comes from the item's sidecar**, so check the sidecar's `client_id`
  rather than the folder the file was in
- **Check the client has a `client_folder_name`.** Without one the receipt is held rather than filed,
  and the reason is recorded
- ~~An unregistered or mistyped `client_code` files under a folder named after the raw code~~ **That
  cannot happen any more: there is no client code.** Corrected 2026-09-04
- Fix the record in IntelliBooks Desktop, never by editing `clients.json` by hand, then re-process

### Can't find a filed receipt?
- Check the folder: `Clients\[client_folder_name]\IntelliBooks\Receipts\[2026-27]\`, and the file
  name carries the date, the supplier and the amount
- Or query the database: `python query_receipts.py | grep filename_part`

---

## For Developers: System Architecture

### Core Components

**Intake Layer** (`worker/intake/`)
- `folder_reader.py` — Scans Receipt Inbox folder for new files and sidecars

**Email Layer** (`worker/email/`)
- `reader.py` — Fetches emails from IMAP, extracts attachments

**Extraction Layer** (`worker/extraction/`)
- `openai_vision.py` — Sends images to OpenAI Vision API, including the reference number and time fields
- `base.py` — Interface for swappable extractors (for future alternatives)
- `retry_helper.py` — Wraps extraction with a short retry on transient API errors

**Validation Layer** (`worker/validation/`)
- `rules.py` — Checks extracted data for consistency and completeness

**Categorisation Layer** (`worker/categorisation/`)
- `engine.py` — **six layers, 0 to 5**: rules 0, client 1, firm 2, fuzzy client 3, fuzzy firm 4,
  AI 5. ~~Rules → Client lookup → Firm lookup → Fuzzy → AI → Unmatched~~ **Corrected 2026-09-04:
  fuzzy is two layers and unmatched is not a layer**
- `chart.py` — **the client's published chart, read from `Intellibills\Charts\`**, filtered to the
  accounts marked `classifier_eligible`. ~~`coa.py` — Chart of Accounts / GL code reference~~
  **Deleted 2026-09-04: its 21, 15 and 7 hardcoded codes belonged to no chart in the library**

**Database Layer** (`worker/database/`)
- `repository.py` — All database access and queries, including receipt locking and the version-gated retry query
- `schema.py` — Database table definitions

**Filing Layer** (`worker/filing.py`)
- Copies (never moves) receipts to the Clients folder or Review folder with proper naming and organisation

**Shared Pipeline** (`worker/extraction_pipeline.py`)
- `process_extraction_result()` is the single function that does validate → semantic-duplicate-check → categorise → file for every path: fresh email intake, fresh folder intake, and automatic retry. This exists specifically to prevent the class of bug where one intake path has a fix the other one is missing, a real bug that happened before this was consolidated. Any future change to this logic should go into this one function, not be reimplemented separately per path.

### Data Flow

```
Receipt arrives (email or folder) OR retry candidate found (auto-retry)
    ↓
Duplicate prevention check (only blocks against genuinely filed receipts)
    ↓
Save original file (new intake only)
    ↓
Extract data (OpenAI Vision, with short transient-error retry)
    ↓
Validate (gross ≈ net + VAT, dates, required fields)
    ↓
Semantic duplicate check (supplier + date + amount, ref/time tiebreakers)
    ↓
Categorise (six layers, 0 to 5), always attempted, never skipped
    ↓
File to disk (if ok) OR Review folder (if needs_review/failed/possible_duplicate)
    ↓
Log everything (database + event log)
```

### Automatic Retry (`app.py`, `_retry_failed_receipts`)

Every extraction attempt is tagged with `pipeline_version`, the git commit short-hash running at the time. On every poll, the app compares a receipt's most recent attempt against the currently running version, if it differs (not "is older than", hashes aren't ordered, so this is a straightforward "has it changed" check, not a numeric comparison), it's retried once through the same shared pipeline, unless it's been stuck in failed/needs_review for more than `AUTO_RETRY_MAX_AGE_DAYS` (7, measured from `receipts.created_at`), in which case it's transitioned to `retry_exhausted` instead and left for manual resolution. Receipts are locked (`receipts.locked_at`) while being worked on by either the auto-retry or `resolve_receipt.py`, with a 60-minute staleness allowance so a crashed process can't permanently block a receipt from ever being retried again.

### Append-Only Design

The database is append-only:
- Receipts are never deleted
- Extractions are never modified; new attempts create new rows, including automatic retries and manual corrections
- Validation notes are appended, never rewritten
- This creates a complete audit trail

---

## Key Rules

1. **No Data Loss** — Original files never deleted or moved, every step is logged
2. **No Assumptions** — If something is uncertain, mark `needs_review` or `possible_duplicate`, don't guess
3. **Deduplication** — Only genuinely filed receipts block a resend; ambiguous matches go to a human, not an automatic guess
4. **Traceability** — Every receipt has a unique ID and a timestamped event log, including every automatic retry and manual correction
5. **Client Tracking** — Always know which client a receipt belongs to
6. **One Pipeline** — Every intake path shares the same validate/categorise/file logic, so a fix applied once applies everywhere

---

## Future Enhancements

Receipt Capture is designed with the cloud in mind:
- Database schema supports multi-firm (`firm_id` already present)
- Extraction engine is swappable (can replace OpenAI with another service)
- File storage is abstracted (can move to S3 or similar)
- Validation rules are configurable
- Categorisation engine is pluggable

Cloud version will:
- Replace IMAP with Microsoft Graph API (for Office 365)
- Replace local file storage with S3
- Replace SQLite with cloud database
- Add async queue processing for higher scale
- Keep the same data model and validation logic

**Planned, not yet built:**
- A dashboard showing system status, the Needs Review/Possible Duplicate queue with links straight into the resolve tool, and OpenAI credit/balance monitoring. Logged in the Automation & AI Backlog.

---

## Summary

Receipt Capture is a complete automated receipt processing system:
- **Intake:** Email and folder uploads
- **Extraction:** AI reads documents (OpenAI Vision), with a short retry on transient errors
- **Validation:** Checks that data makes sense
- **Duplicate handling:** Blocks only genuine repeats, flags ambiguous ones for a quick human check
- **Categorisation:** Always attempted, assigns GL codes for bookkeeping
- **Filing:** Stores receipts in organised folders, originals never touched
- **Automatic recovery:** Failed/needs_review receipts retry themselves once a fix ships, or transiently within the same run, up to a 7-day limit before they're left solely for manual resolution
- **Manual resolution:** One supported tool, `resolve_receipt.py`, for anything a code fix can't solve
- **Audit Trail:** Everything is logged and never deleted

It's designed to be reliable, traceable, and extensible to the cloud.

# Receipt Capture — Plain English Guide

## What Is Receipt Capture?

Receipt Capture is an automated system that collects receipts from multiple sources, extracts the key financial information using AI, validates that information, and stores everything with a complete audit trail. It's designed to handle the entire receipt intake workflow for an accounting firm.

Think of it like this: receipts arrive from clients via email or file upload, the system automatically reads them, pulls out the numbers (supplier name, invoice date, amounts), checks that the numbers make sense, and files them in the right place. Every step is recorded so you always know what happened to each receipt.

---

## How It Works: The Complete Flow

### Step 1: Receipt Arrival

Receipts can arrive in two ways:

**A) Email Attachments**
- Clients email receipts to `capture@lastingimpact.co.uk`
- The system checks the sender's email address against a client list
- Automatically assigns the receipt to the correct client based on who sent it
- Supported file types: PDF, JPG, PNG, GIF, WebP, TIFF, BMP

**B) Folder Upload**
- Files can be placed in the Receipt Inbox folder (shared network drive)
- The sender includes a sidecar file (metadata file) that specifies the client code
- The system picks up these files every 5 minutes

### Step 2: Duplicate Prevention

Before processing, the system checks:
- Has this exact email and attachment been processed before? (message ID + attachment ID)
- Is this the same file that arrived via a different email? (file hash matching)
- Is this a duplicate of an existing receipt in the database? (same supplier, same date, same amount)

If a duplicate is found, the receipt is marked as a duplicate and not processed again.

### Step 3: File Storage

The original receipt file is saved locally to disk in a date-based folder structure:
```
data/files/2026/07/22/[receipt_id]_original_filename.pdf
```

Files are never deleted or overwritten. This ensures you always have the original document.

### Step 4: AI Extraction

OpenAI's Vision API reads the receipt image/PDF and extracts:
- Supplier name (who issued the receipt)
- Invoice date (when was it issued)
- Net amount (price before tax)
- VAT amount (tax charged)
- Gross amount (total price)
- Currency (usually GBP)

The full response from OpenAI is also stored for audit purposes.

### Step 5: Validation

The system checks that the extracted data makes sense:
- ✓ Gross amount is present
- ✓ Supplier name is present
- ✓ Date is in valid format (YYYY-MM-DD)
- ✓ Math checks out: net + VAT ≈ gross (with ±£0.02 tolerance)

**Outcomes:**
- `ok` — All validations pass, receipt is ready
- `needs_review` — Data is present but something doesn't match (e.g., VAT mismatch)
- `failed` — Required data is missing or extraction error occurred

### Step 6: Categorisation (Optional)

If the receipt passes validation, the system attempts to categorise it:
- Looks up the supplier in stored vendor mappings (by client or firm-wide)
- Assigns a GL code (accounting category) for bookkeeping
- Confidence score shows how sure the match is
- If no match found or confidence is low, marks for manual review

### Step 7: Filing

Once a receipt validates successfully:
- It's moved to the Clients folder with an organised folder structure:
  ```
  Clients/[Client Name]/Tax Year 2026/[Supplier Name]/[receipt files]
  ```
- A metadata file (sidecar) is created alongside with all the extracted information
- Status is marked as "filed"

If validation fails or needs review:
- Receipt is moved to the Review folder for manual inspection
- All extracted and sidecar data is preserved for reference

### Step 8: Database Storage

Everything is recorded in an SQLite database (`data/receipts.db`):
- **receipts** — One entry per receipt file (who sent it, where it is, current status)
- **extractions** — AI extraction results (supplier, amounts, dates)
- **categorisations** — GL code assignments (bookkeeping categories)
- **processed_attachments** — Duplicate prevention log
- **statements** — Separate tracking for bank statements and similar documents

---

## Where Data Lives

### Database
- **Location:** `data/receipts.db` (SQLite)
- **What's stored:** All receipts, extractions, categorisations, processing state
- **Backups:** Automatic daily backups in `IntelliBooks/Backups/` folder
- **Always growing** — Nothing is ever deleted, only updated with new information

### Files
- **Original receipts:** `data/files/YYYY/MM/DD/[receipt_id]_filename`
- **Filed receipts:** `Clients/[Client]/Tax Year YYYY/[Supplier]/[receipt_id]_filename`
- **Review folder:** `Clients/[Client]/Review/[receipt_id]_filename`
- **Metadata sidecars:** Same folder as the receipt with `.json` extension

### Logs
- **Processing log:** `logs/runs.ndjson` — Record of each time the system runs
- **Receipt events:** `logs/receipt_events_[firm_id].ndjson` — Timeline of what happened to each receipt
- **Status:** `pipeline-status.json` — Last run time, error messages, stats

---

## Client Assignment

When a receipt arrives via email, the system looks up the sender's email address in `clients.csv`:

**Example:**
- Paul sends from `pdk7@hotmail.co.uk` → automatically assigned to Client_001, business type PHV_DRIVER
- Intellitax admin sends from `paul.keating@intellitax.co.uk` → automatically assigned to Client_002, business type ACCOUNTANCY
- Unknown sender → defaults to client_id UNKNOWN, can be manually assigned later

The client list is stored in the shared Intellitax OneDrive folder at:
```
IntelliBooks/clients.csv
```

---

## Helper Scripts: Tools for Inspection and Maintenance

These scripts help you inspect, debug, and maintain the system. None of them modify the main database unless you explicitly ask them to.

### Inspection Scripts (Read-Only)

**`query_receipts.py`** — Show all receipts and their status
```bash
python query_receipts.py
```
Shows:
- Receipt ID (shortened)
- Filename
- Source (email or inbox folder)
- Email sender and subject (for email receipts)
- Current status (pending, ok, needs_review, failed)
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
- Data integrity issues

### Maintenance Scripts

**`import_vendor_csv.py`** — Load vendor/supplier mappings
```bash
python import_vendor_csv.py path/to/vendors.csv [client_id]
python import_vendor_csv.py vendors.csv Client_001
```
Purpose:
- Import a pre-prepared CSV of supplier → GL code mappings
- Maps specific suppliers to accounting categories for one client
- CSV format: vendor_code, vendor_name, detail, nominal_code, account_name
- Useful for batch-loading categorisations

**`seed_client_vendors.py`** — Populate vendor mappings from existing receipts
```bash
python seed_client_vendors.py
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
- Extracts, validates, and files each receipt
- Logs everything that happens

Start it with:
```bash
python app.py
```

The app runs in a loop and never stops unless you manually stop it. It uses a lock file to prevent multiple instances from running at the same time.

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
Look for status `needs_review` or `failed` to find receipts that need attention.

### Debug a Specific Receipt
Look in the database using `view_receipts.py`, then check:
- The original file: `data/files/YYYY/MM/DD/[receipt_id]_filename`
- The metadata: `Clients/[Client]/Review/[receipt_id]_filename.json` or `[receipt_id]_filename.json`

### Add New Supplier Mappings
1. Prepare a CSV with supplier → GL code mappings
2. Run: `python import_vendor_csv.py my_vendors.csv Client_001`

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

**`clients.csv`** — Client list (in shared OneDrive)
Location: `IntelliBooks/clients.csv`

Columns:
- `client_id` — Unique identifier (e.g., Client_001)
- `name` — Client's display name
- `email` — Email address to match (for auto-assignment)
- `firm_id` — Which firm this client belongs to (usually INTELLITAX)
- `business_type` — Type of client (PHV_DRIVER, ACCOUNTANCY, etc.)
- `client_code` — Code used in folder intake
- `notes` — Any notes

---

## What Happens to Each Receipt

### Timeline Example

**2026-07-22 10:15 AM** — Client sends email to capture@lastingimpact.co.uk with a receipt PDF
↓
**System identifies:** It's from paul.keating@intellitax.co.uk → Client_002

**Step 1 — Check duplicates:** Not seen before ✓

**Step 2 — Save file:** `data/files/2026/07/22/abc123de_receipt.pdf`

**Step 3 — Extract:** OpenAI reads the PDF
- Supplier: Amazon
- Date: 2026-07-22
- Amount: £125.50 (includes £20.92 VAT)

**Step 4 — Validate:** All checks pass ✓ Status: `ok`

**Step 5 — Categorise:** Looks up "Amazon" in vendor list
- Found: GL code 5050 (Office Supplies)
- Confidence: High

**Step 6 — File:** Moves receipt to
`Clients/Intellitax/Tax Year 2026/Amazon/abc123de_receipt.pdf`

**Step 7 — Log:** Everything recorded in database and logs

**Result:** Receipt is now filed and ready for bookkeeping export.

---

## Troubleshooting

### Email receipts not arriving?
- Check `.env` has correct IMAP credentials
- Verify mailbox address is correct (capture@lastingimpact.co.uk)
- Run `python setup_auth.py` to test connection
- Check logs in `logs/` folder

### Receipts marked as "needs_review"?
- Run `python view_receipts.py` to see what's wrong
- Common issues:
  - Date can't be parsed (wrong format)
  - Supplier name missing
  - VAT doesn't add up to gross amount
- Fix the issue, then manually update the receipt in the database or re-upload

### Wrong client assigned?
- Check `clients.csv` has the correct email/client mapping
- Sender's email may not be in the list (defaults to UNKNOWN)
- Edit `clients.csv` to add the sender's email, then re-process

### Can't find a filed receipt?
- Check the folder structure: `Clients/[Client Name]/Tax Year [YYYY]/[Supplier Name]/`
- Or query the database: `python query_receipts.py | grep filename_part`

---

## For Developers: System Architecture

### Core Components

**Intake Layer** (`worker/intake/`)
- `folder_reader.py` — Scans Receipt Inbox folder for new files and sidecars

**Email Layer** (`worker/email/`)
- `reader.py` — Fetches emails from IMAP, extracts attachments

**Extraction Layer** (`worker/extraction/`)
- `openai_vision.py` — Sends images to OpenAI Vision API
- `base.py` — Interface for swappable extractors (for future alternatives)

**Storage Layer** (`worker/storage/`)
- `store.py` — Saves files to disk in date-based folders

**Validation Layer** (`worker/validation/`)
- `rules.py` — Checks extracted data for consistency and completeness

**Categorisation Layer** (`worker/categorisation/`)
- `engine.py` — 6-layer strategy: Rules → Client lookup → Firm lookup → Fuzzy → AI → Unmatched
- `coa.py` — Chart of Accounts / GL code reference

**Database Layer** (`worker/database/`)
- `repository.py` — All database access and queries
- `schema.py` — Database table definitions

**Filing Layer** (`worker/filing.py`)
- Moves filed receipts to the Clients folder with proper naming and organisation

### Data Flow

```
Receipt arrives (email or folder)
    ↓
Duplicate prevention check
    ↓
Save original file
    ↓
Extract data (OpenAI Vision)
    ↓
Validate (gross ≈ net + VAT, dates, required fields)
    ↓
Categorise (6-layer lookup for GL code)
    ↓
File to disk (if ok) OR mark for review (if issues)
    ↓
Log everything (database + event log)
```

### Append-Only Design

The database is append-only:
- Receipts are never deleted
- Extractions are never modified; new attempts create new rows
- Validation notes are appended, never rewritten
- This creates a complete audit trail

---

## Key Rules

1. **No Data Loss** — Original files never deleted, every step is logged
2. **No Assumptions** — If something is uncertain, mark `needs_review`, don't guess
3. **Deduplication** — Same receipt never processed twice
4. **Traceability** — Every receipt has a unique ID and a timestamped event log
5. **Client Tracking** — Always know which client a receipt belongs to

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

---

## Summary

Receipt Capture is a complete automated receipt processing system:
- **Intake:** Email and folder uploads
- **Extraction:** AI reads documents (OpenAI Vision)
- **Validation:** Checks that data makes sense
- **Categorisation:** Assigns GL codes for bookkeeping
- **Filing:** Stores receipts in organised folders
- **Audit Trail:** Everything is logged and never deleted

It's designed to be reliable, traceable, and extensible to the cloud.

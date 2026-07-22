# Email Attachment Processing — Detailed Micro-Steps

This document shows exactly what happens when a receipt email arrives at `capture@lastingimpact.co.uk`.

## Trigger: `process_once()` runs every 5 minutes

The main app calls `process_once()` which handles all email processing.

---

## Phase 1: Fetch New Emails from IMAP

**Function:** `fetch_new_messages(repo)` — [worker/email/reader.py:22]

### Micro-steps:

1. **Connect to IMAP server**
   - Host: `config.IMAP_HOST` (from .env)
   - Port: `config.IMAP_PORT` (from .env, default 993)
   - Username: `config.IMAP_USERNAME` (from .env)
   - Password: `config.IMAP_PASSWORD` (from .env)

2. **Get last processed UID from database**
   - Query: `repo.get_last_uid()`
   - Returns: The last email UID we've seen (or None if first run)
   - This prevents reprocessing the same emails

3. **Search IMAP inbox**
   - If we have a last UID: search for emails after that UID
   - If first run: fetch ALL emails
   - This gives us a list of message UIDs

4. **Filter for new emails only**
   - Remove UIDs we've already processed
   - Result: only genuinely new messages

5. **For each new message:**
   - Fetch the full email body (RFC822 format)
   - Parse into Python email object
   - Check: does it have attachments? (using `_has_attachments()`)
   - If yes: add to messages list with metadata:
     - `id` — IMAP UID
     - `subject` — Email subject line
     - `from` — Sender's email address (from From: header)
     - `receivedDateTime` — When email arrived
     - `msg` — The parsed email object (for later attachment extraction)

6. **Save last processed UID**
   - Update database: `repo.save_last_uid(last_uid)`
   - Next run will start from this UID

7. **Return messages**
   - List of emails with attachments, ready for processing

---

## Phase 2: Loop Through Each Email

**Location:** app.py line 517-740

```python
for msg in messages:
    # Process each email
```

### For each email message:

**Step A: Extract email metadata**
- `message_id` = IMAP UID
- `subject` = Email subject line (e.g., "Receipt from Amazon")
- `email_from` = Sender's email address (e.g., "paul.keating@intellitax.co.uk")
- `received_at` = Timestamp when email arrived

**Step B: Extract all attachments from this email**
- Call: `fetch_attachments(message_id, msg.get("msg"))`
- Returns: List of attachment objects, each with:
  - `id` — Unique identifier (message_id + filename)
  - `name` — Original filename
  - `contentBytes` — Base64-encoded file data

---

## Phase 3: Loop Through Each Attachment

**Location:** app.py line 523-740

```python
for att in fetch_attachments(message_id, msg.get("msg")):
    # Process each attachment
```

### For each attachment in the email:

**Step 1: Validate file type**
- Get filename: `att.get("name", "unknown")`
- Call: `is_supported(filename)`
- Checks: Is it PDF, JPG, PNG, GIF, WebP, TIFF, or BMP?
- If NO: Skip this attachment
  - Log: "skip unsupported: {filename}"
  - Log event: `action="unsupported_file_type"`
  - Continue to next attachment

**Step 2: Check for attachment-level duplicates**
- Call: `repo.is_duplicate(message_id, att_id)`
- Queries: Have we processed this exact message_id + attachment_id pair before?
- If YES: Skip
  - Log: "skip duplicate: {message_id}/{att_id}"
  - Log event: `action="duplicate_skipped"`, `duplicate_reason="message_id_match"`
  - Continue to next attachment

**Step 3: Calculate file hash**
- Decode attachment: `base64.b64decode(att.get("contentBytes", ""))`
- Hash it: `file_hash = compute_hash(file_data)`
- Purpose: Detect if same file arrived via different email or message

**Step 4: Check for file-level duplicates**
- Call: `repo.find_by_hash(file_hash)`
- Queries: Have we seen this exact file before (by hash)?
- If YES: Skip
  - Log: "hash duplicate of {existing_receipt_id}, skipping"
  - Log event: `action="duplicate_skipped"`, `duplicate_reason="file_hash_match"`
  - Mark in database: `repo.mark_processed(message_id, att_id, file_hash, existing_receipt_id)`
  - Continue to next attachment

---

## Phase 4: CLIENT ASSIGNMENT ← THIS IS WHAT YOU ASKED ABOUT

**Location:** app.py lines 562-565

This is where the system figures out which client sent the receipt.

### Micro-steps:

**Step 4a: Resolve client from sender's email**

```python
client_id, firm_id = repo.resolve_client_id(email_from)
_, _, client_code = repo.resolve_client_info(email_from)
```

This calls: `Repository.resolve_client_id(email_from)` [worker/database/repository.py:68]

**Inside `resolve_client_id()`:**

1. Clean the email address:
   - Strip whitespace: `.strip()`
   - Convert to lowercase: `.lower()`
   - Extract from `Name <email@domain>` format if needed:
     ```python
     if "<" in email and ">" in email:
         email = email.split("<")[1].split(">")[0].strip()
     ```
     Example: `"Paul Keating <pdk7@hotmail.co.uk>"` → `"pdk7@hotmail.co.uk"`

2. Look up in clients dictionary:
   ```python
   client = config.CLIENTS.get(email)
   ```
   - `config.CLIENTS` is loaded from `IntelliBooks/clients.csv`
   - Dictionary: `email_address (lowercase) → client_data`
   - Example: `"paul.keating@intellitax.co.uk" → {client_id: "Client_002", firm_id: "FIRM001", ...}`

3. If found:
   - Return the mapped values:
     - `client_id` — e.g., "Client_002"
     - `firm_id` — e.g., "FIRM001"
     - `client_code` — e.g., "INTELLITAX"

4. If NOT found:
   - Return defaults:
     - `client_id` = "UNKNOWN"
     - `firm_id` = "INTELLITAX"
     - `client_code` = "UNKNOWN"

**Data source:** `IntelliBooks/clients.csv`
```
client_id,name,email,firm_id,business_type,client_code
Client_001,Paul Keating,pdk7@hotmail.co.uk,FIRM001,PHV_DRIVER,PAUL
Client_002,Intellitax,paul.keating@intellitax.co.uk,FIRM001,ACCOUNTANCY,INTELLITAX
```

### Example Scenarios:

**Scenario A: Known client**
- Email from: `paul.keating@intellitax.co.uk`
- Lookup in clients.csv: FOUND
- Result:
  - `client_id` = "Client_002"
  - `firm_id` = "FIRM001"
  - `client_code` = "INTELLITAX"
  - `business_type` = "ACCOUNTANCY"

**Scenario B: Unknown sender**
- Email from: `stranger@example.com`
- Lookup in clients.csv: NOT FOUND
- Result:
  - `client_id` = "UNKNOWN"
  - `firm_id` = "INTELLITAX"
  - `client_code` = "UNKNOWN"
  - `business_type` = "UNSPECIFIED"

---

## Phase 5: Save Receipt to Database

**Location:** app.py lines 568-580

Create a unique receipt ID and save to database:

```python
receipt_id = str(uuid.uuid4())  # Generate unique ID
file_path = save_file(receipt_id, client_code, filename, file_data)  # Save to disk
```

Then save to database:

```python
repo.save_receipt(
    receipt_id=receipt_id,              # Unique ID (UUID)
    message_id=message_id,              # IMAP UID
    email_subject=subject,              # "Receipt from Amazon"
    email_from=email_from,              # "paul.keating@intellitax.co.uk"
    email_received_at=received_at,      # ISO timestamp
    filename=filename,                  # "receipt.pdf"
    file_path=file_path,                # "data/files/2026/07/22/abc123_receipt.pdf"
    file_hash=file_hash,                # SHA256 hash
    firm_id=firm_id,                    # "FIRM001" (from clients.csv)
    client_id=client_id,                # "Client_002" (from clients.csv)
    client_code=client_code,            # "INTELLITAX" (from clients.csv)
)
```

### Database insert (receipts table):
```sql
INSERT INTO receipts (
    receipt_id, firm_id, client_id, client_code, source, message_id, email_subject,
    email_from, email_received_at, filename, file_path, file_hash, status, created_at
) VALUES (...)
```

Status is set to: `"pending"` (not yet extracted)

### Log event:
```python
_log_receipt(receipt_id, message_id, filename, "created", 
             firm_id=firm_id, client_id=client_id, run_id=run_id)
```

Writes to: `logs/receipt_events_[firm_id].ndjson`

---

## Phase 6: File Storage

**Location:** app.py line 565

Call: `save_file(receipt_id, client_code, filename, file_data)`

### What happens:

1. Create date-based folder structure:
   - Current date: `2026-07-22`
   - Folder: `data/files/2026/07/22/`
   - Create if doesn't exist

2. Save file:
   - Filename: `{receipt_id}_{original_filename}`
   - Example: `abc123de-456f-7890-abcd_receipt.pdf`
   - Full path: `data/files/2026/07/22/abc123de-456f-7890-abcd_receipt.pdf`

3. Return file_path for database storage

---

## Phase 7: Extract Data with AI

**Location:** app.py lines 584-585

Call: `extractor.extract(str(file_path), filename)`

This calls: `OpenAIVisionExtractor.extract()` [worker/extraction/openai_vision.py]

### What happens:

1. Read the file from disk
2. Send to OpenAI Vision API with prompt asking for:
   - Supplier name
   - Invoice date
   - Net amount
   - VAT amount
   - Gross amount
   - Currency

3. Parse OpenAI response into structured data:
   ```python
   ExtractionResult(
       supplier_name="Amazon",
       invoice_date="2026-07-22",
       net_amount=104.58,
       vat_amount=20.92,
       gross_amount=125.50,
       currency="GBP",
       engine="openai_vision",
       raw_response="..."
   )
   ```

---

## Phase 8: Validate Extracted Data

**Location:** app.py line 585

Call: `validate(extraction)`

This calls: `validation/rules.py:validate()`

### Validation checks:

1. Gross amount present? ✓ Required
2. Supplier name present? ✓ Required
3. Date valid format (YYYY-MM-DD)? 
4. If net + VAT both present:
   - Check: `gross ≈ net + VAT` (tolerance ±£0.02)

### Validation outcome:

- `status` = "ok" | "needs_review" | "failed"
- `notes` = List of validation errors (if any)

Example:
```
status = "ok"
notes = []
```

Or:

```
status = "needs_review"
notes = ["VAT amount mismatch: expected 20.92, got 20.95"]
```

---

## Phase 9: Check for Semantic Duplicates

**Location:** app.py lines 591-609

Check: Is this the same transaction we've already processed?

### Logic:

1. Do we have supplier_name AND gross_amount?
2. If YES:
   - Do we have invoice_date?
   - If YES: Query for existing (supplier, date, amount) match
   - If NO: Query for existing (supplier, amount) match
3. If found:
   - Mark as `duplicate_reason = "transaction_match"`
   - Log: "transaction duplicate: {new_id} matches {existing_id}"

### Example:

Two receipts arrive:
- Receipt A: Amazon, 2026-07-22, £125.50
- Receipt B: Amazon, 2026-07-22, £125.50 (same transaction, different format)

Receipt B is marked as duplicate of Receipt A.

---

## Phase 10: Save Extraction Result

**Location:** app.py lines 611-625

Save the extraction data to database:

```python
repo.save_extraction(
    extraction_id=str(uuid.uuid4()),
    receipt_id=receipt_id,              # Link to receipt
    engine="openai_vision",
    supplier_name=extraction.supplier_name,
    invoice_date=extraction.invoice_date,
    net_amount=extraction.net_amount,
    vat_amount=extraction.vat_amount,
    gross_amount=extraction.gross_amount,
    currency=extraction.currency,
    raw_response=extraction.raw_response,
    validation_status=validation.status,  # "ok", "needs_review", "failed"
    validation_notes=validation.notes,
)
```

### Database update (receipts table):
```sql
UPDATE receipts SET status = ? WHERE receipt_id = ?
```
Status updated to: `validation.status`

---

## Phase 11: Categorisation (if validation passed)

**Location:** app.py lines 675-700

Only if `validation.status == "ok"`:

Call: `engine.categorise()`

### What it does:

1. Takes supplier name: "Amazon"
2. Takes client_id: "Client_002"
3. Takes business_type: "ACCOUNTANCY"
4. Looks up in vendor tables:
   - Client-specific mappings?
   - Firm-level mappings?
   - Fuzzy match?
5. Returns suggested GL code and account name

### Save result:

```python
repo.save_categorisation(
    categorisation_id=str(uuid.uuid4()),
    receipt_id=receipt_id,
    extraction_id=extraction_id,
    client_id=client_id,
    business_type=categorisation.business_type,
    vendor_code=categorisation.vendor_code,
    suggested_code=categorisation.suggested_code,
    suggested_name=categorisation.suggested_name,
    confidence=categorisation.confidence,
    match_source=categorisation.match_source,  # "rules", "client", "firm", "fuzzy", etc.
    matched_vendor=categorisation.matched_vendor,
    needs_review=categorisation.needs_review,
    categorised_at=datetime.now(timezone.utc).isoformat()
)
```

---

## Phase 12: File Receipt (if validation "ok")

**Location:** app.py lines 650-661

If `validation.status == "ok"`:

1. Get client name:
   ```python
   client_name = config.CLIENTS_BY_CODE.get(client_code, {}).get("client_name", client_code)
   ```

2. Calculate tax year:
   ```python
   tax_year = determine_tax_year(invoice_date)
   ```

3. Create metadata sidecar:
   ```python
   sidecar_payload = make_enriched_sidecar(
       receipt_id=receipt_id,
       source="email",
       client_code=client_code,
       client_name=client_name,
       capture_date=now,
       invoice_date=invoice_date,
       supplier=supplier_name,
       net=net_amount,
       vat=vat_amount,
       gross=gross_amount,
       ...
   )
   ```

4. Move file to permanent location:
   ```python
   dest_path, sidecar_path = file_receipt(
       source_path=file_path,              # From data/files/YYYY/MM/DD/
       client_name=client_name,
       tax_year=tax_year,
       supplier=supplier_name,
       gross=gross_amount,
       filename=filename,
       sidecar_payload=sidecar_payload
   )
   ```

   Destination:
   ```
   Clients/[Client Name]/Tax Year [YYYY]/[Supplier Name]/[receipt_id]_filename.pdf
   Clients/[Client Name]/Tax Year [YYYY]/[Supplier Name]/[receipt_id]_filename.json
   ```

5. Mark filed in database:
   ```python
   repo.mark_receipt_filed(receipt_id, dest_path)
   ```

---

## Phase 13: Route to Review (if validation "needs_review")

**Location:** app.py lines 663-672

If `validation.status == "needs_review"`:

Call: `file_review()`

Moves to:
```
Clients/[Client Name]/Review/[receipt_id]_filename.pdf
Clients/[Client Name]/Review/[receipt_id]_filename.json
```

Sidecar includes all extracted data so reviewer can see what was found and what needs fixing.

---

## Phase 14: Mark as Processed

**Location:** app.py line 740

At the very end:

```python
repo.mark_processed(message_id, att_id, file_hash, receipt_id)
```

Inserts into `processed_attachments` table:

```sql
INSERT INTO processed_attachments 
    (message_id, attachment_id, file_hash, processed_at, receipt_id) 
VALUES (...)
```

This prevents the same email/attachment pair from being processed again.

---

## Summary: Full Timeline for One Email

```
10:00:00 — Email arrives at capture@lastingimpact.co.uk from paul.keating@intellitax.co.uk
           Attachment: receipt.pdf

10:05:00 — System wakes up (process_once runs)
           Connects to IMAP, fetches new emails

10:05:01 — Email found, has attachment
           Check: Is receipt.pdf supported? YES
           Check: Already processed (message_id + attachment_id)? NO
           Check: File hash seen before? NO

10:05:02 — Resolve client from email: paul.keating@intellitax.co.uk
           Lookup in clients.csv: FOUND
           client_id = "Client_002"
           firm_id = "FIRM001"
           business_type = "ACCOUNTANCY"

10:05:03 — Save receipt record to database (status=pending)
           Save file to disk: data/files/2026/07/22/abc123_receipt.pdf

10:05:05 — Extract with OpenAI: Supplier="Amazon", Date="2026-07-22", Gross=125.50

10:05:07 — Validate: Gross present? YES. Supplier? YES. Date valid? YES.
           Status = "ok"

10:05:08 — Check for semantic duplicate: No match found

10:05:09 — Save extraction result to database
           Update receipt status to "ok"

10:05:10 — Categorise: "Amazon" → GL code 5050 (Office Supplies)

10:05:12 — File receipt to permanent location:
           Clients/Intellitax/Tax Year 2026/Amazon/abc123_receipt.pdf
           Clients/Intellitax/Tax Year 2026/Amazon/abc123_receipt.json

10:05:13 — Mark message as processed in database

10:05:14 — Done! Receipt is filed and ready for bookkeeping export
```

---

## Configuration Data Flow

**clients.csv** (IntelliBooks folder) loads at app startup:

```python
def load_clients():
    clients_by_email = {}
    if CLIENTS_CSV.exists():
        with CLIENTS_CSV.open("r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get("email", "").strip().lower()
                client_data = {
                    "client_id": row["client_id"],
                    "firm_id": row["firm_id"],
                    "business_type": row["business_type"],
                    "client_code": row["client_code"],
                    "client_name": row["name"]
                }
                if email:
                    clients_by_email[email] = client_data
    return clients_by_email

CLIENTS = load_clients()  # Global dict: email → client data
```

When email arrives:
1. Extract sender: `email_from = "paul.keating@intellitax.co.uk"`
2. Clean it: `email = email_from.strip().lower()`
3. Look up: `client = CLIENTS.get(email)`
4. If found: Use client_id, firm_id, client_code from clients.csv
5. If not: Default to UNKNOWN, INTELLITAX, UNKNOWN

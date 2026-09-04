# Email Attachment Processing — Detailed Micro-Steps

This document shows what happens when a receipt email arrives at `capture@lastingimpact.co.uk`.

**Reconciled with the code on 2026-09-04, step 10h. It was written on 2026-07-26 and nothing had
updated it since.** What it used to say, so that anyone who has read the old version knows what to
unlearn:

| It said | It is |
|---|---|
| Phase 1 gets `repo.get_last_uid()` and searches for emails after that UID | **There is no incremental fetch.** `fetch_new_messages()` searches `ALL` on every poll and identity comes from the `Message-ID` header. **An IMAP UID addresses the mailbox within one poll and is never a cross-poll key** |
| `message_id` = IMAP UID | `message_id` is the email's own `Message-ID` header, resolved by `_resolve_message_id()` |
| The unresolved firm is `INTELLITAX` | **`config.DEFAULT_FIRM_ID`, which is `FIRM001`**, sub-step 10d.20. `INTELLITAX` had already stopped being any firm's id in the data |
| `client_code` throughout, from `clients.csv` | **There is no client code, anywhere.** Sub-step 10d.23 and Paul's ruling of 2026-09-02. The registry is `Intellibills\clients.json` |
| Thirteen phases pinned to `app.py` line numbers | **Function names, below.** Every one of the thirteen was wrong, because `app.py` has roughly doubled since. **A line number is not a citation: it is a guess with a date on it** |
| Validation, duplicate check, categorisation and filing happen inline in `app.py` | **They are one function, `process_extraction_result()` in `worker\extraction_pipeline.py`**, shared by fresh email intake, fresh inbox intake and the automatic retry |

## Trigger: `process_once()` in `app.py`, once per poll

**`POLL_INTERVAL_SECONDS`, 300 by default.** `process_once()` does these in order, and the order is
load-bearing:

0. `config.reload_clients_if_changed()`, **before anything reads the registry**, sub-step 10d.35
1. `Repository()`, the extractor, and `CategorisationEngine(repo=repo, enable_ai_fallback=False)`.
   **Layer 5, the AI, is off in the pipeline**, so it has never run against a real receipt
2. `_consume_resolution_notes()`, the IntelliBooks Desktop back-feed, design document 12.3.
   **Before the retry pass**, or a receipt a person just resolved gets re-extracted in the same cycle
3. `_retry_failed_receipts()`, the version-gated automatic retry
4. `_file_unfiled_ok_receipts()`
5. `scan_inbox()`, the Receipt Inbox folder
6. `fetch_emails_without_attachments()`, which is where embedded images and the two alerts happen
7. `fetch_new_messages()`, the attachments path this document describes

---

## Phase 1: Fetch New Emails from IMAP

**Function:** `fetch_new_messages(repo)` in `worker\email\reader.py`

### Micro-steps:

1. **Connect to IMAP server**
   - Host: `config.IMAP_HOST` (from .env)
   - Port: `config.IMAP_PORT` (from .env, default 993)
   - Username: `config.IMAP_USERNAME` (from .env)
   - Password: `config.IMAP_PASSWORD` (from .env)

2. **Search the whole inbox**
   - `imap.uid("search", None, "ALL")`. **Every poll, every message.**
   - ~~Get `repo.get_last_uid()` and search for emails after that UID~~ **There is no incremental
     fetch and there is no UID watermark.** The reason is in the function's own docstring: **an IMAP
     UID is only valid for addressing the mailbox within one poll and must not be reused as a
     cross-poll dedup key.** Deduplication is by `Message-ID` header and by file hash instead

3. **For each message**
   - Fetch RFC822, parse it, and test `_has_attachments()`
   - If it has attachments, add it with:
     - `id` — **the email's own `Message-ID` header**, via `_resolve_message_id()`, which falls back
       to a synthesised id built from the UID only when the header is missing. ~~IMAP UID~~
     - `uid` — the IMAP UID, for `fetch`, `copy` and `store` **inside this poll only**
     - `subject`, `from`, `receivedDateTime`, `msg`

4. **Return the list**
   - **Nothing is saved.** ~~`repo.save_last_uid(last_uid)`~~ There is no watermark to save

**Fixed 2026-09-04, outstanding item 159, and it was raised by writing the paragraph above.**
~~`fetch_new_messages(repo)` still takes `repo` and never uses it. `get_last_uid()` and
`save_last_uid()` still exist on the repository, and `email_delta` still holds `last_uid` and
`delta_link`.~~ **All of it is gone**: the unused argument, all four repository accessors including
the two `delta_link` ones from the Microsoft Graph design that was never built, and the
`email_delta` table, which `schema.py` no longer creates. **A database created before 2026-09-04
still holds it, empty.**

---

## Phase 2: Loop Through Each Email

**Where:** `process_once()` in `app.py`

```python
for msg in messages:
    # Process each email
```

### For each email message:

**Step A: Extract email metadata**
- `message_id` = **the email's `Message-ID` header**, not the UID. ~~IMAP UID~~ **Corrected 2026-09-04**, and it matters: the UID is only valid inside one poll, so using it as the key would have made every email new again after a mailbox rebuild
- `subject` = Email subject line (e.g., "Receipt from Amazon")
- `email_from` = Sender's email address (e.g., "Paul Keating <pdk7@hotmail.co.uk>", which is the only address on any client record as at 2026-09-04)
- `received_at` = Timestamp when email arrived

**Step B: Extract all attachments from this email**
- Call: `fetch_attachments(message_id, msg.get("msg"))`
- Returns: List of attachment objects, each with:
  - `id` — Unique identifier (message_id + filename)
  - `name` — Original filename
  - `contentBytes` — Base64-encoded file data

---

## Phase 3: Loop Through Each Attachment

**Where:** `process_once()` in `app.py`

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

**Where:** `process_once()` in `app.py`, calling `Repository.resolve_client_info()`

This is where the system figures out which client sent the receipt.

### Micro-steps:

**Step 4a: Resolve client from sender's email**

```python
client_id, firm_id, client_folder_name = repo.resolve_client_info(email_from)
```

~~`_, _, client_code = repo.resolve_client_info(email_from)`~~ **The third element is
`client_folder_name`, not a client code**, which is what every caller wanted it for: naming the
folder under `Clients\`. `resolve_client_id()` still exists and returns the first two.

**Inside `resolve_client_info()`:**

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
   - **`config.CLIENTS` holds one entry per address in each client record's `emails` array**, built
     by `config.load_clients()` from `Intellibills\clients.json`. ~~loaded from
     `IntelliBooks/clients.csv`~~ **Corrected 2026-09-04.** One client can have several addresses
   - Example, and it is the only address on any record as at 2026-09-04:
     `"pdk7@hotmail.co.uk" → Client_004, Test Sole Trader`

3. If found, return:
     - `client_id` — e.g. `Client_004`
     - `firm_id` — `FIRM001`
     - `client_folder_name` — e.g. `Test Sole Trader`

4. If NOT found, return:
     - `client_id` = `config.UNKNOWN_CLIENT_ID`, `UNKNOWN`. **A recorded conclusion, not a
       fallback**, sub-step 10d.16: the receipt is a review item, it reports, and it is never
       `status = ok`
     - `firm_id` = `config.DEFAULT_FIRM_ID`, **`FIRM001`**. ~~`INTELLITAX`~~ **Corrected by sub-step
       10d.20: that string had already stopped being any firm's id in the data**
     - `client_folder_name` = `""`, **empty rather than "UNKNOWN"**, because an unresolved client
       files nothing into `Clients\` at all, sub-step 10d.18. **A plausible-looking folder name is
       what created `Clients\TESTST\`**

**Data source:** `Intellibills\clients.json`, keyed on `client_id`, written by IntelliBooks Desktop
and only read here:
```json
{"client_id": "Client_004", "client_name": "Test Sole Trader",
 "client_folder_name": "Test Sole Trader", "firm_id": "FIRM001",
 "emails": ["pdk7@hotmail.co.uk"], "trade": "UNSPECIFIED", "chart_code": "SALE_OF_SERVICES"}
```
**No `client_code` and no `business_type` field.** `trade` is the field.

### Example Scenarios:

**Both scenarios rewritten 2026-09-04 and both now use values read out of the registry.**

**Scenario A: known client**
- Email from: `pdk7@hotmail.co.uk`
- Found on `Client_004`'s `emails` array in `Intellibills\clients.json`
- Result:
  - `client_id` = `Client_004`
  - `firm_id` = `FIRM001`
  - `client_folder_name` = `Test Sole Trader`
  - `trade` = `UNSPECIFIED`

**Scenario B: unknown sender**
- Email from: `stranger@example.com`
- On no client record
- Result:
  - `client_id` = `UNKNOWN`, **a recorded conclusion and not a fallback**
  - `firm_id` = `FIRM001`
  - `client_folder_name` = `""`, **so nothing is filed into `Clients\` at all**
  - `trade` = `UNSPECIFIED`
- **An alert is sent once, tracked in `email_alerts`, and the email is moved to
  `INBOX.Unknown Sender`**

---

## Phase 5: Save Receipt to Database

**Where:** `process_once()` in `app.py`, calling `Repository.save_receipt()`

Create a unique receipt ID and save to database:

```python
receipt_id = str(uuid.uuid4())
file_path = save_file(receipt_id, client_id, filename, file_data)
```
~~`save_file(receipt_id, client_code, ...)`~~ **It keys on `client_id`**, sub-step 10d.53.

Then save to database:

```python
repo.save_receipt(
    receipt_id=receipt_id,              # Unique ID (UUID)
    message_id=message_id,              # the email's Message-ID header, not the UID
    email_subject=subject,              # "Receipt from Amazon"
    email_from=email_from,              # "pdk7@hotmail.co.uk\"
    email_received_at=received_at,      # ISO timestamp
    filename=filename,                  # "receipt.pdf"
    file_path=file_path,                # Intellibills\Documents\Client_004\2026\09\...
    file_hash=file_hash,                # SHA256 hash
    firm_id=firm_id,                    # "FIRM001", from clients.json
    client_id=client_id,                # "Client_004", from clients.json
    source=EMAIL_SOURCE,                # "email". One of four, sub-step 10d.40
)
```
~~`client_code=client_code`~~ **Gone.** **And `source` is not optional**: sub-step 10d.17 removed
every keyword default from this method, so **every caller states every value**, because a default
supplied in Python before the SQL is reached is a fallback dressed as a conclusion.

### Database insert (receipts table):
```sql
INSERT INTO receipts (
    receipt_id, firm_id, client_id, source, message_id, email_subject, email_from,
    email_received_at, filename, file_path, file_hash, filed_path, status, created_at
) VALUES (..., 'pending', ...)
```

Status is set to: `"pending"` (not yet extracted)

### Log event:
```python
_log_receipt(receipt_id, message_id, filename, "created", 
             firm_id=firm_id, client_id=client_id, run_id=run_id)
```

Writes to `config.LOGS_DIR / receipt_events_[firm_id].ndjson`, which is
`C:\Intellibills\logs\` by default, with `receipt_events_UNATTRIBUTED.ndjson` for an event that
belongs to no firm.

---

## Phase 6: File Storage

**Where:** `process_once()` in `app.py`, calling `save_file()` in `worker\storage\store.py`

Call: `save_file(receipt_id, client_id, filename, file_data)`

### What happens:

1. Build the folder, **client first, then the arrival year and month, and no day level**:
   - `Intellibills\Documents\Client_004\2026\09\`
   - ~~`data/files/2026/07/22/`~~ **Wrong on all three counts until 2026-09-04:** `data\` was
     removed by amendment 76, the first level is the `client_id` and not a client code, and there
     is no day folder
   - **The year and month are the arrival date, deliberately.** This runs before extraction, so
     there is no invoice date yet, and an arrival date never needs correcting, so **no file in the
     store ever has to move**

2. Save the file as `{receipt_id}_{original_filename}`, and **never overwrite**: an existing
   destination is logged as a warning and left alone

3. Return the path for the database

---

## Phase 7: Extract Data with AI

**Where:** `process_once()` in `app.py`, calling the extractor from `worker\extraction\`

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

**Where:** `validate()` in `worker\validation\rules.py`

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

**Where:** `process_extraction_result()` in `worker\extraction_pipeline.py`

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

**Where:** `process_once()` in `app.py`, calling `Repository.save_extraction()`

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

**Where:** `process_extraction_result()` in `worker\extraction_pipeline.py`

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

**Where:** `process_extraction_result()` in `worker\extraction_pipeline.py`, calling `file_receipt()` in `worker\filing.py`

If `validation.status == "ok"`:

1. Get the client's display name and its folder name, **two different things**:
   ```python
   client = config.CLIENTS_BY_ID.get(client_id) or {}
   client_name = client.get("client_name", "")
   client_folder_name = client.get("client_folder_name")
   ```
   ~~`config.CLIENTS_BY_CODE.get(client_code, ...)`~~ **`CLIENTS_BY_CODE` was deleted with the client
   code.** **`client_name` goes in the sidecar and never into a path**: it is display only and freely
   editable, and the folder is `client_folder_name`, fixed once the folder exists, sub-step 10d.14.
   **A receipt whose client has no `client_folder_name` is not filed at all**, and the reason is
   recorded rather than guessed at

2. Calculate tax year:
   ```python
   tax_year = determine_tax_year(invoice_date)
   ```

3. Create metadata sidecar:
   ```python
   sidecar_payload = make_enriched_sidecar(
       receipt_id=receipt_id,
       source=source,                      # "email" here. One of four, 10d.40
       client_id=client_id,                # ~~client_code=client_code~~
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
   filed_path, sidecar_path = file_receipt(
       file_path,                          # the copy in Intellibills\Documents\
       client_folder_name,                 # ~~client_name~~ 10d.14
       tax_year,
       extraction.supplier_name or "unknown",
       extraction.gross_amount or 0.0,
       filename,
       sidecar_payload
   )
   repo.mark_receipt_filed(receipt_id, filed_path)
   repo.update_receipt_status(receipt_id, "ok")
   ```
   **It copies and never moves**, so the document-store original stays exactly where it was.
   **The destination is
   `Clients\[client_folder_name]\IntelliBooks\Receipts\[tax year]\[date]_[supplier]_[gross].[ext]`**,
   with the sidecar beside it under the same name plus `.json`. **There is no `Tax Year` folder and
   no per-supplier folder**, and the tax year reads `2026-27`. **`mark_receipt_filed()` is what
   makes it genuinely done** and is what protects it from ever being filed twice

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

**Where:** `process_extraction_result()` in `worker\extraction_pipeline.py`, calling `file_review()` in `worker\filing.py`

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

**Where:** `process_once()` in `app.py`, calling `Repository.mark_processed()`

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

10:05:02 — Resolve client from email: pdk7@hotmail.co.uk
           Found on Client_004's emails array in Intellibills\clients.json
           client_id = "Client_004"
           firm_id = "FIRM001"
           trade = "UNSPECIFIED"

10:05:03 — Save receipt record to database (status=pending)
           Save file: Intellibills\Documents\Client_004\2026\09\abc123_receipt.pdf

10:05:05 — Extract with OpenAI: Supplier="Amazon", Date="2026-07-22", Gross=125.50

10:05:07 — Validate: Gross present? YES. Supplier? YES. Date valid? YES.
           Status = "ok"

10:05:08 — Check for semantic duplicate: No match found

10:05:09 — Save extraction result to database
           Update receipt status to "ok"

10:05:10 — Categorise: "Amazon" -> 7500 Printing, postage and stationery
           Layer 1, this client's own mapping, confidence high

10:05:12 — File receipt to the client folder:
           Clients\Test Sole Trader\IntelliBooks\Receipts\2026-27\2026-07-22_amazon_125.50.pdf
           Clients\Test Sole Trader\IntelliBooks\Receipts\2026-27\2026-07-22_amazon_125.50.pdf.json

10:05:13 — Mark message as processed in database

10:05:14 — Done! Receipt is filed and ready for bookkeeping export
```

---

## Configuration Data Flow

**`Intellibills\clients.json`**, read by `config.load_clients()`. ~~clients.csv (IntelliBooks
folder) loads at app startup~~ **Rewritten 2026-09-04: the file, the format and the reload are all
different.**

```python
CLIENTS, CLIENTS_BY_ID = load_clients()
```

**Two indexes, both pointing at the same record**, sub-step 10d.4:
- **`CLIENTS_BY_ID`** is the primary lookup, one entry per client, keyed on `client_id`
- **`CLIENTS`** holds one entry per address in that record's `emails` array, all pointing at the
  same record, **so there is no second index that can disagree with the first**
- ~~`CLIENTS_BY_CODE`~~ **deleted with the client code**
- **A record with no `firm_id` is refused** and the pipeline never sees that client, sub-step 10d.19
- **A duplicate `client_id` is a registry fault**, not a supported arrangement: the last record
  loaded wins and the earlier one is lost silently

**It is re-read, not read once at startup.** `config.reload_clients_if_changed()` runs at the top of
every poll and re-reads whenever the file's modification time moves, sub-step 10d.35. **Before that,
a client registered while the pipeline was running stayed invisible to it until a restart.** A failed
parse keeps what is already in memory and never ends the poll.

When an email arrives:
1. Extract the sender: `email_from = "Paul Keating <pdk7@hotmail.co.uk>"`
2. Clean it: strip, lowercase, and take what is inside the angle brackets
3. Look up: `client = config.CLIENTS.get(email)`
4. If found: use `client_id`, `firm_id` and `client_folder_name`
5. If not: `UNKNOWN`, `FIRM001` and an empty folder name. ~~UNKNOWN, INTELLITAX, UNKNOWN~~

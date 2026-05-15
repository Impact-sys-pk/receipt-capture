# CLAUDE.md — Receipt Capture

## Purpose

This is a local receipt ingestion and extraction system.

It reads receipt emails, extracts structured data via OpenAI Vision, validates, and stores in SQLite with full audit trail.

**Local build is reference.** Cloud version will follow the same data model and processing logic.

---

## Architecture

**Email → File → Extraction → Validation → Categorisation → Database**

1. **Email ingestion** — IMAP from `capture@lastingimpact.co.uk`
2. **File storage** — Original attachments saved locally, date-based folders, never overwritten
3. **Extraction** — OpenAI Vision API (swappable interface)
4. **Validation** — Gross ≈ net + VAT, required fields, valid dates
5. **Categorisation** — 6-layer GL code lookup (see CATEGORISATION.md)
6. **Storage** — SQLite, append-only for extractions, immutable receipts

### Categorisation Engine

Automatic GL code assignment via 6-layer lookup strategy:

1. **Rules** (highest priority) — Condition-based matching on vendor details
2. **Client lookup** — Exact match in client-specific vendor mappings
3. **Firm lookup** — Fallback to firm-level mappings by business_type
4. **Fuzzy matching** — Similarity-based matching (70%+ threshold)
5. **AI suggestion** — LLM-based categorisation (if enabled)
6. **Unmatched** — Marked for manual review

**Key features:**
- Preserves all vendor variants with UUID keys (audit trail)
- Fast lookups via indexes on (client_id, vendor_code)
- Supports custom rules with regex conditions
- Confidence scoring and review flags
- Multi-client and multi-business-type support

**See CATEGORISATION.md for detailed implementation guide.**

---

## Core Rules (Non-Negotiable)

### 1. No Data Loss

- Original files: never deleted, never overwritten
- Extractions: append-only (one receipt can have multiple extraction attempts)
- All operations logged to `data/run.log`

### 2. Duplicate Prevention

**File-level deduplication:**
- Track processed attachments by message_id + attachment_id
- File-hash matching catches exact duplicate files across emails
- Duplicate reason: `message_id_match` (same email) or `file_hash_match` (different email, same file)

**Semantic deduplication:**
- After successful extraction, check for existing receipts with matching (supplier_name, invoice_date, gross_amount)
- Marks as `duplicate_reason: "transaction_match"` but still stores (append-only)
- Allows audit trail of duplicate invoice formats (e.g., invoice + receipt for same transaction)

### 3. Firm & Client Tracking

All receipts include:

- `firm_id` — defaults to `INTELLITAX` (multi-firm ready)
- `client_id` — defaults to `UNKNOWN` (will be assigned manually or via rules)

**Do not assume a receipt belongs to a specific client.** Always store as `UNKNOWN` unless explicitly matched.

### 4. Extraction Results

Each extraction stores:

- Supplier name, invoice date, net/VAT/gross amounts, currency
- Full OpenAI response (raw_response) for debugging
- Validation status: `ok` | `needs_review` | `failed`
- Validation notes (append-only)

**Do not discard failed extractions.** Keep them for analysis and retry.

### 5. Validation Logic

```
Gross amount required
Supplier name required
Date must be valid (YYYY-MM-DD)
If net + VAT present: gross ≈ net + VAT (tolerance ±£0.02)
```

Status assignment:

- `ok` — all validations pass
- `failed` — missing gross or supplier, or extraction error
- `needs_review` — present but invalid (VAT mismatch, etc.)

### 6. Email Polling

- Polls every 5 minutes (configurable)
- Uses IMAP with UID tracking (remembers last processed UID per run)
- Does not modify or delete emails (read-only)
- Supports any IMAP server (currently Krystal.io, cloud-ready)

---

## Database Schema

### receipts

| Field             | Type        | Notes                                      |
| ----------------- | ----------- | ------------------------------------------ |
| receipt_id        | TEXT (UUID) | Primary key, unique per attachment         |
| firm_id           | TEXT        | Defaults to 'INTELLITAX', multi-firm ready |
| client_id         | TEXT        | Defaults to 'UNKNOWN'                      |
| message_id        | TEXT        | Email message ID (for duplicate detection) |
| email_subject     | TEXT        | Subject line                               |
| email_from        | TEXT        | Sender address                             |
| email_received_at | TEXT        | ISO timestamp                              |
| filename          | TEXT        | Original attachment filename               |
| file_path         | TEXT        | Local storage path                         |
| file_hash         | TEXT        | SHA256 hash (dedup)                        |
| status            | TEXT        | pending \| ok \| needs_review \| failed    |
| created_at        | TEXT        | ISO timestamp                              |

### extractions

| Field             | Type        | Notes                           |
| ----------------- | ----------- | ------------------------------- |
| extraction_id     | TEXT (UUID) | Unique per extraction attempt   |
| receipt_id        | TEXT (FK)   | Links to receipts               |
| engine            | TEXT        | openai_vision, etc. (swappable) |
| extracted_at      | TEXT        | ISO timestamp                   |
| supplier_name     | TEXT        | Null if not found               |
| invoice_date      | TEXT        | YYYY-MM-DD, null if not found   |
| net_amount        | REAL        | Null if not found               |
| vat_amount        | REAL        | Null if not found               |
| gross_amount      | REAL        | Null if not found               |
| currency          | TEXT        | Defaults to 'GBP'               |
| raw_response      | TEXT        | Full OpenAI response (audit)    |
| validation_status | TEXT        | ok \| needs_review \| failed    |
| validation_notes  | TEXT        | Comma-separated, append-only    |

### processed_attachments

| Field         | Type      | Notes                        |
| ------------- | --------- | ---------------------------- |
| message_id    | TEXT      | Email ID (composite PK)      |
| attachment_id | TEXT      | Attachment ID (composite PK) |
| file_hash     | TEXT      | For dedup detection          |
| processed_at  | TEXT      | ISO timestamp                |
| receipt_id    | TEXT (FK) | Which receipt was created    |

### email_delta

| Field      | Type      | Notes                              |
| ---------- | --------- | ---------------------------------- |
| key        | TEXT (PK) | `last_uid` (IMAP UID tracking)     |
| value      | TEXT      | IMAP UID value                     |
| updated_at | TEXT      | ISO timestamp                      |

### categorisations_client_vendors

| Field         | Type      | Notes                                      |
| ------------- | --------- | ------------------------------------------ |
| vendor_key    | TEXT (PK) | UUID, unique per variant                   |
| client_id     | TEXT      | Client identifier                          |
| vendor_code   | TEXT      | Normalised merchant code (apcoa, amazon)   |
| vendor_name   | TEXT      | Original vendor name from import           |
| detail        | TEXT      | Additional details (audit trail)           |
| nominal_code  | TEXT      | GL code mapping                            |
| account_name  | TEXT      | GL account name                            |
| times_seen    | INTEGER   | Frequency count                            |
| last_updated  | TEXT      | ISO timestamp                              |

### categorisations_firm_vendors

| Field        | Type      | Notes                                    |
| ------------ | --------- | ---------------------------------------- |
| vendor_key   | TEXT (PK) | UUID, unique per variant                 |
| business_type| TEXT      | PHV_DRIVER, CONTRACTOR, UNSPECIFIED      |
| vendor_code  | TEXT      | Normalised merchant code                 |
| vendor_name  | TEXT      | Original vendor name                     |
| nominal_code | TEXT      | GL code mapping                          |
| account_name | TEXT      | GL account name                          |
| times_seen   | INTEGER   | Frequency count                          |
| last_updated | TEXT      | ISO timestamp                            |

### categorisations_client_rules

| Field             | Type      | Notes                                   |
| ----------------- | --------- | --------------------------------------- |
| rule_id           | TEXT (PK) | UUID, unique rule identifier            |
| client_id         | TEXT      | Which client this rule applies to       |
| rule_name         | TEXT      | Human-readable rule name                |
| priority          | INTEGER   | Execution order (higher = first)        |
| vendor_code       | TEXT      | Filter match (NULL = match any vendor)  |
| condition_type    | TEXT      | contains, exact_match, startswith, regex|
| condition_field   | TEXT      | detail or vendor_code                   |
| condition_value   | TEXT      | Pattern to match                        |
| nominal_code      | TEXT      | GL code if rule matches                 |
| account_name      | TEXT      | GL account name                         |
| created_at        | TEXT      | ISO timestamp                           |

---

## Development Rules

### Extraction Engine

- **Interface**: `BaseExtractor` in `worker/extraction/base.py`
- **Current**: OpenAI Vision (`openai_vision.py`)
- **Swappable**: Implement `extract(file_path, filename) → ExtractionResult`
- **Do not hardcode** OpenAI. Always use the interface.

### Categorisation Engine

- **Location**: `worker/categorisation/engine.py`
- **6-layer architecture**: Rules → Client lookup → Firm lookup → Fuzzy → AI → Unmatched
- **Vendor normalization**: Removes noise words and location codes for consistency
- **UUID keys**: Both client_vendors and firm_vendors use UUID primary keys for variant tracking
- **Rules system**: Supports conditions (contains, exact_match, startswith, regex)
- **See CATEGORISATION.md** for detailed usage and examples

### File Storage

- Never overwrite files
- Date-based folder structure: `data/files/YYYY/MM/DD/`
- Filenames: `{receipt_id}_{original_filename}`
- Supported: PDF, JPG, PNG, GIF, WebP, TIFF, BMP

### Logging

- All actions logged to `data/run.log`
- Log format: `timestamp LEVEL name — message`
- Failures must be visible (ERROR level, not silent)
- Do not log sensitive data (API keys, passwords)

### Configuration

- `.env` for secrets (IMAP credentials, API keys)
- `.env.example` shows required fields
- `.gitignore` excludes `.env`, `data/`
- Required: IMAP_HOST, IMAP_PORT, IMAP_USERNAME, IMAP_PASSWORD
- Required: OPENAI_API_KEY
- Optional: OPENAI_MODEL (default: gpt-4o), POLL_INTERVAL_SECONDS (default: 300)
- No hardcoded credentials in code

---

## Workflow

1. **Email arrives** at `capture@lastingimpact.co.uk`
2. **App polls** every 5 minutes (or on demand)
3. **Attachments extracted** and saved locally
4. **OpenAI Vision** extracts structured data
5. **Validation** rules applied
6. **Results stored** in SQLite (never modified after)
7. **Audit trail** shows all processing steps

If extraction fails → status = `failed`, raw error stored
If validation fails → status = `needs_review`, reason logged
If all pass → status = `ok`, receipt ready

---

## Testing

- Query receipts: `python query_receipts.py` (summary) or `python view_receipts.py` (detail)
- Schema info: `python schema_info.py`
- Manual test: send email with PDF to `capture@lastingimpact.co.uk`, wait 5 min for poll

---

## Future: Cloud Version

- Same database schema (firm_id already present)
- Same extraction logic (swappable engine)
- Same validation rules
- Scale: queue system, async extraction, multi-worker
- Storage: S3 or similar instead of local files
- Auth: OAuth2 for client-facing access

**Do not change local schema without considering cloud migration.**

---

## When to Stop

Do not:

- Modify receipts or extractions after creation
- Delete files without documenting why
- Change validation rules without updating this doc
- Add hardcoded firm or client IDs
- Assume extraction success (always check status)

---

## Important Reminder

This is a **capture and audit system**, not a transformation system.

Your job: read, extract, validate, store. Not: clean, normalize, or assume missing data.

If something is uncertain → mark `needs_review`. Do not guess.

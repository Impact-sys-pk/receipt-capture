# Intellitax Practice Console — Design

**Date:** 2026-07-25
**Status:** Design agreed with Paul. Ready for implementation.
**Supersedes:** `2026-07-25_DASHBOARD_DESIGN.md` (earlier draft in this repo, delete it).

Grounded in a direct read of `app.py`, `resolve_receipt.py`, `worker/database/repository.py`, `worker/database/schema.py`, `worker/extraction_pipeline.py`, `worker/validation/rules.py`, `worker/extraction/base.py`, `worker/extraction/openai_vision.py`, `config.py`, plus `IntelliBooks-Desktop-v3.html` and its `Docs\` folder, at commit on branch `fix/imap-message-id-dedup`.

## How to use this document

A build spec, not a discussion. "Must" means the decision was deliberate; check with Paul before reversing it.

Read `CLAUDE.md` first. Everything here is subject to its rules: no data loss, append-only extractions, no hardcoded firm or client IDs, commit after each logical unit.

**Do not start at section 8.** Sections 3 and 4 are prerequisites and matter more than the console does.

---

## 1. What this is

A local, authenticated web console for practice operations, run alongside the existing pipeline on Paul's machine.

**Module 1, Receipts.** Built now. System status, a queue of receipts needing attention, resolve-and-file, a browse and search view, intake problems, OpenAI spend.

**Module 2, Chart of accounts.** Deferred. Specified in section 13 with its schema reserved so it drops in without reworking module 1.

It is a **sixth component** in the system described by `IntelliBooks-System-Specification.md`, alongside the Capture App, Upload Function, Receipt Pipeline, IntelliBooks Desktop and OneDrive. That specification needs updating accordingly; see section 17.

### 1.1 What it does not do

It does not replace IntelliBooks Desktop, and it does not remove anything from it. Desktop keeps bank transactions, receipt-to-transaction matching, cashbook posting, statement rules, VAT, P&L and HMRC reporting. It also keeps its review-and-file flow (change log item 19), which stays fully working.

Both tools can resolve a receipt. Safety comes from the resolution back-feed contract in section 12, not from removing a capability.

---

## 2. Decisions taken

| Question | Decision | Rationale |
|---|---|---|
| Shape | One app, two modules. Receipts now, chart of accounts later. | Both need the same auth, DB access, client list and conventions. Two separate local web apps would drift. |
| Hosting | Localhost, `127.0.0.1`, built so remote is a config change. | Paul operates it alone initially; a remote admin may be needed at short notice. Documented remote path is Tailscale or Cloudflare Tunnel, never port forwarding. |
| Auth | Required from day one. Session cookie, argon2, roles `admin` and `operator`. | Real client financial data, and every write needs an actor. Retrofitting attribution into an append-only trail is impossible. |
| Data access | One process, server-rendered HTML, importing `Repository` and the resolution service in-process. No JSON API. | One consumer, one machine. Domain layer stays free of web imports so a cloud API can wrap it later unchanged. |
| Framework | Flask plus Jinja2, no JS framework. | Codebase is entirely synchronous. FastAPI's async model adds risk for no gain. |
| Database | One database. CoA tables live in `receipts.db` with a `coa_` prefix. | The receipts module reads the CoA on every categorisation and picker render. Separate files mean `ATTACH` for no benefit. |
| Who resolves receipts | Both the console and IntelliBooks Desktop. Made safe by the back-feed contract. | Respects the agreed Corrections rule while fixing the three defects it now causes. Preserves built work. |
| Review folder | Written by the pipeline, treated as a log. Cleared on resolution by whichever tool resolves. | Matches the decision already taken for mailbox folders. |
| GL correction | In scope, against the Default CoA CSV. | `resolve_receipt.py` cannot override a category today and `repo.update_categorisation()` is never called. The GL code is the field most likely to be wrong. |
| Default CoA | Keep the detailed numbered ledger. Mapping columns for QBO and Xero reserved but empty. | Vendor history already encodes the distinctions and they cannot be recovered once collapsed. Export adapters are phase 2 or 3. |
| Provider switching | Phase 1 only: factory, `extractor.name`, shared post-processing, display current engine. | Phase 2 touches `find_failed_by_version` and the retry cap tested on 2026-07-25, and deserves its own session. |
| Locking for the web UI | No lock on view. Lock only for the submit. Optimistic concurrency via `expected_extraction_id`. | The 60-minute stale window suits a CLI that finishes or crashes, not an operator closing a tab. |
| Browsing | Queue defaults to receipts needing attention. A separate browse page filters all receipts by client, tax year or recent days, with search. | Empty queue means nothing needs attention. Browsing filed receipts needs different filters, notably invoice date rather than capture date. |

---

## 3. Phase 0: bugs to fix before anything else

Each gets its own commit and its own red/green test, following the pattern used for the retry cap on 2026-07-25.

### 3.1 Auto-retry loops every poll when extraction throws (highest priority, costs money)

`_retry_failed_receipts()` is meant to retry each receipt once per `pipeline_version` change. When `extract_with_transient_retry()` raises, control jumps to the bare `except Exception` at line 374, which logs and moves on. `process_extraction_result()` never runs, so `save_extraction()` never runs, so the receipt's latest extraction keeps its **old** `pipeline_version`.

`find_failed_by_version()` compares the latest extraction's version against the current one, so the receipt stays eligible permanently and is retried on **every five-minute poll**, burning three real OpenAI calls each time via the transient-retry helper.

Reproduced live: the same `pipeline_version` retried five times, five minutes apart, for two known-broken test receipts.

**Fix.** In the exception path, save a `failed` extraction row tagged with the current `pipeline_version`, mirroring what a normal failed outcome records:

```python
repo.save_extraction(
    extraction_id=str(uuid.uuid4()),
    receipt_id=receipt_id,
    engine=extractor.name,              # not hardcoded, see 3.8
    supplier_name=None, invoice_date=None,
    net_amount=None, vat_amount=None, gross_amount=None,
    currency="GBP",
    raw_response=str(exc),
    validation_status="failed",
    validation_notes=[f"auto-retry extraction error: {exc}"],
    pipeline_version=pipeline_version,
    update_status=False,                 # see below
)
```

**`update_status=False` is deliberate and needs adding to `save_extraction()`.** That method currently also runs `UPDATE receipts SET status = validation_status`, which would flip a `needs_review` receipt to `failed`. A crashed retry is information about the API, not about the document, and the operator-facing distinction is worth keeping. Default the parameter to `True` so no existing caller changes behaviour.

**Same defect, second branch.** The missing-file branch at line 335 calls `add_validation_note()` and `continue`s without saving an extraction row, so a receipt whose original has gone is reconsidered every poll too. No OpenAI cost, since it never reaches extraction, but it logs a warning every five minutes forever. Same fix: save a `failed` row tagged with the current version.

**This compounds with 3.9.** A declined card makes the extractor raise, so an OpenAI billing problem becomes a five-minute loop making three failing calls each time.

**Test.** Mock the extractor to raise. Run `_retry_failed_receipts()` twice under the same `pipeline_version`. Assert the extractor was called on the first pass and **not** on the second. Add a second test for the missing-file branch.

### 3.2 A corrected value of zero is silently ignored

`resolve_receipt.py` lines 209-216 use `corrections.get(k) or extraction.get(k)`. `0.0` is falsy, so `--vat 0` keeps the wrong extracted VAT. Line 192's `if any([...])` compounds it: `--vat 0` alone fails the truthiness test and drops into interactive mode.

Correcting VAT to 0.00 is routine for zero-rated and exempt supplies, and currently cannot be done.

**Fix.** Key presence, not truthiness, everywhere including the mode-selection guard. Build the corrections dict from arguments that are `is not None`.

**Test.** Correct a non-zero extracted VAT to `0`; assert the stored row has `vat_amount = 0.0`.

### 3.3 Amount corrections are typed inconsistently, and the interactive path crashes

`get_corrections_interactive()` returns `input().strip()`, so strings. The `--flags` path uses `type=float`. `validate()` then does `round(result.net_amount + result.vat_amount, 2)` and `val < 0`, both of which raise `TypeError` on a string. Swallowed by the broad `except` at line 353 and surfaced as a bare "ERROR:".

The T3 test passed on 2026-07-25 because it used the typed flags path.

**Fix.** One coercion function, `parse_corrections`, in the service layer, used by the CLI, the interactive prompts, the web form and the back-feed. Returns field-level errors rather than raising. See 4.2.

**Test.** Pass all amounts as strings; assert coerced floats or field errors, never a `TypeError`.

### 3.4 No actor recorded on a manual correction

A correction records `engine='manual_correction'` and nothing about who made it. With two authenticated console users plus `"desktop"` resolutions arriving via the back-feed, attribution is not optional.

**Fix.** New `resolution_events` table, section 5.1. Every resolution writes one row, whatever the entry point.

### 3.5 Review pair left on disk after resolution

`resolve_receipt.py` has no awareness of `Clients\{Name}\Review\`. Every receipt ever resolved has left its image and `.review.json` behind, so IntelliBooks still shows it as needing review and completing it there files a duplicate.

**Fix.** The resolution service removes the pair on a successful resolve or discard. Local file I/O, no IMAP involved. Log and continue if the files are already gone.

### 3.6 `review_count` over-reports, permanently and cumulatively

`_count_review_items()` (line 89) counts files under `Clients\*\Review\`. Because of 3.5, nothing is ever removed, so the count in `pipeline-status.json` only grows. It happens not to show in IntelliBooks today only because change log item 20 removed that clause from the banner.

**Fix.** Count from `receipts.db` by status, which is the stated source of truth. Fixing 3.5 makes the folder count correct too, but the DB is the right source regardless.

### 3.7 The sidecar writes a nominal code where the books expect a name

`make_enriched_sidecar()` writes `category` as a nominal code, for example `"104"`. IntelliBooks' categories are names with no codes, and `catOptions()` matches on name, so the value matches nothing and the receipt arrives uncategorised.

This reaches the books rather than staying cosmetic, because "Post to cashbook" (IntelliBooks change log item 7) creates a transaction directly from a receipt and copies the category across.

**Fix.** The sidecar carries **both**: `category_code` for the nominal and `category_name` for the desktop-compatible name. Keep the existing `category` key populated with the name for backward compatibility with sidecars already on disk. The IntelliBooks half, preferring `category_name` in `parseSidecar`, is covered by the separate brief in `PROMPT_intellibooks_resolution_backfeed.md`.

Until the Default CoA CSV exists there is no code-to-name mapping, so `category_name` falls back to `account_name` from the vendor mapping, which is what the engine already returns.

### 3.8 `engine="openai_vision"` hardcoded on failure paths

`app.py` around lines 530, 709 and 880 hardcode the engine string when saving a failure row. These would misreport after any provider change. Replace with `extractor.name` from the factory in section 10.

### 3.9 Billing errors indistinguishable from unreadable documents

A quota, authentication or rate-limit failure surfaces as a generic extraction exception, marks the receipt `failed`, routes the email to "Failed Processing", and starts the 7-day `retry_exhausted` clock. So a billing outage silently becomes a pile of receipts that look like bad documents, and they can burn their whole retry window while a card is declined.

**Fix.** `worker/extraction/retry_helper.py` already distinguishes transient errors. Extend it to classify quota, auth and rate-limit errors separately, record the classification in the validation notes, exclude billing-blocked receipts from the `AUTO_RETRY_MAX_AGE_DAYS` clock, and surface them distinctly on the status page: "3 receipts failed because of API billing, not because the document was unreadable."

### 3.10 `processed_today` is mislabelled

`app.py` line 908 writes "receipts created in this run" into a field called `processed_today`. `repo.count_processed_today()` does the real thing and is not wired to it. Fix the status file, and do not let the console inherit the confusion; the console reads the DB.

---

## 4. The resolution service

### 4.1 Layering

```
resolve_receipt.py                 CLI wrapper. All print() and input(). ~100 lines.
console/web.py                     Flask routes. All HTTP.
app.py                             Pipeline. Consumes back-feed notes.
worker/resolution/service.py       Domain logic. No print, no input, no Flask, no IMAP.
```

`worker/resolution/service.py` must not import Flask, `argparse`, or anything under `worker/email/`. That is what makes it reusable by a cloud API later and testable now.

**There are four callers and they must all go through the same functions.** The CLI, the console, the back-feed consumer, and any future API. Three independent implementations of resolution is what caused the divergence this design exists to fix.

### 4.2 Service API

```python
CORRECTABLE_FIELDS = (
    "supplier_name", "invoice_date", "net_amount",
    "vat_amount", "gross_amount", "receipt_ref_number", "receipt_time",
)

@dataclass
class ResolutionView:
    receipt: dict
    extraction: dict                    # latest, the one being corrected
    extraction_history: list[dict]      # all, newest first
    categorisation: dict | None         # may be None; the non-ok path saves none
    resolution_events: list[dict]
    duplicate_of_receipt: dict | None   # when status == 'possible_duplicate'
    duplicate_of_extraction: dict | None
    client_name: str
    business_type: str
    gl_code_options: list[dict]         # from the Default CoA, section 11
    effective_gl_code: str | None       # correction_code if set, else suggested_code
    file_path: str
    is_locked: bool                     # informational only

@dataclass
class Corrections:
    values: dict[str, object]           # only fields explicitly supplied
    gl_nominal_code: str | None = None
    gl_account_name: str | None = None
    gl_correction_reason: str | None = None
    remember_gl_for_supplier: bool = False

@dataclass
class ResolutionOutcome:
    outcome: Literal["filed","discarded","still_invalid","stale",
                     "locked","not_found","error"]
    receipt_id: str
    extraction_id: str | None
    filed_path: str | None
    category_code: str | None
    category_name: str | None
    category_confidence: str | None
    validation_notes: list[str]
    message: str                        # safe to show an operator
    error_detail: str | None            # logs only, never rendered


def get_resolution_view(repo, receipt_id) -> ResolutionView | None:
    """Read-only. Takes no lock. None if the receipt does not exist."""

def parse_corrections(raw: dict) -> tuple[Corrections, dict[str, str]]:
    """Normalise operator input. Returns (corrections, field_errors). Never raises."""

def resolve_receipt(repo, categorisation_engine, receipt_id, corrections,
                    actor, expected_extraction_id=None) -> ResolutionOutcome:
    """Apply corrections, re-validate, categorise, file. Append-only throughout."""

def discard_receipt(repo, receipt_id, reason, actor) -> ResolutionOutcome:
    """Status to 'discarded'. Never deletes the original file or any extraction row."""

def apply_resolution_note(repo, categorisation_engine, note: dict) -> ResolutionOutcome:
    """Back-feed entry point. Validates the note, then calls resolve_receipt or
    discard_receipt with actor='desktop'. Must not reimplement resolution."""
```

`parse_corrections` rules:

- A key absent from `raw`, or `None`, is omitted from `values`.
- An empty string means "clear this field", stored as `None`. Distinct from omission, so an operator can remove a wrongly extracted reference number.
- Amounts coerce to float. Reject thousands separators, currency symbols and more than two decimal places as field errors rather than guessing.
- `invoice_date` must be `YYYY-MM-DD` and a real date. Do not reparse other formats; that is the extractor's job and guessing here would undo the day-first work in `openai_vision.py`.
- Never raises. Bad input becomes a field error.

### 4.3 `resolve_receipt` control flow

Order matters. Commit `b480a7e` fixed a foreign key violation caused by categorising before the extraction row existed. Do not reorder steps 7 and 8.

1. Load receipt. Missing, return `not_found`.
2. Load latest extraction. Missing, return `not_found` with a message saying so.
3. If `expected_extraction_id` is supplied and does not match the latest, return `stale` and write nothing.
4. Acquire the receipt lock. Failure, return `locked`. Everything below in `try/finally` releasing it.
5. Merge corrections over the existing extraction by key presence, not truthiness.
6. Build `ExtractionResult` with `engine="manual_correction"`, run `validate()`. Not ok: `add_validation_note()`, write a `resolution_events` row with outcome `still_invalid`, return. Do not file.
7. Generate `extraction_id`, then `save_extraction()`. The FK from `categorisations` requires the row to exist first.
8. `categorisation_engine.categorise()`, then `save_categorisation()` with the engine's suggestion. Never overwrite `suggested_code` with the operator's value; that is the audit trail.
9. If a GL override was supplied, `update_categorisation()` now, before filing. Section 11.2 explains why.
10. Build the enriched sidecar using the **effective** code and name: the override if present, otherwise the suggestion. Populate `category_code`, `category_name` and legacy `category`.
11. `file_receipt()`, `mark_receipt_filed()`, `update_receipt_status(receipt_id, 'ok')`.
12. Remove the Review pair for this receipt, per 3.5. Log and continue if already gone.
13. If `remember_gl_for_supplier`, `upsert_client_vendor()`. Opt-in only, section 11.3.
14. Write a `resolution_events` row with outcome `filed`.
15. Return `filed`.

Keep a broad `except Exception` logging with `exc_info=True` and returning `error` with `error_detail`. Trade-off accepted: the caller cannot see the traceback, but the web layer never 500s on a Save and the traceback still reaches `data/run.log`.

### 4.4 What the CLI keeps

`argparse`, `show_receipt_state()` rewritten to render a `ResolutionView`, `confirm_duplicated_action()`, `get_corrections_interactive()`, every `print()`. Maps outcomes to exit codes: `filed` and `discarded` are 0, everything else 1.

Existing behaviour must not change. Every command in `RECEIPT_CAPTURE_GUIDE.md` keeps working verbatim, except that zero now works and string amounts no longer crash.

Add `discard_receipt.py` as a thin CLI over `discard_receipt()`. Discarding a `failed` receipt has been done by hand three times now; it deserves a command.

---

## 5. Schema additions

Add to `worker/database/schema.py` inside the existing `executescript`, following the `CREATE TABLE IF NOT EXISTS` pattern, and the `PRAGMA table_info` guard pattern at lines 157-189 for new columns. Do not write a migration framework.

### 5.1 `resolution_events`

```sql
CREATE TABLE IF NOT EXISTS resolution_events (
    event_id            TEXT PRIMARY KEY,
    receipt_id          TEXT NOT NULL,
    extraction_id       TEXT,
    actor               TEXT NOT NULL,      -- console username, or 'desktop'
    source              TEXT NOT NULL,      -- 'console' | 'cli' | 'desktop'
    action              TEXT NOT NULL,      -- 'resolve' | 'discard'
    corrections_json    TEXT,
    gl_override_code    TEXT,
    outcome             TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
);

CREATE INDEX IF NOT EXISTS idx_resolution_events_receipt
    ON resolution_events(receipt_id, created_at);
```

`extraction_id` is nullable, because a `still_invalid` outcome produces no extraction row. **Do not add a foreign key on it**; writing the event row for that outcome would then fail, which is the same class of bug as `b480a7e`.

### 5.2 `console_users`

```sql
CREATE TABLE IF NOT EXISTS console_users (
    user_id         TEXT PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('admin', 'operator')),
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL,
    last_login_at   TEXT
);
```

### 5.3 `extraction_usage`

Separate table so the append-only extraction row is untouched and capture stays optional.

```sql
CREATE TABLE IF NOT EXISTS extraction_usage (
    extraction_id       TEXT PRIMARY KEY,
    engine              TEXT NOT NULL,
    model               TEXT,
    prompt_tokens       INTEGER,
    completion_tokens   INTEGER,
    total_tokens        INTEGER,
    estimated_cost_usd  REAL,
    recorded_at         TEXT NOT NULL,
    FOREIGN KEY (extraction_id) REFERENCES extractions(extraction_id)
);
```

### 5.4 `openai_credit_topups` and `openai_cost_daily`

```sql
CREATE TABLE IF NOT EXISTS openai_credit_topups (
    topup_id        TEXT PRIMARY KEY,
    amount_usd      REAL NOT NULL,
    occurred_on     TEXT NOT NULL,
    note            TEXT,
    recorded_by     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS openai_cost_daily (
    day             TEXT PRIMARY KEY,
    amount_usd      REAL NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'USD',
    fetched_at      TEXT NOT NULL,
    raw_json        TEXT
);
```

### 5.5 `coa_accounts` — reserved for module 2, created now

Created and populated from the Default CoA CSV in phase 1, so the receipts module reads it through the query layer from day one and module 2 enriches the same table with no change to the receipts side.

```sql
CREATE TABLE IF NOT EXISTS coa_accounts (
    account_key     TEXT PRIMARY KEY,   -- UUID
    scope           TEXT NOT NULL,      -- 'default' | 'group' | 'client'
    scope_ref       TEXT,               -- NULL for default, business_type, or client_id
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,      -- assets|liabilities|equity|income|expenses
    hmrc_box        TEXT,
    vat_treatment   TEXT,
    parent_code     TEXT,
    status          TEXT NOT NULL DEFAULT 'active',  -- active|not_adopted|archived
    provenance      TEXT NOT NULL DEFAULT 'default', -- default|group|client|imported
    maps_to_code    TEXT,               -- for archived/merged accounts
    source_ref      TEXT,               -- original name/code when imported
    qbo_detail_type TEXT,               -- reserved, phase 2/3
    xero_tax_type   TEXT,               -- reserved, phase 2/3
    notes           TEXT,
    updated_at      TEXT NOT NULL,
    UNIQUE(scope, scope_ref, code)
);

CREATE INDEX IF NOT EXISTS idx_coa_lookup ON coa_accounts(scope, scope_ref, status);
```

Phase 1 uses only `scope='default'`. The group and client tiers, the four import dispositions and the three statuses are specified in section 13 but not built.

### 5.6 Indexes for the queue and browse pages

None currently exist on `receipts.status`, `receipts.client_id` or `extractions.receipt_id`.

```sql
CREATE INDEX IF NOT EXISTS idx_receipts_status ON receipts(status);
CREATE INDEX IF NOT EXISTS idx_receipts_client_created ON receipts(client_id, created_at);
CREATE INDEX IF NOT EXISTS idx_extractions_receipt ON extractions(receipt_id, extracted_at);
CREATE INDEX IF NOT EXISTS idx_extractions_invoice_date ON extractions(invoice_date);
CREATE INDEX IF NOT EXISTS idx_extractions_supplier ON extractions(supplier_name);
```

Unmeasurable at 26 receipts. Free now, matters at a few thousand.

### 5.7 `clients.csv` gains `entity_type`

New column: `sole_trader | partnership | ltd | llp`, blank permitted. `load_clients()` reads it into the client dict with a default of empty string. Unused by module 1; module 2 needs it, because tax mapping targets depend on legal form, not on client group. A PHV driver can be either.

**`business_type` and `entity_type` are orthogonal and must not be merged.** Group drives the CoA template and the vendor mappings; entity type drives the tax mapping.

---

## 6. Data access and concurrency

WAL is **already enabled** (`schema.py` line 7) and persists in the DB file, so concurrent readers do not block on the worker's writes. Three things still need care.

**6.1 Never share a `Repository` across request threads.** It holds a single `self._conn`, and `sqlite3` connections are not thread-safe by default. Create per request. Do not set `check_same_thread=False` to work around it.

**6.2 Never call `init_db()` per request.** `Repository.__init__` runs the whole schema script plus several `PRAGMA table_info` queries every time. For reads, open a read-only connection:

```python
sqlite3.connect(f"file:{config.DB_PATH}?mode=ro", uri=True, timeout=30.0)
```

Set `row_factory = sqlite3.Row`. For writes, construct a normal `Repository`; that path is correct and infrequent.

**6.3 No SQL in route functions.** Add read methods to `Repository` or to `console/queries.py`:

```
get_status_counts() -> dict[str, int]
list_receipts_by_status(statuses, limit, offset) -> list[dict]
count_receipts_by_status(statuses) -> int
list_recent_runs(limit) -> list[dict]                     # from logs/runs.ndjson
get_extractions_for_receipt(receipt_id) -> list[dict]     # all, newest first (new)
list_resolution_events(receipt_id) -> list[dict]
search_receipts(filters, limit, offset) -> list[dict]
count_receipts(filters) -> int
list_clients_with_receipts() -> list[dict]
list_tax_years_with_receipts() -> list[str]
list_gl_code_options(client_id, business_type) -> list[dict]
get_spend_summary(period) -> dict
list_intake_issues() -> dict                              # section 8.6
```

**6.4 The console must run on the same machine as `receipts.db`.** SQLite over a network share risks corruption. The DB is correctly on local disk, not in OneDrive. Do not move it.

---

## 7. Auth

New dependencies: `argon2-cffi`, and `flask-wtf` for CSRF only. Hand-rolled CSRF is a common source of security bugs and these forms perform destructive writes.

- Session cookie login. No self-signup. Users created by `create_console_user.py`, which prompts for a password and never accepts one as an argument.
- argon2 via `argon2-cffi`, defaults fine. Never store, log or display a password.
- `CONSOLE_SECRET_KEY` from `.env`. **No default, no fallback.** Refuse to start if missing. A hardcoded fallback is a session forgery vector the moment this goes remote.
- `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`, `SESSION_COOKIE_SECURE` from config so it can be turned on behind a tunnel without a code change.
- `PERMANENT_SESSION_LIFETIME` 8 hours.
- 5 failed logins per username per 15 minutes, in-memory. Log failures at WARNING, never the attempted password.
- **Deny by default in `before_request`**, not a per-route decorator. A decorator you forget to add is an unauthenticated page.
- `?next=` handling on login, so a deep link to a receipt survives the login redirect.

### 7.1 Roles

| Capability | operator | admin |
|---|---|---|
| View status, queue, browse, receipt detail | yes | yes |
| Correct extracted fields and file | yes | yes |
| Correct GL code | yes | yes |
| Discard a receipt | no | yes |
| Register a client from the intake panel | no | yes |
| Record a credit top-up | no | yes |
| View settings and engine config | no | yes |

Enforce server side in the route. Hiding a button is presentation, not access control.

### 7.2 Config additions

```
CONSOLE_SECRET_KEY=            # required, no default
CONSOLE_BIND_HOST=127.0.0.1    # 0.0.0.0 only behind a tunnel
CONSOLE_PORT=8080
CONSOLE_COOKIE_SECURE=0
OPENAI_ADMIN_KEY=              # optional, Costs API
OPENAI_COST_API_KEY_ID=        # optional, filter costs to this app
RESOLUTIONS_DIR=               # optional override, default IntelliBooks\Resolutions
```

Follow the existing `config.py` pattern. Add every key to `.env.example`. Never commit real values.

### 7.3 Remote access, when needed

Tailscale or Cloudflare Tunnel with Access. Never port forwarding to this workstation. The only code-side change should be `CONSOLE_BIND_HOST` and `CONSOLE_COOKIE_SECURE`. If anything else needs changing, the design has drifted.

---

## 8. Console pages

```
console/__init__.py
console/web.py            Flask app and routes
console/auth.py
console/queries.py
console/costs.py
console/templates/
console/static/
run_console.py
create_console_user.py
```

Name the Flask module `web.py`, not `app.py`, to avoid confusion with the pipeline's `app.py`.

### 8.1 Status page (`/`)

- **Worker health.** Read `config.PIPELINE_LOCKFILE` for `pid` and `started_at`, test liveness with `app.py`'s `_is_process_running()`. **Extract that function to a shared module rather than duplicating it.** Green if the pid is alive and the last run finished within about two poll intervals; amber if alive but stalled; red if no live pid.
- **Last run.** Latest entry in `logs/runs.ndjson`: finished time, duration, per-run stats.
- **Status counts** from the DB: `pending`, `ok`, `needs_review`, `failed`, `possible_duplicate`, `retry_exhausted`, `discarded`.
- **Throughput today** via `repo.count_processed_today()`.
- **Last error** from the most recent run.
- **Billing-blocked banner** when 3.9's classification finds any.
- **Spend**: month to date, cost per receipt, estimated credit remaining.
- **Engine in use**: current engine and model from config.
- **Intake issues** summary, linking to 8.6.
- **Back-feed status**: count of unprocessed notes in `Resolutions\`, and any in `Resolutions\failed\`. A note sitting in `failed` means the DB and the books disagree, which is the one thing this design exists to prevent, so it belongs on the front page.

Do not build this page on `pipeline-status.json`. Read the DB. Leave that file alone; IntelliBooks reads it.

### 8.2 Queue page (`/queue`)

Default filter: `needs_review`, `possible_duplicate`, `failed`, `retry_exhausted`.

Columns: created, client, supplier, gross, status, reason (first validation note), age, and days remaining before the 7-day `AUTO_RETRY_MAX_AGE_DAYS` cutoff. That last column tells the operator what is about to stop being retried.

Rows link to the receipt detail page. Server-side pagination.

### 8.3 Browse page (`/receipts`)

One page, filter bar. Covers both "everything in the last N days" and "everything for a client in a tax year".

| Filter | Behaviour |
|---|---|
| Client | From `list_clients_with_receipts()`, plus "All" and an explicit "Unknown", since `client_id='UNKNOWN'` is a real state. |
| Date basis | Which date the period filter and default sort use: **capture date** (`receipts.created_at`) or **invoice date** (`extractions.invoice_date`). Present it as part of the period control, reading "Period applies to: invoice date". Both dates are always columns. |
| Period | Tax year picker, or last N days with presets 7, 30, 90. Mutually exclusive. |
| Status | Multi-select, default all. |
| Search | `LIKE` against `supplier_name`, `filename`, `receipt_ref_number`. Case-insensitive. |

**Capture date and invoice date are different and confusing them gives wrong answers.** A receipt captured in July 2026 can carry an invoice date in the 2025/26 tax year. Label the chosen basis in the results header, for example "Invoice date between 6 Apr 2026 and 5 Apr 2027". Never default silently to `created_at` while a tax year is selected.

**Tax year filtering must reuse `determine_tax_year()`.** Tax year is not stored anywhere; it is computed at filing time in `worker/filing.py` for the folder path. Do not reimplement the 6 April boundary in SQL and do not add a `tax_year` column. Add a companion `tax_year_bounds(tax_year) -> tuple[str, str]` next to it, have `determine_tax_year()` use it so the two cannot drift, and filter `invoice_date BETWEEN start AND end`.

Receipts with a NULL `invoice_date` cannot be placed in a tax year. Exclude them from tax-year results and show a separate count: "3 receipts excluded: no invoice date". Do not guess.

Columns: received, invoice date, client, supplier, net, VAT, gross, GL code, status, filed. Totals row with count and summed gross for the current filter.

Filters live in the query string so a view is bookmarkable. Server-side pagination. An empty result states what was filtered on and offers to clear.

**This is also the main cross-tool lookup.** From a bank line in IntelliBooks with no receipt attached, the operator searches here by date and amount to find out whether a receipt exists but is stuck.

### 8.4 Receipt detail page (`/receipt/<receipt_id>`)

Rendered from one `ResolutionView`.

1. **Document preview.** Serve from `receipt['file_path']` through a route that validates the path resolves inside `config.FILES_DIR` before opening, and never accepts a caller-supplied path. Look up by `receipt_id` only.
2. **Header.** Client, status, filename, created, source. For `possible_duplicate`, a prominent link to the counterpart.
3. **Side-by-side duplicate comparison** when applicable, highlighting supplier, invoice date, gross, `receipt_ref_number` and `receipt_time`. The last two are exactly what `_signals_differ()` uses, so it shows the operator why the system was unsure.
4. **Correction form.** The seven `CORRECTABLE_FIELDS` prefilled, plus the GL control from section 11, plus a hidden `expected_extraction_id`. Field errors from `parse_corrections`.
5. **Extraction history.** All rows, newest first: engine, extracted at, values, validation status, notes, `pipeline_version`. Read-only.
6. **Resolution events.** Who did what, including `desktop` resolutions arriving via the back-feed.
7. **Actions.** Save and file. Discard, admin only, with a typed reason.

### 8.5 Settings page (`/settings`), admin only

Current engine and model, read-only in phase 1. Credit top-up ledger with an add form. User list. Back-feed folder status with a retry action for anything in `Resolutions\failed\`. **Never render an API key**, not even masked.

### 8.6 Intake panel (`/intake`)

Problems that never become receipt rows, so a DB-only queue is blind to them. `app.py` logs and moves the email on.

| Item | Source | Action |
|---|---|---|
| Pipeline not running or stalled | lockfile, `runs.ndjson` | none, informational |
| Files waiting in Receipt Inbox | filesystem count under `RECEIPT_INBOX_ROOT` | none |
| Unknown senders | `email_alerts` where `alert_type='unknown_sender'` | **Register this client** |
| No-attachment alerts | `email_alerts` where `alert_type='no_attachment'` | none |
| Unsupported file types | `logs/receipt_events_*.ndjson`, action `unsupported_file_type` | none |

**Register this client** is the one that earns its place, and it needs care. `config.CLIENTS` is loaded once at import (`config.py` line 100), so appending a row to `clients.csv` does not reach the running pipeline. Two parts:

- Append the row to `clients.csv` in OneDrive, admin only, with validation that the email and client code are not already present.
- Provide a **reload** mechanism so `app.py` picks it up without a restart. Simplest correct approach: the console writes a small marker, and `app.py` calls `config.load_clients()` again at the top of each `process_once()` if the marker is newer than the last load. Do not add a signal handler or an IPC channel.

Note the unknown-sender email itself has already been moved to `INBOX.Unknown Sender` and no receipt row exists, so registering the client does not retroactively process it. The client must resend. Say so in the UI.

### 8.7 Presentation

Server-rendered Jinja2, plain CSS, no framework, no build step. Vanilla JS only where it earns its place. Must be implementable in one pass and readable cold.

---

## 9. Cost and credit monitoring

### 9.1 What is available

The Usage API and Costs API (`GET /v1/organization/costs`) are official and documented, return spend bucketed by day, and support `group_by` on `project_id`, `line_item` and `api_key_id`. They require an **Admin key**, which is a different credential from `OPENAI_API_KEY`.

There is **no documented endpoint for remaining prepaid credit balance.** Do not build anything depending on `/v1/dashboard/billing/credit_grants`; it is undocumented, has historically needed a session token, and has broken repeatedly.

### 9.2 Local token ledger, build first

`openai_vision.py` keeps only `response.choices[0].message.content` (line 82) and discards `response.usage`.

1. Add optional `prompt_tokens`, `completion_tokens`, `model` to `ExtractionResult` in `worker/extraction/base.py`, defaulting to `None`.
2. Populate them in `OpenAIVisionExtractor.extract()` from `response.usage`, guarded with `getattr`, since a failed or mocked call may not carry usage.
3. Add `MODEL_PRICING` to `config.py` as model to input and output price per token, with a comment pointing at `platform.openai.com/pricing`. **Confirm current prices at implementation time. There are deliberately none in this document.** Unknown model: store tokens, leave `estimated_cost_usd` NULL.
4. Add `repo.save_extraction_usage()` and call it immediately after each `save_extraction()` where usage exists. Call sites: `worker/extraction_pipeline.py` line 160, and the failure paths in `app.py` around 494, 527, 706 and 877. Manual corrections have no usage.

This gives cost per receipt, per day and per client. The Costs API cannot give cost per client, because only the DB knows which client a call belonged to. That is the number to price the service on.

### 9.3 Costs API

`console/costs.py` polls `/v1/organization/costs` once a day, or on demand from Settings, and caches into `openai_cost_daily`. Filter by `api_key_id`, which means issuing a dedicated OpenAI key or project for this app and putting its id in `OPENAI_COST_API_KEY_ID`.

Never call OpenAI on a page load. Read the cache, show `fetched_at`, offer a manual refresh. If the Admin key is absent, degrade to local-ledger figures and say so. Do not fail the page.

### 9.4 Remaining credit

Show as an **estimate**, labelled as one: `openai_credit_topups` minus spend since the earliest top-up, preferring Costs API figures and falling back to the ledger. Do not present it as authoritative.

The real protection against running out is OpenAI's own auto-recharge and billing threshold alerts, configured in their dashboard. Note that in `RECEIPT_CAPTURE_GUIDE.md` as an operational setup step.

---

## 10. Provider factory, phase 1 subset

**10.1 `worker/extraction/factory.py`**

```python
_REGISTRY = {"openai_vision": OpenAIVisionExtractor}

def get_extractor(name: str | None = None) -> BaseExtractor: ...
def available_engines() -> list[str]: ...
```

Add a `name` property to `BaseExtractor`. Replace `extractor = OpenAIVisionExtractor()` in `app.py` line 406 with `get_extractor()`. Replace the hardcoded engine strings per 3.8.

**10.2 Move post-processing out of `openai_vision.py`**

`_parse_ambiguous_date`, the `PREFER_DAYFIRST` logic and the VAT-inclusive-total swap live inside `openai_vision.py` lines 98-214. A second provider would silently not inherit any of it, so the day-first and VAT fixes would stop applying the moment the engine changed.

Move to `worker/extraction/postprocess.py`. **A pure move: behaviour must not change and the existing tests must pass unmodified.** If a test needs editing, something was changed that should not have been.

**10.3** Status page displays the current engine and model. No switching control in phase 1.

Phase 2, not now: the `settings` table, switching from the UI, and making `pipeline_version` a composite of git hash, engine and model. Without that composite key, switching provider will **not** cause `find_failed_by_version()` to re-attempt existing failures under the new engine, which is the main reason to switch. It needs its own regression test against the retry-cap boundary.

---

## 11. GL correction

### 11.1 Where the code options come from

The **Default CoA CSV**, loaded into `coa_accounts` with `scope='default'`. A draft generated from the live vendor mappings is at `chart_of_accounts_DRAFT.csv` in this repo; Paul extends it with income, equity and remaining balance sheet accounts.

`list_gl_code_options(client_id, business_type)` returns active accounts for `scope='default'` in phase 1, ordered by frequency of use in that client's vendor mappings, then by code. Allow free-text entry for a code not yet in the CoA, and record it in the notes so it can be promoted later.

**If the CSV is absent**, fall back to distinct `(nominal_code, account_name)` pairs from the vendor tables so the console still functions. Show a banner saying the CoA has not been loaded.

### 11.2 How the override is applied

`repo.update_categorisation(categorisation_id, correction_code, correction_name, correction_reason)` exists, sets `corrected_at`, and is currently called by nothing.

Ordering matters. `resolve_receipt.py` line 323 builds the sidecar with `categorisation.suggested_code`. Apply the override after filing and the sidecar on disk disagrees with the DB permanently. So:

1. `save_categorisation()` with the engine's suggestion. Never overwrite `suggested_code`; that is the audit trail.
2. `update_categorisation()` with the override.
3. Build the sidecar with the **effective** code and name.
4. `file_receipt()`.

The effective-code rule applies anywhere a category is read for output. **Check `export_bookkeeping.py` during implementation and report whether it needs the same treatment. Do not change it silently.**

### 11.3 Feeding corrections back into the mappings

`repo.upsert_client_vendor()` exists. Offer it as an **explicit opt-in checkbox**, "Remember this code for future receipts from this supplier", default off.

Do not learn automatically. One correction against a possibly misread supplier name would poison the client mapping table, and the engine's layer 2 exact match would then confidently apply the wrong code to every future receipt from that vendor.

Record the choice in `resolution_events.corrections_json`.

---

## 12. The resolution back-feed contract

**This is a two-sided contract.** The IntelliBooks half is specified in `PROMPT_intellibooks_resolution_backfeed.md` and built in a separate session. Both halves must match this section exactly.

### 12.1 Why it exists

`IntelliBooks-System-Specification.md` section 4.3 states that corrections made in Desktop are the practice's decided truth, with no back-feed in Phase 1, and change log item 19 implemented that deliberately. Three pipeline features built afterwards break under that rule:

- **Auto-retry on `pipeline_version`** re-extracts anything the DB still marks `needs_review`.
- **Duplicate protection keyed on `filed_path IS NOT NULL`** is blind to Desktop-filed receipts.
- **Vendor learning** never sees a category corrected in Desktop.

The rule was coherent while the pipeline was fire-and-forget. It no longer is. The back-feed keeps the rule's letter intact: Desktop still never writes `receipts.db`. It writes a note; the pipeline writes the DB.

### 12.2 Location and format

`{practice root}\IntelliBooks\Resolutions\`, override via `RESOLUTIONS_DIR`. Filename `{receipt_id}_{unix_ms}.json`.

```json
{
  "schema": 1,
  "receipt_id": "de3e901e-....",
  "client_code": "TEST",
  "action": "filed",
  "resolved_by": "desktop",
  "resolved_at": "2026-07-25T14:02:11.000Z",
  "values": {
    "supplier_name": "APCOA Parking",
    "invoice_date": "2026-07-14",
    "net_amount": 8.50,
    "vat_amount": 1.70,
    "gross_amount": 10.20,
    "currency": "GBP",
    "category_name": "Parking and tolls"
  },
  "filed_path": "Clients\\Paul Keating\\Receipts\\2026-27\\2026-07-14_APCOA-Parking_10.20.jpg",
  "original_review_files": ["...png", "...png.review.json"]
}
```

- `action` is `filed` or `discarded`. For `discarded`, `values` and `filed_path` are absent.
- `receipt_id` may be `null` if the review sidecar lacked one; then `original_review_files` is used for a filename match.
- `filed_path` is relative to the practice root, backslashes.
- `category_name` is a **name**, not a code. Desktop has no codes.
- Amounts are numbers. Absent rather than null or empty string.

### 12.3 Pipeline consumer

Runs at the start of `process_once()`, before `_retry_failed_receipts()`, so a resolved receipt is never retried in the same cycle it was resolved.

For each `*.json` in `Resolutions\`, oldest first by filename:

1. Parse. On failure, move to `Resolutions\failed\` with a `.error.txt` alongside, log at ERROR, continue. **Never delete.**
2. Resolve the receipt: by `receipt_id`, else by matching `original_review_files` against `receipts.filename`. Not found: move to `failed\`, log, continue.
3. **Idempotency.** If a `resolution_events` row already exists for this receipt with the same `resolved_at`, treat as already applied, move to `processed\`, continue.
4. Call `apply_resolution_note()`, which calls `resolve_receipt()` or `discard_receipt()` with `actor='desktop'`, `source='desktop'`.
5. Special handling for a `filed` note: the file already exists at `filed_path`, so **do not re-file it**. `apply_resolution_note()` must set `filed_path` directly via `mark_receipt_filed()` rather than calling `file_receipt()`, write the `manual_correction` extraction row, categorise, and set status `ok`. This is the one place where the resolution flow diverges from the console path, and it must be explicit rather than a flag threaded through `resolve_receipt()`.
6. `category_name` to code: look up the name in `coa_accounts`. Found, store the code and learn the vendor mapping. Not found, store the name only, skip learning, add a validation note. Until the Default CoA is loaded this is always the second case, which is expected and not an error.
7. On success, move the note to `Resolutions\processed\`. Never delete.

### 12.4 Reverse direction needs nothing

When the console resolves, it files to `Clients\{Name}\Receipts\{tax year}\` and IntelliBooks' item 21 auto-scan imports it. The only requirement is that the console removes the Review pair, per 3.5, or the item lingers in Desktop's list.

---

## 13. Chart of accounts module, specified not built

Reserved so module 1 does not need reworking. `coa_accounts` (5.5) is created in phase 1 with `scope='default'` populated.

**Three tiers.** Default, then Client group, then Client. Resolution runs client, then group, then default: the same fallback the categorisation engine already implements for vendor mappings, where the group tier is `business_type`.

**Group and entity type are orthogonal.** Group drives the CoA template and vendor mappings. Entity type drives the tax mapping, because "Motor expenses" maps to a self assessment box for a sole trader and a corporation tax line for a company. The mapping is `(account, entity_type) → target`.

**Provenance, not restriction.** No account is precluded. Every account records where it came from: inherited from default, inherited from group, added for this client, or imported with the client.

**Three statuses.** `active`, `not_adopted` (inherited but unwanted, keeps pickers clean), `archived` (was in use, retired, `maps_to_code` retained so history can be restated).

**Import as proposal, not permissive.** Nothing enters a client CoA until dispositioned. Four dispositions per imported account: match to an existing account, add as client-specific, archive, or **promote to group or default**. That fourth is how the default improves from real client data.

**Output includes the old-to-new mapping,** not just the new CoA. Without it a client's history cannot be restated and comparatives stop tying.

**Two AI jobs, not one.** Normalising an imported CoA is a matching problem, verifiable line by line, and is the same fuzzy-plus-LLM technique the vendor matcher already uses at a 70 percent threshold. Interviewing the client's circumstances to propose accounts is a judgement problem. Build the first one first.

**The interview is a versioned structured question set,** not a free-form chat: a core set everyone answers plus a branch per client group. Every proposed account carries a reason. The answers are saved, so next year's run starts from last year's answers.

**Transaction evidence beats the interview** where it exists. An account with three years of activity is needed; one with nothing in two years is a candidate to archive; a cluster in "Sundry" is a missing account. That needs counting, not AI.

**Export adapters are phase 2 or 3.** For now the output is a CSV and importing it into QBO, Xero or FreeAgent is manual. Known constraints when that work starts: QBO requires Account Name, Type and Detail Type with Detail Type constrained by Type; Xero needs a template from the specific organisation and its TaxType values must already exist there or the account silently defaults to Tax Exempt at 0%; FreeAgent is not a CoA import target at all, since its structure is rigid and its import is of opening balances matched by category name.

**Already built in IntelliBooks, do not duplicate:** SA103F cash-basis HMRC box mappings on every income and expense category, per-client year end, MTD flag, quarter basis, and the HMRC Summary Export (change log item 8). The five-type taxonomy and optional hierarchical names exist too (spec 5.4 item 4). What the category model lacks is only a **code**.

---

## 14. Explicitly out of scope

Each a deliberate deferral.

- Provider switching from the UI, the `settings` table, and the composite `pipeline_version`. See 10.3 for the trap.
- Mailbox folder sync after resolution. Parked. When picked up: a `pending_mailbox_moves` table written by the service and drained by `app.py`, which already holds an IMAP connection. Do not give the console IMAP credentials.
- The CoA module, section 13.
- CoA export adapters for QBO, Xero and FreeAgent.
- Category conflict resolution when a receipt is matched to a bank transaction. Agreed shape: the receipt wins when its categorisation confidence is high, the statement rule wins when it is low, and the disagreement is flagged either way. It must not auto-update the rule (change log item 2). Needs the shared vocabulary first, and it lives in IntelliBooks.
- Bulk actions on the queue.
- Editing or deleting extraction rows. Forbidden by `CLAUDE.md`.
- Any JSON API, OAuth, SSO, JWT or permission matrix.
- Retry-from-console. The auto-retry loop handles it; a manual trigger invites races with the running worker.

---

## 15. Test plan

Syntax check with `python -m py_compile`, verify imports, then functional tests. The suite passes 17 of 17; keep it green.

**Phase 0 regressions, each red before its fix:**

1. Mock the extractor to raise; run `_retry_failed_receipts()` twice under the same `pipeline_version`; assert extraction attempted once, not twice.
2. Same for the missing-file branch.
3. `save_extraction(update_status=False)` leaves `receipts.status` unchanged; default `True` preserves existing behaviour.
4. Correct VAT from non-zero to `0`; assert stored `0.0`.
5. `--vat 0` alone does not fall through to interactive mode.
6. All amounts as strings: coerced or field errors, never `TypeError`.
7. Resolution removes the Review pair; missing pair does not raise.
8. `review_count` from the DB matches status counts.
9. Sidecar carries `category_code` and `category_name`, and legacy `category` holds the name.

**`parse_corrections`:**

10. Omitted field absent from `values`; `"0"` present as `0.0`; `""` records an explicit clear.
11. Rejects `"1,234.56"`, `"£10"`, `"10.999"`, `"25/12/2026"` with field errors.

**Post-processing move:**

12. `postprocess` produces byte-identical results to the previous in-`openai_vision` behaviour for the existing date and VAT cases, with those tests unmodified.

**Service, temp DB:**

13. Mismatched `expected_extraction_id` returns `stale` and writes nothing.
14. Locked receipt returns `locked`.
15. Nonexistent receipt returns `not_found`, does not raise, does not `sys.exit`.
16. Still-invalid correction returns `still_invalid`, appends a note, writes a `resolution_events` row, does not file.
17. Successful resolve writes exactly one new extraction row and leaves the original untouched.
18. GL override leaves `suggested_code` unchanged, sets `correction_code`, and the written sidecar carries the corrected code and name.
19. Opt-in mapping checkbox off leaves `categorisations_client_vendors` unchanged.
20. `discard_receipt` sets `discarded`, deletes no file, removes no extraction row.
21. Lock released on every path including the exception path.

**Back-feed:**

22. A valid `filed` note sets status `ok`, sets `filed_path` to the note's path, writes a `manual_correction` extraction, writes a `resolution_events` row with `actor='desktop'`, and **does not re-file the image**.
23. Applying the same note twice is idempotent: one extraction row, one event row.
24. A malformed note moves to `Resolutions\failed\` and is not deleted.
25. A note for an unknown receipt moves to `failed\`.
26. A `category_name` absent from `coa_accounts` stores the name, skips vendor learning, adds a note.
27. A `discarded` note sets status `discarded` and deletes no files.
28. The consumer runs before `_retry_failed_receipts()`, so a receipt resolved by note is not retried in the same cycle.

**Browse and tax year:**

29. Receipts dated 5 April and 6 April fall in different tax years and each is returned by the correct year's filter. Use `tax_year_bounds()` in the test, not hardcoded dates.
30. Capture-date and invoice-date filters return different sets when a receipt straddles the boundary.
31. NULL `invoice_date` excluded from tax-year results and counted separately.
32. Search matches supplier, filename and reference number, case-insensitively.

**Web:**

33. Every route except `/login` redirects when unauthenticated. Enumerate routes in the test so a new unprotected route fails the suite.
34. An operator gets 403 on discard, register-client, top-up and settings.
35. POST without a valid CSRF token is rejected.
36. The preview route refuses a path outside `config.FILES_DIR`.
37. `?next=` survives the login redirect.

**Manual, before trusting it:**

38. Resolve a real `needs_review` receipt through the web form; verify the DB, the filed path and the sidecar all agree.
39. Run the console and the pipeline together through a full poll cycle; confirm no `database is locked` in `data/run.log`.
40. `resolve_receipt.py` still works from the CLI in both flag and interactive mode, per `RECEIPT_CAPTURE_GUIDE.md`.
41. Resolve in IntelliBooks Desktop, wait one poll, confirm the DB updated and the note moved to `processed\`.
42. Filter the browse page to Client_001 for the current tax year and reconcile the count and gross total against the OneDrive folder.

---

## 16. Implementation order

Commit after each step.

**Before any code, Paul:**

0. Discard the two disposable failed test receipts. Delete the two untracked draft files. Merge `fix/imap-message-id-dedup` into `main`. Start a fresh branch. Ordering matters: every commit bumps `pipeline_version` and triggers an auto-retry pass, so clear the discards first.

**Phase 0:**

1. The auto-retry loop fix, 3.1, with tests 1 to 3. **First: it is the only bug costing money continuously.**
2. `save_extraction(update_status=False)`.
3. `parse_corrections` plus the zero-value and coercion fixes, tests 4 to 6, 10, 11. Highest value after 3.1.
4. Review-pair cleanup and `review_count` from the DB, tests 7, 8.
5. Sidecar `category_code` and `category_name`, test 9.
6. Move post-processing to `worker/extraction/postprocess.py`, test 12. Pure move.
7. Extraction factory and `extractor.name`, replacing the hardcoded strings.

**Resolution service:**

8. `worker/resolution/service.py`, tests 13 to 21.
9. `resolve_receipt.py` as a thin CLI, plus `discard_receipt.py`. Verify test 40 by hand.
10. Back-feed consumer and `apply_resolution_note()`, tests 22 to 28.

**Console:**

11. Schema additions, including `coa_accounts`. Verify `init_db()` is still idempotent against the live DB.
12. Load `chart_of_accounts_DRAFT.csv` into `coa_accounts` with `scope='default'`.
13. Token usage capture and `extraction_usage`.
14. Auth: `console_users`, `create_console_user.py`, login, deny-by-default, CSRF, `?next=`. Tests 33 to 35, 37.
15. Read queries, status page, queue page.
16. Receipt detail page, correction form, GL control. Tests 18, 19, 36.
17. `tax_year_bounds()`, then the browse page. Tests 29 to 32.
18. Intake panel and the clients.csv reload mechanism.
19. Costs API client and the spend panel.
20. Billing-error classification, 3.9.
21. `RECEIPT_CAPTURE_GUIDE.md`: starting the console, login, resolving through the UI, the GL override, finding a client's receipts for a tax year, that both tools can resolve safely, and OpenAI auto-recharge as a setup step.
22. `CLAUDE.md`: new tables, the resolution service boundary, the back-feed contract, and the rule that the domain layer stays free of web imports.

Steps 1 to 10 are worth doing even if the console slips. They fix live bugs and close the divergence.

---

## 17. Documents and remaining questions

### 17.1 Ownership

| Document | Owner |
|---|---|
| This file | Cowork design session |
| `IntelliBooks-System-Specification.md` | Cowork design session, bump to v1.1 |
| `IntelliBooks-System-Overview.md` | Cowork design session |
| `CLAUDE.md`, `RECEIPT_CAPTURE_GUIDE.md` | Implementation session, steps 21 and 22 |
| `IntelliBooks-Change-Log.md` | The IntelliBooks build session, items 24 to 26 only |

Two sessions editing whole-system documents independently is how the drift began.

### 17.2 Corrections needed to the specification

It is v1.0 of 15 July and describes itself as the single source of truth. Bump to v1.1, keep superseded wording visible with its reason, so the decision trail survives.

- Review holding is `Clients\{Name}\Review\`, not `Receipt Inbox\{CODE}\Review\`. Sections 3 and 5.3 item 6. Change log item 18 removed the latter.
- Books live at `IntelliBooks\Books\{CODE}-books.json`. Section 3 table and 5.4 item 1. Item 12 moved them.
- Section 3 predates item 12's `IntelliBooks\` versus `Clients\` split, so Receipt Inbox is `IntelliBooks\Receipt Inbox\{CODE}\`.
- Section 5.4 item 6's "Import Client's Receipt Folder" was removed in item 22.
- Section 4.3's Corrections rule: record the original, then the back-feed and the three defects that forced it.
- Section 4.3's lifecycle diagram says "human fixes, reprocess", which matches neither implementation.
- Section 2: add the console as a sixth component.
- Section 5.3 item 4's internal store path may have diverged from `CLAUDE.md`. Verify rather than assume.
- Nothing records `possible_duplicate`, `retry_exhausted`, receipt locking, the 7-day retry cap or the IMAP Message-ID fix.

### 17.3 Corrections needed to the overview

More current, 19 July, but: line 28 describes Desktop's review-and-file flow as *the* way to complete reviews; line 36's "the desktop app never writes to receipts.db" needs the note-based nuance; neither `resolve_receipt.py` nor the console appears.

### 17.4 Open questions for Paul

- Confirm the revised answer to the category-conflict question, section 14, bullet 5: receipt wins on high confidence, rule wins on low, flag either way.
- Extend `chart_of_accounts_DRAFT.csv` with income, equity and remaining balance sheet accounts. Not blocking; the 23 expense accounts cover the receipts module.
- Issue a dedicated OpenAI API key or project for this app, needed for clean cost attribution (9.3).
- Whether an org-level OpenAI Admin key on this workstation is acceptable. If not, 9.3 is skipped and the local ledger stands alone.
- Whether `export_bookkeeping.py` needs the effective-GL-code treatment (11.2).
- Whether the browse page should export CSV. `export_bookkeeping.py` already exists and two divergent export formats is worse than one; if yes, reuse its logic.
- Confirm IntelliBooks change log item 19 has been tested end to end before the back-feed is built on it. Note that testing it creates the divergence deliberately, so reset the receipt's DB status afterwards.

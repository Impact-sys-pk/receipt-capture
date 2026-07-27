import sqlite3
import config


def init_db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS categorisations_firm_vendors (
            vendor_key              TEXT PRIMARY KEY,
            business_type           TEXT NOT NULL,
            vendor_code             TEXT NOT NULL,
            nominal_code            TEXT NOT NULL,
            account_name            TEXT NOT NULL,
            vendor_name             TEXT,
            times_seen              INTEGER DEFAULT 1,
            last_updated            TEXT NOT NULL,
            UNIQUE(business_type, vendor_code, vendor_name)
        );

        CREATE INDEX IF NOT EXISTS idx_firm_vendor_code
            ON categorisations_firm_vendors(business_type, vendor_code);

        CREATE TABLE IF NOT EXISTS categorisations_client_vendors (
            vendor_key              TEXT PRIMARY KEY,
            client_id               TEXT NOT NULL,
            vendor_code             TEXT NOT NULL,
            nominal_code            TEXT NOT NULL,
            account_name            TEXT NOT NULL,
            vendor_name             TEXT,
            detail                  TEXT,
            times_seen              INTEGER DEFAULT 1,
            last_updated            TEXT NOT NULL,
            UNIQUE(client_id, vendor_code, vendor_name)
        );

        CREATE INDEX IF NOT EXISTS idx_client_vendor_code
            ON categorisations_client_vendors(client_id, vendor_code);

        CREATE TABLE IF NOT EXISTS categorisations_client_rules (
            rule_id                 TEXT PRIMARY KEY,
            client_id               TEXT NOT NULL,
            rule_name               TEXT NOT NULL,
            priority                INTEGER NOT NULL DEFAULT 50,
            vendor_code             TEXT,
            condition_type          TEXT NOT NULL,
            condition_field         TEXT NOT NULL,
            condition_value         TEXT NOT NULL,
            nominal_code            TEXT NOT NULL,
            account_name            TEXT NOT NULL,
            created_at              TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS categorisations (
            categorisation_id       TEXT PRIMARY KEY,
            receipt_id              TEXT NOT NULL,
            extraction_id           TEXT NOT NULL,
            client_id               TEXT NOT NULL,
            business_type           TEXT NOT NULL,
            vendor_key              TEXT,
            suggested_code          TEXT,
            suggested_name          TEXT,
            confidence              TEXT NOT NULL,
            match_source            TEXT NOT NULL,
            matched_vendor          TEXT,
            needs_review            INTEGER DEFAULT 1,
            categorised_at          TEXT NOT NULL,
            corrected_at            TEXT,
            correction_code         TEXT,
            correction_name         TEXT,
            correction_reason       TEXT,
            FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id),
            FOREIGN KEY (extraction_id) REFERENCES extractions(extraction_id)
        );

        CREATE TABLE IF NOT EXISTS receipts (
            receipt_id          TEXT PRIMARY KEY,
            firm_id             TEXT NOT NULL DEFAULT 'INTELLITAX',
            client_id           TEXT DEFAULT 'UNKNOWN',
            client_code         TEXT DEFAULT 'UNKNOWN',
            source              TEXT DEFAULT 'email',
            message_id          TEXT NOT NULL,
            email_subject       TEXT,
            email_from          TEXT,
            email_received_at   TEXT,
            filename            TEXT NOT NULL,
            file_path           TEXT NOT NULL,
            file_hash           TEXT NOT NULL,
            filed_path          TEXT,
            status              TEXT DEFAULT 'pending',
            created_at          TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS statements (
            statement_id        TEXT PRIMARY KEY,
            client_id           TEXT NOT NULL,
            client_code         TEXT NOT NULL,
            platform            TEXT NOT NULL,
            week_ending         TEXT NOT NULL,
            source              TEXT NOT NULL,
            file_hash           TEXT NOT NULL,
            file_path           TEXT NOT NULL,
            status              TEXT NOT NULL,
            created_at          TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_statements_file_hash
            ON statements(file_hash);

        CREATE TABLE IF NOT EXISTS extractions (
            extraction_id       TEXT PRIMARY KEY,
            receipt_id          TEXT NOT NULL,
            engine              TEXT NOT NULL,
            extracted_at        TEXT NOT NULL,
            supplier_name       TEXT,
            invoice_date        TEXT,
            net_amount          REAL,
            vat_amount          REAL,
            gross_amount        REAL,
            details             TEXT,
            currency            TEXT DEFAULT 'GBP',
            raw_response        TEXT,
            validation_status   TEXT,
            validation_notes    TEXT,
            FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
        );

        CREATE TABLE IF NOT EXISTS processed_attachments (
            message_id      TEXT NOT NULL,
            attachment_id   TEXT NOT NULL,
            file_hash       TEXT NOT NULL,
            processed_at    TEXT NOT NULL,
            receipt_id      TEXT NOT NULL,
            PRIMARY KEY (message_id, attachment_id)
        );

        CREATE TABLE IF NOT EXISTS email_delta (
            key         TEXT PRIMARY KEY,
            value       TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS email_alerts (
            message_id          TEXT NOT NULL,
            alert_type          TEXT NOT NULL,
            recipient_email     TEXT NOT NULL,
            firm_name           TEXT NOT NULL,
            alert_sent_at       TEXT NOT NULL,
            PRIMARY KEY (message_id, alert_type)
        );

        CREATE INDEX IF NOT EXISTS idx_email_alerts_message
            ON email_alerts(message_id);

        -- Design document 5.1. One row per resolution, whatever the entry
        -- point, so a correction records who made it and through which tool.
        -- extraction_id is nullable and deliberately carries NO foreign key: an
        -- outcome with no extraction row would otherwise fail to write its own
        -- audit row, which is the same class of bug as b480a7e.
        CREATE TABLE IF NOT EXISTS resolution_events (
            event_id            TEXT PRIMARY KEY,
            receipt_id          TEXT NOT NULL,
            extraction_id       TEXT,
            actor               TEXT NOT NULL,
            source              TEXT NOT NULL,
            action              TEXT NOT NULL,
            corrections_json    TEXT,
            gl_override_code    TEXT,
            outcome             TEXT NOT NULL,
            reason              TEXT,
            created_at          TEXT NOT NULL,
            FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
        );

        CREATE INDEX IF NOT EXISTS idx_resolution_events_receipt
            ON resolution_events(receipt_id, created_at);
    """)
    conn.commit()

    existing_receipt_columns = {row[1] for row in conn.execute("PRAGMA table_info(receipts)").fetchall()}
    if "client_code" not in existing_receipt_columns:
        conn.execute("ALTER TABLE receipts ADD COLUMN client_code TEXT DEFAULT 'UNKNOWN'")
    if "source" not in existing_receipt_columns:
        conn.execute("ALTER TABLE receipts ADD COLUMN source TEXT DEFAULT 'email'")
    if "filed_path" not in existing_receipt_columns:
        conn.execute("ALTER TABLE receipts ADD COLUMN filed_path TEXT")
    conn.commit()
    # Ensure extractions table has `details` column for older DBs
    existing_extraction_columns = {row[1] for row in conn.execute("PRAGMA table_info(extractions)").fetchall()}
    if "details" not in existing_extraction_columns:
        conn.execute("ALTER TABLE extractions ADD COLUMN details TEXT")

    # Part 1: Auto-retry on version change
    if "pipeline_version" not in existing_extraction_columns:
        conn.execute("ALTER TABLE extractions ADD COLUMN pipeline_version TEXT")

    # Part 2B: Semantic duplicate signals
    if "receipt_ref_number" not in existing_extraction_columns:
        conn.execute("ALTER TABLE extractions ADD COLUMN receipt_ref_number TEXT")
    if "receipt_time" not in existing_extraction_columns:
        conn.execute("ALTER TABLE extractions ADD COLUMN receipt_time TEXT")

    conn.commit()

    # Part 2B: Track duplicate relationships + Part 3 locking
    existing_receipt_columns = {row[1] for row in conn.execute("PRAGMA table_info(receipts)").fetchall()}
    if "duplicate_of" not in existing_receipt_columns:
        conn.execute("ALTER TABLE receipts ADD COLUMN duplicate_of TEXT")
    if "locked_at" not in existing_receipt_columns:
        conn.execute("ALTER TABLE receipts ADD COLUMN locked_at TIMESTAMP")

    conn.commit()

    # Design document 5.1 as amended. discard_receipt() takes a reason and the
    # table had nowhere to put it, so it reached a log line and then vanished. For
    # a discard the reason is the most useful thing to keep: the difference between
    # "duplicate of r-x" and "the client sent a bank statement by mistake".
    existing_event_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(resolution_events)").fetchall()
    }
    if existing_event_columns and "reason" not in existing_event_columns:
        conn.execute("ALTER TABLE resolution_events ADD COLUMN reason TEXT")

    conn.commit()
    conn.close()

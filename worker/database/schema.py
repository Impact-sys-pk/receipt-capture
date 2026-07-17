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
    """)
    conn.commit()

    existing_receipt_columns = {row[1] for row in conn.execute("PRAGMA table_info(receipts)").fetchall()}
    if "client_code" not in existing_receipt_columns:
        conn.execute("ALTER TABLE receipts ADD COLUMN client_code TEXT DEFAULT 'UNKNOWN'")
    if "source" not in existing_receipt_columns:
        conn.execute("ALTER TABLE receipts ADD COLUMN source TEXT DEFAULT 'email'")
    conn.commit()
    conn.close()

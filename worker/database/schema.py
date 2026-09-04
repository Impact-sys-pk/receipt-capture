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
            -- 10d.39, closing outstanding items 17 and 47. Nullable, written and
            -- never read. The UNIQUE key deliberately does not include it, so
            -- behaviour does not change and the learned pool stays shared: the
            -- column exists so the provenance of a learned mapping is captured
            -- while it is still capturable.
            firm_id                 TEXT,
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
            trade                   TEXT NOT NULL,
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

        -- Sub-steps 10d.23 to 10d.28. No column on this table carries a default
        -- any more: each one was a value arriving as a fallback rather than as a
        -- recorded conclusion, and save_receipt() writes all of them explicitly.
        -- client_code is gone entirely, 10d.23.
        --
        -- email_received_at is ISO 8601 UTC and one format only, 10d.27. It used
        -- to take an integer mtime from the folder path and an RFC-shaped string
        -- from the email path, into the same TEXT column.
        --
        -- file_path is the copy in the Intellibills document store and filed_path
        -- is the copy in the client folder. The same two names mean the same two
        -- things on `statements` below, 10d.56.
        --
        -- locked_at is TEXT, 10d.28, so it compares as a string against the ISO
        -- timestamps everything else on this database stores.
        CREATE TABLE IF NOT EXISTS receipts (
            receipt_id          TEXT PRIMARY KEY,
            firm_id             TEXT NOT NULL,
            client_id           TEXT NOT NULL,
            source              TEXT NOT NULL,
            message_id          TEXT NOT NULL,
            email_subject       TEXT,
            email_from          TEXT,
            email_received_at   TEXT,
            filename            TEXT NOT NULL,
            file_path           TEXT NOT NULL,
            file_hash           TEXT NOT NULL,
            filed_path          TEXT,
            filed_at            TEXT,
            duplicate_of        TEXT,
            locked_at           TEXT,
            status              TEXT NOT NULL,
            created_at          TEXT NOT NULL
        );

        -- Sub-steps 10d.29 and 10d.56. client_code is gone, and file_path now
        -- means what it means on `receipts`: the copy in the document store.
        -- filed_path is new here and is the copy in the client folder, which is
        -- what file_path used to hold. One column name, one meaning, both tables.
        -- app.py:361 is why it matters: it takes receipt["file_path"] as the file
        -- to copy FROM when filing, and the same line written against a statement
        -- would have copied the filed copy onto itself.
        CREATE TABLE IF NOT EXISTS statements (
            statement_id        TEXT PRIMARY KEY,
            client_id           TEXT NOT NULL,
            platform            TEXT NOT NULL,
            week_ending         TEXT NOT NULL,
            source              TEXT NOT NULL,
            file_hash           TEXT NOT NULL,
            file_path           TEXT NOT NULL,
            filed_path          TEXT,
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
            -- 10d.31. No default: the currency is what the extraction read, and
            -- every writer states it. The twelve "GBP" literals that used to sit
            -- across app.py, the resolution service and openai_vision.py are now
            -- config.DEFAULT_CURRENCY.
            currency            TEXT,
            raw_response        TEXT,
            validation_status   TEXT,
            validation_notes    TEXT,
            pipeline_version    TEXT,
            receipt_ref_number  TEXT,
            receipt_time        TEXT,
            FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
        );

        -- 10d.32. firm_id is informational and nothing reads it. The key is
        -- deliberately unchanged: a message_id is generated by the sender's mail
        -- client and is unique by design, so the key is already unique across
        -- firms and adding firm_id would loosen it rather than tighten it.
        -- Amendment 129, closing outstanding item 6.
        CREATE TABLE IF NOT EXISTS processed_attachments (
            message_id      TEXT NOT NULL,
            attachment_id   TEXT NOT NULL,
            file_hash       TEXT NOT NULL,
            processed_at    TEXT NOT NULL,
            receipt_id      TEXT NOT NULL,
            firm_id         TEXT,
            PRIMARY KEY (message_id, attachment_id)
        );

        -- email_delta was created here until 2026-09-04, holding a delta_link
        -- and a last_uid. Outstanding item 159: nothing wrote either, because
        -- fetch_new_messages() searches ALL on every poll and an IMAP UID
        -- cannot be carried between polls. The four repository accessors went
        -- with it. A database created before that date still holds the table,
        -- empty; it is not dropped here, because dropping a table is a
        -- migration and this file only creates.

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
        --
        -- 10d.33. Neither receipt_id nor extraction_id carries a foreign key.
        --
        -- The comment that used to sit here said extraction_id had no key so
        -- that an outcome with no extraction row could still write its audit
        -- row. That reason was false: a NULL foreign key value satisfies the
        -- constraint, so the case it claimed to protect was never at risk.
        --
        -- The real reason, and it now applies to both columns: this table is the
        -- audit trail, and an audit row that cannot be written because the thing
        -- it describes has gone is worse than a dangling id. receipt_id's key
        -- also made this table refuse a row about a receipt the rebuild had
        -- dropped, which is exactly when somebody wants the history.
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
            created_at          TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_resolution_events_receipt
            ON resolution_events(receipt_id, created_at);
    """)
    conn.commit()
    conn.close()

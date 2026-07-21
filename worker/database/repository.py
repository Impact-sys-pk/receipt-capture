import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional

import config
from .schema import init_db


class Repository:
    def __init__(self):
        init_db()
        self._conn = sqlite3.connect(config.DB_PATH)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")

    def close(self):
        self._conn.close()

    def is_duplicate(self, message_id: str, attachment_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM processed_attachments WHERE message_id = ? AND attachment_id = ?",
            (message_id, attachment_id)
        ).fetchone()
        return row is not None

    def find_by_hash(self, file_hash: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT receipt_id FROM processed_attachments WHERE file_hash = ? LIMIT 1",
            (file_hash,)
        ).fetchone()
        if row:
            return row["receipt_id"]
        row = self._conn.execute(
            "SELECT receipt_id FROM receipts WHERE file_hash = ? LIMIT 1",
            (file_hash,)
        ).fetchone()
        return row["receipt_id"] if row else None

    def find_by_transaction(self, supplier_name: str, invoice_date: str, gross_amount: float) -> Optional[str]:
        row = self._conn.execute(
            "SELECT receipt_id FROM extractions WHERE supplier_name = ? AND invoice_date = ? AND gross_amount = ? LIMIT 1",
            (supplier_name, invoice_date, gross_amount)
        ).fetchone()
        return row["receipt_id"] if row else None

    def find_by_transaction_no_date(self, supplier_name: str, gross_amount: float) -> Optional[str]:
        row = self._conn.execute(
            "SELECT receipt_id FROM extractions WHERE supplier_name = ? AND gross_amount = ? LIMIT 1",
            (supplier_name, gross_amount)
        ).fetchone()
        return row["receipt_id"] if row else None

    def resolve_client_info(self, email_from: str) -> tuple[str, str, str]:
        """Match email_from to client in clients.csv, return (client_id, firm_id, client_code)."""
        if not email_from:
            return ("UNKNOWN", "INTELLITAX", "UNKNOWN")

        email = email_from.strip().lower()
        if "<" in email and ">" in email:
            email = email.split("<")[1].split(">")[0].strip()

        client = config.CLIENTS.get(email)
        if client:
            return (client["client_id"], client["firm_id"], client.get("client_code", "UNKNOWN"))
        return ("UNKNOWN", "INTELLITAX", "UNKNOWN")

    def resolve_client_id(self, email_from: str) -> tuple[str, str]:
        client_id, firm_id, _ = self.resolve_client_info(email_from)
        return client_id, firm_id

    def resolve_client_by_code(self, client_code: str) -> tuple[str, str, str]:
        """Match client_code from folder intake to client data."""
        if not client_code:
            return ("UNKNOWN", "INTELLITAX", "UNKNOWN")

        client = config.CLIENTS_BY_CODE.get(client_code.upper())
        if client:
            return (client["client_id"], client["firm_id"], client.get("client_code", client_code.upper()))
        return ("UNKNOWN", "INTELLITAX", client_code.upper())

    def save_statement(
        self, statement_id, client_id, client_code, platform,
        week_ending, source, file_hash, file_path, status="filed"
    ):
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT INTO statements
                (statement_id, client_id, client_code, platform, week_ending,
                 source, file_hash, file_path, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (statement_id, client_id, client_code, platform, week_ending,
              source, file_hash, str(file_path), status, now))
        self._conn.commit()

    def find_statement_by_hash(self, file_hash: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT statement_id FROM statements WHERE file_hash = ? LIMIT 1",
            (file_hash,)
        ).fetchone()
        return row["statement_id"] if row else None

    def get_unfiled_ok_receipts(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT receipt_id, client_id, firm_id, client_code, source, file_path, filename FROM receipts WHERE status = 'ok' AND filed_path IS NULL"
        ).fetchall()
        return [dict(row) for row in rows]

    def is_recorded_and_filed(self, file_hash: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM receipts WHERE file_hash = ? AND filed_path IS NOT NULL LIMIT 1",
            (file_hash,)
        ).fetchone()
        return row is not None

    def get_extraction_for_receipt(self, receipt_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM extractions WHERE receipt_id = ? ORDER BY extracted_at DESC LIMIT 1",
            (receipt_id,)
        ).fetchone()
        return dict(row) if row else None

    def mark_receipt_filed(self, receipt_id: str, filed_path: str):
        self._conn.execute(
            "UPDATE receipts SET filed_path = ? WHERE receipt_id = ?",
            (str(filed_path), receipt_id)
        )
        self._conn.commit()

    def save_receipt(
        self, receipt_id, message_id, email_subject, email_from,
        email_received_at, filename, file_path, file_hash,
        firm_id="INTELLITAX", client_id="UNKNOWN", client_code="UNKNOWN", source="email"
    ):
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT INTO receipts
                (receipt_id, firm_id, client_id, client_code, source, message_id, email_subject, email_from,
                 email_received_at, filename, file_path, file_hash, filed_path, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (receipt_id, firm_id, client_id, client_code, source, message_id, email_subject, email_from,
              email_received_at, filename, str(file_path), file_hash, None, now))
        self._conn.commit()

    def save_extraction(
        self, extraction_id, receipt_id, engine,
        supplier_name, invoice_date, net_amount, vat_amount, gross_amount,
        currency, raw_response, validation_status, validation_notes
    ):
        now = datetime.now(timezone.utc).isoformat()
        notes_str = ", ".join(validation_notes) if validation_notes else None
        self._conn.execute("""
            INSERT INTO extractions
                (extraction_id, receipt_id, engine, extracted_at, supplier_name, invoice_date,
                 net_amount, vat_amount, gross_amount, currency, raw_response,
                 validation_status, validation_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (extraction_id, receipt_id, engine, now, supplier_name, invoice_date,
              net_amount, vat_amount, gross_amount, currency, raw_response,
              validation_status, notes_str))
        self._conn.execute(
            "UPDATE receipts SET status = ? WHERE receipt_id = ?",
            (validation_status, receipt_id)
        )
        self._conn.commit()

    def mark_processed(self, message_id: str, attachment_id: str, file_hash: str, receipt_id: str):
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT OR IGNORE INTO processed_attachments
                (message_id, attachment_id, file_hash, processed_at, receipt_id)
            VALUES (?, ?, ?, ?, ?)
        """, (message_id, attachment_id, file_hash, now, receipt_id))
        self._conn.commit()

    def count_processed_today(self) -> int:
        row = self._conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM receipts WHERE DATE(created_at) = DATE('now','utc'))
                + (SELECT COUNT(*) FROM statements WHERE DATE(created_at) = DATE('now','utc'))
                AS total
        """).fetchone()
        return row[0] if row else 0

    def backup_db(self, destination_path):
        with sqlite3.connect(str(destination_path)) as dest_conn:
            self._conn.backup(dest_conn)
            dest_conn.commit()

    def get_delta_link(self) -> Optional[str]:
        row = self._conn.execute(
            "SELECT value FROM email_delta WHERE key = 'delta_link'"
        ).fetchone()
        return row["value"] if row else None

    def save_delta_link(self, link: Optional[str]):
        now = datetime.now(timezone.utc).isoformat()
        if link is None:
            self._conn.execute("DELETE FROM email_delta WHERE key = 'delta_link'")
        else:
            self._conn.execute("""
                INSERT INTO email_delta (key, value, updated_at) VALUES ('delta_link', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """, (link, now))
        self._conn.commit()

    def get_last_uid(self) -> Optional[str]:
        row = self._conn.execute(
            "SELECT value FROM email_delta WHERE key = 'last_uid'"
        ).fetchone()
        return row["value"] if row else None

    def save_last_uid(self, uid: str):
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT INTO email_delta (key, value, updated_at) VALUES ('last_uid', ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """, (uid, now))
        self._conn.commit()

    # Categorisation repository methods

    def get_client_vendor(self, client_id: str, vendor_code: str) -> Optional[dict]:
        """Exact match lookup for client-specific vendor mapping. Returns most-seen variant."""
        row = self._conn.execute("""
            SELECT vendor_key, nominal_code, account_name, vendor_name, times_seen
            FROM categorisations_client_vendors
            WHERE client_id = ? AND vendor_code = ?
            ORDER BY times_seen DESC, last_updated DESC
            LIMIT 1
        """, (client_id, vendor_code)).fetchone()
        return dict(row) if row else None

    def upsert_client_vendor(self, client_id: str, vendor_code: str,
                            nominal_code: str, account_name: str, last_updated: str,
                            vendor_name: str = None, detail: str = None):
        """Insert or update client vendor mapping. Each variant (vendor_name) gets unique vendor_key."""
        # Check if this exact variant exists
        existing = self._conn.execute("""
            SELECT vendor_key FROM categorisations_client_vendors
            WHERE client_id = ? AND vendor_code = ? AND vendor_name = ?
        """, (client_id, vendor_code, vendor_name)).fetchone()

        if existing:
            # Update existing variant
            self._conn.execute("""
                UPDATE categorisations_client_vendors
                SET nominal_code = ?, account_name = ?, detail = ?, times_seen = times_seen + 1, last_updated = ?
                WHERE vendor_key = ?
            """, (nominal_code, account_name, detail, last_updated, existing["vendor_key"]))
        else:
            # Insert new variant
            vendor_key = str(uuid.uuid4())
            self._conn.execute("""
                INSERT INTO categorisations_client_vendors
                    (vendor_key, client_id, vendor_code, nominal_code, account_name, vendor_name, detail, times_seen, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (vendor_key, client_id, vendor_code, nominal_code, account_name, vendor_name, detail, last_updated))

        self._conn.commit()

    def list_client_vendors(self, client_id: str) -> list[str]:
        """Get distinct vendor_codes for a client for fuzzy matching candidates."""
        rows = self._conn.execute(
            "SELECT DISTINCT vendor_code FROM categorisations_client_vendors WHERE client_id = ?",
            (client_id,)
        ).fetchall()
        return [row["vendor_code"] for row in rows]

    def get_firm_vendor(self, business_type: str, vendor_code: str) -> Optional[dict]:
        """Exact match lookup for firm-level vendor mapping. Returns most-seen variant."""
        row = self._conn.execute("""
            SELECT vendor_key, nominal_code, account_name, vendor_name, times_seen
            FROM categorisations_firm_vendors
            WHERE business_type = ? AND vendor_code = ?
            ORDER BY times_seen DESC, last_updated DESC
            LIMIT 1
        """, (business_type, vendor_code)).fetchone()
        return dict(row) if row else None

    def upsert_firm_vendor(self, business_type: str, vendor_code: str,
                          nominal_code: str, account_name: str, last_updated: str,
                          vendor_name: str = None):
        """Insert or update firm vendor mapping. Each variant gets unique vendor_key."""
        # Check if this exact variant exists
        existing = self._conn.execute("""
            SELECT vendor_key FROM categorisations_firm_vendors
            WHERE business_type = ? AND vendor_code = ? AND vendor_name = ?
        """, (business_type, vendor_code, vendor_name)).fetchone()

        if existing:
            # Update existing variant
            self._conn.execute("""
                UPDATE categorisations_firm_vendors
                SET nominal_code = ?, account_name = ?, times_seen = times_seen + 1, last_updated = ?
                WHERE vendor_key = ?
            """, (nominal_code, account_name, last_updated, existing["vendor_key"]))
        else:
            # Insert new variant
            vendor_key = str(uuid.uuid4())
            self._conn.execute("""
                INSERT INTO categorisations_firm_vendors
                    (vendor_key, business_type, vendor_code, nominal_code, account_name, vendor_name, times_seen, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """, (vendor_key, business_type, vendor_code, nominal_code, account_name, vendor_name, last_updated))

        self._conn.commit()

    def list_firm_vendors(self, business_type: str) -> list[str]:
        """Get distinct vendor_codes for a business type for fuzzy matching candidates."""
        rows = self._conn.execute(
            "SELECT DISTINCT vendor_code FROM categorisations_firm_vendors WHERE business_type = ?",
            (business_type,)
        ).fetchall()
        return [row["vendor_code"] for row in rows]

    def increment_firm_vendor_count(self, business_type: str, vendor_code: str):
        """Increment times_seen for the most-seen firm vendor variant."""
        # Find the most-seen variant and increment it
        row = self._conn.execute("""
            SELECT vendor_key FROM categorisations_firm_vendors
            WHERE business_type = ? AND vendor_code = ?
            ORDER BY times_seen DESC, last_updated DESC
            LIMIT 1
        """, (business_type, vendor_code)).fetchone()

        if row:
            self._conn.execute(
                "UPDATE categorisations_firm_vendors SET times_seen = times_seen + 1 WHERE vendor_key = ?",
                (row["vendor_key"],)
            )
            self._conn.commit()

    def save_categorisation(self, categorisation_id: str, receipt_id: str,
                           extraction_id: str, client_id: str, business_type: str,
                           vendor_key: Optional[str], suggested_code: Optional[str],
                           suggested_name: Optional[str], confidence: str,
                           match_source: str, matched_vendor: Optional[str],
                           needs_review: bool, categorised_at: str):
        """Insert categorisation record."""
        self._conn.execute("""
            INSERT INTO categorisations
                (categorisation_id, receipt_id, extraction_id, client_id, business_type,
                 vendor_key, suggested_code, suggested_name, confidence, match_source,
                 matched_vendor, needs_review, categorised_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (categorisation_id, receipt_id, extraction_id, client_id, business_type,
              vendor_key, suggested_code, suggested_name, confidence, match_source,
              matched_vendor, needs_review, categorised_at))
        self._conn.commit()

    def get_categorisation(self, categorisation_id: str) -> Optional[dict]:
        """Retrieve categorisation record by ID."""
        row = self._conn.execute(
            "SELECT * FROM categorisations WHERE categorisation_id = ?",
            (categorisation_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_categorisation(self, categorisation_id: str,
                             correction_code: str, correction_name: str,
                             correction_reason: str):
        """Add correction fields to existing categorisation (append-only)."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            UPDATE categorisations
            SET corrected_at = ?, correction_code = ?, correction_name = ?, correction_reason = ?
            WHERE categorisation_id = ?
        """, (now, correction_code, correction_name, correction_reason, categorisation_id))
        self._conn.commit()

    # Rules repository methods

    def get_client_rules(self, client_id: str) -> list[dict]:
        """Get all rules for a client, ordered by priority (highest first)."""
        rows = self._conn.execute("""
            SELECT rule_id, rule_name, priority, vendor_code, condition_type,
                   condition_field, condition_value, nominal_code, account_name
            FROM categorisations_client_rules
            WHERE client_id = ?
            ORDER BY priority DESC
        """, (client_id,)).fetchall()
        return [dict(row) for row in rows]

    def create_client_rule(self, rule_id: str, client_id: str, rule_name: str,
                         priority: int, vendor_code: str, condition_type: str,
                         condition_field: str, condition_value: str,
                         nominal_code: str, account_name: str):
        """Create a new client categorisation rule."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT INTO categorisations_client_rules
                (rule_id, client_id, rule_name, priority, vendor_code, condition_type,
                 condition_field, condition_value, nominal_code, account_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rule_id, client_id, rule_name, priority, vendor_code, condition_type,
              condition_field, condition_value, nominal_code, account_name, now))
        self._conn.commit()

    def delete_client_rule(self, rule_id: str):
        """Delete a client rule."""
        self._conn.execute(
            "DELETE FROM categorisations_client_rules WHERE rule_id = ?",
            (rule_id,)
        )
        self._conn.commit()

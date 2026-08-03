import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional

import config
from .schema import init_db


class Repository:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = config.DB_PATH
        init_db()
        # timeout=30.0: wait up to 30 seconds for SQLite lock (cross-process locking)
        self._conn = sqlite3.connect(db_path, timeout=30.0)
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

    def get_receipt(self, receipt_id: str) -> Optional[dict]:
        """Retrieve a receipt by ID."""
        row = self._conn.execute(
            "SELECT * FROM receipts WHERE receipt_id = ?",
            (receipt_id,)
        ).fetchone()
        return dict(row) if row else None

    def find_receipts_by_filename(self, filename: str) -> list[dict]:
        """Every receipt with this original filename, case-insensitively.

        The fallback match for a back-feed note whose review sidecar carried no
        receipt id, per design document 12.3 step 2. Case-insensitive because
        Desktop leaves a filename as it found it and the pipeline lowercases the
        supplier part, so the two tools produce differently cased names for the
        same receipt. Returns every match: an ambiguous match is the caller's
        problem to refuse, not this method's to guess at.
        """
        if not filename:
            return []
        rows = self._conn.execute(
            "SELECT * FROM receipts WHERE LOWER(filename) = LOWER(?)",
            (filename,)
        ).fetchall()
        return [dict(row) for row in rows]

    def find_coa_account_by_name(self, account_name: str) -> Optional[dict]:
        """Look up a chart of accounts entry by name. None if there is no match.

        Design document 12.3 step 6. `coa_accounts` (5.5) is not created until step
        11 and not populated until step 12, so until then this returns None for
        every name, which 12.3 says is expected and not an error. Written so it
        starts working when the table arrives with no change here.

        Only the default scope. The client and group tiers in section 13 need the
        client_id and business_type to resolve safely, and that belongs to step 11's
        query layer rather than to a lookup that would otherwise be able to return
        another client's account.
        """
        if not account_name:
            return None
        try:
            row = self._conn.execute("""
                SELECT code, name FROM coa_accounts
                WHERE LOWER(name) = LOWER(?)
                  AND scope = 'default'
                  AND status = 'active'
                LIMIT 1
            """, (account_name,)).fetchone()
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc):
                return None
            raise
        return dict(row) if row else None

    def get_unfiled_ok_receipts(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT receipt_id, client_id, firm_id, client_code, source, file_path, filename FROM receipts WHERE status = 'ok' AND filed_path IS NULL"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_extraction_for_receipt(self, receipt_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM extractions WHERE receipt_id = ? ORDER BY extracted_at DESC LIMIT 1",
            (receipt_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_extractions_for_receipt(self, receipt_id: str) -> list[dict]:
        """Every extraction attempt for a receipt, newest first.

        The singular get_extraction_for_receipt() returns only the latest and is
        what the pipeline uses. The resolution view needs the whole history, so an
        operator can see what previous attempts read.
        """
        rows = self._conn.execute(
            "SELECT * FROM extractions WHERE receipt_id = ? ORDER BY extracted_at DESC",
            (receipt_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    def list_gl_code_options_from_vendors(self) -> list[dict]:
        """Distinct (nominal_code, account_name) pairs from both vendor tables.

        The fallback in design document 11.1, for use until the Default CoA is
        loaded into coa_accounts at step 12. Not the real option list: it only
        contains codes some vendor has already been mapped to.
        """
        rows = self._conn.execute("""
            SELECT nominal_code, account_name FROM categorisations_client_vendors
            WHERE nominal_code IS NOT NULL
            UNION
            SELECT nominal_code, account_name FROM categorisations_firm_vendors
            WHERE nominal_code IS NOT NULL
            ORDER BY nominal_code
        """).fetchall()
        return [{"nominal_code": r["nominal_code"], "account_name": r["account_name"]} for r in rows]

    def mark_receipt_filed(self, receipt_id: str, filed_path: str):
        """Record where a receipt was filed, and when.

        The only writer of filed_path, and therefore the only writer of filed_at,
        so the two cannot disagree. Design document 5.1a.
        """
        self._conn.execute(
            "UPDATE receipts SET filed_path = ?, filed_at = ? WHERE receipt_id = ?",
            (str(filed_path), datetime.now(timezone.utc).isoformat(), receipt_id)
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
        currency, raw_response, validation_status, validation_notes,
        pipeline_version=None, receipt_ref_number=None, receipt_time=None,
        update_status=True, details=None
    ):
        """Append an extraction row. Extractions are never modified in place.

        details records the amendments post-processing made to this extraction,
        for example auto_treated_amount_as_gross(...) where an amount read as net
        was really the gross. The column existed but nothing wrote it, so those
        amendments to two financial figures went unrecorded. Deliberately separate
        from validation_notes: those are validation outcomes, these are changes the
        system made. See design document 3.11.

        update_status=False records the attempt without re-stamping
        receipts.status. The auto-retry exception path needs this: a crashed
        API call says something about the API, not about the document, so it
        must not flip a needs_review receipt to failed. Defaults to True so
        existing callers are unaffected.
        """
        now = datetime.now(timezone.utc).isoformat()
        notes_str = ", ".join(validation_notes) if validation_notes else None
        self._conn.execute("""
            INSERT INTO extractions
                (extraction_id, receipt_id, engine, extracted_at, supplier_name, invoice_date,
                 net_amount, vat_amount, gross_amount, currency, raw_response,
                 validation_status, validation_notes, pipeline_version, receipt_ref_number, receipt_time,
                 details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (extraction_id, receipt_id, engine, now, supplier_name, invoice_date,
              net_amount, vat_amount, gross_amount, currency, raw_response,
              validation_status, notes_str, pipeline_version, receipt_ref_number, receipt_time,
              details))
        if update_status:
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

    def count_receipts_by_status(self, statuses) -> int:
        """Count receipts in any of the given statuses. Empty sequence counts nothing."""
        statuses = tuple(statuses)
        if not statuses:
            return 0
        placeholders = ",".join("?" for _ in statuses)
        row = self._conn.execute(
            f"SELECT COUNT(*) FROM receipts WHERE status IN ({placeholders})",
            statuses,
        ).fetchone()
        return row[0] if row else 0

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

    def save_resolution_event(
        self, event_id: str, receipt_id: str, actor: str, source: str,
        action: str, outcome: str, created_at: str,
        extraction_id: Optional[str] = None, corrections_json: Optional[str] = None,
        gl_override_code: Optional[str] = None, reason: Optional[str] = None,
    ):
        """Append one audit row per resolution. Design document 5.1."""
        self._conn.execute("""
            INSERT INTO resolution_events
                (event_id, receipt_id, extraction_id, actor, source, action,
                 corrections_json, gl_override_code, outcome, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, receipt_id, extraction_id, actor, source, action,
              corrections_json, gl_override_code, outcome, reason, created_at))
        self._conn.commit()

    def list_resolution_events(self, receipt_id: str) -> list[dict]:
        """Every resolution event for a receipt, newest first."""
        rows = self._conn.execute(
            "SELECT * FROM resolution_events WHERE receipt_id = ? ORDER BY created_at DESC",
            (receipt_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    def get_categorisation(self, categorisation_id: str) -> Optional[dict]:
        """Retrieve categorisation record by ID."""
        row = self._conn.execute(
            "SELECT * FROM categorisations WHERE categorisation_id = ?",
            (categorisation_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_categorisation_for_receipt(self, receipt_id: str) -> Optional[dict]:
        """Retrieve the most recent categorisation for a receipt."""
        row = self._conn.execute(
            "SELECT * FROM categorisations WHERE receipt_id = ? ORDER BY categorised_at DESC LIMIT 1",
            (receipt_id,)
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

    def has_alert_been_sent(self, message_id: str, alert_type: str) -> bool:
        """Check if an alert of this type has already been sent for this message."""
        row = self._conn.execute(
            "SELECT 1 FROM email_alerts WHERE message_id = ? AND alert_type = ?",
            (message_id, alert_type)
        ).fetchone()
        return row is not None

    def record_alert_sent(self, message_id: str, alert_type: str, recipient_email: str, firm_name: str):
        """Record that an alert was sent."""
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT INTO email_alerts (message_id, alert_type, recipient_email, firm_name, alert_sent_at)
            VALUES (?, ?, ?, ?, ?)
        """, (message_id, alert_type, recipient_email, firm_name, now))
        self._conn.commit()

    # Part 1: Auto-retry on version change

    def find_failed_by_version(self, current_version: str, stale_lock_cutoff) -> list:
        """Find receipts with failed/needs_review status whose extractions are older than current_version.

        Returns receipts that need retrying, including those with stale locks (older than stale_lock_cutoff).
        The caller should use acquire_receipt_lock() to atomically claim each receipt, which respects
        the stale-lock recovery window. This query just avoids pre-filtering them out.

        Args:
            current_version: Current git short-hash (pipeline version)
            stale_lock_cutoff: datetime cutoff; locks older than this are considered abandoned
        """
        rows = self._conn.execute("""
            SELECT r.receipt_id, r.client_code, r.firm_id, r.client_id, r.filename, r.file_path,
                   r.message_id, r.status, r.locked_at, r.created_at
            FROM receipts r
            INNER JOIN extractions e ON r.receipt_id = e.receipt_id
            WHERE r.status IN ('failed', 'needs_review')
              AND (r.locked_at IS NULL OR r.locked_at < ?)
              AND (
                (SELECT e2.pipeline_version FROM extractions e2 WHERE e2.receipt_id = r.receipt_id ORDER BY e2.extracted_at DESC LIMIT 1) IS NULL
                OR
                (SELECT e2.pipeline_version FROM extractions e2 WHERE e2.receipt_id = r.receipt_id ORDER BY e2.extracted_at DESC LIMIT 1) != ?
              )
            GROUP BY r.receipt_id
            ORDER BY r.created_at ASC
        """, (stale_lock_cutoff, current_version)).fetchall()

        return [dict(row) for row in rows]

    # Part 2B: Duplicate detection & Part 3: Locking

    def find_by_transaction_loose(self, supplier_name: str, invoice_date: str, gross_amount: float,
                                   case_insensitive: bool = True, amount_tolerance: float = 0.01) -> str:
        """Find receipt matching supplier + date + amount (with tolerance).

        Used for semantic duplicate detection. Loosened matching with case-insensitive supplier
        and ±tolerance on amount to reduce false positives.

        Returns receipt_id if found, None otherwise.
        """
        if not supplier_name:
            return None

        supplier_search = supplier_name.strip().lower() if case_insensitive else supplier_name.strip()
        min_amount = gross_amount - amount_tolerance
        max_amount = gross_amount + amount_tolerance

        # Build query based on whether we have invoice_date
        if invoice_date:
            # Match on supplier + date + amount
            query = """
                SELECT r.receipt_id
                FROM receipts r
                INNER JOIN extractions e ON r.receipt_id = e.receipt_id
                WHERE (LOWER(e.supplier_name) = ? OR e.supplier_name = ?)
                  AND e.invoice_date = ?
                  AND e.gross_amount BETWEEN ? AND ?
                  AND r.filed_path IS NOT NULL
                LIMIT 1
            """
            row = self._conn.execute(query, (supplier_search, supplier_name, invoice_date, min_amount, max_amount)).fetchone()
        else:
            # Match on supplier + amount only (no date)
            query = """
                SELECT r.receipt_id
                FROM receipts r
                INNER JOIN extractions e ON r.receipt_id = e.receipt_id
                WHERE (LOWER(e.supplier_name) = ? OR e.supplier_name = ?)
                  AND e.gross_amount BETWEEN ? AND ?
                  AND r.filed_path IS NOT NULL
                LIMIT 1
            """
            row = self._conn.execute(query, (supplier_search, supplier_name, min_amount, max_amount)).fetchone()

        return row[0] if row else None

    def set_duplicate_of(self, receipt_id: str, duplicate_of_receipt_id: str):
        """Mark a receipt as a possible duplicate of another."""
        self._conn.execute(
            "UPDATE receipts SET duplicate_of = ? WHERE receipt_id = ?",
            (duplicate_of_receipt_id, receipt_id)
        )
        self._conn.commit()

    def is_recorded_and_filed(self, receipt_id: str) -> bool:
        """Check if a receipt is genuinely filed (has filed_path set)."""
        row = self._conn.execute(
            "SELECT filed_path FROM receipts WHERE receipt_id = ?",
            (receipt_id,)
        ).fetchone()
        return row and row[0] is not None

    # Part 3: Locking for manual resolution

    def acquire_receipt_lock(self, receipt_id: str, allow_stale_after_minutes: int = 60) -> bool:
        """Acquire lock on receipt. Returns True if successful, False if held by another process.

        Allows recovery of stale locks older than allow_stale_after_minutes (Part 1 can proceed).
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=allow_stale_after_minutes)

        cursor = self._conn.cursor()
        cursor.execute("""
            UPDATE receipts
            SET locked_at = ?
            WHERE receipt_id = ?
              AND (locked_at IS NULL OR locked_at < ?)
        """, (datetime.now(timezone.utc), receipt_id, cutoff))
        self._conn.commit()

        return cursor.rowcount == 1

    def release_receipt_lock(self, receipt_id: str):
        """Release lock on receipt."""
        self._conn.execute(
            "UPDATE receipts SET locked_at = NULL WHERE receipt_id = ?",
            (receipt_id,)
        )
        self._conn.commit()

    # add_validation_note() was removed at step 9. It ran
    # `UPDATE extractions SET validation_notes = ?` on an existing row, which
    # CLAUDE.md forbids: extractions are append-only and never modified after
    # creation. Its last caller was resolve_receipt.py, and the resolution service
    # now appends a new extraction row instead, per design document 4.3 step 6.
    # Deliberately not left in place as a convenience: a tempting mutation in the
    # repository is how the rule gets broken again.

    def update_receipt_status(self, receipt_id: str, status: str):
        """Update receipt status."""
        self._conn.execute(
            "UPDATE receipts SET status = ? WHERE receipt_id = ?",
            (status, receipt_id)
        )
        self._conn.commit()

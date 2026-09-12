import sqlite3
import sys

import config
from worker import london_time

# config.DB_PATH is the one place the database path lives. This script used to
# open Path("data/receipts.db"), a path amendment 76 removed, and an sqlite
# connection to a missing file SUCCEEDS and creates an empty database, so it
# reported no receipts instead of saying it could not find any. Outstanding item
# 158, fixed 2026-09-04.
db = config.DB_PATH
if not db.exists():
    sys.exit(f"no database at {db}. Set INTELLIBILLS_UNSYNCED_ROOT if it has moved.")
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Store UTC, show London: Paul's decision of 2026-09-11. Both timestamp
# columns below go through `london_time.stamp()`, which puts BST or GMT on
# the end, so the two 01:30s on the last Sunday in October read differently
# on the screen even though they are one hour apart in the column.
print(f"=== RECEIPTS ===  (times in {london_time.ZONE_LABEL})")
for row in c.execute("""
    SELECT receipt_id, filename, source, message_id, email_subject, email_from, email_received_at, status, created_at
    FROM receipts
    ORDER BY created_at DESC
"""):
    message_id = row['message_id'] or ""
    email_from = row['email_from'] or ""
    email_subject = row['email_subject'] or ""
    filename = row['filename'] or ""
    source = row['source'] or ""
    status = row['status'] or ""
    received = london_time.stamp(row['email_received_at'])
    created = london_time.stamp(row['created_at'])
    print(f"{row['receipt_id'][:8]}... {filename:<30} {source:<8} {message_id:<25} {email_from:<30} {email_subject:<35} {received:<24} {status:<15} {created}")

print(f"\n=== EMAIL ATTACHMENT MAPPING ===  (times in {london_time.ZONE_LABEL})")
for row in c.execute("""
    SELECT p.message_id, p.attachment_id, p.receipt_id, r.filename, r.email_from, r.email_subject, r.email_received_at, r.status
    FROM processed_attachments p
    LEFT JOIN receipts r ON p.receipt_id = r.receipt_id
    ORDER BY p.processed_at DESC
"""):
    received = london_time.stamp(row['email_received_at'])
    print(f"{row['message_id']:<25} {row['attachment_id']:<40} {row['receipt_id'][:8]}... {row['filename']:<30} {row['email_from']:<30} {row['email_subject']:<35} {received:<24} {row['status']}")

print("\n=== EXTRACTIONS (needs_review) ===")
for row in c.execute("""
    SELECT r.receipt_id, r.filename, e.supplier_name, e.gross_amount, e.validation_notes
    FROM extractions e
    JOIN receipts r ON e.receipt_id = r.receipt_id
    WHERE e.validation_status = 'needs_review'
    ORDER BY e.extracted_at DESC
"""):
    print(f"{row[0][:8]}... {row[1]:<20} {row[2]:<20} £{row[3]} — {row[4]}")

conn.close()

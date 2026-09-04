import csv
import sqlite3
import sys
from pathlib import Path

import config

# config.DB_PATH is the one place the database path lives. This script used to
# open Path("data/receipts.db"), a path amendment 76 removed, and an sqlite
# connection to a missing file SUCCEEDS and creates an empty database, so this
# export wrote a CSV with a header and no rows rather than saying it could not
# find the database. Outstanding item 158, fixed 2026-09-04.
db = config.DB_PATH
if not db.exists():
    sys.exit(f"no database at {db}. Set INTELLIBILLS_UNSYNCED_ROOT if it has moved.")

# Relative to the working directory, and the folder is created rather than
# assumed: it is not in the repository and this script used to fail on open.
output = Path("exports/bookkeeping_export.csv")
output.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

rows = c.execute("""
    SELECT
        r.receipt_id,
        r.firm_id,
        r.client_id,
        e.supplier_name,
        e.invoice_date,
        e.net_amount,
        e.vat_amount,
        e.gross_amount,
        e.currency,
        r.status,
        MIN(e.extracted_at) as first_extracted_at,
        MAX(e.validation_status) as latest_validation_status,
        MAX(e.validation_notes) as latest_review_reason
    FROM receipts r
    LEFT JOIN extractions e ON r.receipt_id = e.receipt_id
    GROUP BY r.receipt_id
    ORDER BY r.created_at DESC
""").fetchall()

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "receipt_id", "firm_id", "client_id",
        "supplier_name", "invoice_date",
        "net_amount", "vat_amount", "gross_amount", "currency",
        "status", "first_extracted_at", "latest_validation_status", "latest_review_reason"
    ])
    for row in rows:
        writer.writerow(row)

print(f"Exported {len(rows)} receipts to {output}")
conn.close()

import sqlite3
import sys

import config

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

print("=== ALL RECEIPTS WITH EXTRACTIONS ===\n")
for receipt in c.execute("SELECT * FROM receipts ORDER BY created_at DESC"):
    print(f"Receipt ID: {receipt['receipt_id']}")
    print(f"  File: {receipt['filename']}")
    print(f"  Status: {receipt['status']}")
    print(f"  Created: {receipt['created_at']}")

    extraction = c.execute(
        "SELECT * FROM extractions WHERE receipt_id = ? ORDER BY extracted_at DESC LIMIT 1",
        (receipt['receipt_id'],)
    ).fetchone()

    if extraction:
        print(f"  Supplier: {extraction['supplier_name']}")
        print(f"  Date: {extraction['invoice_date']}")
        print(f"  Net: £{extraction['net_amount']}")
        print(f"  VAT: £{extraction['vat_amount']}")
        print(f"  Gross: £{extraction['gross_amount']}")
        print(f"  Currency: {extraction['currency']}")
        print(f"  Validation: {extraction['validation_status']}")
        if extraction['validation_notes']:
            print(f"  Notes: {extraction['validation_notes']}")
    print()

conn.close()

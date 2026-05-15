import sqlite3
from pathlib import Path

db = Path("data/receipts.db")
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

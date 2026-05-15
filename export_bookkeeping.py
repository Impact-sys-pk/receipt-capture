import csv
import sqlite3
from pathlib import Path

db = Path("data/receipts.db")
output = Path("exports/bookkeeping_export.csv")

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

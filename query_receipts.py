import sqlite3
from pathlib import Path

db = Path("data/receipts.db")
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=== RECEIPTS ===")
for row in c.execute("SELECT receipt_id, filename, status, created_at FROM receipts ORDER BY created_at DESC"):
    print(f"{row['receipt_id'][:8]}... {row['filename']:<30} {row['status']:<15} {row['created_at']}")

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

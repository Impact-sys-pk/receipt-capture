import sqlite3
from pathlib import Path

db = Path("data/receipts.db")
conn = sqlite3.connect(db)
c = conn.cursor()

tables = [
    ("receipts", "One record per attachment"),
    ("extractions", "Extraction results (append-only, can have multiple per receipt)"),
    ("processed_attachments", "Duplicate prevention tracking"),
    ("email_delta", "State tracking (delta links, UIDs)"),
]

for table_name, desc in tables:
    print(f"\n{'='*60}")
    print(f"TABLE: {table_name}")
    print(f"DESCRIPTION: {desc}")
    print(f"{'='*60}")

    c.execute(f"PRAGMA table_info({table_name})")
    for col in c.fetchall():
        cid, name, type_, notnull, default, pk = col
        pk_marker = " [PK]" if pk else ""
        print(f"  {name:<25} {type_:<15}{pk_marker}")

conn.close()

import csv
import sqlite3
import sys

import config

# config.DB_PATH is the one place the database path lives. This script used to
# open Path("data/receipts.db"), a path amendment 76 removed, and an sqlite
# connection to a missing file SUCCEEDS and creates an empty database, so this
# export wrote a CSV with a header and no rows rather than saying it could not
# find the database. Outstanding item 158, fixed 2026-09-04.
db = config.DB_PATH
if not db.exists():
    sys.exit(f"no database at {db}. Set INTELLIBILLS_UNSYNCED_ROOT if it has moved.")

#: Where the export is written. **Derived from `config.BASE_DIR` rather than
#: written relative to the working directory**, so running this from anywhere
#: but the repository root still writes here rather than scattering an
#: `exports\` wherever the shell happened to be standing. Flag 5 of the step 10n
#: report and Paul's decision of 2026-09-11; `capture_report.py` already did
#: this and its `OUTPUT_DIR` carries the reasoning for the folder itself.
#:
#: The folder is created rather than assumed: it is not in the repository, it is
#: gitignored, and this script used to fail on open.
OUTPUT_DIR = config.BASE_DIR / "exports"
output = OUTPUT_DIR / "bookkeeping_export.csv"
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
        # `first_extracted_at` keeps the stored UTC value and the stored
        # column name. **This CSV is a handoff format**, its headers are the
        # database's own column names, and nothing in this repository reads it
        # back, so converting a column while leaving its name alone would make
        # the file disagree with the column it claims to carry. Store UTC, show
        # London applies to what a person reads on a screen or in a report;
        # this is neither. Reported as a decision rather than taken quietly, per
        # section 2 of the brief of 2026-09-11.
        "status", "first_extracted_at", "latest_validation_status", "latest_review_reason"
    ])
    for row in rows:
        writer.writerow(row)

print(f"Exported {len(rows)} receipts to {output}")
conn.close()

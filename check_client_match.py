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
rows = conn.execute('SELECT firm_id, client_id, email_from, filename FROM receipts ORDER BY created_at').fetchall()

print('=== Client ID Matching Results ===')
print()
for row in rows:
    print(f'{row["firm_id"]:12} {row["client_id"]:12} {row["email_from"]:35} {row["filename"][:40]}')

conn.close()

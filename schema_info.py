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
c = conn.cursor()

# All ten tables in worker/database/schema.py, which is the authority. This list
# named four of them until 2026-09-04, so seven tables could be in the database
# and absent from this script's output. Item 158. email_delta was removed from
# the schema the same day by item 159; a database created before then still
# holds it, empty, and it will simply not be listed here.
tables = [
    ("receipts", "One row per attachment or inbox file"),
    ("extractions", "Extraction results, append-only, many per receipt"),
    ("categorisations", "One row per categorisation, with the correction beside the suggestion"),
    ("statements", "PHV platform statements: uber, bolt, freenow. Never a bank statement"),
    ("processed_attachments", "Duplicate prevention, keyed (message_id, attachment_id)"),
    ("resolution_events", "The audit trail: one row per resolution, whatever the entry point"),
    ("email_alerts", "One row per alert sent, keyed (message_id, alert_type)"),
    ("categorisations_client_vendors", "Layer 1: this client's learned mappings"),
    ("categorisations_firm_vendors", "Layer 2: the firm's shared pool"),
    ("categorisations_client_rules", "Layer 0: the rules a person authors by hand"),
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

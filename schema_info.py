import sqlite3
import sys

import config
from worker.database import schema

# config.DB_PATH is the one place the database path lives. This script used to
# open Path("data/receipts.db"), a path amendment 76 removed, and an sqlite
# connection to a missing file SUCCEEDS and creates an empty database, so it
# reported no receipts instead of saying it could not find any. Outstanding item
# 158, fixed 2026-09-04.

# **The tables come from worker/database/schema.py, which is the authority, and
# only their descriptions are kept here.** Flag F9, 2026-11-14. This script kept
# its own list of names until then, and it drifted twice: it named four of
# eleven tables until 2026-09-04, item 158, and it named
# categorisations_client_rules after step 10bu replaced it, until that commit
# corrected the list by hand. ~~tables = [("receipts", ...), ...]~~
#
# **Neither direction of drift passes silently.** A declared table with no entry
# here is still listed, marked NO_DESCRIPTION; an entry here for a table no
# longer declared is named; and either makes main() return 1.
# tests/test_schema_info.py also asserts these keys equal the declared tables,
# so the suite goes red first.
#
# email_delta was removed from the schema on 2026-09-04 by item 159; a database
# created before then still holds it, empty, and it is not listed here because
# it is not declared.
DESCRIPTIONS = {
    "receipts": "One row per attachment or inbox file",
    "extractions": "Extraction results, append-only, many per receipt",
    "categorisations": "One row per categorisation, with the correction beside the suggestion",
    "statements": "PHV platform statements: uber, bolt, freenow. Never a bank statement",
    "processed_attachments": "Duplicate prevention, keyed (message_id, attachment_id)",
    "resolution_events": "The audit trail: one row per resolution, whatever the entry point",
    "publish_events": "One row per publish attempt, per receipt per destination. 10f.36",
    "email_alerts": "One row per alert sent, keyed (message_id, alert_type)",
    "categorisations_client_vendors": "Layer 1: this client's learned mappings",
    "categorisations_firm_vendors": "Layer 2: the firm's shared pool",
    # ~~categorisations_client_rules~~, replaced by step 10bu on 2026-11-14. A
    # database created before then still holds that table, empty.
    "categorisation_rules": "Layer 0: the rules a person authors, scoped client, firm or sector",
    "rule_mapping_events": "Audit trail, append-only: every rule and mapping write or refusal. F8",
}

NO_DESCRIPTION = "NO DESCRIPTION in schema_info.py: add one to DESCRIPTIONS"


def compare(declared, descriptions):
    """(tables to list with their descriptions, declared but undescribed,
    described but no longer declared). Every list is sorted."""
    listed = [(table, descriptions.get(table, NO_DESCRIPTION)) for table in sorted(declared)]
    undescribed = sorted(set(declared) - set(descriptions))
    stale = sorted(set(descriptions) - set(declared))
    return listed, undescribed, stale


def main() -> int:
    db = config.DB_PATH
    if not db.exists():
        sys.exit(f"no database at {db}. Set INTELLIBILLS_UNSYNCED_ROOT if it has moved.")
    listed, undescribed, stale = compare(schema.declared_columns(), DESCRIPTIONS)
    conn = sqlite3.connect(db)
    try:
        c = conn.cursor()
        for table_name, desc in listed:
            print(f"\n{'='*60}")
            print(f"TABLE: {table_name}")
            print(f"DESCRIPTION: {desc}")
            print(f"{'='*60}")

            c.execute(f"PRAGMA table_info({table_name})")
            for col in c.fetchall():
                cid, name, type_, notnull, default, pk = col
                pk_marker = " [PK]" if pk else ""
                print(f"  {name:<25} {type_:<15}{pk_marker}")
    finally:
        conn.close()

    if undescribed:
        print(f"\nschema_info.py is out of step: declared with no description: "
              f"{', '.join(undescribed)}")
    if stale:
        print(f"\nschema_info.py is out of step: described but no longer declared: "
              f"{', '.join(stale)}")
    return 1 if undescribed or stale else 0


if __name__ == "__main__":
    sys.exit(main())

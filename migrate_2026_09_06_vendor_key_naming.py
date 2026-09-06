"""One-off migration for the vendor_key / vendor_code naming correction.

Paul's brief of 2026-09-06. Two different things happen here, and they are
deliberately different operations:

  * The three learned tables are DROPPED and recreated from schema.py. Paul's
    decision: they held one row between them, made the same morning, and he can
    remake it with the review fixture in three minutes. No data migration, no
    copy to test against.

  * `categorisations` is NOT dropped. Its rows carry the correction history,
    including the one that proves 10j.11 works. Its `vendor_key` column is NULL
    on every row, so ALTER TABLE ... RENAME COLUMN moves no data.

Run once. Running it twice drops the learned tables again, so it prints the row
counts it is about to destroy and does nothing without --yes.
"""

import sqlite3
import sys

import config
from worker.database import schema

LEARNED_TABLES = (
    "categorisations_client_vendors",
    "categorisations_firm_vendors",
    "categorisations_client_rules",
)


def main(confirmed: bool) -> int:
    con = sqlite3.connect(config.DB_PATH)
    try:
        print(f"database: {config.DB_PATH}")
        for table in LEARNED_TABLES + ("categorisations",):
            try:
                n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            except sqlite3.OperationalError:
                n = "no such table"
            print(f"  before  {table:34} {n}")

        if not confirmed:
            print("\nnothing done. Re-run with --yes to drop the three learned tables.")
            return 1

        for table in LEARNED_TABLES:
            con.execute(f"DROP TABLE IF EXISTS {table}")
        print("\ndropped the three learned tables, and their indexes with them")

        cols = [r[1] for r in con.execute("PRAGMA table_info(categorisations)")]
        if "vendor_key" in cols:
            con.execute(
                "ALTER TABLE categorisations RENAME COLUMN vendor_key TO mapping_id"
            )
            print("renamed categorisations.vendor_key -> mapping_id")
        else:
            print("categorisations.vendor_key already gone, nothing renamed")
        con.commit()
    finally:
        con.close()

    schema.init_db()
    print("init_db() recreated the three tables under the new column names")
    return 0


if __name__ == "__main__":
    sys.exit(main("--yes" in sys.argv))

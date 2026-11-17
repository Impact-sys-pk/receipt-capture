r"""Rename the client's sector column on two tables. Item 40, pipeline half.

Paul's instruction of 2026-11-17: one word for the client's sector, and it is
`sector`. `PROMPT_claude_code_2026-11-17_push_f1_test_and_sector_rename.md`.

**`worker/database/schema.py` only ever CREATEs**, so a database that already
exists keeps its old column names when the statements there change. A fresh
database created after this date has the new names; an existing one needs this.
**Until it runs, the pipeline refuses to start**: `schema_drift_message()` sees
the declared `sector` columns missing and `app.py` stops on it.

## What it does

Two renames, and nothing else:

    ALTER TABLE categorisations_firm_vendors RENAME COLUMN business_type TO sector
    ALTER TABLE categorisations RENAME COLUMN trade TO sector

**A rename moves every value with it**, and SQLite rewrites the firm pool's
UNIQUE key and `idx_firm_vendor_key` to the new name in the same statement.
Nothing is copied, nothing is defaulted, and no row is added or removed. The
script checks all of that after it writes rather than trusting it: the row
counts, the values column by column against what was read before, the old names
gone and the index on `sector`.

**Not rewritten: `rule_mapping_events.before_json` and `after_json`.** An audit
row written before today records the firm pool row as it was, with the key
`business_type`, and that is true of its date. A history rewritten to tidy a
key name is a history that is no longer true.

**It is idempotent.** A table whose column is already `sector` is reported and
left alone, so a second run changes nothing.

## Running it

    cd C:\LastingImpact\receipt_capture
    .\.venv\Scripts\python.exe migrate_2026_11_17_sector.py
    .\.venv\Scripts\python.exe migrate_2026_11_17_sector.py --write

**A dry run is the default and `--write` is required to change anything.**
**Stop the pipeline first**, and the script takes its own backup beside the
database before it writes and names the path. `--db PATH` rehearses on a copy.
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

NEW = "sector"
#: (table, old column name). Named here and nowhere else in production Python.
RENAMES = (
    ("categorisations_firm_vendors", "business_type"),
    ("categorisations", "trade"),
)
INDEX = "idx_firm_vendor_key"


def columns(conn, table):
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def snapshot(conn, table, column):
    """Every row's primary key and value in `column`, in a fixed order."""
    key = columns(conn, table)[0]
    return conn.execute(
        f"SELECT {key}, {column} FROM {table} ORDER BY {key}").fetchall()


def build_parser():
    parser = argparse.ArgumentParser(
        description="Rename business_type and trade to sector. Item 40.")
    parser.add_argument("--write", action="store_true",
                        help="actually rename. Without it this is a dry run.")
    parser.add_argument("--dry-run", action="store_true",
                        help="the default. Prints what would happen and changes nothing.")
    parser.add_argument("--db", metavar="PATH", default=None,
                        help="a database other than config.DB_PATH, for rehearsing on a copy.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.db:
        db_path = Path(args.db)
    else:
        # Imported only here, so a rehearsal with --db never reads .env or runs
        # config's folder creation.
        import config
        db_path = config.DB_PATH
    if not db_path.exists():
        print(f"no database at {db_path}. "
              "Set INTELLIBILLS_UNSYNCED_ROOT if it has moved.")
        return 1

    conn = sqlite3.connect(db_path)
    try:
        print(f"database   {db_path}")
        todo = []
        for table, old in RENAMES:
            have = columns(conn, table)
            rows = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if not have:
                print(f"{table}: no such table, nothing to rename")
            elif NEW in have and old not in have:
                print(f"{table}: already has {NEW}, {rows} row(s), nothing to do")
            elif old in have and NEW not in have:
                print(f"{table}: {old} -> {NEW}, {rows} row(s)")
                todo.append((table, old))
            else:
                print(f"{table}: has {old} and {NEW} both, or neither. "
                      "NOT TOUCHED: this is not a shape this script knows.")
                return 1

        if not todo:
            print("\nNothing to do.")
            return 0
        if not args.write:
            print("\nDRY RUN. Nothing was changed. Re-run with --write to apply it, "
                  "after stopping the pipeline.")
            return 0

        before = {table: snapshot(conn, table, old) for table, old in todo}
        conn.close()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup = db_path.with_name(f"{db_path.stem}-backup-{stamp}-pre-sector{db_path.suffix}")
        shutil.copy2(db_path, backup)
        print(f"\nbackup     {backup}")

        conn = sqlite3.connect(db_path)
        with conn:
            for table, old in todo:
                conn.execute(f"ALTER TABLE {table} RENAME COLUMN {old} TO {NEW}")

        wrong = []
        for table, old in todo:
            after = snapshot(conn, table, NEW)
            have = columns(conn, table)
            print(f"{table}: columns now {', '.join(have)}")
            print(f"{table}: {len(before[table])} row(s) before, {len(after)} after, "
                  f"values {'identical' if after == before[table] else 'DIFFERENT'}")
            if after != before[table] or old in have or NEW not in have:
                wrong.append(table)
        index = [row[2] for row in conn.execute(f"PRAGMA index_info('{INDEX}')")]
        print(f"{INDEX}: on {', '.join(index) or '(no such index)'}")
        if index and index[0] != NEW:
            wrong.append(INDEX)

        if wrong:
            print(f"\nTHAT IS NOT WHAT WAS EXPECTED, on {', '.join(wrong)}. "
                  "The backup above is the database as it was.")
            return 1
        print("\nDone.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

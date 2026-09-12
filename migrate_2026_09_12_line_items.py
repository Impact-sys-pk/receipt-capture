r"""Add `extractions.line_items`. Step 10p part one, amendment 340.

**`worker/database/schema.py` only ever CREATEs**, so a database that already
exists does not gain a column when the statement there changes. A fresh
database created after this date has the column; an existing one needs this.

## What it does and does not do

**It adds one column and nothing else.** `ALTER TABLE extractions ADD COLUMN
line_items TEXT`. Every existing row is left holding NULL, which reads as "no
item lines" through `worker/line_items.py`.

**NOTHING IS BACKFILLED and nothing can be.** Paul's instruction of 2026-09-12:
he does not care about the receipts already in the database. Their item lines
were read once, passed to the classifier in memory and dropped, and there is no
record of them anywhere to recover them from. A backfill would have to
re-extract, which costs money per receipt and would overwrite readings a person
may since have corrected.

**It is idempotent.** Run twice, the second run reports the column is already
there and changes nothing.

## Running it

    cd C:\LastingImpact\receipt_capture
    .\.venv\Scripts\python.exe migrate_2026_09_12_line_items.py --dry-run
    .\.venv\Scripts\python.exe migrate_2026_09_12_line_items.py --write

**`--dry-run` is the default and `--write` is required to change anything**, so
the command that does something cannot be reached by pressing return. The
dry run prints the statement it would execute, the row count and the columns as
they stand.

**Back the database up first.** `Intellibills\Backups\` holds the daily copies
the pipeline makes; this takes its own before it writes, beside the database,
and names the path it wrote.

**Stop the pipeline first.** SQLite will let two processes write, and a
migration racing a poll is not a risk worth taking for the sake of not closing
a window.
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import config

TABLE = "extractions"
COLUMN = "line_items"
STATEMENT = f"ALTER TABLE {TABLE} ADD COLUMN {COLUMN} TEXT"


def columns(conn, table):
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def build_parser():
    parser = argparse.ArgumentParser(
        description=f"Add {TABLE}.{COLUMN}. Step 10p part one, amendment 340.",
        epilog="Nothing is backfilled: existing rows keep NULL, which reads as "
               "no item lines.",
    )
    parser.add_argument(
        "--write", action="store_true",
        help="actually alter the table. Without it this is a dry run.")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="the default. Prints what would happen and changes nothing.")
    parser.add_argument(
        "--db", metavar="PATH", default=None,
        help="a database other than config.DB_PATH, for rehearsing on a copy.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    db_path = Path(args.db) if args.db else config.DB_PATH
    if not db_path.exists():
        print(f"no database at {db_path}. "
              "Set INTELLIBILLS_UNSYNCED_ROOT if it has moved.")
        return 1

    conn = sqlite3.connect(db_path)
    try:
        before = columns(conn, TABLE)
        rows = conn.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]

        print(f"database   {db_path}")
        print(f"table      {TABLE}, {rows} row(s)")
        print(f"columns    {', '.join(before)}")
        print(f"statement  {STATEMENT}")

        if COLUMN in before:
            print(f"\nNothing to do: {TABLE}.{COLUMN} already exists.")
            return 0

        if not args.write:
            print("\nDRY RUN. Nothing was changed. Re-run with --write to "
                  "apply it, after stopping the pipeline and taking a backup.")
            return 0

        # Its own backup, beside the database, named for the migration. The
        # daily copies in Intellibills\Backups\ are a different thing and are
        # taken on the pipeline's schedule rather than on this one's.
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup = db_path.with_name(
            f"{db_path.stem}-backup-{stamp}-pre-{COLUMN}{db_path.suffix}")
        shutil.copy2(db_path, backup)
        print(f"\nbackup     {backup}")

        conn.execute(STATEMENT)
        conn.commit()

        after = columns(conn, TABLE)
        rows_after = conn.execute(f"SELECT COUNT(*) FROM {TABLE}").fetchone()[0]
        filled = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE {COLUMN} IS NOT NULL"
        ).fetchone()[0]

        print(f"columns    {', '.join(after)}")
        print(f"rows       {rows_after} before and after: {rows} -> {rows_after}")
        print(f"{COLUMN} filled on {filled} row(s), which must be 0: "
              "nothing is backfilled")
        if rows_after != rows or filled != 0 or COLUMN not in after:
            print("\nTHAT IS NOT WHAT WAS EXPECTED. The backup above is the "
                  "database as it was.")
            return 1
        print("\nDone.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

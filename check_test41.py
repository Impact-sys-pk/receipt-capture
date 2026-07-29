"""Read-only status check for test 41, the resolution back-feed round trip.

Prints what the test-41 walkthrough needs at step 3 (full receipt ids, before
going into Desktop) and again at step 11 (statuses, filed paths, resolution
events, and where the notes ended up). Safe to run at any point, including
while the pipeline is running: it opens the database read-only and writes
nothing anywhere.

    python check_test41.py
"""

import sqlite3
from pathlib import Path

import config

DB = Path("data/receipts.db")


def main() -> None:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    print("=== RECEIPTS, newest first ===")
    rows = conn.execute(
        """
        SELECT receipt_id, filename, status, filed_path, created_at
        FROM receipts ORDER BY created_at DESC LIMIT 8
        """
    ).fetchall()
    for row in rows:
        print(f"\n  {row['receipt_id']}")
        print(f"    file    {row['filename']}")
        print(f"    status  {row['status']}")
        print(f"    filed   {row['filed_path'] or '(not filed)'}")

        latest = conn.execute(
            """
            SELECT engine, supplier_name, invoice_date, net_amount, vat_amount,
                   gross_amount, currency, validation_status, validation_notes
            FROM extractions WHERE receipt_id = ?
            ORDER BY extracted_at DESC LIMIT 1
            """,
            (row["receipt_id"],),
        ).fetchone()
        if latest is None:
            print("    read    (no extraction)")
            continue

        def money(value):
            return "-" if value is None else f"{value:.2f}"

        print(
            f"    read    {latest['supplier_name']} | {latest['invoice_date']} | "
            f"net {money(latest['net_amount'])} vat {money(latest['vat_amount'])} "
            f"gross {money(latest['gross_amount'])} {latest['currency']}"
        )
        print(f"    engine  {latest['engine']} -> {latest['validation_status']}")
        if latest["validation_notes"]:
            print(f"    notes   {latest['validation_notes']}")

    print("\n=== RESOLUTION EVENTS ===")
    events = conn.execute(
        """
        SELECT receipt_id, outcome, actor, source, created_at
        FROM resolution_events ORDER BY created_at DESC LIMIT 8
        """
    ).fetchall()
    if not events:
        print("  none yet")
    for event in events:
        print(
            f"  {event['receipt_id'][:8]}...  {event['outcome']:<14} "
            f"{event['actor']}/{event['source']}  {event['created_at']}"
        )

    conn.close()

    print("\n=== RESOLUTIONS FOLDER ===")
    base = config.RESOLUTIONS_DIR
    print(f"  {base}")
    if not base.is_dir():
        print("  does not exist yet")
        return

    def listing(directory: Path, label: str, missing_is_good: bool = False) -> None:
        if not directory.is_dir():
            print(f"  {label}: does not exist" + (" (good)" if missing_is_good else ""))
            return
        names = sorted(path.name for path in directory.iterdir() if path.is_file())
        print(f"  {label}: {len(names)} file(s)")
        for name in names:
            print(f"      {name}")

    waiting = sorted(path.name for path in base.glob("*.json") if path.is_file())
    print(f"  waiting to be applied: {len(waiting)} file(s)")
    for name in waiting:
        print(f"      {name}")
    listing(base / "processed", "processed")
    listing(base / "failed", "failed", missing_is_good=True)


if __name__ == "__main__":
    main()

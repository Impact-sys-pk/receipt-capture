"""
Import pre-cleaned vendor CSV directly into the database.

CSV format: vendor_code,vendor_name,detail,nominal_code,account_name
"""

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import config
from worker.database.repository import Repository


def import_csv(csv_path: str, client_id: str):
    """Import vendor mappings from cleaned CSV."""
    repo = Repository()
    now = datetime.now(timezone.utc).isoformat()

    total_inserted = 0
    total_skipped = 0

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for i, row in enumerate(reader, start=2):
                # Handle both vendor_key (old) and vendor_code (new) column names
                vendor_code = row.get('vendor_code') or row.get('vendor_key')
                if not vendor_code:
                    total_skipped += 1
                    continue

                vendor_code = vendor_code.strip()
                vendor_name = row.get('vendor_name', '').strip()
                detail = row.get('detail', '').strip()
                nominal_code = row.get('nominal_code', '').strip()
                account_name = row.get('account_name', '').strip()

                if not vendor_code or not nominal_code:
                    total_skipped += 1
                    continue

                try:
                    repo.upsert_client_vendor(
                        client_id=client_id,
                        vendor_code=vendor_code,
                        nominal_code=nominal_code,
                        account_name=account_name,
                        vendor_name=vendor_name,
                        detail=detail,
                        last_updated=now
                    )
                    total_inserted += 1
                    print(f"[+] {vendor_code:30} -> {nominal_code} {account_name}")
                except Exception as e:
                    print(f"[-] Row {i}: {e}")
                    total_skipped += 1

    finally:
        repo.close()

    print(f"\n--- Import complete ---")
    print(f"Inserted: {total_inserted}")
    print(f"Skipped:  {total_skipped}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python import_vendor_csv.py <csv_path> <client_id>")
        print(r'Example: python import_vendor_csv.py "C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\categorisations_client_vendors_cleaned.csv" Client_006')
        sys.exit(1)

    csv_path = sys.argv[1]
    client_id = sys.argv[2]

    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    print(f"Importing: {csv_path}")
    print(f"Client ID: {client_id}\n")
    import_csv(csv_path, client_id)


if __name__ == "__main__":
    main()

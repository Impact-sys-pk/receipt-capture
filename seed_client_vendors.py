"""
Seed categorisations_client_vendors from a transaction CSV export.

Parses a CSV organized by GL code with vendor descriptions,
normalizes vendor names, and inserts mappings into the database.
"""

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import config
from worker.database.repository import Repository
# The engine's own key rule, 2026-11-13, Paul's decision. ~~A copy "embedded
# from engine.py to avoid openai import"~~, which had fallen behind it: it
# never had the rule keeping only the first word of a name of three or more,
# so it wrote keys the engine never computes and layer 1 could never find.
# `normalise` imports nothing but `re`, so this still loads no openai client.
from worker.categorisation.normalise import (
    extract_vendor_key,
    normalise_description,
)


def parse_transactions_csv(csv_path: str) -> dict[str, list[str]]:
    """Parse CSV grouped by GL code, return {gl_code: [vendor_descriptions]}."""
    gl_vendors = {}
    current_gl_code = None
    current_gl_name = None

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0].strip():
                continue

            first_col = row[0].strip()

            # Detect GL code line: "103 Fuel,,,""
            if first_col and first_col[0].isdigit() and len(first_col) <= 50:
                parts = first_col.split(None, 1)
                if len(parts) == 2 and parts[0].isdigit():
                    current_gl_code = parts[0]
                    current_gl_name = parts[1]
                    gl_vendors[current_gl_code] = (current_gl_name, [])
                    continue

            # Skip header and navigation rows
            if first_col in ("Date", "Up to top ↑", "Total"):
                continue

            # Transaction row: Date, Description, Debit, Credit
            if current_gl_code and len(row) >= 2:
                # Check if first column looks like a date
                date_str = first_col.strip()
                if "-" in date_str and len(date_str) <= 11:  # Date format check
                    vendor_desc = row[1].strip() if len(row) > 1 else None
                    if vendor_desc and vendor_desc not in ("Description", "Total"):
                        gl_vendors[current_gl_code][1].append(vendor_desc)

    return gl_vendors


def _detail_of(vendor_desc: str, gl_name: str) -> str:
    """The supplier name, with the account name suffix the export appends removed."""
    # Remove GL code/account name suffix from vendor description
    # CSV uses \xa0 (non-breaking space) as separator
    # e.g., "Bounce Back Loan (Loan Repayment)\xa0Bounce Back Loan" -> "Bounce Back Loan (Loan Repayment)"
    detail = vendor_desc

    # Try regular space first, then non-breaking space
    if vendor_desc.endswith(" " + gl_name):
        detail = vendor_desc[:-len(" " + gl_name)].strip()
    elif vendor_desc.endswith("\xa0" + gl_name):
        detail = vendor_desc[:-len("\xa0" + gl_name)].strip()

    # Also remove any trailing "paul keating:" prefix
    if detail.endswith(" Paul Keating:"):
        detail = detail[:-len(" Paul Keating:")].strip()
    return detail


def seed_database(client_id: str, gl_vendors: dict[str, list[str]]):
    """Seed categorisations_client_vendors with vendor mappings.

    **Skips on key AND name together, 2026-11-14, Paul's decision, amendment
    557.** ~~It skipped a key already seen within one nominal code~~, so a
    second name on the same key was never seeded, although the table is unique
    on `(client_id, vendor_key, vendor_name)` and layer 1 answers by name first
    since sub-step 10bs.9.

    **A name the source files under two different nominal codes is reported
    and not seeded.** It used to be upserted at each occurrence, so the row
    silently kept whichever code came last. Which one is right is a question
    for a person, so neither is written.
    """
    # First pass: every distinct (key, name), and every code each name is under.
    # Sorted on code, as before, so the printed order is unchanged.
    seen = {}            # (vendor_key, detail) -> (gl_code, gl_name), first met
    codes_for = {}       # detail -> {gl_code: gl_name}
    total_skipped = 0
    for gl_code, (gl_name, vendors) in sorted(gl_vendors.items()):
        for vendor_desc in vendors:
            detail = _detail_of(vendor_desc, gl_name)
            vendor_key = extract_vendor_key(normalise_description(detail))
            if not vendor_key:
                total_skipped += 1
                continue
            codes_for.setdefault(detail, {})[gl_code] = gl_name
            if (vendor_key, detail) in seen:
                total_skipped += 1
                continue
            seen[(vendor_key, detail)] = (gl_code, gl_name)

    conflicts = {name: codes for name, codes in codes_for.items() if len(codes) > 1}

    repo = Repository()
    now = datetime.now(timezone.utc).isoformat()
    total_inserted = 0
    try:
        for (vendor_key, detail), (gl_code, gl_name) in seen.items():
            if detail in conflicts:
                continue
            repo.upsert_client_vendor(
                client_id=client_id,
                vendor_key=vendor_key,
                nominal_code=gl_code,
                account_name=gl_name,
                vendor_name=detail,
                detail=detail,
                last_updated=now,
                source="seed_client_vendors",  # flag F8
            )
            total_inserted += 1
            print(f"[+] {client_id} | {vendor_key:20} | {detail:40} -> {gl_code}")
    finally:
        repo.close()

    if conflicts:
        print("\n--- Names under more than one nominal code: NOT SEEDED ---")
        for name in sorted(conflicts):
            codes = ", ".join(f"{code} {account}"
                              for code, account in sorted(conflicts[name].items()))
            print(f"[!] {name:40} | {codes}")

    print(f"\n--- Seeding complete ---")
    print(f"Inserted: {total_inserted}")
    print(f"Skipped:  {total_skipped}")
    print(f"Conflicting names, not seeded: {len(conflicts)}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python seed_client_vendors.py <csv_path> <client_id>")
        print("Example: python seed_client_vendors.py 'Test Receipts/transactions_sample.csv' Client_006")
        sys.exit(1)

    csv_path = sys.argv[1]
    client_id = sys.argv[2]

    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    print(f"Parsing: {csv_path}")
    gl_vendors = parse_transactions_csv(csv_path)
    print(f"Found {len(gl_vendors)} GL codes")

    print(f"\nSeeding database for client: {client_id}")
    seed_database(client_id, gl_vendors)


if __name__ == "__main__":
    main()

"""
Seed categorisations_client_vendors from a transaction CSV export.

Parses a CSV organized by GL code with vendor descriptions,
normalizes vendor names, and inserts mappings into the database.
"""

import csv
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

import config
from worker.database.repository import Repository

# Embedded from engine.py to avoid openai import
NOISE_WORDS = {
    "ltd", "limited", "plc", "inc", "co", "uk",
    "payment", "to", "from", "direct", "debit", "credit",
    "card", "visa", "mastercard", "contactless",
    "purchase", "pos", "online", "mobile",
    "london", "manchester", "birmingham",
    "the", "and", "of", "for", "in", "at", "on",
    "ref", "reference", "txn",
}

LOCATION_WORDS = {
    "dartford", "bromley", "swanley", "london", "croydon",
    "greenwich", "lewisham", "bexley", "sevenoaks", "maidstone",
    "orpington", "sidcup", "eltham", "woolwich", "erith",
    "stn", "serv", "station", "connect", "garage", "petrol",
    "express", "local", "extra", "superstore", "metro",
}

DEFAULT_ALIASES = {
    "amzn": "amazon", "amz": "amazon", "amazon.co.uk": "amazon",
    "pp": "paypal", "tfl": "tfl", "transport for london": "tfl",
    "sumup": "sumup", "sum up": "sumup",
    "google": "google", "goog": "google",
}

def normalise_description(raw: str) -> str:
    """Strip noise from a bank/receipt description to extract usable vendor name."""
    text = raw.lower().strip()
    text = re.sub(r"^(dd|so|bgo|bgc|chq|tfr|bp|fp|ddr)\s*[-–]\s*", "", text)
    text = text.replace("*", " ")
    text = re.sub(r"\b\d{6,}\b", "", text)
    text = re.sub(r"\b\d{1,2}\b", "", text)
    words = text.split()
    filtered = [w for w in words if w not in NOISE_WORDS and len(w) > 1]
    return " ".join(filtered)

def extract_vendor_code(normalised: str, aliases: dict = None) -> str:
    """Extract canonical vendor key from normalised description."""
    if aliases is None:
        aliases = DEFAULT_ALIASES
    if normalised in aliases:
        return aliases[normalised]
    words = normalised.split()
    if words and words[0] in aliases:
        return aliases[words[0]]
    words = [w for w in words if not w.isdigit()]
    core_words = [w for w in words if w not in LOCATION_WORDS]
    if not core_words and words:
        core_words = [words[0]]
    result = " ".join(core_words)
    return result if result else normalised


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


def seed_database(client_id: str, gl_vendors: dict[str, list[str]]):
    """Seed categorisations_client_vendors with vendor mappings."""
    repo = Repository()
    now = datetime.now(timezone.utc).isoformat()

    total_inserted = 0
    total_skipped = 0

    try:
        for gl_code, (gl_name, vendors) in sorted(gl_vendors.items()):
            vendor_codes_seen = set()

            for vendor_desc in vendors:
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

                # Extract and normalise vendor name
                normalised = normalise_description(detail)
                vendor_code = extract_vendor_code(normalised)

                # Skip empty keys and duplicates within this GL code
                if not vendor_code or vendor_code in vendor_codes_seen:
                    total_skipped += 1
                    continue

                vendor_codes_seen.add(vendor_code)

                # Upsert to database
                repo.upsert_client_vendor(
                    client_id=client_id,
                    vendor_code=vendor_code,
                    nominal_code=gl_code,
                    account_name=gl_name,
                    vendor_name=detail,
                    detail=detail,
                    last_updated=now
                )
                total_inserted += 1
                print(f"[+] {client_id} | {vendor_code:20} | {detail:40} -> {gl_code}")

    finally:
        repo.close()

    print(f"\n--- Seeding complete ---")
    print(f"Inserted: {total_inserted}")
    print(f"Skipped:  {total_skipped}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python seed_client_vendors.py <csv_path> [client_id]")
        print("Example: python seed_client_vendors.py 'Test Receipts/transactions_sample.csv' Client_001")
        sys.exit(1)

    csv_path = sys.argv[1]
    client_id = sys.argv[2] if len(sys.argv) > 2 else "Client_001"

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

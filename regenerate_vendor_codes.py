"""
Regenerate vendor_code from vendor_name using engine normalization logic.
This produces short, core merchant names suitable for lookups.
"""

import csv
import re
from pathlib import Path

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
    """Strip noise from description."""
    text = raw.lower().strip()
    text = re.sub(r"^(dd|so|bgo|bgc|chq|tfr|bp|fp|ddr)\s*[-–]\s*", "", text)
    text = text.replace("*", " ")
    text = re.sub(r"\b\d{6,}\b", "", text)
    text = re.sub(r"\b\d{1,2}\b", "", text)
    words = text.split()
    filtered = [w for w in words if w not in NOISE_WORDS and len(w) > 1]
    return " ".join(filtered)

def extract_vendor_key(normalised: str, aliases: dict = None) -> str:
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
    # For vendor code regeneration, take only first 1-2 words to avoid verbosity
    # (e.g., "apcoa hal ss" → "apcoa", "half ords balham" → "halfords")
    if len(core_words) > 2:
        core_words = core_words[:1]
    result = " ".join(core_words)
    return result if result else normalised


def regenerate_codes(csv_path: str):
    """Regenerate vendor_codes from vendor_names."""

    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Processing {len(rows)} rows...\n")

    # Regenerate codes
    updated_rows = []
    code_map = {}  # Track which vendors map to same code

    for row in rows:
        vendor_name = row.get('vendor_name', '').strip()
        if not vendor_name:
            updated_rows.append(row)
            continue

        # Apply engine normalization
        normalised = normalise_description(vendor_name)
        new_code = extract_vendor_key(normalised, DEFAULT_ALIASES)

        old_code = row.get('vendor_code', '')

        if new_code != old_code:
            print(f"{old_code:35} -> {new_code:20} | {vendor_name}")

            # Track consolidations
            if new_code not in code_map:
                code_map[new_code] = []
            code_map[new_code].append(old_code)

        row['vendor_code'] = new_code
        updated_rows.append(row)

    # Write back
    fieldnames = ['vendor_code', 'vendor_name', 'detail', 'nominal_code', 'account_name']
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    print(f"\n--- Results ---")
    print(f"Updated: {csv_path}")
    print(f"Unique vendor_codes: {len(code_map)}")
    print(f"Total rows: {len(updated_rows)}")

    # Show consolidations
    print(f"\nConsolidations (multiple old codes -> 1 new code):")
    for new_code in sorted(code_map.keys()):
        old_codes = code_map[new_code]
        if len(old_codes) > 1:
            print(f"  {new_code:20} <- {', '.join(sorted(set(old_codes)))}")


if __name__ == "__main__":
    input_path = "categorisations_client_vendors_cleaned.csv"
    output_path = "categorisations_client_vendors_regenerated.csv"

    # Read from original
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Processing {len(rows)} rows...\n")

    # Regenerate codes
    updated_rows = []
    code_map = {}

    for row in rows:
        vendor_name = row.get('vendor_name', '').strip()
        if not vendor_name:
            updated_rows.append(row)
            continue

        normalised = normalise_description(vendor_name)
        new_code = extract_vendor_key(normalised, DEFAULT_ALIASES)
        old_code = row.get('vendor_code', '')

        if new_code != old_code:
            print(f"{old_code:35} -> {new_code:20} | {vendor_name}")

            if new_code not in code_map:
                code_map[new_code] = []
            code_map[new_code].append(old_code)

        row['vendor_code'] = new_code
        updated_rows.append(row)

    # Write to new file
    fieldnames = ['vendor_code', 'vendor_name', 'detail', 'nominal_code', 'account_name']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    print(f"\n--- Results ---")
    print(f"Created: {output_path}")
    print(f"Unique vendor_codes: {len(code_map)}")
    print(f"Total rows: {len(updated_rows)}")
    print(f"\nConsolidations (multiple old codes -> 1 new code):")
    for new_code in sorted(code_map.keys()):
        old_codes = code_map[new_code]
        if len(old_codes) > 1:
            print(f"  {new_code:20} <- {', '.join(sorted(set(old_codes)))}")

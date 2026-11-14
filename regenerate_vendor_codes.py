"""
Regenerate vendor_key from vendor_name using engine normalization logic.
The header was `vendor_code` until 2026-09-06; a file still carrying it is
read and written back out under the new name.
This produces short, core merchant names suitable for lookups.
"""

import csv
import sys
from pathlib import Path

# The engine's own key rule, 2026-11-13, Paul's decision. ~~A copy "embedded
# from engine.py to avoid openai import"~~, which had fallen behind it: it
# lacked the four articles added in b61f055. `normalise` imports nothing but
# `re`, so this script still imports neither openai nor `config`, whose import
# creates folders under the practice root. Importing the engine would do both.
from worker.categorisation.normalise import (
    DEFAULT_ALIASES,
    extract_vendor_key,
    normalise_description,
)


# `regenerate_codes(csv_path)` was here and is DELETED, 2026-09-12, item 115
# of `2026-08-20_LIST_outstanding_items_and_decisions.md`. No call site
# anywhere: enumerated from the syntax tree over the 148 Python files
# outside `.history/`, `.git/`, `__pycache__/`, `archive/` and `.venv/`
# before the deletion, and nothing ran it either.
#
# **It was not identical to the block below, and the difference is the
# reason to say so rather than call them the same.** The function wrote
# back over `csv_path` IN PLACE. The `__main__` block reads `input_path`
# and writes a separate `output_path`. **So deleting it removes the only
# in-place variant**, which on a file of learned vendor mappings is the
# variant worth losing: it had no caller, no runner and no backup step.
#
# ~~The `__main__` block is unchanged.~~ **Made runnable 2026-11-14, Paul's
# decision, amendment 557 of `2026-07-25_CONSOLE_DESIGN.md`.** It read the
# input by a relative path the CSV left on 2026-08-01, and it raised on the
# retired `vendor_code` header before writing a row, because `DictWriter`
# refuses a key that is not one of its columns. Now: `main()` takes both
# paths as arguments, refuses to write over its input, and drops the retired
# column from each row.

RETIRED = "vendor_code"
FIELDNAMES = ['vendor_key', 'vendor_name', 'detail', 'nominal_code', 'account_name']
USAGE = "Usage: python regenerate_vendor_codes.py <input_csv> <output_csv>"


def main(argv) -> int:
    if len(argv) < 3:
        print(USAGE)
        return 1
    input_path, output_path = Path(argv[1]), Path(argv[2])
    if not input_path.is_file():
        print(f"Error: input not found: {input_path}")
        return 1
    if output_path.resolve() == input_path.resolve():
        # The in-place variant was deleted on purpose, see above.
        print("Error: the output must be a different file from the input")
        return 1

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Processing {len(rows)} rows...\n")

    updated_rows = []
    code_map = {}

    for row in rows:
        old_code = row.get('vendor_key') or row.get(RETIRED) or ''
        # The retired column goes, whatever happens to the row below. A row
        # with no name keeps its stored key, now under the current name.
        row.pop(RETIRED, None)
        vendor_name = (row.get('vendor_name') or '').strip()
        if not vendor_name:
            row['vendor_key'] = old_code
            updated_rows.append(row)
            continue

        normalised = normalise_description(vendor_name)
        new_code = extract_vendor_key(normalised, DEFAULT_ALIASES)

        if new_code != old_code:
            print(f"{old_code:35} -> {new_code:20} | {vendor_name}")

            if new_code not in code_map:
                code_map[new_code] = []
            code_map[new_code].append(old_code)

        row['vendor_key'] = new_code
        updated_rows.append(row)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(updated_rows)

    print(f"\n--- Results ---")
    print(f"Created: {output_path}")
    print(f"Unique vendor_keys: {len(code_map)}")
    print(f"Total rows: {len(updated_rows)}")
    print(f"\nConsolidations (multiple old codes -> 1 new code):")
    for new_code in sorted(code_map.keys()):
        old_codes = code_map[new_code]
        if len(old_codes) > 1:
            print(f"  {new_code:20} <- {', '.join(sorted(set(old_codes)))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

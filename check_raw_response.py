"""What the model actually returned for the 12:34 duplicate pair.

Written 2026-11-14 by the consultant session. `extractions.raw_response` holds
the model's own answer, so it settles whether the wrong VAT of 8.48 came out of
the model or was made somewhere after it.

**Opens the live database read-only and imports no project module.**

    cd C:\\LastingImpact\\receipt_capture
    py check_raw_response.py

Writes `2026-11-14_QUERY_raw_response.txt`, a new file.
"""
import sqlite3
from pathlib import Path

DB = "file:C:/Intellibills/db/receipts.db?mode=ro"
PAIR = ("cf74484c-70fe-4c3b-9c24-b399fca115c9",   # net 42.63, vat 8.48, the wrong one
        "12495a90-2464-4516-8559-57b6ac1c3cea")   # net 42.60, vat 8.51, matches the receipt
OUT = Path(__file__).parent / "2026-11-14_QUERY_raw_response.txt"

conn = sqlite3.connect(DB, uri=True)
conn.row_factory = sqlite3.Row

lines = []
for rid in PAIR:
    row = conn.execute(
        "SELECT extraction_id, extracted_at, net_amount, vat_amount, gross_amount, "
        "details, line_items, raw_response FROM extractions WHERE receipt_id = ? "
        "ORDER BY extracted_at", (rid,)).fetchone()
    lines.append("=" * 70)
    lines.append("receipt %s" % rid)
    if row is None:
        lines.append("  NO EXTRACTION ROW")
        continue
    for c in ("extraction_id", "extracted_at", "net_amount", "vat_amount", "gross_amount"):
        lines.append("  %-16s %r" % (c, row[c]))
    lines.append("  %-16s %r" % ("details", row["details"]))
    lines.append("  %-16s %r" % ("line_items", row["line_items"]))
    lines.append("  raw_response:")
    raw = row["raw_response"]
    if raw is None:
        lines.append("    NULL")
    else:
        for ln in str(raw).splitlines() or [""]:
            lines.append("    " + ln)
    lines.append("")

text = "\n".join(lines) + "\n"
OUT.write_text(text, encoding="utf-8")
print(text)
print("written to", OUT)

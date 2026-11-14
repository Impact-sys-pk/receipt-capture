"""The two extractions behind the 12:34 duplicate pair, and nothing else.

Written 2026-11-14 by the consultant session to answer one question: why
`_signals_differ()` did or did not veto the `possible_duplicate` flag on two
byte-identical uploads of the same Shell receipt.

**It opens the live database read-only and imports no project module**, so it
cannot run `config.py`'s mkdir block. `CLAUDE.md`: never `import config` to read
a value.

    cd C:\\LastingImpact\\receipt_capture
    py check_dup_signals.py

It prints the answer and also writes it to
`2026-11-14_QUERY_dup_signals.txt`, which is a new file, so the consultant
session's file bridge reads it correctly rather than serving a cached copy.
"""
import sqlite3
from pathlib import Path

DB = "file:C:/Intellibills/db/receipts.db?mode=ro"
PAIR = ("12495a90-2464-4516-8559-57b6ac1c3cea",
        "cf74484c-70fe-4c3b-9c24-b399fca115c9")
OUT = Path(__file__).parent / "2026-11-14_QUERY_dup_signals.txt"

conn = sqlite3.connect(DB, uri=True)
conn.row_factory = sqlite3.Row

cols = [r["name"] for r in conn.execute("PRAGMA table_info(extractions)")]
wanted = [c for c in ("receipt_id", "extracted_at", "engine", "supplier_name",
                      "invoice_date", "gross_amount", "net_amount", "vat_amount",
                      "receipt_ref_number", "receipt_time", "validation_status")
          if c in cols]

lines = []
lines.append("columns present on extractions, of those asked for: " + ", ".join(wanted))
missing = [c for c in ("receipt_ref_number", "receipt_time") if c not in cols]
if missing:
    lines.append("NOT A COLUMN ON extractions: " + ", ".join(missing))
lines.append("")

for rid in PAIR:
    rows = conn.execute(
        "SELECT %s FROM extractions WHERE receipt_id = ? ORDER BY extracted_at"
        % ", ".join(wanted), (rid,)).fetchall()
    lines.append("receipt %s: %d extraction row(s)" % (rid, len(rows)))
    for row in rows:
        for c in wanted:
            lines.append("    %-20s %r" % (c, row[c]))
        lines.append("")

for rid in PAIR:
    r = conn.execute(
        "SELECT receipt_id, status, filed_path, duplicate_of, file_hash "
        "FROM receipts WHERE receipt_id = ?", (rid,)).fetchone()
    lines.append("receipts row %s: %s" % (rid, dict(r) if r else "NO ROW"))

h = conn.execute("SELECT file_hash FROM receipts WHERE receipt_id = ?", (PAIR[0],)).fetchone()
if h and h["file_hash"]:
    same = conn.execute(
        "SELECT receipt_id, status, filed_path FROM receipts WHERE file_hash = ? "
        "ORDER BY created_at", (h["file_hash"],)).fetchall()
    lines.append("")
    lines.append("every receipt carrying that file hash: %d" % len(same))
    for row in same:
        lines.append("    %s" % dict(row))

text = "\n".join(lines) + "\n"
OUT.write_text(text, encoding="utf-8")
print(text)
print("written to", OUT)

import csv
import sqlite3
import sys

import config

# config.DB_PATH is the one place the database path lives. This script used to
# open Path("data/receipts.db"), a path amendment 76 removed, and an sqlite
# connection to a missing file SUCCEEDS and creates an empty database, so this
# export wrote a CSV with a header and no rows rather than saying it could not
# find the database. Outstanding item 158, fixed 2026-09-04.
db = config.DB_PATH
if not db.exists():
    sys.exit(f"no database at {db}. Set INTELLIBILLS_UNSYNCED_ROOT if it has moved.")

#: Where the export is written. **Derived from a config constant rather than
#: written relative to the working directory**, so running this from anywhere
#: still writes to one place rather than scattering an `exports\` wherever the
#: shell happened to be standing. Flag 5 of the step 10n report and Paul's
#: decision of 2026-09-11; `capture_report.py` does the same and its
#: `OUTPUT_DIR` carries the reasoning for the folder itself.
#:
#: ~~Derived from `config.BASE_DIR`~~ **Step 10r, amendment 359, Paul's decision
#: of 2026-09-12: the anchor is `config.EXPORTS_DIR` under the practice root,
#: not the repository.** The reason for pinning it at all is unchanged and is
#: the sentence above: it is about having an anchor, not about which anchor.
#:
#: The folder is created rather than assumed, and the mkdir stays for the same
#: reason it was written: this script used to fail on open. `config.py` now
#: creates it at import as well, which covers the machine that has never run an
#: export; this covers the folder being removed between then and now.
OUTPUT_DIR = config.EXPORTS_DIR
output = OUTPUT_DIR / "bookkeeping_export.csv"
output.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# One receipt, one row, and every extraction column on that row comes from the
# same attempt: the receipt's most recent one by `extracted_at`. Step 10at,
# amendment 413, Paul's decision of 2026-09-13 closing outstanding item 126.
#
# ~~GROUP BY r.receipt_id, with six bare columns, MIN(e.extracted_at) and
# MAX() over validation_status and validation_notes.~~ **That was two separate
# faults and only one of them was about sorting.**
#
# **One, the bare columns.** `supplier_name`, `invoice_date`, `net_amount`,
# `vat_amount`, `gross_amount` and `currency` were neither grouped nor
# aggregated. SQLite takes a bare column from the row that matched a min() or
# max() **only when the query holds exactly one such aggregate**; with two or
# more the choice is documented as arbitrary and may differ per column, section
# 2.5 of https://www.sqlite.org/lang_select.html. That query held three. On
# SQLite 3.50.4 the six landed on whichever attempt had the alphabetically
# greatest `validation_notes`, which is neither the first attempt nor the last
# except by coincidence.
#
# **Two, the text sort.** `extractions.validation_status` holds four values and
# no others: `failed`, `needs_review` and `ok` from `worker/validation/rules.py`
# and the literals at the nine `save_extraction()` call sites, plus
# `possible_duplicate`, which `process_extraction_result()` puts on the
# validation result before saving it. Alphabetically that is
# `failed` < `needs_review` < `ok` < `possible_duplicate`, which is neither time
# nor severity, so `MAX()` answered a question nobody asked. A receipt whose
# latest attempt failed exported as `ok`, and one whose latest attempt was
# anything at all exported as `possible_duplicate` if any earlier attempt had
# been.
#
# **The shape.** The picked row is joined on `extraction_id`, the primary key,
# so at most one extraction can match and the LEFT JOIN still yields a receipt
# that has none. There is no GROUP BY any more, so there are no bare columns
# left to be arbitrary about. `first_extracted_at` is the one thing that still
# spans every attempt, and it is a scalar subquery of its own rather than an
# aggregate over the join.
#
# **`first_extracted_at` deliberately does not change.** The column is called
# *first* and means *first*: when the pipeline first read this document. The
# step names supplier, dates, amounts and status and does not name this one,
# and changing what a column means while leaving its name alone is the fault
# the comment below the header exists to prevent.
#
# **The tiebreak is `rowid DESC`**, for two attempts sharing an `extracted_at`
# to the stored precision. It is `capture_report.py`'s tiebreak over these same
# two tables, so the export and the report cannot disagree about which attempt
# describes a receipt, and the later-written row is the later attempt in the
# only sense left when the timestamps are equal. `extractions` has a TEXT
# primary key rather than an INTEGER one, so it is an ordinary rowid table.
rows = c.execute("""
    SELECT
        r.receipt_id,
        r.firm_id,
        r.client_id,
        e.supplier_name,
        e.invoice_date,
        e.net_amount,
        e.vat_amount,
        e.gross_amount,
        e.currency,
        r.status,
        (SELECT MIN(extracted_at) FROM extractions
          WHERE receipt_id = r.receipt_id) as first_extracted_at,
        e.validation_status as latest_validation_status,
        e.validation_notes as latest_review_reason
    FROM receipts r
    LEFT JOIN extractions e ON e.extraction_id = (
        SELECT extraction_id FROM extractions
        WHERE receipt_id = r.receipt_id
        ORDER BY extracted_at DESC, rowid DESC
        LIMIT 1
    )
    ORDER BY r.created_at DESC
""").fetchall()

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "receipt_id", "firm_id", "client_id",
        "supplier_name", "invoice_date",
        "net_amount", "vat_amount", "gross_amount", "currency",
        # `first_extracted_at` keeps the stored UTC value and the stored
        # column name. **This CSV is a handoff format**, its headers are the
        # database's own column names, and nothing in this repository reads it
        # back, so converting a column while leaving its name alone would make
        # the file disagree with the column it claims to carry. Store UTC, show
        # London applies to what a person reads on a screen or in a report;
        # this is neither. Reported as a decision rather than taken quietly, per
        # section 2 of the brief of 2026-09-11.
        "status", "first_extracted_at", "latest_validation_status", "latest_review_reason"
    ])
    for row in rows:
        writer.writerow(row)

print(f"Exported {len(rows)} receipts to {output}")
conn.close()

#!/usr/bin/env python3
"""Probe: what layer 5 actually returns on the receipts already in the database.

READ ONLY. It calls CategorisationEngine.categorise() and prints the result. It
writes no categorisation row, no sidecar and no file, and it does not touch the
receipts. Run it, read the output, then archive or delete it.

Why it exists. Layer 5 has never been run against the real classifier on this
project. Amendment 197 records that: `CategorisationEngine` is constructed with
`enable_ai_fallback=False` everywhere, so everything asserted about what the AI
suggests rests on unit tests and on reading the code. This runs it once, on the
receipts that exist, and prints two answers side by side for each receipt: what
the engine returns with the AI off, which is production behaviour today, and
what it returns with the AI on.

It also prints the size of the pool layer 5 chooses from, because
`get_eligible_accounts_for_client()` falls back to the master chart with a
WARNING when a client has no `chart_code`, and the pool size is how you tell
which happened.

Cost: one OpenAI call per receipt that reaches layer 5. Receipts answered by
layers 0 to 4 cost nothing, and today all four learned tables hold 0 rows, so
expect every receipt to reach layer 5.

Run from the repository root:

    .\\.venv\\Scripts\\python.exe probe_layer5.py
"""

import sqlite3
import sys

import config
from worker.categorisation.engine import CategorisationEngine
from worker.categorisation.chart import get_eligible_accounts_for_client
from worker.database.repository import Repository


def latest_extractions():
    """(receipt_id, client_id, status, filename, supplier_name, gross_amount).

    The newest extraction per receipt by `extracted_at`, which is the row the
    pipeline would have categorised from. Opened read-only on config.DB_PATH:
    never a hardcoded path, per CLAUDE.md's Testing section.
    """
    if not config.DB_PATH.exists():
        sys.exit(f"no database at {config.DB_PATH}")
    conn = sqlite3.connect(f"file:{config.DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT r.receipt_id, r.client_id, r.status, r.filename,
               e.supplier_name, e.gross_amount, e.extracted_at
        FROM receipts r
        LEFT JOIN extractions e ON e.receipt_id = r.receipt_id
        WHERE e.extracted_at = (
            SELECT MAX(e2.extracted_at) FROM extractions e2
            WHERE e2.receipt_id = r.receipt_id
        )
        OR e.extraction_id IS NULL
        ORDER BY r.created_at
        """
    ).fetchall()
    conn.close()
    return rows


def main():
    rows = latest_extractions()
    print(f"database: {config.DB_PATH}")
    print(f"receipts: {len(rows)}")
    print()

    repo = Repository()
    off = CategorisationEngine(repo=repo, enable_ai_fallback=False)
    on = CategorisationEngine(repo=repo, enable_ai_fallback=True)

    for r in rows:
        client = config.CLIENTS_BY_ID.get(r["client_id"]) or {}
        trade = client.get("trade", "UNSPECIFIED")
        chart_code = client.get("chart_code") or "(none)"
        pool = get_eligible_accounts_for_client(r["client_id"])

        print("-" * 78)
        print(f"receipt   {r['receipt_id']}")
        print(f"file      {r['filename']}")
        print(f"status    {r['status']}")
        print(f"client    {r['client_id']}   trade={trade}   chart_code={chart_code}")
        print(f"supplier  {r['supplier_name']!r}")
        print(f"gross     {r['gross_amount']!r}")
        print(f"pool      {len(pool)} classifier-eligible account(s) offered to layer 5")

        for label, engine in (("AI off", off), ("AI on ", on)):
            res = engine.categorise(
                receipt_id=r["receipt_id"],
                extraction_id="probe",
                supplier_name=r["supplier_name"] or "",
                client_id=r["client_id"],
                business_type=trade,
                # Read out of the database, so the amount is available and the
                # item lines are not: nothing stores them. This probe therefore
                # measures the amount's effect and cannot measure the item
                # lines'. Seeing those needs a receipt through the live pipeline.
                gross_amount=r["gross_amount"],
            )
            print(
                f"  {label}  vendor_code={res.vendor_code!r}  "
                f"source={res.match_source}  code={res.suggested_code!r}  "
                f"name={res.suggested_name!r}  confidence={res.confidence}"
            )

    repo.close()
    print("-" * 78)
    print("Nothing was written. No categorisation row, no sidecar, no file changed.")


if __name__ == "__main__":
    main()

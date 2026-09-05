#!/usr/bin/env python3
"""Probe: extract a receipt, then categorise it with everything the extraction found.

Two stages in one run, so the whole chain is measured rather than half of it.

READ ONLY. It calls the extractor and prints. It writes no database row, no
sidecar and no file, and it does not move or rename the receipt.

Why it exists. `line_items` was added to `_SYSTEM_PROMPT` in
`worker/extraction/openai_vision.py` on 2026-09-05 and **nothing stores it**:
there is no column on `extractions`, nothing in the sidecar and nothing in
IntelliBooks. So a live pipeline run cannot show whether the model returns the
field at all. `probe_layer5.py` cannot show it either, because that one reads the
database and passes `line_items=None`.

This runs the extractor itself, on the file, prints what came back, and then puts
that result through `CategorisationEngine.categorise()` with the AI layer ON, so
layer 5 sees the supplier, the amount and the line items together. `probe_layer5.py`
cannot do that: it reads the database, and line items are not stored there.

The live pipeline still constructs the engine with `enable_ai_fallback=False`, so
nothing here describes production behaviour. It is a measurement.

Cost: two OpenAI calls per file, one to extract and one for layer 5. Give it paths,
or give it nothing and it reads the most recent receipts from the database.

    .\\.venv\\Scripts\\python.exe probe_extract.py
    .\\.venv\\Scripts\\python.exe probe_extract.py "C:\\path\\to\\one.pdf"
"""

import sqlite3
import sys
from pathlib import Path

import config
from worker.categorisation.chart import get_eligible_accounts_for_client
from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.extraction.factory import get_extractor


def recent_receipt_paths(limit: int = 6):
    """file_path for the most recently created receipts. Read-only on config.DB_PATH."""
    if not config.DB_PATH.exists():
        sys.exit(f"no database at {config.DB_PATH}")
    conn = sqlite3.connect(f"file:{config.DB_PATH}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT file_path, filename, receipt_id, client_id "
        "FROM receipts ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def main():
    if len(sys.argv) > 1:
        targets = [(p, Path(p).name, "probe", "UNKNOWN") for p in sys.argv[1:]]
    else:
        targets = recent_receipt_paths()

    extractor = get_extractor()
    repo = Repository()
    engine = CategorisationEngine(repo=repo, enable_ai_fallback=True)
    print(f"extractor: {extractor.name}")
    print(f"model:     {config.OPENAI_MODEL}")
    print(f"files:     {len(targets)}")

    for file_path, filename, receipt_id, client_id in targets:
        print("-" * 78)
        print(filename)
        path = Path(file_path)
        if not path.exists():
            print("  FILE NOT FOUND at", file_path)
            continue

        result = extractor.extract(str(path), filename)

        print(f"  supplier      {result.supplier_name!r}")
        print(f"  date          {result.invoice_date!r}")
        print(f"  net/vat/gross {result.net_amount} / {result.vat_amount} / {result.gross_amount}")
        print(f"  details       {result.details!r}")

        items = getattr(result, "line_items", "NO SUCH ATTRIBUTE")
        if items == "NO SUCH ATTRIBUTE":
            print("  line_items    ExtractionResult has no line_items attribute")
        elif items is None:
            print("  line_items    None. The model returned nothing, or the receipt has no item lines")
        else:
            print(f"  line_items    {len(items)} line(s)")
            for line in items:
                print(f"                {line}")

        # Stage two. The same result through the engine, AI layer on.
        client = config.CLIENTS_BY_ID.get(client_id) or {}
        pool = get_eligible_accounts_for_client(client_id)
        cat = engine.categorise(
            receipt_id=receipt_id,
            extraction_id="probe",
            supplier_name=result.supplier_name or "",
            client_id=client_id,
            business_type=client.get("trade", "UNSPECIFIED"),
            gross_amount=result.gross_amount,
            line_items=items if isinstance(items, list) else None,
        )
        print(f"  client        {client_id}  chart_code={client.get('chart_code') or '(none)'}  "
              f"pool={len(pool)}")
        print(f"  CATEGORISED   source={cat.match_source}  code={cat.suggested_code!r}  "
              f"name={cat.suggested_name!r}  confidence={cat.confidence}")

    repo.close()
    print("-" * 78)
    print("Nothing was written. No database row, no sidecar, no file changed.")


if __name__ == "__main__":
    main()

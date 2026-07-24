#!/usr/bin/env python3
"""Check for receipts that are filed with ok status but have no categorisation."""

import sys
import logging

import config
from worker.database.schema import init_db
from worker.database.repository import Repository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    init_db()
    repo = Repository(config.DB_PATH)

    # Find all filed ok receipts
    rows = repo._conn.execute("""
        SELECT r.receipt_id, r.filename, r.status, r.filed_path, r.created_at
        FROM receipts r
        WHERE r.status = 'ok' AND r.filed_path IS NOT NULL
        ORDER BY r.created_at DESC
    """).fetchall()

    filed_ok = [dict(row) for row in rows] if rows else []
    logger.info(f"Found {len(filed_ok)} receipts with status=ok and filed_path set")

    # Check which ones don't have categorisation
    missing_cat = []
    for receipt in filed_ok:
        cat = repo.get_categorisation_for_receipt(receipt["receipt_id"])
        if not cat:
            missing_cat.append(receipt)

    if missing_cat:
        logger.warning(f"\nFound {len(missing_cat)} receipts with NO categorisation:")
        for receipt in missing_cat:
            logger.warning(f"  {receipt['receipt_id']} | {receipt['filename']} | created={receipt['created_at']}")
        return 1
    else:
        logger.info("\n✓ All filed ok receipts have categorisation")
        return 0


if __name__ == "__main__":
    sys.exit(main())

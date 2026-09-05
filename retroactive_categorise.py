#!/usr/bin/env python3
"""Retroactively categorise receipts that were filed without a category."""

import sys
import json
import logging
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

import config
from worker.database.schema import init_db
from worker.database.repository import Repository
from worker.categorisation.engine import CategorisationEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)

# All 19 receipts filed without categorisation
AFFECTED_RECEIPTS = [
    "581011ce-95f2-40eb-b57b-7c611fe556e0",
    "31b3a1a5-a2fc-454e-9f46-0900f7780016",
    "520c25b4-9a58-468c-9fe6-46aaec967afe",
    "332efabc-c085-427c-9f1a-acbeb61080de",
    "7885f223-7a9b-40ca-b48f-f901e8047539",
    "3436032d-691c-4c08-81c6-ccb3d1dbfbd2",
    "5f7f0cf6-b7d9-4398-8461-f7850dba1323",
    "e8677d6c-1484-406f-8d30-07ae96761834",
    "4f02bba9-bc70-466b-a0c3-b5383169335d",
    "867efabf-8172-4d0b-9dfa-907852f3497b",
    "ab6d0fcb-eb60-4c2a-897d-64bc074ebcfa",
    "86d3f2a4-d903-4500-86e3-c68b2ec34fe1",
    "790452c1-f11c-423b-8ddb-6e64081e06b1",
    "be7d656c-9758-4d55-ae0d-ffedaed16824",
    "2778b72c-1bd4-4569-afe8-69c5c98f780d",
    "dd648f11-a0c7-44fd-ba67-2c63c7233488",
    "c6ce4ff1-f5fc-4a77-b447-025776dcb8f6",
    "ec1c40dc-76eb-4378-aa8c-f399861539a3",
    "8aa9e876-dbbd-43da-baa1-d33ae2131334",
]


def update_sidecar_json(
    sidecar_path: Path,
    category_code: str | None,
    category_name: str | None,
    confidence: str | None,
):
    """Update the sidecar JSON file with category info.

    Writes the same three keys as make_enriched_sidecar(), per design document
    3.7: the nominal code, the Desktop-compatible name, and the legacy
    `category` key holding the name. Null where the engine returned nothing.

    This function is why 18 sidecars on disk hold the string "unmatched" in the
    category field: it used to be handed `suggested_code or "unmatched"`, which
    is a match_source, not a category. Desktop matches categories by name, so it
    matched nothing, and "Post to cashbook" would have copied it into a real
    transaction.
    """
    if not sidecar_path.exists():
        logger.warning(f"Sidecar file not found: {sidecar_path}")
        return False

    try:
        with sidecar_path.open("r", encoding="utf-8") as f:
            sidecar = json.load(f)

        # Update category fields
        sidecar["category_code"] = category_code
        sidecar["category_name"] = category_name
        sidecar["category"] = category_name
        sidecar["confidence"] = confidence

        with sidecar_path.open("w", encoding="utf-8") as f:
            json.dump(sidecar, f, indent=2)

        logger.info(f"Updated sidecar: {sidecar_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to update sidecar {sidecar_path}: {e}")
        return False


def main():
    init_db()
    repo = Repository(config.DB_PATH)
    engine = CategorisationEngine(repo=repo, enable_ai_fallback=False)

    categorised = 0
    skipped = 0

    for receipt_id in AFFECTED_RECEIPTS:
        receipt = repo.get_receipt(receipt_id)
        if not receipt:
            logger.warning(f"Receipt not found: {receipt_id}")
            skipped += 1
            continue

        # Check if already has categorisation, and get it
        existing_cat = repo.get_categorisation_for_receipt(receipt_id)

        # Get extraction
        extraction = repo.get_extraction_for_receipt(receipt_id)
        if not extraction:
            logger.warning(f"Receipt {receipt_id} has no extraction, skipping")
            skipped += 1
            continue

        supplier_name = extraction.get("supplier_name")
        if not supplier_name:
            logger.warning(f"Receipt {receipt_id} has no supplier_name, skipping")
            skipped += 1
            continue

        try:
            business_type = (config.CLIENTS_BY_ID.get(receipt["client_id"]) or {}).get("trade", "UNSPECIFIED")
            extraction_id = extraction.get("extraction_id")
            if not extraction_id:
                logger.warning(f"Receipt {receipt_id} extraction has no extraction_id, skipping")
                skipped += 1
                continue

            if existing_cat:
                # Use existing categorisation
                categorisation_data = existing_cat
                logger.info(f"Receipt {receipt_id} using existing categorisation")
            else:
                # Categorise using the extraction
                categorisation = engine.categorise(
                    receipt_id=receipt_id,
                    extraction_id=extraction_id,
                    supplier_name=supplier_name,
                    client_id=receipt["client_id"],
                    business_type=business_type,
                    # `extraction` here is a dict from
                    # Repository.get_extraction_for_receipt(), which is
                    # SELECT * FROM extractions, so gross_amount is a column and
                    # is in scope. line_items is not a column, so it stays None.
                    gross_amount=extraction.get("gross_amount"),
                )

                # Save categorisation
                cat_id = str(uuid4())
                repo.save_categorisation(
                    categorisation_id=cat_id,
                    receipt_id=receipt_id,
                    extraction_id=extraction_id,
                    client_id=receipt["client_id"],
                    trade=categorisation.business_type,
                    vendor_key=categorisation.vendor_key,
                    suggested_code=categorisation.suggested_code,
                    suggested_name=categorisation.suggested_name,
                    confidence=categorisation.confidence,
                    match_source=categorisation.match_source,
                    matched_vendor=categorisation.matched_vendor,
                    needs_review=categorisation.needs_review,
                    categorised_at=datetime.now(timezone.utc).isoformat()
                )
                categorisation_data = {
                    'suggested_code': categorisation.suggested_code,
                    'suggested_name': categorisation.suggested_name,
                    'confidence': categorisation.confidence
                }

            # Update sidecar JSON
            if receipt.get("filed_path"):
                # Find sidecar next to filed receipt (e.g., file.pdf.json)
                filed_path = Path(receipt["filed_path"])
                sidecar_path = filed_path.parent / (filed_path.name + ".json")
                # No invented values. A receipt the engine could not match gets
                # nulls, not a match_source and not the string "none".
                code = categorisation_data.get('suggested_code')
                name = categorisation_data.get('suggested_name')
                conf = categorisation_data.get('confidence')
                if update_sidecar_json(sidecar_path, code, name, conf):
                    categorised += 1
                    logger.info(f"Receipt {receipt_id} updated with categorisation {code} / {name} ({conf})")
                else:
                    skipped += 1
            else:
                logger.warning(f"Receipt {receipt_id} has no filed_path, cannot update sidecar")
                skipped += 1

        except Exception as e:
            logger.error(f"Failed to categorise receipt {receipt_id}: {e}", exc_info=True)
            skipped += 1

    logger.info(f"\n{'=' * 80}")
    logger.info(f"Retroactive categorisation complete:")
    logger.info(f"  Categorised: {categorised}")
    logger.info(f"  Skipped: {skipped}")
    logger.info(f"  Total: {len(AFFECTED_RECEIPTS)}")

    return 0 if categorised == len(AFFECTED_RECEIPTS) else 1


if __name__ == "__main__":
    sys.exit(main())

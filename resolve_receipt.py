#!/usr/bin/env python3
"""
Manually resolve a needs_review, failed, or possible_duplicate receipt.

Part 3 of the receipt retry/resolution system:
- Shows current extraction and validation errors
- Lets staff correct extracted values
- For possible_duplicate, lets staff confirm or reject
- Re-validates and files if successful
- Appends new extraction row (append-only, never overwrites)
- Sets filed_path so duplicate protection works going forward

Usage:
    python resolve_receipt.py <receipt_id>
    python resolve_receipt.py <receipt_id> --supplier "Corrected Supplier" --gross 100.00
    python resolve_receipt.py <receipt_id> --duplicate-decision file  # or "discard"
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

import config
from worker.database.schema import init_db
from worker.database.repository import Repository
from worker.categorisation.engine import CategorisationEngine
from worker.filing import file_receipt, make_enriched_sidecar, determine_tax_year
from worker.validation.rules import validate, ExtractionResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)


def show_receipt_state(receipt: dict, extraction: dict):
    """Display current receipt state to staff."""
    print(f"\n{'=' * 80}")
    print(f"Receipt ID: {receipt['receipt_id']}")
    print(f"Status: {receipt['status']}")
    print(f"File: {receipt['filename']}")
    print(f"{'=' * 80}")

    if receipt['status'] == 'possible_duplicate':
        dup_id = receipt.get('duplicate_of', 'unknown')
        print(f"⚠️  POSSIBLE DUPLICATE of {dup_id}")
        print(f"   (supplier/date/amount match)")

    print("\nCurrent extraction:")
    print(f"  Supplier: {extraction.get('supplier_name') or '(not extracted)'}")
    print(f"  Date: {extraction.get('invoice_date') or '(not extracted)'}")
    print(f"  Net: {extraction.get('net_amount') or '(not extracted)'}")
    print(f"  VAT: {extraction.get('vat_amount') or '(not extracted)'}")
    print(f"  Gross: {extraction.get('gross_amount') or '(not extracted)'}")
    print(f"  Ref/Ticket: {extraction.get('receipt_ref_number') or '(not extracted)'}")
    print(f"  Time: {extraction.get('receipt_time') or '(not extracted)'}")

    if receipt['status'] in ('needs_review', 'failed'):
        notes = extraction.get('validation_notes', '(none)')
        print(f"\nValidation issue: {notes}")

    print()


def confirm_duplicated_action(receipt: dict) -> str:
    """Ask staff to confirm duplicate decision."""
    while True:
        choice = input(
            "Is this a genuine duplicate? (file/discard): "
        ).strip().lower()
        if choice in ('file', 'discard'):
            return choice
        print("Invalid choice. Enter 'file' or 'discard'.")


def get_corrections_interactive(extraction: dict) -> dict:
    """Interactively ask staff for corrected values."""
    corrections = {}

    fields = [
        ('supplier_name', 'Supplier name'),
        ('invoice_date', 'Invoice date (YYYY-MM-DD)'),
        ('net_amount', 'Net amount'),
        ('vat_amount', 'VAT amount'),
        ('gross_amount', 'Gross amount'),
        ('receipt_ref_number', 'Reference/ticket number'),
        ('receipt_time', 'Time (HH:MM)'),
    ]

    print("\nEnter corrected values (blank = keep existing):")
    for field, label in fields:
        current = extraction.get(field)
        prompt = f"  {label}"
        if current:
            prompt += f" [current: {current}]"
        prompt += ": "

        value = input(prompt).strip()
        if value:
            corrections[field] = value

    return corrections


def main():
    parser = argparse.ArgumentParser(
        description="Manually resolve a receipt that needs review or confirmation."
    )
    parser.add_argument('receipt_id', help='Receipt ID to resolve')
    parser.add_argument(
        '--supplier',
        help='Corrected supplier name'
    )
    parser.add_argument(
        '--invoice-date',
        help='Corrected invoice date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--net',
        type=float,
        help='Corrected net amount'
    )
    parser.add_argument(
        '--vat',
        type=float,
        help='Corrected VAT amount'
    )
    parser.add_argument(
        '--gross',
        type=float,
        help='Corrected gross amount'
    )
    parser.add_argument(
        '--ref-number',
        help='Receipt reference/ticket number'
    )
    parser.add_argument(
        '--time',
        help='Receipt time (HH:MM)'
    )
    parser.add_argument(
        '--duplicate-decision',
        choices=['file', 'discard'],
        help='For possible_duplicate: file it anyway or discard'
    )

    args = parser.parse_args()

    # Initialize database
    init_db()

    # Connect
    repo = Repository(config.DB_PATH)
    engine = CategorisationEngine(repo)

    # Load receipt
    receipt = repo.get_receipt(args.receipt_id)
    if not receipt:
        print(f"ERROR: Receipt not found: {args.receipt_id}")
        sys.exit(1)

    extraction = repo.get_extraction_for_receipt(args.receipt_id)
    if not extraction:
        print(f"ERROR: No extraction found for receipt: {args.receipt_id}")
        sys.exit(1)

    # Try to acquire lock
    acquired = repo.acquire_receipt_lock(args.receipt_id)
    if not acquired:
        print("ERROR: Receipt is locked by another process. Try again in a moment.")
        sys.exit(1)

    try:
        # Show current state
        show_receipt_state(receipt, extraction)

        # Handle possible_duplicate decision if provided
        if receipt['status'] == 'possible_duplicate' and args.duplicate_decision:
            if args.duplicate_decision == 'discard':
                repo.update_receipt_status(args.receipt_id, 'discarded')
                logger.info(f"Receipt {args.receipt_id} discarded as duplicate")
                print("✓ Discarded as duplicate.")
                return 0
            # else: continue to file it

        # Get corrections
        if any([args.supplier, args.invoice_date, args.net, args.vat, args.gross, args.ref_number, args.time]):
            # Command-line args provided
            corrections = {
                'supplier_name': args.supplier,
                'invoice_date': args.invoice_date,
                'net_amount': args.net,
                'vat_amount': args.vat,
                'gross_amount': args.gross,
                'receipt_ref_number': args.ref_number,
                'receipt_time': args.time,
            }
            corrections = {k: v for k, v in corrections.items() if v is not None}
        else:
            # Interactive mode
            corrections = get_corrections_interactive(extraction)

        # Apply corrections
        corrected_values = {
            'supplier_name': corrections.get('supplier_name') or extraction.get('supplier_name'),
            'invoice_date': corrections.get('invoice_date') or extraction.get('invoice_date'),
            'net_amount': corrections.get('net_amount') or extraction.get('net_amount'),
            'vat_amount': corrections.get('vat_amount') or extraction.get('vat_amount'),
            'gross_amount': corrections.get('gross_amount') or extraction.get('gross_amount'),
            'receipt_ref_number': corrections.get('receipt_ref_number') or extraction.get('receipt_ref_number'),
            'receipt_time': corrections.get('receipt_time') or extraction.get('receipt_time'),
            'currency': extraction.get('currency', 'GBP'),
        }

        # Re-validate
        try:
            extraction_obj = ExtractionResult(
                engine='manual_correction',
                supplier_name=corrected_values['supplier_name'],
                invoice_date=corrected_values['invoice_date'],
                net_amount=corrected_values['net_amount'],
                vat_amount=corrected_values['vat_amount'],
                gross_amount=corrected_values['gross_amount'],
                currency=corrected_values['currency'],
                raw_response=json.dumps(corrected_values)
            )
        except Exception as e:
            print(f"ERROR: Invalid corrected values: {e}")
            return 1

        validation = validate(extraction_obj)

        if validation.status != "ok":
            repo.append_validation_notes(
                args.receipt_id,
                f"Manual correction attempted: {', '.join(validation.notes)}"
            )
            logger.warning(f"Corrected receipt {args.receipt_id} still fails validation: {validation.notes}")
            print(f"✗ Still invalid after correction: {validation.notes}")
            return 1

        # Validation passed - now file it
        print("Validation passed. Filing receipt...")

        # Get pipeline version
        pipeline_version = config.get_pipeline_version()

        # Generate extraction_id early (needed for categorisation)
        extraction_id = str(uuid4())

        # Categorise
        business_type = config.CLIENTS_BY_CODE.get(receipt['client_code'], {}).get('business_type', 'UNSPECIFIED')
        categorisation = engine.categorise(
            receipt_id=args.receipt_id,
            extraction_id=extraction_id,
            supplier_name=corrected_values['supplier_name'],
            client_id=receipt['client_id'],
            business_type=business_type
        )

        # Save categorisation
        cat_id = str(uuid4())
        repo.save_categorisation(
            categorisation_id=cat_id,
            receipt_id=args.receipt_id,
            extraction_id=extraction_id,
            client_id=receipt['client_id'],
            business_type=categorisation.business_type,
            vendor_code=categorisation.vendor_code,
            suggested_code=categorisation.suggested_code,
            suggested_name=categorisation.suggested_name,
            confidence=categorisation.confidence,
            match_source=categorisation.match_source,
            matched_vendor=categorisation.matched_vendor,
            needs_review=categorisation.needs_review,
            categorised_at=datetime.now(timezone.utc).isoformat()
        )

        # File receipt
        client_name = config.CLIENTS_BY_CODE.get(receipt['client_code'], {}).get('client_name', receipt['client_code'])
        tax_year = determine_tax_year(corrected_values['invoice_date'] or datetime.now(timezone.utc).date().isoformat())

        sidecar_payload = make_enriched_sidecar(
            receipt_id=args.receipt_id,
            source=receipt.get('source', 'email'),
            client_code=receipt['client_code'],
            client_name=client_name,
            capture_date=datetime.now(timezone.utc).isoformat(),
            invoice_date=corrected_values['invoice_date'],
            supplier=corrected_values['supplier_name'],
            net=corrected_values['net_amount'],
            vat=corrected_values['vat_amount'],
            gross=corrected_values['gross_amount'],
            currency=corrected_values['currency'],
            category=categorisation.suggested_code,
            confidence=categorisation.confidence,
            validation_status="ok",
            asserted=None,
            original_filename=receipt['filename'],
            claimed_client_code=None,
        )

        dest_path, sidecar_path = file_receipt(
            Path(receipt['file_path']),
            client_name,
            tax_year,
            corrected_values['supplier_name'] or "unknown",
            corrected_values['gross_amount'] or 0.0,
            receipt['filename'],
            sidecar_payload
        )

        # Mark filed (CRITICAL: sets filed_path so Part 2A's duplicate protection works)
        repo.mark_receipt_filed(args.receipt_id, str(dest_path))
        repo.update_receipt_status(args.receipt_id, 'ok')

        # Save the manual-correction extraction row (append-only)
        repo.save_extraction(
            extraction_id=extraction_id,
            receipt_id=args.receipt_id,
            engine="manual_correction",
            supplier_name=corrected_values['supplier_name'],
            invoice_date=corrected_values['invoice_date'],
            net_amount=corrected_values['net_amount'],
            vat_amount=corrected_values['vat_amount'],
            gross_amount=corrected_values['gross_amount'],
            currency=corrected_values['currency'],
            raw_response=json.dumps(corrected_values),
            validation_status="ok",
            validation_notes=["manually corrected and filed"],
            receipt_ref_number=corrected_values['receipt_ref_number'],
            receipt_time=corrected_values['receipt_time'],
            pipeline_version=pipeline_version,
        )

        logger.info(f"Receipt {args.receipt_id} manually resolved and filed to {dest_path}")
        print(f"✓ Filed to {dest_path}")
        print(f"  Category: {categorisation.suggested_code} ({categorisation.confidence})")
        return 0

    except KeyboardInterrupt:
        print("\nAborted.")
        return 1
    except Exception as e:
        logger.error(f"Error resolving receipt {args.receipt_id}: {e}", exc_info=True)
        print(f"ERROR: {e}")
        return 1
    finally:
        repo.release_receipt_lock(args.receipt_id)


if __name__ == '__main__':
    sys.exit(main())

"""Shared extraction processing pipeline used by email intake, folder intake, and auto-retry.

Processes: extract → validate → duplicate-check → categorise → file → mark-filed.
All three call sites (email, folder, Part 1 retry) use this function to avoid code duplication.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

import config
from worker.database.repository import Repository
from worker.categorisation.engine import CategorisationEngine
from worker.filing import file_receipt, file_review, make_enriched_sidecar, determine_tax_year
from worker.validation.rules import validate


def _log_receipt(receipt_id, message_id, filename, action, firm_id, client_id=None, extraction_status=None,
                supplier_name=None, invoice_date=None, gross_amount=None, review_reason=None,
                duplicate_of=None, duplicate_reason=None, run_id=None):
    """Log receipt processing event to audit trail."""
    entry = {
        "receipt_id": receipt_id,
        "message_id": message_id,
        "filename": filename,
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
    }
    if client_id:
        entry["client_id"] = client_id
    if extraction_status:
        entry["extraction_status"] = extraction_status
    if supplier_name:
        entry["supplier_name"] = supplier_name
    if invoice_date:
        entry["invoice_date"] = invoice_date
    if gross_amount is not None:
        entry["gross_amount"] = gross_amount
    if review_reason:
        entry["review_reason"] = review_reason
    if duplicate_of:
        entry["duplicate_of"] = duplicate_of
    if duplicate_reason:
        entry["duplicate_reason"] = duplicate_reason

    log_path = config.LOGS_DIR / f"receipt_events_{firm_id}.ndjson"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def process_extraction_result(
    receipt_id: str,
    extraction,
    file_path: Path,
    filename: str,
    client_code: str,
    firm_id: str,
    client_id: str,
    message_id: str,
    attachment_id: str = None,
    file_hash: str = None,
    asserted_values: dict = None,
    repo: Repository = None,
    categorisation_engine: CategorisationEngine = None,
    stats: dict = None,
    run_id: str = None,
    pipeline_version: str = None
) -> tuple:
    """
    Shared extraction processing pipeline: validate → duplicate-check → categorise → file.

    Used by ALL three call sites:
    - Email intake (normal processing)
    - Folder intake (normal processing)
    - Part 1 auto-retry

    Returns: (final_status, filed_path_if_ok_or_none)
    """
    if stats is None:
        stats = {}

    # Validate extraction
    validation = validate(extraction)

    duplicate_of = None

    # Semantic duplicate check (Part 2B gate)
    if validation.status == "ok":
        dup = repo.find_by_transaction_loose(
            extraction.supplier_name,
            extraction.invoice_date,
            extraction.gross_amount,
            case_insensitive=True,
            amount_tolerance=0.01
        )
        if dup and repo.is_recorded_and_filed(dup):
            # Check if distinguishing signals differ (ref_number, receipt_time)
            # For now, if we found a filed duplicate and no signals to distinguish, mark as possible_duplicate
            validation = validation._replace(
                status="possible_duplicate"
            ) if hasattr(validation, '_replace') else type(validation)(
                status="possible_duplicate",
                notes=[f"matches {dup[:8]}... (supplier, date, amount)"]
            )
            duplicate_of = dup

    # Save extraction (append-only)
    extraction_id = str(uuid.uuid4())
    repo.save_extraction(
        extraction_id=extraction_id,
        receipt_id=receipt_id,
        engine=extraction.engine,
        supplier_name=extraction.supplier_name,
        invoice_date=extraction.invoice_date,
        net_amount=extraction.net_amount,
        vat_amount=extraction.vat_amount,
        gross_amount=extraction.gross_amount,
        currency=extraction.currency,
        raw_response=extraction.raw_response,
        validation_status=validation.status,
        validation_notes=validation.notes,
        receipt_ref_number=getattr(extraction, 'receipt_ref_number', None),
        receipt_time=getattr(extraction, 'receipt_time', None),
        pipeline_version=pipeline_version,
    )

    filed_path = None
    review_path = None

    # File based on validation outcome
    if validation.status == "ok":
        # Build sidecar with confidence="high"
        sidecar_payload = make_enriched_sidecar(
            receipt_id=receipt_id,
            source="email" if message_id else "folder",
            client_code=client_code,
            client_name=config.CLIENTS_BY_CODE.get(client_code, {}).get('client_name', client_code),
            capture_date=datetime.now(timezone.utc).isoformat(),
            invoice_date=extraction.invoice_date,
            supplier=extraction.supplier_name,
            net=extraction.net_amount,
            vat=extraction.vat_amount,
            gross=extraction.gross_amount,
            currency=extraction.currency,
            category=None,  # Will be set by categorisation
            confidence="high",
            validation_status="ok",
            asserted=asserted_values,
            original_filename=filename,
            claimed_client_code=None,
        )

        # Categorise
        business_type = config.CLIENTS_BY_CODE.get(client_code, {}).get('business_type', 'UNSPECIFIED')
        categorisation = categorisation_engine.categorise(
            receipt_id=receipt_id,
            extraction_id=extraction_id,
            supplier_name=extraction.supplier_name,
            client_id=client_id,
            business_type=business_type
        )

        # Save categorisation
        cat_id = str(uuid.uuid4())
        repo.save_categorisation(
            categorisation_id=cat_id,
            receipt_id=receipt_id,
            extraction_id=extraction_id,
            client_id=client_id,
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

        # Update sidecar with categorisation
        sidecar_payload['category'] = categorisation.suggested_code
        sidecar_payload['confidence'] = categorisation.confidence

        # File receipt
        client_name = config.CLIENTS_BY_CODE.get(client_code, {}).get('client_name', client_code)
        tax_year = determine_tax_year(extraction.invoice_date or datetime.now(timezone.utc).date().isoformat())
        filed_path, sidecar_path = file_receipt(
            file_path,
            client_name,
            tax_year,
            extraction.supplier_name or "unknown",
            extraction.gross_amount or 0.0,
            filename,
            sidecar_payload
        )

        # Mark filed (critical for Part 2A's duplicate protection)
        repo.mark_receipt_filed(receipt_id, filed_path)
        repo.update_receipt_status(receipt_id, "ok")
        stats['extractions_succeeded'] = stats.get('extractions_succeeded', 0) + 1

    else:  # failed, needs_review, possible_duplicate
        # Build sidecar with confidence="low"
        client_name = config.CLIENTS_BY_CODE.get(client_code, {}).get('client_name', client_code)
        sidecar_payload = make_enriched_sidecar(
            receipt_id=receipt_id,
            source="email" if message_id else "folder",
            client_code=client_code,
            client_name=client_name,
            capture_date=datetime.now(timezone.utc).isoformat(),
            invoice_date=extraction.invoice_date,
            supplier=extraction.supplier_name,
            net=extraction.net_amount,
            vat=extraction.vat_amount,
            gross=extraction.gross_amount,
            currency=extraction.currency,
            category=None,
            confidence="low",
            validation_status=validation.status,
            asserted=asserted_values,
            original_filename=filename,
            claimed_client_code=None,
        )

        # File to Review folder
        review_path, sidecar_path = file_review(
            file_path,
            client_name,
            filename,
            validation.status,
            validation.notes,
            sidecar_payload
        )

        repo.update_receipt_status(receipt_id, validation.status)

        if validation.status == "possible_duplicate":
            repo.set_duplicate_of(receipt_id, duplicate_of)
            stats['possible_duplicates_found'] = stats.get('possible_duplicates_found', 0) + 1
        elif validation.status == "failed":
            stats['extraction_failures'] = stats.get('extraction_failures', 0) + 1
        else:  # needs_review
            stats['review_flags_issued'] = stats.get('review_flags_issued', 0) + 1

    # Mark email attachment as processed (email-only dedup, must happen for ALL outcomes)
    if message_id and attachment_id and file_hash:
        repo.mark_processed(message_id, attachment_id, file_hash, receipt_id)

    # Log
    _log_receipt(
        receipt_id,
        message_id or f"folder:{filename}",
        filename,
        "extracted",
        firm_id=firm_id,
        client_id=client_id,
        extraction_status=validation.status,
        supplier_name=extraction.supplier_name,
        invoice_date=extraction.invoice_date,
        gross_amount=extraction.gross_amount,
        duplicate_of=duplicate_of,
        run_id=run_id
    )

    return (validation.status, filed_path or review_path)

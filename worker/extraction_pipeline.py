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


def _signals_differ(extraction, dup_receipt_id: str, repo: Repository) -> bool:
    """Check if extraction has distinguishing signals from a potential duplicate.

    Compares receipt_ref_number and receipt_time. Returns True if they differ,
    allowing the same-amount receipt to be filed separately (not flagged as duplicate).

    Returns True if:
    - Both have different ref_numbers (both non-empty and differ)
    - Both have different receipt times (both non-empty and differ by >5 min)

    Returns False if:
    - Neither field differs, or fields are missing, or signals match
    """
    dup_extraction = repo.get_extraction_for_receipt(dup_receipt_id)
    if not dup_extraction:
        return False

    # Check reference numbers
    ref_new = getattr(extraction, 'receipt_ref_number', None)
    ref_dup = dup_extraction.get('receipt_ref_number')

    if ref_new and ref_dup and ref_new != ref_dup:
        return True

    # Check receipt times (HH:MM format)
    time_new = getattr(extraction, 'receipt_time', None)
    time_dup = dup_extraction.get('receipt_time')

    if time_new and time_dup:
        try:
            # Parse HH:MM format
            new_h, new_m = map(int, time_new.split(':'))
            dup_h, dup_m = map(int, time_dup.split(':'))

            # Calculate difference in minutes
            new_mins = new_h * 60 + new_m
            dup_mins = dup_h * 60 + dup_m
            diff = abs(new_mins - dup_mins)

            # If more than 5 minutes apart, treat as different transactions
            if diff > 5:
                return True
        except (ValueError, AttributeError):
            pass

    return False


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

    log_path = config.LOGS_DIR / f"receipt_events_{firm_id or config.UNATTRIBUTED_FIRM_ID}.ndjson"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def process_extraction_result(
    receipt_id: str,
    extraction,
    file_path: Path,
    filename: str,
    firm_id: str,
    client_id: str,
    source: str,
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

    `source` is one of the four words of sub-step 10d.40 and is the receipt's own,
    passed in by whichever caller wrote the row. It used to be worked out here as
    "email" if there is a message_id else "folder", which is a fifth and sixth
    word that existed only in the sidecar, so one receipt read `capture` in the
    database and `folder` on disk.

    Sub-steps 10d.16 and 10d.18. A receipt whose client cannot be resolved to a
    folder under Clients is a review item, whatever the extraction says about it.
    That gate is below, before the ok branch, and it is the reason this function
    can no longer reach `ok` with client_id = UNKNOWN.
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
            # Only flag as possible_duplicate if signals do NOT distinguish them
            if not _signals_differ(extraction, dup, repo):
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
        # What post-processing changed and why, e.g. an amount read as net that
        # was really the gross. Unrecorded until now, see design document 3.11.
        details=getattr(extraction, 'details', None),
    )

    filed_path = None
    review_path = None

    # 10d.16 and 10d.18. An unresolved client files nothing into Clients and the
    # item goes to Review, so a clean extraction for a client nobody can name is
    # a review item rather than an ok receipt filed into a guessed folder. This
    # is the only part of step 10d that reports to the operator.
    client_folder_name = (config.CLIENTS_BY_ID.get(client_id) or {}).get("client_folder_name")
    if validation.status == "ok" and (client_id == config.UNKNOWN_CLIENT_ID or not client_folder_name):
        reason = (
            "client could not be resolved"
            if client_id == config.UNKNOWN_CLIENT_ID
            else f"client {client_id} has no client_folder_name in the registry"
        )
        validation = type(validation)(
            status="needs_review",
            notes=list(validation.notes or []) + [reason],
        )

    # File based on validation outcome
    if validation.status == "ok":
        # Categorise first, then build the sidecar once with the result. This
        # used to build the payload with category=None and confidence="high" and
        # overwrite both keys afterwards, which made this a second writer of the
        # same format in all but name.
        client = config.CLIENTS_BY_ID.get(client_id) or {}
        categorisation = categorisation_engine.categorise(
            receipt_id=receipt_id,
            extraction_id=extraction_id,
            supplier_name=extraction.supplier_name,
            client_id=client_id,
            business_type=client.get('trade', 'UNSPECIFIED')
        )

        # Save categorisation
        cat_id = str(uuid.uuid4())
        repo.save_categorisation(
            categorisation_id=cat_id,
            receipt_id=receipt_id,
            extraction_id=extraction_id,
            client_id=client_id,
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

        # 10d.40. The sidecar used its own vocabulary, "email" or "folder", while
        # the database said "capture", so one receipt was two different words in
        # two places. Both now use the receipt's own source, which is one of the
        # four and nothing else.
        sidecar_payload = make_enriched_sidecar(
            receipt_id=receipt_id,
            source=source,
            client_id=client_id,
            client_name=client.get('client_name', ''),
            capture_date=datetime.now(timezone.utc).isoformat(),
            invoice_date=extraction.invoice_date,
            supplier=extraction.supplier_name,
            net=extraction.net_amount,
            vat=extraction.vat_amount,
            gross=extraction.gross_amount,
            currency=extraction.currency,
            category_code=categorisation.suggested_code,
            category_name=categorisation.suggested_name,
            confidence=categorisation.confidence,
            validation_status="ok",
            asserted=asserted_values,
            original_filename=filename,
            claimed_client_id=None,
        )

        # File receipt
        tax_year = determine_tax_year(extraction.invoice_date or datetime.now(timezone.utc).date().isoformat())
        filed_path, sidecar_path = file_receipt(
            file_path,
            client_folder_name,
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
        sidecar_payload = make_enriched_sidecar(
            receipt_id=receipt_id,
            source=source,
            client_id=client_id,
            client_name=(config.CLIENTS_BY_ID.get(client_id) or {}).get('client_name', ''),
            capture_date=datetime.now(timezone.utc).isoformat(),
            invoice_date=extraction.invoice_date,
            supplier=extraction.supplier_name,
            net=extraction.net_amount,
            vat=extraction.vat_amount,
            gross=extraction.gross_amount,
            currency=extraction.currency,
            # Nothing is categorised on this path: the receipt is not filed.
            category_code=None,
            category_name=None,
            confidence="low",
            validation_status=validation.status,
            asserted=asserted_values,
            original_filename=filename,
            claimed_client_id=None,
        )

        # File to Review folder. 10d.54: keyed on client_id.
        review_path, sidecar_path = file_review(
            file_path,
            client_id,
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
    # Sub-step 10d.32, corrected 2026-09-03. firm_id was omitted here, so it took
    # mark_processed()'s None default on the one call site an emailed receipt takes
    # when extraction succeeds. The three call sites in app.py all pass it, and they
    # are the duplicate and failure paths, so the column was populated for everything
    # except the normal case. Found by reading the row after the first emailed receipt
    # of 2026-09-03: firm_id NULL against a receipt whose own row said FIRM001.
    # It is in scope here and _log_receipt() ten lines below already uses it.
    # It stays whatever the caller resolved, including None: a firm this path could not
    # resolve is recorded as unresolved rather than invented, per 10d.19.
    if message_id and attachment_id and file_hash:
        repo.mark_processed(message_id, attachment_id, file_hash, receipt_id, firm_id)

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

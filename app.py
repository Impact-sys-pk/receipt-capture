import base64
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone

import config
from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.email.reader import fetch_attachments, fetch_new_messages
from worker.extraction.openai_vision import OpenAIVisionExtractor
from worker.intake.folder_reader import scan_inbox
from worker.filing import (
    determine_tax_year,
    file_receipt,
    file_statement,
    file_review,
    make_enriched_sidecar,
)
from worker.storage.store import compute_hash, is_supported, save_file, save_inbox_file
from worker.validation.rules import validate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _log_run(run_id, started_at, finished_at, stats, errors=None):
    entry = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "mailbox": config.IMAP_USERNAME,
        **stats,
    }
    if errors:
        entry["errors"] = errors
    with config.RUNS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _log_receipt(receipt_id, message_id, filename, action, firm_id, extraction_status=None, supplier_name=None, invoice_date=None, gross_amount=None, review_reason=None, duplicate_of=None, duplicate_reason=None, client_id=None, run_id=None):
    entry = {
        "receipt_id": receipt_id,
        "message_id": message_id,
        "filename": filename,
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
    }
    if action == "created" and client_id:
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


def process_once():
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    logger.info(f"--- run {run_id[:8]}... start ---")
    repo = Repository()
    extractor = OpenAIVisionExtractor()
    engine = CategorisationEngine(repo=repo, enable_ai_fallback=False)

    stats = {
        "messages_found": 0,
        "attachments_processed": 0,
        "receipts_created": 0,
        "duplicates_skipped": 0,
        "extraction_failures": 0,
        "extractions_succeeded": 0,
        "review_flags_issued": 0,
    }

    try:
        intake_records = scan_inbox()
        logger.info(f"capture inbox files found: {len(intake_records)}")

        messages = fetch_new_messages(repo)
        stats["messages_found"] = len(messages)
        logger.info(f"messages with attachments: {len(messages)}")

        for intake in intake_records:
            if intake.is_statement:
                if repo.find_statement_by_hash(intake.file_hash):
                    logger.info(f"capture duplicate statement by hash, skipping {intake.filename}")
                    stats["duplicates_skipped"] += 1
                    continue

                if not intake.statement_metadata.get("platform") or not intake.statement_metadata.get("week_ending"):
                    logger.warning(f"statement missing metadata, routing to review: {intake.filename}")
                    client_name = config.CLIENTS_BY_CODE.get(intake.client_code, {}).get("client_name", intake.client_code)
                    file_review(intake.source_path, client_name, intake.filename, "missing_statement_metadata", ["missing platform or week_ending"], intake.sidecar or {})
                    stats["review_flags_issued"] += 1
                    continue

                statement_id = str(uuid.uuid4())
                client_name = config.CLIENTS_BY_CODE.get(intake.client_code, {}).get("client_name", intake.client_code)
                tax_year = determine_tax_year(intake.statement_metadata["week_ending"])
                dest_path, sidecar_path = file_statement(
                    intake.source_path,
                    client_name,
                    tax_year,
                    intake.statement_metadata["platform"],
                    intake.statement_metadata["week_ending"],
                    intake.source_path.suffix,
                    intake.sidecar or {
                        "type": "statement",
                        "platform": intake.statement_metadata["platform"],
                        "week_ending": intake.statement_metadata["week_ending"],
                        "source": intake.source,
                    },
                )
                repo.save_statement(
                    statement_id=statement_id,
                    client_id=intake.client_id,
                    client_code=intake.client_code,
                    platform=intake.statement_metadata["platform"],
                    week_ending=intake.statement_metadata["week_ending"],
                    source=intake.source,
                    file_hash=intake.file_hash,
                    file_path=dest_path,
                )
                logger.info(f"statement filed: {statement_id} {dest_path}")
                stats["receipts_created"] += 1
                continue

            existing = repo.find_by_hash(intake.file_hash)
            if existing:
                logger.info(f"capture duplicate by hash, skipping {intake.filename}")
                stats["duplicates_skipped"] += 1
                continue

            receipt_id = str(uuid.uuid4())
            file_path = save_inbox_file(receipt_id, intake.client_code, intake.source_path)
            stats["receipts_created"] += 1

            repo.save_receipt(
                receipt_id=receipt_id,
                message_id=f"capture:{intake.original_name}",
                email_subject=None,
                email_from=None,
                email_received_at=int(intake.source_path.stat().st_mtime),
                filename=intake.filename,
                file_path=file_path,
                file_hash=intake.file_hash,
                firm_id=intake.firm_id,
                client_id=intake.client_id,
                client_code=intake.client_code,
                source=intake.source,
            )
            _log_receipt(receipt_id, f"capture:{intake.original_name}", intake.filename, "created", firm_id=intake.firm_id, client_id=intake.client_id, run_id=run_id)

            try:
                extraction = extractor.extract(str(file_path), intake.filename)
                validation = validate(extraction)

                duplicate_of = None
                duplicate_reason = None
                if extraction.supplier_name and extraction.gross_amount is not None:
                    if extraction.invoice_date:
                        existing = repo.find_by_transaction(
                            extraction.supplier_name,
                            extraction.invoice_date,
                            extraction.gross_amount
                        )
                    else:
                        existing = repo.find_by_transaction_no_date(
                            extraction.supplier_name,
                            extraction.gross_amount
                        )
                    if existing:
                        duplicate_of = existing
                        duplicate_reason = "transaction_match"
                        logger.info(f"transaction duplicate: {receipt_id[:8]}... matches {existing[:8]}...")

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
                )

                client_name = config.CLIENTS_BY_CODE.get(intake.client_code, {}).get("client_name", intake.client_code)
                asserted = {k: intake.sidecar.get(k) for k in ("supplier_name", "invoice_date", "net_amount", "vat_amount", "gross_amount", "client_code") if intake.sidecar and k in intake.sidecar}
                if asserted:
                    mismatches = []
                    if extraction.supplier_name and asserted.get("supplier_name") and asserted["supplier_name"].strip().lower() != extraction.supplier_name.strip().lower():
                        mismatches.append("supplier_name")
                    if extraction.invoice_date and asserted.get("invoice_date") and asserted["invoice_date"] != extraction.invoice_date:
                        mismatches.append("invoice_date")
                    if extraction.gross_amount is not None and asserted.get("gross_amount") is not None and float(asserted["gross_amount"]) != extraction.gross_amount:
                        mismatches.append("gross_amount")
                    if mismatches:
                        asserted["conflict_fields"] = mismatches

                sidecar_payload = make_enriched_sidecar(
                    receipt_id=receipt_id,
                    source=intake.source,
                    client_code=intake.client_code,
                    client_name=client_name,
                    capture_date=datetime.now(timezone.utc).isoformat(),
                    invoice_date=extraction.invoice_date,
                    supplier=extraction.supplier_name or intake.sidecar.get("supplier_name") if intake.sidecar else None,
                    net=extraction.net_amount,
                    vat=extraction.vat_amount,
                    gross=extraction.gross_amount,
                    currency=extraction.currency,
                    category=None,
                    confidence="high" if validation.status == "ok" else "low",
                    validation_status=validation.status,
                    asserted=asserted or None,
                    original_filename=intake.filename,
                    claimed_client_code=intake.sidecar.get("client_code") if intake.sidecar else None,
                )

                if validation.status == "ok":
                    if extraction.invoice_date:
                        tax_year = determine_tax_year(extraction.invoice_date)
                    else:
                        tax_year = determine_tax_year(datetime.now(timezone.utc).date().isoformat())

                    file_receipt(
                        intake.source_path,
                        client_name,
                        tax_year,
                        extraction.supplier_name or "unknown",
                        extraction.gross_amount or 0.0,
                        intake.filename,
                        sidecar_payload,
                    )
                    stats["extractions_succeeded"] += 1
                else:
                    file_review(
                        intake.source_path,
                        client_name,
                        intake.filename,
                        validation.status,
                        validation.notes,
                        sidecar_payload,
                    )
                    stats["review_flags_issued"] += 1

                _log_receipt(
                    receipt_id, f"capture:{intake.original_name}", intake.filename, "extracted",
                    firm_id=intake.firm_id,
                    extraction_status=validation.status,
                    supplier_name=extraction.supplier_name,
                    invoice_date=extraction.invoice_date,
                    gross_amount=extraction.gross_amount,
                    review_reason=validation.notes[0] if validation.notes else None,
                    duplicate_of=duplicate_of,
                    duplicate_reason=duplicate_reason,
                    run_id=run_id
                )

            except Exception as exc:
                logger.error(f"capture extraction failed {receipt_id[:8]}... [{intake.filename}]: {exc}", exc_info=True)
                stats["extraction_failures"] += 1
                repo.save_extraction(
                    extraction_id=str(uuid.uuid4()),
                    receipt_id=receipt_id,
                    engine="openai_vision",
                    supplier_name=None,
                    invoice_date=None,
                    net_amount=None,
                    vat_amount=None,
                    gross_amount=None,
                    currency="GBP",
                    raw_response=str(exc),
                    validation_status="failed",
                    validation_notes=[f"extraction error: {exc}"],
                )
                file_review(
                    intake.source_path,
                    client_name,
                    intake.filename,
                    "failed",
                    [str(exc)],
                    {
                        "receipt_id": receipt_id,
                        "source": intake.source,
                        "client_code": intake.client_code,
                        "client_name": client_name,
                        "original_filename": intake.filename,
                        "error": str(exc),
                    },
                )
                _log_receipt(
                    receipt_id, f"capture:{intake.original_name}", intake.filename, "extraction_failed",
                    firm_id=intake.firm_id,
                    extraction_status="failed",
                    review_reason=str(exc),
                    run_id=run_id
                )

        for msg in messages:
            message_id = msg["id"]
            subject = msg.get("subject", "")
            email_from = msg.get("from", {}).get("emailAddress", {}).get("address", "")
            received_at = msg.get("receivedDateTime", "")

            for att in fetch_attachments(message_id, msg.get("msg")):
                att_id = att["id"]
                filename = att.get("name", "unknown")
                stats["attachments_processed"] += 1

                if not is_supported(filename):
                    logger.info(f"skip unsupported: {filename}")
                    _log_receipt(
                        str(uuid.uuid4()), message_id, filename, "unsupported_file_type",
                        firm_id="INTELLITAX", run_id=run_id
                    )
                    continue

                if repo.is_duplicate(message_id, att_id):
                    logger.info(f"skip duplicate: {message_id}/{att_id}")
                    stats["duplicates_skipped"] += 1
                    _log_receipt(
                        str(uuid.uuid4()), message_id, filename, "duplicate_skipped",
                        firm_id="INTELLITAX", duplicate_reason="message_id_match",
                        run_id=run_id
                    )
                    continue

                file_data = base64.b64decode(att.get("contentBytes", ""))
                file_hash = compute_hash(file_data)

                existing = repo.find_by_hash(file_hash)
                if existing:
                    logger.warning(f"hash duplicate of {existing}, skipping {filename}")
                    stats["duplicates_skipped"] += 1
                    _log_receipt(
                        str(uuid.uuid4()), message_id, filename, "duplicate_skipped",
                        firm_id="INTELLITAX", duplicate_of=existing,
                        duplicate_reason="file_hash_match",
                        run_id=run_id
                    )
                    repo.mark_processed(message_id, att_id, file_hash, existing)
                    continue

                receipt_id = str(uuid.uuid4())
                client_id, firm_id = repo.resolve_client_id(email_from)
                _, _, client_code = repo.resolve_client_info(email_from)
                file_path = save_file(receipt_id, client_code, filename, file_data)
                stats["receipts_created"] += 1

                repo.save_receipt(
                    receipt_id=receipt_id,
                    message_id=message_id,
                    email_subject=subject,
                    email_from=email_from,
                    email_received_at=received_at,
                    filename=filename,
                    file_path=file_path,
                    file_hash=file_hash,
                    firm_id=firm_id,
                    client_id=client_id,
                    client_code=client_code,
                )
                _log_receipt(receipt_id, message_id, filename, "created", firm_id=firm_id, client_id=client_id, run_id=run_id)

                try:
                    extraction = extractor.extract(str(file_path), filename)
                    validation = validate(extraction)

                    duplicate_of = None
                    duplicate_reason = None

                    # Check for semantic duplicates: match on present fields
                    if extraction.supplier_name and extraction.gross_amount is not None:
                        if extraction.invoice_date:
                            # If date is present, match on (supplier, date, amount)
                            existing = repo.find_by_transaction(
                                extraction.supplier_name,
                                extraction.invoice_date,
                                extraction.gross_amount
                            )
                        else:
                            # If date is missing, match on (supplier, amount) only
                            existing = repo.find_by_transaction_no_date(
                                extraction.supplier_name,
                                extraction.gross_amount
                            )

                        if existing:
                            duplicate_of = existing
                            duplicate_reason = "transaction_match"
                            logger.info(f"transaction duplicate: {receipt_id[:8]}... matches {existing[:8]}...")

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
                    )
                    logger.info(f"{receipt_id[:8]}... [{filename}] -> {validation.status}")

                    # Categorise if validation passed
                    if validation.status == "ok" and extraction.supplier_name:
                        categorisation = engine.categorise(
                            receipt_id=receipt_id,
                            extraction_id=extraction_id,
                            supplier_name=extraction.supplier_name,
                            client_id=client_id,
                            business_type=config.CLIENTS.get(email_from.lower(), {}).get("business_type", "UNSPECIFIED")
                        )

                        cat_id = str(uuid.uuid4())
                        repo.save_categorisation(
                            categorisation_id=cat_id,
                            receipt_id=receipt_id,
                            extraction_id=extraction_id,
                            client_id=client_id,
                            business_type=categorisation.business_type,
                            vendor_key=categorisation.vendor_key,
                            suggested_code=categorisation.suggested_code,
                            suggested_name=categorisation.suggested_name,
                            confidence=categorisation.confidence,
                            match_source=categorisation.match_source,
                            matched_vendor=categorisation.matched_vendor,
                            needs_review=categorisation.needs_review,
                            categorised_at=datetime.now(timezone.utc).isoformat()
                        )
                        logger.info(f"{receipt_id[:8]}... categorised: {categorisation.suggested_code} ({categorisation.confidence})")

                    if validation.status == "ok":
                        stats["extractions_succeeded"] += 1
                    elif validation.status == "needs_review":
                        stats["review_flags_issued"] += 1

                    _log_receipt(
                        receipt_id, message_id, filename, "extracted",
                        firm_id=firm_id,
                        extraction_status=validation.status,
                        supplier_name=extraction.supplier_name,
                        invoice_date=extraction.invoice_date,
                        gross_amount=extraction.gross_amount,
                        review_reason=validation.notes[0] if validation.notes else None,
                        duplicate_of=duplicate_of,
                        duplicate_reason=duplicate_reason,
                        run_id=run_id
                    )

                except Exception as exc:
                    logger.error(f"extraction failed {receipt_id[:8]}... [{filename}]: {exc}", exc_info=True)
                    stats["extraction_failures"] += 1
                    repo.save_extraction(
                        extraction_id=str(uuid.uuid4()),
                        receipt_id=receipt_id,
                        engine="openai_vision",
                        supplier_name=None,
                        invoice_date=None,
                        net_amount=None,
                        vat_amount=None,
                        gross_amount=None,
                        currency="GBP",
                        raw_response=str(exc),
                        validation_status="failed",
                        validation_notes=[f"extraction error: {exc}"],
                    )
                    _log_receipt(
                        receipt_id, message_id, filename, "extraction_failed",
                        firm_id=firm_id,
                        extraction_status="failed",
                        review_reason=str(exc),
                        run_id=run_id
                    )

                repo.mark_processed(message_id, att_id, file_hash, receipt_id)

    finally:
        repo.close()
        finished_at = datetime.now(timezone.utc).isoformat()
        duration = (datetime.fromisoformat(finished_at) - datetime.fromisoformat(started_at)).total_seconds()
        stats["duration_seconds"] = round(duration, 2)
        _log_run(run_id, started_at, finished_at, stats)
        logger.info(f"--- run complete ({duration:.1f}s) ---")


def main():
    logger.info(f"receipt capture started — poll every {config.POLL_INTERVAL_SECONDS}s")
    while True:
        try:
            process_once()
        except Exception as exc:
            logger.error(f"run failed: {exc}", exc_info=True)
        logger.info(f"sleeping {config.POLL_INTERVAL_SECONDS}s")
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()

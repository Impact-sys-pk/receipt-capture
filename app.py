import base64
import json
import logging
import os
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import config
from worker.categorisation.engine import CategorisationEngine
from worker.database.repository import Repository
from worker.email.reader import fetch_attachments, fetch_new_messages, move_email_to_folder, fetch_emails_without_attachments, extract_embedded_images
from worker.email.alerts import send_no_attachment_alert, send_unknown_sender_alert
from worker.extraction.openai_vision import OpenAIVisionExtractor
from worker.extraction.retry_helper import extract_with_transient_retry
from worker.extraction_pipeline import process_extraction_result
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

# Wall-clock cutoff for auto-retry, measured from receipts.created_at. A count-based
# cap would be unfair to bursty commit sessions (several pipeline_version bumps in
# an hour would exhaust it almost instantly); wall-clock time isn't affected by that.
AUTO_RETRY_MAX_AGE_DAYS = 7


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


def _count_review_items() -> int:
    review_root = config.CLIENTS_ROOT
    if not review_root.exists():
        return 0
    count = 0
    for path in review_root.rglob("Review/*"):
        if path.is_file():
            count += 1
    return count


def _write_pipeline_status(last_run: str, processed_today: int, review_count: int, last_error: str | None):
    payload = {
        "last_run": last_run,
        "processed_today": processed_today,
        "review_count": review_count,
        "last_error": last_error,
    }
    config.PIPELINE_STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _resolve_client_name(client_code: str) -> str:
    if not client_code:
        return "UNKNOWN"
    return config.CLIENTS_BY_CODE.get(client_code, {}).get("client_name", client_code)


def _remove_inbox_pair(intake) -> None:
    try:
        if intake.source_path.exists():
            intake.source_path.unlink()
    except OSError:
        logger.warning(f"Failed to remove inbox file: {intake.source_path}")
    if intake.sidecar_path:
        try:
            if intake.sidecar_path.exists():
                intake.sidecar_path.unlink()
        except OSError:
            logger.warning(f"Failed to remove inbox sidecar: {intake.sidecar_path}")


def _file_unfiled_ok_receipts(repo: Repository, categorisation_engine: CategorisationEngine, stats: dict[str, int]) -> None:
    unfiled = repo.get_unfiled_ok_receipts()
    if not unfiled:
        return

    logger.info(f"recovering {len(unfiled)} validated receipts that are not yet filed")
    for receipt in unfiled:
        receipt_id = receipt["receipt_id"]
        try:
            extraction = repo.get_extraction_for_receipt(receipt_id)
            if not extraction:
                logger.warning(f"receipt {receipt_id} is marked ok but has no extraction record")
                continue

            source_path = Path(receipt["file_path"])
            if not source_path.exists():
                logger.warning(f"source file missing for receipt {receipt_id}: {source_path}")
                continue

            client_name = _resolve_client_name(receipt["client_code"])
            invoice_date = extraction.get("invoice_date") or datetime.now(timezone.utc).date().isoformat()
            tax_year = determine_tax_year(invoice_date)
            supplier = extraction.get("supplier_name") or "unknown"
            gross = extraction.get("gross_amount") if extraction.get("gross_amount") is not None else 0.0
            currency = extraction.get("currency") or "GBP"

            # Categorise the receipt (reuse the real extraction_id, don't generate a new one)
            business_type = config.CLIENTS_BY_CODE.get(receipt["client_code"], {}).get("business_type", "UNSPECIFIED")
            extraction_id = extraction["extraction_id"]
            categorisation = categorisation_engine.categorise(
                receipt_id=receipt_id,
                extraction_id=extraction_id,
                supplier_name=supplier,
                client_id=receipt["client_id"],
                business_type=business_type
            )

            # Save categorisation
            cat_id = str(uuid.uuid4())
            repo.save_categorisation(
                categorisation_id=cat_id,
                receipt_id=receipt_id,
                extraction_id=extraction_id,
                client_id=receipt["client_id"],
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

            sidecar_payload = make_enriched_sidecar(
                receipt_id=receipt_id,
                source=receipt["source"],
                client_code=receipt["client_code"],
                client_name=client_name,
                capture_date=datetime.now(timezone.utc).isoformat(),
                invoice_date=invoice_date,
                supplier=supplier,
                net=extraction.get("net_amount"),
                vat=extraction.get("vat_amount"),
                gross=gross,
                currency=currency,
                category=categorisation.suggested_code,
                confidence=categorisation.confidence,
                validation_status="ok",
                asserted=None,
                original_filename=receipt["filename"],
                claimed_client_code=None,
            )
            dest_path, sidecar_path = file_receipt(
                source_path,
                client_name,
                tax_year,
                supplier,
                gross,
                receipt["filename"],
                sidecar_payload,
            )
            repo.mark_receipt_filed(receipt_id, dest_path)
            stats["recovery_filed"] = stats.get("recovery_filed", 0) + 1
            logger.info(f"receipt {receipt_id} recovered, categorised as {categorisation.suggested_code}, and filed to {dest_path}")
        except Exception as exc:
            logger.error(f"failed to file recovered receipt {receipt_id}: {exc}", exc_info=True)


def _cleanup_old_backups():
    backups = sorted(config.BACKUPS_ROOT.glob("receipts-*.db"))
    if len(backups) <= 14:
        return
    for old in backups[:-14]:
        try:
            old.unlink()
        except OSError:
            logger.warning(f"Could not remove old backup: {old}")


def _create_daily_backup(repo: Repository):
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    backup_path = config.BACKUPS_ROOT / f"receipts-{today}.db"
    if backup_path.exists():
        return
    config.BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)
    repo.backup_db(backup_path)
    _cleanup_old_backups()


def _is_process_running(pid: int) -> bool:
    try:
        # os.kill(pid, 0) is the standard way to test process existence across platforms.
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def acquire_lock() -> bool:
    lock_path = config.PIPELINE_LOCKFILE
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        try:
            content = lock_path.read_text(encoding="utf-8")
            pid_line = next((line for line in content.splitlines() if line.startswith("pid=")), None)
            existing_pid = int(pid_line.split("=", 1)[1]) if pid_line else None
        except Exception:
            existing_pid = None

        if existing_pid is not None and _is_process_running(existing_pid):
            logger.error("Another pipeline process is already running")
            return False

        logger.warning("Stale pipeline lock detected, removing")
        try:
            lock_path.unlink()
        except OSError:
            logger.error("Unable to remove stale pipeline lock")
            return False

    try:
        with lock_path.open("x", encoding="utf-8") as f:
            f.write(f"pid={os.getpid()}\n")
            f.write(f"started_at={datetime.now(timezone.utc).isoformat()}\n")
        return True
    except FileExistsError:
        logger.error("Failed to acquire pipeline lock")
        return False


def release_lock() -> None:
    try:
        config.PIPELINE_LOCKFILE.unlink()
    except FileNotFoundError:
        pass


def _retry_failed_receipts(repo: Repository, extractor, categorisation_engine, stats: dict, run_id: str, pipeline_version: str) -> None:
    """Part 1: Auto-retry receipts with failed/needs_review status and older pipeline_version.

    Finds receipts that might succeed with the current code, retries them exactly once per version change.
    Uses the same extraction → validation → filing pipeline as normal processing.
    Includes receipts with stale locks (abandoned by crashed resolve_receipt.py), which acquire_receipt_lock()
    will recover and claim atomically.

    Receipts stuck in failed/needs_review for more than AUTO_RETRY_MAX_AGE_DAYS (measured from
    created_at) are transitioned to retry_exhausted instead of being retried again. This is
    evaluated lazily here, not by a separate background job. Manual resolve_receipt.py runs are
    unaffected: they don't touch created_at, and resolve_receipt.py has no status guard, so it can
    still resolve a retry_exhausted receipt directly.
    """
    from datetime import timedelta
    stale_lock_cutoff = (datetime.now(timezone.utc) - timedelta(minutes=60)).isoformat()
    retry_age_cutoff = datetime.now(timezone.utc) - timedelta(days=AUTO_RETRY_MAX_AGE_DAYS)
    failed = repo.find_failed_by_version(pipeline_version, stale_lock_cutoff)
    if not failed:
        return

    logger.info(f"retrying {len(failed)} receipt(s) with older pipeline_version")

    for receipt in failed:
        receipt_id = receipt['receipt_id']
        file_path = Path(receipt['file_path'])

        # Try to acquire lock (handles stale-lock recovery automatically)
        acquired = repo.acquire_receipt_lock(receipt_id, allow_stale_after_minutes=60)
        if not acquired:
            logger.debug(f"skipping locked receipt {receipt_id} (held by another process)")
            continue

        try:
            created_at = datetime.fromisoformat(receipt['created_at'])
            if created_at < retry_age_cutoff:
                logger.info(f"retry window exceeded ({AUTO_RETRY_MAX_AGE_DAYS}d) for {receipt_id}, marking retry_exhausted")
                repo.update_receipt_status(receipt_id, 'retry_exhausted')
                stats['retry_exhausted_count'] = stats.get('retry_exhausted_count', 0) + 1
                continue

            # Defensive: check file exists
            if not file_path.exists():
                logger.warning(f"source file missing for {receipt_id}: {file_path}")
                # Record the attempt against the current pipeline_version.
                # Without a row carrying this version, find_failed_by_version()
                # keeps selecting the receipt on every poll, warning and
                # appending another note each time, forever.
                repo.save_extraction(
                    extraction_id=str(uuid.uuid4()),
                    receipt_id=receipt_id,
                    engine=extractor.name,
                    supplier_name=None, invoice_date=None,
                    net_amount=None, vat_amount=None, gross_amount=None,
                    currency="GBP",
                    raw_response=f"original file missing, cannot retry: {file_path}",
                    validation_status="failed",
                    validation_notes=[f"original file missing, cannot retry: {file_path}"],
                    pipeline_version=pipeline_version,
                    update_status=False,
                )
                continue

            # Re-extract with transient retry
            logger.info(f"auto-retrying {receipt_id}")
            extraction = extract_with_transient_retry(extractor, file_path, receipt['filename'])

            # Process through shared pipeline
            status, filed_path = process_extraction_result(
                receipt_id=receipt_id,
                extraction=extraction,
                file_path=file_path,
                filename=receipt['filename'],
                client_code=receipt['client_code'],
                firm_id=receipt['firm_id'],
                client_id=receipt['client_id'],
                message_id=receipt.get('message_id'),
                attachment_id=None,  # Email dedup already done
                file_hash=None,
                asserted_values=None,
                repo=repo,
                categorisation_engine=categorisation_engine,
                stats=stats,
                run_id=run_id,
                pipeline_version=pipeline_version
            )

            if status == "ok":
                logger.info(f"auto-retry succeeded: {receipt_id}")
                stats['auto_retried_ok'] = stats.get('auto_retried_ok', 0) + 1
            elif status == "possible_duplicate":
                logger.info(f"auto-retry detected possible duplicate: {receipt_id}")
                stats['possible_duplicates_found'] = stats.get('possible_duplicates_found', 0) + 1
            else:
                logger.info(f"auto-retry failed: {receipt_id} (status={status})")
                stats['auto_retried_failed'] = stats.get('auto_retried_failed', 0) + 1

        except Exception as exc:
            logger.error(f"auto-retry error for {receipt_id}: {exc}", exc_info=True)
            stats['auto_retry_errors'] = stats.get('auto_retry_errors', 0) + 1
            # Record the failed attempt against the current pipeline_version.
            # process_extraction_result() never ran, so no extraction row was
            # written, so the latest row still carries the OLD version and
            # find_failed_by_version() would re-select this receipt on every
            # poll. Via extract_with_transient_retry that is three real OpenAI
            # calls every five minutes, indefinitely.
            # update_status=False: the API crashed, the document did not, so
            # a needs_review receipt must not be flipped to failed.
            repo.save_extraction(
                extraction_id=str(uuid.uuid4()),
                receipt_id=receipt_id,
                engine=extractor.name,
                supplier_name=None, invoice_date=None,
                net_amount=None, vat_amount=None, gross_amount=None,
                currency="GBP",
                raw_response=str(exc),
                validation_status="failed",
                validation_notes=[f"auto-retry extraction error: {exc}"],
                pipeline_version=pipeline_version,
                update_status=False,
            )
        finally:
            # Release lock (acquired at line 282)
            repo.release_receipt_lock(receipt_id)


def process_once():
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    pipeline_version = config.get_pipeline_version()
    logger.info(f"--- run {run_id[:8]}... start (pipeline_version={pipeline_version}) ---")
    repo = None
    errors = None
    stats = {
        "messages_found": 0,
        "attachments_processed": 0,
        "receipts_created": 0,
        "duplicates_skipped": 0,
        "extraction_failures": 0,
        "extractions_succeeded": 0,
        "review_flags_issued": 0,
        "auto_retried_ok": 0,
        "auto_retried_failed": 0,
        "auto_retry_errors": 0,
        "possible_duplicates_found": 0,
        "retry_exhausted_count": 0,
    }

    try:
        repo = Repository()
        extractor = OpenAIVisionExtractor()
        engine = CategorisationEngine(repo=repo, enable_ai_fallback=False)

        # Part 1: Auto-retry failed receipts with older pipeline_version
        _retry_failed_receipts(repo, extractor, engine, stats, run_id, pipeline_version)

        _file_unfiled_ok_receipts(repo, engine, stats)

        intake_records = scan_inbox()
        logger.info(f"capture inbox files found: {len(intake_records)}")

        # Check for emails without attachments
        no_attachment_emails = fetch_emails_without_attachments()
        logger.info(f"emails without attachments: {len(no_attachment_emails)}")
        for email_msg in no_attachment_emails:
            message_id = email_msg["id"]
            uid = email_msg["uid"]
            email_from = email_msg["from"]

            # Try to extract embedded images from the email
            embedded_images = extract_embedded_images(email_msg["msg"])
            logger.info(f"extracted {len(embedded_images)} embedded images from {message_id}")

            # If embedded images found, treat them as attachments and process normally
            if embedded_images:
                # Resolve client
                client_id, firm_id = repo.resolve_client_id(email_from)
                _, _, client_code = repo.resolve_client_info(email_from)

                # Check for unknown sender
                if client_id == "UNKNOWN":
                    logger.info(f"unknown sender: {email_from}")
                    stats["review_flags_issued"] = stats.get("review_flags_issued", 0) + 1

                    if not repo.has_alert_been_sent(message_id, "unknown_sender"):
                        recipient_email = email_from
                        if "<" in email_from and ">" in email_from:
                            recipient_email = email_from.split("<")[1].split(">")[0].strip()

                        if send_unknown_sender_alert(recipient_email):
                            repo.record_alert_sent(message_id, "unknown_sender", recipient_email, "Unknown")

                    move_email_to_folder(uid, "INBOX.Unknown Sender")
                    continue

                # Process embedded images like normal attachments
                for embedded_img in embedded_images:
                    att_id = embedded_img["id"]
                    filename = embedded_img["name"]
                    stats["attachments_processed"] += 1

                    file_data = base64.b64decode(embedded_img.get("contentBytes", ""))
                    file_hash = compute_hash(file_data)

                    # Check for duplicates
                    existing = repo.find_by_hash(file_hash)
                    if existing:
                        logger.info(f"hash duplicate of {existing}, skipping embedded image {filename}")
                        stats["duplicates_skipped"] += 1
                        repo.mark_processed(message_id, att_id, file_hash, existing)
                        move_email_to_folder(uid, "INBOX.Duplicates")
                        continue

                    receipt_id = str(uuid.uuid4())
                    file_path = save_file(receipt_id, client_code, filename, file_data)
                    stats["receipts_created"] += 1

                    repo.save_receipt(
                        receipt_id=receipt_id,
                        message_id=message_id,
                        email_subject=email_msg.get("subject", ""),
                        email_from=email_from,
                        email_received_at=email_msg.get("receivedDateTime", ""),
                        filename=filename,
                        file_path=file_path,
                        file_hash=file_hash,
                        firm_id=firm_id,
                        client_id=client_id,
                        client_code=client_code,
                    )
                    _log_receipt(receipt_id, message_id, filename, "created", firm_id=firm_id, client_id=client_id, run_id=run_id)

                    # Extract and process
                    try:
                        extraction = extractor.extract(str(file_path), filename)
                        validation = validate(extraction)

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

                        if validation.status == "ok":
                            stats["extractions_succeeded"] += 1
                        else:
                            stats["review_flags_issued"] += 1

                        _log_receipt(
                            receipt_id, message_id, filename, "extracted",
                            firm_id=firm_id,
                            extraction_status=validation.status,
                            supplier_name=extraction.supplier_name,
                            invoice_date=extraction.invoice_date,
                            gross_amount=extraction.gross_amount,
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

                # After processing all embedded images, move to Processed Receipts if all ok
                move_email_to_folder(uid, "INBOX.Processed Receipts")
                continue

            # No attachments and no embedded images - send alert
            # Skip if we've already sent an alert for this email
            if repo.has_alert_been_sent(message_id, "no_attachment"):
                logger.info(f"alert already sent for {message_id}, skipping")
                continue

            # Resolve sender to firm
            client_info = repo.resolve_client_info(email_from)
            client_id, firm_id, client_code = client_info

            # Get firm name
            firm_name = config.FIRMS.get(firm_id, {}).get("name", firm_id)

            # Extract email address (handle "Name <email>" format)
            recipient_email = email_from
            if "<" in email_from and ">" in email_from:
                recipient_email = email_from.split("<")[1].split(">")[0].strip()

            # Send alert
            if send_no_attachment_alert(recipient_email, firm_name):
                repo.record_alert_sent(message_id, "no_attachment", recipient_email, firm_name)
                stats["review_flags_issued"] = stats.get("review_flags_issued", 0) + 1

            # Move email to "No Attachments" folder
            move_email_to_folder(uid, "INBOX.No Attachments")

        messages = fetch_new_messages(repo)
        stats["messages_found"] = len(messages)
        logger.info(f"messages with attachments: {len(messages)}")

        for intake in intake_records:
            if intake.is_statement:
                if repo.find_statement_by_hash(intake.file_hash):
                    logger.info(f"capture duplicate statement by hash, removing inbox pair {intake.filename}")
                    _remove_inbox_pair(intake)
                    stats["duplicates_skipped"] += 1
                    stats["inbox_duplicates_removed"] = stats.get("inbox_duplicates_removed", 0) + 1
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

            # Part 2A: Only block if genuinely filed (filed_path IS NOT NULL)
            existing = repo.find_by_hash(intake.file_hash)
            if existing:
                if repo.is_recorded_and_filed(existing):
                    logger.info(f"capture duplicate by hash of filed receipt, removing inbox pair {intake.filename}")
                    _remove_inbox_pair(intake)
                    stats["duplicates_skipped"] += 1
                    stats["inbox_duplicates_removed"] = stats.get("inbox_duplicates_removed", 0) + 1
                    continue
                # If hash matches a failed/needs_review receipt, allow reprocessing
                logger.info(f"capture duplicate by hash of failed receipt, allowing reprocessing {intake.filename}")
                # Continue processing (don't skip)

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

            client_name = config.CLIENTS_BY_CODE.get(intake.client_code, {}).get("client_name", intake.client_code)

            # Build sidecar assertion values (folder-specific)
            asserted_values = None
            if intake.sidecar:
                asserted = {k: intake.sidecar.get(k) for k in ("supplier_name", "invoice_date", "net_amount", "vat_amount", "gross_amount", "client_code") if k in intake.sidecar}
                if asserted:
                    # Will be used in shared function to detect mismatches
                    asserted_values = asserted

            try:
                # Extract with transient-error retry
                extraction = extract_with_transient_retry(extractor, file_path, intake.filename)

                # Process through shared pipeline (validate → duplicate-check → categorise → file)
                status, filed_path = process_extraction_result(
                    receipt_id=receipt_id,
                    extraction=extraction,
                    file_path=file_path,
                    filename=intake.filename,
                    client_code=intake.client_code,
                    firm_id=intake.firm_id,
                    client_id=intake.client_id,
                    message_id=None,  # Folder intake, not email
                    attachment_id=None,
                    file_hash=None,
                    asserted_values=asserted_values,
                    repo=repo,
                    categorisation_engine=engine,
                    stats=stats,
                    run_id=run_id,
                    pipeline_version=pipeline_version
                )

                # Remove inbox pair if successfully processed
                if status == "ok":
                    _remove_inbox_pair(intake)

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
                    pipeline_version=pipeline_version,
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
            uid = msg["uid"]
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
                    move_email_to_folder(uid, "INBOX.Unsupported Files")
                    continue

                if repo.is_duplicate(message_id, att_id):
                    logger.info(f"skip duplicate: {message_id}/{att_id}")
                    stats["duplicates_skipped"] += 1
                    _log_receipt(
                        str(uuid.uuid4()), message_id, filename, "duplicate_skipped",
                        firm_id="INTELLITAX", duplicate_reason="message_id_match",
                        run_id=run_id
                    )
                    move_email_to_folder(uid, "INBOX.Duplicates")
                    continue

                file_data = base64.b64decode(att.get("contentBytes", ""))
                file_hash = compute_hash(file_data)

                # Part 2A: Only block if genuinely filed (filed_path IS NOT NULL)
                existing = repo.find_by_hash(file_hash)
                if existing and repo.is_recorded_and_filed(existing):
                    logger.warning(f"hash duplicate of {existing}, skipping {filename}")
                    stats["duplicates_skipped"] += 1
                    _log_receipt(
                        str(uuid.uuid4()), message_id, filename, "duplicate_skipped",
                        firm_id="INTELLITAX", duplicate_of=existing,
                        duplicate_reason="file_hash_match",
                        run_id=run_id
                    )
                    repo.mark_processed(message_id, att_id, file_hash, existing)
                    move_email_to_folder(uid, "INBOX.Duplicates")
                    continue
                # If file_hash matches a failed/needs_review receipt, allow reprocessing

                receipt_id = str(uuid.uuid4())
                client_id, firm_id = repo.resolve_client_id(email_from)
                _, _, client_code = repo.resolve_client_info(email_from)
                client_name = config.CLIENTS_BY_CODE.get(client_code, {}).get("client_name", client_code)

                # Check for unknown sender
                if client_id == "UNKNOWN":
                    logger.info(f"unknown sender: {email_from}")
                    stats["review_flags_issued"] = stats.get("review_flags_issued", 0) + 1

                    # Skip if alert already sent
                    if not repo.has_alert_been_sent(message_id, "unknown_sender"):
                        # Extract email address (handle "Name <email>" format)
                        recipient_email = email_from
                        if "<" in email_from and ">" in email_from:
                            recipient_email = email_from.split("<")[1].split(">")[0].strip()

                        # Send alert
                        if send_unknown_sender_alert(recipient_email):
                            repo.record_alert_sent(message_id, "unknown_sender", recipient_email, "Unknown")

                    # Move to Unknown Sender folder
                    move_email_to_folder(uid, "INBOX.Unknown Sender")
                    _log_receipt(receipt_id, message_id, filename, "unknown_sender",
                                firm_id="INTELLITAX", run_id=run_id)
                    continue

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
                    # Extract with transient-error retry
                    extraction = extract_with_transient_retry(extractor, file_path, filename)

                    # Process through shared pipeline (validate → duplicate-check → categorise → file)
                    status, filed_path = process_extraction_result(
                        receipt_id=receipt_id,
                        extraction=extraction,
                        file_path=file_path,
                        filename=filename,
                        client_code=client_code,
                        firm_id=firm_id,
                        client_id=client_id,
                        message_id=message_id,
                        attachment_id=att_id,
                        file_hash=file_hash,
                        asserted_values=None,
                        repo=repo,
                        categorisation_engine=engine,
                        stats=stats,
                        run_id=run_id,
                        pipeline_version=pipeline_version
                    )

                    # Route email based on outcome
                    if status == "ok":
                        move_email_to_folder(uid, "INBOX.Processed Receipts")
                    elif status == "possible_duplicate":
                        move_email_to_folder(uid, "INBOX.Possible Duplicate")
                    elif status == "needs_review":
                        move_email_to_folder(uid, "INBOX.Needs Review")
                    elif status == "failed":
                        move_email_to_folder(uid, "INBOX.Failed Processing")

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
                        pipeline_version=pipeline_version,
                    )
                    _log_receipt(
                        receipt_id, message_id, filename, "extraction_failed",
                        firm_id=firm_id,
                        extraction_status="failed",
                        review_reason=str(exc),
                        run_id=run_id
                    )
                    move_email_to_folder(uid, "INBOX.Failed Processing")
                    # Mark processed even on failure (extraction error)
                    repo.mark_processed(message_id, att_id, file_hash, receipt_id)

    except Exception as exc:
        errors = exc
        logger.error(f"process_once failed: {exc}", exc_info=True)
        raise
    finally:
        processed_today = stats.get("receipts_created", 0)
        review_count = _count_review_items()
        last_error = None if errors is None else str(errors)
        _write_pipeline_status(datetime.now(timezone.utc).isoformat(), processed_today, review_count, last_error)
        if repo is not None:
            try:
                _create_daily_backup(repo)
            except Exception as backup_exc:
                logger.warning(f"Daily backup failed: {backup_exc}")
            repo.close()
        finished_at = datetime.now(timezone.utc).isoformat()
        duration = (datetime.fromisoformat(finished_at) - datetime.fromisoformat(started_at)).total_seconds()
        stats["duration_seconds"] = round(duration, 2)
        _log_run(run_id, started_at, finished_at, stats)
        logger.info(f"--- run complete ({duration:.1f}s) ---")


def main():
    logger.info(f"receipt capture started — poll every {config.POLL_INTERVAL_SECONDS}s")
    # Part 1: Check for uncommitted changes that might invalidate pipeline_version
    config.check_git_status_on_startup()
    if not acquire_lock():
        logger.error("Exiting because another pipeline instance is active")
        return
    try:
        while True:
            try:
                process_once()
            except Exception as exc:
                logger.error(f"run failed: {exc}", exc_info=True)
            logger.info(f"sleeping {config.POLL_INTERVAL_SECONDS}s")
            time.sleep(config.POLL_INTERVAL_SECONDS)
    finally:
        release_lock()


if __name__ == "__main__":
    main()

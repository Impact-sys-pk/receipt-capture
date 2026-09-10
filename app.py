import base64
import ctypes
import ctypes.wintypes
import json
import logging
import logging.handlers
import os
import shutil
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import config
from worker.categorisation.engine import CategorisationEngine
from worker.categorisation.fallback import resolve_against_chart
from worker.database.repository import Repository
from worker.email.reader import fetch_attachments, fetch_new_messages, move_email_to_folder, fetch_emails_without_attachments, extract_embedded_images
from worker.email.alerts import send_no_attachment_alert, send_unknown_sender_alert
from worker.extraction.factory import get_extractor
from worker.extraction.retry_helper import extract_with_transient_retry
from worker.client_copy import copy_for_published_receipt
from worker.extraction_pipeline import process_extraction_result
from worker.intake.folder_reader import EMAIL_SOURCE, scan_inbox
from worker.logging_setup import LOG_FORMAT, attach_log_handler
from worker.resolution.service import NOTE_APPLIED_OUTCOMES, apply_resolution_note
from worker.filing import (
    determine_tax_year,
    file_statement,
    file_review,
    make_enriched_sidecar,
)
from worker.publish import extra_for, publish_receipt
from worker.storage.store import compute_hash, is_supported, save_file, save_inbox_file
from worker.validation.rules import validate

_LOG_FORMAT = LOG_FORMAT  # one definition, in worker/logging_setup.py

logging.basicConfig(
    level=logging.INFO,
    format=_LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def attach_run_log_handler():
    """Attach the pipeline's data/run.log handler.

    Kept as a named wrapper because it is this entry point's own step, and because
    the one-line body documents which log file the pipeline owns. The shared
    implementation is in worker/logging_setup.py, per design document 6.5, so the
    CLIs and later the console attach their own files the same way.
    """
    return attach_log_handler("run")


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

    log_path = config.LOGS_DIR / f"receipt_events_{firm_id or config.UNATTRIBUTED_FIRM_ID}.ndjson"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


REVIEW_STATUSES = ("needs_review", "possible_duplicate")

# Where an email goes for each extraction outcome, worst first. The order is the
# tie-break when one email carries several images whose outcomes differ, which is
# Paul's decision of 2026-09-07: the worst outcome wins, because a person looking
# in INBOX.Failed Processing wants to see every email that needs them, and an
# email holding one good image and one failure needs them.
#
# The four folders and the four statuses are the attachment path's, unchanged.
# That path routes one email on one outcome and never faces a tie, so it keeps
# its own if/elif chain and this table is not imposed on it; the two are held in
# step by tests/test_embedded_email_routing.py, which drives both paths over each
# outcome and compares.
#
# An extraction that RAISED is "failed" here, because that is the
# validation_status the exception branch writes and because the attachment path
# sends both to the same folder. To the person opening the mailbox they are one
# thing: the document could not be read.
#
# `possible_duplicate` cannot arise on the embedded-image path today, because
# that path does not call process_extraction_result() and so never runs the
# semantic duplicate check. It is in the table because the ranking is a decision
# about outcomes rather than about which path can currently produce them.
EMAIL_OUTCOME_FOLDERS = (
    ("unsupported", "INBOX.Unsupported Files"),
    ("failed", "INBOX.Failed Processing"),
    ("needs_review", "INBOX.Needs Review"),
    ("possible_duplicate", "INBOX.Possible Duplicate"),
    ("ok", "INBOX.Processed Receipts"),
    ("duplicate", "INBOX.Duplicates"),
)


def _worst_outcome_folder(outcomes) -> str | None:
    """The folder for the worst outcome in `outcomes`, or None for no move.

    None has two meanings and both are deliberate:

    - **Nothing to rank.** Every image took the duplicate branch, which moved the
      email itself and continued, so the email is already in INBOX.Duplicates and
      must not be moved again.
    - **An outcome this table does not name.** The email stays in INBOX and is
      offered again on the next poll, which is what the attachment path's
      if/elif chain does with an unrecognised status, having no else.
    """
    for status, folder in EMAIL_OUTCOME_FOLDERS:
        if status in outcomes:
            return folder
    return None


def _count_review_items(repo: Repository | None) -> int:
    """Count receipts a human has to make a decision about.

    This used to walk CLIENTS_ROOT.rglob("Review/*") and count every file, so it
    counted each pair twice (image plus sidecar) and, because nothing removed the
    pairs, only ever grew. The database is the stated source of truth.

    needs_review and possible_duplicate only. failed and retry_exhausted are not
    review items, they are receipts the system could not read, and counting them
    here would send an operator to look at something there is nothing to look at
    yet. The status page reports them as their own counts.

    repo is None when Repository() itself failed. The only call site is inside
    process_once()'s finally block, so raising here would mask the real error.
    """
    if repo is None:
        return 0
    return repo.count_receipts_by_status(REVIEW_STATUSES)


def _write_pipeline_status(last_run: str, processed_today: int, review_count: int, last_error: str | None):
    """The status file IntelliBooks Desktop reads. Five keys, and the shape is a contract.

    `practice_root` is sub-step 10e.10, named by amendment 241 of
    `2026-07-25_CONSOLE_DESIGN.md`. **The browser hands IntelliBooks a folder
    handle and a folder name and no path**, so until this field existed
    IntelliBooks could not say which folder it was working in, nor tell the right
    folder from a similarly-named wrong one. 10e.9 settles that the pipeline's
    configuration is the single authority, because the pipeline cannot read a
    file inside the practice root to learn where the practice root is.
    **IntelliBooks verifies; it does not decide.**

    **The value is `str(config.PRACTICE_ROOT)` as configured, and is deliberately
    not resolved, normalised or case-folded.** The point of the field is that a
    person can reconcile what IntelliBooks shows against `.env`, which is where
    `config.py`'s `_required_root()` reads it from, and see the same
    characters. `.resolve()` collapses `..` and case-folds an existing path, so
    it can differ from the configured string through a junction, a symlink or
    the case somebody typed, and the two products would then disagree over a
    difference that does not exist.

    **Written on every cycle including a failed one**, because the call site at
    the `finally:` block below already guarantees that and the field is not
    conditional. The case where IntelliBooks most needs to know which folder it
    is looking at is the case where the pipeline is unhealthy.

    Backslashes are escaped by `json.dumps()`. That is correct JSON and is not
    worked around.
    """
    payload = {
        "last_run": last_run,
        "processed_today": processed_today,
        "review_count": review_count,
        "last_error": last_error,
        "practice_root": str(config.PRACTICE_ROOT),
    }
    config.PIPELINE_STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _client_folder_name(client_id: str) -> str | None:
    """The folder under Clients for this client, or None if it cannot be resolved.

    Sub-step 10d.13 deletes the fallback that used to sit here, which was
    `CLIENTS_BY_CODE.get(client_code, {}).get("client_name", client_code)`: it
    silently substituted the code for the name whenever the lookup missed, and on
    2026-09-01 that filed four TESTST receipts into a TESTST folder while
    IntelliBooks looked under Test Sole Trader and found nothing, with no message
    on screen.

    Returning None is the whole point. A caller that cannot name the folder must
    not file into Clients at all: the item goes to Review, per 10d.18.
    """
    if not client_id or client_id == config.UNKNOWN_CLIENT_ID:
        return None
    folder = (config.CLIENTS_BY_ID.get(client_id) or {}).get("client_folder_name")
    return folder or None


def _review_key(client_id: str | None) -> str:
    """The Review subfolder name for a client, or for one that could not be resolved.

    Sub-step 10d.54: Intellibills\\Review\\ is keyed on client_id. An item with
    no client still needs somewhere to go, per 10d.18, and it goes under the
    reserved UNKNOWN id rather than being dropped or guessed at. scanReview() in
    IntelliBooks-Desktop-v3.html reads one folder per client, so this is a real
    folder a person can be pointed at.
    """
    return client_id or config.UNKNOWN_CLIENT_ID


def _iso_utc(value) -> str | None:
    """One timestamp format for receipts.email_received_at: ISO 8601 UTC. 10d.27.

    The column used to take whatever each path had: an RFC-shaped string from the
    mail server on one, an integer mtime on the other, into the same TEXT column,
    so the two could not be compared or sorted against each other.

    A value that cannot be read is returned as None rather than as a guess. A
    NULL says the arrival time is not known; a plausible wrong timestamp does not.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
    else:
        text = str(value).strip()
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = parsedate_to_datetime(text)
            except (TypeError, ValueError):
                logger.warning(f"could not read an arrival timestamp from {text!r}; recording NULL")
                return None
        if dt is None:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _iso_utc_from_mtime(path: Path) -> str | None:
    """The arrival time of a folder-intake file, as ISO 8601 UTC. 10d.27."""
    try:
        return _iso_utc(path.stat().st_mtime)
    except OSError as exc:
        logger.warning(f"could not read the modification time of {path}: {exc}; recording NULL")
        return None


def _mailbox_firm_name() -> str:
    """The firm whose capture mailbox this pipeline polls, for an unknown sender.

    Sub-step 10d.36. send_unknown_sender_alert() is the only automatic email that
    reaches somebody who is not a known client, so it is the first thing an
    unregistered sender sees, and it named the wrong company.

    There is no client to take a firm from, by definition, so the firm is the one
    that owns the mailbox. One pipeline instance polls one mailbox, so where the
    registry holds exactly one firm that is the answer. Where it holds none or
    several, this returns an empty string and the alert falls back to wording that
    names nobody, which is better than naming the wrong firm. Row F7 of
    2026-08-20_LIST_settings_firm_and_client.md records the multi-firm case as a
    wall: a single local mailbox cannot tell which firm an unknown sender meant.
    """
    firms = list(config.FIRMS.values())
    if len(firms) == 1:
        return firms[0].get("name", "") or ""
    logger.warning(
        f"{len(firms)} firms in {config.FIRMS_JSON.name}, so the firm behind the capture mailbox "
        "cannot be identified for an unknown-sender alert; sending it without a firm name"
    )
    return ""


# _remove_inbox_pair() was here until 2026-09-07. Sub-step 10f.21, amendment 137,
# closing outstanding item 144. It unlinked the inbox original and its sidecar,
# and its two callers were the only places left where something a client sent was
# deleted: step 9c had already moved the `ok` path from a delete to a move on
# CLAUDE.md's no-data-loss rule, and left the two duplicate paths behind. So an
# identical resend through the phone or Add Receipts removed the file from disk
# with one log line and no receipt row. Both callers now use
# _move_inbox_pair_to_processed() below, which is what every other outcome uses.

INBOX_PROCESSED_DIRNAME = "Processed"


def _unique_processed_stem(directory: Path, name: str) -> str:
    """A stem in `directory` that neither an image nor a sidecar already uses.

    Same `-2`, `-3` convention as `_unique_path()` in worker/filing.py. The stem
    is chosen for the pair rather than the image alone, because the inbox scanner
    finds a sidecar with `Path.with_suffix('.json')`: an image landing as
    `x-2.png` needs its sidecar at `x-2.json` or the two stop being a pair.
    """
    stem = Path(name).stem
    ext = Path(name).suffix
    index = 1
    while True:
        candidate = stem if index == 1 else f"{stem}-{index}"
        if not (directory / f"{candidate}{ext}").exists() and not (
            directory / f"{candidate}.json"
        ).exists():
            return candidate
        index += 1


def _move_inbox_pair_to_processed(intake) -> None:
    """Move a folder-intake original, and any sidecar, out of the client's inbox.

    Design document 3.13. This runs on **every** outcome, not only `ok`. Anything
    left behind is found by `find_by_hash()` on the next poll, is not
    `is_recorded_and_filed()` because `filed_path` is NULL, and is then
    deliberately reprocessed: a new receipt row, a new extraction row, a new
    Review pair and one OpenAI call, every five minutes, indefinitely.

    A move rather than a delete, per CLAUDE.md's no-data-loss rule, and that
    applies to the `ok` path too, which used to delete. The reprocessing rule this
    makes unreachable is deliberately left alone: it still guards the genuine
    resend of a file an operator puts back by hand.
    """
    source = intake.source_path
    sidecar = intake.sidecar_path
    if not source.exists() and not (sidecar and sidecar.exists()):
        return

    processed_dir = source.parent / INBOX_PROCESSED_DIRNAME
    try:
        processed_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error(
            f"could not create {processed_dir}: {exc}; leaving {source.name} in the inbox, "
            "where it will be reprocessed on the next poll"
        )
        return

    stem = _unique_processed_stem(processed_dir, source.name)

    if source.exists():
        destination = processed_dir / f"{stem}{source.suffix}"
        try:
            shutil.move(str(source), str(destination))
            logger.info(f"inbox original moved out of the inbox: {destination}")
        except OSError as exc:
            logger.error(
                f"could not move {source} to {destination}: {exc}; it will be reprocessed "
                "on the next poll"
            )
            return

    if sidecar and sidecar.exists():
        destination = processed_dir / f"{stem}.json"
        try:
            shutil.move(str(sidecar), str(destination))
        except OSError as exc:
            # An orphaned sidecar is re-read by scan_inbox() on every poll, but it
            # produces no receipt and costs nothing, so this is a warning.
            logger.warning(f"could not move inbox sidecar {sidecar} to {destination}: {exc}")


NOTE_PROCESSED_DIRNAME = "processed"
NOTE_FAILED_DIRNAME = "failed"


def _unique_note_destination(directory: Path, name: str) -> Path:
    """Where to put a note in `directory` without overwriting one already there.

    Nothing in Resolutions\\ is ever deleted, and that includes being deleted by
    being written over. Two notes can share a name: the same note re-delivered, or
    a note the operator copied back to be retried.
    """
    stem = Path(name).stem
    suffix = Path(name).suffix
    index = 1
    while True:
        candidate = directory / (name if index == 1 else f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _move_note(note_path: Path, directory_name: str, error_text: str | None = None) -> None:
    """Move a note into processed\\ or failed\\, never delete it.

    An error writes a `.error.txt` beside it, named after the note as it landed, so
    a human reading failed\\ can see which note the reason belongs to.
    """
    target_dir = note_path.parent / directory_name
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        destination = _unique_note_destination(target_dir, note_path.name)
        shutil.move(str(note_path), str(destination))
    except OSError as exc:
        # The note stays in the queue and is tried again next poll. Idempotency in
        # 12.3 step 3 is what makes that safe.
        logger.error(f"could not move resolution note {note_path} to {directory_name}\\: {exc}")
        return

    if error_text is not None:
        try:
            destination.with_name(destination.name + ".error.txt").write_text(
                error_text, encoding="utf-8"
            )
        except OSError as exc:
            logger.error(f"could not write the error file for {destination}: {exc}")


def _consume_resolution_notes(
    repo: Repository, categorisation_engine: CategorisationEngine, stats: dict[str, int]
) -> None:
    """Apply the resolution notes IntelliBooks Desktop has written. Design document 12.3.

    Runs at the start of process_once(), before _retry_failed_receipts(), so a
    receipt resolved by note is never re-extracted in the cycle it was resolved.
    That ordering is the whole reason this runs first and it is worth a comment at
    the call site too.

    Every failure moves the note to failed\\ with the reason beside it and logs at
    ERROR: a note sitting in failed\\ means the database and the books disagree,
    which is the one thing this contract exists to prevent. Nothing is ever deleted.
    """
    resolutions_dir = config.RESOLUTIONS_DIR
    try:
        resolutions_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error(f"cannot reach the resolutions folder {resolutions_dir}: {exc}")
        return

    # Oldest first by filename. The name is {receipt_id}_{unix_ms}.json, so this is
    # time order per receipt, which is the order that matters: two notes for one
    # receipt must be applied in the order they were made.
    notes = sorted(
        (path for path in resolutions_dir.glob("*.json") if path.is_file()),
        key=lambda path: path.name,
    )
    if not notes:
        return

    logger.info(f"resolution notes to apply: {len(notes)}")

    for note_path in notes:
        try:
            payload = json.loads(note_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.error(f"unreadable resolution note {note_path.name}: {exc}")
            stats["notes_failed"] = stats.get("notes_failed", 0) + 1
            _move_note(note_path, NOTE_FAILED_DIRNAME, f"could not read this note: {exc}\n")
            continue

        outcome = apply_resolution_note(repo, categorisation_engine, payload)

        if outcome.outcome in NOTE_APPLIED_OUTCOMES:
            logger.info(
                f"resolution note {note_path.name} applied: {outcome.outcome}, {outcome.message}"
            )
            stats["notes_applied"] = stats.get("notes_applied", 0) + 1
            _move_note(note_path, NOTE_PROCESSED_DIRNAME)
        else:
            logger.error(
                f"resolution note {note_path.name} not applied ({outcome.outcome}): "
                f"{outcome.error_detail or outcome.message}"
            )
            stats["notes_failed"] = stats.get("notes_failed", 0) + 1
            _move_note(
                note_path, NOTE_FAILED_DIRNAME,
                f"outcome: {outcome.outcome}\n"
                f"receipt_id: {outcome.receipt_id}\n"
                f"reason: {outcome.error_detail or outcome.message}\n",
            )


def _publish_unpublished_receipts(repo: Repository, categorisation_engine: CategorisationEngine, stats: dict[str, int]) -> None:
    """Publish anything that was read and never published. Sub-step 10f.13.

    **This is the recovery sweep, repointed rather than deleted.** Paul's
    decision of 2026-09-08, option B of three: what it protects against is a
    receipt that got read and then had nothing happen to it, and that risk moves
    when filing becomes publishing rather than disappearing.

    It used to file into the client folder and was the third of the three writers
    amendment 278 counted. It now publishes, and the client folder copy that
    follows a successful publish is written by the same gated function every
    other route uses.

    `get_unpublished_ok_receipts()` carries the cutover that keeps this from
    backfilling every historical receipt, and the reasoning is in its docstring.
    """
    unfiled = repo.get_unpublished_ok_receipts()
    if not unfiled:
        return

    logger.info(f"recovering {len(unfiled)} validated receipts that were never published")
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

            client_folder_name = _client_folder_name(receipt["client_id"])
            if not client_folder_name:
                # 10d.18. An unresolved client files nothing into Clients. This
                # receipt is already ok and already has its document store copy;
                # leaving it unfiled is the honest outcome and it is reported.
                logger.warning(
                    f"receipt {receipt_id} is ok but its client {receipt['client_id']} has no "
                    "client_folder_name in the registry, so it is not filed into Clients"
                )
                continue
            invoice_date = extraction.get("invoice_date") or datetime.now(timezone.utc).date().isoformat()
            tax_year = determine_tax_year(invoice_date)
            supplier = extraction.get("supplier_name") or "unknown"
            gross = extraction.get("gross_amount") if extraction.get("gross_amount") is not None else 0.0
            currency = extraction.get("currency") or config.DEFAULT_CURRENCY

            # Categorise the receipt (reuse the real extraction_id, don't generate a new one)
            trade = (config.CLIENTS_BY_ID.get(receipt["client_id"]) or {}).get("trade", "UNSPECIFIED")
            extraction_id = extraction["extraction_id"]
            categorisation = categorisation_engine.categorise(
                receipt_id=receipt_id,
                extraction_id=extraction_id,
                supplier_name=supplier,
                client_id=receipt["client_id"],
                business_type=trade,
                # extraction.get("gross_amount"), not the `gross` local above it:
                # that one is coerced to 0.0 for the sidecar, and 0.0 would tell
                # layer 5 the receipt was free. No line_items: this reads the
                # extraction back out of the database and they are not stored.
                gross_amount=extraction.get("gross_amount"),
            )
            # The suggested code has to be one the client's chart holds, whichever
            # layer produced it. Runs before the code reaches either the
            # categorisations row or the sidecar, both of which are below. See
            # resolve_against_chart() in worker/categorisation/fallback.py.
            categorisation = resolve_against_chart(categorisation, repo=repo)

            # Save categorisation
            cat_id = str(uuid.uuid4())
            repo.save_categorisation(
                categorisation_id=cat_id,
                receipt_id=receipt_id,
                extraction_id=extraction_id,
                client_id=receipt["client_id"],
                trade=categorisation.business_type,
                mapping_id=categorisation.mapping_id,
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
                client_id=receipt["client_id"],
                client_name=(config.CLIENTS_BY_ID.get(receipt["client_id"]) or {}).get("client_name", ""),
                capture_date=datetime.now(timezone.utc).isoformat(),
                invoice_date=invoice_date,
                supplier=supplier,
                net=extraction.get("net_amount"),
                vat=extraction.get("vat_amount"),
                gross=gross,
                currency=currency,
                category_code=categorisation.suggested_code,
                category_name=categorisation.suggested_name,
                confidence=categorisation.confidence,
                validation_status="ok",
                asserted=None,
                original_filename=receipt["filename"],
                claimed_client_id=None,
            )
            published = publish_receipt(
                repo, receipt_id, sidecar_payload, source_path,
                # An `ok` receipt has no notes and no duplicate, and the empty
                # list is stated rather than left out so every item carries the
                # key. extra_for() is the one builder, shared with the poll.
                extra=extra_for([]),
            )
            if not published:
                # publish_receipt() has already recorded why and logged it. The
                # receipt is untouched and the next poll offers it again.
                stats["recovery_failed"] = stats.get("recovery_failed", 0) + 1
                continue

            dest_path = copy_for_published_receipt(
                repo,
                receipt_id=receipt_id,
                client_id=receipt["client_id"],
                source_file=source_path,
                invoice_date=invoice_date,
                supplier=supplier,
                gross=gross,
                validation_status="ok",
                filed_path=receipt.get("filed_path"),
            )
            stats["recovery_published"] = stats.get("recovery_published", 0) + 1
            logger.info(
                f"receipt {receipt_id} recovered, categorised as "
                f"{categorisation.suggested_code}, and published"
                + (f"; copied to {dest_path}" if dest_path else ""))
        except Exception as exc:
            logger.error(f"failed to publish recovered receipt {receipt_id}: {exc}", exc_info=True)


def _copy_missing_client_copies(repo: Repository) -> None:
    """Retry the client folder copy for anything that published without one.

    **Claude Code's flag 6 of `2026-09-09_REPORT_claude_code_stage4_pipeline.md`,
    briefed once stage 4 was complete and 18.2b's freeze closed by amendment
    298.** `copy_for_published_receipt()` swallows its own failures, and the
    repointed sweep above asks "was this published", so a receipt whose publish
    succeeded and whose copy failed was never offered again. The document never
    reached the client folder and the only trace was an ERROR in `run.log`.

    **The trigger is asked here, above the query, and that is the deliverable
    rather than a detail.** On `never` and on `post` no receipt ever gets a
    `filed_path`, so the query would answer with every `ok` receipt in the
    database every five minutes. `copy_for_published_receipt()` would no-op on
    each, so nothing would be written; the cost would be a pointless query and a
    sweep line that means nothing.

    **It publishes nothing and categorises nothing.** Both already happened for
    every receipt it can see. Republishing would overwrite an item Desktop may
    have drained, and a second `categorisations` row for one receipt would be a
    duplicate nobody asked for. Held on the syntax tree by
    `tests/test_client_copy_retry.py`.

    **It takes no `stats` and that is deliberate.** `stats` goes into
    `runs.ndjson`, which is the run summary, and the brief says nothing goes
    into the run summary. Taking no parameter makes that structural rather than
    a thing to remember. What a reader sees instead is the line below and
    `copy_for_published_receipt()`'s own INFO line per receipt.
    """
    if config.CLIENT_COPY_TRIGGER != config.CLIENT_COPY_ON_PUBLISH:
        return

    waiting = repo.get_published_receipts_without_client_copy()
    if not waiting:
        return

    logger.info(
        f"retrying the client folder copy for {len(waiting)} published receipt(s) "
        f"that have none")
    for receipt in waiting:
        receipt_id = receipt["receipt_id"]
        try:
            extraction = repo.get_extraction_for_receipt(receipt_id)
            if not extraction:
                logger.warning(
                    f"receipt {receipt_id} published but has no extraction "
                    "record, so there is nothing to name the copy from")
                continue

            source_path = Path(receipt["file_path"])
            if not source_path.exists():
                logger.warning(
                    f"source file missing for receipt {receipt_id}: "
                    f"{source_path}, so its client folder copy cannot be made")
                continue

            # The same gated function every other route reaches. It holds the
            # trigger, the one-copy rule and the missing-folder-name refusal,
            # and it records filed_path itself when it writes.
            copy_for_published_receipt(
                repo,
                receipt_id=receipt_id,
                client_id=receipt["client_id"],
                source_file=source_path,
                invoice_date=(extraction.get("invoice_date")
                              or datetime.now(timezone.utc).date().isoformat()),
                supplier=extraction.get("supplier_name") or "unknown",
                gross=(extraction.get("gross_amount")
                       if extraction.get("gross_amount") is not None else 0.0),
                validation_status="ok",
                # The row's own value rather than None. The query guarantees it
                # is NULL, and passing the row means the one-copy gate still
                # holds if that query ever changes.
                filed_path=receipt["filed_path"],
            )
        except Exception as exc:
            # copy_for_published_receipt() swallows a failing copy already, so
            # reaching here means something above it went wrong. One receipt
            # must not take the poll down either way.
            logger.error(
                f"could not retry the client folder copy for {receipt_id}: "
                f"{exc}", exc_info=True)


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


# Windows constants for the two process queries below, named rather than inlined.
# PROCESS_QUERY_LIMITED_INFORMATION is granted more widely than
# PROCESS_QUERY_INFORMATION and is all GetProcessTimes and GetExitCodeProcess need.
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_ERROR_ACCESS_DENIED = 5
_ERROR_INVALID_PARAMETER = 87
_STILL_ACTIVE = 259
# FILETIME counts 100-nanosecond intervals from this instant, UTC.
_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)

_KERNEL32 = None


def _kernel32():
    """kernel32 with the three calls this module makes declared, loaded once.

    Declared rather than left to ctypes' defaults, and this is not tidiness.
    OpenProcess returns a HANDLE and ctypes' default restype is a signed int, so
    a handle above 2**31 comes back negative and is sign-extended when passed
    back to GetProcessTimes and CloseHandle, which would then be operating on a
    handle nobody holds. Handles are small in practice, which is exactly the kind
    of thing that works until it does not.

    Loaded lazily so that importing this module on a machine with no kernel32
    still works; every caller is behind a sys.platform check in any case.
    """
    global _KERNEL32
    if _KERNEL32 is None:
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = ctypes.wintypes.HANDLE
        k.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL,
                                  ctypes.wintypes.DWORD]
        k.GetExitCodeProcess.restype = ctypes.wintypes.BOOL
        k.GetExitCodeProcess.argtypes = [ctypes.wintypes.HANDLE,
                                         ctypes.POINTER(ctypes.wintypes.DWORD)]
        k.GetProcessTimes.restype = ctypes.wintypes.BOOL
        k.GetProcessTimes.argtypes = [ctypes.wintypes.HANDLE] + [
            ctypes.POINTER(ctypes.wintypes.FILETIME)] * 4
        k.CloseHandle.restype = ctypes.wintypes.BOOL
        k.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
        _KERNEL32 = k
    return _KERNEL32

# How far after the lock's own started_at a process may have been created and
# still be accepted as the process that wrote it. Zero would be correct on a
# clock that never moves: a process must exist before it can write a lock, so
# the genuine gap is negative. The allowance is for a clock adjustment between
# the two readings, and it is small because every second of it is a second in
# which Windows could have recycled the pid onto something unrelated.
_LOCK_START_TOLERANCE_SECONDS = 5.0


def _is_process_running(pid: int) -> bool:
    """Does a process with this pid exist right now.

    **os.kill(pid, 0) cannot answer this on Windows and used to be what answered
    it.** signal.CTRL_C_EVENT is 0, so os.kill(pid, 0) takes the console control
    event branch rather than the TerminateProcess branch: for a pid that is not
    reachable as a process group in the caller's own console it raises
    OSError [WinError 87], which the old body caught and reported as "not
    running". Every pipeline started from another window read as dead, so
    acquire_lock() refused nothing in 67 starts across five weeks. See
    2026-09-07_REPORT_claude_code_lock_out_of_onedrive.md sections 5 and 7.

    OpenProcess answers it. A pid that does not exist fails with
    ERROR_INVALID_PARAMETER; a process this account may not open fails with
    ERROR_ACCESS_DENIED, **which means the process exists** and must read as
    alive, per case F of 2026-09-06_REPORT_claude_code_lock_diagnostic.md. Any
    other failure is treated as existence too, because the cost of a wrong
    "alive" is a start that has to be unblocked by hand and the cost of a wrong
    "dead" is two pipelines against one WAL database.

    A handle can outlive its process, so an opened process is asked for its exit
    code as well.
    """
    if sys.platform != "win32":
        # POSIX, where os.kill(pid, 0) genuinely is an existence check. Kept for
        # the cloud build; unexercised on this machine.
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    kernel32 = _kernel32()
    handle = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        err = ctypes.get_last_error()
        if err == _ERROR_INVALID_PARAMETER:
            return False
        if err != _ERROR_ACCESS_DENIED:
            logger.warning(
                f"OpenProcess on pid {pid} failed with error {err}; treating the "
                "process as alive, which blocks a start rather than allowing two"
            )
        return True

    try:
        exit_code = ctypes.wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return True
        return exit_code.value == _STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def _process_started_at(pid: int):
    """When this process was created, as an aware UTC datetime, or None.

    None means the question could not be answered, not that the process is
    young: a process this account cannot open has no readable creation time, and
    on POSIX this returns None because nothing here needs it yet.

    This is what tells a live pipeline from a recycled pid. A pid on its own
    cannot: Windows reissues pids, a stale lock file is the normal state here
    because closing the console window does not run release_lock(), and a lock
    naming a pid that now belongs to something unrelated would otherwise refuse
    a start with no pipeline running at all.
    """
    if sys.platform != "win32":
        return None

    kernel32 = _kernel32()
    handle = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        creation = ctypes.wintypes.FILETIME()
        exited = ctypes.wintypes.FILETIME()
        kernel_time = ctypes.wintypes.FILETIME()
        user_time = ctypes.wintypes.FILETIME()
        ok = kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation),
            ctypes.byref(exited),
            ctypes.byref(kernel_time),
            ctypes.byref(user_time),
        )
        if not ok:
            return None
        ticks = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
        return _FILETIME_EPOCH + timedelta(microseconds=ticks // 10)
    finally:
        kernel32.CloseHandle(handle)


def _parse_lock(content: str):
    """The pid and the started_at string a lock file names, or None for either.

    A value outside the pid range comes back as None rather than reaching
    OpenProcess. os.kill raised OverflowError on 4294967295, which nothing
    caught, so a lock holding a number that large stopped the pipeline at
    startup with a traceback: case G of
    2026-09-06_REPORT_claude_code_lock_diagnostic.md, recorded there and not
    fixed at the time.
    """
    pid = None
    started_at = None
    for line in content.splitlines():
        if line.startswith("pid="):
            raw = line.split("=", 1)[1].strip()
            if raw.isdigit() and 0 < int(raw) <= 0xFFFFFFFF:
                pid = int(raw)
        elif line.startswith("started_at="):
            started_at = line.split("=", 1)[1].strip() or None
    return pid, started_at


def _lock_describes_process(lock_started_at, process_started_at) -> bool:
    """Is the live process at that pid the one this lock was written for.

    True when it cannot be told apart, and that is deliberate in both
    directions. An unrecorded or unparseable started_at, or a process whose
    creation time this account may not read, falls back to the pid being alive,
    which blocks a start. Blocking a start that did not need blocking leaves a
    file to delete; not blocking one leaves two pipelines writing one database.
    """
    if lock_started_at is None or process_started_at is None:
        return True
    try:
        recorded = datetime.fromisoformat(lock_started_at)
    except ValueError:
        return True
    if recorded.tzinfo is None:
        recorded = recorded.replace(tzinfo=timezone.utc)
    tolerance = timedelta(seconds=_LOCK_START_TOLERANCE_SECONDS)
    return process_started_at <= recorded + tolerance


def acquire_lock() -> bool:
    lock_path = config.PIPELINE_LOCKFILE
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists():
        # Why the lock was judged stale, so that the log distinguishes the four
        # ways it can happen. All four logged one sentence until 2026-09-07,
        # which is why the two-instance runs of 2026-09-06 cannot be
        # reconstructed from run.log.
        stale_reason = None
        try:
            content = lock_path.read_text(encoding="utf-8")
        except OSError as exc:
            content = None
            stale_reason = f"the lock file could not be read ({exc})"

        if content is not None:
            existing_pid, existing_started_at = _parse_lock(content)
            if existing_pid is None:
                stale_reason = "the lock file names no usable pid"
            elif not _is_process_running(existing_pid):
                stale_reason = f"pid {existing_pid} is not running"
            else:
                holder_started_at = _process_started_at(existing_pid)
                if _lock_describes_process(existing_started_at, holder_started_at):
                    logger.error(
                        f"Another pipeline process is already running: pid {existing_pid}, "
                        f"started at {existing_started_at or 'a time the lock did not record'}"
                    )
                    return False
                stale_reason = (
                    f"pid {existing_pid} is alive but was created at "
                    f"{holder_started_at.isoformat()}, so it is not the process this lock "
                    f"describes ({existing_started_at}); the pid has been reused"
                )

        logger.warning(f"Stale pipeline lock detected, removing: {stale_reason}")
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
    """Delete the lock only if it names this process.

    It deleted whatever was there until 2026-09-07, so one pipeline could unlock
    another: observed at 10:05:36 that day, when a second pipeline's stop removed
    a lock the first had created. Doing nothing is the right answer when the file
    names somebody else, because that somebody is still holding it.
    """
    lock_path = config.PIPELINE_LOCKFILE
    try:
        content = lock_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return
    except OSError as exc:
        logger.warning(f"Could not read the pipeline lock to release it: {exc}")
        return

    existing_pid, _ = _parse_lock(content)
    if existing_pid != os.getpid():
        logger.warning(
            f"Not releasing the pipeline lock: it names pid {existing_pid} and this "
            f"process is {os.getpid()}"
        )
        return

    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        logger.error(f"Unable to remove the pipeline lock: {exc}")


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
                    currency=config.DEFAULT_CURRENCY,
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
                firm_id=receipt['firm_id'],
                client_id=receipt['client_id'],
                source=receipt['source'],
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
                currency=config.DEFAULT_CURRENCY,
                raw_response=str(exc),
                validation_status="failed",
                validation_notes=[f"auto-retry extraction error: {exc}"],
                pipeline_version=pipeline_version,
                update_status=False,
            )
        finally:
            # Release the lock repo.acquire_receipt_lock() took at the top of
            # this iteration. Named rather than numbered: this comment said
            # "acquired at line 282" and the file had grown past it, so the
            # number pointed at unrelated code. Amendment 247.
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
        "notes_applied": 0,
        "notes_failed": 0,
    }

    try:
        # 10d.35. Before anything reads the registry. A client registered while
        # the pipeline runs used to be invisible to it until a restart, because
        # config read clients.json once at import and main() polls until the
        # process ends. A failed parse keeps what is already in memory and never
        # ends the poll; config.reload_clients_if_changed() carries that rule.
        config.reload_clients_if_changed()

        repo = Repository()
        extractor = get_extractor()
        engine = CategorisationEngine(repo=repo, enable_ai_fallback=False)

        # Part 0: the resolution back-feed, design document 12.3. Before the retry
        # pass, so a receipt a human resolved in IntelliBooks Desktop is never
        # re-extracted in the same cycle it was resolved. Reordering these two lines
        # costs an OpenAI call per resolved receipt and overwrites the decision.
        _consume_resolution_notes(repo, engine, stats)

        # Part 1: Auto-retry failed receipts with older pipeline_version
        _retry_failed_receipts(repo, extractor, engine, stats, run_id, pipeline_version)

        _publish_unpublished_receipts(repo, engine, stats)
        # Immediately after, so the two recovery clauses read together here and
        # in run.log. A receipt this poll publishes gets its copy in the clause
        # above; this one is for the copies that failed on an earlier poll.
        _copy_missing_client_copies(repo)

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
                client_id, firm_id, _client_folder = repo.resolve_client_info(email_from)

                # Check for unknown sender
                if client_id == config.UNKNOWN_CLIENT_ID:
                    logger.info(f"unknown sender: {email_from}")
                    stats["review_flags_issued"] = stats.get("review_flags_issued", 0) + 1

                    if not repo.has_alert_been_sent(message_id, "unknown_sender"):
                        recipient_email = email_from
                        if "<" in email_from and ">" in email_from:
                            recipient_email = email_from.split("<")[1].split(">")[0].strip()

                        firm_name = _mailbox_firm_name()
                        if send_unknown_sender_alert(recipient_email, firm_name):
                            repo.record_alert_sent(message_id, "unknown_sender", recipient_email, firm_name)

                    # This path wrote no event at all until 2026-09-08, so a stranger
                    # sending a photo from a share button left no trace where one
                    # attaching a file left a row. Same shape as the attachment
                    # path's: one per email, a null filename because there is no one
                    # image it is about, and a synthetic receipt id.
                    #
                    # UNATTRIBUTED is named here rather than passing `firm_id`, and
                    # the difference is not cosmetic: resolve_client_info() returns
                    # the DEFAULT_FIRM_ID constant when it cannot place the sender,
                    # so `firm_id` is FIRM001 on this branch and the event lands in
                    # a real firm's log. The attachment path never had that problem
                    # because it derives msg_firm_id, which folds the unresolved case
                    # into UNATTRIBUTED; this path derives no such thing. Amendment
                    # 128 created receipt_events_UNATTRIBUTED.ndjson for exactly this.
                    _log_receipt(str(uuid.uuid4()), message_id, None, "unknown_sender",
                                 firm_id=config.UNATTRIBUTED_FIRM_ID, run_id=run_id)
                    move_email_to_folder(uid, "INBOX.Unknown Sender")
                    continue

                # Process embedded images like normal attachments
                # One email can carry several, with different outcomes. The worst
                # wins, and _worst_outcome_folder() below is where that is decided.
                email_outcomes = []
                for embedded_img in embedded_images:
                    att_id = embedded_img["id"]
                    filename = embedded_img["name"]
                    stats["attachments_processed"] += 1

                    file_data = base64.b64decode(embedded_img.get("contentBytes", ""))
                    file_hash = compute_hash(file_data)

                    # Part 2A: Only block if genuinely filed (filed_path IS NOT NULL)
                    # 10f.18. Scoped to this client: another client's identical
                    # PDF is not a duplicate of this one.
                    # 10f.20. And only a FILED match is a duplicate, which is the
                    # guard the attachment and folder-intake paths already had.
                    # A hash matching a receipt that failed extraction and was
                    # never filed is the operator's second attempt rather than
                    # a duplicate, and this path used to swallow it. It cannot
                    # loop: mark_processed() runs for every image below and the
                    # email moves to INBOX.Processed Receipts afterwards.
                    existing = repo.find_by_hash(file_hash, client_id)
                    if existing and repo.is_recorded_and_filed(existing):
                        logger.info(f"hash duplicate of {existing}, skipping embedded image {filename}")
                        stats["duplicates_skipped"] += 1
                        repo.mark_processed(message_id, att_id, file_hash, existing, firm_id)
                        # 10f.33. Recorded rather than moved on. It used to move
                        # the email the moment it decided, so a duplicate won by
                        # arriving first; `duplicate` now ranks below `ok`,
                        # because an email holding one duplicate and one filed
                        # receipt has both accounted for.
                        email_outcomes.append("duplicate")
                        continue

                    receipt_id = str(uuid.uuid4())
                    file_path = save_file(receipt_id, client_id, filename, file_data)
                    stats["receipts_created"] += 1

                    repo.save_receipt(
                        receipt_id=receipt_id,
                        message_id=message_id,
                        email_subject=email_msg.get("subject", ""),
                        email_from=email_from,
                        email_received_at=_iso_utc(email_msg.get("receivedDateTime")),
                        filename=filename,
                        file_path=file_path,
                        file_hash=file_hash,
                        firm_id=firm_id,
                        client_id=client_id,
                        source=EMAIL_SOURCE,
                    )
                    _log_receipt(receipt_id, message_id, filename, "created", firm_id=firm_id, client_id=client_id, run_id=run_id)

                    # Extract and process
                    try:
                        # The same transient-error retry the other three
                        # paths use. This was a bare extractor.extract()
                        # until 2026-09-08, so a transient OpenAI error on
                        # an emailed photo failed at the first attempt
                        # where the identical error on an attachment was
                        # retried with backoff.
                        extraction = extract_with_transient_retry(
                            extractor, file_path, filename)

                        # Sub-step 10f.32. Through the shared pipeline, like the
                        # other three intake paths: validate, duplicate-check,
                        # categorise, file.
                        #
                        # This loop used to validate and save an extraction for
                        # itself and stop there, so a receipt arriving as a photo
                        # in an email body was written to the database as `ok`
                        # with filed_path NULL: never categorised, never copied
                        # into the client folder, never seen by IntelliBooks, and
                        # reported nowhere. Amendment 269.
                        #
                        # Nothing here is new behaviour. Everything the call adds
                        # is what the other three paths already do, including
                        # filing a review item into Intellibills\Review\ and
                        # sending an unresolved client there rather than filing
                        # into a guessed folder, per 10d.18.
                        status, _filed_path = process_extraction_result(
                            receipt_id=receipt_id,
                            extraction=extraction,
                            file_path=file_path,
                            filename=filename,
                            firm_id=firm_id,
                            client_id=client_id,
                            source=EMAIL_SOURCE,
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

                        # Amendment 268's ranked move reads this list. The status
                        # is the shared function's answer now rather than one this
                        # path worked out for itself, which is the point: there
                        # was no reason for two answers to the same question.
                        email_outcomes.append(status)
                    except Exception as exc:
                        logger.error(f"extraction failed {receipt_id[:8]}... [{filename}]: {exc}", exc_info=True)
                        stats["extraction_failures"] += 1
                        # The same word the row below records, and the same folder
                        # the attachment path sends a raised extraction to.
                        email_outcomes.append("failed")
                        repo.save_extraction(
                            extraction_id=str(uuid.uuid4()),
                            receipt_id=receipt_id,
                            # extractor.name, not a hardcoded string: this row
                            # would otherwise say OpenAI produced a failure that
                            # a different provider produced. Design document 3.8.
                            engine=extractor.name,
                            supplier_name=None,
                            invoice_date=None,
                            net_amount=None,
                            vat_amount=None,
                            gross_amount=None,
                            currency=config.DEFAULT_CURRENCY,
                            raw_response=str(exc),
                            validation_status="failed",
                            validation_notes=[f"extraction error: {exc}"],
                            pipeline_version=pipeline_version,  # design document 3.12
                        )
                        _log_receipt(
                            receipt_id, message_id, filename, "extraction_failed",
                            firm_id=firm_id,
                            extraction_status="failed",
                            review_reason=str(exc),
                            run_id=run_id
                        )

                    repo.mark_processed(message_id, att_id, file_hash, receipt_id, firm_id)

                # Route the email on the worst outcome across its images, the way
                # the attachment path routes on its one outcome. This line used to
                # be an unconditional move to INBOX.Processed Receipts with a
                # comment claiming "if all ok", so an extraction that raised, one
                # that validated as failed and one that needs a person all
                # reported themselves in the mailbox as processed. Nothing was
                # lost, because the receipt row and its validation_status are
                # written either way; what was wrong is the one place Paul looks
                # to see what became of each email.
                #
                # None means do not move: either every image was a duplicate, in
                # which case the duplicate branch has already put the email in
                # INBOX.Duplicates, or the outcome is one the table does not name.
                outcome_folder = _worst_outcome_folder(email_outcomes)
                if outcome_folder:
                    move_email_to_folder(uid, outcome_folder)
                continue

            # No attachments and no embedded images - send alert
            # Skip if we've already sent an alert for this email
            if repo.has_alert_been_sent(message_id, "no_attachment"):
                logger.info(f"alert already sent for {message_id}, skipping")
                continue

            # Resolve sender to firm
            client_id, firm_id, _client_folder = repo.resolve_client_info(email_from)

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

        messages = fetch_new_messages()
        stats["messages_found"] = len(messages)
        logger.info(f"messages with attachments: {len(messages)}")

        for intake in intake_records:
            if intake.is_statement:
                # Amendment 1 to the step 10f duplicates brief. Scoped to this
                # client, and UNKNOWN where the sidecar names none, which is the
                # same recorded conclusion the receipt path reaches at 10d.16.
                # No statement row is ever written under UNKNOWN, because the
                # branch below routes an unresolvable client to Review before
                # save_statement(), so an unresolved statement now goes to Review
                # rather than being taken for some other client's duplicate.
                statement_client_id = intake.client_id or config.UNKNOWN_CLIENT_ID
                if repo.find_statement_by_hash(intake.file_hash, statement_client_id):
                    logger.info(
                        f"capture duplicate statement by hash, moving inbox pair to "
                        f"{INBOX_PROCESSED_DIRNAME}: {intake.filename}")
                    # 10f.21. Kept rather than deleted.
                    _move_inbox_pair_to_processed(intake)
                    stats["duplicates_skipped"] += 1
                    stats["inbox_duplicates_removed"] = stats.get("inbox_duplicates_removed", 0) + 1
                    continue

                statement_folder_name = _client_folder_name(intake.client_id)
                if not statement_folder_name:
                    # 10d.11 and 10d.18. No sidecar, or a client the registry does
                    # not hold, means no client, so nothing is filed into Clients.
                    logger.warning(f"statement with no resolvable client, routing to review: {intake.filename}")
                    file_review(intake.source_path, _review_key(intake.client_id), intake.filename,
                                "unresolved_client", ["no client_id could be resolved for this file"],
                                intake.sidecar or {})
                    stats["review_flags_issued"] += 1
                    continue

                if not intake.statement_metadata.get("platform") or not intake.statement_metadata.get("week_ending"):
                    logger.warning(f"statement missing metadata, routing to review: {intake.filename}")
                    file_review(intake.source_path, _review_key(intake.client_id), intake.filename, "missing_statement_metadata", ["missing platform or week_ending"], intake.sidecar or {})
                    stats["review_flags_issued"] += 1
                    continue

                statement_id = str(uuid.uuid4())
                tax_year = determine_tax_year(intake.statement_metadata["week_ending"])
                # 10d.55, Paul's decision of 2026-09-02. The statement gets its own
                # copy in the document store BEFORE it is filed, the way the receipt
                # branch below already does. Until now this branch never called into
                # worker/storage/store.py at all, so the copy in the client folder was
                # the only copy and a statement could not be reconstructed where a
                # receipt could.
                store_path = save_inbox_file(statement_id, intake.client_id, intake.source_path)
                # One path back, and no sidecar payload. Paul's decision of
                # 2026-09-10: the copy in the client folder is the document
                # alone, per 18.2b, so the dict that used to be built here
                # existed only to be written into a file nothing read.
                # `sidecar_path` was unpacked at this one call site and never
                # used. See `file_statement()`.
                dest_path = file_statement(
                    intake.source_path,
                    statement_folder_name,
                    tax_year,
                    intake.statement_metadata["platform"],
                    intake.statement_metadata["week_ending"],
                    intake.source_path.suffix,
                )
                repo.save_statement(
                    statement_id=statement_id,
                    client_id=intake.client_id,
                    platform=intake.statement_metadata["platform"],
                    week_ending=intake.statement_metadata["week_ending"],
                    source=intake.source,
                    file_hash=intake.file_hash,
                    # 10d.56. file_path is the document store copy and filed_path is
                    # the client folder copy, which is what both names mean on
                    # `receipts`. file_path used to hold the client folder path.
                    file_path=store_path,
                    filed_path=dest_path,
                )
                logger.info(f"statement filed: {statement_id} {dest_path}")
                stats["receipts_created"] += 1
                continue

            # 10d.16 and 10d.18. An unresolved client is a recorded conclusion,
            # not a fallback. Worked out here rather than after the hash check,
            # because 10f.18 scopes that check to the client and it has to be the
            # same client the receipt row will name.
            receipt_client_id = intake.client_id or config.UNKNOWN_CLIENT_ID
            receipt_firm_id = intake.firm_id or config.UNATTRIBUTED_FIRM_ID

            # Part 2A: Only block if genuinely filed (filed_path IS NOT NULL)
            existing = repo.find_by_hash(intake.file_hash, receipt_client_id)
            if existing:
                if repo.is_recorded_and_filed(existing):
                    logger.info(
                        f"capture duplicate by hash of filed receipt, moving inbox pair "
                        f"to {INBOX_PROCESSED_DIRNAME}: {intake.filename}")
                    # 10f.21. Kept rather than deleted.
                    _move_inbox_pair_to_processed(intake)
                    stats["duplicates_skipped"] += 1
                    stats["inbox_duplicates_removed"] = stats.get("inbox_duplicates_removed", 0) + 1
                    continue
                # If hash matches a failed/needs_review receipt, allow reprocessing
                logger.info(f"capture duplicate by hash of failed receipt, allowing reprocessing {intake.filename}")
                # Continue processing (don't skip)

            receipt_id = str(uuid.uuid4())
            # receipt_client_id and receipt_firm_id are computed above the hash
            # check. The row is written with UNKNOWN rather than guessing, and
            # UNATTRIBUTED is the firm, because there is no client to take a firm
            # from and DEFAULT_FIRM_ID stopped being that answer at 10d.19.
            file_path = save_inbox_file(receipt_id, receipt_client_id, intake.source_path)
            stats["receipts_created"] += 1

            repo.save_receipt(
                receipt_id=receipt_id,
                message_id=f"{intake.source}:{intake.original_name}",
                email_subject=None,
                email_from=None,
                # 10d.27. One format, ISO 8601 UTC. This used to pass an integer
                # mtime into the same column the email path fills with a string.
                email_received_at=_iso_utc_from_mtime(intake.source_path),
                filename=intake.filename,
                file_path=file_path,
                file_hash=intake.file_hash,
                firm_id=receipt_firm_id,
                client_id=receipt_client_id,
                source=intake.source,
            )
            _log_receipt(receipt_id, f"{intake.source}:{intake.original_name}", intake.filename, "created", firm_id=receipt_firm_id, client_id=receipt_client_id, run_id=run_id)

            # Build sidecar assertion values (folder-specific)
            asserted_values = None
            if intake.sidecar:
                asserted = {k: intake.sidecar.get(k) for k in ("supplier_name", "invoice_date", "net_amount", "vat_amount", "gross_amount", "client_id") if k in intake.sidecar}
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
                    firm_id=receipt_firm_id,
                    client_id=receipt_client_id,
                    source=intake.source,
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

            except Exception as exc:
                logger.error(f"capture extraction failed {receipt_id[:8]}... [{intake.filename}]: {exc}", exc_info=True)
                stats["extraction_failures"] += 1
                repo.save_extraction(
                    extraction_id=str(uuid.uuid4()),
                    receipt_id=receipt_id,
                    engine=extractor.name,  # design document 3.8
                    supplier_name=None,
                    invoice_date=None,
                    net_amount=None,
                    vat_amount=None,
                    gross_amount=None,
                    currency=config.DEFAULT_CURRENCY,
                    raw_response=str(exc),
                    validation_status="failed",
                    validation_notes=[f"extraction error: {exc}"],
                    pipeline_version=pipeline_version,
                )
                file_review(
                    intake.source_path,
                    _review_key(receipt_client_id),
                    intake.filename,
                    "failed",
                    [str(exc)],
                    {
                        "receipt_id": receipt_id,
                        "source": intake.source,
                        "client_id": receipt_client_id,
                        "client_name": (config.CLIENTS_BY_ID.get(receipt_client_id) or {}).get("client_name", ""),
                        "original_filename": intake.filename,
                        "error": str(exc),
                    },
                )
                _log_receipt(
                    receipt_id, f"{intake.source}:{intake.original_name}", intake.filename, "extraction_failed",
                    firm_id=receipt_firm_id,
                    extraction_status="failed",
                    review_reason=str(exc),
                    run_id=run_id
                )

            finally:
                # Every outcome, per design document 3.13, and last: the failure
                # branch above copies the original into the Review folder, so the
                # move has to happen after it, and a `finally` is the only place
                # that covers both branches without repeating the call.
                _move_inbox_pair_to_processed(intake)

        for msg in messages:
            message_id = msg["id"]
            uid = msg["uid"]
            subject = msg.get("subject", "")
            email_from = msg.get("from", {}).get("emailAddress", {}).get("address", "")
            received_at = msg.get("receivedDateTime", "")

            # 10d.19. Resolved once per message rather than once per attachment.
            # It was inside the loop below, so a message with four attachments
            # resolved the same sender four times and could in principle have
            # resolved it differently each time if the registry were re-read
            # between attachments, which 10d.35 now makes possible.
            client_id, firm_id, _client_folder = repo.resolve_client_info(email_from)

            # The firm to log an event against when the event is about the
            # message rather than about a receipt: an unsupported attachment, a
            # duplicate skipped before anything was written. UNATTRIBUTED where
            # the sender is not a client, because DEFAULT_FIRM_ID stopped being
            # the answer to an unattributable event at 10d.19.
            msg_firm_id = firm_id if client_id != config.UNKNOWN_CLIENT_ID else config.UNATTRIBUTED_FIRM_ID

            # Sub-step 10f.35. Whose email this is, is a question about the email
            # rather than about an attachment, and resolve_client_info() has just
            # answered it. This check sat INSIDE the loop below until 2026-09-08,
            # beneath is_supported() and the two duplicate checks, each of which
            # `continue`s: so a stranger who sent only an unsupported file was
            # never reached by it and heard nothing at all, while their email was
            # filed as a format problem. The registration alert is the only thing
            # an unregistered sender ever gets back.
            #
            # The embedded-image path above already had it here, so this makes
            # the two agree rather than moving both. Amendment 274.
            if client_id == config.UNKNOWN_CLIENT_ID:
                logger.info(f"unknown sender: {email_from}")
                stats["review_flags_issued"] = stats.get("review_flags_issued", 0) + 1

                # One alert per email, whatever it carried.
                if not repo.has_alert_been_sent(message_id, "unknown_sender"):
                    # Extract email address (handle "Name <email>" format)
                    recipient_email = email_from
                    if "<" in email_from and ">" in email_from:
                        recipient_email = email_from.split("<")[1].split(">")[0].strip()

                    firm_name = _mailbox_firm_name()
                    if send_unknown_sender_alert(recipient_email, firm_name):
                        repo.record_alert_sent(message_id, "unknown_sender", recipient_email, firm_name)

                # One event for the email, with no filename, because there is no
                # one attachment this is about. The key is written as null rather
                # than omitted, and the receipt id is synthetic, which is the
                # shape the other two message-level events already use:
                # unsupported_file_type and duplicate_skipped both pass a fresh
                # uuid because no receipt exists for them either.
                _log_receipt(str(uuid.uuid4()), message_id, None, "unknown_sender",
                             firm_id=config.UNATTRIBUTED_FIRM_ID, run_id=run_id)
                move_email_to_folder(uid, "INBOX.Unknown Sender")
                continue

            # Sub-step 10f.33. One email, one outcome, decided after the loop
            # by the same ranking the embedded-image path uses. This loop used to
            # move the email from inside itself, and move_email_to_folder()
            # expunges, so the FIRST attachment's outcome won while the embedded
            # path's worst one did.
            email_outcomes = []

            for att in fetch_attachments(message_id, msg.get("msg")):
                att_id = att["id"]
                filename = att.get("name", "unknown")
                stats["attachments_processed"] += 1

                if not is_supported(filename):
                    logger.info(f"skip unsupported: {filename}")
                    _log_receipt(
                        str(uuid.uuid4()), message_id, filename, "unsupported_file_type",
                        firm_id=msg_firm_id, run_id=run_id
                    )
                    email_outcomes.append("unsupported")
                    continue

                if repo.is_duplicate(message_id, att_id):
                    logger.info(f"skip duplicate: {message_id}/{att_id}")
                    stats["duplicates_skipped"] += 1
                    _log_receipt(
                        str(uuid.uuid4()), message_id, filename, "duplicate_skipped",
                        firm_id=msg_firm_id, duplicate_reason="message_id_match",
                        run_id=run_id
                    )
                    email_outcomes.append("duplicate")
                    continue

                file_data = base64.b64decode(att.get("contentBytes", ""))
                file_hash = compute_hash(file_data)

                # Part 2A: Only block if genuinely filed (filed_path IS NOT NULL)
                # 10f.18. Scoped to this client.
                existing = repo.find_by_hash(file_hash, client_id)
                if existing and repo.is_recorded_and_filed(existing):
                    logger.warning(f"hash duplicate of {existing}, skipping {filename}")
                    stats["duplicates_skipped"] += 1
                    _log_receipt(
                        str(uuid.uuid4()), message_id, filename, "duplicate_skipped",
                        firm_id=msg_firm_id, duplicate_of=existing,
                        duplicate_reason="file_hash_match",
                        run_id=run_id
                    )
                    repo.mark_processed(message_id, att_id, file_hash, existing, msg_firm_id)
                    email_outcomes.append("duplicate")
                    continue
                # If file_hash matches a failed/needs_review receipt, allow reprocessing

                receipt_id = str(uuid.uuid4())

                file_path = save_file(receipt_id, client_id, filename, file_data)
                stats["receipts_created"] += 1

                repo.save_receipt(
                    receipt_id=receipt_id,
                    message_id=message_id,
                    email_subject=subject,
                    email_from=email_from,
                    email_received_at=_iso_utc(received_at),
                    filename=filename,
                    file_path=file_path,
                    file_hash=file_hash,
                    firm_id=firm_id,
                    client_id=client_id,
                    source=EMAIL_SOURCE,
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
                        firm_id=firm_id,
                        client_id=client_id,
                        source=EMAIL_SOURCE,
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

                    # 10f.33. Recorded rather than acted on, and ranked after
                    # the loop. This was a four-branch move inside the loop.
                    email_outcomes.append(status)

                except Exception as exc:
                    logger.error(f"extraction failed {receipt_id[:8]}... [{filename}]: {exc}", exc_info=True)
                    stats["extraction_failures"] += 1
                    repo.save_extraction(
                        extraction_id=str(uuid.uuid4()),
                        receipt_id=receipt_id,
                        engine=extractor.name,  # design document 3.8
                        supplier_name=None,
                        invoice_date=None,
                        net_amount=None,
                        vat_amount=None,
                        gross_amount=None,
                        currency=config.DEFAULT_CURRENCY,
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
                    email_outcomes.append("failed")
                    # Mark processed even on failure (extraction error)
                    repo.mark_processed(message_id, att_id, file_hash, receipt_id, firm_id)

            # 10f.33. One move for the email, on the worst outcome across its
            # attachments. None means nothing to rank, which on this path is an
            # unknown sender: that branch is deliberately unranked and moves the
            # email itself, because resolve_client_info() runs once per message
            # so every attachment reaches the same answer.
            outcome_folder = _worst_outcome_folder(email_outcomes)
            if outcome_folder:
                move_email_to_folder(uid, outcome_folder)

    except Exception as exc:
        errors = exc
        logger.error(f"process_once failed: {exc}", exc_info=True)
        raise
    finally:
        # processed_today means today, not this run. stats["receipts_created"]
        # counts what this five-minute poll happened to create, which is not
        # what the field is called or what IntelliBooks shows.
        processed_today = repo.count_processed_today() if repo is not None else 0
        review_count = _count_review_items(repo)
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
    attach_run_log_handler()
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

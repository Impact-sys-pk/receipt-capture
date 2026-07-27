"""Resolution service: the one implementation all four callers go through.

Design document sections 3.2, 3.3, 4.1, 4.2 and 4.3.

This module must not import Flask, argparse, anything under `worker/email/`, or
anything that prints or reads input. That is what makes it reusable by the CLI,
the console form, the resolution back-feed and a cloud API later, and three
independent implementations of resolution is what caused the divergence this
design exists to fix.

`apply_resolution_note`, the back-feed entry point, is step 10.
"""

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import config
from worker.extraction.base import ExtractionResult
from worker.filing import (
    determine_tax_year,
    file_receipt,
    make_enriched_sidecar,
    remove_review_pair,
)
from worker.validation.rules import validate

logger = logging.getLogger(__name__)

CORRECTABLE_FIELDS = (
    "supplier_name", "invoice_date", "net_amount",
    "vat_amount", "gross_amount", "receipt_ref_number", "receipt_time",
)

AMOUNT_FIELDS = ("net_amount", "vat_amount", "gross_amount")

# Plain decimal only. No thousands separators, no currency symbols, no more
# than two decimal places. Rejecting is deliberate: stripping a "£" or a comma
# would be guessing at an operator's intent on a financial figure.
_AMOUNT_RE = re.compile(r"^-?(\d+(\.\d{1,2})?|\.\d{1,2})$")

# YYYY-MM-DD, zero-padded. strptime alone accepts "2026-7-5", which we do not.
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class ResolutionView:
    """Everything needed to render a receipt for correction. Read-only.

    The console's detail page and the CLI both render this, so the two cannot
    drift into showing different things.
    """
    receipt: Dict[str, Any]
    extraction: Optional[Dict[str, Any]]        # latest, the one being corrected
    extraction_history: List[Dict[str, Any]]    # all, newest first
    categorisation: Optional[Dict[str, Any]]    # may be None; the non-ok path saves none
    resolution_events: List[Dict[str, Any]]
    duplicate_of_receipt: Optional[Dict[str, Any]]      # when status == 'possible_duplicate'
    duplicate_of_extraction: Optional[Dict[str, Any]]
    client_name: str
    business_type: str
    gl_code_options: List[Dict[str, Any]]
    effective_gl_code: Optional[str]            # correction_code if set, else suggested_code
    file_path: str
    is_locked: bool                             # informational only


@dataclass
class Corrections:
    values: Dict[str, Any] = field(default_factory=dict)  # only fields explicitly supplied
    gl_nominal_code: Optional[str] = None
    gl_account_name: Optional[str] = None
    gl_correction_reason: Optional[str] = None
    remember_gl_for_supplier: bool = False


@dataclass
class ResolutionOutcome:
    outcome: str    # filed | discarded | still_invalid | stale | locked | not_found | error
    receipt_id: str
    extraction_id: Optional[str] = None
    filed_path: Optional[str] = None
    category_code: Optional[str] = None
    category_name: Optional[str] = None
    category_confidence: Optional[str] = None
    validation_notes: List[str] = field(default_factory=list)
    message: str = ""               # safe to show an operator
    error_detail: Optional[str] = None  # logs only, never rendered


def parse_corrections(raw: dict) -> Tuple[Corrections, Dict[str, str]]:
    """Normalise operator input. Returns (corrections, field_errors). Never raises.

    Key presence, never truthiness:

    - A key absent from `raw`, or `None`, is omitted from `values`.
    - An empty (or whitespace-only) string means "clear this field", recorded as
      `None`. Distinct from omission, so an operator can remove a wrongly
      extracted reference number.
    - Amounts coerce to float. `"0"` and `"0.00"` are valid and become `0.0`.
    - `invoice_date` must be YYYY-MM-DD and a real calendar date. Other formats
      are a field error, not something to reparse: guessing here would undo the
      day-first handling in `openai_vision.py`.
    - Bad input becomes a field error keyed by field name. Nothing raises.

    Keys outside CORRECTABLE_FIELDS are ignored, so a web form's own fields
    (CSRF token, buttons) can be passed straight through.
    """
    values: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    if not isinstance(raw, dict):
        return Corrections(values=values), {"_form": "corrections must be a mapping of field names to values"}

    for name in CORRECTABLE_FIELDS:
        if name not in raw:
            continue

        supplied = raw[name]
        if supplied is None:
            continue

        if isinstance(supplied, str):
            text = supplied.strip()
            if text == "":
                values[name] = None  # explicit clear
                continue
        elif name in AMOUNT_FIELDS and isinstance(supplied, (int, float)) and not isinstance(supplied, bool):
            # Already typed, e.g. argparse's type=float. 0.0 must survive.
            values[name] = float(supplied)
            continue
        else:
            errors[name] = f"expected text, got {type(supplied).__name__}"
            continue

        if name in AMOUNT_FIELDS:
            if not _AMOUNT_RE.match(text):
                errors[name] = (
                    f"'{supplied}' is not a plain amount. Use digits and at most two "
                    "decimal places, with no currency symbol and no thousands separator."
                )
                continue
            values[name] = float(text)
        elif name == "invoice_date":
            if not _ISO_DATE_RE.match(text):
                errors[name] = f"'{supplied}' is not a date in YYYY-MM-DD form."
                continue
            try:
                datetime.strptime(text, "%Y-%m-%d")
            except ValueError:
                errors[name] = f"'{supplied}' is not a real calendar date."
                continue
            values[name] = text
        else:
            values[name] = text

    return Corrections(values=values), errors


def _client_details(client_code: Optional[str]) -> Tuple[str, str]:
    """Client name and business type for a client code, with the documented defaults."""
    entry = config.CLIENTS_BY_CODE.get(client_code or "", {})
    return (
        entry.get("client_name", client_code or "UNKNOWN"),
        entry.get("business_type", "UNSPECIFIED"),
    )


def get_resolution_view(repo, receipt_id) -> Optional[ResolutionView]:
    """Read-only. Takes no lock. None if the receipt does not exist.

    Deliberately does not decide policy. A receipt with no extraction still gets a
    view, with `extraction` as None; whether that is `not_found` is
    `resolve_receipt()`'s judgement, and the console needs to render the receipt
    either way.
    """
    receipt = repo.get_receipt(receipt_id)
    if not receipt:
        return None

    history = repo.get_extractions_for_receipt(receipt_id)
    latest = history[0] if history else None
    categorisation = repo.get_categorisation_for_receipt(receipt_id)

    effective_gl_code = None
    if categorisation:
        effective_gl_code = (
            categorisation.get("correction_code") or categorisation.get("suggested_code")
        )

    duplicate_of_receipt = None
    duplicate_of_extraction = None
    duplicate_of = receipt.get("duplicate_of")
    if duplicate_of:
        duplicate_of_receipt = repo.get_receipt(duplicate_of)
        if duplicate_of_receipt:
            duplicate_of_extraction = repo.get_extraction_for_receipt(duplicate_of)

    client_name, business_type = _client_details(receipt.get("client_code"))

    return ResolutionView(
        receipt=receipt,
        extraction=latest,
        extraction_history=history,
        categorisation=categorisation,
        resolution_events=repo.list_resolution_events(receipt_id),
        duplicate_of_receipt=duplicate_of_receipt,
        duplicate_of_extraction=duplicate_of_extraction,
        client_name=client_name,
        business_type=business_type,
        # Fallback per 11.1 until the Default CoA is loaded at step 12. The
        # console shows a banner saying the CoA has not been loaded.
        gl_code_options=repo.list_gl_code_options_from_vendors(),
        effective_gl_code=effective_gl_code,
        file_path=receipt.get("file_path"),
        is_locked=receipt.get("locked_at") is not None,
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_event(repo, receipt_id, actor, source, action, outcome,
                  extraction_id=None, corrections=None, gl_override_code=None) -> None:
    """One audit row per resolution.

    Written for filed, discarded and still_invalid only. Not for not_found, stale
    or locked, because nothing happened. Not for error either: the state is
    unknown at that point and a second write risks compounding it, so the logged
    traceback is the record. See the 2026-07-27 amendment to 4.2.
    """
    corrections_json = None
    if corrections is not None and corrections.values:
        corrections_json = json.dumps(corrections.values, sort_keys=True, default=str)
    repo.save_resolution_event(
        event_id=str(uuid.uuid4()),
        receipt_id=receipt_id,
        extraction_id=extraction_id,
        actor=actor,
        source=source,
        action=action,
        outcome=outcome,
        created_at=_now(),
        corrections_json=corrections_json,
        gl_override_code=gl_override_code,
    )


def _override(value: Optional[str]) -> Optional[str]:
    """Treat an empty or whitespace-only GL field as no override at all."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _merge_corrections(extraction: Dict[str, Any], corrections: Corrections) -> Dict[str, Any]:
    """Step 5. Merge over the existing extraction by key presence, not truthiness.

    A supplied 0.0 is falsy, so an `or` here would keep the wrong extracted value
    and make correcting VAT to zero impossible. That was design document 3.2.
    """
    merged = {name: extraction.get(name) for name in CORRECTABLE_FIELDS}
    merged.update(corrections.values)
    merged["currency"] = extraction.get("currency") or "GBP"
    return merged


def resolve_receipt(repo, categorisation_engine, receipt_id, corrections,
                    actor, source, expected_extraction_id=None) -> ResolutionOutcome:
    """Apply corrections, re-validate, categorise, file. Append-only throughout.

    Design document 4.3. The step numbers in the comments below are that section's,
    and steps 7 and 8 must not be reordered: categorisations.extraction_id has a
    foreign key to extractions, and getting it backwards caused the live
    IntegrityError fixed in b480a7e.

    actor is who did it; source is which tool they used, 'console' | 'cli' |
    'desktop'. Both are required: a default would be wrong for three of the four
    callers and the point of the column is that nobody has to guess.
    """
    # 1. Load receipt.
    receipt = repo.get_receipt(receipt_id)
    if not receipt:
        return ResolutionOutcome(
            outcome="not_found", receipt_id=receipt_id,
            message=f"Receipt not found: {receipt_id}",
        )

    # 2. Load latest extraction.
    extraction = repo.get_extraction_for_receipt(receipt_id)
    if not extraction:
        return ResolutionOutcome(
            outcome="not_found", receipt_id=receipt_id,
            message="This receipt has no extraction to correct.",
        )

    # 3. Optimistic concurrency. Someone else has resolved it since this view was
    #    rendered, so write nothing and let the caller reload.
    if expected_extraction_id is not None and extraction["extraction_id"] != expected_extraction_id:
        return ResolutionOutcome(
            outcome="stale", receipt_id=receipt_id,
            extraction_id=extraction["extraction_id"],
            message=(
                "This receipt changed while you were working on it. "
                "Reload and check the current values before saving again."
            ),
        )

    # 4. Acquire the lock. Everything below is in try/finally releasing it.
    if not repo.acquire_receipt_lock(receipt_id):
        return ResolutionOutcome(
            outcome="locked", receipt_id=receipt_id,
            message="Another process is working on this receipt. Try again in a moment.",
        )

    try:
        # 5. Merge by key presence.
        merged = _merge_corrections(extraction, corrections)

        # 6. Re-validate. Still invalid: append a row recording the attempt and
        #    stop. Deliberately not add_validation_note(), which mutates an
        #    existing row in a table CLAUDE.md says is never modified.
        candidate = ExtractionResult(
            engine="manual_correction",
            supplier_name=merged["supplier_name"],
            invoice_date=merged["invoice_date"],
            net_amount=merged["net_amount"],
            vat_amount=merged["vat_amount"],
            gross_amount=merged["gross_amount"],
            currency=merged["currency"],
            raw_response=json.dumps(merged, sort_keys=True, default=str),
            receipt_ref_number=merged["receipt_ref_number"],
            receipt_time=merged["receipt_time"],
        )
        validation = validate(candidate)
        pipeline_version = config.get_pipeline_version()

        if validation.status != "ok":
            attempt_id = str(uuid.uuid4())
            repo.save_extraction(
                extraction_id=attempt_id,
                receipt_id=receipt_id,
                engine="manual_correction",
                supplier_name=merged["supplier_name"],
                invoice_date=merged["invoice_date"],
                net_amount=merged["net_amount"],
                vat_amount=merged["vat_amount"],
                gross_amount=merged["gross_amount"],
                currency=merged["currency"],
                raw_response=candidate.raw_response,
                validation_status=validation.status,
                validation_notes=validation.notes,
                receipt_ref_number=merged["receipt_ref_number"],
                receipt_time=merged["receipt_time"],
                pipeline_version=pipeline_version,
            )
            _record_event(
                repo, receipt_id, actor, source, "resolve", "still_invalid",
                extraction_id=attempt_id, corrections=corrections,
                gl_override_code=_override(corrections.gl_nominal_code),
            )
            logger.info(
                f"resolution of {receipt_id} by {actor} via {source} still invalid: {validation.notes}"
            )
            return ResolutionOutcome(
                outcome="still_invalid", receipt_id=receipt_id, extraction_id=attempt_id,
                validation_notes=list(validation.notes),
                message="Still not valid after the correction: " + ", ".join(validation.notes),
            )

        # 7. Save the extraction row FIRST. categorisations.extraction_id has an
        #    FK to it. Do not reorder with step 8.
        extraction_id = str(uuid.uuid4())
        repo.save_extraction(
            extraction_id=extraction_id,
            receipt_id=receipt_id,
            engine="manual_correction",
            supplier_name=merged["supplier_name"],
            invoice_date=merged["invoice_date"],
            net_amount=merged["net_amount"],
            vat_amount=merged["vat_amount"],
            gross_amount=merged["gross_amount"],
            currency=merged["currency"],
            raw_response=candidate.raw_response,
            validation_status="ok",
            validation_notes=["manually corrected and filed"],
            receipt_ref_number=merged["receipt_ref_number"],
            receipt_time=merged["receipt_time"],
            pipeline_version=pipeline_version,
        )

        # 8. Categorise, then save the engine's suggestion. Never overwrite
        #    suggested_code with the operator's value: that is the audit trail.
        client_name, business_type = _client_details(receipt.get("client_code"))
        categorisation = categorisation_engine.categorise(
            receipt_id=receipt_id,
            extraction_id=extraction_id,
            supplier_name=merged["supplier_name"],
            client_id=receipt["client_id"],
            business_type=business_type,
        )
        categorisation_id = str(uuid.uuid4())
        repo.save_categorisation(
            categorisation_id=categorisation_id,
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
            categorised_at=_now(),
        )

        # 9. Apply the GL override now, before filing. 11.2: the sidecar is built
        #    from the effective code, so overriding after filing would leave the
        #    file on disk permanently disagreeing with the database.
        override_code = _override(corrections.gl_nominal_code)
        override_name = _override(corrections.gl_account_name)
        if override_code or override_name:
            repo.update_categorisation(
                categorisation_id,
                override_code or categorisation.suggested_code,
                override_name or categorisation.suggested_name,
                _override(corrections.gl_correction_reason) or f"manual override by {actor}",
            )

        effective_code = override_code or categorisation.suggested_code
        effective_name = override_name or categorisation.suggested_name

        # 10. Sidecar from the effective code and name, all three keys.
        invoice_date = merged["invoice_date"] or datetime.now(timezone.utc).date().isoformat()
        sidecar_payload = make_enriched_sidecar(
            receipt_id=receipt_id,
            source=receipt.get("source", "email"),
            client_code=receipt.get("client_code"),
            client_name=client_name,
            capture_date=_now(),
            invoice_date=merged["invoice_date"],
            supplier=merged["supplier_name"],
            net=merged["net_amount"],
            vat=merged["vat_amount"],
            gross=merged["gross_amount"],
            currency=merged["currency"],
            category_code=effective_code,
            category_name=effective_name,
            confidence=categorisation.confidence,
            validation_status="ok",
            asserted=None,
            original_filename=receipt["filename"],
            claimed_client_code=None,
        )

        # 11. File it, then record where it went. mark_receipt_filed sets
        #     filed_path, which is what protects it from duplicate detection.
        dest_path, _sidecar_path = file_receipt(
            Path(receipt["file_path"]),
            client_name,
            determine_tax_year(invoice_date),
            merged["supplier_name"] or "unknown",
            merged["gross_amount"] or 0.0,
            receipt["filename"],
            sidecar_payload,
        )
        repo.mark_receipt_filed(receipt_id, str(dest_path))
        repo.update_receipt_status(receipt_id, "ok")

        # 12. The Review pair is stale now. Already gone is not an error.
        removed = remove_review_pair(receipt_id, receipt.get("client_code"), receipt.get("filename"))
        if not removed:
            logger.info(f"no review pair removed for {receipt_id}, nothing on disk")

        # 13. Learn the mapping only if asked. Never automatically: one correction
        #     against a misread supplier name would poison the mapping table, and
        #     the exact-match layer would then apply the wrong code confidently to
        #     every future receipt from that vendor.
        if corrections.remember_gl_for_supplier and effective_code:
            vendor_code = getattr(categorisation, "vendor_code", None)
            if vendor_code:
                repo.upsert_client_vendor(
                    client_id=receipt["client_id"],
                    vendor_code=vendor_code,
                    nominal_code=effective_code,
                    account_name=effective_name,
                    last_updated=_now(),
                    vendor_name=merged["supplier_name"],
                )
            else:
                logger.warning(
                    f"remember_gl_for_supplier requested for {receipt_id} but the engine "
                    "returned no vendor_code, so nothing was learned"
                )

        # 14. Audit row.
        _record_event(
            repo, receipt_id, actor, source, "resolve", "filed",
            extraction_id=extraction_id, corrections=corrections,
            gl_override_code=override_code,
        )

        logger.info(f"receipt {receipt_id} resolved by {actor} via {source}, filed to {dest_path}")

        # 15. Done.
        return ResolutionOutcome(
            outcome="filed", receipt_id=receipt_id, extraction_id=extraction_id,
            filed_path=str(dest_path),
            category_code=effective_code,
            category_name=effective_name,
            category_confidence=categorisation.confidence,
            validation_notes=["manually corrected and filed"],
            message=f"Filed to {dest_path}",
        )

    except Exception as exc:
        # The web layer must never 500 on a Save. The traceback is the record, and
        # error_detail is for logs only: never render it.
        logger.error(f"error resolving receipt {receipt_id}: {exc}", exc_info=True)
        return ResolutionOutcome(
            outcome="error", receipt_id=receipt_id,
            message="Something went wrong resolving this receipt. It has been logged.",
            error_detail=str(exc),
        )
    finally:
        repo.release_receipt_lock(receipt_id)


def discard_receipt(repo, receipt_id, reason, actor, source) -> ResolutionOutcome:
    """Status to 'discarded'. Never deletes the original file or any extraction row.

    Design document 4.2. Used for a confirmed duplicate, and for a failed receipt
    that is never going to be resolvable.
    """
    receipt = repo.get_receipt(receipt_id)
    if not receipt:
        return ResolutionOutcome(
            outcome="not_found", receipt_id=receipt_id,
            message=f"Receipt not found: {receipt_id}",
        )

    if not repo.acquire_receipt_lock(receipt_id):
        return ResolutionOutcome(
            outcome="locked", receipt_id=receipt_id,
            message="Another process is working on this receipt. Try again in a moment.",
        )

    try:
        repo.update_receipt_status(receipt_id, "discarded")

        # The receipt's life in the Review folder is over. Leaving the pair behind
        # is what made IntelliBooks file a duplicate, per 3.5.
        removed = remove_review_pair(receipt_id, receipt.get("client_code"), receipt.get("filename"))
        if not removed:
            logger.info(f"no review pair removed for {receipt_id}, nothing on disk")

        _record_event(repo, receipt_id, actor, source, "discard", "discarded")
        logger.info(f"receipt {receipt_id} discarded by {actor} via {source}: {reason}")

        return ResolutionOutcome(
            outcome="discarded", receipt_id=receipt_id,
            message=f"Discarded: {reason}" if reason else "Discarded.",
        )

    except Exception as exc:
        logger.error(f"error discarding receipt {receipt_id}: {exc}", exc_info=True)
        return ResolutionOutcome(
            outcome="error", receipt_id=receipt_id,
            message="Something went wrong discarding this receipt. It has been logged.",
            error_detail=str(exc),
        )
    finally:
        repo.release_receipt_lock(receipt_id)

"""Resolution service: the one implementation all four callers go through.

Design document sections 3.2, 3.3, 4.1, 4.2 and 4.3.

This module must not import Flask, argparse, anything under `worker/email/`, or
anything that prints or reads input. That is what makes it reusable by the CLI,
the console form, the resolution back-feed and a cloud API later, and three
independent implementations of resolution is what caused the divergence this
design exists to fix.

`apply_resolution_note`, the back-feed entry point, is section 12. It parses a note
written by IntelliBooks Desktop and applies it. The file walking, and the moving of
notes to `processed\\` and `failed\\`, belong to the pipeline: 4.1 gives app.py the
job of consuming back-feed notes, and this module has no business touching folders
it was not handed.
"""

import json
import logging
import math
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

# Design document 12.2. Bump only when both halves of the contract change.
NOTE_SCHEMA = 1
NOTE_ACTIONS = ("filed", "discarded")

# The note's own timestamp, which is what 12.3 step 3 keys idempotency on.
# resolution_events has no column for it, so it lives in corrections_json, which
# is already a JSON blob and is already the record of what the note corrected.
NOTE_RESOLVED_AT_KEY = "note_resolved_at"

# 12.3 step 4. `source` describes the tool, `actor` describes who: for a note both
# are 'desktop', because Desktop has no user accounts. Note that the note's own
# `source` field is the receipt's intake route, carried through from the pipeline,
# and must never be read as the actor. See the 12.4 amendment of 2026-07-28.
DESKTOP_ACTOR = "desktop"
DESKTOP_SOURCE = "desktop"

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
    outcome: str    # filed | discarded | still_invalid | stale | locked | not_found | already_filed | error
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


class ResolutionNoteError(ValueError):
    """A note that cannot be applied as written.

    The message is written to the `.error.txt` beside the note in `failed\\`, so it
    is read by a human deciding whether the pipeline or Desktop is at fault. Say
    which field and why.
    """


@dataclass
class ResolutionNote:
    """A parsed, normalised back-feed note. Design document 12.2."""
    action: str                             # 'filed' | 'discarded'
    resolved_at: str
    receipt_id: Optional[str] = None        # may be null; then match on filenames
    client_id: Optional[str] = None
    resolved_by: Optional[str] = None
    values: Dict[str, Any] = field(default_factory=dict)
    category_name: Optional[str] = None
    filed_path: Optional[str] = None
    original_review_files: List[str] = field(default_factory=list)
    reason: Optional[str] = None


def _note_text(raw: Dict[str, Any], key: str) -> Optional[str]:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ResolutionNoteError(f"'{key}' must be text, got {type(value).__name__}")
    return value.strip() or None


def _note_amount(value: Any, key: str) -> Optional[float]:
    """12.2: amounts are numbers, and 12.4 as amended: round to two places here.

    A string is rejected rather than coerced. Bug 3.3 exists because string amounts
    reached `validate()` and raised TypeError on `round()`, and the fix was to stop
    strings entering rather than to coerce them in a second place. Integers are
    accepted: JavaScript writes `"net": 80`, not `80.0`.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ResolutionNoteError(
            f"'{key}' must be a JSON number, got {type(value).__name__}. "
            "12.2 forbids strings for amounts."
        )
    if not math.isfinite(value):
        raise ResolutionNoteError(f"'{key}' is not a finite number")
    return round(float(value), 2)


def parse_resolution_note(raw: Any) -> ResolutionNote:
    """Validate and normalise a note. Raises ResolutionNoteError, never returns junk.

    Strict on purpose. The other half of this contract is built by a session that
    cannot see this one, so a note that does not match 12.2 is worth surfacing in
    `failed\\` rather than half-applying. The one deliberate leniency is that extra
    keys are ignored, so the contract can gain a field without every note failing.
    """
    if not isinstance(raw, dict):
        raise ResolutionNoteError(f"a note must be a JSON object, got {type(raw).__name__}")

    schema = raw.get("schema")
    if schema != NOTE_SCHEMA:
        raise ResolutionNoteError(
            f"unsupported note schema {schema!r}; this pipeline understands {NOTE_SCHEMA}"
        )

    action = raw.get("action")
    if action not in NOTE_ACTIONS:
        raise ResolutionNoteError(
            f"'action' must be one of {NOTE_ACTIONS}, got {action!r}"
        )

    resolved_at = _note_text(raw, "resolved_at")
    if not resolved_at:
        raise ResolutionNoteError("'resolved_at' is required: it is the idempotency key")

    review_files = raw.get("original_review_files") or []
    if not isinstance(review_files, list) or not all(isinstance(f, str) for f in review_files):
        raise ResolutionNoteError("'original_review_files' must be a list of filenames")

    note = ResolutionNote(
        action=action,
        resolved_at=resolved_at,
        receipt_id=_note_text(raw, "receipt_id"),
        client_id=_note_text(raw, "client_id"),
        resolved_by=_note_text(raw, "resolved_by"),
        original_review_files=list(review_files),
        reason=_note_text(raw, "reason"),
    )

    if action == "discarded":
        # 12.2: values and filed_path are absent for a discard. Present-and-ignored
        # rather than rejected: refusing a legitimate discard over a harmless extra
        # key would be the wrong trade, and the warning is enough to spot drift.
        for unexpected in ("values", "filed_path"):
            if raw.get(unexpected) is not None:
                logger.warning(
                    f"discard note for {note.receipt_id} carries '{unexpected}', which 12.2 "
                    "says is absent for a discard; ignoring it"
                )
        return note

    filed_path = _note_text(raw, "filed_path")
    if not filed_path:
        raise ResolutionNoteError("'filed_path' is required for a filed note")
    note.filed_path = filed_path

    raw_values = raw.get("values")
    if not isinstance(raw_values, dict):
        raise ResolutionNoteError("'values' must be an object for a filed note")

    values: Dict[str, Any] = {}
    for name in CORRECTABLE_FIELDS:
        if name not in raw_values:
            continue
        supplied = raw_values[name]
        if name in AMOUNT_FIELDS:
            values[name] = _note_amount(supplied, name)
        elif supplied is None:
            values[name] = None
        elif isinstance(supplied, str):
            values[name] = supplied.strip() or None
        else:
            raise ResolutionNoteError(
                f"'values.{name}' must be text, got {type(supplied).__name__}"
            )

    if not values.get("supplier_name"):
        raise ResolutionNoteError("'values.supplier_name' is required for a filed note")
    if values.get("gross_amount") is None:
        raise ResolutionNoteError("'values.gross_amount' is required for a filed note")

    invoice_date = values.get("invoice_date")
    if not invoice_date:
        raise ResolutionNoteError("'values.invoice_date' is required for a filed note")
    if not _ISO_DATE_RE.match(invoice_date):
        raise ResolutionNoteError(
            f"'values.invoice_date' must be YYYY-MM-DD, got {invoice_date!r}"
        )
    try:
        datetime.strptime(invoice_date, "%Y-%m-%d")
    except ValueError:
        raise ResolutionNoteError(f"'values.invoice_date' is not a real date: {invoice_date!r}")

    currency = raw_values.get("currency")
    if currency is not None and not isinstance(currency, str):
        raise ResolutionNoteError("'values.currency' must be text")
    values["currency"] = (currency or config.DEFAULT_CURRENCY).strip() or config.DEFAULT_CURRENCY

    # A name, never a code: Desktop has no codes. An empty string is the common
    # case, because Desktop does not require a category before filing, and it means
    # "no category" rather than a name to look up. See the 12.4 amendment.
    category = raw_values.get("category_name")
    if category is not None and not isinstance(category, str):
        raise ResolutionNoteError("'values.category_name' must be text")
    note.category_name = (category or "").strip() or None

    note.values = values
    return note


def resolve_practice_path(filed_path: str) -> Path:
    """12.2: `filed_path` is relative to the practice root, with backslashes.

    Resolved against config.PRACTICE_ROOT at call time. An absolute path is used as
    given, which costs nothing and means a note written by a future tool that
    happens to be absolute is not silently misread as a relative one.
    """
    candidate = Path(str(filed_path).replace("\\", "/"))
    if candidate.is_absolute():
        return candidate
    return config.PRACTICE_ROOT / candidate


def _client_details(client_id: Optional[str]) -> Tuple[str, str, Optional[str]]:
    """(client_name, trade, client_folder_name) for a client_id.

    Sub-steps 10d.13 and 10d.14. Keyed on client_id, because there is no client
    code any more, and the folder name is returned rather than derived from the
    display name: `client_name` is freely editable and is never used to build a
    path, `client_folder_name` is fixed once a folder exists.

    An unresolved client returns None for the folder, and the caller must not
    file into Clients on that. That is 10d.18 and it is the whole point: the
    lookup that used to substitute the code for the name whenever it missed is
    what filed four receipts into a folder IntelliBooks does not read.
    """
    entry = config.CLIENTS_BY_ID.get(client_id or "") or {}
    return (
        entry.get("client_name") or (client_id or "UNKNOWN"),
        entry.get("trade", "UNSPECIFIED"),
        entry.get("client_folder_name") or None,
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

    client_name, business_type, _folder = _client_details(receipt.get("client_id"))

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
                  extraction_id=None, corrections=None, gl_override_code=None,
                  reason=None, note_resolved_at=None) -> None:
    """One audit row per resolution.

    Written for filed, discarded and still_invalid only. Not for not_found, stale
    or locked, because nothing happened. Not for error either: the state is
    unknown at that point and a second write risks compounding it, so the logged
    traceback is the record. See the 2026-07-27 amendment to 4.2.

    note_resolved_at is the back-feed's idempotency key, stored in corrections_json
    because 5.1 has no column for it. See NOTE_RESOLVED_AT_KEY.
    """
    payload: Dict[str, Any] = {}
    if corrections is not None and corrections.values:
        payload.update(corrections.values)
    if note_resolved_at:
        payload[NOTE_RESOLVED_AT_KEY] = note_resolved_at
    corrections_json = json.dumps(payload, sort_keys=True, default=str) if payload else None
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
        reason=reason,
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
    merged["currency"] = extraction.get("currency") or config.DEFAULT_CURRENCY
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

    # 1a. Refuse a receipt that is already filed. Nothing below inspects
    #     filed_path, so without this an ok receipt is re-filed, gets a second
    #     manual_correction row and leaves a second copy on disk under a -2 name.
    #     That is the double-filing this design exists to prevent, arriving
    #     through the front door. An expected condition, not an error: the
    #     console must be able to offer the existing file.
    #
    #     The back-feed's `filed` note is the one legitimate re-file and does not
    #     come through here; 12.3 step 5 calls mark_receipt_filed() directly.
    filed_path = receipt.get("filed_path")
    if filed_path:
        # filed_at is NULL for anything filed before 5.1a added the column, and is
        # deliberately not back-filled, so the date is offered when it is known and
        # left out rather than guessed when it is not.
        filed_at = receipt.get("filed_at")
        when = f" on {filed_at}" if filed_at else ""
        return ResolutionOutcome(
            outcome="already_filed", receipt_id=receipt_id,
            extraction_id=(repo.get_extraction_for_receipt(receipt_id) or {}).get("extraction_id"),
            filed_path=filed_path,
            message=(
                f"This receipt has already been filed{when}, as {filed_path}. "
                "Nothing was changed. Open that file to check it, or discard the "
                "receipt if it was filed in error."
            ),
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

        # 10d.16 and 10d.18. A receipt whose client has no folder under Clients
        # cannot be filed there, whatever the corrections say, so it stays a
        # review item. Without this a resolved receipt for an unresolved client
        # would reach file_receipt() with None as the folder name and build a
        # path with the string "None" in it.
        _, _, folder_check = _client_details(receipt.get("client_id"))
        if validation.status == "ok" and not folder_check:
            validation = type(validation)(
                status="needs_review",
                notes=list(validation.notes or []) + [
                    f"client {receipt.get('client_id')} has no client_folder_name in the registry, "
                    "so nothing can be filed into Clients"
                ],
            )

        if validation.status != "ok":
            attempt_id = str(uuid.uuid4())
            # possible_duplicate is a statement about the relationship between two
            # receipts, not about the validity of one, so validation must not
            # overwrite it. Overwriting would also hand a receipt a human has
            # already examined back to the pipeline: possible_duplicate is not
            # auto-retry eligible and needs_review is.
            preserve_status = receipt.get("status") == "possible_duplicate"
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
                update_status=not preserve_status,
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
        client_name, business_type, client_folder_name = _client_details(receipt.get("client_id"))
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
            trade=categorisation.business_type,
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
            client_id=receipt.get("client_id"),
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
            claimed_client_id=None,
        )

        # 11. File it, then record where it went. mark_receipt_filed sets
        #     filed_path, which is what protects it from duplicate detection.
        dest_path, _sidecar_path = file_receipt(
            Path(receipt["file_path"]),
            client_folder_name,
            determine_tax_year(invoice_date),
            merged["supplier_name"] or "unknown",
            merged["gross_amount"] or 0.0,
            receipt["filename"],
            sidecar_payload,
        )
        repo.mark_receipt_filed(receipt_id, str(dest_path))
        repo.update_receipt_status(receipt_id, "ok")

        # 12. The Review pair is stale now. Already gone is not an error.
        removed = remove_review_pair(receipt_id, receipt.get("client_id"), receipt.get("filename"))
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


def discard_receipt(repo, receipt_id, reason, actor, source,
                    note_resolved_at=None) -> ResolutionOutcome:
    """Status to 'discarded'. Never deletes the original file or any extraction row.

    Design document 4.2. Used for a confirmed duplicate, and for a failed receipt
    that is never going to be resolvable.

    note_resolved_at is supplied only by the back-feed, and only so the audit row
    carries the note's own timestamp for the idempotency check in 12.3 step 3. It is
    additive: the CLI and the console do not pass it. 4.2's signature does not list
    it, and that is a divergence worth knowing about rather than hiding.
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
        removed = remove_review_pair(receipt_id, receipt.get("client_id"), receipt.get("filename"))
        if not removed:
            logger.info(f"no review pair removed for {receipt_id}, nothing on disk")

        _record_event(repo, receipt_id, actor, source, "discard", "discarded", reason=reason,
                      note_resolved_at=note_resolved_at)
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


# ---------------------------------------------------------------------------
# The resolution back-feed. Design document 12.
# ---------------------------------------------------------------------------


def _note_already_applied(repo, receipt_id: str, resolved_at: str) -> Optional[Dict[str, Any]]:
    """12.3 step 3. The event row this note already wrote, or None.

    Keyed on the note's own `resolved_at`, not on the receipt, so a second,
    genuinely later resolution of the same receipt is applied rather than skipped.
    """
    for event in repo.list_resolution_events(receipt_id):
        if event.get("source") != DESKTOP_SOURCE:
            continue
        try:
            payload = json.loads(event.get("corrections_json") or "{}")
        except ValueError:
            continue
        if isinstance(payload, dict) and payload.get(NOTE_RESOLVED_AT_KEY) == resolved_at:
            return event
    return None


def _receipt_for_note(repo, note: ResolutionNote) -> Optional[Dict[str, Any]]:
    """12.3 step 2. By receipt_id, else by matching the review filenames.

    The filename fallback is case-insensitive because the two tools case names
    differently: Desktop leaves a supplier as typed and the pipeline lowercases it.
    An ambiguous match is not a match, the same rule `_find_review_sidecar()`
    applies, because two receipts can share an original filename.

    The note's `client_id` and `client.name` are deliberately not used to find
    anything. The note's client field was `client_code` until sub-step 10d.60 and
    is now `client_id`, which both tools do agree on, but it is still not what
    finds the receipt: a note identifies a receipt, not a client, and matching on
    the client would turn a mis-keyed note into a wrong receipt rather than into
    no receipt. See the 12.4 amendment of 2026-07-28.
    """
    if note.receipt_id:
        return repo.get_receipt(note.receipt_id)

    candidates: Dict[str, Dict[str, Any]] = {}
    for review_file in note.original_review_files:
        name = Path(review_file.replace("\\", "/")).name
        if name.lower().endswith(".review.json"):
            continue
        for receipt in repo.find_receipts_by_filename(name):
            candidates[receipt["receipt_id"]] = receipt

    if len(candidates) == 1:
        receipt = next(iter(candidates.values()))
        logger.info(
            f"note matched receipt {receipt['receipt_id']} on filename, it carried no receipt_id"
        )
        return receipt
    if len(candidates) > 1:
        logger.error(
            f"{len(candidates)} receipts match {note.original_review_files}; an ambiguous "
            "match is not a match, so the note is not applied"
        )
    return None


def _resolve_category(note: ResolutionNote) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """12.3 step 6. Returns (code, name, validation_note), and the code is always None.

    **A resolution note's category name is not resolved to a code at all.** The name
    is stored, no vendor mapping is learned, and a validation note records it. 12.3
    says that is expected and not an error.

    ~~It looked up `repo.find_coa_account_by_name()`, which queried `coa_accounts`.~~
    **That table was cancelled by amendment 96 and the cancellation confirmed by 124**,
    so the lookup returned None for every name ever asked and the found branch was
    unreachable. Both are deleted, outstanding item 155, 2026-09-04. Deleted rather
    than repointed: the chart now lives in the bundle IntelliCharts publishes and
    could be read here through worker/categorisation/chart.py, and whether a caption
    typed in IntelliBooks may be matched to an account by name, with or without
    `coa_alt_names.csv`, is a decision nobody has taken. **A dead lookup is not a
    place to keep that question.**

    A blank category is not a lookup at all. Desktop does not require a category
    before filing, so `""` is the common case and it means "no category".
    """
    if not note.category_name:
        return None, None, None

    return (
        None,
        note.category_name,
        f"category '{note.category_name}' was stored as a name without a code, "
        "because a note's category is not matched against the chart of accounts",
    )


def _apply_filed_note(repo, categorisation_engine, receipt: Dict[str, Any],
                      note: ResolutionNote) -> ResolutionOutcome:
    """12.3 step 5. Record a filing Desktop has already done on disk.

    **The image is already at `filed_path`.** So this records the filing with
    `mark_receipt_filed()` and never calls `file_receipt()`. Getting that wrong
    leaves a second copy on disk under a `-2` name for every Desktop resolution,
    which is the exact bug this contract exists to prevent. That is why this is its
    own path rather than a flag threaded through `resolve_receipt()`.

    No sidecar is written either. Desktop wrote one when it filed, in its own shape,
    and rewriting it would be a write into a folder Desktop has just written to.
    12.4 leaves that decision to Paul at step 10; until then the sidecar of record
    for a Desktop-filed receipt is the one Desktop wrote.
    """
    receipt_id = receipt["receipt_id"]
    target = resolve_practice_path(note.filed_path)
    if not target.exists():
        return ResolutionOutcome(
            outcome="error", receipt_id=receipt_id,
            message=(
                f"The note says this receipt was filed as {note.filed_path}, but there is "
                "nothing there. Nothing was changed."
            ),
            error_detail=f"filed_path does not exist on disk: {target}",
        )

    existing = receipt.get("filed_path")
    if existing and str(existing) != str(target):
        # Two filings of the same receipt, in two places, by two tools. That is the
        # disagreement between the database and the books that this contract exists
        # to prevent, so it is surfaced rather than resolved by guessing.
        return ResolutionOutcome(
            outcome="already_filed", receipt_id=receipt_id, filed_path=str(existing),
            message=(
                f"This receipt is already filed as {existing}, and the note says it was "
                f"filed as {note.filed_path}. Nothing was changed."
            ),
            error_detail=f"filed_path conflict: db={existing} note={target}",
        )

    if not repo.acquire_receipt_lock(receipt_id):
        return ResolutionOutcome(
            outcome="locked", receipt_id=receipt_id,
            message="Another process is working on this receipt. The note will be retried.",
        )

    try:
        previous = repo.get_extraction_for_receipt(receipt_id) or {}

        # The note is the practice's decided truth, so its values are not merged over
        # the extraction: an amount the note does not carry is absent rather than
        # inherited, or a corrected gross could end up beside a stale net. The two
        # fields Desktop has no input for are carried forward rather than thrown
        # away, because the extractor read them and nobody has contradicted them.
        merged = {name: note.values.get(name) for name in CORRECTABLE_FIELDS}
        for carried in ("receipt_ref_number", "receipt_time"):
            if carried not in note.values:
                merged[carried] = previous.get(carried)
        currency = note.values.get("currency") or previous.get("currency") or config.DEFAULT_CURRENCY

        candidate = ExtractionResult(
            engine="manual_correction",
            supplier_name=merged["supplier_name"],
            invoice_date=merged["invoice_date"],
            net_amount=merged["net_amount"],
            vat_amount=merged["vat_amount"],
            gross_amount=merged["gross_amount"],
            currency=currency,
            raw_response=json.dumps(
                {"resolution_note": {"resolved_at": note.resolved_at, "values": merged}},
                sort_keys=True, default=str,
            ),
            receipt_ref_number=merged["receipt_ref_number"],
            receipt_time=merged["receipt_time"],
        )

        validation_notes = ["filed in IntelliBooks Desktop"]
        # validate() runs for the record, but does not decide the status: a human
        # filed this and 12.3 step 5 says the status is ok. Throwing away what
        # validate() said would be the wrong half of that, so an inconsistent set of
        # figures earns a line on the row.
        validation = validate(candidate)
        if validation.status != "ok":
            validation_notes.append(
                "filed by decision in Desktop despite: " + ", ".join(validation.notes)
            )

        code, category_name, category_note = _resolve_category(note)
        if category_note:
            validation_notes.append(category_note)

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
            currency=currency,
            raw_response=candidate.raw_response,
            validation_status="ok",
            validation_notes=validation_notes,
            receipt_ref_number=merged["receipt_ref_number"],
            receipt_time=merged["receipt_time"],
            pipeline_version=config.get_pipeline_version(),
        )

        # Categorise for the audit trail, exactly as 4.3 step 8 does. The engine's
        # suggestion is never overwritten; Desktop's category goes in the correction
        # columns beside it.
        client_name, business_type, _folder = _client_details(receipt.get("client_id"))
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
            trade=categorisation.business_type,
            vendor_key=categorisation.vendor_key,
            suggested_code=categorisation.suggested_code,
            suggested_name=categorisation.suggested_name,
            confidence=categorisation.confidence,
            match_source=categorisation.match_source,
            matched_vendor=categorisation.matched_vendor,
            needs_review=categorisation.needs_review,
            categorised_at=_now(),
        )
        if code or category_name:
            repo.update_categorisation(
                categorisation_id, code, category_name,
                "category from the IntelliBooks Desktop resolution note",
            )

        # 12.3 step 6 says learn the vendor mapping from a Desktop resolution. 11.3
        # says never learn automatically, because one correction against a misread
        # supplier name poisons the mapping table and the exact-match layer then
        # applies the wrong code confidently to every future receipt from that
        # vendor. **The two sections disagree and nothing here decides it.**
        # There is no code to learn from in any case: _resolve_category() returns
        # None for every note, so this was an `if code:` branch that logged a
        # warning and could never run. Removed with item 155 on 2026-09-04, and the
        # disagreement is recorded here rather than inside unreachable code.

        repo.mark_receipt_filed(receipt_id, str(target))
        repo.update_receipt_status(receipt_id, "ok")

        # Desktop deletes the Review pair itself, per the 12.4 amendment, so finding
        # nothing is the expected case and not a failure.
        removed = remove_review_pair(
            receipt_id, receipt.get("client_id"), receipt.get("filename")
        )
        if not removed:
            logger.info(
                f"no review pair on disk for {receipt_id}; Desktop removes its own pair"
            )

        _record_event(
            repo, receipt_id, DESKTOP_ACTOR, DESKTOP_SOURCE, "resolve", "filed",
            extraction_id=extraction_id,
            corrections=Corrections(values=dict(merged, currency=currency)),
            gl_override_code=code,
            note_resolved_at=note.resolved_at,
        )
        logger.info(
            f"receipt {receipt_id} recorded as filed in IntelliBooks Desktop at {target}, "
            "no second copy written"
        )

        return ResolutionOutcome(
            outcome="filed", receipt_id=receipt_id, extraction_id=extraction_id,
            filed_path=str(target),
            category_code=code,
            category_name=category_name or categorisation.suggested_name,
            category_confidence=categorisation.confidence,
            validation_notes=validation_notes,
            message=f"Recorded the Desktop filing at {target}",
        )

    except Exception as exc:
        logger.error(
            f"error applying the resolution note for {receipt_id}: {exc}", exc_info=True
        )
        return ResolutionOutcome(
            outcome="error", receipt_id=receipt_id,
            message="Something went wrong applying this resolution note. It has been logged.",
            error_detail=str(exc),
        )
    finally:
        repo.release_receipt_lock(receipt_id)


def apply_resolution_note(repo, categorisation_engine, note: dict) -> ResolutionOutcome:
    """Back-feed entry point. Design document 12.3.

    Validates the note, finds its receipt, then either records the filing Desktop
    has already done or discards the receipt, with actor='desktop' and
    source='desktop'. It does not reimplement resolution: a discard goes straight to
    `discard_receipt()`, and the filed path is the one documented divergence, for the
    reason in `_apply_filed_note()`.

    Returns an outcome and never raises. `filed` and `discarded` mean the note was
    applied and the caller may move it to `processed\\`. Anything else means it was
    not, and the caller moves it to `failed\\`. Nothing in `Resolutions\\` is ever
    deleted, on any path.
    """
    receipt_id_hint = note.get("receipt_id") if isinstance(note, dict) else None

    try:
        parsed = parse_resolution_note(note)
    except ResolutionNoteError as exc:
        logger.error(f"unusable resolution note for {receipt_id_hint}: {exc}")
        return ResolutionOutcome(
            outcome="error", receipt_id=str(receipt_id_hint or ""),
            message=f"This resolution note does not match the contract: {exc}",
            error_detail=str(exc),
        )

    receipt = _receipt_for_note(repo, parsed)
    if not receipt:
        return ResolutionOutcome(
            outcome="not_found", receipt_id=str(parsed.receipt_id or ""),
            message=(
                f"No receipt matches this note (receipt_id={parsed.receipt_id!r}, "
                f"review files={parsed.original_review_files})."
            ),
            error_detail="no receipt matched by id or by review filename",
        )

    receipt_id = receipt["receipt_id"]

    applied = _note_already_applied(repo, receipt_id, parsed.resolved_at)
    if applied:
        logger.info(
            f"note for {receipt_id} resolved at {parsed.resolved_at} was already applied "
            f"on {applied['created_at']}; nothing to do"
        )
        outcome = applied["outcome"]
        return ResolutionOutcome(
            outcome=outcome if outcome in ("filed", "discarded") else parsed.action,
            receipt_id=receipt_id,
            extraction_id=applied.get("extraction_id"),
            filed_path=receipt.get("filed_path"),
            message=f"Already applied on {applied['created_at']}. Nothing was changed.",
        )

    if parsed.action == "discarded":
        return discard_receipt(
            repo, receipt_id,
            reason=parsed.reason or "discarded in IntelliBooks Desktop",
            actor=DESKTOP_ACTOR, source=DESKTOP_SOURCE,
            note_resolved_at=parsed.resolved_at,
        )

    return _apply_filed_note(repo, categorisation_engine, receipt, parsed)

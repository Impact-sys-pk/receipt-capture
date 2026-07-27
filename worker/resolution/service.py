"""Resolution service: the one implementation all four callers go through.

Design document sections 3.2, 3.3, 4.1, 4.2 and 4.3.

This module must not import Flask, argparse, anything under `worker/email/`, or
anything that prints or reads input. That is what makes it reusable by the CLI,
the console form, the resolution back-feed and a cloud API later, and three
independent implementations of resolution is what caused the divergence this
design exists to fix.

`apply_resolution_note`, the back-feed entry point, is step 10.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import config

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

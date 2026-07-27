"""Resolution service: operator-input coercion.

Design document sections 3.2, 3.3 and 4.2.

This module must not import Flask, argparse, anything under `worker/email/`, or
anything that prints or reads input. That is what makes it reusable by the CLI,
the console form, the resolution back-feed and a cloud API later.

Only `parse_corrections` lives here for now. The rest of the 4.2 service API
(`get_resolution_view`, `resolve_receipt`, `discard_receipt`,
`apply_resolution_note`) is implementation step 8.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

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

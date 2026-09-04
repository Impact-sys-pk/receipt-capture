from dataclasses import dataclass
from datetime import datetime
from typing import List

from worker.extraction.base import ExtractionResult

# One penny, sub-step 10g.1 and design document 18.4, changed 2026-09-04 from 0.02.
# 18.9 had listed the change as cancelled and the code had never moved either way.
# It is the tolerance on net + VAT against gross on ONE extracted receipt, and it is
# not the same number as the half-penny in matchScore() in IntelliBooks-Desktop-v3.html,
# which is a tolerance between two records.
_VAT_TOLERANCE = 0.01


@dataclass
class ValidationResult:
    status: str  # ok | needs_review | failed
    notes: List[str]


def validate(result: ExtractionResult) -> ValidationResult:
    notes: List[str] = []

    if not result.supplier_name:
        notes.append("missing supplier_name")
    if not result.invoice_date:
        notes.append("missing invoice_date")
    if result.gross_amount is None:
        notes.append("missing gross_amount")

    if result.invoice_date:
        try:
            datetime.strptime(result.invoice_date, "%Y-%m-%d")
        except ValueError:
            notes.append(f"invalid date: {result.invoice_date}")

    if (
        result.net_amount is not None
        and result.vat_amount is not None
        and result.gross_amount is not None
    ):
        expected = round(result.net_amount + result.vat_amount, 2)
        actual = round(result.gross_amount, 2)
        if abs(expected - actual) > _VAT_TOLERANCE:
            notes.append(
                f"gross mismatch: {result.net_amount} + {result.vat_amount} = {expected}, got {actual}"
            )

    for field, val in [
        ("net_amount", result.net_amount),
        ("vat_amount", result.vat_amount),
        ("gross_amount", result.gross_amount),
    ]:
        if val is not None and val < 0:
            notes.append(f"{field} is negative: {val}")

    if not notes:
        status = "ok"
    else:
        # If gross is missing, this is unrecoverable
        if result.gross_amount is None:
            status = "failed"
        # If supplier is missing but we have a valid gross and a valid invoice_date, route to review
        elif not result.supplier_name:
            date_valid = False
            if result.invoice_date:
                try:
                    datetime.strptime(result.invoice_date, "%Y-%m-%d")
                    date_valid = True
                except Exception:
                    date_valid = False

            if date_valid and result.gross_amount is not None:
                status = "needs_review"
            else:
                status = "failed"
        else:
            status = "needs_review"

    return ValidationResult(status=status, notes=notes)

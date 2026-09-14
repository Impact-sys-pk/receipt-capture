from dataclasses import dataclass
from datetime import date, datetime
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


#: The floor, and the only place the figure is written. A year before this is
#: not a case this system has: the practice did not exist and neither did MTD.
_YEAR_FLOOR = 2000


def readable_year_range() -> tuple:
    """The years an `invoice_date` may carry, as (floor, ceiling), inclusive.

    **Computed when asked rather than at import**, which is Paul's instruction
    of 2026-09-14. A module-level `date.today().year` would fix the ceiling at
    whatever year the process started, and this pipeline is left running for
    days at a time, so a receipt arriving after midnight on 31 December would be
    refused by a rule that had stopped reading the clock.
    """
    return _YEAR_FLOOR, date.today().year + 1


def year_is_readable(year: int) -> bool:
    """Is that a year a receipt can carry? Paul's decision, 2026-09-14.

    **2000 to next year inclusive, and the bound is written here and nowhere
    else.** Three doors accept a four-digit `invoice_date` and none of them used
    to question the year: `validate()` below, and `parse_corrections()` and
    `parse_resolution_note()` in `worker\\resolution\\service.py`. A receipt is
    filed at `Clients\\TEST\\IntelliBooks\\Receipts\\26-27\\0026-08-30_...` and
    got there because somebody typed two digits into a date box, the browser
    made it year 26, and `determine_tax_year()` composed `26-27` from it.

    **The ceiling is next year, not this one, because IntelliBooks Desktop has
    shipped exactly that since 2026-09-06** and the two products have to agree
    on the boundary. `badYear()` in `IntelliBooks-Desktop-v3.html`:
    `if(y>=2000&&y<=new Date().getFullYear()+1)return false;`. Its comment
    carries the reasoning for both halves: "four digits, this century, and not
    more than one year ahead. A date genuinely before 2000 is not a case this
    system has."

    **Sub-step 10d.41's two-digit branch in `worker\\extraction\\postprocess.py`
    keeps its own, stricter bound and deliberately does not call this.** There
    `2000 + c` is an inference the system made from two digits; here the year is
    a figure somebody stated. The system may be stricter with its own guesses
    than with a person's statement. `tests/test_implausible_year.py`'s
    `TenD41IsLeftStricterTest` holds that difference so it is not tidied away.
    """
    floor, ceiling = readable_year_range()
    return floor <= year <= ceiling


def unreadable_year(invoice_date) -> int | None:
    """The year of that ISO date if it is not one a receipt can carry, else None.

    **None for anything that is not a real calendar date, which is not evasion.**
    Every door already refuses such a date with its own wording, and a helper
    that refused it too would give one fault two different messages depending on
    which check happened to run first.
    """
    if not isinstance(invoice_date, str):
        return None
    try:
        parsed = datetime.strptime(invoice_date, "%Y-%m-%d")
    except ValueError:
        return None
    return None if year_is_readable(parsed.year) else parsed.year


def unreadable_year_reason(year: int) -> str:
    """The clause both correction doors embed, so one fault has one wording.

    Each door keeps its own subject prefix, exactly as each already does for a
    date that is not a real calendar date: the CLI names the value supplied and
    the note validator names the field. What they must not do is describe the
    same fault two different ways.

    "reads as year" is Desktop's own phrasing in `badYear()`, so an operator who
    has seen the toast recognises the sentence in a `.error.txt`.
    """
    floor, ceiling = readable_year_range()
    return (f"reads as year {year}, and a receipt date must fall between "
            f"{floor} and {ceiling}")


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
        # The two are mutually exclusive: `unreadable_year()` answers None for
        # anything that did not parse above, so one fault never gets two notes.
        # **The date is not corrected and no century is inferred**, which is
        # 10d.41's reasoning unchanged: a pivot tight enough to read 99 as 1999
        # reads 28 as 1928. The note names the year and the receipt goes to
        # Review, which is what CLAUDE.md's closing rule asks for.
        implausible = unreadable_year(result.invoice_date)
        if implausible is not None:
            notes.append(
                f"implausible year {implausible}: {result.invoice_date}")

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
                # An implausible year is not a date this branch can rely on
                # either. The brief asks for the treatment an invalid date
                # already gets, and this is where that treatment differs:
                # with no supplier as well, the receipt is `failed` rather than
                # `needs_review`, because nothing is left to review against.
                if unreadable_year(result.invoice_date) is not None:
                    date_valid = False

            if date_valid and result.gross_amount is not None:
                status = "needs_review"
            else:
                status = "failed"
        else:
            status = "needs_review"

    return ValidationResult(status=status, notes=notes)

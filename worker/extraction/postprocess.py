"""Provider-independent post-processing of an extraction.

Design document 10.2. This logic lived inside `OpenAIVisionExtractor.extract()`,
so a second provider would silently not inherit any of it and both the day-first
date fix and the VAT-inclusive-total fix would stop applying the moment the
engine changed. Neither is provider-specific and both cost real debugging.

A pure move: the behaviour here is byte-for-byte the behaviour that was in
`openai_vision.py`, with one deliberate difference. `prefer_dayfirst` is a
parameter rather than a read of `config.PREFER_DAYFIRST` inside the function, so
these functions are testable without patching module state. The caller passes
`config.PREFER_DAYFIRST`, read at call time, so behaviour is identical.

No `ExtractionResult`, no provider client, and no logging of document content.

The broad `try/except Exception: pass` blocks are kept exactly as they were and
are load-bearing: a numeric coercion failure must leave the values untouched
rather than fail the extraction.
"""

import re
from datetime import date


def parse_ambiguous_date(raw: str, prefer_dayfirst: bool) -> str | None:
    """Parse a numeric date such as 09/05/26 or 9-5-2026. None if it cannot be read.

    Where day and month are both 12 or under the date is genuinely ambiguous and
    `prefer_dayfirst` decides. Where one part is over 12 it can only be the day,
    so the convention does not matter.
    """
    # Handle numeric dates like 09/05/26 or 9-5-2026
    if not raw or not isinstance(raw, str):
        return None
    parts = re.split(r"[^0-9]+", raw)
    parts = [p for p in parts if p]
    if len(parts) != 3:
        return None
    try:
        a, b, c = [int(p) for p in parts]
    except Exception:
        return None
    # Normalize year
    if c < 100:
        year = 2000 + c
    elif c < 1000:
        # unlikely, treat as 2000s
        year = 2000 + c
    else:
        year = c

    # If both day and month <= 12 then ambiguous
    if a <= 12 and b <= 12:
        if prefer_dayfirst:
            day, month = a, b
        else:
            day, month = b, a
    else:
        # Unambiguous: whichever <= 31 but >12 is day
        if a > 12 and a <= 31:
            day = a; month = b
        elif b > 12 and b <= 31:
            day = b; month = a
        else:
            return None
    try:
        return date(year, month, day).isoformat()
    except Exception:
        return None


def apply_vat_inclusive_swap(net, vat, gross, details):
    """Treat an amount read as net as the gross where the VAT rate says so.

    Fires only when there is no gross and both net and VAT are present. If the
    implied rate matches a common VAT rate when the amount is treated as gross,
    and does not when it is treated as net, the amount is the gross. Records the
    correction in `details`.

    Returns (net, vat, gross, details).
    """
    try:
        if gross is None and net is not None and vat is not None:
            # numeric coercion
            n = float(net)
            v = float(vat)
            implied_rate_net = None
            implied_rate_gross = None
            if n > 0:
                implied_rate_net = v / n
            if (n - v) > 0:
                implied_rate_gross = v / (n - v)

            # Common VAT rates to check against (20%, 5%)
            common_rates = [0.2, 0.05]
            # Tolerances
            rate_tol = 0.03

            match_gross_rate = any(abs(implied_rate_gross - r) <= rate_tol for r in common_rates) if implied_rate_gross is not None else False
            match_net_rate = any(abs(implied_rate_net - r) <= rate_tol for r in common_rates) if implied_rate_net is not None else False

            # If treating the extracted `net` as gross makes the implied rate match common VAT rates
            # while treating it as net does not, then swap: treat net as gross
            if match_gross_rate and not match_net_rate:
                gross = round(n, 2)
                net = round(gross - v, 2)
                # annotate details to record the automatic correction
                note = f"auto_treated_amount_as_gross(implied_rate={implied_rate_gross:.3f})"
                if details:
                    details = f"{details}; {note}"
                else:
                    details = note
    except Exception:
        # If any numeric coercion fails, leave values unchanged
        pass

    return net, vat, gross, details


def resolve_invoice_date(invoice_date, invoice_date_raw, details, prefer_dayfirst):
    """Prefer the model's original matched date string, parsed deterministically.

    Where there is no raw string an ambiguous ISO date is annotated and left
    alone: swapping it would be a coin flip that can corrupt correct output.

    Returns (invoice_date, details).
    """
    # If the model returned the original matched date string, prefer parsing it deterministically
    # using local `PREFER_DAYFIRST` rules. Fall back to previously implemented ISO-based enforcement.
    try:
        parsed_from_raw = None
        if invoice_date_raw:
            parsed_from_raw = parse_ambiguous_date(invoice_date_raw, prefer_dayfirst)
            if parsed_from_raw:
                note = f"auto_parsed_invoice_date_from_raw(raw={invoice_date_raw} -> {parsed_from_raw})"
                if details:
                    details = f"{details}; {note}"
                else:
                    details = note
                invoice_date = parsed_from_raw

        # If we do not have a raw string, do NOT guess by swapping ISO month/day because
        # that is effectively a coin flip and can corrupt correct model outputs. Instead,
        # if the model returned an ambiguous ISO date (both day and month <= 12), annotate
        # the extraction `details` to flag ambiguity so reviewers or downstream logic can
        # decide (or we can apply client-specific rules later).
        if not parsed_from_raw and invoice_date:
            try:
                d = date.fromisoformat(invoice_date)
                if d.day <= 12 and d.month <= 12:
                    note = f"ambiguous_invoice_date_no_raw(model_iso={invoice_date})"
                    if details:
                        details = f"{details}; {note}"
                    else:
                        details = note
                    # leave invoice_date unchanged
            except Exception:
                pass
    except Exception:
        pass

    return invoice_date, details

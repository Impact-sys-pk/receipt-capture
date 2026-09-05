"""Provider-independent post-processing of an extraction.

Design document 10.2. This logic lived inside `OpenAIVisionExtractor.extract()`,
so a second provider would silently not inherit any of it and both the day-first
date fix and the gross-figure fix would stop applying the moment the
engine changed. Neither is provider-specific and both cost real debugging.

A pure move: the behaviour here is byte-for-byte the behaviour that was in
`openai_vision.py`, with one deliberate difference. `prefer_dayfirst` is a
parameter rather than a read of `config.PREFER_DAYFIRST` inside the function, so
these functions are testable without patching module state. The same reasoning
gives establish_gross_from_vat() its `recognised_rates` and `rate_allowance`
parameters: the rates live in the VAT rate table IntelliCharts publishes into
config.CHARTS_DIR, and the caller reads them from it. **This module imports
neither `config` nor `worker.vat_rates`, and must keep it that way**, so it needs
neither a populated .env nor a published bundle to be tested. The caller passes
`config.PREFER_DAYFIRST`, read at call time, so behaviour is identical.

No `ExtractionResult`, no provider client, and no logging of document content.

The broad `try/except Exception: pass` blocks are kept exactly as they were and
are load-bearing: a numeric coercion failure must leave the values untouched
rather than fail the extraction.
"""

import logging
import re
from datetime import date

logger = logging.getLogger(__name__)


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

    # An ISO-shaped raw string is not ambiguous: four digits first can only be a
    # year, so prefer_dayfirst does not apply. Without this branch, 2026-05-09
    # split to 2026, 5, 9, read the 9 as a two-digit year, failed both of the
    # branches below and returned None, so the deterministic path did nothing at
    # all for a receipt that prints its date in ISO form.
    if len(parts[0]) == 4 and len(parts[1]) in (1, 2) and len(parts[2]) in (1, 2):
        try:
            return date(int(parts[0]), int(parts[1]), int(parts[2])).isoformat()
        except Exception:
            # 2026-13-01 and 2026-02-30 return None, as they did before.
            return None

    try:
        a, b, c = [int(p) for p in parts]
    except Exception:
        return None

    # Normalise the year. Sub-step 10d.41, findings 3 and 4 of design document
    # 10.2, which step 6b did not take.
    #
    # A two-digit year is still 2000 + c, so 26 is 2026. Where that lands in the
    # future the date is treated as unreadable and this returns None, so
    # 01/01/99 is no longer read as 2099 and filed.
    #
    # There is deliberately NO century pivot. A cutoff tight enough to turn 99
    # into 1999 turns 28 into 1928, so the system would be choosing between 1928
    # and 2028 on its own. CLAUDE.md's closing rule governs: if something is
    # uncertain, mark it for review and do not guess.
    #
    # The `elif c < 1000` branch is deleted. It had an identical body to the one
    # above it and a comment claiming "treat as 2000s" while 2000 + 999 is 2999.
    # A three-digit year is a misread, not a year.
    if c < 100:
        year = 2000 + c
        if year > date.today().year:
            return None
    elif c < 1000:
        return None
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


def establish_gross_from_vat(net, vat, gross, details, recognised_rates, rate_allowance):
    """Which of the two figures on a receipt is the gross. Sub-step 10d.42.

    Nothing here is a VAT question and the naming no longer says it is. The
    function was called apply_vat_inclusive_swap(), which described a mechanism
    rather than a subject: the VAT figure is the evidence, and the gross is what
    is being established.

    Fires only where a receipt yields a money figure and a VAT figure and no
    gross. Assume, verify, and flag rather than guess:

    - ASSUME the figure is the gross. Paul's observation is that a receipt
      showing two numbers always shows gross and VAT.
    - VERIFY. The implied rate is the VAT divided by the figure less the VAT, and
      it must come out at a recognised rate within a rounding allowance only,
      which is a fraction of a percentage point.
    - If it verifies, ACCEPT: gross is the figure, net is the figure less the VAT.
    - If it does not verify, CHANGE NOTHING and route to Review, with the implied
      percentage in the note.

    Three things this deliberately is not.

    It is not gated on the client's VAT registration. A non-registered client's
    expense IS the gross, so getting this wrong overstates their profit and loss
    by the VAT, which makes it matter more for them and not less.

    There is no per-rate window and no minimum receipt size. Both were designed
    and then made unnecessary by the assume-and-verify shape.

    And the recognised rates come from the published VAT rate table rather than
    from a literal list here. The old code had `common_rates = [0.2, 0.05]` and a
    `rate_tol = 0.03`, which is three percentage points: it would have accepted an
    implied 17% or 23% as 20%.

    `recognised_rates` and `rate_allowance` are parameters for the same reason
    `prefer_dayfirst` is one, stated at the top of this module: this module
    imports neither config nor worker.vat_rates, so it needs neither the openai
    package, nor a populated .env, nor a published bundle, and
    tests/test_postprocess.py proves that in a subprocess. The caller passes
    worker.vat_rates.impliable_rates(), which reads the table IntelliCharts
    publishes, and config.VAT_RATE_ROUNDING_ALLOWANCE, both read at call time.

    Returns (net, vat, gross, details).
    """
    try:
        if gross is None and net is not None and vat is not None:
            # numeric coercion
            n = float(net)
            v = float(vat)

            # The assumption: the figure is the gross. So the net is the figure
            # less the VAT, and that is what the rate is measured against.
            if (n - v) <= 0:
                # Not a gross and a VAT: the VAT is the whole figure or more.
                # Change nothing, and say why, so it reaches a person.
                note = f"gross_not_established(vat_not_less_than_amount, amount={n:.2f}, vat={v:.2f})"
                details = f"{details}; {note}" if details else note
                return net, vat, gross, details

            implied_rate = v / (n - v)
            verified = any(
                abs(implied_rate - rate) <= rate_allowance
                for rate in recognised_rates
            )

            if verified:
                gross = round(n, 2)
                net = round(gross - v, 2)
                note = f"treated_amount_as_gross(implied_rate={implied_rate * 100:.1f}%)"
            else:
                # Change nothing. The note carries the implied percentage, which
                # is the one thing a person needs to decide what the figure was.
                note = f"gross_not_established(implied_rate={implied_rate * 100:.1f}%)"

            details = f"{details}; {note}" if details else note
    except Exception:
        # If any numeric coercion fails, leave values unchanged. Logged rather
        # than swallowed: a genuine error here otherwise looks exactly like a
        # receipt that needed no correction. The values themselves are not
        # logged; a receipt is client data.
        logger.warning("gross could not be established, could not process the amounts", exc_info=True)

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
                # Only note it when it actually changes the date. An ISO raw
                # string usually agrees with the model's own ISO reading, and a
                # note recording a change that did not happen is the same class
                # of problem as a note naming the wrong cause.
                if parsed_from_raw != invoice_date:
                    note = f"auto_parsed_invoice_date_from_raw(raw={invoice_date_raw} -> {parsed_from_raw})"
                    if details:
                        details = f"{details}; {note}"
                    else:
                        details = note
                invoice_date = parsed_from_raw

        # A raw string we could not read is worth reporting whatever the model's
        # date looks like: it is the only signal that the deterministic path did
        # not run, and saying "no raw" here would name the wrong cause. The date
        # is left exactly as the model gave it, as in the branch below.
        # This is also where 10d.41's rejection lands: a two-digit year that
        # resolves into the future, and a three-digit year, both make
        # parse_ambiguous_date() return None, so the raw string is reported as
        # unreadable and the model's own date is left exactly as it gave it.
        if invoice_date_raw and not parsed_from_raw:
            note = (
                f"ambiguous_invoice_date_unparsed_raw(raw={invoice_date_raw}, "
                f"model_iso={invoice_date})"
            )
            if details:
                details = f"{details}; {note}"
            else:
                details = note

        # If we do not have a raw string, do NOT guess by swapping ISO month/day because
        # that is effectively a coin flip and can corrupt correct model outputs. Instead,
        # if the model returned an ambiguous ISO date (both day and month <= 12), annotate
        # the extraction `details` to flag ambiguity so reviewers or downstream logic can
        # decide (or we can apply client-specific rules later).
        elif not parsed_from_raw and invoice_date:
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
                # A model date that is not ISO at all reaches here. Left
                # unchanged, and not treated as ambiguous, but no longer silent.
                logger.warning(
                    "invoice_date ambiguity check skipped, the model date is not an ISO date",
                    exc_info=True,
                )
    except Exception:
        logger.warning("invoice_date resolution skipped, could not process the date", exc_info=True)

    return invoice_date, details

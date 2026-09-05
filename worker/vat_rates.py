"""The VAT rate table, read from the Intellibills bundle.

Item 163. The rates used to live in `config.VAT_RATES`, a dict of five keys typed
into this repository by hand, with `config.VAT_RATES_IMPLIABLE` derived from it.
`publish_master.py` in the IntelliCharts folder now publishes `vat_rates.csv`
beside the charts, so the same rates existed in two places and only one of them
was maintained. That is the two-copies fault the one-bundle arrangement of amendment
194 exists to prevent, so our copy is gone and this module reads theirs.

Modelled on `worker/categorisation/chart.py`, which does the same job for the
charts: `config.CHARTS_DIR`, a cache keyed on the file's modification time so a
file in OneDrive is not re-read once per receipt, and an empty result with an
ERROR rather than an exception when it cannot be read.

**What an unreadable file costs, so the next reader does not have to work it out.**
`impliable_rates()` comes back empty, and an empty set of recognised rates
verifies nothing. Every receipt that yields a figure and a VAT figure and no
gross then fails verification in `establish_gross_from_vat()`, which changes no
amount and routes the receipt to Review with `gross_not_established`. Nothing is
rewritten wrongly and a person looks at every one. **That is the safe direction
and it is deliberate.** There is no hardcoded fallback list, because a fallback
list is the second copy this whole item exists to remove.

**The pipeline does not re-validate the published file.** `validate_vat_rates()`
in `publish_master.py` blocks the publish unless the header is exactly
`name,rate,start,end`, every name is non-blank and unique, every rate parses as a
number between 0 and 100, and a dated row carries both dates while an undated one
carries neither. A file that reached the bundle has passed all of that, so
re-implementing any of it here would be the same two-copies fault in a new place.
A file that did not come from `publish_master.py` is not trusted either way: a row
whose rate will not parse is skipped and logged, and a file with no `rate` column
at all loses every row that way and yields no rate, which is the safe direction
above.

The flow is one way. IntelliCharts publishes in; nothing here ever writes into the
bundle.
"""

import csv
import logging
from typing import NamedTuple

import config

logger = logging.getLogger(__name__)

# Published by publish_master.py into the same bundle as the charts.
VAT_RATES_FILENAME = "vat_rates.csv"


class VatRate(NamedTuple):
    """One published row. `rate` is a fraction; the file writes per cent.

    `start` and `end` are the strings as published, both empty for a rate in
    force and both `YYYY-MM-DD` for a temporary sector relief.
    """

    name: str
    rate: float
    start: str
    end: str

    @property
    def is_dated(self) -> bool:
        return bool(self.start or self.end)


# Parsed tables, keyed on the file's full path, valued (st_mtime_ns, rates). The
# same arrangement chart.py uses, and config.reload_clients_if_changed() before
# it: the modification time decides, not a timer and not a process lifetime.
_CACHE: dict[str, tuple[int, list[VatRate]]] = {}


def _parse_rates(path) -> list[VatRate]:
    """Every row of the published table. Reads by column name.

    The `rate` column is a plain number of per cent, so 20 rather than `20%` or
    `0.2`, and it is divided by 100 here. A row whose rate will not parse is
    skipped with an ERROR naming it and the rest of the file is still used: one
    bad row must not cost the rates that are fine.
    """
    rates: list[VatRate] = []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            name = (row.get("name") or "").strip()
            raw = (row.get("rate") or "").strip()
            try:
                percent = float(raw)
            except ValueError:
                logger.error(
                    f"{path} row {name!r} has a rate of {raw!r}, which is not a "
                    "number of per cent, so the row is ignored. publish_master.py "
                    "writes 20, not 20% and not 0.2."
                )
                continue
            rates.append(VatRate(
                name=name,
                rate=percent / 100,
                start=(row.get("start") or "").strip(),
                end=(row.get("end") or "").strip(),
            ))
    return rates


def load_rates() -> list[VatRate]:
    """The published rate table. Empty list if it cannot be read.

    Empty rather than an exception: this runs on the extraction path, and a
    bundle that has not been published must cost a receipt its implied-rate
    check, not stop the receipt being processed. It is logged at ERROR so it is
    not silent. See the module docstring for what the empty case costs.
    """
    path = config.CHARTS_DIR / VAT_RATES_FILENAME
    try:
        mtime = path.stat().st_mtime_ns
    except OSError as exc:
        logger.error(
            f"cannot read the VAT rate table at {path}: {exc}. IntelliCharts "
            "publishes it and nothing here creates it, so no rate can be implied "
            "from a VAT figure and those receipts go to Review instead."
        )
        return []
    key = str(path)
    cached = _CACHE.get(key)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    rates = _parse_rates(path)
    _CACHE[key] = (mtime, rates)
    logger.info(f"VAT rate table read: {VAT_RATES_FILENAME}, {len(rates)} rate(s)")
    return rates


def impliable_rates() -> tuple[float, ...]:
    """The rates a positive VAT figure can imply, as a sorted tuple of fractions.

    **The undated rows only, and it is an accounting rule rather than a
    convenience.** Paul's decision, 2026-09-05. An undated row is a rate in force.
    A dated row is a temporary sector relief that applied in a window and does not
    apply now, and a rate that is not in force cannot be implied by a receipt
    being entered today.

    What recognising the 2021-22 hospitality rate would cost is the half worth
    understanding. A receipt showing 90.00 and VAT of 10.00, where the 90.00 is
    genuinely the figure before VAT, implies 10 / (90 - 10) = 12.5%. With 0.125 in
    this set that receipt is silently rewritten to a gross of 90.00 and a net of
    80.00. The true figures are a gross of 100.00 and a net of 90.00, so the
    expense goes in ten pounds light with nothing on screen to say so. Any receipt
    whose VAT is a ninth of the figure does this, and that is not rare.

    Nought is excluded because a nil rate cannot be implied by a positive VAT
    figure. For the table published on 2026-09-05 this returns (0.05, 0.2), from
    `Standard` and `Reduced`, which is what config.VAT_RATES_IMPLIABLE returned
    before it was deleted.
    """
    return tuple(sorted({r.rate for r in load_rates() if r.rate > 0 and not r.is_dated}))

"""A temp CHARTS_DIR for tests that categorise a receipt.

Added 2026-09-05 with the fallback check. Before it, four test files seeded a
learned vendor mapping and asserted the code came out the other end, and none of
them pinned `config.CHARTS_DIR`. Nothing read a chart on that path, so it did not
matter. **The chart check made it matter, and it surfaced the dependency rather
than creating it:** those tests were reading the real bundle out of OneDrive, and
the codes they seed are the legacy three-digit ones amendment 96 retired, so
every one of them failed the moment the suggestion was checked against a chart
holding four-digit codes.

Two things this fixes at once. The tests no longer read OneDrive, which is the
reason `tests/test_chart_bundle.py` and `tests/test_vat_rates.py` both give for
writing their own small files. And they no longer pass or fail depending on
whether the machine running them has a practice root.

The accounts are the tests' own codes, legacy shape included. This fixture holds
whatever the test seeds; it is not a statement about what a real chart contains.
"""

import tempfile
from pathlib import Path

import config
from worker import vat_rates
from worker.categorisation import chart, fallback

# The master chart's 13 columns, in the published order. Written out rather than
# built from a constant, so a column that moves in the bundle is caught by
# test_chart_bundle.py rather than agreeing with itself here.
MASTER_HEADER = (
    "code,name,type,status,applies_to,vat_default,vat_variable,"
    "vat_explanation,vat_recoverability,sa103f_box,mtd_itsa_category,notes,"
    "classifier_eligible"
)

# What the four files seed: 271 through the engine, 999 as an operator's GL
# override. The override is applied after the chart check and is not checked, so
# 999 is here only so a test that seeds it as a suggestion behaves the same way.
DEFAULT_ACCOUNTS = (
    ("271", "Parking and tolls"),
    ("999", "Override account"),
)

# The VAT rate table as published on 2026-09-05, row for row, written by default.
# **Added 2026-09-05 after the live-path sweep**, which found three more files
# reading the real `vat_rates.csv` out of OneDrive: `test_date_disambiguation.py`
# and `test_vat_swap.py` through the extraction path's
# `establish_gross_from_vat()`, and `test_prefer_dayfirst_isolation.py`, which
# re-runs both classes in process and inherited their reads.
#
# **These are the same values the live file gives**, so no test's expected
# figures move. What changes is that a republished table can no longer move them,
# and the suite stops depending on whether OneDrive has finished syncing.
DEFAULT_VAT_RATES = (
    "Standard,20,,",
    "Reduced,5,,",
    "Zero-rated,0,,",
    "Hospitality (2020-21),5,2020-07-15,2021-09-30",
    "Hospitality (2021-22),12.5,2021-10-01,2022-03-31",
    "Family Attractions (2026),5,2026-06-25,2026-09-01",
)
VAT_RATE_HEADER = "name,rate,start,end"


def _row(code, name, status="active", eligible="Yes"):
    return ",".join([
        code, name, "expense", status, "sole_trader",
        "20", "No", "", "recoverable", "17", "other", "", eligible,
    ])


class TempChartBundle:
    """Pins CHARTS_DIR at a temp bundle, and empties the four parse caches.

    Nests inside a fixture that patches other config values: it touches
    `CHARTS_DIR` and nothing else. The caches are restored rather than only
    emptied, so this cannot leave the real bundle's entries missing for a test
    that runs afterwards.

    Writes the master chart and the VAT rate table by default, and the fallback
    table only when a test asks for one, because an absent fallback table is a
    real state the reader has to survive.

    Usable as a context manager or, for a `unittest` fixture with no `with` to
    hang it on, by calling `__enter__()` in `setUp` and `__exit__()` in
    `tearDown`. Both are in use.
    """

    def __init__(self, accounts=DEFAULT_ACCOUNTS, fallbacks=(),
                 vat_rate_rows=DEFAULT_VAT_RATES):
        self._accounts = list(accounts)
        self._fallbacks = list(fallbacks)
        self._vat_rate_rows = list(vat_rate_rows)

    def __enter__(self):
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.path = Path(self._temp.name)
        self._saved_charts_dir = config.CHARTS_DIR
        config.CHARTS_DIR = self.path
        # Four modules cache a parse of a bundle file on its modification time.
        # Named in one tuple so adding a fifth reader is one edit and cannot be
        # half-done: an uncleared cache would hand a test the real bundle's
        # contents from whatever ran before it.
        self._caches = (chart._CACHE, chart._ACCOUNT_CACHE, fallback._CACHE,
                        vat_rates._CACHE)
        self._saved_caches = tuple(dict(c) for c in self._caches)
        for cache in self._caches:
            cache.clear()

        rows = [_row(code, name) for code, name in self._accounts]
        (self.path / config.MASTER_CHART_FILENAME).write_text(
            "\n".join([MASTER_HEADER, *rows]) + "\n", encoding="utf-8"
        )
        if self._fallbacks:
            lines = [f"{code},{target}" for code, target in self._fallbacks]
            (self.path / fallback.FALLBACK_ACCOUNTS_FILENAME).write_text(
                "\n".join(["code,fallback_code", *lines]) + "\n", encoding="utf-8"
            )
        if self._vat_rate_rows:
            (self.path / vat_rates.VAT_RATES_FILENAME).write_text(
                "\n".join([VAT_RATE_HEADER, *self._vat_rate_rows]) + "\n",
                encoding="utf-8",
            )
        return self

    def __exit__(self, *exc):
        config.CHARTS_DIR = self._saved_charts_dir
        for cache, saved in zip(self._caches, self._saved_caches):
            cache.clear()
            cache.update(saved)
        self._temp.cleanup()
        return False

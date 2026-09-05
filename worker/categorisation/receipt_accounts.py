"""The accounts a receipt can be. Intellibills owns this list and ships it.

Sub-step 10j.10, Paul's decision of 2026-09-05, item 152. The reasoning is
`2026-09-05_DESIGN_receipt_accounts.md` and this docstring does not repeat it,
beyond the one line that decides everything here: **a learned vendor mapping is
only worth anything in a vocabulary its owner controls.**

Until this module existed, layer 5 chose from the client's own published chart
through `chart.get_eligible_accounts_for_client()`. "Halfords is vehicle repairs
and servicing" learned against one client's chart is worth nothing to the next
client, whose chart is numbered and named differently. Learned against this list
it is worth something to every client there will ever be.

**This file is not in the bundle and must never be read from one.** It is not
published by IntelliCharts, it is not in `config.CHARTS_DIR`, and it is not in
`IntelliCharts\\`. An Intellibills sold on its own has no IntelliCharts to read,
which is the whole reason the list exists. So the path is package-relative and
**there is deliberately no `config.py` constant for it**: every path in
`config.py` points into the practice root or the unsynced root, and this file is
in neither. It sits beside this module and is versioned in git with the code.

**Why there is no modification-time cache here, when `chart.py`, `vat_rates.py`
and `fallback.py` all have one.** Those three read files IntelliCharts publishes
into a OneDrive folder, which can change under a running pipeline, so each keys
its cache on `st_mtime_ns` and re-reads when the file moves. **This one ships
with the code.** It cannot change while the process runs without the code having
changed, which means a restart. So it is parsed once into a module-level list and
that is the whole cache. Adding an `st_mtime_ns` check would be answering a
question that cannot arise, and it would read as though this file came from
somewhere it does not.

**66 rows as at 2026-09-05**, every one a four-digit master code, seeded from
`COA_MASTER_v2.xlsx` and then frozen. Nothing here asserts the count: the file is
the authority and a test that hardcoded 66 would have to move every time Paul
adds an account.

**The `synonyms` column is empty on all 66 and is not read here.** It is for a
later step, and reading it now would make an empty column look load-bearing.
"""

import csv
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

#: Beside this module, not in any bundle. See the docstring.
RECEIPT_ACCOUNTS_PATH = Path(__file__).with_name("receipt_accounts.csv")

# The columns this module reads. `code` and `name` are the whole of what layer 5
# is offered; the other eight are carried by the file for later steps and are
# deliberately not read, so a change to one of them cannot alter what the
# classifier sees.
REQUIRED_COLUMNS = ("code", "name")

# Parsed once. A list rather than None-as-unset, with a separate flag, so a file
# that genuinely holds no rows is not re-read on every receipt.
_ACCOUNTS: List[Tuple[str, str]] = []
_LOADED = False


def _parse(path: Path) -> List[Tuple[str, str]]:
    """(code, name) for every row. Reads by column name.

    `encoding="utf-8-sig"` because the file carries a byte order mark, and by
    name rather than position for the reason `chart.py` gives: a column added to
    the file must not shift what is read.
    """
    accounts: List[Tuple[str, str]] = []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            logger.error(
                f"{path} is missing the column(s) {', '.join(missing)}, so no account "
                "can be read from it and the classifier will suggest nothing."
            )
            return []
        for row in reader:
            code = (row.get("code") or "").strip()
            name = (row.get("name") or "").strip()
            if code and name:
                accounts.append((code, name))
    return accounts


def load_receipt_accounts() -> List[Tuple[str, str]]:
    """The accounts a receipt can be. Empty list if the file cannot be read.

    Empty rather than an exception, the same shape as `chart.load_chart()`: this
    runs per receipt inside layer 5, and **a missing shipped file is a packaging
    fault and must not stop a receipt being processed.** It is logged at ERROR so
    it is not silent, and the cost is that layer 5 suggests nothing, which is the
    safe direction.

    The failure is cached like a success. A file that is not there on the first
    receipt is not there on the second, and re-reading would log the same ERROR
    once per receipt for the life of the run.
    """
    global _LOADED
    if _LOADED:
        return _ACCOUNTS
    try:
        parsed = _parse(RECEIPT_ACCOUNTS_PATH)
    except OSError as exc:
        logger.error(
            f"cannot read the receipt accounts list at {RECEIPT_ACCOUNTS_PATH}: {exc}. "
            "It ships with the code and nothing creates it at run time, so this is a "
            "packaging fault and the classifier will suggest nothing."
        )
        parsed = []
    _ACCOUNTS[:] = parsed
    _LOADED = True
    logger.info(
        f"receipt accounts read: {RECEIPT_ACCOUNTS_PATH.name}, {len(_ACCOUNTS)} account(s)"
    )
    return _ACCOUNTS

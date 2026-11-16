r"""Capital items: whether a purchase layer 5 called capital is referred to Paul.

Outstanding item 55, Paul's decisions of 2026-11-16. **His order is the design:**

1. Does it look capital? Layer 5 answers, as `CategorisationResult.looks_capital`.
2. If so, is the gross at or above the threshold?
3. Only below the threshold is the expense account layer 5 named used.

At or above, the receipt is **referred to Paul and never posted by the system**.
Below, it is categorised as the ordinary expense layer 5 chose from the 66. **No
capital account is ever offered to the classifier as a choice**, and nothing here
falls back to `0061`: a purchase under the threshold was never an asset.

**The accounting method is not consulted.** Paul, 2026-11-16: QuickBooks can
switch a report between the cash and accruals bases and back, which it could not
do if an asset had been posted to expenses. The tax treatment is a separate
question.

Two callers, the poll in `process_extraction_result()` and the recovery sweep in
`app.py`, because both run layer 5 and both publish.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

import config

logger = logging.getLogger(__name__)

#: The key on a client record and on the firm record. Desktop writes both: the
#: client's on Client Settings, the firm's default on Firm Settings. Amendment
#: 349, 2026-09-12; restated by Paul on 2026-11-16 at £50.
THRESHOLD_FIELD = "capitalisation_threshold"

#: How a referral's note begins. "Capital item" is Paul's term, 2026-11-16.
NOTE_PREFIX = "capital item"


def _as_threshold(value: Any) -> Optional[float]:
    """A threshold, or None if `value` is not one.

    **A bool is refused before the numeric check**, because `bool` is an `int` in
    Python, so `true` on a record would otherwise read as a threshold of £1.
    Negative and non-finite numbers are refused for Desktop's reason: its own
    guard accepts only a number of £0 or more.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value < 0:
        return None
    return float(value)


def threshold_for(client_id: str) -> Optional[float]:
    """The client's threshold where it has one, the firm's otherwise, or None.

    The rule is Desktop's `clientThresholdDisplayValue()`: the client's own value
    unless it is null or absent, then the firm default. **Null is a stated "use
    the firm default"** and absent is a client nobody has saved Client Settings
    for; both read the firm's.

    **A client value that is present and is not a threshold is not passed over
    to the firm's.** Somebody wrote a figure for this client and it cannot be
    read, so there is no threshold for it, logged at ERROR. The caller refers on
    None, so the receipt reaches Paul rather than being posted against a
    threshold nobody chose.
    """
    client = config.CLIENTS_BY_ID.get(client_id) or {}
    raw = client.get(THRESHOLD_FIELD)
    if raw is not None:
        value = _as_threshold(raw)
        if value is None:
            logger.error(
                f"client {client_id} has {THRESHOLD_FIELD} {raw!r}, which is not a "
                "number of 0 or more, so no threshold applies and a capital "
                "purchase is referred")
        return value

    firm_id = client.get("firm_id")
    firm = config.FIRMS.get(firm_id) or {}
    raw = firm.get(THRESHOLD_FIELD)
    value = _as_threshold(raw)
    if value is None:
        logger.warning(
            f"firm {firm_id} has no usable {THRESHOLD_FIELD} ({raw!r}) and client "
            f"{client_id} has none of its own, so a capital purchase is referred")
    return value


def referral_for(categorisation, gross: Optional[float],
                 client_id: str) -> Optional[dict]:
    """The referral for this receipt, or None to categorise it as usual.

    **At or above the threshold is referred**, so a purchase of exactly the
    threshold reaches Paul. Of the two ways the boundary could be wrong, posting
    an asset as an expense is the one Paul said must never happen, and a referral
    costs a look.

    No threshold, or no gross, refers too, for the same reason.

    The dict is what is published as `publish.CAPITAL_ITEM_KEY`: the gross and
    the threshold it was compared with, the latter None where there was none.
    """
    if categorisation is None or not categorisation.looks_capital:
        return None
    threshold = threshold_for(client_id)
    if threshold is not None and gross is not None and gross < threshold:
        logger.info(
            f"receipt {categorisation.receipt_id} looks capital but its gross "
            f"{gross} is under the threshold {threshold}, so it is categorised "
            f"as {categorisation.suggested_code}")
        return None
    return {"gross": gross, "threshold": threshold}


def note_for(referral: dict) -> str:
    """The receipt's note, starting with Paul's term."""
    gross, threshold = referral["gross"], referral["threshold"]
    if threshold is None:
        why = "no capitalisation threshold is set for this client or the firm"
    elif gross is None:
        why = f"the gross could not be read to compare with the threshold of {threshold:.2f}"
    else:
        why = f"the gross of {gross:.2f} is at or above the threshold of {threshold:.2f}"
    return (f"{NOTE_PREFIX}: the classifier judged this a capital purchase and {why}. "
            "Referred, not posted")

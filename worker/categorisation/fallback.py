"""The published fallback table, and the check that uses it.

Two halves, and they are separable on purpose. The first is a reader for
`fallback_accounts.csv`, modelled on `worker/vat_rates.py`, which was in turn
modelled on `worker/categorisation/chart.py`: `config.CHARTS_DIR`, a cache keyed
on the file's modification time so a file in OneDrive is not re-read once per
receipt, and an empty result with an ERROR rather than an exception when it
cannot be read. The second is `resolve_against_chart()`, which decides what to do
with a suggested code the client's chart does not hold.

**Why a fallback exists at all.** A library chart is a subset of the master, so
the account a layer returns is often not in the client's chart. Counted from the
eight library charts on 2026-09-05, against the 66 accounts a receipt can be:
PHV_DRIVER holds 30, FIN_ADVISER 40, SALE_OF_SERVICES 44, SALE_OF_GOODS 49. **An
absent account is the ordinary case, not the edge one.**

Paul's ruling, 2026-09-05: a car wash goes to `7310 Vehicle repairs and
servicing` where the client's chart does not hold `7391 Car wash`. That is an
accounting fact about the account, so it is recorded per account in the published
table rather than guessed at run time.

**Nothing here re-validates the file.** `validate_fallbacks()` in
`publish_master.py` blocks the publish unless every non-blank target exists in the
master, is not the account itself, is `status = active`, and does not itself carry
a fallback. **One hop only, so there is no chain to walk here and no cycle to
detect.** Duplicating any of those rules would be the two-copies fault in a new
place. A file that did not come from `publish_master.py` is not trusted either
way: a row with no code or no target is skipped, and a file with no `code` column
loses every row that way and yields no fallback, which routes receipts to Review.

**A blank is not in the file.** Only accounts that have a fallback appear, so an
account absent from it has no fallback, and that means Review.

**Why this is not yet reachable in production, which is expected.** Layer 5
chooses from the client's published chart, so its answer is already in that chart.
Layers 0 to 4 return whatever was learned, which may be an account this client's
chart does not hold, and all four learned tables hold 0 rows. It becomes live at
sub-step 10j.10, when layer 5 starts choosing from the 66 receipt accounts
instead of from the client's chart.

The flow is one way. IntelliCharts publishes in; nothing here ever writes into the
bundle.
"""

import csv
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import config

from .chart import get_chart_accounts_for_client

logger = logging.getLogger(__name__)

# Published by publish_master.py into the same bundle as the charts.
FALLBACK_ACCOUNTS_FILENAME = "fallback_accounts.csv"

# The actor and source written on the audit row. Paul's decision, 2026-09-05:
# nothing that means "a person did this" is written by a machine, so the
# substitution is an event of its own rather than a value in the correction
# columns of `categorisations`. See the module note on record_substitution().
EVENT_ACTOR = "pipeline"
EVENT_SOURCE = "categorisation"
EVENT_ACTION = "chart_fallback"

# Parsed tables, keyed on the file's full path, valued (st_mtime_ns, mapping).
# The same arrangement chart.py and vat_rates.py use, and
# config.reload_clients_if_changed() before them: the modification time decides,
# not a timer and not a process lifetime.
_CACHE: dict[str, tuple[int, dict[str, str]]] = {}


def _parse_fallbacks(path) -> dict[str, str]:
    """{code: fallback_code} for every row that carries both. Reads by name.

    A row missing either value is skipped without an ERROR, because the published
    file cannot contain one: `write_fallbacks_csv()` writes only the accounts that
    have a fallback. It is skipped rather than raising so a hand-edited file
    costs its own row and not the whole table.
    """
    fallbacks: dict[str, str] = {}
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            code = (row.get("code") or "").strip()
            target = (row.get("fallback_code") or "").strip()
            if code and target:
                fallbacks[code] = target
    return fallbacks


def load_fallbacks() -> dict[str, str]:
    """The published fallback table. Empty dict if it cannot be read.

    Empty rather than an exception: this runs on the categorisation path, and a
    bundle that has not been published must cost a receipt its fallback, not stop
    the receipt being processed. It is logged at ERROR so it is not silent. What
    the empty case costs is a suggestion outside the client's chart reaching
    Review with no code, which is the safe direction.
    """
    path = config.CHARTS_DIR / FALLBACK_ACCOUNTS_FILENAME
    try:
        mtime = path.stat().st_mtime_ns
    except OSError as exc:
        logger.error(
            f"cannot read the fallback table at {path}: {exc}. IntelliCharts "
            "publishes it and nothing here creates it, so an account outside the "
            "client's chart has no fallback and the receipt goes to Review."
        )
        return {}
    key = str(path)
    cached = _CACHE.get(key)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    fallbacks = _parse_fallbacks(path)
    _CACHE[key] = (mtime, fallbacks)
    logger.info(
        f"fallback table read: {FALLBACK_ACCOUNTS_FILENAME}, {len(fallbacks)} account(s)"
    )
    return fallbacks


def fallback_for(code: str) -> Optional[str]:
    """The fallback account for one code, or None where it has none.

    One hop and never two. `publish_master.py` refuses to publish a target that
    itself carries a fallback, so there is no chain here to walk, and walking one
    would find a target it had already refused.
    """
    if not code:
        return None
    return load_fallbacks().get(code.strip()) or None


def _record_substitution(repo, result, outcome: str, gl_override_code, reason: str):
    """One audit row for a chart check that changed the answer.

    **Paul's decision, 2026-09-05, and the reason is worth keeping.** Three
    places could have carried this. `make_enriched_sidecar()` is frozen by design
    document 18.2b and sub-step 10d.14, so no key was added to the sidecar. A new
    column on `categorisations` would exist only in a database created after this
    change, because there is no `ALTER TABLE` anywhere in this repository and
    `schema.py` only creates. That left the `categorisations` correction columns
    and this table, and the correction columns mean "a person changed it": a
    machine writing `corrected_at` makes a substitution indistinguishable from an
    operator's correction except by reading the reason text.

    So the substitution is an event, with `actor` "pipeline" saying plainly that
    no person did it. `resolution_events` has no foreign key on either id, which
    is why an audit row can always be written; `schema.py` records that reason.

    A missing repo is not an error. `retroactive_categorise.py` and the tests can
    both call the check without one, and the WARNING in the caller still names
    the receipt and the swap.
    """
    if repo is None:
        return
    repo.save_resolution_event(
        event_id=str(uuid.uuid4()),
        receipt_id=result.receipt_id,
        extraction_id=result.extraction_id,
        actor=EVENT_ACTOR,
        source=EVENT_SOURCE,
        action=EVENT_ACTION,
        outcome=outcome,
        corrections_json=json.dumps({
            "match_source": result.match_source,
            "suggested_code": result.original_code,
            "suggested_name": result.original_name,
            "resolved_code": result.suggested_code,
            "resolved_name": result.suggested_name,
        }),
        gl_override_code=gl_override_code,
        reason=reason,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def resolve_against_chart(result, repo=None):
    """Check a categorisation's code against the client's chart, and act on it.

    Runs after `categorise()` has returned and before the code reaches a sidecar
    or a `categorisations` row. Five outcomes, and only two of them write an
    audit row because only two of them change the answer:

    - `no_code`. Nothing was suggested, so there is nothing to check. This is the
      `unmatched` case and it already reaches Review on its own.
    - `unreadable_chart`. The client's chart came back empty, which means it
      could not be read and **not that the chart holds nothing**. The suggestion
      is left exactly as it was. Stripping every code on an unpublished bundle
      would put every receipt in the practice into Review at once, and an empty
      read is not evidence of absence.
    - `in_chart`. The ordinary case. Untouched.
    - `substituted`. The chart does not hold the code, the published table gives
      a fallback, and the chart holds the fallback. The fallback becomes the
      suggestion, because the sidecar and the books need an account the client
      actually has, and the original is kept on the result and in the audit row.
    - `unusable`. The chart does not hold the code and there is no usable
      fallback, either because the account has none or because the chart does not
      hold the fallback either. **No code, `needs_review`, confidence `none`**,
      and the note names the account that was suggested and why it could not be
      used.

    **`match_source` is left alone in every case, including `unusable`.** It says
    which layer answered, and a layer did answer; overwriting it with `unmatched`
    would record that nothing matched, which is untrue and would lose the only
    record of which layer produced an unusable code. `confidence` is left alone
    on a substitution too: Paul's ruling makes the fallback an accounting fact
    about the account, so a substituted receipt is not a less certain one.

    Returns the same object, mutated. It is a dataclass the caller has just been
    handed and does not share, so a copy would only invite the two-object fault
    where one is written to the database and the other to the sidecar.
    """
    code = (result.suggested_code or "").strip()
    if not code:
        result.chart_outcome = "no_code"
        return result

    accounts = get_chart_accounts_for_client(result.client_id)
    if not accounts:
        # Already logged at ERROR by chart.load_accounts(). Said again here
        # because the consequence belongs with the decision: the check did not
        # run, so the code stands unchecked rather than being stripped.
        result.chart_outcome = "unreadable_chart"
        result.chart_note = (
            f"{code} was not checked against client {result.client_id}'s chart: "
            "the chart could not be read, so the suggestion stands unchecked."
        )
        logger.error(result.chart_note)
        return result

    if code in accounts:
        result.chart_outcome = "in_chart"
        return result

    result.original_code = code
    result.original_name = result.suggested_name
    target = fallback_for(code)

    if target and target in accounts:
        result.suggested_code = target
        result.suggested_name = accounts[target]
        result.chart_outcome = "substituted"
        result.chart_note = (
            f"{code} {result.original_name or ''}".strip()
            + f" is not in client {result.client_id}'s chart; "
            f"{FALLBACK_ACCOUNTS_FILENAME} gives {target} {accounts[target]}."
        )
        logger.warning(
            f"receipt {result.receipt_id}: {result.chart_note} "
            f"Substituted from match_source {result.match_source}."
        )
        _record_substitution(repo, result, "substituted", target, result.chart_note)
        return result

    if target:
        why = (
            f"{FALLBACK_ACCOUNTS_FILENAME} gives {target}, which is not in that "
            "chart either"
        )
    else:
        why = f"{FALLBACK_ACCOUNTS_FILENAME} gives it no fallback"
    result.suggested_code = None
    result.suggested_name = None
    result.confidence = "none"
    result.needs_review = True
    result.chart_outcome = "unusable"
    result.chart_note = (
        f"{code} {result.original_name or ''}".strip()
        + f" is not in client {result.client_id}'s chart and {why}, "
        "so the receipt has no account and goes to Review."
    )
    logger.warning(f"receipt {result.receipt_id}: {result.chart_note}")
    _record_substitution(repo, result, "unusable", None, result.chart_note)
    return result

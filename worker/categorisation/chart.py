"""The client's published chart of accounts, read from the Intellibills bundle.

Replaces `coa.py`, deleted 2026-09-04. That module held 21, 15 and 7 hardcoded
four-digit accounts under three business-type keys. None of those codes belongs to
any chart in the IntelliCharts library and none of them is translatable to one,
so there was nothing to migrate.

What this module does instead. `publish_master.py` in the IntelliCharts folder writes one
identical bundle per product; ours is `config.CHARTS_DIR`, and IntelliBooks' copy
of the same content is not ours to read. This module reads the one chart a client
is on and returns the accounts the classifier may propose from it.

Two filters, and both are required:

- `classifier_eligible == "Yes"`. It marks the accounts the classifier may
  propose. **It is not a rule about what a person may post**, so nothing outside
  layer 5 may use this list to decide what to offer anyone.
- `status == "active"`. Every row in today's bundle is active, so this filter
  currently removes nothing. It is here because the column exists and a retired
  account must not be proposed the day one appears.

The flow is one way. IntelliCharts publishes in; nothing here ever writes into the
bundle.
"""

import csv
import logging

import config

logger = logging.getLogger(__name__)

# The chart_code chart_library.csv gives the master chart. It is the one code
# whose file is not named "{chart_code}.csv", so it is resolved rather than
# formatted; see config.MASTER_CHART_FILENAME.
MASTER_CHART_CODE = "MASTER"

# The columns this module reads. A bundle file missing any of them is a publish
# fault: publish_master.py refuses to publish a chart whose classifier_eligible is
# blank on any row, so an absent column means the file did not come from it.
REQUIRED_COLUMNS = ("code", "name", "status", "classifier_eligible")

# Parsed charts, keyed on the file's full path, valued (st_mtime_ns, accounts).
# A chart must not be re-read from OneDrive once per receipt, so this is the same
# arrangement config.reload_clients_if_changed() uses for the registry at 10d.35:
# the modification time decides, not a timer and not a process lifetime.
_CACHE: dict[str, tuple[int, list[tuple[str, str]]]] = {}


def chart_filename(chart_code: str) -> str:
    """The bundle filename for a chart_code. Master_COA.csv for MASTER."""
    if chart_code.strip().upper() == MASTER_CHART_CODE:
        return config.MASTER_CHART_FILENAME
    return f"{chart_code.strip()}.csv"


def _parse_chart(path) -> list[tuple[str, str]]:
    """(code, name) for every eligible, active row. Reads by column name.

    By name and not by position, because Master_COA.csv has 13 columns and the
    eight industry and general charts have 14: they carry a leading `chart_code`
    and the master does not.
    """
    accounts: list[tuple[str, str]] = []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            logger.error(
                f"{path} is missing the column(s) {', '.join(missing)}, so no account "
                "can be read from it. It did not come from publish_master.py."
            )
            return []
        for row in reader:
            if (row.get("classifier_eligible") or "").strip() != "Yes":
                continue
            if (row.get("status") or "").strip() != "active":
                continue
            code = (row.get("code") or "").strip()
            name = (row.get("name") or "").strip()
            if code and name:
                accounts.append((code, name))
    return accounts


def load_chart(filename: str) -> list[tuple[str, str]]:
    """The eligible accounts in one bundle file. Empty list if it cannot be read.

    Empty rather than an exception: this runs per receipt inside layer 5, and a
    bundle that has not been published must stop the classifier suggesting, not
    stop the receipt being processed. It is logged at ERROR so it is not silent.
    """
    path = config.CHARTS_DIR / filename
    try:
        mtime = path.stat().st_mtime_ns
    except OSError as exc:
        logger.error(
            f"cannot read the chart bundle at {path}: {exc}. IntelliCharts publishes "
            "it and nothing here creates it, so the classifier will suggest nothing."
        )
        return []
    key = str(path)
    cached = _CACHE.get(key)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    accounts = _parse_chart(path)
    _CACHE[key] = (mtime, accounts)
    logger.info(f"chart read: {filename}, {len(accounts)} classifier-eligible account(s)")
    return accounts


def get_eligible_accounts_for_client(client_id: str) -> list[tuple[str, str]]:
    """The accounts the classifier may propose for one client.

    `chart_code` on the client's record in clients.json says which chart. It is
    absent from all five records today, and IntelliBooks writes it in a change
    made separately, so the fall back to the master chart is the normal case for
    now and is logged at WARNING naming the client. Not silent, and not an error.

    A chart_code naming a file that is not in the bundle falls back the same way,
    also at WARNING. That is a registry problem, not a receipt problem.
    """
    record = config.CLIENTS_BY_ID.get(client_id) or {}
    chart_code = (record.get("chart_code") or "").strip()
    if not chart_code:
        logger.warning(
            f"client {client_id} has no chart_code in {config.CLIENTS_JSON.name}; "
            f"the classifier is using {config.MASTER_CHART_FILENAME} instead."
        )
        return load_chart(config.MASTER_CHART_FILENAME)
    filename = chart_filename(chart_code)
    if not (config.CHARTS_DIR / filename).is_file():
        logger.warning(
            f"client {client_id} names chart_code {chart_code!r}, and {filename} is "
            f"not in {config.CHARTS_DIR}; the classifier is using "
            f"{config.MASTER_CHART_FILENAME} instead."
        )
        return load_chart(config.MASTER_CHART_FILENAME)
    return load_chart(filename)

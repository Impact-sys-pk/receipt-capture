"""Publish each client's taught supplier mappings. Sub-step 10bs.10, pipeline half.

Amendment 554 of `2026-07-25_CONSOLE_DESIGN.md`, Paul's decision of 2026-11-13,
option A of three: the pipeline publishes the client's taught mappings so
IntelliBooks Desktop can show them at the moment the operator ticks Remember.

**Why it is needed.** Sub-step 10bs.9 made layer 1 match on the supplier name
first and fall back to the key only where every name on the key carries the
same code. So two names that are one supplier need either a row each or
agreeing rows, and the operator can only keep them agreeing if they can see
the other names. The mappings are in `receipts.db`, which Desktop never reads.

**What it writes.** `config.SUPPLIER_MAPPINGS_DIR / f"{client_id}{SUFFIX}"`, for
every client in the registry, holding that client's rows of
`categorisations_client_vendors` exactly as stored. Every key is a constant in
`config.py`. A client with no mappings gets a file with an empty list, so the
reader can tell "nothing taught" from "nothing published".

**When.** Once a poll, after the resolution notes, which is the only place a
poll teaches. A file is written only where it is missing, unreadable or
different from the database, so an unchanged set never touches OneDrive. A
mapping taught from the CLI or the console between polls reaches the file on
the next poll by the same comparison.

**What it never does.** It teaches nothing, merges nothing, trims nothing and
folds no case. A mapping is changed or deleted by `worker/mapping_notes.py`,
flag F2 of step 10bu, and never here. Comparing names is the reader's, and saying two names are one
supplier is the operator's. It never stops a poll: a failed write is logged and
the next poll tries again.

**The firm pool is not published.** That is Paul's decision and it is open.
The one exception is per mapping: where the firm pool answers this client's
supplier name with a different code, that code and its account name sit on the
mapping. Flag H2, Paul's decision of 2026-11-14. A firm row with no client
mapping beside it appears nowhere.
"""

import json
import logging
import os
import uuid

import config

logger = logging.getLogger(__name__)


def write_atomically(path, payload) -> None:
    """A part file in the same folder, forced to disk, then `os.replace()`.

    The method of `write_item()` in `worker/publish.py`, so Desktop never reads
    half a file and a rewrite lands on one file rather than failing on Windows.
    **Not a call to it**: `tests/test_publish_trigger.py` holds that the item
    writer is reached only through `publish_receipt()`, so that nothing writes
    a publish item without recording it, and this file is not a publish item.
    ASCII on disk for that function's reason: a supplier name crosses to a
    product built by a session that cannot see this one.
    """
    partial = path.with_name(f"{path.name}.{uuid.uuid4().hex}.part")
    try:
        with open(partial, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True, indent=1))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(partial, path)
    except BaseException:
        try:
            partial.unlink()
        except OSError:
            logger.warning("could not remove the part file %s", partial)
        raise


def _firm_pool_disagreement(repo, sector, row) -> tuple:
    """(code, account name) where layer 2 answers this supplier name with a
    different code, else (None, None). Flag H2, Paul's decision of 2026-11-14.

    **`get_firm_vendor()` and not a query of its own**, so this cannot drift
    from what layer 2 does: the exact name first, then the key where every
    name on it agrees. Reads only; nothing here writes the firm pool.
    """
    firm = repo.get_firm_vendor(sector, row["vendor_key"], row["vendor_name"])
    if firm is None or firm["nominal_code"] == row["nominal_code"]:
        return None, None
    return firm["nominal_code"], firm["account_name"]


def payload_for(repo, client_id: str) -> dict:
    """The file's content for one client, built only from the database."""
    # The client's sector, as the engine takes it at layer 2.
    sector = (config.CLIENTS_BY_ID.get(client_id) or {}).get("sector") or config.UNSPECIFIED_SECTOR
    mappings = []
    for row in repo.list_client_vendor_mappings(client_id):
        firm_code, firm_name = _firm_pool_disagreement(repo, sector, row)
        mappings.append({
            # Flag F2, 2026-11-14: so Desktop can name one row to change or
            # delete. See config.MAPPING_ID_FIELD for why not the name.
            config.MAPPING_ID_FIELD: row["mapping_id"],
            config.MAPPING_VENDOR_KEY_FIELD: row["vendor_key"],
            config.MAPPING_VENDOR_NAME_FIELD: row["vendor_name"],
            config.MAPPING_NOMINAL_CODE_FIELD: row["nominal_code"],
            config.MAPPING_ACCOUNT_NAME_FIELD: row["account_name"],
            config.MAPPING_TIMES_SEEN_FIELD: row["times_seen"],
            config.MAPPING_LAST_UPDATED_FIELD: row["last_updated"],
            # Flag H2: null unless the firm pool answers this name differently.
            config.MAPPING_FIRM_POOL_CODE_FIELD: firm_code,
            config.MAPPING_FIRM_POOL_ACCOUNT_NAME_FIELD: firm_name,
        })
    return {
        config.MAPPINGS_SCHEMA_FIELD: config.SUPPLIER_MAPPINGS_SCHEMA,
        config.MAPPINGS_CLIENT_ID_FIELD: client_id,
        config.MAPPINGS_LIST_FIELD: mappings,
    }


def on_disk(path):
    """What the file holds now, or None where it is missing or unreadable.

    Public, and was `_on_disk()` until flag F10 of 2026-11-14:
    `worker/receipt_rules.py` publishes by the same method and imports it.
    """
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def publish_client(repo, client_id: str) -> bool:
    """Write one client's file if it differs from the database. True if written.

    Compared as parsed JSON rather than as bytes, so a file a person reformatted
    but did not change is left alone, and one they did change is put back.
    """
    payload = payload_for(repo, client_id)
    path = config.SUPPLIER_MAPPINGS_DIR / f"{client_id}{config.SUPPLIER_MAPPINGS_SUFFIX}"
    if on_disk(path) == payload:
        return False
    config.SUPPLIER_MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
    write_atomically(path, payload)
    logger.info("published %d supplier mapping(s) for %s to %s",
                len(payload[config.MAPPINGS_LIST_FIELD]), client_id, path)
    return True


def publish_all(repo) -> int:
    """Bring every registered client's file up to date. Returns how many were written.

    The registry is `config.CLIENTS_BY_ID`, so `UNKNOWN`, which is a reserved id
    and not a client, is never published, and neither is a client id that has
    rows but no registry record.
    """
    written = 0
    for client_id in sorted(config.CLIENTS_BY_ID):
        try:
            if publish_client(repo, client_id):
                written += 1
        except Exception as exc:
            logger.warning(
                "could not publish the supplier mappings for %s: %s. Nothing is "
                "lost: the database holds them and the next poll tries again",
                client_id, exc)
    return written

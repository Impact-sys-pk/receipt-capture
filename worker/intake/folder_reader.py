import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config
from worker.storage.store import is_supported, compute_hash

logger = logging.getLogger(__name__)

SIDE_CAR_EXT = ".json"
INTAKE_PATTERN = "rcpt_"
STATEMENT_PREFIX = "stmt_"

# receipts.source has four values and no others. Sub-step 10d.40. `capture` was a
# fifth and was hardcoded here; it is retired. Each writer declares its own word:
# the phone app writes `phone`, Add Receipts writes `desktop`, the email path
# writes `email`, and anything the pipeline cannot attribute to a writer is
# `other`.
EMAIL_SOURCE = "email"
PHONE_SOURCE = "phone"
DESKTOP_SOURCE = "desktop"
OTHER_SOURCE = "other"
INTAKE_SOURCES = (EMAIL_SOURCE, PHONE_SOURCE, DESKTOP_SOURCE, OTHER_SOURCE)


class IntakeRecord:
    def __init__(
        self,
        source: str,
        client_id: str | None,
        firm_id: str | None,
        source_path: Path,
        filename: str,
        file_hash: str,
        sidecar_path: Path | None,
        sidecar: dict[str, Any] | None,
        original_name: str,
        is_statement: bool,
        statement_metadata: dict[str, Any] | None,
        internal_path: Path | None = None,
    ):
        self.source = source
        self.client_id = client_id
        self.firm_id = firm_id
        self.source_path = source_path
        self.filename = filename
        self.file_hash = file_hash
        self.sidecar_path = sidecar_path
        self.sidecar = sidecar
        self.original_name = original_name
        self.is_statement = is_statement
        self.statement_metadata = statement_metadata or {}
        self.internal_path = internal_path


def _load_sidecar(sidecar_path: Path) -> dict[str, Any] | None:
    try:
        with sidecar_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("sidecar payload is not an object")
            return data
    except Exception as exc:
        logger.warning(f"Failed to load sidecar {sidecar_path}: {exc}")
        return None


def _find_sidecar_for_file(file_path: Path) -> Path | None:
    candidate = file_path.with_suffix(SIDE_CAR_EXT)
    if candidate.exists():
        return candidate
    return None


def scan_inbox() -> list[IntakeRecord]:
    """Read the Receipt Inbox. The client comes out of the sidecar, never the folder.

    Sub-step 10d.11. The folder name under Receipt Inbox is decoration: it is
    there so a person can see whose inbox they are looking at, and nothing reads
    it. It used to be the client code, resolved through CLIENTS_BY_CODE with a
    silent fallback, which is how a receipt could be attributed to a client that
    was not in the registry at all.

    A file with no sidecar therefore has no client. It gets `source = other` and
    no client_id, and app.py routes it to Review per 10d.16 and 10d.18. It is
    kept and reported, never refused: the file is somebody's receipt whatever
    the pipeline can work out about it.

    A sidecar naming a client_id the registry does not hold is the same case. It
    is logged, because that is a registry problem rather than a receipt problem,
    and it still goes to Review rather than being attributed to anybody.
    """
    intake_records: list[IntakeRecord] = []
    inbox_root = config.RECEIPT_INBOX_ROOT

    if not inbox_root.exists():
        logger.info(f"Receipt inbox root does not exist: {inbox_root}")
        return intake_records

    for client_dir in sorted(p for p in inbox_root.iterdir() if p.is_dir()):
        for item in sorted(client_dir.iterdir()):
            if item.is_dir():
                continue
            if item.suffix.lower() == SIDE_CAR_EXT:
                continue
            if not is_supported(item.name):
                logger.info(f"Skipping unsupported inbox file: {item}")
                continue

            sidecar_path = _find_sidecar_for_file(item)
            sidecar = _load_sidecar(sidecar_path) if sidecar_path else None
            file_hash = compute_hash(item.read_bytes())
            original_name = item.name
            is_statement = bool(sidecar and sidecar.get("type") == "statement")
            statement_metadata = {}

            if is_statement:
                statement_metadata = {
                    "platform": sidecar.get("platform"),
                    "week_ending": sidecar.get("week_ending"),
                    "type": sidecar.get("type"),
                }

            client_id, firm_id, source = _resolve_from_sidecar(sidecar, item)

            intake_records.append(IntakeRecord(
                source=source,
                client_id=client_id,
                firm_id=firm_id,
                source_path=item,
                filename=item.name,
                file_hash=file_hash,
                sidecar_path=sidecar_path,
                sidecar=sidecar,
                original_name=original_name,
                is_statement=is_statement,
                statement_metadata=statement_metadata,
            ))

    return intake_records


def _resolve_from_sidecar(sidecar, item) -> tuple[str | None, str | None, str]:
    """(client_id, firm_id, source) for one inbox item. None means unresolved.

    Sub-steps 10d.11, 10d.19 and 10d.40. The firm comes off the resolved client
    record and is never DEFAULT_FIRM_ID: an item whose client cannot be resolved
    has no firm either, and saying otherwise is what put unattributable receipts
    into a real firm's records.

    `source` is one of the four words of 10d.40 and comes off the sidecar, which
    is what the writer declared. Anything else, including no sidecar at all, is
    `other`.
    """
    declared_source = (sidecar or {}).get("source")
    source = declared_source if declared_source in INTAKE_SOURCES else OTHER_SOURCE
    if sidecar and declared_source and declared_source not in INTAKE_SOURCES:
        logger.warning(
            f"inbox sidecar for {item.name} declares source {declared_source!r}, which is not one "
            f"of {INTAKE_SOURCES}; recording it as {OTHER_SOURCE!r}"
        )

    if not sidecar:
        logger.info(f"inbox file with no sidecar, so no client: {item}")
        return None, None, OTHER_SOURCE

    client_id = sidecar.get("client_id")
    if isinstance(client_id, str):
        client_id = client_id.strip()
    if not client_id:
        logger.info(f"inbox sidecar carries no client_id, so no client: {item}")
        return None, None, source

    client = config.CLIENTS_BY_ID.get(client_id)
    if not client:
        logger.warning(
            f"inbox sidecar for {item.name} names client_id {client_id!r}, which is not in "
            f"{config.CLIENTS_JSON.name}; routing it to Review rather than attributing it"
        )
        return None, None, source

    return client_id, client["firm_id"], source

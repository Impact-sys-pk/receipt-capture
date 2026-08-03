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


class IntakeRecord:
    def __init__(
        self,
        source: str,
        client_code: str,
        client_id: str,
        firm_id: str,
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
        self.client_code = client_code
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


def _format_client_code(code: str) -> str:
    return code.strip().upper()


def scan_inbox() -> list[IntakeRecord]:
    intake_records: list[IntakeRecord] = []
    inbox_root = config.RECEIPT_INBOX_ROOT

    if not inbox_root.exists():
        logger.info(f"Receipt inbox root does not exist: {inbox_root}")
        return intake_records

    for client_dir in sorted(p for p in inbox_root.iterdir() if p.is_dir()):
        client_code = _format_client_code(client_dir.name)
        client = config.CLIENTS_BY_CODE.get(client_code)
        if client:
            client_id = client["client_id"]
            firm_id = client["firm_id"]
        else:
            client_id = "UNKNOWN"
            firm_id = config.DEFAULT_FIRM_ID

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

            intake_records.append(IntakeRecord(
                source="capture",
                client_code=client_code,
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

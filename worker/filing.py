import json
import logging
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger(__name__)

INVALID_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9 _.-]")


def determine_tax_year(date_str: str) -> str:
    dt = datetime.fromisoformat(date_str)
    if dt.month > 4 or (dt.month == 4 and dt.day >= 6):
        start = dt.year
        end = dt.year + 1
    else:
        start = dt.year - 1
        end = dt.year
    return f"{start}-{str(end)[-2:]}"


def normalise_supplier(supplier: str) -> str:
    if not supplier:
        return "unknown"
    text = supplier.strip()
    text = INVALID_FILENAME_CHARS.sub("", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-._ ").lower()
    return text or "unknown"


def normalise_client_name(client_name: str, client_code: str) -> str:
    name = client_name.strip() if client_name else client_code
    name = INVALID_FILENAME_CHARS.sub("", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or client_code


def _unique_path(directory: Path, base_name: str, suffix: str) -> Path:
    destination = directory / f"{base_name}{suffix}"
    if not destination.exists():
        return destination

    index = 2
    while True:
        destination = directory / f"{base_name}-{index}{suffix}"
        if not destination.exists():
            return destination
        index += 1


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def get_client_directory(client_name: str) -> Path:
    return config.CLIENTS_ROOT / client_name


def file_receipt(
    source_file: Path,
    client_name: str,
    tax_year: str,
    supplier: str,
    gross: float,
    original_filename: str,
    enriched_sidecar: dict[str, Any],
) -> tuple[Path, Path]:
    client_dir = get_client_directory(client_name)
    destination_dir = client_dir / "Receipts" / tax_year
    destination_dir.mkdir(parents=True, exist_ok=True)

    ext = source_file.suffix
    supplier_safe = normalise_supplier(supplier)
    gross_text = f"{gross:.2f}"
    base_name = f"{enriched_sidecar['invoice_date']}_{supplier_safe}_{gross_text}"
    dest_image = _unique_path(destination_dir, base_name, ext)
    dest_sidecar = dest_image.with_suffix(dest_image.suffix + ".json")

    shutil.copy2(source_file, dest_image)
    _write_json(dest_sidecar, enriched_sidecar)
    return dest_image, dest_sidecar


def file_statement(
    source_file: Path,
    client_name: str,
    tax_year: str,
    platform: str,
    week_ending: str,
    original_extension: str,
    enriched_sidecar: dict[str, Any],
) -> tuple[Path, Path]:
    client_dir = get_client_directory(client_name)
    destination_dir = client_dir / "Statements" / tax_year / platform
    destination_dir.mkdir(parents=True, exist_ok=True)

    ext = original_extension if original_extension.startswith(".") else f".{original_extension}"
    base_name = f"{platform}_{week_ending}"
    dest_file = _unique_path(destination_dir, base_name, ext)
    dest_sidecar = dest_file.with_suffix(dest_file.suffix + ".json")

    shutil.copy2(source_file, dest_file)
    _write_json(dest_sidecar, enriched_sidecar)
    return dest_file, dest_sidecar


def file_review(
    source_file: Path,
    client_name: str,
    original_filename: str,
    status: str,
    reasons: list[str],
    extracted_values: dict[str, Any],
) -> tuple[Path, Path]:
    client_dir = get_client_directory(client_name)
    review_dir = client_dir / "Review"
    review_dir.mkdir(parents=True, exist_ok=True)

    base_name = Path(original_filename).stem
    dest_file = _unique_path(review_dir, base_name, source_file.suffix)
    dest_sidecar = dest_file.with_suffix(dest_file.suffix + ".review.json")

    shutil.copy2(source_file, dest_file)
    payload = {
        "status": status,
        "reasons": reasons,
        "extracted_values": extracted_values,
        "original_filename": original_filename,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(dest_sidecar, payload)
    return dest_file, dest_sidecar


def write_review_file(review_dir: Path, original_filename: str, receipt_id: str, status: str, reasons: list[str], extracted_values: dict[str, Any]) -> Path:
    review_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"{Path(original_filename).stem}.review"
    path = review_dir / f"{base_name}.json"
    payload = {
        "receipt_id": receipt_id,
        "status": status,
        "reasons": reasons,
        "extracted_values": extracted_values,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(path, payload)
    return path


def make_enriched_sidecar(
    receipt_id: str,
    source: str,
    client_code: str,
    client_name: str,
    capture_date: str,
    invoice_date: str,
    supplier: str,
    net: float | None,
    vat: float | None,
    gross: float | None,
    details: str | None,
    currency: str,
    category: str | None,
    confidence: str,
    validation_status: str,
    asserted: dict[str, Any] | None,
    original_filename: str,
    claimed_client_code: str | None = None,
) -> dict[str, Any]:
    return {
        "receipt_id": receipt_id,
        "client_code": client_code,
        "client_name": client_name,
        "claimed_client_code": claimed_client_code,
        "source": source,
        "capture_date": capture_date,
        "invoice_date": invoice_date,
        "supplier": supplier,
        "net": net,
        "vat": vat,
        "gross": gross,
        "details": details,
        "currency": currency,
        "category": category,
        "confidence": confidence,
        "validation_status": validation_status,
        "asserted": asserted,
        "original_filename": original_filename,
        "pipeline_receipt_id": receipt_id,
    }

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

REVIEW_SIDECAR_SUFFIX = ".review.json"


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
    dest_sidecar = dest_file.with_suffix(dest_file.suffix + REVIEW_SIDECAR_SUFFIX)

    shutil.copy2(source_file, dest_file)
    payload = {
        "status": status,
        "reasons": reasons,
        "extracted_values": extracted_values,
        "original_filename": original_filename,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    # Forward-only: carry the receipt id at the top level so a reader does not
    # have to reach into extracted_values. Statement review items have no
    # receipt, so they get no key rather than a null one.
    receipt_id = _receipt_id_from_extracted_values(extracted_values)
    if receipt_id:
        payload["receipt_id"] = receipt_id
    _write_json(dest_sidecar, payload)
    return dest_file, dest_sidecar


def _receipt_id_from_extracted_values(extracted_values: dict[str, Any] | None) -> str | None:
    if isinstance(extracted_values, dict) and extracted_values.get("receipt_id"):
        return str(extracted_values["receipt_id"])
    return None


def _review_dir_for_client_code(client_code: str) -> Path:
    """The client's Review folder, resolved the same way the writer's callers do."""
    client_name = config.CLIENTS_BY_CODE.get(client_code, {}).get("client_name", client_code)
    return get_client_directory(client_name) / "Review"


def _read_review_sidecar(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning(f"unreadable review sidecar, leaving it alone: {path}: {exc}")
        return None
    return payload if isinstance(payload, dict) else None


def _sidecar_receipt_id(payload: dict[str, Any]) -> str | None:
    if payload.get("receipt_id"):
        return str(payload["receipt_id"])
    return _receipt_id_from_extracted_values(payload.get("extracted_values"))


def _find_review_sidecar(
    review_dir: Path, receipt_id: str, original_filename: str | None = None
) -> Path | None:
    """Find this receipt's review sidecar by reading them, never by name.

    file_review() names the image through _unique_path(), so a second review
    item for the same original filename is {stem}-2{ext} with sidecar
    {stem}-2{ext}.review.json. Rebuilding {stem}{ext} would miss that file, or
    delete a different receipt's pair.

    A sidecar with no receipt id anywhere is skipped: app.py files a statement
    to Review with `intake.sidecar or {}`, which has no receipt and no receipt
    row. Those are only considered for the original_filename fallback, which
    exists for sidecars written before the id was recorded, and only when
    exactly one candidate matches. Two review items can share an original
    filename, and an ambiguous match is not a match.
    """
    if not review_dir.is_dir():
        return None

    fallback_candidates = []
    for sidecar in sorted(review_dir.glob(f"*{REVIEW_SIDECAR_SUFFIX}")):
        payload = _read_review_sidecar(sidecar)
        if payload is None:
            continue

        found_id = _sidecar_receipt_id(payload)
        if found_id:
            if found_id == receipt_id:
                return sidecar
            continue

        nested = payload.get("extracted_values")
        nested_filename = nested.get("original_filename") if isinstance(nested, dict) else None
        if original_filename and nested_filename == original_filename:
            fallback_candidates.append(sidecar)

    if len(fallback_candidates) == 1:
        logger.info(
            f"matched review sidecar for {receipt_id} on original_filename, no receipt id present: "
            f"{fallback_candidates[0]}"
        )
        return fallback_candidates[0]
    if len(fallback_candidates) > 1:
        logger.warning(
            f"{len(fallback_candidates)} review sidecars in {review_dir} match filename "
            f"{original_filename} and none carries a receipt id; leaving all of them alone"
        )
    return None


def _delete_review_pair(sidecar: Path) -> int:
    """Delete the image its name refers to, then the sidecar. Returns files removed."""
    image = sidecar.parent / sidecar.name[: -len(REVIEW_SIDECAR_SUFFIX)]
    removed = 0

    if image.exists():
        try:
            image.unlink()
            removed += 1
        except OSError as exc:
            # Leave the sidecar in place so the pair can still be found and
            # removed later. An image with no sidecar is invisible to this code.
            logger.warning(f"could not remove review image {image}: {exc}; leaving the pair on disk")
            return 0
    else:
        logger.info(f"review image already gone: {image}")

    try:
        sidecar.unlink()
        removed += 1
    except FileNotFoundError:
        logger.info(f"review sidecar already gone: {sidecar}")
    except OSError as exc:
        logger.warning(f"could not remove review sidecar {sidecar}: {exc}")

    return removed


def remove_review_pair(
    receipt_id: str, client_code: str, original_filename: str | None = None
) -> int:
    """Remove a receipt's Review image and sidecar. Returns the number of files removed.

    Called when a receipt's life in the Review folder ends: a successful resolve
    or a discard. Not on a still-invalid correction, because that receipt still
    needs review. Nothing on disk is not an error.

    Design document 3.5. Step 8's resolution service calls this same function.
    """
    review_dir = _review_dir_for_client_code(client_code)
    sidecar = _find_review_sidecar(review_dir, receipt_id, original_filename)

    if sidecar is None:
        sidecar = _scan_other_clients_for_receipt(review_dir, receipt_id)
        if sidecar is not None:
            logger.warning(
                f"review pair for receipt {receipt_id} found under {sidecar.parent}, not the "
                f"expected {review_dir}; the receipt was reassigned after the review item was "
                "written. Removing it."
            )

    if sidecar is None:
        logger.info(f"no review pair on disk for receipt {receipt_id}, nothing to remove")
        return 0

    removed = _delete_review_pair(sidecar)
    if removed:
        logger.info(f"removed {removed} review file(s) for receipt {receipt_id}")
    return removed


def _scan_other_clients_for_receipt(searched_dir: Path, receipt_id: str) -> Path | None:
    """Look for the receipt's sidecar in every other client's Review folder.

    Receipt ids are UUIDs, so matching on one is exact and the scan is safe. No
    filename fallback here: a filename is not unique across clients.
    """
    if not config.CLIENTS_ROOT.exists():
        return None
    for review_dir in sorted(config.CLIENTS_ROOT.glob("*/Review")):
        if review_dir == searched_dir or not review_dir.is_dir():
            continue
        found = _find_review_sidecar(review_dir, receipt_id)
        if found is not None:
            return found
    return None


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
        "currency": currency,
        "category": category,
        "confidence": confidence,
        "validation_status": validation_status,
        "asserted": asserted,
        "original_filename": original_filename,
        "pipeline_receipt_id": receipt_id,
    }

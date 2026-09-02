import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

import config

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".tiff", ".bmp"}


def compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_supported(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def save_file(receipt_id: str, client_id: str, filename: str, data: bytes) -> Path:
    """Write an email attachment into the document store. Sub-step 10d.53.

    Keyed on client_id, not on the client code, which no longer exists. The year
    and month below are the ARRIVAL date and deliberately stay: this runs before
    extraction, so there is no invoice date to file by, and an arrival date never
    needs correcting where an invoice date does, so no file here ever has to move.
    """
    today = datetime.now(timezone.utc)
    folder = config.FILES_DIR / client_id / str(today.year) / f"{today.month:02d}"
    folder.mkdir(parents=True, exist_ok=True)

    dest = folder / f"{receipt_id}_{filename}"

    if dest.exists():
        logger.warning(f"File already exists, skipping write: {dest}")
        return dest

    dest.write_bytes(data)
    return dest


def save_inbox_file(receipt_id: str, client_id: str, file_path: Path) -> Path:
    """Copy a folder-intake file into the document store. Sub-step 10d.53.

    Same key and the same reason for the year and month as save_file() above.
    Sub-step 10d.55 makes the statement branch call this too, so a statement gets
    a copy here before it is filed and can be reconstructed the way a receipt can.
    """
    folder = config.FILES_DIR / client_id / str(datetime.now(timezone.utc).year) / f"{datetime.now(timezone.utc).month:02d}"
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{receipt_id}_{file_path.name}"
    if dest.exists():
        logger.warning(f"File already exists, skipping write: {dest}")
        return dest
    dest.write_bytes(file_path.read_bytes())
    return dest

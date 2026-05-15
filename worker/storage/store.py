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


def save_file(receipt_id: str, filename: str, data: bytes) -> Path:
    today = datetime.now(timezone.utc)
    folder = config.FILES_DIR / str(today.year) / f"{today.month:02d}" / f"{today.day:02d}"
    folder.mkdir(parents=True, exist_ok=True)

    dest = folder / f"{receipt_id}_{filename}"

    if dest.exists():
        logger.warning(f"File already exists, skipping write: {dest}")
        return dest

    dest.write_bytes(data)
    return dest

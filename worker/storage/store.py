import hashlib
import logging
from pathlib import Path

import config
from worker import london_time

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

    **The arrival date is the LONDON date**, Paul's decision of 2026-09-11. A
    receipt arriving at 00:30 on 1 July British time was filed under June, and
    this folder is browsed by a person, so it is one of the surfaces that
    converts. 18.2a's reason for using arrival rather than the document date is
    untouched: which arrival day it is does not bear on it.

    **Nothing migrates and nothing existing moves**, on Paul's instruction. This
    applies from the moment it lands. That is safe rather than two conventions in
    one tree because only this function and `save_inbox_file()` below build this
    path, and both build it to WRITE: nothing recomputes it to read. Every reader
    takes the stored path off the row, `Path(receipt["file_path"])`. Enumerated
    from the syntax tree on 2026-09-12, three references to `config.FILES_DIR` in
    the production tree, the third being a log line.
    """
    today = london_time.now()
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

    Same key and the same reason for the year and month as save_file() above,
    **including the London date**, so the two writers of this path cannot put two
    documents that arrived in the same minute into two different months.
    Sub-step 10d.55 makes the statement branch call this too, so a statement gets
    a copy here before it is filed and can be reconstructed the way a receipt can.

    One `london_time.now()` rather than two calls to the clock: the old line read
    it twice, so a file arriving in the last microsecond of a month could land in
    a folder naming one month's year and the next month's number.
    """
    today = london_time.now()
    folder = config.FILES_DIR / client_id / str(today.year) / f"{today.month:02d}"
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{receipt_id}_{file_path.name}"
    if dest.exists():
        logger.warning(f"File already exists, skipping write: {dest}")
        return dest
    dest.write_bytes(file_path.read_bytes())
    return dest

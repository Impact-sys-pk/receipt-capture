"""Publishing a receipt to IntelliBooks: one JSON file per receipt.

**Stage 1 piece 3 of step 10f. Sub-steps 10f.2, 10f.4 to 10f.7 and 10f.36.**

Until now IntelliBooks pulled a receipt out of the client folder, scanning
`Clients\\{client}\\IntelliBooks\\Receipts\\` for a filed document and its
sidecar. Design document 18.3 reverses that: Intellibills pushes, into one
folder that IntelliBooks owns, and the client identity travels inside the item
rather than in the path to it, per 10f.4 and 10f.5.

**Stage 1 is additive.** The write into `Clients\\` continues unchanged and is
still what IntelliBooks reads. Desktop does not drain this folder until stage 2,
so for now the folder fills and nothing reads it, and the worst outcome of a
defect here is a file nobody opens.

**The item's shape is the enriched sidecar's, plus the document.** Amendment
283, confirmed by 285: `parseSidecar()` in `IntelliBooks-Desktop-v3.html` takes
`out.id` from `data.receipt_id` and `books.receipts` is keyed on it, so an item
carrying the sidecar's keys produces the same id as the same receipt arriving
the old way, and Desktop already skips a receipt it holds. A new shape would
have made one receipt into two.

**`make_enriched_sidecar()` is frozen by 18.2b and is not touched here.** This
module takes the payload it built and adds to a copy of it.
"""

import base64
import json
import logging
import os
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


class PublishError(Exception):
    """Publishing this receipt cannot proceed, and the receipt is unaffected.

    Raised for a condition that is about the item rather than about the file
    system, so it can be told apart from an OSError when the outcome is
    recorded. Either way the receipt keeps its status: the filing route is
    still live and is what IntelliBooks reads today.
    """


#: The document, base64-encoded, and what it is. **Two keys added to the
#: sidecar's own, and their names are part of the contract with IntelliBooks
#: Desktop**, which is written by a session that cannot see this file. They are
#: constants here for `CLIENT_TOP_FOLDER_FIELD`'s reason: a rename that goes
#: half done makes two products that silently stop meeting.
IMAGE_KEY = "image_base64"
MEDIA_TYPE_KEY = "image_media_type"

#: What each accepted document is, keyed by extension.
#:
#: **Deliberately not `mimetypes.guess_type()`**, which reads the registry on
#: Windows, so the answer would depend on what is installed on the machine and
#: two installations could publish one receipt with two different media types.
#:
#: The keys are `worker.storage.store.SUPPORTED_EXTENSIONS`, which is what the
#: pipeline lets in, and `tests/test_publish_item.py` compares the two sets so
#: neither can gain a member the other lacks. Note `.tiff` and no `.tif`, which
#: is `store.py`'s list rather than a choice made here.
MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".tiff": "image/tiff",
    ".bmp": "image/bmp",
}

#: The two outcomes a `publish_events` row can carry, sub-step 10f.36. The
#: third state is no row at all, which is why neither word is "not attempted".
PUBLISHED = "published"
FAILED = "failed"

#: The suffix a part-written item carries. **It must not end in `.json`**: the
#: whole point of renaming into place is that a reader globbing the folder
#: cannot see a half-written file, and a temporary name ending in `.json` would
#: hand it one.
PARTIAL_SUFFIX = ".part"


def media_type_for(filename) -> str:
    """What this document is, off its extension.

    Raises `PublishError` for anything not in the table rather than guessing.
    A wrong media type is worse than a refusal: Desktop would render it and
    show a broken document with no explanation, while a refusal is recorded as
    a failed publish that somebody can read.
    """
    extension = Path(str(filename)).suffix.lower()
    try:
        return MEDIA_TYPES[extension]
    except KeyError:
        raise PublishError(
            f"no media type for {extension!r} (from {filename!r}), so the item "
            f"cannot say what it carries. Known: {', '.join(sorted(MEDIA_TYPES))}. "
            f"worker/storage/store.py's SUPPORTED_EXTENSIONS is what the "
            f"pipeline accepts, and the two lists are compared by "
            f"tests/test_publish_item.py, so a document reaching here with "
            f"another extension got in somewhere else."
        ) from None


def build_item(sidecar: dict, document: Path) -> dict:
    """The published item: the sidecar's keys, plus the document and its type.

    `sidecar` is exactly what `make_enriched_sidecar()` returned and is copied
    rather than added to. It is the same dict the filing route writes into the
    client folder, so putting two keys into it in place would change that file
    as well.
    """
    document = Path(document)
    try:
        raw = document.read_bytes()
    except OSError as error:
        raise PublishError(
            f"the document for this receipt could not be read at {document}: "
            f"{error}"
        ) from error
    item = dict(sidecar)
    item[MEDIA_TYPE_KEY] = media_type_for(document.name)
    item[IMAGE_KEY] = base64.b64encode(raw).decode("ascii")
    return item


def write_item(directory: Path, receipt_id: str, item: dict) -> Path:
    """Write `{receipt_id}.json` into `directory`, temporary name first.

    Sub-step 10f.7. The item is written under a name in the same folder, forced
    to disk, and then renamed. **Same folder** because a rename is only atomic
    within one volume, and the destination is in OneDrive while the temporary
    directory is not.

    `os.replace()` rather than `Path.rename()`: on Windows a rename over an
    existing file raises, and republishing one receipt has to land on one file
    rather than fail.

    The temporary name carries a uuid, so two attempts at one receipt cannot
    write over each other's part file. Nothing today makes two at once; it
    costs one call to make that true rather than to rely on it.
    """
    directory = Path(directory)
    final = directory / f"{receipt_id}.json"
    partial = directory / f"{receipt_id}.{uuid.uuid4().hex}{PARTIAL_SUFFIX}"
    try:
        # `ensure_ascii=True`, so the file on disk is pure ASCII and cannot be
        # mangled by a reader that guesses the encoding. It crosses to a product
        # written by a session that cannot see this one, and a supplier name
        # coming out wrong there is a defect nobody would report. It costs a few
        # bytes per accented character against a base64 document.
        text = json.dumps(item, ensure_ascii=True)
        with open(partial, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(partial, final)
    except BaseException:
        # The part file is the thing this function must not leave behind. It is
        # removed on any failure, including one that is not an Exception, and a
        # failure to remove it is not allowed to replace the real error.
        try:
            partial.unlink()
        except OSError:
            logger.warning("could not remove the part file %s", partial)
        raise
    return final

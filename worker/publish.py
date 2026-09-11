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
from datetime import datetime, timezone
from pathlib import Path

import config

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

#: What validation said about this receipt, and the id it duplicates. **Two more
#: keys whose names are part of the contract with IntelliBooks Desktop**, added
#: 2026-09-09 by amendment 293, which widened publishing from `ok` to every
#: validation status. Desktop routes on `validation_status`, which the sidecar
#: already carried; these two are what a review-queue entry needs beyond it.
#:
#: **`validation_notes` carries the LIST, not the joined string.** The database
#: joins the notes with `", "` in `save_extraction()`, and the gross-mismatch
#: note contains `", "` itself, so a joined string cannot be split back into
#: notes. JSON has lists; the item uses one. `ok` carries an empty list rather
#: than no key, so a reader never has to tell "no notes" from "an old item".
#:
#: **`duplicate_of` is present only where there is one**, which is the same
#: shape `_log_receipt()` uses for its optional keys and keeps a null out of
#: every other item.
NOTES_KEY = "validation_notes"
DUPLICATE_OF_KEY = "duplicate_of"

#: Whether the category on this item is a machine's answer nobody has
#: confirmed. **Step 10l, amendments 237, 330 and 331.** A fifth key whose name
#: is part of the contract with IntelliBooks Desktop, and the one amendment 330
#: deliberately left unnamed because the session that wrote it had not read this
#: file.
#:
#: **Why not `category_needs_review`.** Desktop already compares a string
#: against `"needs_review"` as a **validation status**, at line 3184 of
#: `IntelliBooks-Desktop-v3.html`. Two keys one word apart meaning two different
#: things is the `postTxn()` and `postReceiptToCashbook()` trap `CLAUDE.md`
#: names. This wording also matches amendment 330's screen pill exactly,
#: `Category unconfirmed`, so the key, the pill and the reason line are one
#: phrase.
#:
#: **Why the positive sense rather than `category_confirmed`.** A missing key
#: must not hold a receipt that is fine, which is the rule `drainInbox()`
#: already follows for a blank `validation_status`. In JavaScript `undefined`
#: is falsy, so an absent `category_unconfirmed` reads as "not held" with no
#: special case in the reader. An absent `category_confirmed` would read as
#: "not confirmed" and would hold every item written before the key existed.
#:
#: **It travels on every item**, for `NOTES_KEY`'s reason rather than
#: `DUPLICATE_OF_KEY`'s: a reader must never have to tell "not held" from "an
#: item written before this key existed". Both read as not held, so an absent
#: key is safe either way, and a stated `false` is a positive answer.
#:
#: **The value is a JSON boolean and that matters.** The database column is 0 or
#: 1, and `1 === true` is false in JavaScript, so a reader testing identity
#: would never hold anything. `category_is_unconfirmed()` below coerces.
CATEGORY_UNCONFIRMED_KEY = "category_unconfirmed"

#: Every key a published item carries that the sidecar does not, in one place.
#:
#: **Added 2026-09-11 because adding the fifth broke a test that had the four
#: written out by hand.** `tests/test_sidecar_category_keys.py` compares the
#: sidecar's own keys across four call sites and reads two of them out of a
#: published item, so it has to subtract the item's own keys first. It listed
#: them, and a list in a test of what a module adds goes stale the moment the
#: module adds one.
#:
#: It is a statement about this module's own output, so it belongs here, and a
#: sixth key added below without joining it fails that comparison rather than
#: passing it.
ITEM_ONLY_KEYS = (
    IMAGE_KEY,
    MEDIA_TYPE_KEY,
    NOTES_KEY,
    DUPLICATE_OF_KEY,
    CATEGORY_UNCONFIRMED_KEY,
)

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


def build_item(sidecar: dict, document: Path, extra: dict = None) -> dict:
    """The published item: the sidecar's keys, plus `extra`, plus the document.

    `sidecar` is exactly what `make_enriched_sidecar()` returned and is copied
    rather than added to. ~~It is the same dict the filing route writes into the
    client folder, so putting two keys into it in place would change that file
    as well.~~ **Corrected 2026-09-09 by stage 4: the filing route no longer
    writes a sidecar into the client folder at all, per 18.2b's image-only
    rule.** The copy is still the right thing to do, for the reason below it:
    `process_extraction_result()` hands the same dict to `file_review()` as its
    `extracted_values`, so adding keys in place would change the Review file.

    `extra` is merged **before** the document and its media type, so those two
    always win. A caller passing `image_base64` would otherwise replace the
    document with whatever it liked and the item would say it carried a PDF
    while holding something else.
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
    if extra:
        item.update(extra)
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


def category_is_unconfirmed(categorisation) -> bool:
    """Is this categorisation a machine's answer nobody has confirmed?

    **The whole trigger for step 10l's hold, in one expression, on purpose.**
    Amendment 330 decided the hold lives in `categorisations.needs_review`, so
    that is what this reads, and narrowing it is a change to this one line.

    **It takes the categorisation rather than a boolean** so no call site can
    pass the wrong answer. `extra_for()`'s two callers each have the object in
    hand at the point of the call.

    `None` means nothing was categorised, which is every receipt that is not
    `ok`: the receipt is not filed and no category was produced, so there is no
    category to be unconfirmed about. It returns False, and such an item is held
    by its `validation_status` instead, which is a different question.

    **What `needs_review` covers, measured in `tests/test_category_hold.py`
    rather than read off the engine**: it is True for layers 3, 4 and 5, for no
    match at all, and for the two chart outcomes `resolve_against_chart()`
    forces it on. It is False for layers 0, 1 and 2, which are a rule a person
    wrote and two stored mappings a person taught. **So the hold is wider than
    "a layer 5 guess"**, which is what amendment 237 originally described and
    what the brief's section 6 expected. That divergence is reported rather than
    resolved here: it is Paul's decision, and it is this function's one line.

    `bool()` rather than the value itself: the dataclass field is a Python bool
    but a caller reading the column back out of the database has 0 or 1, and
    `1 === true` is false in JavaScript.
    """
    if categorisation is None:
        return False
    return bool(getattr(categorisation, "needs_review", False))


def extra_for(notes, duplicate_of=None, categorisation=None) -> dict:
    """The keys amendment 293 adds to a published item, built in one place.

    Two callers, `process_extraction_result()` and the recovery sweep in
    `app.py`, and one builder, so a review-queue entry arriving by the sweep
    cannot carry a different shape from one arriving on the poll.
    `tests/test_category_hold.py` holds that set at two and asserts each one
    passes a categorisation.

    `notes` is coerced to a list rather than trusted, because `validate()`
    returns one and a caller reading `extractions.validation_notes` back out of
    the database has a joined string. A string would silently publish as itself
    and Desktop would render one note reading `missing supplier_name, gross
    mismatch: ...`.

    `categorisation` is step 10l's, and `None` is the honest value for a receipt
    that was never categorised rather than a missing argument: see
    `category_is_unconfirmed()`. It defaults to None so a caller that says
    nothing publishes `false`, because a key that said nothing must not hold a
    receipt that is fine.
    """
    if notes is None:
        notes = []
    elif isinstance(notes, str):
        notes = [part for part in notes.split(", ") if part]
    extra = {
        NOTES_KEY: list(notes),
        CATEGORY_UNCONFIRMED_KEY: category_is_unconfirmed(categorisation),
    }
    if duplicate_of:
        extra[DUPLICATE_OF_KEY] = duplicate_of
    return extra


def _record(repo, receipt_id, destination, outcome, created_at,
            item_path=None, reason=None):
    """Write the `publish_events` row, and never let that be the thing that fails.

    The whole point of `publish_receipt()` is that a receipt is unaffected by
    publishing going wrong, and recording the outcome is part of publishing. A
    locked database here would otherwise take down a run that had already filed
    the receipt correctly.
    """
    try:
        repo.save_publish_event(
            event_id=str(uuid.uuid4()),
            receipt_id=receipt_id,
            destination=destination,
            outcome=outcome,
            created_at=created_at,
            item_path=item_path,
            reason=reason,
        )
    except Exception as error:
        logger.error(
            "could not record the %s publish of receipt %s to %s: %s",
            outcome, receipt_id, destination, error)


def _warn_if_already_published(repo, receipt_id, destination) -> None:
    """Say so when this receipt has landed before. **It does not refuse.**

    Deliverable 4 of stage 4's pipeline brief, and flag 5 of
    `2026-09-09_REPORT_claude_code_stage1_piece3_publish.md`. With one status
    publishing once, an overwrite had nil consequence. Amendment 293 widened
    publishing to four statuses, and the auto-retry re-extracts a `failed` or
    `needs_review` receipt, so **one receipt publishing twice is now a normal
    event and it has to work**: a receipt published as `failed` and later
    re-extracted as `ok` must reach Desktop again or the books never see it.

    **So this makes the overwrite visible rather than preventing it**, which is
    what "must not silently overwrite" asks for. The second attempt writes its
    own `publish_events` row, so the history is in the database as well as the
    log.

    Reading the log must never be the thing that stops a publish, so a failure
    here is logged and swallowed, on `_record()`'s reasoning.
    """
    try:
        landed = [row for row in repo.list_publish_events(receipt_id)
                  if row.get("outcome") == PUBLISHED]
    except Exception as error:
        logger.warning(
            "could not read the publish history of receipt %s before "
            "republishing it: %s", receipt_id, error)
        return
    if not landed:
        return
    previous = landed[0]
    logger.warning(
        "receipt %s is already published to %s: %s items(s) landed before, the "
        "last at %s as %s. Publishing again overwrites it, which is deliberate: "
        "an auto-retry that turns a failed receipt into an ok one has to reach "
        "IntelliBooks a second time.",
        receipt_id, destination, len(landed), previous.get("created_at"),
        previous.get("item_path"))


def publish_receipt(repo, receipt_id, sidecar, document,
                    directory=None, destination=None, extra=None) -> bool:
    """Publish one receipt and record the attempt. **This never raises.**

    Sub-step 10f.36. Returns True when the item landed.

    **A failure here must not fail the receipt.** The write into `Clients\\`
    has already happened and is still what IntelliBooks reads, so a receipt
    that files and does not publish is `ok`, filed, and carries a
    `publish_events` row saying why. The alternative would be a receipt marked
    bad because a folder in somebody else's tree was missing.

    **The swallowing lives here rather than at the call site**, so the
    guarantee does not depend on each caller remembering to wrap it. There is
    one call site today and four callers of the function it sits in.

    `KeyboardInterrupt` and `SystemExit` are deliberately not caught: they are
    a shutdown rather than a publishing failure, and swallowing them would make
    the pipeline hard to stop.

    `directory` and `destination` are read from `config` at call time rather
    than bound at import, so a test can point them somewhere without reloading
    this module.
    """
    directory = config.INTELLIBOOKS_PUBLISH_DIR if directory is None else Path(directory)
    destination = config.INTELLIBOOKS_DESTINATION if destination is None else destination
    now = datetime.now(timezone.utc).isoformat()
    _warn_if_already_published(repo, receipt_id, destination)
    try:
        item = build_item(sidecar, document, extra)
        written = write_item(directory, receipt_id, item)
    except Exception as error:
        logger.error("publishing receipt %s to %s failed: %s: %s",
                     receipt_id, destination, type(error).__name__, error)
        _record(repo, receipt_id, destination, FAILED, now,
                reason=f"{type(error).__name__}: {error}")
        return False
    logger.info("published receipt %s to %s at %s", receipt_id, destination, written)
    _record(repo, receipt_id, destination, PUBLISHED, now, item_path=str(written))
    return True

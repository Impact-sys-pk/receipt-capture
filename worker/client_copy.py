"""The copy into the firm's client folder: one writer, image only, once.

**Sub-steps 10f.11, 10f.12 and 10f.13. Stage 4 of `2026-09-08_PLAN_publish_step.md`,
under the freeze narrowed for it by amendment 290.**

Until now three functions wrote into `Clients\\`: the arrival write in
`process_extraction_result()`, the completed review item in `resolve_receipt()`,
and a recovery sweep in `app.py` that no design document had recorded until
amendment 278 counted it from the syntax tree. **This module replaces all
three.** `write_client_copy()` is the only code that writes there, and
`copy_for_published_receipt()` is the only way to reach it.

**Why one gated entry point rather than three call sites each doing the same
four things.** The trigger, the one-copy rule and the missing-folder-name
refusal are one decision each and they belong in one place.
`CLAUDE.md`'s rule: where two or more call sites must all use one helper, assert
it on the source, because `extract_with_transient_retry()` was used by three of
the four intake paths for weeks and nobody noticed the fourth.
`tests/test_stage4_client_copy.py` holds the set of callers.

## What changed against `file_receipt()`, and each is a rule from 18.2b

**Image only.** No sidecar and no data file of any kind beside it. The sidecar
existed to carry figures between the two products and 18.3's inbox handoff
replaces that. **This is what makes amendment 296's Desktop half necessary and
it is not optional there:** `scanFiledReceipts()` pairs an image with a sidecar
on the full filename, so from the moment the copy is image only, every copy
Desktop scans becomes a books row reading "Image only. Edit details." with a
gross of nought. The scan stops first, the copy changes second.

**Written on a successful publish, not on arrival.** Amendments 73, 106 and 122,
and Paul's reasoning: a folder fed from capture shows everything that arrived,
duplicates and misfires included, and what a client should see on a portal is
the result of the work.

**Only an `ok` receipt.** A decision the brief did not settle, taken here.
Amendment 293 widened publishing from `ok` to all four validation statuses in
the same window as this change, and F16's trigger is "on a successful publish",
so the two read together would put a `failed` receipt into a live client folder
as `{date}_unknown_0.00.pdf`. **18.2b's own reasoning decides it**: the folder
shows the result of the work, and a receipt with no gross is not a result.
Reversible with one amendment.

**Once per receipt, ever.** `receipts.filed_path` is the record that a copy was
written, which is what that column has always meant, and a receipt that has one
is not copied again. 18.2b: written once, never withdrawn, and a repost does not
duplicate it. **The filename collision is a different question and keeps
`_unique_path()`**: two documents with the same date, supplier and amount are two
documents and the second gets a `-2`.

**And the collision is decided on the bytes. Sub-step 10f.25, 2026-09-09.**
~~two documents with the same date, supplier and amount are two documents and
the second gets a `-2`~~ **held for two different documents and was applied to
identical ones as well**, because nothing compared them. Identical bytes are
now skipped and said so in the log; different bytes keep the `-2` and are
flagged. **The naming convention does not change**, which is what check 1
depends on. **Why it is nearly free**, in the sub-step's own words: the filename
already carries the three values a semantic duplicate matches on, so the
collision was already the signal and only the response was wrong.

**One consequence of the write stopping, flagged here and REPAIRED the same day
by sub-step 10f.24.** ~~`Repository.is_recorded_and_filed()` gates the semantic
duplicate check on `filed_path`, so with the trigger on `never` or `post` no
receipt ever gets one and that check stops flagging anything.~~ It did, and it
did so in two places rather than the one this paragraph named:
`find_by_transaction_loose()` carried `filed_path IS NOT NULL` in both of its
queries as well, and it runs first. **Both now ask for a `published` row**,
which amendment 293's fifth point named as the marker. Amendment 303, and
`Repository._PUBLISHED` carries the reasoning.
"""

import hashlib
import logging
import shutil
from pathlib import Path
from typing import NamedTuple

import config

# `_unique_path()` is imported rather than copied. It is private to
# `worker/filing.py` and a second copy of collision-avoidance logic is worse
# than reaching for this one: the two would drift, and the half that drifts
# first decides whether a second document is kept or silently lost.
from worker.filing import _unique_path, determine_tax_year, get_client_directory, \
    normalise_supplier

logger = logging.getLogger(__name__)

#: Whether the `post` trigger has already said it has no mechanism. Module
#: state, so a real firm on `post` gets one line per run rather than one per
#: receipt. Reset by `_reset_post_warning()`, which exists for the test.
_POST_WARNED = False


def _reset_post_warning() -> None:
    """Forget that the `post` warning has been given. For tests only."""
    global _POST_WARNED
    _POST_WARNED = False


class ClientCopy(NamedTuple):
    """What `write_client_copy()` did. Sub-step 10f.25.

    `path` is always where this document is in the client folder, whether this
    call put it there or a previous one did, so it is what `filed_path` records
    either way.

    `written` is False only on the identical-bytes skip. `collided_with` is
    every file already under the name this document composed, newest last, and
    is empty when the name was free.

    **A tuple rather than a bare `Path`, because the caller does the
    reporting.** The three log lines have to name the receipt and only
    `copy_for_published_receipt()` knows the `receipt_id`, while only this
    function has read the bytes. One caller, so the shape costs nothing.
    """

    path: Path
    written: bool
    collided_with: list


#: The file was there and is not any more.
REMOVAL_DELETED = "deleted"

#: There was nothing at that path. A normal outcome, not a failure: 18.2b says a
#: copy is never withdrawn, so anything that removed it did so outside this
#: product and the operator's intent is satisfied either way.
REMOVAL_ALREADY_GONE = "already_gone"

#: The path is not one this function will touch. Nothing was deleted and the
#: caller reports it: a `filed_path` that does not resolve to a file inside
#: `config.CLIENTS_ROOT` is a corrupt stored value rather than a client copy.
REMOVAL_REFUSED = "refused"

#: The unlink raised. On OneDrive a locked or syncing file is the ordinary case.
REMOVAL_FAILED = "failed"


class ClientCopyRemoval(NamedTuple):
    """What `remove_client_copy()` did, with enough to log and to record.

    `path` is the resolved path it considered, or None where the value could not
    be resolved at all. `detail` is the reason on `refused` and `failed`, and
    None on the two outcomes that need no explanation.

    A tuple rather than a bare bool for `ClientCopy`'s reason: the caller does
    the reporting, because only `discard_receipt()` knows the receipt id and
    only this function knows what happened to the file.
    """

    outcome: str
    path: Path | None
    detail: str | None


def remove_client_copy(filed_path) -> ClientCopyRemoval:
    """Delete one document from the client folder. **The only deleter.**

    Paul's decision of 2026-09-10, the first of four: an operator deleting a
    receipt from the books in IntelliBooks Desktop is asked whether the copy in
    the client folder goes too, and this is what happens when they say yes.

    **It deletes exactly the file it is given and nothing else.** Not a composed
    name, not a glob, not a directory. The path comes from `receipts.filed_path`,
    which is what `copy_for_published_receipt()` below recorded when it wrote the
    copy, so a `-2` from a collision is already resolved and Desktop never has to
    guess at a name it cannot tell apart from the original.

    **Three refusals, and each is a real stored value away.**

    - **Anything outside `config.CLIENTS_ROOT`**, resolved first so a `..` in
      the middle of the path cannot walk back out of the root. This is what
      keeps `Intellibills\\Documents\\` safe, and that folder is the archive of
      record per 18.2a and the reason deleting the client copy is safe at all.
    - **A directory.** The tax year folder is one bad value away, and refusing
      explicitly is better than relying on `unlink()` to raise.
    - **A relative path.** The caller resolves 12.2's practice-root convention
      with `resolve_practice_path()` in the resolution service, and a second
      copy of that here would be the drift this module already warns about for
      `_unique_path()`.

    **It never raises**, for `copy_for_published_receipt()`'s reason applied to
    the other direction: the status change is the point of a discard, and a file
    left behind is untidy and recoverable, while a note stuck in
    `Resolutions\\failed\\` leaves the database saying `ok` about a receipt the
    books say is gone. That is the disagreement amendment 306 exists to remove.

    **This is the first code in the product that deletes anything under
    `Clients\\`.** Before it, production code deleted files in five places and
    none of them was there: `_cleanup_old_backups()`, `acquire_lock()` and
    `release_lock()` for the lock file, `_delete_review_pair()` for the Review
    pair, and `write_item()` for its own partial. Enumerated from the syntax
    tree, and `tests/test_discard_client_copy.py` holds a guard that keeps the
    deletion in this one function.
    """
    try:
        candidate = Path(filed_path)
    except TypeError as error:
        return ClientCopyRemoval(REMOVAL_REFUSED, None, f"{type(error).__name__}: {error}")

    if not candidate.is_absolute():
        return ClientCopyRemoval(
            REMOVAL_REFUSED, candidate,
            "the path is relative, and this function does not resolve 12.2's "
            "practice-root convention: the caller does")

    # `strict=False`, so a path whose file has already gone still resolves and
    # is still checked for containment. The check has to come first either way:
    # a refusal is about where the path points, not about what is there.
    resolved = candidate.resolve()
    root = Path(config.CLIENTS_ROOT).resolve()
    if resolved == root or root not in resolved.parents:
        return ClientCopyRemoval(
            REMOVAL_REFUSED, resolved,
            f"the path does not resolve to a file inside {root}")

    if resolved.is_dir():
        return ClientCopyRemoval(
            REMOVAL_REFUSED, resolved, "the path is a directory")

    if not resolved.exists():
        return ClientCopyRemoval(REMOVAL_ALREADY_GONE, resolved, None)

    try:
        resolved.unlink()
    except Exception as error:
        return ClientCopyRemoval(
            REMOVAL_FAILED, resolved, f"{type(error).__name__}: {error}")

    return ClientCopyRemoval(REMOVAL_DELETED, resolved, None)


def _digest(path: Path) -> str:
    """SHA256 of a file, read in chunks. The same hash `file_hash` uses."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _same_bytes(one: Path, other: Path) -> bool:
    """Whether two files hold the same bytes.

    Size first because it is cheap and settles almost every pair, then a
    digest. **Not `filecmp.cmp()`**: it caches on a stat signature whose mtime
    resolution is the filesystem's, and a cached wrong answer here would either
    lose a document or duplicate one.
    """
    if one.stat().st_size != other.stat().st_size:
        return False
    return _digest(one) == _digest(other)


def _existing_under(destination_dir: Path, base_name: str, suffix: str) -> list:
    """Every file already using the name this document composed.

    The contiguous run `_unique_path()` walks: the plain name, then `-2`, `-3`
    and so on until one is missing. Enumerated the same way it steps, so the
    two cannot disagree about what a collision is.
    """
    found = []
    candidate = destination_dir / f"{base_name}{suffix}"
    index = 2
    while candidate.exists():
        found.append(candidate)
        candidate = destination_dir / f"{base_name}-{index}{suffix}"
        index += 1
    return found


def write_client_copy(
    source_file: Path,
    client_folder_name: str,
    tax_year: str,
    supplier: str,
    gross: float,
    invoice_date: str,
) -> ClientCopy:
    """Copy one document into the client's folder. **The only writer.**

    Image only, and the document date names both the tax year folder and the
    file: `2026-04-01_apcoa-parking_12.00.pdf`. That is the convention
    `file_receipt()` produced, kept deliberately, so a listing of `Clients\\`
    taken before this change and one taken after differ in nothing but the
    sidecar that is no longer written.

    `invoice_date` is a parameter rather than read out of a sidecar, which is
    how `file_receipt()` got it. There is no sidecar any more.

    **The collision is decided on the bytes, not on the name. 10f.25.**
    Identical bytes are already there, so nothing is written and the file that
    is there is returned. Different bytes are a second document, so the `-2`
    stands and the caller is told to say so.

    **Compared against every file already under the name, not just the first.**
    Once a `-2` exists, a resend of THAT document has to match it, and a
    comparison against the plain name alone would have written a `-3`.

    **Nothing is ever overwritten on either branch**, which is 18.2b and rule 1
    of `CLAUDE.md`.
    """
    destination_dir = (get_client_directory(client_folder_name)
                       / config.CLIENT_RECEIPTS_FOLDER_NAME / tax_year)
    destination_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"{invoice_date}_{normalise_supplier(supplier)}_{gross:.2f}"
    suffix = Path(source_file).suffix

    existing = _existing_under(destination_dir, base_name, suffix)
    for candidate in existing:
        if _same_bytes(Path(source_file), candidate):
            return ClientCopy(path=candidate, written=False,
                              collided_with=[candidate])

    destination = _unique_path(destination_dir, base_name, suffix)
    shutil.copy2(source_file, destination)
    return ClientCopy(path=destination, written=True, collided_with=existing)


def copy_for_published_receipt(
    repo,
    receipt_id: str,
    client_id: str,
    source_file: Path,
    invoice_date: str,
    supplier: str,
    gross: float,
    validation_status: str,
    filed_path: str | None,
) -> Path | None:
    """Write this receipt's client folder copy if the firm's trigger says so.

    Returns where this receipt's document is in the client folder, or None when
    it is not there and this call did not put it there. Records it with
    `mark_receipt_filed()`, which is the only writer of `filed_path` and
    therefore of `filed_at`.

    **A returned path does not mean a file was written. 10f.25.** An identical
    document already under the composed name is not copied again, and the path
    that comes back is the one already there. The log line says which happened.

    **This never raises.** `publish_receipt()`'s reasoning, one step further on:
    by the time this runs the item is already in the folder IntelliBooks drains,
    which is the route into the books, and `Intellibills\\Documents\\` already
    holds the archive of record. `Clients\\` is the firm's own filing structure,
    per 18.2b, and a folder in somebody else's tree being unavailable must not
    fail a receipt that is otherwise complete.

    **A copy that fails is not retried.** Flagged rather than fixed: the
    repointed sweep asks "was this published", and a receipt whose publish
    succeeded and whose copy failed has a `published` row, so it is not swept.
    The failure is an ERROR in `run.log` and `filed_path` stays NULL.

    `filed_path` is passed in rather than read here, because every caller has
    the receipt row in hand and a second read could disagree with the row the
    caller decided from.
    """
    global _POST_WARNED

    if config.CLIENT_COPY_TRIGGER == config.CLIENT_COPY_NEVER:
        return None

    if config.CLIENT_COPY_TRIGGER == config.CLIENT_COPY_AT_POST:
        # The trigger with no mechanism. Sub-step 10f.16 is the Post-time
        # message from Desktop and it does not exist, so a `post` firm gets no
        # copy from the pipeline. **Said out loud rather than looking like
        # `never`**, because a firm that chose `post` and silently got nothing
        # would have no way to tell the two apart. Once per process: a real
        # firm's every receipt would otherwise carry the same line.
        if not _POST_WARNED:
            _POST_WARNED = True
            logger.warning(
                "%s is %r, and the Post-time trigger has no mechanism yet: it "
                "needs the message from IntelliBooks Desktop at sub-step "
                "10f.16, which is not built. No copy is written into %s by this "
                "pipeline until it is. Set %s to %r to copy on a successful "
                "publish instead.",
                config.CLIENT_COPY_TRIGGER_FIELD, config.CLIENT_COPY_AT_POST,
                config.CLIENTS_ROOT, config.CLIENT_COPY_TRIGGER_FIELD,
                config.CLIENT_COPY_ON_PUBLISH)
        return None

    if validation_status != "ok":
        # See the module docstring. 18.2b's folder shows the result of the work.
        return None

    if filed_path:
        logger.info(
            "receipt %s already has a client folder copy at %s, so none is "
            "written: a copy is made once and never withdrawn, per 18.2b",
            receipt_id, filed_path)
        return None

    client_folder_name = (config.CLIENTS_BY_ID.get(client_id) or {}).get(
        "client_folder_name")
    if not client_folder_name:
        # 10d.18, and it keeps its own reason rather than being folded into the
        # trigger: a client nobody can name files nothing, and that is reported.
        logger.warning(
            "receipt %s published, but client %s has no client_folder_name in "
            "the registry, so no copy is written into %s",
            receipt_id, client_id, config.CLIENTS_ROOT)
        return None

    try:
        result = write_client_copy(
            source_file=Path(source_file),
            client_folder_name=client_folder_name,
            tax_year=determine_tax_year(invoice_date),
            supplier=supplier or "unknown",
            gross=gross if gross is not None else 0.0,
            invoice_date=invoice_date,
        )
    except Exception as error:
        logger.error(
            "the client folder copy for receipt %s failed: %s: %s. The receipt "
            "is unaffected: it is published and the document store holds the "
            "archive of record. Nothing retries this copy.",
            receipt_id, type(error).__name__, error)
        return None

    # **`filed_path` is recorded on the skip as well as on the write**, and
    # that is a decision 10f.25's brief did not settle. The path is true either
    # way: this receipt's document is in the client folder, at that name. And
    # leaving it NULL would put the receipt back in
    # `get_published_receipts_without_client_copy()`, which selects on exactly
    # that column, so `_copy_missing_client_copies()` would offer it again on
    # every poll for ever and log the same skip each time.
    repo.mark_receipt_filed(receipt_id, str(result.path))

    if not result.written:
        # 10f.25. No second document, so no second file.
        logger.info(
            "receipt %s needed no client folder copy: %s already holds an "
            "identical document, byte for byte, so nothing was written and "
            "nothing was overwritten",
            receipt_id, result.path)
    elif result.collided_with:
        # 10f.25. The `-2` is right, and nobody was being told.
        logger.warning(
            "receipt %s was copied to %s because %s already holds a document "
            "with the same date, supplier and amount and DIFFERENT content. "
            "Both are kept: two purchases can match on all three. Nothing in "
            "the receipt record says which file belongs to which receipt, so "
            "this line is the record",
            receipt_id, result.path,
            ", ".join(str(path) for path in result.collided_with))
    else:
        logger.info("receipt %s copied into the client folder at %s",
                    receipt_id, result.path)
    return result.path

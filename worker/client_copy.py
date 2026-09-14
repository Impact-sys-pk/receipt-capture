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

## The delivery log. Step 10az, amendment 456, 2026-09-14

**Every document this module writes into `Clients\\` gets one line in
`IntelliBooks\\Delivery\\{client_id}.log`**, appended as it happens. Step 10au
is a reconciliation check on the Desktop side, comparing what is in a client's
folder against what was recorded as delivered there, and it could not be built
because nothing wrote that record. `_record_delivery()` is the record.

**It has the same gate as the copy, because it is not a second decision.**
Whatever the trigger, the `ok`-only rule, the one-copy rule or the byte
comparison refuses, there is no line: a line for a document that is not in the
folder is the false positive step 10au would then have to explain away.

**A log failure does not undo the copy.** The document is on disk before the
line is written, so refusing would undo work that succeeded. It is a WARNING
naming the receipt rather than a silence, which is step 10af's decision applied
on this side.
"""

import hashlib
import json
import logging
import shutil
from datetime import datetime, timezone
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

#: The validation status a receipt has to have reached for its document to go
#: into a live client folder. A named constant from 2026-09-11, when sub-step
#: 10f.38 gave the gate below a second value to let past: two bare literals in
#: one condition read as a list of magic words, and one of them means "a
#: validation ran and passed" while the other means "no validation ever ran".
OK_STATUS = "ok"

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


#: The suffix a filed receipt's data file APPENDS to the document's full name,
#: so `x.pdf` pairs with `x.pdf.json`.
#:
#: **Section 3 of `IntelliBooks-System-Specification.md` states both
#: conventions and says both are deliberate**: this one appends, and an inbox
#: sidecar REPLACES the extension, `x.json` for `x.pdf`. Getting them the wrong
#: way round here would delete a file this change has no business touching, so
#: it is a named constant and a test asserts an extension-replaced name
#: survives.
#:
#: **Nothing writes one of these any more.** 18.2b makes the client folder copy
#: the image alone and `write_client_copy()` below writes nothing beside it, so
#: the set of these on disk is finite and predates 2026-09-09.
CLIENT_COPY_SIDECAR_SUFFIX = ".json"


def _refuse_reason(resolved: Path, root: Path) -> str | None:
    """Why this resolved path is not one to delete, or None if it is.

    **Two checks, and both are applied to the data file as well as to the
    document.** Split out for that reason rather than for brevity: a second
    copy of the containment rule is how the two would come to disagree, and the
    data file is the half a reader would assume is safe because its parent
    already passed.

    **It is not safe by inheritance.** `Path.resolve()` follows a link, so a
    document inside the root can have a `.json` beside it that resolves
    somewhere else entirely, which is exactly the case
    `tests/test_discard_sidecar_and_cli.py` builds.
    """
    if resolved == root or root not in resolved.parents:
        return f"the path does not resolve to a file inside {root}"
    if resolved.is_dir():
        return "the path is a directory"
    return None


class ClientCopyRemoval(NamedTuple):
    """What `remove_client_copy()` did, with enough to log and to record.

    `path` is the resolved path it considered, or None where the value could not
    be resolved at all. `detail` is the reason on `refused` and `failed`, and
    None on the two outcomes that need no explanation.

    A tuple rather than a bare bool for `ClientCopy`'s reason: the caller does
    the reporting, because only `discard_receipt()` knows the receipt id and
    only this function knows what happened to the file.

    ## The three sidecar fields, added 2026-09-10

    They describe the document's data file, the legacy `x.pdf.json` beside a
    receipt filed before 2026-09-09, and they are **separate from the document's
    own three** so a caller can say the document went, the data file went, or
    the document went and there was no data file.

    **`sidecar_outcome` is None where the data file was never considered**,
    which is every branch that did not delete the document: `refused`,
    `already_gone` and `failed`. None is therefore different from
    `already_gone`, and the difference matters: a data file beside a document
    something else removed is left exactly where it is, because this function
    has no business deciding it is stale.
    """

    outcome: str
    path: Path | None
    detail: str | None
    sidecar_outcome: str | None = None
    sidecar_path: Path | None = None
    sidecar_detail: str | None = None


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

    ## The document's data file goes with it. Added 2026-09-10

    **A real orphan on Paul's machine at 14:30 on 2026-09-10**: one document had
    been deleted and `2026-08-15_octopus-energy_248.33.jpeg.json` was still
    beside where it had been. He removed that pair by hand.

    **The name is derived from the document, never composed**, by appending
    `CLIENT_COPY_SIDECAR_SUFFIX` to the resolved document's full name. Not a
    glob, not a pattern, not a directory sweep, and not the inbox convention,
    which replaces the extension instead.

    **It happens only after the document has actually been deleted**, which is
    structural rather than a rule to remember: it is below the `unlink()` and
    every other branch has already returned. An `already_gone` document does
    not take a data file with it, because if something else removed the
    document then nothing here knows the data file is stale.

    **Its absence is the normal case and is not a failure.** Everything filed
    since sub-step 10f.11 has no data file at all.
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
    refusal = _refuse_reason(resolved, root)
    if refusal:
        return ClientCopyRemoval(REMOVAL_REFUSED, resolved, refusal)

    if not resolved.exists():
        return ClientCopyRemoval(REMOVAL_ALREADY_GONE, resolved, None)

    try:
        resolved.unlink()
    except Exception as error:
        return ClientCopyRemoval(
            REMOVAL_FAILED, resolved, f"{type(error).__name__}: {error}")

    # The document is gone. Now its data file, if there is one, and only now:
    # everything above has already returned, so this is unreachable unless the
    # unlink succeeded.
    sidecar = (resolved.with_name(resolved.name + CLIENT_COPY_SIDECAR_SUFFIX)
               .resolve())
    sidecar_refusal = _refuse_reason(sidecar, root)
    if sidecar_refusal:
        return ClientCopyRemoval(REMOVAL_DELETED, resolved, None,
                                 REMOVAL_REFUSED, sidecar, sidecar_refusal)
    if not sidecar.exists():
        return ClientCopyRemoval(REMOVAL_DELETED, resolved, None,
                                 REMOVAL_ALREADY_GONE, sidecar, None)
    try:
        sidecar.unlink()
    except Exception as error:
        return ClientCopyRemoval(
            REMOVAL_DELETED, resolved, None, REMOVAL_FAILED, sidecar,
            f"{type(error).__name__}: {error}")

    return ClientCopyRemoval(REMOVAL_DELETED, resolved, None,
                             REMOVAL_DELETED, sidecar, None)


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


def _delivery_log_path(client_id: str) -> Path | None:
    """This client's delivery log, or None if the id cannot name a file.

    **The id is input, not a value this product composed.** `clients.json` is
    written by IntelliBooks Desktop and read here, per 10d.35, so a `client_id`
    carrying a separator would put the log somewhere other than
    `IntelliBooks\\Delivery\\`, and `..` would put it in that folder's parent.
    Refused rather than sanitised: a rewritten id would name a file that
    belongs to no client, and step 10au would then reconcile a real folder
    against a log nobody can attribute.

    Composed from `config.INTELLIBOOKS_ROOT` at call time rather than from a
    Path constant of its own, which is `config.DELIVERY_FOLDER_NAME`'s reason:
    a test that pins `INTELLIBOOKS_ROOT` pins this with it.
    """
    if not client_id or Path(client_id).name != client_id or client_id in (
            ".", ".."):
        return None
    directory = config.INTELLIBOOKS_ROOT / config.DELIVERY_FOLDER_NAME
    return directory / f"{client_id}{config.DELIVERY_LOG_SUFFIX}"


def _record_delivery(client_id: str, receipt_id: str, destination: Path,
                     client_folder: Path) -> None:
    """Append one line to this client's delivery log. Step 10az.

    **One line per document actually written**, so the set of lines and the set
    of files in the folder answer the same question, which is what step 10au is
    for. Nothing is written on the identical-bytes skip: that document is
    already there and already has the line the copy which put it there wrote,
    and a second would count one file twice.

    **NDJSON, and the field names are `receipt_events_{firm_id}.ndjson`'s own.**
    Amendment 291 makes that log the convention for an event on this project and
    amendment 456 asked for these names to be confirmed against it rather than
    taken from the brief. `_log_receipt()` in `app.py` and its near-copy in
    `worker/extraction_pipeline.py` both spell the moment an event happened
    `timestamp`, so `posted_at` is not used: one spelling for one fact, rather
    than a second for the products to disagree over.
    `tests/test_delivery_log.py` reads that spelling off `app.py`'s syntax tree,
    so the two cannot drift apart in silence.

    **`document_path` is relative to the client's own folder**, per amendment
    456, and POSIX-separated. Relative, because the check that reads it walks
    one client's folder and the absolute path names a firm's top folder that is
    the firm's own and can move, per 18.2. POSIX, because a backslash is escaped
    in JSON and Desktop reads this file.

    **`pipeline_version` is read here rather than passed in.** It is not a
    parameter of `copy_for_published_receipt()` and four of that function's five
    callers have no run-level version in scope at all, so threading one would
    mean changing four signatures for a field. `config.get_pipeline_version()`
    is the same function `process_once()` reads the run's version from, and it
    returns `"unknown"` rather than raising when git is unavailable. **What it
    is, exactly: HEAD at the moment of the copy**, which differs from the run's
    recorded version only if a commit lands mid-run.

    **`client_folder` is passed in and `config.CLIENTS_ROOT` is not read here.**
    `tests/test_stage4_client_copy.py` enumerates every route into `Clients\\`
    from the syntax tree and caught this function reading that root on the first
    run, which is the guard doing its job: this function writes nothing there
    and has no business composing a path into it. The caller derives the folder
    from `get_client_directory()`, the same function `write_client_copy()`
    composed the destination with, so there is one composition rather than two
    that could disagree.

    **This raises on failure and the caller reports it.** Same shape as
    `ClientCopy`: only the caller knows how to say it without stopping the copy.
    """
    path = _delivery_log_path(client_id)
    if path is None:
        raise ValueError(
            f"client_id {client_id!r} does not name a file inside "
            f"{config.DELIVERY_FOLDER_NAME}, so no delivery log line can be "
            f"written for it")
    try:
        relative = destination.relative_to(client_folder).as_posix()
    except ValueError:
        # Cannot happen through write_client_copy(), which composes the
        # destination from get_client_directory(). Stated rather than assumed,
        # because the alternative is a line whose document_path is absolute and
        # which the reconciliation check would silently never match.
        raise ValueError(
            f"{destination} is not inside this client's own folder, so no "
            f"relative document_path can be written for it") from None
    entry = {
        "client_id": client_id,
        "receipt_id": receipt_id,
        "document_path": relative,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": config.get_pipeline_version(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    # Append, never truncate, and never delete. Rule 1 of CLAUDE.md, and the
    # mode the two receipt_events writers use for the same reason.
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


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
    at: str = None,
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

    ## "This never raises" was aspirational until step 10ax, 2026-09-13

    **Two writes happen here and only the first was guarded.** The file write
    sat in a `try`; the `mark_receipt_filed()` below it did not, so a locked,
    full or missing database took the exception out uncaught. Both are guarded
    now and the claim above is true.

    **Why it was not merely untidy.** Four of the five callers hold a per-item
    `try/except Exception`, so there the blast radius was one receipt, reported
    wrongly: on the three intake paths the handler writes a `failed` extraction
    row and moves the email to Failed Processing for a receipt that extracted,
    validated, published and was copied correctly. **The fifth caller,
    `_apply_attached_note()`, had no guard at all between here and
    `process_once()`, which logs and re-raises**, so it took the entire poll
    cycle with it: the remaining resolution notes, the email fetch, the inbox
    scan and both sweeps below it never ran.

    **The failure is self-healing and the log line says so.** `filed_path`
    stays NULL, which is what
    `get_published_receipts_without_client_copy()` selects on, so
    `_copy_missing_client_copies()` offers the receipt again next poll and
    10f.25's byte comparison records the document already there rather than
    writing a second one.

    `filed_path` is passed in rather than read here, because every caller has
    the receipt row in hand and a second read could disagree with the row the
    caller decided from.

    ## `at` says which moment this call is. Sub-step 10f.37, 2026-09-10

    **The firm's trigger names a moment and this parameter names the moment the
    caller is at.** They have to match for a copy to be written. `publish` is
    the default because four of the five callers are the publish path; the
    fifth is `_apply_attached_note()` in the resolution service, which passes
    `post` when IntelliBooks Desktop says a receipt is attached to a
    transaction.

    **Before this the `post` value had no mechanism and this function said so
    in a warning.** It named sub-step 10f.16, which is BUILT: 10f.12 and 10f.16
    each said the message was the other's and neither held it, so three places
    pointed elsewhere. Amendment 315 gave it a number and it is 10f.37.

    **The function's name is still true.** A receipt reaches the books through
    the drain, which needs a publish, so a receipt named by a Post-time message
    has published. See the report's question 1 for what happens if one has not.
    """
    global _POST_WARNED

    at = at or config.CLIENT_COPY_ON_PUBLISH

    if config.CLIENT_COPY_TRIGGER == config.CLIENT_COPY_NEVER:
        return None

    if config.CLIENT_COPY_TRIGGER != at:
        # This call is not the moment this firm's trigger names, so it is not
        # this call's turn. Two ways round, and only one of them needs saying.
        #
        # **A publish-time call on a `post` firm gets a line, once per
        # process.** A firm that chose `post` and silently got nothing would
        # have no way to tell it from `never`, which is what the warning this
        # replaced was for. It is INFO rather than WARNING now, because the
        # mechanism exists: this is the pipeline waiting for the message rather
        # than the pipeline unable to act. Once per process, because a real
        # firm's every receipt would otherwise carry the same line.
        #
        # **A Post-time call on a `publish` firm gets nothing here**, and its
        # own caller logs it: the copy already exists and there is nothing to
        # report from inside the gate.
        if (at == config.CLIENT_COPY_ON_PUBLISH
                and config.CLIENT_COPY_TRIGGER == config.CLIENT_COPY_AT_POST
                and not _POST_WARNED):
            _POST_WARNED = True
            logger.info(
                "%s is %r, so no copy is written into %s when a receipt "
                "publishes. The copy is written when IntelliBooks Desktop says "
                "the receipt is attached to a transaction, which is sub-step "
                "10f.37. Set %s to %r to copy on a successful publish instead.",
                config.CLIENT_COPY_TRIGGER_FIELD, config.CLIENT_COPY_AT_POST,
                config.CLIENTS_ROOT, config.CLIENT_COPY_TRIGGER_FIELD,
                config.CLIENT_COPY_ON_PUBLISH)
        return None

    if validation_status not in (OK_STATUS, config.BANK_ATTACHMENT_STATUS):
        # See the module docstring. 18.2b's folder shows the result of the work.
        #
        # **The second value is sub-step 10f.38's marker, and it is let past
        # rather than excluded.** The `ok`-only rule's own reason is that a
        # receipt with no gross is not a result: amendment 293 widened
        # publishing to all four validation statuses, so without it a `failed`
        # receipt would reach a live client folder as
        # `{date}_unknown_0.00.pdf`. **A document attached to a posted
        # transaction has none of that problem.** It was never offered to
        # extraction, so it has no validation status to pass or fail, and its
        # date, description and amount come off the transaction, which is an
        # accounting record rather than a reading of an image. 18.1: we record
        # the transaction and the document is evidence of it.
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

    if result.written:
        # **Step 10az, amendment 456. Before the database write, deliberately.**
        # The document is on disk from the line above, and this log is the
        # record of what is in the folder rather than of what the database
        # knows. `mark_receipt_filed()` below can fail, and does on a locked or
        # full database; a delivered document must still have its line when it
        # does, because step 10au reads the folder and this file and nothing
        # else.
        #
        # **Only on `result.written`.** The identical-bytes skip delivered
        # nothing: that file is already there with a line of its own from the
        # copy that wrote it, and a second line would count one file twice.
        #
        # **A failure here does not undo the copy and is not swallowed.** Step
        # 10af's decision, applied on this side: refusing would undo work that
        # succeeded, and saying nothing would leave a delivered document with no
        # record and nobody told, which is precisely what step 10au would find
        # and report as a missing delivery.
        try:
            _record_delivery(
                client_id=client_id,
                receipt_id=receipt_id,
                destination=result.path,
                # The client's own folder, one level above the IntelliBooks
                # folder inside it, derived from the same function
                # `write_client_copy()` composed the destination with rather
                # than recomposed from `config.CLIENTS_ROOT`. Two compositions
                # of one path are two that can disagree.
                client_folder=get_client_directory(client_folder_name).parent,
            )
        except Exception as error:
            logger.warning(
                "receipt %s was copied into the client folder at %s, but its "
                "delivery log line could not be written: %s: %s. The copy "
                "itself is unaffected and nothing retries this line, so "
                "reconciling that folder will report this document as one "
                "nothing recorded delivering.",
                receipt_id, result.path, type(error).__name__, error)

    # **`filed_path` is recorded on the skip as well as on the write**, and
    # that is a decision 10f.25's brief did not settle. The path is true either
    # way: this receipt's document is in the client folder, at that name. And
    # leaving it NULL would put the receipt back in
    # `get_published_receipts_without_client_copy()`, which selects on exactly
    # that column, so `_copy_missing_client_copies()` would offer it again on
    # every poll for ever and log the same skip each time.
    try:
        repo.mark_receipt_filed(receipt_id, str(result.path))
    except Exception as error:
        # **Step 10ax, 2026-09-13.** The write above was guarded and this one
        # was not, so the docstring's "this never raises" was aspirational: a
        # database that is locked, full or gone took the exception out through
        # every caller, and one of the five, `_apply_attached_note()`, has no
        # guard between here and `process_once()`, which re-raises. That took
        # the whole poll cycle down for a receipt whose document had already
        # landed correctly.
        #
        # **The path is named because the document is there.** This is the one
        # failure in this function where something was written and the record
        # of it was not, so `run.log` has to say where it is. The reader is
        # otherwise told a copy failed and will look for a file that exists.
        #
        # **Not retried here.** `filed_path` stays NULL, which is exactly what
        # `get_published_receipts_without_client_copy()` selects on, so
        # `_copy_missing_client_copies()` offers this receipt again on the next
        # poll. `write_client_copy()` compares by bytes rather than by name, so
        # that attempt finds the identical document already there and records
        # it instead of writing a second one. 10f.25.
        logger.error(
            "receipt %s was copied into the client folder at %s, but recording "
            "it failed: %s: %s. The document IS there and filed_path is still "
            "NULL, so the next poll's retry sweep will record it without "
            "writing a second copy.",
            receipt_id, result.path, type(error).__name__, error)
        return None

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

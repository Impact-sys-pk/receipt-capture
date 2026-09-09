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

**One consequence of the write stopping, flagged and NOT repaired here.**
`Repository.is_recorded_and_filed()` gates the semantic duplicate check on
`filed_path`, so with the trigger on `never` or `post` no receipt ever gets one
and that check stops flagging anything. The marker that replaces it is a
`published` row in `publish_events`, which is what amendment 293's fifth point
says sub-step 10f.24 needs, and 10f.24 is explicitly not in this stage. With the
trigger on `publish`, which is the live value, an `ok` receipt still gets a
`filed_path` and the check still works.
"""

import logging
import shutil
from pathlib import Path

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


def write_client_copy(
    source_file: Path,
    client_folder_name: str,
    tax_year: str,
    supplier: str,
    gross: float,
    invoice_date: str,
) -> Path:
    """Copy one document into the client's folder. **The only writer.**

    Image only, and the document date names both the tax year folder and the
    file: `2026-04-01_apcoa-parking_12.00.pdf`. That is the convention
    `file_receipt()` produced, kept deliberately, so a listing of `Clients\\`
    taken before this change and one taken after differ in nothing but the
    sidecar that is no longer written.

    `invoice_date` is a parameter rather than read out of a sidecar, which is
    how `file_receipt()` got it. There is no sidecar any more.
    """
    destination_dir = (get_client_directory(client_folder_name)
                       / config.CLIENT_RECEIPTS_FOLDER_NAME / tax_year)
    destination_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"{invoice_date}_{normalise_supplier(supplier)}_{gross:.2f}"
    destination = _unique_path(destination_dir, base_name, Path(source_file).suffix)
    shutil.copy2(source_file, destination)
    return destination


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

    Returns the path written, or None when nothing was written for any reason.
    Records the write with `mark_receipt_filed()`, which is the only writer of
    `filed_path` and therefore of `filed_at`.

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
        written = write_client_copy(
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

    repo.mark_receipt_filed(receipt_id, str(written))
    logger.info("receipt %s copied into the client folder at %s",
                receipt_id, written)
    return written

"""Resolution service: the one implementation all four callers go through.

Design document sections 3.2, 3.3, 4.1, 4.2 and 4.3.

This module must not import Flask, argparse, anything under `worker/email/`, or
anything that prints or reads input. That is what makes it reusable by the CLI,
the console form, the resolution back-feed and a cloud API later, and three
independent implementations of resolution is what caused the divergence this
design exists to fix.

`apply_resolution_note`, the back-feed entry point, is section 12. It parses a note
written by IntelliBooks Desktop and applies it. The file walking, and the moving of
notes to `processed\\` and `failed\\`, belong to the pipeline: 4.1 gives app.py the
job of consuming back-feed notes, and this module has no business touching folders
it was not handed.
"""

import json
import logging
import math
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import config
from worker import attached, line_items, london_time
from worker.categorisation.chart import get_chart_accounts_for_client
from worker.client_copy import (
    REMOVAL_ALREADY_GONE,
    REMOVAL_DELETED,
    copy_for_published_receipt,
    remove_client_copy,
)
from worker.categorisation.fallback import resolve_against_chart
from worker.extraction.base import ExtractionResult
from worker.filing import (
    determine_tax_year,
    make_enriched_sidecar,
    remove_review_pair,
)
from worker.validation.rules import validate

logger = logging.getLogger(__name__)

CORRECTABLE_FIELDS = (
    "supplier_name", "invoice_date", "net_amount",
    "vat_amount", "gross_amount", "receipt_ref_number", "receipt_time",
)

AMOUNT_FIELDS = ("net_amount", "vat_amount", "gross_amount")

# Design document 12.2. Bump only when both halves of the contract change.
NOTE_SCHEMA = 1

#: Sub-step 10f.37, 2026-09-10. "This receipt is attached to a transaction", so
#: on the `post` trigger its client folder copy is written now.
ATTACHED_ACTION = "attached"

#: Step 10k, 2026-09-11. "This already-filed receipt's figures were wrong and
#: these are the right ones." Amendment 235 named the word on Paul's decision
#: closing outstanding items 36 and 167, and 12.2 has carried it since.
#:
#: ## A fourth action word, and amendment 307's rule points the other way
#:
#: **307's rule is that the field chooses the path and not the action word**,
#: settled when a `filed` note's `filed_path` came to mean one of two things.
#: It does not reach this case, and the reason is what the discriminator would
#: have to be. **Nothing in the note distinguishes a correction from a settle.**
#: Both carry the same `values` and neither carries a path. The one difference
#: is that the receipt is ALREADY FILED, which is a fact about the pipeline's
#: own row and not a field Desktop can send.
#:
#: So deriving it would mean one note meaning two different things depending on
#: state this side holds, with Desktop unable to tell which happened. **A word
#: in the note says which act it is, and a pipeline that does not know the word
#: refuses the note loudly**, which is amendment 322's reasoning for `attached`
#: and is the right failure when the two halves are meant to land together.
CORRECTED_ACTION = "corrected"

NOTE_ACTIONS = ("filed", "discarded", ATTACHED_ACTION, CORRECTED_ACTION)

#: The outcomes that mean a note was applied and the caller may move it to
#: `processed\`. Anything else goes to `failed\`.
#:
#: **One definition, imported by `app.py`, added 2026-09-10 with the third
#: action.** `_consume_resolution_notes()` carried its own `("filed",
#: "discarded")` literal and this module's idempotency return carried another,
#: so a third word had to be added to two files that must agree. It was not,
#: on the first run, and every successfully applied Post-time message went to
#: `failed\` with an ERROR.
NOTE_APPLIED_OUTCOMES = ("filed", "discarded", ATTACHED_ACTION, CORRECTED_ACTION)

# The note's own timestamp, which is what 12.3 step 3 keys idempotency on.
# resolution_events has no column for it, so it lives in corrections_json, which
# is already a JSON blob and is already the record of what the note corrected.
NOTE_RESOLVED_AT_KEY = "note_resolved_at"

# Paul's decision of 2026-09-10, the first of four. The operator deleting a
# receipt from the books in IntelliBooks Desktop is asked whether the copy in
# the client folder goes too, and this is how the answer travels.
#
# **Top level, not inside `values`**, on `remember_gl_for_supplier`'s precedent:
# it is not something read off the receipt, it is what the operator asked the
# pipeline to do with one. Absent or false means today's behaviour, which is
# that nothing in the client folder is touched, so `NOTE_SCHEMA` stays 1 and
# neither half of the contract has to ship first.
#
# **No path travels with it.** `receipts.filed_path` already names the file,
# because `copy_for_published_receipt()` recorded it when it wrote the copy, and
# the composed name carries a `-2` on a collision that nothing on Desktop's side
# can tell from the original.
NOTE_DELETE_CLIENT_COPY_KEY = "delete_client_copy"

# The two things a discard records in `resolution_events.corrections_json`, per
# the brief of 2026-09-10: the path that was cleared, and the path that was
# deleted where one was. 5.1 has no column for either, and that blob is already
# where this kind of detail lives. See NOTE_RESOLVED_AT_KEY above.
EVENT_CLIENT_COPY_DELETED_KEY = "client_copy_deleted"
EVENT_FILED_PATH_CLEARED_KEY = "filed_path_cleared"

# The legacy data file beside a client folder copy, `x.pdf.json`, where one was
# there and went with the document. Added 2026-09-10 after a real orphan on
# Paul's machine: the document had been deleted and its data file had not.
# **Recorded separately from the document**, so the row can say the document
# went, the data file went, or the document went and there was no data file.
# `worker\client_copy.py`'s CLIENT_COPY_SIDECAR_SUFFIX carries the convention.
EVENT_CLIENT_COPY_SIDECAR_DELETED_KEY = "client_copy_sidecar_deleted"

# Where a Post-time message put the client folder copy, sub-step 10f.37. On the
# `publish` and `never` triggers no copy is written and the key is absent, so
# its presence is what says this note caused a file to appear.
EVENT_CLIENT_COPY_WRITTEN_KEY = "client_copy_written"

# 12.3 step 4. `source` describes the tool, `actor` describes who: for a note both
# are 'desktop', because Desktop has no user accounts. Note that the note's own
# `source` field is the receipt's intake route, carried through from the pipeline,
# and must never be read as the actor. See the 12.4 amendment of 2026-07-28.
DESKTOP_ACTOR = "desktop"
DESKTOP_SOURCE = "desktop"

# The audit row one learned mapping leaves, sub-step 10j.11. `actor` is the
# operator and not the machine, because a person ticked the box; contrast
# fallback.py's `chart_fallback` row, whose actor is "pipeline" precisely because
# no person did it. That row, amendment 227, is the precedent for recording this
# as an event of its own rather than in the correction columns of
# `categorisations`, which mean "a person changed the category" and would make a
# learned mapping indistinguishable from a correction. 11.3 asks for the choice
# to be recorded in `resolution_events.corrections_json`, and this row is where
# it is: the tick, the vendor and both codes are in that blob.
LEARN_ACTION = "learn_vendor"
LEARN_OUTCOME = "learned"

# Plain decimal only. No thousands separators, no currency symbols, no more
# than two decimal places. Rejecting is deliberate: stripping a "£" or a comma
# would be guessing at an operator's intent on a financial figure.
_AMOUNT_RE = re.compile(r"^-?(\d+(\.\d{1,2})?|\.\d{1,2})$")

# YYYY-MM-DD, zero-padded. strptime alone accepts "2026-7-5", which we do not.
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# A master account code is four digits, and any three-digit code is legacy per
# amendment 96. Used in one place only, to read a note written before Desktop
# gained `category_code`; see the older-note rule in parse_resolution_note().
_ACCOUNT_CODE_RE = re.compile(r"^\d{4}$")


@dataclass
class ResolutionView:
    """Everything needed to render a receipt for correction. Read-only.

    The console's detail page and the CLI both render this, so the two cannot
    drift into showing different things.
    """
    receipt: Dict[str, Any]
    extraction: Optional[Dict[str, Any]]        # latest, the one being corrected
    extraction_history: List[Dict[str, Any]]    # all, newest first
    categorisation: Optional[Dict[str, Any]]    # may be None; the non-ok path saves none
    resolution_events: List[Dict[str, Any]]
    duplicate_of_receipt: Optional[Dict[str, Any]]      # when status == 'possible_duplicate'
    duplicate_of_extraction: Optional[Dict[str, Any]]
    client_name: str
    business_type: str
    gl_code_options: List[Dict[str, Any]]
    effective_gl_code: Optional[str]            # correction_code if set, else suggested_code
    file_path: str
    is_locked: bool                             # informational only


@dataclass
class Corrections:
    values: Dict[str, Any] = field(default_factory=dict)  # only fields explicitly supplied
    gl_nominal_code: Optional[str] = None
    gl_account_name: Optional[str] = None
    gl_correction_reason: Optional[str] = None
    remember_gl_for_supplier: bool = False


@dataclass
class ResolutionOutcome:
    outcome: str    # filed | discarded | still_invalid | stale | locked | not_found | already_filed | error
    receipt_id: str
    extraction_id: Optional[str] = None
    filed_path: Optional[str] = None
    category_code: Optional[str] = None
    category_name: Optional[str] = None
    category_confidence: Optional[str] = None
    validation_notes: List[str] = field(default_factory=list)
    message: str = ""               # safe to show an operator
    error_detail: Optional[str] = None  # logs only, never rendered
    # The two things a discard now has to be able to report, added 2026-09-10.
    # **`discard_receipt()` is the only thing that sets either**, and every
    # other construction site leaves both None, which is what the defaults are
    # for: there were fifteen of those and none of them is about a client
    # folder copy.
    #
    # `filed_path_cleared` is the path that WAS in `filed_path` before the
    # discard forgot it. **It is deliberately not `filed_path` above**, which
    # means "this is where the receipt is filed": on a discard the receipt is
    # not filed anywhere, and reusing the field would make an outcome that
    # reads as a filing. `filed_path` has no production reader at all, which is
    # exactly why reusing it would have gone unnoticed.
    #
    # `client_copy_deleted` is the document that was deleted, where the caller
    # asked and it worked. The two together are what let an operator be told
    # the difference between a copy that has gone and one that has been left.
    # The data file is NOT here: no command-line caller can produce one, and
    # `run.log` and the audit row carry it.
    filed_path_cleared: Optional[str] = None
    client_copy_deleted: Optional[str] = None


def parse_corrections(raw: dict) -> Tuple[Corrections, Dict[str, str]]:
    """Normalise operator input. Returns (corrections, field_errors). Never raises.

    Key presence, never truthiness:

    - A key absent from `raw`, or `None`, is omitted from `values`.
    - An empty (or whitespace-only) string means "clear this field", recorded as
      `None`. Distinct from omission, so an operator can remove a wrongly
      extracted reference number.
    - Amounts coerce to float. `"0"` and `"0.00"` are valid and become `0.0`.
    - `invoice_date` must be YYYY-MM-DD and a real calendar date. Other formats
      are a field error, not something to reparse: guessing here would undo the
      day-first handling in `openai_vision.py`.
    - Bad input becomes a field error keyed by field name. Nothing raises.

    Keys outside CORRECTABLE_FIELDS are ignored, so a web form's own fields
    (CSRF token, buttons) can be passed straight through.
    """
    values: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    if not isinstance(raw, dict):
        return Corrections(values=values), {"_form": "corrections must be a mapping of field names to values"}

    for name in CORRECTABLE_FIELDS:
        if name not in raw:
            continue

        supplied = raw[name]
        if supplied is None:
            continue

        if isinstance(supplied, str):
            text = supplied.strip()
            if text == "":
                values[name] = None  # explicit clear
                continue
        elif name in AMOUNT_FIELDS and isinstance(supplied, (int, float)) and not isinstance(supplied, bool):
            # Already typed, e.g. argparse's type=float. 0.0 must survive.
            values[name] = float(supplied)
            continue
        else:
            errors[name] = f"expected text, got {type(supplied).__name__}"
            continue

        if name in AMOUNT_FIELDS:
            if not _AMOUNT_RE.match(text):
                errors[name] = (
                    f"'{supplied}' is not a plain amount. Use digits and at most two "
                    "decimal places, with no currency symbol and no thousands separator."
                )
                continue
            values[name] = float(text)
        elif name == "invoice_date":
            if not _ISO_DATE_RE.match(text):
                errors[name] = f"'{supplied}' is not a date in YYYY-MM-DD form."
                continue
            try:
                datetime.strptime(text, "%Y-%m-%d")
            except ValueError:
                errors[name] = f"'{supplied}' is not a real calendar date."
                continue
            values[name] = text
        else:
            values[name] = text

    return Corrections(values=values), errors


class ResolutionNoteError(ValueError):
    """A note that cannot be applied as written.

    The message is written to the `.error.txt` beside the note in `failed\\`, so it
    is read by a human deciding whether the pipeline or Desktop is at fault. Say
    which field and why.
    """


@dataclass
class ResolutionNote:
    """A parsed, normalised back-feed note. Design document 12.2."""
    action: str                             # 'filed' | 'discarded'
    resolved_at: str
    receipt_id: Optional[str] = None        # may be null; then match on filenames
    client_id: Optional[str] = None
    resolved_by: Optional[str] = None
    values: Dict[str, Any] = field(default_factory=dict)
    category_name: Optional[str] = None
    category_code: Optional[str] = None
    # **Optional even for a `filed` note, since 2026-09-09, and its presence is
    # what chooses between the two things such a note can mean.** Sub-step
    # 10f.14: with it, "Desktop filed this at that path"; without it, "these are
    # the corrected values, settle this receipt". See `parse_resolution_note()`.
    filed_path: Optional[str] = None
    # Read by `_receipt_for_note()` as the fallback that finds a receipt when the
    # note carries no `receipt_id`, matching each basename against
    # `receipts.filename`. **Desktop now sends the INBOX item, `{receipt_id}.json`,
    # rather than the review pair**, and that never matches an original
    # attachment name, so the fallback no longer works for a Desktop note.
    # Flagged in `2026-09-09_REPORT_claude_code_desktop_note.md`; harmless today
    # because `fileReviewReceipt()` always sends `receipt_id`.
    original_review_files: List[str] = field(default_factory=list)
    reason: Optional[str] = None
    # 11.3's opt-in tick, carried at the top level of the note rather than inside
    # `values`: it is not something read off the receipt, it is what the operator
    # asked the pipeline to do with one. Absent means False, which is what every
    # note written before 2026-09-05 means.
    remember_gl_for_supplier: bool = False
    # Paul's decision of 2026-09-10. The operator deleting a receipt from the
    # books said the copy in the client folder should go too. Absent means False,
    # which is what every note written before 2026-09-10 means, and False is
    # today's behaviour: nothing in the client folder is touched.
    # See NOTE_DELETE_CLIENT_COPY_KEY, and `discard_receipt()` for what it does.
    delete_client_copy: bool = False


def _note_text(raw: Dict[str, Any], key: str) -> Optional[str]:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ResolutionNoteError(f"'{key}' must be text, got {type(value).__name__}")
    return value.strip() or None


def _note_flag(raw: Dict[str, Any], key: str) -> bool:
    """One of the note's top-level booleans. Absent means False.

    **A non-boolean is refused rather than coerced.** Both flags this serves
    decide something durable and irreversible: `remember_gl_for_supplier`
    writes into the client's mapping table, which layer 1 then reads back as an
    exact match with confidence `high`, and `delete_client_copy` deletes a file.
    `"false"` is a true string in every language that would send one, and `0`
    and `1` are the shapes a form serialiser reaches for, so all of them are
    errors here rather than guesses.

    **One reader for both flags, added 2026-09-10 with the second of them.**
    `remember_gl_for_supplier` was parsed by six lines saying exactly this and
    the new field would have been a second copy of them. Behaviour is unchanged
    for it, message included.
    """
    value = raw.get(key, False)
    if not isinstance(value, bool):
        raise ResolutionNoteError(
            f"'{key}' must be true or false, got {type(value).__name__}")
    return value


def _note_amount(value: Any, key: str) -> Optional[float]:
    """12.2: amounts are numbers, and 12.4 as amended: round to two places here.

    A string is rejected rather than coerced. Bug 3.3 exists because string amounts
    reached `validate()` and raised TypeError on `round()`, and the fix was to stop
    strings entering rather than to coerce them in a second place. Integers are
    accepted: JavaScript writes `"net": 80`, not `80.0`.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ResolutionNoteError(
            f"'{key}' must be a JSON number, got {type(value).__name__}. "
            "12.2 forbids strings for amounts."
        )
    if not math.isfinite(value):
        raise ResolutionNoteError(f"'{key}' is not a finite number")
    return round(float(value), 2)


def parse_resolution_note(raw: Any) -> ResolutionNote:
    """Validate and normalise a note. Raises ResolutionNoteError, never returns junk.

    Strict on purpose. The other half of this contract is built by a session that
    cannot see this one, so a note that does not match 12.2 is worth surfacing in
    `failed\\` rather than half-applying. The one deliberate leniency is that extra
    keys are ignored, so the contract can gain a field without every note failing.
    """
    if not isinstance(raw, dict):
        raise ResolutionNoteError(f"a note must be a JSON object, got {type(raw).__name__}")

    schema = raw.get("schema")
    if schema != NOTE_SCHEMA:
        raise ResolutionNoteError(
            f"unsupported note schema {schema!r}; this pipeline understands {NOTE_SCHEMA}"
        )

    action = raw.get("action")
    if action not in NOTE_ACTIONS:
        raise ResolutionNoteError(
            f"'action' must be one of {NOTE_ACTIONS}, got {action!r}"
        )

    resolved_at = _note_text(raw, "resolved_at")
    if not resolved_at:
        raise ResolutionNoteError("'resolved_at' is required: it is the idempotency key")

    review_files = raw.get("original_review_files") or []
    if not isinstance(review_files, list) or not all(isinstance(f, str) for f in review_files):
        raise ResolutionNoteError("'original_review_files' must be a list of filenames")

    # 11.3's opt-in tick, sub-step 10j.11, and Paul's delete flag of 2026-09-10.
    # Both are top level rather than inside `values`, and absent means False, so
    # a note written before either field existed parses exactly as it did
    # before. `_note_flag()` carries why a non-boolean is refused.
    remember = _note_flag(raw, "remember_gl_for_supplier")
    delete_client_copy = _note_flag(raw, NOTE_DELETE_CLIENT_COPY_KEY)

    note = ResolutionNote(
        action=action,
        resolved_at=resolved_at,
        receipt_id=_note_text(raw, "receipt_id"),
        client_id=_note_text(raw, "client_id"),
        resolved_by=_note_text(raw, "resolved_by"),
        original_review_files=list(review_files),
        reason=_note_text(raw, "reason"),
        remember_gl_for_supplier=remember,
        delete_client_copy=delete_client_copy,
    )

    if action != "discarded" and delete_client_copy:
        # A contradiction rather than a shape the contract forbids, so it is
        # said out loud and ignored, which is the treatment the discard branch
        # below already gives `values` and `filed_path`. The field means "the
        # operator deleted this receipt and asked for its copy to go with it",
        # and a note that files or settles a receipt is not that.
        logger.warning(
            f"the note for {note.receipt_id} has action {action!r} and carries "
            f"'{NOTE_DELETE_CLIENT_COPY_KEY}', which only a discard can mean; "
            "ignoring it and deleting nothing"
        )
        note.delete_client_copy = False

    if action in ("discarded", ATTACHED_ACTION):
        # 12.2: values and filed_path are absent for a discard. Present-and-ignored
        # rather than rejected: refusing a legitimate discard over a harmless extra
        # key would be the wrong trade, and the warning is enough to spot drift.
        #
        # **An `attached` note is the same shape and for a sharper reason.**
        # Sub-step 10f.37: the pipeline composes the client folder name itself,
        # and a name composed by Desktop cannot tell a collision's `-2` from
        # its original, so a path here is a Desktop that has misread the
        # contract. Ignored, and said out loud so that does not go on.
        for unexpected in ("values", "filed_path"):
            if raw.get(unexpected) is not None:
                logger.warning(
                    f"{action} note for {note.receipt_id} carries '{unexpected}', which 12.2 "
                    f"says is absent for a {action} note; ignoring it"
                )
        return note

    # **`filed_path` is OPTIONAL from 2026-09-09, and its presence chooses which
    # of two things this note means.** Sub-step 10f.14, and Paul's decision.
    #
    # ~~`filed_path` is required for a filed note.~~ **Struck.** It was required
    # because a `filed` note meant "Desktop has already put the image at this
    # path". Amendment 299 stopped `fileReviewReceipt()` writing into `Clients\`
    # at all, correctly: the pipeline is the only writer there and the firm's
    # `client_copy_trigger` decides whether a copy happens, so a path from
    # Desktop would be one product naming the other's file. **The refusal was
    # left in place and it was a live fault**: receipt
    # a587b166-35a1-473c-aa5a-409749f7b642 went into the books in Desktop and
    # stayed `failed` in the database with no `resolution_events` row, which is
    # the disagreement section 12 exists to prevent.
    #
    # **With the field: "Desktop filed this at that path."** `_apply_filed_note()`
    # records it and writes nothing. Kept because older notes carry it, they are
    # still on disk, and any other writer may still send one.
    #
    # **Without it: "these are the corrected values, settle this receipt."**
    # `_settle_note()` hands them to `resolve_receipt()`, the path the console and
    # the CLI use, which writes the client folder copy itself on the trigger.
    #
    # **`action` stays `filed` for both**, which is a decision and not an
    # oversight; see `_settle_note()`.
    if action == CORRECTED_ACTION:
        # **Step 10k. A correction names no path, and one here is ignored
        # rather than refused.** The receipt was filed earlier, the pipeline
        # holds the path in `receipts.filed_path`, and 18.2b says a copy is
        # never withdrawn, so there is nothing for a path to mean.
        #
        # **Ignored rather than refused, and that is amendment 306's lesson
        # applied before it can happen again.** A refusal puts the note in
        # `failed\` and leaves the database holding figures the books have
        # already replaced, which is the one disagreement section 12 exists to
        # prevent. The warning is what surfaces a Desktop that has misread the
        # contract, and it costs nothing.
        if raw.get("filed_path") is not None:
            logger.warning(
                f"{action} note for {note.receipt_id} carries 'filed_path', "
                "which a correction never sets: the receipt was filed earlier "
                "and this pipeline holds the path. Ignoring it"
            )
    else:
        note.filed_path = _note_text(raw, "filed_path")

    raw_values = raw.get("values")
    if not isinstance(raw_values, dict):
        raise ResolutionNoteError(
            f"'values' must be an object for a {action} note")

    values: Dict[str, Any] = {}
    for name in CORRECTABLE_FIELDS:
        if name not in raw_values:
            continue
        supplied = raw_values[name]
        if name in AMOUNT_FIELDS:
            values[name] = _note_amount(supplied, name)
        elif supplied is None:
            values[name] = None
        elif isinstance(supplied, str):
            values[name] = supplied.strip() or None
        else:
            raise ResolutionNoteError(
                f"'values.{name}' must be text, got {type(supplied).__name__}"
            )

    if not values.get("supplier_name"):
        raise ResolutionNoteError(
            f"'values.supplier_name' is required for a {action} note")
    if values.get("gross_amount") is None:
        raise ResolutionNoteError(
            f"'values.gross_amount' is required for a {action} note")

    invoice_date = values.get("invoice_date")
    if not invoice_date:
        raise ResolutionNoteError(
            f"'values.invoice_date' is required for a {action} note")
    if not _ISO_DATE_RE.match(invoice_date):
        raise ResolutionNoteError(
            f"'values.invoice_date' must be YYYY-MM-DD, got {invoice_date!r}"
        )
    try:
        datetime.strptime(invoice_date, "%Y-%m-%d")
    except ValueError:
        raise ResolutionNoteError(f"'values.invoice_date' is not a real date: {invoice_date!r}")

    currency = raw_values.get("currency")
    if currency is not None and not isinstance(currency, str):
        raise ResolutionNoteError("'values.currency' must be text")
    values["currency"] = (currency or config.DEFAULT_CURRENCY).strip() or config.DEFAULT_CURRENCY

    # 12.2 as amended 2026-09-05 by amendment 231. **Desktop sends the code in
    # `values.category_code` and the name in `values.category_name`**, and both
    # are optional. An empty string is the common case, because Desktop does not
    # require a category before filing, and it means "no category".
    #
    # ~~A name, never a code: Desktop has no codes.~~ **Struck.** `catOptions()`
    # at IntelliBooks-Desktop-v3.html:2610 builds each option with the code as
    # its value and `fileReviewReceipt()` at :3392 writes that value into
    # `category_name`, so **every note written before the Desktop half of 10j.11
    # ships carries a four-digit code in `category_name` and no `category_code`
    # at all.** That is the older-note rule below, and it exists because the two
    # halves of this contract are built by sessions that cannot see each other
    # and neither can be made to ship first.
    #
    # **When it can be removed:** once no unapplied note predates the Desktop
    # change. That is checkable rather than a matter of judgement, because
    # nothing in `Resolutions\` is ever deleted: when the oldest file in
    # `Intellibills\Resolutions\` postdates the Desktop release, no note that
    # needs the rule can still arrive, and the four lines go. Until then,
    # dropping it would file a real account code as if it were a caption.
    category = raw_values.get("category_name")
    if category is not None and not isinstance(category, str):
        raise ResolutionNoteError("'values.category_name' must be text")
    note.category_name = (category or "").strip() or None

    code = raw_values.get("category_code")
    if code is not None and not isinstance(code, str):
        raise ResolutionNoteError("'values.category_code' must be text")
    note.category_code = (code or "").strip() or None

    if (not note.category_code and note.category_name
            and _ACCOUNT_CODE_RE.match(note.category_name)):
        note.category_code = note.category_name
        note.category_name = None
        logger.info(
            f"note for {note.receipt_id} carries {note.category_code!r} in "
            "category_name and no category_code, so it was written before Desktop "
            "gained the field and the value is read as the code it is"
        )

    note.values = values
    return note


def resolve_practice_path(filed_path: str) -> Path:
    """12.2: `filed_path` is relative to the practice root, with backslashes.

    Resolved against config.PRACTICE_ROOT at call time. An absolute path is used as
    given, which costs nothing and means a note written by a future tool that
    happens to be absolute is not silently misread as a relative one.
    """
    candidate = Path(str(filed_path).replace("\\", "/"))
    if candidate.is_absolute():
        return candidate
    return config.PRACTICE_ROOT / candidate


def _client_details(client_id: Optional[str]) -> Tuple[str, str, Optional[str]]:
    """(client_name, trade, client_folder_name) for a client_id.

    Sub-steps 10d.13 and 10d.14. Keyed on client_id, because there is no client
    code any more, and the folder name is returned rather than derived from the
    display name: `client_name` is freely editable and is never used to build a
    path, `client_folder_name` is fixed once a folder exists.

    An unresolved client returns None for the folder, and the caller must not
    file into Clients on that. That is 10d.18 and it is the whole point: the
    lookup that used to substitute the code for the name whenever it missed is
    what filed four receipts into a folder IntelliBooks does not read.
    """
    entry = config.CLIENTS_BY_ID.get(client_id or "") or {}
    return (
        entry.get("client_name") or (client_id or "UNKNOWN"),
        entry.get("trade", "UNSPECIFIED"),
        entry.get("client_folder_name") or None,
    )


def get_resolution_view(repo, receipt_id) -> Optional[ResolutionView]:
    """Read-only. Takes no lock. None if the receipt does not exist.

    Deliberately does not decide policy. A receipt with no extraction still gets a
    view, with `extraction` as None; whether that is `not_found` is
    `resolve_receipt()`'s judgement, and the console needs to render the receipt
    either way.
    """
    receipt = repo.get_receipt(receipt_id)
    if not receipt:
        return None

    history = repo.get_extractions_for_receipt(receipt_id)
    latest = history[0] if history else None
    categorisation = repo.get_categorisation_for_receipt(receipt_id)

    effective_gl_code = None
    if categorisation:
        effective_gl_code = (
            categorisation.get("correction_code") or categorisation.get("suggested_code")
        )

    duplicate_of_receipt = None
    duplicate_of_extraction = None
    duplicate_of = receipt.get("duplicate_of")
    if duplicate_of:
        duplicate_of_receipt = repo.get_receipt(duplicate_of)
        if duplicate_of_receipt:
            duplicate_of_extraction = repo.get_extraction_for_receipt(duplicate_of)

    client_name, business_type, _folder = _client_details(receipt.get("client_id"))

    return ResolutionView(
        receipt=receipt,
        extraction=latest,
        extraction_history=history,
        categorisation=categorisation,
        resolution_events=repo.list_resolution_events(receipt_id),
        duplicate_of_receipt=duplicate_of_receipt,
        duplicate_of_extraction=duplicate_of_extraction,
        client_name=client_name,
        business_type=business_type,
        # Fallback per 11.1 until the Default CoA is loaded at step 12. The
        # console shows a banner saying the CoA has not been loaded.
        gl_code_options=repo.list_gl_code_options_from_vendors(),
        effective_gl_code=effective_gl_code,
        file_path=receipt.get("file_path"),
        is_locked=receipt.get("locked_at") is not None,
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record_event(repo, receipt_id, actor, source, action, outcome,
                  extraction_id=None, corrections=None, gl_override_code=None,
                  reason=None, note_resolved_at=None, detail=None) -> None:
    """One audit row per resolution.

    Written for filed, discarded and still_invalid only. Not for not_found, stale
    or locked, because nothing happened. Not for error either: the state is
    unknown at that point and a second write risks compounding it, so the logged
    traceback is the record. See the 2026-07-27 amendment to 4.2.

    note_resolved_at is the back-feed's idempotency key, stored in corrections_json
    because 5.1 has no column for it. See NOTE_RESOLVED_AT_KEY.

    `detail` is anything else the caller wants on the row, merged into the same
    blob. Added 2026-09-10 for the two paths a discard records: the client
    folder copy it deleted and the `filed_path` it cleared. **Merged last and
    deliberately**, so a key of the same name in `corrections.values` cannot
    silently take its place; nothing named in `CORRECTABLE_FIELDS` collides
    with either today, and this is what keeps that true.
    """
    payload: Dict[str, Any] = {}
    if corrections is not None and corrections.values:
        payload.update(corrections.values)
    if note_resolved_at:
        payload[NOTE_RESOLVED_AT_KEY] = note_resolved_at
    if detail:
        payload.update(detail)
    corrections_json = json.dumps(payload, sort_keys=True, default=str) if payload else None
    repo.save_resolution_event(
        event_id=str(uuid.uuid4()),
        receipt_id=receipt_id,
        extraction_id=extraction_id,
        actor=actor,
        source=source,
        action=action,
        outcome=outcome,
        created_at=_now(),
        corrections_json=corrections_json,
        gl_override_code=gl_override_code,
        reason=reason,
    )


def _record_vendor_learned(repo, receipt_id, extraction_id, client_id, vendor_key,
                           vendor_name, code, account_name, note_resolved_at) -> None:
    """One audit row per mapping learned from a back-feed note. Sub-step 10j.11.

    Its own row rather than a field on the filing's row, so a filing that taught
    something is distinguishable from one that did not by a query and not by
    reading a blob: `action = 'learn_vendor'`. The precedent is amendment 227,
    which made the chart substitution an event of its own for the same reason and
    for one more that applies here: the `categorisations` correction columns mean
    "a person changed the category", and a mapping written into them would be
    indistinguishable from a correction except by reading the reason text.

    **`actor` is the operator, not the machine.** fallback.py's substitution row
    writes actor "pipeline" precisely because no person decided it; here a person
    ticked a box, and the whole point of 11.3's opt-in is that a human is on the
    record for it.

    11.3 says "record the choice in `resolution_events.corrections_json`", and
    this is where it is recorded: the tick, the vendor, and both codes.

    Written directly rather than through `_record_event()`, which is documented as
    one row per resolution outcome and is what writes the `filed` row beside this
    one. Learning is not an outcome of the resolution; it is a second thing the
    same note asked for, and it can fail to happen while the filing succeeds.
    """
    repo.save_resolution_event(
        event_id=str(uuid.uuid4()),
        receipt_id=receipt_id,
        extraction_id=extraction_id,
        actor=DESKTOP_ACTOR,
        source=DESKTOP_SOURCE,
        action=LEARN_ACTION,
        outcome=LEARN_OUTCOME,
        corrections_json=json.dumps({
            "remember_gl_for_supplier": True,
            "client_id": client_id,
            "vendor_key": vendor_key,
            "vendor_name": vendor_name,
            "nominal_code": code,
            "account_name": account_name,
            NOTE_RESOLVED_AT_KEY: note_resolved_at,
        }, sort_keys=True, default=str),
        gl_override_code=code,
        reason=(
            f"the operator ticked remember this supplier, and {vendor_key} now maps "
            f"to {code} {account_name} for client {client_id}"
        ),
        created_at=_now(),
    )


#: The status a receipt carries when the semantic duplicate check found an
#: earlier receipt with the same supplier, date and gross.
#: `worker\extraction_pipeline.py` writes it and this module watches for it in
#: two places: `preserve_status`, which stops a failed re-validation overwriting
#: it, and the warning in `resolve_receipt()` that says when a correction has
#: cleared it.
#:
#: **One constant rather than two literals in one function.** They have to agree
#: and nothing would make them, which is the drift this project's own trap list
#: objects to. `tests/test_service_corrections.py` reads the value back off
#: `extraction_pipeline.py`'s own source, so a rename there goes red rather than
#: leaving this module watching for a status nothing writes.
POSSIBLE_DUPLICATE_STATUS = "possible_duplicate"

#: The `match_source` layer 5 writes, and the only one the confirm case can
#: arise on. Amendment 238: "The confirm case exists only on a layer 5 answer. A
#: layer 1 or layer 2 match returns a stored code and there is no suggestion out
#: of the 66 to agree with, and layer 2 already holds any mapping it would
#: learn."
#:
#: **Deliberately not `publish.MACHINE_MATCH_SOURCES`**, which is step 10l's set
#: and holds the two fuzzy layers as well. A fuzzy match returns a STORED
#: mapping's code, so there is nothing for the operator to confirm and no
#: receipt account behind it. Step 10l's set answers "did a machine choose
#: this"; this answers "did the classifier propose an account out of the
#: shipped list", and they are different questions that happen to overlap.
CLASSIFIER_MATCH_SOURCE = "ai"

#: The two `chart_outcome` values where the chart check actually resolved the
#: classifier's suggestion to an account.
#:
#: **`unreadable_chart` is excluded and that is a narrowing, stated rather than
#: assumed.** Amendment 238's rule compares the operator's code with "the code
#: the chart check resolved the classifier's suggestion to". On an unreadable
#: chart that check did not run: `resolve_against_chart()` leaves the code
#: standing unchecked and forces `needs_review`. So the rule's own input does
#: not exist, and writing a firm row on a comparison against an unchecked code
#: is precisely the failure amendment 238 exists to prevent, in its words "a
#: firm-wide mapping learned from a code whose meaning was never established,
#: applied confidently by layer 2 to every client of that trade".
#:
#: `_resolve_category()` already refuses to teach the CLIENT table on an
#: unreadable chart, for the same reason and in the same words. This is that
#: rule held at the wider-reaching table.
#:
#: `unusable` is excluded too, and there it makes no difference: that branch
#: sets `suggested_code` to None, so the comparison below could never be equal.
CHART_CHECK_RESOLVED = ("in_chart", "substituted")


def _learn_firm_mapping_if_confirmed(repo, receipt, categorisation, chosen_code,
                                     vendor_key, vendor_name):
    """Teach the firm pool where the operator's code confirms the classifier.

    **Step 10m, amendment 238, and the rule is Paul's.** The operator's chosen
    code is compared with the code the chart check resolved the classifier's
    suggestion to.

    - **Equal**: the receipt account is known, because it is the account out of
      the shipped list that the classifier named, so the firm table is written
      with THAT account and not with the operator's code.
    - **Different**: the receipt account is not knowable. Several master codes
      collapse into one under the chart fallback and the operator's pick cannot
      be run backwards, so nothing is written here. The caller has already
      written the client table, which is scoped to one client and is safe.

    **The tick is the caller's to check**, per 11.3, because the caller already
    checks it before writing the client table and two places reading one flag
    is how the two routes would drift apart.

    Returns `(code, name)` if a row was written, else None, so the caller can
    log what happened rather than guess.

    ## Why it is one helper called from two places

    **Paul's decision, 2026-09-12.** There are two learning sites,
    `resolve_receipt()` and `_apply_filed_note()`, and they do not behave the
    same way: their guards differ, one requires the operator's code to be
    chart-confirmed and the other does not. A rule live on one route and absent
    from the other is the half-built change this project has paid for before, so
    the decision is written once and both routes call it.

    **It supersedes amendment 231's point two in this one case, and only this
    one.** That amendment says a Desktop correction writes the client table
    only, and its stated reason is that the receipt account cannot be recovered
    from an operator's chart code, `7310`, `7391` and `7392` all resolving into
    `7310`. **That reason is amendment 238's "Different" half.** 238 carves out
    the single case where the account IS known, because the classifier named it.
    Everything else amendment 231 decided stands.
    """
    if categorisation.match_source != CLASSIFIER_MATCH_SOURCE:
        return None
    if categorisation.chart_outcome not in CHART_CHECK_RESOLVED:
        return None

    resolved = (categorisation.suggested_code or "").strip()
    if not resolved or (chosen_code or "").strip() != resolved:
        return None

    # The account the CLASSIFIER named, which is the one out of the shipped
    # receipt-account list. `original_code` is set only where a substitution
    # moved `suggested_code` off it, so on `in_chart` the suggestion is itself
    # what layer 5 said. Writing `suggested_code` unconditionally would teach
    # the shared pool this client's fallback account instead.
    code = categorisation.original_code or categorisation.suggested_code
    name = categorisation.original_name or categorisation.suggested_name
    if not code:
        return None

    repo.upsert_firm_vendor(
        business_type=categorisation.business_type,
        vendor_key=vendor_key,
        nominal_code=code,
        account_name=name,
        last_updated=_now(),
        vendor_name=vendor_name,
        firm_id=receipt.get("firm_id"),
    )
    return code, name


def _override(value: Optional[str]) -> Optional[str]:
    """Treat an empty or whitespace-only GL field as no override at all."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _merge_corrections(extraction: Dict[str, Any], corrections: Corrections) -> Dict[str, Any]:
    """Step 5. Merge over the existing extraction by key presence, not truthiness.

    A supplied 0.0 is falsy, so an `or` here would keep the wrong extracted value
    and make correcting VAT to zero impossible. That was design document 3.2.
    """
    merged = {name: extraction.get(name) for name in CORRECTABLE_FIELDS}
    merged.update(corrections.values)
    merged["currency"] = extraction.get("currency") or config.DEFAULT_CURRENCY
    return merged


def resolve_receipt(repo, categorisation_engine, receipt_id, corrections,
                    actor, source, expected_extraction_id=None,
                    note_resolved_at=None,
                    decided_by_operator=False,
                    filing_already_settled=False) -> ResolutionOutcome:
    """Apply corrections, re-validate, categorise, file. Append-only throughout.

    Design document 4.3. The step numbers in the comments below are that section's,
    and steps 7 and 8 must not be reordered: categorisations.extraction_id has a
    foreign key to extractions, and getting it backwards caused the live
    IntegrityError fixed in b480a7e.

    actor is who did it; source is which tool they used, 'console' | 'cli' |
    'desktop'. Both are required: a default would be wrong for three of the four
    callers and the point of the column is that nobody has to guess.

    **`note_resolved_at` is the back-feed's idempotency key and is None for
    everybody but `_settle_note()`.** Added 2026-09-09 by sub-step 10f.14. 12.3
    step 3 keys "has this note already been applied" on the note's own
    timestamp, which `_note_already_applied()` reads out of
    `resolution_events.corrections_json`. This function knew nothing about notes,
    so without it a settle note put back by hand would be applied twice: a
    second `manual_correction` row and a second client folder copy.

    **It is recorded on the `filed` event only, and not on `still_invalid`.**
    `_note_already_applied()` returns any event carrying the key, and
    `apply_resolution_note()` then reports the note as applied and its caller
    moves it to `processed\\`. Stamping a failed attempt would therefore turn a
    retry into a silent success. `_apply_filed_note()` records it in the same one
    place for the same reason.

    **`decided_by_operator` says that a person has already acted on this receipt
    elsewhere, so a failed check is recorded rather than used to block.** Default
    False, added 2026-09-09 by amendment 307 and Paul's decision.
    `_settle_note()` is the only production caller that passes True, and
    `tests/test_resolution_service.py`'s `DecidedByOperatorTest` enumerates the
    set from the syntax tree.

    **What it is for.** A `filed` note with no `filed_path` means "settle this
    receipt", and by the time one arrives the row is already in the books in
    IntelliBooks Desktop. A `still_invalid` receipt then leaves the database
    disagreeing with the books, which is the one thing amendment 306's contract
    exists to prevent. `_apply_filed_note()` has always forced `ok` for exactly
    this reason, in 12.3 step 5's words: a human filed this.

    **What it does not change.** `validate()` still runs and still produces its
    notes; they go on the extraction row and into `run.log`. **No figure is
    recalculated**, which 18.4 forbids in terms. And it does not open the
    `client_folder_name` gate below: that is a registry fault rather than a
    judgement about a receipt, and an operator who decides a receipt is right
    cannot decide that a client has a folder.

    **Two failures can reach it and no more**, enumerated from `validate()`'s own
    syntax tree and held by `tests/test_resolution_backfeed.py`: a gross mismatch
    and a negative amount. `parse_resolution_note()` refuses a note that could
    produce any of the other four, so **this can only ever turn a `needs_review`
    receipt `ok`, never a `failed` one.**
    """
    # 1. Load receipt.
    receipt = repo.get_receipt(receipt_id)
    if not receipt:
        return ResolutionOutcome(
            outcome="not_found", receipt_id=receipt_id,
            message=f"Receipt not found: {receipt_id}",
        )

    # 1a. Refuse a receipt that is already filed. Nothing below inspects
    #     filed_path, so without this an ok receipt is re-filed, gets a second
    #     manual_correction row and leaves a second copy on disk under a -2 name.
    #     That is the double-filing this design exists to prevent, arriving
    #     through the front door. An expected condition, not an error: the
    #     console must be able to offer the existing file.
    #
    #     The back-feed's `filed` note is the one legitimate re-file and does not
    #     come through here; 12.3 step 5 calls mark_receipt_filed() directly.
    #
    #     **`filing_already_settled` is the one thing that passes it, step 10k.**
    #     A `corrected` note says the figures on an ALREADY FILED receipt were
    #     wrong, so being filed is the premise of the call rather than an error
    #     in it. **What makes that safe is not this line**: it is that the same
    #     keyword skips the client folder copy at step 11 below, so the second
    #     copy this refusal exists to prevent cannot be written. The second
    #     `manual_correction` row it also mentions IS written, and that is what
    #     a correction is: `extractions` is append-only and one receipt has as
    #     many rows as it has had readings.
    filed_path = receipt.get("filed_path")
    if filed_path and not filing_already_settled:
        # filed_at is NULL for anything filed before 5.1a added the column, and is
        # deliberately not back-filled, so the date is offered when it is known and
        # left out rather than guessed when it is not.
        # Store UTC, show London, 2026-09-11. The column keeps UTC; this is
        # the sentence an operator reads back off the CLI, so it converts and
        # says BST or GMT.
        filed_at = london_time.stamp(receipt.get("filed_at"))
        when = f" on {filed_at}" if filed_at else ""
        return ResolutionOutcome(
            outcome="already_filed", receipt_id=receipt_id,
            extraction_id=(repo.get_extraction_for_receipt(receipt_id) or {}).get("extraction_id"),
            filed_path=filed_path,
            message=(
                f"This receipt has already been filed{when}, as {filed_path}. "
                "Nothing was changed. Open that file to check it, or discard the "
                "receipt if it was filed in error."
            ),
        )

    # 2. Load latest extraction.
    extraction = repo.get_extraction_for_receipt(receipt_id)
    if not extraction:
        return ResolutionOutcome(
            outcome="not_found", receipt_id=receipt_id,
            message="This receipt has no extraction to correct.",
        )

    # 3. Optimistic concurrency. Someone else has resolved it since this view was
    #    rendered, so write nothing and let the caller reload.
    if expected_extraction_id is not None and extraction["extraction_id"] != expected_extraction_id:
        return ResolutionOutcome(
            outcome="stale", receipt_id=receipt_id,
            extraction_id=extraction["extraction_id"],
            message=(
                "This receipt changed while you were working on it. "
                "Reload and check the current values before saving again."
            ),
        )

    # 4. Acquire the lock. Everything below is in try/finally releasing it.
    if not repo.acquire_receipt_lock(receipt_id):
        return ResolutionOutcome(
            outcome="locked", receipt_id=receipt_id,
            message="Another process is working on this receipt. Try again in a moment.",
        )

    try:
        # 5. Merge by key presence.
        merged = _merge_corrections(extraction, corrections)

        # 6. Re-validate. Still invalid: append a row recording the attempt and
        #    stop. Deliberately not add_validation_note(), which mutates an
        #    existing row in a table CLAUDE.md says is never modified.
        candidate = ExtractionResult(
            engine="manual_correction",
            supplier_name=merged["supplier_name"],
            invoice_date=merged["invoice_date"],
            net_amount=merged["net_amount"],
            vat_amount=merged["vat_amount"],
            gross_amount=merged["gross_amount"],
            currency=merged["currency"],
            raw_response=json.dumps(merged, sort_keys=True, default=str),
            receipt_ref_number=merged["receipt_ref_number"],
            receipt_time=merged["receipt_time"],
        )
        validation = validate(candidate)
        pipeline_version = config.get_pipeline_version()

        # 10d.16 and 10d.18. A receipt whose client has no folder under Clients
        # cannot be filed there, whatever the corrections say, so it stays a
        # review item. Without this a resolved receipt for an unresolved client
        # would reach file_receipt() with None as the folder name and build a
        # path with the string "None" in it.
        _, _, folder_check = _client_details(receipt.get("client_id"))
        if validation.status == "ok" and not folder_check:
            validation = type(validation)(
                status="needs_review",
                notes=list(validation.notes or []) + [
                    f"client {receipt.get('client_id')} has no client_folder_name in the registry, "
                    "so nothing can be filed into Clients"
                ],
            )

        # Sub-step 10f.14, amendment 307, and Paul's decision of 2026-09-09.
        #
        # **`and folder_check` is the whole of what the keyword may not
        # override.** The gate above is 10d.16 and 10d.18: a client with no
        # `client_folder_name` cannot be filed for, and that is a registry fault
        # rather than a judgement about this receipt's figures. So a settle note
        # for such a client is still `still_invalid` and its file still lands in
        # `Resolutions\failed\`, which is where a fault somebody has to fix
        # belongs.
        #
        # `despite` carries the notes forward for the row and the log. It is
        # None on every ordinary resolution, which is what keeps the wording of
        # the extraction row unchanged for the CLI and the console.
        despite = None
        if validation.status != "ok" and decided_by_operator and folder_check:
            despite = list(validation.notes or [])
            # Deliverable 2 of the brief. **Paul reads `run.log`**, and a
            # receipt that silently turns green is worse than the fault being
            # fixed. WARNING rather than INFO because nothing else about a
            # settled receipt needs reading and this does.
            logger.warning(
                "receipt %s reached ok by decision in %s despite %d failed "
                "check(s): %s. A person filed it in the books, so the database "
                "agrees with them; the checks are recorded on its extraction "
                "row rather than used to block it, and no figure was "
                "recalculated",
                receipt_id, source, len(despite), ", ".join(despite))
            validation = type(validation)(status="ok", notes=[])

        if validation.status != "ok":
            attempt_id = str(uuid.uuid4())
            # possible_duplicate is a statement about the relationship between two
            # receipts, not about the validity of one, so validation must not
            # overwrite it. Overwriting would also hand a receipt a human has
            # already examined back to the pipeline: possible_duplicate is not
            # auto-retry eligible and needs_review is.
            preserve_status = receipt.get("status") == POSSIBLE_DUPLICATE_STATUS
            repo.save_extraction(
                extraction_id=attempt_id,
                receipt_id=receipt_id,
                engine="manual_correction",
                supplier_name=merged["supplier_name"],
                invoice_date=merged["invoice_date"],
                net_amount=merged["net_amount"],
                vat_amount=merged["vat_amount"],
                gross_amount=merged["gross_amount"],
                currency=merged["currency"],
                raw_response=candidate.raw_response,
                validation_status=validation.status,
                validation_notes=validation.notes,
                receipt_ref_number=merged["receipt_ref_number"],
                receipt_time=merged["receipt_time"],
                pipeline_version=pipeline_version,
                update_status=not preserve_status,
            )
            # No `note_resolved_at` here, deliberately. See this function's
            # docstring: a stamped failure reads as an applied note and its file
            # is moved to `processed\\` on the next poll.
            _record_event(
                repo, receipt_id, actor, source, "resolve", "still_invalid",
                extraction_id=attempt_id, corrections=corrections,
                gl_override_code=_override(corrections.gl_nominal_code),
            )
            logger.info(
                f"resolution of {receipt_id} by {actor} via {source} still invalid: {validation.notes}"
            )
            return ResolutionOutcome(
                outcome="still_invalid", receipt_id=receipt_id, extraction_id=attempt_id,
                validation_notes=list(validation.notes),
                message="Still not valid after the correction: " + ", ".join(validation.notes),
            )

        # 7. Save the extraction row FIRST. categorisations.extraction_id has an
        #    FK to it. Do not reorder with step 8.
        extraction_id = str(uuid.uuid4())
        repo.save_extraction(
            extraction_id=extraction_id,
            receipt_id=receipt_id,
            engine="manual_correction",
            supplier_name=merged["supplier_name"],
            invoice_date=merged["invoice_date"],
            net_amount=merged["net_amount"],
            vat_amount=merged["vat_amount"],
            gross_amount=merged["gross_amount"],
            currency=merged["currency"],
            raw_response=candidate.raw_response,
            validation_status="ok",
            # 10f.14. `despite` is None on every ordinary resolution, so the CLI
            # and the console write the same one note they always did. Where a
            # person decided over a failed check, the check is on the row: the
            # status says a human settled it and the notes say what did not add
            # up, so the row is never a claim that the figures are consistent.
            #
            # **A second wording rather than `_apply_filed_note()`'s**, which
            # says "filed by decision in Desktop despite". These are two
            # different acts: that one records a filing somebody else performed,
            # this one settles a receipt from values somebody else decided. The
            # tool is named from `source` rather than hardcoded, because this
            # function does not know it is serving Desktop.
            validation_notes=(
                ["manually corrected and filed"] if despite is None else
                ["manually corrected and filed",
                 f"settled by decision in {source} despite: "
                 + ", ".join(despite)]),
            receipt_ref_number=merged["receipt_ref_number"],
            receipt_time=merged["receipt_time"],
            pipeline_version=pipeline_version,
        )

        # 8. Categorise, then save the engine's suggestion. Never overwrite
        #    suggested_code with the operator's value: that is the audit trail.
        client_name, business_type, client_folder_name = _client_details(receipt.get("client_id"))
        categorisation = categorisation_engine.categorise(
            receipt_id=receipt_id,
            extraction_id=extraction_id,
            supplier_name=merged["supplier_name"],
            client_id=receipt["client_id"],
            business_type=business_type,
            # merged["gross_amount"] is the corrected figure written to the
            # extraction row twenty lines above. Layer 5 is the only reader; it
            # was the only one of the five call sites on this path not passing
            # it, so a Halfords receipt resolved here could still be answered
            # "0081 Motor vehicles - cars - additions" with nothing in the
            # prompt saying how much had been spent.
            gross_amount=merged["gross_amount"],
            # ~~No line_items: they are not stored, and this path has no
            # extraction call in hand.~~ **Struck 2026-09-12 by step 10p part
            # one: they ARE stored.** Read off the row the pipeline wrote, not
            # off `merged`, which carries the operator's corrections to the
            # figures and has no lines in it. A correction to a supplier name
            # does not change what the document listed.
            line_items=line_items.from_json(
                (repo.get_extraction_for_receipt(receipt_id) or {}).get("line_items")),
        )
        # The suggested code has to be one the client's chart holds, whichever
        # layer produced it. See resolve_against_chart() in
        # worker/categorisation/fallback.py. It runs before save_categorisation()
        # below and before the sidecar at step 10, and it does not touch the
        # operator's own GL override at step 9: that is applied afterwards and
        # still wins.
        categorisation = resolve_against_chart(categorisation, repo=repo)
        categorisation_id = str(uuid.uuid4())
        repo.save_categorisation(
            categorisation_id=categorisation_id,
            receipt_id=receipt_id,
            extraction_id=extraction_id,
            client_id=receipt["client_id"],
            trade=categorisation.business_type,
            mapping_id=categorisation.mapping_id,
            suggested_code=categorisation.suggested_code,
            suggested_name=categorisation.suggested_name,
            confidence=categorisation.confidence,
            match_source=categorisation.match_source,
            matched_vendor=categorisation.matched_vendor,
            needs_review=categorisation.needs_review,
            categorised_at=_now(),
        )

        # 9. Apply the GL override now, before filing. 11.2: the sidecar is built
        #    from the effective code, so overriding after filing would leave the
        #    file on disk permanently disagreeing with the database.
        override_code = _override(corrections.gl_nominal_code)
        override_name = _override(corrections.gl_account_name)
        if override_code or override_name:
            repo.update_categorisation(
                categorisation_id,
                override_code or categorisation.suggested_code,
                override_name or categorisation.suggested_name,
                _override(corrections.gl_correction_reason) or f"manual override by {actor}",
            )

        effective_code = override_code or categorisation.suggested_code
        effective_name = override_name or categorisation.suggested_name

        # 10. The payload this route WOULD write, and the invoice date that
        #     names the client folder copy at step 11.
        #
        #     ~~Sidecar from the effective code and name, all three keys.~~
        #     **Struck 2026-09-12 by amendment 346, on Paul's decision. No
        #     sidecar is produced here and none has been since stage 4.** The
        #     old sentence told the next reader a file is written at this step,
        #     which is the only thing about it that cost anything.
        #
        #     **What actually happens: this route builds the payload and writes
        #     nothing.** `sidecar_payload` is assigned and read nowhere in this
        #     function, and `make_enriched_sidecar()` makes no calls and returns
        #     a dict, so the dictionary is built and dropped. It used to be
        #     handed to `file_receipt()`, which wrote it beside the filed image;
        #     18.2b made the client folder copy image only, so **the consumer
        #     went and the producer stayed.**
        #
        #     **The call is kept deliberately and amendment 346 is the decision
        #     to keep it.** Amendment 344 point four said to delete it; deleting
        #     it was tried on 2026-09-12 and reverted the same hour, for two
        #     reasons neither amendment had in front of it.
        #
        #     **One.** `AllFourCallSitesTest` in
        #     `tests/test_sidecar_category_keys.py` spies on THIS call to
        #     capture what this route would write, and compares its key set
        #     against the other three writers. Its reason is in its own
        #     docstring: four writers of one file format is how the format
        #     diverged. Delete the call and a four-way comparison silently
        #     becomes three-way.
        #
        #     **Two.** That a CLI-resolved receipt's corrected values reach the
        #     database and no file at all is a known, open question, not an
        #     oversight: flagged in
        #     `2026-09-09_REPORT_claude_code_stage4_pipeline.md` and **it is
        #     sub-step 10f.15's to answer.** This payload is the only executable
        #     record of what this route would write, which is 10f.15's own
        #     input, so deleting it now would both destroy that and pre-empt the
        #     decision.
        #
        #     **`invoice_date` below is NOT dead** and is the reason the two
        #     lines are read together: step 11 names the client folder copy from
        #     it. It falls back to today only where the document carried no date
        #     at all, because that filename needs one.
        invoice_date = merged["invoice_date"] or datetime.now(timezone.utc).date().isoformat()
        sidecar_payload = make_enriched_sidecar(
            receipt_id=receipt_id,
            source=receipt.get("source", "email"),
            client_id=receipt.get("client_id"),
            client_name=client_name,
            capture_date=_now(),
            invoice_date=merged["invoice_date"],
            supplier=merged["supplier_name"],
            net=merged["net_amount"],
            vat=merged["vat_amount"],
            gross=merged["gross_amount"],
            currency=merged["currency"],
            category_code=effective_code,
            category_name=effective_name,
            confidence=categorisation.confidence,
            validation_status="ok",
            asserted=None,
            original_filename=receipt["filename"],
            claimed_client_id=None,
        )

        # 11. The client folder copy, by the same single route as any other
        #     receipt. Sub-steps 10f.11 and 10f.14: a completed review item is
        #     not a special case, and `copy_for_published_receipt()` holds the
        #     firm's trigger, so `never` writes nothing here as it writes
        #     nothing anywhere. It records `filed_path` itself when it writes.
        #
        #     **`dest_path` is None when this receipt has no copy in the
        #     client folder**, which is the ordinary outcome on two of the
        #     three triggers, so nothing below may format it into a path
        #     without asking.
        #
        #     ~~None when no copy was written~~ **Corrected 2026-09-09 by
        #     sub-step 10f.25**: a path also comes back when an identical
        #     document was already under that name and nothing was written, so
        #     a returned path means "the document is there" rather than "a file
        #     was just created". `run.log` says which. **The operator message
        #     below still reads `Filed to {path}` in that case**, which is true
        #     and reads as though a file had been created; flagged in
        #     `2026-09-09_REPORT_claude_code_duplicates.md` and not changed
        #     here, because `RECEIPT_CAPTURE_GUIDE.md` documents that wording.
        #     **Step 10k skips it, and the four cases were enumerated rather
        #     than argued, because the first version of this comment named the
        #     wrong one.** With the skip removed,
        #     `copy_for_published_receipt()` is reached with `at` defaulting to
        #     `publish`, and:
        #
        #     - trigger `never`: refused by its first gate.
        #     - trigger `post`: refused because `at` is not the firm's moment.
        #     - trigger `publish` and a `filed_path` already set, which is the
        #       case a correction is usually in: refused by the one-copy gate.
        #     - **trigger `publish` and a NULL `filed_path`: it WRITES.** That
        #       is a receipt whose copy failed when it published, and
        #       `_copy_missing_client_copies()` is what retries it on the next
        #       poll.
        #
        #     **So this skip decides exactly one combination**, and what it
        #     buys there is that the copy keeps one writer at one moment: the
        #     retry sweep's, from the corrected figures, rather than a
        #     correction quietly becoming a filing. Everywhere else it is
        #     defence in depth and a gate below already refuses.
        #     `tests/test_corrected_note.py` drives the one that matters.
        dest_path = None
        if not filing_already_settled:
            dest_path = copy_for_published_receipt(
                repo,
                receipt_id=receipt_id,
                client_id=receipt.get("client_id"),
                source_file=Path(receipt["file_path"]),
                invoice_date=invoice_date,
                supplier=merged["supplier_name"] or "unknown",
                gross=merged["gross_amount"] or 0.0,
                validation_status="ok",
                filed_path=receipt.get("filed_path"),
            )
        # **A correction must not clear a `possible_duplicate` finding
        # silently.** Amendment 343, Paul's decision of 2026-09-12, and it is a
        # control against a double-claimed expense rather than a tidiness rule.
        #
        # The write below is unconditional, so a receipt flagged
        # `possible_duplicate` becomes `ok` here and drains into the books. The
        # guard against that is `preserve_status` above, and it sits inside
        # `if validation.status != "ok":`, which a corrected receipt with sound
        # figures never reaches; `decided_by_operator` forces validation to `ok`
        # before that branch, so it skips it outright.
        #
        # **The guard is deliberately NOT moved here, and that was the first
        # thing to try.** Hoisting it would leave a corrected receipt at
        # `possible_duplicate` for ever, because nothing else clears that
        # status. It would strand receipts rather than fix anything.
        #
        # **What is actually wrong is that the flag is cleared by an unrelated
        # act.** The operator corrects a supplier name or a VAT figure. Nothing
        # asks them about the duplicate and they may never have known there was
        # one. Amendment 309's `decided_by_operator` philosophy is that a person
        # filed it so the database agrees with them, and that holds only where
        # the person was told what they were deciding.
        #
        # So the pipeline says it out loud. **The precedent is the `despite`
        # warning a few lines above**, and its reason is the same one: Paul
        # reads `run.log`, and a receipt that silently turns green is worse than
        # the fault being fixed. WARNING rather than INFO for the same reason.
        #
        # `receipt` is the row read at step 1, so this is the status the receipt
        # actually had on the way in rather than the one it is about to get.
        #
        # **The link survives the status change**: `update_receipt_status()`
        # writes the status column only, so the row reads `ok` while still
        # carrying `duplicate_of`. That is what makes the other receipt
        # nameable here, and it is the other half of amendment 343's finding.
        if receipt.get("status") == POSSIBLE_DUPLICATE_STATUS:
            logger.warning(
                "receipt %s was %s and a correction in %s has cleared it to ok, "
                "so it will now drain into the books. It looked like a "
                "duplicate of receipt %s. Nothing asked the operator about the "
                "duplicate and they may never have known there was one, so "
                "check the two are genuinely different documents before the "
                "expense is claimed twice",
                receipt_id, POSSIBLE_DUPLICATE_STATUS, source,
                receipt.get("duplicate_of") or "(none recorded)")

        repo.update_receipt_status(receipt_id, "ok")

        # 12. The Review pair is stale now. Already gone is not an error.
        removed = remove_review_pair(receipt_id, receipt.get("client_id"), receipt.get("filename"))
        if not removed:
            logger.info(f"no review pair removed for {receipt_id}, nothing on disk")

        # 13. Learn the mapping only if asked. Never automatically: one correction
        #     against a misread supplier name would poison the mapping table, and
        #     the exact-match layer would then apply the wrong code confidently to
        #     every future receipt from that vendor.
        #
        #     **AND ONLY AGAINST A CODE THE CLIENT'S CHART HOLDS. Added
        #     2026-09-12, amendment 344 point three, on Paul's decision.** This
        #     route required only that a code existed;
        #     `_apply_filed_note()` has always required
        #     `_CategoryDecision.chart_confirmed`. Two routes teaching one table
        #     on two rules is the half-built shape this project has paid for
        #     before, and the weaker of the two was here.
        #
        #     **Why it matters on this route in particular.** On the command
        #     line the code is TYPED, so a typo, an old code or another client's
        #     code all taught happily. In Desktop it is picked from a dropdown
        #     `catOptions()` builds from that client's adopted chart.
        #
        #     **And a mapping taught from a code the client does not hold can
        #     never work as taught.** Layer 1 returns it with confidence `high`,
        #     and `resolve_against_chart()` then substitutes or strips it on
        #     every future receipt, silently. `_resolve_category()`'s docstring
        #     already says exactly this about the unreadable case.
        #
        #     **An unreadable chart teaches nothing either**, and that falls out
        #     rather than being special-cased: `get_chart_accounts_for_client()`
        #     returns an empty mapping both when the chart is empty and when the
        #     bundle is missing, so no code is in it. That matches
        #     `_resolve_category()`, which refuses to learn there for the same
        #     reason.
        #
        #     **What is given up is intended and small.** The receipt is still
        #     corrected, still filed and still carries the operator's code; only
        #     the mapping is not learned. The firm write below is unaffected
        #     either way, because `_learn_firm_mapping_if_confirmed()` checks
        #     the chart outcome itself.
        chart_accounts = get_chart_accounts_for_client(receipt.get("client_id") or "")
        code_is_in_the_chart = bool(effective_code) and effective_code in chart_accounts
        if corrections.remember_gl_for_supplier and not code_is_in_the_chart:
            # Said out loud rather than refused in silence. The Desktop route
            # already says it, through the validation note `_resolve_category()`
            # returns; this is the same thing on this route.
            logger.warning(
                "remember_gl_for_supplier was requested for receipt %s but %s "
                "is not in client %s's chart of accounts, so no vendor mapping "
                "was learned. The receipt is still corrected and still filed. "
                "A mapping taught from a code the chart does not hold cannot "
                "work: the chart check would strip it on every future receipt",
                receipt_id, effective_code or "(no code)",
                receipt.get("client_id"))
        if corrections.remember_gl_for_supplier and code_is_in_the_chart:
            # A plain attribute read, matching _apply_filed_note(). Paul's
            # answer of 2026-09-06 to flag 3 of the vendor_key naming report.
            #
            # It was `getattr(categorisation, "vendor_key", None)`, and that
            # default could never fire: `categorisation` is the
            # CategorisationResult that categorise() returned and
            # resolve_against_chart() handed back unchanged, `vendor_key` is a
            # declared field with a default, and step 8 above already reads
            # eight attributes off this same object directly. A missing
            # attribute would have raised there first.
            #
            # What the default could do is swallow a rename. Renamed out from
            # under it, the field reads None, learning silently stops, and the
            # only trace is the warning below saying the engine returned no
            # vendor_key. That is the failure the naming correction of
            # 2026-09-06 existed to fix, sitting in the code that learns.
            vendor_key = categorisation.vendor_key
            if vendor_key:
                repo.upsert_client_vendor(
                    client_id=receipt["client_id"],
                    vendor_key=vendor_key,
                    nominal_code=effective_code,
                    account_name=effective_name,
                    last_updated=_now(),
                    vendor_name=merged["supplier_name"],
                )
                # And the firm pool, ONLY where this code confirms what the
                # classifier proposed. Step 10m, amendment 238. The helper
                # holds the rule; both learning routes call it so neither can
                # drift from the other. Paul's decision, 2026-09-12.
                taught = _learn_firm_mapping_if_confirmed(
                    repo, receipt, categorisation,
                    chosen_code=effective_code,
                    vendor_key=vendor_key,
                    vendor_name=merged["supplier_name"],
                )
                if taught:
                    logger.info(
                        f"receipt {receipt_id}: the operator's {effective_code} "
                        f"confirms the classifier, so {vendor_key} now maps to "
                        f"{taught[0]} {taught[1]} for every "
                        f"{categorisation.business_type} client of this firm"
                    )
            else:
                logger.warning(
                    f"remember_gl_for_supplier requested for {receipt_id} but the engine "
                    "returned no vendor_key, so nothing was learned"
                )

        # 14. Audit row. `note_resolved_at` is the back-feed's idempotency key
        #     and is None for every caller but `_settle_note()`. This is the one
        #     event that carries it; see this function's docstring for why the
        #     `still_invalid` row above must not.
        #     **And the outcome word says what became of the receipt**, which
        #     for a correction is not a filing. Step 10k: the receipt was filed
        #     earlier and this call moved no file, so a row reading `filed`
        #     would be the kind of name that outlives the thing it describes,
        #     which amendment 306 records this project paying for four times in
        #     two days. `_note_already_applied()` keys on the blob rather than
        #     on this word, so idempotency is unaffected.
        outcome_word = CORRECTED_ACTION if filing_already_settled else "filed"
        _record_event(
            repo, receipt_id, actor, source, "resolve", outcome_word,
            extraction_id=extraction_id, corrections=corrections,
            gl_override_code=override_code,
            note_resolved_at=note_resolved_at,
        )

        # Two wordings, because there are two outcomes now and one of them
        # writes no file. Saying "Filed to None" would read as a defect.
        #
        # **`Filed to {path}` is kept verbatim for the case that writes one**,
        # rather than reworded to match the new vocabulary.
        # `RECEIPT_CAPTURE_GUIDE.md` documents that line and Paul reads it off
        # the CLI, so the only message that changes is the one that could not
        # exist before.
        # **A third wording for step 10k**, because "no copy was written
        # because the trigger says so" would be false: the trigger was not
        # asked. Nothing was copied because the receipt's document had already
        # reached wherever it is going before this correction arrived.
        if filing_already_settled:
            message = ("Corrected. The receipt was already filed, so no file "
                       "was moved and nothing was copied.")
        else:
            message = (f"Filed to {dest_path}" if dest_path else
                       f"Resolved. No copy was written into the client folder, "
                       f"because {config.CLIENT_COPY_TRIGGER_FIELD} is "
                       f"{config.CLIENT_COPY_TRIGGER!r}.")
        logger.info(
            f"receipt {receipt_id} resolved by {actor} via {source}: {message}")

        # 15. Done.
        return ResolutionOutcome(
            outcome=outcome_word, receipt_id=receipt_id, extraction_id=extraction_id,
            # The path this receipt's document is at, which for a correction is
            # the one it already had: this call wrote nothing, and returning
            # None would read as "it is not filed", which is the opposite of
            # the premise.
            filed_path=(filed_path if filing_already_settled
                        else str(dest_path) if dest_path else None),
            category_code=effective_code,
            category_name=effective_name,
            category_confidence=categorisation.confidence,
            validation_notes=(["manually corrected and filed"] if despite is None
                              else ["manually corrected and filed"] + despite),
            message=message,
        )

    except Exception as exc:
        # The web layer must never 500 on a Save. The traceback is the record, and
        # error_detail is for logs only: never render it.
        logger.error(f"error resolving receipt {receipt_id}: {exc}", exc_info=True)
        return ResolutionOutcome(
            outcome="error", receipt_id=receipt_id,
            message="Something went wrong resolving this receipt. It has been logged.",
            error_detail=str(exc),
        )
    finally:
        repo.release_receipt_lock(receipt_id)


def _delete_the_client_copy(receipt_id: str, filed_path: str) -> Dict[str, Any]:
    """Delete this receipt's copy in the client folder, and its data file.

    Returns the detail for the audit row: `client_copy_deleted` where the
    document went, and `client_copy_sidecar_deleted` where the legacy
    `x.pdf.json` beside it went too. **Only real deletions are recorded**,
    because "already gone" is not a path this run removed. An empty dict means
    nothing was deleted.

    The reporting half of `worker\\client_copy.py`'s `remove_client_copy()`,
    which owns `Clients\\` and does the deciding. Split out so
    `discard_receipt()` below reads as the sequence of decisions it is rather
    than as five log lines.

    **Nothing here raises and nothing here fails the discard.** The status
    change is the point: a file left behind is untidy and recoverable, while a
    note stuck in `Resolutions\\failed\\` leaves the database saying `ok` about a
    receipt the books say is gone, which is the disagreement amendment 306
    exists to remove.

    **The data file is reported separately from the document**, so `run.log`
    can say which of three things happened: both went, the document went and
    there was no data file, or the document went and its data file would not.
    A data file that could not be deleted is an ERROR of its own and does not
    change the document's outcome, which is already done and cannot be undone.
    """
    result = remove_client_copy(resolve_practice_path(filed_path))
    detail: Dict[str, Any] = {}

    if result.outcome == REMOVAL_DELETED:
        detail[EVENT_CLIENT_COPY_DELETED_KEY] = str(result.path)
        if result.sidecar_outcome == REMOVAL_DELETED:
            detail[EVENT_CLIENT_COPY_SIDECAR_DELETED_KEY] = str(result.sidecar_path)
            logger.info(
                "receipt %s was discarded and the operator asked for its "
                "client folder copy to go: deleted %s and its data file %s. "
                "The document store still holds the archive of record, per "
                "18.2a",
                receipt_id, result.path, result.sidecar_path)
        elif result.sidecar_outcome == REMOVAL_ALREADY_GONE:
            logger.info(
                "receipt %s was discarded and the operator asked for its "
                "client folder copy to go: deleted %s, and it had no data "
                "file beside it. The document store still holds the archive "
                "of record, per 18.2a",
                receipt_id, result.path)
        else:
            # REFUSED or FAILED on the data file alone. The document is already
            # gone, so this leaves the orphan the change exists to prevent and
            # a person has to remove it by hand. Named in full for that reason.
            logger.info(
                "receipt %s was discarded and the operator asked for its "
                "client folder copy to go: deleted %s. The document store "
                "still holds the archive of record, per 18.2a",
                receipt_id, result.path)
            logger.error(
                "the data file beside receipt %s's client folder copy was not "
                "deleted (%s): %s. It is at %s and it is now an orphan, "
                "because the document it described has gone",
                receipt_id, result.sidecar_outcome, result.sidecar_detail,
                result.sidecar_path)
        return detail

    if result.outcome == REMOVAL_ALREADY_GONE:
        logger.info(
            "receipt %s was discarded and the operator asked for its client "
            "folder copy to go, and there is nothing at %s. Not a failure. Any "
            "data file beside it is left alone, because whatever removed the "
            "document did not say the data file was stale",
            receipt_id, result.path)
        return detail

    # REFUSED or FAILED on the document. Both are ERROR, and for the same
    # reason: one says a stored path is not what it claims to be and the other
    # says the file could not be removed, and in both cases a person has to
    # look.
    logger.error(
        "receipt %s was discarded and the operator asked for its client folder "
        "copy to go, and it was not deleted (%s): %s. filed_path was %r. The "
        "discard stands and the file is where it was",
        receipt_id, result.outcome, result.detail, filed_path)
    return detail


def discard_receipt(repo, receipt_id, reason, actor, source,
                    note_resolved_at=None,
                    delete_client_copy: bool = False) -> ResolutionOutcome:
    """Status to 'discarded'. Never deletes the original file or any extraction row.

    Design document 4.2. Used for a confirmed duplicate, and for a failed receipt
    that is never going to be resolvable.

    note_resolved_at is supplied only by the back-feed, and only so the audit row
    carries the note's own timestamp for the idempotency check in 12.3 step 3. It is
    additive: the CLI and the console do not pass it. 4.2's signature does not list
    it, and that is a divergence worth knowing about rather than hiding.

    ## Two things this does to `Clients\\`, from Paul's decisions of 2026-09-10

    **`delete_client_copy` deletes the copy in the client folder**, and only when
    the caller asks. It is the answer to the second question Desktop puts to an
    operator deleting a receipt from the books. **Absent is today's behaviour**,
    so the CLI and the back-feed's other paths do not move, and the sentence at
    the top of this docstring still holds for them: the original file in the
    document store is never deleted on any path, whatever this flag says.

    **`filed_path` is cleared on every discard**, deleted copy or not. A
    discarded receipt is not filed, whatever became of the file, and the column
    would otherwise name something that may not be there.

    **The status is set before either**, so a receipt whose copy is being deleted
    cannot be picked up by `get_published_receipts_without_client_copy()` and
    have the copy written back on the next poll. That query filters
    `status = 'ok'`, and this ordering is what makes that filter enough.

    **The paths are recorded in the audit row**, in `corrections_json`: 5.1 has
    no column for either. See `EVENT_CLIENT_COPY_DELETED_KEY`.
    """
    receipt = repo.get_receipt(receipt_id)
    if not receipt:
        return ResolutionOutcome(
            outcome="not_found", receipt_id=receipt_id,
            message=f"Receipt not found: {receipt_id}",
        )

    if not repo.acquire_receipt_lock(receipt_id):
        return ResolutionOutcome(
            outcome="locked", receipt_id=receipt_id,
            message="Another process is working on this receipt. Try again in a moment.",
        )

    try:
        repo.update_receipt_status(receipt_id, "discarded")

        # Read off the row this function already has, rather than asked for
        # again: a second read could disagree with the row the caller decided
        # from, which is `copy_for_published_receipt()`'s reasoning for taking
        # `filed_path` as a parameter.
        filed_path = receipt.get("filed_path")
        detail: Dict[str, Any] = {}

        if delete_client_copy and filed_path:
            detail.update(_delete_the_client_copy(receipt_id, filed_path))
        elif delete_client_copy:
            # The live shape for a firm whose `client_copy_trigger` is `never`
            # or `post`: the receipt published and no copy was ever written, so
            # there is nothing to delete and the operator's intent is already
            # satisfied. Said out loud, because "asked to delete and deleted
            # nothing" should be readable in the log rather than inferred from
            # its absence.
            logger.info(
                "receipt %s was discarded and the operator asked for its "
                "client folder copy to go, and it has no filed_path, so there "
                "is nothing to delete", receipt_id)

        if filed_path:
            repo.clear_receipt_filed_path(receipt_id)
            detail[EVENT_FILED_PATH_CLEARED_KEY] = str(filed_path)

        # The receipt's life in the Review folder is over. Leaving the pair behind
        # is what made IntelliBooks file a duplicate, per 3.5.
        removed = remove_review_pair(receipt_id, receipt.get("client_id"), receipt.get("filename"))
        if not removed:
            logger.info(f"no review pair removed for {receipt_id}, nothing on disk")

        _record_event(repo, receipt_id, actor, source, "discard", "discarded", reason=reason,
                      note_resolved_at=note_resolved_at, detail=detail or None)
        logger.info(f"receipt {receipt_id} discarded by {actor} via {source}: {reason}")

        return ResolutionOutcome(
            outcome="discarded", receipt_id=receipt_id,
            message=f"Discarded: {reason}" if reason else "Discarded.",
            # What a caller has to be able to tell an operator: the copy has
            # gone, or the copy has been left and nothing records its path any
            # more. Both are read off `detail` rather than rebuilt, so the
            # audit row and the message cannot disagree about what happened.
            filed_path_cleared=detail.get(EVENT_FILED_PATH_CLEARED_KEY),
            client_copy_deleted=detail.get(EVENT_CLIENT_COPY_DELETED_KEY),
        )

    except Exception as exc:
        logger.error(f"error discarding receipt {receipt_id}: {exc}", exc_info=True)
        return ResolutionOutcome(
            outcome="error", receipt_id=receipt_id,
            message="Something went wrong discarding this receipt. It has been logged.",
            error_detail=str(exc),
        )
    finally:
        repo.release_receipt_lock(receipt_id)


# ---------------------------------------------------------------------------
# The resolution back-feed. Design document 12.
# ---------------------------------------------------------------------------


def _note_already_applied(repo, receipt_id: str, resolved_at: str) -> Optional[Dict[str, Any]]:
    """12.3 step 3. The event row this note already wrote, or None.

    Keyed on the note's own `resolved_at`, not on the receipt, so a second,
    genuinely later resolution of the same receipt is applied rather than skipped.
    """
    for event in repo.list_resolution_events(receipt_id):
        if event.get("source") != DESKTOP_SOURCE:
            continue
        try:
            payload = json.loads(event.get("corrections_json") or "{}")
        except ValueError:
            continue
        if isinstance(payload, dict) and payload.get(NOTE_RESOLVED_AT_KEY) == resolved_at:
            return event
    return None


def _receipt_for_note(repo, note: ResolutionNote) -> Optional[Dict[str, Any]]:
    """12.3 step 2. By receipt_id, else by matching the review filenames.

    The filename fallback is case-insensitive because the two tools case names
    differently: Desktop leaves a supplier as typed and the pipeline lowercases it.
    An ambiguous match is not a match, the same rule `_find_review_sidecar()`
    applies, because two receipts can share an original filename.

    The note's `client_id` and `client.name` are deliberately not used to find
    anything. The note's client field was `client_code` until sub-step 10d.60 and
    is now `client_id`, which both tools do agree on, but it is still not what
    finds the receipt: a note identifies a receipt, not a client, and matching on
    the client would turn a mis-keyed note into a wrong receipt rather than into
    no receipt. See the 12.4 amendment of 2026-07-28.
    """
    if note.receipt_id:
        return repo.get_receipt(note.receipt_id)

    candidates: Dict[str, Dict[str, Any]] = {}
    for review_file in note.original_review_files:
        name = Path(review_file.replace("\\", "/")).name
        if name.lower().endswith(".review.json"):
            continue
        for receipt in repo.find_receipts_by_filename(name):
            candidates[receipt["receipt_id"]] = receipt

    if len(candidates) == 1:
        receipt = next(iter(candidates.values()))
        logger.info(
            f"note matched receipt {receipt['receipt_id']} on filename, it carried no receipt_id"
        )
        return receipt
    if len(candidates) > 1:
        logger.error(
            f"{len(candidates)} receipts match {note.original_review_files}; an ambiguous "
            "match is not a match, so the note is not applied"
        )
    return None


@dataclass
class _CategoryDecision:
    """What 12.3 step 6 decided about one note's category.

    `chart_confirmed` is a separate field from `code` because there are two ways
    to come out of the check holding a code and only one of them may teach: the
    client's chart holds it, or the chart could not be read and the code stands
    unchecked. A caller that learned from the second would write a mapping
    nothing has confirmed, and a mapping is read back by layer 1 as an exact
    match with confidence `high`.
    """
    code: Optional[str] = None
    name: Optional[str] = None
    validation_note: Optional[str] = None
    chart_confirmed: bool = False


def _resolve_category(note: ResolutionNote, client_id: Optional[str]) -> _CategoryDecision:
    """12.3 step 6, reversed as that step predicted it would be on 2026-08-17.

    ~~Returns (code, name, validation_note), and the code is always None.~~
    ~~A resolution note's category name is not resolved to a code at all.~~
    **Struck 2026-09-05, sub-step 10j.11 and amendment 231.** Desktop sends the
    code, so this step stops being name-to-code and becomes a validation that the
    code exists in the client's chart. Five outcomes:

    - **No code and no name.** Nothing to check. The common case, because Desktop
      does not require a category before filing, so `""` means "no category".
    - **A code the client's chart holds.** The code is stored, and **the name
      comes from the chart rather than from the note**, so the stored pair cannot
      disagree. This is the only outcome that may teach a mapping.
    - **A code the chart does not hold.** **No code, the note's name if it has
      one, and a validation note naming the code that was rejected.** The
      published fallback table is deliberately NOT applied: `fallback_accounts.csv`
      substitutes for an account the *classifier* proposed, and Paul chose this
      code himself out of his own chart. If it has since left that chart, that is
      an inconsistency for a person to see rather than one to substitute away.
      Paul's decision, 2026-09-05.
    - **The chart could not be read.** `get_chart_accounts_for_client()` returns
      an empty mapping both when the chart is empty and when the bundle is
      missing, and **an empty read is not evidence that the account is absent**.
      `resolve_against_chart()` in fallback.py already rules on this exact
      situation, and this follows it: the code stands, unchecked, with a
      validation note. It is not confirmed, so nothing is learned from it.
    - **A name and no code.** Unchanged. The name is stored, no code, and the
      validation note says why. 12.3 says that is expected and not an error.

    ~~It looked up `repo.find_coa_account_by_name()`, which queried `coa_accounts`.~~
    **That table was cancelled by amendment 96 and the cancellation confirmed by 124**,
    so the lookup returned None for every name ever asked and the found branch was
    unreachable. Both were deleted, outstanding item 155, 2026-09-04, and what
    replaces them is not the same lookup repointed: **the note is matched on the
    code, never on the name.** Whether a caption typed in IntelliBooks may be
    matched to an account by name, with or without `coa_alt_names.csv`, is still a
    decision nobody has taken, and the name-only branch still declines to take it.

    `get_chart_accounts_for_client()` is the production reader here and
    `get_eligible_accounts_for_client()` is deliberately not: `classifier_eligible`
    marks what layer 5 may propose and is not a rule about what a person may post,
    per the module docstring of worker/categorisation/chart.py. An account marked
    `No` is still in the chart and still postable, so an operator who picked one
    must not have it rejected here.
    """
    if not note.category_code:
        if not note.category_name:
            return _CategoryDecision()
        return _CategoryDecision(
            name=note.category_name,
            validation_note=(
                f"category '{note.category_name}' was stored as a name without a code, "
                "because a note's category is not matched against the chart of accounts"
            ),
        )

    code = note.category_code
    accounts = get_chart_accounts_for_client(client_id or "")

    if not accounts:
        # Already logged at ERROR by chart.load_accounts(). Said again on the row
        # because the consequence belongs with the decision: the check did not
        # run, so the code stands rather than being stripped, and it stands
        # unconfirmed so nothing learns from it.
        return _CategoryDecision(
            code=code,
            name=note.category_name,
            validation_note=(
                f"category code {code} was stored unchecked: client {client_id}'s chart "
                "could not be read, so nothing confirms the account exists and no "
                "vendor mapping was learned from it"
            ),
        )

    if code in accounts:
        return _CategoryDecision(code=code, name=accounts[code], chart_confirmed=True)

    kept = (
        f" The name '{note.category_name}' was stored instead."
        if note.category_name else " The note carried no name either, so none was stored."
    )
    return _CategoryDecision(
        name=note.category_name,
        validation_note=(
            f"category code {code} was rejected: it is not in client {client_id}'s "
            "chart of accounts." + kept
        ),
    )


def _settle_note(repo, categorisation_engine, receipt: Dict[str, Any],
                 note: ResolutionNote) -> ResolutionOutcome:
    """12.3 step 5, second shape. Settle a receipt from the note's values.

    **Sub-step 10f.14 and Paul's decision of 2026-09-09.** A `filed` note with
    no `filed_path` no longer says "Desktop filed this"; it says "these are the
    corrected values, settle this receipt". Amendment 299 stopped
    `fileReviewReceipt()` writing into `Clients\\` and stopped it naming a path,
    and the pipeline kept refusing such a note, so one receipt reached the books
    in Desktop and stayed `failed` in the database.

    **This function translates and delegates. It writes nothing itself.** Every
    write is `resolve_receipt()`'s, which is the path the console and the CLI
    take: it applies the corrections, re-validates, categorises, applies the
    category as a GL override, and calls `copy_for_published_receipt()`, the one
    gated writer into `Clients\\`. So a `never` firm gets no copy here exactly as
    it gets none anywhere, and there is no second implementation of resolution to
    drift from the first. `TheTwoShapesTakeDifferentPathsTest` holds that on the
    syntax tree.

    ## Three decisions taken here, because the brief left them open

    **`action` stays `filed` rather than becoming `settle`.** The word is now
    wrong for this shape and the honest name would be `settle`. It is not
    renamed because `action` is a field in a file format: notes already written
    carry `filed`, unapplied ones sit in `Resolutions\\` and in `failed\\`,
    `NOTE_ACTIONS` validates against it, and Desktop is built by a session that
    cannot see this one, so neither half can be made to ship first. `NOTE_SCHEMA`
    would have to bump, which its own comment says to do only when both halves
    change. **The clean route is to add `settle` to `NOTE_ACTIONS` alongside
    `filed`, switch Desktop, then retire `filed` when no unapplied note carries
    it**, which is checkable because nothing in `Resolutions\\` is ever deleted.
    That needs the Desktop half and Paul's word, so it is reported rather than
    done.

    **`actor` and `source` stay `desktop`.** The correction is Desktop's and the
    filing is now the pipeline's, but `resolution_events` records who decided,
    not who wrote the file: `filed_path` and the copy record that.
    **`_note_already_applied()` also filters on `source == DESKTOP_SOURCE`**, so
    changing `source` would silently break idempotency for every note.

    **The category is applied as a GL override and the engine still
    categorises.** That is what `_apply_filed_note()` does, so routing the
    note's code and name through `Corrections.gl_*` reproduces today's rows
    rather than changing them: the engine's suggestion stays in
    `suggested_code`, which is the audit trail, and the person's choice sits in
    the correction columns and is the effective code.

    ## And what it asks resolve_receipt() to do differently

    **`decided_by_operator=True`, and this is the only production call site that
    passes it.** Amendment 307 and Paul's decision of 2026-09-09. A person has
    already put the row in the books, so a failed check is recorded on the
    extraction row and logged rather than used to block the receipt. Before it,
    a settle note whose net and VAT did not sum to its gross landed in
    `Resolutions\\failed\\` as `still_invalid` while its row sat in the books,
    which is the disagreement amendment 306 exists to stop. **It does not open
    the `client_folder_name` gate**, which is a registry fault rather than a
    judgement about figures.

    ## And one guarantee carried across by hand

    **The tick is withheld when the client's chart did not confirm the code.**
    `_apply_filed_note()` learns only on `note.remember_gl_for_supplier and code
    and category.chart_confirmed`; `resolve_receipt()`'s step 13 has no chart
    test, because its corrections come from a person using a picker built from
    the chart. A mapping is read back by layer 1 as an exact match with
    confidence `high`, so writing one nothing has confirmed would apply a code
    confidently to every future receipt from that vendor. Withheld here rather
    than by adding a parameter to `resolve_receipt()`, which serves the console
    and the CLI and must not change for them.
    """
    receipt_id = receipt["receipt_id"]
    category = _resolve_category(note, receipt.get("client_id"))

    # Only the fields the note actually carried, which is what
    # `_merge_corrections()` merges on: presence, not truthiness. A `net_amount`
    # of null in the note therefore lands as NULL rather than inheriting the
    # extractor's figure, which is the stale-figure risk `_apply_filed_note()`
    # guards against by not merging at all. `receipt_ref_number` and
    # `receipt_time` are absent from every Desktop note, so they are carried
    # forward, which is what that function does explicitly.
    values = {name: note.values[name] for name in CORRECTABLE_FIELDS
              if name in note.values}

    remember = bool(note.remember_gl_for_supplier and category.code
                    and category.chart_confirmed)
    if note.remember_gl_for_supplier and not remember:
        logger.warning(
            f"remember_gl_for_supplier was ticked for {receipt_id} but the "
            f"code {category.code!r} is not one the client's chart confirmed, "
            "so nothing will be learned. A mapping is read back by layer 1 as "
            "an exact match with high confidence"
        )

    corrections = Corrections(
        values=values,
        gl_nominal_code=category.code,
        gl_account_name=category.name,
        gl_correction_reason="category from the IntelliBooks Desktop resolution note",
        remember_gl_for_supplier=remember,
    )

    logger.info(
        f"settling receipt {receipt_id} from the IntelliBooks Desktop note "
        f"resolved at {london_time.stamp(note.resolved_at)}: the note names no "
        "filed_path, so the client folder copy is this pipeline's to make on "
        "the firm's trigger"
    )
    outcome = resolve_receipt(
        repo, categorisation_engine, receipt_id, corrections,
        actor=DESKTOP_ACTOR, source=DESKTOP_SOURCE,
        note_resolved_at=note.resolved_at,
        # Amendment 307. **The only production call site that passes this**, and
        # the reason is the one in this function's docstring: by the time a note
        # arrives, the row is in the books in IntelliBooks Desktop. A receipt
        # left as a review item because its net and VAT do not sum to its gross
        # would leave the database disagreeing with the books, which is what
        # amendment 306's contract exists to prevent. The checks still run and
        # are recorded; see `resolve_receipt()` for what it does and does not
        # override.
        decided_by_operator=True,
    )
    if category.validation_note:
        # The chart's verdict on the code, which `_apply_filed_note()` appends to
        # the extraction row. `resolve_receipt()` writes that row and has no
        # notion of a note, so it is surfaced on the outcome instead of being
        # dropped. Reported rather than written into the row, because the row is
        # append-only and already saved by the time this returns.
        outcome.validation_notes = list(outcome.validation_notes or []) + [
            category.validation_note]
        logger.info(
            f"the chart's verdict on the note's category for {receipt_id}: "
            f"{category.validation_note}"
        )
    return outcome


def _apply_filed_note(repo, categorisation_engine, receipt: Dict[str, Any],
                      note: ResolutionNote) -> ResolutionOutcome:
    """12.3 step 5. Record a filing Desktop has already done on disk.

    **The image is already at `filed_path`.** So this records the filing with
    `mark_receipt_filed()` and never calls `file_receipt()`. Getting that wrong
    leaves a second copy on disk under a `-2` name for every Desktop resolution,
    which is the exact bug this contract exists to prevent. That is why this is its
    own path rather than a flag threaded through `resolve_receipt()`.

    No sidecar is written either. Desktop wrote one when it filed, in its own shape,
    and rewriting it would be a write into a folder Desktop has just written to.
    12.4 leaves that decision to Paul at step 10; until then the sidecar of record
    for a Desktop-filed receipt is the one Desktop wrote.
    """
    receipt_id = receipt["receipt_id"]
    target = resolve_practice_path(note.filed_path)
    if not target.exists():
        return ResolutionOutcome(
            outcome="error", receipt_id=receipt_id,
            message=(
                f"The note says this receipt was filed as {note.filed_path}, but there is "
                "nothing there. Nothing was changed."
            ),
            error_detail=f"filed_path does not exist on disk: {target}",
        )

    existing = receipt.get("filed_path")
    if existing and str(existing) != str(target):
        # Two filings of the same receipt, in two places, by two tools. That is the
        # disagreement between the database and the books that this contract exists
        # to prevent, so it is surfaced rather than resolved by guessing.
        return ResolutionOutcome(
            outcome="already_filed", receipt_id=receipt_id, filed_path=str(existing),
            message=(
                f"This receipt is already filed as {existing}, and the note says it was "
                f"filed as {note.filed_path}. Nothing was changed."
            ),
            error_detail=f"filed_path conflict: db={existing} note={target}",
        )

    if not repo.acquire_receipt_lock(receipt_id):
        return ResolutionOutcome(
            outcome="locked", receipt_id=receipt_id,
            message="Another process is working on this receipt. The note will be retried.",
        )

    try:
        previous = repo.get_extraction_for_receipt(receipt_id) or {}

        # The note is the practice's decided truth, so its values are not merged over
        # the extraction: an amount the note does not carry is absent rather than
        # inherited, or a corrected gross could end up beside a stale net. The two
        # fields Desktop has no input for are carried forward rather than thrown
        # away, because the extractor read them and nobody has contradicted them.
        merged = {name: note.values.get(name) for name in CORRECTABLE_FIELDS}
        for carried in ("receipt_ref_number", "receipt_time"):
            if carried not in note.values:
                merged[carried] = previous.get(carried)
        currency = note.values.get("currency") or previous.get("currency") or config.DEFAULT_CURRENCY

        candidate = ExtractionResult(
            engine="manual_correction",
            supplier_name=merged["supplier_name"],
            invoice_date=merged["invoice_date"],
            net_amount=merged["net_amount"],
            vat_amount=merged["vat_amount"],
            gross_amount=merged["gross_amount"],
            currency=currency,
            raw_response=json.dumps(
                {"resolution_note": {"resolved_at": note.resolved_at, "values": merged}},
                sort_keys=True, default=str,
            ),
            receipt_ref_number=merged["receipt_ref_number"],
            receipt_time=merged["receipt_time"],
        )

        validation_notes = ["filed in IntelliBooks Desktop"]
        # validate() runs for the record, but does not decide the status: a human
        # filed this and 12.3 step 5 says the status is ok. Throwing away what
        # validate() said would be the wrong half of that, so an inconsistent set of
        # figures earns a line on the row.
        validation = validate(candidate)
        if validation.status != "ok":
            validation_notes.append(
                "filed by decision in Desktop despite: " + ", ".join(validation.notes)
            )

        category = _resolve_category(note, receipt.get("client_id"))
        code, category_name = category.code, category.name
        if category.validation_note:
            validation_notes.append(category.validation_note)

        extraction_id = str(uuid.uuid4())
        repo.save_extraction(
            extraction_id=extraction_id,
            receipt_id=receipt_id,
            engine="manual_correction",
            supplier_name=merged["supplier_name"],
            invoice_date=merged["invoice_date"],
            net_amount=merged["net_amount"],
            vat_amount=merged["vat_amount"],
            gross_amount=merged["gross_amount"],
            currency=currency,
            raw_response=candidate.raw_response,
            validation_status="ok",
            validation_notes=validation_notes,
            receipt_ref_number=merged["receipt_ref_number"],
            receipt_time=merged["receipt_time"],
            pipeline_version=config.get_pipeline_version(),
        )

        # Categorise for the audit trail, exactly as 4.3 step 8 does. The engine's
        # suggestion is never overwritten; Desktop's category goes in the correction
        # columns beside it.
        client_name, business_type, _folder = _client_details(receipt.get("client_id"))
        categorisation = categorisation_engine.categorise(
            receipt_id=receipt_id,
            extraction_id=extraction_id,
            supplier_name=merged["supplier_name"],
            client_id=receipt["client_id"],
            business_type=business_type,
            # As at 4.3 step 8 above, and for the same reason.
            gross_amount=merged["gross_amount"],
            # ~~No line_items.~~ **Struck 2026-09-12 by step 10p part one**, and
            # read off the stored row for the reason given at 4.3 step 8.
            line_items=line_items.from_json(
                (repo.get_extraction_for_receipt(receipt_id) or {}).get("line_items")),
        )
        # The suggested code has to be one the client's chart holds, whichever
        # layer produced it. Desktop's own category is applied below, into the
        # correction columns, and is unaffected.
        categorisation = resolve_against_chart(categorisation, repo=repo)
        categorisation_id = str(uuid.uuid4())
        repo.save_categorisation(
            categorisation_id=categorisation_id,
            receipt_id=receipt_id,
            extraction_id=extraction_id,
            client_id=receipt["client_id"],
            trade=categorisation.business_type,
            mapping_id=categorisation.mapping_id,
            suggested_code=categorisation.suggested_code,
            suggested_name=categorisation.suggested_name,
            confidence=categorisation.confidence,
            match_source=categorisation.match_source,
            matched_vendor=categorisation.matched_vendor,
            needs_review=categorisation.needs_review,
            categorised_at=_now(),
        )
        if code or category_name:
            repo.update_categorisation(
                categorisation_id, code, category_name,
                "category from the IntelliBooks Desktop resolution note",
            )

        # Learn the mapping, on the tick and to the client table only.
        #
        # ~~12.3 step 6 says learn the vendor mapping from a Desktop resolution.
        # The two sections disagree and nothing here decides it.~~ **Struck
        # 2026-09-05 by amendment 231: they do not disagree and have not since
        # 2026-07-28.** 12.3 step 6's learning clause was struck that day and the
        # correction beneath it reads "11.3 wins: a back-feed note never learns a
        # mapping" and "learning stays opt-in from an operator who ticked a box".
        # This comment said the question was open, and amendment 230 took its word
        # for what the design document says rather than opening 12.3, which is why
        # the wording is replaced here rather than deleted.
        #
        # So: never automatically, because one correction against a misread
        # supplier name poisons the mapping table and layer 1's exact match then
        # applies the wrong code confidently to every future receipt from that
        # vendor. Only on `remember_gl_for_supplier`, and only against a code the
        # client's chart confirmed, per _CategoryDecision.
        #
        # ~~**`upsert_firm_vendor()` is not called here and must not be.**~~
        # **NARROWED 2026-09-12 by step 10m, amendment 238, on Paul's decision.
        # It IS called here now, through `_learn_firm_mapping_if_confirmed()`,
        # and in exactly one case.** The superseded wording is kept above rather
        # than deleted, because the reason it gave is still the reason the
        # ordinary case writes the client table alone.
        #
        # Amendment 231, 2026-09-05: a Desktop correction writes the client
        # table only. The only code Desktop can offer is one from the client's
        # own adopted chart, and the client table is scoped to that client, so
        # it can never reach another. The firm pool is shared across a
        # business_type and needs the receipt account rather than this one,
        # which is a separate decision: item 166, deferred.
        #
        # **Item 166 is the thing amendment 238 closed, so 238 is the deferred
        # decision arriving rather than a reversal of 231.** And 231's stated
        # reason is 238's "Different" half word for word: the receipt account
        # cannot be recovered from an operator's chart code, `7310`, `7391` and
        # `7392` all resolving into `7310`. **238 carves out the single case
        # where the account IS known, because the classifier named it.** The
        # helper holds that rule and both learning routes call it.
        if note.remember_gl_for_supplier and code and category.chart_confirmed:
            # `vendor_key` and not `mapping_id`. What this writes is the
            # normalised merchant key that layer 1 looks up; `mapping_id` is the
            # row id of a mapping that already exists, and is None on exactly the
            # receipts worth learning from, the ones nothing matched.
            #
            # Both names moved on 2026-09-06. This comment said the opposite of
            # what it says now and was right both times: the field holding the
            # normalised key was called `vendor_code` and is now called
            # `vendor_key`, and the field holding the row id was called
            # `vendor_key` and is now called `mapping_id`.
            vendor_key = categorisation.vendor_key
            if vendor_key:
                repo.upsert_client_vendor(
                    client_id=receipt["client_id"],
                    vendor_key=vendor_key,
                    nominal_code=code,
                    account_name=category_name,
                    last_updated=_now(),
                    vendor_name=merged["supplier_name"],
                )
                _record_vendor_learned(
                    repo, receipt_id, extraction_id,
                    client_id=receipt["client_id"],
                    vendor_key=vendor_key,
                    vendor_name=merged["supplier_name"],
                    code=code, account_name=category_name,
                    note_resolved_at=note.resolved_at,
                )
                # And the firm pool, ONLY where this code confirms what the
                # classifier proposed. Step 10m, amendment 238, which is the
                # decision amendment 231 deferred as item 166. See the helper
                # for why that supersedes 231's point two in this one case and
                # in no other.
                taught = _learn_firm_mapping_if_confirmed(
                    repo, receipt, categorisation,
                    chosen_code=code,
                    vendor_key=vendor_key,
                    vendor_name=merged["supplier_name"],
                )
                if taught:
                    logger.info(
                        f"receipt {receipt_id}: the operator's {code} confirms "
                        f"the classifier, so {vendor_key} now maps to "
                        f"{taught[0]} {taught[1]} for every "
                        f"{categorisation.business_type} client of this firm"
                    )
                logger.info(
                    f"learned {vendor_key} -> {code} {category_name} for client "
                    f"{receipt['client_id']} from the Desktop note for {receipt_id}"
                )
            else:
                logger.warning(
                    f"remember_gl_for_supplier requested for {receipt_id} but the engine "
                    "returned no vendor_key, so nothing was learned"
                )

        repo.mark_receipt_filed(receipt_id, str(target))
        repo.update_receipt_status(receipt_id, "ok")

        # Desktop deletes the Review pair itself, per the 12.4 amendment, so finding
        # nothing is the expected case and not a failure.
        removed = remove_review_pair(
            receipt_id, receipt.get("client_id"), receipt.get("filename")
        )
        if not removed:
            logger.info(
                f"no review pair on disk for {receipt_id}; Desktop removes its own pair"
            )

        _record_event(
            repo, receipt_id, DESKTOP_ACTOR, DESKTOP_SOURCE, "resolve", "filed",
            extraction_id=extraction_id,
            corrections=Corrections(values=dict(merged, currency=currency)),
            gl_override_code=code,
            note_resolved_at=note.resolved_at,
        )
        logger.info(
            f"receipt {receipt_id} recorded as filed in IntelliBooks Desktop at {target}, "
            "no second copy written"
        )

        return ResolutionOutcome(
            outcome="filed", receipt_id=receipt_id, extraction_id=extraction_id,
            filed_path=str(target),
            category_code=code,
            category_name=category_name or categorisation.suggested_name,
            category_confidence=categorisation.confidence,
            validation_notes=validation_notes,
            message=f"Recorded the Desktop filing at {target}",
        )

    except Exception as exc:
        logger.error(
            f"error applying the resolution note for {receipt_id}: {exc}", exc_info=True
        )
        return ResolutionOutcome(
            outcome="error", receipt_id=receipt_id,
            message="Something went wrong applying this resolution note. It has been logged.",
            error_detail=str(exc),
        )
    finally:
        repo.release_receipt_lock(receipt_id)


def _apply_attached_note(repo, receipt: Dict[str, Any],
                         note: ResolutionNote) -> ResolutionOutcome:
    """Sub-step 10f.37. IntelliBooks Desktop says this receipt is in the accounts.

    **All it does is write the client folder copy on the `post` trigger, and
    record that it was told.** No status change, no extraction row, no
    categorisation row: the receipt was already `ok` and published, and nothing
    about it has changed. What has changed is that a person attached it to a
    transaction, which on the `post` trigger is the moment 18.2b's copy is due.

    **Paul's reason, in his words**, and it is why this exists at all: on the
    `publish` trigger the client folder holds whatever the pipeline succeeded
    on, including duplicates that got through, strays and documents that turned
    out to be personal, and nothing removes them.
    `Clients\\{client}\\IntelliBooks\\Receipts\\{tax year}\\` should hold the
    receipts relating to that client's transactions and make sense to him and
    to the client years later. On `post` a document reaches the folder because
    it was attached to a transaction, so the folder is curated by construction.

    ## Four decisions in here, and each one is somebody else's rule

    **It reaches the copy through `copy_for_published_receipt()`**, the gated
    caller every other route uses, so the trigger, the one-copy rule, the
    `ok`-only rule and 10d.18's missing-folder-name refusal are not
    reimplemented. 10f.11's one writer stays one writer.

    **It passes the receipt's own `status` as the validation status**, so a
    receipt that is not `ok` is refused by that existing gate rather than by a
    new one here. 18.2b: the folder shows the result of the work.

    **On `publish` and on `never` it writes nothing and is still applied.** A
    firm can be on any of the three and the same Desktop sends the same message
    to all of them, so the pipeline decides and the note is not an error
    anywhere. On `publish` the copy already exists, made when the receipt
    published.

    **A receipt with no `published` row is copied anyway, and warned about.** A
    receipt reaches the books through the drain, which needs a publish, so this
    cannot happen by the built route and means the two products disagree about
    how the receipt got into the books. It is not refused: Desktop owns the
    books and is the authority on what is in them, and refusing would leave a
    receipt in the accounts with no copy AND a note in `failed\\`, which is the
    worse of the two states. See the report of 2026-09-10 for the reasoning.
    """
    receipt_id = receipt["receipt_id"]
    # Sub-step 10f.38. A document attached from the Bank Transactions tab was
    # never offered to extraction, so there is nothing to name its copy from
    # and nothing ever published it. Both of the things below turn on that, so
    # it is read once here rather than twice.
    is_bank_attachment = receipt.get("status") == config.BANK_ATTACHMENT_STATUS
    # What the `ok`-only gate in `copy_for_published_receipt()` is asked about.
    # The row's own status, so that gate does the deciding and this function
    # adds no second rule; emptied below in the one case where an attached
    # document cannot be named.
    copy_status = receipt.get("status") or ""

    if not is_bank_attachment and not repo.is_published(receipt_id):
        logger.warning(
            "IntelliBooks Desktop says receipt %s is attached to a "
            "transaction, and this pipeline has no `published` row for it. A "
            "receipt reaches the books through the drain, which needs a "
            "publish, so the two products disagree about how this one got "
            "there. Applying the note anyway: Desktop owns the books",
            receipt_id)

    if is_bank_attachment:
        # **Named from the transaction, per section 4 of 10f.38's brief and
        # Paul's decision of 2026-09-11**: the transaction date, the
        # description normalised the way a supplier name is, and the amount, so
        # the client folder reads the same way whether a document came from a
        # receipt or from a bank line. The three values were recorded at Attach
        # because Attach and Post are two moments and `receipts` has no column
        # for any of them.
        #
        # **The pipeline composes the name and the message carried the values,
        # not a filename**, which is this function's existing rule: a name
        # composed by Desktop cannot tell a collision's `-2` from its original.
        values = attached.transaction_values(repo, receipt_id) or {}
        extraction = {
            "invoice_date": values.get(attached.ARRIVAL_DATE_KEY),
            "supplier_name": values.get(attached.ARRIVAL_DESCRIPTION_KEY),
            "gross_amount": values.get(attached.ARRIVAL_AMOUNT_KEY),
        }
        if not extraction["invoice_date"]:
            # The row says it is an attached document and its arrival record is
            # missing, unreadable or has no date. **Reported, and no copy
            # written**, rather than papered over with today's date and
            # `unknown`: the transaction date names the tax year folder as well
            # as the file, so a substitute would file a real document into a
            # year nobody would look in under a name nobody could trace back.
            # The archive of record still holds it either way.
            #
            # `copy_status` is emptied rather than the receipt row edited, so
            # the existing `ok`-only gate does the refusing and there is no
            # second place that decides whether a copy happens.
            logger.error(
                "receipt %s carries %r and has no readable transaction record, "
                "so there is nothing to name its client folder copy from and "
                "none is written. %s still holds the document",
                receipt_id, config.BANK_ATTACHMENT_STATUS, config.FILES_DIR)
            copy_status = ""
    else:
        extraction = repo.get_extraction_for_receipt(receipt_id) or {}
    source_path = Path(receipt["file_path"])

    dest_path = None
    if not source_path.exists():
        # The archive of record is missing, so there is nothing to copy FROM.
        # Reported and the note still applied: refusing would put a note in
        # `failed\` for a state no second attempt can fix.
        logger.error(
            "receipt %s is attached to a transaction and the file it was "
            "processed from is not at %s, so no client folder copy can be "
            "made", receipt_id, source_path)
    else:
        dest_path = copy_for_published_receipt(
            repo,
            receipt_id=receipt_id,
            client_id=receipt.get("client_id"),
            source_file=source_path,
            invoice_date=(extraction.get("invoice_date")
                          or datetime.now(timezone.utc).date().isoformat()),
            supplier=extraction.get("supplier_name") or "unknown",
            gross=(extraction.get("gross_amount")
                   if extraction.get("gross_amount") is not None else 0.0),
            # The row's own status, so the `ok`-only gate does the deciding.
            validation_status=copy_status,
            filed_path=receipt.get("filed_path"),
            # The moment this call is. Everything else that reaches that
            # function is the publish path.
            at=config.CLIENT_COPY_AT_POST,
        )

    if config.CLIENT_COPY_TRIGGER == config.CLIENT_COPY_ON_PUBLISH and is_bank_attachment:
        # **Sub-step 10f.38, and it is the one place the two sub-steps differ.**
        # A receipt on this trigger already has its copy, made when it
        # published. A document attached from a bank line is never published,
        # by Paul's own condition, so the moment this trigger names never
        # arrives for one and it gets no copy at all, ever. Said out loud
        # because a firm on `publish` that attaches documents from bank lines
        # would otherwise see nothing and have nothing to read.
        logger.info(
            "receipt %s is a document attached to a transaction and %s is %r. "
            "An attached document is never published, so that moment never "
            "comes for one and no copy is written into %s. Set %s to %r to "
            "copy a document at the moment it is attached to a posted "
            "transaction",
            receipt_id, config.CLIENT_COPY_TRIGGER_FIELD,
            config.CLIENT_COPY_ON_PUBLISH, config.CLIENTS_ROOT,
            config.CLIENT_COPY_TRIGGER_FIELD, config.CLIENT_COPY_AT_POST)
    elif config.CLIENT_COPY_TRIGGER == config.CLIENT_COPY_ON_PUBLISH:
        logger.info(
            "receipt %s is attached to a transaction. %s is %r, so its client "
            "folder copy was already made when it published and there is "
            "nothing to write now",
            receipt_id, config.CLIENT_COPY_TRIGGER_FIELD,
            config.CLIENT_COPY_ON_PUBLISH)
    elif config.CLIENT_COPY_TRIGGER == config.CLIENT_COPY_NEVER:
        logger.info(
            "receipt %s is attached to a transaction. %s is %r, so nothing is "
            "written into %s",
            receipt_id, config.CLIENT_COPY_TRIGGER_FIELD,
            config.CLIENT_COPY_NEVER, config.CLIENTS_ROOT)
    elif dest_path:
        logger.info(
            "receipt %s is attached to a transaction, so its client folder "
            "copy is due: %s", receipt_id, dest_path)

    detail = {ATTACHED_ACTION: True}
    if dest_path:
        detail[EVENT_CLIENT_COPY_WRITTEN_KEY] = str(dest_path)

    # **The audit row is what makes the note idempotent**, because
    # `_note_already_applied()` finds a note by its `resolved_at` in this
    # blob. A handler that wrote no row would apply the same message on every
    # poll for ever.
    _record_event(repo, receipt_id, DESKTOP_ACTOR, DESKTOP_SOURCE,
                  "attach", ATTACHED_ACTION,
                  note_resolved_at=note.resolved_at, detail=detail)

    return ResolutionOutcome(
        outcome=ATTACHED_ACTION, receipt_id=receipt_id,
        filed_path=str(dest_path) if dest_path else None,
        message=(f"Attached to a transaction. Filed to {dest_path}"
                 if dest_path else "Attached to a transaction."),
    )


def _apply_corrected_note(repo, categorisation_engine, receipt: Dict[str, Any],
                          note: ResolutionNote) -> ResolutionOutcome:
    """Step 10k. The figures on an already-filed receipt were wrong.

    **Added 2026-09-11 by amendment 235's step, on Paul's decision closing
    outstanding items 36 and 167.** A receipt has been through the pipeline,
    validated, categorised and filed, and its figures are in the books. Paul
    then finds one of them is wrong. Until this there was no route for that
    correction to reach the pipeline's own record, so the database went on
    holding what the extraction read.

    **This function translates and delegates. It writes nothing itself**, which
    is `_settle_note()`'s rule and the reason there is no second implementation
    of resolution to drift from the first. Every write is `resolve_receipt()`'s:
    it merges the corrected values, re-validates, appends the extraction row,
    categorises, applies the category as a GL override and learns on the tick.

    ## What makes it different from a settle, and it is one thing

    **The receipt is already filed, so no file moves.** `filing_already_settled`
    is what carries that: it lets the call past step 1a's refusal, skips the
    client folder copy at step 11, and makes the audit row say `corrected`
    rather than `filed`. The name says the reason rather than the effect, which
    is amendment 309's rule for `decided_by_operator` and exists so that the
    next person with an inconvenient `already_filed` guard does not reach for
    it: to pass this keyword honestly you have to be correcting a receipt whose
    filing is settled.

    **And 18.2b is why nothing is withdrawn either.** A copy in the client
    folder is written once and never withdrawn, so a corrected figure does not
    rename or replace the file already there. The document is unchanged; it was
    the reading of it that was wrong.

    ## Three decisions taken here

    **`decided_by_operator=True`, and this is the second production call site.**
    Amendment 309 built it for `_settle_note()`, where a person had filed a row
    into the books. **The reasoning is stronger here**: the row has been in the
    books since before this edit, so a correction left as `still_invalid` would
    put the note in `Resolutions\\failed\\` while the books hold the corrected
    figures, which is exactly the disagreement amendment 306 exists to stop.

    **A receipt with no extraction is refused, and that is `resolve_receipt()`
    doing it rather than a guard here.** Its step 2 returns `not_found` with
    "This receipt has no extraction to correct". The live shape is an attached
    document from sub-step 10f.38: never offered to extraction, so there are no
    figures to correct, and 18.1 says the transaction carries them. The note
    goes to `failed\\` with the reason, which is where something a person has to
    look at belongs.

    **A correction for a receipt this pipeline never issued never reaches
    here.** `_receipt_for_note()` returns None and `apply_resolution_note()`
    answers `not_found` before any handler runs, which is every action's
    behaviour and not this one's.

    ## The tick, and the guarantee carried across by hand

    **Withheld when the client's chart did not confirm the code**, exactly as
    `_settle_note()` withholds it. `resolve_receipt()`'s step 13 has no chart
    test, because its corrections come from a person using a picker built from
    the chart, and a mapping is read back by layer 1 as an exact match with
    confidence `high`. So a code nothing confirmed would be applied confidently
    to every future receipt from that vendor.
    """
    receipt_id = receipt["receipt_id"]
    category = _resolve_category(note, receipt.get("client_id"))

    # Only the fields the note actually carried, which is what
    # `_merge_corrections()` merges on: presence, not truthiness. Same as
    # `_settle_note()`, and the same reason: a `net_amount` of null lands as
    # NULL rather than inheriting the extractor's figure.
    values = {name: note.values[name] for name in CORRECTABLE_FIELDS
              if name in note.values}

    remember = bool(note.remember_gl_for_supplier and category.code
                    and category.chart_confirmed)
    if note.remember_gl_for_supplier and not remember:
        logger.warning(
            f"remember_gl_for_supplier was ticked for the correction to "
            f"{receipt_id} but the code {category.code!r} is not one the "
            "client's chart confirmed, so nothing will be learned. A mapping "
            "is read back by layer 1 as an exact match with high confidence"
        )

    corrections = Corrections(
        values=values,
        gl_nominal_code=category.code,
        gl_account_name=category.name,
        gl_correction_reason="category from the IntelliBooks Desktop resolution note",
        remember_gl_for_supplier=remember,
    )

    logger.info(
        f"correcting receipt {receipt_id} from the IntelliBooks Desktop note "
        f"resolved at {london_time.stamp(note.resolved_at)}: it is already filed at "
        f"{receipt.get('filed_path')!r}, so no file moves and nothing is "
        "copied or withdrawn"
    )
    outcome = resolve_receipt(
        repo, categorisation_engine, receipt_id, corrections,
        actor=DESKTOP_ACTOR, source=DESKTOP_SOURCE,
        note_resolved_at=note.resolved_at,
        # See this function's docstring. The row is already in the books, so a
        # failed check is recorded on the extraction row and logged rather than
        # used to block a correction the operator has already made.
        decided_by_operator=True,
        # Step 10k. The one thing that separates a correction from a settle.
        filing_already_settled=True,
    )
    if category.validation_note:
        # The chart's verdict on the code. `resolve_receipt()` writes the
        # extraction row and has no notion of a note, and the row is
        # append-only and already saved by the time this returns, so it is
        # surfaced on the outcome rather than dropped. `_settle_note()` does
        # the same.
        outcome.validation_notes = list(outcome.validation_notes or []) + [
            category.validation_note]
        logger.info(
            f"the chart's verdict on the corrected category for {receipt_id}: "
            f"{category.validation_note}"
        )
    return outcome


def apply_resolution_note(repo, categorisation_engine, note: dict) -> ResolutionOutcome:
    """Back-feed entry point. Design document 12.3.

    Validates the note, finds its receipt, then does one of three things with
    actor='desktop' and source='desktop': discards the receipt, records a filing
    Desktop has already done, or settles the receipt from the note's corrected
    values.

    **It does not reimplement resolution.** A discard goes straight to
    `discard_receipt()`, a note with no `filed_path` goes straight to
    `resolve_receipt()` through `_settle_note()`, and a note that carries one is
    the single documented divergence, for the reason in `_apply_filed_note()`.

    Returns an outcome and never raises. `filed` and `discarded` mean the note was
    applied and the caller may move it to `processed\\`. Anything else means it was
    not, and the caller moves it to `failed\\`. Nothing in `Resolutions\\` is ever
    deleted, on any path.
    """
    receipt_id_hint = note.get("receipt_id") if isinstance(note, dict) else None

    try:
        parsed = parse_resolution_note(note)
    except ResolutionNoteError as exc:
        logger.error(f"unusable resolution note for {receipt_id_hint}: {exc}")
        return ResolutionOutcome(
            outcome="error", receipt_id=str(receipt_id_hint or ""),
            message=f"This resolution note does not match the contract: {exc}",
            error_detail=str(exc),
        )

    receipt = _receipt_for_note(repo, parsed)
    if not receipt:
        return ResolutionOutcome(
            outcome="not_found", receipt_id=str(parsed.receipt_id or ""),
            message=(
                f"No receipt matches this note (receipt_id={parsed.receipt_id!r}, "
                f"review files={parsed.original_review_files})."
            ),
            error_detail="no receipt matched by id or by review filename",
        )

    receipt_id = receipt["receipt_id"]

    applied = _note_already_applied(repo, receipt_id, parsed.resolved_at)
    if applied:
        logger.info(
            f"note for {receipt_id} resolved at "
            f"{london_time.stamp(parsed.resolved_at)} was already applied on "
            f"{london_time.stamp(applied['created_at'])}; nothing to do"
        )
        outcome = applied["outcome"]
        return ResolutionOutcome(
            outcome=outcome if outcome in NOTE_APPLIED_OUTCOMES else parsed.action,
            receipt_id=receipt_id,
            extraction_id=applied.get("extraction_id"),
            filed_path=receipt.get("filed_path"),
            message=("Already applied on "
                     f"{london_time.stamp(applied['created_at'])}. "
                     "Nothing was changed."),
        )

    if parsed.action == "discarded":
        return discard_receipt(
            repo, receipt_id,
            reason=parsed.reason or "discarded in IntelliBooks Desktop",
            actor=DESKTOP_ACTOR, source=DESKTOP_SOURCE,
            note_resolved_at=parsed.resolved_at,
            # Paul's decision of 2026-09-10. The operator was asked whether the
            # copy in the client folder goes too, and this is their answer.
            # `parse_resolution_note()` has already forced it to False on any
            # action but this one.
            delete_client_copy=parsed.delete_client_copy,
        )

    if parsed.action == ATTACHED_ACTION:
        # Sub-step 10f.37. It takes no `categorisation_engine`, because it
        # writes no categorisation: nothing about the receipt changes.
        return _apply_attached_note(repo, receipt, parsed)

    if parsed.action == CORRECTED_ACTION:
        # Step 10k. **The action word chooses here and the field cannot**, and
        # `CORRECTED_ACTION`'s own comment carries why: nothing in the note
        # distinguishes a correction from a settle, because the one difference
        # is that the receipt is already filed, which is a fact about this
        # side's row rather than a field Desktop can send.
        return _apply_corrected_note(repo, categorisation_engine, receipt, parsed)

    # Sub-step 10f.14. **The field chooses, not the action word.** See
    # `parse_resolution_note()` for what each shape means and
    # `TheTwoShapesTakeDifferentPathsTest` for the guard that both stay
    # reachable.
    if parsed.filed_path:
        return _apply_filed_note(repo, categorisation_engine, receipt, parsed)
    return _settle_note(repo, categorisation_engine, receipt, parsed)

r"""A document attached from the Bank Transactions tab. Sub-step 10f.38.

**Paul's requirement of 2026-09-10 and his decisions of 2026-09-11, amendments
320 and 321.** He is looking at a bank line and has the document in his hand.
Today the only route in is the Receipts tab and the pipeline, so he has to send
it, wait, and come back. IntelliBooks now attaches it there and then, and hands
the document to Intellibills to archive and to file.

**Four conditions, all his.**

- **Not extracted and not validated.** The transaction already carries the
  date, the amount and the description, and a document that is not a receipt
  would otherwise fail into Review.
- **Never published back.**
- **Never in the receipts list**, which follows from the one above: that list
  is fed by IntelliBooks draining `IntelliBooks\Incoming\`, per 18.3.
- **The client folder copy happens at Post**, on the same trigger as 10f.37 and
  through the `attached` note that already exists.

## The handoff

`config.ATTACHED_DIR`, which is `Intellibills\Attached\`. Desktop writes two
files into it: the document, and a JSON message naming it. **Only the message
is scanned**, and it names the document, so there is no sidecar naming
convention to get the wrong way round. That matters because there are two in
this system and one was written for the other once: an inbox sidecar replaces
the extension and a filed receipt's appends to it, which is the defect Paul
found at sub-step 10d.12.

Both files move into `processed\` on success and the message moves into
`failed\` with an `.error.txt` beside it otherwise. **Nothing is ever deleted**,
which is `Resolutions\`'s rule and is what makes a handover auditable.

**The document has to move too, and not only for tidiness.** Left where it is,
the next poll would archive it again under a second receipt id, because the
message that connected the two has gone.

## What the message carries, and why each field is in it

`receipt_id`, `client_id`, `transaction_id`, `transaction_date`,
`transaction_description`, `transaction_amount`, `filename`, `attached_at`, plus
`schema` and `action`. Nothing else is read.

**`receipt_id` is minted by Desktop, and that is what makes the handoff need no
reply channel.** Desktop has to send the 10f.37 `attached` note when the
transaction is posted, and that note is keyed on `receipt_id`. 18.3's handoff is
one way and the brief forbids anything reaching `IntelliBooks\Incoming\`, so the
pipeline has no way to tell Desktop an id it invented. Desktop invents it
instead, and it is held to being a uuid rather than to anything a keystroke
could produce. **It is also what makes a re-delivered message idempotent**: the
same attach names the same row.

**A Desktop-composed id is not a Desktop-composed path.** 12.2 already has
Desktop sending a `receipt_id` in every note, and 10f.37's rule is about names
and paths, because a collision's `-2` cannot be told from its original. An id
collides or it does not, and a collision here is simply a row that already
exists.

**The three transaction values are carried and the filename of the copy is
not.** 10f.37's rule again, and section 4 of the brief: the pipeline composes
the client folder name from the transaction date, the description normalised the
way a supplier name is, and the amount, so the folder reads the same way
whichever route a document took.

**They are recorded on arrival and used at Post**, because those are two
moments and the row has no column for any of them. The audit row's
`corrections_json` is where this project already puts what section 5.1 has no
column for: the note's own `resolved_at`, the path a discard cleared, the
document a discard deleted. See `transaction_values()` below.

## The marker

`config.BANK_ATTACHMENT_STATUS` on the row, and the reasoning is written where
the constant is. In short: a plain `ok` row would be offered by
`get_unpublished_ok_receipts()` on the next poll, published, drained by Desktop
and would appear in the receipts list, which Paul's third condition forbids.
"""

import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import config
from worker.storage.store import compute_hash, is_supported, save_inbox_file

logger = logging.getLogger(__name__)

#: Bump only when both halves of the handoff change. The same rule
#: `NOTE_SCHEMA` carries for section 12.2's notes.
ATTACHED_SCHEMA = 1

#: What the message says it is. **A different word from the resolution note's
#: `attached`**, and deliberately: that one says a receipt is now attached to a
#: transaction, this one says a document is being handed over to be recorded.
#: One word apart would be the `postTxn()` and `postReceiptToCashbook()` trap,
#: and a note dropped into the wrong folder has to fail loudly rather than be
#: half-read, which `parse_attached_message()` below is what makes happen.
ATTACH_ACTION = "attach_document"

#: The action recorded on the arrival audit row, and the outcome beside it.
#: Its own word rather than a reuse of the resolution vocabulary: nothing was
#: resolved, a document was recorded.
ARRIVAL_ACTION = "attach_document"
ARRIVAL_OUTCOME = "attached_document"

#: Who and what. `actor` is the operator and `source` the tool, per 12.3 step 4,
#: and both are `desktop` because Desktop has no user accounts. A person did
#: press Attach, which is why this is not `pipeline` the way
#: `worker\categorisation\fallback.py`'s row is.
ATTACHED_ACTOR = "desktop"
ATTACHED_SOURCE = "desktop"

#: The keys the arrival row's `corrections_json` carries, so the reader at Post
#: and the writer at arrival cannot disagree about a spelling.
ARRIVAL_TRANSACTION_ID_KEY = "transaction_id"
ARRIVAL_DATE_KEY = "transaction_date"
ARRIVAL_DESCRIPTION_KEY = "transaction_description"
ARRIVAL_AMOUNT_KEY = "amount"

#: `receipts.source`. 10d.40 gives the column four values and no others, and
#: IntelliBooks Desktop is what `desktop` already means: this is a fifth route
#: into the product and not a fifth word for the column.
ATTACHED_ROW_SOURCE = "desktop"

#: `receipts.message_id` is NOT NULL and already holds "a synthesised id for an
#: inbox file". This is where the transaction the document belongs to lives on
#: the row. **Two documents attached to one transaction share it**, which is
#: correct and harmless: nothing keys on `message_id` for a row off the email
#: path, no `processed_attachments` row is written and no `email_alerts` row
#: either.
MESSAGE_ID_PREFIX = "bank-attachment"

# YYYY-MM-DD, zero-padded. The same expression the resolution service applies to
# a note's `invoice_date`, and for a sharper reason here: this date names the
# tax year folder as well as the file, so `2026-4-1`, which `strptime` accepts,
# would file a document into a folder nobody would look in.
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class AttachedMessageError(Exception):
    """The message does not match the handoff contract.

    Raised rather than returned, and the caller puts the message in `failed\\`
    with the reason beside it. Strict for `parse_resolution_note()`'s reason:
    the other half of this contract is built by a session that cannot see this
    one, so a message that does not match is worth surfacing rather than half
    applying.
    """


@dataclass
class AttachedMessage:
    """One handed-over document, validated."""

    receipt_id: str
    client_id: str
    transaction_id: str
    transaction_date: str
    transaction_description: str
    amount: float
    filename: str
    attached_at: str
    attached_by: Optional[str] = None


def _text(raw: Dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise AttachedMessageError(
            f"{key!r} is required and must be a non-empty string")
    return value.strip()


def parse_attached_message(raw: Any) -> AttachedMessage:
    """Validate and normalise one handoff message. Never returns junk.

    The one deliberate leniency is the same as 12.2's: extra keys are ignored,
    so the contract can gain a field without every message failing.
    """
    if not isinstance(raw, dict):
        raise AttachedMessageError(
            f"a handoff message must be a JSON object, got {type(raw).__name__}")

    schema = raw.get("schema")
    if schema != ATTACHED_SCHEMA:
        raise AttachedMessageError(
            f"unsupported message schema {schema!r}; this pipeline understands "
            f"{ATTACHED_SCHEMA}")

    action = raw.get("action")
    if action != ATTACH_ACTION:
        raise AttachedMessageError(
            f"'action' must be {ATTACH_ACTION!r}, got {action!r}. A resolution "
            f"note belongs in {config.RESOLUTIONS_DIR.name}\\, not here")

    receipt_id = _text(raw, "receipt_id")
    try:
        # `uuid.UUID` accepts a braced or unhyphenated spelling, so the round
        # trip is what holds the id to the form every other receipt_id in the
        # database has. A row whose key is spelled differently from its
        # siblings is one that a hand-written query misses.
        if str(uuid.UUID(receipt_id)) != receipt_id.lower():
            raise ValueError("not the canonical spelling")
    except (ValueError, AttributeError, TypeError) as error:
        raise AttachedMessageError(
            f"'receipt_id' must be a uuid, got {receipt_id!r}: {error}") from None

    filename = _text(raw, "filename")
    if Path(filename).name != filename or filename in (".", ".."):
        raise AttachedMessageError(
            f"'filename' must name one file beside the message and cannot be a "
            f"path, got {filename!r}")
    if not is_supported(filename):
        raise AttachedMessageError(
            f"'filename' {filename!r} is not a document type this pipeline "
            "handles")

    transaction_date = _text(raw, "transaction_date")
    if not _ISO_DATE_RE.match(transaction_date):
        raise AttachedMessageError(
            f"'transaction_date' must be YYYY-MM-DD, got {transaction_date!r}")
    try:
        datetime.fromisoformat(transaction_date)
    except ValueError as error:
        raise AttachedMessageError(
            f"'transaction_date' {transaction_date!r} is not a date: {error}") from None

    amount = raw.get("transaction_amount")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise AttachedMessageError(
            f"'transaction_amount' must be a number, got {amount!r}")
    # Absolute, because a bank payment is negative in the books and a receipt's
    # gross is not, and the filename convention this composes is the receipt
    # one. The same `Math.abs()` Desktop applies to a note's amounts per 12.2.
    # Two decimal places, per Paul's ruling of 2026-07-28: an amount is a money
    # value and must read as one.
    amount = round(abs(float(amount)), 2)

    return AttachedMessage(
        receipt_id=receipt_id,
        client_id=_text(raw, "client_id"),
        transaction_id=_text(raw, "transaction_id"),
        transaction_date=transaction_date,
        transaction_description=_text(raw, "transaction_description"),
        amount=amount,
        filename=filename,
        attached_at=_text(raw, "attached_at"),
        attached_by=raw.get("attached_by"),
    )


@dataclass
class AttachedOutcome:
    """What `record_attached_document()` did.

    `recorded` is what decides `processed\\` from `failed\\`, so the caller has
    one thing to read. `already_recorded` is a success: the row is there and
    this delivery changed nothing.
    """

    recorded: bool
    receipt_id: str
    reason: Optional[str] = None
    stored_path: Optional[Path] = None
    already_recorded: bool = False


def record_attached_document(repo, message: AttachedMessage,
                             document: Path) -> AttachedOutcome:
    """Archive one handed-over document and write its row. **Marked.**

    Three things happen and no others: the document goes into the archive of
    record, a `receipts` row is written carrying the marker, and an audit row
    records the transaction it was attached to.

    **No extraction row, no categorisation row, no `publish_events` row, and
    nothing reaches `IntelliBooks\\Incoming\\`.** Paul's first two conditions,
    and they are satisfied by this function not doing those things rather than
    by a guard. `tests/test_attached_document.py` asserts each absence.

    **No client folder copy here.** That is due at Post, through the `attached`
    note, on the firm's trigger. Writing it here would be the arrival write
    amendment 73 cancelled, arriving through a different door.

    **The client must be in the registry.** A bank line lives in a client's
    books, so Desktop knows the client, and an id the registry does not hold is
    a registry disagreement rather than a receipt with no client. **Not
    `UNKNOWN_CLIENT_ID`**, which is what an unattributable arrival gets: this
    document cannot be filed for a client nobody can name, so recording it and
    leaving it unfilable would be a row nothing would ever finish.
    """
    existing = repo.get_receipt(message.receipt_id)
    if existing:
        logger.info(
            "the document for transaction %s is already recorded as receipt "
            "%s, so nothing is archived and no second row is written",
            message.transaction_id, message.receipt_id)
        return AttachedOutcome(recorded=True, receipt_id=message.receipt_id,
                               already_recorded=True,
                               stored_path=Path(existing["file_path"]))

    client = config.CLIENTS_BY_ID.get(message.client_id)
    if not client:
        return AttachedOutcome(
            recorded=False, receipt_id=message.receipt_id,
            reason=(f"client_id {message.client_id!r} is not in "
                    f"{config.CLIENTS_JSON.name}, so this document cannot be "
                    "attributed or filed"))

    if not document.exists():
        return AttachedOutcome(
            recorded=False, receipt_id=message.receipt_id,
            reason=f"the document named by this message is not at {document}")

    # The same writer into the document store every folder-intake file goes
    # through, so the archive of record has one shape and one owner. 10d.53:
    # keyed on client_id, and the year and month are the arrival date, so no
    # file in the store ever has to move.
    data = document.read_bytes()
    stored = save_inbox_file(message.receipt_id, message.client_id, document)

    repo.save_receipt(
        receipt_id=message.receipt_id,
        message_id=f"{MESSAGE_ID_PREFIX}:{message.transaction_id}",
        email_subject=None,
        email_from=None,
        email_received_at=None,
        filename=message.filename,
        file_path=stored,
        file_hash=compute_hash(data),
        firm_id=client["firm_id"],
        client_id=message.client_id,
        source=ATTACHED_ROW_SOURCE,
    )
    # `save_receipt()` writes `pending` as a SQL literal, which is right for
    # every other caller: a receipt is pending until it has been read.
    # **This one is never going to be read**, so the marker goes on
    # immediately. Done in two statements rather than by giving
    # `save_receipt()` a `status` parameter: 10d.17 removed that function's
    # four keyword defaults precisely so no caller could leave a value unstated,
    # and a defaulted fifth would put one back. A required fifth would touch
    # twenty-six call sites for one row shape, and a second `INSERT INTO
    # receipts` would make two writers of the table where there is one.
    #
    # A crash between the two leaves a `pending` row with no extraction, which
    # is inert: `find_failed_by_version()` asks for `failed` or `needs_review`
    # AND joins `extractions`, and nothing else selects `pending` at all. That
    # is the same residue a crash part way through any intake leaves.
    repo.update_receipt_status(message.receipt_id, config.BANK_ATTACHMENT_STATUS)

    repo.save_resolution_event(
        event_id=str(uuid.uuid4()),
        receipt_id=message.receipt_id,
        actor=ATTACHED_ACTOR,
        source=ATTACHED_SOURCE,
        action=ARRIVAL_ACTION,
        outcome=ARRIVAL_OUTCOME,
        created_at=datetime.now(timezone.utc).isoformat(),
        corrections_json=json.dumps({
            ARRIVAL_TRANSACTION_ID_KEY: message.transaction_id,
            ARRIVAL_DATE_KEY: message.transaction_date,
            ARRIVAL_DESCRIPTION_KEY: message.transaction_description,
            ARRIVAL_AMOUNT_KEY: message.amount,
            "attached_at": message.attached_at,
        }, sort_keys=True),
        reason=None,
    )

    logger.info(
        "receipt %s recorded from a document attached to transaction %s for "
        "client %s, archived at %s. It carries %r, so it is never extracted, "
        "never validated and never published",
        message.receipt_id, message.transaction_id, message.client_id, stored,
        config.BANK_ATTACHMENT_STATUS)
    return AttachedOutcome(recorded=True, receipt_id=message.receipt_id,
                           stored_path=stored)


def transaction_values(repo, receipt_id: str) -> Optional[Dict[str, Any]]:
    """The transaction one attached document was attached to, or None.

    **The three values the client folder copy is named from**, recorded at
    Attach by `record_attached_document()` above and read here at Post, because
    those are two moments and `receipts` has no column for any of them.

    Returns None for a receipt that is not an attached document, which is what
    lets the caller tell the two apart without reading the status twice.

    **The oldest arrival row wins**, by taking the last of
    `list_resolution_events()`, which is newest first. There is only ever one:
    `record_attached_document()` returns before writing a second row for a
    receipt_id it has already seen. Stated because a reader should not have to
    work out that a list of one is a list of one.
    """
    arrivals = [event for event in repo.list_resolution_events(receipt_id)
                if event.get("action") == ARRIVAL_ACTION
                and event.get("outcome") == ARRIVAL_OUTCOME]
    if not arrivals:
        return None
    try:
        payload = json.loads(arrivals[-1].get("corrections_json") or "{}")
    except ValueError as error:
        logger.error(
            "the arrival row for receipt %s does not hold readable JSON, so "
            "its client folder copy cannot be named from the transaction: %s",
            receipt_id, error)
        return None
    if not isinstance(payload, dict):
        return None
    return payload

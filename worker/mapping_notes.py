"""A taught supplier mapping: change its code, or delete it. Flag F2 of step 10bu.

Brief `PROMPT_claude_code_2026-11-14_mapping_edit_and_delete.md`. **Paul's
decision of 2026-11-14, option 1 of three.** A taught mapping's nominal code can
be changed, and the account name moves with it. A taught mapping can be
deleted. **The supplier name and the vendor key cannot be changed**: they are
the row's identity, and the key decides what the row is grouped with and what
the fuzzy layers score against. Changing a name is a delete and a fresh teach.

**Why it exists.** Nothing in production edited or deleted a row of
`categorisations_client_vendors`, so a supplier taught the wrong account stayed
wrong, and the only way out was to teach it again.

**How a change arrives: the route rules and corrections already take.**
IntelliBooks Desktop writes a note into `config.RESOLUTIONS_DIR` with
`writeResolutionNote()`, the poll applies it in `_consume_resolution_notes()`,
and the note moves to `processed\\` or to `failed\\` with the reason beside it.
`apply_resolution_note()` hands these two words here before it looks for a
receipt, because a mapping note is not about a receipt.

**Name the row by its `mapping_id`**, which the published mappings file
carries as `config.MAPPING_ID_FIELD`. For `writeResolutionNote()`'s `fileKey`,
pass the `mapping_id`, so a change and a later delete of one row are applied in
the order they were made.

A `mapping_code_changed` note::

    {"schema": 1, "action": "mapping_code_changed", "resolved_at": "<ISO>",
     "client_id": "Client_007", "mapping_id": "<from the mappings file>",
     "nominal_code": "7301"}

A `mapping_deleted` note::

    {"schema": 1, "action": "mapping_deleted", "resolved_at": "<ISO>",
     "client_id": "Client_007", "mapping_id": "<from the mappings file>"}

**What a code change does.** The row's `nominal_code` becomes the note's code
and its `account_name` becomes **the client's chart's own name for that code**,
the rule the Desktop teaching route already follows in `_resolve_category()`,
so the stored pair cannot disagree. An `account_name` in the note is ignored.
`times_seen` is left alone, because a correction is not a sighting, and
`last_updated` moves. The same code again is applied and changes nothing.

**What it refuses**, each to `failed\\` with the reason, and nothing changes:
a schema other than 1; no `resolved_at`; no `client_id`, or one that is not
text, or not in the registry; no `mapping_id`; a row that belongs to another
client. And on a code change only: a row that is not there; no code, a code
that is not text, or not four digits; a chart that cannot be read; a code the
client's chart does not hold, because the chart check would strip it from
every later receipt; and a note that carries `vendor_name` or `vendor_key`,
because neither can be changed and a Desktop that thinks otherwise should find
out at once rather than have the field ignored.

**Deleting a row that is not there is applied, not refused**, so a note
delivered twice reaches `processed\\` both times.

**The firm pool is never touched here.** Whether a correction should reach it
is not decided; see the report of 2026-11-14.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import config
from worker.categorisation.chart import get_chart_accounts_for_client

logger = logging.getLogger(__name__)

MAPPING_ACTIONS = (config.MAPPING_CODE_CHANGED_ACTION, config.MAPPING_DELETED_ACTION)

_ACCOUNT_CODE_RE = re.compile(r"^\d{4}$")

# Present in a code-change note means somebody tried to change the identity.
_NOT_EDITABLE = (config.MAPPING_VENDOR_NAME_FIELD, config.MAPPING_VENDOR_KEY_FIELD)


class MappingNoteError(ValueError):
    """A mapping note that cannot be applied as written."""


@dataclass
class MappingNoteOutcome:
    outcome: str            # the action word when applied, else "error"
    mapping_id: str
    message: str
    error_detail: Optional[str] = None


def is_mapping_note(note: Any) -> bool:
    return isinstance(note, dict) and note.get("action") in MAPPING_ACTIONS


def _required_text(note: dict, key: str) -> str:
    value = note.get(key)
    if value is None:
        raise MappingNoteError(f"'{key}' is required")
    if not isinstance(value, str):
        raise MappingNoteError(f"'{key}' must be text, got {type(value).__name__}")
    value = value.strip()
    if not value:
        raise MappingNoteError(f"'{key}' is required")
    return value


def _apply(repo, note: dict) -> str:
    if note.get("schema") != 1:
        raise MappingNoteError(f"unsupported note schema {note.get('schema')!r}; "
                               "this pipeline understands 1")
    _required_text(note, "resolved_at")
    client_id = _required_text(note, config.MAPPINGS_CLIENT_ID_FIELD)
    if client_id not in config.CLIENTS_BY_ID:
        raise MappingNoteError(f"client {client_id!r} is not in the registry")
    mapping_id = _required_text(note, config.MAPPING_ID_FIELD)
    row = repo.get_client_vendor_mapping(mapping_id)
    if row is not None and row["client_id"] != client_id:
        raise MappingNoteError(
            f"mapping {mapping_id} belongs to client {row['client_id']}, "
            f"not {client_id}")

    if note["action"] == config.MAPPING_DELETED_ACTION:
        if row is None:
            return "There was no mapping with this id. Nothing was changed."
        repo.delete_client_vendor_mapping(mapping_id)
        return (f"Deleted {row['vendor_name']!r} -> {row['nominal_code']} "
                f"for {client_id}.")

    for key in _NOT_EDITABLE:
        if key in note:
            raise MappingNoteError(
                f"'{key}' cannot be changed: a mapping's supplier name and vendor "
                "key are its identity. Delete it and teach the name afresh")
    if row is None:
        raise MappingNoteError(f"no mapping {mapping_id} for client {client_id}")
    code = _required_text(note, config.MAPPING_NOMINAL_CODE_FIELD)
    if not _ACCOUNT_CODE_RE.match(code):
        raise MappingNoteError(f"'{config.MAPPING_NOMINAL_CODE_FIELD}' must be four "
                               f"digits, got {code!r}")
    accounts = get_chart_accounts_for_client(client_id)
    if not accounts:
        # An empty read is not evidence either way, which is
        # `_resolve_category()`'s rule; the teaching sites learn nothing here.
        raise MappingNoteError(f"client {client_id}'s chart could not be read, so "
                               f"{code} cannot be checked against it")
    if code not in accounts:
        raise MappingNoteError(f"{code} is not in client {client_id}'s chart")
    name = accounts[code]
    if (row["nominal_code"], row["account_name"]) == (code, name):
        return f"{row['vendor_name']!r} is already {code} {name}. Nothing was changed."
    repo.change_client_mapping_code(mapping_id, code, name,
                                   datetime.now(timezone.utc).isoformat())
    return (f"Changed {row['vendor_name']!r} from {row['nominal_code']} to "
            f"{code} {name} for {client_id}.")


def apply_mapping_note(repo, note: dict) -> MappingNoteOutcome:
    """Apply one `mapping_code_changed` or `mapping_deleted` note. Never raises."""
    raw_id = note.get(config.MAPPING_ID_FIELD)
    mapping_id = raw_id if isinstance(raw_id, str) else ""
    try:
        message = _apply(repo, note)
    except MappingNoteError as exc:
        logger.error(f"unusable mapping note for {mapping_id or 'no mapping id'}: {exc}")
        return MappingNoteOutcome(
            outcome="error", mapping_id=mapping_id,
            message=f"This mapping note does not match the contract: {exc}",
            error_detail=str(exc))
    except Exception as exc:
        logger.error(f"could not apply the mapping note for {mapping_id}: {exc}",
                     exc_info=True)
        return MappingNoteOutcome(outcome="error", mapping_id=mapping_id,
                                  message="This mapping note could not be applied.",
                                  error_detail=f"{type(exc).__name__}: {exc}")
    logger.info(f"mapping {mapping_id}: {message}")
    return MappingNoteOutcome(outcome=note["action"], mapping_id=mapping_id,
                              message=message)

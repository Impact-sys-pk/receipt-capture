"""Receipt rules, layer 0: written by note, published per client. Step 10bu.

Amendments 559 and 565 of `2026-07-25_CONSOLE_DESIGN.md`, Paul's decisions of
2026-11-14. Brief `PROMPT_claude_code_2026-11-14_receipt_rules_pipeline.md`.

**Why it exists.** Layer 0 ran on every receipt and could never match: nothing
wrote a rule and nothing showed one. This module is the writer and the
publisher. The matcher stays in `worker/categorisation/engine.py`.

**How a rule arrives: the route corrections already take.** IntelliBooks
Desktop writes a note into `config.RESOLUTIONS_DIR` with `writeResolutionNote()`,
the poll applies it in `_consume_resolution_notes()`, and the note moves to
`processed\\` or to `failed\\` with the reason beside it. Two action words,
`config.RULE_SAVED_ACTION` and `config.RULE_DELETED_ACTION`, and
`apply_resolution_note()` hands them here before it looks for a receipt,
because a rule is not about a receipt and carries no `receipt_id`.

A `rule_saved` note::

    {"schema": 1, "action": "rule_saved", "resolved_at": "<ISO>",
     "rule_id": "<id Desktop mints>",
     "rule": {"scope": "client", "scope_id": "CLIENT001", "rule_name": "...",
              "priority": 50, "vendor_key": null, "condition_type": "contains",
              "condition_field": "detail", "condition_value": "apcoa",
              "nominal_code": "7300", "account_name": "Parking"}}

A `rule_deleted` note carries `schema`, `action`, `resolved_at` and `rule_id`.

**Saving an existing `rule_id` is an edit**, and keeps the rule's `created_at`.
**Deleting a `rule_id` that is not there is applied, not refused**, so a note
delivered twice reaches `processed\\` both times.

**How a rule is shown.** `publish_all()` writes
`config.RECEIPT_RULES_DIR / f"{client_id}{config.RECEIPT_RULES_SUFFIX}"` for
every registered client, listing every rule that answers for that client in the
order layer 0 tries them, on `worker/supplier_mappings.py`'s method: written
only where it differs, atomically, never stopping a poll.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

import config
from worker.supplier_mappings import _on_disk, write_atomically

logger = logging.getLogger(__name__)

RULE_ACTIONS = (config.RULE_SAVED_ACTION, config.RULE_DELETED_ACTION)

_ACCOUNT_CODE_RE = re.compile(r"^\d{4}$")


class RuleNoteError(ValueError):
    """A rule note that cannot be applied as written. The message reaches the
    `.error.txt` beside the note in `failed\\`."""


@dataclass
class RuleNoteOutcome:
    outcome: str            # the action word when applied, else "error"
    rule_id: str
    message: str
    error_detail: Optional[str] = None


def is_rule_note(note: Any) -> bool:
    return isinstance(note, dict) and note.get("action") in RULE_ACTIONS


def _text(raw: dict, key: str, where: str) -> Optional[str]:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise RuleNoteError(f"'{where}{key}' must be text, got {type(value).__name__}")
    return value.strip() or None


def _required(raw: dict, key: str, where: str = "") -> str:
    value = _text(raw, key, where)
    if not value:
        raise RuleNoteError(f"'{where}{key}' is required")
    return value


def _parse_rule(raw: Any) -> dict:
    """The `rule` object of a `rule_saved` note, checked and normalised."""
    where = f"{config.RULE_NOTE_RULE_FIELD}."
    if not isinstance(raw, dict):
        raise RuleNoteError(f"'{config.RULE_NOTE_RULE_FIELD}' must be an object")

    scope = _required(raw, config.RULE_SCOPE_FIELD, where)
    if scope not in config.RULE_SCOPES:
        raise RuleNoteError(f"'{where}{config.RULE_SCOPE_FIELD}' must be one of "
                            f"{config.RULE_SCOPES}, got {scope!r}")
    scope_id = _required(raw, config.RULE_SCOPE_ID_FIELD, where)
    if scope == config.RULE_SCOPE_CLIENT and scope_id not in config.CLIENTS_BY_ID:
        raise RuleNoteError(f"client {scope_id!r} is not in the registry")
    if scope == config.RULE_SCOPE_FIRM and scope_id not in config.FIRMS:
        raise RuleNoteError(f"firm {scope_id!r} is not in the firm registry")
    if scope == config.RULE_SCOPE_SECTOR and scope_id == config.UNSPECIFIED_TRADE:
        raise RuleNoteError(
            f"a sector rule cannot be keyed on {config.UNSPECIFIED_TRADE!r}, which "
            "every client carries until it is given a trade")

    priority = raw.get(config.RULE_PRIORITY_FIELD)
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise RuleNoteError(f"'{where}{config.RULE_PRIORITY_FIELD}' must be a whole "
                            f"number, got {type(priority).__name__}")

    condition_type = _required(raw, config.RULE_CONDITION_TYPE_FIELD, where)
    if condition_type not in config.RULE_CONDITION_TYPES:
        raise RuleNoteError(f"'{where}{config.RULE_CONDITION_TYPE_FIELD}' must be one of "
                            f"{config.RULE_CONDITION_TYPES}, got {condition_type!r}")
    condition_field = _required(raw, config.RULE_CONDITION_FIELD_FIELD, where)
    if condition_field not in config.RULE_CONDITION_FIELDS:
        # Decision 5: the supplier name and the vendor key, nothing else.
        raise RuleNoteError(f"'{where}{config.RULE_CONDITION_FIELD_FIELD}' must be one of "
                            f"{config.RULE_CONDITION_FIELDS}, got {condition_field!r}")
    condition_value = _required(raw, config.RULE_CONDITION_VALUE_FIELD, where)
    if condition_type == "regex":
        # The matcher swallows a bad pattern and returns False, so one stored
        # here would be a rule that silently never matches.
        try:
            re.compile(condition_value.lower())
        except re.error as exc:
            raise RuleNoteError(f"'{where}{config.RULE_CONDITION_VALUE_FIELD}' is not "
                                f"a valid regular expression: {exc}")

    nominal_code = _required(raw, config.RULE_NOMINAL_CODE_FIELD, where)
    if not _ACCOUNT_CODE_RE.match(nominal_code):
        raise RuleNoteError(f"'{where}{config.RULE_NOMINAL_CODE_FIELD}' must be four "
                            f"digits, got {nominal_code!r}")

    return {
        "scope": scope,
        "scope_id": scope_id,
        "rule_name": _required(raw, config.RULE_NAME_FIELD, where),
        "priority": priority,
        "vendor_key": _text(raw, config.RULE_VENDOR_KEY_FIELD, where),
        "condition_type": condition_type,
        "condition_field": condition_field,
        "condition_value": condition_value,
        "nominal_code": nominal_code,
        "account_name": _required(raw, config.RULE_ACCOUNT_NAME_FIELD, where),
    }


def apply_rule_note(repo, note: dict) -> RuleNoteOutcome:
    """Apply one `rule_saved` or `rule_deleted` note. Never raises."""
    rule_id = str(note.get(config.RULE_ID_FIELD) or "")
    try:
        if note.get("schema") != 1:
            raise RuleNoteError(f"unsupported note schema {note.get('schema')!r}; "
                                "this pipeline understands 1")
        resolved_at = _required(note, "resolved_at")
        rule_id = _required(note, config.RULE_ID_FIELD)
        action = note["action"]
        if action == config.RULE_SAVED_ACTION:
            fields = _parse_rule(note.get(config.RULE_NOTE_RULE_FIELD))
            existed = repo.get_rule(rule_id) is not None
            repo.save_rule(rule_id=rule_id, saved_at=resolved_at, **fields)
            message = (f"{'Changed' if existed else 'Added'} {fields['scope']} rule "
                       f"{fields['rule_name']!r} for {fields['scope_id']}.")
        else:
            gone = repo.delete_rule(rule_id)
            message = ("Deleted the rule." if gone
                       else "There was no rule with this id. Nothing was changed.")
    except RuleNoteError as exc:
        logger.error(f"unusable rule note for {rule_id or 'no rule id'}: {exc}")
        return RuleNoteOutcome(
            outcome="error", rule_id=rule_id,
            message=f"This rule note does not match the contract: {exc}",
            error_detail=str(exc))
    except Exception as exc:
        logger.error(f"could not apply the rule note for {rule_id}: {exc}", exc_info=True)
        return RuleNoteOutcome(outcome="error", rule_id=rule_id,
                               message="This rule note could not be applied.",
                               error_detail=f"{type(exc).__name__}: {exc}")
    logger.info(f"rule {rule_id}: {message}")
    return RuleNoteOutcome(outcome=action, rule_id=rule_id, message=message)


def payload_for(repo, client_id: str) -> dict:
    """The file's content for one client, built only from the database."""
    client = config.CLIENTS_BY_ID.get(client_id) or {}
    rules = repo.get_client_rules(client_id, client.get("firm_id"),
                                  client.get("trade"))
    return {
        config.RULES_SCHEMA_FIELD: config.RECEIPT_RULES_SCHEMA,
        config.RULES_CLIENT_ID_FIELD: client_id,
        config.RULES_LIST_FIELD: [
            {
                config.RULE_ID_FIELD: r["rule_id"],
                config.RULE_SCOPE_FIELD: r["scope"],
                config.RULE_SCOPE_ID_FIELD: r["scope_id"],
                config.RULE_NAME_FIELD: r["rule_name"],
                config.RULE_PRIORITY_FIELD: r["priority"],
                config.RULE_VENDOR_KEY_FIELD: r["vendor_key"],
                config.RULE_CONDITION_TYPE_FIELD: r["condition_type"],
                config.RULE_CONDITION_FIELD_FIELD: r["condition_field"],
                config.RULE_CONDITION_VALUE_FIELD: r["condition_value"],
                config.RULE_NOMINAL_CODE_FIELD: r["nominal_code"],
                config.RULE_ACCOUNT_NAME_FIELD: r["account_name"],
                config.RULE_CREATED_AT_FIELD: r["created_at"],
                config.RULE_UPDATED_AT_FIELD: r["updated_at"],
            }
            for r in rules
        ],
    }


def publish_client(repo, client_id: str) -> bool:
    """Write one client's file if it differs from the database. True if written."""
    payload = payload_for(repo, client_id)
    path = config.RECEIPT_RULES_DIR / f"{client_id}{config.RECEIPT_RULES_SUFFIX}"
    if _on_disk(path) == payload:
        return False
    config.RECEIPT_RULES_DIR.mkdir(parents=True, exist_ok=True)
    write_atomically(path, payload)
    logger.info("published %d receipt rule(s) for %s to %s",
                len(payload[config.RULES_LIST_FIELD]), client_id, path)
    return True


def publish_all(repo) -> int:
    """Bring every registered client's file up to date. Returns how many were written."""
    written = 0
    for client_id in sorted(config.CLIENTS_BY_ID):
        try:
            if publish_client(repo, client_id):
                written += 1
        except Exception as exc:
            logger.warning(
                "could not publish the receipt rules for %s: %s. Nothing is lost: "
                "the database holds them and the next poll tries again",
                client_id, exc)
    return written

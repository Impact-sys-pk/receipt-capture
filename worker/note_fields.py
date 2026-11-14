"""Readers for the fields of a note IntelliBooks Desktop writes. Flag H5.

Brief `PROMPT_claude_code_2026-11-14_three_flags.md`, part 3. Three modules read
notes from `Intellibills\\Resolutions\\`: `worker\\resolution\\service.py` for a
receipt, `worker\\receipt_rules.py` for a rule and `worker\\mapping_notes.py` for
a taught mapping. Each held its own text reader and its own four-digit pattern,
word for word alike, so a change to one would leave the others behind.
`tests/test_note_fields.py` holds that no second copy reappears.

**The messages are the ones the three copies already produced, unchanged to the
character**, because tests assert them and an operator reads them in the
`.error.txt` beside a note in `failed\\`. Each caller passes its own error class,
so a receipt note still raises `ResolutionNoteError`, a rule note
`RuleNoteError` and a mapping note `MappingNoteError`.

`error` is keyword-only, so each caller's existing argument order is kept.
`where` is a prefix for a field inside a nested object, `rule.` for a rule
note's `rule` object, and empty otherwise.
"""

import re
from datetime import datetime, timezone
from typing import Any, Iterable, Optional, Tuple, Type

#: A master account code is four digits. Any three-digit code is legacy, per
#: amendment 96.
ACCOUNT_CODE_RE = re.compile(r"^\d{4}$")


def optional_text(raw: dict, key: str, where: str = "", *,
                  error: Type[Exception]) -> Optional[str]:
    """The field stripped, or None where it is absent, null or only spaces.

    Raises `error` where it is present and not text.
    """
    value: Any = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise error(f"'{where}{key}' must be text, got {type(value).__name__}")
    return value.strip() or None


def required_text(raw: dict, key: str, where: str = "", *,
                  error: Type[Exception]) -> str:
    """The field stripped. Raises `error` where it is absent, empty or not text."""
    value = optional_text(raw, key, where, error=error)
    if not value:
        raise error(f"'{where}{key}' is required")
    return value


# Note times, for flag F7 of 2026-11-14: a re-delivered older rule or mapping
# note must not undo a newer one. ------------------------------------------


def parse_time(text) -> Optional[datetime]:
    """An ISO 8601 time as an aware datetime, or None where it is not one.

    A time with no zone is read as UTC, which is what every writer here
    stores; Desktop writes `toISOString()`, which ends in `Z`.
    """
    if not isinstance(text, str):
        return None
    try:
        when = datetime.fromisoformat(text.strip())
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def note_time(raw: dict, key: str, *, error: Type[Exception]) -> Tuple[str, datetime]:
    """The field as text and as a time. Raises `error` where it is not a timestamp."""
    text = required_text(raw, key, error=error)
    when = parse_time(text)
    if when is None:
        raise error(f"'{key}' must be a timestamp, got {text!r}")
    return text, when


def stale_reason(text: str, when: datetime, applied: Iterable[Optional[str]]) -> Optional[str]:
    """Why a note made at `when` is stale, or None where it is not.

    `applied` is the note times already applied to the same rule or mapping.
    **Strictly earlier is stale; an equal time is not**, because that is the
    same note delivered twice, which is harmless. A time that does not parse is
    left out of the comparison rather than guessed at.
    """
    times = [(parse_time(t), t) for t in applied]
    times = [(w, t) for w, t in times if w is not None]
    if not times:
        return None
    newest, newest_text = max(times)
    if when < newest:
        return (f"stale: this note was made at {text}, and a change made at "
                f"{newest_text} has already been applied, so applying it would undo "
                f"a newer change")
    return None

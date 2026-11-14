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
from typing import Any, Optional, Type

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

r"""An item line off a receipt: a description and, where it was readable, an amount.

**Step 10p part one, amendment 340, on Paul's decision of 2026-09-12 after he ran
`probe_layer5.py` against the live database.**

## Why this module exists at all

Item lines were read off the extraction and stored nowhere. **So the same
receipt was categorised from less on every run after the first, and nothing on
screen or in the log said so.** The classifier saw them once, on the live
pipeline path where the extraction object was still in hand; every path that
reads an extraction back out of the database passed `None`.

## Why description and amount separately rather than the strings we had

**Strings are enough for the classifier, which only reads them. They are useless
for a split**, which needs an amount per line as a number. 18.4 says a document
carrying two rates is answered by a split rather than by a second rate on one
line, and Paul's RingGo receipt is that case: parking at 0% and two text
messages at 20% on one document. Splitting the amount out now is a smaller
change than re-doing it later, and the extractor is already being asked for
these lines.

**They are evidence and not an accounting record, per 18.1.** Nothing here
categorises a line, posts a line, or makes a split. This makes a split possible;
it does not build one.

## Why the module is here rather than in `worker\extraction\`

Both `worker\extraction\base.py` and `worker\database\repository.py` need it,
and the repository must not import the extraction layer to store a column. This
module imports nothing but the standard library, so it can sit under both.

## An amount that could not be read is None, and that is a decision

**Nought and absent are different answers and the difference reaches a future
split.** A receipt can print a line at 0.00, a free item or a fully discounted
one, and that is a real amount. A line whose amount could not be read is not a
line worth nought. Storing a missing amount as 0.0 would make a split that sums
the lines silently disagree with the document, which is the one thing 18.4's
split must not do: its lines must sum to the original.

So: **`amount is None` means "not read", and `amount == 0.0` means the receipt
said nought.**
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, List, Optional

#: The most item lines stored for one receipt.
#:
#: **The same 40 the prompt has asked for since 2026-09-05**, when `line_items`
#: was added and `max_tokens` was raised from 500 to 1500 to fit them. The
#: ceiling is a real cost control on the extraction reply, so it does not move
#: as part of this step.
#:
#: **What is new is that it is enforced in code as well as asked for in the
#: prompt.** It was advisory: the prompt said "List at most 40 lines" and
#: nothing truncated a model that answered with more. That was harmless while
#: the lines were held in memory and dropped; it is not harmless now they are
#: written to a column. A receipt with more than 40 lines stores the first 40,
#: which is what the prompt already asked for.
MAX_LINE_ITEMS = 40


@dataclass(frozen=True)
class LineItem:
    """One line as printed on the receipt.

    Frozen, because these are evidence of what a document said and nothing in
    the pipeline may amend one after the extraction that read it.
    """

    description: str
    amount: Optional[float] = None

    def as_dict(self) -> dict:
        return {"description": self.description, "amount": self.amount}

    @classmethod
    def from_dict(cls, raw: Any) -> Optional["LineItem"]:
        """One item from stored or model-supplied JSON, or None if unusable.

        **A line with no description is dropped rather than stored empty.** The
        description is the whole of what the classifier reads, so a line without
        one carries nothing for the reader it exists for, and an amount with no
        description cannot be checked against the document by a person either.
        """
        if not isinstance(raw, dict):
            return None
        description = raw.get("description")
        if not isinstance(description, str) or not description.strip():
            return None
        return cls(description=description.strip(),
                   amount=_as_amount(raw.get("amount")))


def _as_amount(value: Any) -> Optional[float]:
    """A number, or None where it could not be read.

    **A bool is refused before the numeric check**, because `bool` is a subclass
    of `int` in Python, so `True` would otherwise be stored as the amount 1.0.
    A string is parsed, because a model asked for a number sometimes answers
    with one in quotes, and refusing that would throw away a readable amount.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", "").replace("£", "")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def to_json(items: Optional[List[LineItem]]) -> Optional[str]:
    """The column value for a list of items, or None where there are none.

    **None rather than `"[]"`, so "no item lines" has one representation** in
    the column as it already has one in `ExtractionResult.line_items`. A reader
    that has to tell `[]` from `null` is a reader that will eventually get it
    wrong.
    """
    if not items:
        return None
    return json.dumps([item.as_dict() for item in items], ensure_ascii=False)


def from_json(value: Any) -> Optional[List[LineItem]]:
    """The items a stored column holds, or None.

    **Never raises.** This parses a column that an older database does not have
    at all and that a future writer might fill differently, and a categorisation
    must not fail because a line could not be read. Anything unusable reads as
    no item lines, which is the state every receipt written before 2026-09-12 is
    in anyway.
    """
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            value = json.loads(text)
        except ValueError:
            return None
    if not isinstance(value, list):
        return None
    items = [LineItem.from_dict(entry) for entry in value]
    return [item for item in items if item is not None][:MAX_LINE_ITEMS] or None


def for_prompt(items: Optional[List[LineItem]]) -> Optional[List[str]]:
    """The lines as the classifier is given them, one string each.

    **The stored shape and the prompt's wording are two things now**, and this
    is where they meet. The classifier only reads these, so it is given
    something that looks like the printed line it used to be given: the
    description, then the amount where one was read.

    Deliberately the same shape the prompt has always received, so this step
    changes WHERE the lines come from and not what the model is looking at. Part
    two of the same step makes the call deterministic, and two changes to one
    call at once would leave neither measurable.
    """
    if not items:
        return None
    rendered = []
    for item in items:
        if item.amount is None:
            rendered.append(item.description)
        else:
            rendered.append(f"{item.description} {item.amount:.2f}")
    return rendered or None

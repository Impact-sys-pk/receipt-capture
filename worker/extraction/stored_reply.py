"""Could `OpenAIVisionExtractor.extract()` use this stored reply? Flag H4.

Brief `PROMPT_claude_code_2026-11-14_three_flags.md`, part 1, and Paul's
decision of 2026-11-14: a receipt the extractor declined is not auto-retried,
"Not until it is reviewed". `_retry_failed_receipts()` in `app.py` asks this
about the latest extraction's `raw_response` before it re-sends a receipt.

**The parsing here is `extract()`'s, step for step**: strip; drop a leading
"```json", then a leading "```"; drop a trailing "```"; strip again; then
`json.loads()`. `worker/extraction/openai_vision.py` was not to be changed, so
the steps could not be moved into one shared function, and they are held in
step instead by `tests/test_declined_receipt_no_retry.py`'s
`TheTwoParsersAgreeTest`, which drives `extract()` itself over every reply
shape and compares.

**Usable means it parses to a JSON object.** A reply that parses to anything
else, `null`, a list or a bare string, makes `extract()` raise on its first
`parsed.get()`, so it is no more usable than one that does not parse at all.

**A null or empty reply is not usable.** Nor is a stored exception message,
which is what `app.py` writes in `raw_response` when an extraction raises:
Paul's decision of 2026-11-14 was to apply the rule literally rather than tell
the two apart by the wording of `validation_notes`.

**A declined document and a reply cut short look the same here**, and that was
accepted when the option was chosen.
"""

import json
from typing import Optional


def reply_is_usable(raw: Optional[str]) -> bool:
    if not isinstance(raw, str):
        return False
    text = raw.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    try:
        parsed = json.loads(text.strip())
    except json.JSONDecodeError:
        return False
    return isinstance(parsed, dict)

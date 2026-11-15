"""Transient-error retry wrapper for extraction.

Retries extraction when temporary failures occur (API timeouts, rate limits, network blips).
Separate from Part 1's version-gated retry, this operates within a single processing pass.
"""

import time
import logging
from pathlib import Path

from worker.extraction.base import ExtractionReplyError

logger = logging.getLogger(__name__)

#: HTTP statuses for a request the provider refused outright: bad request,
#: unauthorised, forbidden, not found, unprocessable. Asking again sends the same
#: request to the same refusal. **By status code rather than by class**, so this
#: module names no provider, and so it reads the same whatever a test has put in
#: `sys.modules["openai"]`: about forty test files replace that module with a
#: stub holding only `OpenAI`. The OpenAI SDK's status errors carry
#: `status_code`; `tests/test_retry_rule.py` checks that against the real
#: package in a subprocess.
#:
#: 408, 409, 429 and 5xx are deliberately absent: the SDK has already retried
#: them, `openai.DEFAULT_MAX_RETRIES` (2) times, before this helper sees them,
#: read in `openai/_base_client.py` `_should_retry()`; so are timeouts and
#: connection errors.
REFUSED_STATUS_CODES = frozenset({400, 401, 403, 404, 422})


def is_permanent(exc) -> bool:
    """True when a second identical attempt would meet the same answer."""
    return (isinstance(exc, ExtractionReplyError)
            or getattr(exc, "status_code", None) in REFUSED_STATUS_CODES)


def extract_with_transient_retry(extractor, file_path: Path, filename: str, max_retries: int = 3):
    """Extract with transient-error retry (exponential backoff).

    Catches API timeouts, rate limits, network blips within the same processing pass.
    ~~Only used if extraction raises an exception (not if it produces bad data).~~
    **Corrected 2026-11-15**, part 2 of
    `PROMPT_claude_code_2026-11-15_a_raised_extraction_must_not_vanish.md`. That
    sentence stopped being true when bad data became an exception: a reply the
    extractor cannot use now raises `ExtractionReplyError`.

    **The rule, `is_permanent()`.** A failure is NOT retried when a second
    identical attempt would meet it again: an `ExtractionReplyError` (the
    provider replied and the reply could not be used), or a request the
    provider refused outright, `REFUSED_STATUS_CODES`. Paul's photo of four
    receipts was sent three times for one list reply before this.
    **Not retrying a reply is a judgement about a non-deterministic reader**: a
    second call might read differently, and it costs a call to find out.

    **Everything else is retried as before**, including an exception nobody
    classified, because the cost of retrying something permanent is two calls
    and the cost of not retrying something transient is a lost receipt.

    **A failure that is not retried is still raised**, exactly as an exhausted
    one is, so the caller records and publishes it the same way.

    Args:
        extractor: BaseExtractor instance
        file_path: Path to receipt file
        filename: Original filename
        max_retries: Number of retry attempts (total attempts = max_retries)

    Returns:
        ExtractionResult

    Raises:
        Exception: If all retries are exhausted, or at once for a permanent error
    """
    for attempt in range(1, max_retries + 1):
        try:
            return extractor.extract(str(file_path), filename)
        except Exception as exc:
            if is_permanent(exc):
                logger.error(f"extraction failed and is not retried, a second attempt "
                             f"would meet the same answer: {type(exc).__name__}: {exc}")
                raise
            if attempt < max_retries:
                delay = 2 ** attempt  # 2s, 4s, 8s exponential backoff
                logger.info(f"extraction attempt {attempt} failed, retrying after {delay}s: {exc}")
                time.sleep(delay)
            else:
                # All retries exhausted
                logger.error(f"extraction failed after {max_retries} attempts: {exc}")
                raise

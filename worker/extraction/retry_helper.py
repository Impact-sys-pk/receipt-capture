"""Transient-error retry wrapper for extraction.

Retries extraction when temporary failures occur (API timeouts, rate limits, network blips).
Separate from Part 1's version-gated retry, this operates within a single processing pass.
"""

import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_with_transient_retry(extractor, file_path: Path, filename: str, max_retries: int = 3):
    """Extract with transient-error retry (exponential backoff).

    Catches API timeouts, rate limits, network blips within the same processing pass.
    Only used if extraction raises an exception (not if it produces bad data).

    Args:
        extractor: BaseExtractor instance
        file_path: Path to receipt file
        filename: Original filename
        max_retries: Number of retry attempts (total attempts = max_retries)

    Returns:
        ExtractionResult

    Raises:
        Exception: If all retries are exhausted
    """
    for attempt in range(1, max_retries + 1):
        try:
            return extractor.extract(str(file_path), filename)
        except Exception as exc:
            if attempt < max_retries:
                delay = 2 ** attempt  # 2s, 4s, 8s exponential backoff
                logger.info(f"extraction attempt {attempt} failed, retrying after {delay}s: {exc}")
                time.sleep(delay)
            else:
                # All retries exhausted
                logger.error(f"extraction failed after {max_retries} attempts: {exc}")
                raise

"""Extractor registry.

Design document 10.1. One place that knows which providers exist, so switching is
a config value rather than an edit to `app.py`, and so `extractor.name` is
available on failure paths that have no `ExtractionResult` to read `.engine` from.

Phase 1 has one provider. The registry earns its place by making the second one a
one-line change and by failing loudly when the configured engine is not one we
have, rather than quietly using OpenAI.
"""

import config

from .base import BaseExtractor
from .openai_vision import OpenAIVisionExtractor

_REGISTRY = {"openai_vision": OpenAIVisionExtractor}


def available_engines() -> list[str]:
    """The engine names that can be passed to get_extractor()."""
    return sorted(_REGISTRY)


def get_extractor(name: str | None = None) -> BaseExtractor:
    """Build the named extractor, or the configured default when name is None.

    Raises ValueError naming the unrecognised engine and the ones that do exist.
    Deliberately not a fallback to OpenAI: a provider switch that appears to work
    while nothing changed is the failure this registry exists to prevent, and it
    would be invisible in the extraction rows because they would carry the
    OpenAI engine string and be correct.
    """
    engine_name = name if name is not None else config.EXTRACTION_ENGINE
    extractor_class = _REGISTRY.get(engine_name)
    if extractor_class is None:
        source = "requested engine" if name is not None else "config.EXTRACTION_ENGINE"
        raise ValueError(
            f"unknown extraction engine from {source}: {engine_name!r}. "
            f"Available: {', '.join(available_engines())}"
        )
    return extractor_class()

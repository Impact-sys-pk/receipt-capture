"""Design document 10.1: the provider factory.

The point of a registry is that switching provider is one config value rather
than an edit to app.py. So the tests prove the registry is the mechanism, not
decoration: a stub registered into it must come back out.

A config value naming an engine that is not registered must fail loudly. A silent
fallback to OpenAI would mean a provider switch appearing to work while nothing
changed, which is the failure this whole step exists to prevent.
"""

import sys
import types
import unittest
from unittest.mock import patch

import config

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

from worker.extraction import factory
from worker.extraction.base import BaseExtractor, ExtractionResult
from worker.extraction.factory import available_engines, get_extractor
from worker.extraction.openai_vision import OpenAIVisionExtractor


class StubExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "stub_engine"

    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        raise AssertionError("not called")


class GetExtractorTest(unittest.TestCase):
    def test_default_is_the_openai_vision_extractor(self):
        extractor = get_extractor()
        self.assertIsInstance(extractor, OpenAIVisionExtractor)
        self.assertEqual(extractor.name, "openai_vision")

    def test_named_engine_is_returned(self):
        extractor = get_extractor("openai_vision")
        self.assertIsInstance(extractor, OpenAIVisionExtractor)

    def test_a_registered_stub_comes_back_by_name(self):
        # Proves the registry is the mechanism. If get_extractor() ignored it and
        # constructed OpenAIVisionExtractor directly, this would fail.
        with patch.dict(factory._REGISTRY, {"stub_engine": StubExtractor}):
            extractor = get_extractor("stub_engine")
        self.assertIsInstance(extractor, StubExtractor)
        self.assertEqual(extractor.name, "stub_engine")

    def test_the_configured_default_is_honoured(self):
        with patch.dict(factory._REGISTRY, {"stub_engine": StubExtractor}), \
             patch.object(config, "EXTRACTION_ENGINE", "stub_engine"):
            self.assertIsInstance(get_extractor(), StubExtractor)

    def test_unknown_name_names_both_the_bad_value_and_the_options(self):
        with self.assertRaises(ValueError) as caught:
            get_extractor("mistral_vision")
        message = str(caught.exception)
        self.assertIn("mistral_vision", message)
        self.assertIn("openai_vision", message)

    def test_a_configured_engine_that_is_not_registered_fails_loudly(self):
        # A silent fallback here would mean a provider switch that appears to
        # work while nothing changed.
        with patch.object(config, "EXTRACTION_ENGINE", "not_a_real_engine"):
            with self.assertRaises(ValueError) as caught:
                get_extractor()
        self.assertIn("not_a_real_engine", str(caught.exception))

    def test_every_registered_engine_declares_the_name_it_is_registered_under(self):
        for name in available_engines():
            with self.subTest(engine=name):
                self.assertEqual(get_extractor(name).name, name)


class AvailableEnginesTest(unittest.TestCase):
    def test_lists_the_registry_keys(self):
        self.assertEqual(available_engines(), ["openai_vision"])

    def test_reflects_a_registered_stub(self):
        with patch.dict(factory._REGISTRY, {"stub_engine": StubExtractor}):
            self.assertIn("stub_engine", available_engines())
        self.assertNotIn("stub_engine", available_engines())


if __name__ == "__main__":
    unittest.main()

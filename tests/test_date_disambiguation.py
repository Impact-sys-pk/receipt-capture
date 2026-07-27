import os
import tempfile
import json
import unittest
import sys
import types
from types import SimpleNamespace

# Inject a fake `openai` module so tests don't require the real dependency
fake_openai = types.ModuleType("openai")
class FakeOpenAIClient:
    def __init__(self, api_key=None):
        pass
fake_openai.OpenAI = FakeOpenAIClient
sys.modules['openai'] = fake_openai

from worker.extraction.openai_vision import OpenAIVisionExtractor
import config

class FakeResponse:
    def __init__(self, content):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]

class DateDisambiguationTest(unittest.TestCase):
    def setUp(self):
        # Ensure we prefer day-first for this test
        self._original_prefer_dayfirst = config.PREFER_DAYFIRST
        config.PREFER_DAYFIRST = True
        # Create a temporary dummy jpg file
        fd, path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)
        with open(path, 'wb') as f:
            f.write(b'\xff\xd8\xff')
        self.path = path

    def tearDown(self):
        config.PREFER_DAYFIRST = self._original_prefer_dayfirst
        try:
            os.remove(self.path)
        except Exception:
            pass

    def test_parse_raw_090526_as_dayfirst(self):
        extractor = OpenAIVisionExtractor()
        # Mock the client's response
        content = json.dumps({
            "supplier_name": None,
            "invoice_date": None,
            "invoice_date_raw": "09/05/26",
            "net_amount": None,
            "vat_amount": None,
            "gross_amount": None,
            "details": None,
            "currency": "GBP"
        })
        extractor._client = SimpleNamespace(**{"chat": SimpleNamespace(**{"completions": SimpleNamespace(**{"create": lambda **kwargs: FakeResponse(content)})})})

        res = extractor.extract(self.path, os.path.basename(self.path))
        # Expect day-first -> 2026-05-09
        self.assertEqual(res.invoice_date, "2026-05-09")

    def test_ambiguous_iso_without_raw_is_not_swapped_but_flagged(self):
        extractor = OpenAIVisionExtractor()
        # Model returns an ISO date that could be ambiguous (09/05/2026) but no raw string
        content = json.dumps({
            "supplier_name": None,
            "invoice_date": "2026-09-05",
            "invoice_date_raw": None,
            "net_amount": None,
            "vat_amount": None,
            "gross_amount": None,
            "details": None,
            "currency": "GBP"
        })
        extractor._client = SimpleNamespace(**{"chat": SimpleNamespace(**{"completions": SimpleNamespace(**{"create": lambda **kwargs: FakeResponse(content)})})})

        res = extractor.extract(self.path, os.path.basename(self.path))
        # Should NOT swap to 2026-05-09; should remain the model ISO but details should flag ambiguity
        self.assertEqual(res.invoice_date, "2026-09-05")
        self.assertIn('ambiguous_invoice_date_no_raw', res.details)

if __name__ == '__main__':
    unittest.main()

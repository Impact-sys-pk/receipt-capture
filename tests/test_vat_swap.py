import os
import tempfile
import json
import unittest
import sys
import types
from types import SimpleNamespace

# Mock openai module
fake_openai = types.ModuleType("openai")
class FakeOpenAIClient:
    def __init__(self, api_key=None):
        pass
fake_openai.OpenAI = FakeOpenAIClient
sys.modules['openai'] = fake_openai

from worker.extraction.openai_vision import OpenAIVisionExtractor
import config

class VatSwapTest(unittest.TestCase):
    def setUp(self):
        self._original_prefer_dayfirst = config.PREFER_DAYFIRST
        config.PREFER_DAYFIRST = True
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

    def test_positive_swap_net_as_gross(self):
        extractor = OpenAIVisionExtractor()
        # The model returns net=8.0, vat=1.33, gross=null -> treat net as gross
        content = json.dumps({
            "supplier_name": null_converter(None),
            "invoice_date": None,
            "invoice_date_raw": None,
            "net_amount": 8.0,
            "vat_amount": 1.33,
            "gross_amount": None,
            "details": None,
            "currency": "GBP"
        })
        extractor._client = SimpleNamespace(**{"chat": SimpleNamespace(**{"completions": SimpleNamespace(**{"create": lambda **kwargs: SimpleResponse(content)})})})
        res = extractor.extract(self.path, os.path.basename(self.path))
        # After swap: gross should be 8.0 and net should be 6.67 (rounded)
        self.assertAlmostEqual(res.gross_amount, 8.00)
        self.assertAlmostEqual(res.net_amount, 6.67, places=2)
        self.assertIn('treated_amount_as_gross', res.details)

    def test_negative_no_swap_real_net(self):
        extractor = OpenAIVisionExtractor()
        # Genuine net-first receipt: net=100, vat=20, gross=None -> should not swap
        content = json.dumps({
            "supplier_name": null_converter(None),
            "invoice_date": None,
            "invoice_date_raw": None,
            "net_amount": 100.0,
            "vat_amount": 20.0,
            "gross_amount": None,
            "details": None,
            "currency": "GBP"
        })
        extractor._client = SimpleNamespace(**{"chat": SimpleNamespace(**{"completions": SimpleNamespace(**{"create": lambda **kwargs: SimpleResponse(content)})})})
        res = extractor.extract(self.path, os.path.basename(self.path))
        # Should not perform the gross-as-net correction
        self.assertNotIn('treated_amount_as_gross', res.details or '')
        # net should remain 100.0
        self.assertAlmostEqual(res.net_amount, 100.0)

# Helpers used to mock responses where json.dumps of None would produce null
class SimpleResponse:
    def __init__(self, content):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]

# Workaround to produce JSON with null values easily
def null_converter(x):
    return x

if __name__ == '__main__':
    unittest.main()

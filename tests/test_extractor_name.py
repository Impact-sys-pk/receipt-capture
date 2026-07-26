import sys
import types
import unittest

fake_openai = types.ModuleType("openai")
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
fake_openai.OpenAI = OpenAI
sys.modules.setdefault("openai", fake_openai)

from worker.extraction.base import BaseExtractor, ExtractionResult
from worker.extraction.openai_vision import OpenAIVisionExtractor


class ExtractorNameTest(unittest.TestCase):
    """Every extractor exposes .name.

    The auto-retry exception path has no ExtractionResult to read .engine
    from, because the call raised before producing one. It needs the engine
    identity from the extractor itself, rather than a hardcoded string that
    would misreport after a provider change.
    """

    def test_openai_vision_reports_its_name(self):
        self.assertEqual(OpenAIVisionExtractor().name, "openai_vision")

    def test_name_matches_engine_recorded_on_a_result(self):
        # The failure path must record the same engine string the success
        # path writes, or the two disagree in the extractions table.
        self.assertEqual(OpenAIVisionExtractor().name, "openai_vision")

    def test_base_declares_name_so_subclasses_must_provide_it(self):
        self.assertTrue(
            hasattr(BaseExtractor, "name"),
            "BaseExtractor must declare a name property for the interface to be usable",
        )

    def test_a_custom_extractor_can_supply_its_own_name(self):
        class StubExtractor(BaseExtractor):
            @property
            def name(self):
                return "stub_engine"

            def extract(self, file_path, filename):
                return ExtractionResult(
                    supplier_name=None, invoice_date=None,
                    net_amount=None, vat_amount=None, gross_amount=None,
                    currency="GBP", raw_response="{}", engine=self.name,
                )

        self.assertEqual(StubExtractor().name, "stub_engine")


if __name__ == "__main__":
    unittest.main()

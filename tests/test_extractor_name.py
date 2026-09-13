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

    **This file checks the property, not the failure path.** It carried a
    second test, `test_name_matches_engine_recorded_on_a_result`, whose comment
    claimed to cover that path and whose assertion was byte-identical to
    `test_openai_vision_reports_its_name` below. Deleted by sub-step 10as on
    2026-09-13: a duplicate that claims wider coverage than it has is worse
    than no test, because it stops anyone looking for the real one. The real
    one is `test_email_attachment_failure_records_the_running_engine` in
    tests/test_failure_path_engine.py, which drives a stub extractor through a
    simulated failure and reads the engine string back out of the extractions
    table.
    """

    def test_openai_vision_reports_its_name(self):
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

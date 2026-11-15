from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from worker.line_items import LineItem


@dataclass
class ExtractionResult:
    supplier_name: Optional[str]
    invoice_date: Optional[str]
    net_amount: Optional[float]
    vat_amount: Optional[float]
    gross_amount: Optional[float]
    currency: str
    raw_response: str
    engine: str
    details: Optional[str] = None
    receipt_ref_number: Optional[str] = None  # Transaction/ticket/reference number on receipt
    receipt_time: Optional[str] = None  # Time of day (HH:MM format) shown on receipt
    line_items: Optional[List[LineItem]] = None
    """The item lines off the receipt, or None where there are none.

    Added 2026-09-05. It exists so layer 5 can read what was bought rather than
    guessing from the supplier: "Asda Wallington" alone was categorised as
    stationery.

    **A list of `LineItem`, description and amount separate, from 2026-09-12.
    Step 10p part one, amendment 340.** ~~a list of strings, description and
    amount run together~~ Strings were enough for the classifier, which only
    reads them, and useless for 18.4's split, which needs an amount per line as
    a number.

    ~~It is carried in memory and NOT stored: there is no column on
    `extractions` and nothing goes into the sidecar or to IntelliBooks, so it
    reaches layer 5 only on the live pipeline path, where the extraction object
    is still in hand. The two call sites that read an extraction back out of the
    database cannot supply it and pass None.~~ **Struck 2026-09-12: it IS stored
    now**, on `extractions.line_items` as JSON, so every path that re-runs the
    engine reads the same lines the first read saw. That paragraph was the
    defect step 10p exists to fix, and it is kept because it describes what was
    wrong.

    **Nothing is backfilled.** Paul's instruction: the receipts already in the
    database never had their lines captured and they cannot be recovered.
    """


class ExtractionReplyError(Exception):
    """A reply came back from the provider and could not be used. 2026-11-15.

    Brief `PROMPT_claude_code_2026-11-15_a_raised_extraction_must_not_vanish.md`.
    Raised by an extractor for any failure AFTER it holds the provider's reply,
    so the caller can store what the model actually said. Until this existed a
    raise left only `str(exc)` in `extractions.raw_response`, and Paul's live
    test of a photo of four receipts lost the reply that explained it.

    `raw_response` is the reply exactly as received. `note` is optional: what
    the operator reads on the receipt when the failure has a better name than
    the exception's message. Absent, callers say `extraction error: <message>`.
    """

    def __init__(self, message, raw_response, note=None):
        super().__init__(message)
        self.raw_response = raw_response
        self.note = note


class BaseExtractor(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Engine identity, e.g. "openai_vision".

        Needed on failure paths, which have no ExtractionResult to read
        .engine from because the call raised before producing one. Reading it
        from the extractor keeps the recorded engine correct after a provider
        change, where a hardcoded string would silently misreport.
        """

    @abstractmethod
    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        pass

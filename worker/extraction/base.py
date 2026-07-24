from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


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


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        pass

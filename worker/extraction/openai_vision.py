import base64
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from openai import OpenAI

import config
from worker import vat_rates
from .base import BaseExtractor, ExtractionResult
from .postprocess import establish_gross_from_vat, resolve_invoice_date

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a receipt data extractor. Extract the following fields and return JSON only, no other text:
{
    "supplier_name": "string or null",
    "invoice_date": "YYYY-MM-DD or null",
    "invoice_date_raw": "original matched string (e.g. 09/05/26) or null",
    "net_amount": number or null,
    "vat_amount": number or null,
    "gross_amount": number or null,
    "receipt_ref_number": "string or null (a visible transaction, ticket, or reference number on the receipt)",
    "receipt_time": "string or null (HH:MM time of day shown on the receipt, if any, 24-hour format)",
    "details": "string or null",
    "line_items": ["array of strings, one per item line as it appears on the receipt, or null"],
    "currency": "GBP"
}
For amounts use numbers only, no currency symbols. Use null for any field that cannot be determined.
For line_items, copy each item line as printed, keeping its description and its amount on one string, for example "MILK SEMI SKIMMED 2L 1.45". Do not include subtotal, VAT, total, change or payment lines. Where the document has no itemised lines, use null. List at most 40 lines; if there are more, list the first 40."""

_IMAGE_MIME = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png", ".gif": "image/gif",
    ".webp": "image/webp", ".bmp": "image/bmp",
    ".tiff": "image/tiff",
}


def _normalise_line_items(value) -> Optional[List[str]]:
    """Whatever the model returned for line_items, as a list of strings or None.

    The prompt asks for an array of strings and a model will sometimes answer
    with a list of objects, or with one newline-separated string, or with an
    empty list. Normalising here rather than at the reader keeps the shape
    promised by `ExtractionResult.line_items` true for every caller, and keeps
    provider-shaped parsing inside the provider's own module. An empty result
    is None rather than [], so "no item lines" has one representation.
    """
    if value is None:
        return None
    if isinstance(value, str):
        items = [line.strip() for line in value.splitlines()]
    elif isinstance(value, list):
        items = []
        for entry in value:
            if isinstance(entry, dict):
                # e.g. {"description": "MILK 2L", "amount": 1.45}
                items.append(" ".join(str(v) for v in entry.values() if v is not None).strip())
            else:
                items.append(str(entry).strip())
    else:
        return None
    items = [i for i in items if i]
    return items or None


def _image_to_base64(path: Path) -> Tuple[str, str]:
    mime = _IMAGE_MIME.get(path.suffix.lower(), "image/jpeg")
    return base64.standard_b64encode(path.read_bytes()).decode(), mime


def _pdf_first_page_to_base64(path: Path) -> Tuple[str, str]:
    import fitz
    doc = fitz.open(str(path))
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
    data = base64.standard_b64encode(pix.tobytes("jpeg")).decode()
    doc.close()
    return data, "image/jpeg"


class OpenAIVisionExtractor(BaseExtractor):
    def __init__(self):
        self._client = OpenAI(api_key=config.OPENAI_API_KEY)
        self._model = config.OPENAI_MODEL

    @property
    def name(self) -> str:
        return "openai_vision"

    def extract(self, file_path: str, filename: str) -> ExtractionResult:
        path = Path(file_path)

        if path.suffix.lower() == ".pdf":
            image_data, mime = _pdf_first_page_to_base64(path)
        else:
            image_data, mime = _image_to_base64(path)

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{image_data}"},
                        }
                    ],
                },
            ],
            # Raised from 500 on 2026-09-05, when line_items was added to the
            # prompt above. 500 fitted the nine scalar fields with room to spare
            # and does not fit them plus up to 40 item lines: a supermarket
            # receipt would have been truncated mid-JSON, json.loads() would
            # have raised, and `parsed` would have fallen back to {}, so EVERY
            # field would have come back null and the receipt would have failed
            # validation. That is a regression this change would have caused, so
            # the ceiling moves with it. It is a ceiling and not a spend: the
            # reply is billed at the tokens actually generated, and a receipt
            # with no item lines costs what it did before.
            max_tokens=1500,
        )

        raw = response.choices[0].message.content

        try:
            # Strip markdown code block wrapper if present
            text = raw.strip()
            if text.startswith("```json"):
                text = text[7:]  # Remove ```json
            if text.startswith("```"):
                text = text[3:]  # Remove ```
            if text.endswith("```"):
                text = text[:-3]  # Remove trailing ```
            parsed = json.loads(text.strip())
        except json.JSONDecodeError:
            logger.warning(f"Non-JSON response for {filename}: {raw}")
            parsed = {}
        # Post-process extraction for common patterns, e.g. VAT-inclusive totals
        net = parsed.get("net_amount")
        vat = parsed.get("vat_amount")
        gross = parsed.get("gross_amount")
        details = parsed.get("details")
        invoice_date = parsed.get("invoice_date")
        invoice_date_raw = parsed.get("invoice_date_raw")

        # Post-processing is provider-independent and lives in postprocess.py, so
        # a second provider inherits it rather than silently losing it.
        # config.PREFER_DAYFIRST is read here, at call time, as it was before, and
        # so are the rates: vat_rates.impliable_rates() reads the table
        # IntelliCharts publishes into CHARTS_DIR, item 163.
        net, vat, gross, details = establish_gross_from_vat(
            net, vat, gross, details,
            vat_rates.impliable_rates(), config.VAT_RATE_ROUNDING_ALLOWANCE,
        )
        invoice_date, details = resolve_invoice_date(
            invoice_date, invoice_date_raw, details, config.PREFER_DAYFIRST
        )

        return ExtractionResult(
            supplier_name=parsed.get("supplier_name"),
            invoice_date=invoice_date or parsed.get("invoice_date"),
            net_amount=net,
            vat_amount=vat,
            gross_amount=gross,
            details=details,
            currency=parsed.get("currency", config.DEFAULT_CURRENCY),
            raw_response=raw,
            engine="openai_vision",
            receipt_ref_number=parsed.get("receipt_ref_number"),
            receipt_time=parsed.get("receipt_time"),
            line_items=_normalise_line_items(parsed.get("line_items")),
        )

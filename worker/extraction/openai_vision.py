import base64
import json
import logging
from datetime import date
from pathlib import Path
from typing import Tuple

from openai import OpenAI

import config
from .base import BaseExtractor, ExtractionResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a receipt data extractor. Extract the following fields and return JSON only, no other text:
{
    "supplier_name": "string or null",
    "invoice_date": "YYYY-MM-DD or null",
    "invoice_date_raw": "original matched string (e.g. 09/05/26) or null",
    "net_amount": number or null,
    "vat_amount": number or null,
    "gross_amount": number or null,
    "details": "string or null",
    "currency": "GBP"
}
For amounts use numbers only, no currency symbols. Use null for any field that cannot be determined."""

_IMAGE_MIME = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png", ".gif": "image/gif",
    ".webp": "image/webp", ".bmp": "image/bmp",
    ".tiff": "image/tiff",
}


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
            max_tokens=500,
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

        def _parse_ambiguous_date(raw: str):
            # Handle numeric dates like 09/05/26 or 9-5-2026
            import re

            if not raw or not isinstance(raw, str):
                return None
            parts = re.split(r"[^0-9]+", raw)
            parts = [p for p in parts if p]
            if len(parts) != 3:
                return None
            try:
                a, b, c = [int(p) for p in parts]
            except Exception:
                return None
            # Normalize year
            if c < 100:
                year = 2000 + c
            elif c < 1000:
                # unlikely, treat as 2000s
                year = 2000 + c
            else:
                year = c

            # If both day and month <= 12 then ambiguous
            if a <= 12 and b <= 12:
                if config.PREFER_DAYFIRST:
                    day, month = a, b
                else:
                    day, month = b, a
            else:
                # Unambiguous: whichever <= 31 but >12 is day
                if a > 12 and a <= 31:
                    day = a; month = b
                elif b > 12 and b <= 31:
                    day = b; month = a
                else:
                    return None
            try:
                return date(year, month, day).isoformat()
            except Exception:
                return None

        try:
            if gross is None and net is not None and vat is not None:
                # numeric coercion
                n = float(net)
                v = float(vat)
                implied_rate_net = None
                implied_rate_gross = None
                if n > 0:
                    implied_rate_net = v / n
                if (n - v) > 0:
                    implied_rate_gross = v / (n - v)

                # Common VAT rates to check against (20%, 5%)
                common_rates = [0.2, 0.05]
                # Tolerances
                rate_tol = 0.03

                match_gross_rate = any(abs(implied_rate_gross - r) <= rate_tol for r in common_rates) if implied_rate_gross is not None else False
                match_net_rate = any(abs(implied_rate_net - r) <= rate_tol for r in common_rates) if implied_rate_net is not None else False

                # If treating the extracted `net` as gross makes the implied rate match common VAT rates
                # while treating it as net does not, then swap: treat net as gross
                if match_gross_rate and not match_net_rate:
                    gross = round(n, 2)
                    net = round(gross - v, 2)
                    # annotate details to record the automatic correction
                    note = f"auto_treated_amount_as_gross(implied_rate={implied_rate_gross:.3f})"
                    if details:
                        details = f"{details}; {note}"
                    else:
                        details = note
        except Exception:
            # If any numeric coercion fails, leave values unchanged
            pass

        # If the model returned the original matched date string, prefer parsing it deterministically
        # using local `PREFER_DAYFIRST` rules. Fall back to previously implemented ISO-based enforcement.
        try:
            parsed_from_raw = None
            if invoice_date_raw:
                parsed_from_raw = _parse_ambiguous_date(invoice_date_raw)
                if parsed_from_raw:
                    note = f"auto_parsed_invoice_date_from_raw(raw={invoice_date_raw} -> {parsed_from_raw})"
                    if details:
                        details = f"{details}; {note}"
                    else:
                        details = note
                    invoice_date = parsed_from_raw

            # If we do not have a raw string, do NOT guess by swapping ISO month/day because
            # that is effectively a coin flip and can corrupt correct model outputs. Instead,
            # if the model returned an ambiguous ISO date (both day and month <= 12), annotate
            # the extraction `details` to flag ambiguity so reviewers or downstream logic can
            # decide (or we can apply client-specific rules later).
            if not parsed_from_raw and invoice_date:
                try:
                    d = date.fromisoformat(invoice_date)
                    if d.day <= 12 and d.month <= 12:
                        note = f"ambiguous_invoice_date_no_raw(model_iso={invoice_date})"
                        if details:
                            details = f"{details}; {note}"
                        else:
                            details = note
                        # leave invoice_date unchanged
                except Exception:
                    pass
        except Exception:
            pass

        return ExtractionResult(
            supplier_name=parsed.get("supplier_name"),
            invoice_date=invoice_date or parsed.get("invoice_date"),
            net_amount=net,
            vat_amount=vat,
            gross_amount=gross,
            details=details,
            currency=parsed.get("currency", "GBP"),
            raw_response=raw,
            engine="openai_vision",
        )

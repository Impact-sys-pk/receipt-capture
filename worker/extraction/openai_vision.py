import base64
import json
import logging
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
  "net_amount": number or null,
  "vat_amount": number or null,
  "gross_amount": number or null,
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

        return ExtractionResult(
            supplier_name=parsed.get("supplier_name"),
            invoice_date=parsed.get("invoice_date"),
            net_amount=parsed.get("net_amount"),
            vat_amount=parsed.get("vat_amount"),
            gross_amount=parsed.get("gross_amount"),
            currency=parsed.get("currency", "GBP"),
            raw_response=raw,
            engine="openai_vision",
        )

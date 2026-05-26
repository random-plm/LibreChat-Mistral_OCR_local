from __future__ import annotations

from typing import Any

import fitz
import pytesseract
from PIL import Image

from ..config import TESSERACT_LANG


def ocr_pdf_page_tesseract(page: fitz.Page) -> dict[str, Any]:
    pix = page.get_pixmap(dpi=200)
    mode = "RGB" if pix.alpha == 0 else "RGBA"
    image = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(image, lang=TESSERACT_LANG).strip()
    return {
        "index": page.number,
        "markdown": text,
        "images": [],
        "dimensions": {
            "dpi": 72,
            "height": int(page.rect.height),
            "width": int(page.rect.width),
        },
    }

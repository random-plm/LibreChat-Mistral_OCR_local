from __future__ import annotations

import logging
import tempfile
from typing import Any

import fitz
import pytesseract
from PIL import Image

from ..config import TESSERACT_LANG

logger = logging.getLogger(__name__)


def ocr_pdf_page_tesseract(page: fitz.Page) -> dict[str, Any]:
    logger.debug("page %s: tesseract", page.number)
    pix = page.get_pixmap(dpi=200)
    mode = "RGB" if pix.alpha == 0 else "RGBA"
    image = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    page_prefix = f"{page.number}_"
    with tempfile.NamedTemporaryFile(
        mode="wb", suffix=".png", prefix=page_prefix, dir="/tmp", delete=False
    ) as tmp_file:
        image.save(tmp_file.name, format="PNG")
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

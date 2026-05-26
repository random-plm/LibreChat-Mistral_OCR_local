from __future__ import annotations

from pathlib import Path
from typing import Any

import pytesseract
from PIL import Image

from ..config import TESSERACT_LANG


def ocr_image(image_path: Path) -> list[dict[str, Any]]:
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang=TESSERACT_LANG).strip()
    return [
        {
            "index": 0,
            "markdown": text,
            "images": [],
            "dimensions": {
                "dpi": 72,
                "height": int(image.height),
                "width": int(image.width),
            },
        }
    ]

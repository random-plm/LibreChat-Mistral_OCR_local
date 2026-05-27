from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import fitz

from ..clients.client import OCRClient


def ocr_pdf_page_ocr_remote(page: fitz.Page, ocr_client: OCRClient) -> dict[str, Any]:
    pix = page.get_pixmap(dpi=200)
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".png", dir="/tmp", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(pix.tobytes("png"))

    try:
        text = ocr_client.infer(str(tmp_path)).strip()
    finally:
        tmp_path.unlink(missing_ok=True)
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

from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi import HTTPException

from ..config import OCR_TEXT_THRESHOLD, TESSERACT_LANG
from .digital_pdf import pdf_page_texts


def ocr_pdf_if_needed(src_pdf: Path, workdir: Path) -> Path:
    page_texts = pdf_page_texts(src_pdf)
    if all(len(t) >= OCR_TEXT_THRESHOLD for t in page_texts):
        return src_pdf

    out_pdf = workdir / "ocr_output.pdf"
    cmd = [
        "ocrmypdf",
        "--force-ocr",
        "--optimize",
        "0",
        "-l",
        TESSERACT_LANG,
        str(src_pdf),
        str(out_pdf),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCRmyPDF failed: {e.stderr.decode('utf-8', errors='ignore')[:800]}",
        )

    return out_pdf

from __future__ import annotations

from pathlib import Path

import fitz

from ..config import OCR_ROUTER_MIN_TEXT_THRESHOLD
from .domain import OCRPageJob, PageUnit

PDF_SUFFIXES = {".pdf"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


class BackendRouter:
    def route_document(self, input_path: Path) -> str:
        suffix = input_path.suffix.lower()
        if suffix in PDF_SUFFIXES:
            return "pdf_pipeline"
        if suffix in IMAGE_SUFFIXES:
            return "image_pipeline"
        return "unsupported"

    def select_page_backend(self, page: fitz.Page) -> str:
        image_count = len(page.get_images(full=True))
        text = page.get_text("text").strip()
        text_len = len(text)

        if image_count > 0 and text_len < OCR_ROUTER_MIN_TEXT_THRESHOLD:
            return "tesseract_pdf_page"
        if text_len >= OCR_ROUTER_MIN_TEXT_THRESHOLD:
            return "digital_pdf"
        return "tesseract_pdf_page"

    def route_page(self, document_id: str, page_unit: PageUnit) -> OCRPageJob:
        return OCRPageJob(document_id=document_id, page_unit=page_unit)

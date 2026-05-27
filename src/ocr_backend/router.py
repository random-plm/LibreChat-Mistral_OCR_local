from __future__ import annotations

import logging
from pathlib import Path

import fitz

from ..config import (
    OCR_ROUTER_MAX_DIGITAL_IMAGE_COVERAGE,
    OCR_ROUTER_MAX_TESSERACT_IMAGE_COUNT,
    OCR_ROUTER_MAX_TESSERACT_IMAGE_COVERAGE,
    OCR_ROUTER_MIN_PRINTABLE_RATIO,
    OCR_ROUTER_MIN_TEXT_THRESHOLD,
)
from .domain import OCRPageJob, PageUnit

PDF_SUFFIXES = {".pdf"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
logger = logging.getLogger(__name__)


class BackendRouter:
    def _debug_log(
        self,
        page: fitz.Page,
        text_len: int,
        printable_ratio: float,
        image_coverage: float,
        image_count: int,
        backend: str,
    ) -> None:
        logger.debug(
            "router page={page} backend={backend} text_len={text_len} printable_ratio={printable_ratio:.3f} "
            "image_coverage={image_coverage:.3f} image_count={image_count}".format(
                page=page.number,
                backend=backend,
                text_len=text_len,
                printable_ratio=printable_ratio,
                image_coverage=image_coverage,
                image_count=image_count,
            )
        )

    def _printable_ratio(self, text: str) -> float:
        if not text:
            return 0.0
        printable = sum(1 for c in text if c.isprintable() and not c.isspace())
        non_space = sum(1 for c in text if not c.isspace())
        if non_space == 0:
            return 0.0
        return printable / non_space

    def _image_coverage_and_count(self, page: fitz.Page) -> tuple[float, int]:
        page_area = float(max(page.rect.width * page.rect.height, 1))
        image_area = 0.0
        image_count = 0
        for image_info in page.get_images(full=True):
            xref = image_info[0]
            rects = page.get_image_rects(xref)
            image_count += len(rects)
            for rect in rects:
                image_area += max(0.0, rect.width * rect.height)
        return min(1.0, image_area / page_area), image_count

    def route_document(self, input_path: Path) -> str:
        suffix = input_path.suffix.lower()
        if suffix in PDF_SUFFIXES:
            return "pdf_pipeline"
        if suffix in IMAGE_SUFFIXES:
            return "image_pipeline"
        return "unsupported"

    def select_page_backend(self, page: fitz.Page) -> str:
        text = page.get_text("text").strip()
        text_len = len(text)
        printable_ratio = self._printable_ratio(text)
        image_coverage, image_count = self._image_coverage_and_count(page)

        if (
            text_len >= OCR_ROUTER_MIN_TEXT_THRESHOLD
            and printable_ratio >= OCR_ROUTER_MIN_PRINTABLE_RATIO
            and image_coverage <= OCR_ROUTER_MAX_DIGITAL_IMAGE_COVERAGE
        ):
            self._debug_log(
                page=page,
                text_len=text_len,
                printable_ratio=printable_ratio,
                image_coverage=image_coverage,
                image_count=image_count,
                backend="digital_pdf",
            )
            return "digital_pdf"

        if (
            image_coverage <= OCR_ROUTER_MAX_TESSERACT_IMAGE_COVERAGE
            and image_count <= OCR_ROUTER_MAX_TESSERACT_IMAGE_COUNT
        ):
            self._debug_log(
                page=page,
                text_len=text_len,
                printable_ratio=printable_ratio,
                image_coverage=image_coverage,
                image_count=image_count,
                backend="tesseract_pdf_page",
            )
            return "tesseract_pdf_page"

        self._debug_log(
            page=page,
            text_len=text_len,
            printable_ratio=printable_ratio,
            image_coverage=image_coverage,
            image_count=image_count,
            backend="ocr_client_pdf_remote",
        )
        return "ocr_client_pdf_remote"

    def route_page(self, document_id: str, page_unit: PageUnit) -> OCRPageJob:
        return OCRPageJob(document_id=document_id, page_unit=page_unit)

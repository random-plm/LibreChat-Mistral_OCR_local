from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any

from ..config import OCR_QUALITY_MIN_LENGTH, OCR_QUALITY_MIN_SCORE, OCR_WORKER_POOL_SIZE
from ..clients.client import OCRClient
from .digital_pdf import extract_pdf_page_digital
from .domain import DocumentTracker, OCRPageJob, PageResult
from .pdf_page_ocr_remote import ocr_pdf_page_ocr_remote
from .pdf_page_tesseract import ocr_pdf_page_tesseract

logger = logging.getLogger(__name__)


class OCRWorkerPool:
    def __init__(self, tracker: DocumentTracker, ocr_client: OCRClient | None = None) -> None:
        self.tracker = tracker
        self.ocr_client = ocr_client
        self.queue: asyncio.Queue[OCRPageJob] = asyncio.Queue()
        self.workers: list[asyncio.Task[Any]] = []

    async def __aenter__(self) -> "OCRWorkerPool":
        for _ in range(max(1, OCR_WORKER_POOL_SIZE)):
            self.workers.append(asyncio.create_task(self._worker()))
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)

    async def submit(self, job: OCRPageJob) -> None:
        await self.queue.put(job)

    async def _worker(self) -> None:
        while True:
            job = await self.queue.get()
            try:
                payload = await self._run_with_escalation(job)
                self.tracker.mark_done(PageResult(page_index=job.page_unit.page_index, payload=payload))
            except Exception as exc:
                logger.debug(
                    f"worker page={job.page_unit.page_index} backend={job.page_unit.backend} "
                    f"status=error error={exc!r}"
                )
                raise
            finally:
                self.queue.task_done()

    def _next_backend(self, backend: str) -> str | None:
        order = ["digital_pdf", "tesseract_pdf_page", "ocr_client_pdf_remote"]
        if backend not in order:
            return None
        idx = order.index(backend)
        if idx + 1 >= len(order):
            return None
        return order[idx + 1]

    def _quality_score(self, markdown: str) -> float:
        text = (markdown or "").strip()
        if not text:
            return 0.0
        non_space = "".join(ch for ch in text if not ch.isspace())
        if not non_space:
            return 0.0
        length_score = min(1.0, len(text) / max(1, OCR_QUALITY_MIN_LENGTH))
        alnum_ratio = sum(1 for ch in non_space if ch.isalnum()) / len(non_space)
        words = re.findall(r"\w+", text.lower())
        diversity = (len(set(words)) / len(words)) if words else 0.0
        suspicious = 0.0
        if "quick brown fox jumps over the lazy dog" in text.lower():
            suspicious = 1.0
        score = (0.45 * length_score) + (0.35 * alnum_ratio) + (0.20 * diversity) - (0.60 * suspicious)
        return max(0.0, min(1.0, score))

    async def _run_backend(self, backend: str, job: OCRPageJob) -> dict[str, Any]:
        if backend == "digital_pdf":
            return extract_pdf_page_digital(job.page_unit.page)
        if backend == "tesseract_pdf_page":
            return await asyncio.to_thread(ocr_pdf_page_tesseract, job.page_unit.page)
        if backend == "ocr_client_pdf_remote":
            if self.ocr_client is None:
                raise ValueError("OCR client backend selected but OCRClient is not configured")
            return await asyncio.to_thread(ocr_pdf_page_ocr_remote, job.page_unit.page, self.ocr_client)
        raise ValueError(f"Unknown backend: {backend}")

    async def _run_with_escalation(self, job: OCRPageJob) -> dict[str, Any]:
        backend = job.page_unit.backend
        best_payload: dict[str, Any] | None = None
        best_score = -1.0
        page_started_at = time.perf_counter()
        logger.info(
            "page document_id=%s page=%d status=start backend=%s",
            job.document_id,
            job.page_unit.page_index,
            backend,
        )

        while backend is not None:
            logger.debug(f"worker page={job.page_unit.page_index} backend={backend} status=start")
            backend_started_at = time.perf_counter()
            payload = await self._run_backend(backend, job)
            markdown = payload.get("markdown", "")
            score = self._quality_score(markdown)
            preview = markdown[:120].replace("\n", "\\n")
            logger.debug(
                f"worker page={job.page_unit.page_index} backend={backend} status=done "
                f"score={score:.3f} markdown_len={len(markdown)} preview={preview!r}"
            )
            logger.info(
                "page document_id=%s page=%d backend=%s status=attempt_done score=%.3f duration_ms=%.2f",
                job.document_id,
                job.page_unit.page_index,
                backend,
                score,
                (time.perf_counter() - backend_started_at) * 1000.0,
            )

            if score > best_score:
                best_score = score
                best_payload = payload

            if score >= OCR_QUALITY_MIN_SCORE:
                logger.info(
                    "page document_id=%s page=%d status=end backend=%s final_score=%.3f duration_ms=%.2f",
                    job.document_id,
                    job.page_unit.page_index,
                    backend,
                    score,
                    (time.perf_counter() - page_started_at) * 1000.0,
                )
                return payload

            next_backend = self._next_backend(backend)
            if next_backend is None:
                break
            logger.debug(
                f"worker page={job.page_unit.page_index} backend={backend} status=reschedule "
                f"reason=low_quality score={score:.3f} next_backend={next_backend}"
            )
            backend = next_backend

        if best_payload is None:
            raise ValueError("OCR extraction produced no payload")
        logger.debug(
            f"worker page={job.page_unit.page_index} backend=final status=degraded "
            f"best_score={best_score:.3f}"
        )
        logger.info(
            "page document_id=%s page=%d status=end backend=degraded final_score=%.3f duration_ms=%.2f",
            job.document_id,
            job.page_unit.page_index,
            best_score,
            (time.perf_counter() - page_started_at) * 1000.0,
        )
        return best_payload

from __future__ import annotations

import asyncio
from typing import Any

from ..config import OCR_WORKER_POOL_SIZE
from .digital_pdf import extract_pdf_page_digital
from .domain import DocumentTracker, OCRPageJob, PageResult
from .pdf_page_tesseract import ocr_pdf_page_tesseract


class OCRWorkerPool:
    def __init__(self, tracker: DocumentTracker) -> None:
        self.tracker = tracker
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
                if job.page_unit.backend == "digital_pdf":
                    payload = extract_pdf_page_digital(job.page_unit.page)
                elif job.page_unit.backend == "tesseract_pdf_page":
                    payload = await asyncio.to_thread(ocr_pdf_page_tesseract, job.page_unit.page)
                else:
                    raise ValueError(f"Unknown backend: {job.page_unit.backend}")
                self.tracker.mark_done(PageResult(page_index=job.page_unit.page_index, payload=payload))
            finally:
                self.queue.task_done()

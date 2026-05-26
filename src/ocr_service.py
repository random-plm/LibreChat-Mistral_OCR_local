from __future__ import annotations

import uuid
from typing import Any

import fitz
from fastapi import HTTPException

from .models import OCRServiceInput
from .ocr_backend import BackendRouter, DocumentTracker, OCRWorkerPool, PageUnit, ocr_image


async def ocr_pdf(service_input: OCRServiceInput, workdir, router: BackendRouter) -> list[dict[str, Any]]:
    doc = fitz.open(service_input.resolved_input_path)
    document_id = f"doc-{uuid.uuid4().hex}"
    try:
        wanted = set(service_input.requested_pages) if service_input.requested_pages else None
        page_units: list[PageUnit] = []

        for page in doc:
            page_index = page.number
            one_based = page_index + 1
            if wanted is not None and one_based not in wanted and page_index not in wanted:
                continue

            page_units.append(
                PageUnit(
                    page=page,
                    page_index=page_index,
                    height=int(page.rect.height),
                    width=int(page.rect.width),
                    backend=router.select_page_backend(page),
                )
            )

        tracker = DocumentTracker(document_id=document_id, total_pages=len(page_units))
        if tracker.total_pages == 0:
            return []

        async with OCRWorkerPool(tracker) as pool:
            for page_unit in page_units:
                job = router.route_page(document_id, page_unit)
                await pool.submit(job)
            await tracker.wait_done()

        return [tracker.results[idx] for idx in sorted(tracker.results.keys())]
    finally:
        doc.close()


async def process_ocr_input(service_input: OCRServiceInput, workdir) -> dict[str, Any]:
    input_path = service_input.resolved_input_path
    if not input_path.exists():
        raise HTTPException(status_code=400, detail="No input file resolved for OCR")

    router = BackendRouter()
    doc_pipeline = router.route_document(input_path)

    if doc_pipeline == "pdf_pipeline":
        pages = await ocr_pdf(service_input, workdir, router)
    elif doc_pipeline == "image_pipeline":
        pages = ocr_image(input_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported input type: {input_path.suffix.lower() or 'unknown'}")

    document_annotation = None
    if service_input.doc_annotation_format:
        full_text = "\n\n".join([p.get("markdown", "") for p in pages]).strip()
        document_annotation = {
            "format": service_input.doc_annotation_format,
            "prompt": service_input.doc_annotation_prompt,
            "content": full_text,
        }

    return {
        "model": service_input.model_name,
        "pages": pages,
        "document_annotation": document_annotation,
        "usage_info": {
            "pages_processed": len(pages),
            "doc_size_bytes": input_path.stat().st_size,
        },
    }

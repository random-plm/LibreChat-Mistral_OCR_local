from __future__ import annotations

import shutil
from pathlib import Path
from urllib.parse import urlparse

import requests
from fastapi import HTTPException, Request, UploadFile

from .config import MODEL_NAME, PUBLIC_BASE_URL
from .file_store import load_file_meta
from .models import OCRRequest, OCRServiceInput


async def parse_ocr_request_to_service_input(request: Request, tmp_work: Path) -> OCRServiceInput:
    content_type = request.headers.get("content-type", "")

    resolved_input_path: Path | None = None
    model_name = MODEL_NAME
    include_image_base64 = False
    requested_pages = None
    doc_annotation_format = None
    doc_annotation_prompt = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        model_name = str(form.get("model") or MODEL_NAME)
        include_image_base64 = str(form.get("include_image_base64") or "").lower() == "true"
        up = form.get("file")
        if up is None or not isinstance(up, UploadFile):
            raise HTTPException(status_code=400, detail="multipart /v1/ocr requires file field")
        suffix = Path(up.filename or "upload.bin").suffix or ".bin"
        resolved_input_path = tmp_work / f"upload{suffix}"
        with resolved_input_path.open("wb") as f:
            shutil.copyfileobj(up.file, f)
    else:
        req = OCRRequest(**(await request.json()))
        model_name = req.model or MODEL_NAME
        include_image_base64 = bool(req.include_image_base64)
        requested_pages = req.pages
        doc_annotation_format = req.document_annotation_format
        doc_annotation_prompt = req.document_annotation_prompt

        payload_doc = req.document.model_dump() if req.document else None
        if not payload_doc:
            raise HTTPException(status_code=400, detail="JSON /v1/ocr requires document")

        dtype = payload_doc.get("type")
        if dtype == "file":
            file_id = payload_doc.get("file_id") or payload_doc.get("id")
            if not file_id:
                raise HTTPException(status_code=400, detail="document.file_id is required for file type")
            resolved_input_path = Path(load_file_meta(file_id)["path"])
        elif dtype in {"document_url", "image_url"}:
            url_key = "document_url" if dtype == "document_url" else "image_url"
            url = payload_doc.get(url_key)
            if not url:
                raise HTTPException(status_code=400, detail=f"document.{url_key} is required")

            parsed = urlparse(url)
            public_base = urlparse(PUBLIC_BASE_URL)
            if dtype == "document_url" and parsed.scheme == public_base.scheme and parsed.netloc == public_base.netloc and parsed.path.startswith("/v1/files/") and parsed.path.endswith("/content"):
                parts = parsed.path.strip("/").split("/")
                if len(parts) < 4:
                    raise HTTPException(status_code=400, detail="Invalid local document_url format")
                resolved_input_path = Path(load_file_meta(parts[2])["path"])
            else:
                headers = {}
                auth_header = request.headers.get("authorization")
                if auth_header:
                    headers["Authorization"] = auth_header
                resp = requests.get(url, headers=headers, timeout=120)
                resp.raise_for_status()
                suffix = ".pdf" if "pdf" in resp.headers.get("content-type", "").lower() else ".bin"
                resolved_input_path = tmp_work / f"download{suffix}"
                resolved_input_path.write_bytes(resp.content)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported document.type: {dtype}")

    if resolved_input_path is None:
        raise HTTPException(status_code=400, detail="No input file resolved for OCR")

    return OCRServiceInput(
        model_name=model_name,
        include_image_base64=include_image_base64,
        requested_pages=requested_pages,
        doc_annotation_format=doc_annotation_format,
        doc_annotation_prompt=doc_annotation_prompt,
        resolved_input_path=resolved_input_path,
    )

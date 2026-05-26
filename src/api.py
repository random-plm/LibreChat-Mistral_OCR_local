from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from .api_parsers import parse_ocr_request_to_service_input
from .config import DEFAULT_VISIBILITY, MODEL_NAME, PUBLIC_BASE_URL, TMP_DIR
from .file_store import check_auth, delete_file_meta, list_file_meta, load_file_meta, now, public_meta, save_upload_to_storage
from .ocr_service import process_ocr_input

router = APIRouter()


@router.get("/healthz")
def healthz():
    return {"ok": True, "model": MODEL_NAME}


@router.get("/v1/models")
def list_models(authorization: str | None = Header(default=None)):
    check_auth(authorization)
    return {"object": "list", "data": [{"id": MODEL_NAME, "object": "model", "created": now(), "owned_by": "local", "capabilities": ["ocr"]}]}


@router.post("/v1/files")
async def upload_file(file: UploadFile = File(...), purpose: str = Form("ocr"), visibility: str = Form(DEFAULT_VISIBILITY), authorization: str | None = Header(default=None)):
    check_auth(authorization)
    return public_meta(save_upload_to_storage(file, purpose, visibility))


@router.get("/v1/files")
def list_files(authorization: str | None = Header(default=None)):
    check_auth(authorization)
    data = list_file_meta()
    return {"data": data, "object": "list", "total": len(data)}


@router.get("/v1/files/{file_id}")
def get_file(file_id: str, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    return public_meta(load_file_meta(file_id))


@router.get("/v1/files/{file_id}/url")
def get_file_url(file_id: str, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    load_file_meta(file_id)
    return {"url": f"{PUBLIC_BASE_URL}/v1/files/{file_id}/content"}


@router.get("/v1/files/{file_id}/content")
def get_file_content(file_id: str, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    meta = load_file_meta(file_id)
    file_path = Path(meta["path"])
    return FileResponse(path=str(file_path), media_type=meta.get("mimetype", "application/octet-stream"), filename=meta.get("filename", file_path.name))


@router.delete("/v1/files/{file_id}")
def delete_file(file_id: str, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    existed = delete_file_meta(file_id)
    if not existed:
        raise HTTPException(status_code=404, detail=f"Unknown file id: {file_id}")
    return {"id": file_id, "object": "file.deleted", "deleted": True}


@router.post("/v1/ocr")
async def process_ocr(request: Request, authorization: str | None = Header(default=None)):
    check_auth(authorization)

    tmp_work = Path(tempfile.mkdtemp(dir=TMP_DIR))
    try:
        service_input = await parse_ocr_request_to_service_input(request, tmp_work)
        return JSONResponse(await process_ocr_input(service_input, tmp_work))
    finally:
        if tmp_work.exists():
            shutil.rmtree(tmp_work, ignore_errors=True)

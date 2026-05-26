from __future__ import annotations

import hashlib
import json
import mimetypes
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile

from .config import DEFAULT_VISIBILITY, FILE_TTL_SECONDS, STORAGE_DIR


def now() -> int:
    return int(time.time())


def check_auth(auth_header: str | None) -> None:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")


def new_file_id() -> str:
    return f"file-{uuid.uuid4().hex}"


def file_meta_path(file_id: str) -> Path:
    return STORAGE_DIR / f"{file_id}.json"


def guess_mimetype(filename: str | None) -> str:
    mt, _ = mimetypes.guess_type(filename or "")
    return mt or "application/octet-stream"


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_meta(*, file_id: str, filename: str, purpose: str, path: Path, visibility: str) -> dict[str, Any]:
    created_at = now()
    return {
        "id": file_id,
        "object": "file",
        "bytes": path.stat().st_size,
        "created_at": created_at,
        "expires_at": created_at + FILE_TTL_SECONDS,
        "filename": filename,
        "mimetype": guess_mimetype(filename),
        "num_lines": None,
        "purpose": purpose,
        "sample_type": "ocr_input",
        "signature": sha256_of_file(path),
        "source": "local",
        "visibility": visibility or DEFAULT_VISIBILITY,
        "path": str(path),
    }


def save_upload_to_storage(upload: UploadFile, purpose: str, visibility: str) -> dict[str, Any]:
    file_id = new_file_id()
    suffix = Path(upload.filename or "upload.bin").suffix or ".bin"
    bin_path = STORAGE_DIR / f"{file_id}{suffix}"
    with bin_path.open("wb") as f:
        shutil.copyfileobj(upload.file, f)

    meta = build_meta(
        file_id=file_id,
        filename=upload.filename or bin_path.name,
        purpose=purpose,
        path=bin_path,
        visibility=visibility,
    )
    file_meta_path(file_id).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def load_file_meta(file_id: str) -> dict[str, Any]:
    meta_path = file_meta_path(file_id)
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail=f"Unknown file id: {file_id}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def public_meta(meta: dict[str, Any]) -> dict[str, Any]:
    clean = dict(meta)
    clean.pop("path", None)
    return clean


def list_file_meta() -> list[dict[str, Any]]:
    out = []
    for meta_path in sorted(STORAGE_DIR.glob("file-*.json")):
        try:
            out.append(public_meta(json.loads(meta_path.read_text(encoding="utf-8"))))
        except Exception:
            continue
    return out


def delete_file_meta(file_id: str) -> bool:
    deleted = False
    meta_path = file_meta_path(file_id)
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            file_path = Path(meta.get("path", ""))
            if file_path.exists():
                file_path.unlink(missing_ok=True)
                deleted = True
        except Exception:
            pass
        meta_path.unlink(missing_ok=True)
        deleted = True

    for p in STORAGE_DIR.glob(f"{file_id}.*"):
        if p.name.endswith(".json"):
            continue
        if p.exists():
            p.unlink(missing_ok=True)
            deleted = True
    return deleted

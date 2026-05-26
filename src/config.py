from __future__ import annotations

import os
from pathlib import Path

APP_TITLE = "Local Mistral OCR-Compatible Wrapper"
MODEL_NAME = os.getenv("OCR_MODEL_NAME", "mistral-ocr-latest")
STORAGE_DIR = Path(os.getenv("OCR_STORAGE_DIR", "/data/files"))
TMP_DIR = Path(os.getenv("OCR_TMP_DIR", "/tmp/ocr-wrapper"))
TESSERACT_LANG = os.getenv("TESSERACT_LANG", "eng")
OCR_TEXT_THRESHOLD = int(os.getenv("OCR_TEXT_THRESHOLD", "50"))
OCR_ROUTER_MIN_TEXT_THRESHOLD = int(os.getenv("OCR_ROUTER_MIN_TEXT_THRESHOLD", str(OCR_TEXT_THRESHOLD)))
OCR_WORKER_POOL_SIZE = int(os.getenv("OCR_WORKER_POOL_SIZE", "12"))
FILE_TTL_SECONDS = int(os.getenv("FILE_TTL_SECONDS", str(7 * 24 * 3600)))
DEFAULT_VISIBILITY = os.getenv("DEFAULT_VISIBILITY", "workspace")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8089")

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

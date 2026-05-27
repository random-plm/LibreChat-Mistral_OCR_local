from __future__ import annotations

import os
from pathlib import Path

APP_TITLE = "Local Mistral OCR-Compatible Wrapper"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
MODEL_NAME = os.getenv("OCR_MODEL_NAME", "mistral-ocr-latest")
STORAGE_DIR = Path(os.getenv("OCR_STORAGE_DIR", "/data/files"))
TMP_DIR = Path(os.getenv("OCR_TMP_DIR", "/tmp/ocr-wrapper"))
TESSERACT_LANG = os.getenv("TESSERACT_LANG", "eng")
OCR_WORKER_POOL_SIZE = int(os.getenv("OCR_WORKER_POOL_SIZE", "1"))
OCR_API_KEY = os.getenv("OCR_API_KEY", "TODO")
OCR_BASE_URL = os.getenv("OCR_BASE_URL", "http://127.0.0.1:18082/v1")
OCR_MODEL = os.getenv("OCR_MODEL", "paddleocr-vl")
OCR_TIMEOUT = float(os.getenv("OCR_TIMEOUT", "3600"))
OCR_PROMPT = os.getenv("OCR_PROMPT","OCR: ")
FILE_TTL_SECONDS = int(os.getenv("FILE_TTL_SECONDS", str(7 * 24 * 3600)))
DEFAULT_VISIBILITY = os.getenv("DEFAULT_VISIBILITY", "workspace")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8089")

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)


OCR_ROUTER_MIN_TEXT_THRESHOLD = int(os.getenv("OCR_ROUTER_MIN_TEXT_THRESHOLD", "50"))
OCR_ROUTER_MIN_PRINTABLE_RATIO = float(os.getenv("OCR_ROUTER_MIN_PRINTABLE_RATIO", "0.85"))
OCR_ROUTER_MAX_DIGITAL_IMAGE_COVERAGE = float(os.getenv("OCR_ROUTER_MAX_DIGITAL_IMAGE_COVERAGE", "0.05"))
OCR_ROUTER_MAX_TESSERACT_IMAGE_COVERAGE = float(os.getenv("OCR_ROUTER_MAX_TESSERACT_IMAGE_COVERAGE", "0.50"))
OCR_ROUTER_MAX_TESSERACT_IMAGE_COUNT = int(os.getenv("OCR_ROUTER_MAX_TESSERACT_IMAGE_COUNT", "2"))
OCR_ROUTER_DEBUG = os.getenv("OCR_ROUTER_DEBUG", "0").lower() in {"1", "true", "yes", "on"}
OCR_QUALITY_MIN_LENGTH = int(os.getenv("OCR_QUALITY_MIN_LENGTH", "40"))
OCR_QUALITY_MIN_SCORE = float(os.getenv("OCR_QUALITY_MIN_SCORE", "0.45"))

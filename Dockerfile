FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LOG_LEVEL=INFO \
    OCR_STORAGE_DIR=/data/files \
    OCR_TMP_DIR=/tmp/ocr-wrapper \
    OCR_MODEL_NAME=mistral-ocr-latest \
    TESSERACT_LANG=eng \
    OCR_ROUTER_MIN_TEXT_THRESHOLD=50 \
    OCR_ROUTER_MIN_PRINTABLE_RATIO=0.85 \
    OCR_ROUTER_MAX_DIGITAL_IMAGE_COVERAGE=0.05 \
    OCR_ROUTER_MAX_TESSERACT_IMAGE_COVERAGE=0.50 \
    OCR_ROUTER_MAX_TESSERACT_IMAGE_COUNT=2 \
    OCR_QUALITY_MIN_LENGTH=40 \
    OCR_QUALITY_MIN_SCORE=0.45 \
    OCR_WORKER_POOL_SIZE=12 \
    OCR_API_KEY=EMPTY \
    OCR_BASE_URL=http://localhost:8000/v1 \
    OCR_MODEL=PaddlePaddle/PaddleOCR-VL \
    OCR_TIMEOUT=3600 \
    OCR_PROMPT="OCR: " \
    FILE_TTL_SECONDS=604800 \
    DEFAULT_VISIBILITY=workspace \
    PUBLIC_BASE_URL=http://127.0.0.1:8089

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src ./src
RUN mkdir -p /data/files /tmp/ocr-wrapper

EXPOSE 8089
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8089"]

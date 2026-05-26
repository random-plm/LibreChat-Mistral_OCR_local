from __future__ import annotations

import os
from pathlib import Path

from openai import OpenAI


class OCRClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OCR_API_KEY", "EMPTY")
        self.base_url = os.getenv("OCR_BASE_URL", "http://localhost:8000/v1")
        self.model = os.getenv("OCR_MODEL", "PaddlePaddle/PaddleOCR-VL")
        self.timeout = float(os.getenv("OCR_TIMEOUT", "3600"))
        self.prompt = os.getenv("OCR_PROMPT", "OCR:")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def infer(self, file_path: str) -> str:
        input_path = Path(file_path).expanduser().resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": input_path.as_uri()},
                        },
                        {
                            "type": "text",
                            "text": self.prompt,
                        },
                    ],
                }
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content or ""

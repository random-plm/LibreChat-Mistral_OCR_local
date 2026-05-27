from __future__ import annotations

import base64
import mimetypes
import random
import time
from pathlib import Path

from openai import OpenAI


class OCRClient:
    def __init__(self, api_key: str, base_url: str, model: str, timeout: float, prompt: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.prompt = prompt
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def infer(self, file_path: str) -> str:
        input_path = Path(file_path).expanduser().resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        mime_type, _ = mimetypes.guess_type(str(input_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        image_b64 = base64.b64encode(input_path.read_bytes()).decode("ascii")
        data_url = f"data:{mime_type};base64,{image_b64}"

        max_retries = 3
        base_delay = 0.5
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": data_url},
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
            except Exception:
                if attempt >= max_retries:
                    raise
                max_wait = base_delay * (2**attempt)
                time.sleep(random.uniform(0.0, max_wait))

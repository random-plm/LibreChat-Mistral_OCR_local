from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class OCRServiceInput:
    model_name: str
    include_image_base64: bool
    requested_pages: list[int] | None
    doc_annotation_format: str | None
    doc_annotation_prompt: str | None
    resolved_input_path: Path

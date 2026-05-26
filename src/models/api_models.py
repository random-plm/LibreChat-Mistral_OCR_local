from __future__ import annotations

from pydantic import BaseModel


class OCRDocument(BaseModel):
    type: str | None = None
    file_id: str | None = None
    document_url: str | None = None
    image_url: str | None = None


class OCRRequest(BaseModel):
    model: str | None = None
    document: OCRDocument | None = None
    pages: list[int] | None = None
    include_image_base64: bool | None = False
    image_limit: int | None = None
    image_min_size: int | None = None
    extract_header: bool | None = False
    extract_footer: bool | None = False
    table_format: str | None = None
    id: str | None = None
    bbox_annotation_format: str | None = None
    confidence_scores_granularity: str | None = None
    document_annotation_format: str | None = None
    document_annotation_prompt: str | None = None

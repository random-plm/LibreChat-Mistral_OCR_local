from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import fitz


@dataclass
class PageUnit:
    page: fitz.Page
    page_index: int
    width: int
    height: int
    backend: str


@dataclass
class OCRPageJob:
    document_id: str
    page_unit: PageUnit


@dataclass
class PageResult:
    page_index: int
    payload: dict[str, Any]


@dataclass
class DocumentTracker:
    document_id: str
    total_pages: int
    done_event: asyncio.Event = field(default_factory=asyncio.Event)
    results: dict[int, dict[str, Any]] = field(default_factory=dict)
    completed_pages: int = 0

    def mark_done(self, result: PageResult) -> None:
        self.results[result.page_index] = result.payload
        self.completed_pages += 1
        if self.completed_pages >= self.total_pages:
            self.done_event.set()

    async def wait_done(self) -> None:
        await self.done_event.wait()

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import fitz


def pdf_page_texts(pdf_path: Path) -> list[str]:
    doc = fitz.open(pdf_path)
    texts = [page.get_text("text").strip() for page in doc]
    doc.close()
    return texts


def extract_pdf_pages(
    pdf_path: Path,
    include_image_base64: bool = False,
    requested_pages: list[int] | None = None,
) -> list[dict[str, Any]]:
    doc = fitz.open(pdf_path)
    pages = []
    wanted = set(requested_pages) if requested_pages else None
    for page in doc:
        page_index = page.number
        one_based = page_index + 1
        if wanted is not None and one_based not in wanted and page_index not in wanted:
            continue

        try:
            markdown = page.get_text("text").strip()
        except Exception:
            markdown = ""

        images = []
        if include_image_base64:
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                img_bytes = pix.tobytes("png")
                images.append(
                    {
                        "id": f"img-{page_index}-{img_index}",
                        "top_left_x": 0,
                        "top_left_y": 0,
                        "bottom_right_x": 0,
                        "bottom_right_y": 0,
                        "image_base64": base64.b64encode(img_bytes).decode("ascii"),
                    }
                )

        pages.append(
            {
                "index": page_index,
                "markdown": markdown,
                "images": images,
                "dimensions": {
                    "dpi": 72,
                    "height": int(page.rect.height),
                    "width": int(page.rect.width),
                },
            }
        )
    doc.close()
    return pages


def extract_pdf_page_digital(page: fitz.Page) -> dict[str, Any]:
    return {
        "index": page.number,
        "markdown": page.get_text("text").strip(),
        "images": [],
        "dimensions": {
            "dpi": 72,
            "height": int(page.rect.height),
            "width": int(page.rect.width),
        },
    }

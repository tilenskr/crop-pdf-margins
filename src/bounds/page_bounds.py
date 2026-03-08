from typing import override
from .base import BoundsExtractor
import pymupdf
from page_layout import PageCropLayout


class PageBoundsExtractor(BoundsExtractor):
    """Extracts the tightest content bounding‐box on each page."""

    @override
    def get_bounds(
        self, doc: pymupdf.Document, dpi: int | None
    ) -> list[PageCropLayout]:
        _ = dpi
        rectangles: list[PageCropLayout] = []
        for page in doc:
            bounds = page.bound()
            # expand it by border_pt (on each side)
            rect = self._get_layout(
                bounds=pymupdf.Rect(
                    x0=bounds.x0, y0=bounds.y0, x1=bounds.x1, y1=bounds.y1
                ),
                has_content=True,
                page_rect=page.rect,
            )
            rectangles.append(rect)
        return rectangles

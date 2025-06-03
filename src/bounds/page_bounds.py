from typing import override
from bounds.base import BoundsExtractor
import pymupdf


class PageBoundsExtractor(BoundsExtractor):
    """Extracts the tightest content bounding‐box on each page."""

    @override
    def get_bounds(self, doc: pymupdf.Document) -> list[pymupdf.Rect]:
        rectangles: list[pymupdf.Rect] = []
        for page in doc:
            bounds = page.bound()
            # expand it by border_pt (on each side)
            rect = self._get_rectangle(
                bounds=pymupdf.Rect(
                    x0=bounds.x0, y0=bounds.y0, x1=bounds.x1, y1=bounds.y1
                ),
                has_content=True,
                page_rect=page.rect,
            )
            rectangles.append(rect)
        return rectangles

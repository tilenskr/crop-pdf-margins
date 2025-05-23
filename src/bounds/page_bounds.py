from typing import override
from bounds.base import BoundsExtractor
import pymupdf

class PageBoundsExtractor(BoundsExtractor):
    """Extracts the tightest content bounding‐box on each page."""

    @override
    def get_bounds(self, doc: pymupdf.Document) -> list[pymupdf.Rect]:
        rectangles: list[pymupdf.Rect] = []
        for page in doc:
            rect = page.bound()
            # expand it by border_pt (on each side)
            rect = pymupdf.Rect(
                rect.x0 + self._border_pt,
                rect.y0 + self._border_pt,
                rect.x1 - self._border_pt,
                rect.y1 - self._border_pt
            )
            rectangles.append(rect)
        return rectangles

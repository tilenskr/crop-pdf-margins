from abc import ABC, abstractmethod
from typing import TypedDict, override
import pymupdf

from bounds.base import BoundsExtractor

class TextBlock(TypedDict):
    number: int
    type:   int
    bbox:   tuple[float, float, float, float]
    lines:  list[dict]

class TextBlocksBoundsExtractor(BoundsExtractor, ABC):

    def get_bounds(self, doc: pymupdf.Document) -> list[pymupdf.Rect]:
        rectangles: list[pymupdf.Rect] = []
        for page in doc:
            # initialize to extremes
            x0, y0 = float("inf"), float("inf")
            x1, y1 = 0, 0

            text_blocks = self.get_text_blocks(page)
            for text_block in text_blocks:
                bx0, by0, bx1, by1 = text_block["bbox"]
                x0, y0 = min(x0, bx0), min(y0, by0)
                x1, y1 = max(x1, bx1), max(y1, by1)
            # 2) images
            # for img in page.get_images(full=True):
            #     xref = img[0]
            #     ix0, iy0, ix1, iy1 = page.get_image_bbox(xref)
            #     x0, y0 = min(x0, ix0), min(y0, iy0)
            #     x1, y1 = max(x1, ix1), max(y1, iy1)

            # apply border and crop
            if len(text_blocks) != 0:
                rect = pymupdf.Rect(
                    x0 - self._border_pt,
                    y0 - self._border_pt,
                    x1 + self._border_pt,
                    y1 + self._border_pt,
                )
                rectangles.append(rect)
            else:
                current_rect: pymupdf.Rect = page.rect
                rectangles.append(
                    pymupdf.Rect(0, 0, current_rect.width, current_rect.height)
                )
                pass
        return rectangles

    @staticmethod
    @abstractmethod
    def get_text_blocks(page: pymupdf.Page) -> list[TextBlock]:
        pass


class TextPageBoundsExtractor(TextBlocksBoundsExtractor):
    """text blocks (Textpage content as a Python dictionary; . May include text and images.)"""

    @staticmethod
    @override
    def get_text_blocks(page: pymupdf.Page) -> list[TextBlock]:
        return page.get_textpage().extractDICT(sort=True)["blocks"]


class DictTextBoundsExtractor(TextBlocksBoundsExtractor):
    @staticmethod
    @override
    def get_text_blocks(page: pymupdf.Page) -> list[TextBlock]:
        return page.get_text("dict")["blocks"]  # type: ignore

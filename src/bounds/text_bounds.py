from abc import ABC, abstractmethod
from typing import TypedDict, override
import pymupdf

from bounds.base import BoundsExtractor


class TextBlock(TypedDict):
    number: int
    type: int
    bbox: tuple[float, float, float, float]
    lines: list[dict]


class TextBlocksBoundsExtractor(BoundsExtractor, ABC):
    _use_image_bounds: bool = False

    def get_bounds(self, doc: pymupdf.Document) -> list[pymupdf.Rect]:
        rectangles: list[pymupdf.Rect] = []
        for page in doc:
            # initialize to extremes
            x0, y0 = float("inf"), float("inf")
            x1, y1 = 0, 0

            text_blocks = self._get_text_blocks(page)
            for text_block in text_blocks:
                bx0, by0, bx1, by1 = text_block["bbox"]
                x0, y0 = min(x0, bx0), min(y0, by0)
                x1, y1 = max(x1, bx1), max(y1, by1)

            if self._use_image_bounds:
                img_rect = self._get_images_bounds(page)
                x0, y0 = min(x0, img_rect.x0), min(y0, img_rect.y0)
                x1, y1 = max(x1, img_rect.x1), max(y1, img_rect.y1)

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
                # handle empty pages
                current_rect: pymupdf.Rect = page.rect
                rectangles.append(
                    pymupdf.Rect(0, 0, current_rect.width, current_rect.height)
                )
        return rectangles

    @staticmethod
    def _get_images_bounds(page: pymupdf.Page) -> pymupdf.Rect:
        x0, y0 = float("inf"), float("inf")
        x1, y1 = 0, 0

        for img in page.get_images(full=True):
            img_bbox = page.get_image_bbox(img)
            if isinstance(img_bbox, tuple):
                img_rect = img_bbox[0]
            else:
                img_rect = img_bbox
            ix0, iy0, ix1, iy1 = img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1

            x0, y0 = min(x0, ix0), min(y0, iy0)
            x1, y1 = max(x1, ix1), max(y1, iy1)
        return pymupdf.Rect(x0, y0, x1, y1)

    @staticmethod
    @abstractmethod
    def _get_text_blocks(page: pymupdf.Page) -> list[TextBlock]:
        pass


class TextPageBoundsExtractor(TextBlocksBoundsExtractor):
    """text blocks (Textpage content as a Python dictionary; . May include text and images.)"""

    @staticmethod
    @override
    def _get_text_blocks(page: pymupdf.Page) -> list[TextBlock]:
        return page.get_textpage().extractDICT(sort=True)["blocks"]


class DictTextBoundsExtractor(TextBlocksBoundsExtractor):
    @staticmethod
    @override
    def _get_text_blocks(page: pymupdf.Page) -> list[TextBlock]:
        return page.get_text("dict")["blocks"]  # type: ignore


class TextBlocksAndImageBoundsExtractor(TextPageBoundsExtractor):
    _use_image_bounds: bool = True


class DictTextAndImageBoundsExtractor(DictTextBoundsExtractor):
    _use_image_bounds: bool = True

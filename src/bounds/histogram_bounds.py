from typing import override

import pymupdf
from PIL import Image
from tqdm import tqdm

from .base import BoundsExtractor
from collections import Counter


class HistogramBoundsExtractor(BoundsExtractor):
    @override
    def get_bounds(self, doc: pymupdf.Document, dpi: int | None) -> list[pymupdf.Rect]:
        rectangles: list[pymupdf.Rect] = []

        for i in tqdm(range(doc.page_count)):
            page = doc.load_page(i)
            pix: pymupdf.Pixmap = (
                page.get_pixmap(dpi=dpi) if dpi is not None else page.get_pixmap()
            )  # type:ignore
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            pixels: list[tuple[int, int, int]] = list(img.getdata())
            counter = Counter(pixels)
            dominant_color, _ = counter.most_common(1)[0]

            leftmost_point = self._get_leftmost_point(pixels, img.size, dominant_color)
            if self._is_empty_page(pixels, img.size[0], leftmost_point, dominant_color):
                rect = self._get_rectangle(
                bounds=pymupdf.Rect(),
                has_content=False,
                page_rect=page.rect,
            )
                rectangles.append(rect)
                continue
            topmost_point = self._get_topmost_point(pixels, img.size, dominant_color)
            rightmost_point = self._get_rightmost_point(pixels, img.size, dominant_color)
            bottommost_point = self._get_bottommost_point(pixels, img.size, dominant_color)
            
            x0, y0, x1, y1 = leftmost_point[0], topmost_point[1], rightmost_point[0], bottommost_point[1]

            if dpi is not None:
                scale_factor = 72.0 / dpi
                x0, y0, x1, y1 = x0 * scale_factor, y0 * scale_factor, x1 * scale_factor, y1 * scale_factor


            rect = self._get_rectangle(
                bounds=pymupdf.Rect(
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                ),
                has_content=True,
                page_rect=page.rect,
            )
            rectangles.append(rect)
        return rectangles


    def _get_leftmost_point(self, pixels: list[tuple[int, int, int]], 
                            img_size: tuple[int, int], color: tuple[int, int, int]) -> tuple[int, int]:
        width, height = img_size
        for j in range(width):
            for i in range(height):
                if self._pixel_at(pixels, width, i, j) != color:
                    return (j, i)
        return (0, 0)
    
    def _is_empty_page(self, pixels: list[tuple[int, int, int]], 
                       width: int, leftmost_point:tuple[int, int],
                       dominant_color: tuple[int,int,int]) -> bool:
        return leftmost_point == (0, 0) and self._pixel_at(pixels, width, 
                                                            leftmost_point[0], leftmost_point[1]) == dominant_color    
    def _get_topmost_point(self, pixels: list[tuple[int, int, int]], 
                            img_size: tuple[int, int], color: tuple[int, int, int]) -> tuple[int, int]:
        width, height = img_size
        for i in range(height):
            for j in range(width):
                if self._pixel_at(pixels, width, i, j) != color:
                    return (j, i)
        return (0, 0)
    
    def _get_rightmost_point(self, pixels: list[tuple[int, int, int]], 
                            img_size: tuple[int, int], color: tuple[int, int, int]) -> tuple[int, int]:
        width, height = img_size
        for j in range(width - 1, -1, -1):
            for i in range(height - 1, -1, -1):
                if self._pixel_at(pixels, width, i, j) != color:
                    return (j, i)
        return (width - 1, height - 1)
    
    def _get_bottommost_point(self, pixels: list[tuple[int, int, int]],
                            img_size: tuple[int, int], color: tuple[int, int, int]) -> tuple[int, int]:
        width, height = img_size
        for i in range(height - 1, -1, -1):
            for j in range(width - 1, -1, -1):
                if self._pixel_at(pixels, width, i, j) != color:
                    return (j, i)
        return (width - 1, height - 1)


    @staticmethod
    def _pixel_at(pixels: list[tuple[int, int, int]], width, i: int, j: int) -> tuple[int,int,int]:
        return pixels[i * width + j]

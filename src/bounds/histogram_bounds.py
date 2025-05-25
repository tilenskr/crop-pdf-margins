from typing import override

import pymupdf
from PIL import Image
from tqdm import tqdm

from bounds.base import BoundsExtractor
from collections import Counter


class HistogramBoundsExtractor(BoundsExtractor):
    @override
    def get_bounds(self, doc: pymupdf.Document) -> list[pymupdf.Rect]:
        rectangles: list[pymupdf.Rect] = []
        for i in tqdm(range(doc.page_count)):
            page = doc.load_page(i)
            pix: pymupdf.Pixmap = page.get_pixmap()  # type:ignore
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            pixels: list[tuple[int, int, int]] = list(img.getdata())
            counter = Counter(pixels)
            dominant_color, _ = counter.most_common(1)[0]

            leftmost_point = self._get_leftmost_point(pixels, img.size, dominant_color)
            topmost_point = self._get_topmost_point(pixels, img.size, dominant_color)
            rightmost_point = self._get_rightmost_point(pixels, img.size, dominant_color)
            bottommost_point = self._get_bottommost_point(pixels, img.size, dominant_color)
            rect = pymupdf.Rect(
                x0=leftmost_point[0],
                y0=topmost_point[1],
                x1=rightmost_point[0],
                y1=bottommost_point[1],
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

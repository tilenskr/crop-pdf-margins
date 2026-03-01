from collections import Counter
from typing import override

import pymupdf
from PIL import Image
from tqdm import tqdm

from ..base import BoundsExtractor
from .edge_cuts import get_border_cuts
from .raster import pixel_at


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
            left_cut, top_cut, right_cut, bottom_cut = self._get_border_cuts(
                pixels,
                img.size,
                dominant_color,
            )

            leftmost_point = self._get_leftmost_point(
                pixels,
                img.size,
                dominant_color,
                left_cut,
                right_cut,
                top_cut,
                bottom_cut,
            )
            if self._is_empty_page(leftmost_point):
                rect = self._get_rectangle(
                    bounds=pymupdf.Rect(),
                    has_content=False,
                    page_rect=page.rect,
                )
                rectangles.append(rect)
                continue
            topmost_point = self._get_topmost_point(
                pixels,
                img.size,
                dominant_color,
                left_cut,
                right_cut,
                top_cut,
                bottom_cut,
            )
            rightmost_point = self._get_rightmost_point(
                pixels,
                img.size,
                dominant_color,
                left_cut,
                right_cut,
                top_cut,
                bottom_cut,
            )
            bottommost_point = self._get_bottommost_point(
                pixels,
                img.size,
                dominant_color,
                left_cut,
                right_cut,
                top_cut,
                bottom_cut,
            )

            x0 = leftmost_point[0]
            y0 = topmost_point[1]
            x1 = rightmost_point[0]
            y1 = bottommost_point[1]

            if dpi is not None:
                # Pixel coordinates at custom DPI must be mapped back to PDF points.
                scale_factor = 72.0 / dpi
                x0 *= scale_factor
                y0 *= scale_factor
                x1 *= scale_factor
                y1 *= scale_factor

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

    def _get_leftmost_point(
        self,
        pixels: list[tuple[int, int, int]],
        img_size: tuple[int, int],
        color: tuple[int, int, int],
        left_cut: int,
        right_cut: int,
        top_cut: int,
        bottom_cut: int,
    ) -> tuple[int, int]:
        width, height = img_size
        min_col = left_cut
        max_col = width - 1 - right_cut
        min_row = top_cut
        max_row = height - 1 - bottom_cut
        for j in range(min_col, max_col + 1):
            for i in range(min_row, max_row + 1):
                if pixel_at(pixels, width, i, j) != color:
                    return (j, i)
        return (-1, -1)

    def _is_empty_page(self, leftmost_point: tuple[int, int]) -> bool:
        return leftmost_point == (-1, -1)

    def _get_topmost_point(
        self,
        pixels: list[tuple[int, int, int]],
        img_size: tuple[int, int],
        color: tuple[int, int, int],
        left_cut: int,
        right_cut: int,
        top_cut: int,
        bottom_cut: int,
    ) -> tuple[int, int]:
        width, height = img_size
        min_col = left_cut
        max_col = width - 1 - right_cut
        min_row = top_cut
        max_row = height - 1 - bottom_cut
        for i in range(min_row, max_row + 1):
            for j in range(min_col, max_col + 1):
                if pixel_at(pixels, width, i, j) != color:
                    return (j, i)
        return (min_col, min_row)

    def _get_rightmost_point(
        self,
        pixels: list[tuple[int, int, int]],
        img_size: tuple[int, int],
        color: tuple[int, int, int],
        left_cut: int,
        right_cut: int,
        top_cut: int,
        bottom_cut: int,
    ) -> tuple[int, int]:
        width, height = img_size
        min_col = left_cut
        max_col = width - 1 - right_cut
        min_row = top_cut
        max_row = height - 1 - bottom_cut
        for j in range(max_col, min_col - 1, -1):
            for i in range(max_row, min_row - 1, -1):
                if pixel_at(pixels, width, i, j) != color:
                    return (j, i)
        return (max_col, max_row)

    def _get_bottommost_point(
        self,
        pixels: list[tuple[int, int, int]],
        img_size: tuple[int, int],
        color: tuple[int, int, int],
        left_cut: int,
        right_cut: int,
        top_cut: int,
        bottom_cut: int,
    ) -> tuple[int, int]:
        width, height = img_size
        min_col = left_cut
        max_col = width - 1 - right_cut
        min_row = top_cut
        max_row = height - 1 - bottom_cut
        for i in range(max_row, min_row - 1, -1):
            for j in range(max_col, min_col - 1, -1):
                if pixel_at(pixels, width, i, j) != color:
                    return (j, i)
        return (max_col, max_row)

    def _get_border_cuts(
        self,
        pixels: list[tuple[int, int, int]],
        img_size: tuple[int, int],
        dominant_color: tuple[int, int, int],
    ) -> tuple[int, int, int, int]:
        return get_border_cuts(pixels, img_size, dominant_color)

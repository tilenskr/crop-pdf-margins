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
                if self._pixel_at(pixels, width, i, j) != color:
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
                if self._pixel_at(pixels, width, i, j) != color:
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
                if self._pixel_at(pixels, width, i, j) != color:
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
                if self._pixel_at(pixels, width, i, j) != color:
                    return (j, i)
        return (max_col, max_row)

    def _get_border_cuts(
        self,
        pixels: list[tuple[int, int, int]],
        img_size: tuple[int, int],
        dominant_color: tuple[int, int, int],
    ) -> tuple[int, int, int, int]:
        width, height = img_size
        left = self._scan_left_border(pixels, width, height, dominant_color)
        right = self._scan_right_border(pixels, width, height, dominant_color, left)
        top = self._scan_top_border(pixels, width, height, dominant_color, left, right)
        bottom = self._scan_bottom_border(pixels, width, height, dominant_color, left, right, top)
        return left, top, right, bottom

    def _scan_left_border(
        self,
        pixels: list[tuple[int, int, int]],
        width: int,
        height: int,
        dominant_color: tuple[int, int, int],
    ) -> int:
        left_cut = 0
        for col in range(width):
            if self._is_uniform_non_background_column(pixels, width, height, col, dominant_color):
                left_cut += 1
                continue
            break
        return left_cut

    def _scan_right_border(
        self,
        pixels: list[tuple[int, int, int]],
        width: int,
        height: int,
        dominant_color: tuple[int, int, int],
        left_cut: int,
    ) -> int:
        right_cut = 0
        for col in range(width - 1, left_cut - 1, -1):
            if self._is_uniform_non_background_column(pixels, width, height, col, dominant_color):
                right_cut += 1
                continue
            break
        return right_cut

    def _scan_top_border(
        self,
        pixels: list[tuple[int, int, int]],
        width: int,
        height: int,
        dominant_color: tuple[int, int, int],
        left_cut: int,
        right_cut: int,
    ) -> int:
        top_cut = 0
        start_col = left_cut
        end_col = width - 1 - right_cut
        for row in range(height):
            if self._is_uniform_non_background_row(
                pixels,
                width,
                row,
                start_col,
                end_col,
                dominant_color,
            ):
                top_cut += 1
                continue
            break
        return top_cut

    def _scan_bottom_border(
        self,
        pixels: list[tuple[int, int, int]],
        width: int,
        height: int,
        dominant_color: tuple[int, int, int],
        left_cut: int,
        right_cut: int,
        top_cut: int,
    ) -> int:
        bottom_cut = 0
        start_col = left_cut
        end_col = width - 1 - right_cut
        for row in range(height - 1, top_cut - 1, -1):
            if self._is_uniform_non_background_row(
                pixels,
                width,
                row,
                start_col,
                end_col,
                dominant_color,
            ):
                bottom_cut += 1
                continue
            break
        return bottom_cut

    def _is_uniform_non_background_row(
        self,
        pixels: list[tuple[int, int, int]],
        width: int,
        row: int,
        start_col: int,
        end_col: int,
        dominant_color: tuple[int, int, int],
    ) -> bool:
        if start_col > end_col:
            return False
        for col in range(start_col, end_col + 1):
            value = self._pixel_at(pixels, width, row, col)
            if value == dominant_color:
                return False
        return True

    def _is_uniform_non_background_column(
        self,
        pixels: list[tuple[int, int, int]],
        width: int,
        height: int,
        col: int,
        dominant_color: tuple[int, int, int],
    ) -> bool:
        for row in range(height):
            value = self._pixel_at(pixels, width, row, col)
            if value == dominant_color:
                return False
        return True

    @staticmethod
    def _pixel_at(pixels: list[tuple[int, int, int]], width, i: int, j: int) -> tuple[int, int, int]:
        return pixels[i * width + j]

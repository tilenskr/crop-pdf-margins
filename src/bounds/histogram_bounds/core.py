from collections import Counter
from dataclasses import dataclass
from typing import override

import pymupdf
from PIL import Image
from tqdm import tqdm

from ..base import BoundsExtractor
from .edge_cuts import get_border_cuts
from .header_footer import HeaderFooterDetector, HeaderFooterMode
from .raster import pixel_at


@dataclass(frozen=True)
class _PointSearchContext:
    pixels: list[tuple[int, int, int]]
    width: int
    height: int
    color: tuple[int, int, int]
    min_col: int
    max_col: int
    min_row: int
    max_row: int


class HistogramBoundsExtractor(BoundsExtractor):
    _detect_header_footer_mode: HeaderFooterMode | None
    _allow_partial_header_footer_mode: HeaderFooterMode | None
    def __init__(
        self,
        borders,
        detect_header_footer_mode: HeaderFooterMode | None,
        allow_partial_header_footer_mode: HeaderFooterMode | None,
    ):
        super().__init__(borders)
        self._detect_header_footer_mode = detect_header_footer_mode
        self._allow_partial_header_footer_mode = allow_partial_header_footer_mode

    @override
    def get_bounds(self, doc: pymupdf.Document, dpi: int | None) -> list[pymupdf.Rect]:
        total_steps = doc.page_count
        if self._detect_header_footer_mode is not None:
            total_steps += doc.page_count
        with tqdm(total=total_steps, desc="Histogram", unit="page") as progress:
            def on_page_done() -> None:
                progress.update(1)

            detector = HeaderFooterDetector(
                doc=doc,
                dpi=dpi,
                detect_mode=self._detect_header_footer_mode,
                allow_partial_mode=self._allow_partial_header_footer_mode,
            )
            header_footer_cuts = detector.detect_header_footer_cuts(on_page_done=on_page_done)
            rectangles: list[pymupdf.Rect] = []
            for i in range(doc.page_count):
                page = doc.load_page(i)
                pix: pymupdf.Pixmap = (
                    page.get_pixmap(dpi=dpi) if dpi is not None else page.get_pixmap()
                )  # type:ignore
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                pixels: list[tuple[int, int, int]] = list(img.getdata())
                counter = Counter(pixels)
                dominant_color, _ = counter.most_common(1)[0]
                vertical_cuts = header_footer_cuts[i]
                left_cut, top_cut, right_cut, bottom_cut = get_border_cuts(
                    pixels,
                    img.size,
                    dominant_color,
                    vertical_cuts.top_cut,
                    vertical_cuts.bottom_cut,
                )
                search_context = _PointSearchContext(
                    pixels=pixels,
                    width=img.width,
                    height=img.height,
                    color=dominant_color,
                    min_col=left_cut,
                    max_col=img.width - 1 - right_cut,
                    min_row=top_cut,
                    max_row=img.height - 1 - bottom_cut,
                )

                leftmost_point = self._get_leftmost_point(search_context)
                if self._is_empty_page(leftmost_point):
                    rect = self._get_rectangle(
                        bounds=pymupdf.Rect(),
                        has_content=False,
                        page_rect=page.rect,
                    )
                    rectangles.append(rect)
                    progress.update(1)
                    continue
                topmost_point = self._get_topmost_point(search_context)
                rightmost_point = self._get_rightmost_point(search_context)
                bottommost_point = self._get_bottommost_point(search_context)

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
                progress.update(1)
            return rectangles

    def _get_leftmost_point(
        self,
        context: _PointSearchContext,
    ) -> tuple[int, int]:
        for j in range(context.min_col, context.max_col + 1):
            for i in range(context.min_row, context.max_row + 1):
                if pixel_at(context.pixels, context.width, i, j) != context.color:
                    return (j, i)
        return (-1, -1)

    def _is_empty_page(self, leftmost_point: tuple[int, int]) -> bool:
        return leftmost_point == (-1, -1)

    def _get_topmost_point(
        self,
        context: _PointSearchContext,
    ) -> tuple[int, int]:
        for i in range(context.min_row, context.max_row + 1):
            for j in range(context.min_col, context.max_col + 1):
                if pixel_at(context.pixels, context.width, i, j) != context.color:
                    return (j, i)
        return (context.min_col, context.min_row)

    def _get_rightmost_point(
        self,
        context: _PointSearchContext,
    ) -> tuple[int, int]:
        for j in range(context.max_col, context.min_col - 1, -1):
            for i in range(context.max_row, context.min_row - 1, -1):
                if pixel_at(context.pixels, context.width, i, j) != context.color:
                    return (j, i)
        return (context.max_col, context.max_row)

    def _get_bottommost_point(
        self,
        context: _PointSearchContext,
    ) -> tuple[int, int]:
        for i in range(context.max_row, context.min_row - 1, -1):
            for j in range(context.max_col, context.min_col - 1, -1):
                if pixel_at(context.pixels, context.width, i, j) != context.color:
                    return (j, i)
        return (context.max_col, context.max_row)

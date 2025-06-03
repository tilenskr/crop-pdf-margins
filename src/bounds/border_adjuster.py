from abc import ABC, abstractmethod
from typing import override

import pymupdf

from borders import BorderSpec, BorderUnit


class BorderAdjuster(ABC):
    def __init__(self, value: float):
        self._value = value

    def adjust_bounds(
        self, bounds: pymupdf.Rect, page_rect: pymupdf.Rect
    ) -> pymupdf.Rect:
        border_bounds = self._apply_border(bounds, page_rect)

        # the rect should not extend beyond the page bounds
        x0 = max(page_rect.x0, border_bounds.x0)
        y0 = max(page_rect.y0, border_bounds.y0)
        x1 = min(page_rect.x1, border_bounds.x1)
        y1 = min(page_rect.y1, border_bounds.y1)

        return pymupdf.Rect(x0, y0, x1, y1)

    @abstractmethod
    def _apply_border(
        self, bounds: pymupdf.Rect, page_rect: pymupdf.Rect
    ) -> pymupdf.Rect:
        pass


class PointBorderAdjuster(BorderAdjuster):
    @override
    def _apply_border(
        self, bounds: pymupdf.Rect, page_rect: pymupdf.Rect
    ) -> pymupdf.Rect:
        return pymupdf.Rect(
            bounds.x0 - self._value,
            bounds.y0 - self._value,
            bounds.x1 + self._value,
            bounds.y1 + self._value,
        )


class RatioBorderAdjuster(BorderAdjuster):
    @override
    def _apply_border(
        self, bounds: pymupdf.Rect, page_rect: pymupdf.Rect
    ) -> pymupdf.Rect:
        border_width = page_rect.width * self._value
        border_height = page_rect.height * self._value
        return pymupdf.Rect(
            bounds.x0 - border_width,
            bounds.y0 - border_height,
            bounds.x1 + border_width,
            bounds.y1 + border_height,
        )


_BORDER_MAPPING: dict[BorderUnit, type[BorderAdjuster]] = {
    BorderUnit.POINT: PointBorderAdjuster,
    BorderUnit.RATIO: RatioBorderAdjuster,
}


def get_border_adjuster(border: BorderSpec) -> BorderAdjuster:
    try:
        cls = _BORDER_MAPPING[border.unit]
    except KeyError:
        raise ValueError(f"Unknown border adjuster: {border.unit!r}")
    return cls(border.value)

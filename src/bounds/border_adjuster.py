import pymupdf

from borders import BorderSpec, BorderUnit, FourBorders
from page_layout import PageCropLayout


class BorderAdjuster:
    def __init__(self, borders: FourBorders):
        self._borders = borders

    def create_layout(
        self, bounds: pymupdf.Rect, page_rect: pymupdf.Rect
    ) -> PageCropLayout:
        top = self._compute_border(self._borders.top, page_rect.height)
        right = self._compute_border(self._borders.right, page_rect.width)
        bottom = self._compute_border(self._borders.bottom, page_rect.height)
        left = self._compute_border(self._borders.left, page_rect.width)

        visible_rect = pymupdf.Rect(
            bounds.x0 - left,
            bounds.y0 - top,
            bounds.x1 + right,
            bounds.y1 + bottom,
        )

        destination_rect = pymupdf.Rect(
            page_rect.x0 + left,
            page_rect.y0 + top,
            page_rect.x1 - right,
            page_rect.y1 - bottom,
        )

        return PageCropLayout(
            page_rect=page_rect,
            content_rect=bounds,
            visible_rect=self._clamp_rect(visible_rect, page_rect),
            destination_rect=self._clamp_inset_rect(destination_rect, page_rect),
        )

    @staticmethod
    def _clamp_rect(rect: pymupdf.Rect, page_rect: pymupdf.Rect) -> pymupdf.Rect:
        x0 = max(page_rect.x0, rect.x0)
        y0 = max(page_rect.y0, rect.y0)
        x1 = min(page_rect.x1, rect.x1)
        y1 = min(page_rect.y1, rect.y1)
        return pymupdf.Rect(x0, y0, x1, y1)

    @staticmethod
    def _clamp_inset_rect(rect: pymupdf.Rect, page_rect: pymupdf.Rect) -> pymupdf.Rect:
        x0 = min(max(rect.x0, page_rect.x0), page_rect.x1)
        y0 = min(max(rect.y0, page_rect.y0), page_rect.y1)
        x1 = max(min(rect.x1, page_rect.x1), page_rect.x0)
        y1 = max(min(rect.y1, page_rect.y1), page_rect.y0)
        return pymupdf.Rect(x0, y0, x1, y1)

    def _compute_border(self, border_spec: BorderSpec, page_dim: float) -> float:
        if border_spec.unit == BorderUnit.POINT:
            return border_spec.value
        elif border_spec.unit == BorderUnit.RATIO:
            return page_dim * border_spec.value
        else:
            raise ValueError(f"Unknown border unit: {border_spec.unit!r}")

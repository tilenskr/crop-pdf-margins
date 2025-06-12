import pymupdf

from borders import BorderSpec, BorderUnit, FourBorders


class BorderAdjuster:
    def __init__(self, borders: FourBorders):
        self._borders = borders

    def adjust_bounds(self, bounds: pymupdf.Rect, page_rect: pymupdf.Rect) -> pymupdf.Rect:
        # Compute each side separately
        top = self._compute_border(self._borders.top, page_rect.height)
        right = self._compute_border(self._borders.right, page_rect.width)
        bottom = self._compute_border(self._borders.bottom, page_rect.height)
        left = self._compute_border(self._borders.left, page_rect.width)

        border_bounds = pymupdf.Rect(
            bounds.x0 - left,
            bounds.y0 - top,
            bounds.x1 + right,
            bounds.y1 + bottom,
        )

         # The rect should not extend beyond the page bounds
        x0 = max(page_rect.x0, border_bounds.x0)
        y0 = max(page_rect.y0, border_bounds.y0)
        x1 = min(page_rect.x1, border_bounds.x1)
        y1 = min(page_rect.y1, border_bounds.y1)

        return pymupdf.Rect(x0, y0, x1, y1)

    def _compute_border(self, border_spec: BorderSpec, page_dim: float) -> float:
        if border_spec.unit == BorderUnit.POINT:
            return border_spec.value
        elif border_spec.unit == BorderUnit.RATIO:
            return page_dim * border_spec.value
        else:
            raise ValueError(f"Unknown border unit: {border_spec.unit!r}")

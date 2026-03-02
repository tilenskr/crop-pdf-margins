from dataclasses import dataclass

from .raster import pixel_at


@dataclass(frozen=True)
class _EdgeScanContext:
    pixels: list[tuple[int, int, int]]
    width: int
    height: int
    dominant_color: tuple[int, int, int]


def get_border_cuts(
    pixels: list[tuple[int, int, int]],
    img_size: tuple[int, int],
    dominant_color: tuple[int, int, int],
    initial_top_cut: int = 0,
    initial_bottom_cut: int = 0,
) -> tuple[int, int, int, int]:
    width, height = img_size
    context = _EdgeScanContext(
        pixels=pixels,
        width=width,
        height=height,
        dominant_color=dominant_color,
    )
    left = _scan_left_border(context)
    right = _scan_right_border(context, left)
    top = _scan_top_border(
        context,
        left,
        right,
        initial_top_cut,
        initial_bottom_cut,
    )
    bottom = _scan_bottom_border(
        context,
        left,
        right,
        top,
        initial_bottom_cut,
    )
    return left, top, right, bottom


def _scan_left_border(context: _EdgeScanContext) -> int:
    left_cut = 0
    for col in range(context.width):
        if _is_non_background_column(context, col):
            left_cut += 1
            continue
        break
    return left_cut


def _scan_right_border(
    context: _EdgeScanContext,
    left_cut: int,
) -> int:
    right_cut = 0
    for col in range(context.width - 1, left_cut - 1, -1):
        if _is_non_background_column(context, col):
            right_cut += 1
            continue
        break
    return right_cut


def _scan_top_border(
    context: _EdgeScanContext,
    left_cut: int,
    right_cut: int,
    initial_top_cut: int,
    initial_bottom_cut: int,
) -> int:
    top_cut = initial_top_cut
    start_col = left_cut
    end_col = context.width - 1 - right_cut
    bottom_limit = max(initial_top_cut, context.height - initial_bottom_cut)
    for row in range(initial_top_cut, bottom_limit):
        if _is_non_background_row(
            context,
            row,
            start_col,
            end_col,
        ):
            top_cut += 1
            continue
        break
    return top_cut


def _scan_bottom_border(
    context: _EdgeScanContext,
    left_cut: int,
    right_cut: int,
    top_cut: int,
    initial_bottom_cut: int,
) -> int:
    bottom_cut = initial_bottom_cut
    start_col = left_cut
    end_col = context.width - 1 - right_cut
    for row in range(context.height - 1 - initial_bottom_cut, top_cut - 1, -1):
        if _is_non_background_row(
            context,
            row,
            start_col,
            end_col,
        ):
            bottom_cut += 1
            continue
        break
    return bottom_cut


def _is_non_background_row(
    context: _EdgeScanContext,
    row: int,
    start_col: int,
    end_col: int,
) -> bool:
    if start_col > end_col:
        return False
    for col in range(start_col, end_col + 1):
        value = pixel_at(context.pixels, context.width, row, col)
        if value == context.dominant_color:
            return False
    return True


def _is_non_background_column(context: _EdgeScanContext, col: int) -> bool:
    for row in range(context.height):
        value = pixel_at(context.pixels, context.width, row, col)
        if value == context.dominant_color:
            return False
    return True

from .raster import pixel_at


def get_border_cuts(
    pixels: list[tuple[int, int, int]],
    img_size: tuple[int, int],
    dominant_color: tuple[int, int, int],
    initial_top_cut: int = 0,
    initial_bottom_cut: int = 0,
) -> tuple[int, int, int, int]:
    width, height = img_size
    left = _scan_left_border(pixels, width, height, dominant_color)
    right = _scan_right_border(pixels, width, height, dominant_color, left)
    top = _scan_top_border(
        pixels,
        width,
        height,
        dominant_color,
        left,
        right,
        initial_top_cut,
        initial_bottom_cut,
    )
    bottom = _scan_bottom_border(
        pixels,
        width,
        height,
        dominant_color,
        left,
        right,
        top,
        initial_bottom_cut,
    )
    return left, top, right, bottom


def _scan_left_border(
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
    dominant_color: tuple[int, int, int],
) -> int:
    left_cut = 0
    for col in range(width):
        if _is_non_background_column(pixels, width, height, col, dominant_color):
            left_cut += 1
            continue
        break
    return left_cut


def _scan_right_border(
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
    dominant_color: tuple[int, int, int],
    left_cut: int,
) -> int:
    right_cut = 0
    for col in range(width - 1, left_cut - 1, -1):
        if _is_non_background_column(pixels, width, height, col, dominant_color):
            right_cut += 1
            continue
        break
    return right_cut


def _scan_top_border(
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
    dominant_color: tuple[int, int, int],
    left_cut: int,
    right_cut: int,
    initial_top_cut: int,
    initial_bottom_cut: int,
) -> int:
    top_cut = initial_top_cut
    start_col = left_cut
    end_col = width - 1 - right_cut
    bottom_limit = max(initial_top_cut, height - initial_bottom_cut)
    for row in range(initial_top_cut, bottom_limit):
        if _is_non_background_row(
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
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
    dominant_color: tuple[int, int, int],
    left_cut: int,
    right_cut: int,
    top_cut: int,
    initial_bottom_cut: int,
) -> int:
    bottom_cut = initial_bottom_cut
    start_col = left_cut
    end_col = width - 1 - right_cut
    for row in range(height - 1 - initial_bottom_cut, top_cut - 1, -1):
        if _is_non_background_row(
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


def _is_non_background_row(
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
        value = pixel_at(pixels, width, row, col)
        if value == dominant_color:
            return False
    return True


def _is_non_background_column(
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
    col: int,
    dominant_color: tuple[int, int, int],
) -> bool:
    for row in range(height):
        value = pixel_at(pixels, width, row, col)
        if value == dominant_color:
            return False
    return True

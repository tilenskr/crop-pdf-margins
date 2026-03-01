from .raster import pixel_at


def get_border_cuts(
    pixels: list[tuple[int, int, int]],
    img_size: tuple[int, int],
    dominant_color: tuple[int, int, int],
) -> tuple[int, int, int, int]:
    width, height = img_size
    left = scan_left_border(pixels, width, height, dominant_color)
    right = scan_right_border(pixels, width, height, dominant_color, left)
    top = scan_top_border(pixels, width, height, dominant_color, left, right)
    bottom = scan_bottom_border(pixels, width, height, dominant_color, left, right, top)
    return left, top, right, bottom


def scan_left_border(
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
    dominant_color: tuple[int, int, int],
) -> int:
    left_cut = 0
    for col in range(width):
        if is_non_background_column(pixels, width, height, col, dominant_color):
            left_cut += 1
            continue
        break
    return left_cut


def scan_right_border(
    pixels: list[tuple[int, int, int]],
    width: int,
    height: int,
    dominant_color: tuple[int, int, int],
    left_cut: int,
) -> int:
    right_cut = 0
    for col in range(width - 1, left_cut - 1, -1):
        if is_non_background_column(pixels, width, height, col, dominant_color):
            right_cut += 1
            continue
        break
    return right_cut


def scan_top_border(
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
        if is_non_background_row(
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


def scan_bottom_border(
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
        if is_non_background_row(
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


def is_non_background_row(
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


def is_non_background_column(
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

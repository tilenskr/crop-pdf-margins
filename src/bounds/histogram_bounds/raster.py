def pixel_at(
    pixels: list[tuple[int, int, int]], width: int, row: int, col: int
) -> tuple[int, int, int]:
    return pixels[row * width + col]

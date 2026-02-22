import unittest

from src.borders import BorderSpec, BorderUnit, FourBorders
from src.bounds.histogram_bounds import HistogramBoundsExtractor


class HistogramBoundsExtractorBorderTests(unittest.TestCase):
    def setUp(self) -> None:
        zero = BorderSpec(0.0, BorderUnit.POINT)
        self.extractor = HistogramBoundsExtractor(FourBorders(zero, zero, zero, zero))
        self.bg = (255, 255, 255)

    def _build_pixels(
        self,
        width: int,
        height: int,
        default_color: tuple[int, int, int],
    ) -> list[tuple[int, int, int]]:
        return [default_color for _ in range(width * height)]

    def _set_row(
        self,
        pixels: list[tuple[int, int, int]],
        width: int,
        row: int,
        color: tuple[int, int, int],
    ) -> None:
        start = row * width
        for idx in range(start, start + width):
            pixels[idx] = color

    def _set_col(
        self,
        pixels: list[tuple[int, int, int]],
        width: int,
        height: int,
        col: int,
        color: tuple[int, int, int],
    ) -> None:
        for row in range(height):
            pixels[row * width + col] = color

    def test_detects_top_border_lines(self) -> None:
        width, height = 10, 8
        pixels = self._build_pixels(width, height, self.bg)
        border = (0, 0, 0)
        self._set_row(pixels, width, 0, border)
        self._set_row(pixels, width, 1, border)

        cuts = self.extractor._get_border_cuts(pixels, (width, height), self.bg)
        self.assertEqual(cuts, (0, 2, 0, 0))

    def test_detects_bottom_border_lines(self) -> None:
        width, height = 10, 8
        pixels = self._build_pixels(width, height, self.bg)
        border = (0, 0, 0)
        self._set_row(pixels, width, height - 1, border)
        self._set_row(pixels, width, height - 2, border)

        cuts = self.extractor._get_border_cuts(pixels, (width, height), self.bg)
        self.assertEqual(cuts, (0, 0, 0, 2))

    def test_detects_left_border_columns(self) -> None:
        width, height = 10, 8
        pixels = self._build_pixels(width, height, self.bg)
        border = (20, 20, 20)
        self._set_col(pixels, width, height, 0, border)
        self._set_col(pixels, width, height, 1, border)

        cuts = self.extractor._get_border_cuts(pixels, (width, height), self.bg)
        self.assertEqual(cuts, (2, 0, 0, 0))

    def test_detects_right_border_columns(self) -> None:
        width, height = 10, 8
        pixels = self._build_pixels(width, height, self.bg)
        border = (30, 30, 30)
        self._set_col(pixels, width, height, width - 1, border)
        self._set_col(pixels, width, height, width - 2, border)

        cuts = self.extractor._get_border_cuts(pixels, (width, height), self.bg)
        self.assertEqual(cuts, (0, 0, 2, 0))

    def test_does_not_trim_non_uniform_edge(self) -> None:
        width, height = 10, 8
        pixels = self._build_pixels(width, height, self.bg)
        border = (0, 0, 0)
        self._set_row(pixels, width, 0, border)
        pixels[0] = self.bg

        cuts = self.extractor._get_border_cuts(pixels, (width, height), self.bg)
        self.assertEqual(cuts, (0, 0, 0, 0))

    def test_detects_uniform_border_on_all_sides(self) -> None:
        width, height = 10, 8
        pixels = self._build_pixels(width, height, self.bg)
        border = (0, 0, 0)

        self._set_row(pixels, width, 0, border)
        self._set_row(pixels, width, height - 1, border)
        self._set_col(pixels, width, height, 0, border)
        self._set_col(pixels, width, height, width - 1, border)

        cuts = self.extractor._get_border_cuts(pixels, (width, height), self.bg)
        self.assertEqual(cuts, (1, 1, 1, 1))


if __name__ == "__main__":
    unittest.main()

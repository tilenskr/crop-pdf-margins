import unittest
from unittest.mock import MagicMock

from src.bounds.histogram_bounds.header_footer import (
    HeaderFooterDetector,
    HeaderFooterMode,
    _ContentRowBand,
)


class HeaderFooterFooterCutTests(unittest.TestCase):
    def _detector(self) -> HeaderFooterDetector:
        return HeaderFooterDetector(
            doc=MagicMock(page_count=0),
            dpi=None,
            detect_mode=HeaderFooterMode.BOTH,
            allow_partial_mode=None,
        )

    def test_footer_cut_uses_first_footer_band_after_body_gap(self) -> None:
        detector = self._detector()
        height = 1000
        bands = [
            _ContentRowBand(start_row=500, end_row=700),   # body
            _ContentRowBand(start_row=860, end_row=880),   # footer part 1
            _ContentRowBand(start_row=900, end_row=920),   # footer part 2
        ]

        cut = detector._detect_footer_cut(bands, height)

        # Cut starts at the first footer band after the body/footer gap.
        self.assertEqual(cut, 140)

    def test_footer_cut_stays_on_last_band_when_nearby_band_exists(self) -> None:
        detector = self._detector()
        height = 1000
        bands = [
            _ContentRowBand(start_row=500, end_row=700),   # body
            _ContentRowBand(start_row=830, end_row=835),   # nearby band
            _ContentRowBand(start_row=900, end_row=920),   # footer
        ]

        cut = detector._detect_footer_cut(bands, height)

        # Nearby band is treated as adjacent context, so the last band remains
        # the detected footer start.
        self.assertEqual(cut, 100)


if __name__ == "__main__":
    unittest.main()

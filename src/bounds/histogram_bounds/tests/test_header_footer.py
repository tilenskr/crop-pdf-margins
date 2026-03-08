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

        # With the smaller minimum-gap threshold, the later footer band counts
        # as a separate footer candidate once the intermediate gap is large
        # enough, so the cut starts at the final band.
        self.assertEqual(cut, 100)

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


class HeaderFooterHeaderCutTests(unittest.TestCase):
    def _detector(self) -> HeaderFooterDetector:
        return HeaderFooterDetector(
            doc=MagicMock(page_count=0),
            dpi=None,
            detect_mode=HeaderFooterMode.BOTH,
            allow_partial_mode=None,
        )

    def test_header_cut_uses_last_header_band_before_body_gap(self) -> None:
        detector = self._detector()
        height = 1000
        bands = [
            _ContentRowBand(start_row=60, end_row=80),     # header part 1
            _ContentRowBand(start_row=100, end_row=120),   # header part 2
            _ContentRowBand(start_row=260, end_row=700),   # body
        ]

        cut = detector._detect_header_cut(bands, height)

        # With the smaller minimum-gap threshold, the second band is no longer
        # grouped with the first header band, so the cut is placed after the
        # first band.
        self.assertEqual(cut, 81)

    def test_header_cut_stays_on_first_band_when_nearby_band_exists(self) -> None:
        detector = self._detector()
        height = 1000
        bands = [
            _ContentRowBand(start_row=60, end_row=80),     # header
            _ContentRowBand(start_row=95, end_row=100),    # nearby band
            _ContentRowBand(start_row=260, end_row=700),   # body
        ]

        cut = detector._detect_header_cut(bands, height)

        # The nearby band is separated by more than the reduced minimum gap, so
        # the cut still lands after the first band.
        self.assertEqual(cut, 81)


if __name__ == "__main__":
    unittest.main()

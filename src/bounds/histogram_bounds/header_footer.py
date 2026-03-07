from collections import Counter
from collections.abc import Callable
from dataclasses import InitVar, dataclass, field
from enum import Enum
from math import ceil
from statistics import median

import pymupdf
from PIL import Image

from .edge_cuts import get_border_cuts
from .raster import pixel_at


@dataclass(frozen=True)
class HeaderFooterCuts:
    top_cut: int = 0
    bottom_cut: int = 0


@dataclass(frozen=True)
class _ContentRowBand:
    start_row: int
    end_row: int

    @property
    def height(self) -> int:
        return self.end_row - self.start_row + 1


@dataclass(frozen=True)
class _PageCandidate:
    height: int
    header_cut: int | None
    footer_cut: int | None


class _BandKind(Enum):
    HEADER = "header"
    FOOTER = "footer"


class HeaderFooterMode(Enum):
    HEADER = "header"
    FOOTER = "footer"
    BOTH = "both"


@dataclass
class _BandDetectionThresholds:
    """
    Thresholds for deciding whether a top or bottom content band can be
    treated as a header or footer candidate.

    Attributes:
        search_boundary: Row boundary that restricts detection to the top or
            bottom 18% of the page.
        max_band_height: Maximum height allowed for a header/footer candidate band.
        min_gap: Minimum whitespace gap required between body content and the
            candidate band.
    """

    height: InitVar[int]
    kind: InitVar[_BandKind]
    search_boundary: int = field(init=False)
    max_band_height: int = field(init=False)
    min_gap: int = field(init=False)

    def __post_init__(self, height, kind) -> None:
        # Restrict detection to the top or bottom 18% of the page.
        search_margin = max(1, int(height * 0.18))
        self.search_boundary = (
            search_margin if kind is _BandKind.HEADER else height - search_margin
        )
        # If a band is taller than 12% of page height, it is probably not a
        # header or footer.
        self.max_band_height = max(1, int(height * 0.12))
        self.min_gap = max(4, int(height * 0.02))


class HeaderFooterDetector:
    def __init__(
        self,
        doc: pymupdf.Document,
        dpi: int | None,
        detect_mode: HeaderFooterMode | None,
        allow_partial_mode: HeaderFooterMode | None,
    ) -> None:
        self.doc = doc
        self.dpi = dpi
        self.detect_mode = detect_mode
        self.allow_partial_mode = allow_partial_mode

    def detect_header_footer_cuts(
        self,
        on_page_done: Callable[[], None] | None = None,
    ) -> list[HeaderFooterCuts]:
        if self.detect_mode is None:
            return [HeaderFooterCuts() for _ in range(self.doc.page_count)]

        page_candidates: list[_PageCandidate] = []
        for i in range(self.doc.page_count):
            page = self.doc.load_page(i)
            page_candidates.append(self._detect_page_candidate(page))
            if on_page_done is not None:
                on_page_done()

        if not page_candidates:
            return []

        tolerance = self._get_cut_tolerance(page_candidates)

        # The minimum number of pages that must share the same detected header
        # or footer pattern before it is recognized as document-level.
        support_threshold = max(3, ceil(self.doc.page_count * 0.4))
        header_cut = None
        if self._mode_includes_header(self.detect_mode):
            header_cut = self._get_repeated_cut(
                [candidate.header_cut for candidate in page_candidates],
                tolerance,
                support_threshold,
            )

        footer_cut = None
        if self._mode_includes_footer(self.detect_mode):
            footer_cut = self._get_repeated_cut(
                [candidate.footer_cut for candidate in page_candidates],
                tolerance,
                support_threshold,
            )

        return self._get_matching_page_cuts(
            page_candidates=page_candidates,
            repeated_header_cut=header_cut,
            repeated_footer_cut=footer_cut,
            tolerance=tolerance,
        )

    def _detect_page_candidate(self, page: pymupdf.Page) -> _PageCandidate:
        pix: pymupdf.Pixmap = (
            page.get_pixmap(dpi=self.dpi)
            if self.dpi is not None
            else page.get_pixmap()
        )  # type:ignore
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        pixels: list[tuple[int, int, int]] = list(img.getdata())
        dominant_color, _ = Counter(pixels).most_common(1)[0]

        # Limit row-activity checks to the central text area so vertical edge
        # artifacts do not make header/footer candidates look active.
        left_cut, _, right_cut, _ = get_border_cuts(pixels, img.size, dominant_color)

        # Rows with at least one pixel with non-dominant color
        active_rows = self._get_rows_with_content(
            pixels,
            img.size,
            dominant_color,
            left_cut,
            right_cut,
        )
        bands = self._get_content_row_bands(active_rows)

        header_cut = (
            self._detect_header_cut(bands, img.height)
            if self._mode_includes_header(self.detect_mode)
            else None
        )
        footer_cut = (
            self._detect_footer_cut(bands, img.height)
            if self._mode_includes_footer(self.detect_mode)
            else None
        )

        return _PageCandidate(
            height=img.height,
            header_cut=header_cut,
            footer_cut=footer_cut,
        )
    
    @staticmethod
    def _get_rows_with_content(
        pixels: list[tuple[int, int, int]],
        img_size: tuple[int, int],
        dominant_color: tuple[int, int, int],
        left_cut: int,
        right_cut: int,
    ) -> list[bool]:
        width, height = img_size
        start_col = left_cut
        end_col = width - 1 - right_cut
        if start_col > end_col:
            return [False] * height

        usable_width = end_col - start_col + 1
        min_ink = max(2, int(usable_width * 0.003))
        active_rows: list[bool] = []
        for row in range(height):
            ink = 0
            for col in range(start_col, end_col + 1):
                if pixel_at(pixels, width, row, col) != dominant_color:
                    ink += 1
            active_rows.append(ink >= min_ink)
        return active_rows

    @staticmethod
    def _get_content_row_bands(active_rows: list[bool]) -> list[_ContentRowBand]:
        """Group nearby rows with content into continuous vertical bands.

        Example:
        [False, False, True, True, True, False, False, True, True]
        becomes bands 2..4 and 7..8.

        With a tolerated one-row gap:
        [False, False, True, True, False, True, True, False, False]
        becomes one band 2..6.
        """
        bands: list[_ContentRowBand] = []
        gap_tolerance = 1
        row = 0
        last_index = len(active_rows)

        while row < last_index:
            if not active_rows[row]:
                row += 1
                continue

            start_row = row
            end_row = row
            blank_gap = 0
            row += 1
            while row < last_index:
                if active_rows[row]:
                    end_row = row
                    blank_gap = 0
                    row += 1
                    continue
                blank_gap += 1
                if blank_gap > gap_tolerance:
                    break
                row += 1

            bands.append(_ContentRowBand(start_row=start_row, end_row=end_row))
        return bands

    def _detect_header_cut(self,bands: list[_ContentRowBand], height: int) -> int | None:
        if not bands:
            return None

        thresholds = _BandDetectionThresholds(height=height, kind=_BandKind.HEADER)

        for index, band in enumerate(bands):
            if band.start_row >= thresholds.search_boundary:
                break
            if band.height > thresholds.max_band_height:
                continue

            next_band_index = self._find_next_band_index_with_gap(
                bands,
                index + 1,
                band.end_row,
                thresholds.min_gap,
            )
            if next_band_index is None:
                continue
            return bands[next_band_index - 1].end_row + 1
        return None

    @staticmethod
    def _find_next_band_index_with_gap(
        bands: list[_ContentRowBand],
        start_index: int,
        previous_end_row: int,
        min_gap: int,
    ) -> int | None:
        for index in range(start_index, len(bands)):
            band = bands[index]
            gap = band.start_row - previous_end_row - 1
            if gap >= min_gap:
                return index
        return None
    
    @staticmethod
    def _mode_includes_header(mode: HeaderFooterMode | None) -> bool:
        return mode in (HeaderFooterMode.HEADER, HeaderFooterMode.BOTH)
    
    def _detect_footer_cut(self,bands: list[_ContentRowBand], height: int) -> int | None:
        if not bands:
            return None

        thresholds = _BandDetectionThresholds(height=height, kind=_BandKind.FOOTER)

        for index in range(len(bands) - 1, -1, -1):
            band = bands[index]
            if band.end_row < thresholds.search_boundary:
                break
            if band.height > thresholds.max_band_height:
                continue

            previous_band_index = self._find_previous_band_index_with_gap(
                bands,
                index - 1,
                band.start_row,
                thresholds.min_gap,
            )
            if previous_band_index is None:
                continue
            return height - bands[previous_band_index + 1].start_row
        return None

    @staticmethod
    def _find_previous_band_index_with_gap(
        bands: list[_ContentRowBand],
        start_index: int,
        next_start_row: int,
        min_gap: int,
    ) -> int | None:
        for index in range(start_index, -1, -1):
            band = bands[index]
            gap = next_start_row - band.end_row - 1
            if gap >= min_gap:
                return index
        return None

    @staticmethod
    def _mode_includes_footer(mode: HeaderFooterMode | None) -> bool:
        return mode in (HeaderFooterMode.FOOTER, HeaderFooterMode.BOTH)
    

    @staticmethod
    def _get_repeated_cut(
        raw_cuts: list[int | None],
        tolerance: int,
        support_threshold: int,
    ) -> int | None:
        """Find the document-level cut position repeated across enough pages.

        Example:
        raw_cuts = [22, 24, 23, 90]
        tolerance = 3
        support_threshold = 3

        Clusters become roughly:
        - [22, 23, 24]
        - [90]

        The biggest cluster is [22, 23, 24], which has size 3, so the
        function returns 23.
        """
        cuts = sorted(cut for cut in raw_cuts if cut is not None)
        if not cuts:
            return None

        # groups nearby cuts into clusters using tolerance
        clusters: list[list[int]] = [[cuts[0]]]
        for cut in cuts[1:]:
            cluster = clusters[-1]
            if abs(cut - cluster[-1]) <= tolerance:
                cluster.append(cut)
                continue
            clusters.append([cut])

        # picks the largest cluster, which should container header / footer
        best_cluster = max(clusters, key=len)
        if len(best_cluster) < support_threshold:
            return None
        repeated_cut = int(round(median(data=best_cluster)))
        return repeated_cut

    @staticmethod
    def _get_cut_tolerance(page_candidates: list[_PageCandidate]) -> int:
        """Return the allowed difference between similar page cut positions.

        Example:
        header cuts at 22, 24 and 23 are close enough to be treated as the
        same repeated header pattern.
        """
        heights = [candidate.height for candidate in page_candidates]
        if not heights:
            return 4
        return max(4, int(median(heights) * 0.01))



    def _get_matching_page_cuts(
        self,
        page_candidates: list[_PageCandidate],
        repeated_header_cut: int | None,
        repeated_footer_cut: int | None,
        tolerance: int,
    ) -> list[HeaderFooterCuts]:
        """
        Return per-page cuts only for candidates matching the repeated pattern.
        Otherwise they get default value of 0.
        """
        page_cuts: list[HeaderFooterCuts] = []
        for candidate in page_candidates:
            header_matches = self._candidate_matches(
                candidate_cut=candidate.header_cut,
                repeated_cut=repeated_header_cut,
                tolerance=tolerance,
            )
            footer_matches = self._candidate_matches(
                candidate_cut=candidate.footer_cut,
                repeated_cut=repeated_footer_cut,
                tolerance=tolerance,
            )

            top_cut = 0
            if self._should_apply_header_cut(
                header_matches=header_matches,
                footer_matches=footer_matches,
                repeated_footer_cut=repeated_footer_cut,
            ):
                top_cut = candidate.header_cut or 0

            bottom_cut = 0
            if self._should_apply_footer_cut(
                header_matches=header_matches,
                footer_matches=footer_matches,
                repeated_header_cut=repeated_header_cut,
            ):
                bottom_cut = candidate.footer_cut or 0

            page_cuts.append(HeaderFooterCuts(top_cut=top_cut, bottom_cut=bottom_cut))
        return page_cuts
    
    @staticmethod
    def _candidate_matches(
        candidate_cut: int | None,
        repeated_cut: int | None,
        tolerance: int,
    ) -> bool:
        """Return whether a page-local cut matches the repeated document-level cut.

        Example:
        repeated_cut = 23, candidate_cut = 24, tolerance = 3 -> True
        repeated_cut = 23, candidate_cut = 80, tolerance = 3 -> False
        """
        if repeated_cut is None or candidate_cut is None:
            return False
        return abs(candidate_cut - repeated_cut) <= tolerance

    def _should_apply_header_cut(
        self,
        header_matches: bool,
        footer_matches: bool,
        repeated_footer_cut: int | None,
    ) -> bool:
        detect_mode = self.detect_mode
        if detect_mode is None:
            return False
        if not self._mode_includes_header(detect_mode):
            return False
        if not header_matches:
            return False
        if not self._mode_includes_footer(detect_mode):
            return True
        if repeated_footer_cut is None:
            return True
        if footer_matches:
            return True
        return self._mode_includes_header(self.allow_partial_mode)

    def _should_apply_footer_cut(
        self,
        header_matches: bool,
        footer_matches: bool,
        repeated_header_cut: int | None,
    ) -> bool:
        detect_mode = self.detect_mode
        if detect_mode is None:
            return False
        if not self._mode_includes_footer(detect_mode):
            return False
        if not footer_matches:
            return False
        if not self._mode_includes_header(detect_mode):
            return True
        if repeated_header_cut is None:
            return True
        if header_matches:
            return True
        return self._mode_includes_footer(self.allow_partial_mode)

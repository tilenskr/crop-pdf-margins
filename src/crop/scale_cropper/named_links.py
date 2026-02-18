import math
from dataclasses import dataclass
from typing import Any, Optional, Union

import pymupdf


@dataclass
class Converted:
    link: dict[str, Any]


@dataclass
class Unchanged:
    link: dict[str, Any]


@dataclass
class Invalid:
    pass


ResolveResult = Union[Converted, Unchanged, Invalid]


class NamedLinkResolver:
    """
    Converts PyMuPDF kind=4 links (named-ish internal links)
    into LINK_GOTO links without zoom.
    Supports:
      - zoom=a,b,c triplet
      - dest='/Fit' style links
      - to is present
    """

    def __init__(self, page_count: int):
        self.page_count = page_count

    def resolve(self, link: dict[str, Any]) -> ResolveResult:
        if link.get("kind") != pymupdf.LINK_NAMED:
            return Unchanged(link)

        dest_page = self._parse_page(link)
        if dest_page is None:
            return Invalid()

        point = self._point_from_explicit_to(link)

        if point is None:
            point = self._parse_zoom_triplet_point(link)

        if point is None:
            point = self._handle_fit_destination(link)

        if point is None:
            return Invalid()

        new_link = {
            "kind": pymupdf.LINK_GOTO,
            "page": dest_page,
            "to": point,
        }

        # Page links have a 'from' rectangle, TOC bookmarks do not.
        if "from" in link:
            new_link["from"] = link["from"]

        return Converted(new_link)

    def _point_from_explicit_to(self, link: dict[str, Any]) -> Optional[pymupdf.Point]:
        """
        Handle kind=4 links that already contain an explicit destination point:
        {'kind': 4, 'page': 348, 'to': Point(...), 'zoom': 0.0, 'nameddest': 'p346', ...}

        If 'to' exists and is a Point, we can convert to LINK_GOTO directly.
        We ignore 'zoom' on purpose.
        """
        to = link.get("to")
        if isinstance(to, pymupdf.Point):
            return to

        # Sometimes 'to' might come as a tuple/list
        if isinstance(to, (tuple, list)) and len(to) == 2:
            x, y = to
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                return pymupdf.Point(float(x), float(y))

        return None

    def _parse_page(self, link: dict[str, Any]) -> Optional[int]:
        """
        Return a 0-based destination page index for a PyMuPDF link dict.

        Practical rule based on real PyMuPDF outputs:
        - if link["page"] is int -> treat as already 0-based
        - if link["page"] is str digits -> treat as 1-based and subtract 1

        Returns None if missing / invalid / out of range.
        """
        page = link.get("page")

        if isinstance(page, int):
            p0 = page

        elif isinstance(page, str):
            s = page.strip()
            if not s.isdigit():
                return None
            p = int(s)
            if p <= 0:  # 1-based pages can't be 0 or negative
                return None
            p0 = p - 1

        else:
            return None

        if 0 <= p0 < self.page_count:
            return p0
        return None

    def _parse_zoom_triplet_point(
        self, link: dict[str, Any]
    ) -> Optional[pymupdf.Point]:
        """
        Parse MuPDF-style 'zoom=a,b,c' triplet used in Link.uri / Page.get_links().

        We want a destination POINT (x,y) and we IGNORE zoom.
        Heuristic:
        - x comes from slot 1 (a) if present
        - y comes from slot 2 (b) if present
        - if b is NaN/None, but slot 3 (c) looks like a plausible y (0..page_height),
            treat c as y (this matches your observation).
        """
        zoom = link.get("zoom")
        if not isinstance(zoom, str):
            return None

        parts = [p.strip() for p in zoom.split(",")]

        a = self._parse_float(parts[0]) if len(parts) >= 1 else None
        b = self._parse_float(parts[1]) if len(parts) >= 2 else None
        c = self._parse_float(parts[2]) if len(parts) >= 3 else None

        if a is not None and math.isnan(a):
            a = None
        if b is not None and math.isnan(b):
            b = None
        if c is not None and math.isnan(c):
            c = None

        x = a if a is not None else 0.0

        if b is not None:
            return pymupdf.Point(x, b)
        if c is not None:
            return pymupdf.Point(x, c)

        return pymupdf.Point(x, 0.0)

    def _handle_fit_destination(self, link: dict[str, Any]) -> Optional[pymupdf.Point]:
        """
        Handle link dicts like:
        {'kind': 4, 'page': 23, 'dest': '/Fit', 'nameddest': '...', 'from': Rect(...)}

        /Fit has no (x,y). We preserve navigation by converting to LINK_GOTO
        targeting the top of the destination page and do NOT set zoom.
        """
        dest = link.get("dest")

        if dest in ("/Fit", "/FitB", "/FitH", "/FitV", "/FitBH", "/FitBV"):
            # Fit modes do not provide coordinates.
            # We choose top-of-page.
            return pymupdf.Point(0.0, 0.0)

        return None

    @staticmethod
    def _parse_float(s: str) -> Optional[float]:
        try:
            return float(s)
        except Exception:
            return None

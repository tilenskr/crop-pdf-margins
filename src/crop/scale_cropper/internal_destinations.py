import logging
import math
import re
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


class InternalDestinationResolver:
    """
    Converts PyMuPDF kind=4 links (named-ish internal links)
    into LINK_GOTO links without zoom.
    Supports:
      - zoom=a,b,c triplet
      - dest='/Fit' style links
      - to is present
    """

    def __init__(self, src_doc: pymupdf.Document, page_count: int):
        self._src_doc = src_doc
        self.page_count = page_count

    def resolve(self, link: dict[str, Any]) -> ResolveResult:
        if link.get("kind") != pymupdf.LINK_NAMED:
            return Unchanged(link)

        dest_page = self._parse_page(link)
        if dest_page is None:
            return Invalid()
        
        point = self._resolve_point(link, dest_page)

        if point is None:
            logging.warning(
                "Could not resolve internal destination point; converting to page-only LINK_GOTO. Full link dict: %r",
                link,
            )
            new_link = dict(link)
            new_link["kind"] = pymupdf.LINK_GOTO
            new_link["page"] = dest_page
            return Converted(new_link)

        new_link = {
            "kind": pymupdf.LINK_GOTO,
            "page": dest_page,
            "to": point,
            "xref": link["xref"],
        }

        # Page links have a 'from' rectangle, TOC bookmarks do not.
        if "from" in link:
            new_link["from"] = link["from"]

        return Converted(new_link)

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

    def _resolve_point(
        self, link: dict[str, Any], dest_page: int
    ) -> Optional[pymupdf.Point]:
        return (
            self._point_from_explicit_to(link)
            or self._parse_zoom_triplet_point(link)
            or self._handle_fit_destination(link)
            or self._point_from_outline_xref_dest(link, dest_page)
        )

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

        view = link.get("view")
        if view == "Fit":
            return pymupdf.Point(0.0, 0.0)

        return None

    @staticmethod
    def _parse_float(s: str) -> Optional[float]:
        try:
            return float(s)
        except Exception:
            return None

    def _point_from_outline_xref_dest(
        self, link: dict[str, Any], dest_page: int
    ) -> Optional[pymupdf.Point]:
        """
        Fallback for TOC/bookmark entries from get_toc(simple=False) that have an xref but
        no usable 'to'/'zoom'/'dest' fields.

        Reads the raw outline object and parses /Dest [ ... ].
        Supports common forms:
        /Dest [ <page_xref> 0 R /XYZ left top zoom ]
        /Dest [ <page_xref> 0 R /Fit* ... ]
        """
        xref = link.get("xref")
        if not isinstance(xref, int) or xref <= 0:
            return None

        try:
            raw = self._src_doc.xref_object(xref)
        except Exception:
            return None

        # Extract /Dest [ ... ]
        m = re.search(r"/Dest\s*\[(.*?)\]", raw, re.DOTALL)
        if not m:
            return None

        dest_content = m.group(1).strip()
        return self._parse_raw_dest_array_point(dest_content, link, dest_page)

    def _parse_raw_dest_array_point(
        self, dest_content: str, link: dict[str, Any], dest_page: int
    ) -> Optional[pymupdf.Point]:
        """
        Parse a raw PDF dest array content string (inside [ ... ]) and return a Point only.

        Example input:
        '532 0 R /XYZ null 310.6724 null'
        """
        tokens = dest_content.split()
        # Need at least: <xref> 0 R <mode>
        if len(tokens) < 4:
            return None

        mode = tokens[3]

        if mode == "/XYZ":
            # /XYZ left top zoom
            if len(tokens) < 7:
                return None
            x = self._parse_float(tokens[4])
            top_pdf = self._parse_float(tokens[5])  # PDF 'top'
            x_val = 0.0 if x is None else x
            # zoom = tokens[6] ignored

            if top_pdf is None:
                return pymupdf.Point(x_val, 0.0)

            # when converting to PyMuPDF page coordinates, you usually need to flip Y
            page_height = self._src_doc[dest_page].rect.height
            y_mupdf = page_height - top_pdf

            return pymupdf.Point(x_val, y_mupdf)

        if mode in ("/Fit", "/FitB", "/FitH", "/FitV", "/FitBH", "/FitBV"):
            return pymupdf.Point(0.0, 0.0)

        logging.warning(
            "Unhandled PDF destination mode in outline /Dest array; cannot extract point. "
            "mode=%r raw_dest=%r full link dict=%r",
            mode,
            dest_content,
            link,
        )
        return None

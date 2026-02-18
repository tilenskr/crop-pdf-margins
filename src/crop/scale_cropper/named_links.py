from __future__ import annotations

from typing import Any, Mapping, Optional
import math
import pymupdf


def convert_named_link_to_goto(link: dict[str, Any]) -> Optional[dict[str, Any]]:
    """
    Convert MuPDF/PyMuPDF kind=4 'named' links that encode destinations like:
      page=12&zoom=0,nan,72
    """

    dest_page = _get_page(link)
    if dest_page is None:
        return None

    to = _parse_zoom_triplet_point(link)
    if to[0] is None and to[1] is None:
        return None
    out: dict[str, Any] = {
        "kind": pymupdf.LINK_GOTO,
        "from": link.get("from"),
        "page": dest_page - 1,
        "to": pymupdf.Point(to[0], to[1]),
    }

    return out

def _get_page(link: dict[str, Any]): 
    page = link.get("page")
    if isinstance(page, str) and page.strip().isdigit():
        return int(page.strip())
    else: 
        return None

def _parse_zoom_triplet_point(link: Mapping[str, Any],) -> tuple[Optional[float], Optional[float]]:
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
        return (None, None)

    parts = [p.strip() for p in zoom.split(",")]
    a = _parse_float_or_none(parts[0]) if len(parts) >= 1 else None
    b = _parse_float_or_none(parts[1]) if len(parts) >= 2 else None
    c = _parse_float_or_none(parts[2]) if len(parts) >= 3 else None

    if a is not None and math.isnan(a):
        a = None
    if b is not None and math.isnan(b):
        b = None
    if c is not None and math.isnan(c):
        c = None

    x = a if a is not None else 0.0

    if b is not None:
        return (x, b)

    if c is not None:
        return (x, c)

    return (x, 0.0)


def _parse_float_or_none(s: str) -> Optional[float]:
    try:
        return float(s)
    except Exception:
        return None

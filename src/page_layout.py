from dataclasses import dataclass

import pymupdf


@dataclass(frozen=True, slots=True)
class PageCropLayout:
    # full original page
    page_rect: pymupdf.Rect
    # detected real content
    content_rect: pymupdf.Rect
    # content plus border, for box
    visible_rect: pymupdf.Rect
    # inset area where scaled content should be drawn, for scale
    destination_rect: pymupdf.Rect

from abc import ABC, abstractmethod

import pymupdf

from borders import FourBorders
from page_layout import PageCropLayout
from .border_adjuster import BorderAdjuster


class BoundsExtractor(ABC):
    def __init__(self, borders: FourBorders):
        self._border_adjuster = BorderAdjuster(borders)

    @abstractmethod
    def get_bounds(
        self, doc: pymupdf.Document, dpi: int | None
    ) -> list[PageCropLayout]:
        pass

    def _get_layout(
        self,
        bounds: pymupdf.Rect,
        has_content: bool,
        page_rect: pymupdf.Rect,
    ) -> PageCropLayout:
        if has_content:
            return self._border_adjuster.create_layout(bounds, page_rect)

        # Keep blank pages unchanged regardless of padding settings.
        return PageCropLayout(
            page_rect=page_rect,
            content_rect=page_rect,
            visible_rect=page_rect,
            destination_rect=page_rect,
        )


# def process_pdf(filename: str):
#     doc = fitz.open(file_name)  # open document


#     for page in doc:  # iterate through the pages
#         pix = page.getPixmap(...)  # render page to an image
#         pix.writePNG("page-%i.png" % page.number)  # store image as a PNG

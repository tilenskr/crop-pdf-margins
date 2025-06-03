from abc import ABC, abstractmethod

import pymupdf

from borders import BorderSpec
from bounds.border_adjuster import get_border_adjuster


class BoundsExtractor(ABC):
    def __init__(self, border: BorderSpec):
        self._border_adjuster = get_border_adjuster(border)

    @abstractmethod
    def get_bounds(self, doc: pymupdf.Document) -> list[pymupdf.Rect]:
        pass

    def _get_rectangle(
        self,
        bounds: pymupdf.Rect,
        has_content: bool,
        page_rect: pymupdf.Rect,
    ) -> pymupdf.Rect:
        if has_content:
            return self._border_adjuster.adjust_bounds(bounds, page_rect)
        else:
            # handle empty pages
            return pymupdf.Rect(0, 0, page_rect.width, page_rect.height)


# def process_pdf(filename: str):
#     doc = fitz.open(file_name)  # open document


#     for page in doc:  # iterate through the pages
#         pix = page.getPixmap(...)  # render page to an image
#         pix.writePNG("page-%i.png" % page.number)  # store image as a PNG

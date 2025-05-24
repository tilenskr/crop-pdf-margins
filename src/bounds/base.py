from abc import ABC, abstractmethod

import pymupdf


class BoundsExtractor(ABC):
    def __init__(self, border_pt: float = 0):
        self._border_pt = border_pt

    @abstractmethod
    def get_bounds(self, doc: pymupdf.Document) -> list[pymupdf.Rect]:
        pass

    def _get_rectangle(
        self,
        *,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        has_content: bool,
        page_rect: pymupdf.Rect,
    ) -> pymupdf.Rect:
        if has_content:
            rect = pymupdf.Rect(
                x0 - self._border_pt,
                y0 - self._border_pt,
                x1 + self._border_pt,
                y1 + self._border_pt,
            )
            return rect
        else:
            # handle empty pages
            return pymupdf.Rect(0, 0, page_rect.width, page_rect.height)


# def process_pdf(filename: str):
#     doc = fitz.open(file_name)  # open document


#     for page in doc:  # iterate through the pages
#         pix = page.getPixmap(...)  # render page to an image
#         pix.writePNG("page-%i.png" % page.number)  # store image as a PNG

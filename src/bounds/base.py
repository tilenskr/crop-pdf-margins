from abc import ABC, abstractmethod

import pymupdf


class BoundsExtractor(ABC):
    def __init__(self, border_pt: float = 0):
        self._border_pt = border_pt

    @abstractmethod
    def get_bounds(self, doc: pymupdf.Document) -> list[pymupdf.Rect]:
        pass


# def process_pdf(filename: str):
#     doc = fitz.open(file_name)  # open document


#     for page in doc:  # iterate through the pages
#         pix = page.getPixmap(...)  # render page to an image
#         pix.writePNG("page-%i.png" % page.number)  # store image as a PNG


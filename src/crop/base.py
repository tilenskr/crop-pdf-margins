from abc import ABC, abstractmethod
from typing import Sequence

import pymupdf
from page_layout import PageCropLayout


class Cropper(ABC):
    def __init__(self, doc: pymupdf.Document):
        self._doc = doc

    @abstractmethod
    def crop(self, bounds: Sequence[PageCropLayout]) -> pymupdf.Document:
        pass

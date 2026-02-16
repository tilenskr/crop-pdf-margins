from abc import ABC, abstractmethod
from typing import Sequence

import pymupdf


class Cropper(ABC):
    def __init__(self, doc: pymupdf.Document):
        self._doc = doc

    @abstractmethod
    def crop(self, bounds: Sequence[pymupdf.Rect]) -> pymupdf.Document:
        pass

from abc import ABC, abstractmethod

import pymupdf


class Cropper(ABC):
    def __init__(self, doc: pymupdf.Document):
        self._doc = doc

    @abstractmethod
    def crop(self,  bounds: list[pymupdf.Rect]) -> pymupdf.Document:
        pass

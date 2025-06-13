from typing import override

import pymupdf

from crop.base import Cropper


class BoxCropper(Cropper):
    """Crop each page by setting its CropBox to the computed bounds,
    without scaling the content."""

    @override
    def crop(self, bounds: list[pymupdf.Rect]) -> pymupdf.Document:
        for page_index, rect in enumerate(bounds):
            page = self._doc[page_index]
            page.set_cropbox(rect)
        return self._doc

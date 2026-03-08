from collections.abc import Sequence
from typing import override

import pymupdf
from page_layout import PageCropLayout

from .base import Cropper


class BoxCropper(Cropper):
    """Crop each page by setting its CropBox to the computed bounds,
    without scaling the content."""

    @override
    def crop(self, bounds: Sequence[PageCropLayout]) -> pymupdf.Document:
        for page_index, layout in enumerate(bounds):
            page = self._doc[page_index]
            page.set_cropbox(layout.visible_rect)
        return self._doc

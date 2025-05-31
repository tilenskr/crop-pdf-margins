from typing import override

import pymupdf

from crop.base import Cropper


class ScaleCropper(Cropper):
    @override
    def crop(self, bounds: list[pymupdf.Rect]) -> pymupdf.Document:
        output_doc: pymupdf.Document = pymupdf.open()
        for page_num, clipped_rect in enumerate(bounds):
            src_page = self._doc[page_num]
            width, height = src_page.rect.width, src_page.rect.height
            new_page: pymupdf.Page = output_doc.new_page(width=width, height=height)  # type: ignore[reportUnknownMemberType]

            # draw clipped area into full page
            new_page.show_pdf_page(  # type: ignore[reportUnknownMemberType]
                pymupdf.Rect(0, 0, width, height),
                self._doc,
                page_num,
                clip=clipped_rect,
            )
        return output_doc

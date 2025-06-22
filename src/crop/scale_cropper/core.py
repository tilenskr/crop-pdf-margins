import warnings
from typing import override

import pymupdf

from ..base import Cropper


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
        self._copy_properties(output_doc)
        return output_doc

    def _copy_properties(self, dst: pymupdf.Document):
        self._copy_metadata(dst)
        self._copy_page_labels(dst)
        self._copy_table_of_contents(dst)
        self._copy_attachments(dst)
        self._copy_optional_content_groups(dst)

    def _copy_metadata(self, dst: pymupdf.Document):
        """Copy basic metadata (Title, Author, etc.)."""
        dst.set_metadata(self._doc.metadata)  # type: ignore

    def _copy_page_labels(self, dst: pymupdf.Document):
        """Copy page labels."""
        labels = self._doc.get_page_labels()  # type: ignore
        if labels:
            dst.set_page_labels(labels)  # type:ignore

    def _copy_table_of_contents(self, dst: pymupdf.Document):
        """Copy able-of-Contents / outlines (bookmarks)."""
        toc = self._doc.get_toc(simple=False)  # type:ignore
        if toc:
            dst.set_toc(toc)  # type:ignore

    def _copy_attachments(self, dst: pymupdf.Document):
        """Copy embedded files / attachments."""
        for name in self._doc.embfile_names():
            info = self._doc.embfile_info(name)  # a dict of metadata
            data = self._doc.embfile_get(name)  # raw bytes
            dst.embfile_add(
                name,
                data,
                info["filename"],
                ufilename=info["ufilename"],
                desc=info["description"],
            )

    def _copy_optional_content_groups(self, dst: pymupdf.Document):
        """Copy Optional Content Groups (layers)."""
        ocgs = self._doc.get_ocgs()  # list of dicts
        if len(ocgs) > 0:
            warnings.warn("Ocgs (Optional Content Groups) are not yet supported.")
            # ocmd = src.get_ocmd()       # list of on/off commands
            # dst.set_ocgs(ocgs)
            # dst.set_ocmd(ocmd)

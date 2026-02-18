from collections.abc import Sequence
import warnings
from typing import Any, override

import pymupdf

from crop.scale_cropper.links import copy_links, transform_link_destination
from crop.scale_cropper.named_links import NamedLinkResolver

from ..base import Cropper
from .annotations import copy_annotations


class ScaleCropper(Cropper):
    @override
    def crop(self, bounds: Sequence[pymupdf.Rect]) -> pymupdf.Document:
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
        self._copy_properties(bounds, output_doc)
        return output_doc

    def _copy_properties(
        self, page_bounds: Sequence[pymupdf.Rect], dst: pymupdf.Document
    ):
        self._copy_metadata(dst)
        self._copy_page_labels(dst)
        self._copy_table_of_contents(dst, page_bounds)
        self._copy_attachments(dst)
        self._copy_optional_content_groups(dst)
        copy_annotations(self._doc, page_bounds, dst)
        copy_links(self._doc, page_bounds, dst)

    def _copy_metadata(self, dst: pymupdf.Document):
        """Copy basic metadata (Title, Author, etc.)."""
        dst.set_metadata(self._doc.metadata)  # type: ignore

    def _copy_page_labels(self, dst: pymupdf.Document):
        """Copy page labels."""
        labels = self._doc.get_page_labels()  # type: ignore
        if labels:
            dst.set_page_labels(labels)  # type:ignore

    def _copy_table_of_contents(
        self, dst: pymupdf.Document, page_bounds: Sequence[pymupdf.Rect]
    ):
        """Copy able-of-Contents / outlines (bookmarks)."""
        toc = self._doc.get_toc(simple=False)  # type:ignore
        if not toc:
            return

        resolver = NamedLinkResolver(dst.page_count)
        new_toc: list[list[Any]] = []
        for lvl, title, page, dest in toc:
            transformed_dest = transform_link_destination(
                dest, dst, page_bounds, resolver
            )
            if transformed_dest:
                new_toc.append([lvl, title, page, transformed_dest])
            else:
                new_toc.append([lvl, title, page, dest])

        dst.set_toc(new_toc)  # type:ignore

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

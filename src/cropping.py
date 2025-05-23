import pymupdf


def crop_and_scale(
    src_doc: pymupdf.Document, bounds: list[pymupdf.Rect]
) -> pymupdf.Document:
    """Return a new Document with each page trimmed & scaled to fill."""
    output_doc: pymupdf.Document = pymupdf.open()
    for page_num, clipped_rect in enumerate(bounds):
        src_page = src_doc[page_num]
        width, height = src_page.rect.width, src_page.rect.height
        new_page: pymupdf.Page = output_doc.new_page(width=width, height=height)  # type: ignore[reportUnknownMemberType]

        # draw clipped area into full page 
        new_page.show_pdf_page(  # type: ignore[reportUnknownMemberType]
            pymupdf.Rect(0, 0, width, height), src_doc, page_num, clip=clipped_rect
        )
    return output_doc


# todo add here method to override the current pdf and save it to the file cuz we have losed all the metadata
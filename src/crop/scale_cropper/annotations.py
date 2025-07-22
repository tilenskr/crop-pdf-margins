from typing import Optional
import warnings
import pymupdf

from .annotations_fonts import extract_font_info

from .constants import AnnotType 


def copy_annotations(src: pymupdf.Document, dst: pymupdf.Document):
    xref_map: dict[int, int] = {}
    for page_num in range(src.page_count):
        src_page = src[page_num]
        dst_page = dst[page_num]
        if not src_page.annots():
            continue

        for src_annotation in src_page.annots():
            # r = src_annotation.rect
            annotation_type = AnnotType(src_annotation.type[0])

            try:
                dst_annotation = get_annotation(src, src_annotation, annotation_type, dst_page)
                if not dst_annotation:
                    warnings.warn(f"Unsupported annotation type ({annotation_type.name}) on page {page_num + 1}. Skipping.")
                    continue
            except Exception as e:
                warnings.warn(f"Error copying annotation ({annotation_type.name}) on page {page_num + 1}: {e}")
                continue

            xref_map[src_annotation.xref] = dst_annotation.xref

            dst_annotation.set_info(src_annotation.info)
            dst_annotation.set_border(src_annotation.border)
            if src_annotation.blendmode is not None:
                dst_annotation.set_blendmode(src_annotation.blendmode)
            if annotation_type != AnnotType.PDF_ANNOT_FREE_TEXT:
                dst_annotation.set_colors(src_annotation.colors)
            dst_annotation.set_flags(src_annotation.flags)
            if src_annotation.irt_xref != 0:
                dst_annotation.set_irt_xref(xref_map[src_annotation.irt_xref])
            if src_annotation.line_ends is not None:
                dst_annotation.set_line_ends(src_annotation.line_ends[0], src_annotation.line_ends[1])
            dst_annotation.set_name(src_annotation.info["name"])
            dst_annotation.set_oc(src_annotation.get_oc())
            dst_annotation.set_opacity(src_annotation.opacity)
            dst_annotation.set_open(src_annotation.is_open)
            dst_annotation.set_popup(src_annotation.popup_rect)
            dst_annotation.set_rect(src_annotation.rect)
            dst_annotation.set_rotation(src_annotation.rotation)
            dst_annotation.update()

def get_annotation(src_document: pymupdf.Document, src_annotation: pymupdf.Annot, 
                   annotation_type: AnnotType, dst_page: pymupdf.Page) -> Optional[pymupdf.Annot]:
    match annotation_type:
        case AnnotType.PDF_ANNOT_CARET:
            return dst_page.add_caret_annot(src_annotation.rect.tl)
        case AnnotType.PDF_ANNOT_TEXT:
            return dst_page.add_text_annot(
                src_annotation.rect.tl,
                src_annotation.info["content"],
                src_annotation.info["name"],
            )
        case AnnotType.PDF_ANNOT_FREE_TEXT:
            free_text_info = extract_font_info(src_document, src_annotation)
            return dst_page.add_freetext_annot(
                src_annotation.rect,
                free_text_info.text,
                
                fontsize=free_text_info.font_size,
                fontname=free_text_info.font_name,
                text_color=free_text_info.text_color,
                fill_color=free_text_info.fill_color,
                border_color=free_text_info.border_color,
                border_width=free_text_info.border_width,
                dashes=free_text_info.dashes,
                callout=free_text_info.callout,
                line_end=free_text_info.line_end,
                opacity=free_text_info.opacity,
                align=free_text_info.align,
                rotate=free_text_info.rotate,
                richtext=free_text_info.richtext,
            )
        case AnnotType.PDF_ANNOT_FILE_ATTACHMENT:
            try:
                src_filename = src_annotation.file_info["filename"]
            except Exception:
                src_filename = "attachment"
            return dst_page.add_file_annot(
                src_annotation.rect.tl,
                src_annotation.get_file(),
                src_filename,
                src_annotation.file_info.get("ufilename", src_filename),
                src_annotation.file_info["description"],
                src_annotation.info["name"],
            )

        case _:
            return None
        

           # elif a_type == PDF_ANNOT_LINE:
            #     # add_line_annot(p1, p2)
            #     p1, p2 = verts[0], verts[-1] if verts else (r.tl, r.br)
            #     dst_annotation = dst_page.add_line_annot(p1, p2)

            # elif a_type == PDF_ANNOT_SQUARE:
            #     # add_rect_annot(rect)
            #     dst_annotation = dst_page.add_rect_annot(r)

            # elif a_type == PDF_ANNOT_CIRCLE:
            #     # add_circle_annot(rect)
            #     dst_annotation = dst_page.add_circle_annot(r)

            # elif a_type == PDF_ANNOT_POLYGON:
            #     # add_polygon_annot(points)
            #     dst_annotation = dst_page.add_polygon_annot(verts or [])

            # elif a_type == PDF_ANNOT_POLY_LINE:
            #     # add_polyline_annot(points)
            #     dst_annotation = dst_page.add_polyline_annot(verts or [])

            # elif a_type == PDF_ANNOT_HIGHLIGHT:
            #     # add_highlight_annot(quads)
            #     quads = getattr(src_annotation, "quads", None) or [r]
            #     dst_annotation = dst_page.add_highlight_annot(quads)

            # elif a_type == PDF_ANNOT_UNDERLINE:
            #     # add_underline_annot(quads)
            #     quads = getattr(src_annotation, "quads", None) or [r]
            #     dst_annotation = dst_page.add_underline_annot(quads)

            # elif a_type == PDF_ANNOT_SQUIGGLY:
            #     # add_squiggly_annot(quads)
            #     quads = getattr(src_annotation, "quads", None) or [r]
            #     dst_annotation = dst_page.add_squiggly_annot(quads)

            # elif a_type == PDF_ANNOT_STRIKE_OUT:
            #     # add_strikeout_annot(quads)
            #     quads = getattr(src_annotation, "quads", None) or [r]
            #     dst_annotation = dst_page.add_strikeout_annot(quads)

            # elif a_type == PDF_ANNOT_REDACT:
            #     # add_redact_annot(quad, …)
            #     quad = getattr(src_annotation, "quad_points", r)
            #     dst_annotation = dst_page.add_redact_annot(
            #         quad,
            #         text=content,
            #         fontname=src_annotation.set_info.get("fontname", None),
            #         fontsize=src_annotation.set_info.get("fontsize", 11),
            #         align=src_annotation.set_info.get("align", TEXT_ALIGN_LEFT),
            #         fill=colors.get("fill", (1,1,1)),
            #         text_color=colors.get("stroke", (0,0,0)),
            #         cross_out=src_annotation.set_info.get("cross_out", True),
            #     )

            # elif a_type == PDF_ANNOT_STAMP:
            #     # add_stamp_annot(rect, stamp=0)
            #     stamp = getattr(src_annotation, "stamp", 0)
            #     dst_annotation = dst_page.add_stamp_annot(r, stamp=stamp)

            # elif a_type == PDF_ANNOT_FILE_ATTACHMENT:
            #     # add_file_annot(pos, buffer, filename, ufilename=None, desc=None, icon='PushPin')
            #     fname = src_annotation.set_info.get("filename", "attachment")
            #     data  = src_page.parent.embfile_get(fname)
            #     dst_annotation = dst_page.add_file_annot(r.tl, data, filename=fname,
            #                                 ufilename=src_annotation.set_info.get("ufilename"),
            #                                 desc=src_annotation.set_info.get("desc"),
            #                                 icon=src_annotation.set_info.get("icon", "PushPin"))

            # elif a_type == PDF_ANNOT_INK:
            #     # add_ink_annot(list_of_point_lists)
            #     dst_annotation = dst_page.add_ink_annot(verts or [])

            # elif a_type == PDF_ANNOT_POPUP:
            #     # add_popup_annot(rect)
            #     dst_annotation = dst_page.add_popup_annot(r)

            # elif a_type == PDF_ANNOT_LINK:
            #     # add_link(rect=..., uri=..., dest=...)
            #     dst_annotation = dst_page.add_link(rect=r, uri=getattr(src_annotation, "uri", None),
            #                             dest=getattr(src_annotation, "dest", None))

            # elif a_type == PDF_ANNOT_WIDGET:
            #     # form‐field widgets are complex; skip or handle separately
            #     continue

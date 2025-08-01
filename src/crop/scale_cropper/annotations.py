from dataclasses import dataclass
import logging
from typing import Callable, Optional
import pymupdf

from .annotations_fonts import extract_font_info

from .constants import AnnotType

ANNOT_TYPES_WITHOUT_RECT_PROPERTY = {
    AnnotType.PDF_ANNOT_INK,
    AnnotType.PDF_ANNOT_LINE,
    AnnotType.PDF_ANNOT_POLY_LINE,  # Not tested, because is not available in Adobe Acrobat Reader free version
    AnnotType.PDF_ANNOT_POLYGON,
    AnnotType.PDF_ANNOT_UNDERLINE,
    AnnotType.PDF_ANNOT_STRIKE_OUT,
    AnnotType.PDF_ANNOT_SQUIGGLY,  # Not tested, because is not available in Adobe Acrobat Reader free version
    AnnotType.PDF_ANNOT_HIGHLIGHT,
}


@dataclass(frozen=True, slots=True)
class AnnotationInfo:
    type: AnnotType
    page_num: int
    vertices: Optional[list[float]]


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
                dst_annotation = get_annotation(
                    src, src_annotation, annotation_type, dst_page
                )
                if not dst_annotation:
                    logging.warning(
                        f"Unsupported annotation type ({annotation_type.name}) on page {page_num + 1}. Skipping."
                    )
                    continue
            except Exception as e:
                logging.error(
                    f"Error copying annotation ({annotation_type.name}) on page {page_num + 1}: {e}"
                )
                continue

            xref_map[src_annotation.xref] = dst_annotation.xref

            dst_annotation.set_info(src_annotation.info)
            if dst_annotation.border:
                dst_annotation.set_border(src_annotation.border)
            if src_annotation.blendmode is not None:
                dst_annotation.set_blendmode(src_annotation.blendmode)
            if annotation_type != AnnotType.PDF_ANNOT_FREE_TEXT:
                dst_annotation.set_colors(src_annotation.colors)
            dst_annotation.set_flags(src_annotation.flags)
            if src_annotation.irt_xref != 0:
                dst_annotation.set_irt_xref(xref_map[src_annotation.irt_xref])
            if src_annotation.line_ends is not None:
                dst_annotation.set_line_ends(
                    src_annotation.line_ends[0], src_annotation.line_ends[1]
                )
            dst_annotation.set_name(src_annotation.info["name"])
            dst_annotation.set_oc(src_annotation.get_oc())
            dst_annotation.set_opacity(src_annotation.opacity)
            dst_annotation.set_open(src_annotation.is_open)
            dst_annotation.set_popup(src_annotation.popup_rect)
            if annotation_type not in ANNOT_TYPES_WITHOUT_RECT_PROPERTY:
                dst_annotation.set_rect(src_annotation.rect)
            dst_annotation.set_rotation(src_annotation.rotation)
            dst_annotation.update()


def get_annotation(
    src_document: pymupdf.Document,
    src_annotation: pymupdf.Annot,
    annotation_type: AnnotType,
    dst_page: pymupdf.Page,
) -> Optional[pymupdf.Annot]:
    assert dst_page.number is not None
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
        case AnnotType.PDF_ANNOT_INK:
            return get_annotation_with_vertices(
                AnnotationInfo(
                    annotation_type, dst_page.number, src_annotation.vertices
                ),
                dst_page.add_ink_annot,
            )
        case AnnotType.PDF_ANNOT_LINE:
            if (
                vertices := get_valid_vertices(
                    AnnotationInfo(
                        annotation_type,
                        dst_page.number,
                        src_annotation.vertices,
                    )
                )
            ) is None:
                return None
            return dst_page.add_line_annot(vertices[0], vertices[1])
        case AnnotType.PDF_ANNOT_SQUARE:
            return dst_page.add_rect_annot(src_annotation.rect)
        case AnnotType.PDF_ANNOT_CIRCLE:
            return dst_page.add_circle_annot(src_annotation.rect)
        case AnnotType.PDF_ANNOT_REDACT:
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
            return None
        case AnnotType.PDF_ANNOT_POLY_LINE:
            return get_annotation_with_vertices(
                AnnotationInfo(
                    annotation_type, dst_page.number, src_annotation.vertices
                ),
                dst_page.add_polyline_annot,
            )
        case AnnotType.PDF_ANNOT_POLYGON:
            return get_annotation_with_vertices(
                AnnotationInfo(
                    annotation_type, dst_page.number, src_annotation.vertices
                ),
                dst_page.add_polygon_annot,
            )
        case AnnotType.PDF_ANNOT_UNDERLINE:
            return get_annotation_with_quads(
                AnnotationInfo(
                    annotation_type, dst_page.number, src_annotation.vertices
                ),
                dst_page.add_underline_annot,
            )
        case AnnotType.PDF_ANNOT_STRIKE_OUT:
            return get_annotation_with_quads(
                AnnotationInfo(
                    annotation_type, dst_page.number, src_annotation.vertices
                ),
                dst_page.add_strikeout_annot,
            )
        case AnnotType.PDF_ANNOT_SQUIGGLY:
            return get_annotation_with_quads(
                AnnotationInfo(
                    annotation_type, dst_page.number, src_annotation.vertices
                ),
                dst_page.add_squiggly_annot,
            )
        case AnnotType.PDF_ANNOT_HIGHLIGHT:
            return get_annotation_with_quads(
                AnnotationInfo(
                    annotation_type, dst_page.number, src_annotation.vertices
                ),
                dst_page.add_highlight_annot,
            )
        case AnnotType.PDF_ANNOT_STAMP:
                # m = pymupdf.Matrix(1, 1)
                # pix = src_document[dst_page.number].get_pixmap(clip=src_annotation.rect, matrix=m, alpha=True)
                pix = src_annotation.get_pixmap(alpha=True)
                return dst_page.add_stamp_annot(src_annotation.rect, stamp=pix)
        case _:
            return None


def get_annotation_with_vertices(
    annotation_info: AnnotationInfo,
    add_annotation: Callable[[list[float]], pymupdf.Annot],
) -> Optional[pymupdf.Annot]:
    if (vertices := get_valid_vertices(annotation_info)) is None:
        return None
    return add_annotation(vertices)


def get_valid_vertices(info: AnnotationInfo) -> Optional[list[float]]:
    if info.vertices is None:
        logging.error(
            f"{info.type} on page {info.page_num} annotation has no vertices, skipping."
        )
        return None
    return info.vertices


def get_annotation_with_quads(
    annotation_info: AnnotationInfo,
    add_annotation: Callable[[list[pymupdf.Quad]], pymupdf.Annot],
) -> Optional[pymupdf.Annot]:
    if (vertices := get_valid_vertices(annotation_info)) is None:
        return None
    quads = [vertices[i : i + 4] for i in range(0, len(vertices), 4)]
    pymupdf_quads = [pymupdf.Quad(quad) for quad in quads]
    return add_annotation(pymupdf_quads)

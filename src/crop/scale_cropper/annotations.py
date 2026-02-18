from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Callable, Optional

import pymupdf

from .annotations_fonts import (extract_font_info,
                                extract_text_style_from_appearance)
from .constants import AnnotType
from .coordinate_transformer import CoordinateTransformer

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
    vertices: Optional[list[Any]]


@dataclass(frozen=True, slots=True)
class AnnotationContext:
    src_document: pymupdf.Document
    src_annotation: pymupdf.Annot
    annotation_type: AnnotType
    dst_page: pymupdf.Page
    new_rect: pymupdf.Rect
    coordinate_transformer: CoordinateTransformer


def copy_annotations(
    src: pymupdf.Document,
    src_page_bounds: Sequence[pymupdf.Rect],
    dst: pymupdf.Document,
):
    xref_map: dict[int, int] = {}
    for page_num in range(src.page_count):
        src_page = src[page_num]
        dst_page = dst[page_num]
        if not src_page.annots():
            continue

        coordinate_transformer = CoordinateTransformer(
            src_page_bounds[page_num], dst_page.rect.width, dst_page.rect.height
        )

        for src_annotation in src_page.annots():
            annotation_type = AnnotType(src_annotation.type[0])
            new_rect = coordinate_transformer.transform_rect(src_annotation.rect)
            try:
                annotation_context = AnnotationContext(
                    src_document=src,
                    src_annotation=src_annotation,
                    annotation_type=annotation_type,
                    dst_page=dst_page,
                    new_rect=new_rect,
                    coordinate_transformer=coordinate_transformer,
                )
                dst_annotation = get_annotation(annotation_context)
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
            if dst_annotation.border:  # same check you already have
                bw = dst_annotation.border["width"] * coordinate_transformer._scale_x
                dst_annotation.set_border(width=bw, dashes=src_annotation.border["dashes"])
            if src_annotation.blendmode is not None:
                dst_annotation.set_blendmode(src_annotation.blendmode)
            if annotation_type != AnnotType.PDF_ANNOT_FREE_TEXT:
                dst_annotation.set_colors(src_annotation.colors)
            dst_annotation.set_flags(src_annotation.flags)
            if src_annotation.irt_xref != 0:                                                                          
                # Check if the referenced annotation's xref was successfully mapped
                # Could be missing an attachment                                  
                if src_annotation.irt_xref in xref_map:                                                               
                    dst_annotation.set_irt_xref(xref_map[src_annotation.irt_xref])                                    
                else:                                                                                                 
                    logging.warning(                                                                                
                        f"Annotation (type: {annotation_type.name}) on page {page_num + 1} "                          
                        f"references an unmapped annotation with xref {src_annotation.irt_xref}. "                    
                        "Skipping setting irt_xref."                                                                  
                    ) 
            if src_annotation.line_ends is not None:
                dst_annotation.set_line_ends(
                    src_annotation.line_ends[0], src_annotation.line_ends[1]
                )
            dst_annotation.set_name(src_annotation.info["name"])
            dst_annotation.set_oc(src_annotation.get_oc())
            dst_annotation.set_opacity(src_annotation.opacity)
            dst_annotation.set_open(src_annotation.is_open)
            dst_annotation.set_popup(
                coordinate_transformer.transform_rect(src_annotation.popup_rect)
            )
            if annotation_type not in ANNOT_TYPES_WITHOUT_RECT_PROPERTY:
                dst_annotation.set_rect(new_rect)
            dst_annotation.set_rotation(src_annotation.rotation)
            dst_annotation.update()


def get_annotation(annotation_context: AnnotationContext) -> Optional[pymupdf.Annot]:
    src_document = annotation_context.src_document
    src_annotation = annotation_context.src_annotation
    annotation_type = annotation_context.annotation_type
    dst_page = annotation_context.dst_page
    new_rect = annotation_context.new_rect
    coordinate_transformer = annotation_context.coordinate_transformer
    assert dst_page.number is not None
    match annotation_type:
        case AnnotType.PDF_ANNOT_CARET:
            return dst_page.add_caret_annot((new_rect.tl))
        case AnnotType.PDF_ANNOT_TEXT:
            return dst_page.add_text_annot(
                new_rect.tl,
                src_annotation.info["content"],
                src_annotation.info["name"],
            )
        case AnnotType.PDF_ANNOT_FREE_TEXT:
            free_text_info = extract_font_info(src_document, src_annotation)
            return dst_page.add_freetext_annot(
                new_rect,
                free_text_info.text,
                fontsize=free_text_info.font_size,
                fontname=free_text_info.font_name,
                text_color=free_text_info.text_color,
                fill_color=free_text_info.fill_color,
                border_color=free_text_info.border_color,
                border_width=free_text_info.border_width,
                dashes=free_text_info.dashes,
                callout=coordinate_transformer.transform_vertices(
                    src_annotation.vertices
                ),
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
                new_rect.tl,
                src_annotation.get_file(),
                src_filename,
                src_annotation.file_info.get("ufilename", src_filename),
                src_annotation.file_info["description"],
                src_annotation.info["name"],
            )
        case AnnotType.PDF_ANNOT_INK:
            if src_annotation.vertices:
                ink_vertices = [
                    coordinate_transformer.transform_vertices(sub)
                    for sub in src_annotation.vertices
                ]
            else:
                ink_vertices = []
            return get_annotation_with_vertices(
                AnnotationInfo(annotation_type, dst_page.number, ink_vertices),
                dst_page.add_ink_annot,
            )
        case AnnotType.PDF_ANNOT_LINE:
            if (
                vertices := get_valid_vertices(
                    AnnotationInfo(
                        annotation_type,
                        dst_page.number,
                        coordinate_transformer.transform_vertices(
                            src_annotation.vertices
                        ),
                    )
                )
            ) is None:
                return None
            return dst_page.add_line_annot(vertices[0], vertices[1])
        case AnnotType.PDF_ANNOT_SQUARE:
            return dst_page.add_rect_annot(new_rect)
        case AnnotType.PDF_ANNOT_CIRCLE:
            return dst_page.add_circle_annot(new_rect)
        case AnnotType.PDF_ANNOT_REDACT:
            text_style = extract_text_style_from_appearance(
                src_document, src_annotation
            )
            return dst_page.add_redact_annot(
                quad=coordinate_transformer.transform_vertices(src_annotation.vertices),
                text=src_annotation.info["content"],
                fontname=text_style.font_name,
                fontsize=text_style.font_size,
                align=text_style.align,
                fill=src_annotation.colors["fill"],
                text_color=text_style.text_color,
                cross_out=True,  #  Most viewers’ defaults show the X
            )
        case AnnotType.PDF_ANNOT_POLY_LINE:
            return get_annotation_with_vertices(
                AnnotationInfo(
                    annotation_type,
                    dst_page.number,
                    coordinate_transformer.transform_vertices(src_annotation.vertices),
                ),
                dst_page.add_polyline_annot,
            )
        case AnnotType.PDF_ANNOT_POLYGON:
            return get_annotation_with_vertices(
                AnnotationInfo(
                    annotation_type,
                    dst_page.number,
                    coordinate_transformer.transform_vertices(src_annotation.vertices),
                ),
                dst_page.add_polygon_annot,
            )
        case AnnotType.PDF_ANNOT_UNDERLINE:
            return get_annotation_with_quads(
                AnnotationInfo(
                    annotation_type,
                    dst_page.number,
                    coordinate_transformer.transform_vertices(src_annotation.vertices),
                ),
                dst_page.add_underline_annot,
            )
        case AnnotType.PDF_ANNOT_STRIKE_OUT:
            return get_annotation_with_quads(
                AnnotationInfo(
                    annotation_type,
                    dst_page.number,
                    coordinate_transformer.transform_vertices(src_annotation.vertices),
                ),
                dst_page.add_strikeout_annot,
            )
        case AnnotType.PDF_ANNOT_SQUIGGLY:
            return get_annotation_with_quads(
                AnnotationInfo(
                    annotation_type,
                    dst_page.number,
                    coordinate_transformer.transform_vertices(src_annotation.vertices),
                ),
                dst_page.add_squiggly_annot,
            )
        case AnnotType.PDF_ANNOT_HIGHLIGHT:
            return get_annotation_with_quads(
                AnnotationInfo(
                    annotation_type,
                    dst_page.number,
                    coordinate_transformer.transform_vertices(src_annotation.vertices),
                ),
                dst_page.add_highlight_annot,
            )
        case AnnotType.PDF_ANNOT_STAMP:
            pix = src_annotation.get_pixmap(alpha=True)
            return dst_page.add_stamp_annot(new_rect, stamp=pix)  # type: ignore[arg-type]
        case _:
            return None


def get_annotation_with_vertices(
    annotation_info: AnnotationInfo,
    add_annotation: Callable[[list[Any]], pymupdf.Annot],
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
    pymupdf_quads = get_quads(vertices)
    return add_annotation(pymupdf_quads)


def get_quads(vertices: list[float]) -> list[pymupdf.Quad]:
    quads = [vertices[i : i + 4] for i in range(0, len(vertices), 4)]
    return [pymupdf.Quad(quad) for quad in quads]

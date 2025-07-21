from dataclasses import dataclass
import re
from typing import Literal, Optional
import pymupdf


@dataclass
class TextStyle:
    font_name: Optional[str] = None  # Ignored if richtext=True
    font_size: float = -1  # Ignored if richtext=True
    text_color: Optional[list[float]] = None  # Ignored if richtext=True
    # pymupdf.TEXT_ALIGN_LEFT = 0, CENTER = 1, RIGHT = 2
    align: int = -1  # Ignored if richtext=True

    def are_all_values_set(self) -> bool:
        return (
            self.font_name is not None
            and self.font_size != -1
            and self.text_color is not None
            and self.align != -1
        )


@dataclass
class FreeTextInfo(TextStyle):
    text: str = (
        ""  # If richtext=True (see below), the string is interpreted as HTML syntax.
    )
    fill_color: Optional[list[float]] = None
    border_color: Optional[list[float]] = None  # Only has effect if richtext=True
    border_width: float = 0
    dashes: Optional[list[float]] = None
    callout: Optional[list[float]] = None
    line_end: int = pymupdf.mupdf.PDF_ANNOT_LE_OPEN_ARROW
    opacity: float = 1
    rotate: int = 0
    richtext: bool = False
    # style: Optional[str] = None  # Ignored if richtext=False


def extract_font_info(doc: pymupdf.Document, annotation: pymupdf.Annot) -> FreeTextInfo:
    text_info = FreeTextInfo()
    text_info.fill_color = annotation.colors["fill"]
    text_info.border_width = (
        annotation.border["width"] if annotation.border["width"] >= 0 else 0
    )
    text_info.dashes = annotation.border["dashes"]
    text_info.callout = annotation.vertices
    if annotation.line_ends:
        text_info.line_end = annotation.line_ends[0]
    if annotation.opacity != -1:
        text_info.opacity = annotation.opacity
    if annotation.rotation != -1:
        text_info.rotate = annotation.rotation
    rich_text_info = doc.xref_get_key(annotation.xref, "RC")

    if rich_text_info[0] != "null":
        text_info.border_color = annotation.colors["stroke"]
        text_info.richtext = True
        text_info.text = rich_text_info[1]
        return text_info

    text_info.text = annotation.info["content"]

    text_style_ds = extract_text_style_from_display_style(
        doc.xref_get_key(annotation.xref, "DS")[1]
    )

    if text_style_ds.are_all_values_set():
        set_text_style_free_text_info(text_style_ds, text_info)
        return text_info

    text_style_da_and_q = extract_text_style_from_da_and_quadding(
        doc.xref_get_key(annotation.xref, "DA")[1],
        doc.xref_get_key(annotation.xref, "Q")[1],
    )
    merged_style = merge_two_text_styles(text_style_da_and_q, text_style_ds)
    set_text_style_free_text_info(merged_style, text_info)
    return text_info


def extract_text_style_from_display_style(display_text: str) -> TextStyle:
    ## Example: font: Helvetica, sans-serif 12pt; color: #F00;
    text_style = TextStyle()

    # Font name
    font_match = re.search(r"font\s*:\s*([^;,]+)", display_text)
    if font_match:
        families = font_match.group(1).split(",")
        text_style.font_name = families[0].strip().strip("'\"")

    # Font size
    size_match = re.search(r"(\d+(?:\.\d+)?)pt", display_text)
    if size_match:
        text_style.font_size = float(size_match.group(1))

    # Text color
    color_match = re.search(r"color\s*:\s*#?([0-9a-fA-F]{6})", string=display_text)
    if color_match:
        hex_color = color_match.group(1)
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        text_style.text_color = [r, g, b]

    return text_style


def set_text_style_free_text_info(text_style: TextStyle, text_info: FreeTextInfo):
    text_info.font_name = text_style.font_name
    text_info.font_size = text_style.font_size
    text_info.text_color = text_style.text_color
    text_info.align = text_style.align


def extract_text_style_from_da_and_quadding(da: str, quadding: str) -> TextStyle:
    text_style = TextStyle()

    font_name, font_size, text_color = extract_font_style_from_default_appearance(da)
    text_style.font_name = font_name
    text_style.font_size = font_size
    text_style.text_color = text_color

    alignment = extract_alignment_from_quadding(quadding)
    text_style.align = alignment

    return text_style


def extract_font_style_from_default_appearance(
    text: str,
) -> tuple[Optional[str], float, Optional[list[float]]]:
    ## Example: '0.9725 0.3922 0.3922 rg /Helv 12 Tf'
    font_name: Optional[str] = None
    font_size: float = -1
    text_color: Optional[list[float]] = None

    # Font name and size (e.g., /Helv 12 Tf)
    font_match = re.search(r"/(\S+)\s+(\d+(?:\.\d+)?)\s+Tf", text)
    if font_match:
        font_name = font_match.group(1)
        font_size = float(font_match.group(2))

    # Text color (e.g., r g b rg)
    color_match = re.search(
        r"(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+rg", text
    )
    if color_match:
        r, g, b = map(float, color_match.groups())
        text_color = [r, g, b]

    return font_name, font_size, text_color


def extract_alignment_from_quadding(text: str) -> int:
    alignment = -1
    if text == "null":
        return alignment

    try:
        parsed_alignment = int(text)
        return parsed_alignment if parsed_alignment in (0, 1, 2) else alignment
    except ValueError:
        return False


def merge_two_text_styles(first: TextStyle, second: TextStyle) -> TextStyle:
    merged = TextStyle()
    merged.font_name = first.font_name or second.font_name
    if first.font_size != -1:
        merged.font_size = first.font_size
    elif second.font_size != -1:
        merged.font_size = second.font_size
    else:
        merged.font_size = 11

    merged.text_color = first.text_color or second.text_color

    if first.align != -1:
        merged.align = first.align
    elif second.font_size != -1:
        merged.align = second.align
    else:
        merged.align = 0

    return merged

from dataclasses import dataclass
from pathlib import Path

import pymupdf

from borders import FourBorders
from bounds import get_bounds_extractor
from bounds.histogram_bounds.header_footer import HeaderFooterMode
from crop import get_cropper


@dataclass(frozen=True)
class ProcessPdfRequest:
    input_path: Path
    output_path: Path
    bounds_extractor: str
    borders: FourBorders
    cropper_name: str
    dpi: int | None
    detect_header_footer_mode: HeaderFooterMode | None
    allow_partial_header_footer_mode: HeaderFooterMode | None


def process_pdf(request: ProcessPdfRequest):
    doc = pymupdf.open(request.input_path)
    extractor = get_bounds_extractor(
        request.bounds_extractor,
        request.borders,
        detect_header_footer_mode=request.detect_header_footer_mode,
        allow_partial_header_footer_mode=request.allow_partial_header_footer_mode,
    )
    bounds = extractor.get_bounds(doc, request.dpi)
    cropper = get_cropper(request.cropper_name, doc)
    new_doc = cropper.crop(bounds)

    Path(request.output_path).parent.mkdir(parents=True, exist_ok=True)
    new_doc.save(request.output_path)

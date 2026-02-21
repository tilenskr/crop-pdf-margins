from dataclasses import dataclass
from pathlib import Path

import pymupdf

from borders import FourBorders
from bounds import get_bounds_extractor
from crop import get_cropper


@dataclass(frozen=True)
class ProcessPdfRequest:
    input_path: Path
    output_path: Path
    bounds_extractor: str
    borders: FourBorders
    cropper_name: str
    dpi: int | None


def process_pdf(request: ProcessPdfRequest):
    doc = pymupdf.open(request.input_path)
    extractor = get_bounds_extractor(request.bounds_extractor, request.borders)
    bounds = extractor.get_bounds(doc, request.dpi)
    cropper = get_cropper(request.cropper_name, doc)
    new_doc = cropper.crop(bounds)

    Path(request.output_path).parent.mkdir(parents=True, exist_ok=True)
    new_doc.save(request.output_path)

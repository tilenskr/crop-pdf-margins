from pathlib import Path

import pymupdf

from bounds.factory import get_bounds_extractor
from cropping import crop_and_scale


def process_pdf(input_path: Path, output_path: Path, bounds_extractor: str, border_pt: float):
    doc = pymupdf.open(input_path)
    extractor = get_bounds_extractor(bounds_extractor, border_pt)
    bounds = extractor.get_bounds(doc)
    new_doc = crop_and_scale(doc, bounds)
    new_doc.save(output_path)

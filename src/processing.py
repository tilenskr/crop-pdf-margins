from pathlib import Path

import pymupdf

from borders import FourBorders
from bounds.factory import get_bounds_extractor
from crop.factory import get_cropper


def process_pdf(input_path: Path, output_path: Path, bounds_extractor: str, borders: FourBorders, 
                cropper_name:str):
    doc = pymupdf.open(input_path)
    extractor = get_bounds_extractor(bounds_extractor, borders)
    bounds = extractor.get_bounds(doc)
    cropper = get_cropper(cropper_name, doc)
    new_doc = cropper.crop(bounds)
    new_doc.save(output_path)

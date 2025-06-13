from borders import FourBorders
from .base import BoundsExtractor
from .histogram_bounds import HistogramBoundsExtractor
from .ocr_bounds import OCRBoundsExtractor
from .page_bounds import PageBoundsExtractor
from .text_bounds import (DictTextAndImageBoundsExtractor,
                                DictTextBoundsExtractor,
                                TextBlocksAndImageBoundsExtractor,
                                TextPageBoundsExtractor)

EXTRACTOR_MAPPING: dict[str, type[BoundsExtractor]] = {
    "page_bounds": PageBoundsExtractor,
    "text_page": TextPageBoundsExtractor,
    "dict_text": DictTextBoundsExtractor,
    "text_page_images": TextBlocksAndImageBoundsExtractor,
    "dict_text_images": DictTextAndImageBoundsExtractor,
    "ocr": OCRBoundsExtractor,
    "histogram": HistogramBoundsExtractor,
}


def get_bounds_extractor(name: str, borders: FourBorders) -> BoundsExtractor:
    try:
        cls = EXTRACTOR_MAPPING[name]
    except KeyError:
        raise ValueError(f"Unknown bounds extractor: {name!r}")
    return cls(borders)

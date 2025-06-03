from borders import BorderSpec
from bounds.base import BoundsExtractor
from bounds.histogram_bounds import HistogramBoundsExtractor
from bounds.ocr_bounds import OCRBoundsExtractor
from bounds.page_bounds import PageBoundsExtractor
from bounds.text_bounds import (DictTextAndImageBoundsExtractor,
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


def get_bounds_extractor(name: str, border: BorderSpec) -> BoundsExtractor:
    try:
        cls = EXTRACTOR_MAPPING[name]
    except KeyError:
        raise ValueError(f"Unknown bounds extractor: {name!r}")
    return cls(border)

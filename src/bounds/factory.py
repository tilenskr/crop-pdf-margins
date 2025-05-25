from bounds.base import BoundsExtractor
from bounds.histogram_bounds import HistogramBoundsExtractor
from bounds.ocr_bounds import OCRBoundsExtractor
from bounds.text_bounds import DictTextAndImageBoundsExtractor, DictTextBoundsExtractor, TextBlocksAndImageBoundsExtractor, TextPageBoundsExtractor
from bounds.page_bounds import PageBoundsExtractor


EXTRACTOR_MAPPING: dict[str, type[BoundsExtractor]] = {
    "page_bounds": PageBoundsExtractor,
    "text_page": TextPageBoundsExtractor,
    "dict_text": DictTextBoundsExtractor,
    "text_page_images": TextBlocksAndImageBoundsExtractor,
    "dict_text_images": DictTextAndImageBoundsExtractor,
    "ocr": OCRBoundsExtractor,
    "histogram": HistogramBoundsExtractor,
}


def get_bounds_extractor(name: str, border_pt: float = 0) -> BoundsExtractor:
    try:
        cls = EXTRACTOR_MAPPING[name]
    except KeyError:
        raise ValueError(f"Unknown bounds extractor: {name!r}")
    return cls(border_pt)

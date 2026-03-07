from borders import FourBorders
from .base import BoundsExtractor
from .histogram_bounds import HistogramBoundsExtractor
from .histogram_bounds.header_footer import HeaderFooterMode
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


def get_bounds_extractor(
    name: str,
    borders: FourBorders,
    detect_header_footer_mode: HeaderFooterMode | None,
    allow_partial_header_footer_mode: HeaderFooterMode | None,
) -> BoundsExtractor:
    if name == "histogram":
        return HistogramBoundsExtractor(
            borders,
            detect_header_footer_mode,
            allow_partial_header_footer_mode,
        )

    try:
        cls = EXTRACTOR_MAPPING[name]
    except KeyError:
        raise ValueError(f"Unknown bounds extractor: {name!r}")
    return cls(borders)

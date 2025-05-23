from bounds.base import BoundsExtractor
from bounds.text_bounds import DictTextBoundsExtractor, TextPageBoundsExtractor
from bounds.page_bounds import PageBoundsExtractor


EXTRACTOR_MAPPING: dict[str, type[BoundsExtractor]] = {
    "page_bounds": PageBoundsExtractor,
    "text_page": TextPageBoundsExtractor,
    "dict_text": DictTextBoundsExtractor,
}


def get_bounds_extractor(name: str, border_pt: float = 0) -> BoundsExtractor:
    try:
        cls = EXTRACTOR_MAPPING[name]
    except KeyError:
        raise ValueError(f"Unknown bounds extractor: {name!r}")
    return cls(border_pt)

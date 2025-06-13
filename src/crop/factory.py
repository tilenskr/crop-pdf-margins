import pymupdf

from .base import Cropper
from .box_cropper import BoxCropper
from .scale_cropper import ScaleCropper

CROPPER_MAPPING: dict[str, type[Cropper]] = {
    "box": BoxCropper,
    "scale": ScaleCropper,
}


def get_cropper(name: str, doc: pymupdf.Document) -> Cropper:
    try:
        cls = CROPPER_MAPPING[name]
    except KeyError:
        raise ValueError(f"Unknown cropper: {name!r}")
    return cls(doc)

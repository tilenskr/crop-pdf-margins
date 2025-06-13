import pymupdf

from crop.base import Cropper
from crop.box_cropper import BoxCropper
from crop.scale_cropper.core import ScaleCropper

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

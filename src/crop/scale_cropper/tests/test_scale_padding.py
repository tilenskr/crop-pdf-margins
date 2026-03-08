import unittest

import pymupdf
from PIL import Image

from src.crop.box_cropper import BoxCropper
from src.crop.scale_cropper.coordinate_transformer import CoordinateTransformer
from src.crop.scale_cropper.core import ScaleCropper
from src.crop.scale_cropper.internal_destinations import InternalDestinationResolver
from src.crop.scale_cropper.links import transform_link_destination
from src.page_layout import PageCropLayout


class ScalePaddingTests(unittest.TestCase):
    def test_scale_cropper_leaves_bottom_padding_blank(self) -> None:
        doc = pymupdf.open()
        page = doc.new_page(width=200, height=200)
        page.insert_text((40, 120), "Body text", fontsize=20)
        page.insert_text((50, 188), "Footer", fontsize=12)

        layout = PageCropLayout(
            page_rect=page.rect,
            content_rect=pymupdf.Rect(0, 0, 200, 160),
            visible_rect=pymupdf.Rect(0, 0, 200, 170),
            destination_rect=pymupdf.Rect(0, 0, 200, 180),
        )

        out = ScaleCropper(doc).crop([layout])
        rendered = out[0].get_pixmap()
        image = Image.frombytes(
            "RGB", (rendered.width, rendered.height), rendered.samples
        )

        bottom_band = image.crop((0, 182, rendered.width, rendered.height))
        self.assertEqual(
            self._count_non_white_pixels(bottom_band),
            0,
            "Bottom padding should stay blank after scale cropping.",
        )

    def test_box_cropper_uses_visible_rect(self) -> None:
        doc = pymupdf.open()
        page = doc.new_page(width=200, height=200)
        layout = PageCropLayout(
            page_rect=page.rect,
            content_rect=pymupdf.Rect(20, 30, 180, 170),
            visible_rect=pymupdf.Rect(10, 15, 190, 180),
            destination_rect=page.rect,
        )

        out = BoxCropper(doc).crop([layout])
        self.assertEqual(out[0].cropbox, layout.visible_rect)

    def test_transform_link_destination_respects_inset_padding(self) -> None:
        dst_doc = pymupdf.open()
        dst_doc.new_page(width=200, height=200)
        layout = PageCropLayout(
            page_rect=pymupdf.Rect(0, 0, 200, 200),
            content_rect=pymupdf.Rect(0, 0, 100, 100),
            visible_rect=pymupdf.Rect(0, 0, 100, 100),
            destination_rect=pymupdf.Rect(10, 20, 110, 120),
        )
        link = {
            "kind": pymupdf.LINK_GOTO,
            "page": 0,
            "to": pymupdf.Point(0, 0),
            "from": pymupdf.Rect(0, 0, 10, 10),
        }

        transformed = transform_link_destination(
            link,
            dst_doc,
            [layout],
            0,
            InternalDestinationResolver(dst_doc, dst_doc.page_count),
        )

        self.assertIsNotNone(transformed)
        assert transformed is not None
        self.assertEqual(transformed["to"], pymupdf.Point(10, 20))

    def test_coordinate_transformer_handles_empty_destination_rect(self) -> None:
        transformer = CoordinateTransformer(
            pymupdf.Rect(0, 0, 100, 100),
            pymupdf.Rect(50, 50, 50, 50),
        )
        self.assertEqual(transformer.transform_point(10, 10), (50.0, 50.0))

    @staticmethod
    def _count_non_white_pixels(image: Image.Image) -> int:
        return sum(1 for pixel in image.getdata() if pixel != (255, 255, 255))


if __name__ == "__main__":
    unittest.main()

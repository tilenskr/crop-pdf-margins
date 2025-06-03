from typing import override

import pymupdf
import pytesseract
from PIL import Image, ImageOps
from tqdm import tqdm

from bounds.base import BoundsExtractor


class OCRBoundsExtractor(BoundsExtractor):
    @override
    def get_bounds(self, doc: pymupdf.Document) -> list[pymupdf.Rect]:
        dpi = 500
        dpi_pdf = 72.0
        scale_factor = dpi_pdf / dpi

        rectangles: list[pymupdf.Rect] = []
        for i in tqdm(range(doc.page_count)):
            page = doc.load_page(i)
            x0, y0 = float("inf"), float("inf")
            x1, y1 = 0, 0

            raster_img: pymupdf.Pixmap = page.get_pixmap(dpi=dpi)  # type:ignore
            img = Image.frombytes(
                "RGB", (raster_img.width, raster_img.height), raster_img.samples
            )
            # img.save("output/test.png")
            gray = ImageOps.grayscale(img)
            ocr_data = pytesseract.image_to_data(
                gray, output_type=pytesseract.Output.DICT
            )
            text_data = ocr_data["text"]
            for word, left, top, width, height in zip(
                text_data,
                ocr_data["left"],
                ocr_data["top"],
                ocr_data["width"],
                ocr_data["height"],
            ):
                if not word.strip():
                    continue
                # convert pixel coords → PDF‐point coords
                bx0 = left * scale_factor
                by0 = top * scale_factor
                bx1 = (left + width) * scale_factor
                by1 = (top + height) * scale_factor
                x0, y0 = min(x0, bx0), min(y0, by0)
                x1, y1 = max(x1, bx1), max(y1, by1)
            rect = self._get_rectangle(
                bounds=pymupdf.Rect(
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                ),
                has_content=any(text_data),
                page_rect=page.rect,
            )
            rectangles.append(rect)
        return rectangles

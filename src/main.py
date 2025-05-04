import argparse
from pathlib import Path

import pymupdf


def main():
    parser = argparse.ArgumentParser(description="Crop PDF Margins")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Path to the PDF file.",
    )
    parser.add_argument(
        "-d",
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where the cropped PDF will be saved.",
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        default=None,
        help="Optional output filename (without extension). Defaults to input basename.",
    )

    args = parser.parse_args()
    file_name = args.name if args.name is not None else args.input.name
    output = args.output_dir / file_name
    auto_crop_pdf(args.input, output, 0)


# def process_pdf(filename: str):
#     doc = fitz.open(file_name)  # open document


#     for page in doc:  # iterate through the pages
#         pix = page.getPixmap(...)  # render page to an image
#         pix.writePNG("page-%i.png" % page.number)  # store image as a PNG


def auto_crop_pdf(input_path: Path, output_path: Path, border_pt=0):
    doc = pymupdf.open(input_path)
    for page_num, page in enumerate(doc):
        # initialize to extremes
        x0, y0 = float("inf"), float("inf")
        x1, y1 = 0, 0

        does_any_block_exist = False
        # 1) text blocks (Textpage content as a Python dictionary; . May include text and images.)
        # for text_block in page.get_text("dict")["blocks"]:  # type: ignore
        for text_block in page.get_textpage().extractDICT(sort=True)["blocks"]:
            bx0, by0, bx1, by1 = text_block["bbox"]
            x0, y0 = min(x0, bx0), min(y0, by0)
            x1, y1 = max(x1, bx1), max(y1, by1)
            does_any_block_exist = True
        # 2) images
        # for img in page.get_images(full=True):
        #     xref = img[0]
        #     ix0, iy0, ix1, iy1 = page.get_image_bbox(xref)
        #     x0, y0 = min(x0, ix0), min(y0, iy0)
        #     x1, y1 = max(x1, ix1), max(y1, iy1)

        # apply border and crop
        if does_any_block_exist:
            rect = pymupdf.Rect(
                x0 - border_pt, y0 - border_pt, x1 + border_pt, y1 + border_pt
            )
            page.set_cropbox(rect)

    doc.save(output_path)


if __name__ == "__main__":
    main()

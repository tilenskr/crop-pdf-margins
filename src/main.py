import argparse
from pathlib import Path

from borders import BorderSpec, BorderUnit, parse_border
from bounds.factory import EXTRACTOR_MAPPING
from crop.factory import CROPPER_MAPPING
from processing import process_pdf


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
    parser.add_argument(
        "-be",
        "--bounds-extractor",
        choices=list(EXTRACTOR_MAPPING.keys()),
        required=True,
        help="Which bounds extractor to use.",
    )
    parser.add_argument(
        "-b",
        "--border",
        type=parse_border,
        default=BorderSpec(0.0, BorderUnit.POINT),
        help="Padding (pts) around extracted bounds",
    )
    parser.add_argument(
        "-c",
        "--cropper",
        choices=list(CROPPER_MAPPING.keys()),
        required=True,
        help="Which cropper to use.",
    )

    args = parser.parse_args()
    file_name = args.name if args.name is not None else args.input.name
    output = args.output_dir / file_name
    process_pdf(args.input, output, args.bounds_extractor, args.border, args.cropper)


def validate_border_input(border: str) -> BorderSpec:
    try:
        return parse_border(border)
    except ValueError as e:
        raise argparse.ArgumentTypeError(e)


if __name__ == "__main__":
    main()

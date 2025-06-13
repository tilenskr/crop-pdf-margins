import argparse
from pathlib import Path

from borders import BorderSpec, BorderUnit, FourBorders, expand_css_border, parse_border
from bounds import EXTRACTOR_MAPPING
from crop import CROPPER_MAPPING
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
        nargs="+",
        type=validate_border_input,
        default=[BorderSpec(0.0, BorderUnit.POINT)],
        help=(
            "Padding around extracted bounds, specified in pixels (e.g., 10.5) or percentage (e.g., 5.3%). "
            "Supports either a single value (applied to all sides) or four values like in CSS "
            "(top, right, bottom, left)."
        ),
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
    borders = validate_and_expand_border(parser, args.border)
    process_pdf(args.input, output, args.bounds_extractor, borders, args.cropper)


def validate_border_input(border: str) -> BorderSpec:
    try:
        return parse_border(border)
    except ValueError as e:
        raise argparse.ArgumentTypeError(e)


def validate_and_expand_border(parser, raw_specs) -> FourBorders:
    try:
        return expand_css_border(raw_specs)
    except ValueError as e:
        return parser.error(e)


if __name__ == "__main__":
    main()

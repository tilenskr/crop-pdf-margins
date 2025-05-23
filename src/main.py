import argparse
from pathlib import Path

from bounds.factory import EXTRACTOR_MAPPING
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
        type=float,
        default=0,
        help="Padding (pts) around extracted bounds",
    )

    args = parser.parse_args()
    file_name = args.name if args.name is not None else args.input.name
    output = args.output_dir / file_name
    process_pdf(args.input, output, args.bounds_extractor, args.border)


if __name__ == "__main__":
    main()

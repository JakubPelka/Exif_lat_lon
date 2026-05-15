from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import scan_images, write_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="exif-lat-lon",
        description="Extract GPS coordinates from images and export CSV + GeoJSON.",
    )
    parser.add_argument("-i", "--input", default="indata", help="Folder with images. Default: indata")
    parser.add_argument("-o", "--output", default="output/image_gps.csv", help="Output CSV path or output base path. Default: output/image_gps.csv")
    parser.add_argument("--extractor", choices=["auto", "exiftool", "pillow"], default="auto", help="Metadata extractor. Default: auto")
    parser.add_argument("--exiftool-path", default=None, help="Optional path to exiftool executable.")
    parser.add_argument("--no-recursive", action="store_true", help="Do not scan subfolders.")
    parser.add_argument("--gui", action="store_true", help="Open the graphical interface.")
    return parser


def run_cli(args: argparse.Namespace) -> int:
    result = scan_images(
        input_folder=args.input,
        recursive=not args.no_recursive,
        extractor=args.extractor,
        exiftool_path=args.exiftool_path,
    )
    csv_path, geojson_path, summary_path, no_gps_path = write_outputs(result, args.output)

    print(f"Extractor: {result.extractor}")
    print(f"Supported files scanned: {result.total_supported_files}")
    print(f"Files with GPS: {result.gps_count}")
    print(f"Files without GPS: {result.no_gps_count}")
    print(f"Errors: {result.error_count}")
    print(f"CSV: {csv_path}")
    print(f"GeoJSON: {geojson_path}")
    print(f"Summary: {summary_path}")
    if no_gps_path:
        print(f"Files without GPS list: {no_gps_path}")
    return 0 if result.error_count == 0 else 2


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.gui:
        from .gui import main as gui_main
        gui_main()
        return 0

    try:
        return run_cli(args)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

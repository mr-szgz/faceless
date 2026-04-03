#!/usr/bin/env python3
import argparse
import sys

from faceless.faceless import IDENTITY_TEXT

DEFAULT_MATCH_SELECTORS = "216,594"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="faceless")
    parser.add_argument("path", nargs="?", help="Source directory containing images")
    parser.add_argument("-Path", "--path", dest="path_option", help="Source directory containing images")
    parser.add_argument(
        "-Label",
        "--label",
        "-Force",
        "--force",
        action="store_true",
        dest="force_labels",
        help="Force regeneration of labels",
    )
    parser.add_argument("-Conf", "--conf", type=float, default=0.2, help="Model confidence threshold")
    parser.add_argument(
        "-Match",
        "--match",
        default=DEFAULT_MATCH_SELECTORS,
        dest="match",
        help='Required match class IDs, comma-separated (example: "1,43,51"). Default: "216,594".',
    )
    parser.add_argument(
        "-Directory",
        "--directory",
        default="faceless",
        help="Output directory name for moved files (default: faceless)",
    )
    parser.add_argument(
        "-Auto",
        "--auto",
        "-a",
        action="store_true",
        dest="auto_directory",
        help="Move non-matching files into per-label folders under the output directory",
    )
    parser.add_argument("--version", "-Version", "-v", action="version", version=IDENTITY_TEXT)
    return parser.parse_args(sys.argv[1:])


def main() -> None:
    args = parse_arguments()
    from faceless.faceless import run_faceless

    run_faceless(args)


if __name__ == "__main__":
    main()

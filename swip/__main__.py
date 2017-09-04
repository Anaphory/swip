#!/usr/bin/env python

"Render Kartesian SignWriting strings as SVG graphics."

import sys
import argparse

from .compose import glyphogram
from .iswa_font import ISWAFont


def main():
    """The main CLI."""
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument(
        "ksw_string",
        help="The KSW string to be rendered.")
    parser.add_argument(
        "--output",
        type=argparse.FileType('w'),
        default=sys.stdout,
        help="The file to write output to.")
    parser.add_argument(
        "-a", "--auto-output",
        action="store_true",
        default=False,
        help="Write output to KSW_STRING.svg")
    parser.add_argument(
        "--font",
        default="font_svg1",
        help="The font to use")
    args = parser.parse_args()
    if args.auto_output and args.output != sys.stdout:
        raise ValueError("Both auto-output and output file specified.")
    elif args.auto_output:
        args.output = open(args.ksw_string + '.svg', 'w')

    args.output.write(
        glyphogram(args.ksw_string,
                   font=ISWAFont(name=args.font)))


if __name__ == "__main__":
    main()

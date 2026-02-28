import argparse
import os
import sys

from clibib.api import extract_bibkey, fetch_bibtex


def build_parser():
    """Return the argument parser for clibib."""
    parser = argparse.ArgumentParser(
        prog="clibib",
        description="Fetch BibTeX entries for a URL, DOI, ISBN, PMID, paper title or arXiv ID.",
    )
    parser.add_argument("query", help="URL, DOI, ISBN, PMID, paper title or arXiv ID to look up")
    parser.add_argument(
        "-o", metavar="OUTPUT_DIR",
        help="save BibTeX entry to OUTPUT_DIR/<bibkey>.bib",
    )
    return parser


def main(argv=None):
    """Entry point for the clibib CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        bibtex = fetch_bibtex(args.query)
        print(bibtex)
        if args.o:
            bibkey = extract_bibkey(bibtex)
            os.makedirs(args.o, exist_ok=True)
            output_path = os.path.join(args.o, f"{bibkey}.bib")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(bibtex)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

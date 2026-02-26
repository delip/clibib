import argparse
import sys

from clibib.api import fetch_bibtex


def build_parser():
    """Return the argument parser for clibib."""
    parser = argparse.ArgumentParser(
        prog="clibib",
        description="Fetch BibTeX entries for a URL, DOI, ISBN, PMID, or arXiv ID.",
    )
    parser.add_argument("query", help="URL, DOI, ISBN, PMID, or arXiv ID to look up")
    return parser


def main(argv=None):
    """Entry point for the clibib CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        bibtex = fetch_bibtex(args.query)
        print(bibtex)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

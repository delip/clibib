import argparse


def build_parser():
    """Return the argument parser for clibib."""
    parser = argparse.ArgumentParser(
        prog="clibib",
        description="Fetch BibTeX entries for a given URL.",
    )
    parser.add_argument("url", help="URL to fetch a BibTeX entry for")
    return parser


def main(argv=None):
    """Entry point for the clibib CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    print(f"TODO: fetch BibTeX for {args.url}")

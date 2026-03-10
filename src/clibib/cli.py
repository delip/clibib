import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from clibib.api import (
    AmbiguousQueryError,
    convert_to_bibtex,
    extract_bibkey,
    fetch_bibtex,
    rank_candidates,
    resolve_identifier,
)


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
    parser.add_argument(
        "--first", action="store_true",
        help="only output the highest-ranked result",
    )
    return parser


def _resolve_and_print(identifier, args):
    """Resolve an identifier to BibTeX, print it, and optionally save to file."""
    items = resolve_identifier(identifier)
    bibtex = convert_to_bibtex(items)
    print(bibtex)
    if args.o:
        bibkey = extract_bibkey(bibtex)
        os.makedirs(args.o, exist_ok=True)
        output_path = os.path.join(args.o, f"{bibkey}.bib")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(bibtex)


def main(argv=None):
    """Entry point for the clibib CLI."""
    env_file = Path.home() / ".clibib" / ".env"
    load_dotenv(env_file)

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
    except AmbiguousQueryError as e:
        ranked = rank_candidates(e.query, e.candidates)
        if args.first:
            try:
                _resolve_and_print(ranked[0][0], args)
            except Exception as ex:
                print(f"Error: {ex}", file=sys.stderr)
                sys.exit(1)
        else:
            print(
                f"Multiple records found for \"{e.query}\".",
                file=sys.stderr,
            )
            errors = []
            for identifier, meta, score in ranked:
                try:
                    _resolve_and_print(identifier, args)
                except Exception as ex:
                    errors.append(f"{identifier}: {ex}")
            if errors:
                for err in errors:
                    print(f"Warning: {err}", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

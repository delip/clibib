# clibib

Fetch BibTeX entries from a URL, ISBN, DOI, PMID, arXiv, or even just title!

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```bash
# Fetch BibTeX from a DOI
clibib 10.1038/nature12373

# From an arXiv URL
clibib https://arxiv.org/abs/2301.07041

# From an ISBN
clibib 978-0-13-468599-1

# From any URL
clibib https://example.com/article
```

## Development

Run tests:

```bash
pytest
```

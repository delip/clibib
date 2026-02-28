# clibib
[![CI](https://github.com/delip/clibib/actions/workflows/ci.yml/badge.svg)](https://github.com/delip/clibib/actions/workflows/ci.yml)

<!--
<img width="2816" height="1536" alt="image" src="https://github.com/user-attachments/assets/bed7c6f8-f5fb-46da-8d4a-2df5b9c1baad" />
-->

<p align="center">
<img width="600" height="470" alt="image" src="https://github.com/user-attachments/assets/0c60331c-dbbd-4ada-92c6-c2df952177cb" />
</p>
A Python-based CLI tool to fetch BibTeX entries from a URL, ISBN, DOI, PMID, arXiv, or even just title!



## Installation

```bash
pip install clibib
```

## Usage

```bash
# Fetch BibTeX from a DOI
clibib 10.1038/nature12373

# From an arXiv ID
clibib 2301.07041

# From a URL
clibib https://academic.oup.com/bib/article/25/1/bbad467/7512647

# From an ISBN
clibib 978-0-13-468599-1

# Save BibTeX to a file
clibib -o ~/bibs 10.1038/nature12373
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

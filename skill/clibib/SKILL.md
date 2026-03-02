---
name: clibib
description: >
  Fetch BibTeX citations from DOIs, arXiv IDs, ISBNs, PMIDs, URLs, or paper titles
  using the clibib CLI. Triggers on: cite, bibtex, citation, DOI, arXiv, ISBN, PMID,
  bibliography, reference, "get bibtex for", "add to references", "fetch citation",
  "look up paper", "find reference".
allowed-tools:
  - Bash(clibib *)
  - Bash(pip install clibib)
  - Bash(pip show clibib)
  - Bash(which clibib)
  - Bash(cat *)
  - Bash(ls *)
  - Bash(mkdir *)
---

# clibib — Fetch BibTeX Citations

## Prerequisites

Check if clibib is installed:

```bash
which clibib || pip show clibib
```

If not found, install it:

```bash
pip install clibib
```

## Basic Usage

Run `clibib <query>` where query is any of:

| Input Type | Example |
|---|---|
| DOI | `clibib 10.1038/nature12373` |
| arXiv ID | `clibib 2301.07041` |
| ISBN | `clibib 978-0-13-468599-1` |
| PMID | `clibib 23624526` |
| URL | `clibib https://academic.oup.com/bib/article/25/1/bbad467/7512647` |
| Paper title | `clibib "Attention Is All You Need"` |

The command prints BibTeX to stdout. Capture and use the output as needed.

## Saving to File

Use `-o OUTPUT_DIR` to save the BibTeX entry to a file named `<bibkey>.bib` inside the given directory:

```bash
clibib -o ~/bibs 10.1038/nature12373
```

The directory is created automatically if it doesn't exist.

## Appending to an Existing .bib File

clibib doesn't append directly. To add a citation to an existing `.bib` file:

1. Run clibib and capture the output
2. Check for duplicate citation keys in the target file before appending
3. Append with a blank line separator

```bash
OUTPUT=$(clibib 10.1038/nature12373)
KEY=$(echo "$OUTPUT" | head -1 | grep -oP '(?<=\{)[^,]+')
if grep -q "$KEY" refs.bib 2>/dev/null; then
  echo "Duplicate key: $KEY — skipping"
else
  echo "" >> refs.bib
  echo "$OUTPUT" >> refs.bib
fi
```

## Handling Multiple Queries

Run clibib once per query. Do not batch multiple queries in a single call.

```bash
clibib 10.1038/nature12373
clibib 2301.07041
```

## Error Handling

| Scenario | Behavior |
|---|---|
| No results found | Exits with code 1, prints "Error: No results found" to stderr |
| Network error | Exits with code 1, prints the error message to stderr |
| Command not found | Install with `pip install clibib` |

If clibib returns an error, inform the user of the issue. For "no results found", suggest checking the query format or trying an alternative identifier for the same paper.

## Additional Resources

See [references/api-guide.md](references/api-guide.md) for detailed information on input formats, URL normalization, output format, and troubleshooting.

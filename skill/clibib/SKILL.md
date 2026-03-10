---
name: clibib
description: >
  Fetch BibTeX citations from DOIs, arXiv IDs, ISBNs, PMIDs, URLs, alphaxiv, huggingface papers, or paper titles using the clibib CLI. Triggers on: cite, bibtex, citation, DOI, arXiv, ISBN, PMID, alphaxiv, huggingface.co/papers/, bibliography, reference, "get bibtex for", "add to references", "fetch citation", "look up paper", "find reference".
allowed-tools:
  - Bash(clibib *)
  - Bash(pip install clibib)
  - Bash(pip show clibib)
  - Bash(which clibib)
  - Bash(cat *)
  - Bash(ls *)
  - Bash(mkdir *)
  - WebSearch
  - WebFetch
---

# clibib — Fetch BibTeX Citations

## MANDATORY: Always Search Before Invoking clibib With a Title

When the user provides a direct identifier (DOI, arXiv ID, ISBN, PMID, or URL), **invoke clibib immediately** with that identifier. No web search is needed.

When the user provides only a paper title (no identifier), **you MUST search the web first** to find the correct identifier before invoking clibib. Title-based searches in clibib are unreliable — CrossRef and Zotero databases often return incomplete, incorrect, or ambiguous matches. Never skip the search step for title queries.

### Search workflow for title queries

1. **Search the web for the paper's publication venue** (which conference, journal, or workshop it appeared in). Inspect the top few search results to identify the correct venue — don't blindly take the first hit, as it may be a blog post, preprint mirror, or a different paper entirely.
2. **Search for the DOI/URL of that paper at that specific venue** (e.g., "Attention Is All You Need DOI NeurIPS 2017"). Inspect the top few results and pick the one that best matches the paper's title, authors, and venue — don't just take the first DOI/URL returned.
3. Use the venue-specific DOI/URL with clibib

This two-step approach avoids retrieving the wrong version when a paper has multiple DOIs (e.g., conference proceedings, journal version, workshop version, preprint).

Only fall back to `clibib "<title>"` if a web search fails to locate any identifier.

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

| Input Type  | Example                                                            |
| ----------- | ------------------------------------------------------------------ |
| DOI         | `clibib 10.1038/nature12373`                                       |
| arXiv ID    | `clibib 2301.07041`                                                |
| ISBN        | `clibib 978-0-13-468599-1`                                         |
| PMID        | `clibib 23624526`                                                  |
| URL         | `clibib https://academic.oup.com/bib/article/25/1/bbad467/7512647` |
| alphaxiv    | `clibib https://alphaxiv.org/abs/2301.07041`                       |
| huggingface | `clibib https://huggingface.co/papers/2301.07041`                  |
| Paper title | `clibib "Attention Is All You Need"` *(less reliable — see above)* |

For title searches that return multiple candidates, clibib prints all matching BibTeX entries ranked by relevance. Use `--first` to output only the top result:

```bash
clibib --first "Attention Is All You Need"
```

**Reminder:** Title search is a last resort. Always search the web for the paper's venue and DOI first, then use `clibib <DOI>`.

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

| Scenario          | Behavior                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------ |
| No results found  | Exits with code 1, prints "Error: No results found" to stderr                              |
| Ambiguous title   | Prints all matching BibTeX entries ranked by relevance. With `--first`: only the top match |
| Network error     | Exits with code 1, prints the error message to stderr                                      |
| Command not found | Install with `pip install clibib`                                                          |

If clibib returns an error, inform the user of the issue. For "no results found", suggest checking the query format or trying an alternative identifier for the same paper. If a title search returns wrong or no results, search the web for the paper's venue, then find the DOI at that venue, and retry.

## Additional Resources

See [references/api-guide.md](references/api-guide.md) for detailed information on input formats, URL normalization, output format, and troubleshooting.

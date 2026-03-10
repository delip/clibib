# clibib API & Format Reference

## Input Types

### DOI (Digital Object Identifier)

- Format: `10.XXXX/...` (e.g., `10.1038/nature12373`)
- Sent directly to the search endpoint

### arXiv ID

- Format: `YYMM.NNNNN` (e.g., `2301.07041`)
- Older format: `category/NNNNNNN` (e.g., `hep-th/9905111`)
- Sent directly to the search endpoint

### ISBN (International Standard Book Number)

- Format: `978-X-XX-XXXXXX-X` or `0-XX-XXXXXX-X`
- Hyphens are optional

### PMID (PubMed Identifier)

- Format: numeric string (e.g., `23624526`)
- Sent directly to the search endpoint

### URL

- Any `http://` or `https://` URL pointing to a paper or publication page
- URLs are normalized before resolution (see below)

### Paper Title (Free Text) — Less Reliable

- Any text that doesn't match the above formats
- Triggers an ambiguous search; the server may return multiple candidates (HTTP 300)
- If exactly one candidate is returned, it is resolved automatically
- If multiple candidates are returned, clibib ranks them by Jaccard token similarity against the query and outputs all matching BibTeX entries (use `--first` to output only the top match)
- If the primary server returns no results, clibib falls back to CrossRef to find candidate DOIs
- Wrap multi-word titles in quotes on the command line
- **Title searches are less reliable** than identifier-based lookups because CrossRef and Zotero databases may return incomplete, incorrect, or ambiguous matches. Prefer DOI, arXiv ID, or URL whenever possible. If you only have a title, first search the web for the paper's publication venue, then search for the DOI at that specific venue, and use that instead.

## URL Normalization

Before sending URLs to the backend, clibib normalizes them for better resolution:

| Original URL | Normalized URL |
|---|---|
| `https://arxiv.org/pdf/2301.07041` | `https://arxiv.org/abs/2301.07041` |
| `https://arxiv.org/html/2301.07041` | `https://arxiv.org/abs/2301.07041` |
| `https://arxiv.org/pdf/2301.07041.pdf` | `https://arxiv.org/abs/2301.07041` |
| `https://example.com/article.pdf` | `https://example.com/article` |
| `https://example.com/pdf/article` | `https://example.com/article` |

## Output Format

clibib outputs BibTeX to stdout. Citation keys are sanitized: any character that is not alphanumeric or underscore is replaced with `_`.

Example output:

```bibtex
@article{beltagy_longformer_2020,
    title = {Longformer: The Long-Document Transformer},
    author = {Beltagy, Iz and Peters, Matthew E. and Cohan, Arman},
    year = {2020},
    ...
}
```

## The `-o` Flag

When `-o OUTPUT_DIR` is provided:

1. The BibTeX is still printed to stdout
2. The directory is created if it doesn't exist
3. The entry is saved to `OUTPUT_DIR/<bibkey>.bib`
4. The bibkey is extracted from the first `@type{key,` pattern in the output

## Backend

clibib uses a Zotero Translation Server instance as its backend, with CrossRef as a fallback for title searches. The server handles:

- `/web` endpoint: resolves URLs to metadata
- `/search` endpoint: resolves identifiers (DOI, ISBN, arXiv, PMID) and free-text queries
- `/export` endpoint: converts Zotero JSON to BibTeX format

The search endpoint returns HTTP 200 for exact identifier matches and HTTP 300 for ambiguous text queries (with a choice map). For single-candidate 300 responses, clibib resolves automatically. For multi-candidate responses, candidates are ranked by Jaccard token similarity and all matching BibTeX entries are output (use `--first` for only the top match). When the search endpoint returns no results for a title query, clibib falls back to CrossRef's open API to find candidate DOIs.

## Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| "No results found" | Identifier not in Zotero's database | Try an alternative identifier (e.g., URL instead of DOI) |
| "No results found" for title | Title too vague or too specific | Adjust the search terms; try the exact paper title |
| Network timeout | Server unreachable | Check internet connection; retry |
| Garbled citation key | Special characters in original key | Expected — keys are auto-sanitized |
| Wrong paper returned for title | Ambiguous search picked wrong match | Search the web for the paper's venue, then find the DOI at that venue, or use an arXiv ID for exact results |
| PDF URL returns no results | Some publisher PDF URLs aren't resolvable | Use the abstract/landing page URL instead |

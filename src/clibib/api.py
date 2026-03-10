"""Zotero Translation Server client for fetching BibTeX entries."""

import re
from urllib.parse import quote_plus, urlparse

import requests

TRANSLATION_SERVER = "https://t0guvf0w17.execute-api.us-east-1.amazonaws.com/Prod"


class AmbiguousQueryError(Exception):
    """Raised when a title search returns multiple candidates."""

    def __init__(self, query: str, candidates: dict):
        self.query = query
        self.candidates = candidates
        super().__init__(f"Ambiguous query: {len(candidates)} candidates found")


def _tokenize(text: str) -> set[str]:
    """Return a set of lowercase alphanumeric tokens from text."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def rank_candidates(query: str, candidates: dict) -> list[tuple[str, dict, float]]:
    """Rank candidates by Jaccard similarity of tokens against the query.

    Returns a list of (identifier, metadata, score) tuples sorted by
    descending score.
    """
    query_tokens = _tokenize(query)
    query_lower = query.lower()
    scored = []
    for identifier, meta in candidates.items():
        title = meta.get("title", "")
        title_tokens = _tokenize(title)
        union = query_tokens | title_tokens
        jaccard = len(query_tokens & title_tokens) / len(union) if union else 0.0
        # Tiebreaker: boost if the query appears as a substring of the title
        substring_match = 1 if query_lower in title.lower() else 0
        scored.append((identifier, meta, jaccard, substring_match))
    # Stable sort preserves input order for ties (e.g. CrossRef relevance)
    scored.sort(key=lambda x: (x[2], x[3]), reverse=True)
    return [(ident, meta, jaccard) for ident, meta, jaccard, _ in scored]


def resolve_identifier(identifier: str) -> list[dict]:
    """Resolve a single identifier via /search and return Zotero JSON."""
    resp = _search(identifier)
    resp.raise_for_status()
    return resp.json()


CROSSREF_API = "https://api.crossref.org/works"


def _crossref_search(query: str, rows: int = 10) -> dict:
    """Search CrossRef for candidate DOIs matching a free-text query.

    Returns a candidates dict in the same format as a Zotero 300 response:
    {doi: {"title": ..., "description": ...}, ...}
    """
    resp = requests.get(
        CROSSREF_API,
        params={"query": query, "rows": rows, "select": "DOI,title,author"},
        headers={"User-Agent": "clibib/1.0 (https://github.com/delip/clibib)"},
        timeout=15,
    )
    resp.raise_for_status()
    items = resp.json().get("message", {}).get("items", [])
    candidates = {}
    for item in items:
        doi = item.get("DOI", "")
        title = item.get("title", [""])[0] if item.get("title") else ""
        authors = ", ".join(
            a.get("family", "") for a in item.get("author", [])[:3]
        )
        description = authors if authors else ""
        if doi:
            candidates[doi] = {"title": title, "description": description}
    return candidates


def normalize_url(url: str) -> str:
    """Transform variant URLs to canonical forms for better resolution.

    Converts arxiv PDF/HTML links to abstract pages, and strips /pdf/ suffixes
    from publisher URLs where possible.
    """
    parsed = urlparse(url)
    path = parsed.path

    if "arxiv.org" in parsed.netloc:
        # /pdf/ID or /html/ID → /abs/ID
        match = re.match(r"^/(pdf|html)/(.+?)(?:\.pdf)?$", path)
        if match:
            new_path = f"/abs/{match.group(2)}"
            return parsed._replace(path=new_path).geturl()
        return url

    # Generic: strip trailing /pdf/ or .pdf from paths
    if path.endswith(".pdf"):
        return parsed._replace(path=path.removesuffix(".pdf")).geturl()
    pdf_match = re.match(r"^(.*)/pdf(/.*)?$", path)
    if pdf_match:
        new_path = pdf_match.group(1) + (pdf_match.group(2) or "")
        return parsed._replace(path=new_path).geturl()

    return url


def classify_input(text: str) -> str:
    """Return 'url' for web URLs, 'search' for everything else.

    Identifiers (DOI, ISBN, arXiv ID, PMID) and free-text title queries
    all go through the /search endpoint. Only actual URLs use /web.
    """
    text = text.strip()
    if text.startswith(("http://", "https://")):
        return "url"
    return "search"


def _search(text: str) -> requests.Response:
    return requests.post(
        f"{TRANSLATION_SERVER}/search",
        data=text,
        headers={"Content-Type": "text/plain"},
        timeout=30,
    )


def fetch_zotero_json(text: str) -> list[dict]:
    """Resolve a query to Zotero JSON items via the translation server.

    For URLs, uses the /web endpoint. For everything else, uses /search.
    The /search endpoint returns 200 with Zotero JSON for exact identifiers,
    or 300 with a choice map for ambiguous text queries — in that case we
    pick the first result and re-query with its identifier.
    """
    input_type = classify_input(text)

    if input_type == "url":
        if "doi.org" in text:
            doi = text.split("doi.org/")[1]
            return fetch_zotero_json(doi)
        if "alphaxiv.org" in text:
            text = text.replace("alphaxiv.org", "arxiv.org")
        if "huggingface.co/papers/" in text:
            text = text.replace("huggingface.co/papers/", "arxiv.org/abs/")
        url = normalize_url(text)
        resp = requests.post(
            f"{TRANSLATION_SERVER}/web",
            data=url,
            headers={"Content-Type": "text/plain"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    resp = _search(text)

    if resp.status_code == 300:
        choices = resp.json()
        if not choices:
            raise ValueError("No results found")
        if len(choices) == 1:
            return resolve_identifier(next(iter(choices)))
        raise AmbiguousQueryError(text, choices)

    resp.raise_for_status()
    items = resp.json()
    if items:
        return items

    # Zotero returned nothing — fall back to CrossRef for title queries
    candidates = _crossref_search(text)
    if not candidates:
        raise ValueError("No results found")
    if len(candidates) == 1:
        return resolve_identifier(next(iter(candidates)))
    raise AmbiguousQueryError(text, candidates)


# Characters unsafe for use in filesystem paths (replaced with _)
_UNSAFE_KEY_RE = re.compile(r"[^a-zA-Z0-9_]")


def _sanitize_bibtex_keys(bibtex: str) -> str:
    """Replace special characters in BibTeX citation keys with underscores.

    Keys must be safe for use as directory names.
    """

    def _replace_key(m: re.Match) -> str:
        entry_type = m.group(1)
        raw_key = m.group(2)
        clean_key = _UNSAFE_KEY_RE.sub("_", raw_key)
        clean_key = re.sub(r"_+", "_", clean_key)
        return f"@{entry_type}{{{clean_key},"

    return re.sub(r"@(\w+)\{(.+?),", _replace_key, bibtex)


def extract_bibkey(bibtex: str) -> str:
    """Extract the citation key from a BibTeX entry string."""
    match = re.match(r"@\w+\{([^,]+)", bibtex.strip())
    if not match:
        raise ValueError("Could not extract BibTeX key from entry")
    return match.group(1).strip()


def convert_to_bibtex(items: list[dict]) -> str:
    """Convert Zotero JSON items to BibTeX via the translation server."""
    resp = requests.post(
        f"{TRANSLATION_SERVER}/export",
        params={"format": "bibtex"},
        json=items,
        timeout=30,
    )
    resp.raise_for_status()
    return _sanitize_bibtex_keys(resp.text)


def fetch_bibtex(text: str) -> str:
    """Fetch BibTeX for a URL, DOI, ISBN, PMID, or arXiv ID."""
    items = fetch_zotero_json(text)
    if not items:
        raise ValueError("No results found")
    return convert_to_bibtex(items)

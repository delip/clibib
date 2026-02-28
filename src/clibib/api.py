"""Zotero Translation Server client for fetching BibTeX entries."""

import re
from urllib.parse import urlparse

import requests

TRANSLATION_SERVER = (
    "https://t0guvf0w17.execute-api.us-east-1.amazonaws.com/Prod"
)


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
        # Multiple choices: {identifier: {title, description, ...}, ...}
        choices = resp.json()
        if not choices:
            raise ValueError("No results found")
        first_id = next(iter(choices))
        resp = _search(first_id)

    resp.raise_for_status()
    return resp.json()


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

from unittest.mock import MagicMock, patch

import pytest

from clibib.api import _sanitize_bibtex_keys, classify_input, extract_bibkey, fetch_bibtex, normalize_url
from clibib.cli import build_parser, main


# --- CLI argument parsing ---


def test_parser_accepts_query():
    parser = build_parser()
    args = parser.parse_args(["https://example.com"])
    assert args.query == "https://example.com"


def test_parser_accepts_doi():
    parser = build_parser()
    args = parser.parse_args(["10.1038/nature12373"])
    assert args.query == "10.1038/nature12373"


def test_parser_accepts_output_dir():
    parser = build_parser()
    args = parser.parse_args(["-o", "/tmp/bibs", "10.1038/nature12373"])
    assert args.o == "/tmp/bibs"
    assert args.query == "10.1038/nature12373"


def test_parser_output_dir_default_is_none():
    parser = build_parser()
    args = parser.parse_args(["10.1038/nature12373"])
    assert args.o is None


# --- extract_bibkey ---


@pytest.mark.parametrize(
    "bibtex, expected",
    [
        ("@article{doe_2023,\n\ttitle={T},\n}", "doe_2023"),
        ("@book{smith_intro_2020,\n\ttitle={T},\n}", "smith_intro_2020"),
        ("@misc{key123,\n\ttitle={T},\n}", "key123"),
        ("@inproceedings{vaswani_attention_2017,\n\ttitle={T},\n}", "vaswani_attention_2017"),
    ],
)
def test_extract_bibkey(bibtex, expected):
    assert extract_bibkey(bibtex) == expected


def test_extract_bibkey_malformed():
    with pytest.raises(ValueError, match="Could not extract BibTeX key"):
        extract_bibkey("not a bibtex entry")


# --- classify_input ---


@pytest.mark.parametrize(
    "text, expected",
    [
        ("10.1038/nature12373", "search"),
        ("10.1145/3292500.3330919", "search"),
        ("978-0-13-468599-1", "search"),
        ("0131103628", "search"),
        ("2301.07041", "search"),
        ("2301.07041v2", "search"),
        ("12345678", "search"),
        ("Attention is all you need", "search"),
        ("https://arxiv.org/abs/2301.07041", "url"),
        ("https://example.com/paper", "url"),
        ("http://example.com/paper", "url"),
    ],
)
def test_classify_input(text, expected):
    assert classify_input(text) == expected


# --- normalize_url ---


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "https://arxiv.org/pdf/2301.07041",
            "https://arxiv.org/abs/2301.07041",
        ),
        (
            "https://arxiv.org/pdf/2301.07041.pdf",
            "https://arxiv.org/abs/2301.07041",
        ),
        (
            "https://arxiv.org/html/2301.07041",
            "https://arxiv.org/abs/2301.07041",
        ),
        (
            "https://arxiv.org/abs/2301.07041",
            "https://arxiv.org/abs/2301.07041",
        ),
        (
            "https://example.com/article/123.pdf",
            "https://example.com/article/123",
        ),
        (
            "https://example.com/article/123",
            "https://example.com/article/123",
        ),
    ],
)
def test_normalize_url(url, expected):
    assert normalize_url(url) == expected


# --- _sanitize_bibtex_keys ---


@pytest.mark.parametrize(
    "raw, expected_key",
    [
        ("@article{doe_test_2023,\n\ttitle={T},\n}", "doe_test_2023"),
        ("@article{doe:test:2023,\n\ttitle={T},\n}", "doe_test_2023"),
        ("@misc{smith/foo-bar.baz,\n\ttitle={T},\n}", "smith_foo_bar_baz"),
        ("@book{key with spaces,\n\ttitle={T},\n}", "key_with_spaces"),
    ],
)
def test_sanitize_bibtex_keys(raw, expected_key):
    result = _sanitize_bibtex_keys(raw)
    assert f"@" in result
    assert f"{expected_key}," in result


# --- fetch_bibtex (mocked) ---

SAMPLE_ZOTERO_JSON = [
    {
        "itemType": "journalArticle",
        "title": "Test Article",
        "creators": [{"firstName": "Jane", "lastName": "Doe", "creatorType": "author"}],
    }
]

SAMPLE_BIBTEX = """@article{doe_test_2023,
\ttitle = {Test Article},
\tauthor = {Doe, Jane},
}"""


@patch("clibib.api.requests.post")
def test_fetch_bibtex_identifier(mock_post):
    search_resp = MagicMock()
    search_resp.status_code = 200
    search_resp.json.return_value = SAMPLE_ZOTERO_JSON
    search_resp.raise_for_status = MagicMock()

    export_resp = MagicMock()
    export_resp.text = SAMPLE_BIBTEX
    export_resp.raise_for_status = MagicMock()

    mock_post.side_effect = [search_resp, export_resp]

    result = fetch_bibtex("10.1038/nature12373")
    assert "Test Article" in result
    assert mock_post.call_count == 2

    first_call = mock_post.call_args_list[0]
    assert "/search" in first_call.args[0]


@patch("clibib.api.requests.post")
def test_fetch_bibtex_title_search(mock_post):
    """Title queries get a 300 with choices, then a re-query with the top identifier."""
    choices_resp = MagicMock()
    choices_resp.status_code = 300
    choices_resp.json.return_value = {
        "10.1234/found": {
            "itemType": "journalArticle",
            "title": "Attention is all you need",
        },
    }

    resolve_resp = MagicMock()
    resolve_resp.status_code = 200
    resolve_resp.json.return_value = SAMPLE_ZOTERO_JSON
    resolve_resp.raise_for_status = MagicMock()

    export_resp = MagicMock()
    export_resp.text = SAMPLE_BIBTEX
    export_resp.raise_for_status = MagicMock()

    mock_post.side_effect = [choices_resp, resolve_resp, export_resp]

    result = fetch_bibtex("Attention is all you need")
    assert "Test Article" in result
    assert mock_post.call_count == 3

    # Second call should re-query /search with the chosen identifier
    second_call = mock_post.call_args_list[1]
    assert "/search" in second_call.args[0]
    assert second_call.kwargs["data"] == "10.1234/found"


@patch("clibib.api.requests.post")
def test_fetch_bibtex_url(mock_post):
    search_resp = MagicMock()
    search_resp.status_code = 200
    search_resp.json.return_value = SAMPLE_ZOTERO_JSON
    search_resp.raise_for_status = MagicMock()

    export_resp = MagicMock()
    export_resp.text = SAMPLE_BIBTEX
    export_resp.raise_for_status = MagicMock()

    mock_post.side_effect = [search_resp, export_resp]

    result = fetch_bibtex("https://arxiv.org/abs/2301.07041")
    assert "Test Article" in result

    first_call = mock_post.call_args_list[0]
    assert "/web" in first_call.args[0]


@patch("clibib.api.requests.post")
def test_fetch_bibtex_empty_results(mock_post):
    resp = MagicMock()
    resp.json.return_value = []
    resp.raise_for_status = MagicMock()
    mock_post.return_value = resp

    with pytest.raises(ValueError, match="No results found"):
        fetch_bibtex("10.1234/nonexistent")


@patch("clibib.api.requests.post")
def test_fetch_bibtex_http_error(mock_post):
    import requests

    resp = MagicMock()
    resp.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    mock_post.return_value = resp

    with pytest.raises(requests.HTTPError):
        fetch_bibtex("10.1234/nonexistent")


# --- CLI integration (mocked) ---


@patch("clibib.cli.fetch_bibtex")
def test_main_prints_bibtex(mock_fetch, capsys):
    mock_fetch.return_value = SAMPLE_BIBTEX
    main(["10.1038/nature12373"])
    captured = capsys.readouterr()
    assert "Test Article" in captured.out


@patch("clibib.cli.fetch_bibtex")
def test_main_saves_to_output_dir(mock_fetch, capsys, tmp_path):
    mock_fetch.return_value = SAMPLE_BIBTEX
    main(["-o", str(tmp_path), "10.1038/nature12373"])
    captured = capsys.readouterr()
    assert "Test Article" in captured.out
    bib_file = tmp_path / "doe_test_2023.bib"
    assert bib_file.exists()
    assert bib_file.read_text(encoding="utf-8") == SAMPLE_BIBTEX


@patch("clibib.cli.fetch_bibtex")
def test_main_no_output_dir_no_file(mock_fetch, capsys, tmp_path):
    mock_fetch.return_value = SAMPLE_BIBTEX
    main(["10.1038/nature12373"])
    assert not list(tmp_path.iterdir())


@patch("clibib.cli.fetch_bibtex")
def test_main_exits_on_error(mock_fetch):
    mock_fetch.side_effect = Exception("network error")
    with pytest.raises(SystemExit) as exc_info:
        main(["10.1038/bad"])
    assert exc_info.value.code == 1

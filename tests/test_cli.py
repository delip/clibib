from unittest.mock import MagicMock, patch

import pytest

from clibib.api import (
    AmbiguousQueryError,
    _sanitize_bibtex_keys,
    _tokenize,
    classify_input,
    extract_bibkey,
    fetch_bibtex,
    normalize_url,
    rank_candidates,
)
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


def test_parser_first_flag():
    parser = build_parser()
    args = parser.parse_args(["--first", "Attention is all you need"])
    assert args.first is True
    assert args.query == "Attention is all you need"


def test_parser_first_flag_default():
    parser = build_parser()
    args = parser.parse_args(["10.1038/nature12373"])
    assert args.first is False


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


# --- _tokenize ---


def test_tokenize_basic():
    assert _tokenize("Hello World") == {"hello", "world"}


def test_tokenize_strips_punctuation():
    assert _tokenize("Attention Is All You Need!") == {"attention", "is", "all", "you", "need"}


def test_tokenize_empty():
    assert _tokenize("") == set()


def test_tokenize_numbers():
    assert _tokenize("GPT-3 2020") == {"gpt", "3", "2020"}


# --- rank_candidates ---


def test_rank_candidates_exact_match_first():
    candidates = {
        "id1": {"title": "Something else entirely"},
        "id2": {"title": "Attention Is All You Need"},
        "id3": {"title": "Attention mechanisms in deep learning"},
    }
    ranked = rank_candidates("Attention is all you need", candidates)
    assert ranked[0][0] == "id2"


def test_rank_candidates_partial_overlap():
    candidates = {
        "id1": {"title": "Deep Learning"},
        "id2": {"title": "Deep Learning for NLP"},
    }
    ranked = rank_candidates("Deep Learning", candidates)
    # "Deep Learning" exact match should rank higher (higher Jaccard)
    assert ranked[0][0] == "id1"


def test_rank_candidates_empty():
    ranked = rank_candidates("test query", {})
    assert ranked == []


def test_rank_candidates_missing_title():
    candidates = {
        "id1": {"description": "A paper about attention"},
        "id2": {"title": "Attention Is All You Need"},
    }
    ranked = rank_candidates("Attention is all you need", candidates)
    assert ranked[0][0] == "id2"


def test_rank_candidates_uses_description():
    candidates = {
        "id1": {"title": "Paper A", "description": "attention is all you need"},
        "id2": {"title": "Paper B"},
    }
    ranked = rank_candidates("attention is all you need", candidates)
    assert ranked[0][0] == "id1"


# --- AmbiguousQueryError ---


@patch("clibib.api.requests.post")
def test_ambiguous_query_error_raised(mock_post):
    """Multiple candidates in a 300 response should raise AmbiguousQueryError."""
    choices_resp = MagicMock()
    choices_resp.status_code = 300
    choices_resp.json.return_value = {
        "10.1234/a": {"title": "Paper A"},
        "10.1234/b": {"title": "Paper B"},
    }
    mock_post.return_value = choices_resp

    with pytest.raises(AmbiguousQueryError) as exc_info:
        fetch_bibtex("some title query")
    assert exc_info.value.query == "some title query"
    assert len(exc_info.value.candidates) == 2


@patch("clibib.api.requests.get")
@patch("clibib.api.requests.post")
def test_crossref_fallback_on_empty_zotero(mock_post, mock_get):
    """When Zotero returns empty 200, CrossRef fallback should produce candidates."""
    zotero_resp = MagicMock()
    zotero_resp.status_code = 200
    zotero_resp.json.return_value = []
    zotero_resp.raise_for_status = MagicMock()
    mock_post.return_value = zotero_resp

    crossref_resp = MagicMock()
    crossref_resp.json.return_value = {
        "message": {
            "items": [
                {"DOI": "10.1234/a", "title": ["Paper A"], "author": [{"family": "Smith"}]},
                {"DOI": "10.1234/b", "title": ["Paper B"], "author": [{"family": "Jones"}]},
            ]
        }
    }
    crossref_resp.raise_for_status = MagicMock()
    mock_get.return_value = crossref_resp

    with pytest.raises(AmbiguousQueryError) as exc_info:
        fetch_bibtex("some title query")
    assert len(exc_info.value.candidates) == 2
    assert "10.1234/a" in exc_info.value.candidates


@patch("clibib.api.requests.get")
@patch("clibib.api.requests.post")
def test_crossref_fallback_single_result(mock_post, mock_get):
    """Single CrossRef result should auto-resolve without AmbiguousQueryError."""
    zotero_empty = MagicMock()
    zotero_empty.status_code = 200
    zotero_empty.json.return_value = []
    zotero_empty.raise_for_status = MagicMock()

    resolve_resp = MagicMock()
    resolve_resp.status_code = 200
    resolve_resp.json.return_value = SAMPLE_ZOTERO_JSON
    resolve_resp.raise_for_status = MagicMock()

    export_resp = MagicMock()
    export_resp.text = SAMPLE_BIBTEX
    export_resp.raise_for_status = MagicMock()

    mock_post.side_effect = [zotero_empty, resolve_resp, export_resp]

    crossref_resp = MagicMock()
    crossref_resp.json.return_value = {
        "message": {
            "items": [
                {"DOI": "10.1234/only", "title": ["Only Paper"], "author": []},
            ]
        }
    }
    crossref_resp.raise_for_status = MagicMock()
    mock_get.return_value = crossref_resp

    result = fetch_bibtex("some title query")
    assert "Test Article" in result


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
    """Single-choice 300 should auto-resolve without raising AmbiguousQueryError."""
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


@patch("clibib.api.requests.get")
@patch("clibib.api.requests.post")
def test_fetch_bibtex_empty_results(mock_post, mock_get):
    resp = MagicMock()
    resp.json.return_value = []
    resp.raise_for_status = MagicMock()
    mock_post.return_value = resp

    # CrossRef fallback also returns nothing
    crossref_resp = MagicMock()
    crossref_resp.json.return_value = {"message": {"items": []}}
    crossref_resp.raise_for_status = MagicMock()
    mock_get.return_value = crossref_resp

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


# --- CLI disambiguation ---


@patch("clibib.cli.resolve_identifier")
@patch("clibib.cli.convert_to_bibtex")
@patch("clibib.cli.fetch_bibtex")
def test_main_first_flag(mock_fetch, mock_convert, mock_resolve, capsys):
    """--first flag outputs only the highest-ranked result."""
    candidates = {
        "10.1234/wrong": {"title": "Wrong Paper"},
        "10.1234/right": {"title": "Attention Is All You Need"},
    }
    mock_fetch.side_effect = AmbiguousQueryError("Attention is all you need", candidates)
    mock_resolve.return_value = SAMPLE_ZOTERO_JSON
    mock_convert.return_value = SAMPLE_BIBTEX

    main(["--first", "Attention is all you need"])

    captured = capsys.readouterr()
    assert "Test Article" in captured.out
    mock_resolve.assert_called_once()
    selected_id = mock_resolve.call_args[0][0]
    assert selected_id == "10.1234/right"


@patch("clibib.cli.resolve_identifier")
@patch("clibib.cli.convert_to_bibtex")
@patch("clibib.cli.fetch_bibtex")
def test_main_ambiguous_dumps_all(mock_fetch, mock_convert, mock_resolve, capsys):
    """Without --first, all ranked candidates are resolved and printed."""
    candidates = {
        "10.1234/a": {"title": "Paper A"},
        "10.1234/b": {"title": "Paper B"},
    }
    mock_fetch.side_effect = AmbiguousQueryError("query", candidates)
    mock_resolve.return_value = SAMPLE_ZOTERO_JSON
    mock_convert.return_value = SAMPLE_BIBTEX

    main(["query"])

    captured = capsys.readouterr()
    assert "Multiple records found" in captured.err
    assert mock_resolve.call_count == 2
    assert captured.out.count("Test Article") == 2


@patch("clibib.cli.resolve_identifier")
@patch("clibib.cli.convert_to_bibtex")
@patch("clibib.cli.fetch_bibtex")
def test_main_ambiguous_partial_failure(mock_fetch, mock_convert, mock_resolve, capsys):
    """If some candidates fail to resolve, the rest still print."""
    candidates = {
        "10.1234/good": {"title": "Good Paper"},
        "10.1234/bad": {"title": "Bad Paper"},
    }
    mock_fetch.side_effect = AmbiguousQueryError("query", candidates)
    mock_resolve.side_effect = [SAMPLE_ZOTERO_JSON, Exception("timeout")]
    mock_convert.return_value = SAMPLE_BIBTEX

    main(["query"])

    captured = capsys.readouterr()
    assert "Test Article" in captured.out
    assert "Warning:" in captured.err

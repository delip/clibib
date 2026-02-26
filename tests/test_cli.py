from clibib.cli import build_parser, main


def test_parser_accepts_url():
    parser = build_parser()
    args = parser.parse_args(["https://example.com"])
    assert args.url == "https://example.com"


def test_main_prints_placeholder(capsys):
    main(["https://example.com"])
    captured = capsys.readouterr()
    assert "https://example.com" in captured.out

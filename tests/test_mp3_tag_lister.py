import pytest

from mp3_tag_lister import main


def test_mp3_tag_lister_help(capsys):
    args = ["-h"]
    with pytest.raises(SystemExit):
        main(args)
    captured = capsys.readouterr()
    assert "[-h]" in captured.out
    assert "scan_dir" in captured.out

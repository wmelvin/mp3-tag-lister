from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path
from re import match

import eyed3
import pytest
from pydub import AudioSegment

from mp3_tag_lister import LOG_FILE_NAME, fit_str, get_options, main


def skipif_ffmpeg_not_installed():
    file = shutil.which("ffmpeg")
    err = "ffmpeg not installed" if file is None else ""
    return pytest.mark.skipif(file is None, reason=err)


@pytest.fixture()
def temp_mp3file(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, Path]:
    """Create a temporary mp3 file with a tag and return the file path.

    returns (scan_dir, mp3_file, out_dir)
    """
    dir_path = tmp_path_factory.mktemp("test_mp3_tag_lister")
    scan_dir = dir_path / "mp3s_go_here"
    scan_dir.mkdir()
    out_dir = dir_path / "output"
    out_dir.mkdir()
    mp3_file = scan_dir / "example.mp3"
    file_dt = datetime.fromisoformat("2024-01-23T04:56")
    if not mp3_file.exists():
        # Create a 2 second silent audio segment
        audio = AudioSegment.silent(duration=2000)
        audio.export(mp3_file, format="mp3")
        audiofile = eyed3.load(mp3_file)
        if audiofile.tag is None:
            audiofile.initTag()
        audiofile.tag.artist = "Tester"
        audiofile.tag.album = "Tests"
        audiofile.tag.title = "Feeling Testy"
        audiofile.tag.track_num = "1"
        audiofile.tag.release_date = "2023-04-01"
        audiofile.tag.save()
        assert mp3_file.exists()
        time_stamp = file_dt.timestamp()
        os.utime(mp3_file, (time_stamp, time_stamp))
    return scan_dir, mp3_file, out_dir


def test_mp3_tag_lister_help(capsys):
    args = ["-h"]
    with pytest.raises(SystemExit):
        main(args)
    captured = capsys.readouterr()
    assert "[-h]" in captured.out
    assert "scan_dir" in captured.out


@skipif_ffmpeg_not_installed()
def test_mp3_tag_lister(temp_mp3file: tuple[Path, Path, Path]):
    scan_path, mp3_file, out_dir = temp_mp3file

    log_file = out_dir / LOG_FILE_NAME

    args = [str(scan_path), "-o", "mp3_tags.csv", "--output-dir", str(out_dir)]
    main(args)

    csv_file = out_dir / "mp3_tags.csv"
    assert csv_file.exists()

    with csv_file.open() as file:
        lines = file.readlines()

    assert len(lines) == 2

    # Check the header line.
    assert lines[0].strip() == (
        "FullName,FileName,FileModified,"
        "Album,Artist,Title,Track,Year,TDAT,TIT3,error"
    )

    # Check the data line.
    assert lines[1].startswith(f'"{mp3_file}","{mp3_file.name}","2024-01-23 04:56:00",')
    assert '"Tests","Tester","Feeling Testy","1","2023"' in lines[1]

    # Check the log file was created.
    assert log_file.exists()


def test_mp3_tag_lister_bad_output_dir(tmp_path: Path, capsys):
    args = [str(tmp_path), "-o", "mp3_tags.csv", "--output-dir", "no_such_folder"]
    with pytest.raises(SystemExit):
        main(args)
    captured = capsys.readouterr()
    assert "no_such_folder" in captured.err


def test_mp3_tag_lister_bad_scan_dir(tmp_path: Path, capsys):
    args = ["no_such_folder", "-o", "mp3_tags.csv"]
    with pytest.raises(SystemExit):
        main(args)
    captured = capsys.readouterr()
    assert "no_such_folder" in captured.err


def test_mp3_tag_lister_bad_output_dir_in_output_file(tmp_path, capsys):
    args = [str(tmp_path), "-o", "no_such_folder/mp3_tags.csv"]
    with pytest.raises(SystemExit):
        main(args)
    captured = capsys.readouterr()
    assert "no_such_folder" in captured.err


def test_mp3_tag_lister_output_dir_overrides_output_file_dir(tmp_path: Path):
    out_dir1 = tmp_path / "output1"
    out_dir1.mkdir()
    out_dir2 = tmp_path / "output2"
    out_dir2.mkdir()
    out_file = out_dir1 / "mp3_tags.csv"
    args = [str(tmp_path), "-o", str(out_file), "--output-dir", str(out_dir2)]
    mp3_path, out_file, _ = get_options(args)
    assert str(mp3_path) == str(tmp_path)
    assert str(out_file) == str(out_dir2 / "mp3_tags.csv")


@skipif_ffmpeg_not_installed()
def test_mp3_tag_lister_no_log_option(temp_mp3file: tuple[Path, Path, Path]):
    scan_path, mp3_file, out_dir = temp_mp3file

    log_file = out_dir / LOG_FILE_NAME

    args = [
        str(scan_path),
        "-o",
        "mp3_tags.csv",
        "--output-dir",
        str(out_dir),
        "--no-log",
    ]
    main(args)

    csv_file = out_dir / "mp3_tags.csv"
    assert csv_file.exists()

    # Check the log file was not created.
    assert not log_file.exists()


@skipif_ffmpeg_not_installed()
def test_mp3_tag_lister_add_date_time_option(temp_mp3file: tuple[Path, Path, Path]):
    scan_path, mp3_file, out_dir = temp_mp3file
    args = [
        str(scan_path),
        "-o",
        "mp3_tags.csv",
        "--output-dir",
        str(out_dir),
        "--dt",
    ]
    main(args)

    files = list(out_dir.glob("mp3-tags-*.csv"))
    assert len(files) == 1
    csv_file = files[0]
    assert match(csv_file.name, r"mp3-tags-\d{8}_\d{6}.csv")


def test_fit_str_exact_length():
    # Test with a string that is exactly the fit_len
    text = "This is a test string."
    result = fit_str(text, len(text))
    assert result == "This is a test string."


def test_fit_str_less_than_fit_len():
    # Test with a string that is shorter than fit_len
    text = "Short string"
    result = fit_str(text, 20)
    # expect right-padded with spaces
    assert result == "Short string        "


def test_fit_str_greater_than_fit_len():
    # Test with a string that is longer than fit_len
    text = "This is a string that is longer than fit_len."
    result = fit_str(text, 20)
    assert result == "...ger than fit_len."


def test_fit_str_empty_string():
    # Test with an empty string
    text = ""
    result = fit_str(text, 20)
    # expect right-padded with spaces
    assert result == "                    "


def test_fit_str_negative_fit_len():
    # Test with a negative fit_len
    text = "This is a test string."
    with pytest.raises(ValueError):
        fit_str(text, -5)

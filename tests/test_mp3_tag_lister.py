from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path

import eyed3
import pytest
from pydub import AudioSegment

from mp3_tag_lister import get_options, main


def skipif_ffmpeg_not_installed():
    file = shutil.which("ffmpeg")
    err = "ffmpeg not installed" if file is None else ""
    return pytest.mark.skipif(file is None, reason=err)


@pytest.fixture(scope="module")
def temp_mp3file(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    dir_path = tmp_path_factory.mktemp("test_mp3_tag_lister")
    mp3_file = dir_path / "example.mp3"
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
    return dir_path, mp3_file


def test_mp3_tag_lister_help(capsys):
    args = ["-h"]
    with pytest.raises(SystemExit):
        main(args)
    captured = capsys.readouterr()
    assert "[-h]" in captured.out
    assert "scan_dir" in captured.out


@skipif_ffmpeg_not_installed()
def test_mp3_tag_lister(temp_mp3file: tuple[Path, Path]):
    dir_path, mp3_file = temp_mp3file
    args = [str(dir_path), "-o", "mp3_tags.csv", "--output-dir", str(dir_path)]
    main(args)
    csv_file = dir_path / "mp3_tags.csv"
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

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import eyed3
from rich.console import Console

LOG_FILE_NAME = "mp3_tag_lister.log"

__version__ = "2025.05.1"

app_title = f"mp3-tag-lister (v{__version__})"

run_dt = datetime.now()

console = Console()


@dataclass
class Mp3Info:
    FullName: str = ""
    FileName: str = ""
    FileModified: str = ""
    Album: str = ""
    Artist: str = ""
    Title: str = ""
    Track: str = ""
    Year: str = ""
    TDAT: str = ""
    TIT3: str = ""
    error: str = ""


def get_options(arglist=None):
    ap = argparse.ArgumentParser(
        description="Command-line utility to write specific ID3 tags to a CSV output."
    )

    ap.add_argument(
        "scan_dir",
        help="Name of the folder (directory) to scan for mp3 file(s).",
    )

    ap.add_argument(
        "-o",
        "--output-file",
        dest="output_file",
        action="store",
        help=(
            "Optional. Name of output file. Default output is "
            "mp3-tags-(date)_(time).csv."
        ),
    )

    ap.add_argument(
        "--output-dir",
        dest="output_dir",
        action="store",
        help="Optional. Name of output folder. Default is current folder.",
    )

    ap.add_argument(
        "-y",
        "--overwrite",
        dest="do_overwrite",
        action="store_true",
        help="Optional. Overwrite output file if it exists.",
    )

    ap.add_argument(
        "--no-log",
        dest="no_log",
        action="store_true",
        help="Optional. Do not write a log file.",
    )

    ap.add_argument(
        "--dt",
        dest="do_tag",
        action="store_true",
        help="Optional. Add a date_time tag to the output file name.",
    )

    args = ap.parse_args(arglist)

    mp3_path = Path(args.scan_dir)
    if not mp3_path.exists():
        sys.stderr.write(f"\nERROR: Cannot find '{mp3_path}'\n")
        sys.exit(1)

    out_dir = args.output_dir
    if out_dir:
        out_dir = Path(out_dir)
        if not out_dir.exists():
            sys.stderr.write(f"\nERROR: Output folder '{out_dir}' does not exist.\n")
            sys.exit(1)

    out_file = args.output_file
    if out_file:
        out_file = Path(out_file)
        if out_dir:
            out_file = out_dir / out_file.name
        elif not out_file.parent.exists():
            sys.stderr.write(
                f"\nERROR: Output folder '{out_file.parent}' does not exist.\n"
            )
            sys.exit(1)
        if args.do_tag:
            out_file = out_file.parent.joinpath(
                f"{out_file.stem}-{run_dt.strftime('%Y%m%d_%H%M%S')}{out_file.suffix}"
            )
        if out_file.exists() and not args.do_overwrite:
            sys.stderr.write(
                f"\nERROR: Output file '{out_file}' exists. Use -y to overwrite.\n"
            )
            sys.exit(1)
    else:
        out_file = Path(f"mp3-tags-{run_dt.strftime('%Y%m%d_%H%M%S')}.csv")

    if args.no_log:
        log_file = None
    else:
        log_file = out_dir / LOG_FILE_NAME if out_dir else Path(LOG_FILE_NAME)

    return mp3_path, out_file, log_file


def fit_str(text: str, fit_len: int = 70) -> str:
    """Fit text to exact length by either padding with spaces on the right
    or trimming with ellipsis on the left"""
    if fit_len < 0:
        raise ValueError("fit_len must be a positive integer")
    if len(text) == fit_len:
        return text
    if len(text) < fit_len:
        return f"{text}{' ' * (fit_len - len(text))}"
    return f"...{text[-(fit_len - 3) :]}"


def prep(value: str) -> str:
    if not isinstance(value, str):
        return value
    return value.replace('"', "'")


def get_tags(mp3_path: Path) -> list[Mp3Info]:
    files = sorted(mp3_path.glob("**/*.mp3"))
    tags = []
    for file in files:
        console.print(
            f"File: {fit_str(str(file))}",
            end="\r",
            overflow="ellipsis",
            highlight=False,
        )
        logging.info(f"FILE: {file}")
        info = Mp3Info(
            FullName=str(file),
            FileName=file.name,
            FileModified=datetime.fromtimestamp(file.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        )

        try:
            mp3 = eyed3.load(file)
            if mp3 is None:
                info.error = "Failed to read file"
            elif mp3.tag is None:
                info.error = "No tag info"
            else:
                info.Album = prep(mp3.tag.album) if mp3.tag.album else ""
                info.Artist = prep(mp3.tag.artist) if mp3.tag.artist else ""
                info.Title = prep(mp3.tag.title) if mp3.tag.title else ""
                info.Track = prep(mp3.tag.track_num[0]) if mp3.tag.track_num[0] else ""
                bd = mp3.tag.getBestDate()
                if bd:
                    info.Year = bd.year
                info.TDAT = (
                    prep(mp3.tag.getTextFrame("TDAT"))
                    if mp3.tag.getTextFrame("TDAT")
                    else ""
                )
                info.TIT3 = (
                    prep(mp3.tag.getTextFrame("TIT3"))
                    if mp3.tag.getTextFrame("TIT3")
                    else ""
                )

        except Exception as e:
            info.error = prep(str(e))

        tags.append(info)

    return tags


def setup_logging(log_file: Path) -> None:
    """Set up logging to a file.
    Using logging.basicConfig() will not add a handler when one is already
    present. That is a problem if wanting to test log file functionality,
    as pytest has already added its own handlers.
    This function will add a handler to the root logger.
    """
    if not log_file:
        return
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)


def main(arglist=None):
    mp3_path, out_file, log_file = get_options(arglist)

    setup_logging(log_file)

    logging.info("BEGIN")

    console.print(f"\n{app_title}\n", highlight=False, style="cyan")
    console.print(f"Scanning '{mp3_path}'\n")

    tags = get_tags(mp3_path)

    console.print(f"\n\nWriting to '{out_file}'\n")

    with out_file.open("w") as f:
        f.write(
            "FullName,FileName,FileModified,Album,Artist,Title,Track,Year,TDAT,TIT3,error\n"
        )
        for tag in tags:
            f.write(
                f'"{tag.FullName}","{tag.FileName}","{tag.FileModified}",'
                f'"{tag.Album}","{tag.Artist}","{tag.Title}","{tag.Track}",'
                f'"{tag.Year}","{tag.TDAT}","{tag.TIT3}","{tag.error}"\n'
            )

    logging.info(f"END: Run time = {datetime.now() - run_dt}")


if __name__ == "__main__":
    main()

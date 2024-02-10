from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import eyed3

__version__ = "2024.02.1.dev0"

app_title = f"mp3-tag-lister (v{__version__})"

run_dt = datetime.now()


@dataclass
class Mp3Info:
    FullName: str
    FileName: str
    FileModified: str
    Album: str
    Artist: str
    Title: str
    Track: str
    Year: str
    TDAT: str
    TIT3: str
    error: str


def get_options(arglist=None):
    ap = argparse.ArgumentParser(
        description="Command-line utility to write specific ID3 tags to a CSV output."
    )

    ap.add_argument(
        "scan_dir",
        help="Name of the folder to scan for mp3 file(s).",
    )

    ap.add_argument(
        "-o",
        "--output-file",
        dest="output_file",
        action="store",
        help= (
            "Optional. Name of output file. Default output is "
            "mp3-tags-(date)_(time).csv."
        ),
    )

    ap.add_argument(
        "-y",
        "--overwrite",
        dest="do_overwrite",
        action="store_true",
        help="Optional. Overwrite output file if it exists.",
    )

    args = ap.parse_args(arglist)

    mp3_path = Path(args.scan_dir)
    if not mp3_path.exists():
        sys.stderr.write(f"\nERROR: Cannot find '{args.mp3_file}'\n")
        sys.exit(1)

    out_file = args.output_file
    if out_file:
        out_file = Path(out_file)
        if not out_file.parent.exists():
            sys.stderr.write(
                f"\nERROR: Output folder '{out_file.parent}' does not exist.\n"
            )
            sys.exit(1)
        if out_file.exists() and not args.do_overwrite:
            sys.stderr.write(
                f"\nERROR: Output file '{out_file}' exists. Use -y to overwrite.\n"
            )
            sys.exit(1)
    else:
        out_file = Path(f"mp3-tags-{run_dt.strftime('%Y%m%d_%H%M%S')}.csv")

    return mp3_path, out_file


def get_tags(mp3_path: Path) -> list:
    files = sorted(mp3_path.glob("**/*.mp3"))
    tags = []
    for file in files:
        logging.info(f"FILE: {file}")
        info = Mp3Info
        info.FullName = str(file)
        info.FileName = file.name
        info.FileModified = file.stat().st_mtime

        try:
            mp3 = eyed3.load(file)
            if mp3 is None:
                info.error = "Failed to read file"
            elif mp3.tag is None:
                info.error = "No tag info"
            else:
                info.Album = mp3.tag.album if mp3.tag.album else ""
                info.Artist = mp3.tag.artist if mp3.tag.artist else ""
                info.Title = mp3.tag.title if mp3.tag.title else ""
                info.Track = mp3.tag.track_num[0] if mp3.tag.track_num[0] else ""
                info.Year = mp3.tag.getBestDate() if mp3.tag.getBestDate() else ""
                info.TDAT = (
                    mp3.tag.getTextFrame("TDAT") if mp3.tag.getTextFrame("TDAT") else ""
                )
                info.TIT3 = (
                    mp3.tag.getTextFrame("TIT3") if mp3.tag.getTextFrame("TIT3") else ""
                )

        except Exception as e:
            info.error = str(e)

        tags.append(info)

    return tags


def main(arglist=None):
    logging.basicConfig(
        filename="mp3_tag_lister.log",
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s %(message)s",
    )
    logging.info("BEGIN")

    mp3_path, out_file = get_options(arglist)

    if out_file:
        print(f"\n{app_title}\n")
        print(f"Scanning '{mp3_path}' for mp3 file(s).\n")

    tags = get_tags(mp3_path)

    print(f"Writing to '{out_file}'\n")

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
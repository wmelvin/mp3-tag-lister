
# mp3-tag-lister

The mp3-tag-lister command-line tool scans a folder for mp3 files and writes specific ID3 tags to a CSV output.

The [eyed3](https://pypi.org/project/eyed3/) library is used to read the ID3 tags.

## Usage

```
usage: mp3_tag_lister [-h] [-o OUTPUT_FILE] [--output-dir OUTPUT_DIR] [-y]
                   scan_dir

Command-line utility to write specific ID3 tags to a CSV output.

positional arguments:
  scan_dir              Name of the folder (directory) to scan for mp3
                        file(s).

options:
  -h, --help            show this help message and exit
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Optional. Name of output file. Default output is
                        mp3-tags-(date)_(time).csv.
  --output-dir OUTPUT_DIR
                        Optional. Name of output folder. Default is current
                        folder.
  -y, --overwrite       Optional. Overwrite output file if it exists.
```

## Reference

PyPI: [eyed3](https://pypi.org/project/eyed3/)

Documentation: [eyeD3](https://eyed3.readthedocs.io/en/latest/)

GitHub: [nicfit/eyeD3](https://github.com/nicfit/eyeD3)

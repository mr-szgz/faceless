# Faceless

Faceless analyzes images and video using Ultralytics YOLO to segregate faceless media and/or group media into YOLO labelled folders.

## Install

Download Binary for your system or install .whl from latest Release
Visit release and find latest <https://github.com/mr-szgz/faceless/releases>

Install the whl directly like 

```sh
pip install https://github.com/mr-szgz/faceless/releases/download/v0.3.1/faceless-0.3.1-py3-none-any.whl --force
```

or clone the repo and you can `pip install -e .` (`mise run devel` reccomended)


## Usage

**Automatically Move Faceless Media and Group by Label**

```sh
faceless "p:/path/to/media" -Auto
```

```sh
$ faceless --help
usage: faceless [-h] [-Path PATH_OPTION] [-Label] [-Conf CONF] [-Directory DIRECTORY] [-Auto] [-Version] [path]                                    

positional arguments:
  path                  Source directory containing images

options:
  -h, --help            show this help message and exit
  -Path PATH_OPTION, --path PATH_OPTION
                        Source directory containing images
  -Label, --label, -Force, --force
                        Force regeneration of labels
  -Conf CONF, --conf CONF
                        Model confidence threshold
  -Directory DIRECTORY, --directory DIRECTORY
                        Output directory name for moved files (default: faceless)
  -Auto, --auto, -a     Move non-matching files into per-label folders under the output directory
  -Version, --version, -v
                        show program's version number and exit
```

## Changes

See [CHANGELOG.md](./CHANGELOG.md) for release notes and version history.

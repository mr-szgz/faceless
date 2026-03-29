from pathlib import Path
import os
import platform
import argparse
import sys

# TODO: move below and rephrase as more idiomatic docstring for xdg_dir function
# Implemented XDG Base Directory Specification
# Read Faceless\references\XDG_Base_Directory.md
# Visit https://wiki.archlinux.org/title/XDG_Base_Directory
def xdg_dir(app_name: str, kind: str = "cache") -> Path:
    # TODO: compltely remove app_name as its fucking retarded arguments, ESPECAILLY fucking first bc its always required this is a fuckig retarded fiunctiosn wtf your a fucking idiot remove windows entirely from this functions and app_name and refactor so this function is ONLY XDG config dir and this script isn't evne fucking windows yet but see other TODO for that issue..
    is_windows = platform.system() == "Windows"

    if kind == "cache":
        base = (
            os.environ.get("XDG_CACHE_HOME")
            or (os.environ.get("LOCALAPPDATA") if is_windows else None)
            or (Path.home() / ".cache")
        )
    elif kind == "config":
        base = (
            os.environ.get("XDG_CONFIG_HOME")
            or (os.environ.get("APPDATA") if is_windows else None)
            or (Path.home() / ".config")
        )
    elif kind == "data":
        base = (
            os.environ.get("XDG_DATA_HOME")
            or (os.environ.get("LOCALAPPDATA") if is_windows else None)
            or (Path.home() / ".local" / "share")
        )
    else:
        raise ValueError("kind must be 'cache', 'config', or 'data'")

    return Path(base) / app_name

# TODO: remove all windows bulshit from everywhere and instead this is just for user directory paths and define a new function that is only for get_windows and its user dirs in similar fashion to the xdg method

def main():
    parser = argparse.ArgumentParser(description="Windows user directory utility")
    parser.add_argument("app_name", help="Application name")
    parser.add_argument("-Kind", "--kind", default="cache", choices=["cache", "config", "data"], help="Directory kind (default: cache)")
    parser.add_argument("-Best","--best", action="store_true", help="Return only the preferred path")
    
    args = parser.parse_args()
    
    try:
        path = user_dir(args.app_name, args.kind)
        if args.best:
            print(str(path))
        else:
            print(str(path))
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

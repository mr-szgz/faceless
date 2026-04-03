import os
import sys
import subprocess
from pathlib import Path

def ask_user_yn(challenge_text: str, defaults_yes: bool = False) -> bool:
    prompt = " [Y/n] " if defaults_yes else " [y/N] "
    answer = input(f"{challenge_text}{prompt}").strip().lower()
    if answer == "":
        return defaults_yes
    if answer in ("y", "yes"):
        return True
    if answer in ("n", "no"):
        return False
    return defaults_yes

def open_user_folder(open_path: str | Path):
    open_path = Path(open_path)
    if sys.platform.startswith("win"):
        return os.startfile(open_path)
    elif sys.platform == "darwin":
        return subprocess.run(["open", str(open_path)])
    else:
        return subprocess.run(["xdg-open", str(open_path)])
    raise RuntimeError("Unsupported platform")

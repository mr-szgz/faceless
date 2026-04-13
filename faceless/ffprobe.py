from pathlib import Path
import subprocess
from fractions import Fraction

from faceless.config import DEPENDENCIES_DIR
import os
env = {**os.environ, "PYTHONNOUSERSITE": "1", "PYTHONPATH": ""}

def run_ffprobe_dump(path: str | Path):
    from tqdm import tqdm
    dependencies = Path(DEPENDENCIES_DIR).expanduser().resolve()
    source_path = Path(path).expanduser().resolve()
    output_dir = source_path / "ffprobes"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    source_files = sorted(path for path in source_path.iterdir() if path.is_file())
    progress = tqdm(source_files, desc="Probing media files")

    for item in progress:
        if not item.is_file():
            continue

        output_path = output_dir / f"{item.stem}.txt"
        with output_path.open("wb") as handle:
            subprocess.check_call(
                [
                    str(dependencies / "ffprobe.exe"),
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-count_frames",
                    "-show_entries",
                    "stream=avg_frame_rate,r_frame_rate,nb_read_frames",
                    "-of",
                    "default=noprint_wrappers=1:nokey=0",
                    str(item),
                ],
                env=env,
                stdout=handle,
            )
    
    calc_median_fps(path)
    calc_median_frames(path)
            
    return output_dir

def get_probe_for_source_file(source: Path):
    source = source.expanduser().resolve()
    return source / "ffprobes" / f"{source.stem}.txt"

def parse_probe_file(probe_file: Path) -> dict[str, str]:
    properties: dict[str, str] = {}

    with probe_file.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            key, separator, value = line.strip().partition("=")
            if not separator:
                continue

            properties[key] = value

    return properties

def calc_median_fps(source: Path):
    source = source.expanduser().resolve()
    probes_dir = source / "ffprobes"
    output_path = source / "median_framerate.txt"
    frame_rates: list[Fraction] = []

    with os.scandir(probes_dir) as entries:
        for entry in entries:
            if not entry.is_file() or not entry.name.endswith(".txt"):
                continue

            properties = parse_probe_file(Path(entry.path))
            frame_rate = properties.get("r_frame_rate")
            if frame_rate is None:
                continue

            try:
                frame_rates.append(Fraction(frame_rate))
            except (ValueError, ZeroDivisionError):
                pass

    if not frame_rates:
        raise FileNotFoundError(f"No valid r_frame_rate entries found in {probes_dir}")

    frame_rates.sort()
    middle = len(frame_rates) // 2
    if len(frame_rates) % 2:
        median_rate = frame_rates[middle]
    else:
        median_rate = (frame_rates[middle - 1] + frame_rates[middle]) / 2

    output_path.write_text(
        f"r_frame_rate={median_rate.numerator}/{median_rate.denominator}\n",
        encoding="utf-8",
    )
    return output_path

def calc_median_frames(source: Path):
    source = source.expanduser().resolve()
    probes_dir = source / "ffprobes"
    output_path = source / "median_frames.txt"
    frame_counts: list[int] = []

    with os.scandir(probes_dir) as entries:
        for entry in entries:
            if not entry.is_file() or not entry.name.endswith(".txt"):
                continue

            properties = parse_probe_file(Path(entry.path))
            frame_count = properties.get("nb_read_frames")
            if frame_count is None:
                continue

            try:
                frame_counts.append(int(frame_count))
            except ValueError:
                pass

    if not frame_counts:
        raise FileNotFoundError(f"No valid nb_read_frames entries found in {probes_dir}")

    frame_counts.sort()
    middle = len(frame_counts) // 2
    if len(frame_counts) % 2:
        median_frames = Fraction(frame_counts[middle], 1)
    else:
        median_frames = Fraction(frame_counts[middle - 1] + frame_counts[middle], 2)

    if median_frames.denominator == 1:
        value = str(median_frames.numerator)
    else:
        value = f"{median_frames.numerator}/{median_frames.denominator}"

    output_path.write_text(
        f"nb_read_frames={value}\n",
        encoding="utf-8",
    )
    return output_path

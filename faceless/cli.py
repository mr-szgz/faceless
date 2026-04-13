#!/usr/bin/env python3
import argparse
import glob
import os
import shutil
import sys
from pathlib import Path

from tqdm import tqdm
from ultralytics import YOLO
from faceless.config import get_config, DEPENDENCIES_DIR, DEFAULT_YOLO_MATCH_CLASSES, DEFAULT_YOLO_FACE_CLASSES, DEFAULT_MODEL_NAME
from pathlib import Path
from ultralytics.utils.downloads import attempt_download_asset

def main() -> None:
    parser = argparse.ArgumentParser(prog="faceless")
    parser.add_argument(
        "path", nargs="?", help="Source directory containing videos/images"
    )
    conf_float = get_config("detect", "yolo_confidence", 0.2)
    parser.add_argument(
        "-Confidence", "--confidence", dest="conf_float", type=float, default=conf_float, help=f"YOLO confidence"
    )
    yolo_match_classes = get_config("detect", "yolo_match_classes", DEFAULT_YOLO_MATCH_CLASSES)
    parser.add_argument(
        "-RequireIds",
        "--require-ids",
        default=yolo_match_classes,
        dest="yolo_match_classes",
        help=f"YOLO class IDs to keep comma-separated. All classes available in faceless/datasets/OpenImagesV7.yaml",
    )
    
    output_folder = get_config('project', 'output_folder', 'faceless')
    parser.add_argument(
        "-Output",
        "--output",
        default=output_folder,
        dest="output_folder",
        help=f"Override output directory",
    )

    args = parser.parse_args(sys.argv[1:])
    
    sources_path = Path(args.path).expanduser().resolve()

    labels = sources_path / "labels"
    scan_markers = labels / ".scanned"
    source_files = sorted(path for path in sources_path.iterdir() if path.is_file())
    source_files_by_name = {path.name: path for path in source_files}
    source_stems = {path.stem for path in source_files}
    video_extensions = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".webm", ".m4v"}

    def get_label_paths(path: Path) -> list[Path]:
        label_paths: list[Path] = []
        label_path = labels / f"{path.stem}.txt"
        if label_path.is_file():
            label_paths.append(label_path)

        if path.suffix.lower() in video_extensions:
            frame_label_paths = sorted(labels.glob(f"{path.stem}_*.txt"))
            label_paths.extend(
                frame_label_path
                for frame_label_path in frame_label_paths
                if frame_label_path.stem not in source_stems
            )

        return label_paths

    def get_scan_marker_path(path: Path) -> Path:
        return scan_markers / f"{path.name}.done"

    def has_completed_scan(path: Path) -> bool:
        if get_scan_marker_path(path).is_file():
            return True

        if path.suffix.lower() in video_extensions:
            return False

        return bool(get_label_paths(path))

    generate_labels = not labels.is_dir() or any(
        not has_completed_scan(path) for path in source_files
    )
    
    dependencies = Path(get_config("project", "dependencies", DEPENDENCIES_DIR))
    print(f"[CHECK] Installed dependencies {dependencies}")
    
    from faceless.ffprobe import run_ffprobe_dump
    ffprobes = sources_path / "ffprobes"

    def has_completed_ffprobe(path: Path) -> bool:
        return (ffprobes / f"{path.stem}.txt").is_file()

    generate_ffprobes = not ffprobes.is_dir() or any(
        not has_completed_ffprobe(path) for path in source_files
    )

    if not generate_ffprobes and ffprobes.is_dir() and next(ffprobes.glob("*.txt"), None) is not None:
        print(f"[INFO] Existing ffprobe dumps found {ffprobes}. Skipping ffprobe generation.")
    elif generate_ffprobes and source_files:
        run_ffprobe_dump(sources_path)
    

    model_name = get_config("detect", "model_name", DEFAULT_MODEL_NAME)
    print(f"[CHECK] Model download {model_name} ")
    model_file = Path(attempt_download_asset(dependencies / "models" / model_name)).resolve()
    model = YOLO(model_file)
    
    if not generate_labels and labels.is_dir() and next(labels.glob("*.txt"), None) is not None:
        print(f"[INFO] Existing labels found {labels}. Skipping labels generation.")
    elif generate_labels and source_files:
        labels.mkdir(parents=True, exist_ok=True)
        scan_markers.mkdir(parents=True, exist_ok=True)
        escaped_source = glob.escape(str(sources_path))
        ends_with_sep = escaped_source.endswith(("/", os.sep))
        source_pattern = f"{escaped_source}{'' if ends_with_sep else os.sep}*.*"
        print(f"[INFO] Generating labels in {labels}")
        
        vid_stride=300   # A value of 1 processes every frame, higher values skip frames.
        print(f"[DEBUG] Predict vid_stride={vid_stride}")
        
        half=True        # Enables half-precision (FP16) inference, which can speed up model inference on supported GPUs with minimal impact on accuracy.
        print(f"[DEBUG] Predict half={half} (FP16 inference)")
        
        batch=5
        print(f"[DEBUG] Predict batch={batch}")
        
        import torch
        if torch.cuda.is_available():
            print(f"[DEBUG] Torch CUDA Available. {torch.__version__}")
        else:
            print(f"[WARN] Torch CUDA Unavailable. {torch.__version__}. Performance params will be disabled for CPU-Only.")
            half=False
            batch=1
        
        for result in model.predict( # pyright: ignore[reportOptionalMemberAccess]
            source=source_pattern,
            conf=args.conf_float,
            project=str(sources_path),
            name=".",
            save=False,
            save_txt=True,
            save_conf=True,
            batch=batch,
            vid_stride=vid_stride,
            half=half,
            stream=True,
            exist_ok=True,
            verbose=True,
        ):
            result_name = Path(str(getattr(result, "path", ""))).name
            result_source_file = source_files_by_name.get(result_name)
            if result_source_file is not None:
                get_scan_marker_path(result_source_file).touch()
    
    def parse_class_ids(selector_text: str) -> set[int]:
        return {int(token.strip()) for token in selector_text.split(",") if token.strip()}

    classes_to_keep = parse_class_ids(args.yolo_match_classes)
    required_face_classes = parse_class_ids(DEFAULT_YOLO_FACE_CLASSES)

    label_names: dict[int, str] = {}
    if model is not None:
        if isinstance(model.names, dict):
            label_names = {int(key): str(value) for key, value in model.names.items()}
        else:
            label_names = {index: str(value) for index, value in enumerate(model.names)}

    moved_count = 0
    skipped_unlabeled_count = 0
    progress = tqdm(source_files, desc="Processing labels..", unit="file")
    for source_file in progress:
        label_counts: dict[int, int] = {}
        if not has_completed_scan(source_file):
            skipped_unlabeled_count += 1
            progress.set_postfix_str(
                f"moved={moved_count} skipped_unlabeled={skipped_unlabeled_count}"
            )
            continue

        available_label_paths = get_label_paths(source_file)
        progress.set_postfix_str(
            f"moved={moved_count} skipped_unlabeled={skipped_unlabeled_count}"
        )

        for current_label_path in available_label_paths:
            for line in current_label_path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                class_id = int(float(line.split()[0].lstrip("\ufeff")))
                label_counts[class_id] = label_counts.get(class_id, 0) + 1

        detected_classes = set(label_counts)
        has_required_id = bool(detected_classes & classes_to_keep)
        has_face_present = bool(detected_classes & required_face_classes)

        if has_required_id and has_face_present:
            continue

        final_destination = sources_path / args.output_folder
        if label_counts:
            top_class_id = sorted(label_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
            save_class_name = label_names.get(top_class_id, str(top_class_id))
            final_destination = sources_path / args.output_folder / save_class_name

        final_destination.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(final_destination / source_file.name))
        moved_count += 1

    print(f"Moved {moved_count} file(s).")
    print(f"Skipped {skipped_unlabeled_count} unlabeled file(s).")


if __name__ == "__main__":
    main()

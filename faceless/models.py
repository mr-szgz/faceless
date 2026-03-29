from pathlib import Path

from ultralytics.utils.downloads import attempt_download_asset

from .configs import USER_DATA

def download_models(model_name: str = "yolov8n-oiv7.pt"):
    models_dir = USER_DATA / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    destination = models_dir / model_name
    destination.write_bytes(Path(attempt_download_asset(model_name)).read_bytes())
    return destination

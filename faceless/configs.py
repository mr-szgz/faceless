from pathlib import Path
from urllib.request import urlretrieve

USER_DATA = Path.home() / ".faceless"

def download_configs():
    configs_dir = USER_DATA / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)
    destination = configs_dir / "OpenImagesV7.yaml"
    urlretrieve("https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/datasets/OpenImagesV7.yaml", destination)
    return destination

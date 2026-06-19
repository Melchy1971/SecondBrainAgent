from pathlib import Path
from .config import load_simple_yaml

def load_service_config(project_root: Path) -> dict:
    data = load_simple_yaml(project_root / "config" / "service.yaml")
    return data.get("service", data)

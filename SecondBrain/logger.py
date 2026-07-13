from pathlib import Path
from .utils import now_datetime

def log(project_root: Path, message: str) -> None:
    p = project_root / "logs" / "import.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.open("a", encoding="utf-8").write(f"[{now_datetime()}] {message}\n")

def log_error(project_root: Path, message: str) -> None:
    p = project_root / "logs" / "error.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.open("a", encoding="utf-8").write(f"[{now_datetime()}] ERROR {message}\n")

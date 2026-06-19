from pathlib import Path
from .utils import now_datetime

def audit(project_root: Path, event: str, detail: str = "") -> None:
    p = project_root / "logs" / "audit.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    safe_detail = detail.replace("\n", " ")[:1000]
    p.open("a", encoding="utf-8").write(f"[{now_datetime()}] {event} | {safe_detail}\n")

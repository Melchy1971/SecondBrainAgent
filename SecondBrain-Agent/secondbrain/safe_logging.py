from pathlib import Path
import re
from .utils import now_datetime

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_\-]{10,}",
    r"(api[_-]?key\s*[:=]\s*)[A-Za-z0-9_\-]{8,}",
    r"(password\s*[:=]\s*)[^\s]{4,}",
    r"(token\s*[:=]\s*)[A-Za-z0-9_\-\.]{8,}",
]

def redact(text: str) -> str:
    out = text
    for pattern in SECRET_PATTERNS:
        out = re.sub(pattern, lambda m: m.group(1) + "***REDACTED***" if m.groups() else "***REDACTED***", out, flags=re.IGNORECASE)
    return out

def safe_log(project_root: Path, log_name: str, message: str) -> None:
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    safe = redact(message).replace("\n", " ")[:4000]
    (log_dir / log_name).open("a", encoding="utf-8").write(f"[{now_datetime()}] {safe}\n")

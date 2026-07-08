from pathlib import Path
import json
from .path import from_settings_mapping
from .utils import now_date
from .config import load_simple_yaml
from .vault_scan import iter_markdown, read_note, word_tokens

def build_federation_index(project_root: Path, settings: dict) -> Path:
    vault = from_settings_mapping(settings, project_root).vault
    config = load_simple_yaml(project_root / "config" / "vaults.yaml")
    vaults = config.get("vaults", {})
    folder = vault / "38_MultiVault"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Federation_Index.md"

    lines = ["# Multi-Vault Federation Index", "", f"Aktualisiert: {now_date()}", "", "| Vault | Status | Markdown-Dateien |", "|---|---|---:|"]
    for name, cfg in vaults.items():
        path = Path(cfg.get("path", ""))
        enabled = cfg.get("enabled", False)
        count = len(list(path.rglob("*.md"))) if enabled and path.exists() else 0
        lines.append(f"| {name} | {'enabled' if enabled else 'disabled'} | {count} |")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target

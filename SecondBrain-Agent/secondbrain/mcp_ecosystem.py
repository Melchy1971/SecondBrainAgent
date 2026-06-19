from pathlib import Path
from .utils import now_date
from .config import load_simple_yaml

def write_mcp_ecosystem_status(project_root: Path, settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "72_MCPEcosystem"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "MCP_Ecosystem_Status.md"
    cfg = load_simple_yaml(project_root / "config" / "mcp_ecosystem.yaml").get("mcp_ecosystem", {})
    lines = ["# MCP Ecosystem Status", "", f"Aktualisiert: {now_date()}", "", "| MCP | Status | Priorität |", "|---|---|---|"]
    for name, data in cfg.items():
        lines.append(f"| {name} | {data.get('status')} | {data.get('priority')} |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

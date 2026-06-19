from pathlib import Path
from .utils import now_date

def write_mcp_hub_status(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "37_MCPHub"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "MCP_Hub_Status.md"

    connectors = [
        "Claude Desktop", "ChatGPT", "Gemini", "Perplexity", "Ollama",
        "GitHub", "Gmail", "Google Calendar", "Google Drive", "Notion",
        "Jira", "Confluence", "Home Assistant", "myGEKKO", "PostgreSQL",
        "Docker", "Unraid"
    ]

    lines = ["# MCP Hub Status", "", f"Aktualisiert: {now_date()}", "", "| Connector | Status | Aktion |", "|---|---|---|"]
    for c in connectors:
        lines.append(f"| {c} | prepared | Aktivierung konfigurieren |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

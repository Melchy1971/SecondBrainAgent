from pathlib import Path
from .v9_common import now_date, ensure

def write_monitoring_report(vault: Path, agent_root: Path) -> Path:
    folder = ensure(vault / "84_MonitoringTelemetry")
    target = folder / f"{now_date()}_monitoring.md"
    logs = list((agent_root / "logs").glob("*")) if (agent_root / "logs").exists() else []
    scripts = list((agent_root / "scripts").glob("*.py")) if (agent_root / "scripts").exists() else []
    modules = list((agent_root / "modules").glob("*")) if (agent_root / "modules").exists() else []
    lines = [
        "# Monitoring & Telemetry",
        "",
        f"Datum: {now_date()}",
        "",
        "| Bereich | Wert |",
        "|---|---:|",
        f"| Logdateien | {len(logs)} |",
        f"| Skripte | {len(scripts)} |",
        f"| Module | {len(modules)} |",
        "",
        "## Checks",
        "",
        "- Importfehler prüfen.",
        "- AI-Fehler prüfen.",
        "- Backupstatus prüfen.",
        "- Connectorstatus prüfen.",
        "- Pluginstatus prüfen.",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

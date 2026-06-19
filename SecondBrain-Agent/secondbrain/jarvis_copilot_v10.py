from pathlib import Path
from .v10_common import VAULT, now_date, ensure

def read_optional(p: Path, limit=3000):
    if not p.exists():
        return "Nicht vorhanden."
    return p.read_text(encoding="utf-8", errors="ignore")[:limit]

def write_jarvis_copilot(vault: Path = VAULT) -> Path:
    target = ensure(vault / "125_JarvisCopilot") / f"{now_date()}_jarvis-copilot.md"
    sources = [
        vault / "121_DailyOperatingSystem" / f"{now_date()}_daily-os.md",
        vault / "123_PersonalKPIs" / f"{now_date()}_personal-kpis.md",
        vault / "119_KnowledgeIntelligenceDashboard" / "Knowledge_Intelligence_Dashboard_v99.md",
        vault / "112_ChiefOfStaff" / f"{now_date()}_chief-of-staff-v98.md",
    ]
    lines = ["# Jarvis Copilot v10", "", f"Datum: {now_date()}", "", "## Lage", ""]
    for src in sources:
        lines.append(f"### {src.parent.name}")
        lines.append(read_optional(src))
        lines.append("")
    lines += ["## Copilot-Regeln", "", "- Keine Löschaktionen.", "- Keine E-Mails senden.", "- Empfehlungen review-first.", "- Lokales Vault-Wissen bevorzugen."]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

from pathlib import Path
import re
from .utils import now_date, now_datetime
from .vault_scan import iter_markdown, read_note

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_\-]{20,}",
    r"api[_-]?key\s*[:=]\s*[A-Za-z0-9_\-]{16,}",
    r"password\s*[:=]\s*[^\s]{6,}",
    r"token\s*[:=]\s*[A-Za-z0-9_\-\.]{16,}",
]

def scan_secret_leaks(settings: dict) -> list[dict]:
    vault = Path(settings["vault_path"])
    findings = []
    for note in iter_markdown(vault):
        text = read_note(note)
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                findings.append({"file": str(note), "pattern": pattern})
    return findings

def write_governance_report(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    target_dir = vault / "99_System" / "governance"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{now_date()}_governance-report.md"
    findings = scan_secret_leaks(settings)

    lines = [
        f"# Governance Report {now_datetime()}",
        "",
        "## Secret-Leak-Prüfung",
        "",
        f"- Findings: {len(findings)}",
        "",
        "| Datei | Muster |",
        "|---|---|",
    ]
    if not findings:
        lines.append("| Keine Findings | - |")
    for f in findings:
        lines.append(f"| `{f['file']}` | `{f['pattern']}` |")

    lines += [
        "",
        "## Regeln",
        "",
        "- Keine API-Keys im Vault speichern.",
        "- `secrets.local.yaml` nicht teilen.",
        "- E-Mail-Versand bleibt deaktiviert.",
        "- Destruktive Aktionen bleiben deaktiviert.",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

from pathlib import Path
from .path import from_settings_mapping
from .utils import now_date

MODULES = ["CRM", "ERP", "DMS", "Projektmanagement", "Prozessmanagement", "Wissensmanagement", "Finanzen", "Gesundheit", "Lernen", "Verein", "Smart Home"]

def write_business_os(settings: dict) -> Path:
    vault = from_settings_mapping(settings).vault
    folder = vault / "63_BusinessOS"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Business_OS_Modules.md"
    lines = ["# Autonomous Business OS", "", f"Aktualisiert: {now_date()}", "", "| Modul | Status |", "|---|---|"]
    for m in MODULES:
        lines.append(f"| {m} | vorbereitet |")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

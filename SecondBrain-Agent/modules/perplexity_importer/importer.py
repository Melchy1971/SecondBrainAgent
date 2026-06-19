from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
from datetime import datetime
import json
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

TAG_RULES = {
    "tischtennis": ["tischtennis", "ttr", "belag", "holz", "victas", "ventus", "rozena"],
    "sap": ["sap", "p01", "p02", "pfs", "crm", "ctam", "cisco", "ea"],
    "obsidian": ["obsidian", "vault", "secondbrain", "markdown", "mcp"],
    "ki": ["chatgpt", "claude", "gemini", "perplexity", "ollama", "ki", "ai"],
    "gesundheit": ["diabetes", "gewicht", "hba1c", "ozempic", "tresiba", "training"],
    "projekt": ["projekt", "roadmap", "sprint", "release", "backlog"],
    "code": ["python", "docker", "github", "react", "typescript", "postgres"],
    "verein": ["ttc", "zaberfeld", "verein", "turnier", "jedermann"],
}

def slugify(value: str, max_len: int = 90) -> str:
    value = value.strip() or "Ohne Titel"
    value = re.sub(r"[^\w\sÄÖÜäöüß.-]", "-", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"-+", "-", value)
    return value[:max_len].strip("._-") or "Ohne_Titel"

def derive_tags(title: str, body: str, source_tag: str) -> list[str]:
    low = (title + "\n" + body).lower()
    tags = [source_tag, "import"]
    for tag, keys in TAG_RULES.items():
        if any(k.lower() in low for k in keys):
            tags.append(tag)
    return sorted(set(tags))

def frontmatter(title: str, created: str, tags: list[str], source: str, source_id: str = "") -> str:
    tag_lines = "\n".join(f"  - {tag}" for tag in tags)
    return f"""---
title: "{title.replace('"', "'")}"
type: {source}_conversation
source: {source}
source_id: "{source_id}"
created: {created}
tags:
{tag_lines}
---

"""

def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def maybe_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None

def extract_zip(zip_path: Path) -> Path:
    tmp = Path(tempfile.mkdtemp())
    with ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp)
    return tmp

def write_report(report_folder: Path, source: str, zip_path: Path, imported: list[str], errors: list[dict]) -> dict:
    report_folder.mkdir(parents=True, exist_ok=True)
    report = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "zip": str(zip_path),
        "imported_count": len(imported),
        "error_count": len(errors),
        "imported": imported,
        "errors": errors,
    }
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    json_path = report_folder / f"{stamp}_{source}_import_report.json"
    md_path = report_folder / f"{stamp}_{source}_import_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# {source.title()} Import Report",
        "",
        f"Zeit: {report['time']}",
        f"ZIP: `{zip_path}`",
        f"Importiert: {len(imported)}",
        f"Fehler: {len(errors)}",
        "",
        "## Importierte Dateien",
        "",
    ]
    lines += [f"- `{p}`" for p in imported[:300]] or ["- Keine."]
    if errors:
        lines += ["", "## Fehler", ""]
        lines += [f"- {e}" for e in errors]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    report["report_json"] = str(json_path)
    report["report_md"] = str(md_path)
    return report

def run_semantic_update(agent_root: Path, query: str) -> str:
    script = agent_root / "scripts" / "semantic_search.py"
    if not script.exists():
        return "semantic_search.py nicht gefunden."
    try:
        result = subprocess.run(
            [sys.executable, str(script), query],
            cwd=str(agent_root),
            capture_output=True,
            text=True,
            timeout=180,
        )
        return (result.stdout + "\n" + result.stderr)[-2000:]
    except Exception as exc:
        return f"Semantic Update fehlgeschlagen: {exc}"

DEFAULT_AGENT_ROOT = Path(r"H:\SecondBrainAgent\SecondBrain-Agent")
DEFAULT_TARGET = Path(r"H:\SecondBrainAgent\SecondBrain\05_Quellen\Perplexity")
DEFAULT_PROCESSED = Path(r"H:\SecondBrainAgent\SecondBrain-Inbox\Perplexity\processed")
DEFAULT_REPORT = Path(r"H:\SecondBrainAgent\SecondBrain\99_System\perplexity_import")

def normalize_perplexity_item(path: Path, data: Any | None) -> tuple[str, str, str]:
    """Unterstützt JSON, Markdown, TXT und HTML-nahe Textdateien aus Perplexity Exporten."""
    created = datetime.now().strftime("%Y-%m-%d")
    title = path.stem
    body = ""

    if isinstance(data, dict):
        title = data.get("title") or data.get("query") or data.get("name") or path.stem
        created = str(data.get("created_at") or data.get("created") or data.get("time") or created)[:10]
        question = data.get("query") or data.get("question") or ""
        answer = data.get("answer") or data.get("content") or data.get("response") or ""
        sources = data.get("sources") or data.get("citations") or []
        parts = []
        if question:
            parts.append(f"## Frage\n\n{question}")
        if answer:
            parts.append(f"## Antwort\n\n{answer}")
        if sources:
            parts.append("## Quellen\n\n" + "\n".join(f"- {s}" for s in sources))
        body = "\n\n".join(parts) if parts else json.dumps(data, ensure_ascii=False, indent=2)
    elif isinstance(data, list):
        body = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        body = read_text_file(path)

    return title, created, body

def import_perplexity_export(
    zip_path: str | Path,
    target_folder: str | Path = DEFAULT_TARGET,
    processed_folder: str | Path = DEFAULT_PROCESSED,
    report_folder: str | Path = DEFAULT_REPORT,
    agent_root: str | Path = DEFAULT_AGENT_ROOT,
    update_semantic_search: bool = True,
) -> dict[str, Any]:
    zip_path = Path(zip_path)
    target_folder = Path(target_folder)
    processed_folder = Path(processed_folder)
    report_folder = Path(report_folder)
    agent_root = Path(agent_root)
    target_folder.mkdir(parents=True, exist_ok=True)
    processed_folder.mkdir(parents=True, exist_ok=True)

    imported, errors = [], []
    extracted = extract_zip(zip_path)

    try:
        files = [p for p in extracted.rglob("*") if p.is_file() and p.suffix.lower() in [".json", ".md", ".txt", ".html"]]
        for i, p in enumerate(files, start=1):
            try:
                data = maybe_json(p) if p.suffix.lower() == ".json" else None
                title, created, body = normalize_perplexity_item(p, data)
                tags = derive_tags(title, body, "perplexity")
                md = frontmatter(title, created, tags, "perplexity", p.name)
                md += f"# {title}\n\n## Quelle\n\nPerplexity Export: `{p.name}`\n\n## Inhalt\n\n{body.strip()}\n"
                target = target_folder / f"{slugify(title)}.md"
                if target.exists():
                    target = target_folder / f"{slugify(title)}_{i}.md"
                target.write_text(md, encoding="utf-8")
                imported.append(str(target))
            except Exception as exc:
                errors.append({"file": str(p), "error": str(exc)})
    finally:
        shutil.rmtree(extracted, ignore_errors=True)

    try:
        processed_target = processed_folder / zip_path.name
        if processed_target.exists():
            processed_target = processed_folder / f"{zip_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{zip_path.suffix}"
        shutil.copy2(zip_path, processed_target)
    except Exception as exc:
        errors.append({"processed_copy": str(exc)})

    if update_semantic_search:
        run_semantic_update(agent_root, "Perplexity Import")

    return write_report(report_folder, "perplexity", zip_path, imported, errors)

def import_perplexity_folder(exports_folder: str | Path, **kwargs) -> list[dict[str, Any]]:
    exports_folder = Path(exports_folder)
    exports_folder.mkdir(parents=True, exist_ok=True)
    return [import_perplexity_export(p, **kwargs) for p in sorted(exports_folder.glob("*.zip"))]

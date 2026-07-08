from pathlib import Path
import json
from .config import load_simple_yaml
from .ollama_client import ollama_generate

def _ai_config(project_root: Path) -> dict:
    return load_simple_yaml(project_root / "config" / "ai_layer.yaml").get("ai_layer", {})

def run_ai(project_root: Path, task: str, prompt: str) -> str:
    cfg = _ai_config(project_root)
    base_url = cfg.get("base_url", "http://localhost:11434")
    timeout = int(cfg.get("timeout_seconds", 120))
    tasks = cfg.get("tasks", {})
    model = tasks.get(task, cfg.get("default_model", "llama3.1"))
    return ollama_generate(base_url, model, prompt, timeout=timeout)

def ai_classify(project_root: Path, text: str) -> str:
    prompt = "Klassifiziere folgenden Inhalt als genau einen Typ: project, knowledge, person, task, source, inbox. Gib nur den Typ aus.\n\n" + text[:4000]
    return run_ai(project_root, "classify", prompt).strip().split()[0].lower()

def ai_summarize(project_root: Path, text: str) -> str:
    prompt = "Fasse folgenden Inhalt auf Deutsch strukturiert zusammen.\n\n" + text[:8000]
    return run_ai(project_root, "summarize", prompt)

def ai_extract_tasks(project_root: Path, text: str) -> str:
    prompt = "Extrahiere Aufgaben als Markdown-Checkboxen. Keine erfundenen Aufgaben.\n\n" + text[:8000]
    return run_ai(project_root, "extract_tasks", prompt)

def ai_review_note(project_root: Path, markdown: str) -> str:
    prompt = "Verbessere diese Obsidian-Markdown-Notiz. YAML Frontmatter erhalten. Keine Fakten erfinden.\n\n" + markdown[:10000]
    return run_ai(project_root, "review", prompt)

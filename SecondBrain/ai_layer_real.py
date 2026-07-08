from pathlib import Path
import json
from .config import load_simple_yaml
from .ollama_client import ollama_generate

def ai_config(project_root: Path) -> dict:
    return load_simple_yaml(project_root / "config" / "ai_layer.yaml").get("ai_layer", {})

def run_ollama_task(project_root: Path, task: str, prompt: str) -> str:
    cfg = ai_config(project_root)
    base_url = cfg.get("base_url", "http://localhost:11434")
    timeout = int(cfg.get("timeout_seconds", 120))
    tasks = cfg.get("tasks", {})
    model = tasks.get(task, cfg.get("default_model", "llama3.1"))
    return ollama_generate(base_url, model, prompt, timeout=timeout)

def ai_classify(project_root: Path, text: str) -> str:
    prompt = "Klassifiziere als genau einen Typ: project, knowledge, person, task, source, email, meeting, decision, process, inbox. Gib nur den Typ aus.\n\n" + text[:5000]
    return run_ollama_task(project_root, "classify", prompt).strip().lower().split()[0]

def ai_summarize(project_root: Path, text: str) -> str:
    prompt = "Erstelle eine strukturierte deutsche Zusammenfassung mit Kernaussage, Details, Aufgaben, Risiken.\n\n" + text[:9000]
    return run_ollama_task(project_root, "summarize", prompt)

def ai_extract_tasks(project_root: Path, text: str) -> str:
    prompt = "Extrahiere nur echte Aufgaben als Markdown-Checkboxen. Keine Aufgaben erfinden.\n\n" + text[:9000]
    return run_ollama_task(project_root, "extract_tasks", prompt)

def ai_generate_tags(project_root: Path, text: str) -> str:
    prompt = "Erzeuge maximal fünf fachliche Obsidian-Tags, kleingeschrieben, ohne #, kommasepariert.\n\n" + text[:6000]
    return run_ollama_task(project_root, "tag", prompt)

def ai_review_note(project_root: Path, markdown: str) -> str:
    prompt = "Verbessere diese Obsidian-Notiz. YAML erhalten. Titel, Zusammenfassung, Tags und Backlinks verbessern. Keine Fakten erfinden.\n\n" + markdown[:12000]
    return run_ollama_task(project_root, "review", prompt)

def ai_rag_answer(project_root: Path, question: str, context: str) -> str:
    prompt = f"Beantworte die Frage nur mit dem Kontext. Zitiere Notiznamen, wenn vorhanden.\n\nFrage: {question}\n\nKontext:\n{context[:12000]}"
    return run_ollama_task(project_root, "rag_answer", prompt)

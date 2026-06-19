from pathlib import Path
from .config import load_simple_yaml
from .ollama_client import ollama_generate

def route_task(project_root: Path, task_type: str) -> dict:
    cfg = load_simple_yaml(project_root / "config" / "llm_router.yaml").get("llm_router", {})
    tasks = cfg.get("tasks", {})
    route = tasks.get(task_type, {})
    return {
        "provider": route.get("provider", cfg.get("default_provider", "ollama")),
        "model": route.get("model", cfg.get("default_model", "llama3.1")),
    }

def run_llm_task(project_root: Path, settings: dict, task_type: str, prompt: str) -> str:
    route = route_task(project_root, task_type)
    if route["provider"] == "ollama":
        return ollama_generate("http://localhost:11434", route["model"], prompt)
    return "Provider nicht aktiviert."

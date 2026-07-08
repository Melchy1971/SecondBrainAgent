from pathlib import Path
from .utils import now_date

def write_local_ai_cluster(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "61_LocalAICluster"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Local_AI_Cluster.md"
    lines = [
        "# Local AI Cluster",
        "",
        f"Aktualisiert: {now_date()}",
        "",
        "| Aufgabe | Modell |",
        "|---|---|",
        "| Extraction | Gemma |",
        "| Coding | DeepSeek Coder |",
        "| Reasoning | Qwen |",
        "| Summary | Llama |",
        "| Vision | LLaVA |",
        "| Embeddings | nomic-embed-text |",
        "| Reranking | bge-reranker |",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

from pathlib import Path
from .utils import now_date

def write_enterprise_rag_status(settings: dict) -> Path:
    vault = Path(settings["vault_path"])
    folder = vault / "55_EnterpriseRAG"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "Enterprise_RAG_Status.md"
    sources = ["Markdown", "PDF", "Word", "Excel", "PowerPoint", "E-Mails", "YouTube", "Webseiten", "Code"]
    lines = ["# Enterprise RAG Status", "", f"Aktualisiert: {now_date()}", "", "| Quelle | Status |", "|---|---|"]
    for s in sources:
        status = "aktiv" if s == "Markdown" else "vorbereitet"
        lines.append(f"| {s} | {status} |")
    lines += ["", "## Pipeline", "", "Chunking → Embeddings → Reranking → Quellenbewertung → Zitation"]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

from __future__ import annotations
from pathlib import Path
from datetime import datetime
import json, urllib.request
from .vector_rag_v95 import search_vector

VAULT = Path(r"H:\SecondBrainAgent\SecondBrain")

def ollama_generate(prompt: str, model: str = "llama3.1", base_url: str = "http://localhost:11434", timeout: int = 120) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/api/generate", data=payload, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("response", "")

def answer_with_rag(question: str, model: str = "llama3.1") -> Path:
    hits = search_vector(question, top_k=8)
    context = "\n\n---\n\n".join([f"Quelle: {h['note']}\n{h['text']}" for h in hits])
    prompt = f"""Beantworte die Frage ausschließlich auf Basis des Kontextes.
Wenn die Antwort nicht im Kontext steht, sage: 'Nicht im Vault gefunden.'

Frage:
{question}

Kontext:
{context}
"""
    try:
        answer = ollama_generate(prompt, model=model)
    except Exception as exc:
        answer = f"Ollama nicht erreichbar oder Fehler: {exc}\n\nKontexttreffer wurden trotzdem erzeugt."

    target = VAULT / "88_VectorRAG" / f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_rag_answer.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# RAG Answer: {question}", "", "## Antwort", "", answer, "", "## Quellen", ""]
    for h in hits:
        lines.append(f"- [[{h['note']}]] — Score {h['score']}, Chunk {h['chunk']}")
    target.write_text("\n".join(lines), encoding="utf-8")
    return target

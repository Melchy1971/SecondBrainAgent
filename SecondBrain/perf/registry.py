"""Benchmark case registry.

Registers all core components. Sandbox-capable, pure-Python components carry a
real callable; components that need external services (PostgreSQL, embeddings,
OCR, connectors, a display) are registered as ``requires_service`` placeholders
so the same run on a fully provisioned machine fills in real numbers.

Setup work (temp dirs, object construction) happens once at registry build time,
so the timed callable exercises the component itself, not fixture setup.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from typing import Any, Callable

__all__ = ["BenchmarkCase", "default_registry", "REQUIRES_SERVICE"]


@dataclass
class BenchmarkCase:
    component: str
    name: str
    requires_service: bool = False
    fn: Callable[[], Any] | None = None
    iterations: int = 1
    note: str = ""


# -- real, sandbox-capable cases ---------------------------------------------

def _case_chunking() -> BenchmarkCase:
    from secondbrain.rag import chunk_text

    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 400

    def run() -> None:
        chunk_text(text, 1200, 150)

    return BenchmarkCase("Chunking", "chunk_text_23k_chars", fn=run, iterations=20)


def _case_approval() -> BenchmarkCase:
    from secondbrain.native.approval import NativeApprovalQueue

    queue = NativeApprovalQueue(tempfile.mkdtemp())
    counter = {"n": 0}

    def run() -> None:
        counter["n"] += 1
        approval = queue.create(
            command=f"records.delete.{counter['n']}",
            intent="delete_record",
            text=f"Delete record {counter['n']}",
            category="delete_request",
            risk_level="high",
        )
        queue.transition(approval["approval_id"], "approved", actor="bench")

    return BenchmarkCase("Approval", "create_and_transition", fn=run, iterations=25)


def _case_memory() -> BenchmarkCase:
    from secondbrain.agent.memory_extractor import MemoryExtractor
    from secondbrain.agent.memory_service import GovernedMemoryService

    service = GovernedMemoryService(project_root=tempfile.mkdtemp())
    extractor = MemoryExtractor()
    counter = {"n": 0}

    def run() -> None:
        counter["n"] += 1
        candidate = extractor.extract(
            f"Fakt Nummer {counter['n']} ueber die Systemarchitektur",
            source_id="bench",
            workspace_id="w1",
            confidence=0.95,
        )
        service.submit(candidate)

    return BenchmarkCase("Memory", "extract_and_submit", fn=run, iterations=25)


def _case_planner() -> BenchmarkCase:
    from secondbrain.agent.task_planner import TaskPlanner

    try:
        from secondbrain.agent.tool_registry import ToolRegistry

        planner = TaskPlanner(ToolRegistry())
    except Exception:  # noqa: BLE001 - fall back to a no-arg planner
        planner = TaskPlanner()

    def run() -> None:
        planner.create_chat_plan(text="Plane diese Benchmark-Aufgabe mit mehreren Woertern Eingabe")

    return BenchmarkCase("Agent Planner", "create_chat_plan", fn=run, iterations=25)


def _case_metrics() -> BenchmarkCase:
    from secondbrain.metrics.review_approval_metrics import ReviewApprovalMetrics
    from secondbrain.native.approval import NativeApprovalQueue

    root = tempfile.mkdtemp()
    queue = NativeApprovalQueue(root)
    for i in range(20):
        queue.create(command=f"c{i}", intent="i", text=f"t{i}", category="delete_request", risk_level="high")

    def run() -> None:
        ReviewApprovalMetrics(root).export()

    return BenchmarkCase("Metriken", "export", fn=run, iterations=10)


# -- service-dependent placeholders ------------------------------------------

REQUIRES_SERVICE = [
    ("Import", "import_pipeline", "PostgreSQL + Datei-/AI-Import-Pipeline"),
    ("OCR", "ocr_extract", "OCR-Engine (Tesseract/PaddleOCR)"),
    ("Embedding", "embed_batch", "Ollama/OpenAI Embedding-Provider"),
    ("Vector Search", "vector_topk", "pgvector"),
    ("Hybrid Search", "hybrid_topk", "pgvector + Embeddings + BM25"),
    ("GUI", "render_native_gui", "Tk-Display"),
    ("Connector Sync", "connector_incremental_sync", "Connector-Credentials"),
    ("Dashboard", "dashboard_snapshot", "native Desktop-Runtime"),
    ("RAG", "rag_answer", "Embeddings + Vector Store"),
]


def default_registry() -> list[BenchmarkCase]:
    real = [
        _case_chunking(),
        _case_approval(),
        _case_memory(),
        _case_planner(),
        _case_metrics(),
    ]
    service = [
        BenchmarkCase(component, name, requires_service=True, fn=None, note=note)
        for component, name, note in REQUIRES_SERVICE
    ]
    return real + service

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from secondbrain.p1_retrieval import evaluate_ranked_hits

GOLDEN_SCHEMA = "secondbrain.p1_golden_retrieval.v1"
DEFAULT_GOLDEN_DATASET_ID = "builtin_v1"


@dataclass(frozen=True)
class GoldenQuery:
    query: str
    expected_terms: tuple[str, ...]
    min_recall_at_k: float = 0.5
    min_mrr: float = 0.25
    min_ndcg: float = 0.35
    k: int = 10
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["expected_terms"] = list(self.expected_terms)
        return data


class RetrievalRuntime(Protocol):
    def hybrid_search(self, query: str, limit: int = 5) -> dict[str, Any]:
        ...

    def answer(self, query: str, limit: int = 4) -> dict[str, Any]:
        ...


DEFAULT_GOLDEN_QUERIES: tuple[GoldenQuery, ...] = (
    GoldenQuery(
        query="Jarvis RAG Quellen",
        expected_terms=("jarvis", "rag", "quellen"),
        min_recall_at_k=0.66,
        min_mrr=0.25,
        min_ndcg=0.35,
        note="Core local RAG source-discovery smoke.",
    ),
    GoldenQuery(
        query="Memory Evidenz",
        expected_terms=("memory", "evidenz"),
        min_recall_at_k=0.5,
        min_mrr=0.25,
        min_ndcg=0.35,
        note="Checks memory/evidence vocabulary.",
    ),
    GoldenQuery(
        query="lokale Quellen",
        expected_terms=("lokale", "quellen"),
        min_recall_at_k=0.5,
        min_mrr=0.25,
        min_ndcg=0.35,
        note="German local source query.",
    ),
)


def _coerce_query(raw: dict[str, Any]) -> GoldenQuery:
    query = str(raw.get("query", "")).strip()
    expected_terms = tuple(str(term).strip().lower() for term in raw.get("expected_terms", []) if str(term).strip())
    if not query:
        raise ValueError("golden_query_missing_query")
    if not expected_terms:
        raise ValueError(f"golden_query_missing_expected_terms:{query}")
    return GoldenQuery(
        query=query,
        expected_terms=expected_terms,
        min_recall_at_k=float(raw.get("min_recall_at_k", 0.5)),
        min_mrr=float(raw.get("min_mrr", 0.25)),
        min_ndcg=float(raw.get("min_ndcg", 0.35)),
        k=max(1, int(raw.get("k", 10))),
        note=str(raw.get("note", "")),
    )


def golden_dataset_path(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / "config" / "golden_retrieval.json"


def load_golden_dataset(project_root: str | Path) -> dict[str, Any]:
    path = golden_dataset_path(project_root)
    if not path.exists():
        return {
            "schema": GOLDEN_SCHEMA,
            "ok": True,
            "dataset_id": DEFAULT_GOLDEN_DATASET_ID,
            "source": "builtin",
            "path": None,
            "queries": [query.to_dict() for query in DEFAULT_GOLDEN_QUERIES],
        }
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        queries = [_coerce_query(item).to_dict() for item in raw.get("queries", [])]
        if not queries:
            raise ValueError("golden_dataset_empty")
        return {
            "schema": GOLDEN_SCHEMA,
            "ok": True,
            "dataset_id": str(raw.get("dataset_id") or path.stem),
            "source": "config",
            "path": str(path),
            "queries": queries,
        }
    except Exception as exc:  # noqa: BLE001 - config validation boundary
        return {
            "schema": GOLDEN_SCHEMA,
            "ok": False,
            "dataset_id": str(path.stem),
            "source": "config",
            "path": str(path),
            "queries": [],
            "error": str(exc),
        }


def evaluate_golden_retrieval(runtime: RetrievalRuntime, project_root: str | Path, *, write_report: bool = False) -> dict[str, Any]:
    dataset = load_golden_dataset(project_root)
    rows: list[dict[str, Any]] = []
    if not dataset.get("ok"):
        payload = {
            "schema": GOLDEN_SCHEMA,
            "ok": False,
            "status": "blocked",
            "dataset": dataset,
            "blockers": 1,
            "warnings": 0,
            "results": [],
        }
    else:
        blockers = 0
        warnings = 0
        for item in dataset["queries"]:
            k = max(1, int(item.get("k", 10)))
            result = runtime.hybrid_search(item["query"], k)
            metrics = evaluate_ranked_hits(result.get("hits", []), list(item["expected_terms"]), k=k)
            answer = runtime.answer(item["query"], min(k, 4))
            passed = (
                float(metrics["recall_at_k"]) >= float(item["min_recall_at_k"])
                and float(metrics["mrr"]) >= float(item["min_mrr"])
                and float(metrics["ndcg"]) >= float(item["min_ndcg"])
            )
            if not passed:
                blockers += 1
            if result.get("hit_count", 0) == 0:
                warnings += 1
            rows.append({
                "query": item["query"],
                "expected_terms": item["expected_terms"],
                "thresholds": {
                    "min_recall_at_k": item["min_recall_at_k"],
                    "min_mrr": item["min_mrr"],
                    "min_ndcg": item["min_ndcg"],
                    "k": k,
                },
                "ok": passed,
                "hit_count": result.get("hit_count", 0),
                "confidence": answer.get("confidence", 0.0),
                "metrics": metrics,
                "note": item.get("note", ""),
            })
        n = max(1, len(rows))
        payload = {
            "schema": GOLDEN_SCHEMA,
            "ok": blockers == 0,
            "status": "pass" if blockers == 0 else "blocked",
            "dataset": dataset,
            "blockers": blockers,
            "warnings": warnings,
            "query_count": len(rows),
            "pass_rate": round(sum(1 for row in rows if row["ok"]) / n, 4),
            "avg_recall_at_k": round(sum(float(row["metrics"]["recall_at_k"]) for row in rows) / n, 4),
            "avg_mrr": round(sum(float(row["metrics"]["mrr"]) for row in rows) / n, 4),
            "avg_ndcg": round(sum(float(row["metrics"]["ndcg"]) for row in rows) / n, 4),
            "results": rows,
        }
    if write_report:
        reports_dir = Path(project_root).resolve() / "runtime" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        target = reports_dir / "p1_golden_retrieval_latest.json"
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        payload["report"] = {"path": str(target), "bytes": target.stat().st_size}
    return payload

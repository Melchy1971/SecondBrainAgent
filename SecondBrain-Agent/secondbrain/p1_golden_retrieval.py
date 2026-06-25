from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

from secondbrain.p1_retrieval import evaluate_ranked_hits

GOLDEN_SCHEMA = "secondbrain.p1_golden_retrieval.v2"
DEFAULT_GOLDEN_DATASET_ID = "builtin_v2"


@dataclass(frozen=True)
class GoldenQuery:
    query: str
    expected_terms: tuple[str, ...]
    min_recall_at_k: float = 0.5
    min_mrr: float = 0.25
    min_ndcg: float = 0.35
    k: int = 10
    note: str = ""
    min_hit_count: int = 1
    expected_sources: tuple[str, ...] = field(default_factory=tuple)
    expected_titles: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["expected_terms"] = list(self.expected_terms)
        data["expected_sources"] = list(self.expected_sources)
        data["expected_titles"] = list(self.expected_titles)
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


def _terms(raw: Any) -> tuple[str, ...]:
    return tuple(str(term).strip().lower() for term in (raw or []) if str(term).strip())


def _coerce_query(raw: dict[str, Any]) -> GoldenQuery:
    query = str(raw.get("query", "")).strip()
    expected_terms = _terms(raw.get("expected_terms", []))
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
        min_hit_count=max(0, int(raw.get("min_hit_count", 1))),
        expected_sources=_terms(raw.get("expected_sources", [])),
        expected_titles=_terms(raw.get("expected_titles", [])),
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
            "quality_policy": {
                "mode": str(raw.get("quality_policy", {}).get("mode", "blocking")),
                "min_pass_rate": float(raw.get("quality_policy", {}).get("min_pass_rate", 1.0)),
            },
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


def _contains_any(value: str, expected: list[str]) -> bool:
    value_l = (value or "").lower()
    return any(token in value_l for token in expected)


def _lineage_metrics(hits: list[dict[str, Any]], expected_sources: list[str], expected_titles: list[str]) -> dict[str, Any]:
    source_hits = 0
    title_hits = 0
    if expected_sources:
        source_hits = sum(1 for hit in hits if _contains_any(str(hit.get("source", "")), expected_sources))
    if expected_titles:
        title_hits = sum(1 for hit in hits if _contains_any(str(hit.get("title", "")), expected_titles))
    return {
        "expected_sources": expected_sources,
        "expected_titles": expected_titles,
        "source_match_count": source_hits,
        "title_match_count": title_hits,
        "source_coverage": 1.0 if not expected_sources else round(source_hits / max(1, len(hits)), 4),
        "title_coverage": 1.0 if not expected_titles else round(title_hits / max(1, len(hits)), 4),
        "lineage_ok": (not expected_sources or source_hits > 0) and (not expected_titles or title_hits > 0),
    }


def evaluate_golden_retrieval(runtime: RetrievalRuntime, project_root: str | Path, *, write_report: bool = False) -> dict[str, Any]:
    dataset = load_golden_dataset(project_root)
    rows: list[dict[str, Any]] = []
    if not dataset.get("ok"):
        payload = {
            "schema": GOLDEN_SCHEMA,
            "ok": False,
            "status": "blocked",
            "technical_ok": False,
            "quality_ok": False,
            "dataset": dataset,
            "blockers": 1,
            "warnings": 0,
            "results": [],
        }
    else:
        blockers = 0
        warnings = 0
        runtime_errors = 0
        for item in dataset["queries"]:
            k = max(1, int(item.get("k", 10)))
            result = runtime.hybrid_search(item["query"], k)
            hits = list(result.get("hits", []))
            technical_ok = bool(result.get("ok"))
            if not technical_ok:
                runtime_errors += 1
            metrics = evaluate_ranked_hits(hits, list(item["expected_terms"]), k=k)
            answer = runtime.answer(item["query"], min(k, 4)) if technical_ok else {"confidence": 0.0, "citations": []}
            lineage = _lineage_metrics(hits, list(item.get("expected_sources", [])), list(item.get("expected_titles", [])))
            enough_hits = int(result.get("hit_count", 0)) >= int(item.get("min_hit_count", 1))
            threshold_ok = (
                float(metrics["recall_at_k"]) >= float(item["min_recall_at_k"])
                and float(metrics["mrr"]) >= float(item["min_mrr"])
                and float(metrics["ndcg"]) >= float(item["min_ndcg"])
            )
            quality_ok = technical_ok and enough_hits and threshold_ok and bool(lineage["lineage_ok"])
            failure_reasons: list[str] = []
            if not technical_ok:
                failure_reasons.append("hybrid_search_failed")
            if not enough_hits:
                failure_reasons.append("min_hit_count_not_met")
            if not threshold_ok:
                failure_reasons.append("retrieval_thresholds_not_met")
            if not lineage["lineage_ok"]:
                failure_reasons.append("expected_lineage_not_found")
            if not quality_ok:
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
                    "min_hit_count": item.get("min_hit_count", 1),
                    "k": k,
                },
                "ok": quality_ok,
                "technical_ok": technical_ok,
                "quality_ok": quality_ok,
                "failure_reasons": failure_reasons,
                "hit_count": result.get("hit_count", 0),
                "confidence": answer.get("confidence", 0.0),
                "metrics": metrics,
                "lineage": lineage,
                "note": item.get("note", ""),
            })
        n = max(1, len(rows))
        pass_rate = round(sum(1 for row in rows if row["ok"]) / n, 4)
        min_pass_rate = float(dataset.get("quality_policy", {}).get("min_pass_rate", 1.0))
        quality_ok = blockers == 0 and pass_rate >= min_pass_rate
        technical_ok = runtime_errors == 0
        payload = {
            "schema": GOLDEN_SCHEMA,
            "ok": technical_ok and quality_ok,
            "status": "pass" if technical_ok and quality_ok else "blocked",
            "technical_ok": technical_ok,
            "quality_ok": quality_ok,
            "dataset": dataset,
            "blockers": blockers + (0 if technical_ok else runtime_errors),
            "warnings": warnings,
            "runtime_errors": runtime_errors,
            "query_count": len(rows),
            "pass_rate": pass_rate,
            "min_pass_rate": min_pass_rate,
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

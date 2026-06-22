"""P1 v19.3 - file based retrieval KPI store."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from time import time


@dataclass(frozen=True)
class RetrievalKpiRecord:
    query_id: str
    query: str
    metrics: dict[str, float]
    created_at: float


class RetrievalKpiStore:
    def __init__(self, path: str | Path = "runtime/rag/retrieval_kpis.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, query_id: str, query: str, metrics: dict[str, float]) -> RetrievalKpiRecord:
        record = RetrievalKpiRecord(query_id=query_id, query=query, metrics=metrics, created_at=time())
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")
        return record

    def list(self) -> list[RetrievalKpiRecord]:
        if not self.path.exists():
            return []
        records: list[RetrievalKpiRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            records.append(RetrievalKpiRecord(
                query_id=row["query_id"],
                query=row["query"],
                metrics={k: float(v) for k, v in row["metrics"].items()},
                created_at=float(row["created_at"]),
            ))
        return records

    def summary(self) -> dict[str, float]:
        records = self.list()
        if not records:
            return {"records": 0}
        keys = sorted({k for r in records for k in r.metrics})
        result: dict[str, float] = {"records": float(len(records))}
        for key in keys:
            values = [r.metrics[key] for r in records if key in r.metrics]
            result[f"avg_{key}"] = sum(values) / len(values)
        return result

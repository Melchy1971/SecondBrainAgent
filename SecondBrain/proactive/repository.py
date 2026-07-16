"""PostgreSQL-first persistence for proactive suggestions, rules and feedback."""

from __future__ import annotations

import json
import os
from typing import Any, Mapping

from secondbrain.proactive.models import FeedbackRecord, Suggestion, SuggestionRule


class ProactiveRepositoryError(RuntimeError):
    pass


_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS proactive_records (
        kind TEXT NOT NULL, workspace_id TEXT NOT NULL, record_id TEXT NOT NULL,
        data TEXT NOT NULL, PRIMARY KEY(kind, workspace_id, record_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_proactive_workspace ON proactive_records(workspace_id, kind)",
)


class PostgresProactiveRepository:
    backend = "postgres"

    def __init__(self, executor: Any) -> None:
        self.executor = executor

    def ensure_schema(self) -> None:
        for statement in _SCHEMA:
            self.executor.execute(statement)

    def save_suggestion(self, suggestion: Suggestion) -> None:
        self._upsert("suggestion", suggestion.workspace_id, suggestion.suggestion_id,
                     suggestion.to_dict())

    def save_rule(self, rule: SuggestionRule, *, workspace_id: str) -> None:
        data = {
            "rule_id": rule.rule_id, "category": rule.category, "conditions": rule.conditions,
            "enabled": rule.enabled, "confidence_threshold": rule.confidence_threshold,
            "cooldown_minutes": rule.cooldown_minutes, "priority": rule.priority,
            "maximum_open_items": rule.maximum_open_items, "workspace_scope": workspace_id,
            "created_at": rule.created_at, "updated_at": rule.updated_at,
        }
        self._upsert("rule", workspace_id, rule.rule_id, data)

    def append_feedback(self, feedback: FeedbackRecord, *, workspace_id: str) -> None:
        record_id = f"{feedback.at}:{feedback.suggestion_id}:{len(self.list_feedback(workspace_id=workspace_id))}"
        self._upsert("feedback", workspace_id, record_id, feedback.to_dict())

    def list_rules(self) -> list[tuple[str, SuggestionRule]]:
        rows = self.executor.execute(
            "SELECT workspace_id,data FROM proactive_records WHERE kind='rule' ORDER BY record_id")
        result = []
        for workspace_id, encoded in rows:
            data = json.loads(encoded)
            result.append((str(workspace_id), SuggestionRule(**data)))
        return result

    def list_feedback(self, *, workspace_id: str) -> list[FeedbackRecord]:
        rows = self.executor.execute(
            "SELECT data FROM proactive_records WHERE kind='feedback' AND workspace_id=:workspace_id "
            "ORDER BY record_id", {"workspace_id": workspace_id})
        return [FeedbackRecord(**json.loads(row[0])) for row in rows]

    def _upsert(self, kind: str, workspace_id: str, record_id: str,
                data: Mapping[str, Any]) -> None:
        params = {"kind": kind, "workspace_id": workspace_id, "record_id": record_id,
                  "data": json.dumps(dict(data), ensure_ascii=False, sort_keys=True)}
        self.executor.execute(
            "INSERT INTO proactive_records(kind,workspace_id,record_id,data) "
            "VALUES(:kind,:workspace_id,:record_id,:data) "
            "ON CONFLICT(kind,workspace_id,record_id) DO UPDATE SET data=:data", params)


def create_proactive_repository(*, env: Mapping[str, str] | None = None,
                                executor: Any | None = None) -> PostgresProactiveRepository | None:
    values = env if env is not None else os.environ
    profile = str(values.get("SECONDBRAIN_ENV") or "development").lower()
    backend = str(values.get("PROACTIVE_REPOSITORY_BACKEND") or
                  ("postgres" if profile.startswith("prod") else "memory")).lower()
    if backend == "memory":
        if profile.startswith("prod"):
            raise ProactiveRepositoryError("memory_not_allowed_in_production")
        return None
    if backend != "postgres":
        raise ProactiveRepositoryError(f"unknown_proactive_repository_backend:{backend}")
    if executor is None:
        url = str(values.get("SECOND_BRAIN_DATABASE_URL") or values.get("DATABASE_URL") or "").strip()
        if not url:
            raise ProactiveRepositoryError("postgres_proactive_repository_requires_database_url")
        from secondbrain.storage.database import Database
        from secondbrain.storage.database_config import DatabaseConfig
        from secondbrain.storage.db_executor import SqlAlchemyExecutor
        executor = SqlAlchemyExecutor(Database(DatabaseConfig(url=url)))
    repository = PostgresProactiveRepository(executor)
    repository.ensure_schema()
    return repository

import pytest

from secondbrain.proactive.models import SuggestionCategory
from secondbrain.proactive.repository import (
    PostgresProactiveRepository, ProactiveRepositoryError, create_proactive_repository,
)
from secondbrain.proactive.service import ProactiveEngine
from secondbrain.storage.db_executor import SqliteExecutor


def test_disabled_rule_and_feedback_survive_restart(tmp_path):
    path = str(tmp_path / "proactive.sqlite")
    repository = PostgresProactiveRepository(SqliteExecutor(path))
    repository.ensure_schema()
    engine = ProactiveEngine(repository=repository)
    engine.disable_rule(SuggestionCategory.DEADLINE_RISK.value, workspace_id="ws")

    restarted_repository = PostgresProactiveRepository(SqliteExecutor(path))
    restarted = ProactiveEngine(repository=restarted_repository)
    assert ("ws", SuggestionCategory.DEADLINE_RISK.value) in restarted.disabled_rules


def test_feedback_is_workspace_scoped_and_redacted(tmp_path):
    repository = PostgresProactiveRepository(SqliteExecutor(str(tmp_path / "feedback.sqlite")))
    repository.ensure_schema()
    engine = ProactiveEngine(repository=repository)
    suggestion = engine.generate(workspace_id="ws", context={
        "connectors": [{"name": "Mail", "error_count": 4}],
    })[0]
    engine.record_feedback(suggestion.suggestion_id, "false_positive", "token=secret-value")
    rows = repository.list_feedback(workspace_id="ws")
    assert rows[0].action == "false_positive" and "secret-value" not in rows[0].detail
    assert repository.list_feedback(workspace_id="other") == []


def test_production_requires_postgres_configuration():
    with pytest.raises(ProactiveRepositoryError, match="memory_not_allowed"):
        create_proactive_repository(env={"SECONDBRAIN_ENV": "production",
                                         "PROACTIVE_REPOSITORY_BACKEND": "memory"})
    with pytest.raises(ProactiveRepositoryError, match="requires_database_url"):
        create_proactive_repository(env={"SECONDBRAIN_ENV": "production"})

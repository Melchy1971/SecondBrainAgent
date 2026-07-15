import pytest

from secondbrain.personal_dashboard.models import DashboardConfig
from secondbrain.personal_dashboard.repository import (
    DashboardRepositoryError, PostgresDashboardRepository, create_dashboard_repository,
)
from secondbrain.storage.db_executor import SqliteExecutor


def test_preferences_persist_and_are_workspace_isolated(tmp_path):
    repository = PostgresDashboardRepository(SqliteExecutor(str(tmp_path / "dashboard.sqlite")))
    repository.ensure_schema()
    config = DashboardConfig(enabled=["tasks"], order=["tasks"], timeframe="week",
                             workspace_id="ws", density="compact", preferred_home="dashboard")
    version = repository.save(config, profile_id="person")
    loaded, loaded_version = repository.load(workspace_id="ws", profile_id="person")
    assert loaded.to_dict() == config.to_dict() and loaded_version == version
    assert repository.load(workspace_id="other", profile_id="person") is None


def test_optimistic_version_blocks_stale_preferences(tmp_path):
    repository = PostgresDashboardRepository(SqliteExecutor(str(tmp_path / "version.sqlite")))
    repository.ensure_schema()
    config = DashboardConfig(enabled=["tasks"], order=["tasks"], workspace_id="ws")
    repository.save(config, expected_version=0)
    with pytest.raises(DashboardRepositoryError, match="stale"):
        repository.save(config, expected_version=0)


def test_production_requires_postgres():
    with pytest.raises(DashboardRepositoryError, match="memory_not_allowed"):
        create_dashboard_repository(env={"SECONDBRAIN_ENV": "production",
                                         "DASHBOARD_REPOSITORY_BACKEND": "memory"})
    with pytest.raises(DashboardRepositoryError, match="requires_database_url"):
        create_dashboard_repository(env={"SECONDBRAIN_ENV": "production"})

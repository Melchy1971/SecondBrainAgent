from secondbrain.storage.db_provider import DatabaseProvider


def test_provider_migrates_and_reports_health(tmp_path):
    (tmp_path / "001_x.sql").write_text("CREATE TABLE x(id INTEGER);", encoding="utf-8")
    provider = DatabaseProvider.start(
        {"SECOND_BRAIN_ENV": "development", "DATABASE_URL": "sqlite:///:memory:"},
        retry=None, sleeper=lambda _s: None)
    # point runner at the fixture migrations
    provider.migrations_dir = tmp_path
    result = provider.migrate()
    assert result["applied"] == ["001_x"]
    health = provider.health()
    assert health["backend"] == "sqlite"
    assert health["migrations"]["up_to_date"] is True

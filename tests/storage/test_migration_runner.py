import pytest
from secondbrain.storage.db_executor import SqliteExecutor
from secondbrain.storage.migration_runner import MigrationRunner


def _mig(tmp_path, name, sql):
    (tmp_path / name).write_text(sql, encoding="utf-8")


def test_apply_tracks_and_is_idempotent(tmp_path):
    _mig(tmp_path, "001_a.sql", "CREATE TABLE a(id INTEGER PRIMARY KEY); INSERT INTO a VALUES (1);")
    _mig(tmp_path, "002_b.sql", "CREATE TABLE b(id INTEGER PRIMARY KEY);")
    ex = SqliteExecutor(":memory:")
    runner = MigrationRunner(ex, tmp_path)
    first = runner.apply()
    assert first["applied"] == ["001_a", "002_b"]
    assert runner.apply()["applied"] == []            # idempotent
    assert runner.status()["up_to_date"] is True
    assert runner.applied() == {"001_a", "002_b"}


def test_ordering_by_numeric_prefix(tmp_path):
    _mig(tmp_path, "010_ten.sql", "CREATE TABLE ten(id INTEGER);")
    _mig(tmp_path, "002_two.sql", "CREATE TABLE two(id INTEGER);")
    runner = MigrationRunner(SqliteExecutor(":memory:"), tmp_path)
    assert [m.version for m in runner.discover()] == ["002_two", "010_ten"]


def test_bad_migration_rolls_back_and_is_not_recorded(tmp_path):
    _mig(tmp_path, "001_ok.sql", "CREATE TABLE ok(id INTEGER);")
    _mig(tmp_path, "002_bad.sql", "CREATE TABLE bad(id INTEGER); INSERT INTO missing VALUES (1);")
    ex = SqliteExecutor(":memory:")
    runner = MigrationRunner(ex, tmp_path)
    with pytest.raises(Exception):
        runner.apply()
    assert "002_bad" not in runner.applied()
    assert ex.execute("SELECT name FROM sqlite_master WHERE name='bad'") == []  # rolled back
    assert runner.status()["pending"] == ["002_bad"]

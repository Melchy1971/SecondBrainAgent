import pytest
from secondbrain.storage.db_executor import SqliteExecutor


def test_execute_and_ping():
    ex = SqliteExecutor(":memory:")
    ex.execute("CREATE TABLE t(id INTEGER, name TEXT)")
    ex.execute("INSERT INTO t VALUES (1, 'a')")
    assert ex.execute("SELECT COUNT(*) FROM t")[0][0] == 1
    assert ex.ping() is True


def test_transaction_commits():
    ex = SqliteExecutor(":memory:")
    ex.execute("CREATE TABLE t(id INTEGER)")
    with ex.transaction():
        ex.execute("INSERT INTO t VALUES (1)")
        ex.execute("INSERT INTO t VALUES (2)")
    assert ex.execute("SELECT COUNT(*) FROM t")[0][0] == 2


def test_transaction_rolls_back_including_ddl():
    ex = SqliteExecutor(":memory:")
    ex.execute("CREATE TABLE t(id INTEGER)")
    with pytest.raises(Exception):
        with ex.transaction():
            ex.execute("INSERT INTO t VALUES (1)")
            ex.execute("CREATE TABLE t2(id INTEGER)")
            ex.execute("INSERT INTO nope VALUES (1)")  # fails
    assert ex.execute("SELECT COUNT(*) FROM t")[0][0] == 0            # insert rolled back
    assert ex.execute("SELECT name FROM sqlite_master WHERE name='t2'") == []  # DDL rolled back


def test_file_backed_persists(tmp_path):
    path = tmp_path / "d.sqlite3"
    ex = SqliteExecutor(f"sqlite:///{path}")
    ex.execute("CREATE TABLE t(id INTEGER)")
    ex.execute("INSERT INTO t VALUES (7)")
    ex.close()
    ex2 = SqliteExecutor(str(path))
    assert ex2.execute("SELECT id FROM t")[0][0] == 7

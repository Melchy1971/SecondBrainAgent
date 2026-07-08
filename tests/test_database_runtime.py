from secondbrain.database import DatabaseRuntime


def test_migrate_health(tmp_path):
    db = DatabaseRuntime(tmp_path)
    db.migrate()
    assert db.health()["reachable"] is True


def test_memory_search(tmp_path):
    db = DatabaseRuntime(tmp_path)
    db.add_memory("Jarvis nutzt PostgreSQL", kind="architecture")
    assert db.search_memories("postgresql")


def test_tasks_documents_events(tmp_path):
    db = DatabaseRuntime(tmp_path)
    db.add_task("DB testen")
    db.add_document("Plan", content="Datenbankplan")
    db.publish_event("db.created", "{}")
    stats = db.stats()
    assert stats["tasks"] == 1
    assert stats["documents"] == 1
    assert stats["events"] == 1


def test_embedding(tmp_path):
    db = DatabaseRuntime(tmp_path)
    item = db.add_embedding("memory", "m1", [0.1, 0.2, 0.3])
    assert item["vector"] == "0.1,0.2,0.3"


def test_postgres_plan(tmp_path):
    db = DatabaseRuntime(tmp_path)
    assert db.postgres_plan()["target"] == "PostgreSQL + pgvector"

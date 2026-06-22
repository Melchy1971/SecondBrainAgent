import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        applied_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY,
        kind TEXT NOT NULL,
        content TEXT NOT NULL,
        source TEXT,
        importance REAL DEFAULT 0.5,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        status TEXT DEFAULT 'open',
        priority TEXT DEFAULT 'medium',
        due_at TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        path TEXT,
        mime_type TEXT,
        content TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        topic TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS automations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        trigger_type TEXT NOT NULL,
        action TEXT NOT NULL,
        enabled INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS embeddings (
        id TEXT PRIMARY KEY,
        owner_type TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        vector TEXT NOT NULL,
        model TEXT,
        created_at TEXT NOT NULL
    )
    """,
]


class DatabaseRuntime:
    def __init__(self, root=".", db_path=None):
        self.root = Path(root)
        self.data_dir = self.root / "data" / "database"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else self.data_dir / "secondbrain.sqlite3"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def migrate(self):
        with self.connect() as conn:
            for statement in SCHEMA:
                conn.execute(statement)
            version = "v16.1_001_core_schema"
            conn.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (version, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        return {"ok": True, "db_path": str(self.db_path), "migration": "v16.1_001_core_schema"}

    def health(self):
        exists = self.db_path.exists()
        try:
            with self.connect() as conn:
                conn.execute("SELECT 1").fetchone()
            reachable = True
        except Exception:
            reachable = False
        return {"db_path": str(self.db_path), "exists": exists, "reachable": reachable, "engine": "sqlite_postgres_ready"}

    def migrations(self):
        self.migrate()
        with self.connect() as conn:
            rows = conn.execute("SELECT version, applied_at FROM schema_migrations ORDER BY applied_at").fetchall()
        return [dict(r) for r in rows]

    def add_memory(self, content, kind="note", source="manual", importance=0.5):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "kind": kind,
            "content": content,
            "source": source,
            "importance": importance,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO memories(id, kind, content, source, importance, created_at) VALUES (:id, :kind, :content, :source, :importance, :created_at)",
                item,
            )
            conn.commit()
        return item

    def search_memories(self, query):
        self.migrate()
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE lower(content) LIKE ? OR lower(kind) LIKE ? ORDER BY created_at DESC",
                (f"%{query.lower()}%", f"%{query.lower()}%"),
            ).fetchall()
        return [dict(r) for r in rows]

    def add_task(self, title, status="open", priority="medium", due_at=None):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "title": title,
            "status": status,
            "priority": priority,
            "due_at": due_at,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO tasks(id, title, status, priority, due_at, created_at) VALUES (:id, :title, :status, :priority, :due_at, :created_at)",
                item,
            )
            conn.commit()
        return item

    def tasks(self):
        self.migrate()
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def add_document(self, title, path="", mime_type="text/plain", content=""):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "title": title,
            "path": path,
            "mime_type": mime_type,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO documents(id, title, path, mime_type, content, created_at) VALUES (:id, :title, :path, :mime_type, :content, :created_at)",
                item,
            )
            conn.commit()
        return item

    def documents(self):
        self.migrate()
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def publish_event(self, topic, payload):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "topic": topic,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO events(id, topic, payload, created_at) VALUES (:id, :topic, :payload, :created_at)",
                item,
            )
            conn.commit()
        return item

    def events(self):
        self.migrate()
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM events ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def add_embedding(self, owner_type, owner_id, vector, model="placeholder"):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "owner_type": owner_type,
            "owner_id": owner_id,
            "vector": ",".join(str(x) for x in vector),
            "model": model,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO embeddings(id, owner_type, owner_id, vector, model, created_at) VALUES (:id, :owner_type, :owner_id, :vector, :model, :created_at)",
                item,
            )
            conn.commit()
        return item

    def stats(self):
        self.migrate()
        tables = ["memories", "tasks", "documents", "events", "automations", "embeddings"]
        result = {}
        with self.connect() as conn:
            for table in tables:
                result[table] = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
        return result

    def postgres_plan(self):
        return {
            "target": "PostgreSQL + pgvector",
            "current": "SQLite compatibility layer",
            "steps": [
                "replace sqlite connection with psycopg pool",
                "convert embeddings.vector TEXT to vector(n)",
                "add Alembic migrations",
                "add indexes for memory/source/document search",
                "add pgvector similarity queries",
            ],
            "tables": ["memories", "tasks", "documents", "events", "automations", "embeddings"],
        }

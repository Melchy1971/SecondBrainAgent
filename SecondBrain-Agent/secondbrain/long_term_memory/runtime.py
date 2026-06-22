import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


class LongTermMemoryRuntime:
    def __init__(self, root=".", db_path=None):
        self.root = Path(root)
        self.data_dir = self.root / "data" / "long_term_memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else self.data_dir / "memory.sqlite3"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def migrate(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    what TEXT NOT NULL,
                    context_json TEXT DEFAULT '{}',
                    outcome TEXT,
                    importance REAL DEFAULT 0.5,
                    emotion_weight REAL DEFAULT 0.0,
                    occurred_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_memory (
                    id TEXT PRIMARY KEY,
                    entity TEXT NOT NULL,
                    attribute TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL DEFAULT 0.6,
                    source TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS procedural_memory (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_used_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_links (
                    id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS consolidation_runs (
                    id TEXT PRIMARY KEY,
                    summary TEXT NOT NULL,
                    created_facts INTEGER DEFAULT 0,
                    created_links INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_entity ON semantic_memory(entity)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_episode_title ON episodic_memory(title)")
            conn.commit()
        return {"ok": True, "db_path": str(self.db_path)}

    def status(self):
        self.migrate()
        counts = {}
        with self.connect() as conn:
            for table in ["episodic_memory", "semantic_memory", "procedural_memory", "memory_links", "consolidation_runs"]:
                counts[table] = conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]
        return {"version": "16.6", "counts": counts, "memory_types": ["episodic", "semantic", "procedural"]}

    def add_episode(self, title, what, context=None, outcome="", importance=0.5, emotion_weight=0.0, occurred_at=None):
        self.migrate()
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "id": str(uuid4()),
            "title": title,
            "what": what,
            "context_json": json.dumps(context or {}, ensure_ascii=False),
            "outcome": outcome,
            "importance": importance,
            "emotion_weight": emotion_weight,
            "occurred_at": occurred_at or now,
            "created_at": now,
        }
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO episodic_memory(id, title, what, context_json, outcome, importance, emotion_weight, occurred_at, created_at)
                VALUES (:id, :title, :what, :context_json, :outcome, :importance, :emotion_weight, :occurred_at, :created_at)
            """, item)
            conn.commit()
        return item

    def add_fact(self, entity, attribute, value, confidence=0.6, source="manual"):
        self.migrate()
        now = datetime.now(timezone.utc).isoformat()
        existing = None
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT * FROM semantic_memory WHERE lower(entity)=? AND lower(attribute)=?",
                (entity.lower(), attribute.lower())
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE semantic_memory SET value=?, confidence=?, source=?, updated_at=? WHERE id=?",
                    (value, confidence, source, now, existing["id"])
                )
                conn.commit()
                return dict(existing) | {"value": value, "confidence": confidence, "updated": True}
            item = {
                "id": str(uuid4()),
                "entity": entity,
                "attribute": attribute,
                "value": value,
                "confidence": confidence,
                "source": source,
                "created_at": now,
                "updated_at": None,
            }
            conn.execute("""
                INSERT INTO semantic_memory(id, entity, attribute, value, confidence, source, created_at, updated_at)
                VALUES (:id, :entity, :attribute, :value, :confidence, :source, :created_at, :updated_at)
            """, item)
            conn.commit()
        return item | {"updated": False}

    def add_procedure(self, name, steps):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "name": name,
            "steps_json": json.dumps(steps, ensure_ascii=False),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO procedural_memory(id, name, steps_json, created_at) VALUES (:id, :name, :steps_json, :created_at)",
                item
            )
            conn.commit()
        return item

    def record_procedure_result(self, procedure_id, success=True):
        self.migrate()
        with self.connect() as conn:
            field = "success_count" if success else "failure_count"
            conn.execute(
                f"UPDATE procedural_memory SET {field}={field}+1, last_used_at=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), procedure_id)
            )
            row = conn.execute("SELECT * FROM procedural_memory WHERE id=?", (procedure_id,)).fetchone()
            conn.commit()
        return dict(row) if row else {"ok": False, "error": "procedure_not_found"}

    def link(self, source_type, source_id, target_type, target_id, relation):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "source_type": source_type,
            "source_id": source_id,
            "target_type": target_type,
            "target_id": target_id,
            "relation": relation,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO memory_links(id, source_type, source_id, target_type, target_id, relation, created_at)
                VALUES (:id, :source_type, :source_id, :target_type, :target_id, :relation, :created_at)
            """, item)
            conn.commit()
        return item

    def recall(self, query, memory_type="all"):
        self.migrate()
        q = f"%{query.lower()}%"
        result = {"episodic": [], "semantic": [], "procedural": []}
        with self.connect() as conn:
            if memory_type in {"all", "episodic"}:
                result["episodic"] = [dict(r) for r in conn.execute(
                    "SELECT * FROM episodic_memory WHERE lower(title) LIKE ? OR lower(what) LIKE ? OR lower(outcome) LIKE ? ORDER BY importance DESC, occurred_at DESC",
                    (q, q, q)
                ).fetchall()]
            if memory_type in {"all", "semantic"}:
                result["semantic"] = [dict(r) for r in conn.execute(
                    "SELECT * FROM semantic_memory WHERE lower(entity) LIKE ? OR lower(attribute) LIKE ? OR lower(value) LIKE ? ORDER BY confidence DESC",
                    (q, q, q)
                ).fetchall()]
            if memory_type in {"all", "procedural"}:
                result["procedural"] = [dict(r) for r in conn.execute(
                    "SELECT * FROM procedural_memory WHERE lower(name) LIKE ? OR lower(steps_json) LIKE ? ORDER BY success_count DESC",
                    (q, q)
                ).fetchall()]
        return result

    def consolidate(self):
        self.migrate()
        created_facts = 0
        created_links = 0
        episodes = []
        with self.connect() as conn:
            episodes = [dict(r) for r in conn.execute("SELECT * FROM episodic_memory ORDER BY created_at DESC LIMIT 50").fetchall()]
        for ep in episodes:
            candidates = sorted(set(re.findall(r"\b[A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9_-]{2,}\b", ep["what"] + " " + (ep.get("outcome") or ""))))
            for c in candidates[:5]:
                self.add_fact(c, "mentioned_in_episode", ep["title"], 0.55, "consolidation")
                created_facts += 1
                self.link("episode", ep["id"], "entity", c, "mentions")
                created_links += 1
        summary = f"Consolidated {len(episodes)} episodes into {created_facts} candidate facts."
        run = {
            "id": str(uuid4()),
            "summary": summary,
            "created_facts": created_facts,
            "created_links": created_links,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO consolidation_runs(id, summary, created_facts, created_links, created_at) VALUES (:id, :summary, :created_facts, :created_links, :created_at)",
                run
            )
            conn.commit()
        return run

    def importance_report(self):
        self.migrate()
        with self.connect() as conn:
            episodes = [dict(r) for r in conn.execute(
                "SELECT id, title, importance, emotion_weight, (importance + abs(emotion_weight)) AS score FROM episodic_memory ORDER BY score DESC"
            ).fetchall()]
            procedures = [dict(r) for r in conn.execute(
                "SELECT id, name, success_count, failure_count, (success_count - failure_count) AS score FROM procedural_memory ORDER BY score DESC"
            ).fetchall()]
        return {"episodes": episodes, "procedures": procedures}

    def graph_export(self):
        self.migrate()
        nodes = []
        edges = []
        with self.connect() as conn:
            for r in conn.execute("SELECT id, title FROM episodic_memory").fetchall():
                nodes.append({"id": r["id"], "label": r["title"], "kind": "episode"})
            for r in conn.execute("SELECT id, entity, attribute, value FROM semantic_memory").fetchall():
                nodes.append({"id": r["id"], "label": f"{r['entity']}.{r['attribute']}={r['value']}", "kind": "fact"})
            for r in conn.execute("SELECT * FROM memory_links").fetchall():
                edges.append(dict(r))
        return {"nodes": nodes, "edges": edges}

    def seed_demo(self):
        ep = self.add_episode(
            "Jarvis Entwicklung",
            "Markus entwickelt SecondBrain Jarvis mit Knowledge Graph und Multi Agent Runtime.",
            {"project": "SecondBrain"},
            "v16.6 Long Term Memory ergänzt.",
            0.9,
            0.2,
        )
        self.add_fact("Jarvis", "project_type", "Personal Operating System", 0.8, "seed")
        proc = self.add_procedure("Release entwickeln", ["Anforderung klären", "Code erzeugen", "Tests ergänzen", "ZIP bereitstellen"])
        self.link("episode", ep["id"], "procedure", proc["id"], "uses")
        return self.status()

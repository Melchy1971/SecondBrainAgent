import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from collections import defaultdict, deque


class KnowledgeGraphRuntime:
    def __init__(self, root=".", db_path=None):
        self.root = Path(root)
        self.data_dir = self.root / "data" / "knowledge_graph"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else self.data_dir / "knowledge_graph.sqlite3"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def migrate(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    properties_json TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    properties_json TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS graph_events (
                    id TEXT PRIMARY KEY,
                    node_id TEXT,
                    title TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    properties_json TEXT DEFAULT '{}'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_label ON nodes(label)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
            conn.commit()
        return {"ok": True, "db_path": str(self.db_path)}

    def status(self):
        self.migrate()
        with self.connect() as conn:
            nodes = conn.execute("SELECT COUNT(*) c FROM nodes").fetchone()["c"]
            edges = conn.execute("SELECT COUNT(*) c FROM edges").fetchone()["c"]
            events = conn.execute("SELECT COUNT(*) c FROM graph_events").fetchone()["c"]
        return {"version": "16.5", "nodes": nodes, "edges": edges, "events": events, "backend": "sqlite_graph_neo4j_ready"}

    def add_node(self, label, kind="concept", properties=None):
        self.migrate()
        existing = self.find_node(label, kind)
        if existing:
            return existing | {"existing": True}
        node = {
            "id": str(uuid4()),
            "label": label,
            "kind": kind,
            "properties_json": json.dumps(properties or {}, ensure_ascii=False),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO nodes(id, label, kind, properties_json, created_at) VALUES (:id, :label, :kind, :properties_json, :created_at)",
                node
            )
            conn.commit()
        return node | {"existing": False}

    def find_node(self, label, kind=None):
        self.migrate()
        with self.connect() as conn:
            if kind:
                row = conn.execute("SELECT * FROM nodes WHERE lower(label)=? AND kind=?", (label.lower(), kind)).fetchone()
            else:
                row = conn.execute("SELECT * FROM nodes WHERE lower(label)=?", (label.lower(),)).fetchone()
        return dict(row) if row else None

    def nodes(self, query=None):
        self.migrate()
        with self.connect() as conn:
            if query:
                rows = conn.execute("SELECT * FROM nodes WHERE lower(label) LIKE ? ORDER BY label", (f"%{query.lower()}%",)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM nodes ORDER BY label").fetchall()
        return [dict(r) for r in rows]

    def add_edge(self, source_label, target_label, edge_type="related_to", weight=1.0, source_kind="concept", target_kind="concept", properties=None):
        self.migrate()
        source = self.add_node(source_label, source_kind)
        target = self.add_node(target_label, target_kind)
        edge = {
            "id": str(uuid4()),
            "source_id": source["id"],
            "target_id": target["id"],
            "type": edge_type,
            "weight": weight,
            "properties_json": json.dumps(properties or {}, ensure_ascii=False),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO edges(id, source_id, target_id, type, weight, properties_json, created_at) VALUES (:id, :source_id, :target_id, :type, :weight, :properties_json, :created_at)",
                edge
            )
            conn.commit()
        return edge | {"source": source["label"], "target": target["label"]}

    def edges(self):
        self.migrate()
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT e.*, s.label AS source_label, t.label AS target_label
                FROM edges e
                JOIN nodes s ON s.id=e.source_id
                JOIN nodes t ON t.id=e.target_id
                ORDER BY e.created_at DESC
            """).fetchall()
        return [dict(r) for r in rows]

    def neighbors(self, label):
        node = self.find_node(label)
        if not node:
            return []
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT e.type, e.weight, s.label AS source_label, t.label AS target_label,
                       CASE WHEN e.source_id=? THEN t.label ELSE s.label END AS neighbor_label
                FROM edges e
                JOIN nodes s ON s.id=e.source_id
                JOIN nodes t ON t.id=e.target_id
                WHERE e.source_id=? OR e.target_id=?
            """, (node["id"], node["id"], node["id"])).fetchall()
        return [dict(r) for r in rows]

    def shortest_path(self, start_label, end_label, max_depth=5):
        start = self.find_node(start_label)
        end = self.find_node(end_label)
        if not start or not end:
            return {"ok": False, "error": "node_not_found"}
        adjacency = defaultdict(list)
        labels = {}
        with self.connect() as conn:
            for row in conn.execute("SELECT id, label FROM nodes").fetchall():
                labels[row["id"]] = row["label"]
            for edge in conn.execute("SELECT source_id, target_id, type FROM edges").fetchall():
                adjacency[edge["source_id"]].append((edge["target_id"], edge["type"]))
                adjacency[edge["target_id"]].append((edge["source_id"], edge["type"]))
        q = deque([(start["id"], [])])
        seen = {start["id"]}
        while q:
            node_id, path = q.popleft()
            if len(path) > max_depth:
                continue
            if node_id == end["id"]:
                return {"ok": True, "path": path, "labels": [labels[start["id"]]] + [step["to"] for step in path]}
            for nxt, etype in adjacency[node_id]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, path + [{"from": labels[node_id], "to": labels[nxt], "type": etype}]))
        return {"ok": False, "error": "path_not_found"}

    def communities(self):
        self.migrate()
        nodes = self.nodes()
        adjacency = defaultdict(set)
        for e in self.edges():
            adjacency[e["source_label"]].add(e["target_label"])
            adjacency[e["target_label"]].add(e["source_label"])
        seen = set()
        communities = []
        for node in nodes:
            label = node["label"]
            if label in seen:
                continue
            comp = []
            q = deque([label])
            seen.add(label)
            while q:
                cur = q.popleft()
                comp.append(cur)
                for nxt in adjacency[cur]:
                    if nxt not in seen:
                        seen.add(nxt)
                        q.append(nxt)
            communities.append({"id": f"community_{len(communities)+1}", "size": len(comp), "nodes": sorted(comp)})
        communities.sort(key=lambda c: c["size"], reverse=True)
        return communities

    def add_event(self, title, event_type="note", node_label=None, properties=None):
        self.migrate()
        node = self.find_node(node_label) if node_label else None
        event = {
            "id": str(uuid4()),
            "node_id": node["id"] if node else None,
            "title": title,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "properties_json": json.dumps(properties or {}, ensure_ascii=False),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO graph_events(id, node_id, title, event_type, timestamp, properties_json) VALUES (:id, :node_id, :title, :event_type, :timestamp, :properties_json)",
                event
            )
            conn.commit()
        return event

    def timeline(self, node_label=None):
        self.migrate()
        with self.connect() as conn:
            if node_label:
                node = self.find_node(node_label)
                if not node:
                    return []
                rows = conn.execute("SELECT * FROM graph_events WHERE node_id=? ORDER BY timestamp", (node["id"],)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM graph_events ORDER BY timestamp").fetchall()
        return [dict(r) for r in rows]

    def export_neo4j_cypher(self):
        statements = []
        for n in self.nodes():
            props = json.loads(n["properties_json"] or "{}")
            props["id"] = n["id"]
            props["label"] = n["label"]
            prop_text = ", ".join([f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in props.items()])
            statements.append(f"MERGE (n:{n['kind'].replace('-', '_')} {{id: {json.dumps(n['id'])}}}) SET n += {{{prop_text}}};")
        for e in self.edges():
            rel = e["type"].upper().replace("-", "_")
            statements.append(
                f"MATCH (a {{id: {json.dumps(e['source_id'])}}}), (b {{id: {json.dumps(e['target_id'])}}}) "
                f"MERGE (a)-[r:{rel} {{id: {json.dumps(e['id'])}}}]->(b) SET r.weight = {e['weight']};"
            )
        return {"statements": statements, "count": len(statements)}

    def seed_demo(self):
        self.add_edge("Jarvis", "SecondBrain", "powers")
        self.add_edge("SecondBrain", "Gmail", "connects_to")
        self.add_edge("SecondBrain", "GitHub", "connects_to")
        self.add_edge("Jarvis", "Knowledge Graph", "uses")
        self.add_event("Knowledge Graph v16.5 erstellt", "release", "Knowledge Graph")
        return self.status()

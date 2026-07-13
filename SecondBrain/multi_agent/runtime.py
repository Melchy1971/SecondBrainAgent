import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


AGENTS = {
    "supervisor": {"role": "orchestrates task lifecycle"},
    "planner": {"role": "decomposes goals into steps"},
    "research": {"role": "collects context and evidence"},
    "execution": {"role": "executes approved safe actions"},
    "review": {"role": "checks quality and risks"},
    "memory": {"role": "writes durable learnings"},
    "improvement": {"role": "creates improvement backlog"},
}


class MultiAgentRuntime:
    def __init__(self, root=".", db_path=None):
        self.root = Path(root)
        self.data_dir = self.root / "data" / "multi_agent"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else self.data_dir / "agents.sqlite3"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def migrate(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk TEXT DEFAULT 'low',
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_messages (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    decision TEXT NOT NULL,
                    findings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_writes (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS improvement_backlog (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    created_at TEXT NOT NULL
                )
            """)
            now = datetime.now(timezone.utc).isoformat()
            for aid, meta in AGENTS.items():
                conn.execute(
                    "INSERT OR IGNORE INTO agents(id, role, enabled, created_at) VALUES (?, ?, 1, ?)",
                    (aid, meta["role"], now)
                )
            conn.commit()
        return {"ok": True, "agents": len(AGENTS), "db_path": str(self.db_path)}

    def status(self):
        self.migrate()
        with self.connect() as conn:
            counts = {}
            for table in ["agents", "tasks", "plans", "agent_messages", "results", "reviews", "memory_writes", "improvement_backlog"]:
                counts[table] = conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]
        return {"version": "16.4", "counts": counts}

    def agents(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM agents ORDER BY id").fetchall()]

    def create_task(self, title, objective, risk="low"):
        self.migrate()
        task = {
            "id": str(uuid4()),
            "title": title,
            "objective": objective,
            "status": "created",
            "risk": risk,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO tasks(id, title, objective, status, risk, created_at) VALUES (:id, :title, :objective, :status, :risk, :created_at)",
                task
            )
            conn.commit()
        self.message(task["id"], "supervisor", "planner", f"Plan task: {objective}")
        return task

    def tasks(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()]

    def get_task(self, task_id):
        self.migrate()
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return dict(row) if row else None

    def message(self, task_id, sender, recipient, message):
        msg = {
            "id": str(uuid4()),
            "task_id": task_id,
            "sender": sender,
            "recipient": recipient,
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO agent_messages(id, task_id, sender, recipient, message, created_at) VALUES (:id, :task_id, :sender, :recipient, :message, :created_at)",
                msg
            )
            conn.commit()
        return msg

    def messages(self, task_id=None):
        self.migrate()
        with self.connect() as conn:
            if task_id:
                rows = conn.execute("SELECT * FROM agent_messages WHERE task_id=? ORDER BY created_at", (task_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM agent_messages ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def plan(self, task_id):
        task = self.get_task(task_id)
        if not task:
            return {"ok": False, "error": "task_not_found"}
        steps = [
            {"id": "research", "agent": "research", "action": "collect_context", "depends_on": []},
            {"id": "execute", "agent": "execution", "action": "produce_result", "depends_on": ["research"]},
            {"id": "review", "agent": "review", "action": "quality_gate", "depends_on": ["execute"]},
            {"id": "memory", "agent": "memory", "action": "write_learning", "depends_on": ["review"]},
            {"id": "improvement", "agent": "improvement", "action": "create_backlog_if_needed", "depends_on": ["review"]},
        ]
        plan = {
            "id": str(uuid4()),
            "task_id": task_id,
            "steps_json": json.dumps(steps, ensure_ascii=False),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO plans(id, task_id, steps_json, created_at) VALUES (:id, :task_id, :steps_json, :created_at)",
                plan
            )
            conn.execute("UPDATE tasks SET status='planned' WHERE id=?", (task_id,))
            conn.commit()
        self.message(task_id, "planner", "supervisor", "Plan created")
        return {"ok": True, "plan_id": plan["id"], "steps": steps}

    def _record_result(self, task_id, agent, status, payload):
        result = {
            "id": str(uuid4()),
            "task_id": task_id,
            "agent": agent,
            "status": status,
            "payload_json": json.dumps(payload, ensure_ascii=False),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO results(id, task_id, agent, status, payload_json, created_at) VALUES (:id, :task_id, :agent, :status, :payload_json, :created_at)",
                result
            )
            conn.commit()
        return result

    def run(self, task_id):
        task = self.get_task(task_id)
        if not task:
            return {"ok": False, "error": "task_not_found"}
        if task["status"] == "created":
            self.plan(task_id)

        research = {"summary": f"Context collected for {task['objective']}", "sources": ["local_memory", "document_index"]}
        self._record_result(task_id, "research", "success", research)
        self.message(task_id, "research", "execution", "Context ready")

        if task["risk"] == "high":
            execution = {"status": "approval_required", "reason": "high_risk_task"}
            self._record_result(task_id, "execution", "approval_required", execution)
        else:
            execution = {"output": f"Completed objective: {task['objective']}", "mode": "simulated_safe_execution"}
            self._record_result(task_id, "execution", "success", execution)

        score = 0.95 if task["risk"] == "low" else 0.55
        decision = "pass" if score >= 0.7 else "needs_approval"
        findings = [{"type": "risk", "value": task["risk"]}]
        review = {
            "id": str(uuid4()),
            "task_id": task_id,
            "score": score,
            "decision": decision,
            "findings_json": json.dumps(findings, ensure_ascii=False),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO reviews(id, task_id, score, decision, findings_json, created_at) VALUES (:id, :task_id, :score, :decision, :findings_json, :created_at)",
                review
            )
            conn.commit()

        memory_text = f"Task '{task['title']}' reviewed with decision {decision}"
        memory = {
            "id": str(uuid4()),
            "task_id": task_id,
            "content": memory_text,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO memory_writes(id, task_id, content, created_at) VALUES (:id, :task_id, :content, :created_at)",
                memory
            )
            if decision != "pass":
                conn.execute(
                    "INSERT INTO improvement_backlog(id, task_id, title, priority, status, created_at) VALUES (?, ?, ?, ?, 'open', ?)",
                    (str(uuid4()), task_id, "Reduce approval friction or clarify risk", "high", datetime.now(timezone.utc).isoformat())
                )
            conn.execute(
                "UPDATE tasks SET status=?, completed_at=? WHERE id=?",
                ("completed" if decision == "pass" else "needs_approval", datetime.now(timezone.utc).isoformat(), task_id)
            )
            conn.commit()

        return {"ok": True, "task_id": task_id, "decision": decision, "score": score}

    def results(self, task_id=None):
        self.migrate()
        with self.connect() as conn:
            if task_id:
                rows = conn.execute("SELECT * FROM results WHERE task_id=? ORDER BY created_at", (task_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM results ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def reviews(self, task_id=None):
        self.migrate()
        with self.connect() as conn:
            if task_id:
                rows = conn.execute("SELECT * FROM reviews WHERE task_id=? ORDER BY created_at", (task_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM reviews ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def memory(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM memory_writes ORDER BY created_at DESC").fetchall()]

    def backlog(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM improvement_backlog ORDER BY created_at DESC").fetchall()]

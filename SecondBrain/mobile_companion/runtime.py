import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


DEFAULT_WIDGETS = [
    {"id": "today", "name": "Today", "kind": "summary", "enabled": 1},
    {"id": "quick_capture", "name": "Quick Capture", "kind": "action", "enabled": 1},
    {"id": "approvals", "name": "Approvals", "kind": "inbox", "enabled": 1},
    {"id": "voice_note", "name": "Voice Note", "kind": "action", "enabled": 1},
    {"id": "camera_ocr", "name": "Camera OCR", "kind": "action", "enabled": 1},
]


class MobileCompanionRuntime:
    def __init__(self, root=".", db_path=None):
        self.root = Path(root)
        self.data_dir = self.root / "data" / "mobile_companion"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else self.data_dir / "mobile.sqlite3"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def migrate(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    trust_level TEXT DEFAULT 'untrusted',
                    capabilities_json TEXT DEFAULT '[]',
                    paired_at TEXT,
                    last_seen TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pairing_requests (
                    id TEXT PRIMARY KEY,
                    device_name TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    pairing_code TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    decided_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS offline_queue (
                    id TEXT PRIMARY KEY,
                    device_id TEXT,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT DEFAULT 'queued',
                    created_at TEXT NOT NULL,
                    replayed_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS push_outbox (
                    id TEXT PRIMARY KEY,
                    device_id TEXT,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    priority TEXT DEFAULT 'normal',
                    status TEXT DEFAULT 'queued',
                    created_at TEXT NOT NULL,
                    delivered_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mobile_widgets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_runs (
                    id TEXT PRIMARY KEY,
                    device_id TEXT,
                    domains_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    conflicts INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mobile_sessions (
                    id TEXT PRIMARY KEY,
                    device_id TEXT,
                    title TEXT NOT NULL,
                    state_json TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL
                )
            """)
            for widget in DEFAULT_WIDGETS:
                conn.execute(
                    "INSERT OR IGNORE INTO mobile_widgets(id, name, kind, enabled) VALUES (:id, :name, :kind, :enabled)",
                    widget
                )
            conn.commit()
        return {"ok": True, "db_path": str(self.db_path)}

    def status(self):
        self.migrate()
        counts = {}
        with self.connect() as conn:
            for table in ["devices", "pairing_requests", "offline_queue", "push_outbox", "mobile_widgets", "sync_runs", "mobile_sessions"]:
                counts[table] = conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]
        return {"version": "16.9", "counts": counts, "platforms": ["ios", "android", "web"], "mode": "backend_foundation"}

    def pair_request(self, device_name, platform):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "device_name": device_name,
            "platform": platform,
            "pairing_code": str(uuid4())[:8],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO pairing_requests(id, device_name, platform, pairing_code, created_at) VALUES (:id, :device_name, :platform, :pairing_code, :created_at)",
                item
            )
            conn.commit()
        return item

    def approve_pairing(self, request_id):
        self.migrate()
        with self.connect() as conn:
            req = conn.execute("SELECT * FROM pairing_requests WHERE id=?", (request_id,)).fetchone()
            if not req:
                return {"ok": False, "error": "request_not_found"}
            now = datetime.now(timezone.utc).isoformat()
            conn.execute("UPDATE pairing_requests SET status='approved', decided_at=? WHERE id=?", (now, request_id))
            device = {
                "id": str(uuid4()),
                "name": req["device_name"],
                "platform": req["platform"],
                "trust_level": "trusted",
                "capabilities_json": json.dumps(["sync", "push", "capture", "voice", "camera_ocr"]),
                "paired_at": now,
                "last_seen": now,
                "created_at": now,
            }
            conn.execute(
                "INSERT INTO devices(id, name, platform, trust_level, capabilities_json, paired_at, last_seen, created_at) VALUES (:id, :name, :platform, :trust_level, :capabilities_json, :paired_at, :last_seen, :created_at)",
                device
            )
            conn.commit()
        return {"ok": True, "device": device}

    def devices(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM devices ORDER BY created_at DESC").fetchall()]

    def pairing_requests(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM pairing_requests ORDER BY created_at DESC").fetchall()]

    def capture(self, kind, payload, device_id=None):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "device_id": device_id,
            "kind": kind,
            "payload_json": json.dumps(payload, ensure_ascii=False),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO offline_queue(id, device_id, kind, payload_json, created_at) VALUES (:id, :device_id, :kind, :payload_json, :created_at)",
                item
            )
            conn.commit()
        return item

    def voice_note(self, text, device_id=None):
        return self.capture("voice_note", {"text": text, "transcription_status": "manual"}, device_id)

    def camera_ocr(self, image_ref, device_id=None):
        return self.capture("camera_ocr", {"image_ref": image_ref, "ocr_status": "pending", "text": ""}, device_id)

    def offline_queue(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM offline_queue ORDER BY created_at DESC").fetchall()]

    def replay_offline(self, limit=50):
        self.migrate()
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            rows = [dict(r) for r in conn.execute("SELECT * FROM offline_queue WHERE status='queued' ORDER BY created_at LIMIT ?", (limit,)).fetchall()]
            for row in rows:
                conn.execute("UPDATE offline_queue SET status='replayed', replayed_at=? WHERE id=?", (now, row["id"]))
            conn.commit()
        return {"ok": True, "replayed": len(rows), "items": rows}

    def push(self, title, body, device_id=None, priority="normal"):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "device_id": device_id,
            "title": title,
            "body": body,
            "priority": priority,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO push_outbox(id, device_id, title, body, priority, created_at) VALUES (:id, :device_id, :title, :body, :priority, :created_at)",
                item
            )
            conn.commit()
        return item

    def push_outbox(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM push_outbox ORDER BY created_at DESC").fetchall()]

    def deliver_push(self):
        self.migrate()
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            rows = [dict(r) for r in conn.execute("SELECT * FROM push_outbox WHERE status='queued'").fetchall()]
            for row in rows:
                conn.execute("UPDATE push_outbox SET status='delivered', delivered_at=? WHERE id=?", (now, row["id"]))
            conn.commit()
        return {"ok": True, "delivered": len(rows)}

    def widgets(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM mobile_widgets ORDER BY id").fetchall()]

    def widget_enable(self, widget_id, enabled=True):
        self.migrate()
        with self.connect() as conn:
            conn.execute("UPDATE mobile_widgets SET enabled=? WHERE id=?", (1 if enabled else 0, widget_id))
            row = conn.execute("SELECT * FROM mobile_widgets WHERE id=?", (widget_id,)).fetchone()
            conn.commit()
        return dict(row) if row else {"ok": False, "error": "widget_not_found"}

    def sync(self, device_id=None):
        self.migrate()
        domains = ["memories", "tasks", "documents", "notifications", "sessions", "settings"]
        run = {
            "id": str(uuid4()),
            "device_id": device_id,
            "domains_json": json.dumps(domains),
            "status": "success",
            "conflicts": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO sync_runs(id, device_id, domains_json, status, conflicts, created_at) VALUES (:id, :device_id, :domains_json, :status, :conflicts, :created_at)",
                run
            )
            conn.commit()
        return run

    def sync_runs(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM sync_runs ORDER BY created_at DESC").fetchall()]

    def session_create(self, title, device_id=None, state=None):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "device_id": device_id,
            "title": title,
            "state_json": json.dumps(state or {}, ensure_ascii=False),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO mobile_sessions(id, device_id, title, state_json, created_at) VALUES (:id, :device_id, :title, :state_json, :created_at)",
                item
            )
            conn.commit()
        return item

    def sessions(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM mobile_sessions ORDER BY created_at DESC").fetchall()]

    def app_manifest(self):
        return {
            "name": "SecondBrain Mobile Companion",
            "version": "16.9",
            "targets": ["iOS", "Android", "PWA"],
            "screens": ["Today", "Capture", "Approvals", "Voice", "Camera OCR", "Settings"],
            "api": ["pair", "sync", "push", "capture", "widgets", "sessions"],
        }

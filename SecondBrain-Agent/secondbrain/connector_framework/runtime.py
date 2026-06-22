import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


CONNECTORS = {
    "gmail": {"kind": "email", "auth": "oauth2", "scopes": ["gmail.readonly"]},
    "google_calendar": {"kind": "calendar", "auth": "oauth2", "scopes": ["calendar.readonly"]},
    "google_drive": {"kind": "documents", "auth": "oauth2", "scopes": ["drive.readonly"]},
    "github": {"kind": "code", "auth": "oauth2", "scopes": ["repo", "read:user"]},
    "obsidian": {"kind": "vault", "auth": "local_path", "scopes": ["files.read"]},
    "paperless": {"kind": "documents", "auth": "api_token", "scopes": ["documents.read"]},
}


class ConnectorFrameworkRuntime:
    def __init__(self, root=".", db_path=None):
        self.root = Path(root)
        self.data_dir = self.root / "data" / "connector_framework"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path else self.data_dir / "connectors.sqlite3"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def migrate(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS connectors (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    auth TEXT NOT NULL,
                    enabled INTEGER DEFAULT 0,
                    config_json TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS connector_tokens (
                    id TEXT PRIMARY KEY,
                    connector_id TEXT NOT NULL,
                    token_ref TEXT NOT NULL,
                    scopes_json TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS connector_cursors (
                    connector_id TEXT PRIMARY KEY,
                    cursor TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS connector_runs (
                    id TEXT PRIMARY KEY,
                    connector_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    items INTEGER DEFAULT 0,
                    error TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS connector_items (
                    id TEXT PRIMARY KEY,
                    connector_id TEXT NOT NULL,
                    remote_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS connector_dead_letters (
                    id TEXT PRIMARY KEY,
                    connector_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    error TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            for cid, meta in CONNECTORS.items():
                conn.execute(
                    "INSERT OR IGNORE INTO connectors(id, kind, auth, enabled, config_json, created_at) VALUES (?, ?, ?, 0, '{}', ?)",
                    (cid, meta["kind"], meta["auth"], datetime.now(timezone.utc).isoformat())
                )
            conn.commit()
        return {"ok": True, "db_path": str(self.db_path), "connectors": len(CONNECTORS)}

    def status(self):
        self.migrate()
        with self.connect() as conn:
            connectors = conn.execute("SELECT COUNT(*) c FROM connectors").fetchone()["c"]
            enabled = conn.execute("SELECT COUNT(*) c FROM connectors WHERE enabled=1").fetchone()["c"]
            runs = conn.execute("SELECT COUNT(*) c FROM connector_runs").fetchone()["c"]
            items = conn.execute("SELECT COUNT(*) c FROM connector_items").fetchone()["c"]
            dlq = conn.execute("SELECT COUNT(*) c FROM connector_dead_letters").fetchone()["c"]
        return {"version": "16.2", "connectors": connectors, "enabled": enabled, "runs": runs, "items": items, "dead_letters": dlq}

    def list_connectors(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM connectors ORDER BY id").fetchall()]

    def enable(self, connector_id, enabled=True):
        self.migrate()
        if connector_id not in CONNECTORS:
            return {"ok": False, "error": "unknown_connector"}
        with self.connect() as conn:
            conn.execute(
                "UPDATE connectors SET enabled=?, updated_at=? WHERE id=?",
                (1 if enabled else 0, datetime.now(timezone.utc).isoformat(), connector_id)
            )
            conn.commit()
        return {"ok": True, "connector_id": connector_id, "enabled": enabled}

    def configure(self, connector_id, config):
        self.migrate()
        if connector_id not in CONNECTORS:
            return {"ok": False, "error": "unknown_connector"}
        with self.connect() as conn:
            conn.execute(
                "UPDATE connectors SET config_json=?, updated_at=? WHERE id=?",
                (json.dumps(config, ensure_ascii=False), datetime.now(timezone.utc).isoformat(), connector_id)
            )
            conn.commit()
        return {"ok": True, "connector_id": connector_id, "config": config}

    def oauth_template(self, connector_id):
        if connector_id not in CONNECTORS:
            return {"ok": False, "error": "unknown_connector"}
        meta = CONNECTORS[connector_id]
        return {
            "connector_id": connector_id,
            "auth": meta["auth"],
            "scopes": meta["scopes"],
            "redirect_uri": "http://127.0.0.1:8765/oauth/callback",
            "status": "template_only",
        }

    def token_store(self, connector_id, token_ref, scopes=None):
        self.migrate()
        item = {
            "id": str(uuid4()),
            "connector_id": connector_id,
            "token_ref": token_ref,
            "scopes_json": json.dumps(scopes or CONNECTORS.get(connector_id, {}).get("scopes", [])),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO connector_tokens(id, connector_id, token_ref, scopes_json, created_at) VALUES (:id, :connector_id, :token_ref, :scopes_json, :created_at)",
                item
            )
            conn.commit()
        return {k: v for k, v in item.items() if k != "token_ref"} | {"token_ref": "***REDACTED***"}

    def cursor(self, connector_id):
        self.migrate()
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM connector_cursors WHERE connector_id=?", (connector_id,)).fetchone()
        return dict(row) if row else {"connector_id": connector_id, "cursor": None}

    def _fake_fetch(self, connector_id, cursor):
        samples = {
            "gmail": [{"remote_id": "mail-1", "kind": "email", "subject": "Demo Mail", "cursor": cursor}],
            "google_calendar": [{"remote_id": "event-1", "kind": "calendar_event", "title": "Demo Termin", "cursor": cursor}],
            "google_drive": [{"remote_id": "drive-1", "kind": "drive_file", "name": "Demo Datei", "cursor": cursor}],
            "github": [{"remote_id": "issue-1", "kind": "github_issue", "title": "Demo Issue", "cursor": cursor}],
            "obsidian": [{"remote_id": "note-1", "kind": "markdown_note", "title": "Demo Note", "cursor": cursor}],
            "paperless": [{"remote_id": "doc-1", "kind": "paperless_document", "title": "Demo Dokument", "cursor": cursor}],
        }
        return samples.get(connector_id, [])

    def sync(self, connector_id):
        self.migrate()
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM connectors WHERE id=?", (connector_id,)).fetchone()
            if not row:
                return {"ok": False, "error": "unknown_connector"}
            if not row["enabled"]:
                return {"ok": False, "error": "connector_disabled"}
            cursor_row = conn.execute("SELECT cursor FROM connector_cursors WHERE connector_id=?", (connector_id,)).fetchone()
            cursor = cursor_row["cursor"] if cursor_row else None

        try:
            items = self._fake_fetch(connector_id, cursor)
            run_id = str(uuid4())
            now = datetime.now(timezone.utc).isoformat()
            with self.connect() as conn:
                for payload in items:
                    conn.execute(
                        "INSERT INTO connector_items(id, connector_id, remote_id, kind, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (str(uuid4()), connector_id, payload["remote_id"], payload["kind"], json.dumps(payload, ensure_ascii=False), now)
                    )
                conn.execute(
                    "INSERT INTO connector_runs(id, connector_id, status, items, created_at) VALUES (?, ?, 'success', ?, ?)",
                    (run_id, connector_id, len(items), now)
                )
                conn.execute(
                    "INSERT OR REPLACE INTO connector_cursors(connector_id, cursor, updated_at) VALUES (?, ?, ?)",
                    (connector_id, now, now)
                )
                conn.commit()
            return {"ok": True, "connector_id": connector_id, "items": len(items), "run_id": run_id}
        except Exception as exc:
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO connector_dead_letters(id, connector_id, payload_json, error, created_at) VALUES (?, ?, ?, ?, ?)",
                    (str(uuid4()), connector_id, "{}", str(exc), datetime.now(timezone.utc).isoformat())
                )
                conn.commit()
            return {"ok": False, "connector_id": connector_id, "error": str(exc)}

    def sync_all(self):
        self.migrate()
        with self.connect() as conn:
            ids = [r["id"] for r in conn.execute("SELECT id FROM connectors WHERE enabled=1").fetchall()]
        return [self.sync(cid) for cid in ids]

    def runs(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM connector_runs ORDER BY created_at DESC").fetchall()]

    def items(self, connector_id=None):
        self.migrate()
        with self.connect() as conn:
            if connector_id:
                rows = conn.execute("SELECT * FROM connector_items WHERE connector_id=? ORDER BY created_at DESC", (connector_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM connector_items ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def dead_letters(self):
        self.migrate()
        with self.connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM connector_dead_letters ORDER BY created_at DESC").fetchall()]

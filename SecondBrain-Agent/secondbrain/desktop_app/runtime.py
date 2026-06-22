import json
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


class Store:
    def __init__(self, root="."):
        self.base = Path(root) / "data" / "desktop_app"
        self.base.mkdir(parents=True, exist_ok=True)

    def load(self, name, default):
        path = self.base / f"{name}.json"
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, name, value):
        (self.base / f"{name}.json").write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")

    def append(self, name, item):
        items = self.load(name, [])
        items.append(item)
        self.save(name, items)
        return item


class DesktopAppRuntime:
    def __init__(self, root="."):
        self.store = Store(root)

    def status(self):
        return {
            "version": "16.0",
            "app": "PySide6 Desktop App Foundation",
            "runtime": self.store.load("runtime", {"status": "stopped"}),
            "notifications": len(self.notifications()),
            "tasks": len(self.tasks()),
            "knowledge_items": len(self.knowledge()),
            "chat_messages": len(self.messages()),
            "settings": self.settings(),
        }

    def start_runtime(self):
        state = {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()}
        self.store.save("runtime", state)
        return state

    def stop_runtime(self):
        state = {"status": "stopped", "stopped_at": datetime.now(timezone.utc).isoformat()}
        self.store.save("runtime", state)
        return state

    def settings(self):
        settings = self.store.load("settings", None)
        if settings is None:
            settings = {"theme": "dark", "accent": "blue", "system_tray": True}
            self.store.save("settings", settings)
        return settings

    def set_setting(self, key, value):
        settings = self.settings()
        settings[key] = value
        self.store.save("settings", settings)
        return settings

    def notify(self, title, message, level="info"):
        item = {"id": str(uuid4()), "title": title, "message": message, "level": level, "created_at": datetime.now(timezone.utc).isoformat()}
        return self.store.append("notifications", item)

    def notifications(self):
        return self.store.load("notifications", [])

    def chat(self, text):
        user = {"id": str(uuid4()), "role": "user", "text": text, "created_at": datetime.now(timezone.utc).isoformat()}
        assistant = {"id": str(uuid4()), "role": "assistant", "text": f"Echo: {text}", "created_at": datetime.now(timezone.utc).isoformat()}
        self.store.append("chat_messages", user)
        self.store.append("chat_messages", assistant)
        return {"user": user, "assistant": assistant}

    def messages(self):
        return self.store.load("chat_messages", [])

    def add_knowledge(self, title, text="", tags=None):
        item = {"id": str(uuid4()), "title": title, "text": text, "tags": tags or []}
        return self.store.append("knowledge", item)

    def knowledge(self):
        return self.store.load("knowledge", [])

    def search_knowledge(self, query):
        q = query.lower()
        return [x for x in self.knowledge() if q in x["title"].lower() or q in x.get("text", "").lower() or any(q in t.lower() for t in x.get("tags", []))]

    def add_task(self, title, column="backlog", priority="medium"):
        item = {"id": str(uuid4()), "title": title, "column": column, "priority": priority, "created_at": datetime.now(timezone.utc).isoformat()}
        return self.store.append("tasks", item)

    def tasks(self):
        return self.store.load("tasks", [])

    def seed(self):
        self.start_runtime()
        self.notify("SecondBrain", "Desktop App bereit")
        self.add_task("PySide6 GUI testen", "doing", "high")
        self.add_knowledge("Jarvis Architektur", "Desktop, Agenten, Memory, RAG", ["jarvis", "architecture"])
        self.chat("Systemstatus")
        return self.status()

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Iterable
import fnmatch
import json
import time
import uuid

Handler = Callable[[dict[str, Any]], Any]

@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    topic: str
    source: str
    payload: dict[str, Any]
    risk_level: int
    created_at: float
    correlation_id: str | None = None

class JsonlEventStore:
    def __init__(self, runtime_dir: str | Path):
        self.root = Path(runtime_dir) / 'events_v121'
        self.root.mkdir(parents=True, exist_ok=True)
        self.events_file = self.root / 'events.jsonl'
        self.dlq_file = self.root / 'dead_letter.jsonl'
        self.subscriptions_file = self.root / 'subscriptions.json'

    def append(self, envelope: EventEnvelope) -> dict[str, Any]:
        row = asdict(envelope)
        with self.events_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
        return row

    def append_dead_letter(self, envelope: EventEnvelope, error: str, subscriber: str) -> dict[str, Any]:
        row = asdict(envelope) | {'error': error, 'subscriber': subscriber, 'failed_at': time.time()}
        with self.dlq_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
        return row

    def _read_jsonl(self, path: Path, limit: int | None = None) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows = []
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.strip():
                rows.append(json.loads(line))
        if limit is not None:
            return rows[-limit:]
        return rows

    def events(self, topic: str | None = None, limit: int | None = None, since: float | None = None) -> list[dict[str, Any]]:
        rows = self._read_jsonl(self.events_file, None)
        if topic:
            rows = [r for r in rows if fnmatch.fnmatch(r.get('topic',''), topic)]
        if since is not None:
            rows = [r for r in rows if float(r.get('created_at', 0)) >= since]
        if limit is not None:
            rows = rows[-limit:]
        return rows

    def dead_letters(self, limit: int | None = None) -> list[dict[str, Any]]:
        return self._read_jsonl(self.dlq_file, limit)

    def save_subscriptions(self, subscriptions: list[dict[str, Any]]) -> None:
        self.subscriptions_file.write_text(json.dumps(subscriptions, indent=2, ensure_ascii=False), encoding='utf-8')

    def load_subscriptions(self) -> list[dict[str, Any]]:
        if not self.subscriptions_file.exists():
            return []
        return json.loads(self.subscriptions_file.read_text(encoding='utf-8'))

class EventBus:
    def __init__(self, runtime_dir: str | Path):
        self.store = JsonlEventStore(runtime_dir)
        self._handlers: dict[str, list[tuple[str, Handler]]] = {}
        self._persistent_subscriptions = self.store.load_subscriptions()

    def subscribe(self, pattern: str, subscriber: str, handler: Handler | None = None, persistent: bool = False) -> dict[str, Any]:
        if handler is not None:
            self._handlers.setdefault(pattern, []).append((subscriber, handler))
        row = {'pattern': pattern, 'subscriber': subscriber, 'persistent': persistent, 'created_at': time.time()}
        if persistent:
            existing = self.store.load_subscriptions()
            if not any(x['pattern'] == pattern and x['subscriber'] == subscriber for x in existing):
                existing.append(row)
                self.store.save_subscriptions(existing)
                self._persistent_subscriptions = existing
        return row

    def publish(self, topic: str, source: str, payload: dict[str, Any] | None = None, risk_level: int = 1, correlation_id: str | None = None) -> dict[str, Any]:
        envelope = EventEnvelope(
            event_id=f'evt_{uuid.uuid4().hex[:12]}',
            topic=topic,
            source=source,
            payload=payload or {},
            risk_level=max(1, min(5, int(risk_level))),
            created_at=time.time(),
            correlation_id=correlation_id,
        )
        row = self.store.append(envelope)
        for pattern, handlers in list(self._handlers.items()):
            if not fnmatch.fnmatch(topic, pattern):
                continue
            for subscriber, handler in handlers:
                try:
                    handler(row)
                except Exception as exc:
                    self.store.append_dead_letter(envelope, str(exc), subscriber)
        return row

    def replay(self, topic: str | None = None, limit: int = 100, since: float | None = None) -> list[dict[str, Any]]:
        return self.store.events(topic, limit, since)

    def dead_letters(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.store.dead_letters(limit)

    def status(self) -> dict[str, Any]:
        return {
            'component': 'event_bus_v121',
            'events': len(self.store.events()),
            'dead_letters': len(self.store.dead_letters()),
            'runtime_handlers': sum(len(v) for v in self._handlers.values()),
            'persistent_subscriptions': len(self.store.load_subscriptions()),
            'healthy': True,
        }

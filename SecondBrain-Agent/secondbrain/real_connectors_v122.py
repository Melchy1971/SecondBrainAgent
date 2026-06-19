from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable
from datetime import datetime, timezone, timedelta
import hashlib, json, time, uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding='utf-8')
    tmp.replace(path)


@dataclass
class OAuthConfig:
    provider: str
    client_id_env: str
    client_secret_env: str
    scopes: list[str]
    redirect_uri: str = 'http://localhost:8765/oauth/callback'
    auth_url: str = ''
    token_url: str = ''
    enabled: bool = False


@dataclass
class ConnectorDefinition:
    name: str
    provider: str
    kind: str
    scopes: list[str]
    enabled: bool = False
    supports_delta: bool = True
    supports_webhook: bool = False
    risk_level: int = 1


@dataclass
class SyncResult:
    connector: str
    status: str
    pulled: int
    emitted: int
    cursor_before: str | None
    cursor_after: str | None
    errors: list[str]


class ConnectorStateStore:
    def __init__(self, runtime_dir: str | Path):
        self.root = Path(runtime_dir) / 'real_connectors_v122'
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_file = self.root / 'connector_state.json'
        self.queue_file = self.root / 'offline_queue.jsonl'
        self.runs_file = self.root / 'sync_runs.jsonl'
        self.webhook_file = self.root / 'webhook_inbox.jsonl'
        self.oauth_file = self.root / 'oauth_configs.json'

    def load_state(self) -> dict[str, Any]:
        return _read_json(self.state_file, {'connectors': {}, 'updated_at': _now()})

    def save_state(self, state: dict[str, Any]) -> None:
        state['updated_at'] = _now()
        _write_json(self.state_file, state)

    def get_connector_state(self, name: str) -> dict[str, Any]:
        state = self.load_state()
        return state.setdefault('connectors', {}).setdefault(name, {'cursor': None, 'last_sync_at': None, 'failures': 0})

    def update_connector_state(self, name: str, patch: dict[str, Any]) -> dict[str, Any]:
        state = self.load_state()
        c = state.setdefault('connectors', {}).setdefault(name, {'cursor': None, 'last_sync_at': None, 'failures': 0})
        c.update(patch)
        self.save_state(state)
        return c

    def append_run(self, run: dict[str, Any]) -> None:
        self.runs_file.parent.mkdir(parents=True, exist_ok=True)
        with self.runs_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(run, ensure_ascii=False, sort_keys=True) + '\n')

    def runs(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.runs_file.exists():
            return []
        lines = self.runs_file.read_text(encoding='utf-8').splitlines()[-limit:]
        return [json.loads(x) for x in lines if x.strip()]

    def enqueue(self, item: dict[str, Any]) -> dict[str, Any]:
        item = dict(item)
        item.setdefault('id', str(uuid.uuid4()))
        item.setdefault('created_at', _now())
        item.setdefault('attempts', 0)
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        with self.queue_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + '\n')
        return item

    def queue_items(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self.queue_file.exists():
            return []
        lines = self.queue_file.read_text(encoding='utf-8').splitlines()[:limit]
        return [json.loads(x) for x in lines if x.strip()]

    def replace_queue(self, items: list[dict[str, Any]]) -> None:
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        with self.queue_file.open('w', encoding='utf-8') as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + '\n')

    def append_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = {'id': str(uuid.uuid4()), 'received_at': _now(), 'payload': payload}
        self.webhook_file.parent.mkdir(parents=True, exist_ok=True)
        with self.webhook_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + '\n')
        return event

    def webhooks(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.webhook_file.exists():
            return []
        return [json.loads(x) for x in self.webhook_file.read_text(encoding='utf-8').splitlines()[-limit:] if x.strip()]


class DeltaCursor:
    @staticmethod
    def next_cursor(connector: str, previous: str | None, items: list[dict[str, Any]]) -> str:
        material = json.dumps({'connector': connector, 'previous': previous, 'ids': [i.get('id') for i in items], 'count': len(items)}, sort_keys=True)
        return hashlib.sha256(material.encode('utf-8')).hexdigest()[:16]


class MockConnectorAdapter:
    """Deterministic offline adapter. Replaced later by Gmail/Graph/Drive API adapters."""
    def __init__(self, definition: ConnectorDefinition):
        self.definition = definition

    def pull(self, cursor: str | None = None, limit: int = 10) -> tuple[list[dict[str, Any]], str]:
        base = cursor or 'initial'
        items=[]
        for i in range(min(limit, 3)):
            item_id = hashlib.sha1(f'{self.definition.name}:{base}:{i}'.encode()).hexdigest()[:12]
            items.append({
                'id': item_id,
                'connector': self.definition.name,
                'provider': self.definition.provider,
                'kind': self.definition.kind,
                'title': f'{self.definition.name} item {i+1}',
                'body': f'Deterministic {self.definition.kind} payload for {self.definition.provider}',
                'updated_at': _now(),
            })
        return items, DeltaCursor.next_cursor(self.definition.name, cursor, items)


class RetryPolicy:
    def __init__(self, max_attempts: int = 3, base_delay_seconds: int = 5):
        self.max_attempts=max_attempts
        self.base_delay_seconds=base_delay_seconds

    def next_delay(self, attempts: int) -> int:
        return min(3600, self.base_delay_seconds * (2 ** max(0, attempts-1)))

    def can_retry(self, attempts: int) -> bool:
        return attempts < self.max_attempts


class RealConnectorRegistry:
    def __init__(self, runtime_dir: str | Path, event_bus: Any | None = None):
        self.store = ConnectorStateStore(runtime_dir)
        self.event_bus = event_bus
        self.definitions: dict[str, ConnectorDefinition] = {}
        self.adapters: dict[str, Any] = {}
        self.retry = RetryPolicy()
        self._register_defaults()

    def _register_defaults(self) -> None:
        defaults = [
            ConnectorDefinition('gmail', 'google', 'email', ['email.read'], True, True, True, 1),
            ConnectorDefinition('google_calendar', 'google', 'calendar', ['calendar.read'], True, True, True, 1),
            ConnectorDefinition('google_drive', 'google', 'document', ['drive.read'], False, True, True, 1),
            ConnectorDefinition('outlook_mail', 'microsoft', 'email', ['email.read'], False, True, True, 1),
            ConnectorDefinition('outlook_calendar', 'microsoft', 'calendar', ['calendar.read'], False, True, True, 1),
            ConnectorDefinition('onedrive', 'microsoft', 'document', ['drive.read'], False, True, True, 1),
            ConnectorDefinition('github', 'github', 'code', ['repo.read'], False, True, True, 1),
            ConnectorDefinition('obsidian', 'local', 'document', ['files.read'], True, True, False, 1),
            ConnectorDefinition('paperless', 'local_api', 'document', ['documents.read'], False, True, True, 1),
            ConnectorDefinition('home_assistant', 'local_api', 'smart_home', ['home.read'], False, True, True, 2),
            ConnectorDefinition('mygekko', 'local_api', 'smart_home', ['home.read'], False, True, False, 2),
            ConnectorDefinition('solaredge', 'cloud_api', 'energy', ['energy.read'], False, True, True, 1),
        ]
        for d in defaults:
            self.register(d, MockConnectorAdapter(d))

    def register(self, definition: ConnectorDefinition, adapter: Any | None = None) -> None:
        self.definitions[definition.name]=definition
        self.adapters[definition.name]=adapter or MockConnectorAdapter(definition)

    def status(self) -> dict[str, Any]:
        state=self.store.load_state()
        return {
            'version':'12.2',
            'connectors': [asdict(d) | {'state': state.get('connectors', {}).get(d.name, {})} for d in self.definitions.values()],
            'queue_depth': len(self.store.queue_items(10000)),
            'webhooks': len(self.store.webhooks(10000)),
            'runs': len(self.store.runs(10000)),
        }

    def list_connectors(self, enabled_only: bool = False) -> list[dict[str, Any]]:
        rows=[]
        state=self.store.load_state().get('connectors', {})
        for d in self.definitions.values():
            if enabled_only and not d.enabled:
                continue
            rows.append(asdict(d) | {'state': state.get(d.name, {})})
        return rows

    def set_enabled(self, name: str, enabled: bool) -> dict[str, Any]:
        if name not in self.definitions:
            raise KeyError(f'Unknown connector: {name}')
        d=self.definitions[name]
        self.definitions[name]=ConnectorDefinition(**(asdict(d) | {'enabled': enabled}))
        self.store.update_connector_state(name, {'enabled': enabled, 'updated_at': _now()})
        return asdict(self.definitions[name])

    def sync(self, name: str, limit: int = 10, force: bool = False) -> SyncResult:
        if name not in self.definitions:
            raise KeyError(f'Unknown connector: {name}')
        definition=self.definitions[name]
        if not definition.enabled and not force:
            result=SyncResult(name, 'skipped_disabled', 0, 0, None, None, [])
            self.store.append_run(asdict(result) | {'run_at': _now()})
            return result
        state=self.store.get_connector_state(name)
        before=state.get('cursor')
        errors=[]
        try:
            items, after = self.adapters[name].pull(before, limit)
            emitted=0
            for item in items:
                event_payload={'connector': name, 'item': item, 'cursor': after}
                if self.event_bus:
                    self.event_bus.publish(f'connector.{name}.item', f'connector:{name}', event_payload, definition.risk_level)
                    emitted += 1
                else:
                    self.store.enqueue({'target':'event_bus', 'topic':f'connector.{name}.item', 'payload':event_payload})
            self.store.update_connector_state(name, {'cursor': after, 'last_sync_at': _now(), 'failures': 0, 'last_count': len(items)})
            result=SyncResult(name, 'ok', len(items), emitted, before, after, [])
        except Exception as exc:
            failures=int(state.get('failures',0))+1
            self.store.update_connector_state(name, {'failures': failures, 'last_error': str(exc), 'last_failed_at': _now()})
            self.store.enqueue({'target':'connector.sync', 'connector':name, 'attempts':failures, 'not_before': (_now())})
            result=SyncResult(name, 'error', 0, 0, before, before, [str(exc)])
        self.store.append_run(asdict(result) | {'run_at': _now()})
        return result

    def sync_all(self, enabled_only: bool = True, limit: int = 10) -> list[dict[str, Any]]:
        out=[]
        for name,d in self.definitions.items():
            if enabled_only and not d.enabled:
                continue
            out.append(asdict(self.sync(name, limit=limit)))
        return out

    def drain_queue(self, max_items: int = 50) -> dict[str, Any]:
        items=self.store.queue_items(10000)
        remaining=[]; processed=[]; failed=[]
        now=time.time()
        for item in items[:max_items]:
            attempts=int(item.get('attempts',0))
            if attempts and not self.retry.can_retry(attempts):
                failed.append(item); continue
            try:
                if item.get('target') == 'event_bus' and self.event_bus:
                    self.event_bus.publish(item['topic'], 'offline_queue', item.get('payload',{}), item.get('risk',1))
                    processed.append(item)
                elif item.get('target') == 'connector.sync':
                    self.sync(item['connector'], force=True)
                    processed.append(item)
                else:
                    item['attempts']=attempts+1
                    remaining.append(item)
            except Exception as exc:
                item['attempts']=attempts+1
                item['last_error']=str(exc)
                remaining.append(item)
        remaining.extend(items[max_items:])
        self.store.replace_queue(remaining)
        return {'processed': len(processed), 'failed': len(failed), 'remaining': len(remaining)}

    def receive_webhook(self, connector: str, payload: dict[str, Any]) -> dict[str, Any]:
        if connector not in self.definitions:
            raise KeyError(f'Unknown connector: {connector}')
        event=self.store.append_webhook({'connector': connector, 'data': payload})
        if self.event_bus:
            self.event_bus.publish(f'connector.{connector}.webhook', f'webhook:{connector}', {'webhook':event}, self.definitions[connector].risk_level)
        return event

    def webhook_inbox(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.store.webhooks(limit)

    def oauth_templates(self) -> list[dict[str, Any]]:
        return [
            asdict(OAuthConfig('google','GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET',['openid','email','https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/calendar.readonly','https://www.googleapis.com/auth/drive.readonly'], auth_url='https://accounts.google.com/o/oauth2/v2/auth', token_url='https://oauth2.googleapis.com/token')),
            asdict(OAuthConfig('microsoft','MS_CLIENT_ID','MS_CLIENT_SECRET',['offline_access','Mail.Read','Calendars.Read','Files.Read'], auth_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize', token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token')),
            asdict(OAuthConfig('github','GITHUB_CLIENT_ID','GITHUB_CLIENT_SECRET',['repo:read'], auth_url='https://github.com/login/oauth/authorize', token_url='https://github.com/login/oauth/access_token')),
        ]

    def sync_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.store.runs(limit)

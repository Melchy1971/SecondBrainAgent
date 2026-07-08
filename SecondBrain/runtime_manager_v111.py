from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Callable
import json
import os
import platform
import time
import traceback


@dataclass
class ServiceDefinition:
    name: str
    enabled: bool = True
    dependencies: list[str] = field(default_factory=list)
    autostart: bool = True
    description: str = ""


@dataclass
class ServiceRuntimeState:
    name: str
    status: str
    started_at: float | None = None
    stopped_at: float | None = None
    last_error: str = ""
    checks: int = 0


class JsonStateStore:
    """Small persistent state store for long-running desktop/runtime state.

    Design constraints:
    - stdlib only
    - human-readable files
    - atomic writes to reduce corruption risk
    - no background daemon assumption
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        safe = name.replace('/', '_').replace('\\', '_')
        return self.root / f"{safe}.json"

    def read(self, name: str, default: Any = None) -> Any:
        p = self.path(name)
        if not p.exists():
            return default
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            backup = p.with_suffix('.json.corrupt')
            p.replace(backup)
            return default

    def write(self, name: str, data: Any) -> Path:
        p = self.path(name)
        tmp = p.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        tmp.replace(p)
        return p

    def append_event(self, name: str, event: dict[str, Any], limit: int = 500) -> Path:
        events = self.read(name, []) or []
        events.append(event)
        if len(events) > limit:
            events = events[-limit:]
        return self.write(name, events)


class SessionManager:
    def __init__(self, store: JsonStateStore):
        self.store = store

    def current(self) -> dict[str, Any]:
        return self.store.read('session_current', {
            'active_project': None,
            'last_chat': None,
            'active_agents': [],
            'open_documents': [],
            'last_search': None,
            'window_state': {},
        })

    def update(self, **changes: Any) -> dict[str, Any]:
        session = self.current()
        session.update(changes)
        session['updated_at'] = time.time()
        self.store.write('session_current', session)
        return session


class ServiceRegistry:
    def __init__(self):
        self._services: dict[str, ServiceDefinition] = {}
        self._start_callbacks: dict[str, Callable[[], Any]] = {}
        self._stop_callbacks: dict[str, Callable[[], Any]] = {}
        self._health_callbacks: dict[str, Callable[[], dict[str, Any]]] = {}

    def register(self, service: ServiceDefinition, *, start: Callable[[], Any] | None = None, stop: Callable[[], Any] | None = None, health: Callable[[], dict[str, Any]] | None = None) -> None:
        self._services[service.name] = service
        if start:
            self._start_callbacks[service.name] = start
        if stop:
            self._stop_callbacks[service.name] = stop
        if health:
            self._health_callbacks[service.name] = health

    def get(self, name: str) -> ServiceDefinition:
        return self._services[name]

    def names(self) -> list[str]:
        return list(self._services.keys())

    def definitions(self) -> list[ServiceDefinition]:
        return list(self._services.values())

    def resolve_order(self, names: list[str] | None = None) -> list[str]:
        requested = names or [s.name for s in self.definitions() if s.enabled and s.autostart]
        seen: set[str] = set()
        visiting: set[str] = set()
        order: list[str] = []

        def visit(name: str) -> None:
            if name in seen:
                return
            if name in visiting:
                raise RuntimeError(f'Circular service dependency detected: {name}')
            if name not in self._services:
                raise KeyError(f'Unknown service dependency: {name}')
            visiting.add(name)
            svc = self._services[name]
            for dep in svc.dependencies:
                visit(dep)
            visiting.remove(name)
            seen.add(name)
            if name not in order:
                order.append(name)

        for n in requested:
            visit(n)
        return order

    def start_callback(self, name: str) -> Callable[[], Any] | None:
        return self._start_callbacks.get(name)

    def stop_callback(self, name: str) -> Callable[[], Any] | None:
        return self._stop_callbacks.get(name)

    def health_callback(self, name: str) -> Callable[[], dict[str, Any]] | None:
        return self._health_callbacks.get(name)


class RuntimeManager:
    def __init__(self, project_root: str | Path, launcher: Any):
        self.project_root = Path(project_root).resolve()
        self.launcher = launcher
        self.runtime_root = self.project_root / 'runtime'
        self.state_store = JsonStateStore(self.runtime_root / 'state')
        self.sessions = SessionManager(self.state_store)
        self.registry = ServiceRegistry()
        self._register_default_services()

    def _register_default_services(self) -> None:
        self.registry.register(ServiceDefinition('eventbus', True, [], True, 'JSONL event store'), health=lambda: {'events': self.launcher.event_store.summarize()})
        self.registry.register(ServiceDefinition('connectors', True, ['eventbus'], True, 'Connector sync runtime'), start=lambda: {'results': [r.__dict__ for r in self.launcher.sync_connectors()]})
        self.registry.register(ServiceDefinition('rag', True, ['eventbus'], True, 'Advanced RAG index'), health=lambda: {'indexed': self.launcher.rag.index_path.exists(), 'index_path': str(self.launcher.rag.index_path)})
        self.registry.register(ServiceDefinition('ai', True, ['eventbus'], True, 'AI runtime/router'), health=lambda: {'default_provider': self.launcher.config.default_provider})
        self.registry.register(ServiceDefinition('agent', True, ['eventbus', 'ai', 'rag'], True, 'Autonomous agent runtime'), health=lambda: self.launcher.autonomous_status())
        self.registry.register(ServiceDefinition('monitoring', True, ['eventbus'], True, 'Metrics and diagnostics'))
        self.registry.register(ServiceDefinition('desktop_commands', True, ['eventbus'], True, 'Quick capture and notifications'))
        self.registry.register(ServiceDefinition('gui', False, ['eventbus', 'monitoring'], False, 'Tk desktop dashboard'))

    def _load_service_states(self) -> dict[str, ServiceRuntimeState]:
        raw = self.state_store.read('services', {}) or {}
        states: dict[str, ServiceRuntimeState] = {}
        for name in self.registry.names():
            if name in raw:
                data = raw[name]
                states[name] = ServiceRuntimeState(**{k: data.get(k) for k in ServiceRuntimeState.__dataclass_fields__.keys()})
            else:
                states[name] = ServiceRuntimeState(name=name, status='stopped')
        return states

    def _save_service_states(self, states: dict[str, ServiceRuntimeState]) -> None:
        self.state_store.write('services', {k: asdict(v) for k, v in states.items()})

    def start(self, services: list[str] | None = None) -> dict[str, Any]:
        self.launcher.init_runtime()
        order = self.registry.resolve_order(services)
        states = self._load_service_states()
        events: list[dict[str, Any]] = []
        for name in order:
            svc = self.registry.get(name)
            if not svc.enabled:
                states[name].status = 'disabled'
                continue
            try:
                cb = self.registry.start_callback(name)
                result = cb() if cb else {'started': True}
                states[name] = ServiceRuntimeState(name=name, status='running', started_at=time.time(), checks=states[name].checks)
                events.append({'service': name, 'status': 'running', 'result': result})
            except Exception as exc:
                states[name] = ServiceRuntimeState(name=name, status='error', last_error=str(exc), checks=states[name].checks)
                events.append({'service': name, 'status': 'error', 'error': str(exc)})
        self._save_service_states(states)
        self.sessions.update(active_agents=['agent'] if 'agent' in order else [])
        self.state_store.append_event('activity', {'ts': time.time(), 'type': 'runtime.start', 'services': order})
        return {'status': 'started', 'order': order, 'services': events}

    def stop(self, services: list[str] | None = None) -> dict[str, Any]:
        states = self._load_service_states()
        names = services or list(reversed(self.registry.resolve_order()))
        events = []
        for name in names:
            try:
                cb = self.registry.stop_callback(name)
                result = cb() if cb else {'stopped': True}
                states[name] = ServiceRuntimeState(name=name, status='stopped', stopped_at=time.time(), checks=states[name].checks)
                events.append({'service': name, 'status': 'stopped', 'result': result})
            except Exception as exc:
                states[name].status = 'error'
                states[name].last_error = str(exc)
                events.append({'service': name, 'status': 'error', 'error': str(exc)})
        self._save_service_states(states)
        self.state_store.append_event('activity', {'ts': time.time(), 'type': 'runtime.stop', 'services': names})
        return {'status': 'stopped', 'services': events}

    def restart(self) -> dict[str, Any]:
        down = self.stop()
        up = self.start()
        return {'status': 'restarted', 'down': down, 'up': up}

    def status(self) -> dict[str, Any]:
        states = self._load_service_states()
        return {
            'runtime': self.state_store.read('runtime', {'boot_count': 0}),
            'session': self.sessions.current(),
            'services': {name: asdict(state) for name, state in states.items()},
            'activity_count': len(self.state_store.read('activity', []) or []),
        }

    def metrics(self) -> dict[str, Any]:
        states = self._load_service_states()
        event_summary = self.launcher.event_store.summarize()
        runtime_files = list((self.project_root / 'runtime').rglob('*')) if (self.project_root / 'runtime').exists() else []
        data_files = [p for p in runtime_files if p.is_file()]
        return {
            'platform': platform.platform(),
            'pid': os.getpid(),
            'services_total': len(states),
            'services_running': sum(1 for s in states.values() if s.status == 'running'),
            'services_error': sum(1 for s in states.values() if s.status == 'error'),
            'events': event_summary,
            'runtime_file_count': len(data_files),
            'runtime_bytes': sum(p.stat().st_size for p in data_files),
        }

    def diagnose(self) -> dict[str, Any]:
        states = self._load_service_states()
        checks = []
        for name in self.registry.names():
            state = states[name]
            detail: dict[str, Any] = {}
            try:
                cb = self.registry.health_callback(name)
                detail = cb() if cb else {'ok': True}
                state.checks += 1
                if state.status == 'error':
                    status = 'error'
                elif state.status in {'running', 'stopped'}:
                    status = 'ok'
                else:
                    status = state.status
            except Exception as exc:
                status = 'error'
                detail = {'error': str(exc), 'trace': traceback.format_exc(limit=3)}
                state.last_error = str(exc)
                state.status = 'error'
            checks.append({'service': name, 'status': status, 'detail': detail})
        self._save_service_states(states)
        return {'status': 'ok' if all(c['status'] != 'error' for c in checks) else 'error', 'checks': checks, 'metrics': self.metrics()}

    def recover(self) -> dict[str, Any]:
        # Safe recovery: archive corrupt state files, recreate required directories, do not delete data.
        for p in [self.runtime_root, self.runtime_root / 'state', self.runtime_root / 'sessions', self.project_root / 'events']:
            p.mkdir(parents=True, exist_ok=True)
        status = self.status()
        self.state_store.append_event('activity', {'ts': time.time(), 'type': 'runtime.recover', 'status_before': status})
        return {'status': 'recovered', 'state': self.status()}

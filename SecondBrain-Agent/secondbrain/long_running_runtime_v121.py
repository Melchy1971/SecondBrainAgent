from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import time
import uuid

@dataclass
class RuntimeService:
    name: str
    status: str = 'stopped'
    heartbeat_at: float = 0.0
    restarts: int = 0
    dependencies: list[str] | None = None

class LongRunningRuntime:
    def __init__(self, runtime_dir: str | Path, event_bus: Any, tool_registry: Any):
        self.root = Path(runtime_dir) / 'long_runtime_v121'
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_file = self.root / 'runtime_state.json'
        self.runs_file = self.root / 'runtime_runs.jsonl'
        self.event_bus = event_bus
        self.tool_registry = tool_registry
        self.services: dict[str, RuntimeService] = {}
        self._load()
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        for name, deps in {
            'event_bus': [],
            'tool_registry': ['event_bus'],
            'scheduler': ['event_bus','tool_registry'],
            'agent_runtime': ['event_bus','tool_registry'],
            'api_bridge': ['event_bus','tool_registry'],
        }.items():
            self.services.setdefault(name, RuntimeService(name=name, dependencies=deps))
        self._save()

    def _load(self) -> None:
        if not self.state_file.exists():
            return
        data=json.loads(self.state_file.read_text(encoding='utf-8'))
        self.services={k:RuntimeService(**v) for k,v in data.get('services',{}).items()}

    def _save(self) -> None:
        data={'services': {k: asdict(v) for k,v in self.services.items()}, 'updated_at': time.time()}
        self.state_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

    def _append_run(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        row={'run_id': f'rt_{uuid.uuid4().hex[:10]}', 'action': action, 'payload': payload, 'created_at': time.time()}
        with self.runs_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n')
        return row

    def start(self) -> dict[str, Any]:
        order=self.start_order()
        for name in order:
            self.services[name].status='running'
            self.services[name].heartbeat_at=time.time()
            self.event_bus.publish('runtime.service_started','long_runtime_v121',{'service': name},1)
        self._save()
        return {'status':'running', 'started': order, 'services': self.status()['services']}

    def stop(self) -> dict[str, Any]:
        for name in reversed(self.start_order()):
            self.services[name].status='stopped'
            self.event_bus.publish('runtime.service_stopped','long_runtime_v121',{'service': name},1)
        self._save()
        return {'status':'stopped', 'services': self.status()['services']}

    def tick(self) -> dict[str, Any]:
        now=time.time()
        for service in self.services.values():
            if service.status == 'running':
                service.heartbeat_at=now
        self.event_bus.publish('runtime.tick','long_runtime_v121',{'running': self.running_services()},1)
        self._save()
        return {'status':'tick', 'running': self.running_services(), 'heartbeat_at': now}

    def recover(self) -> dict[str, Any]:
        recovered=[]
        now=time.time()
        for service in self.services.values():
            if service.status == 'running' and service.heartbeat_at and now - service.heartbeat_at > 300:
                service.restarts += 1
                service.heartbeat_at = now
                recovered.append(service.name)
        self.event_bus.publish('runtime.recovered','long_runtime_v121',{'recovered': recovered},2)
        self._save()
        return {'recovered': recovered, 'services': self.status()['services']}

    def running_services(self) -> list[str]:
        return sorted([s.name for s in self.services.values() if s.status == 'running'])

    def start_order(self) -> list[str]:
        order=[]
        temp=set()
        perm=set()
        def visit(name: str):
            if name in perm: return
            if name in temp: raise ValueError(f'Cyclic dependency at {name}')
            temp.add(name)
            for dep in self.services[name].dependencies or []:
                if dep in self.services:
                    visit(dep)
            temp.remove(name); perm.add(name); order.append(name)
        for name in sorted(self.services):
            visit(name)
        return order

    def run_tool(self, tool: str, payload: dict[str, Any] | None = None, scopes: list[str] | None = None, approved: bool = False) -> dict[str, Any]:
        result=self.tool_registry.execute(tool, payload or {}, scopes or [], approved)
        run=self._append_run('tool.execute', {'tool': tool, 'status': result['status']})
        self.event_bus.publish('runtime.tool_executed','long_runtime_v121',{'tool': tool, 'run_id': run['run_id']}, result.get('risk_level',1))
        return result | {'run_id': run['run_id']}

    def runs(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.runs_file.exists(): return []
        rows=[json.loads(x) for x in self.runs_file.read_text(encoding='utf-8').splitlines() if x.strip()]
        return rows[-limit:]

    def status(self) -> dict[str, Any]:
        return {
            'component': 'long_running_runtime_v121',
            'healthy': True,
            'services': [asdict(s) for s in sorted(self.services.values(), key=lambda x: x.name)],
            'running': self.running_services(),
            'start_order': self.start_order(),
        }

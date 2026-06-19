from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import json
import uuid


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
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    tmp.replace(path)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + '\n')


@dataclass
class Capability:
    key: str
    title: str
    version: str
    domain: str
    launcher_command: str
    risk_level: int = 1
    status: str = 'available'
    description: str = ''


class CapabilityRegistry:
    def __init__(self, runtime_dir: str | Path):
        self.runtime_dir = Path(runtime_dir)
        self.path = self.runtime_dir / 'os' / 'capabilities.json'

    def defaults(self) -> list[Capability]:
        return [
            Capability('runtime', 'Persistent Runtime', '11.1', 'core', 'status', 1, description='Service lifecycle, sessions, diagnostics'),
            Capability('rag', 'Advanced RAG', '10.9', 'knowledge', 'rag-answer', 1, description='Ingestion, hybrid search, citations'),
            Capability('agent', 'Autonomous Agent Runtime', '11.0', 'agent', 'agent-run', 3, description='Observe, plan, execute, verify, learn'),
            Capability('workflow', 'Workflow Engine', '11.2', 'automation', 'workflow-run', 2, description='Dependency-aware workflow execution'),
            Capability('digital_twin', 'Digital Twin', '11.3', 'planning', 'twin-status', 1, description='Goals, projects, capacity, scenarios'),
            Capability('decision', 'Decision Engine', '11.3', 'planning', 'decision-evaluate', 1, description='Option scoring and decision history'),
            Capability('voice', 'Voice Assistant 2.0', '11.4', 'interface', 'voice-handle', 2, description='Voice sessions and command routing'),
            Capability('mobile', 'Mobile Bridge', '11.5', 'interface', 'mobile-status', 2, description='Device registry, push, capture, approval inbox'),
            Capability('api', 'API Bridge', '11.6', 'integration', 'api-dispatch', 3, description='Tokened local API bridge'),
            Capability('automation', 'Automation Scheduler', '11.7', 'automation', 'automation-run-due', 2, description='One-time and interval jobs'),
            Capability('improvement', 'Self Improvement', '11.8', 'operations', 'improve-analyze', 1, description='Feedback, backlog, regression analysis'),
            Capability('operations', 'Operations & Release', '11.9', 'operations', 'ops-release-gate', 2, description='Backups, release gates, migrations'),
            Capability('os', 'Personal AGI OS Orchestrator', '12.0', 'core', 'os-run', 2, description='Capability registry and end-to-end orchestration'),
        ]

    def ensure(self) -> list[dict[str, Any]]:
        rows = _read_json(self.path, None)
        if rows is None:
            rows = [asdict(x) for x in self.defaults()]
            _write_json(self.path, rows)
        return rows

    def list(self, domain: str | None = None) -> list[dict[str, Any]]:
        rows = self.ensure()
        if domain:
            rows = [r for r in rows if r.get('domain') == domain]
        return rows

    def get(self, key: str) -> dict[str, Any]:
        for row in self.ensure():
            if row.get('key') == key:
                return row
        raise KeyError(f'Unknown capability: {key}')

    def set_status(self, key: str, status: str) -> dict[str, Any]:
        rows = self.ensure()
        updated = None
        for row in rows:
            if row.get('key') == key:
                row['status'] = status
                row['updated_at'] = _now()
                updated = row
                break
        if updated is None:
            raise KeyError(f'Unknown capability: {key}')
        _write_json(self.path, rows)
        return updated

    def summary(self) -> dict[str, Any]:
        rows = self.ensure()
        by_status: dict[str, int] = {}
        by_domain: dict[str, int] = {}
        for row in rows:
            by_status[row.get('status', 'unknown')] = by_status.get(row.get('status', 'unknown'), 0) + 1
            by_domain[row.get('domain', 'unknown')] = by_domain.get(row.get('domain', 'unknown'), 0) + 1
        return {'total': len(rows), 'by_status': by_status, 'by_domain': by_domain, 'capabilities': rows}


class OSRunStore:
    def __init__(self, runtime_dir: str | Path):
        self.runtime_dir = Path(runtime_dir)
        self.path = self.runtime_dir / 'os' / 'runs.jsonl'

    def append(self, row: dict[str, Any]) -> dict[str, Any]:
        _append_jsonl(self.path, row)
        return row

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding='utf-8').splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        return rows[-limit:]


class PersonalOSOrchestrator:
    def __init__(self, runtime_dir: str | Path, dispatcher: Callable[[str, dict[str, Any]], Any] | None = None):
        self.runtime_dir = Path(runtime_dir)
        self.capabilities = CapabilityRegistry(runtime_dir)
        self.runs = OSRunStore(runtime_dir)
        self.dispatcher = dispatcher
        self.manifest_path = self.runtime_dir / 'os' / 'manifest.json'

    def manifest(self) -> dict[str, Any]:
        capabilities = self.capabilities.summary()
        manifest = {
            'product': 'SecondBrain OS',
            'version': '12.0',
            'generated_at': _now(),
            'architecture': [
                'Connector Layer', 'Event Bus', 'Memory Layer', 'Knowledge Graph', 'RAG Engine',
                'AI Runtime', 'Agent Runtime', 'Workflow Engine', 'Digital Twin', 'Voice Layer',
                'Mobile Bridge', 'API Bridge', 'Automation Scheduler', 'Operations Layer', 'Self Improvement Engine'
            ],
            'capability_count': capabilities['total'],
            'capabilities': capabilities['capabilities'],
            'control_model': {
                'read_only': ['status', 'search', 'diagnose'],
                'approval_required': ['agent', 'api', 'workflow', 'automation', 'operations'],
                'audit_required': True,
            },
        }
        _write_json(self.manifest_path, manifest)
        return manifest

    def status(self) -> dict[str, Any]:
        caps = self.capabilities.summary()
        unavailable = [c for c in caps['capabilities'] if c.get('status') != 'available']
        return {
            'version': '12.0',
            'runtime_dir': str(self.runtime_dir),
            'manifest_path': str(self.manifest_path),
            'capabilities_total': caps['total'],
            'capabilities_available': caps['by_status'].get('available', 0),
            'capabilities_by_domain': caps['by_domain'],
            'unavailable': unavailable,
            'last_runs': self.runs.list(5),
            'status': 'READY' if not unavailable else 'DEGRADED',
        }

    def plan(self, objective: str) -> dict[str, Any]:
        text = objective.lower()
        steps: list[dict[str, Any]] = []
        if any(k in text for k in ['wissen', 'suche', 'recherche', 'zusammenfass', 'rag']):
            steps.append({'capability': 'rag', 'action': 'rag.answer', 'payload': {'question': objective}, 'risk_level': 1})
        if any(k in text for k in ['projekt', 'entscheidung', 'kapazität', 'ziel', 'planung']):
            steps.append({'capability': 'digital_twin', 'action': 'twin.status', 'payload': {}, 'risk_level': 1})
            steps.append({'capability': 'decision', 'action': 'decision.evaluate', 'payload': {'question': objective}, 'risk_level': 1})
        if any(k in text for k in ['workflow', 'prozess', 'ablauf', 'automation']):
            steps.append({'capability': 'workflow', 'action': 'workflow.status', 'payload': {}, 'risk_level': 1})
        if any(k in text for k in ['backup', 'release', 'health', 'migration']):
            steps.append({'capability': 'operations', 'action': 'ops.release_gate', 'payload': {}, 'risk_level': 2})
        if not steps:
            steps = [
                {'capability': 'runtime', 'action': 'status', 'payload': {}, 'risk_level': 1},
                {'capability': 'agent', 'action': 'agent.run', 'payload': {'objective': objective}, 'risk_level': 3},
            ]
        return {'objective': objective, 'steps': steps, 'step_count': len(steps), 'max_risk_level': max(s['risk_level'] for s in steps)}

    def run(self, objective: str, dry_run: bool = False) -> dict[str, Any]:
        run_id = 'osrun_' + uuid.uuid4().hex[:12]
        plan = self.plan(objective)
        row: dict[str, Any] = {'run_id': run_id, 'objective': objective, 'dry_run': dry_run, 'started_at': _now(), 'plan': plan, 'results': [], 'status': 'PLANNED' if dry_run else 'RUNNING'}
        if dry_run or not self.dispatcher:
            row['status'] = 'PLANNED'
            row['finished_at'] = _now()
            self.runs.append(row)
            return row
        for step in plan['steps']:
            try:
                result = self.dispatcher(step['action'], step.get('payload', {}))
                row['results'].append({'step': step, 'status': 'OK', 'result': result})
            except Exception as exc:
                row['results'].append({'step': step, 'status': 'ERROR', 'error': str(exc)})
                row['status'] = 'FAILED'
                break
        else:
            row['status'] = 'COMPLETED'
        row['finished_at'] = _now()
        self.runs.append(row)
        return row

    def readiness_gate(self) -> dict[str, Any]:
        status = self.status()
        checks: list[dict[str, Any]] = []
        def add(name: str, passed: bool, severity: str = 'fail', detail: str = '') -> None:
            checks.append({'name': name, 'passed': bool(passed), 'severity': severity, 'detail': detail})
        add('capability registry initialized', status['capabilities_total'] >= 12)
        add('all capabilities available', status['status'] == 'READY', 'warning')
        add('manifest writable', self._writable(self.manifest_path.parent))
        add('run store writable', self._writable(self.runtime_dir / 'os'))
        manifest = self.manifest()
        add('manifest includes architecture', len(manifest.get('architecture', [])) >= 10)
        failures = [c for c in checks if not c['passed'] and c['severity'] == 'fail']
        warnings = [c for c in checks if not c['passed'] and c['severity'] == 'warning']
        gate = 'PASS' if not failures and not warnings else ('CONDITIONAL_PASS' if not failures else 'FAIL')
        return {'version': '12.0', 'status': gate, 'failures': len(failures), 'warnings': len(warnings), 'checks': checks, 'generated_at': _now()}

    def _writable(self, path: Path) -> bool:
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / '.write_test'
            probe.write_text('ok', encoding='utf-8')
            probe.unlink(missing_ok=True)
            return True
        except Exception:
            return False

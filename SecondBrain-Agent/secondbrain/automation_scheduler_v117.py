
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
import json
import uuid


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _utc_now()).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


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


@dataclass
class ScheduleRule:
    kind: str = 'interval'              # interval | once
    every_minutes: int | None = None
    run_at: str | None = None
    max_runs: int | None = None


@dataclass
class AutomationTask:
    task_id: str
    name: str
    target: str                         # api.dispatch | agent.run | workflow.run | rag.answer | capture | notify
    payload: dict[str, Any]
    rule: dict[str, Any]
    enabled: bool = True
    created_at: str = ''
    updated_at: str = ''
    next_run_at: str | None = None
    last_run_at: str | None = None
    run_count: int = 0
    status: str = 'scheduled'           # scheduled | disabled | completed | blocked | failed


@dataclass
class AutomationRun:
    run_id: str
    task_id: str
    started_at: str
    finished_at: str | None
    ok: bool
    result: Any = None
    error: str | None = None


class AutomationStore:
    def __init__(self, runtime_dir: str | Path):
        self.base = Path(runtime_dir) / 'automation'
        self.tasks_path = self.base / 'tasks.json'
        self.runs_path = self.base / 'runs.jsonl'
        self.base.mkdir(parents=True, exist_ok=True)

    def list_tasks(self, include_disabled: bool = True) -> list[dict[str, Any]]:
        rows = _read_json(self.tasks_path, [])
        if not include_disabled:
            rows = [r for r in rows if r.get('enabled')]
        return rows

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        for row in self.list_tasks(True):
            if row.get('task_id') == task_id:
                return row
        return None

    def save_tasks(self, rows: list[dict[str, Any]]) -> None:
        _write_json(self.tasks_path, rows)

    def upsert_task(self, task: dict[str, Any]) -> dict[str, Any]:
        rows = self.list_tasks(True)
        replaced = False
        for i, row in enumerate(rows):
            if row.get('task_id') == task.get('task_id'):
                rows[i] = task
                replaced = True
                break
        if not replaced:
            rows.append(task)
        self.save_tasks(rows)
        return task

    def append_run(self, run: dict[str, Any]) -> None:
        self.runs_path.parent.mkdir(parents=True, exist_ok=True)
        with self.runs_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(run, ensure_ascii=False, default=str) + '\n')

    def list_runs(self, limit: int = 30, task_id: str | None = None) -> list[dict[str, Any]]:
        if not self.runs_path.exists():
            return []
        lines = self.runs_path.read_text(encoding='utf-8').splitlines()
        rows = [json.loads(x) for x in lines if x.strip()]
        if task_id:
            rows = [r for r in rows if r.get('task_id') == task_id]
        return rows[-limit:]


class AutomationScheduler:
    SAFE_TARGETS = {'api.dispatch','agent.run','workflow.run','rag.answer','capture','notify'}

    def __init__(self, runtime_dir: str | Path, launcher: Any):
        self.runtime_dir = Path(runtime_dir)
        self.launcher = launcher
        self.store = AutomationStore(runtime_dir)

    def _compute_next(self, task: dict[str, Any], from_dt: datetime | None = None) -> str | None:
        rule = task.get('rule', {})
        kind = rule.get('kind', 'interval')
        base = from_dt or _utc_now()
        if rule.get('max_runs') is not None and int(task.get('run_count', 0)) >= int(rule['max_runs']):
            return None
        if kind == 'once':
            if int(task.get('run_count', 0)) > 0:
                return None
            run_at = _parse_iso(rule.get('run_at')) or base
            return _iso(run_at)
        if kind == 'interval':
            minutes = max(1, int(rule.get('every_minutes') or 60))
            last = _parse_iso(task.get('last_run_at'))
            if not last and task.get('next_run_at'):
                existing = _parse_iso(task.get('next_run_at'))
                if existing and existing > base:
                    return _iso(existing)
            anchor = last or base
            return _iso(anchor + timedelta(minutes=minutes))
        raise ValueError(f'unsupported schedule kind: {kind}')

    def create_interval(self, name: str, target: str, payload: dict[str, Any], every_minutes: int = 60, max_runs: int | None = None) -> dict[str, Any]:
        if target not in self.SAFE_TARGETS:
            raise ValueError(f'unsupported target: {target}')
        now = _iso()
        task = asdict(AutomationTask(
            task_id='auto_' + uuid.uuid4().hex[:12],
            name=name,
            target=target,
            payload=payload,
            rule={'kind':'interval','every_minutes':max(1, int(every_minutes)), 'max_runs': max_runs},
            created_at=now,
            updated_at=now,
        ))
        task['next_run_at'] = self._compute_next(task, _utc_now())
        return self.store.upsert_task(task)

    def create_once(self, name: str, target: str, payload: dict[str, Any], run_at: str | None = None) -> dict[str, Any]:
        if target not in self.SAFE_TARGETS:
            raise ValueError(f'unsupported target: {target}')
        now = _iso()
        task = asdict(AutomationTask(
            task_id='auto_' + uuid.uuid4().hex[:12],
            name=name,
            target=target,
            payload=payload,
            rule={'kind':'once','run_at': run_at or now, 'max_runs': 1},
            created_at=now,
            updated_at=now,
        ))
        task['next_run_at'] = self._compute_next(task, _utc_now())
        return self.store.upsert_task(task)

    def set_enabled(self, task_id: str, enabled: bool) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        if not task:
            raise KeyError(f'task not found: {task_id}')
        task['enabled'] = enabled
        task['updated_at'] = _iso()
        task['status'] = 'scheduled' if enabled else 'disabled'
        if enabled and not task.get('next_run_at'):
            task['next_run_at'] = self._compute_next(task, _utc_now())
        return self.store.upsert_task(task)

    def due_tasks(self, now: datetime | None = None) -> list[dict[str, Any]]:
        now = now or _utc_now()
        out = []
        for task in self.store.list_tasks(False):
            if task.get('status') in {'completed','blocked'}:
                continue
            due = _parse_iso(task.get('next_run_at'))
            if due is None or due <= now:
                out.append(task)
        return out

    def run_due(self, limit: int = 10) -> dict[str, Any]:
        due = self.due_tasks()[:max(1, int(limit))]
        runs = [self.run_task(t['task_id']) for t in due]
        return {'due': len(due), 'executed': len(runs), 'runs': runs}

    def run_task(self, task_id: str) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        if not task:
            raise KeyError(f'task not found: {task_id}')
        if not task.get('enabled'):
            raise PermissionError('task disabled')
        run = {'run_id':'run_' + uuid.uuid4().hex[:12], 'task_id':task_id, 'started_at':_iso(), 'finished_at':None, 'ok':False}
        try:
            result = self._execute(task['target'], task.get('payload', {}))
            run.update({'ok': True, 'result': result})
            task['last_run_at'] = _iso()
            task['run_count'] = int(task.get('run_count', 0)) + 1
            task['next_run_at'] = self._compute_next(task, _utc_now())
            if not task['next_run_at']:
                task['enabled'] = False
                task['status'] = 'completed'
            else:
                task['status'] = 'scheduled'
        except Exception as exc:
            run.update({'ok': False, 'error': str(exc)})
            task['last_run_at'] = _iso()
            task['status'] = 'failed'
            # Conservative retry in one hour.
            task['next_run_at'] = _iso(_utc_now() + timedelta(hours=1))
        finally:
            run['finished_at'] = _iso()
            task['updated_at'] = _iso()
            self.store.upsert_task(task)
            self.store.append_run(run)
        return run

    def _execute(self, target: str, payload: dict[str, Any]) -> Any:
        if target == 'api.dispatch':
            return self.launcher.api_dispatch(payload.get('method','GET'), payload.get('path','/status'), payload.get('payload',{}), internal=True)
        if target == 'agent.run':
            return self.launcher.agent_run(payload.get('objective',''), int(payload.get('max_steps', 5)))
        if target == 'workflow.run':
            return self.launcher.workflow_run(payload.get('name','automation_workflow'), payload.get('objective',''))
        if target == 'rag.answer':
            return self.launcher.rag_answer(payload.get('question',''))
        if target == 'capture':
            return self.launcher.capture(payload.get('text',''), payload.get('title','Automation Capture'))
        if target == 'notify':
            return self.launcher.notify(payload.get('message','Automation notification'), payload.get('severity','info'))
        raise ValueError(f'unsupported target: {target}')

    def status(self) -> dict[str, Any]:
        tasks = self.store.list_tasks(True)
        enabled = [t for t in tasks if t.get('enabled')]
        due = self.due_tasks()
        return {
            'version': '11.7',
            'tasks_total': len(tasks),
            'tasks_enabled': len(enabled),
            'tasks_due': len(due),
            'runs_total_visible': len(self.store.list_runs(1000)),
            'next_run_at': min([t.get('next_run_at') for t in enabled if t.get('next_run_at')] or [None]),
        }

    def list_tasks(self) -> list[dict[str, Any]]:
        return self.store.list_tasks(True)

    def list_runs(self, limit: int = 30, task_id: str | None = None) -> list[dict[str, Any]]:
        return self.store.list_runs(limit, task_id)

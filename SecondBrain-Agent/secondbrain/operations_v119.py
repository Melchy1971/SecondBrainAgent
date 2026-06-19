
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import os
import shutil
import sys
import zipfile


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


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class BackupManifest:
    backup_id: str
    created_at: str
    project_root: str
    runtime_dir: str
    include_runtime: bool
    file_count: int
    size_bytes: int
    sha256: str = ''
    version: str = '11.9'


class BackupManager:
    SKIP_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', 'node_modules'}
    SKIP_SUFFIXES = {'.pyc', '.pyo'}

    def __init__(self, project_root: str | Path, runtime_dir: str | Path):
        self.project_root = Path(project_root).resolve()
        self.runtime_dir = Path(runtime_dir).resolve()
        self.backup_dir = self.project_root / 'backups'
        self.index_path = self.backup_dir / 'backup_index.json'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _iter_files(self, include_runtime: bool) -> list[Path]:
        roots = [self.project_root]
        if include_runtime and self.runtime_dir.exists() and self.runtime_dir not in roots:
            roots.append(self.runtime_dir)
        files: list[Path] = []
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob('*'):
                if not path.is_file():
                    continue
                parts = set(path.parts)
                if parts & self.SKIP_DIRS:
                    continue
                if path.suffix in self.SKIP_SUFFIXES:
                    continue
                if self.backup_dir in path.parents:
                    continue
                files.append(path)
        return sorted(set(files))

    def create(self, include_runtime: bool = True, label: str | None = None) -> dict[str, Any]:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup_id = f"backup_{stamp}" + (f"_{label}" if label else '')
        target = self.backup_dir / f'{backup_id}.zip'
        files = self._iter_files(include_runtime)
        manifest = BackupManifest(
            backup_id=backup_id,
            created_at=_now(),
            project_root=str(self.project_root),
            runtime_dir=str(self.runtime_dir),
            include_runtime=include_runtime,
            file_count=len(files),
            size_bytes=0,
        )
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for path in files:
                if self.project_root in path.parents or path == self.project_root:
                    arc = Path('project') / path.relative_to(self.project_root)
                elif self.runtime_dir in path.parents or path == self.runtime_dir:
                    arc = Path('runtime') / path.relative_to(self.runtime_dir)
                else:
                    arc = Path('external') / path.name
                zf.write(path, arc.as_posix())
            zf.writestr('BACKUP_MANIFEST.json', json.dumps(asdict(manifest), indent=2, ensure_ascii=False))
        manifest.size_bytes = target.stat().st_size
        manifest.sha256 = _sha256(target)
        with zipfile.ZipFile(target, 'a', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('BACKUP_MANIFEST_FINAL.json', json.dumps(asdict(manifest), indent=2, ensure_ascii=False))
        row = asdict(manifest) | {'path': str(target)}
        index = _read_json(self.index_path, [])
        index.append(row)
        _write_json(self.index_path, index)
        return row

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = _read_json(self.index_path, [])
        return rows[-limit:]

    def verify(self, backup_id_or_path: str) -> dict[str, Any]:
        path = Path(backup_id_or_path)
        if not path.exists():
            matches = [Path(x['path']) for x in _read_json(self.index_path, []) if x.get('backup_id') == backup_id_or_path]
            if not matches:
                raise FileNotFoundError(f'Backup not found: {backup_id_or_path}')
            path = matches[-1]
        result = {'backup': str(path), 'exists': path.exists(), 'zip_ok': False, 'manifest_ok': False, 'file_count': 0, 'sha256': None}
        if not path.exists():
            return result
        result['sha256'] = _sha256(path)
        with zipfile.ZipFile(path, 'r') as zf:
            bad = zf.testzip()
            result['zip_ok'] = bad is None
            names = zf.namelist()
            result['manifest_ok'] = 'BACKUP_MANIFEST.json' in names or 'BACKUP_MANIFEST_FINAL.json' in names
            result['file_count'] = len([n for n in names if not n.endswith('/')])
        return result

    def restore_plan(self, backup_id_or_path: str, target_dir: str | Path | None = None) -> dict[str, Any]:
        path = Path(backup_id_or_path)
        if not path.exists():
            matches = [Path(x['path']) for x in _read_json(self.index_path, []) if x.get('backup_id') == backup_id_or_path]
            if matches:
                path = matches[-1]
        target = Path(target_dir) if target_dir else self.project_root.parent / f'restore_{path.stem}'
        verify = self.verify(str(path))
        return {'backup': str(path), 'target_dir': str(target), 'safe_restore_only': True, 'verify': verify, 'action': 'extract to separate folder; does not overwrite active project'}

    def restore(self, backup_id_or_path: str, target_dir: str | Path | None = None) -> dict[str, Any]:
        plan = self.restore_plan(backup_id_or_path, target_dir)
        if not plan['verify'].get('zip_ok'):
            raise ValueError('Backup verification failed')
        target = Path(plan['target_dir'])
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(plan['backup'], 'r') as zf:
            zf.extractall(target)
        return plan | {'restored': True}


class ReleaseGate:
    def __init__(self, project_root: str | Path, runtime_dir: str | Path):
        self.project_root = Path(project_root)
        self.runtime_dir = Path(runtime_dir)

    def run(self) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        def check(name: str, passed: bool, severity: str = 'fail', detail: str = '') -> None:
            checks.append({'name': name, 'passed': bool(passed), 'severity': severity, 'detail': detail})
        check('launcher.py exists', (self.project_root / 'launcher.py').exists())
        check('requirements.txt exists', (self.project_root / 'requirements.txt').exists(), 'warning')
        check('secondbrain package exists', (self.project_root / 'secondbrain').exists())
        check('runtime dir writable', self._writable(self.runtime_dir), detail=str(self.runtime_dir))
        check('config dir exists', (self.project_root / 'config').exists(), 'warning')
        check('tests dir exists', (self.project_root / 'tests').exists(), 'warning')
        check('backups dir writable', self._writable(self.project_root / 'backups'), 'warning')
        version_files = list(self.project_root.glob('CHANGELOG_v11.*.md'))
        check('v11 changelog present', bool(version_files), 'warning', f'{len(version_files)} changelog files')
        fails = [c for c in checks if not c['passed'] and c['severity'] == 'fail']
        warnings = [c for c in checks if not c['passed'] and c['severity'] == 'warning']
        status = 'PASS' if not fails and not warnings else ('CONDITIONAL_PASS' if not fails else 'FAIL')
        return {'version': '11.9', 'status': status, 'checks': checks, 'failures': len(fails), 'warnings': len(warnings), 'generated_at': _now()}

    def _writable(self, path: Path) -> bool:
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / '.write_test'
            probe.write_text('ok', encoding='utf-8')
            probe.unlink(missing_ok=True)
            return True
        except Exception:
            return False


class MigrationManager:
    def __init__(self, project_root: str | Path, runtime_dir: str | Path):
        self.project_root = Path(project_root)
        self.runtime_dir = Path(runtime_dir)
        self.state_path = self.runtime_dir / 'operations' / 'migrations.json'

    def status(self) -> dict[str, Any]:
        return _read_json(self.state_path, {'applied': []})

    def plan(self, target_version: str = '12.0') -> dict[str, Any]:
        applied = {x.get('id') for x in self.status().get('applied', [])}
        steps = [
            {'id': 'v119_backup_gate', 'title': 'Create verified backup before upgrade', 'required': True},
            {'id': 'v119_release_gate', 'title': 'Run release gate and resolve FAIL checks', 'required': True},
            {'id': 'v119_runtime_state', 'title': 'Persist operations migration marker', 'required': True},
            {'id': 'v120_readiness', 'title': 'Prepare v12.0 Personal OS integration checkpoint', 'required': False},
        ]
        for step in steps:
            step['applied'] = step['id'] in applied
        return {'current_version': '11.9', 'target_version': target_version, 'steps': steps, 'ready': all(s['applied'] or not s['required'] for s in steps)}

    def apply_marker(self, migration_id: str, note: str = '') -> dict[str, Any]:
        state = self.status()
        rows = state.setdefault('applied', [])
        if not any(x.get('id') == migration_id for x in rows):
            rows.append({'id': migration_id, 'note': note, 'applied_at': _now()})
            _write_json(self.state_path, state)
        return self.status()


class OperationsEngine:
    def __init__(self, project_root: str | Path, runtime_dir: str | Path):
        self.project_root = Path(project_root)
        self.runtime_dir = Path(runtime_dir)
        self.backups = BackupManager(project_root, runtime_dir)
        self.gate = ReleaseGate(project_root, runtime_dir)
        self.migrations = MigrationManager(project_root, runtime_dir)
        self.audit_path = self.runtime_dir / 'operations' / 'operations_audit.jsonl'

    def _audit(self, action: str, payload: dict[str, Any]) -> None:
        _append_jsonl(self.audit_path, {'action': action, 'payload': payload, 'at': _now()})

    def status(self) -> dict[str, Any]:
        gate = self.gate.run()
        backups = self.backups.list(5)
        return {'version': '11.9', 'project_root': str(self.project_root), 'runtime_dir': str(self.runtime_dir), 'release_gate': gate['status'], 'backup_count': len(self.backups.list(10000)), 'last_backup': backups[-1] if backups else None, 'migration': self.migrations.plan()}

    def create_backup(self, include_runtime: bool = True, label: str | None = None) -> dict[str, Any]:
        row = self.backups.create(include_runtime, label)
        self._audit('backup.create', {'backup_id': row['backup_id']})
        return row

    def release_gate(self) -> dict[str, Any]:
        row = self.gate.run()
        self._audit('release.gate', {'status': row['status'], 'failures': row['failures'], 'warnings': row['warnings']})
        return row

    def health_report(self) -> dict[str, Any]:
        report = {
            'generated_at': _now(),
            'python': sys.version.split()[0],
            'platform': sys.platform,
            'cwd': os.getcwd(),
            'operations': self.status(),
            'release_gate': self.release_gate(),
        }
        path = self.runtime_dir / 'operations' / 'health_report.json'
        _write_json(path, report)
        report['path'] = str(path)
        return report

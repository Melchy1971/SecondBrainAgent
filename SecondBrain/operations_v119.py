
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
import base64
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile
from contextlib import contextmanager
from datetime import timedelta
from urllib.parse import unquote, urlparse
from uuid import uuid4

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from secondbrain.vault.crypto import derive_key_from_passphrase


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
    tmp = path.with_name(f'.{path.name}.{uuid4().hex}.tmp')
    try:
        with tmp.open('w', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(data, indent=2, ensure_ascii=False, default=str))
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


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
    version: str = '30.96'
    schema: str = 'secondbrain.backup.manifest.v30_96'
    format_version: int = 1
    encryption: str = 'none'
    files: list[dict[str, Any]] = field(default_factory=list)
    components: dict[str, dict[str, Any]] = field(default_factory=dict)
    database: dict[str, Any] = field(default_factory=dict)


class BackupError(RuntimeError):
    """Controlled backup or restore failure."""


class BackupValidationError(BackupError):
    """Raised when backup authenticity or integrity cannot be proven."""


class BackupManager:
    """Versioned, validated backup service retaining the v11.9 public API."""

    SKIP_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', 'node_modules'}
    SKIP_SUFFIXES = {'.pyc', '.pyo'}
    MANIFEST_NAME = 'BACKUP_MANIFEST.json'
    FORMAT_VERSION = 1
    ENCRYPTED_MAGIC = b'SBBK3096'
    SALT_SIZE = 16
    NONCE_SIZE = 12
    TAG_SIZE = 16
    MAX_ARCHIVE_MEMBERS = 250_000
    MAX_RESTORE_BYTES = 2 * 1024 * 1024 * 1024 * 1024
    COMPONENT_PATHS = {
        'configuration': ('config', '.env'),
        'memory': ('memory', 'runtime/memory'),
        'secret_vault': ('runtime/vault', 'vault'),
        'approval_queue': ('runtime/native', 'runtime/agent/plans', 'runtime/review_approval'),
        'connector_checkpoints': ('runtime/connectors', 'runtime/connector_runtime'),
        'runtime': ('runtime',),
        'audit': ('audit', 'runtime/audit'),
        'logs': ('logs', 'runtime/logs'),
    }

    def __init__(
        self,
        project_root: str | Path,
        runtime_dir: str | Path,
        *,
        env: Mapping[str, str] | None = None,
        command_runner: Callable[..., Any] | None = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.runtime_dir = Path(runtime_dir).resolve()
        self.env = dict(os.environ if env is None else env)
        self.command_runner = command_runner
        self.backup_dir = self.project_root / 'backups'
        self.index_path = self.backup_dir / 'backup_index.json'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _iter_files(self, include_runtime: bool) -> list[Path]:
        return [entry[1] for entry in self._component_files(include_runtime, encrypted=True)]

    def _component_files(self, include_runtime: bool, *, encrypted: bool) -> list[tuple[str, Path, str]]:
        candidates: dict[Path, str] = {}
        for component, relative_paths in self.COMPONENT_PATHS.items():
            if component == 'runtime' and not include_runtime:
                continue
            for relative in relative_paths:
                base = self.project_root / relative
                if relative == 'runtime' and self.runtime_dir != self.project_root / 'runtime':
                    base = self.runtime_dir
                if base.is_file():
                    paths = [base]
                elif base.is_dir():
                    paths = [path for path in base.rglob('*') if path.is_file()]
                else:
                    continue
                for path in paths:
                    if self.backup_dir in path.parents:
                        continue
                    if set(path.parts) & self.SKIP_DIRS or path.suffix.lower() in self.SKIP_SUFFIXES:
                        continue
                    if not encrypted and (path.name == '.env' or component == 'secret_vault'):
                        continue
                    # Specific components win over the broad runtime root.
                    if path not in candidates or component != 'runtime':
                        candidates[path] = component

        rows: list[tuple[str, Path, str]] = []
        for path, component in candidates.items():
            if self.project_root in path.parents:
                archive_name = (Path('project') / path.relative_to(self.project_root)).as_posix()
            elif self.runtime_dir in path.parents:
                archive_name = (Path('runtime') / path.relative_to(self.runtime_dir)).as_posix()
            else:
                archive_name = (Path('external') / path.name).as_posix()
            rows.append((component, path, archive_name))
        return sorted(rows, key=lambda row: row[2])

    def _key(self, salt: bytes) -> bytes | None:
        encoded = self.env.get('SECONDBRAIN_BACKUP_KEY', '').strip()
        if encoded:
            try:
                key = base64.b64decode(encoded, validate=True)
            except Exception as exc:  # noqa: BLE001 - configuration boundary
                raise BackupError('invalid_backup_key_encoding') from exc
            if len(key) != 32:
                raise BackupError('backup_key_must_be_32_bytes')
            return key
        passphrase = self.env.get('SECONDBRAIN_BACKUP_PASSPHRASE', '')
        if passphrase:
            return derive_key_from_passphrase(passphrase, salt)
        return None

    @property
    def encryption_configured(self) -> bool:
        return bool(
            self.env.get('SECONDBRAIN_BACKUP_KEY', '').strip()
            or self.env.get('SECONDBRAIN_BACKUP_PASSPHRASE', '')
        )

    def create(
        self,
        include_runtime: bool = True,
        label: str | None = None,
        *,
        encrypt: bool | None = None,
        include_database: bool = True,
    ) -> dict[str, Any]:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        safe_label = re.sub(r'[^A-Za-z0-9_.-]+', '-', str(label or '')).strip('-')[:48]
        backup_id = f"backup_{stamp}_{uuid4().hex[:8]}" + (f"_{safe_label}" if safe_label else '')
        use_encryption = self.encryption_configured if encrypt is None else bool(encrypt)
        if use_encryption and not self.encryption_configured:
            raise BackupError('backup_encryption_key_missing')
        if self.env.get('SECONDBRAIN_ENV', '').lower() == 'production' and not use_encryption:
            raise BackupError('unencrypted_backup_blocked_in_production')

        suffix = '.sbbackup' if use_encryption else '.zip'
        target = self.backup_dir / f'{backup_id}{suffix}'
        temporary_target = self.backup_dir / f'.{backup_id}.{uuid4().hex}.tmp'
        salt = os.urandom(self.SALT_SIZE) if use_encryption else bytes(self.SALT_SIZE)
        key = self._key(salt) if use_encryption else None

        with tempfile.TemporaryDirectory(prefix='.backup-build-', dir=self.backup_dir) as directory:
            build_root = Path(directory)
            archive_path = build_root / 'payload.zip'
            database = self._postgres_dump(build_root) if include_database else {'status': 'excluded'}
            component_rows = self._component_files(include_runtime, encrypted=use_encryption)
            if database.get('path'):
                component_rows.append(('postgresql', Path(database['path']), 'database/postgresql.dump'))

            manifest_files: list[dict[str, Any]] = []
            components: dict[str, dict[str, Any]] = {}
            with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
                for component, path, archive_name in component_rows:
                    file_row = self._write_archive_file(archive, path, archive_name, component)
                    manifest_files.append(file_row)
                    stats = components.setdefault(component, {'files': 0, 'size_bytes': 0})
                    stats['files'] += 1
                    stats['size_bytes'] += file_row['size_bytes']
                if database.get('status') == 'created':
                    components['pgvector'] = {
                        'files': 1,
                        'size_bytes': int(database.get('size_bytes', 0)),
                        'included_in': 'postgresql',
                    }
                manifest = BackupManifest(
                    backup_id=backup_id,
                    created_at=_now(),
                    project_root=str(self.project_root),
                    runtime_dir=str(self.runtime_dir),
                    include_runtime=include_runtime,
                    file_count=len(manifest_files),
                    size_bytes=sum(item['size_bytes'] for item in manifest_files),
                    encryption='AES-256-GCM' if use_encryption else 'none',
                    files=manifest_files,
                    components=components,
                    database={key: value for key, value in database.items() if key != 'path'},
                )
                archive.writestr(self.MANIFEST_NAME, json.dumps(asdict(manifest), indent=2, ensure_ascii=False))

            if use_encryption:
                assert key is not None
                self._encrypt_file(archive_path, temporary_target, key, salt)
            else:
                shutil.copy2(archive_path, temporary_target)
            with temporary_target.open('r+b') as handle:
                os.fsync(handle.fileno())
            os.replace(temporary_target, target)

        outer_sha = _sha256(target)
        verification: dict[str, Any] = {}
        for attempt in range(3):
            verification = self.verify(str(target), expected_sha256=outer_sha)
            if verification.get('ok') or attempt == 2:
                break
            time.sleep(0.02)
        if not verification.get('ok'):
            target.unlink(missing_ok=True)
            raise BackupValidationError('backup_post_write_validation_failed')
        row = asdict(manifest) | {
            'path': str(target),
            'sha256': outer_sha,
            'status': 'verified',
            'encrypted': use_encryption,
        }
        index = _read_json(self.index_path, [])
        index.append(row)
        _write_json(self.index_path, index)
        return row

    create_backup = create

    @staticmethod
    def _write_archive_file(
        archive: zipfile.ZipFile,
        path: Path,
        archive_name: str,
        component: str,
    ) -> dict[str, Any]:
        digest = hashlib.sha256()
        size = 0
        with path.open('rb') as source, archive.open(archive_name, 'w', force_zip64=True) as destination:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
                size += len(chunk)
                destination.write(chunk)
        return {
            'path': archive_name,
            'component': component,
            'size_bytes': size,
            'sha256': digest.hexdigest(),
        }

    def _postgres_dump(self, build_root: Path) -> dict[str, Any]:
        dsn = (
            self.env.get('SECOND_BRAIN_DATABASE_URL')
            or self.env.get('DATABASE_URL')
            or ''
        ).strip()
        if not dsn:
            return {'status': 'not_configured', 'pgvector': 'not_configured'}
        parsed = urlparse(dsn)
        if parsed.scheme not in {'postgres', 'postgresql'}:
            raise BackupError('database_url_is_not_postgresql')
        executable = self.env.get('SECONDBRAIN_PG_DUMP') or shutil.which('pg_dump')
        if not executable and self.command_runner is None:
            raise BackupError('pg_dump_not_available')
        target = build_root / 'postgresql.dump'
        child_env = dict(os.environ)
        child_env.update({
            'PGHOST': parsed.hostname or '',
            'PGPORT': str(parsed.port or 5432),
            'PGUSER': unquote(parsed.username or ''),
            'PGPASSWORD': unquote(parsed.password or ''),
            'PGDATABASE': unquote((parsed.path or '/').lstrip('/')),
        })
        command = [str(executable or 'pg_dump'), '--format=custom', '--no-owner', '--no-acl', '--file', str(target)]
        runner = self.command_runner or subprocess.run
        result = runner(command, env=child_env, capture_output=True, text=True, timeout=3600)
        if int(getattr(result, 'returncode', 0)) != 0 or not target.exists():
            raise BackupError('postgres_backup_failed')
        return {
            'status': 'created',
            'format': 'pg_dump_custom',
            'pgvector': 'included',
            'size_bytes': target.stat().st_size,
            'path': str(target),
        }

    def _encrypt_file(self, source: Path, target: Path, key: bytes, salt: bytes) -> None:
        nonce = os.urandom(self.NONCE_SIZE)
        header = self.ENCRYPTED_MAGIC + salt + nonce
        encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
        encryptor.authenticate_additional_data(header)
        with source.open('rb') as source_handle, target.open('wb') as target_handle:
            target_handle.write(header)
            for chunk in iter(lambda: source_handle.read(1024 * 1024), b''):
                target_handle.write(encryptor.update(chunk))
            target_handle.write(encryptor.finalize())
            target_handle.write(encryptor.tag)
            target_handle.flush()
            os.fsync(target_handle.fileno())

    def _decrypt_file(self, source: Path, target: Path) -> None:
        minimum_size = len(self.ENCRYPTED_MAGIC) + self.SALT_SIZE + self.NONCE_SIZE + self.TAG_SIZE
        if source.stat().st_size < minimum_size:
            raise BackupValidationError('encrypted_backup_too_short')
        with source.open('rb') as source_handle:
            magic = source_handle.read(len(self.ENCRYPTED_MAGIC))
            if magic != self.ENCRYPTED_MAGIC:
                raise BackupValidationError('invalid_backup_magic')
            salt = source_handle.read(self.SALT_SIZE)
            nonce = source_handle.read(self.NONCE_SIZE)
            key = self._key(salt)
            if key is None:
                raise BackupValidationError('backup_decryption_key_missing')
            ciphertext_size = source.stat().st_size - minimum_size
            source_handle.seek(-self.TAG_SIZE, os.SEEK_END)
            tag = source_handle.read(self.TAG_SIZE)
            source_handle.seek(len(self.ENCRYPTED_MAGIC) + self.SALT_SIZE + self.NONCE_SIZE)
            decryptor = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
            decryptor.authenticate_additional_data(magic + salt + nonce)
            remaining = ciphertext_size
            try:
                with target.open('wb') as target_handle:
                    while remaining:
                        chunk = source_handle.read(min(1024 * 1024, remaining))
                        if not chunk:
                            raise BackupValidationError('encrypted_backup_truncated')
                        remaining -= len(chunk)
                        target_handle.write(decryptor.update(chunk))
                    target_handle.write(decryptor.finalize())
            except InvalidTag as exc:
                target.unlink(missing_ok=True)
                raise BackupValidationError('backup_authentication_failed') from exc

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = _read_json(self.index_path, [])
        return rows[-limit:]

    def _resolve_backup(self, backup_id_or_path: str) -> tuple[Path, dict[str, Any] | None]:
        path = Path(backup_id_or_path)
        rows = _read_json(self.index_path, [])
        match = next((row for row in reversed(rows) if row.get('backup_id') == backup_id_or_path), None)
        if not path.exists() and match:
            path = Path(match['path'])
        if not path.exists():
            raise FileNotFoundError('backup_not_found')
        return path.resolve(), match

    @staticmethod
    def _safe_member(name: str) -> bool:
        normalized = name.replace('\\', '/')
        parts = Path(normalized).parts
        return bool(normalized) and not normalized.startswith('/') and '..' not in parts and ':' not in parts[0]

    def verify(self, backup_id_or_path: str, *, expected_sha256: str | None = None) -> dict[str, Any]:
        path, index_row = self._resolve_backup(backup_id_or_path)
        outer_sha = _sha256(path)
        expected = expected_sha256 or str((index_row or {}).get('sha256') or '')
        encrypted = path.suffix.lower() == '.sbbackup'
        result: dict[str, Any] = {
            'backup': str(path),
            'exists': True,
            'encrypted': encrypted,
            'sha256': outer_sha,
            'hash_ok': not expected or outer_sha == expected,
            'zip_ok': False,
            'manifest_ok': False,
            'files_ok': False,
            'file_count': 0,
            'ok': False,
            'errors': [],
        }
        try:
            with tempfile.TemporaryDirectory(prefix='.backup-verify-', dir=self.backup_dir) as directory:
                payload = Path(directory) / 'payload.zip'
                if encrypted:
                    self._decrypt_file(path, payload)
                else:
                    shutil.copy2(path, payload)
                with zipfile.ZipFile(payload, 'r') as archive:
                    infos = archive.infolist()
                    if len(infos) > self.MAX_ARCHIVE_MEMBERS:
                        raise BackupValidationError('archive_member_limit_exceeded')
                    for info in infos:
                        if not self._safe_member(info.filename):
                            raise BackupValidationError('archive_path_traversal')
                        if stat.S_ISLNK(info.external_attr >> 16):
                            raise BackupValidationError('archive_symlink_not_allowed')
                    result['zip_ok'] = archive.testzip() is None
                    manifest_name = self.MANIFEST_NAME if self.MANIFEST_NAME in archive.namelist() else 'BACKUP_MANIFEST_FINAL.json'
                    if manifest_name not in archive.namelist():
                        raise BackupValidationError('backup_manifest_missing')
                    manifest = json.loads(archive.read(manifest_name).decode('utf-8'))
                    result['manifest_ok'] = manifest.get('schema') in {None, BackupManifest.__dataclass_fields__['schema'].default}
                    files = list(manifest.get('files') or [])
                    result['file_count'] = len(files) if files else len([info for info in infos if not info.is_dir()])
                    files_ok = True
                    names = set(archive.namelist())
                    for row in files:
                        name = str(row.get('path') or '')
                        if name not in names or not self._safe_member(name):
                            files_ok = False
                            break
                        digest = hashlib.sha256()
                        size = 0
                        with archive.open(name) as source:
                            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                                digest.update(chunk)
                                size += len(chunk)
                        if digest.hexdigest() != row.get('sha256') or size != int(row.get('size_bytes', -1)):
                            files_ok = False
                            break
                    result['files_ok'] = files_ok
                    result['manifest'] = {
                        'backup_id': manifest.get('backup_id'),
                        'schema': manifest.get('schema'),
                        'version': manifest.get('version'),
                        'encryption': manifest.get('encryption'),
                        'components': sorted((manifest.get('components') or {}).keys()),
                        'database': manifest.get('database') or {},
                    }
        except (BackupError, OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
            result['errors'].append(str(exc) if isinstance(exc, BackupError) else type(exc).__name__)
        if not result['hash_ok']:
            result['errors'].append('backup_hash_mismatch')
        result['ok'] = bool(
            result['hash_ok']
            and result['zip_ok']
            and result['manifest_ok']
            and result['files_ok']
            and not result['errors']
        )
        return result

    def restore_plan(self, backup_id_or_path: str, target_dir: str | Path | None = None) -> dict[str, Any]:
        path, _ = self._resolve_backup(backup_id_or_path)
        # Keep restore artifacts below the backup area.  Putting them next to
        # the live project can trigger file watchers/importers and makes a
        # validated restore look like active application data.
        target = Path(target_dir) if target_dir else self.backup_dir / 'restores' / f'restore_{path.stem}'
        verify = self.verify(str(path))
        target_exists = target.exists()
        return {
            'backup': str(path),
            'target_dir': str(target.resolve()),
            'safe_restore_only': True,
            'dry_run': True,
            'can_restore': bool(verify.get('ok')) and not target_exists,
            'target_exists': target_exists,
            'verify': verify,
            'steps': [
                'validate_ciphertext_and_manifest',
                'extract_to_temporary_staging',
                'validate_restored_file_hashes',
                'atomically_publish_separate_restore_folder',
            ],
            'database_restore': 'manual_explicit_step' if verify.get('manifest', {}).get('database', {}).get('status') == 'created' else 'not_included',
            'action': 'extract to separate folder; does not overwrite active project',
        }

    @contextmanager
    def _open_payload(self, backup: Path):
        with tempfile.TemporaryDirectory(prefix='.backup-restore-', dir=self.backup_dir) as directory:
            payload = Path(directory) / 'payload.zip'
            if backup.suffix.lower() == '.sbbackup':
                self._decrypt_file(backup, payload)
            else:
                shutil.copy2(backup, payload)
            yield payload

    @staticmethod
    def _hash_stream(source, destination=None) -> tuple[str, int]:
        digest = hashlib.sha256()
        size = 0
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
            size += len(chunk)
            if destination is not None:
                destination.write(chunk)
        return digest.hexdigest(), size

    def restore(self, backup_id_or_path: str, target_dir: str | Path | None = None) -> dict[str, Any]:
        plan = self.restore_plan(backup_id_or_path, target_dir)
        if not plan['verify'].get('ok'):
            raise BackupValidationError('backup_verification_failed')
        if not plan['can_restore']:
            raise BackupError('restore_target_must_not_exist')
        target = Path(plan['target_dir']).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = target.parent / f'.{target.name}.{uuid4().hex}.restore-tmp'
        staging.mkdir(parents=False, exist_ok=False)
        restored_files = 0
        restored_bytes = 0
        try:
            with self._open_payload(Path(plan['backup'])) as payload, zipfile.ZipFile(payload, 'r') as archive:
                manifest = json.loads(archive.read(self.MANIFEST_NAME).decode('utf-8'))
                expected = {str(row['path']): row for row in manifest.get('files') or []}
                for info in archive.infolist():
                    if info.is_dir() or info.filename == self.MANIFEST_NAME:
                        continue
                    if not self._safe_member(info.filename):
                        raise BackupValidationError('archive_path_traversal')
                    if stat.S_ISLNK(info.external_attr >> 16):
                        raise BackupValidationError('archive_symlink_not_allowed')
                    restored_bytes += info.file_size
                    if restored_bytes > self.MAX_RESTORE_BYTES:
                        raise BackupValidationError('restore_size_limit_exceeded')
                    destination = (staging / info.filename).resolve()
                    if not destination.is_relative_to(staging.resolve()):
                        raise BackupValidationError('archive_path_traversal')
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info) as source, destination.open('wb') as output:
                        digest, size = self._hash_stream(source, output)
                        output.flush()
                        os.fsync(output.fileno())
                    row = expected.get(info.filename)
                    if row and (digest != row.get('sha256') or size != int(row.get('size_bytes', -1))):
                        raise BackupValidationError('restored_file_hash_mismatch')
                    restored_files += 1
            # Windows rejects os.replace() for directories even when the
            # destination does not exist.  os.rename() keeps the publication
            # atomic on the same volume, which is guaranteed by staging under
            # the restore parent directory.
            os.rename(staging, target)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        validation = self.validate_restored_target(plan['backup'], target)
        if not validation['ok']:
            shutil.rmtree(target, ignore_errors=True)
            raise BackupValidationError('restore_validation_failed')
        return plan | {
            'dry_run': False,
            'restored': True,
            'restored_files': restored_files,
            'restored_bytes': restored_bytes,
            'restore_validation': validation,
        }

    def validate_restored_target(self, backup_id_or_path: str, target_dir: str | Path) -> dict[str, Any]:
        backup, _ = self._resolve_backup(backup_id_or_path)
        target = Path(target_dir).resolve()
        errors: list[str] = []
        checked = 0
        with self._open_payload(backup) as payload, zipfile.ZipFile(payload, 'r') as archive:
            manifest = json.loads(archive.read(self.MANIFEST_NAME).decode('utf-8'))
            for row in manifest.get('files') or []:
                destination = (target / str(row['path'])).resolve()
                if not destination.is_relative_to(target) or not destination.is_file():
                    errors.append('restored_file_missing')
                    continue
                if destination.stat().st_size != int(row.get('size_bytes', -1)) or _sha256(destination) != row.get('sha256'):
                    errors.append('restored_file_hash_mismatch')
                checked += 1
        return {'ok': not errors, 'checked_files': checked, 'errors': sorted(set(errors))}

    def health(self) -> dict[str, Any]:
        production = self.env.get('SECONDBRAIN_ENV', '').lower() == 'production'
        dsn_configured = bool(self.env.get('SECOND_BRAIN_DATABASE_URL') or self.env.get('DATABASE_URL'))
        checks = [
            {'name': 'backup_directory', 'passed': self.backup_dir.is_dir(), 'severity': 'blocker'},
            {
                'name': 'aes256_key',
                'passed': self.encryption_configured,
                'severity': 'blocker' if production else 'warning',
            },
            {
                'name': 'pg_dump',
                'passed': not dsn_configured or bool(self.env.get('SECONDBRAIN_PG_DUMP') or shutil.which('pg_dump') or self.command_runner),
                'severity': 'blocker' if dsn_configured else 'info',
            },
            {
                'name': 'pg_restore',
                'passed': not dsn_configured or bool(self.env.get('SECONDBRAIN_PG_RESTORE') or shutil.which('pg_restore') or self.command_runner),
                'severity': 'blocker' if dsn_configured else 'info',
            },
        ]
        rows = self.list(1)
        latest_validation = None
        if rows:
            latest_validation = self.verify(rows[-1]['backup_id'])
            checks.append({'name': 'latest_backup_valid', 'passed': latest_validation['ok'], 'severity': 'blocker'})
        else:
            checks.append({'name': 'latest_backup_valid', 'passed': False, 'severity': 'warning'})
        blockers = [check['name'] for check in checks if not check['passed'] and check['severity'] == 'blocker']
        warnings = [check['name'] for check in checks if not check['passed'] and check['severity'] == 'warning']
        return {
            'schema': 'secondbrain.backup.health.v30_96',
            'status': 'PASS' if not blockers and not warnings else ('CONDITIONAL_PASS' if not blockers else 'BLOCKED'),
            'checks': checks,
            'blockers': blockers,
            'warnings': warnings,
            'backup_count': len(self.list(100_000)),
            'latest_validation': latest_validation,
            'generated_at': _now(),
        }

    def write_report(self) -> dict[str, Any]:
        report = {
            'schema': 'secondbrain.backup.report.v30_96',
            'version': '30.96',
            'generated_at': _now(),
            'health': self.health(),
            'history': self.list(20),
            'components': sorted(self.COMPONENT_PATHS),
        }
        path = self.runtime_dir / 'reports' / 'backup_report.json'
        _write_json(path, report)
        return report | {'path': str(path)}


class BackupScheduler:
    INTERVALS = {
        'hourly': timedelta(hours=1),
        'daily': timedelta(days=1),
        'weekly': timedelta(days=7),
    }

    def __init__(self, backups: BackupManager, path: str | Path | None = None) -> None:
        self.backups = backups
        self.path = Path(path) if path else backups.runtime_dir / 'operations' / 'backup_schedule.json'

    def configure(self, *, interval: str = 'daily', enabled: bool = True) -> dict[str, Any]:
        if interval not in self.INTERVALS:
            raise ValueError('unsupported_backup_interval')
        state = self.status()
        state.update({'interval': interval, 'enabled': bool(enabled), 'updated_at': _now()})
        _write_json(self.path, state)
        return state

    def status(self) -> dict[str, Any]:
        return _read_json(self.path, {
            'schema': 'secondbrain.backup.schedule.v30_96',
            'enabled': False,
            'interval': 'daily',
            'last_success_at': '',
            'last_backup_id': '',
        })

    def run_due(self, *, now: datetime | None = None) -> dict[str, Any]:
        current = now or datetime.now(timezone.utc)
        state = self.status()
        if not state.get('enabled'):
            return {'status': 'disabled', 'created': False}
        last_raw = str(state.get('last_success_at') or '')
        last = datetime.fromisoformat(last_raw) if last_raw else None
        interval = self.INTERVALS[str(state.get('interval') or 'daily')]
        if last is not None and current - last < interval:
            return {'status': 'not_due', 'created': False, 'last_backup_id': state.get('last_backup_id', '')}
        backup = self.backups.create(label='scheduled', encrypt=True)
        state.update({'last_success_at': current.isoformat(), 'last_backup_id': backup['backup_id']})
        _write_json(self.path, state)
        return {'status': 'created', 'created': True, 'backup': backup}


class RestoreWizard:
    """Safe restore workflow; active data is never overwritten implicitly."""

    def __init__(self, backups: BackupManager) -> None:
        self.backups = backups
        self.state_path = backups.runtime_dir / 'operations' / 'restore_wizard.json'

    def status(self) -> dict[str, Any]:
        return _read_json(self.state_path, {
            'schema': 'secondbrain.restore.wizard.v30_96',
            'status': 'NOT_STARTED',
            'dry_run': True,
        })

    def dry_run(self, backup: str, target_dir: str | Path | None = None) -> dict[str, Any]:
        plan = self.backups.restore_plan(backup, target_dir)
        row = {
            'schema': 'secondbrain.restore.wizard.v30_96',
            'status': 'READY' if plan['can_restore'] else 'BLOCKED',
            'dry_run': True,
            'plan': plan,
            'updated_at': _now(),
        }
        _write_json(self.state_path, row)
        return row

    def restore(self, backup: str, target_dir: str | Path | None = None) -> dict[str, Any]:
        dry_run = self.dry_run(backup, target_dir)
        if dry_run['status'] != 'READY':
            raise BackupError('restore_dry_run_blocked')
        result = self.backups.restore(backup, target_dir)
        row = {
            'schema': 'secondbrain.restore.wizard.v30_96',
            'status': 'COMPLETED',
            'dry_run': False,
            'backup': result['backup'],
            'target_dir': result['target_dir'],
            'restore_validation': result['restore_validation'],
            'updated_at': _now(),
        }
        _write_json(self.state_path, row)
        return row

    def rollback(self) -> dict[str, Any]:
        state = _read_json(self.state_path, {})
        if state.get('status') != 'COMPLETED' or not state.get('target_dir'):
            return {'status': 'nothing_to_rollback', 'rolled_back': False}
        target = Path(state['target_dir']).resolve()
        if target == self.backups.project_root or not target.name.startswith('restore_'):
            raise BackupError('unsafe_restore_rollback_target')
        shutil.rmtree(target)
        row = state | {'status': 'ROLLED_BACK', 'rolled_back': True, 'updated_at': _now()}
        _write_json(self.state_path, row)
        return row


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
    def __init__(
        self,
        project_root: str | Path,
        runtime_dir: str | Path,
        *,
        env: Mapping[str, str] | None = None,
        command_runner: Callable[..., Any] | None = None,
    ):
        self.project_root = Path(project_root)
        self.runtime_dir = Path(runtime_dir)
        self.backups = BackupManager(project_root, runtime_dir, env=env, command_runner=command_runner)
        self.backup_scheduler = BackupScheduler(self.backups)
        self.restore_wizard = RestoreWizard(self.backups)
        self.gate = ReleaseGate(project_root, runtime_dir)
        self.migrations = MigrationManager(project_root, runtime_dir)
        self.audit_path = self.runtime_dir / 'operations' / 'operations_audit.jsonl'

    def _audit(self, action: str, payload: dict[str, Any]) -> None:
        _append_jsonl(self.audit_path, {'action': action, 'payload': payload, 'at': _now()})

    def status(self) -> dict[str, Any]:
        gate = self.gate.run()
        backups = self.backups.list(5)
        return {'version': '11.9', 'project_root': str(self.project_root), 'runtime_dir': str(self.runtime_dir), 'release_gate': gate['status'], 'backup_count': len(self.backups.list(10000)), 'last_backup': backups[-1] if backups else None, 'migration': self.migrations.plan()}

    def create_backup(
        self,
        include_runtime: bool = True,
        label: str | None = None,
        *,
        encrypt: bool | None = None,
        include_database: bool = True,
    ) -> dict[str, Any]:
        row = self.backups.create(
            include_runtime,
            label,
            encrypt=encrypt,
            include_database=include_database,
        )
        self._audit('backup.create', {'backup_id': row['backup_id']})
        return row

    def backup_health(self) -> dict[str, Any]:
        return self.backups.health()

    def backup_report(self) -> dict[str, Any]:
        row = self.backups.write_report()
        self._audit('backup.report', {'status': row['health']['status']})
        return row

    def scheduled_backup(self, *, now: datetime | None = None) -> dict[str, Any]:
        row = self.backup_scheduler.run_due(now=now)
        self._audit('backup.schedule', {'status': row['status']})
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

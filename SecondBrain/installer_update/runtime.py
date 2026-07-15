"""Signed, transactional application updater (v31.01).

Network and process lifecycle operations are injectable so the updater can be
embedded in the desktop application without granting documents control over
update endpoints.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from packaging.version import InvalidVersion, Version

CHANNELS = ("stable", "beta", "development")
SCHEMA_VERSION = 1
PRESERVED_PATHS = frozenset({"data", "runtime", "update_backups", ".env"})


class UpdateError(RuntimeError):
    """Controlled update failure with a stable machine-readable code."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(detail or code)
        self.code = code
        self.detail = detail or code


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())
        temporary = Path(stream.name)
    temporary.replace(path)


class Store:
    def __init__(self, root: str | Path = ".") -> None:
        self.base = Path(root) / "data" / "installer_update"
        self.base.mkdir(parents=True, exist_ok=True)

    def load(self, name: str, default: Any) -> Any:
        path = self.base / f"{name}.json"
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise UpdateError("state_corrupt", str(exc)) from exc

    def save(self, name: str, value: Any) -> None:
        _atomic_json(self.base / f"{name}.json", value)

    def append(self, name: str, item: Mapping[str, Any]) -> dict[str, Any]:
        items = self.load(name, [])
        items.append(dict(item))
        self.save(name, items)
        return dict(item)


@dataclass(frozen=True)
class ReleaseManifest:
    schema_version: int
    application_version: str
    build: str
    channel: str
    published_at: str
    minimum_supported_version: str
    package_url: str
    package_size: int
    sha256: str
    signature: str
    signing_key_id: str
    migrations: list[dict[str, Any]]
    release_notes: str
    rollout_percentage: int
    mandatory: bool

    @classmethod
    def parse(cls, value: Mapping[str, Any]) -> "ReleaseManifest":
        required = {field.name for field in fields(cls)}
        missing = sorted(required - value.keys())
        if missing:
            raise UpdateError("manifest_invalid", f"missing: {', '.join(missing)}")
        try:
            manifest = cls(**{name: value[name] for name in required})
        except (TypeError, ValueError) as exc:
            raise UpdateError("manifest_invalid", str(exc)) from exc
        if manifest.schema_version != SCHEMA_VERSION:
            raise UpdateError("schema_unsupported")
        if manifest.channel not in CHANNELS:
            raise UpdateError("channel_invalid")
        if not isinstance(manifest.package_size, int) or manifest.package_size <= 0:
            raise UpdateError("package_size_invalid")
        if not isinstance(manifest.rollout_percentage, int) or not 0 <= manifest.rollout_percentage <= 100:
            raise UpdateError("rollout_invalid")
        if len(manifest.sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in manifest.sha256):
            raise UpdateError("hash_invalid")
        _https_url(manifest.package_url)
        _version(manifest.application_version)
        _version(manifest.minimum_supported_version)
        return manifest

    def signed_payload(self) -> bytes:
        value = asdict(self)
        value.pop("signature")
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _version(value: str) -> Version:
    try:
        return Version(value)
    except InvalidVersion as exc:
        raise UpdateError("version_invalid", value) from exc


def _https_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise UpdateError("insecure_url", value)
    return value


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        _https_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _default_fetch(url: str, destination: Path | None = None) -> bytes | Path:
    _https_url(url)
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    request = urllib.request.Request(url, headers={"User-Agent": "SecondBrain-Updater/31.01"})
    try:
        with opener.open(request, timeout=30) as response:
            _https_url(response.geturl())
            if destination is None:
                return response.read()
            with destination.open("wb") as stream:
                shutil.copyfileobj(response, stream)
            return destination
    except (OSError, urllib.error.URLError) as exc:
        raise UpdateError("offline", str(exc)) from exc


class InstallerUpdateRuntime:
    def __init__(
        self,
        root: str | Path = ".",
        *,
        current_version: str = "15.2",
        manifest_url: str | None = None,
        trusted_keys: Mapping[str, bytes | str] | None = None,
        installation_id: str | None = None,
        fetcher: Callable[[str, Path | None], bytes | Path] = _default_fetch,
        stop_application: Callable[[], None] | None = None,
        start_application: Callable[[], None] | None = None,
        migration_runner: Callable[[Sequence[Mapping[str, Any]], Path], None] | None = None,
        smoke_test: Callable[[Path], bool] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.store = Store(self.root)
        self.backup_dir = self.root / "update_backups"
        self.download_dir = self.root / "runtime" / "updates"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.current_version = current_version
        self.manifest_url = _https_url(manifest_url) if manifest_url else None
        self.trusted_keys = dict(trusted_keys or {})
        self.installation_id = installation_id or self._installation_id()
        self.fetcher = fetcher
        self.stop_application = stop_application or (lambda: None)
        self.start_application = start_application or (lambda: None)
        self.migration_runner = migration_runner or (lambda migrations, root: None)
        self.smoke_test = smoke_test or (lambda root: True)

    def _installation_id(self) -> str:
        value = self.store.load("installation", {}).get("id")
        if not value:
            value = str(uuid4())
            self.store.save("installation", {"id": value, "created_at": _now()})
        return str(value)

    def _audit(self, action: str, status: str, **detail: Any) -> dict[str, Any]:
        return self.store.append("update_history", {"id": str(uuid4()), "at": _now(), "action": action, "status": status, **detail})

    def _verify_signature(self, manifest: ReleaseManifest) -> None:
        raw_key = self.trusted_keys.get(manifest.signing_key_id)
        if raw_key is None:
            raise UpdateError("signing_key_unknown")
        try:
            key_bytes = base64.b64decode(raw_key, validate=True) if isinstance(raw_key, str) else raw_key
            signature = base64.b64decode(manifest.signature, validate=True)
            Ed25519PublicKey.from_public_bytes(key_bytes).verify(signature, manifest.signed_payload())
        except (ValueError, InvalidSignature) as exc:
            raise UpdateError("signature_invalid") from exc

    def validate_update(self, value: Mapping[str, Any] | ReleaseManifest) -> ReleaseManifest:
        manifest = value if isinstance(value, ReleaseManifest) else ReleaseManifest.parse(value)
        self._verify_signature(manifest)
        if manifest.channel != self.channel():
            raise UpdateError("channel_mismatch")
        current, target = _version(self.current_version), _version(manifest.application_version)
        if target < current:
            raise UpdateError("downgrade_blocked")
        if current < _version(manifest.minimum_supported_version):
            raise UpdateError("compatibility_blocked")
        bucket = int(hashlib.sha256(self.installation_id.encode()).hexdigest()[:8], 16) % 100
        if not manifest.mandatory and bucket >= manifest.rollout_percentage:
            raise UpdateError("rollout_deferred")
        return manifest

    def check_for_updates(self, manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if self.paused():
            return {"ok": True, "status": "paused", "update_available": False}
        try:
            if manifest is None:
                if not self.manifest_url:
                    raise UpdateError("manifest_url_not_configured")
                payload = self.fetcher(self.manifest_url, None)
                if not isinstance(payload, bytes):
                    raise UpdateError("manifest_invalid")
                manifest = json.loads(payload)
            parsed = self.validate_update(manifest)
            available = _version(parsed.application_version) > _version(self.current_version)
            result = {"ok": True, "status": "available" if available else "current", "update_available": available, "manifest": asdict(parsed)}
            self._audit("check", result["status"], version=parsed.application_version)
            return result
        except (UpdateError, json.JSONDecodeError) as exc:
            error = exc if isinstance(exc, UpdateError) else UpdateError("manifest_invalid", str(exc))
            self._audit("check", "blocked", error=error.code, detail=error.detail)
            return {"ok": False, "status": "offline" if error.code == "offline" else "blocked", "error": error.code, "detail": error.detail, "update_available": False}

    def download_update(self, manifest: Mapping[str, Any] | ReleaseManifest) -> Path:
        parsed = self.validate_update(manifest)
        free = shutil.disk_usage(self.download_dir).free
        required = parsed.package_size * 2
        if free < required:
            raise UpdateError("insufficient_space", f"required={required}, available={free}")
        target = self.download_dir / f"{parsed.application_version}-{parsed.build}.zip"
        partial = target.with_suffix(".part")
        try:
            result = self.fetcher(parsed.package_url, partial)
            if result != partial or not partial.exists():
                raise UpdateError("download_failed")
            if partial.stat().st_size != parsed.package_size:
                raise UpdateError("package_size_mismatch")
            if self._sha256(partial) != parsed.sha256.lower():
                raise UpdateError("hash_mismatch")
            partial.replace(target)
            self._audit("download", "success", version=parsed.application_version, bytes=parsed.package_size)
            return target
        except Exception:
            partial.unlink(missing_ok=True)
            raise

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def _extract(self, package: Path, target: Path) -> None:
        try:
            with zipfile.ZipFile(package) as archive:
                for member in archive.infolist():
                    destination = (target / member.filename).resolve()
                    if target.resolve() not in destination.parents and destination != target.resolve():
                        raise UpdateError("package_path_invalid", member.filename)
                archive.extractall(target)
        except zipfile.BadZipFile as exc:
            raise UpdateError("package_invalid") from exc

    def _backup(self, manifest: ReleaseManifest) -> dict[str, Any]:
        backup_id = str(uuid4())
        path = self.backup_dir / backup_id
        files = path / "application"
        files.mkdir(parents=True)
        for source in self.root.iterdir():
            if source.name in PRESERVED_PATHS or source == path:
                continue
            destination = files / source.name
            shutil.copytree(source, destination) if source.is_dir() else shutil.copy2(source, destination)
        record = {"id": backup_id, "path": str(path), "from_version": self.current_version, "to_version": manifest.application_version, "package_sha256": manifest.sha256, "package_signature": manifest.signature, "signing_key_id": manifest.signing_key_id, "created_at": _now(), "status": "created"}
        _atomic_json(path / "backup.json", record)
        self.store.append("update_backups", record)
        return record

    def install_update(self, manifest: Mapping[str, Any] | ReleaseManifest, package: str | Path) -> dict[str, Any]:
        parsed = self.validate_update(manifest)
        package_path = Path(package)
        if not package_path.is_file() or self._sha256(package_path) != parsed.sha256.lower():
            raise UpdateError("hash_mismatch")
        backup = self._backup(parsed)
        staging = self.download_dir / f"staging-{uuid4()}"
        staging.mkdir(parents=True)
        stopped = False
        try:
            self._extract(package_path, staging)
            self.stop_application()
            stopped = True
            for source in staging.iterdir():
                if source.name in PRESERVED_PATHS:
                    continue
                destination = self.root / source.name
                if destination.is_dir():
                    shutil.rmtree(destination)
                elif destination.exists():
                    destination.unlink()
                shutil.move(str(source), str(destination))
            self.migration_runner(parsed.migrations, self.root)
            if not self.smoke_test(self.root):
                raise UpdateError("smoke_test_failed")
            self.current_version = parsed.application_version
            self.store.save("installed_version", {"version": self.current_version, "build": parsed.build, "installed_at": _now()})
            self.start_application()
            result = {"ok": True, "status": "installed", "version": self.current_version, "backup_id": backup["id"]}
            self._audit("install", "success", result=result)
            return result
        except Exception as exc:
            rollback = self.rollback_update(backup["id"], restart=stopped)
            code = exc.code if isinstance(exc, UpdateError) else "install_failed"
            self._audit("install", "rolled_back", error=code, detail=str(exc), rollback=rollback)
            return {"ok": False, "status": "rolled_back", "error": code, "detail": str(exc), "rollback": rollback}
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def rollback_update(self, backup_id: str, *, restart: bool = True) -> dict[str, Any]:
        record = next((row for row in self.store.load("update_backups", []) if row.get("id") == backup_id), None)
        if not record:
            raise UpdateError("backup_not_found")
        # A rollback is accepted only when bound to the previously verified signed release.
        if not record.get("package_signature") or record.get("signing_key_id") not in self.trusted_keys:
            raise UpdateError("rollback_unsigned")
        source_root = Path(record["path"]) / "application"
        if not source_root.is_dir():
            raise UpdateError("backup_invalid")
        for target in self.root.iterdir():
            if target.name in PRESERVED_PATHS:
                continue
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        for source in source_root.iterdir():
            destination = self.root / source.name
            shutil.copytree(source, destination) if source.is_dir() else shutil.copy2(source, destination)
        self.current_version = str(record["from_version"])
        if restart:
            self.start_application()
        result = {"ok": True, "status": "rolled_back", "version": self.current_version, "backup_id": backup_id, "user_data_preserved": True}
        self._audit("rollback", "success", result=result)
        return result

    def pause_updates(self, paused: bool = True) -> dict[str, Any]:
        self.store.save("settings", {**self.store.load("settings", {}), "paused": bool(paused), "updated_at": _now()})
        return {"ok": True, "paused": bool(paused)}

    def paused(self) -> bool:
        return bool(self.store.load("settings", {}).get("paused", False))

    def update_history(self) -> list[dict[str, Any]]:
        return self.store.load("update_history", [])

    def channel(self) -> str:
        return str(self.store.load("settings", {}).get("channel", "stable"))

    def switch_channel(self, channel: str) -> dict[str, Any]:
        if channel not in CHANNELS:
            raise UpdateError("channel_invalid")
        settings = {**self.store.load("settings", {}), "channel": channel, "updated_at": _now()}
        self.store.save("settings", settings)
        self._audit("switch_channel", "success", channel=channel)
        return {"ok": True, "channel": channel}

    # Compatibility with the previous installer API.
    def validate(self) -> dict[str, Any]:
        checks = [{"name": name, "exists": (self.root / name).exists(), "path": str(self.root / name)} for name in ("launcher.py", "secondbrain", "requirements.txt")]
        return {"ok": all(row["exists"] for row in checks), "checks": checks}

    def status(self) -> dict[str, Any]:
        return {"version": self.current_version, "channel": self.channel(), "paused": self.paused(), "config": self.validate(), "backups": len(self.store.load("update_backups", [])), "update_runs": len(self.update_history())}

    def update_check(self, current_version: str = "unknown") -> dict[str, Any]:
        self.current_version = current_version
        manifest = self.store.load("release_manifest", None)
        return self.check_for_updates(manifest) if manifest else {"current_version": current_version, "update_available": False, "status": "not_configured"}

    def manifest_create(self, version: str = "15.2") -> dict[str, Any]:
        """Create the legacy local installer descriptor (never a trusted update)."""
        value = {"name": "SecondBrain OS", "version": version, "channel": "local", "required_files": ["launcher.py", "secondbrain", "requirements.txt"], "rollback_supported": True, "created_at": _now()}
        self.store.save("legacy_release_manifest", value)
        return value

    def manifest(self) -> dict[str, Any]:
        return self.store.load("legacy_release_manifest", None) or self.manifest_create(self.current_version)

    def portable_plan(self, target_dir: str | Path) -> dict[str, Any]:
        return {"target_dir": str(Path(target_dir)), "portable": True, "steps": ["create_directory", "copy_project_files", "create_config", "run_validation"]}

    def portable_marker(self, target_dir: str | Path) -> dict[str, Any]:
        return self.store.append("installations", {"id": str(uuid4()), "target_dir": str(Path(target_dir)), "status": "planned", "created_at": _now()})

    def backup_create(self, from_version: str = "unknown", to_version: str = "15.2") -> dict[str, Any]:
        backup_id = str(uuid4())
        target = self.backup_dir / backup_id
        target.mkdir(parents=True, exist_ok=True)
        data = self.root / "data"
        if data.exists():
            shutil.copytree(data, target / "data", dirs_exist_ok=True)
        return self.store.append("legacy_update_backups", {"id": backup_id, "from_version": from_version, "to_version": to_version, "path": str(target), "status": "created", "created_at": _now()})

    def backups(self) -> list[dict[str, Any]]:
        return self.store.load("legacy_update_backups", [])

    def update_plan(self, current_version: str = "unknown") -> dict[str, Any]:
        validation = self.validate()
        return {"id": str(uuid4()), "current_version": current_version, "target_version": self.current_version, "can_update": validation["ok"], "steps": ["validate_config", "backup", "apply_files", "smoke_test", "mark_version"], "validation": validation, "created_at": _now()}

    def update_run(self, current_version: str = "unknown") -> dict[str, Any]:
        """Retain the old local dry-run API without bypassing signed installation."""
        plan = self.update_plan(current_version)
        if not plan["can_update"]:
            return {"ok": False, "error": "validation_failed", "plan": plan}
        backup = self.backup_create(current_version, plan["target_version"])
        result = {"ok": True, "plan": plan, "backup": backup, "status": "simulated_success", "applied_at": _now()}
        self.store.append("legacy_update_runs", result)
        return result

    def rollback_plan(self, backup_id: str) -> dict[str, Any]:
        backup = next((row for row in self.backups() if row["id"] == backup_id), None)
        if not backup:
            return {"ok": False, "error": "backup_not_found"}
        return {"ok": True, "backup": backup, "steps": ["stop_runtime", "restore_backup_data", "validate", "start_runtime"]}

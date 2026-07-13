from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from typing import Iterable, Sequence

DEFAULT_REQUIRED_PATHS = ("README.md", "secondbrain", "tests")
DEFAULT_RUNTIME_DIRS = ("release", "backups")


@dataclass(frozen=True)
class PreflightCheck:
    name: str
    status: str
    message: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class PreflightReport:
    root: str
    status: str
    checks: tuple[PreflightCheck, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict[str, object]:
        return {"root": self.root, "status": self.status, "checks": [check.to_dict() for check in self.checks]}


@dataclass(frozen=True)
class BackupItem:
    source: str
    target: str
    sha256: str | None = None
    size_bytes: int = 0
    required: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BackupPlan:
    backup_id: str
    root: str
    items: tuple[BackupItem, ...]
    status: str = "PENDING"
    issues: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MigrationStep:
    id: str
    description: str
    required: bool = True
    reversible: bool = True
    status: str = "PENDING"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MigrationPlan:
    from_version: str
    to_version: str
    steps: tuple[MigrationStep, ...]
    status: str = "PENDING"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RollbackPlan:
    backup_id: str
    steps: tuple[str, ...]
    status: str = "READY"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class UpgradePlan:
    from_version: str
    to_version: str
    root: str
    preflight: PreflightReport
    backup: BackupPlan
    migration: MigrationPlan
    rollback: RollbackPlan
    status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "root": self.root,
            "status": self.status,
            "preflight": self.preflight.to_dict(),
            "backup": self.backup.to_dict(),
            "migration": self.migration.to_dict(),
            "rollback": self.rollback.to_dict(),
        }


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_preflight(root: str | Path, *, required_paths: Sequence[str] = DEFAULT_REQUIRED_PATHS) -> PreflightReport:
    base = Path(root)
    checks: list[PreflightCheck] = []

    checks.append(PreflightCheck("root_exists", "PASS" if base.exists() else "FAIL", str(base)))
    checks.append(PreflightCheck("root_is_directory", "PASS" if base.is_dir() else "FAIL", str(base)))

    for rel in required_paths:
        path = base / rel
        checks.append(PreflightCheck(f"required:{rel}", "PASS" if path.exists() else "FAIL", rel))

    release_dir = base / "release"
    writable_target = release_dir if release_dir.exists() else base
    can_write = writable_target.exists() and writable_target.is_dir()
    checks.append(PreflightCheck("metadata_target_writable", "PASS" if can_write else "FAIL", str(writable_target)))

    status = "PASS" if all(check.status == "PASS" for check in checks) else "FAIL"
    return PreflightReport(root=str(base), status=status, checks=tuple(checks))


def create_backup_plan(root: str | Path, *, include_paths: Sequence[str] = ("README.md", "pyproject.toml", "pytest.ini"), backup_id: str | None = None) -> BackupPlan:
    base = Path(root)
    active_backup_id = backup_id or f"backup-{_utc_stamp()}"
    items: list[BackupItem] = []
    issues: list[str] = []

    for rel in include_paths:
        source = base / rel
        target = base / "backups" / active_backup_id / rel
        if source.exists() and source.is_file():
            items.append(BackupItem(source=rel, target=target.relative_to(base).as_posix(), sha256=_hash_file(source), size_bytes=source.stat().st_size))
        else:
            items.append(BackupItem(source=rel, target=target.relative_to(base).as_posix(), required=False))

    if not any(item.sha256 for item in items):
        issues.append("backup plan contains no existing files")

    return BackupPlan(backup_id=active_backup_id, root=str(base), items=tuple(items), status="READY" if not issues else "WARN", issues=tuple(issues))


def create_migration_plan(from_version: str, to_version: str, *, include_tests: bool = True) -> MigrationPlan:
    steps = [
        MigrationStep("preflight", "Validate project root, required paths and metadata target."),
        MigrationStep("backup", "Create rollback metadata for mutable release files."),
        MigrationStep("apply_delta", "Apply validated delta files to the project tree.", reversible=True),
        MigrationStep("write_metadata", "Write upgrade manifest and build metadata.", reversible=True),
    ]
    if include_tests:
        steps.append(MigrationStep("run_tests", "Run pytest after delta application.", required=True, reversible=False))
    steps.append(MigrationStep("finalize", "Mark upgrade complete only after all required steps pass."))
    return MigrationPlan(from_version=from_version, to_version=to_version, steps=tuple(steps), status="READY")


def create_rollback_plan(backup: BackupPlan) -> RollbackPlan:
    restore_steps = tuple(f"restore {item.source} from {item.target}" for item in backup.items if item.sha256)
    status = "READY" if restore_steps else "WARN"
    return RollbackPlan(backup_id=backup.backup_id, steps=restore_steps, status=status)


def build_upgrade_plan(root: str | Path, *, from_version: str, to_version: str) -> UpgradePlan:
    preflight = run_preflight(root)
    backup = create_backup_plan(root)
    migration = create_migration_plan(from_version, to_version)
    rollback = create_rollback_plan(backup)
    status = "READY" if preflight.passed and backup.status in {"READY", "WARN"} and migration.status == "READY" else "BLOCKED"
    return UpgradePlan(
        from_version=from_version,
        to_version=to_version,
        root=str(Path(root)),
        preflight=preflight,
        backup=backup,
        migration=migration,
        rollback=rollback,
        status=status,
    )


def write_upgrade_plan(root: str | Path, *, from_version: str, to_version: str, output_path: str | Path | None = None) -> UpgradePlan:
    base = Path(root)
    plan = build_upgrade_plan(base, from_version=from_version, to_version=to_version)
    target = Path(output_path) if output_path is not None else base / "release" / "upgrade_plan.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(plan.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return plan


def validate_upgrade_plan(plan: UpgradePlan) -> tuple[str, tuple[str, ...]]:
    issues: list[str] = []
    if not plan.preflight.passed:
        issues.append("preflight failed")
    if plan.from_version == plan.to_version:
        issues.append("from_version and to_version must differ")
    if not plan.migration.steps:
        issues.append("migration plan contains no steps")
    if plan.rollback.status not in {"READY", "WARN"}:
        issues.append("rollback plan invalid")
    required_steps = [step for step in plan.migration.steps if step.required]
    if not required_steps:
        issues.append("migration plan contains no required steps")
    return ("PASS" if not issues else "FAIL", tuple(issues))

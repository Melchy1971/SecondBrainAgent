"""Repository abstraction for review/approval persistence.

Decouples the review/approval services from direct JSONL storage. JSONL remains
a development fallback; PostgreSQL is the production-grade backend. The backend
is selected via ``REVIEW_APPROVAL_BACKEND`` (jsonl|postgres) and there is *no*
silent fallback to JSONL when PostgreSQL is explicitly configured.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable

__all__ = [
    "RepositoryConflict",
    "RepositoryUnavailable",
    "RepositoryHealth",
    "ReviewApprovalRepository",
    "resolve_backend",
    "create_review_approval_repository",
    "migrate_repository",
]


class RepositoryConflict(RuntimeError):
    """Raised on a compare-and-set version conflict (controlled conflict)."""


class RepositoryUnavailable(RuntimeError):
    """Raised when a configured backend cannot be constructed (no fallback)."""


@dataclass(frozen=True)
class RepositoryHealth:
    backend: str
    healthy: bool
    degraded: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "healthy": self.healthy,
            "degraded": self.degraded,
            "detail": self.detail,
        }


@runtime_checkable
class ReviewApprovalRepository(Protocol):
    backend: str

    def create_approval(self, **fields: Any) -> dict[str, Any]: ...
    def create_review(self, **fields: Any) -> dict[str, Any]: ...
    def get_item(self, item_id: str) -> dict[str, Any] | None: ...
    def list_items(
        self,
        *,
        item_type: str | None = None,
        status: str | None = None,
        workspace_id: str | None = None,
    ) -> list[dict[str, Any]]: ...
    def update_status(
        self,
        item_id: str,
        new_status: str,
        *,
        actor: str,
        expected_version: int | None = None,
        note: str = "",
        deferred_until: str = "",
    ) -> dict[str, Any] | None: ...
    def compare_and_set_status(
        self,
        item_id: str,
        expected_version: int,
        new_status: str,
        *,
        actor: str,
        note: str = "",
        deferred_until: str = "",
    ) -> dict[str, Any]: ...
    def append_audit_event(self, item_id: str, event: Mapping[str, Any]) -> dict[str, Any]: ...
    def list_audit_events(self, item_id: str) -> list[dict[str, Any]]: ...
    def acquire_execution_lease(
        self,
        item_id: str,
        *,
        executor_id: str,
        lease_seconds: int = 300,
        expected_version: int | None = None,
    ) -> dict[str, Any]: ...
    def release_execution_lease(
        self,
        item_id: str,
        *,
        execution_token: str,
        result_status: str = "completed",
        expected_version: int | None = None,
    ) -> dict[str, Any]: ...
    def health(self) -> RepositoryHealth: ...


_STRICT_ENV_KEYS = ("SECONDBRAIN_ENV", "SECONDBRAIN_PROFILE", "ENVIRONMENT")


def resolve_backend(env: Mapping[str, str] | None = None) -> str:
    environ = env if env is not None else os.environ
    backend = str(environ.get("REVIEW_APPROVAL_BACKEND") or "jsonl").strip().lower()
    if backend not in {"jsonl", "postgres"}:
        raise RepositoryUnavailable(f"unknown_review_approval_backend:{backend}")
    return backend


def is_production(env: Mapping[str, str] | None = None) -> bool:
    environ = env if env is not None else os.environ
    for key in _STRICT_ENV_KEYS:
        if str(environ.get(key) or "").strip().lower() in {"prod", "production", "strict"}:
            return True
    return False


def create_review_approval_repository(
    project_root: Any = ".",
    *,
    env: Mapping[str, str] | None = None,
    executor: Any | None = None,
):
    """Construct the configured repository. No silent fallback for postgres."""

    backend = resolve_backend(env)
    if backend == "postgres":
        if executor is None:
            raise RepositoryUnavailable(
                "postgres_backend_requires_executor: refusing to fall back to jsonl"
            )
        from secondbrain.repositories.postgres_review_approval_repository import (
            PostgresReviewApprovalRepository,
        )

        repo = PostgresReviewApprovalRepository(executor)
        repo.ensure_schema()
        return repo
    from secondbrain.repositories.jsonl_review_approval_repository import (
        JsonlReviewApprovalRepository,
    )

    return JsonlReviewApprovalRepository(project_root, production=is_production(env))


def migrate_repository(
    source: ReviewApprovalRepository,
    target: ReviewApprovalRepository,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Copy all items and their audit history from source into target.

    IDs and decision history are preserved; items already present in the target
    (by id) are skipped as duplicates. ``dry_run`` computes the report without
    writing anything.
    """

    imported: list[str] = []
    skipped: list[str] = []
    audit_events = 0
    for item in source.list_items():
        item_id = str(item.get("approval_id") or item.get("review_id") or item.get("id") or "")
        if not item_id:
            continue
        if target.get_item(item_id) is not None:
            skipped.append(item_id)
            continue
        events = source.list_audit_events(item_id)
        if not dry_run:
            target.import_item(item, events)
        imported.append(item_id)
        audit_events += len(events)
    return {
        "dry_run": dry_run,
        "source_backend": getattr(source, "backend", "unknown"),
        "target_backend": getattr(target, "backend", "unknown"),
        "imported": imported,
        "imported_count": len(imported),
        "skipped_duplicates": skipped,
        "skipped_count": len(skipped),
        "audit_events": audit_events,
    }

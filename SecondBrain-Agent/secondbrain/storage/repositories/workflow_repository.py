"""v30.1 - Workflow repository."""

from __future__ import annotations

from secondbrain.storage.repositories.base_repository import BaseRepository, RepositoryResult


class WorkflowRepository(BaseRepository):
    def create_minimal(self, workflow_id: str, status: str = "PENDING") -> RepositoryResult:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(
                text("INSERT INTO workflows (id, status) VALUES (:id, :status)"),
                {"id": workflow_id, "status": status},
            )
        return RepositoryResult(status="PASS", affected=1)

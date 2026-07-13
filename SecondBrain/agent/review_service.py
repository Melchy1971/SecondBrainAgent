from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from secondbrain.events.domain_events import ReviewCreated, ReviewResolved
from secondbrain.events.event_bus import EventBus
from secondbrain.native.approval import REVIEW_CATEGORIES, NativeApprovalQueue, ReviewQueue

from .approval_service import AgentApprovalService


class UnifiedReviewInbox:
    """Unified read and decision model over native review and approval queues."""

    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        approval_queue: NativeApprovalQueue | None = None,
        review_queue: ReviewQueue | None = None,
        approval_service: AgentApprovalService | None = None,
        event_bus: EventBus | None = None,
        memory_governance: Any | None = None,
        notifier: Any | None = None,
    ) -> None:
        root = Path(project_root or Path.cwd()).resolve()
        self.approvals = approval_queue or NativeApprovalQueue(root)
        self.reviews = review_queue or ReviewQueue(self.approvals.project_root)
        if self.approvals.project_root != self.reviews.project_root:
            raise ValueError("review_approval_root_mismatch")
        if approval_service is not None and approval_service.queue.path != self.approvals.path:
            raise ValueError("approval_service_queue_mismatch")
        if event_bus is not None and approval_service is not None and event_bus is not approval_service.event_bus:
            raise ValueError("review_approval_event_bus_mismatch")
        self.event_bus = event_bus or (approval_service.event_bus if approval_service is not None else EventBus())
        self.approval_service = approval_service or AgentApprovalService(queue=self.approvals, event_bus=self.event_bus)
        # Optional collaborator that commits/discards memory candidates when a
        # memory-governed review is decided. Duck-typed to avoid an import cycle
        # with secondbrain.agent.memory_service.
        self.memory_governance = memory_governance
        # Optional review-notification collaborator (decision events).
        self.notifier = notifier
        self._notification_service = None

    def create_review(
        self,
        *,
        category: str,
        title: str,
        description: str = "",
        source: str = "",
        target: str = "",
        approval_id: str = "",
        metadata: Mapping[str, Any] | None = None,
        workspace_id: str = "",
        actor: str = "system",
        correlation_id: str = "",
        causation_id: str = "",
    ) -> dict[str, Any]:
        review_metadata = dict(metadata or {})
        review = self.reviews.create(
            category=category,
            title=title,
            description=description,
            source=source,
            target=target,
            approval_id=approval_id,
            metadata=review_metadata,
        )
        review_id = str(review["review_id"])
        plan_id = str(review_metadata.get("plan_id") or "")
        step_id = str(review_metadata.get("step_id") or "")
        workspace = workspace_id or str(review_metadata.get("workspace_id") or "")
        self.event_bus.publish(
            ReviewCreated(
                workspace_id=workspace,
                actor=actor,
                correlation_id=correlation_id or plan_id or approval_id or review_id,
                causation_id=causation_id,
                item_id=review_id,
                plan_id=plan_id,
                step_id=step_id,
                category=str(review.get("category") or category),
                sanitized_metadata={
                    "approval_id": approval_id,
                    "source": source,
                    "target": target,
                    "title": title,
                    **review_metadata,
                },
            )
        )
        return review

    def create(self, **kwargs: Any) -> dict[str, Any]:
        return self.create_review(**kwargs)

    def list_all(self, *, category: str | None = None) -> list[dict[str, Any]]:
        self._validate_category(category)
        approvals = self.approvals.list()
        reviews = self.reviews.list()
        reviews_by_approval: dict[str, list[dict[str, Any]]] = {}
        for review in reviews:
            if review.get("approval_id"):
                reviews_by_approval.setdefault(str(review["approval_id"]), []).append(review)

        items = []
        linked_review_ids = set()
        for approval in approvals:
            linked = reviews_by_approval.get(str(approval.get("approval_id") or ""), [])
            review_id = str(approval.get("review_id") or "")
            review = next((row for row in linked if row.get("review_id") == review_id), None)
            if review is None and linked:
                review = linked[0]
            if review is not None:
                linked_review_ids.update(str(row.get("review_id") or "") for row in linked)
            items.append(self._approval_view(approval, review))
        for review in reviews:
            if str(review.get("review_id") or "") not in linked_review_ids:
                items.append(self._review_view(review))

        if category:
            items = [item for item in items if item["category"] == category]
        return sorted(items, key=self._sort_key)

    def list_pending(self, *, category: str | None = None) -> list[dict[str, Any]]:
        return [item for item in self.list_all(category=category) if item["status"] == "pending"]

    def list_deferred(self, *, category: str | None = None) -> list[dict[str, Any]]:
        return [item for item in self.list_all(category=category) if item["status"] == "deferred"]

    def list_completed(self, *, category: str | None = None) -> list[dict[str, Any]]:
        return [item for item in self.list_all(category=category) if item["status"] not in {"pending", "deferred"}]

    def get(self, item_id: str) -> dict[str, Any] | None:
        approval = self.approvals.get(item_id)
        if approval is not None:
            return self._approval_view(approval, self._review_for_approval(approval))
        review = self.reviews.get(item_id)
        if review is None:
            return None
        if review.get("approval_id"):
            approval = self.approvals.get(str(review["approval_id"]))
            if approval is not None:
                return self._approval_view(approval, review)
        return self._review_view(review)

    def approve(
        self,
        item_id: str,
        actor: str,
        note: str = "",
        *,
        correlation_id: str = "",
        causation_id: str = "",
    ) -> dict[str, Any]:
        return self._decide(
            item_id,
            "approved",
            actor=actor,
            note=note,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    def reject(
        self,
        item_id: str,
        actor: str,
        note: str = "",
        *,
        correlation_id: str = "",
        causation_id: str = "",
    ) -> dict[str, Any]:
        return self._decide(
            item_id,
            "rejected",
            actor=actor,
            note=note,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    def defer(
        self,
        item_id: str,
        actor: str,
        until: str = "",
        note: str = "",
        *,
        correlation_id: str = "",
        causation_id: str = "",
    ) -> dict[str, Any]:
        return self._decide(
            item_id,
            "deferred",
            actor=actor,
            until=until,
            note=note,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    def _decide(
        self,
        item_id: str,
        status: str,
        *,
        actor: str,
        until: str = "",
        note: str,
        correlation_id: str = "",
        causation_id: str = "",
    ) -> dict[str, Any]:
        approval, reviews = self._linked_records(item_id)
        if approval is None and not reviews:
            raise KeyError(f"inbox_item_not_found:{item_id}")
        if approval is not None:
            self._validate_transition("approval", str(approval.get("status") or "pending"), status)
        for review in reviews:
            self._validate_transition("review", str(review.get("status") or "pending"), status)

        correlation = self._correlation_id(approval, reviews, correlation_id)

        if approval is not None:
            method = {
                "approved": self.approval_service.approve,
                "rejected": self.approval_service.reject,
                "deferred": self.approval_service.defer,
            }[status]
            if status == "deferred":
                method(
                    str(approval["approval_id"]),
                    actor,
                    until=until,
                    note=note,
                    correlation_id=correlation,
                    causation_id=causation_id,
                )
            else:
                method(
                    str(approval["approval_id"]),
                    actor,
                    note,
                    correlation_id=correlation,
                    causation_id=causation_id,
                )
        for review in reviews:
            updated = self.reviews.transition(
                str(review["review_id"]),
                status,
                actor=actor,
                note=note,
                deferred_until=until,
            )
            if updated is None:
                raise RuntimeError(f"linked_review_missing:{review['review_id']}")
            metadata = updated.get("metadata") if isinstance(updated.get("metadata"), dict) else {}
            approval_workspace = str((approval or {}).get("workspace_id") or "")
            approval_plan = str((approval or {}).get("plan_id") or "")
            approval_step = str((approval or {}).get("step_id") or "")
            self.event_bus.publish(
                ReviewResolved(
                    workspace_id=str(metadata.get("workspace_id") or approval_workspace),
                    actor=actor,
                    correlation_id=correlation,
                    causation_id=causation_id,
                    item_id=str(updated.get("review_id") or ""),
                    plan_id=str(metadata.get("plan_id") or approval_plan),
                    step_id=str(metadata.get("step_id") or approval_step),
                    category=str(updated.get("category") or "risky_agent_action"),
                    sanitized_metadata={
                        "approval_id": str(updated.get("approval_id") or ""),
                        "status": status,
                        "decision_note": note,
                        "deferred_until": until,
                        "source": str(updated.get("source") or ""),
                    },
                )
            )
            self._apply_memory_governance(metadata, status, actor)
        canonical_id = str(approval["approval_id"]) if approval is not None else str(reviews[0]["review_id"])
        result = self.get(canonical_id)
        if result is None:
            raise RuntimeError(f"inbox_item_missing_after_decision:{canonical_id}")
        if result is not None:
            (self.notifier or self.notification_service()).record_decision(result, status)
        return result

    def notification_service(self):
        """Lazily create the persistent review-notification service."""

        if self._notification_service is None:
            from secondbrain.notifications.review_notifications import ReviewNotificationService

            state_path = self.approvals.project_root / "runtime" / "native" / "review_notifications_state.json"
            self._notification_service = ReviewNotificationService(state_path=state_path)
        return self._notification_service

    def notification_items(self) -> list[dict[str, Any]]:
        """Inbox items enriched with the fields notifications need.

        The public list_all view is intentionally not changed; enrichment adds
        ``deferred_until`` and ``change_type`` pulled from the raw records.
        """

        enriched: list[dict[str, Any]] = []
        for view in self.list_all():
            item = dict(view)
            if view["item_type"] == "approval":
                raw = self.approvals.get(view["item_id"])
            else:
                raw = self.reviews.get(view["item_id"])
            if raw:
                item["deferred_until"] = str(raw.get("deferred_until") or "")
                meta = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
                change_type = str(
                    raw.get("change_type") or meta.get("change_type") or raw.get("intent") or ""
                )
                action_probe = " ".join(
                    str(raw.get(key) or "").lower()
                    for key in ("command", "tool_name", "category")
                )
                if "credential" in action_probe:
                    change_type = "credential_change"
                elif any(token in action_probe for token in ("send", "forward", "publish")):
                    change_type = "external_send"
                item["change_type"] = change_type
            enriched.append(item)
        return enriched

    def metrics(self, *, window_days: int | None = None) -> dict[str, Any]:
        """Governance metrics for this inbox (ids/payloads/secrets excluded)."""

        from secondbrain.metrics.review_approval_metrics import ReviewApprovalMetrics

        return ReviewApprovalMetrics(inbox=self).export(window_days=window_days)

    def evaluate_notifications(self, *, now=None, service=None):
        svc = service or self.notification_service()
        return svc.evaluate(self.notification_items(), now=now)

    def notification_badge(self, *, now=None, service=None) -> int:
        svc = service or self.notification_service()
        return svc.badge_count(self.notification_items(), now=now)

    def _apply_memory_governance(
        self,
        review_metadata: Mapping[str, Any],
        status: str,
        actor: str,
    ) -> None:
        """Route a decided memory-governed review to the governance service.

        Runs only after the review transition has succeeded, guaranteeing no
        memory is written before a decision exists.
        """

        if self.memory_governance is None:
            return
        if str(review_metadata.get("governance") or "") != "memory":
            return
        candidate_id = str(review_metadata.get("candidate_id") or "")
        if not candidate_id:
            return
        self.memory_governance.apply_memory_decision(candidate_id, status, actor=actor)

    @staticmethod
    def _correlation_id(
        approval: dict[str, Any] | None,
        reviews: list[dict[str, Any]],
        requested: str,
    ) -> str:
        if requested:
            return requested
        if approval is not None:
            return str(approval.get("plan_id") or approval.get("approval_id") or "")
        review = reviews[0]
        metadata = review.get("metadata") if isinstance(review.get("metadata"), dict) else {}
        return str(metadata.get("plan_id") or review.get("approval_id") or review.get("review_id") or "")

    def _linked_records(self, item_id: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        approval = self.approvals.get(item_id)
        review = self.reviews.get(item_id)
        if approval is None and review is not None and review.get("approval_id"):
            approval = self.approvals.get(str(review["approval_id"]))
        reviews = []
        if approval is not None:
            approval_id = str(approval["approval_id"])
            reviews = [row for row in self.reviews.list() if row.get("approval_id") == approval_id]
            linked_id = str(approval.get("review_id") or "")
            if linked_id and not any(row.get("review_id") == linked_id for row in reviews):
                linked = self.reviews.get(linked_id)
                if linked is not None:
                    reviews.append(linked)
        elif review is not None:
            reviews = [review]
        return approval, reviews

    def _review_for_approval(self, approval: dict[str, Any]) -> dict[str, Any] | None:
        review_id = str(approval.get("review_id") or "")
        if review_id:
            review = self.reviews.get(review_id)
            if review is not None:
                return review
        approval_id = str(approval.get("approval_id") or "")
        return next((row for row in self.reviews.list() if row.get("approval_id") == approval_id), None)

    @classmethod
    def _approval_view(cls, approval: dict[str, Any], review: dict[str, Any] | None) -> dict[str, Any]:
        status = str(approval.get("status") or "pending")
        return {
            "item_id": str(approval.get("approval_id") or ""),
            "item_type": "approval",
            "category": str(approval.get("category") or review and review.get("category") or "risky_agent_action"),
            "status": status,
            "title": str(review.get("title") if review else approval.get("text") or approval.get("command") or ""),
            "description": str(review.get("description") if review else approval.get("reason") or ""),
            "source": str(review.get("source") if review else "agent" if approval.get("plan_id") else "native"),
            "target": str(approval.get("target") or review and review.get("target") or ""),
            "risk_level": str(approval.get("risk_level") or ""),
            "plan_id": str(approval.get("plan_id") or ""),
            "step_id": str(approval.get("step_id") or ""),
            "created_at": str(approval.get("created_at") or review and review.get("created_at") or ""),
            "updated_at": cls._latest_timestamp(approval, review),
            "actions_allowed": cls._actions_allowed(status),
        }

    @classmethod
    def _review_view(cls, review: dict[str, Any]) -> dict[str, Any]:
        metadata = review.get("metadata") if isinstance(review.get("metadata"), dict) else {}
        status = str(review.get("status") or "pending")
        return {
            "item_id": str(review.get("review_id") or ""),
            "item_type": "review",
            "category": str(review.get("category") or "risky_agent_action"),
            "status": status,
            "title": str(review.get("title") or ""),
            "description": str(review.get("description") or ""),
            "source": str(review.get("source") or ""),
            "target": str(review.get("target") or ""),
            "risk_level": str(metadata.get("risk_level") or ""),
            "plan_id": str(metadata.get("plan_id") or ""),
            "step_id": str(metadata.get("step_id") or ""),
            "created_at": str(review.get("created_at") or ""),
            "updated_at": str(review.get("decided_at") or review.get("created_at") or ""),
            "actions_allowed": cls._actions_allowed(status),
        }

    @staticmethod
    def _actions_allowed(status: str) -> list[str]:
        if status == "pending":
            return ["approve", "reject", "defer"]
        if status == "deferred":
            return ["approve", "reject"]
        return []

    @staticmethod
    def _latest_timestamp(approval: dict[str, Any], review: dict[str, Any] | None) -> str:
        values = [str(approval.get("decided_at") or approval.get("created_at") or "")]
        if review is not None:
            values.append(str(review.get("decided_at") or review.get("created_at") or ""))
        return max(values)

    @staticmethod
    def _sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
        critical = item["category"] in {"delete_request", "connector_permission_change", "sensitive_document"} or item[
            "risk_level"
        ] in {"high", "critical", "destructive"}
        completed = item["status"] not in {"pending", "deferred"}
        return (0 if critical else 1, 1 if completed else 0, item["created_at"])

    @staticmethod
    def _validate_category(category: str | None) -> None:
        if category is not None and category not in REVIEW_CATEGORIES:
            raise ValueError(f"invalid_review_category:{category}")

    @staticmethod
    def _validate_transition(item_type: str, old_status: str, new_status: str) -> None:
        allowed = {
            "pending": {"approved", "rejected", "deferred"},
            "deferred": {"approved", "rejected"},
        }
        if new_status not in allowed.get(old_status, set()):
            raise ValueError(f"invalid_{item_type}_transition:{old_status}->{new_status}")

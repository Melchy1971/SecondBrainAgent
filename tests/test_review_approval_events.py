from __future__ import annotations

import json

import pytest

from secondbrain.agent.approval_service import AgentApprovalService
from secondbrain.agent.review_service import UnifiedReviewInbox
from secondbrain.agent.tool_registry import ToolDefinition, ToolInputSchema, ToolRiskLevel
from secondbrain.events.domain_events import (
    AgentPlanPaused,
    AgentPlanRejected,
    AgentPlanResumed,
    ApprovalApproved,
    ApprovalDeferred,
    ApprovalRejected,
    ApprovalRequested,
    ReviewCreated,
    ReviewResolved,
)
from secondbrain.events.event_bus import EventBus
from secondbrain.native.approval import NativeApprovalQueue, ReviewQueue


def _tool() -> ToolDefinition:
    return ToolDefinition(
        "documents.delete",
        "Delete a document",
        input_schema=ToolInputSchema(
            properties={
                "document_id": {"type": "string"},
                "token": {"type": "string", "sensitive": True},
            }
        ),
        risk_level=ToolRiskLevel.HIGH,
        requires_approval=True,
        handler=lambda payload: payload,
    )


def _queued_approval(queue: NativeApprovalQueue, suffix: str = "1") -> dict:
    return queue.create(
        command="documents.delete",
        intent="delete_document",
        text="Delete document",
        category="delete_request",
        plan_id=f"plan-{suffix}",
        step_id=f"step-{suffix}",
        tool_name="documents.delete",
        workspace_id="workspace-1",
    )


def test_approval_creation_publishes_requested_and_plan_paused(tmp_path) -> None:
    bus = EventBus()
    events = []
    bus.subscribe(ApprovalRequested, events.append)
    bus.subscribe(AgentPlanPaused, events.append)
    service = AgentApprovalService(tmp_path, event_bus=bus)

    approval = service.create_approval(
        plan_id="plan-1",
        step_id="step-1",
        tool=_tool(),
        intent="delete_document",
        payload={"document_id": "doc-1", "token": "raw-secret"},
        workspace_id="workspace-1",
        actor="agent",
        correlation_id="corr-1",
    )

    assert [event.event_type for event in events] == ["ApprovalRequested", "AgentPlanPaused"]
    requested, paused = events
    assert requested.item_id == approval["approval_id"]
    assert requested.workspace_id == "workspace-1"
    assert requested.plan_id == paused.plan_id == "plan-1"
    assert paused.causation_id == requested.event_id
    assert "raw-secret" not in json.dumps([event.to_dict() for event in events])


@pytest.mark.parametrize(
    ("method", "event_type", "plan_event_type", "expected_status"),
    [
        ("approve", ApprovalApproved, AgentPlanResumed, "approved"),
        ("reject", ApprovalRejected, AgentPlanRejected, "rejected"),
        ("defer", ApprovalDeferred, AgentPlanPaused, "deferred"),
    ],
)
def test_approval_decisions_publish_domain_and_plan_events(
    tmp_path,
    method: str,
    event_type,
    plan_event_type,
    expected_status: str,
) -> None:
    bus = EventBus()
    events = []
    bus.subscribe(event_type, events.append)
    bus.subscribe(plan_event_type, events.append)
    queue = NativeApprovalQueue(tmp_path)
    approval = _queued_approval(queue, method)
    service = AgentApprovalService(queue=queue, event_bus=bus)

    if method == "defer":
        updated = service.defer(approval["approval_id"], "reviewer", until="2026-08-01T00:00:00Z")
    else:
        updated = getattr(service, method)(approval["approval_id"], "reviewer")

    assert updated["status"] == expected_status
    assert [event.event_type for event in events] == [event_type.EVENT_TYPE, plan_event_type.EVENT_TYPE]
    assert events[1].causation_id == events[0].event_id
    assert events[0].actor == "reviewer"


def test_handler_failure_is_audited_without_rolling_back_decision(tmp_path) -> None:
    bus = EventBus()

    def broken_handler(event) -> None:
        raise RuntimeError("token=must-not-leak")

    bus.subscribe(ApprovalApproved, broken_handler)
    queue = NativeApprovalQueue(tmp_path)
    approval = _queued_approval(queue)
    service = AgentApprovalService(queue=queue, event_bus=bus)

    updated = service.approve(approval["approval_id"], "reviewer")

    assert updated["status"] == "approved"
    assert service.get(approval["approval_id"])["status"] == "approved"
    assert len(bus.error_audit) == 1
    assert "must-not-leak" not in json.dumps(bus.error_audit)


def test_correlation_id_survives_approval_and_plan_resume(tmp_path) -> None:
    bus = EventBus()
    events = []
    for event_type in (ApprovalRequested, AgentPlanPaused, ApprovalApproved, AgentPlanResumed):
        bus.subscribe(event_type, events.append)
    service = AgentApprovalService(tmp_path, event_bus=bus)
    approval = service.create_approval(
        plan_id="plan-correlated",
        step_id="step-1",
        tool=_tool(),
        intent="delete_document",
        payload={"document_id": "doc-1"},
        correlation_id="correlation-42",
    )

    service.approve(approval["approval_id"], "reviewer")

    assert len(events) == 4
    assert {event.correlation_id for event in events} == {"correlation-42"}
    assert events[-1].event_type == "AgentPlanResumed"
    assert events[-1].causation_id == events[-2].event_id


def test_sensitive_metadata_is_removed_and_inline_secrets_are_redacted() -> None:
    event = ApprovalRequested(
        item_id="approval-1",
        sanitized_metadata={
            "token": "top-secret",
            "accessToken": "also-hidden",
            "nested": {"password": "hidden", "safe": "visible"},
            "message": "Authorization failed for Bearer abcdef123456",
            "api_response": "api_key=abcdef123456",
        },
    )
    serialized = json.dumps(event.to_dict())

    assert "top-secret" not in serialized
    assert "also-hidden" not in serialized
    assert "hidden" not in serialized
    assert "abcdef123456" not in serialized
    assert event.sanitized_metadata["nested"] == {"safe": "visible"}
    assert "token" not in event.sanitized_metadata


def test_cyclic_event_publication_is_blocked_and_audited() -> None:
    bus = EventBus(max_processing_depth=4)
    calls = []

    def republish(event) -> None:
        calls.append(event.event_id)
        result = bus.publish(ApprovalRequested(correlation_id=event.correlation_id))
        assert result.accepted is False
        assert result.blocked_reason == "cyclic_event_processing_blocked"

    bus.subscribe(ApprovalRequested, republish)

    result = bus.publish(ApprovalRequested(correlation_id="cycle-1"))

    assert result.accepted is True
    assert calls and len(calls) == 1
    assert bus.error_audit[-1]["error"] == "cyclic_event_processing_blocked"


def test_subscribe_and_unsubscribe_are_idempotent() -> None:
    bus = EventBus()
    events = []
    handler = events.append
    bus.subscribe(ApprovalRequested, handler)
    bus.subscribe("ApprovalRequested", handler)

    bus.publish(ApprovalRequested())
    assert len(events) == 1
    assert bus.unsubscribe(ApprovalRequested, handler) is True
    assert bus.unsubscribe(ApprovalRequested, handler) is False
    bus.publish(ApprovalRequested())
    assert len(events) == 1


def test_review_creation_and_decision_publish_events(tmp_path) -> None:
    bus = EventBus()
    events = []
    bus.subscribe(ReviewCreated, events.append)
    bus.subscribe(ReviewResolved, events.append)
    inbox = UnifiedReviewInbox(
        tmp_path,
        review_queue=ReviewQueue(tmp_path),
        event_bus=bus,
    )
    review = inbox.create_review(
        category="failed_import",
        title="Import failed",
        source="importer",
        metadata={"plan_id": "import-plan", "workspace_id": "workspace-1"},
        actor="import-service",
    )

    resolved = inbox.approve(review["review_id"], "reviewer", "retry allowed")

    assert resolved["status"] == "approved"
    assert [event.event_type for event in events] == ["ReviewCreated", "ReviewResolved"]
    assert {event.correlation_id for event in events} == {"import-plan"}
    assert events[1].sanitized_metadata["status"] == "approved"

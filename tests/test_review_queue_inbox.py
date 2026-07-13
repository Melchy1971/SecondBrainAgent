from __future__ import annotations

from secondbrain.agent.safety import ApprovalItem, ReviewItem, SafetyService
from secondbrain.gui.approval_inbox import ApprovalInbox
from secondbrain.native.approval import REVIEW_CATEGORIES, NativeApprovalQueue, ReviewQueue


def test_entities_exist_and_categories_are_supported(tmp_path):
    queue = NativeApprovalQueue(tmp_path)
    created = queue.create(command="file.delete", intent="delete", text="rm", category="delete_request")

    item = ApprovalItem(**created)
    assert item.category == "delete_request"
    assert "risky_agent_action" in REVIEW_CATEGORIES

    review = ReviewQueue(tmp_path).create(
        category="failed_import",
        title="Import fehlgeschlagen",
        description="Datei unvollständig",
        source="importer",
        target="file.pdf",
        approval_id=item.approval_id,
    )
    review_item = ReviewItem(**review)
    assert review_item.category == "failed_import"


def test_inbox_supports_approve_reject_defer_and_audits(tmp_path):
    service = SafetyService(tmp_path)
    rec = service.request(actor="agent", action="email.send", text="mail", target="target1")
    inbox = ApprovalInbox(tmp_path, safety=service)

    rendered = inbox.render()
    assert rendered["pending"] == 1
    assert "defer" in rendered["actions"]

    defer_result = inbox.defer(rec["approval_id"], decided_by="markus", note="warte auf input")
    assert defer_result["status"] == "deferred"

    # Deferred items remain visible in the open inbox.
    rendered_after_defer = inbox.render()
    assert rendered_after_defer["deferred"] == 1

    approve_result = inbox.approve(rec["approval_id"], decided_by="markus")
    assert approve_result["status"] == "approved"

    events = service.audit_events(limit=10)
    intents = [e.get("intent") for e in events]
    assert "safety.defer" in intents
    assert "safety.approve" in intents

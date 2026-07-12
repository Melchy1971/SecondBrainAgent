from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path

import pytest

from secondbrain.agent.review_service import UnifiedReviewInbox
from secondbrain.gui.approval_inbox import (
    INBOX_TABS,
    TAB_APPROVALS,
    TAB_COMPLETED,
    TAB_DEFERRED,
    ApprovalInboxViewModel,
)
from secondbrain.native.ai_workspace.service import AIWorkspaceService
from secondbrain.native.approval import NativeApprovalQueue, ReviewQueue, approval_path


def _approval(tmp_path, *, command: str = "records.delete", payload: dict | None = None):
    return NativeApprovalQueue(tmp_path).create(
        command=command,
        intent="test_action",
        text=f"Execute {command}",
        target="document-1",
        risk_level="high",
        category="delete_request" if "delete" in command else "risky_agent_action",
        plan_id="plan-1",
        step_id="step-1",
        tool_name=command,
        payload=payload or {},
    )


def test_view_model_starts_without_queue_files(tmp_path):
    model = ApprovalInboxViewModel(tmp_path)

    state = model.load(TAB_APPROVALS)

    assert state["ok"] is True
    assert state["items"] == []
    assert state["empty_message"] == "Keine offenen Freigaben"
    assert INBOX_TABS == ("Alle", "Freigaben", "Prüfungen", "Zurückgestellt", "Erledigt")


def test_pending_approval_is_visible_without_plan_id_in_list(tmp_path):
    approval = _approval(tmp_path)
    model = ApprovalInboxViewModel(tmp_path)

    state = model.load(TAB_APPROVALS)
    detail = model.detail(approval["approval_id"])

    assert [item["item_id"] for item in state["items"]] == [approval["approval_id"]]
    assert "plan_id" not in state["items"][0]
    assert detail["plan_id"] == "plan-1"
    assert detail["plan_step"] == "plan-1:step-1"
    assert state["pending_count"] == 1
    assert state["critical_count"] == 1


def test_approve_refreshes_pending_and_completed_views(tmp_path):
    approval = _approval(tmp_path)
    model = ApprovalInboxViewModel(tmp_path)

    model.approve(approval["approval_id"], note="confirmed")

    assert model.load(TAB_APPROVALS)["items"] == []
    assert [item["item_id"] for item in model.load(TAB_COMPLETED)["items"]] == [approval["approval_id"]]


def test_reject_removes_item_from_pending(tmp_path):
    approval = _approval(tmp_path)
    model = ApprovalInboxViewModel(tmp_path)

    model.reject(approval["approval_id"], note="rejected")

    assert model.load(TAB_APPROVALS)["items"] == []
    assert model.detail(approval["approval_id"])["status"] == "rejected"


def test_defer_moves_item_to_deferred_tab(tmp_path):
    approval = _approval(tmp_path)
    model = ApprovalInboxViewModel(tmp_path)

    model.defer(approval["approval_id"], until="2026-07-15T09:00:00+00:00", note="later")

    assert model.load(TAB_APPROVALS)["items"] == []
    deferred = model.load(TAB_DEFERRED)
    assert [item["item_id"] for item in deferred["items"]] == [approval["approval_id"]]
    assert deferred["empty_message"] == "Keine zurückgestellten Einträge"


def test_linked_review_and_approval_render_only_once(tmp_path):
    approval = _approval(tmp_path)
    reviews = ReviewQueue(tmp_path)
    review = reviews.create(
        category="delete_request",
        title="Linked delete review",
        approval_id=approval["approval_id"],
    )
    NativeApprovalQueue(tmp_path).link_review(approval["approval_id"], review["review_id"])
    model = ApprovalInboxViewModel(
        tmp_path,
        inbox=UnifiedReviewInbox(
            approval_queue=NativeApprovalQueue(tmp_path),
            review_queue=reviews,
        ),
    )

    assert len(model.load()["items"]) == 1
    assert model.load()["items"][0]["item_type"] == "approval"


def test_detail_redacts_payload_and_audit_secret_values(tmp_path):
    secret = "super-secret-value"
    approval = _approval(
        tmp_path,
        command="mail.send",
        payload={"recipient": "person@example.com", "token": secret, "nested": {"password": "nested-secret"}},
    )
    queue = NativeApprovalQueue(tmp_path)
    queue.transition(approval["approval_id"], "deferred", actor="reviewer", note=f"never show {secret}")

    detail = ApprovalInboxViewModel(tmp_path).detail(approval["approval_id"])
    rendered = json.dumps(detail, ensure_ascii=False)

    assert secret not in rendered
    assert "nested-secret" not in rendered
    assert detail["payload"]["token"] == "***"
    assert detail["payload"]["nested"]["password"] == "***"
    assert "Sendeaktion" in detail["warning"]


def test_corrupt_queue_returns_controlled_loading_error(tmp_path):
    path = approval_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{broken json\n", encoding="utf-8")

    state = ApprovalInboxViewModel(tmp_path).load()

    assert state["ok"] is False
    assert state["items"] == []
    assert state["empty_message"] == "Fehler beim Laden"


def test_native_workspace_registers_existing_inbox_module():
    root = Path(__file__).resolve().parents[1]
    service = AIWorkspaceService(root)
    modules = {module.id: module for module in service.snapshot().modules}

    assert modules["review_inbox"].title == "Prüfungen & Freigaben"
    assert modules["review_inbox"].status == "ready"
    assert service.module_payload("review_inbox")["status"] in {"ready", "error"}


def _display_available() -> bool:
    try:
        root = tk.Tk()
    except tk.TclError:
        return False
    root.destroy()
    return True


@pytest.mark.skipif(not _display_available(), reason="kein Display verfügbar")
def test_embedded_frame_builds_without_queue_files(tmp_path):
    from secondbrain.gui.approval_inbox import ApprovalInboxFrame

    root = tk.Tk()
    root.withdraw()
    try:
        frame = ApprovalInboxFrame(root, tmp_path)
        assert frame.winfo_exists()
        assert tuple(frame.trees) == INBOX_TABS
        assert frame.badge_var.get().startswith("0 offen")
    finally:
        root.destroy()

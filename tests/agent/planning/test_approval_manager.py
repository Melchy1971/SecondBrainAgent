from secondbrain.agent.planning.approval_manager import ApprovalManager


def test_approval_required_for_high_risk_tool():
    manager = ApprovalManager()

    assert manager.requires_approval(["delete_documents"])


def test_approval_required_for_large_bulk_action():
    manager = ApprovalManager()

    assert manager.requires_approval([], {"bulk_items": 101})


def test_approval_decision_is_recorded():
    manager = ApprovalManager()
    request = manager.request("task-1", "Risky")

    manager.decide(request.request_id, True)

    assert manager.granted_for("task-1") is True

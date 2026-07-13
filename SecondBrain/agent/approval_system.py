"""P2 v21.1 - Approval System."""

class ApprovalSystem:
    def __init__(self):
        self._approvals: dict[str, bool] = {}

    def approve(self, action_id: str):
        self._approvals[action_id] = True

    def reject(self, action_id: str):
        self._approvals[action_id] = False

    def is_approved(self, action_id: str) -> bool:
        return self._approvals.get(action_id, False)

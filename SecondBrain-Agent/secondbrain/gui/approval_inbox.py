"""P5 v23.0 - Approval Inbox."""

class ApprovalInbox:
    def render(self, approvals: list[dict]):
        return {
            "pending": len(approvals),
            "items": approvals,
        }

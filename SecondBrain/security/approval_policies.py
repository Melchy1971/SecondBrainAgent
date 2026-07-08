"""P8 v26.0 - Approval Policies."""

class ApprovalPolicies:
    def requires_approval(self, action: str) -> bool:
        protected = {"delete", "export", "connector_write"}
        return action in protected

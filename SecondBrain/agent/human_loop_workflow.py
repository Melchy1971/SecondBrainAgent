"""P2 v21.2 - Human in the Loop Workflow."""

class HumanLoopWorkflow:
    def create_approval_request(self, action_id: str, description: str):
        return {
            "action_id": action_id,
            "description": description,
            "status": "PENDING",
        }

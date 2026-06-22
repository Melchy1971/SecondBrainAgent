"""P2 v21.2 - Agent State Machine."""

from enum import Enum


class AgentState(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentStateMachine:
    def __init__(self):
        self.state = AgentState.IDLE

    def transition(self, state: AgentState):
        self.state = state
        return self.state

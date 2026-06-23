from dataclasses import dataclass
from .gui_state import GuiState

@dataclass(frozen=True)
class ShutdownResult:
    status: str
    saved_state: dict

class ShutdownManager:
    def __init__(self, state: GuiState) -> None:
        self.state = state

    def shutdown(self) -> ShutdownResult:
        self.state.startup_status = "stopped"
        return ShutdownResult(status="STOPPED", saved_state=self.state.snapshot())

from dataclasses import dataclass, asdict
from pathlib import Path
import json
from .permissions_v106 import PermissionPolicy
from .job_queue_v106 import JsonlJobQueue, JobRunner

@dataclass
class AgentState:
    name: str
    status: str = "idle"
    last_task: str = ""
    cycles: int = 0

class AgentKernel:
    def __init__(self, runtime_dir: str | Path, policy: PermissionPolicy | None = None):
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime_dir / "agent_state.json"
        self.queue = JsonlJobQueue(self.runtime_dir / "jobs.jsonl")
        self.policy = policy or PermissionPolicy(max_level=1)
        self.handlers = {}

    def register_handler(self, action: str, handler, level: int | str = 1, risk_score: int = 0):
        self.handlers[action] = (handler, level, risk_score)

    def submit(self, action: str, payload: dict):
        return self.queue.add(action, payload)

    def _guarded_handlers(self):
        guarded = {}
        for action, (handler, level, risk_score) in self.handlers.items():
            def make_guard(a, h, l, r):
                def wrapped(payload):
                    decision = self.policy.evaluate(a, l, r)
                    if not decision.allowed:
                        raise PermissionError(decision.reason)
                    if decision.requires_approval and not payload.get("approved"):
                        raise PermissionError("approval_required")
                    return h(payload)
                return wrapped
            guarded[action] = make_guard(action, handler, level, risk_score)
        return guarded

    def tick(self) -> dict:
        state = self.load_state()
        state.status = "running"
        state.cycles += 1
        self.save_state(state)
        result = JobRunner(self.queue, self._guarded_handlers()).run_once()
        state.status = "idle"
        state.last_task = json.dumps(result, ensure_ascii=False)
        self.save_state(state)
        return result

    def load_state(self) -> AgentState:
        if self.state_path.exists():
            return AgentState(**json.loads(self.state_path.read_text(encoding="utf-8")))
        return AgentState(name="SecondBrain Agent")

    def save_state(self, state: AgentState) -> None:
        self.state_path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")

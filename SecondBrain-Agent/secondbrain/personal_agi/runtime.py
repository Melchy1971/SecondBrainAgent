import json
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


class Store:
    def __init__(self, root="."):
        self.base = Path(root) / "data" / "personal_agi"
        self.base.mkdir(parents=True, exist_ok=True)

    def load(self, name, default):
        path = self.base / f"{name}.json"
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, name, value):
        (self.base / f"{name}.json").write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")

    def append(self, name, item):
        items = self.load(name, [])
        items.append(item)
        self.save(name, items)
        return item


class GovernancePolicy:
    blocked = {"delete_all", "send_email", "execute_shell", "purchase", "modify_system"}
    approval = {"calendar_write", "email_draft", "connector_write", "file_write", "system_change"}

    def evaluate(self, action, risk="low"):
        if action in self.blocked:
            return {"allowed": False, "requires_approval": False, "reason": "blocked_action"}
        if risk == "high" or action in self.approval:
            return {"allowed": True, "requires_approval": True, "reason": "approval_required"}
        return {"allowed": True, "requires_approval": False, "reason": "allowed"}


class PersistentDaemon:
    def __init__(self, store):
        self.store = store

    def start(self):
        state = {"id": str(uuid4()), "status": "running", "mode": "supervised", "heartbeat": datetime.now(timezone.utc).isoformat()}
        self.store.save("daemon", state)
        return state

    def stop(self):
        state = self.store.load("daemon", {"status": "stopped"})
        state["status"] = "stopped"
        state["stopped_at"] = datetime.now(timezone.utc).isoformat()
        self.store.save("daemon", state)
        return state

    def tick(self):
        state = self.store.load("daemon", {"status": "stopped"})
        if state.get("status") != "running":
            return {"ok": False, "status": "stopped"}
        state["heartbeat"] = datetime.now(timezone.utc).isoformat()
        self.store.save("daemon", state)
        return {"ok": True, "heartbeat": state["heartbeat"]}

    def status(self):
        return self.store.load("daemon", {"status": "stopped"})


class CognitiveCycle:
    def __init__(self, store, policy):
        self.store = store
        self.policy = policy

    def run(self, signal, source="manual"):
        observation = {"id": str(uuid4()), "phase": "observe", "signal": signal, "source": source}
        thought = {"id": str(uuid4()), "phase": "think", "summary": f"Interpreted: {signal}", "intent": "assist"}
        plan = {
            "id": str(uuid4()),
            "phase": "plan",
            "steps": [
                {"id": "step_1", "action": "recommend", "risk": "low"},
                {"id": "step_2", "action": "notify_user", "risk": "low"},
            ],
        }
        results = []
        for step in plan["steps"]:
            decision = self.policy.evaluate(step["action"], step["risk"])
            status = "blocked" if not decision["allowed"] else "approval_required" if decision["requires_approval"] else "executed"
            results.append({**step, "policy": decision, "status": status})
        action = {"id": str(uuid4()), "phase": "act", "results": results}
        verification = {
            "id": str(uuid4()),
            "phase": "verify",
            "status": "success" if all(r["status"] == "executed" for r in results) else "pending_or_failed",
        }
        learning = {
            "id": str(uuid4()),
            "phase": "learn",
            "lesson": "Continue strategy" if verification["status"] == "success" else "Review autonomy boundary",
        }
        cycle = {
            "id": str(uuid4()),
            "signal": signal,
            "observation": observation,
            "thought": thought,
            "plan": plan,
            "action": action,
            "verification": verification,
            "learning": learning,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.append("cycles", cycle)


class ProactiveAssistant:
    def __init__(self, store):
        self.store = store

    def briefing(self):
        cycles = self.store.load("cycles", [])
        pending = []
        for cycle in cycles:
            pending.extend([r for r in cycle["action"]["results"] if r["status"] == "approval_required"])
        return {
            "date": datetime.now().date().isoformat(),
            "cycles": len(cycles),
            "pending_approvals": len(pending),
            "message": "System bereit" if not pending else "Freigaben erforderlich",
        }

    def recommendations(self):
        cycles = self.store.load("cycles", [])
        if not cycles:
            return [{"priority": "medium", "title": "Ersten AGI-Zyklus ausführen", "reason": "no_cycle_data"}]
        return [{"priority": "low", "title": "Lernstand prüfen", "reason": "cycle_data_available", "cycles": len(cycles)}]


class SelfOptimizer:
    def __init__(self, store):
        self.store = store

    def analyze(self):
        cycles = self.store.load("cycles", [])
        failed = [c for c in cycles if c["verification"]["status"] != "success"]
        report = {
            "cycles": len(cycles),
            "failed_or_pending": len(failed),
            "recommendations": [{"type": "continue", "priority": "low"}] if not failed else [{"type": "review_plan_quality", "priority": "medium"}],
        }
        self.store.save("optimization_report", report)
        return report

    def backlog(self):
        report = self.analyze()
        items = []
        for rec in report["recommendations"]:
            items.append({"id": str(uuid4()), "title": f"Optimization: {rec['type']}", "priority": rec["priority"], "status": "open"})
        self.store.save("optimization_backlog", items)
        return items


class PersistentPersonalAGI:
    def __init__(self, root="."):
        self.store = Store(root)
        self.policy = GovernancePolicy()
        self.daemon = PersistentDaemon(self.store)
        self.cycle = CognitiveCycle(self.store, self.policy)
        self.assistant = ProactiveAssistant(self.store)
        self.optimizer = SelfOptimizer(self.store)

    def status(self):
        return {
            "version": "14.0",
            "daemon": self.daemon.status(),
            "cycles": len(self.store.load("cycles", [])),
            "mode": "supervised_personal_agi",
            "autonomy_boundary": "approval_required_for_high_risk_actions",
        }

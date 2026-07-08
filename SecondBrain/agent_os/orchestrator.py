from .store import JsonStore
from secondbrain.runtime_supervisor import RuntimeSupervisor
from secondbrain.background_jobs import BackgroundJobScheduler
from secondbrain.goal_engine import GoalEngine
from secondbrain.recommendations import RecommendationEngine
from secondbrain.notifications import NotificationEngine
from secondbrain.personal_assistant import ProactiveAssistant


class PersonalAGIOS:
    def __init__(self, root="."):
        self.store = JsonStore(root, "agent_os")
        self.supervisor = RuntimeSupervisor(self.store)
        self.jobs = BackgroundJobScheduler(self.store)
        self.goals = GoalEngine(self.store)
        self.notifications = NotificationEngine(self.store)
        self.recommendations = RecommendationEngine(self.store, self.goals, self.supervisor)
        self.assistant = ProactiveAssistant(self.supervisor, self.jobs, self.goals, self.recommendations, self.notifications)

    def status(self) -> dict:
        return {
            "version": "13.0",
            "runtime": self.supervisor.health(),
            "services": self.supervisor.services(),
            "jobs": len(self.jobs.jobs()),
            "goals": len(self.goals.goals()),
            "notifications": len(self.notifications.list(100000)),
        }

    def start(self) -> dict:
        return self.supervisor.start()

    def stop(self) -> dict:
        return self.supervisor.stop()

    def health(self) -> dict:
        return self.supervisor.health()

    def recover(self) -> dict:
        return self.supervisor.recover()

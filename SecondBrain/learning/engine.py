from .store import LearningStore
from .models import Experience
from .experience import ExperienceStore
from .episodes import EpisodeMemory
from .metrics import SkillMetrics
from .reflection import ReflectionEngine
from .backlog import LearningBacklog


class LearningEngine:
    def __init__(self, root="."):
        self.store = LearningStore(root)
        self.experiences = ExperienceStore(self.store)
        self.episodes = EpisodeMemory(self.store)
        self.metrics = SkillMetrics(self.store)
        self.reflection = ReflectionEngine(self.store)
        self.backlog = LearningBacklog(self.store)

    def status(self) -> dict:
        return {
            "experiences": len(self.experiences.list(100000)),
            "episodes": len(self.episodes.list(100000)),
            "backlog": len(self.backlog.list()),
            "skills": len(self.metrics.compute()),
        }

    def add_experience(self, task: str, outcome: str, success: bool, capability: str, duration_seconds: float = 0.0, error: str | None = None) -> dict:
        return self.experiences.add(Experience(task, outcome, success, capability, duration_seconds, error))

    def reflect(self) -> dict:
        return self.reflection.reflect()

    def create_backlog_from_reflection(self) -> list[dict]:
        return self.backlog.from_reflection(self.reflect())

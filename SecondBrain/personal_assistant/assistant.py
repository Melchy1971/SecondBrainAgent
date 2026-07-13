from datetime import datetime


class ProactiveAssistant:
    def __init__(self, supervisor, jobs, goals, recommendations, notifications):
        self.supervisor = supervisor
        self.jobs = jobs
        self.goals = goals
        self.recommendations = recommendations
        self.notifications = notifications

    def briefing(self) -> dict:
        recs = self.recommendations.generate()
        briefing = {
            "date": datetime.now().date().isoformat(),
            "runtime": self.supervisor.health(),
            "open_goals": len(self.goals.goals()),
            "recommendations": recs,
            "message": "System bereit" if self.supervisor.health()["status"] == "healthy" else "System benötigt Recovery",
        }
        self.notifications.send("Daily Briefing", briefing["message"], priority="info")
        return briefing

    def review(self) -> dict:
        runs = self.jobs.runs()
        forecast = self.goals.forecast()
        return {
            "job_runs": len(runs),
            "goals": forecast,
            "runtime": self.supervisor.health(),
            "recommendations": self.recommendations.generate(),
        }

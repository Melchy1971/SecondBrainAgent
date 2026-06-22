"""P5 v23.2 - Agent Live Console."""

class AgentLiveConsole:
    def __init__(self):
        self._events = []

    def write(self, level: str, message: str):
        self._events.append({"level": level, "message": message})

    def history(self):
        return list(self._events)

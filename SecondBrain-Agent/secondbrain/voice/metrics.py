"""P6 v24.1 - Voice Metrics and Analytics."""

class VoiceMetrics:
    def summarize(self, sessions: int, utterances: int):
        return {
            "sessions": sessions,
            "utterances": utterances,
            "avg_utterances_per_session":
                0 if sessions == 0 else round(utterances / sessions, 2),
        }

"""P6 v24.0 - Audio Streaming Foundation."""

class AudioStream:
    def __init__(self):
        self._frames = []

    def push(self, frame):
        self._frames.append(frame)

    def size(self):
        return len(self._frames)

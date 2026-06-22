"""P2 v21.2 - Execution Queue."""

from collections import deque


class ExecutionQueue:
    def __init__(self):
        self._queue = deque()

    def enqueue(self, task):
        self._queue.append(task)

    def dequeue(self):
        return None if not self._queue else self._queue.popleft()

    def size(self):
        return len(self._queue)

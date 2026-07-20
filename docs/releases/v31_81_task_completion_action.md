# v31.81 Task Completion Action

The native Action Registry now exposes a workspace-bound `tasks.complete`
action for typed, spoken and trusted adapter input. The action collects a task
reference through the existing dialog flow and requires payload-bound
confirmation before changing the persistent task store.

References resolve by exact task ID first or by a unique, case-insensitive
title. Missing and ambiguous references fail without changing any task.
Repeated completion by ID is idempotent and preserves the original completion
timestamp.

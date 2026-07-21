# v31.85 Recoverable Task Restore

The native Action Registry now exposes a workspace-bound `tasks.restore`
action for typed and spoken recovery of archived tasks. The action collects a
task reference and requires payload-bound confirmation before writing.

Restoring returns the task to its recorded pre-archive column, preserves the
last archive timestamp, clears the active archive timestamp, and records when
recovery occurred. Invalid legacy archive metadata falls back safely to
`backlog`, while active tasks are rejected without changing the store.

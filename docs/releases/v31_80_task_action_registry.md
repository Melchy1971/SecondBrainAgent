# v31.80 Task Action Registry

The native Action Registry now exposes workspace-bound `tasks.list` and
`tasks.create` actions. German typed and spoken aliases route through the same
Action Bus as the desktop shell, without launching a subprocess.

Task creation collects a missing title through the existing dialog flow and
requires payload-bound confirmation before writing. Priorities are restricted
to `low`, `medium` or `high`; invalid values fail without changing the task
store. Listing remains read-only and uses the same persistent desktop task
service.

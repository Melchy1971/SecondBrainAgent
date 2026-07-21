# v31.83 Task Rename Action

The native Action Registry now exposes a workspace-bound `tasks.rename`
action. Typed and spoken flows collect the task reference and new title before
requiring payload-bound confirmation.

Completion and rename operations share the same ID-first, unique-title
reference resolver. Rename normalizes whitespace, rejects empty or oversized
titles before writing, and preserves its first update timestamp when repeated
with the same value.

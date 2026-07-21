# v31.84 Recoverable Task Archive

The native Action Registry now exposes a workspace-bound `tasks.archive`
action as the safe alternative to permanent deletion. Typed and spoken flows
collect a task reference and require payload-bound confirmation.

Archiving retains the complete task record, records its previous column and an
archive timestamp, and is idempotent. The native Tasks view reports archived
items separately so they are not counted as open or completed. Ambiguous
references fail without changing the store.

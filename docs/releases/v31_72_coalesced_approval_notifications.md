# v31.72 Coalesced Approval Notifications

Jarvis now combines simultaneous new-pending and newly-overdue approval events
into one tray notification. A refresh therefore emits at most one approval
notification while preserving the dedicated overdue title when that is the
only change.

The coalescing function operates exclusively on aggregate counters and does
not consume approval payloads or identifiers.

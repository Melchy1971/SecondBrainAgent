# v31.73 Risk-Aware Approval Notifications

Jarvis approval notifications now include aggregate newly-elevated risk counts.
When elevated approvals increase, the coalesced tray message receives a
dedicated high-attention title while still emitting at most once per refresh.

The risk transition uses only the existing redacted activity counters. No
approval payload, target or recipient is included in the notification.

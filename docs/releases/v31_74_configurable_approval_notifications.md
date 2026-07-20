# v31.74 Configurable Approval Notifications

Approval tray notifications can now be disabled with
`SECONDBRAIN_APPROVAL_NOTIFICATIONS_ENABLED=0`. The values `false`, `no` and
`off` are also accepted case-insensitively. Notifications remain enabled by
default.

Disabling notifications does not stop the approval refresh or reset transition
baselines. The tray status explicitly reports `Notifications Off`, and enabling
the feature later does not replay an accumulated backlog.

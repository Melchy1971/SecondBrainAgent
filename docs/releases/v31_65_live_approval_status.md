# v31.65 Live Approval Status

The native Jarvis approval alert now refreshes from the existing
workspace-isolated Approval Surface every two seconds. It reports the total
pending count and the number of visible external-write, destructive or
privileged approvals.

The projection only consumes the already-redacted snapshot. Approval payloads,
recipients and workspace identifiers remain excluded from the desktop status
surface.

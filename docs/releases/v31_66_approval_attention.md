# v31.66 Approval Attention

The live native approval status now marks visible approvals as overdue after
15 minutes. This makes unattended decisions discoverable without opening the
approval view.

The calculation uses only the timestamp already present in the redacted,
workspace-isolated snapshot. Invalid timestamps are ignored and no approval
payload data is consumed or exposed.

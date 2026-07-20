# v31.77 Approval Runtime Diagnostics

The native Diagnostics view now reports the effective approval notification
state, overdue threshold and refresh interval alongside the pending count.
This makes runtime configuration verifiable after environment parsing and
fallback handling.

Diagnostics expose only validated booleans and aggregate timing values. Raw
environment input, approval payloads, identifiers and local paths remain
excluded.

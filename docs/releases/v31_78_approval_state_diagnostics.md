# v31.78 Approval State Diagnostics

The native Diagnostics view now reports approval snapshot availability plus
aggregate pending, elevated and overdue counts. Overdue state is calculated
with the same effective threshold used by the live desktop alert.

Diagnostics derive the state from one workspace-isolated, redacted snapshot.
Provider failures produce an unavailable state with zero counters and expose
no exception details, payloads, identifiers or local paths.

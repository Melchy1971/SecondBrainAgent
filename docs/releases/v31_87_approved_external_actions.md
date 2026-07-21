# v31.87 Approved External Action Execution

The native Action Bus now prepares Calendar and Mail writes through their
existing assistant services instead of creating unbound generic approvals.
Approval records retain workspace, payload hash, expiry, and idempotency
bindings while exposing no payload through the native Approval surface.

Typed and spoken approval decisions require confirmation. Rejections never
invoke a connector. Approvals validate the persisted execution envelope before
calling the existing service, require a configured connector, and finalize the
single-use execution lease as completed or failed. Missing connectors leave the
request pending and unchanged.

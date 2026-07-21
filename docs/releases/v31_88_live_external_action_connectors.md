# v31.88 Live External Action Connectors

The native desktop app can now execute approved Calendar and Mail writes through
the existing Google Workspace or Microsoft 365 OAuth runtime. The provider is
disabled by default and must be selected explicitly:

```text
SECONDBRAIN_EXTERNAL_ACTION_PROVIDER=google
```

Use `m365` for Microsoft 365. The corresponding existing credentials and login
remain required (`google-login` or `m365-login`). A configured but unauthenticated
provider exposes no writer, so the native approval remains pending and no network
request is attempted. Restart the native desktop app after changing the provider
or completing login so it can re-evaluate the persisted authentication state.

The adapters run only after the persistent native approval validates workspace,
payload hash, expiry, and its single-use execution lease. They translate the
bounded `calendar.create` and `mail.send` payloads to the authenticated provider
clients without creating a second approval system. Diagnostics expose only the
provider readiness and write capabilities; credentials, tokens, message content,
recipients, and event details are never included.

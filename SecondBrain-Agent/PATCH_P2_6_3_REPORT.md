# PATCH P2.6.3 — Settings Security & Governance

## Inhalt

- PrivacyModeService mit blockierender `require_not_privacy_mode()`-Fassade
- SecretReference mit `secret://`-Validierung
- SecretSanitizer mit REDACT, REFERENCE_ONLY und BLOCK_EXPORT
- SecureSettingsExporter für Settings und Provider-Profile
- SettingsAuditLog für auditierbare Settings-Änderungen
- Tests für Secret-Handling, Privacy Mode, Export-Sanitizing und Audit Trail

## Validierung

- `8 passed in 0.25s`

## Wirkung

- Settings-Exports leaken keine Roh-Secrets
- Privacy Mode besitzt eine zentrale technische Sperre
- Provider-Profile können sicher exportiert werden
- Settings-Änderungen sind auditierbar

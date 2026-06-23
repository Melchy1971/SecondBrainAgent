# PATCH P0.6 — Secrets Vault Hardening

## Ziel
Produktionskritische Security-Lücke im lokalen SecretsVault schließen.

## Problem vorher
`secondbrain/production_core/security/secrets.py` speicherte Secrets nur Base64-kodiert als `value_enc`.

Risiko:
- Base64 ist keine Verschlüsselung.
- Real Secrets wären trivial rekonstruierbar.
- Release-Gate/Production-Core suggeriert Secret-Schutz, obwohl nur Obfuscation vorhanden war.

## Änderung
- `value_enc` entfernt.
- Neues `value_envelope` eingeführt.
- Lokale At-Rest-Verschlüsselung mit Python-Stdlib:
  - per Environment-Key `SECONDBRAIN_SECRETS_KEY` oder lokal generiertem Master-Key
  - Nonce je Secret
  - SHA-256-Keystream
  - HMAC-SHA256 Integritätsprüfung
- `get(name, scope)` ergänzt.
- Tamper Detection ergänzt.
- Redaction in `list()` beibehalten.

## Geänderte Dateien
- `secondbrain/production_core/security/secrets.py`
- `tests/test_p0_6_secrets_vault.py`

## Validierung
```bash
pytest -q
```

Ergebnis:
```text
395 passed in 18.43s
```

## Restrisiko
Diese Implementierung ist eine lokale stdlib-basierte Schutzschicht. Für echte Enterprise-Produktion weiterhin vorzuziehen:
- OS Keyring / Windows DPAPI
- HashiCorp Vault
- SOPS/Age
- Cloud KMS

Der vorherige Base64-Blocker ist geschlossen.

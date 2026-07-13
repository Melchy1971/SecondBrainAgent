# v30.66 — Secret-Verwaltung (AES-256, Rotation, Audit, Zeroization)

Additiv in `secondbrain/secret_manager/`. Bestehende `secrets.py`/`security/secret_vault.py` unangetastet.

## Krypto (echt, kein Fake)
Envelope-Verschluesselung: Master-Passwort -> **scrypt**-KEK (stdlib hashlib) -> umschliesst einen
zufaelligen **AES-256** Data-Key (DEK). Secrets werden mit **AES-256-GCM** (`cryptography`) verschluesselt,
AAD an den Secret-Namen gebunden. `cryptography` ist Pflicht (requirements-security.txt) - es gibt
bewusst keinen Fake-Cipher-Fallback.

## Zwei harte Regeln (getestet)
1. **Keine Secrets im Klartext** - nicht auf Platte (Vault-Datei verschluesselt), nicht im Audit-Log,
   nicht in Logs (Redaction + `SecretRedactingFilter`), nicht in `list_secrets()`/`health()`.
2. **Echte Krypto** - falsches Passwort/AAD/Manipulation -> `CryptoError`/`VaultLockedError`.

## Funktionen
- **Master Key** + **Passwortwechsel** (nur DEK-Rewrap, Secrets nicht neu verschluesselt).
- **Master-Key-Rotation** (`rotate_master_key`) - alle Secrets unter neuem DEK neu verschluesselt.
- Typen: **API Keys**, **OAuth Tokens**, **Workspace Secrets**.
- **Audit-Log** (append-only, ohne Werte).
- **Memory-Zeroization** (`SecretBytes`, `zeroize`) - DEK wird beim `lock()` ueberschrieben.
- **Export/Import** - portables, mit eigenem Passwort verschluesseltes Bundle.
- **Health** - Status/Anzahl/Typen/KDF-Parameter, keine Werte.

## GUI (ehrlich deklariert)
`secondbrain/gui/secret_manager.py` (Tkinter): Secret Manager, Passwort aendern, Export, Import,
Health-Anzeige; Secrets werden nie im Klartext angezeigt (nur Metadaten). **Windows/Desktop-Code, in
der Sandbox nicht ausgefuehrt/abgenommen** (kein Display); tkinter lazy. Logik dahinter voll getestet.

## Launcher (Python 3.11+, requirements-security.txt)
Passwoerter/Werte nur ueber ENV, nie als CLI-Argument (Shell-History):
```
SECOND_BRAIN_VAULT_PASSWORD=... python launcher.py secret-init
SECOND_BRAIN_VAULT_PASSWORD=... SECRET_VALUE=sk-... python launcher.py secret-set --name OPENAI_API_KEY --type api_key
SECOND_BRAIN_VAULT_PASSWORD=... python launcher.py secret-list        # nur Metadaten
SECOND_BRAIN_VAULT_PASSWORD=... python launcher.py secret-rotate
python launcher.py secret-health
```
Es gibt bewusst **kein** `secret-get` im Launcher (kein Klartext in Logs).

## Tests (16 passed)
Crypto-Roundtrip + falsches Passwort/AAD, Zeroization, Vault (set/get/list-ohne-Werte, Versionen,
Lock), Rotation (re-encrypt, Passwortwechsel), Export/Import (Bundle verschluesselt, falsches Passwort),
**No-Leak** (Vault-Datei/Audit/Log ohne Klartext), Health.

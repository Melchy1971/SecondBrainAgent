# Security Report — SecondBrain-Agent v30.77
Stand: 2026-07-07 | Umfang: statische Sicht + gezielte Stichproben. Kein vollständiger Secret-/Dependency-Scan (langsamer Netz-Mount, fehlende Laufzeit-Tools). Vollscan auf Windows nachziehen.

## 1. Secrets / Schlüssel im Arbeitsverzeichnis
- `auto.key` (**EC PRIVATE KEY**) und `auto.crt` liegen im Code-Root. `.env` mit lokaler Konfiguration ebenfalls.
- **Positiv:** `.gitignore` deckt `.env`, `.env/`, `auto.key` ab; `auto.key` ist **nicht** git-getrackt → kein Leak in der Versionshistorie (stichprobenhaft bestätigt).
- **Restrisiko:** Private Key liegt im Klartext im Arbeitsbaum → landet potenziell in `backups/`, `exports/`, Kopien (der zweite Baum!). Anforderung: Key-Handling zentralisieren, Backup-Ausschluss prüfen, Rotation dokumentieren.
- **Offen (auf Windows prüfen):** `git log --all -- auto.crt .env` gegen historische Commits; `git ls-files | findstr /I "key pem crt .env"`.

## 2. Dynamische Import-/Ausführungsfläche
- 15 Module nutzen `importlib`/`__import__`/`import_module`/`entry_points`/`pkgutil`. Dynamisches Laden nach String ist eine Angriffsfläche, wenn der Modul-/Pfadname aus externer Eingabe stammt (Plugins, Connector-Discovery, `plugin_manifest.json`).
- Anforderung: sicherstellen, dass Registry-/Plugin-Lader nur aus vertrauenswürdigen, festverdrahteten Verzeichnissen laden (Allowlist), keine benutzer-/netzgesteuerten Modulnamen.

## 3. Connector-/Token-Fläche
- Module `connectors.token_repository`, `connectors.webhook_manager`, `connectors.*_sync` verwalten Fremdsystem-Zugänge (GitHub, Google). Diese stehen zwar auf der statischen Orphan-Liste, sind aber sicherheitsrelevant und mit hoher Wahrscheinlichkeit registry-geladen → **nicht ohne Live-Test entfernen**.
- Anforderung: Token-Speicherung (Verschlüsselung at rest), Webhook-Signaturprüfung und Scope-Minimierung je Connector auditieren.

## 4. Auszuführender Vollscan (Windows)
1. `pip-audit` / `pip install pip-audit && pip-audit` gegen alle `requirements*.txt`.
2. Secret-Scan: `gitleaks detect` bzw. `trufflehog filesystem .` über beide Bäume.
3. `bandit -r secondbrain -ll` (statische Python-Security-Lints).

## 5. Bewertung
Kein akuter VCS-Secret-Leak nachgewiesen. Hauptrisiken: Klartext-Key im Arbeitsbaum + dynamische Ladepfade. Beides ist adressierbar, aber vor einem Release zu klären.

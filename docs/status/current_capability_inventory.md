# Capability-Inventar — tatsächlicher Stand auf `main`

Erhebungsdatum: 2026-07-21
Erhoben gegen: `origin/main` = `f0a9dd9` (Merge PR #116, `codex/v31.88-live-connectors`)
Methode: Analyse der Git-Historie, des Launcher-Kommandobestands und der Modulpfade auf `main`. Keine Live-Läufe.

## Lesehinweis

`Status` beschreibt ausschließlich den **Implementierungsstand im Code**.
`Live-Nachweis` beschreibt, ob die Funktion in einer produktionsnahen Umgebung nachweislich fehlerfrei gelaufen ist.

Beides ist getrennt zu bewerten. Eine Capability mit `implemented` und `Live-Nachweis: nein` ist nach Projektstandard **nicht abgenommen**.

Statuswerte: `implemented`, `implemented_not_certified`, `partially_implemented`, `deprecated`, `missing`, `blocked`

---

## 1. Versionierung

| Feld | Wert |
|---|---|
| `pyproject.toml` `[project].version` | `30.77.0` |
| `docs/09_MASTERPLAN_STATUS.json` `documented_feature_level` | `v31.32` |
| Höchste gemergte Feature-Stufe auf `main` | `v31.88` |

`SecondBrain/version.py` ist als Single Source of Truth implementiert und liest aus `pyproject.toml`. Die Feature-Bezeichner `v31.xx` sind Release-Labels der Entwicklungspakete und wurden nie in die Paketversion überführt.

**Befund:** Zwischen Paketversion, dokumentierter Feature-Stufe und tatsächlichem Codebestand liegen 56 Feature-Stufen. Das ist der Kern des Synchronisationsproblems.

---

## 2. Gates und Launcher-Kommandos

### Vorhanden auf `main`

| Kommando | Codepfad | Status | Live-Nachweis | Gate-Verantwortung |
|---|---|---|---|---|
| `repo-doctor` | `launcher.py:98` | implemented | ja (CI) | Repo-Hygiene |
| `dependency-inventory` | `launcher.py:116` | implemented | ja (CI) | Abhängigkeiten |
| `rc-gate` | `launcher.py:128` | implemented | ja (CI) | Release Candidate |
| `system-rc-gate` | `launcher.py:~985` | implemented | offen | System-RC |
| `review-approval-gate` | `launcher.py:145` | implemented | ja | Approval |
| `review-approval-release-gate` | `launcher.py:158` | implemented | **nein** | Approval Release |
| `connector-e2e-gate` | `launcher.py:179` | implemented_not_certified | **nein** | Connector |
| `provider-live-gate` | `launcher.py:193` | implemented_not_certified | **nein** | Provider |
| `security-gate` | `launcher.py:207` | implemented | ja (CI) | Security |
| `backup-gate` | `launcher.py:227` | implemented | offen | Backup |
| `native-voice-app-gate` | `SecondBrain/desktop_native/native_voice_app_gate.py` | implemented_not_certified | **nein** | Voice |
| `ga-readiness-gate` | `launcher.py:249` | implemented | offen | GA-Aggregation |
| `embed-gate` | `launcher.py:727` | implemented | offen | Embeddings |
| `p1-gate` | `launcher.py:~1012` | implemented | ja (CI) | RAG/P1 |
| `p0-gate`, `p0-doctor` | `launcher.py` | implemented | ja (CI) | P0 |
| `gui-doctor`, `config-doctor`, `native-desktop-doctor` | `launcher.py` | implemented | offen | Diagnose |
| `p3-pgvector-readiness` | `launcher.py:393` | partially_implemented | **nein** | pgvector |
| `version-sync` | `launcher.py:~911` | implemented | ja | Versionskonsistenz |
| `secret-init/set/list/health/rotate/export/import` | `SecondBrain/secret_manager/` | implemented | offen | Vault |
| `native-startup-enable/disable/status` | `launcher.py:~970` | implemented | offen | Autostart |

### Fehlend auf `main`

| Kommando | Gefordert in | Status |
|---|---|---|
| `postgres-live-gate` | Prompt 68 | missing |
| `live-certification` | Prompt 69 | missing |
| `disaster-recovery-gate` | Prompt 71 | missing |
| `windows-installer-gate` | Prompt 74 | missing |
| `support-bundle` | Prompt 75 | missing |
| `jarvis-1.0-gate` | Prompt 76 | missing |

---

## 3. Persistenz

| Capability | Codepfad | Status | Live-Nachweis |
|---|---|---|---|
| Task Repository (PostgreSQL) | `SecondBrain/tasks/repository.py:41` `PostgresTaskRepository` | implemented | **nein** |
| Task JSONL→Repo-Migration | `SecondBrain/tasks/repository.py:153` | implemented | **nein** |
| Produktions-Guard gegen JSONL | `SecondBrain/tasks/repository.py:136` `jsonl_not_allowed_in_production` | implemented | **nein** |
| Review/Approval Repository (PostgreSQL) | `SecondBrain/repositories/postgres_review_approval_repository.py` | implemented | **nein** |
| Review/Approval Repository (JSONL) | `SecondBrain/repositories/jsonl_review_approval_repository.py` | implemented | ja (Dev) |
| Approval PostgreSQL Live Gate | `SecondBrain/release/approval_postgres_live_gate.py` | implemented_not_certified | **nein** |
| pgvector / KPI Store | `SecondBrain/rag/postgres_kpi_store.py` | partially_implemented | **nein** |

`PostgresTaskRepository` verwendet `FOR UPDATE` mit SQLite-Dialektausnahme (Zeile 69) — Concurrency-Absicherung ist vorhanden, aber unbelegt.

---

## 4. Job-Runtime

| Capability | Codepfad | Status | Live-Nachweis |
|---|---|---|---|
| Job Models / Repository / Service | `SecondBrain/jobs/{models,repository,service}.py` | implemented | offen |
| Job Worker | `SecondBrain/jobs/worker.py` | implemented | offen |
| Job Monitoring | `SecondBrain/jobs/monitoring.py` | implemented | offen |
| Job GUI | `SecondBrain/jobs/gui.py` | implemented | offen |
| Job Surface (Desktop) | `SecondBrain/desktop_native/job_surface.py` | implemented | offen |
| Migration aller Langläufer | — | partially_implemented | nein |

**Offene Lücke:** Ob alle Langläufer (Reindex, Embedding Rebuild, Graph Extraction, Großimporte, Connector Sync, Backup/Restore, OCR) tatsächlich über diese Runtime laufen, ist nicht erhoben. Das ist Gegenstand von Prompt 70 Phase 1.

---

## 5. Connectoren

| Capability | Codepfad | Status | Live-Nachweis |
|---|---|---|---|
| Adapter Contract / Lifecycle | `SecondBrain/connectors/adapter_{contract,lifecycle}.py` | implemented | offen |
| Connector Registry | `SecondBrain/connectors/connector_registry.py` | implemented | offen |
| Cursor Store | `SecondBrain/connectors/cursor_store.py` | implemented | **nein** |
| Delta Sync | `SecondBrain/connectors/delta_sync.py` | implemented | **nein** |
| Dead Letter Queue | `SecondBrain/connectors/dead_letter{,_store}.py` | implemented | offen |
| Conflict Detection / Resolution | `SecondBrain/connectors/conflict_*.py` | implemented | offen |
| Connector E2E Gate | `launcher.py:179` | implemented_not_certified | **nein** |
| Live-Connector-Anbindung Desktop | `SecondBrain/desktop_native/external_action_connectors.py` (PR #116) | implemented | **nein** |

---

## 6. Desktop

| Capability | Codepfad | Status | Live-Nachweis |
|---|---|---|---|
| Qt-Shell (PySide6) | `SecondBrain/desktop_native/qt_shell.py` | implemented | **nein** |
| Action Bus / Registry | `SecondBrain/desktop_native/action_{bus,registry}.py` | implemented | offen |
| Navigation | `SecondBrain/desktop_native/navigation.py` (PR #78) | implemented | offen |
| Approval Surface | `SecondBrain/desktop_native/approval_surface.py` (PR #79) | implemented | offen |
| Job Surface | `SecondBrain/desktop_native/job_surface.py` (PR #80) | implemented | offen |
| Task Surface + Filter/Archiv/Restore | `SecondBrain/desktop_native/task_surface.py` (PR #112–#114) | implemented | offen |
| System Tray | `SecondBrain/desktop_native/tray.py` (PR #69) | implemented | **nein** |
| Lifecycle / Single Instance | `SecondBrain/desktop_native/lifecycle.py` (PR #68) | implemented | **nein** |
| Windows Autostart | PR #70 | implemented | **nein** |
| Health/Alert/Storage/Metrics Surfaces | `SecondBrain/desktop_native/{health,alert,storage_alerts,system_metrics}*.py` (PR #84–#92) | implemented | offen |
| Vault Surface | `SecondBrain/desktop_native/vault_surface.py` (PR #86) | implemented | offen |

**Kritischer Befund:** `qt_shell.py` importiert PySide6, aber **PySide6 ist in keiner `requirements*.txt` und nicht in `pyproject.toml` deklariert.** Auf einer sauberen Installation startet die Qt-Shell nicht. Das blockiert Prompt 74 (Installer) unmittelbar.

---

## 7. Voice

| Capability | Codepfad | Status | Live-Nachweis |
|---|---|---|---|
| Voice Runtime | `SecondBrain/desktop_native/voice_runtime.py` | implemented | **nein** |
| Deutsche Sprachsteuerung | `SecondBrain/desktop_native/voice_de.py` | implemented | **nein** |
| STT + Policy | `SecondBrain/desktop_native/stt.py` (PR #65) | implemented | **nein** |
| TTS + Safety | `SecondBrain/desktop_native/tts.py` (PR #66) | implemented | **nein** |
| Wake Word (lokal) | PR #67, PR #71 | implemented | **nein** |
| Hotkey / Mikrofon | `SecondBrain/desktop_native/{hotkey,microphone}.py` | implemented | **nein** |
| Voice Command Router | `SecondBrain/voice/command_router.py` | implemented | offen |
| Native Voice App Gate | `SecondBrain/desktop_native/native_voice_app_gate.py` | implemented_not_certified | **nein** |

Kein Voice-Nachweis ist ohne Audiohardware führbar. Alle Einträge bleiben bis zum Live-Lauf auf der Zielmaschine unbelegt.

---

## 8. Secret Vault und Backup

| Capability | Codepfad | Status | Live-Nachweis |
|---|---|---|---|
| Secret Manager (Crypto) | `SecondBrain/secret_manager/crypto.py` | implemented | offen |
| Secret Audit | `SecondBrain/secret_manager/audit.py` | implemented | offen |
| Secret Redaction | `SecondBrain/secret_manager/redaction.py` | implemented | offen |
| Secret Health | `SecondBrain/secret_manager/health.py` | implemented | offen |
| Secret Policy | `SecondBrain/desktop/settings/security/secret_policy.py` | implemented | offen |
| Backup | `SecondBrain/backup.py` | implemented | offen |
| Backup Verification | `SecondBrain/backup_verification.py` | implemented | offen |
| Backup/Restore Test | `SecondBrain/backup_restore_test.py` | implemented | offen |
| Windows Credential Manager Backend | — | missing | nein |
| Restore-Rollback / Atomarität | — | partially_implemented | nein |

---

## 9. Installer und Verteilung

| Capability | Codepfad | Status | Live-Nachweis |
|---|---|---|---|
| PyInstaller Spec | `packaging/windows/jarvis.spec` | implemented | **nein** |
| WiX MSI | `packaging/windows/jarvis.wxs` | implemented | **nein** |
| Inno Setup | `packaging/windows/installer.iss` | implemented | **nein** |
| Build-Skript | `packaging/windows/build.ps1` | implemented | **nein** |
| Installer Smoke | `packaging/windows/installer_smoke.ps1` | implemented | **nein** |
| Bootstrap | `packaging/windows/jarvis_bootstrap.py` | implemented | **nein** |
| Updater Runtime | `SecondBrain/installer_update/runtime.py` | implemented | **nein** |
| Release Pipeline mit Secret-Sperrliste | `SecondBrain/install/release_pipeline.py:15` | implemented | offen |
| Code Signing | — | missing | nein |
| Uninstall | `uninstall_jarvis.ps1` | implemented | **nein** |

Der Installerbau ist deutlich weiter als vom Masterplan angenommen. Verifiziert ist er nicht.

---

## 10. CI

| Workflow | Pfad | Status |
|---|---|---|
| Pull Request Validation | `.github/workflows/pull-request.yml` | implemented |
| Main Validation | `.github/workflows/main-validation.yml` | implemented |
| Nightly | `.github/workflows/nightly.yml` | implemented |
| Release Candidate | `.github/workflows/release-candidate.yml` | implemented |
| Release | `.github/workflows/release.yml` | implemented |
| Security | `.github/workflows/security.yml` | implemented |
| SecondBrain CI | `.github/workflows/secondbrain-ci.yml` | implemented |

---

## 11. Strukturelle Befunde außerhalb des Prompt-Umfangs

Diese Punkte verletzen die Projektregeln „keine parallelen Subsysteme" und „keine technischen Schulden" und sollten vor weiteren Feature-Paketen entschieden werden.

### 11.1 Fünf parallele Planner-Implementierungen

```
SecondBrain/agent/planner.py
SecondBrain/agent/planning/planner.py
SecondBrain/agent/task_planner.py
SecondBrain/autonomous_planner.py
SecondBrain/planner_v2/service.py      <- trägt die v31.16-Parallelisierung
```

Nur `planner_v2/service.py` enthält Ressourcen-Locks und die Regel, dass approval-pflichtige Knoten seriell bleiben. Welche der übrigen vier produktiv sind, ist unklar. Kandidaten für `deprecated`.

### 11.2 Doppelte Voice-Implementierung

```
SecondBrain/desktop_native/voice_de.py
SecondBrain/native/voice_de.py
```

Zwei Pfade mit gleichem Dateinamen. Prompt 73 fordert ausdrücklich „nur erweitern, nicht parallel neu bauen" — dafür muss zuerst geklärt werden, welcher der beiden der aktive ist.

### 11.3 PySide6 nicht deklariert

Siehe Abschnitt 6. Blockiert jeden Installer- und Desktop-Nachweis.

### 11.4 `auto.crt` war versioniert

Bereinigt im Commit `48f6361`. `SecondBrain/install/release_pipeline.py:15` führt `auto.crt` und `auto.key` in `FORBIDDEN_NAMES` — die Datei stand also im Widerspruch zur eigenen Auslieferungsregel.

---

## 12. Zusammenfassung Live-Nachweise

| Bereich | Implementiert | Live zertifiziert |
|---|---|---|
| CI / Repo-Hygiene / Security | ja | ja |
| RAG / P1 | ja | ja |
| Approval (JSONL, Dev) | ja | ja |
| Approval (PostgreSQL) | ja | **nein** |
| Task-/Projekt-Persistenz (PostgreSQL) | ja | **nein** |
| pgvector | teilweise | **nein** |
| Provider (OpenAI/Ollama) | ja | **nein** |
| Connectoren E2E | ja | **nein** |
| Job-Runtime | ja | **nein** |
| Desktop Qt-Shell | ja | **nein** |
| Voice | ja | **nein** |
| Backup / Restore | ja | **nein** |
| Secret Vault | ja | **nein** |
| Windows Installer | ja | **nein** |

**Kernaussage:** Der Implementierungsstand ist erheblich weiter als dokumentiert. Der Zertifizierungsstand ist es nicht. Für Jarvis 1.0 fehlt fast durchgehend nicht Code, sondern belastbarer Live-Nachweis auf der Zielumgebung.

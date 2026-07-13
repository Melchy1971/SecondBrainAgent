# Umsetzungsbericht: GUI, RuntimeConfig, Observability, Import-Pipeline, Klassifizierung

Stand: 2026-07-09. Fünf Arbeitspakete, sequenziell umgesetzt, jeweils mit Tests.

## 1. Zentrale Runtime-Konfiguration (`secondbrain/runtime_config/`)

Prioritätenkette (hoch → niedrig): `os.environ` → `<workspace>/.env` → `<workspace>/config.json` → `<AppData>/config/config.json` (via `install.app_home`: `JARVIS_HOME` > `%APPDATA%\Jarvis` > `~/.jarvis`) → `runtime/gui/settings.json` (nur lesend, Legacy) → dokumentierte Defaults (`schema.py`).

Eigenschaften: Secrets stehen in JSON-Quellen ausschließlich als Referenz `{"ref": "ENV_NAME"}`; Werte kommen nur aus environ/.env. Rohwerte in JSON werden gemeldet und ignoriert. Pfad-Keys (`SECONDBRAIN_VAULT_DIR`, `SECONDBRAIN_INBOX_DIR`) sind workspace-relativ — keine hart codierten lokalen Pfade. Fehlende Pflichtwerte (`required_if`, z. B. `OPENAI_API_KEY` bei Provider `openai`, `DATABASE_URL` bei Store `pgvector`) erzeugen Status **BLOCKED** mit benannten Blockern. Schreiben: Nicht-Secrets → `config.json` (Scope workspace|appdata), Secrets → `.env` (Kommentare bleiben erhalten), maskierte Secrets werden nie überschrieben.

CLI (Launcher): `config-status`, `config-snapshot`, `config-set KEY=WERT [--scope]`, `config-doctor` (Exit 1 bei BLOCKED). GUI und CLI nutzen dieselbe Klasse.

Tests: `tests/test_runtime_config.py` (17) — Prioritäten je Ebene, Secret-Referenzen, BLOCKED-Fälle, .env-Roundtrip mit Kommentarerhalt, Validierungsfehler, relpath-Auflösung.

## 2. GUI-Überarbeitung + Einstellungen in Bereichen

Die produktive Shell (`native/ai_workspace/gui.py`, Start: `python launcher.py native-gui`):

- Modul „Settings Center": statt JSON-Dump jetzt `SettingsEditorFrame` (`native/settings_workspace_panel.py`) — editierbar, gegliedert in *KI/Embedding, Datenbank/Speicher, GUI/Allgemein, Sprache/Voice, Pfade/Workspace, Sicherheit/Secrets*; je Feld Typ-Widget (Dropdown/Checkbox/maskiertes Secret-Feld), Herkunftsanzeige (env/.env/config.json/Default), Beschreibung, Pflicht-Markierung, BLOCKED-Banner, Speichern/Neu laden.
- `_render_active_module` tabellengetrieben refaktoriert (vorher: sechsfach dupliziertes pack_forget-Muster).
- Neue Module: **Audit Viewer** (`observability`), **Import Historie** (`import_history`), **Tag Editor** (`tags`).
- Zweitfläche `native/app.py` komplett überarbeitet: ttk-Theme aus `secondbrain/ui`-Tokens (dark/light, umschaltbar, persistiert über `SECONDBRAIN_GUI_THEME`), strukturierte Treeview-Ansichten statt JSON-Dumps in allen Tabs, Statuskarten, Config-BLOCKED-Banner, Chat-Antwortformatierung, Audit-JSON-Export; Einstellungen-Tab bettet denselben `SettingsEditorFrame` ein (DRY).

## 3. Observability (`secondbrain/observability/`)

`ids` (cor_/job_/plan_/sync_-Präfixe), `redaction` (Pattern- + schlüsselbasierte Maskierung, baut auf `safe_logging` auf), `taxonomy` (Fehlerkategorien: configuration, network, provider, storage, parsing, permission, timeout, validation, resource, unknown; Gruppierung), `structured_log` (JSONL `runtime/observability/logs.jsonl`), `audit_store` (append-only, Query, JSON-Export), `health_timeline` (Status je Komponente, Gesamtzustand = schlechtester Einzelstatus), `service.track_action()` (ein Aufruf → Audit + Log + Health).

Integriert: `NativeActionDispatcher._finalize` (jede native Agent-Aktion), Import-Pipeline (alle Stufen/Fehler), sensitive Inhalte aus der Klassifikation. GUI: Audit Viewer mit Filtern, Health-Zeile, kritischen Events, Fehlergruppen, Export.

Tests: `tests/test_observability.py` (10).

## 4. Einheitliche Import-Pipeline (`secondbrain/import_pipeline/`)

Eine `ImportJob`-Entität für lokale Dateien (`submit_file`) und Connector-Inhalte (`submit_text` bzw. `submit_file` mit `connector=`) — identischer Verarbeitungspfad. Statusmodell: `queued → parsing → classified → chunked → embedded → indexed`; Terminal: `indexed | failed→dead_letter | duplicate | ocr_required | rejected`; ergänzt um Review-Status (`review_required`, `failed_reviewable`, `review_deferred`). ParserRegistry (`document_understanding`) durchgängig; `ParseStatus.OCR_REQUIRED` wird als eigener Wartestatus abgebildet (requeue-fähig). Duplicate Detection über SHA-256-Content-Index. Retry bis `max_attempts`, danach Dead Letter; manuelles Requeue setzt Versuche zurück. Partial Failure: `process_batch` verarbeitet weiter, Parserfehler blockieren die Queue nicht. Source Lineage je Job (Quelle, Connector, Sync-ID, Hash, Correlation-ID). Indexierung inkrementell je Dokument über `P1RagRuntime.ingest_text` (Indexer injizierbar). GUI: Import-Historie mit Statusfilter, Stufenverlauf, Retry, „Offene verarbeiten".

Tests: `tests/test_import_pipeline.py` (11).

## 5. Dokumentklassifizierung (`secondbrain/classification/`)

Regelbasierte Basisklassifikation (deutsch, deterministisch, erklärbar über `matched_markers`): rechnung, vertrag, protokoll, task, projekt, prozess, person, quelle, wissen, inbox — mit Tag-Vorschlägen und Confidence (0.3–0.9). PII-/Secret-Erkennung (IBAN, E-Mail, Telefon, Kreditkarte, Steuer-ID, API-Keys, Private Keys, Vertraulichkeitsmarker) → Tag `sensibel` + Audit-Event. Optionale LLM-Klassifikation injizierbar; überstimmt Regeln nur bei höherer Confidence, Fehler degradieren still zu Regeln. Confidence < 0.6 → Review Queue. Manuelle Korrekturen im GUI Tag Editor überschreiben Vorschläge nachvollziehbar (Tag-Historie append-only: alt→neu, source=manual, Editor). Import-Pipeline nutzt die Engine automatisch.

Tests: `tests/test_classification.py` (11, inkl. Pipeline-Integration).

## Verifikationsstand

- Sandbox (Linux, Python 3.10 + Kompatibilitäts-Shim): 90+ Tests grün über alle betroffenen Suiten; ruff clean auf allen neuen/geänderten Dateien.
- Zwei bekannte Sandbox-Artefakte (kein Codefehler): `review_inbox` braucht tkinter (in der Sandbox nicht installierbar); ein Alt-Test nutzt Windows-Pfade (`D:/CustomVault`).
- **Offen bis zum fehlerfreien Live-Lauf auf deinem Rechner (Python 3.13):**
  1. `python -m pytest -q` (volle Suite)
  2. `python launcher.py config-doctor`
  3. `python launcher.py native-gui` — Sichtprüfung: Einstellungen (Bereiche, Speichern, BLOCKED-Banner), Audit Viewer, Import Historie, Tag Editor, Theme-Wechsel
  Erst danach gilt die Abnahme nach deinem Standard.

## Hinweise

- `pyproject.toml` und `launcher.py` wurden inhaltsgleich neu geschrieben (Sandbox-Sync-Reparatur) — funktional unverändert bis auf die neuen `config-*`-Kommandos.
- Alt-Flächen (`gui/settings_center.py`, `gui/persistent_settings.py`) bleiben unangetastet (eigene Tests, `desktop/app.py`-Abhängigkeit); Ablösung als separater Cleanup empfohlen.
- Das native View-Model liefert `settings` jetzt als RuntimeConfig-Snapshot (`secondbrain.runtime_config.v1`) plus `config_status`; die Assertion in `test_v3026` wurde entsprechend angepasst.

## Nachtrag: paralleler Umbau der Import-Pipeline (im Flug)

Während der Abschlussverifikation hat eine parallele Sitzung `import_pipeline/models.py` und
`import_pipeline/pipeline.py` erweitert (UnifiedReviewInbox aus `agent/review_service.py`,
Review-Hold-Status `review_required`/`failed_reviewable`/`review_deferred`/`rejected`,
`document_id`, Blockierungs-Flags). Stand bei Sitzungsende:

- `pipeline.py` ruft `_classification_review`, `_review_was_approved`, `_hold_for_review`
  auf, die **noch nicht definiert sind** — der Parallel-Edit ist unfertig. Nicht mergen/starten,
  bevor diese Methoden existieren.
- `tests/test_classification.py::test_pipeline_classifies_and_routes_low_confidence_to_review`
  prüft die bisherige Route (niedrige Confidence -> `classification.ReviewQueue`) und ist durch
  die Umleitung auf die UnifiedReviewInbox rot. Nach Abschluss des Parallel-Umbaus auf die
  Inbox-Route anpassen oder die ReviewQueue-Route wiederherstellen — eine Entscheidung, nicht beides.
- Alle übrigen Suiten der fünf Arbeitspakete: grün (68+ Tests in der Sandbox; volle Suite
  auf Windows ausstehend).

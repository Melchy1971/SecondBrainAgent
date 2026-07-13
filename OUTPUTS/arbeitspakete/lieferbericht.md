# Lieferbericht: 4 Arbeitspakete

Stand: 2026-07-08. Alle Änderungen direkt in `secondbrain/`. Gesamttest der neuen
Suiten: 50 passed. Lint (`ruff`) sauber. Sandbox-Python 3.10; siehe Umgebungshinweis.

## Reihenfolge / Abhängigkeiten
Embeddings -> Secret Vault -> Connector Runtime (Tokens im Vault) -> Dokumentcenter.

## Task 1 - Embedding-Provider (Analyse + Härtung Alt-Stack)
Detailanalyse: `OUTPUTS/embedding-provider-analyse/embedding-provider-analyse.md`.
Kurz: drei Embedding-Ebenen im Repo; der produktive p1-Gate-Pfad war bereits
gehärtet, der Alt-Stack `secondbrain/rag/providers/` nicht. Gehärtet:
- `deterministic_provider.py` als DEV_ONLY (`production_ready=False`), Fallback-Framing entfernt.
- `factory.py` fail-closed: kein stiller `deterministic`-Default; DEV_ONLY in Production geblockt.
- `openai_/ollama_/gemini_embedding_provider.py`: Live-`health()` = FAIL statt Fake; Dimension-Contract.
- neu `health.py` (`embedding_production_gate`), `base.py` (Health-Report, validate_dimensions/model, reindex-Identität).
- Tests: `tests/rag/providers/test_hardening.py` (18). Gesamt mit Alt-Suiten 60 passed.

## Task 2 - Secret Vault (`secondbrain/vault/`)
- AES-256-GCM (`cryptography`), Envelope-Keys: Master-Key (KEK) aus Env/Passphrase/Keyfile, DEKs KEK-gewrappt.
- `store.py`: put/get, Workspace-Isolation (AES-GCM AAD), Secret-Referenzen `secret://ws/name`, DEK-Rotation (re-encrypt), KEK-Rewrap, verschlüsselter Import/Export.
- `redaction.py`: Werte-, Muster- und Key-Namen-Redaction; in `safe_logging.py` verdrahtet.
- `migration.py`: Klartext aus `secrets.local.yaml` und `.env` -> Vault + Referenzen (mit `.env`-Backup).
- `health.py`: Canary-Decrypt + Klartext-Leak-Scan (meldet Dateinamen + Secret-Name, nie den Wert).
- `audit.py`: append-only, ohne Werte. GUI: `secondbrain/gui/secret_manager_panel.py` (nicht-blockierend).
- Tests: `tests/vault/test_vault.py` (16): Verschlüsselung, Rotation, Redaction, Migration, Isolation, Health, Import/Export.

Akzeptanz: keine Secrets im Log/JSON-Report (Redaction + `list_secrets` ohne Werte + Audit ohne Werte);
Nutzung nur über Referenzen; Tests vorhanden.

## Task 3 - Connector Runtime (`secondbrain/connector_runtime/`)
- Connectoren: lokaler Ordner (voll real, mtime-inkrementell), Gmail/Drive/Calendar/GitHub (echte Parsing-/Cursor-Logik, injizierbarer Transport-Client).
- `oauth.py`: `VaultTokenProvider` - Tokens liegen ausschließlich im Vault (Task 2).
- `runtime.py`: Registry, Cursor-Store, Import-Job-Lifecycle (queued/running/succeeded/partial/failed), Audit, Reindex-Hook nach Sync, Source-Status fresh/stale/error.
- `resilience.py`: Retry/Backoff (honoriert `retry_after`), Token-Bucket-Rate-Limit, Dead-Letter-Queue.
- GUI: `center.py` (`build_panel`, nicht-blockierend).
- Tests: `tests/connectors/test_connector_runtime.py` (11): Dokumenterzeugung, simulierte API-Fehler (Rate-Limit-Retry, Auth, transient erschöpft -> DLQ, permanent), Status-Übergänge, Reindex-Hook, Job-Lifecycle, Tokens nie außerhalb des Vaults.

## Task 4 - Dokumentcenter (`secondbrain/document_center/`)
Baut auf `document_understanding.parsers` (liefert bereits kontrollierte Fehlerzustände).
- `core.py`: `PreviewBuilder` (Text/Markdown/PDF/Bild/Office/Error), OCR-Status (`OcrStatus`), `ImportQueue` (Mehrfachimport, nicht-blockierender Worker-Thread), `JobMonitor`, `TagStore`, `DocumentHistory`.
- `center.py`: Service + Controller + Tk-Panel mit Drag&Drop-Mehrfachimport, nicht-blockierende Vorschau.
- Tests: `tests/document_center/test_document_center.py` (7): Mehrfachimport, PDF/MD/TXT/Bild-Preview (echte Dateien), kontrollierter Error-State bei defekter Datei, Job-Monitor-Status, Tags+History, Async ohne Blockieren.

## Umgebungshinweis (wichtig für Abnahme)
- Sandbox-Interpreter ist Python 3.10; die p1-/launcher-Tests importieren `datetime.UTC` (>=3.11) und wurden hier nicht ausgeführt. Die neuen Pakete sind 3.10-kompatibel und laufen grün.
- Neue harte Abhängigkeit: `cryptography>=42` (bereits in `requirements-security.txt`).
- Standard "Abnahme erst bei fehlerfreiem Live-Lauf": vollständige Suite bitte einmal unter deinem Python >=3.11 laufen lassen.

## Offener Punkt
Drei parallele Embedding-Stacks bleiben bestehen (nur Alt-Stack gehärtet, wie freigegeben).
Konsolidierung als separates Arbeitspaket empfohlen.

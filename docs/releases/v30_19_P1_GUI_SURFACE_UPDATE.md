# v30.19 P1 GUI Surface Update

## Ziel
Alle P0/P1 Runtime-Neuerungen aus v30.6 bis v30.18 in die bestehende GUI-Oberfläche einhängen, bevor weitere Backend-Entwicklung erfolgt.

## Umgesetzt
- Neuer P1 Control Panel Adapter mit allen relevanten Runtime-Aktionen.
- Desktop Views ergänzt: `rag-import`, `rag-index`, `p1-control`, `production`, `settings-p1`.
- Settings Center um Embedding-/Store-/Security-Konfiguration erweitert.
- RAG Explorer um Import Center und Vector Index Center erweitert.
- Production Dashboard um P1 Gate/Provider/Vector/Golden-Sektionen erweitert.
- Schreibende und destruktive Aktionen werden als confirmation-required markiert.

## Validierung
- `pytest -q tests/test_v3019_gui_p1_surface.py tests/desktop/test_app.py` → PASS.
- `pytest --collect-only -q` → geprüft.

## Offen
- Volltest ohne Sandbox-Timeout.
- Live-VPS pgvector Migration/Audit.
- Produktive Connector Runtime.
- Secret Vault/Encryption.

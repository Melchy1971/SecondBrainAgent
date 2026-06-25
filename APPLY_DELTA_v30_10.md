# Delta v30.10 — P1 Parser Ingest Hardening

## Ziel
P1-RAG-Ingest verarbeitet Dateien nicht mehr nur als Erfolg/Fehler, sondern liefert für alle Parserzustände ein strukturiertes Parse-Event. Damit werden PDF/OCR-, JSON-, CSV-, EML- und Unsupported-Fehler im End-to-End-RAG-Pfad sichtbar und gate-fähig.

## Dateien kopieren
Repository-Root: `SecondBrain-Agent/`

```text
SecondBrain-Agent/launcher.py
SecondBrain-Agent/secondbrain/p1_rag_runtime.py
SecondBrain-Agent/secondbrain/module_registry.py
SecondBrain-Agent/tests/test_v3010_p1_parser_ingest_hardening.py
SecondBrain-Agent/docs/09_MASTERPLAN_STATUS.json
```

## Neu
- `P1_PARSE_EVENT_SCHEMA = secondbrain.p1_parse_event.v1`
- `P1RagRuntime.ingest_file()` liefert `parse` auch bei blockierten Parserzuständen.
- `ocr_required` wird nicht verschluckt, sondern als `requires_ocr` und `metadata.ocr_required` ausgewiesen.
- `P1RagRuntime.ingest_directory()` ergänzt Batch-Import-Diagnose.
- Neuer Launcher-Befehl: `p1-rag-ingest-dir`.
- ModuleRegistry kennt `p1-rag-ingest-dir`.

## Validierung
```bash
python -m pytest -q tests/test_v3010_p1_parser_ingest_hardening.py tests/test_v180_p1_rag.py
```

Erwartung:
```text
13 passed
```

## Offene Punkte nach v30.10
- Vollständiger `pytest -q` außerhalb Sandbox-Timeout.
- Live-VPS pgvector Migration/Audit.
- Production Gate mit echten Store-/Provider-Thresholds weiter verschärfen.
- Connector Runtime/OAuth.
- Secret Vault/Encryption.

# v30.95 — Security Hardening

Stand: 2026-07-14  
Branch: `feature/v30.95-security-hardening`

## Release Notes

- Zentrale, deterministische Erkennung für Ignore-Previous-, System-Override-, Jailbreak-, Hidden-Markdown-, HTML/XML-, Tool- und Function-Override-Muster.
- `PromptRiskLevel`, inhaltsminimierter `PromptRiskReport` und `PromptSanitizer` erweitern die bestehende Security-Komponente.
- Dokument-, Memory- und Workspace-Kontext wird als unvertrauenswürdige Evidenz statt als Systemnachricht an Provider übergeben.
- RAG-Chunks tragen `trusted`, `untrusted` oder `sanitized`; eingebettete Agenten-, Tool- und externe Aktionsanweisungen werden neutralisiert.
- Parser lehnen Traversal, Symlinks, übergroße Dateien/JSON-Strukturen, ZIP-Bomben, Archive Traversal, zu tiefe Archive und übergroße PDF/PST-Verarbeitung kontrolliert ab.
- Neues lokales Gate: `python launcher.py security-gate`.

## Security Report

Status des lokalen v30.95 Security Gates: **PASS** (`9/9`, keine Blocker).

| Bereich | Kontrolle | Erwartung |
| --- | --- | --- |
| Prompt | acht Injection-Familien, Zero-Width-Text, System-Boundary | PASS |
| RAG | Steueranweisung, externe Aktion, Tool Override, Trust Label | PASS |
| Parser | Traversal, JSON-Tiefe, ZIP Ratio, Archive Traversal | PASS |

Der Report wurde atomar und ohne Rohangriffstexte nach `runtime/reports/v30_95_security_gate.json` geschrieben. Keine Prüfung benötigt Netzwerk, LLM oder Connector-Credentials.

Security-Gate-Zusammenfassung:

- Prompt Injection: PASS
- RAG Injection: PASS
- Parser Hardening: PASS
- Dokumentinhalt in Systemnachricht: nicht vorhanden
- Externe Dienste oder Credentials verwendet: nein

## Sicherheitsregeln

- Dokument- und RAG-Inhalte sind Daten, keine Instruktionen.
- Direkte Benutzeraktionen bleiben möglich; externe Seiteneffekte werden weiterhin ausschließlich durch die bestehende Approval Policy autorisiert.
- Sanitization ersetzt keine Tool-Freigabe und verändert keine persistente Approval-Bindung.
- Parser validieren Ressourcenbudgets vor beziehungsweise während iterativer Extraktion.
- Security-Audit und Gate speichern nur Regelcodes, Zähler und Hashes, keine Prompt- oder Dokumentinhalte.

## Testreport

Auszuführende Befehle:

```text
python launcher.py security-gate
python -m pytest -q tests/test_security_hardening_gate.py
python -m pytest -q tests/unit/test_security_v107.py tests/test_v3074_prompt_pipeline.py tests/test_prompt_builder.py
python -m pytest -q tests/test_p1_1_5_context_builder.py
python -m pytest -q tests/test_p1_3_2_concrete_document_parsers.py tests/test_p1_3_4_parser_orchestrator.py tests/test_v3010_p1_parser_ingest_hardening.py
```

Tatsächliche Resultate:

| Prüfung | Ergebnis |
| --- | --- |
| `python launcher.py security-gate` | PASS, 9/9 Checks |
| Isolierte v30.95 Hardening-Regression | 60 passed |
| Plugin Trust und Read-only Connector | 17 passed |
| Phase 2 Prompt/Security | 25 passed |
| Phase 3 Prompt/RAG | 35 passed |
| Phase 4 Parser/Ingestion | 22 passed |
| DOCX-Kompatibilität plus Parser | 13 passed |
| Ruff für alle geänderten Python-Dateien | PASS |
| `py_compile` für Runtime-Dateien und Launcher | PASS |
| Vollständige Suite, Lauf vor DOCX-Kompatibilitätsfix | 2.086 passed, 173 failed, 10 skipped |

Die 173 Fehler der Vollsuite liegen überwiegend im auf `main` bereits inkonsistenten Review-/Approval-/Runtime-Stand, darunter `ApprovalRequest`-Feldabweichungen, Tool-Registry-Vertragstests, Workflow-/Notification-/Unified-Inbox-Folgetests sowie provider- und konfigurationsabhängige Tests. Ein durch die neue DOCX-Preflight-Reihenfolge sichtbar gewordener Kompatibilitätsfehler wurde anschließend behoben und mit 13/13 Parser-/Kompatibilitätstests grün bestätigt; die komplette Suite wurde danach nicht erneut ausgeführt. Ein zusätzlicher GUI-Test scheitert lokal an einer unvollständigen Tcl/Tk-Installation (`tk8.6/msgs/de.msg` fehlt), nicht am Security Change.

Release-Empfehlung: **Keinen nächsten Sprint beginnen**, bis die bestehenden Suite-Blocker auf dem Integrationsstand bereinigt oder als explizite Baseline akzeptiert sind. Das isolierte v30.95 Security Gate selbst ist freigabefähig.

## Bekannte Grenzen

- Pattern-basierte Erkennung reduziert bekannte lokale Injection-Klassen, ist aber kein formaler Beweis gegen jede zukünftige semantische Umschreibung.
- Python-Plugins laufen nach expliziter Trust-Freigabe weiterhin im Hauptprozess; Prozess-Sandboxing ist ausdrücklich nicht Teil dieses Sprints.
- Parserbudgets begrenzen Arbeit im Prozess, erzwingen jedoch kein hartes Betriebssystem-CPU-Limit für native Drittbibliotheken.
- Direkte User-Anfragen nach Tools werden nicht als Dokument-Injection behandelt; Mandatory Approval bleibt dafür die maßgebliche Kontrollschicht.
- Die Repository-Gesamtsuite ist auf diesem Branch nicht grün; der Security-Gate-PASS ist daher keine Freigabe des gesamten Produkts.

## Rollback

1. Gate-Aufruf aus `launcher.py` entfernen.
2. RAG-Trust-Metadaten und Parser-Preflights zurücknehmen.
3. Prompt-Layer-Rollen nur gemeinsam mit den zugehörigen Regressionstests zurücksetzen.
4. Approval-/Connector-/Plugin-Sicherheitslogik bleibt von diesem Rollback unberührt.

## Commit-Vorschläge

```text
docs(security): document current local assistant attack surface
feat(security): neutralize prompt and rag instruction injection
fix(parser): enforce document resource and archive limits
test(security): add v30.95 local security gate
```

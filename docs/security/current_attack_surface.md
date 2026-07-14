# Current Attack Surface — v30.95

Stand: 2026-07-14  
Scope: produktive lokale RAG-, Import-, Agent-, Connector- und Plugin-Pfade.

## Bewertungsmaßstab

| Priorität | Bedeutung |
| --- | --- |
| P0 | Direkter Kontrollverlust, unfreigegebene externe Aktion oder lokale Ressourcenerschöpfung |
| P1 | Manipulation von Agentenantworten, Datenabfluss oder Umgehung einer Trust Boundary |
| P2 | Defense-in-depth, eingeschränkte Wirkung oder bereits vorhandene Primärkontrolle |

## Komponenten und Trust Boundaries

| Komponente | Produktiver Pfad | Angriffsfläche | Trust Boundary | Risiko | Priorität |
| --- | --- | --- | --- | --- | --- |
| Prompt Builder | `secondbrain/chat/context/prompt_pipeline.py` | System-, Workspace-, Memory-, Goal-, Dokument-, Provider- und User-Layer; vorherige Chatnachrichten | Unvertrauenswürdiger Benutzer-/Dokumenttext → Provider-Request | `DocumentPrompt` und `MemoryPrompt` erben aktuell die Systemrolle. Eingebettete Anweisungen können dadurch mit höherer Autorität erscheinen; Hidden Markdown, HTML/XML und Tool-/Function-Override werden nicht bewertet. | P0 |
| RAG Context Builder | `secondbrain/rag/context_builder.py` | Suchtreffer, Chunk-Text und Metadaten externer/importierter Dokumente | Index/Connector/Ingestion → Prompt-Kontext | Chunks werden nur normalisiert, dedupliziert und budgetiert. Ein Dokument kann Agentensteuerung, externe Aktionen oder manipulierte Tool Calls enthalten; es existiert kein `trusted`/`untrusted`/`sanitized`-Label. | P0 |
| Dokumentparser | `secondbrain/document_understanding/parsers.py`, `orchestrator.py` | Text, JSON/JSONL, CSV, E-Mail/PST, PDF, DOCX/XLSX, Bilder | Lokales Dateisystem/Connector-Datei → Parserprozess | Text ist auf 25 MiB begrenzt, aber Symlinks, PDF-Seiten, PDF-Größe, JSON-Komplexität, ZIP-Kompressionsverhältnis und rekursive Container sind nicht zentral begrenzt. PST-Rekursion ist unbeschränkt. Fehlertexte können Parserdetails enthalten. | P0 |
| Import/RAG Ingestion | `secondbrain/p1_rag_runtime.py`, `secondbrain/import_pipeline/pipeline.py` | Pfade, Quellen, Parserresultate, Chunks, Embeddings | Dateisystem/Review Queue → Langzeitspeicher/Index | Pfade werden auf Existenz und Dateityp geprüft, aber nicht gegen Symlinks oder Ressourcenbomben. Review Governance reduziert sensible Weitergabe, verhindert jedoch keine Parser-DoS. | P1 |
| Connector Runtime | `secondbrain/connectors_v13/runtime.py`, moderne Connector-Runtimes | OAuth-Tokens, Webhooks, Delta-Daten, externe Antworten, Schreibaktionen | Externe Dienste/Netzwerk → lokaler Store und Agent | Externe Inhalte sind unvertrauenswürdig und können Prompt-Injection tragen. Moderne Schreibpfade sind approval-gebunden; der Legacy-V13-Pfad besitzt keine Inhaltsklassifizierung und sollte nur als Datenquelle gelten. | P1 |
| Tool Registry / Executor | `secondbrain/agent/tool_registry.py`, `safe_executor.py` | Toolname, Payload, Scopes, persistente Approvals, Handler | Agentenplan → lokale/externe Seiteneffekte | Mandatory Approval, Payload-Bindung und `confirmed=True`-Bypass-Schutz sind vorhanden. Verbleibendes Risiko: manipulierte Inhalte können die Planung beeinflussen, bevor die Registry die konkrete Aktion blockiert. | P1 |
| Agent Planner | `secondbrain/agent/task_planner.py`, `planner.py` | Intent, Kontext, Tool-Mapping, Planpayload | Prompt/RAG/Memory → ausführbarer Plan | Das Zustandsmodell unterstützt Approval/Resume, trägt aber keine Herkunfts- oder Prompt-Risikokennzeichnung. Unvertrauenswürdiger Text kann einen riskanten Plan vorschlagen; die Tool-Policy bleibt letzte Schutzschicht. | P1 |
| Plugin Loader | `secondbrain/plugins/loader.py`, `sandbox.py`, `permissions.py` | Manifest, Entry Point, Python-Modul, deklarierte/granted Permissions | Pluginverzeichnis → Codeausführung im Hauptprozess | Aktivierung erfordert explizites Trust-Listing, Pfadauflösung und Permission Policy. Nach Aktivierung läuft Plugin-Code jedoch im Prozess; ein vertrautes, kompromittiertes Plugin kann CPU/Memory blockieren oder Python-Rechte missbrauchen. | P1 |
| Audit/History | `prompt_pipeline.py`, Tool-/Approval-Audit | Prompt-Metadaten, redaktierte Historie, Fehlermeldungen | Laufzeitdaten → persistente Logs | Prompt-Audit speichert nur Hashes, History nutzt Redaction. Parser- und Pluginfehler können weiterhin unkontrollierte Detailtexte enthalten; Injection-Befunde werden noch nicht separat auditiert. | P2 |

## Priorisierte Maßnahmen

1. **P0 — Prompt Boundary:** Unvertrauenswürdige Dokument-/Memory-Inhalte nie als Systemanweisung behandeln; zentrale Pattern-Erkennung, Sanitization und fail-closed Behandlung kritischer Befunde.
2. **P0 — RAG Boundary:** Jeden Chunk klassifizieren, riskante Steueranweisungen neutralisieren und Trust-Status in Chunk-Metadaten erhalten.
3. **P0 — Parser Boundary:** Symlinks und Traversal ablehnen; komprimierte Container, PDF-Seiten, Dateigröße, JSON-Tiefe und Iterationen hart begrenzen.
4. **P1 — Defense in Depth:** Tool-/Approval-Policy unverändert als letzte Autorisierungsgrenze beibehalten; Prompt-Risiko darf niemals eine Freigabe ersetzen.
5. **P1 — Gate:** Regressionssuite muss Injection, RAG-Manipulation und Parserbomben deterministisch und ohne externe Dienste prüfen.

## Bestehende wirksame Kontrollen

- Tool Registry ignoriert einfache `approved`-/`confirmed`-Booleans und verlangt persistente, payload-gebundene Freigaben.
- Mandatory Approval schützt destructive/external writes auch bei falscher Toolkonfiguration.
- Plugin Loader verlangt explizit vertraute Plugins; Entry Points werden auf den Plugin-Root begrenzt und Permissions getrennt geprüft.
- Prompt Audit speichert Hashes statt Rohprompts; Prompt History und Approval-Payloads verwenden bestehende Redaction.
- Import Review und Memory Governance blockieren sensible Weitergabe, sind jedoch keine Parser- oder Prompt-Injection-Abwehr.

## Nicht-Ziele dieses Sprints

- Kein separater Prozess-/Container-Sandbox für Python-Plugins.
- Keine neue Connector-, Agent- oder RAG-Architektur.
- Keine semantische LLM-basierte Malware-Erkennung; alle Gate-Prüfungen bleiben lokal und deterministisch.

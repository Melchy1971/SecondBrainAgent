# PATCH P1.3.4 - Parser Orchestration

## Ziel
Multi-Format-Parser zentral orchestrieren, damit Import, Connector-Bridge und UI nicht direkt gegen einzelne Parserklassen koppeln.

## Geändert
- `secondbrain/document_understanding/orchestrator.py`
  - `MultiFormatParserOrchestrator`
  - `ParserSelection`
  - `ParseOrchestrationResult`
  - MIME-/Extension-basierte Parserauswahl
  - deterministische Fehlerzustände statt Exception-Leaks
  - `default_multi_format_orchestrator()` mit Text, Markdown, JSON, CSV, EML, PDF/OCR-Fassade
- `secondbrain/document_understanding/__init__.py`
  - öffentliche Exporte ergänzt
- `tests/test_p1_3_4_parser_orchestrator.py`
  - Extension-Auswahl
  - MIME-Priorität
  - Unsupported-State
  - Exception-Isolation
  - Warnungen für sehr kurze Texte

## Validierung
- Delta-Test: `5 passed`

## Risiko
Niedrig. Neue Orchestrierung ist additiv und bricht bestehende Parser-APIs nicht.

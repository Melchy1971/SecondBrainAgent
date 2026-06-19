# SecondBrain-Agent FINAL v1.0 Masterplan

## Architekturentscheidungen

| Bereich | Entscheidung |
|---|---|
| Betriebsmodell | vollständig plattformunabhängig |
| KI-Provider | ChatGPT, Claude, Gemini, Perplexity, Ollama |
| Synchronisation | mehrere gleichzeitig |
| Datenbank | Markdown-only |
| Wissensgraph | vollständiger Knowledge Graph mit Gewichtungen |
| E-Mail | Gmail, Outlook, IONOS, IMAP; Import und Analyse |
| Dokumente | PDF, Office, Bilder/OCR, Audio, Video, ZIP, CAD, Code |
| Browser | Chrome, Edge, Firefox |
| Mobile | später |
| Automation | Level 5 |
| Sicherheit | API-Key-Management |
| Benutzer | Team-/Mehrbenutzerbetrieb |

## Systemprinzip

Markdown bleibt Source of Truth.

Alle sekundären Strukturen werden aus Markdown erzeugt:

- Graph
- Index
- Dashboard
- Empfehlungen
- Digest
- Reports
- Review Queue

## Implementierungsgrenze v1.0

v1.0 enthält:
- finale Zielstruktur
- lauffähigen Markdown-Agent-Kern
- Importpipeline
- Konfiguration
- Platzhalter-Module für alle Zielbereiche
- API-Key-Management-Struktur
- Teamstruktur
- Weighted Graph
- Recommendations
- Dashboard
- Betriebsdokumentation

Nicht vollständig produktiv enthalten:
- echte API-Anbindung an alle Provider
- vollständige OCR-Pipeline
- echte Browser-History-Extraktion
- CAD-Parser
- vollständiger IMAP-Client
- mobile App

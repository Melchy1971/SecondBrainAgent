---
title: "Jarvis"
type: chatgpt_conversation
source: chatgpt
source_id: "6a22b309-3398-838d-8c9b-da8c67026a4d"
created: 2026-06-05
tags:
  - chatgpt
  - code
  - gesundheit
  - import
  - ki
  - obsidian
  - projekt
  - sap
  - verein
---


# Jarvis

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6a22b309-3398-838d-8c9b-da8c67026a4d`
- Nachrichten: 56

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Jarvis. Das ist mein aktueller Code. analysire ihn und finde Fehler.

### 2. Assistent

Ich prüfe die ZIP statisch: Projektstruktur, Abhängigkeiten, Startpunkte, Konfiguration, offensichtliche Laufzeitfehler, Sicherheitsrisiken und Architekturbrüche. Danach liefere ich priorisierte Fehlerliste mit konkreten Fixes.

### 3. Assistent

Erster harter Befund: Die ZIP enthält `.venv`, `.git`, Logdateien und echte API-Keys. Das ist kein Codepaket, sondern ein Runtime-Abzug mit Secrets.

### 4. Assistent

Analyse abgeschlossen.

## Kritische Fehler

1. **API-Keys im Paket**
   - `config/api_keys.json` enthält echte Gemini- und OpenRouter-Keys.
   - Risiko: Kostenmissbrauch, Account-Sperre, Datenabfluss.
   - Maßnahme: Keys sofort rotieren, Datei löschen, nur `api_keys.example.json` committen.

2. **ZIP enthält `.venv`, `.git`, Logs**
   - Paketgröße: ca. 1,35 GB entpackt.
   - Fehlerbild: langsam, unsaubere Deployments, fremde Pfade, unnötige Abhängigkeiten.
   - Maßnahme: `.venv/`, `.git/`, `jarvis.log`, Modelle und Runtime-Dateien nie exportieren.

3. **Viele Tools sind nur Platzhalter**
   Beispiele:
   - `google_calendar.py`: gibt nur `"Google Calendar synced and updated."` zurück.
   - `web_search.py`: keine echte Suche.
   - `scheduler.py`: speichert keine Aufgabe.
   - `morning_brief.py`: kein echter Briefing-Prozess.
   - `arca_invoice.py`: kein Invoice-Processing.

4. **Tool-Versprechen ≠ Tool-Funktion**
   - In `main.py` wird dem Modell gesagt: „Nutze Tools, simuliere nie.“
   - Mehrere Tools simulieren aber Ergebnisse.
   - Folge: Jarvis wirkt erfolgreich, obwohl nichts passiert.

5. **Fehlende harte Null-Prüfung**
   Beispiel:
   ```python
   elif name == "google_calendar":
       r = await loop.run_in_executor(... google_calendar(...))
   ```
   Wenn Import fehlschlägt, ist `google_calendar = None` → Runtime-Crash.

6. **Gefährliche Selbständerungs- und Terminalfunktionen**
   Gefunden:
   - `terminal_agent`
   - `self_edit`
   - `auto_programmer`
   - `tool_creator`
   - `subprocess`
   - `eval`
   - `exec`
   - `shell=True`
   
   Risiko: Jarvis kann Code ausführen, Dateien ändern, Tools erzeugen. Ohne Sandbox/Allowlist ist das ein Sicherheitsproblem.

7. **Encoding-Probleme**
   Viele Texte zeigen kaputte Zeichen:
   - `â€”`
   - `Ã³`
   - `ðŸ”§`
   
   Ursache: UTF-8 falsch interpretiert. Folge: UI/Logs/Prompts wirken kaputt.

8. **Startmodell vermutlich fragil**
   ```python
   LIVE_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
   ```
   Preview-/Datumsmodell. Risiko: Modellname nicht verfügbar → Startfehler.

9. **Windows-only Architektur**
   Starke Kopplung an:
   - `pyautogui`
   - `pywinauto`
   - `comtypes`
   - `pycaw`
   - `win10toast`
   - `.bat`, `.vbs`
   
   Auf Linux/VPS/Docker nicht lauffähig.

10. **Kein Testsystem**
   - Keine `tests/`
   - Keine Tool-Contract-Tests
   - Keine Smoke-Tests
   - Keine CI
   - Keine Mock-Konfiguration

## Positiv

- Syntaxprüfung über alle `.py`-Dateien: bestanden.
- Projektstruktur ist grundsätzlich modular.
- `requirements.txt` existiert.
- `.gitignore` enthält bereits wichtige Regeln, wurde aber beim Export offenbar nicht konsequent angewendet.

## Priorität Fix-Reihenfolge

1. API-Keys rotieren.
2. Sauberes Repo-Paket erstellen ohne `.venv`, `.git`, Logs, echte Configs.
3. Alle Platzhalter-Tools entweder entfernen oder als `NOT_IMPLEMENTED` markieren.
4. Tool-Dispatch mit Null-Checks absichern.
5. Terminal-, Self-Edit- und Tool-Creator-Funktionen per Allowlist absichern.
6. Encoding auf UTF-8 normalisieren.
7. Smoke-Test bauen: Import, Start, Tool-Registry, Config-Load.
8. Erst danach neue Funktionen erweitern.

### 5. Benutzer

liefere Prompts zum weiterentwickeln oder besser erstelle mir einen passenden Masterplan und karkiere was bereits implementiert ist.

### 6. Assistent

Ich erstelle einen Masterplan auf Basis des aktuellen ZIP-Stands, nicht generisch. Ergebnis: Umsetzungsphasen, Statusmarkierung je Modul, Risiken, Gates und direkt nutzbare Entwicklungs-Prompts.

### 7. Assistent

Erstellt: [Jarvis_Masterplan.md](sandbox:/mnt/data/Jarvis_Masterplan.md)

Inhalt:
- Implementierungsstatus je Modul
- Sicherheitsrisiken
- Zielarchitektur
- Phasenplan
- Qualitäts-Gates
- konkrete Entwicklungs-Prompts
- empfohlene Reihenfolge

Nächster Schritt: Prompt 1 ausführen: Clean Repo, Secrets entfernen, saubere ZIP bauen.

### 8. Benutzer

entwickle

### 9. Assistent

Ich entwickle direkt im vorhandenen Codepaket weiter. Schwerpunkt zuerst: Sicherheitsbasis, saubere Paketstruktur, stabile Tool-Registry, Smoke-Tests und ausführbarer Entwicklungsstand als neue ZIP.

### 10. Assistent

Ich korrigiere jetzt nicht primär Features, sondern die Tragfähigkeit: Secrets raus, Platzhalter transparent machen, Tool-Aufrufe gegen fehlende Module absichern, Scheduler/Websuche minimal realisieren, Tests und Doku ergänzen.

### 11. Assistent

Entwickelt und gepackt:

[Jarvis_developed_v1.zip](sandbox:/mnt/data/Jarvis_developed_v1.zip)

Umgesetzt:
- Secrets entfernt
- Config-Loader ergänzt
- Tool-Runtime-Guard ergänzt
- Websuche minimal realisiert
- Scheduler persistent gemacht
- Terminal-Agent im Safe Mode blockiert
- Tool-Creator deaktiviert
- Dummy-Tools als `NOT_IMPLEMENTED` markiert
- Smoke-Test ergänzt
- Entwicklungsstatus dokumentiert

Validierung grün:
```text
PASS test_no_real_secrets
PASS test_python_files_compile
PASS test_declared_tools_have_modules_or_builtin_handler
```

### 12. Assistent

Verstanden.

Ab jetzt liefere ich nur noch Entwicklungs-Prompts für Claude Code, Cursor oder Gemini, bis ausdrücklich eine ZIP-Datei angefordert wird.

Da dein aktueller Jarvis-Stand bereits eine Grundstruktur besitzt, sollte die Weiterentwicklung in dieser Reihenfolge erfolgen:

# Prompt 01 – Tool Registry zentralisieren

```text
Aufgabe:

Analysiere das gesamte Projekt.

Ziel:
Alle Tools dürfen nur noch über eine zentrale Registry registriert werden.

Implementiere:

1. Neue Datei:
core/tool_registry.py

2. Klasse:
ToolRegistry

Methoden:
- register_tool()
- unregister_tool()
- get_tool()
- list_tools()
- validate_tools()

3. Jeder Tool-Import muss über die Registry erfolgen.

4. Entferne harte Tool-Zuweisungen aus main.py.

5. Beim Start:

registry.validate_tools()

6. Fehlerhafte Tools dürfen Jarvis nicht stoppen.

7. Fehlende Tools als:

{
  "status": "unavailable",
  "reason": "module_not_loaded"
}

melden.

8. Dokumentiere:
docs/architecture/tool_registry.md

Akzeptanzkriterien:

- Jarvis startet auch bei defekten Tools.
- Toolliste wird dynamisch erzeugt.
- Keine Hardcodierung mehr in main.py.
```

---

# Prompt 02 – Event Bus einführen

```text
Aufgabe:

Implementiere ein zentrales Event-System.

Neue Datei:

core/event_bus.py

Events:

USER_MESSAGE
ASSISTANT_RESPONSE
TOOL_STARTED
TOOL_FINISHED
TOOL_FAILED
MEMORY_CREATED
MEMORY_UPDATED
TASK_CREATED

Implementiere:

EventBus

Methoden:

subscribe()
unsubscribe()
publish()

Ziel:

Module dürfen nicht direkt miteinander kommunizieren.

Kommunikation nur über Events.

Dokumentation:

docs/architecture/event_bus.md
```

---

# Prompt 03 – Langzeitgedächtnis V1

```text
Aufgabe:

Implementiere echtes Langzeitgedächtnis.

Neue Struktur:

memory/
├── short_term/
├── long_term/
├── episodic/
├── semantic/

Funktionen:

save_memory()
search_memory()
update_memory()
delete_memory()

Regeln:

- Gesprächszusammenfassungen automatisch speichern.
- Fakten getrennt von Konversationen speichern.
- JSON-Struktur verwenden.

Erstelle:

memory_manager.py

Dokumentation:

docs/memory_system.md
```

---

# Prompt 04 – Aufgabenmanager V2

```text
Aufgabe:

Ersetze den bisherigen Scheduler.

Neue Datei:

modules/task_manager.py

Funktionen:

create_task()
update_task()
delete_task()
list_tasks()
complete_task()

Speicherung:

data/tasks.json

Zusätzlich:

- Priorität
- Fälligkeitsdatum
- Tags
- Status

Status:

pending
running
completed
cancelled

Dokumentation:

docs/task_system.md
```

---

# Prompt 05 – RAG-System vorbereiten

```text
Aufgabe:

Implementiere Dokumentensuche V1.

Neue Struktur:

knowledge/
├── documents/
├── embeddings/
├── index/

Implementiere:

document_importer.py
document_search.py

Unterstützte Formate:

- PDF
- TXT
- MD

Verwende:

sentence-transformers

Erzeuge:

- Dokumentindex
- Embeddings
- Metadaten

Dokumentation:

docs/rag_system.md
```

---

# Prompt 06 – Agent Framework

```text
Aufgabe:

Implementiere Agentenarchitektur.

Neue Struktur:

agents/

Basisagent:

BaseAgent

Agenten:

PlannerAgent
ResearchAgent
MemoryAgent
TaskAgent
SystemAgent

Fähigkeiten:

- Ziele annehmen
- Teilaufgaben erzeugen
- Ergebnisse zurückmelden

Kommunikation ausschließlich über EventBus.

Dokumentation:

docs/agents.md
```

---

# Prompt 07 – Persönlichkeits-Engine

```text
Aufgabe:

Implementiere persistente Persönlichkeit.

Neue Datei:

personality/profile.json

Eigenschaften:

- Name
- Rolle
- Kommunikationsstil
- Interessen
- Vorlieben

Neue Klasse:

PersonalityManager

Funktionen:

load_profile()
save_profile()
update_profile()

Der Systemprompt muss dynamisch daraus erzeugt werden.

Dokumentation:

docs/personality.md
```

---

# Prompt 08 – Voice-System neu aufbauen

```text
Aufgabe:

Refaktorisiere Sprachsystem.

Module:

voice_input.py
voice_output.py

Provider:

- Whisper
- FasterWhisper
- ElevenLabs
- Windows TTS

Konfigurierbar über:

config/voice.json

Implementiere Fallback-Logik.

Dokumentation:

docs/voice_system.md
```

---

# Prompt 09 – Plugin-System

```text
Aufgabe:

Implementiere echtes Plugin-System.

Neue Struktur:

plugins/

Jedes Plugin enthält:

plugin.json

Beispiel:

{
  "name": "",
  "version": "",
  "entrypoint": ""
}

Jarvis soll Plugins automatisch erkennen.

Methoden:

load_plugin()
unload_plugin()

Dokumentation:

docs/plugin_system.md
```

---

# Prompt 10 – Jarvis V2 Architektur-Gate

```text
Aufgabe:

Analysiere das gesamte Projekt.

Prüfe:

- Architektur
- Sicherheit
- Tool-System
- Speicherverwaltung
- Agentensystem
- Logging
- Konfiguration
- Performance

Erstelle:

docs/reports/v2_architecture_report.md

Bewerte jede Kategorie:

0–100 Punkte

Für jede Schwachstelle:

- Ursache
- Risiko
- Fix
- Aufwand

Definiere anschließend den Masterplan für V3.
```

Diese Reihenfolge baut Jarvis von einem Tool-Wrapper zu einem echten lokalen Agentensystem mit Gedächtnis, Aufgabenverwaltung, RAG und Multi-Agenten-Architektur aus.

### 13. Benutzer

liefer mir nur noch die Promts und keine Zip Datei mehr bis ich es sage

### 14. Benutzer

weiter entwickeln

### 15. Assistent

# Prompt 11 – Konfigurationssystem stabilisieren

```text
Aufgabe:

Refaktorisiere das komplette Konfigurationssystem.

Ziel:
Jarvis darf keine festen Pfade, Keys, Modellnamen oder Provider-Werte mehr im Code enthalten.

Implementiere:

1. Neue Struktur:

config/
├── app.example.json
├── providers.example.json
├── voice.example.json
├── security.example.json
├── paths.example.json

2. Neue Datei:

core/config_manager.py

3. Klasse:

ConfigManager

Methoden:
- load_config()
- get()
- set()
- validate()
- create_missing_from_examples()

4. Regeln:

- Echte Config-Dateien dürfen nicht versioniert werden.
- Fehlende Configs werden aus Example-Dateien erzeugt.
- Secrets dürfen nie geloggt werden.
- Ungültige Configs erzeugen klare Fehlermeldungen.
- Jarvis muss mit leerer Erstinstallation starten können.

5. Entferne alle Hardcodings aus:
- main.py
- provider-Dateien
- voice-Dateien
- tool-Dateien

6. Dokumentation:

docs/configuration.md

Akzeptanzkriterien:

- Start ohne echte Config möglich.
- Keine Secrets im Repository.
- Alle Provider sind konfigurierbar.
- Tests für Config-Validierung vorhanden.
```

# Prompt 12 – Logging und Audit-System

```text
Aufgabe:

Ersetze das aktuelle Logging durch ein strukturiertes Logging- und Audit-System.

Neue Dateien:

core/logger.py
core/audit_log.py

Logging-Level:

DEBUG
INFO
WARNING
ERROR
CRITICAL

Audit-Events:

TOOL_CALL
CONFIG_CHANGE
TASK_CHANGE
MEMORY_CHANGE
FILE_ACCESS
SECURITY_BLOCK

Regeln:

- Keine API-Keys loggen.
- Keine kompletten User-Prompts ungefiltert loggen.
- Jeder Tool-Aufruf erhält eine request_id.
- Fehler werden mit Stacktrace in Debug-Logs gespeichert.
- User-Ausgabe bleibt kurz und verständlich.

Speicherorte:

logs/app.log
logs/error.log
logs/audit.log

Dokumentation:

docs/logging_audit.md

Akzeptanzkriterien:

- Jeder Tool-Aufruf ist nachvollziehbar.
- Fehler sind reproduzierbar.
- Secrets werden maskiert.
```

# Prompt 13 – Provider-Abstraktion für KI-Modelle

```text
Aufgabe:

Implementiere eine saubere Provider-Schicht.

Neue Struktur:

providers/
├── base_provider.py
├── gemini_provider.py
├── openrouter_provider.py
├── ollama_provider.py
├── provider_factory.py

BaseProvider definiert:

- chat()
- stream_chat()
- validate_connection()
- list_models()

Regeln:

- main.py darf keinen Provider direkt importieren.
- Providerwahl erfolgt nur über config/providers.json.
- Fallback-Provider möglich.
- Fehler eines Providers stoppen Jarvis nicht.
- Provider-Antworten werden normalisiert.

Response-Format:

{
  "status": "ok|error",
  "provider": "",
  "model": "",
  "content": "",
  "usage": {},
  "error": null
}

Dokumentation:

docs/providers.md

Akzeptanzkriterien:

- Gemini, OpenRouter und Ollama sind austauschbar.
- Providerfehler werden sauber behandelt.
- Tests mit MockProvider vorhanden.
```

# Prompt 14 – Sicherheits-Gate für gefährliche Aktionen

```text
Aufgabe:

Implementiere ein zentrales Security-Gate.

Neue Datei:

core/security_gate.py

Zu kontrollierende Aktionen:

- Terminal-Befehle
- Dateischreibzugriffe
- Datei-Löschungen
- Self-Edit
- Plugin-Erstellung
- Netzwerkzugriffe
- Zugriff auf Secrets

Security-Modi:

SAFE
CONFIRM
ADMIN

Regeln:

SAFE:
- keine Shell-Ausführung
- keine Self-Edit-Funktion
- keine Löschung außerhalb data/

CONFIRM:
- gefährliche Aktionen erzeugen Approval-Request

ADMIN:
- erlaubt, aber vollständig auditiert

Implementiere:

check_permission()
require_approval()
block_action()

Dokumentation:

docs/security_model.md

Akzeptanzkriterien:

- Kein subprocess ohne Security-Gate.
- Kein Dateischreibzugriff ohne Pfadprüfung.
- Jeder Block wird auditiert.
```

# Prompt 15 – Fehler- und Statusmodell vereinheitlichen

```text
Aufgabe:

Führe ein einheitliches Result-Objekt für alle Module ein.

Neue Datei:

core/result.py

Struktur:

{
  "ok": true|false,
  "status": "",
  "data": {},
  "error": {
    "code": "",
    "message": "",
    "details": {}
  },
  "meta": {
    "request_id": "",
    "timestamp": "",
    "duration_ms": 0
  }
}

Regeln:

- Keine freien String-Rückgaben mehr aus Tools.
- Alle Tools geben Result zurück.
- Alle Provider geben Result zurück.
- Scheduler, Memory und RAG geben Result zurück.

Fehlercodes:

CONFIG_ERROR
TOOL_UNAVAILABLE
VALIDATION_ERROR
SECURITY_BLOCKED
PROVIDER_ERROR
IO_ERROR
NOT_IMPLEMENTED

Dokumentation:

docs/result_model.md

Akzeptanzkriterien:

- Einheitliche Fehlerbehandlung.
- main.py braucht keine Sonderlogik pro Tool.
- Tests für Erfolgs- und Fehlerfälle vorhanden.
```

# Prompt 16 – UI/API-Trennung vorbereiten

```text
Aufgabe:

Trenne Jarvis-Kernlogik von Benutzeroberfläche.

Neue Struktur:

app/
├── core_app.py
├── cli_app.py
├── api_app.py

core_app.py:
- initialisiert Config
- initialisiert Provider
- initialisiert ToolRegistry
- initialisiert EventBus
- stellt process_message() bereit

cli_app.py:
- Terminal-Interface

api_app.py:
- FastAPI-Server

API-Endpunkte:

POST /chat
GET /status
GET /tools
GET /tasks
GET /memory/search

Regeln:

- main.py wird nur noch Startpunkt.
- Keine Businesslogik in main.py.
- API darf keine Secrets ausgeben.

Dokumentation:

docs/runtime_architecture.md

Akzeptanzkriterien:

- Jarvis läuft per CLI.
- Jarvis läuft per API.
- Kernlogik ist identisch.
```

# Prompt 17 – Testbasis erweitern

```text
Aufgabe:

Baue eine robuste Teststruktur auf.

Neue Struktur:

tests/
├── unit/
├── integration/
├── smoke/
├── fixtures/

Tests für:

- ConfigManager
- ToolRegistry
- EventBus
- Result-Modell
- SecurityGate
- ProviderFactory
- TaskManager
- MemoryManager

Zusätzlich:

pytest.ini

Befehle:

pytest tests/smoke
pytest tests/unit
pytest tests/integration

Regeln:

- Keine echten API-Calls in Tests.
- Keine echten Secrets.
- MockProvider verwenden.
- Temporäre Testdaten unter tmp_path.

Akzeptanzkriterien:

- Smoke-Tests grün.
- Unit-Tests grün.
- CI-fähig.
```

# Prompt 18 – Entwicklungsdokumentation aktualisieren

```text
Aufgabe:

Aktualisiere die Projektdokumentation.

Erstelle oder aktualisiere:

README.md
docs/setup.md
docs/development.md
docs/security.md
docs/architecture.md
docs/known_limitations.md
docs/changelog.md

README muss enthalten:

- Zweck von Jarvis
- aktueller Status
- Installation
- Start per CLI
- Start per API
- Konfiguration
- Sicherheitsmodell
- bekannte Einschränkungen

known_limitations.md muss ehrlich markieren:

- echte Funktion
- Teilfunktion
- Dummy
- geplant
- blockiert

Akzeptanzkriterien:

- Neue Entwickler verstehen Projektstart.
- Keine falschen Feature-Versprechen.
- Aktueller Implementierungsstand ist sichtbar.
```

# Prompt 19 – V2 Gate Report

```text
Aufgabe:

Führe nach Umsetzung der Prompts 11 bis 18 ein V2-Gate durch.

Erstelle:

docs/reports/v2_gate_report.md

Bewerte mit 0–100 Punkten:

1. Sicherheit
2. Konfiguration
3. Architektur
4. Tool-System
5. Provider-System
6. Testbarkeit
7. Fehlerbehandlung
8. Dokumentation
9. Erweiterbarkeit
10. Betriebsfähigkeit

Für jede Kategorie:

- Score
- Befund
- Risiko
- notwendiger Fix
- Aufwand

Definiere Ergebnis:

GO
GO_WITH_RESTRICTIONS
NO_GO

Akzeptanzkriterien:

- Kein GO bei offenen Secrets.
- Kein GO bei unkontrolliertem subprocess.
- Kein GO bei fehlenden Smoke-Tests.
```

# Prompt 20 – V3 Masterplan erzeugen

```text
Aufgabe:

Erstelle nach V2-Gate einen Masterplan für Jarvis V3.

Datei:

docs/masterplan_v3.md

Inhalte:

1. Zielbild V3
2. Abgrenzung V2 zu V3
3. Funktionscluster
4. Architekturentscheidungen
5. Datenmodell
6. Agentenmodell
7. Pluginmodell
8. RAG-Ausbau
9. Lokale Automation
10. Risiken
11. Priorisierte Roadmap
12. Akzeptanzkriterien

Markiere jeden Punkt als:

IMPLEMENTED
PARTIAL
PLANNED
BLOCKED
DEPRECATED

Akzeptanzkriterien:

- Masterplan basiert auf tatsächlichem Code.
- Keine Wunschliste ohne Umsetzungslogik.
- Jede Phase hat messbare Gates.
```

### 16. Benutzer

weiter

### 17. Assistent

# Prompt 11 – Konfigurationssystem härten

```text
Aufgabe:

Refaktorisiere das gesamte Konfigurationssystem.

Ziel:
Keine hartcodierten Pfade, Keys, Modelle oder Provider mehr.

Implementiere:

config/
├── default.json
├── local.example.json
├── schema.json

Neue Datei:
core/config_manager.py

Funktionen:
- load_config()
- validate_config()
- get_config_value()
- reload_config()

Regeln:
- local.json darf nicht committet werden.
- Fehlende Pflichtwerte erzeugen klare Fehler.
- Secrets dürfen niemals geloggt werden.
- ENV-Variablen überschreiben JSON-Werte.

Akzeptanzkriterien:
- Jarvis startet mit default.json.
- Jarvis erkennt fehlende Secrets sauber.
- Keine echten Keys im Repository.
- docs/configuration.md existiert.
```

# Prompt 12 – Logging standardisieren

```text
Aufgabe:

Ersetze verstreute print-Ausgaben durch strukturiertes Logging.

Neue Datei:
core/logger.py

Anforderungen:
- Log-Level: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log-Ausgabe in Konsole und Datei
- Rotation nach Dateigröße
- Secrets automatisch maskieren
- Tool-Aufrufe mit request_id protokollieren

Ersetze:
print()

durch:
logger.info()
logger.warning()
logger.error()

Akzeptanzkriterien:
- Keine unkontrollierten print-Ausgaben in Core-Modulen.
- Logs enthalten Zeitstempel, Modul, Level, request_id.
- API-Keys werden maskiert.
- docs/logging.md existiert.
```

# Prompt 13 – Error Handling vereinheitlichen

```text
Aufgabe:

Implementiere zentrales Fehlerhandling.

Neue Datei:
core/errors.py

Fehlerklassen:
- JarvisError
- ConfigError
- ToolError
- ToolUnavailableError
- SecurityError
- MemoryError
- ProviderError

Jeder Fehler braucht:
- code
- message
- details
- recoverable: true/false

Regeln:
- Keine rohen Exceptions an User ausgeben.
- Stacktraces nur im Debug-Log.
- User erhält verständliche Fehlermeldung.

Akzeptanzkriterien:
- Tool-Fehler stoppen Jarvis nicht.
- Fehler sind maschinenlesbar.
- docs/error_handling.md existiert.
```

# Prompt 14 – Provider-Abstraktion für KI-Modelle

```text
Aufgabe:

Erstelle eine Provider-Schicht für LLMs.

Neue Struktur:
providers/

Provider:
- BaseProvider
- GeminiProvider
- OpenRouterProvider
- OllamaProvider

Funktionen:
- generate()
- stream_generate()
- validate_connection()
- list_models()

Regeln:
- main.py darf keinen konkreten Provider direkt kennen.
- Provider-Auswahl erfolgt über config.
- Fallback-Provider möglich.

Akzeptanzkriterien:
- Jarvis kann zwischen Gemini, OpenRouter und Ollama wechseln.
- Fehlerhafte Provider werden sauber gemeldet.
- docs/providers.md existiert.
```

# Prompt 15 – Sicherheits-Gate für gefährliche Aktionen

```text
Aufgabe:

Implementiere Security-Gate für alle riskanten Aktionen.

Neue Datei:
core/security_gate.py

Riskante Aktionen:
- Terminal-Befehle
- Dateiänderungen
- Codegenerierung
- Plugin-Installation
- Netzwerkzugriffe
- Tool-Erstellung

Implementiere:
- classify_action_risk()
- require_confirmation()
- enforce_allowlist()
- block_action()

Risikostufen:
- LOW
- MEDIUM
- HIGH
- CRITICAL

Regeln:
- CRITICAL wird standardmäßig blockiert.
- HIGH braucht explizite Freigabe.
- Terminalbefehle nur per Allowlist.

Akzeptanzkriterien:
- Kein subprocess ohne Security-Gate.
- Kein Datei-Schreibzugriff ohne Policy-Prüfung.
- docs/security_gate.md existiert.
```

# Prompt 16 – Testsuite V1 aufbauen

```text
Aufgabe:

Baue eine echte Testsuite.

Neue Struktur:
tests/
├── unit/
├── integration/
├── smoke/

Tests für:
- ConfigManager
- ToolRegistry
- EventBus
- MemoryManager
- TaskManager
- ProviderManager
- SecurityGate

Nutze pytest.

Zusätzlich:
- pytest.ini
- requirements-dev.txt

Akzeptanzkriterien:
- pytest läuft ohne externe API-Keys.
- Smoke-Test prüft Jarvis-Start.
- Defekte Tools brechen Tests nicht unkontrolliert.
- docs/testing.md existiert.
```

# Prompt 17 – CLI-Modus ergänzen

```text
Aufgabe:

Implementiere einen stabilen CLI-Modus.

Neue Datei:
cli.py

Funktionen:
- jarvis chat
- jarvis tools
- jarvis tasks
- jarvis memory
- jarvis config-check
- jarvis doctor

Nutze argparse oder typer.

Akzeptanzkriterien:
- Jarvis ist ohne GUI nutzbar.
- config-check validiert Konfiguration.
- doctor prüft Systemzustand.
- docs/cli.md existiert.
```

# Prompt 18 – Healthcheck und Doctor-System

```text
Aufgabe:

Implementiere Systemdiagnose.

Neue Datei:
core/doctor.py

Prüfungen:
- Python-Version
- Abhängigkeiten
- Config-Dateien
- Schreibrechte
- Tool-Verfügbarkeit
- Provider-Verbindung
- Memory-Pfade
- Task-Datei
- Security-Policy

Ausgabe:
- OK
- WARNING
- ERROR

Akzeptanzkriterien:
- jarvis doctor liefert klare Diagnose.
- Fehler enthalten Fix-Hinweise.
- docs/doctor.md existiert.
```

# Prompt 19 – Dokumentation aktualisieren

```text
Aufgabe:

Erstelle konsistente Projektdokumentation.

Dateien:
README.md
docs/architecture.md
docs/setup.md
docs/development.md
docs/security.md
docs/roadmap.md
docs/status.md

README muss enthalten:
- Zweck
- Installation
- Start
- Konfiguration
- Architekturüberblick
- Sicherheitswarnungen
- aktueller Entwicklungsstand

Akzeptanzkriterien:
- Neue Entwickler können Jarvis lokal starten.
- Keine veralteten Feature-Versprechen.
- Nicht implementierte Features sind klar markiert.
```

# Prompt 20 – V2 Stabilitätsgate

```text
Aufgabe:

Führe ein vollständiges Stabilitätsgate durch.

Prüfe:
- Startfähigkeit
- Imports
- Tests
- Konfiguration
- Security
- Tool-Registry
- Provider
- Memory
- Tasks
- Logging
- Dokumentation

Erstelle:
docs/reports/stability_gate_v2.md

Bewertung:
- Kategorie
- Status: PASS / WARNING / FAIL
- Risiko
- Fix
- Priorität

Akzeptanzkriterium:
Jarvis erhält nur PASS, wenn keine kritischen Sicherheits- oder Startfehler bestehen.
```

### 18. Assistent

# Prompt 21 – GUI entkoppeln

```text
Aufgabe:

Entkopple GUI vollständig von Core-Logik.

Ziel:
GUI darf keine Businesslogik, Tool-Logik oder Providerlogik enthalten.

Neue Struktur:
ui/
├── desktop/
├── cli/
├── web/
└── shared/

Regeln:
- UI ruft nur Application Services auf.
- Kein direkter Zugriff auf Tools.
- Kein direkter Zugriff auf Config-Dateien.
- Kein direkter Zugriff auf Memory-Dateien.

Erstelle:
core/application_service.py

Funktionen:
- send_message()
- execute_tool()
- list_tools()
- get_status()

Akzeptanzkriterien:
- Core läuft ohne GUI.
- CLI und GUI nutzen dieselbe Service-Schicht.
- docs/ui_architecture.md existiert.
```

# Prompt 22 – Application Service Layer

```text
Aufgabe:

Implementiere eine klare Application-Service-Schicht.

Neue Struktur:
services/

Services:
- ChatService
- ToolService
- MemoryService
- TaskService
- ProviderService
- HealthService

Regeln:
- main.py orchestriert nur noch.
- Services kapseln Use Cases.
- Services geben standardisierte Result-Objekte zurück.

Result-Objekt:
{
  "success": true,
  "data": {},
  "error": null,
  "metadata": {}
}

Akzeptanzkriterien:
- Keine Geschäftslogik mehr in main.py.
- Jeder Service ist einzeln testbar.
- docs/services.md existiert.
```

# Prompt 23 – Result-Pattern einführen

```text
Aufgabe:

Führe ein einheitliches Result-Pattern ein.

Neue Datei:
core/result.py

Klasse:
Result

Felder:
- success: bool
- data: dict | list | str | None
- error: dict | None
- metadata: dict

Methoden:
- ok()
- fail()
- to_dict()

Regeln:
- Tools geben nie rohe Strings zurück.
- Services geben immer Result zurück.
- Fehler laufen über core/errors.py.

Akzeptanzkriterien:
- Alle Tool- und Service-Rückgaben sind standardisiert.
- Tests prüfen Result-Format.
- docs/result_pattern.md existiert.
```

# Prompt 24 – Tool Contracts definieren

```text
Aufgabe:

Definiere formale Tool Contracts.

Neue Datei:
core/tool_contract.py

Jeder Tool Contract enthält:
- name
- description
- input_schema
- output_schema
- risk_level
- enabled
- requires_confirmation
- timeout_seconds

Regeln:
- ToolRegistry akzeptiert nur Tools mit Contract.
- Input wird vor Ausführung validiert.
- Output wird nach Ausführung validiert.

Nutze jsonschema.

Akzeptanzkriterien:
- Ungültige Tool-Inputs werden blockiert.
- Ungültige Tool-Outputs erzeugen ToolError.
- docs/tool_contracts.md existiert.
```

# Prompt 25 – Timeout- und Retry-Mechanismus

```text
Aufgabe:

Implementiere Timeout und Retry für Tools und Provider.

Neue Datei:
core/execution_policy.py

Policy-Felder:
- timeout_seconds
- max_retries
- retry_backoff_seconds
- retry_on_errors

Regeln:
- Kein Tool darf unbegrenzt laufen.
- Provider-Aufrufe haben Timeout.
- Retries nur bei recoverable Errors.

Akzeptanzkriterien:
- Hängende Tools werden abgebrochen.
- Retry-Verhalten wird geloggt.
- docs/execution_policy.md existiert.
```

# Prompt 26 – Persistenter Conversation Store

```text
Aufgabe:

Implementiere persistente Gesprächsspeicherung.

Neue Struktur:
data/conversations/

Neue Datei:
memory/conversation_store.py

Funktionen:
- create_conversation()
- append_message()
- get_conversation()
- list_conversations()
- summarize_conversation()

Datenmodell:
{
  "conversation_id": "",
  "created_at": "",
  "updated_at": "",
  "messages": [],
  "summary": "",
  "tags": []
}

Akzeptanzkriterien:
- Jeder Chat wird gespeichert.
- Alte Chats können geladen werden.
- Zusammenfassung wird getrennt gespeichert.
- docs/conversation_store.md existiert.
```

# Prompt 27 – Memory Extraction Pipeline

```text
Aufgabe:

Implementiere Memory Extraction aus Gesprächen.

Neue Datei:
memory/memory_extractor.py

Ziel:
Aus Konversationen automatisch relevante Fakten extrahieren.

Memory-Typen:
- user_preference
- project_fact
- task_fact
- system_fact
- contact_fact

Regeln:
- Keine Secrets speichern.
- Keine temporären Nebensächlichkeiten speichern.
- Jede Memory bekommt Quelle und Zeitstempel.
- Duplikate vermeiden.

Akzeptanzkriterien:
- Nach Gesprächsende werden Memory-Kandidaten erzeugt.
- Memories müssen vor Persistenz validiert werden.
- docs/memory_extraction.md existiert.
```

# Prompt 28 – Memory Review Queue

```text
Aufgabe:

Implementiere Review-Queue für neue Memories.

Neue Struktur:
data/memory_review/

Funktionen:
- add_candidate()
- list_candidates()
- approve_candidate()
- reject_candidate()
- merge_candidate()

Regeln:
- Automatisch extrahierte Memories werden nicht sofort dauerhaft gespeichert.
- User oder Admin muss sie freigeben.
- Rejected Memories werden protokolliert, aber nicht aktiv genutzt.

Akzeptanzkriterien:
- Memory-Kandidaten landen in Review Queue.
- Freigabe verschiebt sie nach long_term.
- docs/memory_review.md existiert.
```

# Prompt 29 – Projektkontext-System

```text
Aufgabe:

Implementiere Projektkontexte.

Neue Struktur:
data/projects/

Datenmodell:
{
  "project_id": "",
  "name": "",
  "description": "",
  "status": "",
  "goals": [],
  "constraints": [],
  "decisions": [],
  "open_tasks": [],
  "related_files": [],
  "created_at": "",
  "updated_at": ""
}

Funktionen:
- create_project()
- update_project()
- get_project()
- list_projects()
- attach_memory()
- attach_task()

Akzeptanzkriterien:
- Aufgaben und Memories können Projekten zugeordnet werden.
- Aktiver Projektkontext kann gesetzt werden.
- docs/project_context.md existiert.
```

# Prompt 30 – Kontext-Budget-Manager

```text
Aufgabe:

Implementiere Context Budget Management.

Neue Datei:
core/context_manager.py

Ziel:
Jarvis soll steuern, welche Informationen in den Prompt gehen.

Quellen:
- aktuelle Nachricht
- Conversation Summary
- relevante Memories
- relevante Tasks
- aktiver Projektkontext
- Tool-Ergebnisse

Funktionen:
- build_context()
- rank_context_items()
- trim_context()
- estimate_tokens()

Regeln:
- Kein unbegrenztes Prompt-Wachstum.
- Wichtigkeit vor Aktualität.
- Aktive Projekte priorisieren.
- Secrets nie in Kontext einfügen.

Akzeptanzkriterien:
- Lange Gespräche bleiben stabil.
- Prompt-Zusammensetzung ist nachvollziehbar.
- docs/context_management.md existiert.
```

### 19. Benutzer

weiter

### 20. Assistent

# Prompt 31 – Datei-Import-Service

```text
Aufgabe:

Implementiere einen stabilen Datei-Import-Service.

Neue Struktur:
services/file_import_service.py
data/imports/
data/imports/originals/
data/imports/processed/
data/imports/failed/

Unterstützte Formate:
- .txt
- .md
- .pdf
- .docx
- .json
- .csv

Funktionen:
- import_file()
- validate_file()
- extract_text()
- store_original()
- store_processed()
- mark_failed()

Datenmodell:
{
  "import_id": "",
  "filename": "",
  "mime_type": "",
  "size_bytes": 0,
  "status": "pending|processing|completed|failed",
  "source_path": "",
  "processed_path": "",
  "error": null,
  "created_at": "",
  "updated_at": ""
}

Akzeptanzkriterien:
- Ungültige Dateitypen werden sauber abgelehnt.
- Fehlerhafte Dateien landen in failed.
- Importstatus ist jederzeit abrufbar.
- docs/file_import.md existiert.
```

# Prompt 32 – Dokument-Chunks erzeugen

```text
Aufgabe:

Implementiere Chunking für importierte Dokumente.

Neue Datei:
knowledge/chunker.py

Funktionen:
- chunk_text()
- chunk_markdown()
- chunk_pdf_text()
- create_chunk_metadata()

Chunk-Metadaten:
{
  "chunk_id": "",
  "document_id": "",
  "index": 0,
  "text": "",
  "token_estimate": 0,
  "source": "",
  "page": null,
  "created_at": ""
}

Regeln:
- Maximal 800 Tokens pro Chunk.
- 100 Tokens Overlap.
- Markdown-Überschriften als Strukturhinweis verwenden.
- Leere Chunks verwerfen.

Akzeptanzkriterien:
- Lange Dokumente werden stabil geteilt.
- Jeder Chunk ist auf Quelle rückführbar.
- docs/chunking.md existiert.
```

# Prompt 33 – Embedding Provider abstrahieren

```text
Aufgabe:

Implementiere Embedding-Provider-Schicht.

Neue Struktur:
providers/embeddings/

Provider:
- BaseEmbeddingProvider
- SentenceTransformerProvider
- OllamaEmbeddingProvider

Funktionen:
- embed_text()
- embed_batch()
- validate_connection()

Regeln:
- Provider-Auswahl über config.
- Batch-Verarbeitung unterstützen.
- Fehlerhafte Provider sauber melden.

Akzeptanzkriterien:
- Embeddings können lokal erzeugt werden.
- Keine Cloud-Pflicht.
- docs/embedding_providers.md existiert.
```

# Prompt 34 – Vektorindex V1

```text
Aufgabe:

Implementiere lokalen Vektorindex.

Neue Datei:
knowledge/vector_store.py

Option:
- FAISS, falls verfügbar
- sonst JSON-basierter Fallback

Funktionen:
- add_vectors()
- search_vectors()
- delete_document_vectors()
- rebuild_index()
- persist_index()
- load_index()

Daten:
data/vector_index/

Akzeptanzkriterien:
- Dokument-Chunks sind semantisch suchbar.
- Index überlebt Neustart.
- Fallback funktioniert ohne FAISS.
- docs/vector_store.md existiert.
```

# Prompt 35 – RAG Retrieval Pipeline

```text
Aufgabe:

Implementiere Retrieval-Pipeline.

Neue Datei:
knowledge/retriever.py

Funktionen:
- retrieve_relevant_chunks()
- rank_results()
- apply_filters()
- build_source_context()

Filter:
- Projekt
- Datum
- Dateityp
- Tags
- Score-Minimum

Regeln:
- Maximal 8 Chunks pro Antwort.
- Quellen immer mitliefern.
- Schlechte Treffer unter Score-Schwelle verwerfen.

Akzeptanzkriterien:
- ChatService kann relevante Dokumente abrufen.
- Antworten mit Dokumentbezug enthalten Quellen.
- docs/retrieval.md existiert.
```

# Prompt 36 – Quellenpflicht bei Dokumentantworten

```text
Aufgabe:

Erzwinge Quellenangaben bei dokumentbasierten Antworten.

Regeln:
- Wenn Antwort aus Dokument-Chunks erzeugt wird, müssen Quellen angezeigt werden.
- Quelle enthält Dateiname, Chunk-ID, Seite falls vorhanden.
- Wenn keine Quelle vorhanden ist, darf Jarvis keine dokumentbasierte Behauptung formulieren.

Implementiere in:
services/chat_service.py
knowledge/retriever.py

Akzeptanzkriterien:
- Dokumentantwort ohne Quelle ist nicht möglich.
- Unsichere Treffer werden als unsicher markiert.
- docs/source_policy.md existiert.
```

# Prompt 37 – Import-Queue

```text
Aufgabe:

Implementiere Import-Queue.

Neue Datei:
services/import_queue.py

Funktionen:
- enqueue_import()
- process_next()
- retry_failed()
- list_queue()
- clear_completed()

Status:
- queued
- processing
- completed
- failed
- skipped

Regeln:
- Import läuft sequenziell.
- Fehler blockieren nicht die Queue.
- Retry maximal 3-mal.

Akzeptanzkriterien:
- Mehrere Dateien können eingereiht werden.
- Defekte Datei stoppt andere Imports nicht.
- docs/import_queue.md existiert.
```

# Prompt 38 – Dokument-Deduplizierung

```text
Aufgabe:

Implementiere Deduplizierung für importierte Dokumente.

Neue Datei:
knowledge/deduplication.py

Prüfungen:
- SHA256 Hash der Originaldatei
- normalisierter Texthash
- Dateiname + Größe

Regeln:
- Exakte Duplikate überspringen.
- Textgleiche Dateien als mögliche Duplikate markieren.
- Keine automatische Löschung.

Akzeptanzkriterien:
- Doppelte Dokumente werden erkannt.
- Nutzer bekommt klaren Status.
- docs/deduplication.md existiert.
```

# Prompt 39 – Dokument-Metadaten und Tags

```text
Aufgabe:

Implementiere Metadaten- und Tag-System für Dokumente.

Neue Datei:
knowledge/document_metadata.py

Datenmodell:
{
  "document_id": "",
  "filename": "",
  "title": "",
  "author": "",
  "created_at": "",
  "imported_at": "",
  "tags": [],
  "project_id": null,
  "source_type": "",
  "language": "",
  "summary": ""
}

Funktionen:
- create_metadata()
- update_metadata()
- add_tags()
- remove_tags()
- assign_project()

Akzeptanzkriterien:
- Dokumente können Projekten zugeordnet werden.
- Tags sind such- und filterbar.
- docs/document_metadata.md existiert.
```

# Prompt 40 – RAG-Gate

```text
Aufgabe:

Führe ein RAG-Gate durch.

Prüfe:
- Dateiimport
- Text-Extraktion
- Chunking
- Embeddings
- Vektorindex
- Retrieval
- Quellenpflicht
- Fehlerfälle
- Performance bei 10, 100, 1000 Chunks

Erstelle:
docs/reports/rag_gate_v1.md

Bewertung:
- PASS
- WARNING
- FAIL

Jeder FAIL braucht:
- Ursache
- Risiko
- Fix
- Priorität

Akzeptanzkriterium:
RAG gilt nur als bestanden, wenn dokumentbasierte Antworten Quellen enthalten.
```

### 21. Benutzer

weiter

### 22. Assistent

# Prompt 41 – Lokale Web-UI vorbereiten

```text
Aufgabe:

Implementiere eine lokale Web-UI als optionales Interface.

Neue Struktur:
webui/
├── backend/
├── frontend/
└── README.md

Backend:
- FastAPI
- REST-Endpunkte für Chat, Tools, Tasks, Memory, Health

Frontend:
- React
- einfache Chat-Oberfläche
- Tool-Liste
- Task-Liste
- Systemstatus

Regeln:
- Web-UI nutzt nur Services.
- Kein direkter Zugriff auf Core-Dateien.
- Kein Secret im Frontend.

Akzeptanzkriterien:
- Web-UI startet lokal.
- Chat funktioniert über ChatService.
- Healthcheck sichtbar.
- docs/webui.md existiert.
```

# Prompt 42 – REST API Layer

```text
Aufgabe:

Implementiere REST API für Jarvis.

Neue Struktur:
api/

Endpunkte:
- GET /health
- GET /tools
- POST /chat
- GET /tasks
- POST /tasks
- PATCH /tasks/{id}
- DELETE /tasks/{id}
- GET /memory
- POST /memory/search
- GET /projects
- POST /projects

Regeln:
- API ruft nur Services auf.
- Jede Antwort nutzt Result-Pattern.
- Fehler werden standardisiert ausgegeben.

Akzeptanzkriterien:
- OpenAPI-Doku verfügbar.
- API ohne GUI nutzbar.
- docs/api.md existiert.
```

# Prompt 43 – API Auth lokal absichern

```text
Aufgabe:

Implementiere lokale API-Authentifizierung.

Ziel:
Web-UI und API dürfen nicht offen ohne Schutz laufen.

Mechanismus:
- lokaler API-Token aus config/local.json oder ENV
- Header: Authorization: Bearer <token>

Regeln:
- Kein Default-Token.
- Ohne Token keine schreibenden Aktionen.
- Token niemals loggen.
- localhost-only als Standard.

Akzeptanzkriterien:
- API blockiert unautorisierte Requests.
- Healthcheck darf optional öffentlich sein.
- docs/api_auth.md existiert.
```

# Prompt 44 – WebSocket Streaming

```text
Aufgabe:

Implementiere Streaming für Chat-Antworten.

Backend:
- WebSocket-Endpunkt /ws/chat

Frontend:
- Tokenweise Ausgabe der Antwort
- Abbruchbutton
- Fehleranzeige

Regeln:
- Provider muss Streaming unterstützen oder fallback auf Nicht-Streaming.
- Abbruch stoppt Provider-Aufruf sauber.
- ConversationStore speichert vollständige Antwort.

Akzeptanzkriterien:
- Streaming funktioniert mit mindestens einem Provider.
- Abbruch erzeugt keinen defekten Gesprächseintrag.
- docs/streaming.md existiert.
```

# Prompt 45 – Desktop UI stabilisieren

```text
Aufgabe:

Stabilisiere vorhandene Desktop-UI.

Ziel:
Desktop-UI soll nur noch Thin Client sein.

Regeln:
- UI ruft ApplicationService.
- Keine Tool-Ausführung direkt aus UI.
- Keine Provider-Auswahl direkt aus UI ohne ConfigManager.
- UI-Fehler dürfen Core nicht stoppen.

Funktionen:
- Chat
- Toolliste
- Taskliste
- Memory-Suche
- Systemstatus

Akzeptanzkriterien:
- Desktop-UI startet auch bei fehlenden optionalen Tools.
- UI zeigt klare Fehlermeldungen.
- docs/desktop_ui.md existiert.
```

# Prompt 46 – UI Statusmodell

```text
Aufgabe:

Implementiere ein einheitliches UI-Statusmodell.

Neue Datei:
ui/shared/view_state.py

Status:
- idle
- loading
- streaming
- success
- warning
- error

Regeln:
- Jede UI-Aktion hat klaren Status.
- Fehler enthalten user_message und technical_details.
- UI darf keine rohen Exceptions anzeigen.

Akzeptanzkriterien:
- Chat-, Task- und Toolansicht nutzen gleiches Statusmodell.
- docs/ui_status_model.md existiert.
```

# Prompt 47 – Einstellungen-UI

```text
Aufgabe:

Implementiere lokale Einstellungen-UI.

Bereiche:
- Provider
- Modelle
- Voice
- Security
- Memory
- RAG
- API

Regeln:
- Secrets werden nie im Klartext angezeigt.
- Änderungen gehen über ConfigManager.
- Änderungen werden validiert.
- Neustartpflichtige Änderungen werden markiert.

Akzeptanzkriterien:
- Nutzer kann Provider wechseln.
- Ungültige Einstellungen werden verhindert.
- docs/settings_ui.md existiert.
```

# Prompt 48 – Web-UI Audit

```text
Aufgabe:

Führe ein UI/API-Audit durch.

Prüfe:
- API-Endpunkte
- Auth
- Secret-Leaks
- Fehlerausgaben
- Streaming
- UI-State
- Service-Kopplung
- CORS
- localhost-only Default

Erstelle:
docs/reports/ui_api_audit_v1.md

Bewertung:
- PASS
- WARNING
- FAIL

Akzeptanzkriterium:
Kein FAIL bei Auth, Secrets oder Schreibzugriffen.
```

# Prompt 49 – Lokale Installer-Struktur

```text
Aufgabe:

Bereite lokale Installation vor.

Neue Dateien:
install.ps1
install.sh
run.ps1
run.sh
doctor.ps1
doctor.sh

Regeln:
- Installation erstellt .venv lokal.
- requirements.txt wird installiert.
- local.example.json wird nach local.json kopiert, falls nicht vorhanden.
- Keine echten Secrets eintragen.
- Doctor wird nach Installation ausgeführt.

Akzeptanzkriterien:
- Windows-Installation funktioniert mit PowerShell.
- Linux/macOS-Installation funktioniert mit Shell.
- docs/installation.md existiert.
```

# Prompt 50 – Release Gate V2

```text
Aufgabe:

Führe Release Gate V2 durch.

Prüfe:
- Installation
- Start
- CLI
- Desktop-UI
- Web-UI
- API
- Auth
- Tools
- Memory
- Tasks
- RAG
- Provider
- SecurityGate
- Tests
- Dokumentation

Erstelle:
docs/reports/release_gate_v2.md

Bewertung:
- PASS
- WARNING
- FAIL

Release-Regel:
V2 darf nur freigegeben werden, wenn:
- keine kritischen Security-FAILS bestehen
- Start ohne echte API-Keys möglich ist
- Tests grün sind
- README aktuellen Stand korrekt beschreibt
```

### 23. Benutzer

weiter

### 24. Assistent

# Prompt 51 – Windows-Automation absichern

```text
Aufgabe:

Refaktorisiere alle Windows-Automation-Funktionen.

Betroffene Bereiche:
- pyautogui
- pywinauto
- comtypes
- pycaw
- win10toast
- Tastatursteuerung
- Maussteuerung
- Fenstersteuerung

Neue Datei:
automation/windows_automation_service.py

Regeln:
- Automation ist standardmäßig deaktiviert.
- Jede Aktion braucht SecurityGate-Prüfung.
- Maus-/Tastaturaktionen brauchen HIGH-Risk-Freigabe.
- Keine blind ausgeführten Klicks.
- Fenster müssen eindeutig identifiziert werden.
- Timeout je Aktion Pflicht.

Akzeptanzkriterien:
- Keine Windows-Aktion läuft ohne Policy.
- Defekte Fenstererkennung bricht sauber ab.
- docs/windows_automation.md existiert.
```

# Prompt 52 – Terminal Agent Safe Mode V2

```text
Aufgabe:

Ersetze den Terminal-Agent durch eine sichere Version.

Neue Datei:
automation/terminal_service.py

Funktionen:
- validate_command()
- execute_allowed_command()
- dry_run()
- get_command_risk()

Allowlist:
- dir
- ls
- pwd
- python --version
- pip list
- git status
- pytest
- jarvis doctor

Blockieren:
- rm
- del
- format
- shutdown
- powershell encodedcommand
- curl | bash
- wget | bash
- sudo
- chmod 777
- net user
- reg delete

Regeln:
- Keine shell=True-Ausführung.
- Alle Befehle als Argumentliste.
- Timeout Pflicht.
- stdout/stderr begrenzen.

Akzeptanzkriterien:
- Gefährliche Befehle werden blockiert.
- Dry-Run zeigt geplante Ausführung.
- docs/terminal_service.md existiert.
```

# Prompt 53 – Dateioperationen kapseln

```text
Aufgabe:

Implementiere sicheren FileService.

Neue Datei:
services/file_service.py

Funktionen:
- read_file()
- write_file()
- append_file()
- delete_file()
- list_directory()
- copy_file()
- move_file()

Regeln:
- Zugriff nur innerhalb erlaubter Workspace-Pfade.
- Path Traversal blockieren.
- Schreibzugriffe brauchen SecurityGate.
- Löschungen brauchen HIGH-Risk-Freigabe.
- Maximalgröße je Datei prüfen.

Akzeptanzkriterien:
- Kein direkter open()-Zugriff außerhalb FileService in Core/Services.
- Pfade mit ../ werden blockiert.
- docs/file_service.md existiert.
```

# Prompt 54 – Workspace-Konzept

```text
Aufgabe:

Implementiere Workspace-Isolation.

Neue Struktur:
workspaces/
data/workspaces.json

Datenmodell:
{
  "workspace_id": "",
  "name": "",
  "root_path": "",
  "allowed_paths": [],
  "blocked_paths": [],
  "created_at": "",
  "updated_at": ""
}

Funktionen:
- create_workspace()
- set_active_workspace()
- get_active_workspace()
- validate_workspace_path()

Regeln:
- Dateioperationen nur im aktiven Workspace.
- Systempfade sind standardmäßig blockiert.
- Workspace muss explizit aktiviert sein.

Akzeptanzkriterien:
- Jarvis kann nicht beliebig im Dateisystem schreiben.
- docs/workspaces.md existiert.
```

# Prompt 55 – Audit Log

```text
Aufgabe:

Implementiere manipulationsarmes Audit Log.

Neue Datei:
core/audit_log.py

Ereignisse:
- TOOL_EXECUTED
- SECURITY_BLOCKED
- FILE_WRITTEN
- FILE_DELETED
- TERMINAL_COMMAND
- CONFIG_CHANGED
- MEMORY_APPROVED
- TASK_COMPLETED

Datenmodell:
{
  "audit_id": "",
  "timestamp": "",
  "actor": "user|system|agent",
  "event_type": "",
  "risk_level": "",
  "summary": "",
  "details": {},
  "hash_previous": "",
  "hash_current": ""
}

Regeln:
- Hash-Kette zur Manipulationserkennung.
- Secrets maskieren.
- Audit Log nie automatisch löschen.

Akzeptanzkriterien:
- Riskante Aktionen sind nachvollziehbar.
- Hash-Kette validierbar.
- docs/audit_log.md existiert.
```

# Prompt 56 – Berechtigungsmodell

```text
Aufgabe:

Implementiere lokales Berechtigungsmodell.

Neue Datei:
core/permissions.py

Rollen:
- viewer
- user
- power_user
- admin

Permissions:
- chat:send
- tools:list
- tools:execute
- files:read
- files:write
- files:delete
- terminal:execute
- config:edit
- memory:approve
- plugins:install

Regeln:
- Standardrolle: user
- Kritische Aktionen nur admin
- Permission-Check vor Service-Ausführung

Akzeptanzkriterien:
- Services prüfen Permissions.
- Admin-Aktionen sind blockiert, wenn Rolle fehlt.
- docs/permissions.md existiert.
```

# Prompt 57 – Plugin Sandbox Policy

```text
Aufgabe:

Erweitere Plugin-System um Sandbox-Policy.

plugin.json muss enthalten:
{
  "name": "",
  "version": "",
  "entrypoint": "",
  "permissions": [],
  "risk_level": "",
  "enabled": false
}

Regeln:
- Plugins sind standardmäßig deaktiviert.
- Plugin-Permissions müssen genehmigt werden.
- Keine Plugins mit Terminalzugriff ohne admin.
- Plugin-Importfehler stoppen Jarvis nicht.

Akzeptanzkriterien:
- Plugin kann nicht mehr Rechte nutzen als deklariert.
- docs/plugin_sandbox.md existiert.
```

# Prompt 58 – Dependency Audit

```text
Aufgabe:

Implementiere Dependency-Audit.

Neue Datei:
core/dependency_audit.py

Prüfungen:
- requirements.txt vorhanden
- requirements-dev.txt vorhanden
- bekannte gefährliche Pakete markieren
- doppelte Abhängigkeiten erkennen
- ungenutzte Hauptabhängigkeiten optional melden

Optional:
- pip-audit Integration, falls installiert

Akzeptanzkriterien:
- jarvis doctor zeigt Dependency-Risiken.
- Fehlendes pip-audit blockiert nicht.
- docs/dependency_audit.md existiert.
```

# Prompt 59 – Secrets Scanner

```text
Aufgabe:

Implementiere lokalen Secrets Scanner.

Neue Datei:
core/secrets_scanner.py

Prüfe:
- API Keys
- Bearer Tokens
- Private Keys
- Passwörter
- .env
- config/local.json
- Logs

Regeln:
- Scanner darf Secret-Werte nur maskiert ausgeben.
- Scanner läuft im doctor.
- Scanner läuft im Release Gate.

Akzeptanzkriterien:
- Echte Keys werden erkannt.
- False Positives werden dokumentiert.
- docs/secrets_scanner.md existiert.
```

# Prompt 60 – Security Gate V2 Audit

```text
Aufgabe:

Führe Security Gate V2 Audit durch.

Prüfe:
- SecurityGate
- TerminalService
- FileService
- Workspace-Isolation
- Permissions
- Plugin Sandbox
- API Auth
- Secrets Scanner
- Audit Log
- Dependency Audit

Erstelle:
docs/reports/security_gate_v2.md

Bewertung:
- PASS
- WARNING
- FAIL

Release-Regel:
Keine Freigabe, wenn eines dieser Themen FAIL hat:
- Secrets
- Terminal
- Dateioperationen
- Plugin-Sandbox
- Auth
```

### 25. Benutzer

weiter

### 26. Benutzer

weiter

### 27. Assistent

# Prompt 61 – Agent Orchestrator V1

```text
Aufgabe:

Implementiere zentralen Agent Orchestrator.

Neue Datei:
agents/orchestrator.py

Ziel:
Mehrere Agenten dürfen nicht unkoordiniert handeln.

Funktionen:
- register_agent()
- route_goal()
- create_execution_plan()
- execute_plan()
- collect_results()
- stop_execution()

Regeln:
- Nur Orchestrator darf Agenten starten.
- Agenten dürfen keine Tools direkt ausführen.
- Tool-Ausführung läuft über ToolService.
- Jede Ausführung bekommt execution_id.

Akzeptanzkriterien:
- PlannerAgent kann Teilaufgaben erzeugen.
- Orchestrator führt Teilaufgaben sequenziell aus.
- Fehler eines Agenten stoppen nicht automatisch alle anderen.
- docs/agent_orchestrator.md existiert.
```

# Prompt 62 – Agent Execution Plan

```text
Aufgabe:

Implementiere formale Execution Plans.

Neue Datei:
agents/execution_plan.py

Datenmodell:
{
  "execution_id": "",
  "goal": "",
  "steps": [
    {
      "step_id": "",
      "agent": "",
      "action": "",
      "input": {},
      "status": "pending|running|completed|failed|skipped",
      "depends_on": [],
      "result": null,
      "error": null
    }
  ],
  "created_at": "",
  "updated_at": ""
}

Regeln:
- Schritte mit Abhängigkeiten erst ausführen, wenn Vorgänger completed sind.
- Fehlgeschlagene Pflichtschritte blockieren abhängige Schritte.
- Plan wird persistent gespeichert.

Akzeptanzkriterien:
- Execution Plan ist nachvollziehbar.
- Abhängigkeiten werden korrekt respektiert.
- docs/execution_plan.md existiert.
```

# Prompt 63 – Agent Limits und Loop-Schutz

```text
Aufgabe:

Implementiere harte Agent-Limits.

Neue Datei:
agents/agent_limits.py

Limits:
- max_steps_per_goal
- max_tool_calls_per_goal
- max_runtime_seconds
- max_retries_per_step
- max_memory_reads
- max_file_reads

Regeln:
- Keine Endlosschleifen.
- Limitüberschreitung erzeugt recoverable AgentError.
- Limitwerte über config steuerbar.

Akzeptanzkriterien:
- Agent kann sich nicht unbegrenzt selbst aufrufen.
- Orchestrator stoppt sauber bei Limitüberschreitung.
- docs/agent_limits.md existiert.
```

# Prompt 64 – PlannerAgent verbessern

```text
Aufgabe:

Implementiere PlannerAgent V2.

Ziel:
PlannerAgent erzeugt strukturierte, prüfbare Pläne statt Freitext.

Output-Schema:
{
  "goal": "",
  "assumptions": [],
  "constraints": [],
  "steps": [],
  "required_tools": [],
  "risks": [],
  "success_criteria": []
}

Regeln:
- Keine Tool-Ausführung im PlannerAgent.
- PlannerAgent darf nur planen.
- Unsichere Annahmen müssen markiert werden.

Akzeptanzkriterien:
- PlannerAgent erzeugt valides JSON.
- Orchestrator kann daraus Execution Plan bauen.
- docs/planner_agent.md existiert.
```

# Prompt 65 – ResearchAgent V1

```text
Aufgabe:

Implementiere ResearchAgent.

Fähigkeiten:
- interne Dokumente durchsuchen
- Websuche nur nutzen, wenn Tool verfügbar und erlaubt
- Quellen sammeln
- Erkenntnisse zusammenfassen

Regeln:
- Keine Behauptung ohne Quelle, wenn Recherchemodus aktiv ist.
- Quellen enthalten Typ: document|web|memory.
- Webzugriff braucht SecurityGate MEDIUM.

Akzeptanzkriterien:
- ResearchAgent liefert strukturierte Findings.
- Findings enthalten Quellen.
- docs/research_agent.md existiert.
```

# Prompt 66 – CodingAgent V1

```text
Aufgabe:

Implementiere CodingAgent im Safe Mode.

Fähigkeiten:
- Code analysieren
- Dateien über FileService lesen
- Patches vorschlagen
- Tests vorschlagen

Regeln:
- Keine Dateiänderung ohne SecurityGate.
- Kein Terminal ohne TerminalService.
- Kein direkter open()-Zugriff.
- Kein subprocess.

Output:
{
  "summary": "",
  "findings": [],
  "proposed_changes": [],
  "tests": [],
  "risks": []
}

Akzeptanzkriterien:
- CodingAgent kann Code bewerten.
- CodingAgent schreibt nicht ungeprüft Dateien.
- docs/coding_agent.md existiert.
```

# Prompt 67 – SystemAgent V1

```text
Aufgabe:

Implementiere SystemAgent.

Fähigkeiten:
- Doctor ausführen
- Health prüfen
- Logs zusammenfassen
- Security-Audit starten
- Dependency-Audit starten

Regeln:
- SystemAgent darf keine Reparaturen automatisch durchführen.
- Reparaturen nur als Plan ausgeben.
- Kritische Aktionen brauchen Admin-Permission.

Akzeptanzkriterien:
- SystemAgent erstellt Diagnosebericht.
- Keine automatische riskante Änderung.
- docs/system_agent.md existiert.
```

# Prompt 68 – TaskAgent V1

```text
Aufgabe:

Implementiere TaskAgent.

Fähigkeiten:
- Aufgaben aus Nutzeranfragen extrahieren
- Aufgaben priorisieren
- Aufgaben Projekten zuordnen
- Aufgabenstatus aktualisieren

Regeln:
- Keine Aufgaben automatisch löschen.
- Fälligkeiten müssen ISO-Format haben.
- Unsichere Fälligkeiten als null speichern.

Akzeptanzkriterien:
- TaskAgent erzeugt valide Task-Objekte.
- TaskAgent nutzt TaskService.
- docs/task_agent.md existiert.
```

# Prompt 69 – MemoryAgent V1

```text
Aufgabe:

Implementiere MemoryAgent.

Fähigkeiten:
- relevante Memories suchen
- Memory-Kandidaten erzeugen
- Duplikate erkennen
- Review Queue befüllen

Regeln:
- MemoryAgent speichert nicht direkt in Long-Term.
- Keine Secrets speichern.
- Keine Gesundheits-, Finanz- oder sensiblen Daten ohne explizite Freigabe speichern.

Akzeptanzkriterien:
- MemoryAgent nutzt MemoryService.
- Memory-Kandidaten landen in Review Queue.
- docs/memory_agent.md existiert.
```

# Prompt 70 – Agent Gate V1

```text
Aufgabe:

Führe Agent Gate V1 durch.

Prüfe:
- Orchestrator
- Execution Plans
- Agent Limits
- PlannerAgent
- ResearchAgent
- CodingAgent
- SystemAgent
- TaskAgent
- MemoryAgent
- Tool-Zugriff
- SecurityGate
- Permissions
- Audit Log

Erstelle:
docs/reports/agent_gate_v1.md

Bewertung:
- PASS
- WARNING
- FAIL

Release-Regel:
Agent-System gilt nur als bestanden, wenn:
- keine Agenten Tools direkt ausführen
- Limits greifen
- riskante Aktionen blockiert werden
- Execution Plans persistent nachvollziehbar sind
```

### 28. Benutzer

weiter

### 29. Assistent

# Prompt 71 – Autonomie-Level einführen

```text
Aufgabe:

Implementiere Autonomie-Level für Jarvis.

Neue Datei:
core/autonomy.py

Level:
- LEVEL_0_READ_ONLY
- LEVEL_1_SUGGEST
- LEVEL_2_EXECUTE_SAFE
- LEVEL_3_EXECUTE_WITH_CONFIRMATION
- LEVEL_4_ADMIN_CONTROLLED

Regeln:
- Standard: LEVEL_1_SUGGEST
- Dateiänderungen erst ab LEVEL_3
- Terminal erst ab LEVEL_3
- Plugin-Installation erst ab LEVEL_4
- Autonomie-Level ist über config steuerbar
- Jede riskante Aktion prüft Autonomie-Level zusätzlich zu Permissions und SecurityGate

Akzeptanzkriterien:
- Orchestrator berücksichtigt Autonomie-Level.
- SecurityGate blockiert Aktionen unterhalb des erforderlichen Levels.
- docs/autonomy_levels.md existiert.
```

# Prompt 72 – Human Approval Workflow

```text
Aufgabe:

Implementiere Genehmigungsworkflow für riskante Aktionen.

Neue Struktur:
data/approvals/

Neue Datei:
core/approval_workflow.py

Datenmodell:
{
  "approval_id": "",
  "requested_by": "",
  "action_type": "",
  "risk_level": "",
  "summary": "",
  "details": {},
  "status": "pending|approved|rejected|expired",
  "created_at": "",
  "expires_at": "",
  "decision_at": null
}

Funktionen:
- request_approval()
- approve()
- reject()
- list_pending()
- expire_old_requests()

Regeln:
- HIGH und CRITICAL Aktionen erzeugen Approval Request.
- CRITICAL bleibt standardmäßig blockiert.
- Approval wird im Audit Log protokolliert.
- Approval hat Ablaufzeit.

Akzeptanzkriterien:
- Riskante Aktionen werden pausiert, nicht blind ausgeführt.
- Abgelehnte Aktionen werden nicht erneut automatisch gestartet.
- docs/approval_workflow.md existiert.
```

# Prompt 73 – Dry-Run-Modus global

```text
Aufgabe:

Implementiere globalen Dry-Run-Modus.

Neue Datei:
core/dry_run.py

Regeln:
- Im Dry-Run werden keine schreibenden Aktionen ausgeführt.
- Tools liefern geplante Änderungen als Vorschau.
- FileService, TerminalService, ConfigManager, PluginManager respektieren Dry-Run.
- Dry-Run ist über config und CLI aktivierbar.

Akzeptanzkriterien:
- `jarvis --dry-run` verändert keine Dateien.
- Audit Log markiert simulierte Aktionen.
- docs/dry_run.md existiert.
```

# Prompt 74 – ChangeSet-Modell

```text
Aufgabe:

Implementiere ChangeSets für geplante Änderungen.

Neue Datei:
core/change_set.py

Datenmodell:
{
  "change_set_id": "",
  "title": "",
  "summary": "",
  "changes": [
    {
      "type": "file_write|file_delete|config_update|task_update|memory_update",
      "target": "",
      "before_hash": null,
      "after_hash": null,
      "diff": "",
      "risk_level": ""
    }
  ],
  "status": "draft|pending_approval|applied|rejected|failed",
  "created_at": "",
  "applied_at": null
}

Funktionen:
- create_change_set()
- add_change()
- validate_change_set()
- apply_change_set()
- rollback_change_set()

Regeln:
- CodingAgent darf nur ChangeSets vorschlagen.
- Anwendung nur über Approval Workflow.
- Jede Änderung braucht Diff oder strukturierte Beschreibung.

Akzeptanzkriterien:
- Codeänderungen sind vor Anwendung prüfbar.
- Rollback ist für Dateiänderungen möglich.
- docs/change_sets.md existiert.
```

# Prompt 75 – Rollback-System

```text
Aufgabe:

Implementiere Rollback für riskante Änderungen.

Neue Struktur:
data/backups/
data/rollbacks/

Neue Datei:
core/rollback_manager.py

Funktionen:
- create_backup()
- restore_backup()
- register_rollback_point()
- list_rollback_points()
- rollback_change_set()

Regeln:
- Vor Dateiänderung Backup erstellen.
- Vor Config-Änderung Backup erstellen.
- Rollback-Punkte enthalten Hashes.
- Rollback wird auditiert.

Akzeptanzkriterien:
- Dateiänderungen können zurückgesetzt werden.
- Config-Änderungen können zurückgesetzt werden.
- docs/rollback.md existiert.
```

# Prompt 76 – Policy Engine

```text
Aufgabe:

Implementiere zentrale Policy Engine.

Neue Datei:
core/policy_engine.py

Policies:
- security_policy.json
- workspace_policy.json
- plugin_policy.json
- automation_policy.json
- data_policy.json

Funktionen:
- load_policies()
- evaluate_policy()
- explain_decision()
- reload_policies()

Regeln:
- SecurityGate nutzt PolicyEngine.
- Entscheidungen müssen erklärbar sein.
- Default Policy ist restriktiv.

Akzeptanzkriterien:
- Jede Blockierung enthält Policy-Grund.
- Policies sind dokumentiert.
- docs/policy_engine.md existiert.
```

# Prompt 77 – Datenklassifizierung

```text
Aufgabe:

Implementiere Datenklassifizierung.

Neue Datei:
core/data_classification.py

Klassen:
- PUBLIC
- INTERNAL
- CONFIDENTIAL
- SECRET
- SENSITIVE_PERSONAL

Regeln:
- Secrets automatisch SECRET.
- Gesundheitsdaten automatisch SENSITIVE_PERSONAL.
- API-Keys nie in Memory, Context oder Logs.
- Dokumente bekommen Klassifizierung als Metadatum.

Akzeptanzkriterien:
- MemoryExtractor nutzt DataClassification.
- FileImportService klassifiziert Dokumente.
- docs/data_classification.md existiert.
```

# Prompt 78 – Retention Policy

```text
Aufgabe:

Implementiere Aufbewahrungsregeln.

Neue Datei:
core/retention_policy.py

Datenarten:
- logs
- audit_logs
- conversations
- memories
- imported_documents
- embeddings
- task_history
- approvals

Regeln:
- Audit Logs nicht automatisch löschen.
- Normale Logs rotieren.
- Temporäre Importdateien nach konfigurierter Zeit löschen.
- Löschung immer auditiert.

Akzeptanzkriterien:
- Datenaufbewahrung ist konfigurierbar.
- Keine automatische Löschung kritischer Auditdaten.
- docs/retention_policy.md existiert.
```

# Prompt 79 – Privacy Mode

```text
Aufgabe:

Implementiere Privacy Mode.

Neue Datei:
core/privacy_mode.py

Funktionen:
- enable_privacy_mode()
- disable_privacy_mode()
- is_privacy_mode_enabled()

Im Privacy Mode:
- keine Memory Extraction
- keine Conversation Persistenz
- keine Tool-Result-Speicherung
- keine sensiblen Logs
- nur minimale Audit-Einträge

Akzeptanzkriterien:
- Chat kann ohne Speicherung laufen.
- Privacy Mode ist sichtbar im UI/CLI.
- docs/privacy_mode.md existiert.
```

# Prompt 80 – Autonomy and Governance Gate

```text
Aufgabe:

Führe Autonomy and Governance Gate durch.

Prüfe:
- Autonomie-Level
- Approval Workflow
- Dry-Run
- ChangeSets
- Rollback
- Policy Engine
- Datenklassifizierung
- Retention Policy
- Privacy Mode
- Audit Log

Erstelle:
docs/reports/autonomy_governance_gate_v1.md

Bewertung:
- PASS
- WARNING
- FAIL

Release-Regel:
Keine Freigabe, wenn:
- Jarvis riskante Aktionen ohne Approval ausführen kann
- Rollback für Dateiänderungen fehlt
- Secrets gespeichert oder geloggt werden
- Privacy Mode nicht zuverlässig wirkt
```

### 30. Benutzer

Gesamtergebnis: ⚠️ CONDITIONAL PASS — Release blockiert
4 PASS / 5 WARNING / 0 FAIL
Blocking:

Warning #4: DataClassification nicht in MemoryExtractor, FileImportService, Audit-Logger eingebaut → Secrets könnten in Memory und Logs landen
Warning #5: require_not_privacy_mode() nicht in MemoryExtractor / ConversationService aufgerufen → Privacy Mode feuert nicht

Die Governance-Infrastruktur ist vollständig implementiert. Die Lücke liegt ausschließlich in der Verdrahtung mit bestehenden Services — kein Architektur-Problem, sondern ausstehende Integrationsarbeit.

### 31. Assistent

# Prompt 81 – Governance Integration Fix

```text
Aufgabe:

Behebe die zwei blockierenden Governance-Warnings.

Ziel:
Release von CONDITIONAL PASS auf PASS bringen.

Blocking Warnings:
1. DataClassification ist nicht in MemoryExtractor, FileImportService und AuditLogger eingebaut.
2. require_not_privacy_mode() wird nicht in MemoryExtractor und ConversationService aufgerufen.

Implementiere:

A) DataClassification verdrahten

Integriere core/data_classification.py in:

- memory/memory_extractor.py
- services/file_import_service.py
- core/audit_log.py

Regeln:
- MemoryExtractor darf keine SECRET-Daten speichern.
- MemoryExtractor darf SENSITIVE_PERSONAL nur als Review-Kandidat markieren, nicht automatisch übernehmen.
- FileImportService klassifiziert jedes Dokument vor Verarbeitung.
- AuditLogger maskiert SECRET-Felder immer.
- AuditLogger speichert keine Rohwerte von Secrets.
- Klassifizierung muss im Metadatenobjekt persistiert werden.

B) Privacy Mode erzwingen

Integriere require_not_privacy_mode() in:

- memory/memory_extractor.py
- services/conversation_service.py oder memory/conversation_store.py

Regeln:
- Privacy Mode blockiert Memory Extraction vollständig.
- Privacy Mode blockiert Conversation Persistenz vollständig.
- Privacy Mode blockiert Tool-Result-Persistenz.
- Im Privacy Mode dürfen nur minimale Audit Events entstehen.
- Kein stilles Speichern trotz aktiviertem Privacy Mode.

C) Tests ergänzen

Erstelle Tests:

tests/unit/test_data_classification_integration.py
tests/unit/test_privacy_mode_enforcement.py

Testfälle:
- API-Key in Usertext wird als SECRET erkannt.
- SECRET wird nicht als Memory gespeichert.
- SECRET wird im Audit Log maskiert.
- Gesundheitsdaten werden als SENSITIVE_PERSONAL klassifiziert.
- Privacy Mode verhindert Conversation Persistenz.
- Privacy Mode verhindert Memory Extraction.
- Privacy Mode verhindert Tool-Result-Speicherung.

D) Gate erneut ausführen

Aktualisiere:

docs/reports/autonomy_governance_gate_v1.md

Erwartetes Ergebnis:
PASS

Akzeptanzkriterien:
- 5 PASS / 0 WARNING / 0 FAIL
- Keine Secrets in Memory
- Keine Secrets in Logs
- Privacy Mode verhindert Persistenz zuverlässig
- Tests grün
```

# Prompt 82 – Final Governance Regression Test

```text
Aufgabe:

Führe nach dem Governance Integration Fix eine Regression durch.

Prüfe gezielt:

1. DataClassification
- PUBLIC
- INTERNAL
- CONFIDENTIAL
- SECRET
- SENSITIVE_PERSONAL

2. MemoryExtractor
- normale Fakten
- Projektfakten
- API Keys
- Passwörter
- Gesundheitsdaten
- Finanzdaten

3. FileImportService
- normale Markdown-Datei
- JSON mit Token
- PDF mit personenbezogenen Daten
- defekte Datei

4. Audit Log
- Tool-Ausführung
- Security Block
- Config Change
- Memory Candidate
- Secret Masking

5. Privacy Mode
- Chat ohne Speicherung
- keine Memory Extraction
- keine Conversation Persistenz
- keine Tool-Result-Persistenz
- minimales Audit Event

Erstelle Bericht:

docs/reports/governance_regression_v1.md

Bewertung:
PASS / WARNING / FAIL

Release-Regel:
Kein WARNING erlaubt bei:
- Secrets
- Privacy Mode
- Memory Persistenz
- Audit Masking
```

### 32. Benutzer

aktualisiere den masterplan

### 33. Assistent

# Jarvis Masterplan v2.1 (aktualisiert nach Governance Gate)

## Gesamtstatus

| Bereich | Status |
|----------|----------|
| Core Architektur | PASS |
| Tool Registry | PASS |
| Event Bus | PASS |
| Memory System | PASS |
| Task System | PASS |
| RAG Foundation | PASS |
| Provider Layer | PASS |
| Security Gate | PASS |
| Permissions | PASS |
| Audit Logging | PASS |
| Workspace Isolation | PASS |
| Agent Framework | PASS |
| Autonomy Framework | PASS |
| Approval Workflow | PASS |
| ChangeSets | PASS |
| Rollback | PASS |
| Policy Engine | PASS |
| Privacy Mode | WARNING |
| Data Classification Integration | WARNING |
| Governance Gate | CONDITIONAL PASS |

---

# Phase 1 — Foundation (Abgeschlossen)

## Core

- ConfigManager
- Logger
- Error Framework
- Result Pattern
- Tool Registry
- Event Bus
- Service Layer
- CLI
- Doctor System

Status:

```text
PASS
```

---

# Phase 2 — Knowledge & RAG (Abgeschlossen)

## Dokumentenverarbeitung

Implementiert:

- Import Service
- Chunking
- Embeddings
- Vector Store
- Retrieval
- Source Tracking
- Metadata System
- Deduplication

Status:

```text
PASS
```

Offen:

- Hybrid Search
- Re-Ranking
- Cross-Document Reasoning

Priorität:

```text
Mittel
```

---

# Phase 3 — UI & API (Abgeschlossen)

Implementiert:

- REST API
- Auth Layer
- Websocket Streaming
- Desktop UI Refactoring
- Settings UI
- Installation Scripts

Status:

```text
PASS
```

---

# Phase 4 — Security (Abgeschlossen)

Implementiert:

- SecurityGate
- Terminal Service
- File Service
- Workspace Isolation
- Permissions
- Plugin Sandbox
- Dependency Audit
- Secret Scanner

Status:

```text
PASS
```

---

# Phase 5 — Agent Framework (Abgeschlossen)

Implementiert:

- Agent Orchestrator
- PlannerAgent
- ResearchAgent
- CodingAgent
- TaskAgent
- MemoryAgent
- SystemAgent
- Agent Limits
- Execution Plans

Status:

```text
PASS
```

---

# Phase 6 — Governance (99% fertig)

Implementiert:

- Autonomy Levels
- Approval Workflow
- Dry Run
- ChangeSets
- Rollback
- Policy Engine
- Retention Policy
- Privacy Mode
- Data Classification

Status:

```text
CONDITIONAL PASS
```

Blocker:

```text
WARNING-04
WARNING-05
```

---

## Governance Fix Sprint (JETZT)

### Sprint G1

Ziel:

```text
Governance Gate → PASS
```

Umsetzung:

### G1.1 Data Classification Integration

Einbauen in:

```text
memory_extractor.py
file_import_service.py
audit_log.py
```

Erwartung:

```text
Keine Secrets in Memory
Keine Secrets in Logs
```

Status:

```text
OFFEN
```

---

### G1.2 Privacy Mode Enforcement

Einbauen in:

```text
conversation_service.py
conversation_store.py
memory_extractor.py
```

Erwartung:

```text
Keine Persistenz im Privacy Mode
```

Status:

```text
OFFEN
```

---

### G1.3 Governance Regression

Tests:

```text
test_data_classification_integration.py
test_privacy_mode_enforcement.py
```

Status:

```text
OFFEN
```

---

# Release Candidate RC1

Wird erreicht nach:

```text
Governance PASS
```

Voraussetzungen:

- 5 PASS
- 0 WARNING
- 0 FAIL

---

# Phase 7 — Jarvis Intelligence Layer

Beginn nach RC1.

## Memory Intelligence

Neue Komponenten:

```text
Memory Ranking Engine
Memory Confidence Scores
Memory Aging
Memory Merging
Memory Conflict Detection
```

Status:

```text
NICHT BEGONNEN
```

---

## Context Intelligence

Neue Komponenten:

```text
Context Ranking
Context Compression
Token Budget Optimizer
Project Context Fusion
```

Status:

```text
NICHT BEGONNEN
```

---

## Reasoning Layer

Neue Agenten:

```text
DecisionAgent
CriticAgent
ReflectionAgent
ValidationAgent
```

Ziel:

```text
Agenten prüfen sich gegenseitig.
```

Status:

```text
NICHT BEGONNEN
```

---

# Phase 8 — Multi-Agent Collaboration

Implementieren:

```text
Agent Teams
Shared Workspace
Agent Delegation
Agent Voting
Conflict Resolution
```

Status:

```text
NICHT BEGONNEN
```

---

# Phase 9 — Autonomous Operations

Implementieren:

```text
Scheduled Goals
Background Research
Continuous Monitoring
Project Watchers
Automation Pipelines
```

Status:

```text
NICHT BEGONNEN
```

Freigabe erst wenn:

```text
Governance PASS
Security PASS
Agent PASS
```

---

# Phase 10 — Jarvis Enterprise

Implementieren:

```text
Multi User
RBAC
SSO
LDAP
PostgreSQL Backend
Distributed Agents
Audit Dashboard
Admin Console
```

Status:

```text
NICHT BEGONNEN
```

---

# Nächster konkreter Schritt

```text
Sprint G1
├── Prompt 81
├── Prompt 82
└── Governance Gate erneut ausführen
```

Erwartetes Ergebnis:

```text
Governance Gate:
5 PASS
0 WARNING
0 FAIL

Release Candidate RC1 erreicht.
```

### 34. Benutzer

Sprint G1
├── Prompt 81
├── Prompt 82
└── Governance Gate erneut ausführen

### 35. Assistent

# Prompt 83 – Sprint G1 ausführen

```text
Aufgabe:

Führe Sprint G1 vollständig aus.

Umfang:
- Prompt 81 umsetzen
- Prompt 82 umsetzen
- Governance Gate erneut ausführen

Ziel:
CONDITIONAL PASS auf PASS heben.

Pflichtfixes:

1. DataClassification Integration

Verdrahte core/data_classification.py verbindlich in:

- memory/memory_extractor.py
- services/file_import_service.py
- core/audit_log.py

Regeln:
- SECRET niemals in Memory speichern.
- SECRET niemals unmaskiert ins Audit Log schreiben.
- SENSITIVE_PERSONAL nur als Review-Kandidat, nicht automatisch persistieren.
- FileImportService klassifiziert jedes Dokument vor Chunking, Embedding oder Persistenz.
- Klassifizierung wird als Metadatum gespeichert.

2. Privacy Mode Enforcement

Verdrahte require_not_privacy_mode() verbindlich in:

- memory/memory_extractor.py
- services/conversation_service.py
- memory/conversation_store.py
- Tool-Result-Persistenz, falls vorhanden

Regeln:
- Privacy Mode blockiert Conversation Persistenz.
- Privacy Mode blockiert Memory Extraction.
- Privacy Mode blockiert Tool-Result-Speicherung.
- Privacy Mode erzeugt nur minimale Audit Events.
- Kein Fallback darf trotzdem speichern.

3. Tests

Erstelle oder erweitere:

- tests/unit/test_data_classification_integration.py
- tests/unit/test_privacy_mode_enforcement.py
- tests/integration/test_governance_regression.py

Testfälle:
- API-Key wird als SECRET erkannt.
- Passwort wird als SECRET erkannt.
- SECRET wird nicht Memory.
- SECRET wird im Audit Log maskiert.
- Gesundheitsdaten werden als SENSITIVE_PERSONAL klassifiziert.
- SENSITIVE_PERSONAL landet nur in Review Queue.
- Privacy Mode verhindert Conversation Persistenz.
- Privacy Mode verhindert Memory Extraction.
- Privacy Mode verhindert Tool-Result-Persistenz.
- FileImportService speichert Klassifizierung im Dokument-Metadatum.

4. Reports

Aktualisiere:

- docs/reports/autonomy_governance_gate_v1.md
- docs/reports/governance_regression_v1.md
- docs/status.md
- README.md, falls Status dort genannt wird

Erwartetes Ergebnis:

```text
Governance Gate:
5 PASS
0 WARNING
0 FAIL

Gesamtstatus:
PASS

Release:
RC1 erreicht
```

Akzeptanzkriterien:
- pytest grün
- keine Secrets in Memory
- keine Secrets in Logs
- Privacy Mode speichert nichts außer minimalem Audit
- Governance Gate PASS
```

# Prompt 84 – Sprint G1 Verifikation und RC1-Freeze

```text
Aufgabe:

Verifiziere Sprint G1 nach Umsetzung.

Prüfe den aktuellen Codezustand vollständig.

Nicht neu bauen, sondern prüfen.

Checkliste:

1. DataClassification
- Wird in MemoryExtractor aufgerufen?
- Wird in FileImportService aufgerufen?
- Wird im AuditLogger aufgerufen?
- Werden SECRET-Werte maskiert?
- Werden SECRET-Werte aus Memory ausgeschlossen?
- Werden SENSITIVE_PERSONAL-Werte korrekt behandelt?

2. Privacy Mode
- Wird require_not_privacy_mode() vor Conversation Persistenz aufgerufen?
- Wird require_not_privacy_mode() vor Memory Extraction aufgerufen?
- Wird Tool-Result-Persistenz blockiert?
- Gibt es alternative Speicherpfade, die Privacy Mode umgehen?

3. Tests
- pytest vollständig ausführen
- Smoke Tests ausführen
- Governance Regression ausführen
- Secret Scanner ausführen
- Doctor ausführen

4. Dokumentation
- autonomy_governance_gate_v1.md aktualisiert
- governance_regression_v1.md vorhanden
- docs/status.md korrekt
- README widerspruchsfrei

5. Release Freeze

Wenn alles PASS:

Setze Status:

```text
Release Candidate:
RC1

Governance:
PASS

Security:
PASS

Autonomy:
PASS

Known Blockers:
0
```

Wenn nicht PASS:

Erstelle:

docs/reports/rc1_blockers.md

Format:
- Blocker-ID
- Kategorie
- Ursache
- Risiko
- betroffene Dateien
- Fix
- Priorität
```

# Prompt 85 – RC1 Masterplan aktualisieren

```text
Aufgabe:

Aktualisiere den Masterplan nach Sprint G1.

Datei:
docs/masterplan.md

Setze:

Governance:
PASS, falls Gate grün.

Sprint G1:
COMPLETED, falls alle Tests grün.

Release Candidate:
RC1 erreicht, falls 0 Blocker.

Ergänze neuen Abschnitt:

RC1 Baseline

Inhalt:
- Architekturstand
- Sicherheitsstand
- Governance-Stand
- Agentenstand
- RAG-Stand
- UI/API-Stand
- bekannte Limitierungen
- nächste Phase

Bekannte Limitierungen:
- Hybrid Search offen
- Re-Ranking offen
- Multi-Agent Collaboration offen
- Scheduled Goals offen
- Enterprise Features offen

Nächste Phase:
Phase 7 – Jarvis Intelligence Layer

Akzeptanzkriterien:
- Masterplan widerspricht keinem Gate-Report.
- Keine offenen Governance-Warnings.
- RC1-Status ist eindeutig.
```

### 36. Benutzer

weiter

### 37. Assistent

# Prompt 86 – Phase 7 starten: Intelligence Layer Foundation

```text
Aufgabe:

Starte Phase 7 nach RC1.

Ziel:
Jarvis soll nicht nur speichern und ausführen, sondern Kontext bewerten, priorisieren, verdichten und Widersprüche erkennen.

Implementiere Foundation für:

1. Memory Intelligence
2. Context Intelligence
3. Reasoning Validation

Neue Struktur:

intelligence/
├── memory/
├── context/
├── reasoning/
└── README.md

Erstelle Basisklassen:

- MemoryScorer
- ContextRanker
- ContextCompressor
- ConflictDetector
- ConfidenceModel
- ValidationAgent

Regeln:
- Keine bestehende Persistenzlogik duplizieren.
- Intelligence Layer liest über Services.
- Intelligence Layer schreibt nur über genehmigte Services.
- Keine direkten Dateioperationen.
- Privacy Mode muss respektiert werden.
- DataClassification muss respektiert werden.

Akzeptanzkriterien:
- Neue Module sind importierbar.
- Keine Architekturverletzung gegen Service Layer.
- docs/intelligence_layer.md existiert.
```

# Prompt 87 – Memory Scoring Engine

```text
Aufgabe:

Implementiere Memory Scoring Engine.

Neue Datei:
intelligence/memory/memory_scorer.py

Ziel:
Memories bekommen Relevanz-, Aktualitäts- und Vertrauensscores.

Score-Felder:

{
  "memory_id": "",
  "relevance_score": 0.0,
  "recency_score": 0.0,
  "confidence_score": 0.0,
  "usage_score": 0.0,
  "final_score": 0.0,
  "reasons": []
}

Regeln:
- final_score = gewichtete Summe
- Gewichtung über config steuerbar
- Sensible Memories bekommen keinen automatischen Boost
- Veraltete Memories verlieren Recency Score
- Häufig genutzte Memories bekommen Usage Score

Akzeptanzkriterien:
- Memory-Suche sortiert nach final_score.
- Score-Erklärung ist nachvollziehbar.
- docs/memory_scoring.md existiert.
```

# Prompt 88 – Memory Aging

```text
Aufgabe:

Implementiere Memory Aging.

Neue Datei:
intelligence/memory/memory_aging.py

Ziel:
Alte Memories werden nicht gelöscht, aber niedriger gewichtet.

Funktionen:
- calculate_age_days()
- calculate_decay_score()
- mark_stale_memory()
- suggest_memory_review()

Regeln:
- Projektentscheidungen altern langsamer.
- Temporäre Präferenzen altern schneller.
- Identitäts-/Basisdaten altern nur bei Konflikt.
- Aging löscht keine Daten automatisch.

Akzeptanzkriterien:
- MemoryScorer nutzt Aging.
- Stale Memories werden für Review markiert.
- docs/memory_aging.md existiert.
```

# Prompt 89 – Memory Conflict Detection

```text
Aufgabe:

Implementiere Konflikterkennung für Memories.

Neue Datei:
intelligence/memory/conflict_detector.py

Konflikttypen:
- value_conflict
- status_conflict
- date_conflict
- preference_conflict
- project_state_conflict

Funktionen:
- detect_conflicts()
- classify_conflict()
- create_conflict_report()
- suggest_resolution()

Regeln:
- Keine automatische Überschreibung.
- Konflikte gehen in Review Queue.
- Neuere Information gewinnt nicht automatisch.
- Quelle und Confidence müssen berücksichtigt werden.

Akzeptanzkriterien:
- Widersprüchliche Memories werden erkannt.
- Conflict Report enthält betroffene Memory IDs.
- docs/memory_conflicts.md existiert.
```

# Prompt 90 – Memory Merge Workflow

```text
Aufgabe:

Implementiere Memory Merge Workflow.

Neue Datei:
intelligence/memory/memory_merge.py

Funktionen:
- find_duplicate_memories()
- propose_merge()
- approve_merge()
- reject_merge()
- apply_merge()

Regeln:
- Merge braucht Approval.
- Original-Memories werden nicht hart gelöscht.
- Merge erzeugt Audit Event.
- Merge darf keine SECRET-Daten erzeugen.

Akzeptanzkriterien:
- Duplikate werden erkannt.
- Merge-Vorschläge landen in Review.
- docs/memory_merge.md existiert.
```

# Prompt 91 – Context Ranking

```text
Aufgabe:

Implementiere Context Ranking.

Neue Datei:
intelligence/context/context_ranker.py

Quellen:
- aktuelle Anfrage
- aktive Conversation Summary
- relevante Memories
- aktive Tasks
- Projektkontext
- RAG-Chunks
- Tool-Ergebnisse

Ranking-Faktoren:
- Relevanz
- Aktualität
- Quelle
- Vertrauen
- Projektbezug
- Datenklassifizierung
- Token-Kosten

Regeln:
- SECRET nie in Prompt-Kontext.
- SENSITIVE_PERSONAL nur, wenn explizit notwendig und erlaubt.
- Aktiver Projektkontext priorisiert.
- Niedrige Relevanz wird verworfen.

Akzeptanzkriterien:
- build_context() nutzt ContextRanker.
- Ranking ist im Debug nachvollziehbar.
- docs/context_ranking.md existiert.
```

# Prompt 92 – Context Compression

```text
Aufgabe:

Implementiere Context Compression.

Neue Datei:
intelligence/context/context_compressor.py

Ziel:
Lange Kontexte werden verdichtet, ohne kritische Fakten zu verlieren.

Funktionen:
- compress_conversation_summary()
- compress_memory_set()
- compress_rag_chunks()
- preserve_decisions()
- preserve_constraints()

Regeln:
- Entscheidungen nie ohne Markierung entfernen.
- Constraints priorisieren.
- Quellenverweise bei RAG erhalten.
- Kompression darf keine neuen Fakten erfinden.

Akzeptanzkriterien:
- Lange Kontexte bleiben unter Token-Budget.
- Quellen bleiben erhalten.
- docs/context_compression.md existiert.
```

# Prompt 93 – Token Budget Optimizer

```text
Aufgabe:

Implementiere Token Budget Optimizer.

Neue Datei:
intelligence/context/token_budget_optimizer.py

Funktionen:
- estimate_tokens()
- allocate_budget()
- trim_by_priority()
- report_budget_usage()

Budget-Kategorien:
- system_prompt
- user_message
- conversation_summary
- memories
- project_context
- rag_chunks
- tools

Regeln:
- User Message nie kürzen.
- System Prompt nie automatisch entfernen.
- RAG-Chunks nach Score kürzen.
- Memories nach final_score kürzen.

Akzeptanzkriterien:
- ContextManager nutzt Budget Optimizer.
- Budget Report ist verfügbar.
- docs/token_budget.md existiert.
```

# Prompt 94 – Reasoning Validation Agent

```text
Aufgabe:

Implementiere ValidationAgent.

Neue Datei:
intelligence/reasoning/validation_agent.py

Ziel:
Antworten vor Ausgabe auf Risiken prüfen.

Prüfungen:
- Quellenpflicht erfüllt
- keine Secrets enthalten
- keine Privacy-Mode-Verletzung
- keine widersprüchlichen Projektstände
- keine nicht belegten Dokumentbehauptungen
- keine Tool-Simulation als echter Erfolg

Output:

{
  "valid": true,
  "warnings": [],
  "blockers": [],
  "required_changes": []
}

Regeln:
- Blocker verhindern Ausgabe.
- Warnings werden intern geloggt.
- ValidationAgent verändert Antwort nicht selbst, sondern meldet Befunde.

Akzeptanzkriterien:
- ChatService nutzt ValidationAgent vor Antwortausgabe.
- Dokumentantworten ohne Quellen werden blockiert.
- docs/validation_agent.md existiert.
```

# Prompt 95 – Intelligence Layer Gate V1

```text
Aufgabe:

Führe Intelligence Layer Gate V1 durch.

Prüfe:
- MemoryScorer
- MemoryAging
- ConflictDetector
- MemoryMerge
- ContextRanker
- ContextCompressor
- TokenBudgetOptimizer
- ValidationAgent
- Privacy Mode Integration
- DataClassification Integration

Erstelle:

docs/reports/intelligence_layer_gate_v1.md

Bewertung:
- PASS
- WARNING
- FAIL

Release-Regel:
Keine Freigabe, wenn:
- SECRET in Kontext gelangen kann
- Privacy Mode umgangen wird
- Dokumentantworten ohne Quellen möglich sind
- Token Budget unbegrenzt wächst
```

### 38. Benutzer

weiter

### 39. Assistent

# Prompt 96 – DecisionAgent V1

```text
Aufgabe:

Implementiere DecisionAgent.

Neue Datei:
intelligence/reasoning/decision_agent.py

Ziel:
Jarvis soll Entscheidungen strukturiert vorbereiten, nicht nur Antworten generieren.

Input:
{
  "decision_context": "",
  "options": [],
  "constraints": [],
  "success_criteria": [],
  "risks": []
}

Output:
{
  "recommended_option": "",
  "ranking": [],
  "tradeoffs": [],
  "assumptions": [],
  "risks": [],
  "confidence": 0.0,
  "reasoning_summary": ""
}

Regeln:
- Keine Entscheidung ohne Annahmenliste.
- Risiken müssen explizit bewertet werden.
- Confidence darf nie 1.0 sein.
- Quellenpflicht bei dokumentbasierten Entscheidungen.

Akzeptanzkriterien:
- DecisionAgent erzeugt valides JSON.
- Optionen werden nachvollziehbar gerankt.
- docs/decision_agent.md existiert.
```

# Prompt 97 – CriticAgent V1

```text
Aufgabe:

Implementiere CriticAgent.

Neue Datei:
intelligence/reasoning/critic_agent.py

Ziel:
Jarvis soll eigene Pläne, Antworten und Tool-Ergebnisse kritisch prüfen.

Prüfbereiche:
- falsche Annahmen
- fehlende Quellen
- schwache Constraints
- Sicherheitsrisiken
- Privacy-Verletzungen
- Tool-Simulationen
- unklare Erfolgskriterien

Output:
{
  "accepted": true,
  "issues": [],
  "severity": "low|medium|high|critical",
  "required_revision": false
}

Regeln:
- Critical Issues blockieren Ausgabe.
- CriticAgent darf keine Tools ausführen.
- CriticAgent bewertet nur.

Akzeptanzkriterien:
- Orchestrator kann CriticAgent nach PlannerAgent einsetzen.
- ChatService kann Antworten prüfen lassen.
- docs/critic_agent.md existiert.
```

# Prompt 98 – ReflectionAgent V1

```text
Aufgabe:

Implementiere ReflectionAgent.

Neue Datei:
intelligence/reasoning/reflection_agent.py

Ziel:
Jarvis soll nach abgeschlossenen Ausführungen Lessons Learned erzeugen.

Input:
- execution_plan
- tool_results
- errors
- final_response

Output:
{
  "what_worked": [],
  "what_failed": [],
  "unexpected_risks": [],
  "memory_candidates": [],
  "process_improvements": []
}

Regeln:
- Keine direkte Memory-Persistenz.
- Memory-Kandidaten gehen in Review Queue.
- Keine Secrets reflektieren.
- Privacy Mode blockiert Reflection vollständig.

Akzeptanzkriterien:
- Orchestrator ruft ReflectionAgent nach komplexen Runs optional auf.
- docs/reflection_agent.md existiert.
```

# Prompt 99 – Validation Pipeline

```text
Aufgabe:

Baue eine zentrale Validation Pipeline.

Neue Datei:
intelligence/reasoning/validation_pipeline.py

Pipeline-Stufen:
1. DataClassificationCheck
2. PrivacyModeCheck
3. SourcePolicyCheck
4. ToolTruthCheck
5. SecurityPolicyCheck
6. OutputConsistencyCheck

Funktionen:
- validate_response()
- validate_plan()
- validate_tool_result()

Regeln:
- ValidationAgent nutzt diese Pipeline.
- Pipeline liefert strukturierte Blocker und Warnings.
- Blocker verhindern Ausgabe oder Ausführung.

Akzeptanzkriterien:
- Antworten laufen vor Ausgabe durch Pipeline.
- Pläne laufen vor Ausführung durch Pipeline.
- docs/validation_pipeline.md existiert.
```

# Prompt 100 – Intelligence RC Gate

```text
Aufgabe:

Führe Intelligence RC Gate durch.

Prüfe:
- DecisionAgent
- CriticAgent
- ReflectionAgent
- ValidationAgent
- ValidationPipeline
- MemoryScorer
- ConflictDetector
- ContextRanker
- ContextCompressor
- TokenBudgetOptimizer

Erstelle:
docs/reports/intelligence_rc_gate.md

Bewertung:
- PASS
- WARNING
- FAIL

Release-Regel:
Intelligence Layer darf nur auf RC gesetzt werden, wenn:
- keine Secrets in Kontext oder Ausgabe gelangen
- Privacy Mode alle Reflection- und Memory-Prozesse blockiert
- Dokumentantworten ohne Quellen blockiert werden
- Agenten keine Tools direkt ausführen
- Token Budget begrenzt ist

Erwartetes Ergebnis:
Intelligence Layer RC1
```

### 40. Benutzer

weiter

### 41. Assistent

# Prompt 101 – Phase 8 starten: Multi-Agent Collaboration Foundation

```text
Aufgabe:

Starte Phase 8 nach Intelligence Layer RC1.

Ziel:
Jarvis soll mehrere Agenten koordiniert einsetzen können, ohne Kontrollverlust, Tool-Konflikte oder widersprüchliche Ergebnisse.

Neue Struktur:

collaboration/
├── teams/
├── protocols/
├── arbitration/
├── shared_workspace/
└── README.md

Implementiere Basiskomponenten:

- AgentTeam
- CollaborationProtocol
- SharedWorkspace
- ArbitrationEngine
- ConflictResolver
- ConsensusBuilder

Regeln:
- Kein Agent darf direkt Tools ausführen.
- Alle Aktionen laufen über Orchestrator und Services.
- SharedWorkspace nutzt Workspace-Isolation.
- Privacy Mode und DataClassification müssen respektiert werden.
- Jede Multi-Agent-Ausführung bekommt collaboration_id.

Akzeptanzkriterien:
- AgentTeam ist registrierbar.
- Team-Ausführung erzeugt nachvollziehbaren Ablauf.
- docs/multi_agent_collaboration.md existiert.
```

# Prompt 102 – AgentTeam Modell

```text
Aufgabe:

Implementiere formales AgentTeam-Modell.

Neue Datei:
collaboration/teams/agent_team.py

Datenmodell:

{
  "team_id": "",
  "name": "",
  "description": "",
  "agents": [],
  "roles": {},
  "allowed_goals": [],
  "risk_level": "",
  "enabled": false,
  "created_at": "",
  "updated_at": ""
}

Funktionen:
- create_team()
- register_agent_to_team()
- remove_agent_from_team()
- list_teams()
- validate_team()

Regeln:
- Teams sind standardmäßig deaktiviert.
- Team braucht eindeutige Rollen.
- Kein Team darf Agent Limits überschreiten.
- Risk Level ergibt sich aus den erlaubten Agenten und Zielen.

Akzeptanzkriterien:
- Teams können validiert werden.
- Ungültige Teams starten nicht.
- docs/agent_teams.md existiert.
```

# Prompt 103 – Collaboration Protocol

```text
Aufgabe:

Implementiere Collaboration Protocol.

Neue Datei:
collaboration/protocols/collaboration_protocol.py

Protokollphasen:
1. goal_intake
2. plan_generation
3. critique
4. revision
5. execution
6. validation
7. synthesis
8. reflection

Regeln:
- Jede Phase hat Input- und Output-Schema.
- Jede Phase kann blockieren.
- Kritische Issues führen zu Revision oder Abbruch.
- Reflection entfällt im Privacy Mode.

Akzeptanzkriterien:
- Orchestrator kann Protocol ausführen.
- Phasenstatus wird gespeichert.
- docs/collaboration_protocol.md existiert.
```

# Prompt 104 – Shared Workspace

```text
Aufgabe:

Implementiere Shared Workspace für Agenten.

Neue Datei:
collaboration/shared_workspace/shared_workspace.py

Datenmodell:

{
  "workspace_id": "",
  "collaboration_id": "",
  "artifacts": [],
  "notes": [],
  "decisions": [],
  "open_questions": [],
  "created_at": "",
  "updated_at": ""
}

Funktionen:
- add_artifact()
- add_note()
- add_decision()
- add_open_question()
- get_workspace_snapshot()
- clear_workspace()

Regeln:
- Keine SECRET-Daten speichern.
- SENSITIVE_PERSONAL nur mit Policy-Freigabe.
- Workspace wird nicht im Privacy Mode persistiert.
- Jede Änderung wird auditiert.

Akzeptanzkriterien:
- Agenten können indirekt Ergebnisse ablegen.
- Workspace Snapshot ist lesbar.
- docs/shared_workspace.md existiert.
```

# Prompt 105 – Arbitration Engine

```text
Aufgabe:

Implementiere Arbitration Engine.

Neue Datei:
collaboration/arbitration/arbitration_engine.py

Ziel:
Wenn Agenten widersprüchliche Empfehlungen liefern, entscheidet nicht der lauteste Agent.

Bewertungsfaktoren:
- Quellenqualität
- Confidence
- Rollenkompetenz
- Risiko
- Policy-Konformität
- Aktualität
- Kosten/Aufwand

Output:

{
  "selected_position": "",
  "rejected_positions": [],
  "reasoning_summary": "",
  "confidence": 0.0,
  "risks": [],
  "requires_human_approval": false
}

Regeln:
- CRITICAL Risk verlangt Human Approval.
- Niedrige Quellenqualität reduziert Confidence.
- Kein automatischer Override von SecurityGate.
- Arbitration wird auditiert.

Akzeptanzkriterien:
- Konfliktfälle erzeugen Arbitration Report.
- docs/arbitration_engine.md existiert.
```

# Prompt 106 – Consensus Builder

```text
Aufgabe:

Implementiere Consensus Builder.

Neue Datei:
collaboration/arbitration/consensus_builder.py

Funktionen:
- collect_positions()
- compare_positions()
- identify_agreements()
- identify_disagreements()
- build_consensus()

Regeln:
- Konsens darf Unsicherheit nicht verstecken.
- Minderheitspositionen mit hoher Risikorelevanz bleiben sichtbar.
- Quellenarme Aussagen werden markiert.

Akzeptanzkriterien:
- Team-Ergebnisse enthalten Konsens und Dissens.
- docs/consensus_builder.md existiert.
```

# Prompt 107 – Conflict Resolver

```text
Aufgabe:

Implementiere Conflict Resolver für Multi-Agent-Ergebnisse.

Neue Datei:
collaboration/arbitration/conflict_resolver.py

Konflikttypen:
- factual_conflict
- policy_conflict
- tool_result_conflict
- priority_conflict
- risk_conflict
- resource_conflict

Funktionen:
- detect_agent_conflicts()
- classify_conflict()
- resolve_conflict()
- escalate_conflict()

Regeln:
- Policy-Konflikte werden nicht automatisch aufgelöst.
- Tool-Result-Konflikte brauchen erneute Validierung.
- Risk-Konflikte ab HIGH verlangen Approval.

Akzeptanzkriterien:
- Konflikte werden strukturiert erkannt.
- Eskalationspfade sind klar.
- docs/conflict_resolver.md existiert.
```

# Prompt 108 – Team Execution Limits

```text
Aufgabe:

Implementiere Team Execution Limits.

Neue Datei:
collaboration/team_limits.py

Limits:
- max_agents_per_team
- max_protocol_phases
- max_total_tool_calls
- max_total_runtime_seconds
- max_shared_workspace_items
- max_revision_cycles

Regeln:
- Limits über config steuerbar.
- Überschreitung stoppt Team-Ausführung sauber.
- Limitverletzung wird auditiert.

Akzeptanzkriterien:
- Multi-Agent-Schleifen werden verhindert.
- docs/team_limits.md existiert.
```

# Prompt 109 – Multi-Agent Audit Report

```text
Aufgabe:

Implementiere Audit Report für Team-Ausführungen.

Neue Datei:
collaboration/reports/multi_agent_report.py

Report enthält:
- collaboration_id
- goal
- agents
- protocol_phases
- decisions
- conflicts
- arbitration
- tool_calls
- policy_blocks
- final_result
- risks
- duration

Regeln:
- Keine Secrets im Report.
- Report respektiert Privacy Mode.
- Report ist maschinenlesbar und Markdown-exportierbar.

Akzeptanzkriterien:
- Jeder Team-Run erzeugt Report, außer Privacy Mode blockiert Persistenz.
- docs/multi_agent_reports.md existiert.
```

# Prompt 110 – Multi-Agent Collaboration Gate V1

```text
Aufgabe:

Führe Multi-Agent Collaboration Gate V1 durch.

Prüfe:
- AgentTeam
- CollaborationProtocol
- SharedWorkspace
- ArbitrationEngine
- ConsensusBuilder
- ConflictResolver
- TeamLimits
- MultiAgentReport
- Orchestrator-Integration
- SecurityGate
- Privacy Mode
- DataClassification

Erstelle:

docs/reports/multi_agent_collaboration_gate_v1.md

Bewertung:
- PASS
- WARNING
- FAIL

Release-Regel:
Keine Freigabe, wenn:
- Agenten Tools direkt ausführen können
- Team-Limits fehlen
- SECRET im SharedWorkspace oder Report landen kann
- Policy-Konflikte automatisch übergangen werden
- Privacy Mode Persistenz nicht blockiert
```

### 42. Benutzer

aktualisiere die gui

### 43. Assistent

# Prompt 111 – GUI auf aktuellen RC1/Phase-8-Stand aktualisieren

```text
Aufgabe:

Aktualisiere die Jarvis GUI auf den aktuellen Masterplan-Stand.

Ziel:
Die GUI soll nicht nur Chat anzeigen, sondern den aktuellen Systemzustand, Governance, Agenten, RAG, Memory, Tasks und Multi-Agent-Collaboration sichtbar und steuerbar machen.

Keine ZIP erzeugen.

Betroffene Bereiche:
- Desktop UI
- Web UI
- Shared UI State
- Settings UI
- API-Anbindung

Neue/aktualisierte GUI-Bereiche:

1. Dashboard

Anzeigen:
- Systemstatus
- Release-Status
- Governance Gate
- Security Gate
- Intelligence Layer Status
- Multi-Agent Status
- aktive Provider
- aktive Workspace
- Privacy Mode Status
- Autonomie-Level

Statusfarben:
- PASS
- WARNING
- FAIL
- BLOCKED
- DISABLED

2. Chat View

Erweitern um:
- Quellenanzeige bei RAG-Antworten
- verwendete Memories
- verwendeter Projektkontext
- Token-Budget-Anzeige
- Validation-Warnings
- Tool-Aufruf-Verlauf
- Streaming-Status
- Abbruchbutton

Regeln:
- SECRET niemals anzeigen.
- Privacy Mode sichtbar markieren.
- Dokumentantworten ohne Quelle als BLOCKED anzeigen.

3. Tool Center

Anzeigen:
- Toolname
- Status
- Risk Level
- Requires Confirmation
- Timeout
- letzter Lauf
- letzter Fehler

Aktionen:
- Tool aktivieren/deaktivieren
- Tool testen
- Tool Contract anzeigen

Regeln:
- Riskante Tools nur mit Approval.
- CRITICAL Tools standardmäßig blockiert.

4. Memory Center

Anzeigen:
- Memories
- Memory Scores
- Aging Status
- Conflicts
- Review Queue
- Merge-Vorschläge

Aktionen:
- Memory freigeben
- Memory ablehnen
- Memory mergen
- Conflict Report öffnen

Regeln:
- SECRET nicht anzeigen.
- SENSITIVE_PERSONAL nur mit Policy-Hinweis.

5. Task Center

Anzeigen:
- Aufgaben
- Status
- Priorität
- Fälligkeit
- Projektzuordnung
- Agent-Zuordnung

Aktionen:
- Aufgabe erstellen
- Aufgabe bearbeiten
- Aufgabe abschließen
- Aufgabe abbrechen

6. Project Center

Anzeigen:
- Projekte
- Ziele
- Constraints
- Entscheidungen
- offene Aufgaben
- verknüpfte Dokumente
- verknüpfte Memories

Aktionen:
- Projekt aktiv setzen
- Kontext anzeigen
- Tasks/Memories verknüpfen

7. RAG Center

Anzeigen:
- importierte Dokumente
- Importstatus
- Klassifizierung
- Chunks
- Embedding-Status
- Quellen
- Duplikate

Aktionen:
- Datei importieren
- Dokument neu indexieren
- Dokument Projekt zuordnen
- Dokument-Tags bearbeiten

Regeln:
- SECRET-Dokumente nicht in RAG-Kontext geben.
- Privacy Mode blockiert Persistenz.

8. Agent Center

Anzeigen:
- Agenten
- Rollen
- Status
- Limits
- letzte Execution Plans
- Reflection Reports

Aktionen:
- Agent aktivieren/deaktivieren
- Execution Plan öffnen
- Agent Report anzeigen

Regeln:
- Agenten dürfen keine Tools direkt starten.
- Toolausführung nur über Orchestrator sichtbar machen.

9. Collaboration Center

Anzeigen:
- Agent Teams
- Collaboration Runs
- Shared Workspace
- Consensus Reports
- Arbitration Reports
- Conflicts
- Team Limits

Aktionen:
- Team anzeigen
- Collaboration Report öffnen
- Konflikte prüfen
- Human Approval auslösen

10. Governance Center

Anzeigen:
- Autonomie-Level
- Approval Queue
- ChangeSets
- Rollback Points
- Policy Decisions
- Audit Log
- Privacy Mode
- Data Classification

Aktionen:
- Approval akzeptieren/ablehnen
- ChangeSet anzeigen
- Rollback auslösen
- Policy-Entscheidung erklären

Regeln:
- Rollback braucht Admin Permission.
- Approval-Entscheidungen werden auditiert.

Technische Anforderungen:

- GUI nutzt ausschließlich Services oder REST API.
- Kein direkter Dateizugriff aus UI.
- Kein direkter Toolzugriff aus UI.
- Kein direkter Providerzugriff aus UI.
- Einheitliches ViewState-Modell verwenden.
- Fehler über Result-Pattern darstellen.
- Auth Token niemals im Frontend loggen.
- Secrets immer maskieren.
- Privacy Mode muss global sichtbar sein.

Erstelle/aktualisiere:

ui/shared/view_state.py
ui/shared/status_badges.py
ui/shared/result_mapper.py

webui/frontend/src/pages/Dashboard.tsx
webui/frontend/src/pages/Chat.tsx
webui/frontend/src/pages/Tools.tsx
webui/frontend/src/pages/Memory.tsx
webui/frontend/src/pages/Tasks.tsx
webui/frontend/src/pages/Projects.tsx
webui/frontend/src/pages/Rag.tsx
webui/frontend/src/pages/Agents.tsx
webui/frontend/src/pages/Collaboration.tsx
webui/frontend/src/pages/Governance.tsx
webui/frontend/src/pages/Settings.tsx

webui/frontend/src/components/StatusBadge.tsx
webui/frontend/src/components/RiskBadge.tsx
webui/frontend/src/components/PrivacyModeBanner.tsx
webui/frontend/src/components/SourceList.tsx
webui/frontend/src/components/ApprovalQueue.tsx
webui/frontend/src/components/AuditLogTable.tsx
webui/frontend/src/components/ExecutionPlanView.tsx
webui/frontend/src/components/ChangeSetDiff.tsx

API-Endpunkte prüfen/ergänzen:

GET /health
GET /status
GET /governance/status
GET /security/status
GET /tools
GET /memory
GET /memory/review
GET /tasks
GET /projects
GET /rag/documents
GET /agents
GET /agents/executions
GET /collaboration/teams
GET /collaboration/runs
GET /approvals
GET /audit
GET /policies
GET /settings

POST /chat
POST /tasks
POST /rag/import
POST /approvals/{id}/approve
POST /approvals/{id}/reject
POST /changesets/{id}/apply
POST /rollback/{id}

Dokumentation aktualisieren:

docs/gui.md
docs/webui.md
docs/ui_state_model.md
docs/governance_ui.md
docs/reports/gui_update_v1.md

Tests ergänzen:

tests/ui/test_dashboard_status.py
tests/ui/test_privacy_mode_banner.py
tests/ui/test_secret_masking.py
tests/ui/test_governance_views.py
tests/ui/test_rag_sources_visible.py
tests/ui/test_agent_execution_view.py

Akzeptanzkriterien:

- GUI zeigt RC1-/Governance-Status korrekt.
- Privacy Mode ist global sichtbar.
- SECRET-Werte werden nie angezeigt.
- RAG-Antworten zeigen Quellen.
- Tool-Risiko ist sichtbar.
- Approval Queue ist bedienbar.
- ChangeSets sind prüfbar.
- Agent Execution Plans sind sichtbar.
- Multi-Agent Reports sind sichtbar.
- Keine UI-Komponente greift direkt auf Core-Dateien zu.
- Tests grün.
```

# Prompt 112 – GUI Gate V1

```text
Aufgabe:

Führe nach der GUI-Aktualisierung ein GUI Gate durch.

Prüfe:

1. Architektur
- UI nutzt nur API/Services.
- Keine Businesslogik im Frontend.
- Kein direkter Toolzugriff.
- Kein direkter Dateizugriff.

2. Security
- Secrets maskiert.
- Auth Token nicht im Log.
- Schreibaktionen geschützt.
- Riskante Aktionen brauchen Approval.

3. Governance
- Privacy Mode sichtbar.
- Autonomie-Level sichtbar.
- Approval Queue funktioniert.
- Audit Log sichtbar.
- Policy Decisions erklärbar.

4. RAG
- Dokumente sichtbar.
- Quellen sichtbar.
- Klassifizierung sichtbar.
- Dokumentantworten ohne Quelle blockiert.

5. Agenten
- Agentenstatus sichtbar.
- Execution Plans sichtbar.
- Agent Limits sichtbar.
- Tool Calls nachvollziehbar.

6. Multi-Agent
- Teams sichtbar.
- Collaboration Runs sichtbar.
- Arbitration Reports sichtbar.
- Konflikte sichtbar.
- Team Limits sichtbar.

Erstelle Bericht:

docs/reports/gui_gate_v1.md

Bewertung:
PASS / WARNING / FAIL

Release-Regel:
GUI darf nur PASS erhalten, wenn:
- keine Secrets angezeigt werden
- Privacy Mode sichtbar und wirksam ist
- riskante Aktionen nicht direkt ausführbar sind
- RAG-Quellen angezeigt werden
- Governance-Status korrekt dargestellt wird
```

### 44. Benutzer

implementiere alle neuen feature in die gui, paase auch die Einstellungen Gui an

### 45. Assistent

Ich setze die GUI-Änderungen direkt im aktuellen Jarvis-Code um. Ausgabe bleibt ohne ZIP, außer du forderst später explizit ein Paket an.

### 46. Assistent

GUI aktualisiert.

Geändert:
- `ui.py`
- `docs/gui.md`
- `docs/reports/gui_update_v1.md`

Patch:
[jarvis_gui_update_v1.patch](sandbox:/mnt/data/jarvis_gui_update_v1.patch)

Validierung:
```text
python -m py_compile ui.py
PASS
```

Status:
```text
GUI Update: PASS mit Integrations-WARNING
```

Offen:
```text
Live-Anbindung an finale API-Endpunkte für Audit Log, Approval Queue, Execution Plans, RAG-Dokumente und Collaboration Runs

### 47. Benutzer

erstelle mir die prompt zum implementieren aller neuen feature in die gui, passe auch die Einstellungen Gui an.

### 48. Assistent

# Prompt 113 – GUI Feature Implementation Sprint

```text
Aufgabe:

Implementiere alle neuen Masterplan-Features vollständig in die Jarvis-GUI.

Ziel:
Die GUI muss den aktuellen Systemstand abbilden und bedienbar machen:

- Governance
- Security
- Privacy Mode
- Data Classification
- Approval Queue
- ChangeSets
- Rollback
- Audit Log
- RAG
- Memory Intelligence
- Context Intelligence
- Agenten
- Multi-Agent Collaboration
- Settings

Keine Mock-Daten als finalen Stand verwenden.
Falls Backend-Endpunkte fehlen, API-Contract definieren und UI mit sauberem Empty/Error State vorbereiten.

Grundregeln:
- GUI greift nie direkt auf Dateien zu.
- GUI führt nie direkt Tools aus.
- GUI ruft nur API/Services auf.
- Secrets niemals anzeigen.
- Auth Token niemals loggen.
- Riskante Aktionen immer über Approval Workflow.
- Privacy Mode global sichtbar machen.
- Result-Pattern für alle API-Antworten verwenden.
- ViewState-Pattern für alle UI-Zustände verwenden.

Zu implementieren:

1. Global Layout

Ergänze:
- linke Navigation
- globaler Status-Header
- PrivacyModeBanner
- aktiver Workspace
- aktiver Provider
- Autonomie-Level
- Release-Status
- Systemstatus

Navigationspunkte:
- Dashboard
- Chat
- Tools
- Memory
- Tasks
- Projects
- RAG
- Agents
- Collaboration
- Governance
- Settings

2. Dashboard

Anzeigen:
- Release Candidate Status
- Governance Gate
- Security Gate
- Intelligence Layer Gate
- Multi-Agent Gate
- Provider Status
- Workspace Status
- Privacy Mode
- Autonomie-Level
- offene Approvals
- letzte kritische Audit Events
- aktive Blocker

Komponenten:
- StatusBadge
- RiskBadge
- GateStatusCard
- SystemHealthCard
- OpenApprovalsCard
- RecentAuditEventsCard

3. Chat

Erweitern:
- Quellenliste bei RAG-Antworten
- verwendete Memories
- verwendeter Projektkontext
- Tool Calls
- Validation Warnings
- Token Budget Report
- Streaming Status
- Stop Generation Button

Blockieren:
- Antwort ohne Quellen, wenn RAG-Kontext genutzt wurde.
- Anzeige von SECRET-Inhalten.
- Speicherung bei Privacy Mode.

4. Tool Center

Anzeigen:
- Toolname
- Beschreibung
- Status
- Risk Level
- Enabled
- Requires Confirmation
- Timeout
- letzter Lauf
- letzter Fehler
- Contract

Aktionen:
- Tool Contract öffnen
- Tool Health prüfen
- Tool aktivieren/deaktivieren
- Tool-Test nur über Approval bei HIGH/CRITICAL

5. Memory Center

Anzeigen:
- Memory-Liste
- Memory Scores
- Aging Status
- Confidence
- Review Queue
- Conflict Reports
- Merge-Vorschläge
- Data Classification

Aktionen:
- Memory freigeben
- Memory ablehnen
- Merge prüfen
- Conflict Report öffnen
- Memory suchen

Regeln:
- SECRET nicht anzeigen.
- SENSITIVE_PERSONAL nur mit Hinweis und Permission.

6. Task Center

Anzeigen:
- Aufgaben
- Status
- Priorität
- Fälligkeitsdatum
- Projekt
- Tags
- Agent-Zuordnung

Aktionen:
- Aufgabe erstellen
- Aufgabe ändern
- Aufgabe abschließen
- Aufgabe abbrechen
- Aufgabe Projekt zuordnen

7. Project Center

Anzeigen:
- Projekte
- Ziele
- Constraints
- Entscheidungen
- offene Aufgaben
- verknüpfte Dokumente
- verknüpfte Memories
- Projektstatus

Aktionen:
- Projekt erstellen
- Projekt aktiv setzen
- Task verknüpfen
- Memory verknüpfen
- Dokument verknüpfen

8. RAG Center

Anzeigen:
- Dokumente
- Importstatus
- Klassifizierung
- Chunks
- Embedding Status
- Tags
- Projektzuordnung
- Duplikatstatus
- Quellenfähigkeit

Aktionen:
- Datei importieren
- Dokument neu indexieren
- Tags ändern
- Projekt zuordnen
- Retrieval-Test ausführen

Regeln:
- SECRET-Dokumente nicht als Prompt-Kontext verwenden.
- Privacy Mode blockiert Import-Persistenz.

9. Agent Center

Anzeigen:
- Agenten
- Rollen
- Status
- Limits
- letzte Execution Plans
- Tool Calls
- Reflection Reports
- Validation Reports

Aktionen:
- Agent aktivieren/deaktivieren
- Execution Plan öffnen
- Agent Report anzeigen
- Limits anzeigen

Regeln:
- Kein direkter Toolstart aus Agent-UI.
- Agent-Aktionen nur über Orchestrator.

10. Collaboration Center

Anzeigen:
- Agent Teams
- Team Status
- Collaboration Runs
- Shared Workspace Snapshot
- Consensus Reports
- Arbitration Reports
- Conflicts
- Team Limits

Aktionen:
- Team anzeigen
- Collaboration Report öffnen
- Konflikt eskalieren
- Human Approval starten

Regeln:
- Shared Workspace zeigt keine SECRET-Daten.
- Privacy Mode blockiert persistente Reports.

11. Governance Center

Anzeigen:
- Autonomie-Level
- Approval Queue
- ChangeSets
- Rollback Points
- Policy Decisions
- Audit Log
- Privacy Mode
- Data Classification Regeln
- Retention Policy

Aktionen:
- Approval approve/reject
- ChangeSet anzeigen
- ChangeSet anwenden
- Rollback auslösen
- Policy Decision erklären
- Privacy Mode toggeln

Regeln:
- Rollback nur mit Admin Permission.
- Approval-Entscheidungen auditieren.
- CRITICAL Aktionen standardmäßig blockieren.

12. Settings GUI

Passe Settings vollständig an.

Bereiche:

A) Provider Settings
- aktiver Provider
- Fallback Provider
- Modell
- Streaming aktiv
- Timeout
- Retry Policy
- API-Key Status nur als vorhanden/nicht vorhanden anzeigen

B) Voice Settings
- Input Provider
- Output Provider
- Sprache
- TTS Engine
- ElevenLabs Key Status
- Fallback TTS

C) Security Settings
- SecurityGate aktiv
- Terminal Safe Mode
- FileService Workspace Lock
- Plugin Sandbox
- Secret Scanner aktiv
- Dependency Audit aktiv

D) Governance Settings
- Autonomie-Level
- Approval Ablaufzeit
- Dry-Run Mode
- Rollback aktiv
- Privacy Mode
- Retention Policy

E) RAG Settings
- Embedding Provider
- Chunkgröße
- Overlap
- Score Threshold
- Max Chunks
- Quellenpflicht aktiv

F) Memory Settings
- Memory Extraction aktiv
- Review Queue Pflicht
- Aging aktiv
- Conflict Detection aktiv
- Merge Workflow aktiv

G) Agent Settings
- Agenten aktiv
- Max Steps
- Max Tool Calls
- Max Runtime
- Reflection aktiv
- Validation Pipeline aktiv

H) Collaboration Settings
- Multi-Agent aktiv
- Max Agents per Team
- Max Revision Cycles
- Arbitration aktiv
- Consensus Builder aktiv

I) UI Settings
- Theme
- Sprache
- Dichte
- Sidebar Modus
- Debug Infos anzeigen

Regeln für Settings:
- Keine Secrets im Klartext anzeigen.
- Secret-Felder nur als masked + update action.
- Ungültige Werte blockieren.
- Änderungen über ConfigManager/API.
- Neustartpflichtige Änderungen markieren.
- Dry-Run für riskante Settings anbieten.

13. Shared Components

Erstelle/aktualisiere:
- StatusBadge
- RiskBadge
- PrivacyModeBanner
- DataClassificationBadge
- ApprovalQueue
- AuditLogTable
- SourceList
- TokenBudgetView
- ExecutionPlanView
- ChangeSetDiff
- RollbackPointList
- PolicyDecisionView
- MemoryScoreCard
- ConflictReportView
- AgentLimitView
- CollaborationRunView
- SettingsSection
- SecretInput

14. API Client

Erstelle zentralen API Client:
webui/frontend/src/lib/apiClient.ts

Regeln:
- Authorization Header zentral
- Result-Pattern auswerten
- Fehler normalisieren
- Secrets maskieren
- Keine Tokens loggen

15. View State

Erweitere:
webui/frontend/src/lib/viewState.ts

States:
- idle
- loading
- streaming
- success
- warning
- error
- blocked
- unauthorized
- empty

16. API Contracts

Falls Backend-Endpunkte fehlen, definiere Contracts in:
docs/api/gui_contracts.md

Benötigte Endpunkte:

GET /status
GET /health
GET /governance/status
GET /security/status
GET /settings
PATCH /settings
GET /tools
POST /tools/{id}/health
PATCH /tools/{id}
GET /memory
GET /memory/review
POST /memory/review/{id}/approve
POST /memory/review/{id}/reject
GET /memory/conflicts
GET /tasks
POST /tasks
PATCH /tasks/{id}
GET /projects
POST /projects
PATCH /projects/{id}
GET /rag/documents
POST /rag/import
POST /rag/documents/{id}/reindex
GET /agents
GET /agents/executions
GET /collaboration/teams
GET /collaboration/runs
GET /approvals
POST /approvals/{id}/approve
POST /approvals/{id}/reject
GET /audit
GET /policies/decisions
GET /changesets
POST /changesets/{id}/apply
GET /rollback
POST /rollback/{id}

17. Tests

Erstelle:
tests/ui/test_gui_navigation.py
tests/ui/test_settings_gui.py
tests/ui/test_secret_masking.py
tests/ui/test_privacy_mode_banner.py
tests/ui/test_governance_center.py
tests/ui/test_rag_sources.py
tests/ui/test_memory_center.py
tests/ui/test_agent_center.py
tests/ui/test_collaboration_center.py

Akzeptanzkriterien:
- Alle Seiten rendern.
- Settings validieren Eingaben.
- Secrets werden maskiert.
- Privacy Mode Banner sichtbar.
- Approval Buttons erzeugen API Calls.
- RAG Quellen werden angezeigt.
- Execution Plans werden angezeigt.
- Collaboration Reports werden angezeigt.
- Kein direkter Datei- oder Toolzugriff aus UI.

18. Dokumentation

Aktualisiere:
docs/gui.md
docs/settings_gui.md
docs/webui.md
docs/ui_state_model.md
docs/api/gui_contracts.md
docs/reports/gui_update_v2.md

Abschlussbericht:
docs/reports/gui_update_v2.md muss enthalten:
- implementierte Seiten
- implementierte Komponenten
- offene API-Lücken
- Sicherheitsprüfung
- Governance-Prüfung
- Testergebnis

Erwartetes Ergebnis:
GUI Update V2 PASS oder PASS_WITH_API_WARNINGS.
```

# Prompt 114 – Settings GUI Detail Sprint

```text
Aufgabe:

Implementiere die Settings GUI vollständig und robust.

Ziel:
Alle steuerbaren Jarvis-Konfigurationen sollen sichtbar, validierbar und sicher änderbar sein.

Keine Secret-Leaks.
Keine direkten Dateiänderungen aus der UI.
Alle Änderungen über PATCH /settings.

Seitenstruktur:

Settings
├── Provider
├── Voice
├── Security
├── Governance
├── RAG
├── Memory
├── Agents
├── Collaboration
└── UI

1. Provider Settings

Felder:
- active_provider
- fallback_provider
- active_model
- streaming_enabled
- request_timeout_seconds
- max_retries
- retry_backoff_seconds
- api_key_status
- api_key_update

Validierung:
- Timeout: 1–300 Sekunden
- Retries: 0–5
- Provider muss aus erlaubter Liste stammen
- API-Key nie anzeigen

2. Voice Settings

Felder:
- voice_input_provider
- voice_output_provider
- language
- tts_engine
- elevenlabs_key_status
- fallback_tts_enabled

Validierung:
- Sprache ISO-Code
- Provider aus erlaubter Liste
- Secret maskieren

3. Security Settings

Felder:
- security_gate_enabled
- terminal_safe_mode
- file_workspace_lock
- plugin_sandbox_enabled
- secret_scanner_enabled
- dependency_audit_enabled
- allowed_workspace_paths
- blocked_workspace_paths

Validierung:
- Workspace-Pfade dürfen nicht leer sein, wenn FileService aktiv ist.
- Systempfade als allowed_paths blockieren.
- Plugin Sandbox darf nicht deaktiviert werden, wenn Plugins aktiv sind.

4. Governance Settings

Felder:
- autonomy_level
- approval_expiry_minutes
- dry_run_enabled
- rollback_enabled
- privacy_mode_enabled
- retention_policy

Validierung:
- Autonomie-Level nur erlaubte Enum-Werte.
- Approval Expiry: 1–1440 Minuten.
- Rollback darf nicht deaktiviert werden, wenn ChangeSets aktiv sind.
- Privacy Mode Änderung sichtbar bestätigen lassen.

5. RAG Settings

Felder:
- embedding_provider
- chunk_size_tokens
- chunk_overlap_tokens
- retrieval_score_threshold
- max_chunks_per_answer
- source_required

Validierung:
- Chunkgröße: 100–2000
- Overlap kleiner als Chunkgröße
- Score Threshold: 0.0–1.0
- Max Chunks: 1–20
- source_required darf nur mit Admin deaktiviert werden.

6. Memory Settings

Felder:
- memory_extraction_enabled
- review_queue_required
- aging_enabled
- conflict_detection_enabled
- merge_workflow_enabled
- sensitive_memory_policy

Validierung:
- review_queue_required darf nicht deaktiviert werden, wenn memory_extraction_enabled aktiv ist.
- sensitive_memory_policy darf SECRET nie automatisch speichern.

7. Agent Settings

Felder:
- agents_enabled
- max_steps_per_goal
- max_tool_calls_per_goal
- max_runtime_seconds
- reflection_enabled
- validation_pipeline_enabled

Validierung:
- Max Steps: 1–100
- Max Tool Calls: 0–50
- Runtime: 1–3600
- Validation Pipeline darf nicht deaktiviert werden, wenn Agents aktiv sind.

8. Collaboration Settings

Felder:
- collaboration_enabled
- max_agents_per_team
- max_revision_cycles
- arbitration_enabled
- consensus_builder_enabled
- shared_workspace_enabled

Validierung:
- Max Agents: 1–10
- Revision Cycles: 0–10
- Arbitration muss aktiv sein, wenn Collaboration aktiv ist.

9. UI Settings

Felder:
- theme
- language
- density
- sidebar_mode
- show_debug_info

Validierung:
- Enum-Werte prüfen.

10. UX-Regeln

- Jede Section hat Save Button.
- Änderungen werden lokal als dirty markiert.
- Ungültige Felder zeigen Inline-Fehler.
- Erfolgreiches Speichern zeigt Status.
- Fehler zeigt Result.error.message.
- Neustartpflichtige Änderungen zeigen Badge.
- Riskante Änderungen zeigen Approval/Dry-Run Hinweis.

11. Komponenten

Erstelle:
- SettingsPage
- SettingsSection
- SettingField
- SecretSettingField
- EnumSelect
- NumberInput
- ToggleField
- RestartRequiredBadge
- DirtyStateIndicator
- ValidationError
- SaveSettingsButton

12. API

Nutze:
GET /settings
PATCH /settings

Payload:
{
  "section": "provider|voice|security|governance|rag|memory|agents|collaboration|ui",
  "changes": {},
  "dry_run": false
}

Antwort:
Result Pattern.

13. Tests

Erstelle:
tests/ui/test_settings_provider.py
tests/ui/test_settings_security.py
tests/ui/test_settings_governance.py
tests/ui/test_settings_rag.py
tests/ui/test_settings_memory.py
tests/ui/test_settings_agents.py
tests/ui/test_settings_collaboration.py
tests/ui/test_settings_secret_masking.py

Akzeptanzkriterien:
- Alle Settings Sections rendern.
- Ungültige Werte werden blockiert.
- Secrets werden nie angezeigt.
- PATCH /settings wird korrekt aufgerufen.
- Riskante Settings zeigen Warnung.
- Restart-Badges erscheinen korrekt.
```

# Prompt 115 – GUI API Contract Backend Alignment

```text
Aufgabe:

Richte Backend und GUI API Contracts aufeinander aus.

Ziel:
Die GUI darf keine Mock-Endpunkte brauchen. Fehlende Endpunkte müssen sauber als Backend-Contracts ergänzt werden.

Prüfe:

Frontend API Calls:
- Dashboard
- Chat
- Tools
- Memory
- Tasks
- Projects
- RAG
- Agents
- Collaboration
- Governance
- Settings

Backend Routes:
- api/
- services/
- Result Pattern
- Auth Middleware

Erstelle Matrix:

docs/reports/gui_api_alignment_matrix.md

Spalten:
- Feature
- Frontend Component
- API Endpoint
- Backend Route vorhanden: yes/no
- Service vorhanden: yes/no
- Result Pattern: yes/no
- Auth geprüft: yes/no
- Status: PASS/WARNING/FAIL
- Fix

Implementiere fehlende Backend-Endpunkte minimal, aber korrekt.

Pflicht:
- GET /settings
- PATCH /settings
- GET /status
- GET /governance/status
- GET /security/status
- GET /approvals
- GET /audit
- GET /changesets
- GET /rollback
- GET /agents/executions
- GET /collaboration/runs

Regeln:
- Kein Endpoint liest Dateien direkt, wenn Service vorhanden ist.
- Kein Endpoint gibt Secrets zurück.
- Alle Responses Result Pattern.
- Schreibende Endpunkte brauchen Auth und Permission.
- Riskante Endpunkte erzeugen Approval statt Direkt-Ausführung.

Tests:
- tests/api/test_gui_contracts.py
- tests/api/test_settings_endpoints.py
- tests/api/test_secret_masking_api.py

Akzeptanzkriterien:
- GUI Contract Matrix ohne FAIL.
- Kritische Endpunkte geben keine Secrets aus.
- Settings GUI kann echte Daten laden und speichern.
```

# Prompt 116 – GUI Gate V2

```text
Aufgabe:

Führe GUI Gate V2 durch.

Prüfe:

1. Feature Coverage
- Dashboard
- Chat
- Tools
- Memory
- Tasks
- Projects
- RAG
- Agents
- Collaboration
- Governance
- Settings

2. Settings Coverage
- Provider
- Voice
- Security
- Governance
- RAG
- Memory
- Agents
- Collaboration
- UI

3. Security
- keine Secrets sichtbar
- Auth Token nicht geloggt
- riskante Aktionen über Approval
- CRITICAL blockiert
- API maskiert Secrets

4. Governance
- Privacy Mode global sichtbar
- Autonomie-Level sichtbar
- Data Classification sichtbar
- Retention Policy sichtbar
- Audit Log sichtbar
- ChangeSets sichtbar
- Rollback geschützt

5. RAG
- Quellen sichtbar
- Klassifizierung sichtbar
- Reindex möglich
- Importstatus sichtbar
- SECRET-Dokumente blockiert

6. Agenten
- Execution Plans sichtbar
- Agent Limits sichtbar
- Validation Reports sichtbar
- Reflection Reports sichtbar
- Kein direkter Toolstart

7. Collaboration
- Teams sichtbar
- Runs sichtbar
- Shared Workspace Snapshot sichtbar
- Consensus sichtbar
- Arbitration sichtbar
- Konflikte sichtbar

8. API Alignment
- alle GUI-Endpunkte vorhanden oder sauber dokumentiert
- keine Mock-Daten als finaler Zustand

Erstelle:
docs/reports/gui_gate_v2.md

Bewertung:
PASS / WARNING / FAIL

Release-Regel:
GUI Gate V2 darf nur PASS erhalten, wenn:
- keine Secrets in UI/API auftauchen
- Settings GUI echte Daten validiert und speichert
- Privacy Mode global sichtbar ist
- Governance-Aktionen geschützt sind
- RAG-Quellen angezeigt werden
- Agenten und Collaboration nur über Orchestrator laufen

Falls nicht PASS:
Erstelle Blockerliste mit:
- Blocker-ID
- Kategorie
- Datei/Komponente
- Risiko
- Fix
- Priorität
```

### 49. Benutzer

entwickle weiter

### 50. Assistent

# Prompt 117 – GUI Implementation Sprint V2 ausführen

```text
Aufgabe:

Entwickle die GUI weiter.

Setze Prompt 113 bis Prompt 116 vollständig um.

Priorität:
1. Settings GUI vollständig
2. API Contract Alignment
3. Governance Center
4. RAG Center
5. Agent Center
6. Collaboration Center
7. GUI Gate V2

Keine ZIP erstellen.

Akzeptanzkriterien:
- Settings GUI nutzt echte Daten über GET /settings.
- Settings GUI speichert über PATCH /settings.
- Secrets werden nie angezeigt.
- Privacy Mode ist global sichtbar.
- Governance-Aktionen sind geschützt.
- RAG-Dokumente zeigen Quellen und Klassifizierung.
- Agent Execution Plans sind sichtbar.
- Collaboration Runs sind sichtbar.
- GUI Gate V2 Report erstellt.
```

# Prompt 118 – Backend-Endpunkte für GUI vervollständigen

```text
Aufgabe:

Implementiere alle fehlenden Backend-Endpunkte für die GUI.

Pflicht-Endpunkte:

GET /status
GET /settings
PATCH /settings
GET /governance/status
GET /security/status
GET /approvals
POST /approvals/{id}/approve
POST /approvals/{id}/reject
GET /audit
GET /changesets
POST /changesets/{id}/apply
GET /rollback
POST /rollback/{id}
GET /agents/executions
GET /collaboration/runs
GET /rag/documents
POST /rag/import
POST /rag/documents/{id}/reindex

Regeln:
- Alle Responses im Result-Pattern.
- Keine Secrets in Responses.
- Schreibende Aktionen brauchen Auth und Permission.
- Riskante Aktionen erzeugen Approval.
- Keine direkte Dateioperation im API-Layer.

Tests:
- tests/api/test_gui_backend_endpoints.py
- tests/api/test_gui_secret_masking.py
- tests/api/test_settings_patch.py

Akzeptanzkriterien:
- Alle Endpunkte antworten stabil.
- Keine 500er bei fehlenden Daten.
- Empty States sind sauber.
```

# Prompt 119 – Settings GUI finalisieren

```text
Aufgabe:

Finalisiere die Settings GUI.

Implementiere Sections:

- Provider
- Voice
- Security
- Governance
- RAG
- Memory
- Agents
- Collaboration
- UI

Pflicht:
- Dirty State
- Inline Validation
- Save pro Section
- RestartRequiredBadge
- SecretSettingField
- Dry-Run Option bei riskanten Änderungen
- Approval-Hinweis bei Governance/Security-Änderungen

Validierung:
- Timeout 1–300
- Retries 0–5
- Chunkgröße 100–2000
- Overlap < Chunkgröße
- Score Threshold 0.0–1.0
- Max Chunks 1–20
- Max Agents 1–10
- Revision Cycles 0–10

Regeln:
- API-Keys nur als vorhanden/nicht vorhanden anzeigen.
- Secret-Update nur schreiben, nie lesen.
- Validation Pipeline darf nicht deaktiviert werden, wenn Agents aktiv sind.
- Arbitration darf nicht deaktiviert werden, wenn Collaboration aktiv ist.
- Review Queue darf nicht deaktiviert werden, wenn Memory Extraction aktiv ist.

Akzeptanzkriterien:
- Ungültige Werte blockieren Save.
- PATCH /settings enthält nur geänderte Felder.
- Secrets erscheinen nie im DOM als Klartext.
```

# Prompt 120 – GUI Gate V2 durchführen

```text
Aufgabe:

Führe GUI Gate V2 durch.

Erstelle Bericht:

docs/reports/gui_gate_v2.md

Bewerte:

1. Feature Coverage
2. Settings Coverage
3. Security
4. Governance
5. RAG
6. Agenten
7. Collaboration
8. API Alignment
9. Secret Masking
10. Privacy Mode

Bewertung:
PASS / WARNING / FAIL

Release-Regel:
GUI Gate V2 ist nur PASS, wenn:

- keine Secrets in UI/API auftauchen
- Settings GUI echte Daten lädt und speichert
- Privacy Mode global sichtbar ist
- Governance-Aktionen geschützt sind
- RAG-Quellen sichtbar sind
- Agenten nur über Orchestrator laufen
- Collaboration nur über Orchestrator läuft
- keine finalen Mock-Daten verwendet werden

Falls nicht PASS:
Erstelle zusätzlich:

docs/reports/gui_gate_v2_blockers.md
```

# Prompt 121 – Masterplan nach GUI Gate aktualisieren

```text
Aufgabe:

Aktualisiere docs/masterplan.md nach GUI Gate V2.

Setze Status:

GUI:
PASS / WARNING / FAIL gemäß gui_gate_v2.md

Settings GUI:
PASS / WARNING / FAIL

API Alignment:
PASS / WARNING / FAIL

Ergänze Abschnitt:

GUI V2 Baseline

Inhalt:
- implementierte Seiten
- implementierte Settings Sections
- vorhandene API-Endpunkte
- offene API-Lücken
- Security-Status
- Governance-Status
- bekannte Limitierungen

Regel:
Masterplan darf keinem Gate-Report widersprechen.
```

### 51. Benutzer

weiter

### 52. Assistent

# Prompt 122 – GUI V2 Blocker-Fix Sprint

```text
Aufgabe:

Entwickle nach GUI Gate V2 gezielt weiter.

Ziel:
Alle WARNING/FAIL aus gui_gate_v2.md und gui_gate_v2_blockers.md beheben.

Vorgehen:

1. Reports lesen
- docs/reports/gui_gate_v2.md
- docs/reports/gui_gate_v2_blockers.md
- docs/reports/gui_api_alignment_matrix.md

2. Blocker klassifizieren
Kategorien:
- API fehlt
- Service fehlt
- UI zeigt Mock-Daten
- Secret Masking unvollständig
- Privacy Mode unvollständig
- Settings Validation fehlt
- Governance-Aktion ungeschützt
- RAG-Quelle fehlt
- Agent/Collaboration umgeht Orchestrator

3. Fixes umsetzen
Für jeden Blocker:
- betroffene Datei identifizieren
- minimalen robusten Fix implementieren
- Test ergänzen
- Report aktualisieren

4. Pflichtregeln
- Keine finalen Mock-Daten.
- Keine Secrets im UI-State.
- Keine Secrets im API-Response.
- Keine Governance-Aktion ohne Auth + Permission + Approval.
- Keine Agent-/Collaboration-Aktion ohne Orchestrator.
- Keine RAG-Antwort ohne SourceList.

Akzeptanzkriterien:
- gui_gate_v2.md zeigt PASS.
- gui_gate_v2_blockers.md zeigt 0 offene Blocker.
- Tests grün.
```

# Prompt 123 – UI Mock-Daten entfernen

```text
Aufgabe:

Entferne alle finalen Mock-Daten aus der GUI.

Prüfe:
- Dashboard
- Tools
- Memory
- Tasks
- Projects
- RAG
- Agents
- Collaboration
- Governance
- Settings

Regeln:
- Mock-Daten nur noch in Storybook/Testfixtures erlaubt.
- Produktive UI nutzt API Client.
- Fehlende API-Daten zeigen Empty State.
- API-Fehler zeigen Error State.
- Loading State während Requests.

Erstelle:
docs/reports/gui_mock_data_audit.md

Tests:
- tests/ui/test_no_production_mock_data.py
- tests/ui/test_empty_states.py
- tests/ui/test_error_states.py

Akzeptanzkriterien:
- Keine produktive Seite rendert harte Beispielwerte.
- Empty States sind verständlich.
- Error States zeigen keine technischen Secrets.
```

# Prompt 124 – Settings Validation Hardening

```text
Aufgabe:

Härte die Settings GUI Validierung.

Prüfe alle Settings Sections:

- Provider
- Voice
- Security
- Governance
- RAG
- Memory
- Agents
- Collaboration
- UI

Implementiere zentrale Validierung:

webui/frontend/src/lib/settingsValidation.ts

Regeln:
- Frontend validiert vor PATCH.
- Backend validiert erneut.
- PATCH enthält nur geänderte Felder.
- Ungültige Werte blockieren Save.
- Abhängige Regeln prüfen.

Abhängige Regeln:
- Overlap < Chunkgröße
- source_required darf nur Admin deaktivieren
- review_queue_required darf nicht deaktiviert werden, wenn memory_extraction_enabled aktiv ist
- validation_pipeline_enabled darf nicht deaktiviert werden, wenn agents_enabled aktiv ist
- arbitration_enabled darf nicht deaktiviert werden, wenn collaboration_enabled aktiv ist
- rollback_enabled darf nicht deaktiviert werden, wenn ChangeSets aktiv sind
- plugin_sandbox_enabled darf nicht deaktiviert werden, wenn Plugins aktiv sind

Tests:
- tests/ui/test_settings_validation_dependencies.py
- tests/api/test_settings_backend_validation.py

Akzeptanzkriterien:
- Frontend und Backend verhindern ungültige Konfiguration.
- Fehler werden feldbezogen angezeigt.
```

# Prompt 125 – Secret Masking End-to-End

```text
Aufgabe:

Implementiere Secret Masking End-to-End.

Bereiche:
- API Responses
- Logs
- Audit Log
- UI State
- Settings
- Chat
- Tool Results
- RAG Metadata
- Memory Review Queue

Neue/zu prüfende Funktionen:
- mask_secret_value()
- mask_object_recursive()
- redact_for_ui()
- redact_for_log()

Regeln:
- API-Key-Werte nie ausliefern.
- Secret-Felder nur als status: present/missing anzeigen.
- Token nie im Browser-Log.
- Audit Log speichert nur maskierte Details.
- Memory Review zeigt Secret-Kandidaten nicht als Klartext.
- Chat Output blockiert SECRET über Validation Pipeline.

Tests:
- tests/api/test_secret_masking_e2e.py
- tests/ui/test_no_secret_in_dom.py
- tests/unit/test_recursive_redaction.py

Akzeptanzkriterien:
- Test mit künstlichem API-Key findet keinen Klartext in API, UI, Logs, Audit, Memory.
```

# Prompt 126 – Governance Actions Hardening

```text
Aufgabe:

Härte alle Governance-Aktionen in GUI und API.

Aktionen:
- Approval approve/reject
- ChangeSet apply
- Rollback execute
- Privacy Mode toggle
- Autonomy Level change
- Policy reload
- Retention cleanup
- Plugin enable/disable
- Tool enable/disable

Regeln:
- Jede schreibende Aktion braucht Auth.
- Jede riskante Aktion braucht Permission.
- HIGH erzeugt Approval.
- CRITICAL blockiert oder Admin + Approval.
- Jede Aktion erzeugt Audit Event.
- UI zeigt RiskBadge und Folgenabschätzung.

Tests:
- tests/api/test_governance_actions_auth.py
- tests/api/test_governance_actions_approval.py
- tests/ui/test_governance_action_protection.py

Akzeptanzkriterien:
- Keine Governance-Aktion ist direkt ungeschützt ausführbar.
```

# Prompt 127 – RAG Source Enforcement in GUI

```text
Aufgabe:

Erzwinge Quellenanzeige in der GUI.

Bereiche:
- Chat
- RAG Center
- Document Detail
- Retrieval Test

Regeln:
- Wenn Antwort `used_rag_context=true`, muss SourceList sichtbar sein.
- Wenn sources leer sind, Antwort als BLOCKED darstellen.
- Jede Source zeigt:
  - Dokumentname
  - Chunk-ID
  - Seite falls vorhanden
  - Score
  - Klassifizierung
- SECRET-Sources werden nicht angezeigt, sondern als blocked_source_count zusammengefasst.

Tests:
- tests/ui/test_rag_answer_requires_sources.py
- tests/ui/test_secret_sources_blocked.py
- tests/api/test_rag_response_sources_contract.py

Akzeptanzkriterien:
- Keine RAG-Antwort ohne sichtbare Quelle.
```

# Prompt 128 – Agent/Collaboration Orchestrator Enforcement

```text
Aufgabe:

Erzwinge Orchestrator-Nutzung für Agenten und Collaboration.

Bereiche:
- Agent Center
- Collaboration Center
- API Routes
- Services

Regeln:
- UI darf keinen Agent direkt starten.
- UI darf kein Team direkt starten.
- Start läuft über Orchestrator Endpoint.
- Tool Calls werden nur als Orchestrator Events angezeigt.
- Direct Tool Calls aus Agent-Komponenten entfernen.
- Execution Plan Pflicht für Agent Runs.
- Collaboration Protocol Pflicht für Team Runs.

API:
POST /orchestrator/goals
GET /orchestrator/executions/{id}
POST /collaboration/runs

Tests:
- tests/api/test_orchestrator_enforcement.py
- tests/ui/test_no_direct_agent_start.py
- tests/ui/test_collaboration_uses_protocol.py

Akzeptanzkriterien:
- Agenten und Teams können keine Tools direkt auslösen.
```

# Prompt 129 – GUI Performance Baseline

```text
Aufgabe:

Erstelle Performance Baseline für GUI.

Prüfe:
- Dashboard Initial Load
- Settings Load
- Chat Streaming
- Audit Log Table mit 1000 Einträgen
- RAG Documents Table mit 1000 Dokumenten
- Memory Table mit 1000 Memories
- Agent Execution View mit 100 Steps

Implementiere:
- Pagination
- Lazy Loading
- Virtualized Tables für große Listen
- Request Debouncing bei Suche
- AbortController für Requests

Erstelle:
docs/reports/gui_performance_baseline.md

Akzeptanzkriterien:
- Große Tabellen blockieren UI nicht.
- Chat Streaming bleibt bedienbar.
- Requests sind abbrechbar.
```

# Prompt 130 – GUI V2 Final Gate

```text
Aufgabe:

Führe GUI V2 Final Gate durch.

Prüfe:
- Feature Coverage
- Settings Coverage
- API Alignment
- Secret Masking
- Privacy Mode
- Governance Actions
- RAG Sources
- Agent Orchestrator
- Collaboration Protocol
- Mock Data
- Performance
- Tests
- Dokumentation

Erstelle:
docs/reports/gui_v2_final_gate.md

Bewertung:
PASS / WARNING / FAIL

Release-Regel:
GUI V2 PASS nur wenn:
- 0 FAIL
- 0 offene Security-Warnings
- 0 offene Governance-Warnings
- keine produktiven Mock-Daten
- keine Secrets in UI/API/Logs
- Settings schreiben echte validierte Werte
- RAG zeigt Quellen
- Agenten/Teams laufen über Orchestrator
```

### 53. Assistent

# Prompt 131 – GUI V2 Release Fix Sprint

```text
Aufgabe:

Setze alle offenen Punkte aus GUI V2 Final Gate um.

Lies zuerst:

- docs/reports/gui_v2_final_gate.md
- docs/reports/gui_gate_v2.md
- docs/reports/gui_gate_v2_blockers.md
- docs/reports/gui_api_alignment_matrix.md
- docs/reports/gui_performance_baseline.md
- docs/reports/gui_mock_data_audit.md

Ziel:
GUI V2 von PASS_WITH_WARNINGS oder WARNING auf PASS bringen.

Fix-Reihenfolge:

1. Security-Warnings
2. Governance-Warnings
3. Secret Masking
4. Privacy Mode
5. Settings Persistence
6. RAG Sources
7. Orchestrator Enforcement
8. Mock Data Removal
9. Performance
10. Dokumentation

Regeln:
- Keine neue Funktion ohne Test.
- Keine kosmetischen Änderungen vor Blocker-Fixes.
- Keine finalen Mock-Daten.
- Keine direkte Datei-/Tool-/Agent-Ausführung aus UI.
- Alle Schreibaktionen über API + Auth + Permission + Approval.

Akzeptanzkriterien:
- gui_v2_final_gate.md zeigt PASS.
- 0 FAIL.
- 0 Security-Warnings.
- 0 Governance-Warnings.
```

# Prompt 132 – Dashboard Finalisierung

```text
Aufgabe:

Finalisiere das Dashboard.

Pflichtdaten:
- Release Status
- System Health
- Provider Status
- Workspace Status
- Privacy Mode
- Autonomy Level
- Governance Gate
- Security Gate
- GUI Gate
- RAG Status
- Agent Status
- Collaboration Status
- offene Approvals
- kritische Audit Events
- offene Blocker

Regeln:
- Dashboard nutzt nur GET /status und ergänzende Service-Endpunkte.
- Keine hartcodierten PASS-Werte.
- Fehlende Daten zeigen UNKNOWN, nicht PASS.
- Kritische Blocker immer oben anzeigen.
- Privacy Mode prominent anzeigen.

Tests:
- tests/ui/test_dashboard_no_fake_pass.py
- tests/ui/test_dashboard_blockers_visible.py
- tests/api/test_status_endpoint_contract.py

Akzeptanzkriterien:
- Dashboard kann keinen falschen grünen Status anzeigen.
```

# Prompt 133 – Chat UI Finalisierung

```text
Aufgabe:

Finalisiere Chat UI.

Pflicht:
- Streaming
- Stop Generation
- Tool Call Timeline
- SourceList
- Memory Context List
- Project Context Anzeige
- Token Budget View
- Validation Warning Panel
- Blocked Response State
- Privacy Mode Speicherhinweis

Regeln:
- used_rag_context=true ohne sources => BLOCKED.
- SECRET im Chat Response => BLOCKED.
- Validation Blocker verhindert Ausgabe.
- Tool-Erfolge nur anzeigen, wenn ToolResult success=true.
- Simulierte oder NOT_IMPLEMENTED Tools nicht als Erfolg darstellen.

Tests:
- tests/ui/test_chat_blocked_states.py
- tests/ui/test_chat_tool_truth.py
- tests/ui/test_chat_privacy_mode_notice.py

Akzeptanzkriterien:
- Chat zeigt keine falschen Erfolge.
- Chat zeigt keine RAG-Antwort ohne Quelle.
```

# Prompt 134 – Tool Center Finalisierung

```text
Aufgabe:

Finalisiere Tool Center.

Pflicht:
- Tool Registry anzeigen
- Tool Contract anzeigen
- Risk Level anzeigen
- Requires Confirmation anzeigen
- Timeout anzeigen
- letzter Lauf
- letzter Fehler
- Health Check
- Enable/Disable mit Permission
- Test Run über Approval bei HIGH/CRITICAL

Regeln:
- NOT_IMPLEMENTED Tools klar markieren.
- Unavailable Tools nicht testbar machen.
- Critical Tools blockieren.
- Kein direkter Toolaufruf aus UI.

Tests:
- tests/ui/test_tool_center_contracts.py
- tests/ui/test_tool_center_risk_controls.py
- tests/api/test_tool_center_permissions.py

Akzeptanzkriterien:
- Tool Center kann keine riskante Aktion direkt ausführen.
```

# Prompt 135 – Memory Center Finalisierung

```text
Aufgabe:

Finalisiere Memory Center.

Pflicht:
- Memory Liste
- Search
- Score Anzeige
- Confidence Anzeige
- Aging Anzeige
- DataClassificationBadge
- Review Queue
- Conflict Reports
- Merge Vorschläge
- Approval Flow

Regeln:
- SECRET Memories nie anzeigen.
- SENSITIVE_PERSONAL nur mit Permission + Hinweis.
- Memory Merge braucht Approval.
- Conflict Resolution löscht nichts automatisch.
- Privacy Mode deaktiviert Memory-Operationen.

Tests:
- tests/ui/test_memory_secret_hidden.py
- tests/ui/test_memory_review_queue.py
- tests/ui/test_memory_conflicts.py
- tests/ui/test_memory_privacy_mode_disabled.py

Akzeptanzkriterien:
- Memory Center verletzt keine Data-Policy.
```

# Prompt 136 – RAG Center Finalisierung

```text
Aufgabe:

Finalisiere RAG Center.

Pflicht:
- Dokumentliste
- Import Queue
- Import Status
- Data Classification
- Duplicate Status
- Chunk Count
- Embedding Status
- Source Capability
- Project Assignment
- Tags
- Retrieval Test
- Reindex Action

Regeln:
- SECRET-Dokumente nicht für Retrieval freigeben.
- Import im Privacy Mode blockieren oder nur volatile ausführen.
- Reindex braucht Permission.
- Retrieval Test zeigt Quellen.
- Fehlerhafte Dokumente mit failed status anzeigen.

Tests:
- tests/ui/test_rag_secret_documents_blocked.py
- tests/ui/test_rag_import_states.py
- tests/ui/test_rag_retrieval_sources.py
- tests/api/test_rag_document_contract.py

Akzeptanzkriterien:
- RAG Center zeigt korrekte Quelle/Klassifizierung je Dokument.
```

# Prompt 137 – Agent Center Finalisierung

```text
Aufgabe:

Finalisiere Agent Center.

Pflicht:
- Agent Liste
- Agent Status
- Agent Role
- Agent Limits
- Execution Plans
- Step Status
- Tool Call Timeline
- Validation Reports
- Reflection Reports
- Stop Execution

Regeln:
- Agent Start nur über Orchestrator.
- Kein direkter Toolaufruf.
- Execution Plan Pflicht.
- Limitverletzungen sichtbar anzeigen.
- Reflection im Privacy Mode blockieren.

Tests:
- tests/ui/test_agent_execution_plan_visible.py
- tests/ui/test_agent_no_direct_tool_start.py
- tests/ui/test_agent_limits_visible.py
- tests/api/test_agent_orchestrator_contract.py

Akzeptanzkriterien:
- Agent Center ist reine Orchestrator-Sicht.
```

# Prompt 138 – Collaboration Center Finalisierung

```text
Aufgabe:

Finalisiere Collaboration Center.

Pflicht:
- Agent Teams
- Team Status
- Collaboration Runs
- Protocol Phases
- Shared Workspace Snapshot
- Consensus Report
- Arbitration Report
- Conflict Report
- Team Limits
- Human Approval Status

Regeln:
- Team Start nur über Collaboration Protocol.
- Shared Workspace zeigt keine SECRET-Daten.
- Policy Conflict nie automatisch lösen.
- HIGH/CRITICAL Konflikte brauchen Approval.
- Privacy Mode blockiert persistente Reports.

Tests:
- tests/ui/test_collaboration_protocol_phases.py
- tests/ui/test_collaboration_no_secret_workspace.py
- tests/ui/test_collaboration_arbitration_visible.py
- tests/ui/test_collaboration_policy_conflict_approval.py

Akzeptanzkriterien:
- Collaboration Center macht Konflikte und Entscheidungen nachvollziehbar.
```

# Prompt 139 – Governance Center Finalisierung

```text
Aufgabe:

Finalisiere Governance Center.

Pflicht:
- Autonomy Level
- Approval Queue
- ChangeSets
- Rollback Points
- Policy Decisions
- Audit Log
- Privacy Mode
- Retention Policy
- Data Classification Rules

Aktionen:
- Approval approve/reject
- ChangeSet apply
- Rollback request
- Policy Decision explain
- Privacy Mode toggle
- Autonomy Level change

Regeln:
- Jede Aktion über API.
- Jede riskante Aktion mit Permission.
- HIGH erzeugt Approval.
- CRITICAL blockiert oder Admin + Approval.
- Jede Entscheidung auditiert.
- Secrets im Audit Log maskieren.

Tests:
- tests/ui/test_governance_approval_queue.py
- tests/ui/test_governance_changeset_diff.py
- tests/ui/test_governance_rollback_permission.py
- tests/ui/test_governance_audit_secret_masking.py

Akzeptanzkriterien:
- Governance Center kann keine Policy umgehen.
```

# Prompt 140 – Settings GUI Final Gate

```text
Aufgabe:

Führe Final Gate nur für Settings GUI durch.

Prüfe Sections:
- Provider
- Voice
- Security
- Governance
- RAG
- Memory
- Agents
- Collaboration
- UI

Prüfe:
- Daten laden
- Dirty State
- Inline Validation
- Save pro Section
- PATCH enthält nur Änderungen
- Backend Validation
- Secret Masking
- RestartRequiredBadge
- Risky Change Hinweis
- Permission Checks

Erstelle:
docs/reports/settings_gui_final_gate.md

Bewertung:
PASS / WARNING / FAIL

Release-Regel:
PASS nur wenn:
- keine Secrets sichtbar
- alle Sections echte Daten laden
- alle Sections speichern
- ungültige Werte blockiert werden
- abhängige Regeln greifen
```

### 54. Benutzer

weiter

### 55. Benutzer

weiter

### 56. Assistent

# Prompt 141 – Settings Backend Finalisierung

```text
Aufgabe:

Finalisiere das Settings Backend.

Ziel:
Die Settings GUI darf nur echte validierte Backend-Daten anzeigen und speichern.

Pflicht:

1. GET /settings

Liefert alle Sections:

- provider
- voice
- security
- governance
- rag
- memory
- agents
- collaboration
- ui

Response:
Result Pattern.

Secrets:
- niemals Klartext
- nur status:
  - present
  - missing
  - invalid
  - unknown

2. PATCH /settings

Payload:
{
  "section": "",
  "changes": {},
  "dry_run": false
}

Regeln:
- Nur erlaubte Sections.
- Nur erlaubte Felder.
- Backend validiert erneut.
- PATCH schreibt nur geänderte Felder.
- Riskante Änderungen erzeugen Approval.
- Restart-pflichtige Änderungen werden markiert.
- Secrets werden nur geschrieben, nie gelesen.
- Jede Änderung erzeugt Audit Event.

3. Validierung

Pflichtregeln:
- timeout: 1–300
- retries: 0–5
- chunk_size_tokens: 100–2000
- chunk_overlap_tokens < chunk_size_tokens
- score_threshold: 0.0–1.0
- max_chunks_per_answer: 1–20
- max_agents_per_team: 1–10
- max_revision_cycles: 0–10
- validation_pipeline darf nicht aus, wenn agents aktiv
- arbitration darf nicht aus, wenn collaboration aktiv
- review_queue darf nicht aus, wenn memory_extraction aktiv
- rollback darf nicht aus, wenn ChangeSets aktiv
- plugin_sandbox darf nicht aus, wenn Plugins aktiv

4. Tests

Erstelle:
tests/api/test_settings_get_contract.py
tests/api/test_settings_patch_validation.py
tests/api/test_settings_secret_status.py
tests/api/test_settings_risky_changes.py

Akzeptanzkriterien:
- GET /settings liefert keine Secrets.
- PATCH /settings validiert korrekt.
- Riskante Änderungen laufen nicht direkt durch.
- Settings GUI kann ohne Mock-Daten arbeiten.
```

# Prompt 142 – GUI Auth und Permission Handling

```text
Aufgabe:

Implementiere konsistentes Auth- und Permission-Handling in der GUI.

Ziel:
Die GUI darf keine Aktionen anzeigen oder ausführen, für die der Nutzer keine Berechtigung hat.

Implementiere:

1. Permission Model im Frontend

Neue Datei:
webui/frontend/src/lib/permissions.ts

Funktionen:
- hasPermission()
- canExecuteAction()
- getRequiredPermission()
- explainMissingPermission()

2. Permission-Aware Components

Komponenten:
- PermissionGate
- DisabledActionTooltip
- ProtectedButton
- RiskAwareActionButton

3. Betroffene Bereiche:
- Tool Center
- Governance Center
- Settings
- RAG Center
- Agent Center
- Collaboration Center
- Memory Center

Regeln:
- Nicht erlaubte Aktionen disabled anzeigen.
- Fehlende Permission erklärbar machen.
- UI darf keine blockierten API-Calls auslösen.
- Backend bleibt trotzdem maßgeblich.
- Admin-only Aktionen klar markieren.

4. Tests

Erstelle:
tests/ui/test_permission_gate.py
tests/ui/test_protected_buttons.py
tests/ui/test_admin_only_actions.py
tests/api/test_permission_backend_enforcement.py

Akzeptanzkriterien:
- Nutzer ohne Permission kann keine riskante Aktion aus UI auslösen.
- Backend blockiert direkte API-Calls trotzdem.
```

# Prompt 143 – Approval Queue UX finalisieren

```text
Aufgabe:

Finalisiere Approval Queue UX.

Bereiche:
- Dashboard
- Governance Center
- Tool Center
- Settings
- Collaboration Center

Anzeigen:
- Approval ID
- Aktion
- Risk Level
- angefordert von
- Zusammenfassung
- Details
- Ablaufzeit
- Status
- Policy-Grund
- betroffene Ressourcen

Aktionen:
- approve
- reject
- details öffnen
- ChangeSet ansehen
- Risikoauswirkung ansehen

Regeln:
- HIGH braucht Approval.
- CRITICAL braucht Admin + Approval oder bleibt blockiert.
- Abgelaufene Approvals nicht ausführbar.
- Approval-Entscheidung erzeugt Audit Event.
- SECRET Details maskieren.

Tests:
- tests/ui/test_approval_queue_rendering.py
- tests/ui/test_approval_expired_disabled.py
- tests/ui/test_approval_secret_masking.py
- tests/api/test_approval_decision_audit.py

Akzeptanzkriterien:
- Approval Queue ist bedienbar und auditierbar.
```

# Prompt 144 – ChangeSet Diff Viewer finalisieren

```text
Aufgabe:

Finalisiere ChangeSet Diff Viewer.

Bereiche:
- Governance Center
- CodingAgent Reports
- Approval Queue

Anzeigen:
- ChangeSet ID
- Titel
- Summary
- Status
- Risk Level
- betroffene Dateien/Konfigurationen
- Diff
- before_hash
- after_hash
- Rollback-Verfügbarkeit

Aktionen:
- ChangeSet prüfen
- Apply anfordern
- Approval öffnen
- Rollback Point anzeigen

Regeln:
- Apply nicht direkt bei HIGH/CRITICAL.
- SECRET Inhalte im Diff maskieren.
- Dateiänderungen nur über FileService.
- Rollback Point Pflicht vor Apply.

Tests:
- tests/ui/test_changeset_diff_viewer.py
- tests/ui/test_changeset_secret_masking.py
- tests/api/test_changeset_apply_requires_approval.py
- tests/api/test_changeset_rollback_point_required.py

Akzeptanzkriterien:
- Kein ChangeSet wird blind angewendet.
```

# Prompt 145 – Rollback UX finalisieren

```text
Aufgabe:

Finalisiere Rollback UX.

Bereiche:
- Governance Center
- ChangeSet Detail
- Dashboard Blocker Panel

Anzeigen:
- Rollback Points
- betroffene Ressourcen
- erstellt durch
- Zeitpunkt
- Hash
- Risk Level
- Restore-Status

Aktionen:
- Rollback Details öffnen
- Rollback anfordern
- Restore-Ergebnis anzeigen

Regeln:
- Rollback braucht Admin Permission.
- Rollback erzeugt Approval bei HIGH.
- Rollback erzeugt Audit Event.
- Rollback darf keine SECRET-Daten anzeigen.

Tests:
- tests/ui/test_rollback_points_rendering.py
- tests/ui/test_rollback_admin_only.py
- tests/api/test_rollback_requires_permission.py
- tests/api/test_rollback_audit_event.py

Akzeptanzkriterien:
- Rollback ist sichtbar, geschützt und nachvollziehbar.
```

# Prompt 146 – Audit Log UX finalisieren

```text
Aufgabe:

Finalisiere Audit Log UX.

Bereiche:
- Governance Center
- Dashboard
- Security Center falls vorhanden

Anzeigen:
- Zeit
- Actor
- Event Type
- Risk Level
- Summary
- Policy Decision
- Hash Validity
- Details
- Masking Status

Funktionen:
- Suche
- Filter nach Event Type
- Filter nach Risk Level
- Filter nach Actor
- Pagination
- Detail Drawer

Regeln:
- SECRET niemals anzeigen.
- Große Logs paginiert laden.
- Hash-Kette Validierung anzeigen.
- Fehlerhafte Hash-Kette als CRITICAL markieren.

Tests:
- tests/ui/test_audit_log_filters.py
- tests/ui/test_audit_log_secret_masking.py
- tests/ui/test_audit_log_hash_status.py
- tests/api/test_audit_log_pagination.py

Akzeptanzkriterien:
- Audit Log ist für Governance nutzbar und sicher.
```

# Prompt 147 – Policy Decision UX finalisieren

```text
Aufgabe:

Finalisiere Policy Decision UX.

Bereiche:
- Governance Center
- Approval Queue
- Tool Center
- Settings

Anzeigen:
- Policy Name
- Entscheidung: allowed|blocked|approval_required
- Begründung
- Risk Level
- betroffene Regel
- betroffene Aktion
- Zeitstempel

Funktionen:
- Policy Decision erklären
- Policy-Historie anzeigen
- Blockierte Aktion nachvollziehen

Regeln:
- Policy Engine bleibt maßgeblich.
- UI darf Entscheidungen nicht überschreiben.
- Policy Reload nur Admin + Approval.

Tests:
- tests/ui/test_policy_decision_view.py
- tests/api/test_policy_decision_explain.py
- tests/ui/test_policy_reload_protected.py

Akzeptanzkriterien:
- Blockierungen sind erklärbar statt nur “Fehler”.
```

# Prompt 148 – GUI Accessibility und Bedienbarkeit

```text
Aufgabe:

Verbessere Accessibility und Bedienbarkeit der GUI.

Bereiche:
- Navigation
- Forms
- Settings
- Tables
- Modals
- Approval Dialoge
- Diff Viewer

Pflicht:
- Tastaturbedienbarkeit
- sichtbarer Fokus
- Labels für Inputs
- ARIA für Statusbadges
- verständliche Error Messages
- keine rein farbbasierte Statusinformation
- Tabellen mit Sortierung und Suche
- Dialoge mit Escape schließbar

Tests:
- tests/ui/test_accessibility_labels.py
- tests/ui/test_keyboard_navigation.py
- tests/ui/test_status_not_color_only.py

Akzeptanzkriterien:
- GUI ist ohne Maus grundlegend bedienbar.
- Status ist nicht nur über Farbe erkennbar.
```

# Prompt 149 – GUI Documentation Finalisierung

```text
Aufgabe:

Finalisiere GUI-Dokumentation.

Aktualisiere:

- docs/gui.md
- docs/settings_gui.md
- docs/governance_ui.md
- docs/rag_ui.md
- docs/agent_ui.md
- docs/collaboration_ui.md
- docs/api/gui_contracts.md
- docs/ui_state_model.md

Jede Doku enthält:
- Zweck
- Datenquelle/API
- Berechtigungen
- Fehlerzustände
- Security-Regeln
- Privacy-Mode-Verhalten
- bekannte Limitierungen

Akzeptanzkriterien:
- Dokumentation entspricht Code.
- Keine nicht implementierten Features als fertig beschreiben.
```

# Prompt 150 – GUI Release Gate V3

```text
Aufgabe:

Führe GUI Release Gate V3 durch.

Prüfe:

1. Feature Coverage
2. Settings Backend
3. Auth/Permissions
4. Approval UX
5. ChangeSet UX
6. Rollback UX
7. Audit Log UX
8. Policy Decision UX
9. Secret Masking
10. Privacy Mode
11. RAG Sources
12. Agent Orchestrator
13. Collaboration Protocol
14. Performance
15. Accessibility
16. Dokumentation

Erstelle:
docs/reports/gui_release_gate_v3.md

Bewertung:
PASS / WARNING / FAIL

Release-Regel:
PASS nur wenn:
- 0 FAIL
- 0 Security-Warnings
- 0 Governance-Warnings
- keine Secrets in UI/API/Logs
- keine finalen Mock-Daten
- Settings Backend echt und validiert
- Approval/ChangeSet/Rollback geschützt
- Audit Log paginiert und maskiert
- RAG Quellen sichtbar
- Agent/Collaboration nur über Orchestrator
- Grundlegende Accessibility erfüllt
```

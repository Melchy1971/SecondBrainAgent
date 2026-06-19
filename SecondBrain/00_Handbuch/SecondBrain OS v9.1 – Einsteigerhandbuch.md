## Inhaltsverzeichnis

1. Was ist SecondBrain OS?
2. Ordnerstruktur verstehen
3. Erster Start
4. Tagesablauf
5. KI-Chats importieren
6. Obsidian verwenden
7. Projekte anlegen
8. Suchen und Wissen finden
9. Dashboards und Berichte
10. Claude Desktop Integration
11. Wartung
12. Backup
13. Fehlerbehebung
14. Empfohlener Arbeitsablauf
15. Erweiterte Funktionen

---

# 1. Was ist SecondBrain OS?

SecondBrain OS ist ein lokales Wissensbetriebssystem.

Es:

- sammelt Wissen aus verschiedenen Quellen
- speichert alles als Markdown
- erstellt Zusammenfassungen
- erkennt Zusammenhänge
- erzeugt Empfehlungen
- baut einen Wissensgraphen auf
- unterstützt Projekte und Entscheidungen

Das gesamte Wissen bleibt lokal auf deinem Rechner.

---

# 2. Ordnerstruktur verstehen

## Hauptordner

```
H:\SecondBrainAgent├── SecondBrain├── SecondBrain-Inbox└── SecondBrain-Agent
```

---

## SecondBrain

Das eigentliche Wissensarchiv.

Beispiele:

```
05_Quellen10_DailyBriefings12_Decisions32_ExecutiveDashboard66_KnowledgeGraph75_SecondBrainOS76_WorkflowEngine77_RecommendationEngine87_ControlCenter99_System
```

---

## SecondBrain-Inbox

Temporäre Ablage für Importe.

Beispiele:

```
ChatGPTGeminiPerplexityPDFE-Mails
```

---

## SecondBrain-Agent

Enthält:

```
scriptsmodulesconfigmcp-serverdocs
```

Dies ist die technische Steuerzentrale.

---

# 3. Erster Start

PowerShell öffnen:

```
cd H:\SecondBrainAgent\SecondBrain-Agentpython scripts\menu.py
```

Das Menü erscheint:

```
1 = Import AI Exports2 = SecondBrain OS Cycle v83 = SecondBrain v9 Cycle4 = API Gateway10 = Release Gate11 = Regression Tests
```

---

# 4. Tagesablauf

## Morgens

### 1.

```
python scripts\import_ai_exports.py
```

Importiert:

- ChatGPT
- Gemini
- Perplexity

---

### 2.

```
python scripts\run_v9_cycle.py
```

Aktualisiert:

- Dashboards
- Wissensgraph
- Empfehlungen
- Digital Twin
- Learning Engine
- Control Center

---

### 3.

Obsidian:

```
Strg + R
```

---

# 5. KI-Chats importieren

# ChatGPT

Export:

```
SettingsData ControlsExport Data
```

ZIP speichern:

```
H:\SecondBrainAgent\SecondBrain-Inbox\ChatGPT\exports
```

Import:

```
python scripts\import_chatgpt_folder.py
```

---

# Gemini

ZIP:

```
H:\SecondBrainAgent\SecondBrain-Inbox\Gemini\exports
```

Import:

```
python scripts\import_gemini_folder.py
```

---

# Perplexity

ZIP:

```
H:\SecondBrainAgent\SecondBrain-Inbox\Perplexity\exports
```

Import:

```
python scripts\import_perplexity_folder.py
```

---

# Sammelimport

```
python scripts\import_ai_exports.py
```

---

# 6. Obsidian verwenden

Vault öffnen:

```
H:\SecondBrainAgent\SecondBrain
```

---

## Neue Notiz

```
Strg + N
```

---

## Verlinken

```
[[Projekt Wissensdatenbank]]
```

---

## Aufgaben

```
- [ ] API entwickeln- [ ] Meeting vorbereiten- [ ] Dokumentation schreiben
```

---

## Tags

```
#projekt#ki#sap#tischtennis
```

---

# 7. Projekte anlegen

In Claude:

```
/plan
```

Abfrage:

```
Projektname?
```

Beispiel:

```
Wissensdatenbank2026
```

Es wird automatisch erstellt:

```
01_Projekte└── Wissensdatenbank2026    ├── Inbox    ├── Meetings    ├── Entscheidungen    ├── Aufgaben    ├── Dokumente    └── Roadmap
```

---

# 8. Wissen finden

In Obsidian:

```
Strg + O
```

Suche:

```
SAP
```

oder:

```
Tischtennis
```

---

## Semantic Search

```
python scripts\semantic_search.py "SAP"
```

Beispiele:

```
python scripts\semantic_search.py "Docker"python scripts\semantic_search.py "Obsidian"python scripts\semantic_search.py "Tischtennis"
```

---

# 9. Dashboards

## Executive Dashboard

```
32_ExecutiveDashboard81_ExecutiveDashboard
```

Zeigt:

- offene Aufgaben
- Risiken
- Entscheidungen
- Wissensstand

---

## Control Center

```
87_ControlCenter
```

Zeigt:

- Modulstatus
- Importstatus
- Tagesroutine
- Systemübersicht

---

## Recommendation Engine

```
77_RecommendationEngine
```

Zeigt:

- Verbesserungsvorschläge
- Prioritäten
- Risiken
- Wissenslücken

---

# 10. Claude Desktop Integration

Start:

```
Claude Desktop
```

MCP-Server:

```
H:\SecondBrainAgent\SecondBrain-Agent\mcp-server\server.py
```

Verfügbare Tools:

```
run_v9_cyclerun_ai_importsrun_release_gate_v9run_regression_tests_v9get_control_center
```

Beispiele:

```
Importiere meine KI-Chats.
```

```
Führe den v9 Cycle aus.
```

```
Zeige das Control Center.
```

---

# 11. Wartung

Einmal pro Woche:

```
python scripts\check_paths_v9.pypython scripts\release_gate_v9.pypython scripts\run_regression_tests_v9.py
```

---

# 12. Backup

Backup:

```
H:\SecondBrainAgent
```

Empfohlen:

- externe Festplatte
- NAS
- Git-Repository ohne persönliche Daten

---

# 13. Fehlerbehebung

## Obsidian zeigt neue Dateien nicht

```
Strg + R
```

---

## Import funktioniert nicht

Prüfen:

```
dir H:\SecondBrainAgent\SecondBrain-Inbox\Gemini\exports
```

---

## Python funktioniert nicht

```
python --version
```

oder:

```
py --version
```

---

## Systemprüfung

```
python scripts\release_gate_v9.py
```

---

## Regressionstests

```
python scripts\run_regression_tests_v9.py
```

---

# 14. Empfohlener Arbeitsablauf

## Morgens

```
python scripts\import_ai_exports.pypython scripts\run_v9_cycle.py
```

---

## Tagsüber

- Notizen schreiben
- Projekte pflegen
- Aufgaben abhaken
- Entscheidungen dokumentieren

---

## Abends

```
python scripts\run_v9_cycle.py
```

Obsidian:

```
Strg + R
```

---

# 15. Erweiterte Funktionen

## Wissensgraph

```
66_KnowledgeGraph
```

---

## Digital Twin

```
86_DigitalTwinV6
```

---

## Learning Engine

```
78_LearningEngine
```

---

## Personal CRM

```
80_PersonalCRM
```

---

## Workflow Engine

```
76_WorkflowEngine
```

---

## Zielzustand

```
KI-Chats      ↓Inbox      ↓Importer      ↓Markdown      ↓Semantic Search      ↓Knowledge Graph      ↓Recommendations      ↓Digital Twin      ↓Executive Dashboard      ↓Control Center
```

Das System wird damit zu einem lokalen, quellenübergreifenden persönlichen Wissensbetriebssystem, das kontinuierlich Wissen sammelt, strukturiert und für Entscheidungen nutzbar macht.
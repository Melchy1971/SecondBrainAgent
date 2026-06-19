## Benutzerhandbuch für Einsteiger

### Version

v8.1.2 Production Edition

### Autor

Markus Dickscheit / SecondBrain OS

### Plattform

Windows · Obsidian · Claude Desktop · Ollama · MCP

---

# Inhaltsverzeichnis

1. Einführung
2. Systemübersicht
3. Ordnerstruktur
4. Installation
5. Erste Inbetriebnahme
6. Obsidian einrichten
7. Claude Desktop einrichten
8. Ollama einrichten
9. MCP einrichten
10. Das Hauptmenü
11. Informationen importieren
12. Semantic Search
13. Knowledge Graph
14. Projektverwaltung
15. Der neue /plan-Befehl
16. Meetings verwalten
17. Entscheidungen dokumentieren
18. Aufgabenverwaltung
19. Journal
20. Digital Twin
21. Project Intelligence
22. Decision Intelligence
23. Meeting Intelligence
24. Data Warehouse
25. SecondBrain OS Cycle
26. Obsidian Plugin
27. Backup
28. Updates
29. Fehlerbehebung
30. Empfohlene Arbeitsweise
31. Tastaturbefehle
32. FAQ

---

# 1. Einführung

SecondBrain OS ist ein lokales, KI-gestütztes Wissensmanagementsystem auf Basis von Obsidian.

Das System dient dazu:

- Wissen zu sammeln
- Projekte zu verwalten
- Informationen zu verknüpfen
- Entscheidungen zu dokumentieren
- Meetings auszuwerten
- Aufgaben zu verfolgen
- Informationen semantisch zu durchsuchen
- persönliche Wissensmuster zu erkennen

Alle Daten bleiben lokal auf dem eigenen Rechner.

---

# 2. Systemübersicht

Architektur:

Claude Desktop  
↓

MCP Server  
↓

SecondBrain Agent  
↓

Obsidian Vault  
↓

Knowledge Graph  
↓

Semantic Search  
↓

Digital Twin

---

# 3. Ordnerstruktur

## SecondBrain

H:\SecondBrainAgent\SecondBrain

Enthält sämtliche Informationen.

### Hauptordner

00_Inbox

Neue Informationen.

01_Projekte

Alle Projekte.

02_Wissen

Wissensartikel.

03_Personen

Kontakte.

04_Tasks

Aufgaben.

05_Quellen

Quellen.

06_Journal

Tagesnotizen.

07_Graph

Graphdateien.

65_SemanticSearch

Semantische Suchergebnisse.

66_KnowledgeGraph

Wissensgraph.

67_ProjectIntelligence

Projektanalysen.

68_DecisionIntelligence

Entscheidungsanalysen.

69_MeetingIntelligence

Meetinganalysen.

70_CalendarIntelligence

Kalenderinformationen.

71_DataWarehouse

Kennzahlen.

72_MCPEcosystem

MCP-Konfigurationen.

73_DigitalTwin

Persönliches Wissensmodell.

74_SelfImprovingKnowledge

Optimierungsvorschläge.

75_SecondBrainOS

Dashboard.

90_Templates

Vorlagen.

99_System

Technische Dateien.

---

# 4. Installation

Benötigt:

- Windows 10 oder 11
- Python 3.11+
- Obsidian
- Claude Desktop
- Ollama

Empfohlene Struktur:

H:\SecondBrainAgent  
├── SecondBrain  
├── SecondBrain-Inbox  
└── SecondBrain-Agent

---

# 5. Erste Inbetriebnahme

PowerShell öffnen:

```
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\menu.py
```

---

# 6. Obsidian einrichten

Vault öffnen:

H:\SecondBrainAgent\SecondBrain

Danach:

Einstellungen

↓

Community Plugins

↓

SecondBrain Agent aktivieren

---

# 7. Claude Desktop einrichten

Datei:

%APPDATA%\Claude\claude_desktop_config.json

Konfiguration:

```
{
  "mcpServers": {
    "secondbrain": {
      "command": "python",
      "args": [
        "H:\\SecondBrainAgent\\SecondBrain-Agent\\mcp-server\\server.py"
      ]
    }
  }
}
```

Claude neu starten.

---

# 8. Ollama einrichten

Installation:

[https://ollama.com](https://ollama.com)

Modelle installieren:

```
ollama pull llama3.1
ollama pull qwen
ollama pull deepseek-coder
```

Server starten:

```
ollama serve
```

---

# 9. MCP einrichten

Installation:

```
cd H:\SecondBrainAgent\SecondBrain-Agent\mcp-server
pip install -r requirements.txt
```

---

# 10. Das Hauptmenü

Start:

```
python scripts\menu.py
```

Funktionen:

1 Import

2 SecondBrain OS Cycle

3 Semantic Search

4 MCP Status

5 Connector Status

6 AI Healthcheck

7 Plugin Status

8 Release Gate

9 REST API

10 Pfade anzeigen

---

# 11. Informationen importieren

PDF:

```
python scripts\import_document.py "C:\Datei.pdf"
```

Word:

```
python scripts\import_document.py "C:\Datei.docx"
```

Excel:

```
python scripts\import_document.py "C:\Datei.xlsx"
```

---

# 12. Semantic Search

Menü:

3

Beispiel:

Cisco EA

Das System durchsucht:

- Titel
- Inhalte
- Tags
- Verknüpfungen

---

# 13. Knowledge Graph

Erkennt:

- Projekte
- Personen
- Aufgaben
- Entscheidungen
- Risiken
- Zusammenhänge

---

# 14. Projektverwaltung

Alle Projekte befinden sich unter:

01_Projekte

Jedes Projekt besitzt:

Projektübersicht

Aufgaben

Entscheidungen

Notizen

---

# 15. Der neue /plan-Befehl

In Claude:

/plan

Claude fragt:

Wie soll das Projekt heißen?

Beispiel:

Jarvis

Ergebnis:

01_Projekte  
└── Jarvis  
├── 00_Projektübersicht.md  
├── 01_Aufgaben.md  
├── 02_Entscheidungen.md  
└── 03_Notizen.md

---

# 16. Meetings verwalten

In Claude:

Erstelle ein Meeting für SAP P01.

Es wird erzeugt:

- Zusammenfassung
- Teilnehmer
- Aufgaben
- Risiken
- Follow-up

---

# 17. Entscheidungen dokumentieren

In Claude:

Erstelle eine Entscheidung zu Cisco EA.

Es werden erzeugt:

- Entscheidung
- Annahmen
- Alternativen
- Risiken
- Ergebnis

---

# 18. Aufgabenverwaltung

In Claude:

Erstelle eine Aufgabe.

Erzeugt:

- Beschreibung
- Projektbezug
- Status
- Nächster Schritt

---

# 19. Journal

In Claude:

Merke dir diese Unterhaltung.

Es wird automatisch ein Journaleintrag angelegt.

---

# 20. Digital Twin

Der Digital Twin erkennt:

- Interessen
- Arbeitsmuster
- Prioritäten
- Wissensschwerpunkte
- Risiken

---

# 21. Project Intelligence

Analysiert:

- offene Aufgaben
- Risiken
- Aktivität
- Empfehlungen

---

# 22. Decision Intelligence

Bewertet:

- Entscheidungsqualität
- fehlende Informationen
- Risiken
- Alternativen

---

# 23. Meeting Intelligence

Erkennt:

- Aufgaben
- Entscheidungen
- Risiken
- Follow-ups

---

# 24. Data Warehouse

Erzeugt Kennzahlen:

- Dokumente
- Aufgaben
- Entscheidungen
- Projekte
- Tags

---

# 25. SecondBrain OS Cycle

Start:

```
python scripts\run_secondbrain_os_cycle.py
```

Erzeugt:

Semantic Search

Knowledge Graph

Digital Twin

Dashboards

Analysen

Empfehlungen

---

# 26. Obsidian Plugin

Befehle:

Open Dashboard

Open API Status

Run Import

Run Intelligence Cycle

Run Governance

---

# 27. Backup

Regelmäßig sichern:

H:\SecondBrainAgent\SecondBrain

H:\SecondBrainAgent\SecondBrain-Inbox

H:\SecondBrainAgent\SecondBrain-Agent

Empfohlen:

täglich

---

# 28. Updates

Vor jedem Update:

1 Backup erstellen

2 ZIP entpacken

3 Dateien überschreiben

4 Obsidian neu starten

---

# 29. Fehlerbehebung

API:

```
python scripts\rest_api.py
```

Ollama:

```
ollama serve
```

MCP:

```
python scripts\mcp_status.py
```

---

# 30. Empfohlene Arbeitsweise

Morgens:

Import

Semantic Search

Dashboard prüfen

Tags prüfen

Abends:

SecondBrain OS Cycle

Projektstatus prüfen

Backups

---

# 31. Tastaturbefehle

Obsidian:

Strg + P

Befehlspalette öffnen

Strg + O

Datei öffnen

Strg + Shift + F

Volltextsuche

---

# 32. FAQ

Frage:  
Muss Obsidian immer geöffnet sein?

Antwort:  
Nein.

Frage:  
Brauche ich Internet?

Antwort:  
Nein.

Frage:  
Werden Daten an OpenAI gesendet?

Antwort:  
Nein, wenn ausschließlich Ollama genutzt wird.

Frage:  
Kann Claude direkt schreiben?

Antwort:  
Ja, über MCP.

Frage:  
Kann ich mehrere Vaults verwenden?

Antwort:  
Ja, durch Anpassung der Konfiguration.

Frage:  
Kann ich weitere KI-Modelle integrieren?

Antwort:  
Ja. ChatGPT, Claude, Gemini, Perplexity und Ollama werden unterstützt.

Ende des Benutzerhandbuchs.
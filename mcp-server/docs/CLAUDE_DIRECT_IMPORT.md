# Claude Direct Import für SecondBrain OS

## Ziel

Claude Desktop kann direkt in dein Obsidian Vault schreiben und daraus lesen.

## Installation

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent\mcp-server
pip install -r requirements.txt
```

## Claude Desktop Config

Datei öffnen:

```text
%APPDATA%\Claude\claude_desktop_config.json
```

Einfügen:

```json
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

Danach Claude Desktop vollständig neu starten.

## Verfügbare Tools

```text
create_note
append_note
read_note
search_notes
create_project
create_meeting
create_decision
create_task
create_journal
semantic_search
run_import
run_os_cycle
get_today_dashboard
```

## Beispiele in Claude

```text
Merke dir diese Unterhaltung als Journaleintrag.
```

```text
Erstelle daraus eine Projektnotiz für Jarvis.
```

```text
Suche alles zu Cisco EA.
```

```text
Starte den SecondBrain OS Cycle.
```

## Sicherheitsgrenzen

- Der MCP Server schreibt nur innerhalb von `H:\SecondBrainAgent\SecondBrain`.
- Pfade außerhalb des Vaults werden blockiert.
- Keine Datei wird gelöscht.
- Gleichnamige neue Notizen erhalten Zeitstempel.


## Neues Feature v8.1.2: /plan

Ziel:

```text
/plan
```

legt einen Projektordner unter:

```text
H:\SecondBrainAgent\SecondBrain\01_Projekte
```

an.

Da Claude bei Slash-Befehlen je nach Oberfläche unterschiedlich reagiert, gibt es zwei Varianten:

### Variante A

```text
Nutze secondbrain slash_command mit command="/plan" und argument="Jarvis".
```

### Variante B

```text
Nutze secondbrain create_project_folder und lege einen Projektordner "Jarvis" an.
```

Ergebnis:

```text
01_Projekte\Jarvis\
├── 00_Projektübersicht.md
├── 01_Aufgaben.md
├── 02_Entscheidungen.md
└── 03_Notizen.md
```

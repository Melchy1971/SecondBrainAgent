# SecondBrain Agent Plugin Installation

## Zielordner

Diese ZIP entpacken nach:

```text
H:\SecondBrainAgent\SecondBrain\.obsidian\plugins\
```

Danach muss der Ordner so aussehen:

```text
H:\SecondBrainAgent\SecondBrain\.obsidian\plugins\secondbrain-agent\
├── manifest.json
├── main.js
├── styles.css
└── INSTALLATION.md
```

## Obsidian aktivieren

1. Obsidian öffnen
2. Einstellungen
3. Community Plugins
4. Safe Mode / Restricted Mode aus
5. SecondBrain Agent aktivieren

## Lokale API starten

Für Plugin-Aktionen:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\rest_api.py
```

## Befehle in Obsidian

Mit `Strg + P`:

```text
SecondBrain Agent: Open SecondBrain Dashboard
SecondBrain Agent: Open SecondBrain API Status
SecondBrain Agent: Run Import
SecondBrain Agent: Run Intelligence Cycle
SecondBrain Agent: Run Governance
SecondBrain Agent: Show SecondBrain OS Cycle Command
```
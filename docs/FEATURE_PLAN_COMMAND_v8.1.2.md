# Feature v8.1.2 – /plan

## Ziel

Mit `/plan` wird ein neuer Projektordner unter `01_Projekte` erstellt.

## Verhalten

Claude fragt nach dem Projektnamen, falls keiner angegeben wurde.

## Technische Umsetzung

MCP Tools:

```text
create_project_folder(project_name, description="")
slash_command(command="/plan", argument="Projektname")
```

## Ergebnisstruktur

```text
SecondBrain\01_Projekte\Projektname\
├── 00_Projektübersicht.md
├── 01_Aufgaben.md
├── 02_Entscheidungen.md
└── 03_Notizen.md
```

## Beispiel in Claude

```text
/plan
```

Wenn Claude nicht automatisch fragt:

```text
Nutze secondbrain slash_command mit command="/plan" und argument="Jarvis".
```

oder:

```text
Nutze secondbrain create_project_folder und lege einen Projektordner "Jarvis" an.
```

# Claude MCP Arbeitsanweisung für SecondBrain

## Zweck

Claude darf Inhalte im Obsidian Vault lesen, analysieren, verbessern und neu verlinken.

## Erlaubte Bereiche

```text
H:\SecondBrainAgent\SecondBrain
H:\SecondBrainAgent\SecondBrain-Inbox
H:\SecondBrainAgent\SecondBrain-Agent
```

## Regeln

- Keine Dateien außerhalb der freigegebenen Ordner bearbeiten.
- Keine bestehenden Notizen löschen.
- Technische Systemdateien nur ändern, wenn ausdrücklich angefordert.
- Importierte Notizen verbessern, aber Frontmatter erhalten.
- Aufgaben nicht entfernen, sondern Status ändern.
- Review Queue regelmäßig abarbeiten.

## Standardauftrag an Claude

Prüfe die Datei in `99_System/claude_review`.
Verbessere Titel, Zusammenfassung, Tags und Backlinks.
Verschiebe unklare Inhalte aus `00_Inbox` in den passenden Zielordner.

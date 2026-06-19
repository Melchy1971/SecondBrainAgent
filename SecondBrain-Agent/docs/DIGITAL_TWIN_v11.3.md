# SecondBrain OS v11.3 – Digital Twin & Decision Engine

## Ziel

v11.3 ergänzt ein deterministisches persönliches Modell für Ziele, Projekte, Zeitbudget, Szenarien und Entscheidungen.

## Neue Befehle

```powershell
python launcher.py twin-status
python launcher.py twin-capacity 40 --fixed 8 --buffer 5
python launcher.py twin-add-project "Jarvis GUI" 6 --priority 2 --risk 2
python launcher.py twin-add-goal "TTR 1200" --target 1200 --current 1147 --unit TTR
python launcher.py twin-simulate "Neues Projekt" "Mobile Bridge:5:3"
python launcher.py decision-evaluate "Was zuerst bauen?" "Mobile Bridge:5:4:3:5:3" "Voice 2.0:4:3:2:4:4"
python launcher.py decision-history
```

## Bewertungslogik

Entscheidungen werden nicht durch ein LLM geraten. Der Score ist deterministisch:

```text
Score = Nutzen + strategischer Fit + Reversibilität - Risiko - Kapazitätsstrafe
```

Kapazitätsstrafe greift bei weniger als 3 freien Stunden pro Woche oder Überlast.

## Persistenz

```text
data/runtime/digital_twin_v113.json
data/runtime/decisions_v113.json
```

## Grenzen

- Keine medizinische Beratung
- Keine Finanzberatung
- Keine automatische Selbstoptimierung
- Keine echten Kalenderdaten ohne Connector-Sync

## Nutzen

Das System kann ab v11.3 Szenarien vergleichen, Überlast sichtbar machen und Entscheidungen mit nachvollziehbarem Score begründen.

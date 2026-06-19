# SecondBrain OS v12.7 – Digital Twin 2.0

## Ziel
Digital Twin 2.0 erweitert den bisherigen Ziel-/Projektstand um belastbare Entscheidungslogik.

## Komponenten
- Twin State Store
- Goal Model
- Project Model
- Habit Model
- Capacity Forecast
- Goal Forecast
- Scenario Engine
- Risk Model
- Decision Simulator

## Befehle
```powershell
python launcher.py twin2-status
python launcher.py twin2-add-goal ttr "TTR 1200" 1200 1147 points --deadline-days 120 --priority 4
python launcher.py twin2-add-project jarvis "Jarvis Desktop" --weekly-hours 4 --impact 0.8 --risk 0.3 --strategic-score 0.9
python launcher.py twin2-forecast
python launcher.py twin2-simulate-project p1 "Neues Projekt" --weekly-hours 6 --impact 0.7 --risk 0.5
python launcher.py twin2-decision p1 "Neues Projekt" --weekly-hours 6 --impact 0.7 --risk 0.5
```

## Metriken
- Load Ratio
- Free Hours
- Energy Risk
- Project Risk
- Goal On Track
- Decision Score

## Grenzen
- Deterministisches Modell.
- Keine medizinische, finanzielle oder rechtliche Beratung.
- Forecasts sind Entscheidungsindikatoren, keine Prognosegarantien.

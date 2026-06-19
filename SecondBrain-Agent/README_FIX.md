# Patch: Reasoning Engine v9.7 Sortierfehler

## Fehler

```text
TypeError: '<' not supported between instances of 'dict' and 'dict'
```

## Ursache

`sorted(rows, reverse=True)` verglich Tupel mit Dictionaries.

## Fix

Sortierung geändert auf:

```python
sorted(rows, key=lambda x: x["impact"], reverse=True)
```

## Installation

Diese ZIP nach folgendem Ordner entpacken:

```text
H:\SecondBrainAgent\SecondBrain-Agent
```

Dabei die vorhandene Datei überschreiben:

```text
H:\SecondBrainAgent\SecondBrain-Agent\secondbrain\reasoning_engine_v97.py
```

## Danach testen

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\run_v97_cycle.py
python scripts\run_v98_cycle.py
```

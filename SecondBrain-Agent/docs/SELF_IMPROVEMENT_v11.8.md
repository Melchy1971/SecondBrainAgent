# SecondBrain OS v11.8 – Self Improvement & Feedback Layer

## Zweck
Der Layer erzeugt aus Feedback, Laufzeitfehlern und Regressionen ein priorisiertes Verbesserungs-Backlog.

## Datenfluss

```text
Feedback / Runs / Metrics
↓
Classifier
↓
Failure Cluster
↓
Improvement Backlog
↓
Recommendation Ranking
```

## Befehle

```powershell
python launcher.py improve-status
python launcher.py improve-feedback user command launcher -2 --text "launcher command unclear"
python launcher.py improve-backlog
python launcher.py improve-analyze
python launcher.py improve-recommend
python launcher.py improve-report
```

## Scoring

```text
score = weighted(severity, impact, confidence) / effort
```

## Konsequenz
Das System sammelt nicht nur Fehler. Es erzeugt konkrete, priorisierte Arbeitspakete.

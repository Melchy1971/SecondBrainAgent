# Release Gate: aktueller Nachweisstand

## Aktuelle Bewertung

| Bereich | Status | Evidenz |
|---|---|---|
| Paketversion | KONSISTENT, ABER HISTORISCH | `pyproject.toml` meldet weiterhin 30.77.0; Funktionsstand ist v31.16 |
| v31.01-v31.14 | IN `main` | Merge-Historie bis PR #43 belegt |
| Task PostgreSQL v31.15 | BRANCH BEREIT | Repository-Tests bestanden; echter PostgreSQL-Lauf offen |
| Planner Parallel Runtime v31.16 | BRANCH BEREIT | 30 fokussierte Planner-/Persistenztests und Ruff bestanden |
| P0/P1 Vollgate | NICHT NEU AUSGEFUEHRT | fuer diese Dokumentationsbereinigung nicht erforderlich |
| PostgreSQL/pgvector Apply | BLOCKED | pgvector deaktiviert, DSN fehlt; nichts angewendet |
| Produktive Embeddings | CONDITIONAL | echte Provider-Konfiguration umgebungsabhaengig |
| Connectoren/OAuth | BLOCKER | keine belegte produktive Live-Synchronisation |
| Secret-Verschluesselung | BLOCKER | produktiver Secret Store offen |
| Vollstaendiger Testlauf | NICHT NEU AUSGEFUEHRT | fuer v31.15/v31.16 liefen fokussierte Tests; Gesamt-GA muss neu laufen |

## Ergebnis

Der implementierte Funktionsstand ist dokumentiert. Ein Production PASS ist nicht belegt, bis v31.15/v31.16 integriert und die umgebungsabhaengigen GA-Pruefungen erfolgreich ausgefuehrt wurden.

## Pflichtchecks vor Release

```powershell
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
python launcher.py gui-bootstrap
python launcher.py gui-doctor
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
python launcher.py ga-readiness-gate
```

Produktive pgvector-Freigabe erfordert zusaetzlich eine gepruefte Ziel-DSN, Backup/Restore-Plan und:

```powershell
python launcher.py p3-pgvector-readiness --live
python launcher.py p3-pgvector-readiness --live --apply
```

Der zweite Befehl darf erst nach Review des SQL-Previews ausgefuehrt werden.

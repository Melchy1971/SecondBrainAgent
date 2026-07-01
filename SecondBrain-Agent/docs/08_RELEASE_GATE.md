# Release Gate v30.25

## Aktuelle Bewertung

| Bereich | Status | Evidenz |
|---|---|---|
| Packaging / Version | PASS | `pyproject.toml` meldet 30.25.0 |
| Command Index | PASS | am 2026-06-30 erfolgreich ausgefuehrt |
| Native Desktop v30.25 | PASS laut Release-Artefakt | fokussierte Tests im v30.25-Manifest dokumentiert |
| P0/P1 Vollgate | NICHT NEU AUSGEFUEHRT | fuer diese Dokumentationsbereinigung nicht erforderlich |
| PostgreSQL/pgvector Apply | BLOCKED | pgvector deaktiviert, DSN fehlt; nichts angewendet |
| Produktive Embeddings | CONDITIONAL | echte Provider-Konfiguration umgebungsabhaengig |
| Connectoren/OAuth | BLOCKER | keine belegte produktive Live-Synchronisation |
| Secret-Verschluesselung | BLOCKER | produktiver Secret Store offen |
| Vollstaendiger Testlauf | NICHT AUSGEFUEHRT | Dokumentationsaenderung; Link-/Strukturchecks laufen separat |

## Ergebnis

Lokale Entwicklung und die v30.25-Oberflaeche sind dokumentiert. Ein Production PASS ist nicht belegt.

## Pflichtchecks vor Release

```powershell
python launcher.py repo-doctor --execute-runtime-checks
python launcher.py dependency-inventory
python launcher.py gui-bootstrap
python launcher.py gui-doctor
python launcher.py p0-gate
python launcher.py p1-gate
pytest -q
```

Produktive pgvector-Freigabe erfordert zusaetzlich eine gepruefte Ziel-DSN, Backup/Restore-Plan und:

```powershell
python launcher.py p3-pgvector-readiness --live
python launcher.py p3-pgvector-readiness --live --apply
```

Der zweite Befehl darf erst nach Review des SQL-Previews ausgefuehrt werden.

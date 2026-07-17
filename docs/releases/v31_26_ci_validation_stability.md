# v31.26 – CI- und Pull-Request-Validation

## Ziel

Die bestehenden GitHub-Actions-Workflows werden stabilisiert, ohne ein
paralleles CI-System einzuführen. Pull Requests und `main` prüfen Python 3.12
und 3.13 reproduzierbar; Live-Dienste und GUI-Sessions bleiben opt-in.

## Änderungen

- Version Sync aktualisiert nur generierte Skalare, bewahrt unbekannte
  Masterplan-Felder und bestehende Einrückung und ist nach wiederholtem Lauf
  diff-frei.
- Das lowercase Import-Shim ist ein Modul statt eines mit `SecondBrain/`
  kollidierenden Verzeichnisses. Editable Install und
  `import secondbrain.knowledge_graph.service` funktionieren dadurch auf
  case-sensitiven und case-insensitiven Dateisystemen.
- Der bestehende Release-Smoke-Workflow verwendet SHA-gepinnte Actions,
  deaktivierte Checkout-Credentials und explizite Ausschlüsse für Live- und
  GUI-Tests.
- Repo Doctor und Dependency Inventory schreiben begrenzte JSON-Berichte.
  Pytest erzeugt getrennte JUnit-Berichte.
- Artefakt-Uploads enthalten ausschließlich definierte JSON-/XML-Berichte,
  keine Logs, Secrets oder Dokumentinhalte.
- Bereits validierte Approval-, Chat-, Graph-, Memory- und Agent-Fixes wurden
  wiederverwendet, um die plattformübergreifende Testmatrix zu stabilisieren.

## Verifikation

```powershell
python -m pytest -q tests\test_ci_workflow_contract.py
python -m pytest -q tests\version\test_version.py
python launcher.py version-sync
git diff --exit-code README.md docs\09_MASTERPLAN_STATUS.json
python launcher.py repo-doctor --execute-runtime-checks --write-report
python scripts\personal_jarvis_gate.py --project-root .
```

Live-PostgreSQL-, Provider- und Connector-Zertifizierungen bleiben getrennte,
explizit konfigurierte Gates.

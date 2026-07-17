# CI Failure Analysis v31.26

Stand: 2026-07-16, Basis `main` (`743b58ca536`).

## Evidenz

Analysiert wurden die öffentlichen Metadaten der GitHub-Actions-Runs
`29495982399`, `29495982397`, `29495774686` und `29495774673` sowie PR #55.
Die GitHub API stellt die Job-Logs ohne authentifizierte Admin-Rechte nicht
bereit; Job-, Step- und Conclusion-Daten wurden deshalb mit identischen lokalen
Befehlen ergänzt. Security ist auf dem aktuellen Commit grün.

## Fehler

| Workflow | Job / Step | Python | Fehlermeldung | Ursache | Lokaler Befehl | Fix | Regressionstest |
|---|---|---:|---|---|---|---|---|
| SecondBrain CI | Release smoke / Version metadata | 3.12, 3.13 | `version_drift` | `version-sync` serialisiert das vollständige Masterplan-JSON und erzeugt rein formatbedingte Diffs. | `python scripts/ci_gate.py version` | PR #55 übernehmen und semantische, formatbewahrende Aktualisierung vervollständigen. | `python -m pytest -q tests/version/test_version.py` |
| Pull Request Validation | Version drift and workflow policy | 3.12 | `secondbrain-ci.yml: checkout persists credentials`; `unpinned action` | Der neue Workflow nutzt bewegliche Action-Tags und setzt Checkout-Credentials nicht explizit aus. | `python scripts/ci_gate.py workflows` | Actions auf vollständige SHAs pinnen und `persist-credentials: false` setzen. | `python -m pytest -q tests/test_ci_workflow_contract.py tests/test_v3103_cicd.py` |
| SecondBrain CI | Repository doctor | 3.12, 3.13 | Doctor `BLOCKED`; Dependency Inventory läuft in das 60-Sekunden-Limit | Repo Doctor scannt lokale ignorierte Artefakte zu breit; der Runtime-Check startet ein nicht terminierendes Dependency Inventory. | `python launcher.py repo-doctor --execute-runtime-checks` | CI-relevante Git-Dateien von lokalen Caches trennen; Dependency Inventory begrenzen und Reports unabhängig hochladen. | `python -m pytest -q tests/test_repo_doctor_v18_7.py tests/test_dependency_inventory_v18_8.py` |
| Main Validation | Test matrix Ubuntu / Windows | 3.12, 3.13 | 50 lokale Fehler, u. a. fehlende Approval-Methoden, Chat-Prompt-Vertrag, Graph-Quellenformat und Agent-Rollback | `main` enthält die v31.23-Gate-Struktur, aber nicht die danach validierten Kompatibilitätsfixes. | `python -m pytest -q -m "not live and not slow" tests` | Bereits getestete v31.23-Fixes gezielt übernehmen; keine parallelen Implementierungen. | Betroffene Tests plus vollständige nicht-live Matrix |
| Main Validation | Test matrix / workflow contract | 3.12, 3.13 | `secondbrain-ci.yml` fehlt in statischer Workflow-Allowlist | Workflow-Vertrag ist als exakte Dateimengenprüfung modelliert und bricht bei legitimer Erweiterung. | `python -m pytest -q tests/test_v3103_cicd.py` | Vertrag auf erforderliche Mindestmenge und SHA-Pinning umstellen. | `tests/test_v3103_cicd.py` |
| Windows Checkout | Package import / Git status | 3.13 lokal | Checkout verändert `SecondBrain/__init__.py` unmittelbar | Git trackt gleichzeitig `SecondBrain/` und `secondbrain/`; beide Pfade kollidieren auf case-insensitiven Dateisystemen. | `git checkout main && git status --short` | Lowercase-Kompatibilität ohne kollidierendes Verzeichnis bereitstellen und Editable Install auf beiden Plattformen testen. | Frischer Editable-Install; `import secondbrain`; Knowledge-Graph-Import |
| SecondBrain CI | Integration tests | 3.12, 3.13 | Schritt nach frühem Doctor-Fehler übersprungen | Sequentieller Job verhindert unabhängige Diagnose; optionale Verzeichnisse und Live-Abhängigkeiten sind nicht vollständig entkoppelt. | `pytest -q -m "integration and not live" tests/integration tests/connectors_runtime tests/storage tests/vision tests/voice` | Live/GUI/optionale Integrationen explizit ausschließen und fehlende optionale Verzeichnisse kontrolliert behandeln. | Workflow-Vertrag plus Marker-Collection |
| SecondBrain CI | Personal Jarvis / RC Gate | 3.12, 3.13 | Wegen früherer Fehler übersprungen | Gates liegen hinter Version/Doctor im selben Job. | `python scripts/personal_jarvis_gate.py --project-root .`; `python launcher.py rc-gate --write-report` | Gate-Ausführung diagnostisch trennen; Reports bei Fehlern immer hochladen. | Personal-Jarvis- und RC-Gate-Tests |
| Release / RC | Release marker | 3.13 | Kein aktueller isolierter Fehler beobachtet | Marker-Selektion ist vorhanden, wurde aber durch frühere Workflow-Abbrüche nicht erreicht. | `pytest -q -m "release or connector"` | Marker-Vertrag beibehalten, Live und GUI explizit ausschließen. | Pytest-Collection und Workflow-Vertrag |
| Artifact upload | Upload diagnostic reports | 3.12, 3.13 | Upload erfolgreich, aber JUnit fehlt und Logs sind nicht explizit redigiert | Pytest erzeugt kein verpflichtendes JUnit-Artefakt; Reportpfade sind nur best effort. | Workflow-Inspektion | JUnit immer erzeugen; nur definierte JSON/XML-Berichte hochladen; keine Nutzinhalte oder Secrets. | Workflow-Vertrag und Report-Redaction-Test |

## Priorisierte Umsetzung

1. PR #55 als bestehenden Version-Sync-Delta übernehmen und um CRLF,
   fehlende Felder, unbekannte Felder sowie alternative Einrückung testen.
2. Die bereits vollständig getesteten v31.23-Kompatibilitätsfixes selektiv
   übernehmen.
3. Workflow-Actions pinnen, Checkout-Credentials deaktivieren und die
   Testselektion hermetisch machen.
4. JUnit-, Repo-Doctor-, Personal-Jarvis- und RC-Berichte mit `if: always()`
   bereitstellen.
5. Das Windows-Case-Collision-Paketlayout ohne öffentliche API-Änderung
   auflösen.


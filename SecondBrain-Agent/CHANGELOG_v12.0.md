# SecondBrain OS v12.0 – Personal AGI OS Foundation

## Ziel
Konsolidierung der Releases v10.4 bis v11.9 zu einem zentralen Personal-OS-Einstieg.

## Neu
- Personal OS Orchestrator
- Capability Registry
- OS Manifest
- OS Readiness Gate
- End-to-End-Planung über `os-plan`
- kontrollierte Ausführung über `os-run`
- persistente OS Run History

## Neue Launcher-Befehle
- `os-status`
- `os-manifest`
- `os-capabilities`
- `os-capability-set-status`
- `os-plan`
- `os-run`
- `os-runs`
- `os-readiness-gate`

## Architekturwirkung
v12.0 macht aus den Einzel-Layern ein steuerbares Systemmodell:
Connectoren, RAG, Agent Runtime, Workflow Engine, Digital Twin, Voice, Mobile, API, Automation, Operations und Self Improvement werden als Fähigkeiten im OS geführt.

## Risikoabgrenzung
`os-run` führt keine beliebige Systemaktion aus. Nicht explizit unterstützte Aktionen werden blockiert. Riskante Fähigkeiten bleiben an bestehende Governance-/Approval-Grenzen gekoppelt.

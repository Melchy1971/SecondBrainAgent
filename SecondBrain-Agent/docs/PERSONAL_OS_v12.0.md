# Personal AGI OS v12.0

## Start

```powershell
python launcher.py os-status
python launcher.py os-readiness-gate
python launcher.py os-manifest
```

## Fähigkeiten anzeigen

```powershell
python launcher.py os-capabilities
python launcher.py os-capabilities --domain operations
```

## Ziel planen

```powershell
python launcher.py os-plan "Fasse mein Wissen zu Jarvis zusammen"
```

## Ziel ausführen

```powershell
python launcher.py os-run "Fasse mein Wissen zu Jarvis zusammen"
```

Trockenlauf:

```powershell
python launcher.py os-run "Release Health prüfen" --dry-run
```

## Run-Historie

```powershell
python launcher.py os-runs
```

## Kontrollmodell

| Ebene | Bedeutung |
|---|---|
| Capability Registry | Welche Fähigkeiten existieren |
| OS Plan | Welche Schritte für ein Ziel notwendig sind |
| OS Run | Persistente Ausführung eines Ziels |
| Readiness Gate | Reifeprüfung des v12.0-Kerns |
| Manifest | Systembeschreibung für GUI/API/Mobile |

## Grenzen

v12.0 ist die Orchestrierungs-Foundation. Es ersetzt nicht die Fachmodule, sondern verbindet sie. Echte produktive Autonomie bleibt abhängig von Connector-Konfiguration, AI-Provider, Berechtigungen, Backups und Approval-Regeln.

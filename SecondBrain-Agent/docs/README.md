# SecondBrain-Agent Dokumentation

Stand: v30.25, 2026-06-30

Dieser Ordner enthaelt die aktuelle Betriebs- und Architekturdokumentation. Historische Versionsdetails liegen ausschliesslich unter [`releases/`](releases/).

## Einstieg

1. [`04_STARTBEFEHLE.md`](04_STARTBEFEHLE.md) - Installation, Start, Diagnose und Fehlerbehebung.
2. [`CLIENTS_AND_INTERFACES.md`](CLIENTS_AND_INTERFACES.md) - Native App, Web-HUD, Voice und Mobile.
3. [`RAG_AND_DATA.md`](RAG_AND_DATA.md) - Dokumentimport, RAG, Embeddings, Datenbanken, Graph und Memory.
4. [`AGENTS_AND_CONNECTORS.md`](AGENTS_AND_CONNECTORS.md) - Agenten, Automationen, Connectoren und Governance.

## Betrieb und Entwicklung

- [`01_ARCHITEKTUR_UEBERSICHT.md`](01_ARCHITEKTUR_UEBERSICHT.md) - Systemgrenzen und Datenfluss.
- [`03_MODUL_MATRIX.md`](03_MODUL_MATRIX.md) - Reifegrad der aktiven Bereiche.
- [`05_OFFENE_LUECKEN.md`](05_OFFENE_LUECKEN.md) - priorisierte Roadmap und bekannte Grenzen.
- [`07_IMPLEMENTIERUNGSREGELN.md`](07_IMPLEMENTIERUNGSREGELN.md) - Entwicklungs- und Sicherheitsregeln.
- [`RELEASE_WORKFLOW_v18_9.md`](RELEASE_WORKFLOW_v18_9.md) - verbindlicher Gate- und Release-Ablauf. Der Dateiname bleibt wegen Repo-Doctor-Kompatibilitaet bestehen.
- [`08_RELEASE_GATE.md`](08_RELEASE_GATE.md) - zuletzt belegter Gate-Status.
- [`09_MASTERPLAN_STATUS.json`](09_MASTERPLAN_STATUS.json) - maschinenlesbarer Projektstatus.

## Spezielle Funktionen

- [`VOICE_CONTROL_v20.md`](VOICE_CONTROL_v20.md) - aktuelle Voice-Pipeline; Dateiname bleibt wegen Code-Verweisen bestehen.
- [`SECURITY_CAMERAS_v30.md`](SECURITY_CAMERAS_v30.md) - Kamera- und Stream-Gateway-Konfiguration.

## Quellen der Wahrheit

- Bedienung und Installation: Root-`README.md` und diese Dokumentation.
- Aktuelle Befehle: `python launcher.py command-index`.
- Packaging und Extras: `pyproject.toml`.
- Release-Historie: [`02_RELEASE_HISTORY.md`](02_RELEASE_HISTORY.md), Git-History und [`releases/`](releases/).
- Laufzeitstatus: generierte Reports unter `runtime/` und `release/`; diese werden nicht als statische Dokumentation gepflegt.

Versionierte Feature-Snapshots aus v6 bis v18 wurden entfernt. Sie beschrieben ueberwiegend alte Launcher-Oberflaechen oder Foundations und waren keine verlaessliche Betriebsanleitung mehr.

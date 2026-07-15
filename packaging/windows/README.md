# Jarvis Windows Release

Der Releaseprozess erzeugt eine native Anwendung inklusive Python, Tkinter und Assets.
Die Standardinstallation benötigt keine Administratorrechte und liegt unter
`%LOCALAPPDATA%\Programs\Jarvis`. Im Privilegdialog kann optional die systemweite
Installation unter `Program Files` gewählt werden.

## Build

Voraussetzungen: Windows 10/11 x64, Python 3.11+, Inno Setup 6 sowie WiX v4 mit
`wix.exe` und `heat.exe`.

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
```

Der Build verwendet reviewbare direkte Pins aus `constraints.txt`, ein sauberes
venv und `SOURCE_DATE_EPOCH`. Fehlende Installer-Werkzeuge brechen den Build ab.
Nur für gezielte Teil-Builds können MSI oder EXE explizit mit `-SkipMsi` bzw.
`-SkipInstaller` ausgelassen werden.

Die Pipeline führt folgende Schritte aus:

1. Abhängigkeiten installieren und mit `pip check` prüfen.
2. `Jarvis.exe` und `jarvis-cli.exe` per PyInstaller erzeugen.
3. Payload auf Tests, Runtime-Daten, Secrets und lokale absolute Pfade prüfen.
4. Frozen-Smoke-Test ausführen.
5. Deterministisches Portable ZIP mit `.portable`-Marker erzeugen.
6. Inno-Setup-EXE und WiX-MSI bauen.
7. CycloneDX-SBOM, Release Notes, Release Manifest und SHA-256-Datei erzeugen.
8. Alle Checksums erneut verifizieren.

## Artefakte

`dist\release` enthält:

- `Jarvis-<version>-portable-win64.zip`
- `Jarvis-Setup-<version>.exe`
- `Jarvis-<version>.msi`
- `Jarvis-<version>-sbom.cdx.json`
- `release-manifest.json`
- `RELEASE_NOTES.md`
- `SHA256SUMS.txt`

## Installations- und Datenmodell

Inno Setup unterstützt Benutzer- und Systeminstallation, Startmenü, optionale
Desktop-Verknüpfung, optionalen Autostart, Upgrade/Repair und Uninstall. WiX blockiert
Downgrades über `MajorUpgrade`. Ein normales Uninstall löscht ausschließlich
Programmdateien. Nutzerdaten werden nur nach expliziter Bestätigung gelöscht.

```text
%LOCALAPPDATA%\Programs\Jarvis\  Programmdateien (Standard)
%APPDATA%\Jarvis\                 config, database, data, vault, backups
%LOCALAPPDATA%\Jarvis\            logs, cache, updates, runtime
<Portable>\JarvisData\            ausschließlich portable Daten
```

`JARVIS_HOME` bleibt der explizite Workspace-Override. Portable ZIPs enthalten den
Marker `.portable`; dadurch verwendet der Bootstrap `JarvisData` neben der Anwendung
und niemals die Daten einer installierten Instanz. Migrationen kopieren nur in leere
Ziele und überschreiben vorhandene Nutzerdaten nicht.

## Automatisierte Prüfung

`tests/test_v3102_windows_release.py` prüft reproduzierbare ZIPs, Pfadtrennung,
Schreibzugriff, Payload-Sicherheit, SBOM/Manifest/Checksums und die Installerregeln.
Der reale Windows-Build führt zusätzlich `jarvis-cli.exe smoke-test` aus; der Installer
wiederholt ihn nach Installation. Ein erneuter Installerlauf dient als Repair und
behält Verzeichnis und ausgewählte Tasks bei.

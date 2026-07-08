# Jarvis - Windows-Installer

Produktiver Windows-Build ohne Entwickler-Setup fuer Endnutzer. Programmdateien
liegen unter `Program Files\Jarvis`, alle Nutzerdaten unter `%APPDATA%\Jarvis`.
Damit ueberlebt jede Nutzerdatei ein Update, und ein Uninstall kann das Programm
entfernen, ohne die Daten anzutasten.

## Komponenten

| Datei | Zweck |
|------|-------|
| `jarvis_bootstrap.py` | Eingefrorener Einstiegspunkt: AppData-Home setzen, Migration, dann Launcher |
| `jarvis.spec` | PyInstaller-Spec (onedir): `Jarvis.exe` (GUI) + `jarvis-cli.exe` (Konsole/Smoke) |
| `installer.iss` | Inno-Setup-Installer (Shortcuts, Uninstaller, Datenerhalt) - der produktive Installer |
| `jarvis.wxs` | WiX-MSI-Skelett (MSI/MSIX-Vorbereitung fuer Intune u. ae.) |
| `build.ps1` | Orchestriert venv -> PyInstaller -> Portable ZIP -> Installer -> Checksums |

Testbarer Kern (im Repo, `secondbrain/install/`, unit-getestet):
`app_home.py` (Home-Auflösung), `migrate.py` (Datenmigration), `smoke.py` (Smoke-Test).

## Voraussetzungen (Build-Maschine)

- Windows 10/11 x64
- Python 3.11+ (die App nutzt `datetime.UTC`)
- optional Inno Setup 6 (`iscc`) fuer den `.exe`-Installer
- optional WiX Toolset v4 (`wix`, `heat`) fuer die MSI-Variante

## Build

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
```

Schritte: sauberes venv -> Runtime-/Security-/Vision-Requirements -> PyInstaller
-> Smoke-Test auf der frozen `jarvis-cli.exe` -> Portable ZIP -> (falls `iscc` da)
Installer -> `SHA256SUMS.txt`. Ohne Inno Setup entsteht trotzdem die Portable ZIP.

MSI (optional):

```powershell
heat dir dist\Jarvis -cg JarvisFiles -dr INSTALLFOLDER -srd -sreg -gg -var var.SourceDir -out packaging\windows\harvest.wxs
wix build packaging\windows\jarvis.wxs packaging\windows\harvest.wxs -d SourceDir=dist\Jarvis -o dist\release\Jarvis.msi
```

## Release-Artefaktstruktur

```
dist/
  Jarvis/                         # PyInstaller onedir (Rohbuild)
    Jarvis.exe                    # GUI-Einstieg (Shortcut-Ziel)
    jarvis-cli.exe                # CLI + smoke-test
    _internal/ ...                # Python-Runtime, Ressourcen (web, prompts, config)
  release/                        # Auslieferbare Artefakte
    Jarvis-Setup-<version>.exe    # Inno-Setup-Installer
    Jarvis-<version>-portable-win64.zip
    Jarvis.msi                    # optional (WiX)
    SHA256SUMS.txt
```

## Laufzeit-Layout (Zielrechner)

```
%ProgramFiles%\Jarvis\           # Programmdateien (bei Update ersetzt)
%APPDATA%\Jarvis\                # Nutzerdaten (bei Update erhalten)
  config\  data\  logs\  runtime\  vault\
  .jarvis_migrated.json          # Migrationshistorie
```

Die Home-Auflösung: `JARVIS_HOME` (env) > `%APPDATA%\Jarvis` > `~/.jarvis`.
Der Bootstrap setzt `JARVIS_HOME`, wechselt in die Home und reicht
`--project-root <home>` an den Launcher durch.

## Akzeptanz -> Umsetzung

- Frische Installation startet Jarvis: PyInstaller-Bundle + Smoke-Test im Build und im Installer.
- Desktop-Shortcut startet native GUI: `Jarvis.exe` (Bootstrap-Default `native-gui`).
- Daten bleiben bei Update: Nutzerdaten in `%APPDATA%`, Migration ueberschreibt nie vorhandene Daten.
- Uninstall entfernt Programm, nicht Daten ohne Bestaetigung: `installer.iss` fragt beim Uninstall explizit nach.

## Integrationshinweis (ein offener Punkt)

Der Bootstrap erzwingt die AppData-Home ueber `JARVIS_HOME`, `--project-root` und
den Arbeitsverzeichniswechsel. Acht Module im App-Code lösen ihren Projekt-Root noch
ueber `Path(__file__).parents[1]` auf. Fuer die volle Sauberkeit sollten diese auf
`secondbrain.install.app_home.project_root()` umgestellt werden; solange sie
nur Ressourcen lesen (nicht schreiben), ist der Datenerhalt nicht betroffen. Empfehlung
als kleines Folge-Arbeitspaket.

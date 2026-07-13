# v30.36 Native Installer Center

## Ziel
Jarvis wird als eigenständiges natives Desktop-Tool startbar, ohne Web-HUD als Primärpfad.

## Enthalten
- Installer Status
- Installer Plan
- Windows Start-Batch
- PowerShell Shortcut Installer
- PowerShell Uninstaller
- Native Installer GUI
- Report unter `runtime/native/installer/installer_v30_36.json`

## Kommandos

```bash
python launcher.py native-installer-status
python launcher.py native-installer-plan
python launcher.py native-installer-write
python launcher.py native-installer-gui
```

## Ergebnis
Nach `native-installer-write` liegen Start-/Installationsdateien unter:

```text
dist/native-installer/
```

Primärstart bleibt:

```bash
python launcher.py
```

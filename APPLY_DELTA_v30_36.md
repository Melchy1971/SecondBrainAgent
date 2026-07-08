# APPLY_DELTA_v30_36

## Inhalt
v30.36 Native Installer Center.

## Dateien kopieren
ZIP-Inhalt in den Projektordner `SecondBrain-Agent/` kopieren und vorhandene Dateien überschreiben.

## Validierung

```bash
pytest tests/test_v3036_native_installer_center.py -q
python launcher.py native-installer-status
python launcher.py native-installer-plan
python launcher.py native-installer-write
```

## Start

```bash
python launcher.py
```

## Windows-Verknüpfungen erzeugen

```powershell
powershell -ExecutionPolicy Bypass -File dist/native-installer/Install-Jarvis-Native.ps1
```

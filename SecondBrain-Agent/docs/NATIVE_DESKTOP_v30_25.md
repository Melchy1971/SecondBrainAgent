# Native Desktop v30.25

## Zielbild

Jarvis läuft als eigenständiges lokales Tool. Der Browser ist nicht mehr die Hauptoberfläche.

## Primäre Befehle

```powershell
python launcher.py
python launcher.py jarvis
python launcher.py native-gui
```

## Oberflächenbereiche

- Dashboard
- Assistant
- Documents
- Memory
- Search
- Imports
- Production
- Settings
- Voice
- Developer

## Deutsche Sprachkommandos

| Befehl | Wirkung |
|---|---|
| `Jarvis Status` | Native-/Bootstrap-/Runtime-Status anzeigen |
| `Suche <Begriff>` | Hybrid-RAG-Suche ausführen |
| `Frage <Frage>` | RAG-Antwort mit Quellen ausführen |
| `Öffne Dokumente` | Document/RAG-Ansicht öffnen |
| `Öffne Einstellungen` | Bootstrap/Settings anzeigen |
| `Repariere Index` | Vector-Index-Reparatur nach Bestätigung |
| `Importiere Datei <Pfad>` | Datei nach Bestätigung importieren |

## Mark-XLVI-Übernahme

Übernommenes Prinzip:

- eigenständiges Desktop-HUD
- zentrale Kommandozeile im Fenster
- Spracheingabe als Bedienkanal
- lokale Systemdiagnose
- klare Trennung zwischen UI, STT/TTS und Aktionen

Nicht übernommen:

- harte Cloud-/Gemini-Abhängigkeit als Pflicht
- PyQt6 als Pflichtdependency
- automatische OS-Aktionen ohne Bestätigung

## Sicherheitsgrenze

Schreibende Aktionen wie Dateiimport und Indexreparatur verlangen Bestätigung. Mikrofon- und TTS-Pakete sind optional und werden nicht als harte Runtime-Abhängigkeit vorausgesetzt.

---
title: "PDF-Wandler Zusammenfassung"
type: chatgpt_conversation
source: chatgpt
source_id: "67a21ac3-9194-8007-bd54-e91db518c6dd"
created: 2025-02-04
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
---


# PDF-Wandler Zusammenfassung

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67a21ac3-9194-8007-bd54-e91db518c6dd`
- Nachrichten: 3

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

stelle mir nachfolgenden inhalt ansprechend dar. Inhalt: # PDF-Wandler



## Übersicht



Dieses Tool dient zum Umbenennen und Organisieren von Dateien basierend auf extrahierten Informationen wie Datum, Firmenname und Rechnungsnummer.



## Installation



Stellen Sie sicher, dass die folgenden Python-Pakete installiert sind:

- tkinter

- dateutil

- requests



```bash

pip install python-dateutil requests

```



## Konfiguration



Die Konfiguration erfolgt über die `config.json` Datei. Standardwerte sind in der Datei `main.py` definiert.



### Standardkonfiguration



```json

{

    "DEFAULT_SOURCE_DIR": "",

    "BACKUP_DIR": "backup",

    "ALLOWED_EXTENSIONS": ["pdf", "png", "jpg", "jpeg", "docx", "xlsx", "eml"],

    "BATCH_SIZE": 10,

    "DATE_FORMATS": ["%Y.%m.%d", "%Y-%m-%d", "%d.%m.%Y"],

    "MAIN_TARGET_DIR": "",

    "LOG_LEVEL": "DEBUG",

    "FILENAME_PATTERN": "{date}_{company}_{number}.{ext}",

    "DARK_MODE": false

}

```



## Verwendung



1. Starten Sie das Tool.

2. Wählen Sie das Quellverzeichnis aus, das die zu verarbeitenden Dateien enthält.

3. Klicken Sie auf "Dateien umbenennen und organisieren", um den Umbenennungsprozess zu starten.

4. Die Dateien werden analysiert, um Informationen wie Rechnungsdatum, Firmenname und Rechnungsnummer zu extrahieren.

5. Die Dateien werden im Format `{date}_{company}_{number}.{ext}` umbenannt und in entsprechende Unterordner verschoben.

6. Verwenden Sie die "Firmenpflege"-Option, um die Liste der Firmennamen zu verwalten.

7. Über die "Konfiguration"-Option können Sie die Standardeinstellungen anpassen.

8. Der "Bericht anzeigen"-Button zeigt eine Zusammenfassung der verarbeiteten Dateien und Fehler an.

9. Das Protokollfenster zeigt detaillierte Log-Einträge zur Fehlerbehebung.

10. Über die "Hilfe"-Option erhalten Sie eine Anleitung zur Verwendung des Tools.

11. Mit der "Info"-Option erhalten Sie Informationen über das Tool.

12. Nutzen Sie die Vorschau-Funktion, um die neuen Dateinamen vor der Umbenennung zu überprüfen.

13. Aktivieren Sie den Dark Mode in den Einstellungen, um die Benutzeroberfläche anzupassen.



## Funktionen



- **Dateiumbenennung und -organisation**: Basierend auf extrahierten Informationen wie Datum, Firmenname und Rechnungsnummer.

- **Firmenpflege**: Verwaltung der Liste der Firmennamen.

- **Konfiguration**: Anpassung der Standardeinstellungen.

- **Berichtsanzeige**: Zusammenfassung der verarbeiteten Dateien und Fehler.

- **Protokollanzeige**: Detaillierte Log-Einträge zur Fehlerbehebung.

- **Hilfe**: Anleitung zur Verwendung des Tools.

- **Info**: Informationen über das Tool.

- **Vorschau**: Anzeige der neuen Dateinamen vor der Umbenennung.

- **Dark Mode**: Anpassung der Benutzeroberfläche.



## Lizenz



Dieses Projekt ist unter der MIT-Lizenz lizenziert.

### 2. Assistent

Hier ist die überarbeitete, ansprechend dargestellte Version deines Inhalts:

### 3. Assistent

Ich habe den Inhalt nun ansprechender und strukturierter dargestellt, sodass er leicht verständlich und visuell ansprechend ist. Lass mich wissen, falls du noch Anpassungen wünschst! 🚀📂

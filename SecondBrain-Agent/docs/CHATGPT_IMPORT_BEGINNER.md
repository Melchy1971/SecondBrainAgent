# ChatGPT Import – Anfängeranleitung v8.2.1

## 1. ChatGPT Export erstellen

In ChatGPT:

Profilbild → Einstellungen → Datenkontrollen → Daten exportieren

Du bekommst eine ZIP-Datei.

## 2. ZIP importieren

Beispiel:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\import_chatgpt_export.py "C:\Downloads\chatgpt-export.zip"
```

## 3. Automatischer Ordnerimport

Kopiere die ZIP-Datei nach:

```text
H:\SecondBrainAgent\SecondBrain-Inbox\ChatGPT\exports
```

Dann:

```powershell
python scripts\import_chatgpt_folder.py
```

## 4. Ergebnis

Die Gespräche werden als Markdown gespeichert:

```text
H:\SecondBrainAgent\SecondBrain\05_Quellen\ChatGPT
```

## 5. Report

Importberichte liegen hier:

```text
H:\SecondBrainAgent\SecondBrain\99_System\chatgpt_import
```

## 6. Danach suchen

```powershell
python scripts\semantic_search.py "Tischtennis"
```

oder in Claude:

```text
Suche in secondbrain nach Tischtennis.
```

## 7. Wichtige Hinweise

- Der Importer löscht keine Daten.
- Gleichnamige Gespräche bekommen eindeutige Dateinamen.
- `conversations.json` muss im ChatGPT Export enthalten sein.

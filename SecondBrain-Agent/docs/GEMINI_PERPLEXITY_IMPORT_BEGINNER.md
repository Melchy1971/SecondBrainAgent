# Gemini und Perplexity Import – Anfängeranleitung

## Gemini

Export-ZIP kopieren nach:

```text
H:\SecondBrainAgent\SecondBrain-Inbox\Gemini\exports
```

Einzelimport:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\import_gemini_export.py "C:\Downloads\gemini-export.zip"
```

Ordnerimport:

```powershell
python scripts\import_gemini_folder.py
```

Ergebnis:

```text
H:\SecondBrainAgent\SecondBrain\05_Quellen\Gemini
```

## Perplexity

Export-ZIP kopieren nach:

```text
H:\SecondBrainAgent\SecondBrain-Inbox\Perplexity\exports
```

Einzelimport:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\import_perplexity_export.py "C:\Downloads\perplexity-export.zip"
```

Ordnerimport:

```powershell
python scripts\import_perplexity_folder.py
```

Ergebnis:

```text
H:\SecondBrainAgent\SecondBrain\05_Quellen\Perplexity
```

## Sammelimport

Wenn ChatGPT-, Gemini- und Perplexity-Importer vorhanden sind:

```powershell
python scripts\import_ai_exports.py
```

## Hinweise

- Unterstützt ZIP-Dateien mit JSON, Markdown, TXT oder HTML-Dateien.
- Der genaue Exportaufbau kann je nach Anbieter variieren.
- Fehler werden als Importreport gespeichert.
- Es wird nichts gelöscht.

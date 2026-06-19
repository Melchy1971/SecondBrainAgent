# Real Connectors v6.2

## Dokumentimport

```powershell
python scripts\import_document.py "C:\Pfad\datei.pdf"
```

## Bookmarks

```powershell
python scripts\import_bookmarks.py Chrome "C:\Users\User\AppData\Local\Google\Chrome\User Data\Default\Bookmarks"
```

## Code Repository

```powershell
python scripts\index_code_repo.py "H:\Projekt"
```

## IMAP

IMAP-Funktion ist im Code enthalten, aber nicht im Menü direkt aktiv.
Grund: Zugangsdaten müssen sicher in `secrets.local.yaml` liegen.

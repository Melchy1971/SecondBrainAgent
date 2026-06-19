---
title: PDF-Analyse-Tool (Python)
tags: [python, pdf, automatisierung, projekt]
status: idee
erstellt: 2026-06-18
---

# PDF-Analyse-Tool (Python)

## Ziel
Python-Projekt zur automatischen Analyse von PDF-Dateien.

## Offene Fragen (vor Konzeptbeginn zu klären)

- Was soll analysiert werden? (Text, Tabellen, Metadaten, Struktur, Bilder)
- Input: einzelne PDFs, Stapelverarbeitung, Ordner-Watch?
- Output-Format: strukturierte Daten (JSON/CSV), Datenbank, Report?
- Handelt es sich um gescannte PDFs (OCR erforderlich) oder maschinenlesbare?
- Welche Dokumenttypen / welches Schema? (Rechnungen, Verträge, Prozessdokumente)
- Muss die Lösung in bestehende Systeme integriert werden? (SAP, Jira, myWiki)

## Technologiestack (Kandidaten)

| Bibliothek     | Einsatzbereich                          |
| -------------- | --------------------------------------- |
| `pdfplumber`   | Textextraktion, Tabellenstruktur        |
| `pypdf`        | Metadaten, Seitenoperationen            |
| `pytesseract`  | OCR für gescannte PDFs                  |
| `pdfminer.six` | Low-Level-Textextraktion                |
| `camelot`      | Tabellenextraktion aus maschinenles. PDF |
| `langchain`    | LLM-gestützte semantische Analyse       |

## Nächste Schritte

- [ ] Anforderungen konkretisieren (s. offene Fragen)
- [ ] 2–3 Beispiel-PDFs als Testgrundlage beschaffen
- [ ] Proof of Concept mit `pdfplumber` auf Beispieldaten

## Verknüpfungen

- [[Python-Projekte]]
- [[Automatisierung]]

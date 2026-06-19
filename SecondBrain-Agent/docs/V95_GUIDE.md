# SecondBrain OS v9.5 Guide

## Start

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\menu.py
```

## Neue Optionen

```text
3 = SecondBrain v9.5 Cycle
4 = Vector RAG Index bauen
5 = RAG Suche
6 = RAG Antwort mit Ollama
7 = Meeting Transkript importieren
```

## RAG Index bauen

```powershell
python scripts\build_vector_rag.py
```

## RAG Suche

```powershell
python scripts\rag_search.py "Was weiß ich über SAP?"
```

## RAG Antwort mit Ollama

Ollama starten:

```powershell
ollama serve
```

Dann:

```powershell
python scripts\rag_answer.py "Was weiß ich über Tischtennis?"
```

## Meeting Transkripte

```powershell
python scripts\import_meeting_transcript.py "C:\Users\User\Downloads\meeting.txt"
```

## v9.5 Cycle

```powershell
python scripts\run_v95_cycle.py
```

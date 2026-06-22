# Startbefehle

## v16.0 Desktop

```powershell
pip install -r requirements.txt
python launcher.py desktop16-gui
python launcher.py desktop16-status
python launcher.py desktop16-seed
```

## v16.1 Datenbank

```powershell
python launcher.py db16-migrate
python launcher.py db16-health
python launcher.py db16-stats
```

## v16.2 Connectoren

```powershell
python launcher.py conn16-migrate
python launcher.py conn16-enable gmail
python launcher.py conn16-sync gmail
python launcher.py conn16-status
```

## v16.3 Dokumente

```powershell
python launcher.py doc16-migrate
python launcher.py doc16-ingest-file .\sample_docs\demo.md
python launcher.py doc16-search Jarvis
```

## v16.4 Agenten

```powershell
python launcher.py agent16-migrate
python launcher.py agent16-task-create "Sprint" "Plane den nächsten Sprint"
python launcher.py agent16-tasks
```

## v16.5 Knowledge Graph

```powershell
python launcher.py kg16-migrate
python launcher.py kg16-seed
python launcher.py kg16-status
```

## v16.6 Memory

```powershell
python launcher.py mem16-migrate
python launcher.py mem16-seed
python launcher.py mem16-recall Jarvis
```

## v16.7 RAG

```powershell
python launcher.py rag16-migrate
python launcher.py rag16-seed
python launcher.py rag16-search Jarvis
```

## v16.8 Voice

```powershell
python launcher.py voice16-migrate
python launcher.py voice16-wake "Jarvis status"
python launcher.py voice16-status
```

## v16.9 Mobile

```powershell
python launcher.py mobile16-migrate
python launcher.py mobile16-pair-request "iPhone Markus" ios
python launcher.py mobile16-status
```

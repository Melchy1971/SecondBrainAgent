# v30.51 - Enterprise Streaming Import Engine

## Architektur

- `StreamingImportService` ist der zentrale Datei- und Chat-Importpfad.
- `ImportSession`, `CheckpointManager`, `BatchWriter` und `ImportProgress`
  bilden Session, Resume, transaktionale Batches und Fortschritt ab.
- Persistenz erfolgt im bestehenden P1-RAG-SQLite-Store. Es gibt keine zweite
  Importdatenbank.
- ChatGPT-, Claude- und Gemini-Adapter sowie der klassische Import-Orchestrator
  delegieren an dieselbe Engine.
- Der bestehende `JobQueueService` verfolgt laufende Import-Jobs.

## Streaming und Resume

- JSON und Exportformate werden mit `ijson` inkrementell gelesen.
- JSONL/NDJSON verwendet `ijson` mit mehreren JSON-Werten.
- Markdown wird in festen 64-KiB-Blöcken mit inkrementellem UTF-8-Decoder gelesen.
- ZIP-Mitglieder werden direkt aus `ZipFile.open()` gestreamt und nicht komplett
  in den Arbeitsspeicher oder ein Extraktionsverzeichnis geladen.
- Checkpoints speichern Bytes, Datensatzposition, Chats, Chunks, Embeddings,
  Status und Fehler in `import_sessions`.

## Batches

- Standard-Batchgröße: 500, konfigurierbar.
- Dokumente und Chunks werden ausschließlich mit `executemany` geschrieben.
- Datenbatch und Checkpoint werden in derselben Transaktion committed.

## Bereinigte Doppelpfade

- Vollständiges `read_text()`/`json.loads()` in ChatGPT- und Gemini-Importern entfernt.
- JSON/JSONL/Markdown/ZIP im klassischen Orchestrator auf Streaming umgestellt.
- File-Copy im Document Explorer verwendet einen begrenzten 1-MiB-Puffer.

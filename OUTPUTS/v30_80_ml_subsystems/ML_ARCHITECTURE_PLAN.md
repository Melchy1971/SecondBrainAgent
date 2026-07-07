# Architektur-Konzept: ML-Subsysteme (Vision/OCR + Voice)
Stand: 2026-07-07 | Kein Code. Vorbedingung für spätere Umsetzung.

## 0. Warum getrennt von den Connectoren
Connectoren (M365, Google, …) sind zustandslose API-Adapter — offline mit FakeTransport voll
testbar, `pytest` echt grün. Vision und Voice sind das Gegenteil: sie hängen an Modellen (Gewichte),
Hardware (Kamera, Mikrofon, ggf. GPU) und schweren Dependencies. „compileall + pytest grün" ist dort
ohne Modelle/Hardware **bedeutungslos** — Import-Stubs beweisen nichts. Deshalb zuerst dieses Konzept
mit klaren Abnahmekriterien, dann Umsetzung in testbaren Schichten.

## 1. Gemeinsames Architekturprinzip
Beide Subsysteme werden in drei Schichten getrennt, damit die Logik testbar bleibt und Modelle/Hardware
austauschbar sind:
- **Port (Protocol):** reine Schnittstelle (z.B. `OcrEngine.recognize(image) -> OcrResult`), stdlib-only,
  100% unit-testbar mit Fake-Implementierung.
- **Adapter:** konkrete Anbindung an eine Engine/Modell (Tesseract, Whisper, …). Integrationstest,
  läuft nur mit installierter Engine — als `@pytest.mark.integration` markiert, im Standardlauf übersprungen.
- **Orchestrierung:** Pipeline, Memory-/RAG-Anbindung, Agent-Hooks — testbar über den Port mit Fakes.

Ergebnis: Standard-`pytest` bleibt grün (Ports + Orchestrierung mit Fakes), echte Engines werden separat
mit Marker/Extra-Deps getestet. Das ist die einzige ehrliche Form von „grün" hier.

## 2. Vision / OCR (Batch: OCR, Camera, Desktop/Screenshot-Analyse, Klassifizierung, Objekterkennung, Diagramme)

### 2.1 Bausteine + Kandidaten
| Fähigkeit | Kandidat (lokal/offline) | Dependency | Hardware |
|---|---|---|---|
| OCR (Dokumente) | Tesseract (pytesseract) oder PaddleOCR | Systempaket + Modelle | CPU |
| OCR (Screenshots/UI) | Tesseract + Preprocessing (OpenCV) | opencv-python | CPU |
| Screenshot-Capture | `mss` (plattformübergreifend) | mss | Desktop-Session |
| Kamera-Capture | OpenCV VideoCapture | opencv-python | Kamera |
| Dokument-Klassifizierung | Embeddings (bereits im RAG vorhanden) + Klassifikator | vorhanden | CPU |
| Objekterkennung | YOLO (ultralytics) oder ONNX-Modell | ultralytics/onnxruntime | GPU empfohlen |
| Diagramm-Verständnis | VLM (lokal: z.B. moondream/llava) oder Cloud-VLM | groß / optional Cloud | GPU/Cloud |

### 2.2 Schnittstellen (Ports)
- `ScreenSource.capture() -> Image` | `CameraSource.frame() -> Image`
- `OcrEngine.recognize(image, *, lang) -> OcrResult{text, blocks, confidence}`
- `ImageClassifier.classify(image) -> list[Label]`
- `ObjectDetector.detect(image) -> list[Box]`
- `VisionIngest.to_connector_items(result) -> list[ConnectorItem]` (Wiederverwendung der bestehenden
  ConnectorItem/Import-Bridge -> Memory/RAG ohne Sonderweg).

### 2.3 Anbindung an Bestehendes
OCR-/Vision-Ergebnisse werden als `ConnectorItem` normalisiert und über `ConnectorImportBridge` in
Memory/RAG importiert — identischer Pfad wie die Connectoren. Kein zweites Ingestion-System.

### 2.4 Testbarkeit / Abnahme
- Ports + Ingest: Unit-Tests mit Fake-Engine (Standardlauf, grün).
- Engine-Adapter: Integrationstests mit Golden-Images (bekannter Text) -> `recognize()` muss definierten
  Text mit Mindest-Confidence liefern. Nur mit installierter Engine.
- Abnahme: „fehlerfreier Live-Lauf" = definierte Golden-Set-Genauigkeit (z.B. OCR CER < X%) auf deiner Maschine.

## 3. Voice (Batch: Wake Word, Offline/Streaming STT, Streaming TTS, Voice Memory, Speaker Profiles, Commands, Interrupt, Conversation Mode)

### 3.1 Bausteine + Kandidaten
| Fähigkeit | Kandidat (offline) | Dependency | Hardware |
|---|---|---|---|
| Wake Word | openWakeWord oder Porcupine | Modell + Runtime | Mikrofon |
| Offline STT | faster-whisper / whisper.cpp | Modelle (GB) | CPU/GPU |
| Streaming STT | faster-whisper (chunked) + VAD (webrtcvad/silero) | + VAD | Mikrofon |
| Streaming TTS | Piper (lokal) | Piper + Stimmen | CPU |
| Speaker Profiles | Sprecher-Embeddings (resemblyzer/pyannote) | Modell | CPU/GPU |
| Voice Memory | vorhandenes Memory/RAG | vorhanden | — |
| Interrupt / Conversation | Barge-in-Steuerung (Audio-Duplex) | Audio-Stack | Mikro+Lautspr. |

### 3.2 Schnittstellen (Ports)
- `WakeWordDetector.stream(frames) -> events`
- `SttEngine.transcribe(audio) -> Transcript` und `StreamingStt.push(chunk) -> partials`
- `TtsEngine.synthesize(text) -> audio` / `stream(text) -> chunks`
- `SpeakerIdentifier.identify(audio) -> SpeakerId`
- `VoiceCommandRouter.route(transcript) -> AgentIntent` (Anbindung an bestehende Agent-/Command-Ebene)

### 3.3 Bekannte Hürden (ehrlich)
- Latenz-Budget für „Conversation Mode" (Barge-in/Interrupt) ist hart: Wake→STT→Agent→TTS unter ~1 s
  ist nur mit passender Hardware realistisch.
- Modellgrößen (Whisper) und Lizenz/Datenschutz (Sprecherprofile) sind vorab zu klären.
- Existierende `voice/*`-Module im Repo (u.a. `speaker_identification`, `streaming_pipeline`) zuerst
  sichten und wiederverwenden statt neu bauen (standen teils auf der v30.77-Orphan-Liste — Zustand prüfen).

### 3.4 Testbarkeit / Abnahme
- Ports + Router + Voice-Memory: Unit-Tests mit Fake-STT/TTS (Standardlauf, grün).
- Engine-Adapter: Integrationstests mit Golden-Audio (bekannte Phrase) -> Transkript-WER unter Schwelle.
- Abnahme: End-to-End-Latenz- und WER-Ziele auf deiner Maschine.

## 4. Vorgeschlagene Reihenfolge (je eigenes Delta)
1. v30.80 Vision-Ports + OCR-Adapter (Tesseract) + Ingest in Memory/RAG (Standardtests grün, OCR-Integration markiert).
2. v30.81 Screenshot/Desktop-Analyse + Klassifizierung.
3. v30.82 Objekterkennung/Diagramme (GPU-abhängig, optional Cloud-VLM).
4. v30.83 Voice-Ports + Offline-STT (faster-whisper) + TTS (Piper).
5. v30.84 Wake Word + Streaming + Interrupt/Conversation.
6. v30.85 Speaker Profiles + Voice Memory + Agent-Command-Integration.

## 5. Entscheidungen, die ich von dir brauche (vor v30.80)
- Offline-Pflicht oder Cloud-VLM/-STT erlaubt (Datenschutz vs. Qualität/Latenz)?
- Zielhardware (CPU-only? GPU vorhanden?) — bestimmt Modellwahl und Latenzziele.
- Dependency-Politik: schwere ML-Pakete als optionales Extra (`requirements-vision.txt`,
  `requirements-voice.txt`), damit der Kern schlank bleibt.

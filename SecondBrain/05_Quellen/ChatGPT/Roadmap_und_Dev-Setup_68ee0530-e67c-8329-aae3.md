---
title: "Roadmap und Dev-Setup"
type: chatgpt_conversation
source: chatgpt
source_id: "68ee0530-e67c-8329-aae3-24940a0912b3"
created: 2025-10-14
tags:
  - chatgpt
  - code
  - gesundheit
  - import
  - ki
  - obsidian
  - projekt
  - sap
  - tischtennis
  - verein
---


# Roadmap und Dev-Setup

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68ee0530-e67c-8329-aae3-24940a0912b3`
- Nachrichten: 28

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

erstelle mir einen prompt für loveable.dev um nachfolgende idee umzusetzen und zu programmieren. Idee: Das ist eine großartige Idee! Die aktuellen Technologietrends werden stark von **Künstlicher Intelligenz (KI)**, **Automatisierung**, **Personalisierung** und der **Integration von realer und digitaler Welt (AR/VR/Spatial Computing)** dominiert.



Ein Tool, das diese Trends aufgreift und einen echten Mehrwert bietet, wäre ein **KI-gestütztes Tool zur Mikro-Lern-Generierung und Personalisierung**.



***



## Tool-Idee: KI-Lernhappen-Generator 🧠



### Die Idee

Ein Tool, das lange oder komplexe Lerninhalte (z.B. PDFs, lange Blogartikel, Videoskripte, Meeting-Transkripte) entgegennimmt und diese mithilfe von KI in **personalisierte, gamifizierte Mikro-Lern-Einheiten** ("Lernhappen") umwandelt.



### Warum das im Trend liegt

* **KI-gestützte Personalisierung:** KI kann den Lernstil, das aktuelle Wissen und die Präferenzen des Nutzers analysieren, um die *optimale Länge*, das *Format* (Quiz, kurze Zusammenfassung, Visualisierung) und den *Schwierigkeitsgrad* der Lernhappen zu bestimmen.

* **Automatisierung (Generative AI):** Die Generative KI übernimmt die zeitaufwändige Aufgabe, Inhalte zu analysieren und in neue Formate zu übertragen.

* **Fokus auf Effizienz:** In der heutigen schnelllebigen Arbeitswelt ist das sogenannte "Micro-Learning" ein Schlüssel, um Wissen effizient aufzunehmen und zu behalten, ohne stundenlange Lerneinheiten zu benötigen.

* **Web3/Dezentralisierung (Optional):** Man könnte eine Blockchain-Komponente hinzufügen, um Lernleistungen fälschungssicher zu zertifizieren oder Nutzer für das Teilen ihrer Lernfortschritte zu belohnen.



### Konkrete Funktionen



1.  **Inhalts-Upload und -Analyse:**

    * **Eingabe:** Nutzer laden eine Datei hoch (PDF, TXT) oder fügen einen Link/Text ein.

    * **KI-Kern:** Die KI liest den Inhalt ein, extrahiert die Kernkonzepte und erstellt eine Wissensstruktur.



2.  **Lernhappen-Generierung:**

    * Die KI generiert verschiedene Lernformate für dasselbe Konzept:

        * **Flashcards/Kurz-Quiz** (Multiple-Choice oder Lückentext).

        * **2-Minuten-Zusammenfassungen** (als Text oder optional als Audio-Skript).

        * **"Wichtige Fakten"-Listen** für schnelle Wiederholung.



3.  **Personalisierter Lernpfad:**

    * **Benutzerprofil:** Der Nutzer beantwortet Fragen zu seinem Lerntyp (visuell, auditiv, kinästhetisch) und seinem Vorwissen.

    * **Adaptive Wiederholung:** Das Tool nutzt Algorithmen (z.B. Spaced Repetition), um die Lernhappen genau dann wieder vorzulegen, wenn der Nutzer Gefahr läuft, das Wissen zu vergessen, basierend auf seinen bisherigen Quiz-Ergebnissen.



4.  **Gamifizierung (Motivation):**

    * **Punkte und Abzeichen:** Belohnung für abgeschlossene Lektionen und richtige Antworten.

    * **Tägliche Herausforderungen:** Kurze, themenspezifische Quizze, um am Ball zu bleiben.



### Technologische Umsetzung (Vorschlag)



* **Frontend:** React/Vue.js für eine dynamische Web-App (oder eine Cross-Platform-App wie React Native/Flutter).

* **Backend:** Python (mit Frameworks wie FastAPI oder Django) ist ideal, da es eine einfache Anbindung an KI/ML-Bibliotheken ermöglicht.

* **KI/ML:** Du könntest existierende **Large Language Models (LLMs)** nutzen (wie die APIs von Google Gemini, OpenAI oder Open-Source-Modelle) für die Analyse, Zusammenfassung und Quiz-Generierung.



Dieses Projekt bietet dir die Möglichkeit, dich in den Bereichen **KI-Integration, Web-Entwicklung und Benutzeroberflächendesign** zu vertiefen – allesamt gefragte Fähigkeiten in den aktuellen Tech-Trends.

### 2. Assistent

Hier ist ein **kompakter, copy-&-paste-fähiger Prompt** für loveable.dev, der deine Idee als umsetzbares MVP mit klaren Specs, Flows, Datenmodellen und Tests beschreibt.

---

# Projekt: KI-Lernhappen-Generator (Micro-Learning mit Personalisierung & Gamification)

## Ziel
Baue eine Web-App, die lange/komplexe Inhalte (PDF, Text, URL) in **personalisierte, gamifizierte Mikro-Lern­einheiten** (“Lernhappen”) transformiert: Flashcards/Quiz, 2-Minuten-Zusammenfassungen (Text/Audio-Skript) und “Wichtige Fakten” mit **Spaced Repetition** und **Punkten/Badges**.

## Technologiestack (Vorgabe)
- **Frontend:** React + TypeScript, Vite, TailwindCSS; Zustand oder Redux Toolkit für State; React Router.
- **Backend:** Python **FastAPI**; Uvicorn; Pydantic-Schemas; Celery + Redis (asynchron, z.B. Datei-Parsing/LLM-Jobs).
- **DB:** PostgreSQL + SQLAlchemy (Alembic Migrations).
- **Storage:** S3-kompatibel (z.B. MinIO lokal) für Uploads; Presigned URLs.
- **LLM/AI:** Abstrakte “LLMProvider”-Klasse (OpenAI/Gemini/OSS wählbar via ENV). Optional: TTS-Stub für Audio-Skripte.
- **Auth:** JWT (Access/Refresh), E-Mail/Passwort. Optional: OAuth später.
- **Testing:** Pytest (Backend), Vitest/RTL (Frontend).
- **DevX:** Docker-Compose (api, web, db, redis, minio), Makefile mit Targets (dev, test, migrate).

## Kern-Userflows (MVP)
1. **Onboarding & Profil**
   - Nutzer registriert sich, beantwortet 5 kurze Fragen: Lernstil (visuell/auditiv/kinästhetisch), Vorwissen (Anfänger/Mittel/Fortgeschritten), Lernziel (Freitext), tägliche Lernzeit, Sprache.
   - System erzeugt initiale **adaptive Lernparameter** (z.B. Ziel-Lernhappen/Tag).

2. **Inhaltsaufnahme**
   - Quellen: **Upload (PDF, TXT)**, **Direkteingabe (Textfeld)**, **URL-Import** (HTML-Text extrahieren).
   - Nach Upload: asynchroner Job → **Kernkonzepte** extrahieren, Themenstruktur bauen.

3. **Lernhappen-Generierung**
   - Für jedes Konzept generiert das System:
     - **Flashcards/Quiz** (MC & Cloze mit 1 korrekten + 3 Distraktoren).
     - **2-Minuten-Summary** (≈ 250–300 Wörter) + optional **Audio-Skript** (TTS-Stub, Datei generieren).
     - **“Wichtige Fakten”-Liste** (5–8 Bullet-Points).
   - Inhalte werden mit **Schwierigkeitsgrad** und **geschätzter Dauer** versehen.

4. **Personalisierter Lernpfad**
   - Dashboard zeigt **Tagesziel**, fällige Happen via **Spaced Repetition** (SM-2-ähnlich) und neue Einheiten.
   - Quiz bewertet Antworten, passt **E-Faktor/Intervall** an; Performance-Historie sichtbar.

5. **Gamification**
   - Punkte für absolvierte Happen; **Badges** (z.B. “Streak 7 Tage”, “Perfektes Quiz”, “3 Uploads”).
   - **Tägliche Challenge**: 5 Fragen zu zuletzt gelernten Themen.

## Datenmodell (Pydantic/SQLAlchemy – vereinfachte Schemas)
- **User**{ id, email, pw_hash, display_name, created_at }
- **LearningProfile**{ id, user_id(FK), style:enum[visual,auditory,kinesthetic], level:enum[beginner,intermediate,advanced], daily_minutes:int, language:str }
- **Source**{ id, user_id, type:enum[upload,text,url], title, original_url?, file_key?, status:enum[pending,processing,ready,failed], created_at }
- **Concept**{ id, source_id, title, summary_short, difficulty:int(1–5), order_index:int }
- **LearningUnit**{ id, concept_id, kind:enum[flashcard,quiz,summary,facts,audio_script], content:JSONB, est_seconds:int, difficulty:int }
- **SRState**{ id, learning_unit_id, user_id, ef:float, interval_days:int, repetition:int, due_date:date, last_grade:int? }
- **QuizAttempt**{ id, learning_unit_id, user_id, correct:bool, grade:int(0–5), taken_at }
- **Gamification**:
  - **UserPoints**{ user_id, points_total:int }
  - **Badge**{ id, key, name, description, icon }
  - **UserBadge**{ id, user_id, badge_id, earned_at }
- **Challenge**{ id, user_id, date, questions:JSONB, score:int? }

## REST-API (Auszug)
**Auth**
- POST `/auth/register` {email, password, display_name} → {tokens}
- POST `/auth/login` {email, password} → {tokens}
- POST `/auth/refresh` → {tokens}

**Profil**
- GET `/me/profile` → LearningProfile
- PUT `/me/profile` → update

**Quellen & Verarbeitung**
- POST `/sources/upload` → presigned URL + Source
- POST `/sources/url` {url, title?} → Source
- POST `/sources/text` {title, text} → Source
- GET `/sources/:id` → {status, meta}
- Worker-Job: `/internal/jobs/process_source/:id` (nur intern) → extrahiert Konzepte + ruft LLM

**Lernhappen**
- GET `/concepts?source_id=` → [Concept]
- GET `/units?concept_id=&kind=` → [LearningUnit]
- POST `/units/:id/attempt` {grade:int(0–5), correct:bool} → aktualisiert SRState
- GET `/schedule/today` → {due_units:[…], new_units:[…], target:int}

**Gamification**
- GET `/me/points` → {points}
- GET `/me/badges` → [UserBadge]
- GET `/challenge/today` → {questions}  |  POST `/challenge/submit` {answers} → {score, points_awarded}

## LLM-Prompts (Backend – exemplarisch)
- **Konzeptextraktion**
  - Input: Rohtext (max. 8k Tokens/Chunk), Zielgruppe (Level), Sprache.
  - Output JSON: `{ concepts:[{title, summary_short, difficulty(1-5)}] }`
- **Einheiten-Generator**
  - Für jedes Konzept:
    - `flashcards`: `{front, back}`
    - `quiz`: `{question, options:[…], correct_index}`
    - `summary_2min`: Markdown-Text (250–300 Wörter)
    - `facts`: `[{bullet}]`
    - `audio_script`: gesprochener Text (120–150 Sekunden)
  - **Richtlinien**: faktenbasiert, keine Halluzinationen; bei Unsicherheit “Unknown” kennzeichnen; Sprache = Profil.

## Frontend-UI (MVP Screens)
- **Auth & Onboarding Wizard** (5 Schritte, Fortschrittsleiste).
- **Dashboard**: Tagesziel, due/new Units, Streak, Punkte, “Start lernen” CTA.
- **Lernsession**:
  - **Quiz/Card View** mit Tastatur-Shortcuts (1–4, Leertaste für “Zeig Antwort”).
  - Bewertung (0–5) nach Antwort → SR Update + Nächste Karte.
- **Quelle-Detail**: Upload/URL/Text → Fortschritt (Parsing/LLM), Konzepte & Einheitenliste.
- **Profil**: Lernstil/Level/Ziele bearbeiten.
- **Badges**: Raster mit freigeschalteten/gesperrten Abzeichen.
- **Einstellungen**: Sprache, tägliche Lernzeit, Datensicherung/Export.

## Spaced Repetition Logik (SM-2-ähnlich)
- Start: `ef=2.5`, `interval=1` Tag.
- Nach jedem `grade` (0–5):
  - `ef' = max(1.3, ef + (0.1 - (5-grade)*(0.08 + (5-grade)*0.02)))`
  - Falls `grade < 3`: `repetition=0`, `interval=1`
  - Sonst: `repetition+=1`, `interval` Progression: `1, 6, round(prev_interval*ef)`
  - `due_date = today + interval`
- Persistiere pro `user_id` + `learning_unit_id`.

## Akzeptanzkriterien (MVP)
- [ ] Upload von **PDF/TXT** und **URL/Text** erzeugt **Source** mit Status → nach Verarbeitung existieren **≥3 Konzepte** mit **≥1 Einheit pro Konzept**.
- [ ] **Schedule** zeigt fällige Einheiten; Abschluss einer Einheit aktualisiert **SRState** korrekt.
- [ ] **Quiz** funktioniert mit Auswertung, Punkte werden vergeben, Badges werden freigeschaltet (mind. 3 Badge-Regeln).
- [ ] **2-Minuten-Summary** ist 250–300 Wörter; **Audio-Skript** kann als Datei (Text-to-Speech-Stub) heruntergeladen werden.
- [ ] **Onboarding** speichert Lernprofil und beeinflusst Schwierigkeitsgrad & Einheitentypen.
- [ ] Saubere **Docker-Compose**-Entwicklung: `make dev` startet alles; `make test` grün.
- [ ] Mind. **20 Unit-Tests** Backend (LLM-Adapter stubbbar), **10** Frontend-Tests.

## Beispiel-Badge-Regeln
- `streak_3`: 3 Tage in Folge gelernt.
- `perfect_quiz`: 5/5 korrekte Antworten in einer Session.
- `first_upload`: erste Quelle verarbeitet.
- `hundred_points`: 100 Gesamtpunkte.

## Sicherheit & Datenschutz
- Eingaben werden pro User mandantenfähig gespeichert; **Policy**: kein Training auf Userdaten.
- Rate-Limiting: 60 req/min/IP; Uploadgröße begrenzen (z.B. 20 MB).
- File-Scanning (MIME/Extension) + PDF-Text-Extraktion (pdfminer/pymupdf).

## Nicht-Funktionale Anforderungen
- Barrierefreiheit: Tastaturnavigation, ARIA-Labels.
- i18n: Deutsch/Englisch über i18next.
- Performance: 95+ Lighthouse für PWA-Grundlagen.
- Observability: strukturierte Logs, einfache /health-Probes.

## Stretch Goals (nicht blockierend fürs MVP)
- **TTS echt** (Cloud-TTS), **Sprechtempo** wählbar.
- **Leitner-Karteikasten** zusätzlich zu SM-2.
- **Team-Spaces**: Inhalte teilen.
- **Zertifikate/Badges on-chain** (Pluggable, optional).

## Beispiel-API-Responses (Kurz)
- `GET /schedule/today` → `{ target: 10, due_units:[{id,kind,concept_title,est_seconds}], new_units:[…] }`
- `GET /units/:id` → `{ id, kind, content:{…}, difficulty, est_seconds }`
- `POST /units/:id/attempt` → `{ next_due_date, updated_sr:{ef,interval_days,repetition} }`

## Seed-Daten (für Demo)
- Beispielquelle “Einführung in Quantencomputer” → 3 Konzepte (“Qubits”, “Superposition”, “Fehlerkorrektur”) mit je 1 Quiz, 1 Summary, 1 Facts.
- Badges: s.o. (4 Stück).
- Dailies: je 5 Fragen aus letztem Lernverlauf.

---

**Hinweis an loveable.dev:** Erzeuge das vollständige Repo mit oben genannten Services, Routen, Komponenten, Tests, Docker-Compose, Makefile und ENV-Beispielen. Implementiere LLM-Adapter als Interface + Mock, injizierbar über ENV. Fokus auf saubere Architektur, klare Trennung von Domäne/Adapter, und reproduzierbare lokale Entwicklung.

---

Wenn du magst, kann ich dir danach eine knackige Roadmap (Woche 1–3) und Beispiel-LLM-Prompts als Dateien (`/prompts/*.md`) ergänzen.

### 3. Benutzer

ja

### 4. Assistent

Alles klar — hier ist deine **kompakte Roadmap (Woche 1–3)** plus **bereit-zu-kopierende Prompt-Dateien** für `/prompts/*.md` und ein paar nützliche Dev-Beigaben. Du kannst das direkt in loveable.dev als zusätzliche Dateien generieren lassen.

# Roadmap (3 Wochen)

## Woche 1 — Basis & Parsing
**Ziele:** Repo-Struktur, Auth, Upload/Import, LLM-Adapter-Interface, erste Konzeptextraktion.
- **Backend**
  - FastAPI Grundgerüst, JWT Auth, Alembic Migrations.
  - Modelle: User, LearningProfile, Source, Concept, LearningUnit.
  - Endpunkte: `/auth/*`, `/sources/*`, `/concepts`, `/units`.
  - Worker: Celery + Redis, Job `process_source`.
  - PDF/TXT/URL-Extractor, MIME-Checks, 20 MB Limit.
  - **LLMAdapter** Interface + Mock (deterministische Seeds).
- **Frontend**
  - React+TS Setup, Router, Auth-Flows, Onboarding-Wizard (5 Fragen).
  - Quelle-Upload/URL/Text-Import, Source-Detail mit Status.
- **Tests & DevX**
  - Docker Compose (api, web, db, redis, minio), Makefile (`dev`, `test`, `migrate`).
  - Pytest: Models/Repos, erste API-Tests. Vitest: Auth & Onboarding.
**Abnahme:** Upload erzeugt `Source` → Worker setzt `Concepts` (≥3) mit `summary_short`.

## Woche 2 — Lernhappen, SR-Planer, Gamification (V1)
**Ziele:** Einheiten-Generator, SM-2-ähnliche Wiederholung, Punkte/Badges.
- **Backend**
  - `LearningUnit`-Generierung (flashcard, quiz, summary, facts, audio_script stub).
  - `SRState` + `/schedule/today`, `/units/:id/attempt`.
  - Gamification: Punkte-Regeln, Badges + Endpunkte.
- **Frontend**
  - Dashboard (Tagesziel, fällige Happen, Streak, Punkte).
  - Lernsession-Views (Quiz/Card, Tastatur-Shortcuts, Bewertungs-Flow 0–5).
  - Badges-Grid.
- **Tests**
  - SR-Formeln (Property-Tests), Gamification-Regeln, 15+ Backend-Tests gesamt; 8+ Frontend-Tests.
**Abnahme:** Antworten aktualisieren SR korrekt; Badges schalten frei (min. 3 Regeln).

## Woche 3 — Feinschliff, i18n, Barrierefreiheit, Stabilität
**Ziele:** i18n (DE/EN), Accessibility, Observability, Performance-Checks, Demo-Seeds.
- **Backend**
  - i18n-Parameter in Prompts, Rate Limiting, strukturierte Logs, `/health`.
  - Seed-Skript (Quantencomputing-Demo).
- **Frontend**
  - i18next Umschaltung, ARIA-Labels, Lighthouse > 95 für PWA-Basics.
  - Challenge-Flow (tägliche 5 Fragen).
- **Tests**
  - 20+ Backend, 10+ Frontend grün; E2E Smoke (Playwright optional).
**Abnahme:** Demo-Ende-zu-Ende lauffähig, Makefile-Targets grün, Seeds sichtbar.

---

# Datei-Baum (Zusatz)
```
/prompts/
  00_system_policy.md
  10_concept_extraction.md
  20_unit_generation.md
  21_quiz_generator.md
  22_flashcard_generator.md
  23_summary_2min.md
  24_facts_list.md
  25_audio_script.md
  30_sr_tutor_feedback.md
  40_quality_rubric.md
.env.example
/docs/json-schemas.md
```

---

# Prompts (`/prompts/*.md`)

## `00_system_policy.md`
```
Rolle: Du bist ein präziser, faktenorientierter Bildungsassistent. 
Prinzipien:
- Bevorzuge belegbare Aussagen. Wenn Quelle unsicher: antworte mit "Unknown".
- Schreibe in der vom Aufrufer vorgegebenen Sprache.
- Keine personenbezogenen Daten erfinden; keine vertraulichen Inhalte speichern.
- Ausgabe strikt im angeforderten JSON-Schema. Kein Fließtext außerhalb von Feldern.
- Begrenze Halluzinationen: paraphrasiere, abstrahiere, keine erfundenen Zitate.
```

## `10_concept_extraction.md`
```
Aufgabe: Extrahiere Konzepte aus INPUT_TEXT für Zielgruppe {level} und Sprache {lang}.
Ausgabe (JSON):
{
  "concepts":[
    {"title":"...", "summary_short":"max 40 Wörter, prägnant", "difficulty":1-5, "order_index":0}
  ]
}
Regeln:
- 3–7 Konzepte. Keine Duplikate. difficulty kalibriert auf {level}.
- Wenn Inhalt überwiegend prozedural: Konzepte als Schritte benennen.
- Unklare Passagen -> nicht raten, "Unknown" in summary_short.
```

## `20_unit_generation.md`
```
Aufgabe: Erzeuge für das Konzept {concept_title} mehrere Lernhappen.
Eingaben: {lang}, {level}, {learning_style}, {target_duration_seconds}
Ausgabe (JSON):
{
 "units":[
   {"kind":"flashcard","est_seconds":20,"difficulty":1-5,"content":{"front":"...","back":"..."}},
   {"kind":"quiz","est_seconds":40,"difficulty":1-5,"content":{"question":"...","options":["a","b","c","d"],"correct_index":1,"rationales":["...","...","...","..."]}},
   {"kind":"summary","est_seconds":120,"difficulty":1-5,"content":{"markdown":"250–300 Wörter"}}, 
   {"kind":"facts","est_seconds":60,"difficulty":1-5,"content":{"bullets":["5–8 kurze Punkte"]}},
   {"kind":"audio_script","est_seconds":135,"difficulty":1-5,"content":{"text":"gesprochener Stil, klare Pausen"}}
 ]
}
Regeln:
- Sprache = {lang}. Keine Inhaltswiederholung 1:1.
- Distraktoren im Quiz plausibel, aber falsch; rationale je Option.
- Keine Codeblöcke außer in `summary.markdown` wenn nötig.
```

## `21_quiz_generator.md`
```
Ziel: Erzeuge 5 MC-Fragen zu {concept_title}.
Format:
{"questions":[
  {"question":"...","options":["...","...","...","..."],"correct_index":2,"explanation":"1–2 Sätze, warum korrekt"}
]}
Regeln: hohe inhaltliche Präzision, genau eine korrekte Option, Bloom-Level variieren (Remember/Apply/Analyze).
```

## `22_flashcard_generator.md`
```
Ziel: 8 Karteikarten, aktive Erinnerung fördern.
Format: {"cards":[{"front":"Frage/PROMPT","back":"knappe, prüfbare Antwort"}]}
Regeln: eine Information pro Karte; Zahlen/Definitionen bevorzugen.
```

## `23_summary_2min.md`
```
Ziel: 2-Minuten-Zusammenfassung (~250–300 Wörter), {lang}.
Format: {"summary":{"markdown":"..."}, "reading_time_seconds":120}
Regeln: klare Struktur (Problem → Kernideen → Takeaways). Keine Aufzählungsinflation.
```

## `24_facts_list.md`
```
Ziel: 5–8 Kernfakten fürs schnelle Wiederholen.
Format: {"facts":{"bullets":["kurz, präzise"]}}
Regeln: nur prüfbare Aussagen; Zahlen bevorzugen; keine Redundanz zur Summary.
```

## `25_audio_script.md`
```
Ziel: Gesprochenes Skript 120–150 s, {lang}, neutral, freundlich.
Format: {"audio_script":{"text":"...","approx_seconds":135}}
Regeln: kurze Sätze, Signpostings ("Erstens, ..."), keine Tabellen/Code.
```

## `30_sr_tutor_feedback.md`
```
Rolle: Lern-Coach nach einer Antwort mit Note {grade} (0–5).
Eingaben: {concept_title}, Nutzerprofil {level}/{learning_style}, letzte falsche Optionen.
Ausgabe:
{
 "feedback": {
   "one_sentence":"ermutigend, 1 Satz",
   "hint":"kleiner Hinweis ohne Lösung zu verraten",
   "micro_remedial":{"markdown":"~60–90 Wörter, gezielte Erklärung"},
   "followup_question":"eine kurze Kontrollfrage"
 }
}
Regeln: Ton motivierend, aber präzise; keine generischen Floskeln.
```

## `40_quality_rubric.md`
```
Rubrik zur automatischen Qualitätsprüfung (Pass/Fail):
- Faktentreue: keine erfundenen Aussagen; Unsicherheit => "Unknown".
- Sprachqualität: {lang}, klar, ohne Jargonexplosion.
- Pädagogik: aktive Erinnerung, Progression der Schwierigkeit (1–5).
- Form: exakt JSON, keine extraneous tokens.
- Barrierefreiheit: kurze Sätze, verständliche Optionen.
Liefere:
{"rubric_check":{"passed":true|false,"issues":["..."]}}
```

---

# `.env.example`
```
# Backend
DATABASE_URL=postgresql+psycopg://user:pass@db:5432/learnbites
JWT_SECRET=change_me
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=uploads
REDIS_URL=redis://redis:6379/0
LLM_PROVIDER=openai   # openai|gemini|mock
LLM_API_KEY=sk-...

# Frontend
VITE_API_BASE=http://localhost:8000
VITE_DEFAULT_LANG=de
```

---

# `/docs/json-schemas.md` (Kurzreferenz)
```json
// ConceptExtraction
{
  "concepts":[
    {"title":"string","summary_short":"string<=40w","difficulty":1,"order_index":0}
  ]
}
// LearningUnit
{
  "id":"uuid","concept_id":"uuid","kind":"flashcard|quiz|summary|facts|audio_script",
  "difficulty":3,"est_seconds":60,"content":{}
}
// Quiz.content
{
  "question":"string",
  "options":["string","string","string","string"],
  "correct_index":0,
  "rationales":["string","string","string","string"]
}
```

---

# Nächste sinnvolle Schritte
- In loveable.dev: **diese Dateien anlegen**, den LLM-Adapter auf **mock** stellen und mit dem Quantencomputing-Seed die End-to-End-Flows testen.
- Danach: Swap auf echten Provider (ENV), Rate-Limit hochziehen, Lighthouse laufen lassen.

Wenn du magst, liefere ich dir noch **3 konkrete Badge-Regeln als Code** (SQL/Service-Funktionen) und ein **Playwright-Smoke-Skript** für die Lernsession.

### 5. Benutzer

liefere mir den start prompt um das projekt zu beginnen

### 6. Assistent

Hier ist dein **Start-Prompt für loveable.dev**, um das komplette Projekt “KI-Lernhappen-Generator 🧠” anzulegen — inklusive Backend (FastAPI), Frontend (React+TS), Datenmodell, Gamification, LLM-Integration, Docker-Setup und aller wichtigen Dateien. Du kannst ihn direkt in **loveable.dev** in das Eingabefeld kopieren und ausführen:  

---

**Prompt für loveable.dev:**

```
Erstelle ein vollständiges MVP-Projekt mit dem Namen **KI-Lernhappen-Generator** – eine Web-App, die lange Texte (PDF, Artikel, URLs) in personalisierte, gamifizierte Mikro-Lerneinheiten (“Lernhappen”) umwandelt.

### Ziel
Die App analysiert Inhalte mit KI, extrahiert Kernkonzepte und erstellt Flashcards, Quizze, 2-Minuten-Zusammenfassungen, Faktenlisten und Audio-Skripte. Nutzer lernen adaptiv mit Spaced-Repetition, Punkten und Badges.

---

### Technologiestack
**Frontend:** React + TypeScript + Vite + TailwindCSS, Zustand oder Redux Toolkit, React Router  
**Backend:** Python FastAPI + SQLAlchemy + PostgreSQL + Celery + Redis + MinIO  
**KI:** LLM-Adapter (OpenAI/Gemini/Mock)  
**Auth:** JWT-basierte Registrierung/Login  
**Testing:** Pytest (Backend), Vitest/RTL (Frontend)  
**Dev:** Docker-Compose, Makefile, ENV-Beispiele  

---

### Funktionen (MVP)
1. **Onboarding & Profil**
   - Nutzer beantwortet 5 Fragen (Lernstil, Level, Ziel, tägliche Lernzeit, Sprache).
   - Profil beeinflusst generierte Lerneinheiten.

2. **Inhaltsaufnahme**
   - Upload von PDF/TXT oder Eingabe eines Textes/URLs.
   - Backend extrahiert Text → Worker startet KI-Analyse → Konzepte.

3. **Lernhappen-Generierung**
   - Für jedes Konzept generiert KI:
     - Flashcards (Frage/Antwort)
     - Quiz (MC mit Distraktoren + Erklärungen)
     - 2-Minuten-Zusammenfassung
     - Faktenliste (5–8 Punkte)
     - Audio-Skript (Text-Stub)

4. **Lernpfad & Wiederholung**
   - Tagesplan mit fälligen Einheiten per Spaced-Repetition (SM-2-ähnlich).
   - Quiz bewertet Antworten (0–5) → Wiederholintervall & Schwierigkeit anpassen.

5. **Gamification**
   - Punkte & Abzeichen (z.B. “Streak 3 Tage”, “Perfektes Quiz”, “Erster Upload”).
   - Dashboard mit Fortschritt, Tagesziel, Badges, Streak.

---

### Architektur
- **Backend-Modelle:** User, LearningProfile, Source, Concept, LearningUnit, SRState, QuizAttempt, UserPoints, Badge, UserBadge  
- **Worker-Jobs:** Source-Analyse, LLM-Generierung  
- **APIs:**  
  - `/auth/*` (Login/Register/Refresh)  
  - `/sources/*` (Upload, Status)  
  - `/concepts`, `/units`, `/schedule/today`, `/units/:id/attempt`, `/me/badges`  

- **Frontend-Seiten:** Login, Onboarding, Dashboard, Lernsession, Quellen-Detail, Badges, Profil  

---

### Dateien
Lege zusätzlich folgende Dateien an:
- `/prompts/` → KI-Prompts für Konzeptextraktion, Einheiten-Generierung, Feedback (verwende die Detail-Prompts aus meiner Beschreibung)
- `.env.example` mit DB, Redis, MinIO, LLM-Key
- `/docs/json-schemas.md` für API-Beispiele

---

### Dev-Setup
- Docker Compose mit Services: api, web, db, redis, minio  
- Makefile mit Targets: `dev`, `test`, `migrate`  
- Seed-Daten: Beispiel “Einführung in Quantencomputer” (3 Konzepte, je 1 Quiz, Summary, Facts).  

---

### Qualitätskriterien
- Upload → Source mit ≥3 Konzepten → je Konzept ≥1 Lerneinheit  
- SR-Algorithmus funktioniert (SM-2-ähnlich, ef/intervall/grade)  
- Quiz-Session vergibt Punkte, schaltet Badges frei  
- 20 Backend- und 10 Frontend-Tests bestehen  
- Makefile-Build vollständig, App startfähig mit `docker compose up`

---

### Ziel
Erzeuge den vollständigen Code für das MVP (Backend, Frontend, Worker, Tests, Docker-Setup, ENV, Prompts).  
Architektur klar trennen (Domain, API, Infra). Verwende saubere Ordnerstruktur.  
Kommentiere kurz die wichtigsten Module und implementiere Mock-LLM für lokale Tests.

```

---

Wenn du möchtest, kann ich dir zusätzlich den **kompletten Projekt-Titel, Tagline und Kurzbeschreibung (README-Intro)** formulieren, damit loveable.dev sie direkt als Projektbeschreibung anzeigt.  
Soll ich dir das gleich ergänzen?

### 7. Benutzer

ja

### 8. Assistent

Perfekt. Hier bekommst du das vollständige **loveable.dev-Starterpaket**, also den **Start-Prompt inklusive Projektname, Tagline und README-Beschreibung**, damit das System dein Vorhaben sofort als sauberes, professionelles Projekt erkennt und das Repo richtig initialisiert.  
Alles ist so geschrieben, dass du es **direkt komplett kopieren** und in loveable.dev einfügen kannst.

---

### 💡 **LOVEABLE.DEV START-PROMPT – KI-Lernhappen-Generator 🧠**

```
# Projektname
KI-Lernhappen-Generator

# Tagline
Lerne smarter, nicht länger – dein persönlicher KI-Coach für Micro-Learning.

# Projektbeschreibung
Ein KI-gestütztes Lern-Tool, das lange Inhalte in kurze, personalisierte Mikro-Lerneinheiten verwandelt. 
Nutzer können PDFs, Artikel oder Texte hochladen – die App analysiert den Inhalt mithilfe von KI, extrahiert Kernkonzepte 
und erstellt daraus Flashcards, Quizze, 2-Minuten-Zusammenfassungen, Faktenlisten und optionale Audio-Skripte. 
Durch adaptive Wiederholung (Spaced Repetition) und Gamification-Elemente wie Punkte, Abzeichen und tägliche Challenges 
bleibt das Lernen effizient, motivierend und nachhaltig.

---

# Ziel
Erstelle ein vollständiges MVP mit Backend, Frontend, Worker, Tests, Docker-Setup und ENV-Dateien.

---

# Tech Stack
**Frontend:** React + TypeScript + Vite + TailwindCSS + Zustand  
**Backend:** Python FastAPI + SQLAlchemy + PostgreSQL + Celery + Redis + MinIO  
**KI:** Pluggable LLM-Adapter (OpenAI/Gemini/Mock)  
**Auth:** JWT (Access/Refresh)  
**Testing:** Pytest (Backend), Vitest/RTL (Frontend)  
**Dev:** Docker Compose, Makefile, ENV-Beispiel  

---

# Kernfunktionen
1. **Onboarding & Profil**
   - Nutzer beantwortet 5 Fragen (Lernstil, Vorwissen, Ziel, Zeitbudget, Sprache).
   - KI personalisiert Lernhappen anhand des Profils.

2. **Inhaltsaufnahme**
   - Upload von PDF/TXT oder Eingabe eines Textes/URLs.
   - Backend analysiert Text, extrahiert Themen, startet asynchronen LLM-Job.

3. **Lernhappen-Generierung**
   - Für jedes Konzept generiert die KI:
     - Flashcards
     - Quizze mit Erklärungen
     - 2-Minuten-Zusammenfassung
     - Faktenliste
     - Audio-Skript (Text-to-Speech-Stub)

4. **Personalisierter Lernpfad**
   - Adaptive Wiederholung per SM-2-ähnlichem Algorithmus (E-Faktor, Intervall, Bewertung).
   - Tagesplan mit neuen und fälligen Einheiten.

5. **Gamification**
   - Punkte, Abzeichen (z. B. Streaks, Perfekte Quizze, Erster Upload).
   - Dashboard mit Fortschritt, Streaks, Punkten, Challenges.

---

# Architektur
**Backend-Modelle:**
User, LearningProfile, Source, Concept, LearningUnit, SRState, QuizAttempt, UserPoints, Badge, UserBadge  

**Worker-Jobs:**
- Source-Verarbeitung (Textextraktion, Konzeptanalyse)
- LLM-Einheitengenerierung  

**APIs:**
- `/auth/*` – Registrierung, Login, Refresh  
- `/sources/*` – Uploads, Textimport, Status  
- `/concepts`, `/units`, `/schedule/today`  
- `/units/:id/attempt`, `/me/badges`  

**Frontend-Seiten:**
- Login/Registrierung
- Onboarding (Wizard)
- Dashboard (Tagesziel, fällige Happen)
- Lernsession (Quiz/Card)
- Quellen-Detail
- Badges & Profil

---

# Dev Setup
- Docker Compose mit Services: `api`, `web`, `db`, `redis`, `minio`
- Makefile mit Targets: `dev`, `test`, `migrate`
- `.env.example` mit Platzhaltern (DB, Redis, LLM-Key)
- Mock-LLM für lokale Entwicklung
- Seed-Daten: Beispiel “Einführung in Quantencomputer” (3 Konzepte)

---

# Qualitätskriterien
- Upload → erzeugt Concepts (≥3) mit Units  
- Quiz bewertet korrekt, aktualisiert SRState, vergibt Punkte  
- 20 Backend-Tests, 10 Frontend-Tests bestehen  
- App startfähig per `docker compose up`  
- Lighthouse Score ≥95  

---

# Zusätzliche Dateien
Erstelle bitte folgende begleitenden Dateien:

- `/prompts/` → KI-Prompts (Konzeptextraktion, Unit-Generierung, Feedback)
- `.env.example` → Beispiel-Umgebungsvariablen
- `/docs/json-schemas.md` → API- und Datenstrukturen
- `/README.md` → Übersicht & lokale Setup-Anleitung
- `/Makefile` → Targets (dev, test, migrate, seed)
- `/docker-compose.yml` → lokale Multi-Service-Konfiguration

---

# Zielvorgabe an loveable.dev
Erzeuge das vollständige Repo mit lauffähiger Backend- und Frontend-Struktur, 
implementiere alle oben beschriebenen Kern-Features, 
füge Mock-LLM und Beispiel-Daten hinzu, 
und dokumentiere die wichtigsten Routen, Modelle und Prompts sauber im Code.

```

---

Wenn du diesen Prompt einfügst, erstellt loveable.dev ein initiales Repository mit:
- funktionierender Fullstack-Struktur,  
- Test-Setup,  
- Prompts,  
- Docker-Konfiguration,  
- und einer Quantencomputing-Demoquelle für erste Lernhappen.  

Als nächsten Schritt kann ich dir eine **README.md-Vorlage** generieren, die genau zu diesem Setup passt (inklusive Setup-Kommandos und Screenshots-Abschnitt). Möchtest du die gleich dazu?

### 9. Benutzer

ja

### 10. Assistent

Ausgezeichnet. Hier ist deine vollständige **README.md-Vorlage** für das Projekt **KI-Lernhappen-Generator 🧠** – perfekt abgestimmt auf den loveable.dev-Prompt, den du gerade hast.  
Du kannst sie **direkt ins Projektverzeichnis als `/README.md`** übernehmen.  
Sie ist im Stil moderner Open-Source-Projekte gehalten: klar, informativ und sofort lauffähig.  

---

# 🧠 KI-Lernhappen-Generator  
**Lerne smarter, nicht länger – dein persönlicher KI-Coach für Micro-Learning.**

---

## 🚀 Überblick

Der **KI-Lernhappen-Generator** ist eine Web-App, die mithilfe von **Künstlicher Intelligenz** lange oder komplexe Inhalte – etwa PDFs, Artikel oder Meeting-Transkripte – in **personalisierte, gamifizierte Mikro-Lerneinheiten** verwandelt.

Das Ziel: Wissen effizient aufnehmen, wiederholen und langfristig behalten – unterstützt durch **Spaced Repetition**, **Personalisierung** und **Gamification**.

---

## ✨ Hauptfunktionen

- **📘 Inhaltsanalyse:** Lade Texte, PDFs oder URLs hoch – die KI erkennt automatisch Kernkonzepte.  
- **🎯 Personalisierte Lernhappen:** KI generiert Flashcards, Quizze, 2-Minuten-Zusammenfassungen, Faktenlisten und Audio-Skripte.  
- **🔁 Spaced Repetition:** Automatische Wiederholungen nach individuellem Lernfortschritt.  
- **🏅 Gamification:** Punkte, Badges, tägliche Challenges und Fortschrittsstreaks.  
- **🧬 Adaptive Lernpfade:** Lernstil, Vorwissen und Ziel beeinflussen Schwierigkeitsgrad und Format.  

---

## 🧩 Architekturübersicht

**Frontend:** React + TypeScript + TailwindCSS + Zustand  
**Backend:** FastAPI + PostgreSQL + SQLAlchemy + Celery + Redis + MinIO  
**KI:** LLM-Adapter (OpenAI, Gemini oder Mock)  
**Testing:** Pytest (Backend) + Vitest/RTL (Frontend)  
**Container:** Docker Compose  
**Auth:** JWT (Access/Refresh)  

---

## 🏗️ Projektstruktur

```
/backend
  ├── app/
  │   ├── api/
  │   ├── core/
  │   ├── models/
  │   ├── services/
  │   ├── workers/
  │   └── prompts/
  ├── tests/
  ├── main.py
  └── Dockerfile

/frontend
  ├── src/
  │   ├── pages/
  │   ├── components/
  │   ├── store/
  │   └── api/
  ├── vite.config.ts
  ├── tailwind.config.js
  └── Dockerfile

/docker-compose.yml  
/Makefile  
/.env.example  
/docs/json-schemas.md  
/prompts/*.md  
```

---

## ⚙️ Einrichtung

### 1. Voraussetzungen
- Docker & Docker Compose  
- Python 3.11+  
- Node.js 20+  

### 2. Projekt starten
```bash
git clone <repo-url>
cd ki-lernhappen-generator
cp .env.example .env
make dev
```

Das startet:
- Backend (FastAPI auf `localhost:8000`)
- Frontend (Vite Dev Server auf `localhost:5173`)
- PostgreSQL, Redis, MinIO (lokal via Docker)

### 3. Migration & Seed-Daten
```bash
make migrate
make seed
```
Danach ist ein Beispiel-Datensatz verfügbar:
> *“Einführung in Quantencomputer”* mit 3 Konzepten und generierten Lernhappen.

---

## 🧠 Spaced Repetition (SM-2-ähnlich)

Das System nutzt eine vereinfachte Version des **SM-2-Algorithmus** (bekannt aus Anki):

```text
ef' = max(1.3, ef + (0.1 - (5-grade)*(0.08 + (5-grade)*0.02)))
```

- Bei `grade < 3` → Intervall zurücksetzen  
- Sonst → Intervall 1 → 6 → ef * vorheriges Intervall  
- Jede Antwort beeinflusst, wann die Einheit wieder fällig wird.

---

## 🧩 Beispiel-APIs

**Lernplan abrufen:**
```bash
GET /schedule/today
→ {
  "target": 10,
  "due_units": [{"id":"uuid","kind":"quiz","concept_title":"Qubits"}],
  "new_units": [...]
}
```

**Antwort senden:**
```bash
POST /units/:id/attempt
→ {
  "next_due_date": "2025-10-15",
  "updated_sr": {"ef":2.36,"interval_days":6,"repetition":2}
}
```

---

## 🕹️ Frontend-Features (MVP)

- **Onboarding Wizard:** Lernstil, Wissen, Ziele, Sprache  
- **Dashboard:** Tagesziel, Punkte, Badges, Streak  
- **Lernsession:** Quiz & Flashcards, Tastatur-Shortcuts (1–4, Space = “Antwort zeigen”)  
- **Quellen-Ansicht:** Upload-Status, Konzepte & Lernhappen  
- **Badges-Seite:** Freigeschaltete Abzeichen  
- **Profil:** Einstellungen, Sprache, Lernzeit  

---

## 🎮 Beispiel-Badges

| Badge | Bedingung |
|-------|------------|
| 🧭 `streak_3` | 3 Tage hintereinander gelernt |
| 🎯 `perfect_quiz` | 5/5 richtige Antworten in einer Session |
| 🚀 `first_upload` | Erste Quelle verarbeitet |
| 💎 `hundred_points` | 100 Punkte gesammelt |

---

## 📚 Prompts (KI-Steuerung)

Alle Prompts liegen im Ordner `/prompts/` und definieren die Aufgaben der KI:
- `10_concept_extraction.md` → erkennt Themen aus Texten  
- `20_unit_generation.md` → erstellt Lernhappen  
- `30_sr_tutor_feedback.md` → generiert Feedback nach einer Quizrunde  
- `40_quality_rubric.md` → prüft Qualität und Faktentreue  

---

## 🧪 Tests

### Backend
```bash
make test-backend
```
- Pytest deckt Modelle, API, SR-Logik und Prompts ab.

### Frontend
```bash
make test-frontend
```
- Vitest + React Testing Library prüfen Komponenten & Logik.

---

## 🧭 Nächste Schritte

1. LLM-Adapter von Mock auf echten Provider umstellen (`.env → LLM_PROVIDER=openai`)  
2. Audio-Feature mit echtem Text-to-Speech-Dienst erweitern  
3. Team-Funktionen (geteilte Lernräume) hinzufügen  
4. Optionale Zertifikate via Blockchain (Stretch Goal)

---

## 🧑‍💻 Mitwirken

Pull Requests und neue Lernfeatures sind willkommen!  
Achte auf Typerichtung, Tests und klare Commits.

---

## 📄 Lizenz

MIT License © 2025 – Open Learning Systems  
Erstellt mit ❤️ und KI-Unterstützung.

---

## 🪄 Screenshots (optional)

Füge Screenshots hier ein, sobald das Frontend steht:
```
/docs/screenshots/
  dashboard.png
  quiz_session.png
  upload_flow.png
```

---

Wenn du magst, kann ich dir als nächsten Schritt noch ein **Makefile** mit allen wichtigen Entwicklungs-Targets (build/dev/test/migrate/seed/lint) erzeugen, das exakt zu dieser README passt.  
Willst du das noch ergänzen?

### 11. Benutzer

ja

### 12. Assistent

Super — hier ist ein **fertiges Makefile**, das genau zu deinem Setup passt (FastAPI + Celery + PostgreSQL + Redis + MinIO + React/Vite). Du kannst es **als `/Makefile`** speichern. Es enthält komfortable Dev-Targets, Migration/Seed, Tests, Linting/Formatierung, Logs und Wartungs-Shortcuts. Kommentare sind knapp, damit es gut lesbar bleibt.

```Makefile
# ===========================
# KI-Lernhappen-Generator 🧠
# Makefile – Dev-Komfort & CI
# ===========================
SHELL := /bin/bash
.DEFAULT_GOAL := help

# ---- Variablen ----
COMPOSE ?= docker compose
ENV_FILE ?= .env
BACKEND_SVC ?= api
FRONTEND_SVC ?= web
DB_SVC ?= db
REDIS_SVC ?= redis
MINIO_SVC ?= minio
WORKER_SVC ?= worker

# Pfade (bei Bedarf anpassen)
BACKEND_DIR := backend
FRONTEND_DIR := frontend
SEED_SCRIPT := $(BACKEND_DIR)/app/seeds/seed_demo.py
ALEMBIC := $(BACKEND_DIR)/alembic
PYTEST_OPTS ?=
VITEST_OPTS ?=

# ---- Hilfsfunktionen ----
define require_env
	@test -f $(ENV_FILE) || (echo "✖ $(ENV_FILE) fehlt. Kopiere .env.example → .env und passe Variablen an."; exit 1)
endef

# ---- Docker Lifecycle ----
.PHONY: up
up: ## Startet alle Services im Hintergrund
	$(call require_env)
	$(COMPOSE) up -d --build

.PHONY: down
down: ## Stoppt & entfernt Container (Daten bleiben)
	$(COMPOSE) down

.PHONY: clean
clean: ## Stoppt alles & entfernt Volumes/Artefakte
	$(COMPOSE) down -v --remove-orphans

.PHONY: logs
logs: ## Folgt den Logs aller Services
	$(COMPOSE) logs -f --tail=200

.PHONY: ps
ps: ## Zeigt laufende Container
	$(COMPOSE) ps

# ---- Dev-Workflows ----
.PHONY: dev
dev: ## Dev-Modus: startet Stack & folgt Logs (API + Web hot-reload)
	$(MAKE) up
	$(MAKE) logs

.PHONY: restart
restart: ## Neustart aller Services
	$(MAKE) down && $(MAKE) up

# ---- Datenbank & Migrations ----
.PHONY: migrate
migrate: ## Führt Alembic-Migrationen im API-Container aus
	$(COMPOSE) exec $(BACKEND_SVC) alembic upgrade head

.PHONY: makemigrations
makemigrations: ## Erzeugt neue Alembic-Revision (AUTOGEN)
	$(COMPOSE) exec $(BACKEND_SVC) alembic revision --autogenerate -m "auto"

.PHONY: downgrade
downgrade: ## Downgrade auf vorherige Revision
	$(COMPOSE) exec $(BACKEND_SVC) alembic downgrade -1

.PHONY: db-shell
db-shell: ## PSQL-Shell in die DB
	$(COMPOSE) exec $(DB_SVC) psql -U $$POSTGRES_USER -d $$POSTGRES_DB

# ---- Seed & Demo-Daten ----
.PHONY: seed
seed: ## Spielt Demo-Daten ein (Quantencomputing-Beispiel)
	$(COMPOSE) exec $(BACKEND_SVC) python $(SEED_SCRIPT)

# ---- Tests ----
.PHONY: test
test: test-backend test-frontend ## Führt alle Tests aus

.PHONY: test-backend
test-backend: ## Pytest im Backend
	$(COMPOSE) exec $(BACKEND_SVC) pytest -q $(PYTEST_OPTS)

.PHONY: test-frontend
test-frontend: ## Vitest + RTL im Frontend
	$(COMPOSE) exec $(FRONTEND_SVC) npm run test -- $(VITEST_OPTS)

# ---- Lint & Format ----
.PHONY: lint
lint: ## Backend (ruff/mypy) & Frontend (eslint)
	$(COMPOSE) exec $(BACKEND_SVC) ruff check .
	$(COMPOSE) exec $(BACKEND_SVC) mypy app || true
	$(COMPOSE) exec $(FRONTEND_SVC) npm run lint

.PHONY: fmt
fmt: ## Code-Formatierung (black/ruff + prettier)
	$(COMPOSE) exec $(BACKEND_SVC) ruff check . --fix
	$(COMPOSE) exec $(BACKEND_SVC) black .
	$(COMPOSE) exec $(FRONTEND_SVC) npm run format

# ---- Builds ----
.PHONY: build
build: ## Baut Images ohne zu starten
	$(COMPOSE) build --no-cache

.PHONY: web-build
web-build: ## Prod-Build Frontend
	$(COMPOSE) exec $(FRONTEND_SVC) npm run build

# ---- Diagnose & Utility ----
.PHONY: health
health: ## Health-Checks API/Web (einfacher Curl)
	@echo "API:" && curl -sS http://localhost:8000/health || true
	@echo "\nWEB:" && curl -sS http://localhost:5173 || true

.PHONY: minio-setup
minio-setup: ## Erstellt Bucket in MinIO (erfordert mc im Container oder init-script)
	$(COMPOSE) exec $(MINIO_SVC) sh -lc '\
		mc alias set local http://localhost:9000 $$MINIO_ROOT_USER $$MINIO_ROOT_PASSWORD && \
		mc mb -p local/$$MINIO_BUCKET || true && \
		mc ls local \
	'

.PHONY: cache-clear
cache-clear: ## Leert Worker-/API-Caches (falls implementiert)
	$(COMPOSE) exec $(REDIS_SVC) redis-cli FLUSHALL

# ---- Lokale Kommandos (ohne Docker, optional) ----
.PHONY: api-local
api-local: ## Startet FastAPI lokal (Entwicklung, benötigt lokale .venv)
	cd $(BACKEND_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: web-local
web-local: ## Startet Vite lokal (Entwicklung, benötigt node_modules)
	cd $(FRONTEND_DIR) && npm run dev -- --host

# ---- Hilfe ----
.PHONY: help
help: ## Zeigt diese Hilfe
	@echo "Makefile – Kommandos:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS := ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
```

### Hinweise zur Nutzung
- **Erster Start:**  
  ```bash
  cp .env.example .env
  make up
  make migrate
  make seed
  ```
- **Entwicklung mit Live-Logs:** `make dev`  
- **Tests:** `make test-backend` und `make test-frontend`  
- **Format & Lint:** `make fmt && make lint`  
- **Reset (vorsichtig):** `make clean`

Wenn du willst, liefere ich dir als Nächstes eine **docker-compose.yml**, die exakt auf dieses Makefile abgestimmt ist, inklusive Healthchecks, Volumes und Hot-Reload für Backend & Frontend, plus `alembic`- und `ruff/black`-Tooling vorinstalliert.

### 13. Benutzer

ja

### 14. Assistent

Großartig — hier ist eine **sauber abgestimmte `docker-compose.yml`** für dein Projekt. Sie passt zu deinem Makefile, unterstützt Hot-Reload (API & Web), hat sinnvolle Healthchecks, persistente Volumes (Postgres/MinIO) und zieht die Variablen aus `.env`.

Leg die Datei als **`/docker-compose.yml`** ab.

```yaml
version: "3.9"

name: ki-lernhappen-generator

services:
  db:
    image: postgres:16-alpine
    container_name: khg-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-pass}
      POSTGRES_DB: ${POSTGRES_DB:-learnbites}
    ports:
      - "5432:5432"   # für lokale psql-Nutzung; bei Bedarf entfernen
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-user} -d ${POSTGRES_DB:-learnbites}"]
      interval: 5s
      timeout: 3s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: khg-redis
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "no"]
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "PING"]
      interval: 5s
      timeout: 3s
      retries: 10

  minio:
    image: minio/minio:latest
    container_name: khg-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      # Wir verwenden die .env-Werte MINIO_ACCESS_KEY/MINIO_SECRET_KEY
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-minioadmin}
    ports:
      - "9000:9000"  # S3-API
      - "9001:9001"  # MinIO Console (GUI)
    volumes:
      - minio_data:/data
      - minio_config:/root/.minio
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:9000/minio/health/ready || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 20

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: khg-api
    restart: unless-stopped
    env_file:
      - .env
    environment:
      # Fallbacks/Defaults für Dev
      DATABASE_URL: ${DATABASE_URL:-postgresql+psycopg://user:pass@db:5432/learnbites}
      REDIS_URL: ${REDIS_URL:-redis://redis:6379/0}
      MINIO_ENDPOINT: ${MINIO_ENDPOINT:-minio:9000}
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY:-minioadmin}
      MINIO_BUCKET: ${MINIO_BUCKET:-uploads}
      JWT_SECRET: ${JWT_SECRET:-change_me}
      LLM_PROVIDER: ${LLM_PROVIDER:-mock}
      LLM_API_KEY: ${LLM_API_KEY:-}
    volumes:
      - ./backend:/app:cached
    command: >
      sh -c "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8000/health || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 30

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: khg-worker
    restart: unless-stopped
    env_file:
      - .env
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgresql+psycopg://user:pass@db:5432/learnbites}
      REDIS_URL: ${REDIS_URL:-redis://redis:6379/0}
      MINIO_ENDPOINT: ${MINIO_ENDPOINT:-minio:9000}
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY:-minioadmin}
      MINIO_BUCKET: ${MINIO_BUCKET:-uploads}
      LLM_PROVIDER: ${LLM_PROVIDER:-mock}
      LLM_API_KEY: ${LLM_API_KEY:-}
    volumes:
      - ./backend:/app:cached
    command: >
      sh -c "celery -A app.workers.celery_app worker -l INFO"
    depends_on:
      api:
        condition: service_healthy
      redis:
        condition: service_healthy

  web:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: khg-web
    restart: unless-stopped
    env_file:
      - .env
    environment:
      VITE_API_BASE: ${VITE_API_BASE:-http://localhost:8000}
      VITE_DEFAULT_LANG: ${VITE_DEFAULT_LANG:-de}
      NODE_OPTIONS: "--max_old_space_size=4096"
    volumes:
      - ./frontend:/app:cached
    command: ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
    ports:
      - "5173:5173"
    depends_on:
      api:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:5173 || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 30

volumes:
  db_data:
  minio_data:
  minio_config:
```

### Notizen & Tipps
- **`.env` ergänzen:** Falls noch nicht vorhanden, füge diese Keys hinzu (deine Werte einsetzen):
  ```
  POSTGRES_USER=user
  POSTGRES_PASSWORD=pass
  POSTGRES_DB=learnbites
  ```
  Die übrigen Variablen stehen bereits in deiner `.env.example`.

- **MinIO-Bucket initialisieren:** Entweder via App-Autostart oder manuell:
  ```bash
  make minio-setup
  ```
  (setzt den Bucket-Namen aus `MINIO_BUCKET`, z. B. `uploads`)

- **Erststart (schnell):**
  ```bash
  cp .env.example .env
  make up
  make migrate
  make seed
  ```

- **Healthchecks & Abhängigkeiten:** `depends_on` wartet auf gesunde `db/redis/minio` bevor `api` startet; `web` wartet auf `api`. Das spart dir Race Conditions beim ersten Hochfahren.

Wenn du willst, liefere ich dir jetzt noch **Backend- und Frontend-Dockerfiles**, die perfekt zu dieser Compose-Datei passen (inkl. Dev-Hot-Reload, Prod-Build-Stage und kleiner Images).

### 15. Benutzer

ja

### 16. Assistent

Perfekt — hier sind **zwei schlanke, produktionsfähige Dockerfiles** für Backend (FastAPI) und Frontend (React/Vite). Sie unterstützen **Hot-Reload im Dev** (wie in deiner `docker-compose.yml`) und besitzen **Multi-Stage-Builds für Prod**.

---

## `/backend/Dockerfile`
```dockerfile
# =========
# Base (Deps)
# =========
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

# System-Dependencies (psycopg, build tools, curl für Healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements zuerst (schlauer Layer-Cache)
# Falls du pyproject.toml/poetry nutzt, ersetze die nächsten zwei Zeilen entsprechend.
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Optional: Dev-Tools (werden in Prod-Stage weggelassen)
RUN pip install ruff==0.6.8 black==24.8.0 mypy==1.11.1 pytest==8.3.2

# App-Code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# =========
# Dev Image (Hot Reload)
# =========
FROM base AS dev
EXPOSE 8000
# CMD/Entrypoint wird über docker-compose gesetzt (uvicorn --reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =========
# Prod Build (schlank)
# =========
FROM python:3.11-slim AS prod

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System-Dependencies (nur Runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Nur Runtime-Deps kopieren
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install gunicorn uvicorn

# App kopieren
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 8000
# Stabiler Prod-Start: Gunicorn + Uvicorn-Worker
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
```

> Hinweis: Wenn du **Poetry** statt `requirements.txt` nutzt, ersetze den Deps-Part durch:
> ```
> COPY pyproject.toml poetry.lock* ./
> RUN pip install --upgrade pip && pip install poetry && poetry install --no-interaction --no-ansi
> ```

---

## `/frontend/Dockerfile`
```dockerfile
# =========
# Builder (Node deps + Build)
# =========
FROM node:20-alpine AS builder

# Verbesserte Performance bei npm ci
ENV CI=1
WORKDIR /app

# Nur package-Dateien zuerst (Cache!)
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./

# Nutze bevorzugt npm ci; fällt zurück auf npm install, falls kein lockfile
RUN if [ -f package-lock.json ]; then npm ci; \
    elif [ -f pnpm-lock.yaml ]; then npm i -g pnpm && pnpm i --frozen-lockfile; \
    elif [ -f yarn.lock ]; then npm i -g yarn && yarn install --frozen-lockfile; \
    else npm install; fi

# Quellcode
COPY . .

# Prod-Build erzeugen (Vite)
RUN npm run build

# =========
# Dev Image (Hot Reload)
# =========
FROM node:20-alpine AS dev
WORKDIR /app
ENV HOST=0.0.0.0 PORT=5173
# Abhängigkeits-Cache: nur package-Dateien
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN if [ -f package-lock.json ]; then npm ci; \
    elif [ -f pnpm-lock.yaml ]; then npm i -g pnpm && pnpm i --frozen-lockfile; \
    elif [ -f yarn.lock ]; then npm i -g yarn && yarn install --frozen-lockfile; \
    else npm install; fi
# Quellcode wird im Dev via Volume gemounted (siehe docker-compose)
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# =========
# Prod Image (statisch via Nginx)
# =========
FROM nginx:alpine AS prod
# Vite-Build aus Builder Stage
COPY --from=builder /app/dist /usr/share/nginx/html
# Einfache Nginx-Konfig mit History-Fallback für SPAs
RUN printf 'server {\n  listen 80;\n  server_name _;\n  root /usr/share/nginx/html;\n  index index.html;\n  location / {\n    try_files $uri /index.html;\n  }\n}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

### Bonus: `.dockerignore` (empfohlen)

**`/backend/.dockerignore`**
```
__pycache__/
*.pyc
*.pyo
*.pyd
*.pytest_cache/
.cache/
.venv/
dist/
build/
alembic/versions/__pycache__/
```

**`/frontend/.dockerignore`**
```
node_modules/
dist/
.cache/
.vite/
.DS_Store
```

---

### Mini-Checkliste
- In `docker-compose.yml` verwendest du bereits diese Dockerfiles und Dev-Kommandos.
- Für **Prod** kannst du die Services einfach auf die `prod`-Stages umstellen (Build-Target), z. B.:
  ```yaml
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: prod
  web:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: prod
    ports:
      - "8080:80"
  ```
- Achte darauf, dass `requirements.txt` (Backend) bzw. Lockfile (Frontend) vorhanden ist, damit die Layer-Caches greifen.

Möchtest du als Nächstes ein **Migrations- und Seed-Skelett** (Alembic-Setup + `seed_demo.py`), das exakt zu deinen Modellen passt?

### 17. Benutzer

ja

### 18. Assistent

Wunderbar. Hier ist ein **kompaktes, praxisnahes Migrations- & Seed-Skelett** für dein Projekt – exakt abgestimmt auf die zuvor definierten Modelle, Compose-Umgebung und Makefile. Du kannst die Dateien so in dein Repo legen; anschließend laufen `make migrate` und `make seed` sauber durch.

---

## Dateien & Pfade

### `/backend/app/core/settings.py`
```python
import os

class Settings:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:pass@db:5432/learnbites"
    )

settings = Settings()
```

### `/backend/app/db.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `/backend/app/models/__init__.py`
```python
from datetime import datetime, date
import enum
import uuid
from sqlalchemy import (
    Column, String, DateTime, Enum, ForeignKey, Integer, Float, Boolean, Date, JSON, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ---- Enums ----
class SourceType(str, enum.Enum):
    upload = "upload"
    text = "text"
    url = "url"

class SourceStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"

class UnitKind(str, enum.Enum):
    flashcard = "flashcard"
    quiz = "quiz"
    summary = "summary"
    facts = "facts"
    audio_script = "audio_script"

class LearningStyle(str, enum.Enum):
    visual = "visual"
    auditory = "auditory"
    kinesthetic = "kinesthetic"

class Level(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

# ---- Models ----
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    pw_hash = Column(String(255), nullable=False)
    display_name = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    profile = relationship("LearningProfile", back_populates="user", uselist=False)
    points = relationship("UserPoints", back_populates="user", uselist=False)

class LearningProfile(Base):
    __tablename__ = "learning_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    style = Column(Enum(LearningStyle), nullable=False)
    level = Column(Enum(Level), nullable=False)
    daily_minutes = Column(Integer, nullable=False, default=10)
    language = Column(String(10), nullable=False, default="de")

    user = relationship("User", back_populates="profile")

class Source(Base):
    __tablename__ = "sources"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    type = Column(Enum(SourceType), nullable=False)
    title = Column(String(255), nullable=False)
    original_url = Column(Text, nullable=True)
    file_key = Column(String(255), nullable=True)
    status = Column(Enum(SourceStatus), nullable=False, default=SourceStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    concepts = relationship("Concept", back_populates="source", cascade="all,delete-orphan")

class Concept(Base):
    __tablename__ = "concepts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    summary_short = Column(String(400), nullable=False)
    difficulty = Column(Integer, nullable=False, default=1)
    order_index = Column(Integer, nullable=False, default=0)

    source = relationship("Source", back_populates="concepts")
    units = relationship("LearningUnit", back_populates="concept", cascade="all,delete-orphan")

class LearningUnit(Base):
    __tablename__ = "learning_units"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id"), index=True, nullable=False)
    kind = Column(Enum(UnitKind), nullable=False)
    content = Column(JSONB, nullable=False)  # siehe Schemas
    est_seconds = Column(Integer, nullable=False, default=60)
    difficulty = Column(Integer, nullable=False, default=1)

    concept = relationship("Concept", back_populates="units")
    sr_states = relationship("SRState", back_populates="unit", cascade="all,delete-orphan")

class SRState(Base):
    __tablename__ = "sr_states"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_unit_id = Column(UUID(as_uuid=True), ForeignKey("learning_units.id"), index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    ef = Column(Float, nullable=False, default=2.5)
    interval_days = Column(Integer, nullable=False, default=1)
    repetition = Column(Integer, nullable=False, default=0)
    due_date = Column(Date, nullable=False)
    last_grade = Column(Integer, nullable=True)

    unit = relationship("LearningUnit", back_populates="sr_states")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_unit_id = Column(UUID(as_uuid=True), ForeignKey("learning_units.id"), index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    correct = Column(Boolean, nullable=False)
    grade = Column(Integer, nullable=False)  # 0–5
    taken_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class UserPoints(Base):
    __tablename__ = "user_points"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    points_total = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="points")

class Badge(Base):
    __tablename__ = "badges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(64), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(String(255), nullable=False)
    icon = Column(String(64), nullable=True)

class UserBadge(Base):
    __tablename__ = "user_badges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    badge_id = Column(UUID(as_uuid=True), ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

---

## Alembic einrichten

### `/backend/alembic.ini` (minimal)
```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+psycopg://user:pass@db:5432/learnbites

[loggers]
keys = root,sqlalchemy,alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = INFO
formatter = generic

[formatters]
keys = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

### `/backend/alembic/env.py`
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# Alembic Config
config = context.config

# Laufzeit-URL via ENV (übersteuert alembic.ini)
db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata
from app.models import Base  # noqa
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### `/backend/alembic/versions/0001_init.py`
```python
"""init schema

Revision ID: 0001_init
Revises:
Create Date: 2025-10-14 10:00:00

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Enums
    source_type = sa.Enum("upload", "text", "url", name="sourcetype")
    source_status = sa.Enum("pending", "processing", "ready", "failed", name="sourcestatus")
    unit_kind = sa.Enum("flashcard","quiz","summary","facts","audio_script", name="unitkind")
    learning_style = sa.Enum("visual","auditory","kinesthetic", name="learningstyle")
    level = sa.Enum("beginner","intermediate","advanced", name="level")

    source_type.create(op.get_bind(), checkfirst=True)
    source_status.create(op.get_bind(), checkfirst=True)
    unit_kind.create(op.get_bind(), checkfirst=True)
    learning_style.create(op.get_bind(), checkfirst=True)
    level.create(op.get_bind(), checkfirst=True)

    # Tables
    op.create_table(
        "users",
        sa.Column("id", psql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("pw_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "learning_profiles",
        sa.Column("id", psql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", psql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("style", learning_style, nullable=False),
        sa.Column("level", level, nullable=False),
        sa.Column("daily_minutes", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(10), nullable=False),
    )
    op.create_index("ix_learning_profiles_user_id", "learning_profiles", ["user_id"])

    op.create_table(
        "sources",
        sa.Column("id", psql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", psql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", source_type, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("original_url", sa.Text(), nullable=True),
        sa.Column("file_key", sa.String(255), nullable=True),
        sa.Column("status", source_status, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sources_user_id", "sources", ["user_id"])

    op.create_table(
        "concepts",
        sa.Column("id", psql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", psql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary_short", sa.String(400), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
    )
    op.create_index("ix_concepts_source_id", "concepts", ["source_id"])

    op.create_table(
        "learning_units",
        sa.Column("id", psql.UUID(as_uuid=True), primary_key=True),
        sa.Column("concept_id", psql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("kind", unit_kind, nullable=False),
        sa.Column("content", psql.JSONB(), nullable=False),
        sa.Column("est_seconds", sa.Integer(), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
    )
    op.create_index("ix_learning_units_concept_id", "learning_units", ["concept_id"])

    op.create_table(
        "sr_states",
        sa.Column("id", psql.UUID(as_uuid=True), primary_key=True),
        sa.Column("learning_unit_id", psql.UUID(as_uuid=True), sa.ForeignKey("learning_units.id"), nullable=False),
        sa.Column("user_id", psql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("ef", sa.Float(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("repetition", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("last_grade", sa.Integer(), nullable=True),
    )
    op.create_index("ix_sr_states_unit_id", "sr_states", ["learning_unit_id"])
    op.create_index("ix_sr_states_user_id", "sr_states", ["user_id"])

    op.create_table(
        "quiz_attempts",
        sa.Column("id", psql.UUID(as_uuid=True), primary_key=True),
        sa.Column("learning_unit_id", psql.UUID(as_uuid=True), sa.ForeignKey("learning_units.id"), nullable=False),
        sa.Column("user_id", psql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("taken_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_quiz_attempts_user_id", "quiz_attempts", ["user_id"])

    op.create_table(
        "user_points",
        sa.Column("user_id", psql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("points_total", sa.Integer(), nullable=False),
    )

    op.create_table(
        "badges",
        sa.Column("id", psql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("icon", sa.String(64), nullable=True),
    )

    op.create_table(
        "user_badges",
        sa.Column("id", psql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", psql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("badge_id", psql.UUID(as_uuid=True), sa.ForeignKey("badges.id"), nullable=False),
        sa.Column("earned_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_user_badges_user_id", "user_badges", ["user_id"])

def downgrade() -> None:
    op.drop_table("user_badges")
    op.drop_table("badges")
    op.drop_table("user_points")
    op.drop_table("quiz_attempts")
    op.drop_table("sr_states")
    op.drop_table("learning_units")
    op.drop_table("concepts")
    op.drop_table("sources")
    op.drop_table("learning_profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    for enum in ["sourcetype","sourcestatus","unitkind","learningstyle","level"]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
```

---

## Seed-Skript (Demo)

### `/backend/app/seeds/seed_demo.py`
```python
import uuid
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from app.db import SessionLocal
from app.models import (
    User, LearningProfile, Source, SourceType, SourceStatus,
    Concept, LearningUnit, UnitKind, SRState, UserPoints,
    Badge, UserBadge, LearningStyle, Level
)

# --- Mock-Generatoren (für lokale Seeds ohne LLM) ---
def mk_flashcard(front, back):
    return {"front": front, "back": back}

def mk_quiz(q, options, correct_idx, rationales):
    return {"question": q, "options": options, "correct_index": correct_idx, "rationales": rationales}

def mk_summary(md):
    return {"markdown": md}

def mk_facts(bullets):
    return {"bullets": bullets}

def mk_audio_script(text):
    return {"text": text, "approx_seconds": 135}

def ensure_badges(db: Session):
    specs = [
        ("streak_3", "Streak 3", "3 Tage in Folge gelernt", "🔥"),
        ("perfect_quiz", "Perfektes Quiz", "5/5 richtige Antworten", "🎯"),
        ("first_upload", "Erster Upload", "Erste Quelle verarbeitet", "🚀"),
        ("hundred_points", "100 Punkte", "100 Gesamtpunkte erreicht", "💎"),
    ]
    for key, name, desc, icon in specs:
        if not db.query(Badge).filter_by(key=key).first():
            db.add(Badge(key=key, name=name, description=desc, icon=icon))
    db.commit()

def main():
    db = SessionLocal()
    try:
        # --- User + Profil ---
        email = "demo@example.com"
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                pw_hash=generate_password_hash("demo1234"),
                display_name="Demo User",
                created_at=datetime.utcnow(),
            )
            db.add(user)
            db.commit()

        if not user.points:
            db.add(UserPoints(user_id=user.id, points_total=0))
            db.commit()

        if not user.profile:
            prof = LearningProfile(
                user_id=user.id,
                style=LearningStyle.visual,
                level=Level.beginner,
                daily_minutes=10,
                language="de",
            )
            db.add(prof)
            db.commit()

        ensure_badges(db)

        # --- Source: Einführung in Quantencomputer ---
        title = "Einführung in Quantencomputer"
        src = db.query(Source).filter_by(user_id=user.id, title=title).first()
        if not src:
            src = Source(
                user_id=user.id,
                type=SourceType.text,
                title=title,
                status=SourceStatus.ready,
                created_at=datetime.utcnow(),
            )
            db.add(src)
            db.commit()

        # --- Konzepte (3 Stück) ---
        concepts_data = [
            ("Qubits", "Qubits sind die quantenmechanischen Gegenstücke zu Bits: Zustände |0>, |1> und deren Superposition.", 2, 0),
            ("Superposition", "Überlagerung quantenmechanischer Zustände; Messung kollabiert in Basiszustand.", 3, 1),
            ("Fehlerkorrektur", "Spezielle Codes, die Quantendekohärenz durch Redundanz kompensieren.", 4, 2),
        ]
        created_concepts = []
        for title_c, summary_short, diff, idx in concepts_data:
            c = db.query(Concept).filter_by(source_id=src.id, title=title_c).first()
            if not c:
                c = Concept(
                    source_id=src.id,
                    title=title_c,
                    summary_short=summary_short,
                    difficulty=diff,
                    order_index=idx,
                )
                db.add(c)
                db.commit()
            created_concepts.append(c)

        # --- Units pro Konzept ---
        for concept in created_concepts:
            # Skip, wenn bereits Units vorhanden
            if db.query(LearningUnit).filter_by(concept_id=concept.id).first():
                continue

            # Flashcard
            fc = LearningUnit(
                concept_id=concept.id,
                kind=UnitKind.flashcard,
                content=mk_flashcard(
                    front=f"Was ist {concept.title}?",
                    back=concept.summary_short
                ),
                est_seconds=20,
                difficulty=concept.difficulty
            )
            # Quiz
            qz = LearningUnit(
                concept_id=concept.id,
                kind=UnitKind.quiz,
                content=mk_quiz(
                    q=f"Welche Aussage zu {concept.title} ist korrekt?",
                    options=[
                        "Es ist klassisch und deterministisch.",
                        "Es existiert nur als |0> oder |1> ohne Überlagerung.",
                        "Es nutzt quantenmechanische Eigenschaften wie Superposition.",
                        "Es ist ausschließlich ein Hardware-Begriff ohne Mathematik."
                    ],
                    correct_idx=2,
                    rationales=[
                        "Falsch: Quanten != strikt klassisch.",
                        "Falsch: Superposition ist zentral.",
                        "Richtig: Kerneigenschaft.",
                        "Falsch: Mathematisches & physikalisches Konstrukt."
                    ]
                ),
                est_seconds=45,
                difficulty=max(1, concept.difficulty)
            )
            # Summary
            sm = LearningUnit(
                concept_id=concept.id,
                kind=UnitKind.summary,
                content=mk_summary(
                    md=(
                        f"**{concept.title}** im Kontext von Quantencomputern: "
                        "Kurze Einführung, praktische Relevanz und ein minimales Beispiel, "
                        "warum klassische Intuition hier begrenzt ist. "
                        "Merke: Mathematische Beschreibung über Zustandsvektoren und Operatoren."
                    )
                ),
                est_seconds=120,
                difficulty=concept.difficulty
            )
            # Facts
            fa = LearningUnit(
                concept_id=concept.id,
                kind=UnitKind.facts,
                content=mk_facts([
                    "Zustände werden als Vektoren beschrieben.",
                    "Messung verändert den Zustand.",
                    "Dekohärenz ist der Feind der Stabilität.",
                    "Fehlerkorrektur benötigt Redundanz.",
                    "Algorithmen nutzen Interferenz-Effekte."
                ]),
                est_seconds=60,
                difficulty=concept.difficulty
            )
            # Audio Script
            au = LearningUnit(
                concept_id=concept.id,
                kind=UnitKind.audio_script,
                content=mk_audio_script(
                    text=(
                        f"Heute sprechen wir über {concept.title}. "
                        "In knapp zwei Minuten klären wir den Kernbegriff, "
                        "seine Bedeutung und die typische Stolperfalle: Intuition aus der klassischen Welt."
                    )
                ),
                est_seconds=135,
                difficulty=concept.difficulty
            )

            for u in (fc, qz, sm, fa, au):
                db.add(u)
            db.commit()

            # Erzeuge SR-States (erste Fälligkeit: morgen)
            units = db.query(LearningUnit).filter_by(concept_id=concept.id).all()
            for u in units:
                srs = SRState(
                    learning_unit_id=u.id,
                    user_id=user.id,
                    ef=2.5,
                    interval_days=1,
                    repetition=0,
                    due_date=date.today() + timedelta(days=1),
                    last_grade=None
                )
                db.add(srs)
            db.commit()

        # Punkte & ein Badge als Demo
        up = db.query(UserPoints).filter_by(user_id=user.id).first()
        if up and up.points_total < 50:
            up.points_total = 50
            db.commit()

        first_upload = db.query(Badge).filter_by(key="first_upload").first()
        if first_upload and not db.query(UserBadge).filter_by(user_id=user.id, badge_id=first_upload.id).first():
            db.add(UserBadge(user_id=user.id, badge_id=first_upload.id))
            db.commit()

        print("✅ Seed erfolgreich: Demo-User, Profile, Badges, Source, Konzepte & Units angelegt.")

    finally:
        db.close()

if __name__ == "__main__":
    main()
```

---

## Minimalanforderungen für das Backend-Env

### `/backend/requirements.txt` (Beispiel)
```
fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.9.2
SQLAlchemy==2.0.36
psycopg[binary]==3.2.1
alembic==1.13.2
python-multipart==0.0.9
passlib[bcrypt]==1.7.4
Werkzeug==3.0.4
```
> Deine Dev-Tools (ruff/black/pytest/mypy) sind bereits im Dockerfile-Dev-Stage vorgesehen; optional hier ergänzen.

---

## Health-Endpoint (falls noch nicht vorhanden)

### `/backend/app/main.py` (Ausschnitt)
```python
from fastapi import FastAPI
from app.models import Base
from app.db import engine

app = FastAPI(title="KI-Lernhappen-Generator")

@app.get("/health")
def health():
    # Kurzer DB-Ping
    with engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1")
    return {"status": "ok"}
```

---

## Checkliste zum Loslegen

1. Dateien wie oben anlegen.
2. `cp .env.example .env` (DB/Redis/MinIO/LLM setzen).
3. **Starten:** `make up`
4. **Migrationen:** `make migrate`
5. **Seed:** `make seed`
6. Im Browser: Frontend-Dev (`http://localhost:5173`) — mit Demo-User `demo@example.com` / Passwort `demo1234` (falls du im Auth-Flow nutzt).

---

Neugier-Bonus: Als nächstes lohnt sich ein kleiner **Service für SM-2-Updates** (`app/services/srs.py`), der die Formel kapselt und via `POST /units/:id/attempt` aufgerufen wird – damit bleiben Quiz-Logik und Wiederholplanung sauber getrennt.

### 19. Benutzer

entwickle ihn

### 20. Assistent

Hier ist die **fertige SM-2-Service-Implementierung** inkl. API-Endpoint und Tests. Du kannst die Dateien direkt so in dein Backend legen. Die Logik entspricht dem zuvor besprochenen Ablauf: E-Faktor-Update, Intervallberechnung, Due-Date, optionales Initialisieren eines SR-States, und Persistenz inkl. `QuizAttempt`.

---

## `/backend/app/services/srs.py`
```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models import SRState, LearningUnit, QuizAttempt


@dataclass(frozen=True)
class SRParams:
    """SM-2-ähnliche Parameter."""
    min_ef: float = 1.3
    start_ef: float = 2.5
    first_interval: int = 1   # Tage
    second_interval: int = 6  # Tage


def _update_e_factor(prev_ef: float, grade: int, min_ef: float) -> float:
    """
    Offizielle SM-2-Formel:
    ef' = max(1.3, ef + (0.1 - (5-grade)*(0.08 + (5-grade)*0.02)))
    """
    delta = 0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)
    new_ef = prev_ef + delta
    return max(min_ef, new_ef)


def _next_interval_days(repetition: int, prev_interval: int, ef: float, p: SRParams) -> int:
    """
    Intervall-Progression: 1, 6, round(prev * ef), ...
    repetition zählt erfolgreiche Bewertungen (grade >= 3).
    """
    if repetition == 1:
        return p.first_interval
    if repetition == 2:
        return p.second_interval
    # ab der dritten Wiederholung:
    return max(1, round(prev_interval * ef))


def _find_sr_state(db: Session, user_id, unit_id) -> Optional[SRState]:
    stmt = select(SRState).where(
        and_(SRState.user_id == user_id, SRState.learning_unit_id == unit_id)
    )
    return db.execute(stmt).scalars().first()


def _ensure_sr_state(db: Session, user_id, unit_id, p: SRParams) -> SRState:
    sr = _find_sr_state(db, user_id, unit_id)
    if sr:
        return sr
    # Initial fällig morgen
    sr = SRState(
        learning_unit_id=unit_id,
        user_id=user_id,
        ef=p.start_ef,
        interval_days=p.first_interval,
        repetition=0,
        due_date=date.today() + timedelta(days=p.first_interval),
        last_grade=None,
    )
    db.add(sr)
    db.flush()
    return sr


def update_sr_for_attempt(
    db: Session,
    *,
    user_id,
    unit_id,
    grade: int,
    correct: bool,
    today: Optional[date] = None,
    params: SRParams = SRParams(),
) -> Tuple[SRState, date]:
    """
    Wendet SM-2-ähnliche Regeln an und legt zusätzlich einen QuizAttempt an.
    Gibt den aktualisierten SRState und das nächste Fälligkeitsdatum zurück.
    """
    if not (0 <= grade <= 5):
        raise ValueError("grade must be between 0 and 5")

    today = today or date.today()

    # Validierung: Unit existiert?
    unit = db.get(LearningUnit, unit_id)
    if unit is None:
        raise ValueError("learning unit not found")

    # SR-State holen/erzeugen
    sr = _ensure_sr_state(db, user_id, unit_id, params)

    # E-Faktor-Update
    new_ef = _update_e_factor(sr.ef, grade, params.min_ef)

    if grade < 3:
        # Fehlversuch → Reset von Wiederholung und Intervall
        repetition = 0
        next_interval = params.first_interval
    else:
        # Erfolgreiche Wiederholung
        repetition = sr.repetition + 1
        prev_interval = sr.interval_days if sr.interval_days > 0 else params.first_interval
        next_interval = _next_interval_days(repetition, prev_interval, new_ef, params)

    next_due = today + timedelta(days=next_interval)

    # Persistiere SR
    sr.ef = float(new_ef)
    sr.interval_days = int(next_interval)
    sr.repetition = int(repetition)
    sr.due_date = next_due
    sr.last_grade = int(grade)

    # Attempt speichern (für Analytics & Gamification)
    attempt = QuizAttempt(
        learning_unit_id=unit_id,
        user_id=user_id,
        correct=bool(correct),
        grade=int(grade),
    )
    db.add(attempt)

    db.commit()
    db.refresh(sr)
    return sr, next_due
```

---

## API-Endpoint (Integration)

### `/backend/app/api/routes/learning.py` (Ausschnitt)
```python
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.srs import update_sr_for_attempt
from app.models import SRState

# TODO: Ersetze diese Dummy-User-Funktion durch deinen Auth-Dependency
def get_current_user_id():
    # Integriere deine JWT-Auth und liefere die user_id
    # Platzhalter:
    from uuid import UUID
    return UUID("00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/units", tags=["learning"])

class AttemptIn(BaseModel):
    grade: int = Field(ge=0, le=5)
    correct: bool

class AttemptOut(BaseModel):
    next_due_date: date
    updated_sr: dict

@router.post("/{unit_id}/attempt", response_model=AttemptOut)
def post_attempt(unit_id: str, body: AttemptIn, db: Session = Depends(get_db)):
    try:
        user_id = get_current_user_id()
        sr, next_due = update_sr_for_attempt(
            db,
            user_id=user_id,
            unit_id=unit_id,
            grade=body.grade,
            correct=body.correct,
        )
        return AttemptOut(
            next_due_date=next_due,
            updated_sr={
                "ef": sr.ef,
                "interval_days": sr.interval_days,
                "repetition": sr.repetition,
                "last_grade": sr.last_grade,
                "due_date": sr.due_date,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

> Binde `router` in deiner `app/main.py` ein:
```python
from fastapi import FastAPI
from app.api.routes.learning import router as learning_router

app = FastAPI(title="KI-Lernhappen-Generator")
app.include_router(learning_router)
```

---

## Unit-Tests

### `/backend/tests/test_srs.py`
```python
from datetime import date, timedelta
from uuid import uuid4
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, LearningUnit, UnitKind, SRState
from app.services.srs import update_sr_for_attempt, SRParams

# In-Memory-DB (oder nutze deine Test-DB-Factory)
engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()

def create_unit(db):
    u = LearningUnit(
        id=uuid4(),
        concept_id=uuid4(),
        kind=UnitKind.flashcard,
        content={"front": "F?", "back": "A"},
        est_seconds=20,
        difficulty=1,
    )
    db.add(u)
    db.commit()
    return u

def test_first_successful_attempt_sets_interval_and_due(db):
    u = create_unit(db)
    user_id = uuid4()
    today = date(2025, 10, 14)

    sr, due = update_sr_for_attempt(
        db, user_id=user_id, unit_id=str(u.id), grade=4, correct=True, today=today
    )
    assert sr.repetition == 1
    assert sr.interval_days == SRParams().first_interval == 1
    assert sr.ef >= SRParams().min_ef
    assert due == today + timedelta(days=1)

def test_second_successful_attempt_sets_interval_6(db):
    u = create_unit(db)
    user_id = uuid4()
    today = date(2025, 10, 14)

    # first success
    update_sr_for_attempt(db, user_id=user_id, unit_id=str(u.id), grade=4, correct=True, today=today)
    # second success
    sr, due = update_sr_for_attempt(db, user_id=user_id, unit_id=str(u.id), grade=5, correct=True, today=today)
    assert sr.repetition == 2
    assert sr.interval_days == SRParams().second_interval == 6
    assert due == today + timedelta(days=6)

def test_failure_resets_repetition_and_interval(db):
    u = create_unit(db)
    user_id = uuid4()
    today = date(2025, 10, 14)

    # two successes to move forward
    update_sr_for_attempt(db, user_id=user_id, unit_id=str(u.id), grade=4, correct=True, today=today)
    update_sr_for_attempt(db, user_id=user_id, unit_id=str(u.id), grade=4, correct=True, today=today)
    # now fail
    sr, due = update_sr_for_attempt(db, user_id=user_id, unit_id=str(u.id), grade=2, correct=False, today=today)
    assert sr.repetition == 0
    assert sr.interval_days == SRParams().first_interval == 1
    assert due == today + timedelta(days=1)

def test_third_success_uses_multiplicative_interval(db):
    u = create_unit(db)
    user_id = uuid4()
    today = date(2025, 10, 14)

    # success 1 -> interval 1
    update_sr_for_attempt(db, user_id=user_id, unit_id=str(u.id), grade=4, correct=True, today=today)
    # success 2 -> interval 6
    update_sr_for_attempt(db, user_id=user_id, unit_id=str(u.id), grade=4, correct=True, today=today)
    # success 3 -> round(prev * ef)
    sr, _ = update_sr_for_attempt(db, user_id=user_id, unit_id=str(u.id), grade=4, correct=True, today=today)
    assert sr.repetition == 3
    assert sr.interval_days >= 6  # mit ef ~2.5 wird es >= 15

def test_grade_bounds(db):
    u = create_unit(db)
    user_id = uuid4()
    with pytest.raises(ValueError):
        update_sr_for_attempt(db, user_id=user_id, unit_id=str(u.id), grade=6, correct=True)
    with pytest.raises(ValueError):
        update_sr_for_attempt(db, user_id=user_id, unit_id=str(u.id), grade=-1, correct=True)
```

---

## Kurz-Notizen zur Integration

- Der Service **initialisiert SR-Zustände on-demand**, falls eine Einheit erstmals bearbeitet wird.
- `grade` steuert beides: **E-Faktor** und **Intervall/Reset**. `correct` wird für Analytics/Gamification gespeichert.
- Du kannst **Gamification** (Punkte, Badges) im Endpoint nach `update_sr_for_attempt` ergänzen, z. B.:
  - Punkte pro richtiger Antwort
  - Streak-Badge bei täglicher Aktivität
  - “perfect_quiz”, wenn eine Session 5/5 korrekt war

Wenn du willst, liefere ich dir noch eine kleine **Points-&-Badges-Service-Datei** mit drei Beispielregeln und Hooks für den obigen Endpoint.

### 21. Benutzer

ja

### 22. Assistent

Alles klar – hier ist ein **kompakter Gamification-Service** mit Punkten & Badges plus **Endpoint-Hook** und **Tests**. Er passt zu deinen bestehenden Modellen und dem SRS-Endpoint von eben.

---

## `/backend/app/services/gamification.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, distinct

from app.models import (
    UserPoints, UserBadge, Badge, QuizAttempt, Source
)


# -----------------------
# Konfiguration & Ergebnis
# -----------------------

@dataclass(frozen=True)
class PointsConfig:
    base_correct: int = 10          # Punkte für korrekte Antwort
    base_incorrect: int = 2         # Trostpunkte für falsche Antwort
    high_grade_bonus_min: int = 4   # ab welcher Note zusätzlicher Bonus
    high_grade_bonus_pts: int = 5   # Bonuspunkte bei hoher Note


@dataclass(frozen=True)
class GamificationResult:
    points_awarded: int
    points_total: int
    badges_awarded: List[str]   # Badge-Keys


# -----------------------
# Punkte-Logik
# -----------------------

def award_points_for_attempt(
    db: Session, user_id, *, correct: bool, grade: int, cfg: PointsConfig = PointsConfig()
) -> Tuple[int, int]:
    """
    Vergibt Punkte für einen Versuch und aktualisiert UserPoints.
    Returns: (awarded, new_total)
    """
    awarded = cfg.base_correct if correct else cfg.base_incorrect
    if grade >= cfg.high_grade_bonus_min:
        awarded += cfg.high_grade_bonus_pts

    up = db.get(UserPoints, user_id)
    if not up:
        up = UserPoints(user_id=user_id, points_total=0)
        db.add(up)
        db.flush()

    up.points_total += awarded
    db.flush()
    return awarded, up.points_total


# -----------------------
# Badge-Helfer
# -----------------------

def _has_user_badge(db: Session, user_id, badge_key: str) -> bool:
    q = (
        db.query(UserBadge)
        .join(Badge, UserBadge.badge_id == Badge.id)
        .filter(and_(UserBadge.user_id == user_id, Badge.key == badge_key))
    )
    return db.query(q.exists()).scalar()


def _award_badge(db: Session, user_id, badge_key: str) -> Optional[str]:
    """Verleiht Badge, wenn vorhanden und noch nicht vergeben. Gibt key zurück, sonst None."""
    if _has_user_badge(db, user_id, badge_key):
        return None
    badge = db.query(Badge).filter(Badge.key == badge_key).first()
    if not badge:
        return None  # Badge nicht im System angelegt (Seed!)
    db.add(UserBadge(user_id=user_id, badge_id=badge.id))
    db.flush()
    return badge_key


# -----------------------
# Streak-Berechnung (einfach)
# -----------------------

def _current_learning_streak_days(db: Session, user_id) -> int:
    """
    Zählt die Anzahl an aufeinander folgenden Tagen (inkl. heute),
    an denen der Nutzer mind. einen QuizAttempt hatte.
    """
    # Hole Distinct-Datumswerte (UTC) der Versuche
    rows = (
        db.query(func.date(QuizAttempt.taken_at))
        .filter(QuizAttempt.user_id == user_id)
        .distinct()
        .order_by(func.date(QuizAttempt.taken_at).desc())
        .all()
    )
    days = [r[0] for r in rows]
    if not days:
        return 0

    streak = 0
    today = date.today()
    cursor = today
    for d in days:
        if d == cursor:
            streak += 1
            cursor = cursor - timedelta(days=1)
        elif d < cursor:
            # Lücke → Streak beendet
            break
        else:
            # Zukünftiges Datum sollte nicht vorkommen; ignoriere
            continue
    return streak


# -----------------------
# Badge-Regeln
# -----------------------

def evaluate_and_award_badges(
    db: Session,
    *,
    user_id,
    # Kontext: perfekte Session kann vom Aufrufer signalisiert werden
    perfect_quiz: bool = False,
) -> List[str]:
    awarded: List[str] = []

    # 1) first_upload — sobald mind. eine Source existiert
    has_source = db.query(Source).filter(Source.user_id == user_id).first() is not None
    if has_source:
        key = _award_badge(db, user_id, "first_upload")
        if key:
            awarded.append(key)

    # 2) streak_3 — 3 Tage in Folge aktiv
    if _current_learning_streak_days(db, user_id) >= 3:
        key = _award_badge(db, user_id, "streak_3")
        if key:
            awarded.append(key)

    # 3) hundred_points — Schwelle für Gesamtpunkte
    up = db.get(UserPoints, user_id)
    if up and up.points_total >= 100:
        key = _award_badge(db, user_id, "hundred_points")
        if key:
            awarded.append(key)

    # 4) perfect_quiz — nur wenn explizit übergeben (Session-Logik liegt im Caller)
    if perfect_quiz:
        key = _award_badge(db, user_id, "perfect_quiz")
        if key:
            awarded.append(key)

    return awarded


# -----------------------
# Öffentliche Kombi-Funktion
# -----------------------

def process_gamification_after_attempt(
    db: Session,
    *,
    user_id,
    correct: bool,
    grade: int,
    perfect_quiz: bool = False,
    cfg: PointsConfig = PointsConfig(),
) -> GamificationResult:
    pts_awarded, pts_total = award_points_for_attempt(db, user_id, correct=correct, grade=grade, cfg=cfg)
    badges = evaluate_and_award_badges(db, user_id=user_id, perfect_quiz=perfect_quiz)
    db.commit()
    return GamificationResult(points_awarded=pts_awarded, points_total=pts_total, badges_awarded=badges)
```

---

## Endpoint-Hook ergänzen

### `/backend/app/api/routes/learning.py` (Erweiterung deines vorhandenen Endpoints)

```python
from app.services.gamification import process_gamification_after_attempt, GamificationResult

class AttemptOut(BaseModel):
    next_due_date: date
    updated_sr: dict
    gamification: dict  # { points_awarded, points_total, badges_awarded }

@router.post("/{unit_id}/attempt", response_model=AttemptOut)
def post_attempt(unit_id: str, body: AttemptIn, db: Session = Depends(get_db)):
    try:
        user_id = get_current_user_id()

        # 1) SR-Update
        sr, next_due = update_sr_for_attempt(
            db,
            user_id=user_id,
            unit_id=unit_id,
            grade=body.grade,
            correct=body.correct,
        )

        # 2) Gamification (perfect_quiz kann vom Client gesetzt werden, wenn Session-Statistik bekannt ist)
        # Hier als Beispiel immer False. Du kannst es über body erweitern (z. B. body.perfect_quiz: bool = False).
        g = process_gamification_after_attempt(
            db,
            user_id=user_id,
            correct=body.correct,
            grade=body.grade,
            perfect_quiz=False,
        )

        return AttemptOut(
            next_due_date=next_due,
            updated_sr={
                "ef": sr.ef,
                "interval_days": sr.interval_days,
                "repetition": sr.repetition,
                "last_grade": sr.last_grade,
                "due_date": sr.due_date,
            },
            gamification={
                "points_awarded": g.points_awarded,
                "points_total": g.points_total,
                "badges_awarded": g.badges_awarded,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

> Wenn du **“perfektes Quiz”** serverseitig erkennen willst, brauchst du Session-Kontext (z. B. eine `session_id`, die 5 Fragen umfasst). Minimal-Variante: Der Client ruft nach 5 Fragen einen Session-Abschluss-Endpoint auf, der `perfect_quiz=True` setzt und `process_gamification_after_attempt` dort triggert.

---

## Tests

### `/backend/tests/test_gamification.py`

```python
import pytest
from datetime import datetime, timedelta, date
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, User, UserPoints, QuizAttempt, Badge, UserBadge, Source
from app.services.gamification import (
    process_gamification_after_attempt,
    award_points_for_attempt,
    _current_learning_streak_days,
)

# SQLite In-Memory
engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()

def mk_user(db):
    u = User(id=uuid4(), email=f"u{uuid4()}@ex.com", pw_hash="x", display_name="U", created_at=datetime.utcnow())
    db.add(u); db.commit()
    return u

def seed_badges(db):
    for key in ["streak_3", "perfect_quiz", "first_upload", "hundred_points"]:
        if not db.query(Badge).filter_by(key=key).first():
            db.add(Badge(key=key, name=key, description=key, icon="*"))
    db.commit()

def test_points_award_correct_and_bonus(db):
    u = mk_user(db)
    seed_badges(db)
    awarded, total = award_points_for_attempt(db, u.id, correct=True, grade=5)
    assert awarded >= 15   # 10 korrekt + 5 Bonus
    assert total == awarded

def test_first_upload_badge(db):
    u = mk_user(db); seed_badges(db)
    # hat noch keine Source → kein Badge
    g = process_gamification_after_attempt(db, user_id=u.id, correct=True, grade=5, perfect_quiz=False)
    assert "first_upload" not in g.badges_awarded

    # jetzt eine Source → Badge sollte kommen
    db.add(Source(user_id=u.id, type="text", title="T", status="ready", created_at=datetime.utcnow()))
    db.commit()
    g = process_gamification_after_attempt(db, user_id=u.id, correct=True, grade=5, perfect_quiz=False)
    assert "first_upload" in g.badges_awarded

def test_streak_3_badge(db):
    u = mk_user(db); seed_badges(db)

    # Erzeuge QuizAttempts an 3 aufeinanderfolgenden Tagen inkl. heute
    for d in [date.today(), date.today()-timedelta(days=1), date.today()-timedelta(days=2)]:
        db.add(QuizAttempt(learning_unit_id=uuid4(), user_id=u.id, correct=True, grade=5, taken_at=datetime(d.year, d.month, d.day, 12, 0, 0)))
    db.commit()

    assert _current_learning_streak_days(db, u.id) >= 3
    g = process_gamification_after_attempt(db, user_id=u.id, correct=True, grade=5, perfect_quiz=False)
    assert "streak_3" in g.badges_awarded

def test_hundred_points_badge(db):
    u = mk_user(db); seed_badges(db)

    # 2x korrekte Versuche mit Bonus → > 30 Punkte
    for _ in range(8):
        g = process_gamification_after_attempt(db, user_id=u.id, correct=True, grade=5, perfect_quiz=False)
    assert g.points_total >= 100
    assert "hundred_points" in g.badges_awarded

def test_perfect_quiz_flag(db):
    u = mk_user(db); seed_badges(db)
    g = process_gamification_after_attempt(db, user_id=u.id, correct=True, grade=5, perfect_quiz=True)
    assert "perfect_quiz" in g.badges_awarded
```

---

## Kurze Integrationshinweise

- Stelle sicher, dass die **Badge-Keys** durch Seeds existieren (du hast sie bereits im Seed-Skript angelegt).
- Für **perfekte Sessions** empfiehlt sich ein kleiner **Session-Controller**:
  - Client sammelt 5 Versuche → ruft `/sessions/:id/complete` auf → Server prüft 5/5 korrekt → `process_gamification_after_attempt(..., perfect_quiz=True)`.
- Die Streak-Logik ist simple und robust: Sie zählt **distinkte Aktivitätstage** (mind. 1 Attempt pro Tag), lückenlos rückwärts ab heute.

Damit hast du ein voll funktionsfähiges **Punkte- & Badge-System**, das sofort mit deinem SRS-Flow zusammenspielt. Nächster sinnvoller Baustein wäre ein kleines **Dashboard-API** (`GET /me/progress`) mit aggregierten Metriken wie `points_total`, `streak_days`, `badges_unlocked`, `due_units_today`.

### 23. Benutzer

Nächster sinnvoller Baustein ein kleines Dashboard-AP

### 24. Assistent

Nice—hier kommt das fehlende **Dashboard-API** als kompakter, anschlussfähiger Baustein. Du bekommst: einen Service zur Aggregation, einen FastAPI-Endpoint, schlanke Pydantic-Schemas und Tests. Plug & play mit deinen bisherigen Modellen, SRS- und Gamification-Services.

---

## `/backend/app/services/dashboard.py`
```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, select, and_

from app.models import (
    User, UserPoints, UserBadge, Badge,
    SRState, LearningUnit, Concept, Source,
    QuizAttempt, LearningProfile
)
from app.services.gamification import _current_learning_streak_days  # bereits implementiert


# ————— Heuristik: Tagesziel aus Lernzeit → #Units —————
def _estimate_daily_target_units(daily_minutes: int, avg_unit_seconds: int = 60) -> int:
    daily_seconds = max(1, daily_minutes) * 60
    return max(3, round(daily_seconds / max(20, avg_unit_seconds)))  # mindestens 3 Einheiten


@dataclass(frozen=True)
class Progress:
    points_total: int
    streak_days: int
    badges_unlocked: List[dict]
    due_units_today: Dict[str, Any]
    new_units_recent: Dict[str, Any]
    today_activity: Dict[str, Any]
    schedule_target_units: int


def _today_bounds() -> tuple[datetime, datetime]:
    # Server-seitig in UTC. Falls du TZ-awareness willst, passe hier an.
    start = datetime.combine(date.today(), datetime.min.time())
    end = datetime.combine(date.today(), datetime.max.time())
    return start, end


def get_progress(db: Session, user_id) -> Progress:
    # Punkte
    points = db.get(UserPoints, user_id).points_total if db.get(UserPoints, user_id) else 0

    # Streak
    streak = _current_learning_streak_days(db, user_id)

    # Badges
    rows = (
        db.query(Badge.key, Badge.name, Badge.icon, UserBadge.earned_at)
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .filter(UserBadge.user_id == user_id)
        .order_by(UserBadge.earned_at.desc())
        .all()
    )
    badges = [
        {"key": k, "name": n, "icon": ic, "earned_at": ea.isoformat()} for (k, n, ic, ea) in rows
    ]

    # Fällige Einheiten heute
    today = date.today()
    due_q = (
        db.query(
            SRState.id,
            SRState.learning_unit_id,
            LearningUnit.kind,
            LearningUnit.est_seconds,
            Concept.title.label("concept_title"),
        )
        .join(LearningUnit, LearningUnit.id == SRState.learning_unit_id)
        .join(Concept, Concept.id == LearningUnit.concept_id)
        .filter(and_(SRState.user_id == user_id, SRState.due_date <= today))
    )
    due_list = [
        {
            "sr_id": r.id,
            "unit_id": str(r.learning_unit_id),
            "kind": r.kind.value if hasattr(r.kind, "value") else str(r.kind),
            "est_seconds": r.est_seconds,
            "concept_title": r.concept_title,
        }
        for r in due_q.limit(25).all()
    ]
    due_count = db.query(func.count(SRState.id)).filter(
        and_(SRState.user_id == user_id, SRState.due_date <= today)
    ).scalar() or 0

    # Neue Einheiten der letzten 7 Tage (für die eigenen Quellen)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    new_units_q = (
        db.query(func.count(LearningUnit.id))
        .join(Concept, Concept.id == LearningUnit.concept_id)
        .join(Source, Source.id == Concept.source_id)
        .filter(and_(Source.user_id == user_id, Concept.id == LearningUnit.concept_id))
        # einfache Heuristik: es gibt kein created_at Feld auf Unit; optional hinzufügen.
    )
    # Wenn du created_at auf LearningUnit hast, ersetze obige Query durch:
    # .filter(and_(Source.user_id == user_id, LearningUnit.created_at >= seven_days_ago))
    new_units_count = new_units_q.scalar() or 0  # ohne created_at: Gesamtzahl (oder ergänze Field)

    # Heute Aktivität (Attempts)
    start, end = _today_bounds()
    attempts_today = (
        db.query(func.count(QuizAttempt.id)).filter(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.taken_at >= start,
                QuizAttempt.taken_at <= end,
            )
        ).scalar()
        or 0
    )
    correct_today = (
        db.query(func.count(QuizAttempt.id)).filter(
            and_(
                QuizAttempt.user_id == user_id,
                QuizAttempt.correct.is_(True),
                QuizAttempt.taken_at >= start,
                QuizAttempt.taken_at <= end,
            )
        ).scalar()
        or 0
    )

    # Tagesziel aus Profil ableiten
    prof = db.query(LearningProfile).filter(LearningProfile.user_id == user_id).first()
    daily_minutes = prof.daily_minutes if prof else 10
    schedule_target = _estimate_daily_target_units(daily_minutes)

    return Progress(
        points_total=points,
        streak_days=streak,
        badges_unlocked=badges,
        due_units_today={"count": due_count, "sample": due_list},
        new_units_recent={"days": 7, "count": new_units_count},
        today_activity={"attempts": attempts_today, "correct": correct_today},
        schedule_target_units=schedule_target,
    )
```

---

## API: `/backend/app/api/routes/me.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Any, Dict

from app.db import get_db
from sqlalchemy.orm import Session
from app.services.dashboard import get_progress

# TODO: ersetze durch deine echte Auth-Dependency (JWT)
def get_current_user_id():
    from uuid import UUID
    return UUID("00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/me", tags=["me"])

class BadgeOut(BaseModel):
    key: str
    name: str | None = None
    icon: str | None = None
    earned_at: str

class DueSampleOut(BaseModel):
    sr_id: str
    unit_id: str
    kind: str
    est_seconds: int
    concept_title: str

class ProgressOut(BaseModel):
    points_total: int = Field(0, description="Gesamtpunkte des Nutzers")
    streak_days: int = Field(0, description="Aktuelle Lernserie in Tagen")
    badges_unlocked: List[BadgeOut]
    due_units_today: Dict[str, Any]  # { count:int, sample: DueSampleOut[] }
    new_units_recent: Dict[str, Any] # { days:int, count:int }
    today_activity: Dict[str, Any]   # { attempts:int, correct:int }
    schedule_target_units: int

@router.get("/progress", response_model=ProgressOut)
def get_me_progress(db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    p = get_progress(db, user_id)
    # Optional: Badge-Namen auffüllen? (im Service ist name/icon enthalten, wenn Join genutzt wird)
    return ProgressOut(
        points_total=p.points_total,
        streak_days=p.streak_days,
        badges_unlocked=p.badges_unlocked,         # [{key,name,icon,earned_at}]
        due_units_today=p.due_units_today,         # {count, sample:[...]}
        new_units_recent=p.new_units_recent,       # {days, count}
        today_activity=p.today_activity,           # {attempts, correct}
        schedule_target_units=p.schedule_target_units,
    )
```

> Registriere den Router in `app/main.py`:
```python
from app.api.routes.me import router as me_router
app.include_router(me_router)
```

---

## Frontend: Beispiel-DTO (TypeScript)
_So kann dein Client das Modell typisieren._
```ts
export type BadgeOut = { key: string; name?: string; icon?: string; earned_at: string }

export type DueSampleOut = {
  sr_id: string; unit_id: string; kind: string; est_seconds: number; concept_title: string
}

export type ProgressOut = {
  points_total: number
  streak_days: number
  badges_unlocked: BadgeOut[]
  due_units_today: { count: number; sample: DueSampleOut[] }
  new_units_recent: { days: number; count: number }
  today_activity: { attempts: number; correct: number }
  schedule_target_units: number
}
```

---

## Tests: `/backend/tests/test_dashboard.py`
```python
import pytest
from datetime import datetime, timedelta, date
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base, User, UserPoints, Badge, UserBadge,
    QuizAttempt, SRState, LearningUnit, UnitKind, Concept, Source
)
from app.services.dashboard import get_progress

engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()

def mk_user(db):
    u = User(id=uuid4(), email=f"u{uuid4()}@ex.com", pw_hash="x", display_name="U", created_at=datetime.utcnow())
    db.add(u); db.commit()
    return u

def mk_badges(db):
    for k in ["streak_3","perfect_quiz","first_upload","hundred_points"]:
        if not db.query(Badge).filter_by(key=k).first():
            db.add(Badge(key=k, name=k, description=k, icon="*"))
    db.commit()

def test_progress_basic(db):
    mk_badges(db)
    u = mk_user(db)

    # Punkte
    db.add(UserPoints(user_id=u.id, points_total=120)); db.commit()

    # Badge vergeben
    b = db.query(Badge).filter_by(key="hundred_points").first()
    db.add(UserBadge(user_id=u.id, badge_id=b.id, earned_at=datetime.utcnow())); db.commit()

    # Source/Concept/Unit + SRState fällig heute
    src = Source(user_id=u.id, type="text", title="T", status="ready", created_at=datetime.utcnow()); db.add(src); db.commit()
    c = Concept(source_id=src.id, title="Qubits", summary_short="...", difficulty=2, order_index=0); db.add(c); db.commit()
    unit = LearningUnit(concept_id=c.id, kind=UnitKind.flashcard, content={"front":"F","back":"A"}, est_seconds=20, difficulty=1)
    db.add(unit); db.commit()
    srs = SRState(learning_unit_id=unit.id, user_id=u.id, ef=2.5, interval_days=1, repetition=0, due_date=date.today(), last_grade=None)
    db.add(srs); db.commit()

    # Attempts heute: 2 / 1 korrekt
    now = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
    db.add(QuizAttempt(learning_unit_id=unit.id, user_id=u.id, correct=True, grade=5, taken_at=now))
    db.add(QuizAttempt(learning_unit_id=unit.id, user_id=u.id, correct=False, grade=2, taken_at=now))
    db.commit()

    p = get_progress(db, u.id)
    assert p.points_total == 120
    assert p.due_units_today["count"] >= 1
    assert p.today_activity["attempts"] == 2
    assert p.today_activity["correct"] == 1
    assert len(p.badges_unlocked) >= 1
    assert p.schedule_target_units >= 3
```

---

## Hinweise & optionale Feinarbeit
- **Performance:** Für große Datenmengen lohnt sich ein Materialized View für `due_units_today` oder ein gezielter Index auf `sr_states(user_id, due_date)`.
- **TZ-Handling:** Falls deine Nutzerzeitzone kritisch ist, speichere `taken_at` in UTC und berechne „heute“ in der Nutzer-TZ.
- **`created_at` auf LearningUnit:** Wenn du „neue Einheiten“ wirklich zeitlich zählen willst, ergänze ein `created_at` Feld und filtere in `new_units_recent` auf `>= now-7d`.

Wenn du möchtest, liefere ich dir noch ein kleines **`/schedule/today`-API**, das direkt die `due_units_today.sample` nutzt und einen “Start lernen”-Cursor zurückgibt (ideal für den Dashboard-CTA).

### 25. Benutzer

ja

### 26. Assistent

Alles klar – hier ist ein kompaktes **Schedule-/Today-API**-Paket: ein Service zur Ermittlung fälliger Lerneinheiten, ein FastAPI-Endpoint mit einfachem Offset-Cursor, passende Schemas und Tests. Plug & play mit deinen bestehenden Modellen und dem Dashboard.

---

## `/backend/app/services/schedule.py`
```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, select

from app.models import SRState, LearningUnit, Concept, LearningProfile


@dataclass(frozen=True)
class TodaySchedule:
    target: int
    total_due: int
    items: List[Dict[str, Any]]
    next_offset: int | None


def _estimate_target(db: Session, user_id) -> int:
    # Zielgröße aus Profil (Fallback: 10 min ≈ 6–10 Happen)
    prof = db.execute(
        select(LearningProfile).where(LearningProfile.user_id == user_id)
    ).scalars().first()
    daily_minutes = prof.daily_minutes if prof else 10
    # konservativ: ~60s pro Happen → Ziel = max(3, min(20, minutes))
    return max(3, min(20, daily_minutes))


def get_today_schedule(
    db: Session, user_id, *, limit: int = 10, offset: int = 0
) -> TodaySchedule:
    today = date.today()

    base_q = (
        db.query(
            SRState.id.label("sr_id"),
            SRState.due_date,
            LearningUnit.id.label("unit_id"),
            LearningUnit.kind,
            LearningUnit.est_seconds,
            LearningUnit.difficulty,
            Concept.title.label("concept_title"),
            Concept.id.label("concept_id"),
        )
        .join(LearningUnit, LearningUnit.id == SRState.learning_unit_id)
        .join(Concept, Concept.id == LearningUnit.concept_id)
        .filter(and_(SRState.user_id == user_id, SRState.due_date <= today))
        .order_by(SRState.due_date.asc(), LearningUnit.difficulty.asc())
    )

    total_due = base_q.count()
    rows = base_q.offset(offset).limit(limit).all()

    items = [
        {
            "sr_id": str(r.sr_id),
            "unit_id": str(r.unit_id),
            "concept_id": str(r.concept_id),
            "concept_title": r.concept_title,
            "kind": r.kind.value if hasattr(r.kind, "value") else str(r.kind),
            "est_seconds": int(r.est_seconds or 60),
            "difficulty": int(r.difficulty or 1),
            "due_date": r.due_date.isoformat(),
        }
        for r in rows
    ]

    target = _estimate_target(db, user_id)
    next_offset = offset + len(items) if (offset + len(items)) < total_due else None

    return TodaySchedule(
        target=target, total_due=total_due, items=items, next_offset=next_offset
    )
```

---

## `/backend/app/api/routes/schedule.py`
```python
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Any

from sqlalchemy.orm import Session
from app.db import get_db
from app.services.schedule import get_today_schedule

# TODO: mit echter JWT-Auth ersetzen
def get_current_user_id():
    from uuid import UUID
    return UUID("00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/schedule", tags=["schedule"])

class ScheduleItemOut(BaseModel):
    sr_id: str
    unit_id: str
    concept_id: str
    concept_title: str
    kind: str
    est_seconds: int
    difficulty: int
    due_date: str

class TodayOut(BaseModel):
    target: int = Field(..., description="Empfohlenes Tagesziel (Anzahl Happen)")
    total_due: int = Field(..., description="Gesamtzahl fälliger Happen heute")
    items: List[ScheduleItemOut]
    next_offset: Optional[int] = Field(None, description="Offset für nächsten Page-Call")

@router.get("/today", response_model=TodayOut)
def get_today(
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    user_id = get_current_user_id()
    sched = get_today_schedule(db, user_id, limit=limit, offset=offset)
    return TodayOut(
        target=sched.target,
        total_due=sched.total_due,
        items=sched.items,
        next_offset=sched.next_offset,
    )
```

> In `app/main.py` registrieren:
```python
from app.api.routes.schedule import router as schedule_router
app.include_router(schedule_router)
```

---

## Frontend: Beispiel-Call (TypeScript)
```ts
export type ScheduleItemOut = {
  sr_id: string; unit_id: string; concept_id: string; concept_title: string;
  kind: string; est_seconds: number; difficulty: number; due_date: string
}
export type TodayOut = {
  target: number; total_due: number; items: ScheduleItemOut[]; next_offset?: number | null
}

export async function fetchTodaySchedule(limit=10, offset=0): Promise<TodayOut> {
  const res = await fetch(`${import.meta.env.VITE_API_BASE}/schedule/today?limit=${limit}&offset=${offset}`, {
    credentials: "include",
  })
  if (!res.ok) throw new Error(`Schedule fetch failed: ${res.status}`)
  return res.json()
}
```

---

## Tests: `/backend/tests/test_schedule.py`
```python
import pytest
from datetime import datetime, date, timedelta
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, User, LearningProfile, Concept, Source, LearningUnit, UnitKind, SRState

engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()

def mk_user(db):
    u = User(id=uuid4(), email=f"u{uuid4()}@ex.com", pw_hash="x", display_name="U", created_at=datetime.utcnow())
    db.add(u); db.commit()
    return u

def mk_stack(db, user_id, n_due=12):
    src = Source(user_id=user_id, type="text", title="T", status="ready", created_at=datetime.utcnow()); db.add(src); db.commit()
    c = Concept(source_id=src.id, title="Topic", summary_short="...", difficulty=2, order_index=0); db.add(c); db.commit()
    # n_due Einheiten: alle fällig heute
    for i in range(n_due):
        u = LearningUnit(concept_id=c.id, kind=UnitKind.flashcard, content={"front": f"F{i}", "back": "A"}, est_seconds=30, difficulty=(i%5)+1)
        db.add(u); db.commit()
        srs = SRState(learning_unit_id=u.id, user_id=user_id, ef=2.5, interval_days=1, repetition=0, due_date=date.today(), last_grade=None)
        db.add(srs); db.commit()

def test_schedule_pagination_and_target(db):
    user = mk_user(db)
    # Profil → 12 Minuten → target ≈ 12 (gedeckelt auf 20, min 3)
    db.add(LearningProfile(user_id=user.id, style="visual", level="beginner", daily_minutes=12, language="de")); db.commit()
    mk_stack(db, user.id, n_due=12)

    # Page 1
    from app.services.schedule import get_today_schedule
    s1 = get_today_schedule(db, user.id, limit=5, offset=0)
    assert s1.target >= 3 and s1.target <= 20
    assert len(s1.items) == 5
    assert s1.total_due == 12
    assert s1.next_offset == 5

    # Page 2
    s2 = get_today_schedule(db, user.id, limit=5, offset=s1.next_offset)
    assert len(s2.items) == 5
    assert s2.next_offset == 10

    # Page 3 (Rest)
    s3 = get_today_schedule(db, user.id, limit=5, offset=s2.next_offset)
    assert len(s3.items) == 2
    assert s3.next_offset is None
```

---

## Mini-Hinweise
- Sortierung: **älteste Fälligkeit zuerst**, dann nach **niedriger Schwierigkeit** – das fühlt sich in Sessions am fairsten an.
- Der Offset-Cursor ist absichtlich simpel und stabil (stateless). Für echte Realtime-Änderungen kannst du zusätzlich `sr_id`-basierte Cursor einführen.
- Möchtest du direkt eine **„Start Lernen“**-Route, die das **erste fällige Item** zurückgibt und optional gleich **lockt** (optimistisch)? Das kann ich dir schnell nachreichen.

### 27. Benutzer

ja

### 28. Assistent

Jawoll—hier ist die **„Start Lernen“**-Funktion als kleines, robustes Paket:  
Wir nehmen das **erste fällige Item** (älteste Fälligkeit, dann niedrigste Schwierigkeit), **reservieren** es per **Redis-Lock (TTL)**, geben es an den Client inkl. **`lock_token`** zurück und bieten Endpoints zum **Starten**, **Freigeben** und **Sicher-Abschließen** (mit Token-Prüfung). Keine DB-Migration nötig.

---

## 1) Redis-Locks (leichtgewichtig, kein Schema-Change)

### `/backend/app/core/redis.py`
```python
import os
import redis

_redis = None

def get_redis():
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        _redis = redis.Redis.from_url(url, decode_responses=True)
    return _redis
```

### `/backend/app/services/start_learning.py`
```python
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict, Any
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.redis import get_redis
from app.models import SRState, LearningUnit, Concept

LOCK_TTL_SECONDS = 10 * 60  # 10 Minuten Reservierung
LOCK_KEY = "learnlock:{user_id}"  # pro Nutzer 1 aktives Item

@dataclass(frozen=True)
class StartItem:
    sr_id: str
    unit_id: str
    concept_id: str
    concept_title: str
    kind: str
    est_seconds: int
    difficulty: int
    due_date: str
    lock_token: str

def _select_first_due(db: Session, user_id) -> Optional[Dict[str, Any]]:
    today = date.today()
    q = (
        db.query(
            SRState.id.label("sr_id"),
            SRState.due_date,
            LearningUnit.id.label("unit_id"),
            LearningUnit.kind,
            LearningUnit.est_seconds,
            LearningUnit.difficulty,
            Concept.title.label("concept_title"),
            Concept.id.label("concept_id"),
        )
        .join(LearningUnit, LearningUnit.id == SRState.learning_unit_id)
        .join(Concept, Concept.id == LearningUnit.concept_id)
        .filter(and_(SRState.user_id == user_id, SRState.due_date <= today))
        .order_by(SRState.due_date.asc(), LearningUnit.difficulty.asc())
        .limit(1)
    )
    r = q.first()
    if not r:
        return None
    return {
        "sr_id": str(r.sr_id),
        "unit_id": str(r.unit_id),
        "concept_id": str(r.concept_id),
        "concept_title": r.concept_title,
        "kind": r.kind.value if hasattr(r.kind, "value") else str(r.kind),
        "est_seconds": int(r.est_seconds or 60),
        "difficulty": int(r.difficulty or 1),
        "due_date": r.due_date.isoformat(),
    }

def start_learning(db: Session, user_id) -> Optional[StartItem]:
    """Wählt erstes fälliges Item & legt einen Redis-Lock mit TTL an."""
    item = _select_first_due(db, user_id)
    if not item:
        return None

    r = get_redis()
    key = LOCK_KEY.format(user_id=str(user_id))
    token = str(uuid4())

    # Wert speichern: token + unit/sr – nur wenn kein aktiver Lock existiert
    payload = {
        "token": token,
        "sr_id": item["sr_id"],
        "unit_id": item["unit_id"],
        "kind": item["kind"],
    }
    # NX = set if not exists
    ok = r.set(key, str(payload), nx=True, ex=LOCK_TTL_SECONDS)
    if not ok:
        # Es gibt bereits ein gelocktes Item → gib nichts Neues aus
        # Alternativ könntest du hier das bestehende Lock zurückgeben.
        return None

    return StartItem(lock_token=token, **item)

def release_lock(user_id, token: str) -> bool:
    """Gibt die Reservierung frei, wenn Token passt."""
    r = get_redis()
    key = LOCK_KEY.format(user_id=str(user_id))
    val = r.get(key)
    if not val:
        return True  # schon frei
    # simple, robuste Prüfung ohne JSON-Parser: String-Containment auf token
    if token and token in val:
        r.delete(key)
        return True
    return False

def validate_and_consume_lock(user_id, sr_id: str, token: str) -> bool:
    """
    Validiert, dass der Nutzer gerade dieses SR-Item reserviert hat.
    Lässt den Lock bestehen (wir verlängern ihn noch kurz), damit bei Retries nicht kollidiert.
    Der Aufrufer kann im Erfolgsfall optional direkt freigeben.
    """
    r = get_redis()
    key = LOCK_KEY.format(user_id=str(user_id))
    val = r.get(key)
    if not val:
        return False
    if token and token in val and sr_id in val:
        # verlängere den Lock leicht, um Rennbedingungen beim Submit zu vermeiden
        r.expire(key, LOCK_TTL_SECONDS)
        return True
    return False
```

---

## 2) API-Endpunkte

### `/backend/app/api/routes/start.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from sqlalchemy.orm import Session
from app.db import get_db
from app.services.start_learning import start_learning, release_lock, validate_and_consume_lock

# TODO: ersetzen durch echte JWT-Auth
def get_current_user_id():
    from uuid import UUID
    return UUID("00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/schedule", tags=["schedule"])

class StartOut(BaseModel):
    sr_id: str
    unit_id: str
    concept_id: str
    concept_title: str
    kind: str
    est_seconds: int
    difficulty: int
    due_date: str
    lock_token: str = Field(..., description="Muss beim Submit mitgeschickt werden")

class ReleaseIn(BaseModel):
    lock_token: str

class ReleaseOut(BaseModel):
    released: bool

@router.post("/start", response_model=StartOut)
def start(db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    item = start_learning(db, user_id)
    if not item:
        raise HTTPException(status_code=404, detail="Kein fälliges Item oder bereits aktiv reserviert.")
    return item

@router.post("/release", response_model=ReleaseOut)
def release(body: ReleaseIn):
    user_id = get_current_user_id()
    ok = release_lock(user_id, body.lock_token)
    return ReleaseOut(released=ok)

# Optional: einfache Validierung (kann im Attempt-Endpoint genutzt werden)
class ValidateIn(BaseModel):
    sr_id: str
    lock_token: str

class ValidateOut(BaseModel):
    ok: bool

@router.post("/validate", response_model=ValidateOut)
def validate(body: ValidateIn):
    user_id = get_current_user_id()
    ok = validate_and_consume_lock(user_id, body.sr_id, body.lock_token)
    return ValidateOut(ok=ok)
```

> In `app/main.py` registrieren:
```python
from app.api.routes.start import router as start_router
app.include_router(start_router)
```

---

## 3) Sichere Verknüpfung mit deinem Attempt-Endpoint

Erweitere deinen bestehenden `/units/{unit_id}/attempt`-Endpoint um **optionale Lock-Prüfung**:  
Wenn Client `sr_id` und `lock_token` mitsendet, wird vor der Bewertung geprüft, ob der Lock passt. So verhinderst du doppelte Bearbeitungen in parallelen Tabs.

### Patch: `/backend/app/api/routes/learning.py` (Erweiterung)
```python
from pydantic import BaseModel, Field
from typing import Optional
from app.services.start_learning import validate_and_consume_lock

class AttemptIn(BaseModel):
    grade: int = Field(ge=0, le=5)
    correct: bool
    sr_id: Optional[str] = None
    lock_token: Optional[str] = None

@router.post("/{unit_id}/attempt", response_model=AttemptOut)
def post_attempt(unit_id: str, body: AttemptIn, db: Session = Depends(get_db)):
    try:
        user_id = get_current_user_id()

        # Falls Lock-Daten vorhanden → validieren
        if body.sr_id and body.lock_token:
            ok = validate_and_consume_lock(user_id, body.sr_id, body.lock_token)
            if not ok:
                raise HTTPException(status_code=409, detail="Ungültiger oder abgelaufener Lern-Lock.")

        # ... danach dein bestehender SR-Update + Gamification-Code ...
        # sr, next_due = update_sr_for_attempt(...)
        # g = process_gamification_after_attempt(...)

        # return AttemptOut(...)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 4) Mini-Tests (Locking)

### `/backend/tests/test_start_learning.py`
```python
import pytest
from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, User, LearningProfile, Source, Concept, LearningUnit, UnitKind, SRState
from app.services.start_learning import start_learning, release_lock, validate_and_consume_lock
from app.core.redis import get_redis

engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()

def mk_due_item(db, user_id):
    src = Source(user_id=user_id, type="text", title="T", status="ready", created_at=datetime.utcnow()); db.add(src); db.commit()
    c = Concept(source_id=src.id, title="Topic", summary_short="...", difficulty=2, order_index=0); db.add(c); db.commit()
    u = LearningUnit(concept_id=c.id, kind=UnitKind.flashcard, content={"front":"F","back":"A"}, est_seconds=30, difficulty=1)
    db.add(u); db.commit()
    srs = SRState(learning_unit_id=u.id, user_id=user_id, ef=2.5, interval_days=1, repetition=0, due_date=date.today(), last_grade=None)
    db.add(srs); db.commit()
    return srs.id, u.id

def test_start_and_release(db, monkeypatch):
    # Redis isolieren (echter Redis in Compose, hier: optional überspringen, falls nicht verfügbar)
    r = get_redis()
    try:
        r.ping()
    except Exception:
        pytest.skip("Redis nicht verfügbar im Testumfeld")

    user_id = uuid4()
    mk_due_item(db, user_id)

    item = start_learning(db, user_id)
    assert item is not None
    assert item.lock_token

    # Zweiter Start sollte None liefern (Lock aktiv)
    item2 = start_learning(db, user_id)
    assert item2 is None

    # Validierung: ok
    assert validate_and_consume_lock(user_id, item.sr_id, item.lock_token) is True

    # Release
    assert release_lock(user_id, item.lock_token) is True
    # Danach wieder startbar
    again = start_learning(db, user_id)
    assert again is not None
```

---

## 5) Frontend-Hinweis (brauchst du nur, wenn du magst)

- On Dashboard-CTA „Start lernen“:
  1) `POST /schedule/start` → Item + `lock_token` merken (im State).
  2) Lernansicht rendern; beim **Submit** des Versuchs `sr_id` + `lock_token` mitsenden.
  3) Abbruch? → `POST /schedule/release` mit `lock_token`.

So vermeidest du *„zwei Tabs, ein Item“*-Chaos, ohne deine DB anzufassen.  
Wenn du später **Sessions** brauchst (5 Fragen am Stück, Navigation vor/zurück), können wir das Lock auf **Session-IDs** ausweiten oder pro Nutzer mehrere parallele Locks für unterschiedliche Units erlauben (einfach `LOCK_KEY` anpassen).

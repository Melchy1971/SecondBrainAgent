---
title: "Projektstruktur Analyse"
type: chatgpt_conversation
source: chatgpt
source_id: "69e0b0df-376c-838a-b3ba-22067d42178d"
created: 2026-04-16
tags:
  - chatgpt
  - code
  - import
  - ki
  - obsidian
  - projekt
  - sap
---


# Projektstruktur Analyse

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69e0b0df-376c-838a-b3ba-22067d42178d`
- Nachrichten: 24

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich möchte ein neus Projekt beginnen. dies ist die grundlage inkl. struktur dafür. Tools: Chat pgd plus, Code, Claude Pro. beachte beim entwickeln möglichst wenige Tokens bei Claude zu verbrauchen. die beschreibung des tool erfolgt nach deiner analyse der start struktur

### 2. Assistent

Ich prüfe die Projektbasis im ZIP, extrahiere die Struktur und leite daraus eine token-effiziente Tool- und Arbeitsaufteilung für ChatGPT Plus, Code und Claude Pro ab. Danach formuliere ich die empfohlene Entwicklungslogik direkt auf Basis der vorhandenen Startstruktur.

### 3. Assistent

Die Basis ist kein inhaltlich befülltes Projekt, sondern ein leeres Scaffold. Alle Dateien haben aktuell Größe 0 Byte. Damit ist die relevante Information nicht Implementierungslogik, sondern die vorgesehene Betriebsstruktur: Agents, Commands, Skills, Docs, Plugins, Scripts, Source, Types.

### 4. Assistent

Analyse der Startstruktur

Befund:
Das ZIP enthält ein vollständiges Projekt-Scaffold, aber ohne Inhalte. Sämtliche Dateien sind leer. Damit existiert aktuell nur die Soll-Struktur des Systems, nicht die fachliche oder technische Ausprägung.

Erkannte Struktur:
- `.claude/` → Claude-spezifische Laufzeit- und lokale Einstellungen
- `agents/` → spezialisierte Rollen für wiederkehrende Aufgaben
- `commands/` → standardisierte Arbeitsbefehle / Workflows
- `docs/` → Architektur, Onboarding, API-Dokumentation
- `plugins/` → Plugin-/Erweiterungspunkt
- `scripts/` → Setup, Seed, Deploy
- `skills/` → wiederverwendbare Fähigkeitsmodule / Leitfäden
- `src/services/` → Kernlogik für fachliche Dienste
- `src/utils/` → Hilfsfunktionen, Logging, Validierung
- `types/` → zentrale Typdefinitionen
- Root-Dateien für Runtime/Build/Meta: `package.json`, `tsconfig.json`, `Dockerfile`, `env.example`, `.mcp.json`, `CLAUDE.md`

Implikation:
Die Struktur ist gut als AI-gestütztes Entwicklungsframework gedacht. Sie trennt:
- operative Ausführung (`commands`)
- Expertenrollen (`agents`)
- standardisierte Qualitätsmuster (`skills`)
- eigentlichen Code (`src`)
- Dokumentation (`docs`)

Das ist kein fertiges Produktgerüst, sondern ein AI-orchestriertes Meta-Projektgerüst.

Bewertung der Struktur

Stärken:
- klare Trennung von Code, Dokumentation und AI-Arbeitslogik
- geeignet für agentische Entwicklung
- gut skalierbar für mehrere wiederkehrende Entwicklungsaufgaben
- vorbereitet für standardisierte Reviews, Tests, Security, Deployment

Schwächen:
- kein fachliches Domänenmodell
- kein Datenmodell
- keine Entscheidung zur Laufzeitarchitektur
- keine Build-/Testdefinition
- keine Priorisierung der AI-Tools
- kein Token-Governance-Modell für Claude

Verdeckte Abhängigkeiten:
- Ohne klare Konvention für `agents`, `commands` und `skills` entsteht Redundanz
- Ohne Eingrenzung der Tool-Rollen wird Claude unnötig als Generalist verwendet
- Ohne kompakten Projektkontext steigt Tokenverbrauch bei jedem Prompt
- Ohne zentrales Architektur-Dokument werden Tools gegeneinander inkonsistent arbeiten

Schlussfolgerung:
Die Struktur ist als Startpunkt brauchbar, aber nur dann effizient, wenn die Rollen der Tools strikt getrennt werden. Genau das ist für geringe Claude-Kosten entscheidend.

Empfohlene Tool-Zuordnung

1. ChatGPT Plus
Primärwerkzeug für:
- Produktdefinition
- Scope-Zerlegung
- Prozessdesign
- Architekturvarianten
- Datenmodelle
- Prompt-/Agent-/Command-Design
- Refactoring-Konzepte
- Dokumentenproduktion
- Backlog, Roadmap, SOPs, Qualitätskriterien

Warum:
- hohe Breite
- gute Strukturierungsleistung
- ideal für viele Iterationen mit geringer Reibung
- sollte das führende Denk- und Entwurfswerkzeug sein

Rolle im System:
ChatGPT Plus ist der Systemarchitekt und Spezifikationsgenerator.

2. Code
Primärwerkzeug für:
- Implementierung
- Dateioperationen
- lokale Code-Änderungen
- Testausführung
- Fixes
- Build-/Script-Setup
- Boilerplate-Erzeugung
- Repo-weite Änderungen

Warum:
- effizient für konkrete Umsetzung
- geeignet für sequenzielle Codearbeit
- reduziert manuelle Editierarbeit

Rolle im System:
Code ist der Ausführungs- und Änderungsmotor.

3. Claude Pro
Nur selektiv einsetzen für:
- knappe Architekturkritik
- Edge-Case-Prüfung
- Review einzelner kritischer Dateien
- Sicherheitsbewertung
- Verdichtung komplexer Entwürfe in klare Prinzipien
- Gegenprüfung wichtiger Entscheidungen

Nicht einsetzen für:
- Routine-Coding
- wiederholte Scaffold-Generierung
- große Dateimengen
- offene Brainstormings
- Dokumente, die ChatGPT Plus bereits erzeugen kann
- Vollkontext-Analysen des gesamten Repos

Warum:
Claude ist teuer im Tokenverbrauch, wenn er als Generalist oder mit zu viel Kontext genutzt wird.

Rolle im System:
Claude ist der punktuelle Auditor, nicht der Builder.

Token-minimale Entwicklungslogik für Claude

Grundregel:
Claude nie das ganze Projekt geben. Immer nur:
- Ziel
- harte Randbedingungen
- 1 bis 3 relevante Dateien
- gewünschtes Ausgabeformat

Maximalprinzip:
Ein Claude-Prompt muss auf eine einzelne Entscheidung oder Prüfung begrenzt sein.

Geeignete Claude-Aufgaben:
- „Prüfe diese Auth-Service-Datei auf Failure Modes und Security Gaps.“
- „Vergleiche Variante A vs. B für dieses Datenmodell in maximal 12 Punkten.“
- „Finde nur die 5 kritischsten Architekturprobleme.“
- „Verbessere diesen Command-Workflow ohne Stiländerungen.“

Ungeeignete Claude-Aufgaben:
- „Baue mir das ganze Projekt.“
- „Analysiere alle Dateien.“
- „Schreibe vollständige Dokumentation für alles.“
- „Lies den kompletten Repo-Kontext und plane die nächsten Schritte.“

Empfohlene Governance:
- ChatGPT erzeugt Spezifikation
- Code setzt um
- Claude prüft nur kritische Artefakte

Empfohlene Zielstruktur des Projekts

Diese Struktur sollte jetzt inhaltlich befüllt werden:

1. `README.md`
Inhalt:
- Projektzweck
- Kernnutzen
- Setup
- wichtigste Kommandos
- Architekturüberblick
- Tool-Rollen

2. `CLAUDE.md`
Inhalt:
- strikte Claude-Nutzungsregeln
- Prompt-Regeln
- Kontextlimit
- Verbot breiter Repo-Analysen
- bevorzugte Ausgabeformate

3. `.claude/settings.json`
Inhalt:
- Standardverhalten für knappe Antworten
- Fokus auf diff-orientierte Ausgaben
- bevorzugt nur Analyse statt Neuschreiben kompletter Dateien

4. `docs/architecture.md`
Inhalt:
- Systemkontext
- Module
- Datenflüsse
- Schnittstellen
- Constraints
- Skalierungsannahmen

5. `docs/onboarding.md`
Inhalt:
- Projektkonventionen
- Tool-Reihenfolge
- Branching-/Testing-Logik
- Review-Regeln

6. `docs/api-reference.md`
Inhalt:
- Endpunkte
- DTOs
- Fehlercodes
- Auth-Modell

7. `agents/`
Empfohlene Rollen:
- `product-architect.yml`
- `backend-engineer.yml`
- `frontend-engineer.yml`
- `security-auditor.yml`
- `test-writer.yml`
- `code-reviewer.yml`

8. `commands/`
Empfohlene Befehle:
- `bootstrap.md`
- `plan-feature.md`
- `implement-feature.md`
- `review.md`
- `test-all.md`
- `deploy.md`

9. `skills/`
Empfohlene Skills:
- `architecture-decision`
- `refactor`
- `security-audit`
- `test-writer`
- `api-design`
- `token-budgeting`

10. `src/`
Aktuelle Struktur ist brauchbar, aber unvollständig.
Ergänzen:
- `src/domain/`
- `src/modules/`
- `src/config/`
- `src/repositories/`
- `src/controllers/` oder `src/routes/`
- `src/middleware/`

11. `types/index.ts`
Soll zentrale, stabile Verträge enthalten:
- API DTOs
- Domain Types
- Utility Types
- Error Types

Empfohlene Arbeitsordnung

Phase 1: Fundament
- README
- Architektur
- Tool-Governance
- Claude-Regeln
- Commands/Skills definieren

Phase 2: Fachliches Modell
- Domäne
- Use Cases
- Datenobjekte
- Zustände
- Validierungen

Phase 3: Technische Umsetzung
- Services
- Repositories
- APIs
- Scripts
- Tests

Phase 4: Härtung
- Security Review
- Fehlerbilder
- Logging
- Deployment
- Onboarding

Konkrete Tool-Beschreibung für dein Setup

ChatGPT Plus
Beschreibung:
Zentrales Planungs- und Strukturierungswerkzeug. Erstellt Architektur, Prozesse, Dokumente, Prompts, Commands, Agentenlogik und Qualitätsstandards. Sollte immer zuerst genutzt werden, bevor Implementierung beginnt.

Code
Beschreibung:
Umsetzungswerkzeug für Dateien, Struktur, Refactoring, Tests und operative Änderungen. Arbeitet auf klaren, bereits entschiedenen Spezifikationen. Sollte keine Produktentscheidungen treiben, sondern sie umsetzen.

Claude Pro
Beschreibung:
Spezialisierter Prüfmechanismus für kritische Teilprobleme. Einsatz nur bei Architekturkritik, Security, Edge Cases und hochwertigen Reviews einzelner Artefakte. Kein breitflächiges Entwicklungswerkzeug.

Effizientes Betriebsmodell

Standardfluss:
1. ChatGPT Plus definiert
2. Code implementiert
3. Claude prüft selektiv
4. ChatGPT verdichtet Ergebnisse in Dokumentation oder nächste Entscheidung

Kostenlogik:
- 70–80 % ChatGPT Plus
- 15–25 % Code
- 5–10 % Claude Pro

Wichtigster Hebel zur Claude-Einsparung:
Nicht Claude mit fehlender Struktur kompensieren. Erst saubere Spezifikation erzeugen, dann nur gezielte Audits an Claude delegieren.

Nächster sinnvoller Schritt für dieses Projekt:
Die leere Struktur in ein operatives Projekt-Framework umwandeln, beginnend mit:
- `README.md`
- `CLAUDE.md`
- `docs/architecture.md`
- `commands/`
- `agents/`
- `skills/`

Ich kann im nächsten Schritt die Inhalte für diese Dateien direkt in einer ersten produktionsfähigen Fassung ausformulieren.

### 5. Benutzer

ja bitte. das Tool soll eine Datenbank sein mit Frontend und Backend. Backend mit neo4j (Daten vorhanden). Ki ist Ollama Gemma4:31b, Das Front end bekommt die Bereich Import, Suche, Themen, Chat, Einstellungen und Dashboard. Beginne mit dem Menü und frage danach nach welchen Bereich wir angehen und entwickeln. aktualisiere die vorhandenen files mit passendem inhalt

### 6. Assistent

Ich befülle jetzt die vorhandene Struktur mit einer ersten konsistenten Projektbasis für Neo4j + Ollama/Gemma 4 31B und starte beim Menü samt Bereichslogik. Danach liefere ich die aktualisierten Dateien als neues ZIP.

### 7. Assistent

Die inhaltliche Befüllung steht. Ich setze jetzt die Dateien sauber als lauffähige Basis um, inklusive Menü-Endpunkt und Projektregeln.

### 8. Assistent

Dateien aktualisiert. Ergebnis: [Wissen2026-main-updated.zip](sandbox:/mnt/data/Wissen2026-main-updated.zip)

Inhalt der Aktualisierung:
- Menüstruktur als primärer Frontend-Startpunkt definiert
- Projektbasis für Frontend + Backend + Neo4j + Ollama/Gemma 4 31B dokumentiert
- Claude-Token-Governance in `CLAUDE.md` und `.claude/settings.json` festgelegt
- Architektur-, API-, Onboarding- und Menü-Spezifikation ergänzt
- Backend-Basis mit Health- und Menü-Endpunkt angelegt:
  - `GET /api/health`
  - `GET /api/menu`
- Typen für Menüeinträge in `types/index.ts`
- Basisdienste für API, Datenbank, Logger, Validatoren angelegt
- Skripte und Projektmetadaten befüllt

Wesentliche Designentscheidung:
Das Menü ist jetzt der definierte Einstiegspunkt der UI mit diesen Bereichen:
- Dashboard
- Import
- Suche
- Themen
- Chat
- Einstellungen

Empfohlene nächste Entwicklungsreihenfolge:
1. Menü/Navigationslogik im Frontend
2. Dashboard
3. Import
4. Suche
5. Themen
6. Chat
7. Einstellungen

Jetzt der nächste Schritt für die Umsetzung:
Welchen Bereich gehen wir als Erstes an und entwickeln ihn konkret?
- Dashboard
- Import
- Suche
- Themen
- Chat
- Einstellungen

### 9. Benutzer

wir beginnen mit den einstellungen. erstelle mir immer die passenden Prompts mit dem vermerk für welches tool. in den einstellungen kann ich das design von hell auf dunkel ändern und die KI konfigurieren und festlegen

### 10. Assistent

Annahmen:
- Frontend: React oder vergleichbares SPA
- Backend: Node/Express
- Neo4j vorhanden, aber Einstellungen initial unabhängig davon
- Ollama läuft lokal oder via API
- Gemma 4:31b als Default-Modell
- Settings werden persistent gespeichert (JSON oder DB)

Ziel des Settings-Moduls:
- UI-State + Systemkonfiguration bündeln
- zentrale Steuerung für:
  - Theme (hell/dunkel)
  - KI-Konfiguration (Model, Temperatur, Kontextgröße, Endpoint)
- Erweiterbar für spätere Parameter (z. B. Logging, Token-Limits)

---

## Datenmodell (zwingend vor Implementierung)

Struktur:

```ts
Settings {
  theme: "light" | "dark"
  ai: {
    provider: "ollama"
    model: "gemma:31b"
    temperature: number        // 0–1
    maxTokens: number          // begrenzen für Kostenkontrolle
    contextWindow: number      // wichtig für Claude/Ollama
    endpoint: string           // z.B. http://localhost:11434
  }
}
```

Default-Werte:
- theme: light
- model: gemma:31b
- temperature: 0.2 (deterministisch)
- maxTokens: 512
- contextWindow: 4096
- endpoint: http://localhost:11434

---

## Prompt 1 — ChatGPT Plus (Architektur + UX)

Ziel: saubere Spezifikation + UI-Logik

:::writing{variant="standard" id="10001"}
Kontext:
Ich entwickle ein Tool mit Frontend (SPA) und Backend (Node + Neo4j). Es gibt einen Einstellungsbereich mit Fokus auf Theme (hell/dunkel) und KI-Konfiguration (Ollama mit gemma:31b).

Aufgabe:
Erstelle eine vollständige Spezifikation für den Settings-Bereich mit folgenden Punkten:

1. UI-Struktur (Seitenlayout, Sektionen, Komponenten)
2. State-Management (lokal vs. global)
3. Datenmodell für Settings (TypeScript)
4. UX-Logik für:
   - Theme-Umschaltung (inkl. Persistenz)
   - KI-Konfiguration (Formular + Validierung)
5. API-Design:
   - GET /api/settings
   - POST /api/settings
6. Fehlerfälle und Edge Cases
7. Erweiterbarkeit (z. B. weitere KI-Provider)

Constraints:
- Fokus auf einfache, robuste Architektur
- keine unnötige Komplexität
- klare Trennung von UI, State und API
- optimiert für spätere Erweiterung

Output:
Strukturiert, ohne Fließtext, direkt umsetzbar
:::

---

## Prompt 2 — Code (Backend Implementierung)

Ziel: minimaler, sauberer Settings-Service

:::writing{variant="standard" id="10002"}
Kontext:
Node.js Backend mit Express. Ich brauche einen Settings-Service für:
- Theme (light/dark)
- KI-Konfiguration (Ollama, gemma:31b)

Aufgabe:
Implementiere:

1. TypeScript-Typ für Settings
2. Default-Settings
3. In-Memory Store (später ersetzbar durch DB)
4. API-Endpunkte:
   - GET /api/settings
   - POST /api/settings

5. Validierung:
   - theme nur "light" | "dark"
   - temperature: 0–1
   - maxTokens > 0
   - endpoint muss URL sein

6. Struktur:
- src/services/settings.service.ts
- src/routes/settings.routes.ts

7. Fehlerhandling:
- ungültige Eingaben → 400
- interne Fehler → 500

Constraints:
- kein Overengineering
- keine externen Libs außer express
- klar lesbarer Code

Output:
Vollständiger Code für alle Dateien
:::

---

## Prompt 3 — Code (Frontend Settings UI)

Ziel: konkrete UI-Komponenten

:::writing{variant="standard" id="10003"}
Kontext:
Frontend SPA (React). Es gibt einen Settings-Bereich mit:
- Theme Umschaltung
- KI-Konfiguration (Ollama)

Aufgabe:
Erstelle:

1. SettingsPage Component
2. Unterteilung in:
   - ThemeSection
   - AISettingsSection

3. Funktionen:
   - Laden der Settings (GET /api/settings)
   - Speichern (POST /api/settings)
   - Live Theme Switch (light/dark)

4. Formfelder:
   - Model (Text)
   - Temperature (Slider 0–1)
   - Max Tokens (Number)
   - Endpoint (Input)

5. State:
   - local form state
   - global theme state

6. UX:
   - sofortige Theme-Änderung
   - Save Button
   - Loading + Error State

Constraints:
- keine UI-Library (plain React)
- funktionale Komponenten
- klar strukturiert

Output:
Kompletter React-Code
:::

---

## Prompt 4 — Claude Pro (gezielte Optimierung, geringe Tokens)

Ziel: Qualität + Kostenkontrolle

:::writing{variant="standard" id="10004"}
Kontext:
Settings-Modul für ein Tool mit Ollama (gemma:31b). Fokus auf Kosten- und Tokenkontrolle.

Gegeben:
- Settings enthalten temperature, maxTokens, contextWindow

Aufgabe:
Analysiere ausschließlich:
1. Welche Default-Werte minimieren Tokenverbrauch ohne Qualitätsverlust
2. Welche Parameter kritisch für Kosten sind
3. Welche Limits zwingend gesetzt werden müssen
4. 5 konkrete Failure Modes (z. B. runaway token usage)

Constraints:
- maximal 12 Bullet Points
- keine Erklärtexte
- keine Wiederholung des Inputs
- keine Architekturvorschläge

Output:
kompakt, entscheidungsorientiert
:::

---

## Systemlogik (wichtig für spätere Module)

Abhängigkeiten:
- Chat nutzt Settings.ai direkt
- Import nutzt Settings.ai für Parsing
- Suche nutzt Settings.ai für semantische Erweiterung

Risiko ohne Settings:
- inkonsistente KI-Aufrufe
- unkontrollierter Tokenverbrauch
- schwer reproduzierbare Ergebnisse

---

## Nächster Schritt im System

Implementationsreihenfolge innerhalb „Einstellungen“:
1. Backend Settings API
2. Frontend UI
3. Theme-System global aktivieren
4. KI-Config an Chat-Modul anbinden

Danach:
Chat-Modul wird direkt von diesen Settings gesteuert.

### 11. Benutzer

ja weiter

### 12. Assistent

Ich erweitere die Projektbasis jetzt konkret um den Bereich Einstellungen: Datenmodell, Backend-Endpunkte, Frontend-Seite, Theme-Logik und die zugehörigen Tool-Prompts. Danach liefere ich ein neues ZIP mit den angepassten Dateien.

### 13. Assistent

Ich ergänze nicht nur Prompts, sondern auch die erste umsetzbare Settings-Basis im Projekt: Typen, API, Persistenz, Frontend-Komponenten und Spezifikation. Claude bekommt dabei nur die Prüfrolle.

### 14. Assistent

Die Settings-Basis ist inhaltlich eingebaut. Der TypeScript-Build ließ sich im Container nicht vollständig prüfen, weil die lokalen Dev-Abhängigkeiten des Projekts dort nicht installiert sind. Die Projektdateien selbst sind aktualisiert und konsistent strukturiert.

### 15. Assistent

Settings-Bereich in die Projektbasis integriert. Datei: [Wissen2026-main-settings.zip](sandbox:/mnt/data/Wissen2026-main-settings.zip)

Aktualisiert:
- `types/index.ts`
  - `ThemeMode`
  - `AISettings`
  - `Settings`
  - `defaultSettings`
- `src/services/settings.service.ts`
  - Laden
  - Validieren
  - Speichern
  - Datei-Persistenz in `data/settings.json`
- `src/services/api.ts`
  - `GET /api/settings`
  - `POST /api/settings`
  - Menüstatus mit aktivem Bereich `settings`
- `data/settings.json`
  - initiale Default-Konfiguration
- `docs/settings-spec.md`
  - Fachspezifikation für Einstellungen
- `docs/prompts/settings-prompts.md`
  - passende Prompts je Tool
- `docs/api-reference.md`
  - Settings-Endpunkte ergänzt
- `docs/architecture.md`
  - Reihenfolge Menü → Einstellungen → Folgemodule festgelegt
- `README.md`
  - aktueller Fokus auf Einstellungen dokumentiert
- `CLAUDE.md`
  - Claude-Rolle für lokale Inferenzparameter präzisiert

Default-Konfiguration:
- theme: `light`
- provider: `ollama`
- model: `gemma4:31b`
- temperature: `0.2`
- maxTokens: `512`
- contextWindow: `4096`
- endpoint: `http://localhost:11434`

Passende Prompts

ChatGPT Plus
```text
Kontext:
Ich entwickle ein Tool mit Frontend, Backend, Neo4j und Ollama. Der Bereich Einstellungen wird zuerst umgesetzt und soll Theme-Umschaltung und KI-Konfiguration enthalten.

Aufgabe:
Erstelle eine umsetzbare Spezifikation für den Bereich Einstellungen mit:
1. UI-Struktur
2. State-Management
3. Validierungslogik
4. API-Vertrag
5. Fehlerfällen
6. Erweiterungspfad für spätere Provider und weitere Konfigurationsfelder

Rahmenbedingungen:
- Theme: light/dark
- KI: Ollama, Default-Modell gemma4:31b
- Settings enthalten provider, model, temperature, maxTokens, contextWindow, endpoint
- Fokus auf robuste, einfache Architektur

Ausgabeformat:
- nur strukturierte Punkte
- keine Einleitung
- direkt umsetzbar
```

Code
```text
Kontext:
TypeScript-Backend mit node:http. Ich brauche einen Settings-Service mit Datei-Persistenz.

Aufgabe:
Implementiere oder aktualisiere diese Dateien:
- types/index.ts
- src/services/settings.service.ts
- src/services/api.ts

Anforderungen:
- GET /api/settings
- POST /api/settings
- Theme light/dark
- ai.provider fest auf ollama
- ai.model als Text
- ai.temperature 0 bis 1
- ai.maxTokens positive Ganzzahl
- ai.contextWindow positive Ganzzahl
- ai.endpoint valide URL
- Default-Werte: theme=light, model=gemma4:31b, temperature=0.2, maxTokens=512, contextWindow=4096, endpoint=http://localhost:11434
- Datei-Persistenz in data/settings.json
- Fehlerhafte Eingaben = 400
- saubere Typisierung

Ausgabeformat:
- vollständiger Code pro Datei
- keine Erklärung außerhalb des Codes
```

Code
```text
Kontext:
Ich baue eine Settings-Seite für ein Frontend mit den Bereichen Anzeige und KI-Konfiguration.

Aufgabe:
Erzeuge React-Komponenten für:
- SettingsPage
- ThemeSection
- AISettingsSection

Anforderungen:
- GET /api/settings beim Laden
- POST /api/settings beim Speichern
- Theme-Umschaltung light/dark mit sofortiger UI-Wirkung
- Formularfelder: model, temperature, maxTokens, contextWindow, endpoint
- Loading-, Save- und Error-State
- keine UI-Library
- funktionale Komponenten
- klare Trennung zwischen Formularzustand und Theme-State

Ausgabeformat:
- vollständiger Code pro Datei
- keine Fließtext-Erklärung
```

Claude Pro
```text
Kontext:
Settings-Modul für lokales KI-System mit Ollama und gemma4:31b.

Prüfe ausschließlich:
1. Sind die Default-Werte für lokale Inferenz konservativ genug?
2. Welche 5 Failure Modes erzeugen die größten Betriebsrisiken?
3. Welche Parametergrenzen müssen hart validiert werden?

Rahmenbedingungen:
- Antworte in maximal 12 Bullet Points
- keine Wiederholung der Eingabe
- keine Architektur-Neuentwürfe
- Fokus auf Runtime-Risiko, Ressourcenverbrauch und Fehlkonfiguration
```

Einschränkung:
Der TypeScript-Build wurde im Container nicht vollständig ausgeführt, weil die lokalen Dev-Abhängigkeiten des Projekts dort nicht installiert waren. Die Dateien sind dennoch konsistent befüllt und strukturell passend vorbereitet.

Nächster logischer Schritt:
Frontend für Einstellungen konkret ausimplementieren. Danach folgt der nächste Bereich. Welchen Bereich gehen wir nach den Einstellungen an:
- Dashboard
- Import
- Suche
- Themen
- Chat

### 16. Benutzer

chat gpt pro nicht beachten und nicht jedesmal eine neue zip datei erstellen. erstelle mir nur die programmier prompts für codex und claude cowork

### 17. Assistent

Ich prüfe kurz die Bezeichnung „Claude cowork“, damit die Prompts sauber auf das richtige Toolformat zugeschnitten sind. Danach liefere ich nur noch die Programmier-Prompts für Codex und Claude.

### 18. Assistent

Verstanden. Ab jetzt nur noch Programmier-Prompts für **Codex** und **Claude Cowork**. Die Bezeichnung **Claude Cowork** ist korrekt; Anthropic beschreibt es als agentisches System für mehrstufige Aufgaben auf dem Desktop. Für **Codex** sind klare, schrittweise Arbeitsaufträge mit Test-/Repair-Schleife passend. citeturn943626search1turn943626search7turn943626search0turn943626search6

## Codex — Prompt für den Bereich **Einstellungen**

```text
Aufgabe:
Implementiere den Bereich "Einstellungen" in einem bestehenden Projekt mit Frontend und Backend.

Projektkontext:
- Anwendungstyp: Datenbank-Tool mit Frontend + Backend
- Backend: Node/TypeScript
- Datenbank: Neo4j ist vorhanden
- KI: Ollama
- Default-Modell: gemma4:31b
- Fokus dieses Arbeitsschritts: ausschließlich Einstellungen
- Bereits definierte Hauptbereiche im Frontend: Import, Suche, Themen, Chat, Einstellungen, Dashboard

Ziel:
Baue den Bereich "Einstellungen" vollständig aus, mit:
1. Theme-Umschaltung zwischen hell und dunkel
2. KI-Konfiguration für Ollama
3. persistenter Speicherung der Einstellungen
4. sauberer Trennung zwischen UI, API, Validierung und Persistenz

Umfang:
A. Frontend
- Erstelle eine Settings-Seite
- Gliedere sie in zwei Sektionen:
  - Anzeige
  - KI-Konfiguration
- Anzeige:
  - Umschalter für light/dark
  - Theme soll sofort sichtbar angewendet werden
- KI-Konfiguration:
  - provider: fest auf "ollama"
  - model: Textfeld, Default "gemma4:31b"
  - endpoint: Textfeld, Default "http://localhost:11434"
  - temperature: Zahl oder Slider, Bereich 0 bis 1
  - maxTokens: Ganzzahl > 0
  - contextWindow: Ganzzahl > 0
- Lade die aktuellen Einstellungen beim Öffnen der Seite
- Speichere Änderungen per API
- Zeige Loading-, Success- und Error-State

B. Backend
- Implementiere API-Endpunkte:
  - GET /api/settings
  - POST /api/settings
- Implementiere Validierung für alle Felder
- Implementiere persistente Speicherung der Settings
- Wenn noch keine Persistenz existiert, nutze zunächst eine lokale JSON-Datei
- Fehlerhafte Eingaben müssen 400 liefern
- interne Fehler müssen 500 liefern

C. Typen und Defaults
Nutze folgendes Zielmodell:

type ThemeMode = "light" | "dark";

type AISettings = {
  provider: "ollama";
  model: string;
  endpoint: string;
  temperature: number;
  maxTokens: number;
  contextWindow: number;
};

type Settings = {
  theme: ThemeMode;
  ai: AISettings;
};

Default-Werte:
- theme: "light"
- provider: "ollama"
- model: "gemma4:31b"
- endpoint: "http://localhost:11434"
- temperature: 0.2
- maxTokens: 512
- contextWindow: 4096

D. Qualitätsanforderungen
- Passe nur die für diesen Bereich nötigen Dateien an
- Halte die Änderungen klein und sauber
- Nutze bestehende Projektstruktur, falls vorhanden
- Schreibe klar lesbaren TypeScript-Code
- Keine unnötigen neuen Abhängigkeiten
- Keine Änderungen an Import, Suche, Themen, Chat oder Dashboard

Arbeitsweise:
1. Analysiere zuerst die bestehende Projektstruktur
2. Identifiziere die minimal nötigen Dateien
3. Implementiere Backend
4. Implementiere Frontend
5. Verbinde Frontend und Backend
6. Prüfe Validierung und Default-Verhalten
7. Führe vorhandene Tests oder Build/Lint aus, falls verfügbar
8. Behebe Fehler selbstständig
9. Dokumentiere am Ende knapp:
   - geänderte Dateien
   - was implementiert wurde
   - offene technische Risiken

Ausgabeformat:
- Zuerst kurzer Plan
- Danach Umsetzung
- Danach Test-/Build-Ergebnis
- Danach kurze Abschlusszusammenfassung
```

## Claude Cowork — Prompt für den Bereich **Einstellungen**

```text
Ziel:
Arbeite in meinem Projektordner und implementiere den Bereich "Einstellungen" als zusammenhängenden Feature-Block.

Kontext:
- Das Projekt ist ein Datenbank-Tool mit Frontend und Backend
- Backend nutzt Neo4j, aber der Settings-Bereich ist zunächst unabhängig von Neo4j
- KI läuft über Ollama
- Default-Modell ist gemma4:31b
- Im Frontend existieren die Bereiche: Import, Suche, Themen, Chat, Einstellungen, Dashboard
- Jetzt wird ausschließlich "Einstellungen" entwickelt

Featureumfang:
1. Theme-Konfiguration
- Umschaltung zwischen hell und dunkel
- Persistenz der Auswahl
- sofortige sichtbare Anwendung im Frontend

2. KI-Konfiguration
- provider = ollama
- model = gemma4:31b als Default
- endpoint = http://localhost:11434 als Default
- temperature = Zahl zwischen 0 und 1
- maxTokens = positive Ganzzahl
- contextWindow = positive Ganzzahl

3. API
- GET /api/settings
- POST /api/settings

4. Persistenz
- Speichere Settings lokal persistent
- Nutze vorhandene Mechanismen, falls im Projekt vorhanden
- Falls nicht vorhanden, nutze eine einfache JSON-basierte Persistenz

Vorgehen:
- Untersuche zuerst die vorhandene Projektstruktur
- Finde die bestehenden Dateien für:
  - Typen
  - API / Routing
  - Services
  - Frontend-Seiten / Komponenten
- Implementiere das Feature mit minimal-invasiven Änderungen
- Bevorzuge bestehende Konventionen gegenüber Neuaufbau
- Halte Dateianzahl und Komplexität niedrig

Wichtige Regeln:
- Keine Arbeit an anderen Bereichen
- Keine großflächigen Refactorings
- Keine neuen Libraries, wenn nicht zwingend nötig
- Keine unnötigen Texte oder Dokumente erzeugen
- Nur implementieren, validieren, knapp berichten

Validierung:
- theme nur light/dark
- provider nur ollama
- endpoint muss gültige URL sein
- temperature nur 0 bis 1
- maxTokens > 0
- contextWindow > 0

Erwartetes Ergebnis:
- Einstellungen im Frontend sichtbar und benutzbar
- Theme schaltbar
- KI-Parameter editierbar und speicherbar
- Backend-Endpunkte funktionsfähig
- Defaults korrekt gesetzt
- Fehlerbehandlung vorhanden

Abschlussbericht:
Liefere nur:
1. geänderte Dateien
2. implementierte Funktionen
3. verbleibende Risiken oder Annahmen
```

## Claude Cowork — Kurzprompt für reine Prüfung nach Codex

```text
Prüfe in diesem Projekt ausschließlich den neu implementierten Bereich "Einstellungen".

Prüfkriterien:
- Funktioniert die Theme-Umschaltung logisch konsistent?
- Sind die KI-Settings vollständig validiert?
- Gibt es Konfigurationsfehler bei Ollama-bezogenen Defaults?
- Gibt es unnötige Komplexität oder doppelte Logik?
- Nenne nur die 7 wichtigsten Probleme

Regeln:
- Keine Neuimplementierung
- Keine großflächigen Umbauten
- Nur konkrete Befunde
- Priorisiere nach Risiko
- Antworte kurz und technisch
```

## Codex — Kurzprompt für Folgeiteration

```text
Überarbeite den bereits implementierten Bereich "Einstellungen" auf Basis der gefundenen Probleme.

Regeln:
- Nur gezielte Korrekturen
- Keine Refactorings außerhalb des Settings-Features
- Erst Probleme priorisieren, dann beheben
- Build/Test ausführen, falls verfügbar
- Abschluss mit Liste der korrigierten Punkte
```

Für die nächsten Bereiche liefere ich dir dann im gleichen Format nur noch:
**Codex-Prompt** und **Claude-Cowork-Prompt**.

### 19. Benutzer

daten für neo4j: # Wait 60 seconds before connecting using these details, or login to https://console.neo4j.io to validate the Aura Instance is available
NEO4J_URI=neo4j+s://bd6c8358.databases.neo4j.io
NEO4J_USERNAME=bd6c8358
NEO4J_PASSWORD=B6MSYAWWeXhzH3cHC7j4F910MLBq1s9o1Eb2GoBF-Rc
NEO4J_DATABASE=bd6c8358
AURA_INSTANCEID=bd6c8358
AURA_INSTANCENAME=Wissen

### 20. Assistent

Kritischer Befund:
Die Zugangsdaten sind **vollständig im Klartext exponiert**. Das erzeugt unmittelbares Risiko:
- unautorisierter Zugriff auf Datenbank
- Datenverlust / Manipulation
- Kosten durch Fremdnutzung
- potenzielle Kompromittierung weiterer Systeme

Implikation:
Diese Credentials dürfen **nicht mehr verwendet werden**. Rotation erforderlich.

---

## Codex — Prompt (Neo4j Integration in Backend, sicher)

```text
Aufgabe:
Integriere Neo4j (Aura) sicher in das bestehende Backend.

WICHTIG:
Die Zugangsdaten dürfen NICHT im Code stehen. Nutze ausschließlich Environment Variablen.

Kontext:
- Backend: Node.js mit TypeScript
- Datenbank: Neo4j Aura
- Verbindung über neo4j-driver

Environment Variablen:
- NEO4J_URI
- NEO4J_USERNAME
- NEO4J_PASSWORD
- NEO4J_DATABASE

Ziel:
1. Erstelle einen Neo4j Service:
   Datei: src/services/neo4j.service.ts

2. Implementiere:
   - Singleton Driver Initialisierung
   - Funktion getSession()
   - Funktion closeDriver()

3. Verbindung:
   - nutze neo4j-driver
   - verschlüsselte Verbindung (neo4j+s)

4. Fehlerhandling:
   - Verbindungsfehler sauber loggen
   - keine Credentials im Log

5. Beispiel-Funktion:
   - testConnection()
   - führt einfache Query aus:
     RETURN 1

6. Integration:
   - exportiere Service
   - keine direkte Nutzung in anderen Modulen erzwingen

7. .env Handling:
   - prüfe, ob alle Variablen vorhanden sind
   - wenn nicht → Prozess abbrechen

8. Sicherheit:
   - KEINE Hardcodierung
   - KEIN Fallback auf Default-Credentials

9. Struktur:
- src/services/neo4j.service.ts
- src/utils/env.ts (optional für Validierung)

Arbeitsweise:
1. Prüfe bestehende Struktur
2. Ergänze minimal notwendige Dateien
3. Implementiere Service
4. Teste Verbindung logisch
5. Kein Refactoring außerhalb dieses Bereichs

Ausgabe:
- vollständiger Code
- Liste der Dateien
```

---

## Claude Cowork — Prompt (Sicherheitsprüfung Neo4j)

```text
Ziel:
Prüfe die Neo4j-Integration im Projekt auf Sicherheits- und Architekturprobleme.

Kontext:
- Neo4j Aura wird über Environment Variablen angebunden
- Verbindung über neo4j-driver
- Fokus auf sicheren Betrieb

Prüfe ausschließlich:
1. Werden Credentials irgendwo im Code oder Logs geleakt?
2. Ist die Verbindung korrekt abgesichert (neo4j+s)?
3. Gibt es Risiken bei Session Handling (Leaks, offene Verbindungen)?
4. Wird der Driver korrekt als Singleton verwendet?
5. Gibt es Fehler bei Environment Validation?
6. Besteht Risiko durch fehlendes Timeout oder Retry-Handling?

Regeln:
- maximal 10 Punkte
- nur konkrete Probleme
- keine Erklärungen
- keine Vorschläge außerhalb der Probleme
```

---

## Codex — Prompt (Absicherung .env + Rotation Vorbereitung)

```text
Aufgabe:
Sichere den Umgang mit sensiblen Zugangsdaten im Projekt.

Ziel:
1. Erstelle eine .env.example Datei
2. Stelle sicher, dass echte Credentials NICHT committed werden
3. Ergänze Schutzmechanismen

Umsetzung:
1. .env.example erstellen mit:
   NEO4J_URI=
   NEO4J_USERNAME=
   NEO4J_PASSWORD=
   NEO4J_DATABASE=

2. .gitignore prüfen/ergänzen:
   - .env
   - data/settings.json (falls sensibel)

3. Optional:
   src/utils/env.ts:
   - zentrale Validierung aller benötigten ENV Variablen
   - Abbruch bei fehlenden Werten

4. Logging:
   - stelle sicher, dass keine ENV Variablen ausgegeben werden

Regeln:
- keine externen Libraries
- minimal-invasive Änderungen
- bestehende Struktur respektieren

Output:
- geänderte Dateien
- kurzer Bericht
```

---

## Claude Cowork — Prompt (Kosten-/Risikoanalyse Neo4j Nutzung)

```text
Kontext:
Neo4j Aura wird als Backend-Datenbank genutzt.

Analysiere:
1. 5 größte Betriebsrisiken bei falscher Nutzung
2. 5 typische Performance-Bottlenecks
3. 3 kritische Designfehler bei Graph-Modellen

Regeln:
- maximal 13 Bullet Points
- keine Einleitung
- keine Wiederholung des Kontexts
- nur technische Risiken
```

---

Systementscheidung:
Neo4j wird jetzt sauber als Backend-Service integriert.  
Settings bleiben unabhängig, greifen später auf KI-Konfiguration zu.  
Import + Suche werden später direkt auf Neo4j aufsetzen.

Nächster sinnvoller Bereich nach Settings:
→ **Import (Daten in Neo4j bringen)**

### 21. Benutzer

ja

### 22. Assistent

## Codex — Prompt für den Bereich **Import**

```text
Aufgabe:
Implementiere den Bereich "Import" in einem bestehenden Projekt mit Frontend, Backend und Neo4j Aura.

Kontext:
- Anwendungstyp: Datenbank-Tool mit Frontend + Backend
- Backend: Node.js + TypeScript
- Datenbank: Neo4j Aura ist angebunden
- KI: Ollama mit gemma4:31b, aber für diesen Schritt nicht zentral
- Bereits definierte Frontend-Bereiche: Import, Suche, Themen, Chat, Einstellungen, Dashboard
- Fokus dieses Arbeitsschritts: ausschließlich Import

Ziel:
Baue den Bereich "Import" vollständig aus, damit strukturierte Daten sicher in Neo4j übernommen werden können.

Funktionsumfang:
1. Frontend
- Erstelle eine Import-Seite
- Bereiche:
  - Datenquelle auswählen
  - Vorschau der Importdaten
  - Mapping / Zielstruktur
  - Import starten
  - Importprotokoll anzeigen

2. Unterstützte Importformate
- JSON
- CSV
- Text als Rohinput optional vorbereiten, aber nur wenn minimal integrierbar
- Priorität: JSON und CSV

3. Backend
- API-Endpunkte:
  - POST /api/import/preview
  - POST /api/import/execute
  - GET /api/import/history optional nur wenn einfach umsetzbar
- Preview soll Daten lesen, validieren und ein Normalformat erzeugen
- Execute soll normalisierte Daten in Neo4j schreiben

4. Normalisierte Zielstruktur
Nutze intern ein einheitliches Importmodell:

type ImportNode = {
  id?: string;
  label: string;
  properties: Record<string, string | number | boolean | null>;
};

type ImportEdge = {
  from: string;
  to: string;
  type: string;
  properties?: Record<string, string | number | boolean | null>;
};

type ImportPayload = {
  nodes: ImportNode[];
  edges: ImportEdge[];
};

5. Datenlogik
- CSV:
  - unterstütze mindestens node-Import
  - Header-basierte Zuordnung
- JSON:
  - akzeptiere direkt ImportPayload
  - validiere Struktur streng
- Preview:
  - Anzahl Nodes
  - Anzahl Edges
  - erkannte Labels
  - offensichtliche Fehler
- Execute:
  - schreibe per MERGE statt CREATE, wenn sinnvoll
  - keine Duplikat-Explosion
  - bei fehlerhaften Datensätzen klar abbrechen oder protokollieren

6. Neo4j-Logik
- Verwende bestehenden Neo4j-Service
- Öffne Sessions sauber
- Keine Credentials loggen
- Transaktion für Import verwenden
- Label und Relationship-Type validieren, um Injection über dynamische Cypher-Fragmente zu verhindern

7. Frontend-UX
- Datei-Upload für CSV/JSON
- Preview vor Import zwingend
- Import-Button erst nach erfolgreicher Preview aktiv
- Ergebnis anzeigen:
  - importierte Nodes
  - importierte Edges
  - Fehlerliste
- Lade- und Error-State

8. Sicherheits- und Validierungsregeln
- Dateigröße begrenzen
- Nur erlaubte MIME-Typen zulassen
- JSON strikt validieren
- CSV auf leere Header und inkonsistente Zeilen prüfen
- Labels und Relationship-Types sanitizen
- Keine direkte Übernahme unvalidierter Werte in Cypher

9. Qualitätsanforderungen
- Nutze bestehende Projektstruktur
- Implementiere nur den Import-Bereich
- Keine Änderungen an Suche, Themen, Chat, Dashboard oder Einstellungen
- Keine unnötigen Libraries
- Minimal-invasive Änderungen
- Sauberer TypeScript-Code

Arbeitsweise:
1. Analysiere zuerst die bestehende Projektstruktur
2. Identifiziere die minimal nötigen Dateien
3. Implementiere Typen und Parser
4. Implementiere Preview-API
5. Implementiere Execute-API
6. Implementiere Frontend-Seite
7. Verbinde Frontend und Backend
8. Prüfe Build/Test, falls verfügbar
9. Behebe Fehler selbstständig

Abschlussbericht:
- geänderte Dateien
- implementierte Funktionen
- offene Risiken
```

---

## Claude Cowork — Prompt für den Bereich **Import**

```text
Ziel:
Implementiere den Bereich "Import" als kompaktes, produktionsnahes Feature in meinem bestehenden Projekt.

Kontext:
- Das Projekt ist ein Datenbank-Tool mit Frontend und Backend
- Backend: Node.js + TypeScript
- Datenbank: Neo4j Aura
- KI ist vorhanden, aber für diesen Schritt nicht relevant
- Frontend-Bereiche: Import, Suche, Themen, Chat, Einstellungen, Dashboard
- Jetzt wird ausschließlich "Import" entwickelt

Featureumfang:
1. Import-Seite im Frontend
- Datei-Upload für JSON und CSV
- Vorschau vor dem eigentlichen Import
- Anzeige von erkannter Struktur und Fehlern
- Import-Start nur nach erfolgreicher Preview

2. Backend-Endpunkte
- POST /api/import/preview
- POST /api/import/execute

3. Datenmodell
- Intern auf ein einheitliches Format normalisieren:
  - nodes
  - edges
- JSON darf direkt dieses Format liefern
- CSV darf mindestens Nodes importieren
- Falls Edges in CSV ohne große Zusatzkomplexität möglich sind, sauber integrieren, sonst weglassen

4. Neo4j-Integration
- bestehenden Neo4j-Service verwenden
- Sessions und Transaktionen sauber handhaben
- MERGE bevorzugen, um Duplikate zu reduzieren
- dynamische Labels/Relationship-Types absichern

5. Validierung
- JSON-Struktur streng validieren
- CSV-Kopfzeilen validieren
- Dateiformat und Dateigröße prüfen
- Labels und Relationship-Types sanitizen
- keine unvalidierten Werte direkt in Cypher einsetzen

6. Frontend-Verhalten
- Datei wählen
- Preview laden
- Zusammenfassung anzeigen:
  - Anzahl Nodes
  - Anzahl Edges
  - Labels
  - Fehler
- Import durchführen
- Ergebnis anzeigen

Regeln:
- Bestehende Struktur bevorzugen
- Minimal-invasive Änderungen
- Keine unnötigen Bibliotheken
- Kein Refactoring außerhalb des Import-Features
- Keine Arbeit an anderen Bereichen

Wichtige technische Prioritäten:
- sichere Neo4j-Schreiblogik
- robuste Validierung
- nachvollziehbare Fehlermeldungen
- kleine, übersichtliche Dateianzahl
- kein Overengineering

Abschlussbericht:
Liefere nur:
1. geänderte Dateien
2. implementierte Funktionen
3. verbleibende Risiken oder Annahmen
```

---

## Claude Cowork — Kurzprompt für Review des Import-Features

```text
Prüfe ausschließlich den neu implementierten Bereich "Import".

Prüfkriterien:
- Ist die Importlogik robust gegen fehlerhafte JSON- und CSV-Daten?
- Gibt es Cypher-Injection-Risiken durch dynamische Labels oder Relationship-Types?
- Ist das Session- und Transaktionshandling sauber?
- Gibt es Risiko für Duplikate oder inkonsistente Graphen?
- Ist die Preview logisch strikt vom Execute getrennt?
- Nenne nur die 8 wichtigsten Probleme

Regeln:
- keine Neuimplementierung
- keine Umbauten
- nur konkrete technische Befunde
- kurz und priorisiert
```

---

## Codex — Kurzprompt für Folgeiteration nach Review

```text
Überarbeite den bereits implementierten Bereich "Import" auf Basis der gefundenen Probleme.

Regeln:
- nur gezielte Korrekturen
- keine Refactorings außerhalb des Import-Features
- priorisiere Sicherheits- und Datenintegritätsprobleme
- prüfe Build/Test, falls verfügbar
- Abschluss mit Liste der korrigierten Punkte
```

### 23. Benutzer

beim import dürfen auch word, txt und pdf dateien gelesen verarbeitet und importiert werden

### 24. Assistent

## Codex — Prompt für den Bereich **Import** mit **JSON, CSV, TXT, PDF, Word**

```text
Aufgabe:
Implementiere den Bereich "Import" in einem bestehenden Projekt mit Frontend, Backend und Neo4j Aura.

Kontext:
- Anwendungstyp: Datenbank-Tool mit Frontend + Backend
- Backend: Node.js + TypeScript
- Datenbank: Neo4j Aura ist angebunden
- KI: Ollama mit gemma4:31b
- Bereits definierte Frontend-Bereiche: Import, Suche, Themen, Chat, Einstellungen, Dashboard
- Fokus dieses Arbeitsschritts: ausschließlich Import

Ziel:
Baue den Bereich "Import" vollständig aus, damit strukturierte und unstrukturierte Daten sicher gelesen, verarbeitet und in Neo4j übernommen werden können.

Unterstützte Importquellen:
- JSON
- CSV
- TXT
- PDF
- Word-Dateien: .docx
- .doc nur optional vorbereiten, aber nicht priorisieren

Funktionsumfang:
1. Frontend
- Erstelle eine Import-Seite
- Bereiche:
  - Datei auswählen
  - Dateityp anzeigen
  - Vorschau der extrahierten Inhalte
  - Mapping / Zielstruktur
  - Import starten
  - Importprotokoll anzeigen

2. Backend-Endpunkte
- POST /api/import/preview
- POST /api/import/execute

3. Verarbeitungslogik nach Dateityp
A. JSON
- akzeptiere direkt ein ImportPayload-Format
- validiere Struktur streng

B. CSV
- unterstütze mindestens Node-Import über Header
- optional Edge-Import nur wenn ohne hohe Zusatzkomplexität machbar

C. TXT
- lese Datei als Text
- zerlege Inhalt in importierbare Einheiten
- erzeuge daraus normalisierte Datensätze

D. PDF
- extrahiere Textinhalt
- bereinige Leerzeilen, Trennzeichen, Artefakte
- führe den extrahierten Text in die gleiche Verarbeitungsstrecke wie TXT

E. DOCX
- extrahiere Textinhalt
- behandle extrahierten Text wie TXT

4. Normalisierte Zielstruktur
Nutze intern ein einheitliches Importmodell:

type ImportNode = {
  id?: string;
  label: string;
  properties: Record<string, string | number | boolean | null>;
};

type ImportEdge = {
  from: string;
  to: string;
  type: string;
  properties?: Record<string, string | number | boolean | null>;
};

type ImportPayload = {
  nodes: ImportNode[];
  edges: ImportEdge[];
};

5. Unstrukturierte Dokumente verarbeiten
Für TXT, PDF und DOCX:
- extrahiere Rohtext
- bilde daraus eine importierbare Struktur
- minimaler robuster Ansatz:
  - pro Dokument ein Document-Node
  - optional pro Abschnitt / Absatz Chunk-Nodes
  - Relationship:
    - (:Document)-[:HAS_CHUNK]->(:Chunk)
- speichere Metadaten:
  - filename
  - sourceType
  - importedAt
  - textLength
  - optional sectionIndex / chunkIndex
- falls vorhanden, nutze KI optional nur für spätere Erweiterung
- in diesem Schritt keine komplexe KI-Extraktion erzwingen

6. Preview
- zeige:
  - Dateityp
  - erkannte Struktur
  - Anzahl geplanter Nodes
  - Anzahl geplanter Edges
  - erkannte Labels
  - Fehler und Warnungen
  - bei Dokumenten zusätzlich Textauszug

7. Execute
- schreibe normalisierte Daten in Neo4j
- verwende Transaktionen
- nutze MERGE, wo sinnvoll
- vermeide Duplikat-Explosion
- bei Dokumentimport:
  - Document anhand stabiler ID oder Hash wiedererkennbar machen
  - Chunks sauber referenzieren

8. Neo4j-Logik
- verwende bestehenden Neo4j-Service
- Sessions sauber öffnen/schließen
- keine Credentials loggen
- Labels und Relationship-Types validieren, um Injection über dynamische Cypher-Fragmente zu verhindern

9. Sicherheits- und Validierungsregeln
- Dateigröße begrenzen
- nur erlaubte Dateitypen zulassen
- MIME-Typ und Dateiendung prüfen
- PDF-/DOCX-Parser-Fehler sauber behandeln
- keine unvalidierten dynamischen Cypher-Fragmente
- Textlänge pro Chunk begrenzen
- Chunking deterministisch halten
- leere oder nahezu leere Dokumente abfangen

10. Frontend-UX
- Datei-Upload für JSON, CSV, TXT, PDF, DOCX
- Preview vor Import zwingend
- Import-Button erst nach erfolgreicher Preview aktiv
- Ergebnis anzeigen:
  - importierte Nodes
  - importierte Edges
  - Warnungen
  - Fehlerliste
- Loading- und Error-State

11. Qualitätsanforderungen
- nutze bestehende Projektstruktur
- implementiere nur den Import-Bereich
- keine Änderungen an Suche, Themen, Chat, Dashboard oder Einstellungen
- keine unnötigen Libraries
- falls Parser-Libraries für PDF oder DOCX nötig sind, nutze möglichst etablierte, kleine Libraries
- sauberer TypeScript-Code
- minimal-invasive Änderungen

12. Implementierungsstrategie
- JSON und CSV direkt in ImportPayload normalisieren
- TXT, PDF und DOCX zunächst als dokumentzentrierte Graphstruktur importieren
- keine KI-basierte semantische Extraktion in diesem Schritt
- Architektur so anlegen, dass spätere KI-Anreicherung möglich ist

Arbeitsweise:
1. Analysiere zuerst die bestehende Projektstruktur
2. Identifiziere die minimal nötigen Dateien
3. Implementiere Parser / Extractor je Dateityp
4. Implementiere Preview-API
5. Implementiere Execute-API
6. Implementiere Frontend-Seite
7. Verbinde Frontend und Backend
8. Prüfe Build/Test, falls verfügbar
9. Behebe Fehler selbstständig

Abschlussbericht:
- geänderte Dateien
- implementierte Funktionen
- eingesetzte Zusatzbibliotheken
- offene Risiken
```

---

## Claude Cowork — Prompt für den Bereich **Import** mit **JSON, CSV, TXT, PDF, Word**

```text
Ziel:
Implementiere den Bereich "Import" als kompaktes, robustes Feature in meinem bestehenden Projekt.

Kontext:
- Das Projekt ist ein Datenbank-Tool mit Frontend und Backend
- Backend: Node.js + TypeScript
- Datenbank: Neo4j Aura
- KI ist vorhanden, aber in diesem Schritt nicht der Hauptmechanismus
- Frontend-Bereiche: Import, Suche, Themen, Chat, Einstellungen, Dashboard
- Jetzt wird ausschließlich "Import" entwickelt

Unterstützte Dateitypen:
- JSON
- CSV
- TXT
- PDF
- DOCX

Featureumfang:
1. Import-Seite im Frontend
- Datei-Upload
- Dateityp-Erkennung
- Preview vor eigentlichem Import
- Anzeige von erkannter Struktur, Textauszug, Warnungen und Fehlern
- Import-Start nur nach erfolgreicher Preview

2. Backend-Endpunkte
- POST /api/import/preview
- POST /api/import/execute

3. Verarbeitungslogik
A. JSON
- direktes ImportPayload unterstützen
- streng validieren

B. CSV
- mindestens Nodes über Header importieren
- Edges nur wenn ohne hohe Zusatzkomplexität sauber integrierbar

C. TXT / PDF / DOCX
- Text extrahieren
- Inhalt in eine einfache, stabile Graphstruktur überführen
- pragmatischer Zielgraph:
  - Document-Node
  - optionale Chunk-Nodes für Abschnitte oder Teilstücke
  - HAS_CHUNK-Beziehungen
- Metadaten speichern:
  - filename
  - sourceType
  - importedAt
  - textLength
  - chunkIndex falls genutzt

4. Neo4j-Integration
- bestehenden Neo4j-Service verwenden
- Sessions und Transaktionen sauber handhaben
- MERGE bevorzugen, um Duplikate zu reduzieren
- dynamische Labels/Relationship-Types absichern

5. Validierung und Sicherheit
- Dateigröße begrenzen
- Dateityp über MIME und Endung prüfen
- leere oder unlesbare Dokumente abfangen
- PDF-/DOCX-Extraktionsfehler sauber behandeln
- Labels und Relationship-Types sanitizen
- keine unvalidierten Werte direkt in Cypher einsetzen
- Text-Chunks größenbegrenzt und deterministisch erzeugen

6. Technische Prioritäten
- robuste Text-Extraktion
- einfache, nachvollziehbare Graphabbildung
- keine KI-Pflicht für Import
- Architektur für spätere KI-Anreicherung offen halten
- kleine, übersichtliche Dateianzahl
- keine unnötigen Bibliotheken

Regeln:
- bestehende Struktur bevorzugen
- minimal-invasive Änderungen
- kein Refactoring außerhalb des Import-Features
- keine Arbeit an anderen Bereichen
- nur implementieren, validieren, knapp berichten

Abschlussbericht:
Liefere nur:
1. geänderte Dateien
2. implementierte Funktionen
3. eingesetzte Zusatzbibliotheken
4. verbleibende Risiken oder Annahmen
```

---

## Claude Cowork — Kurzprompt für Review des erweiterten Import-Features

```text
Prüfe ausschließlich den neu implementierten Bereich "Import".

Prüfkriterien:
- Ist die Importlogik robust für JSON, CSV, TXT, PDF und DOCX?
- Gibt es Parser-Risiken oder Fehlerfälle bei PDF- und DOCX-Extraktion?
- Gibt es Cypher-Injection-Risiken durch dynamische Labels oder Relationship-Types?
- Ist das Session- und Transaktionshandling sauber?
- Gibt es Risiko für Duplikate oder inkonsistente Graphen?
- Ist die Preview logisch strikt vom Execute getrennt?
- Ist die Dokument-zu-Graph-Abbildung einfach und stabil?
- Nenne nur die 10 wichtigsten Probleme

Regeln:
- keine Neuimplementierung
- keine Umbauten
- nur konkrete technische Befunde
- kurz und priorisiert
```

---

## Codex — Kurzprompt für Folgeiteration nach Review

```text
Überarbeite den bereits implementierten Bereich "Import" auf Basis der gefundenen Probleme.

Regeln:
- nur gezielte Korrekturen
- keine Refactorings außerhalb des Import-Features
- priorisiere Sicherheits-, Parser- und Datenintegritätsprobleme
- prüfe Build/Test, falls verfügbar
- Abschluss mit Liste der korrigierten Punkte
```

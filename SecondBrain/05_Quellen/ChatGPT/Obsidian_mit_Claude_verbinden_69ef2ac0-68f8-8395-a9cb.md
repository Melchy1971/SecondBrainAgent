---
title: "Obsidian mit Claude verbinden"
type: chatgpt_conversation
source: chatgpt
source_id: "69ef2ac0-68f8-8395-a9cb-ba8af80c74e1"
created: 2026-04-27
tags:
  - chatgpt
  - code
  - import
  - ki
  - obsidian
  - sap
---


# Obsidian mit Claude verbinden

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69ef2ac0-68f8-8395-a9cb-ba8af80c74e1`
- Nachrichten: 5

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich habe obsidian mitbrat plugin und möchte dies nun mit claude verknüpfen. Wie?

### 2. Assistent

Kurzfassung: Direkt geht es nicht. Das entity["software","BRAT plugin Obsidian","Beta Reviewer's Auto-update Tool"] verwaltet Plugins aus GitHub. entity["software","Claude","Anthropic AI assistant"] hat keine native Obsidian-Integration. Verbindung entsteht nur indirekt über ein kompatibles Plugin oder API-Bridge.

---

## Architektur-Realität

**Systemgrenzen:**
- Obsidian Plugins laufen lokal (TypeScript/JS).
- BRAT installiert Plugins aus GitHub-Repos.
- Claude ist ein externer API-Dienst (Anthropic API).
- Keine offizielle „Claude ↔ Obsidian“-Schnittstelle.

---

## Option 1: Community-Plugin mit Claude-Support

Ziel: Plugin nutzen, das bereits Anthropic integriert.

**Beispielklasse:**
- AI-Plugins für Obsidian (z. B. „Text Generator“, „AI Assistant“-Forks)

**Vorgehen:**
1. Plugin-Repo finden (mit Claude/Anthropic Support).
2. GitHub-URL kopieren.
3. In BRAT hinzufügen:
   - Settings → BRAT → „Add Beta Plugin“
   - Repo einfügen
4. Plugin aktivieren.
5. API-Key von Anthropic eintragen.

**Constraint:**
- Viele Plugins unterstützen primär OpenAI, Claude oft nur in Forks.
- Qualität variiert stark.

---

## Option 2: Eigenes Plugin (robusteste Lösung)

**Systemdesign:**
- Obsidian Plugin → HTTP Client → Anthropic API

**Minimalfluss:**
1. API-Key bei Anthropic erzeugen.
2. Plugin scaffolden (`obsidian-sample-plugin`).
3. Request an Claude API:

```ts
const response = await fetch("https://api.anthropic.com/v1/messages", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "x-api-key": YOUR_API_KEY,
    "anthropic-version": "2023-06-01"
  },
  body: JSON.stringify({
    model: "claude-3-opus-20240229",
    max_tokens: 1024,
    messages: [{ role: "user", content: "Dein Prompt" }]
  })
});
```

4. Response in Obsidian UI rendern.

**Vorteile:**
- volle Kontrolle (Prompts, Kontext, Vault-Zugriff)
- keine Drittanbieter-Abhängigkeit

**Risiken:**
- Rate Limits
- Kosten pro Token
- API-Änderungen

---

## Option 3: Lokale Bridge (Low Coupling)

**Architektur:**
Obsidian → Local Script (Node/Python) → Claude API

**Mechanik:**
- Obsidian Plugin ruft lokalen Endpoint auf (z. B. `localhost:3000`)
- Script übernimmt Auth + API Calls

**Vorteil:**
- API-Key nicht im Plugin
- flexiblere Orchestrierung (z. B. Retrieval, Caching)

---

## Option 4: Indirekt über Tools

Kein echter „Connect“, sondern Workflow:

- Markdown → Copy → Claude UI
- oder CLI-Tools (z. B. wrappers um Claude API)

Niedriger Integrationsgrad, aber stabil.

---

## Entscheidungslogik

| Option | Setup-Aufwand | Kontrolle | Stabilität | Skalierbarkeit |
|------|-------------|----------|-----------|--------------|
| Community Plugin | niedrig | gering | mittel | gering |
| Eigenes Plugin | hoch | maximal | hoch | hoch |
| Lokale Bridge | mittel | hoch | hoch | hoch |
| Manuell | minimal | none | hoch | none |

---

## Hidden Constraints

- Obsidian sandbox → kein direkter Zugriff auf systemweite Dienste ohne Plugin-Code
- Claude API erfordert aktiven Billing-Account
- Tokenkosten steigen stark bei großen Vault-Kontexten
- Kontextfenster ≠ kompletter Vault → Chunking notwendig

---

## Typischer Fehler

- Erwartung: „BRAT verbindet Tools“
- Realität: BRAT ist nur ein Installer, kein Integrationslayer

---

## Fazit

Integration = Plugin oder Middleware.  
BRAT = nur Verteilung.

### 3. Benutzer

option 1 schritt für schritt anleitung

### 4. Assistent

Ich prüfe kurz die aktuelle Lage, weil Obsidian-Plugins und Claude-Modellnamen sich häufig ändern. Danach bekommst du eine belastbare Schrittfolge ohne unnötige Abzweige.

### 5. Assistent

## Zielbild

**Obsidian + BRAT → Text Generator Plugin → Anthropic API → Claude**

Text Generator unterstützt Anthropic/Claude laut GitHub. BRAT kann die Beta-Version direkt aus dem GitHub-Repo installieren. citeturn967470search0turn967470search1

## Schritt-für-Schritt

### 1. Anthropic API-Key erstellen

1. Öffne die Anthropic Console.
2. Erstelle einen API-Key.
3. Kopiere den Key.
4. Speichere ihn nicht in einer normalen Obsidian-Notiz.

### 2. BRAT öffnen

In Obsidian:

1. `Settings`
2. `Community plugins`
3. BRAT muss aktiviert sein.
4. Öffne `BRAT` in den Plugin-Einstellungen.

### 3. Text Generator per BRAT installieren

1. In Obsidian Command Palette öffnen:  
   `Ctrl + P`
2. Befehl ausführen:  
   `BRAT: Add a beta plugin for testing`
3. Diese GitHub-URL einfügen:

```text
https://github.com/nhaouari/obsidian-textgenerator-plugin
```

4. Bestätigen.
5. Danach ausführen:  
   `BRAT: Check for updates to all beta plugins`

### 4. Plugin aktivieren

1. `Settings`
2. `Community plugins`
3. `Installed plugins`
4. `Text Generator` aktivieren

### 5. Claude / Anthropic konfigurieren

1. `Settings`
2. `Text Generator`
3. Provider auswählen:
   - `Anthropic`
   - oder `Chat Anthropic`
4. API-Key einfügen.
5. Modell wählen, z. B.:
   - `claude-3-5-sonnet-latest`
   - falls vorhanden: neueres Claude-Modell aus der Plugin-Auswahl

### 6. Testlauf

Neue Notiz erstellen:

```text
Schreibe eine kurze Zusammenfassung zu Prozessdesign in 5 Bulletpoints.
```

Dann:

1. Text markieren
2. Command Palette öffnen
3. Befehl suchen:
   - `Text Generator`
   - `Generate Text`
   - oder ähnlich benannter Plugin-Befehl
4. Ausführen

## Fehlerdiagnose

| Problem | Ursache | Lösung |
|---|---|---|
| Plugin erscheint nicht | BRAT hat nicht installiert | BRAT Update ausführen |
| Kein Claude-Modell sichtbar | falscher Provider | Anthropic/Chat Anthropic wählen |
| 401 Error | API-Key falsch | neuen Key erzeugen |
| 429 Error | Rate Limit/Kontingent | später testen oder Billing prüfen |
| Keine Antwort | Modellname inkompatibel | anderes Claude-Modell wählen |

## Wichtige Einschränkung

Das Plugin sendet ausgewählten oder kontextbezogenen Notizinhalt an Anthropic. Keine sensiblen Notizen ungeprüft verwenden.

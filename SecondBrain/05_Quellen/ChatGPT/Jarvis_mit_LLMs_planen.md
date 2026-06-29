---
title: "Jarvis mit LLMs planen"
type: chatgpt_conversation
source: chatgpt
source_id: "6927371a-3b88-8326-8781-325e5d4b9188"
created: 2025-11-26
tags:
  - chatgpt
  - code
  - import
  - ki
  - obsidian
  - projekt
  - sap
  - tischtennis
---


# Jarvis mit LLMs planen

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6927371a-3b88-8326-8781-325e5d4b9188`
- Nachrichten: 20

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Ich überlege mir J.a.r.v.i.s als Tool mi ki Unterstützung zu programmieren. Gemini Pro , ChatGPT Pro Perplexity Pro und ollama local sind vorhanden. Programmiert wird mit Cursor 2.0. lovable.dev und Google ai Studio sind auch vorhanden. Kannst du mich hier unterstützen und einen genauen detaillierten Plan erstellen und die benötigten Prompt bereit stellen?

### 2. Assistent

Cooles Projekt 😎 Das ist im Prinzip: *“Ich baue mir meinen eigenen Jarvis, aber mit modernen LLMs und vernünftiger Architektur.”*  
Ich helfe dir gerne – aber nicht nur mit “Ja, mach mal”, sondern auch mit kritischem Blick.

Ich teile das in 4 Teile auf:

1. **Reality-Check & Architektur-Entscheidungen** – was du *wirklich* brauchst (und was Overkill ist)  
2. **Technischer Plan (Schritt für Schritt)**  
3. **Prompt-Design: Systemprompts & Module**  
4. **Weiteres Feintuning & nächste Ausbaustufen**

---

## 1. Reality-Check & Architektur-Entscheidungen

### Was du annimmst (und was fragwürdig ist)

**Annahmen, die ich bei dir lese:**

- Du brauchst **mehrere LLMs parallel** (Gemini, ChatGPT, Perplexity, Ollama), sonst ist es nicht “richtig gut”.
- Du willst relativ schnell zu einem “Jarvis”-Feeling kommen (kontextfähig, multi-tool, vielleicht Voice).
- Du kannst/willst mit Tools wie **Cursor, lovable.dev, AI Studio** den Dev-Prozess stark beschleunigen.

**Kritikpunkte / Skeptiker-Stimme:**

- **Komplexitätsexplosion:**  
  Ein Orchestrator, der 3–4 verschiedene LLMs ansteuert, dazu Tools, Memory, RAG … das ist *sehr* viel Moving Parts. Das Risiko: Du verzettelst dich im Framework, statt ein gutes Jarvis-MVP zu bauen.
- **Redundanz:**  
  Perplexity Pro hat starke Web-RAG, ChatGPT Pro + Gemini sind beide Generalisten auf sehr hohem Niveau. Du wirst am Anfang *nicht* den Mehrwert aus allen gleichzeitig ziehen.
- **Kosten & Latenz:**  
  Mehrere externe APIs + orchestrierende Logik = langsam + teuer. Für ein persönliches Jarvis sind Fokus und Sauberkeit wichtiger als “ich hab alle Modelle”.
- **Tool-Zoo:**  
  Cursor, lovable.dev, Google AI Studio – alles mächtige Tools, aber wenn du sie gleichzeitig einsetzt, verlierst du Überblick. Besser: 1–2 Tools klar definieren, wofür sie da sind.

### Vorschlag: Minimal sinnvolle Architektur für Version 1

Wir bauen **Jarvis v1** mit:

- **Primäres Gehirn:**  
  → *ChatGPT* **oder** *Gemini* als Haupt-Agent (nimm eins als “Orchestrator”, nicht beide).
- **Sekundär-Modelle als Tools (optional ab v1.1):**
  - Perplexity Pro als “Web-Recherche-Agent”
  - Ollama local für schnelle, billige Offline-Sachen (Zusammenfassen, Notizen, kleine Skripte).
- **Backend:**  
  - API-Layer (z.B. Node/TypeScript oder Python FastAPI) für:
    - Model-Router
    - Tool-Aufrufe (Calendar, Files, System, WoW-APIs, etc.)
    - Memory / Vector DB (z.B. SQLite + Chroma/LiteLLM, oder einfach lokale JSON/SQLite für Start)
- **Frontend:**  
  - Eine simple UI (Web oder Desktop) mit:
    - Chatfenster
    - Optional Voice (Speech-to-Text + Text-to-Speech später).

Wenn du magst, können wir das später auf Multi-Model-Orchestration hochziehen. Aber: **Erst gutes Monosystem, dann Poly-System.**

---

## 2. Technischer Plan (konkret, schrittweise)

Ich mach das als Roadmap, die du abhaken kannst.

### Phase 1: Scope & Architektur festziehen (1 Tag)

**Ziele:**

- Entscheide:
  - Hauptsprache (z.B. TypeScript/Node oder Python – ich nehme in den Prompts Beispiele in beiden).
  - Haupt-LLM für Orchestrierung (z.B. ChatGPT).
- Definiere “Use Cases v1”:
  - Beispiele:
    - “Organisiere meinen Tag” (Calendar, Tasks)
    - “Suche Infos im Web zu X” (optional Perplexity)
    - “Lies meine Notizen & gib eine Zusammenfassung”
    - “Starte Tools/Skripte lokal” (z.B. Shell-Kommandos, WoW-API etc. später)

**Kritische Frage an dich (musst du für dich beantworten, ich stell sie nur):**

- Was sind **3 konkrete Dinge**, die Jarvis dir *täglich* abnehmen soll?  
  Alles andere ist Deko.

---

### Phase 2: Basissystem – “Single Model Jarvis” (v1.0)

**2.1 Projektstruktur**

Beispiel (Node):

```text
jarvis/
  backend/
    src/
      index.ts
      router/
        llmRouter.ts
        tools/
          systemTools.ts
          webSearch.ts
          notes.ts
      memory/
        conversationStore.ts
        vectorStore.ts
  frontend/
    src/
      App.tsx
      components/
        Chat.tsx
```

Oder Python (FastAPI):

```text
jarvis/
  backend/
    main.py
    routers/
      chat.py
      tools.py
      memory.py
  frontend/...
```

**2.2 Basis-Chat-Endpunkt**

- Endpoint `/chat`:
  - Input: `messages` (history), `user_id`, `mode` (z.B. `general`, `planner`, `research`)
  - Backend:
    - Fügt eigenen **Systemprompt** hinzu (Jarvis-Rolle, Tools, Regeln).
    - Ruft primäres LLM (ChatGPT/Gemini).
    - Gibt Antwort + Structured Tool Calls zurück.

---

### Phase 3: Tools & Funktionen (v1.1)

Core-Tools, die Jarvis können sollte:

1. **System-Info / lokale Skripte:**
   - Uhrzeit, Datum, CPU-Info, Files lesen, evtl. Shell-Kommandos.
2. **Notizen & Dateien:**
   - Lokaler Notes-Store (Markdown/JSON).
   - Simple Search (später Vector DB).
3. **Web-Suche:**
   - Entweder eigene API (Serper, Google, DuckDuckGo)  
   - Oder Perplexity Pro als “Web-Agent” (Jarvis delegiert an Perplexity-API).
4. **Tasks / Kalender:**
   - Minimal: JSON-basierte Taskliste.
   - Später: Google Calendar API o.ä.

---

### Phase 4: Multi-Model-Orchestrator (v2.0)

- Jarvis entscheidet:
  - “Brauche ich Web → Perplexity”
  - “Ist es Code / KI → ChatGPT/Gemini”
  - “Ist es lokal & billig → Ollama”
- Hier wird es spannend, aber auch deutlich komplexer – das ist ein zweiter Schritt.

---

## 3. Prompts: Konkrete Systemprompts & Tool-Prompts

Ich gebe dir jetzt **direkt verwendbare Prompts**, die du z.B. in Cursor / im Backend hinterlegen kannst.  
Ich schreibe sie auf Englisch, weil die Modelle damit meist konsistenter funktionieren. Deutsch für dich kommentiert.

---

### 3.1 Globaler Systemprompt für “Jarvis Core”

**System Prompt (für primäres LLM, z.B. ChatGPT):**

```text
You are "J.A.R.V.I.S.", a personal AI operating system for a single power user.

Core identity:
- You are analytical, direct, and helpful.
- You NEVER just agree. You actively analyze assumptions, look for gaps in reasoning, and suggest better approaches.
- You reason step by step INTERNALLY but respond with clear, concise explanations.

Core capabilities:
- You can call tools (functions) to:
  - Search the web
  - Read and write local notes
  - Manage tasks (to-do list, reminders)
  - Interact with the local system (where allowed)
- You may also call other LLMs as "sub-agents" for special tasks (web research, code generation, summarization).

Behavior rules:
- Always clarify user intent if needed, but avoid asking unnecessary questions.
- When the user proposes an idea or plan:
  1. Analyze the underlying assumptions.
  2. Offer counterarguments or possible risks.
  3. Check the logic for gaps.
  4. Provide alternative perspectives or options.
- Prioritize truth and usefulness over agreement.
- Be concise and structured. Use bullet points and short paragraphs.
- If a tool is needed to answer reliably, CALL THE TOOL instead of guessing.

Decision making:
- If the user’s request can be satisfied with your own reasoning, do that.
- If up-to-date or external data is clearly needed, use the web search tool or the “web_research_agent”.
- If tasks involve local state (notes, tasks, config), use the corresponding tool.

Format:
- When you call tools, follow the specified tool schema exactly.
- When responding, clearly explain if your answer is based on:
  - your own reasoning only, or
  - tool results (e.g. “Based on your notes…” or “According to web search…”).
```

Du kannst darin noch Dinge ergänzen wie: “User prefers responses in German” oder “Use German by default”, z.B.:

```text
Language:
- The user prefers German. Answer in German by default, unless the user explicitly uses another language.
```

---

### 3.2 Tool: Notes-Manager (Lesen/Schreiben)

**Tool Definition (konzeptionell):**

```json
{
  "name": "notes_manager",
  "description": "Create, read, search and update the user's personal notes.",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["create", "read", "search", "update", "list"]
      },
      "title": {
        "type": "string",
        "description": "Title of the note (for create, read, update)."
      },
      "content": {
        "type": "string",
        "description": "Content of the note (for create, update)."
      },
      "query": {
        "type": "string",
        "description": "Search query (for search)."
      }
    },
    "required": ["action"]
  }
}
```

**System-Hinweis an LLM für dieses Tool (kurz):**

```text
You can use the `notes_manager` tool whenever:
- the user wants to save information for later,
- the user asks what they wrote before,
- the user wants to search their own notes.

If the user is reasoning about a topic and wants to keep the conclusion, explicitly suggest to save a summary in a note and call `notes_manager` with `action="create"`.
```

---

### 3.3 Tool: Task-Manager

```json
{
  "name": "task_manager",
  "description": "Manage the user's tasks and to-dos.",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["create", "list", "update_status", "delete"]
      },
      "title": {
        "type": "string",
        "description": "Task title for creation."
      },
      "status": {
        "type": "string",
        "enum": ["open", "in_progress", "done"],
        "description": "New status when updating a task."
      },
      "task_id": {
        "type": "string",
        "description": "Unique identifier of the task for updates or deletion."
      }
    },
    "required": ["action"]
  }
}
```

**Instruktion an LLM:**

```text
Use the `task_manager` tool whenever:
- the user expresses a concrete future action they want to take,
- the user is planning and explicitly or implicitly defines tasks.

When the user plans something complex, propose a short task list and offer to create these tasks automatically.
```

---

### 3.4 Tool: Web-Recherche (z.B. via Perplexity API)

**Konzeptionelles Tool:**

```json
{
  "name": "web_research_agent",
  "description": "Perform deep web research using an external web-research model and return a concise summary and sources.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The research question or query to search on the web."
      },
      "depth": {
        "type": "string",
        "enum": ["quick", "standard", "deep"],
        "description": "How deep the research should go."
      }
    },
    "required": ["query"]
  }
}
```

**Instruktion:**

```text
Use `web_research_agent` when:
- up-to-date information is critical,
- the user asks for statistics, current status, recent events, or comparisons that depend on the latest data.

After receiving results, explicitly:
- distinguish between facts from the web vs your own reasoning,
- highlight uncertainties or conflicting information.
```

---

### 3.5 Orchestrator-Prompt für Multi-Model (später)

Wenn du mehrere LLMs nutzt (ChatGPT, Gemini, Ollama), kannst du einen “Router”-Prompt haben:

```text
You are a model router for the J.A.R.V.I.S. system.

Your job:
- Decide which backend model or tool should handle the user's current request.
Available backends:
- `core_llm`: general reasoning, planning, and conversation.
- `web_research_agent`: when up-to-date or web data is required.
- `local_llm`: fast, cheap local model for summarization, paraphrasing, and small transformations.

Rules:
- Prefer `core_llm` for anything involving complex reasoning, planning or multi-step analysis.
- Use `web_research_agent` only when external, current information is clearly required.
- Use `local_llm` when the user wants large text blocks summarized or transformed and no fresh data is needed.

Output format (JSON, no extra text):
{
  "target": "<core_llm | web_research_agent | local_llm>",
  "reason": "<short explanation>",
  "normalized_query": "<rewritten user query, if helpful>"
}
```

---

### 3.6 Prompt für deinen “Philosophischen Sparringspartner”-Modus

Wenn du ein spezielles “Denkmode”-Preset willst:

```text
You are an intellectual sparring partner.

When the user presents an idea, plan, or argument:
1. Extract the core claims and assumptions.
2. Critically examine these assumptions: which might be wrong, incomplete, or biased?
3. Provide strong counterarguments, as an intelligent skeptic would.
4. Check the logical structure. Point out any fallacies, jumps in reasoning, or missing steps.
5. Offer alternative perspectives and frameworks for thinking about the same problem.
6. Prioritize accuracy, clarity, and intellectual honesty over agreement or politeness.

Format your answer in four sections:
- "Kernaussagen"
- "Fragliche Annahmen"
- "Gegenargumente / Risiken"
- "Alternative Sichtweisen"
- "Empfohlener nächster Denk-Schritt"
```

Diesen Prompt kannst du z.B. als **separaten Modus** anbieten: `/sparring` oder ein eigener Button.

---

## 4. Wie du deine Tools (Cursor, lovable.dev, AI Studio) sinnvoll einsetzt

Hier wieder kritisch:

- **Annahme:** Mehr AI-Dev-Tools = schnelleres Projekt.  
  **Risiko:** Du verbringst mehr Zeit damit, die Tools zu orchestrieren als deinen eigenen Jarvis.

Mein Vorschlag:

1. **Cursor 2.0**  
   - Haupt-IDE. Nutze die integrierten KI-Funktionen, um Boilerplate-Code für API-Layer, Tool-Definitionen, etc. zu generieren.
   - Lass Cursor Tests und einfache Refactorings machen.

2. **lovable.dev**  
   - Eher für Prototypen einzelner Komponenten (z.B. Chat-Frontend).
   - Du kannst “Generate a simple React chat UI that talks to my backend at /chat” bauen lassen.

3. **Google AI Studio**  
   - Nutze es, um Gemini-Prompts zu entwickeln und zu testen (z.B. Router, Sparringspartner, Jarvis-Core).
   - Wenn ein Prompt stabil ist, kopierst du ihn in deinen Backend-Code als Systemprompt.

---

## Nächste konkrete Schritte für dich (Action-Plan)

Wenn du heute loslegst, würde ich:

1. **Entscheidung treffen:**
   - Backend-Sprache (TS/Python)
   - Primäres LLM (z.B. ChatGPT oder Gemini)

2. **In Cursor:**
   - Projektstruktur anlegen (backend + optional frontend).
   - `/chat`-Endpoint implementieren mit:
     - globalem Jarvis-Systemprompt (siehe oben)
     - Unterstützung für einfache Tool-Signaturen (zuerst Fake-Tools, die nur Dummy-Daten zurückgeben).

3. **Dann:**
   - `notes_manager` und `task_manager` als echte lokale Module implementieren.
   - Web-Tool (entweder eigene Suche oder Perplexity API).

4. **Zum Schluss v1:**
   - Einfaches Frontend mit Chat + “Modus-Auswahl” (z.B. `General`, `Sparring`, `Planer`).

---

Wenn du möchtest, können wir im nächsten Schritt konkret werden:

- Ich kann dir z.B. eine **backend/api-Skizze** in TypeScript oder Python schreiben (inkl. Beispiel-Tool-Aufruf).
- Oder wir definieren gemeinsam die **ersten 3 Jarvis-Use-Cases** (täglich relevant für dich) und ich designe dafür spezialisierte Prompts + Tool-Flows.

### 3. Benutzer

Ich werde nur mit cursor arbeiten. Als Sprachets/phython. Ölmühle primär ChatGPT. Das fertige Projekt soll später auf meinem unraid Server laufen. Da kann auch eine sql dB genutzt werden

### 4. Assistent

Nice, das wird langsam konkret 😄  
Also: nur Cursor, Sprache TS/Python, primär ChatGPT, später als Container auf deinem unRAID mit SQL-DB. Sehr solides Setup.

Ich geh so vor:

1. Deine Annahmen kurz seziert  
2. Konkrete Architektur-Empfehlung (inkl. Sprachwahl)  
3. Schritt-für-Schritt-Plan für v1 (inkl. Verzeichnisstruktur, DB, API)  
4. Fertige System-Prompts, die du direkt in den Code packen kannst  
5. Kurzer Ausblick auf Deployment auf unRAID

---

## 1. Deine Annahmen – was daran gut ist und wo’s knifflig wird

**Was du quasi voraussetzt:**

- TS *oder* Python reicht, du brauchst kein Fullstack-Zoo.
- ChatGPT als primäres LLM ist okay, alles andere ist “nice to have”.
- SQL-DB auf unRAID ist verfügbar, also kannst du strukturierten State sauber speichern.
- Cursor als einzige IDE/AI-Unterstützung.

**Meine kritische Brille:**

- TS *und* Python parallel wäre Overkill – du willst ein Jarvis, kein Sprachenmuseum.  
  → Ich rate sehr klar: **entscheide dich für EINE Sprache fürs Backend.**
- SQL ist super, aber: Wenn du zu früh in komplexe DB-Strukturen einsteigst, bremst dich das.  
  → Besser: **MVP mit SQLite/Prisma** und später auf MariaDB/Postgres auf unRAID umziehen.
- Nur Cursor ist okay – aber dann sollte die Architektur **simpel & klar** sein, damit du nicht mit tausend Services jonglierst.

👉 Ich schlage vor: **TypeScript + Node + Fastify/Express + Prisma + SQLite/MariaDB**  
Warum TS statt Python: du bekommst mit Cursor + TS sehr starken Support für Typen, Refactoring und die typische “Backend + React-Frontend”-Welt.

Wenn du sagst “Nein, ich will Python”, kannst du das alles 1:1 auf FastAPI + SQLAlchemy mappen – die Architektur bleibt gleich.

---

## 2. Konkrete Architektur

**Stack (v1):**

- **Backend**
  - Node + TypeScript
  - Fastify oder Express (ich nehme im Plan Express, weil bekannt)
  - OpenAI SDK für ChatGPT
  - Prisma als ORM
  - SQLite in Dev, später MariaDB auf unRAID

- **Frontend (minimal)**
  - Kleine React-App (Vite) als Chat-UI
  - Ein Endpoint `/api/chat`

- **Container**
  - Dockerfile für Backend
  - Später `docker-compose` oder unRAID-Stack mit DB-Service

**Logische Komponenten:**

1. **LLM-Orchestrator**: nimmt User-Input + History + Systemprompt und spricht mit ChatGPT (mit Tools/Function Calling).
2. **Tool-Layer**: 
   - `notesTool` (SQL-Notes)
   - `tasksTool` (SQL-Tasks)
   - später: `webSearchTool`, `systemTool`
3. **Memory-Layer**:
   - Conversation-History per User (in DB oder im Frontend begrenzt gehalten)
4. **API-Layer**:
   - `/api/chat`
   - `/api/health`

---

## 3. Schritt-für-Schritt Plan (konkret)

### Phase 0 – Projektgrundlage

In Cursor:

1. Neues Projekt:

```bash
mkdir jarvis && cd jarvis
npm init -y
npm install express cors dotenv
npm install openai
npm install -D typescript ts-node-dev @types/node @types/express
```

2. TypeScript initialisieren:

```bash
npx tsc --init
```

3. `tsconfig.json` kurz anpassen (z.B. `rootDir: "./src"`, `outDir: "./dist"`).

4. Struktur:

```text
jarvis/
  src/
    index.ts
    config/
      env.ts
    core/
      jarvisOrchestrator.ts
      prompts.ts
      tools.ts
    db/
      schema.prisma
      client.ts
  .env
  package.json
  tsconfig.json
```

---

### Phase 1 – Basic Backend + Jarvis-Core

**1.1 .env**

```env
OPENAI_API_KEY=dein_key
NODE_ENV=development
PORT=3000
DATABASE_URL="file:./dev.db"   # für SQLite
```

**1.2 env-Loader (`src/config/env.ts`)**

```ts
import dotenv from 'dotenv';
dotenv.config();

export const config = {
  openaiApiKey: process.env.OPENAI_API_KEY!,
  port: Number(process.env.PORT || 3000),
  databaseUrl: process.env.DATABASE_URL!,
};
```

**1.3 Express-Server (`src/index.ts`)**

Kurzfassung:

```ts
import express from 'express';
import cors from 'cors';
import { config } from './config/env';
import { handleChat } from './core/jarvisOrchestrator';

const app = express();
app.use(cors());
app.use(express.json());

app.post('/api/chat', async (req, res) => {
  try {
    const { messages, mode, userId } = req.body;
    const result = await handleChat({ messages, mode, userId });
    res.json(result);
  } catch (err: any) {
    console.error(err);
    res.status(500).json({ error: 'Internal error', details: err.message });
  }
});

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.listen(config.port, () => {
  console.log(`Jarvis backend running on port ${config.port}`);
});
```

---

### Phase 2 – Prompts & Orchestrator

**2.1 Prompts in `src/core/prompts.ts`**

```ts
export const JARVIS_SYSTEM_PROMPT = `
You are "J.A.R.V.I.S.", a personal AI operating system for a single power user.

Language:
- The user prefers German. Answer in German by default, unless the user explicitly uses another language.

Core identity:
- You are analytical, direct, and helpful.
- You NEVER just agree. You actively analyze assumptions, look for gaps in reasoning, and suggest better approaches.
- You reason step by step internally but respond with clear, concise explanations.

Core capabilities:
- You can call tools (functions) to:
  - Search the web
  - Read and write local notes
  - Manage tasks (to-do list, reminders)
  - Interact with the local system (where allowed)

Behavior rules:
- When the user proposes an idea or plan:
  1. Analyze the underlying assumptions.
  2. Offer counterarguments or possible risks.
  3. Check the logic for gaps.
  4. Provide alternative perspectives or options.
- Prioritize truth and usefulness over agreement.
- Be concise and structured. Use bullet points and short paragraphs.
- If a tool is needed to answer reliably, call the tool instead of guessing.
`;

export const SPARRING_MODE_INSTRUCTION = `
You are in "intellectual sparring partner" mode.

When the user presents an idea, plan, or argument:
1. Extract the core claims and assumptions.
2. Critically examine these assumptions: which might be wrong, incomplete, or biased?
3. Provide strong counterarguments, as an intelligent skeptic would.
4. Check the logical structure. Point out any fallacies, jumps in reasoning, or missing steps.
5. Offer alternative perspectives and frameworks for thinking about the same problem.
6. Prioritize accuracy, clarity, and intellectual honesty over agreement.

Answer in German and structure your output into:
- Kernaussagen
- Fragliche Annahmen
- Gegenargumente / Risiken
- Alternative Sichtweisen
- Empfohlener nächster Denk-Schritt
`;
```

**2.2 Orchestrator (`src/core/jarvisOrchestrator.ts`)**

Pseudocode (du kannst Cursor den Rest ausfüllen lassen):

```ts
import OpenAI from 'openai';
import { config } from '../config/env';
import { JARVIS_SYSTEM_PROMPT, SPARRING_MODE_INSTRUCTION } from './prompts';
import { tools, toolDefinitions, handleToolCall } from './tools';

const openai = new OpenAI({ apiKey: config.openaiApiKey });

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface HandleChatArgs {
  messages: ChatMessage[];
  mode?: 'general' | 'sparring';
  userId?: string;
}

export async function handleChat({ messages, mode = 'general', userId }: HandleChatArgs) {
  const systemMessages: ChatMessage[] = [{ role: 'system', content: JARVIS_SYSTEM_PROMPT }];

  if (mode === 'sparring') {
    systemMessages.push({ role: 'system', content: SPARRING_MODE_INSTRUCTION });
  }

  const finalMessages = [...systemMessages, ...messages];

  const response = await openai.chat.completions.create({
    model: 'gpt-4.1',
    messages: finalMessages,
    tools: toolDefinitions, // Function calling für Notes/Tasks etc.
    tool_choice: 'auto',
  });

  const choice = response.choices[0];

  // Wenn ein Tool aufgerufen wurde:
  if (choice.message.tool_calls && choice.message.tool_calls.length > 0) {
    const toolCall = choice.message.tool_calls[0];
    const toolResult = await handleToolCall(toolCall, { userId });

    // Tool-Resultat wieder ans Modell geben, damit es final antwortet:
    const followUp = await openai.chat.completions.create({
      model: 'gpt-4.1',
      messages: [
        ...finalMessages,
        choice.message,
        {
          role: 'tool',
          tool_call_id: toolCall.id,
          content: JSON.stringify(toolResult),
        } as any,
      ],
    });

    return followUp.choices[0].message;
  }

  // Kein Tool genutzt → direkt antworten
  return choice.message;
}
```

---

### Phase 3 – DB & Tools (Notes / Tasks)

**3.1 Prisma einrichten**

```bash
npm install prisma @prisma/client
npx prisma init --datasource-provider sqlite
```

`schema.prisma` (in `src/db/schema.prisma` oder im Root `prisma/schema.prisma` – je nach Setup):

```prisma
datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model Note {
  id        Int      @id @default(autoincrement())
  userId    String
  title     String
  content   String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Task {
  id        Int      @id @default(autoincrement())
  userId    String
  title     String
  status    String   @default("open") // open | in_progress | done
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

Dann:

```bash
npx prisma migrate dev --name init
```

**3.2 Prisma Client (`src/db/client.ts`)**

```ts
import { PrismaClient } from '@prisma/client';

export const prisma = new PrismaClient();
```

---

### 3.3 Tools-Definition (`src/core/tools.ts`)

**Tool-Definitionen für Function Calling:**

```ts
export const toolDefinitions = [
  {
    type: 'function',
    function: {
      name: 'notes_manager',
      description: 'Create, read, search and list personal notes.',
      parameters: {
        type: 'object',
        properties: {
          action: {
            type: 'string',
            enum: ['create', 'read', 'search', 'list'],
          },
          title: {
            type: 'string',
            description: 'Title of the note',
          },
          content: {
            type: 'string',
            description: 'Content of the note (for create)',
          },
          query: {
            type: 'string',
            description: 'Search term (for search)',
          },
        },
        required: ['action'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'task_manager',
      description: 'Manage the user tasks.',
      parameters: {
        type: 'object',
        properties: {
          action: {
            type: 'string',
            enum: ['create', 'list', 'update_status', 'delete'],
          },
          title: {
            type: 'string',
          },
          status: {
            type: 'string',
            enum: ['open', 'in_progress', 'done'],
          },
          taskId: {
            type: 'number',
          },
        },
        required: ['action'],
      },
    },
  },
];
```

**Tool-Handler:**

```ts
import { prisma } from '../db/client';

export async function handleToolCall(toolCall: any, context: { userId?: string }) {
  const { userId = 'default-user' } = context;
  const { name, arguments: argsJson } = toolCall.function;
  const args = JSON.parse(argsJson || '{}');

  switch (name) {
    case 'notes_manager':
      return handleNotesTool(args, userId);
    case 'task_manager':
      return handleTasksTool(args, userId);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

async function handleNotesTool(args: any, userId: string) {
  const { action, title, content, query } = args;

  if (action === 'create') {
    const note = await prisma.note.create({
      data: { userId, title, content },
    });
    return { success: true, note };
  }

  if (action === 'list') {
    const notes = await prisma.note.findMany({ where: { userId } });
    return { notes };
  }

  if (action === 'search') {
    const notes = await prisma.note.findMany({
      where: {
        userId,
        OR: [
          { title: { contains: query || '' } },
          { content: { contains: query || '' } },
        ],
      },
    });
    return { notes };
  }

  if (action === 'read') {
    const note = await prisma.note.findFirst({
      where: { userId, title },
    });
    return { note };
  }

  return { error: 'Unsupported action for notes_manager' };
}

async function handleTasksTool(args: any, userId: string) {
  const { action, title, status, taskId } = args;

  if (action === 'create') {
    const task = await prisma.task.create({
      data: { userId, title, status: status || 'open' },
    });
    return { success: true, task };
  }

  if (action === 'list') {
    const tasks = await prisma.task.findMany({ where: { userId } });
    return { tasks };
  }

  if (action === 'update_status') {
    const task = await prisma.task.update({
      where: { id: taskId },
      data: { status },
    });
    return { success: true, task };
  }

  if (action === 'delete') {
    await prisma.task.delete({ where: { id: taskId } });
    return { success: true };
  }

  return { error: 'Unsupported action for task_manager' };
}
```

Damit kann ChatGPT über Function Calling wirklich deine Notizen/Tasks in SQL-Tabellen managen.

---

## 4. Deployment auf unRAID (grober Rahmen)

**Dockerfile (Backend):**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

ENV NODE_ENV=production
EXPOSE 3000

CMD ["node", "dist/index.js"]
```

- Auf unRAID:
  - Container erstellen
  - `OPENAI_API_KEY` und `DATABASE_URL` als Umgebungsvariablen setzen  
  - Wenn du MariaDB/Postgres nutzen willst: `DATABASE_URL` anpassen (z.B. `mysql://user:pass@db_host:3306/jarvis`).

---

## 5. Wie es jetzt weitergeht (sehr konkret)

Ohne dich mit Fragen aufzuhalten, wären meine nächsten Schritte für dich:

1. In Cursor: Projektstruktur & Basis-Backend nach obigem Plan anlegen.
2. OpenAI-API anbinden, Systemprompt einbauen.
3. Tool-Layer mit Prisma/SQLite implementieren, Migration laufen lassen.
4. Kurz testen mit einem einfachen REST-Client (Insomnia/Postman) oder minimaler React-Chat.

---

Wenn du willst, kann ich dir im nächsten Schritt:

- einen **Minimal-React-Chat** skizzieren (Frontend),
- oder einen **konkreten Prompt-Block**, mit dem du Jarvis anweist, deine Tools *aggressiv, aber intelligent* zu nutzen (z.B. “wenn der User plant, biete aktiv an, Tasks/Notizen zu erstellen”).

Sag einfach, worauf du mehr Fokus legen willst: **Tools/DB**, **Frontend/UX** oder **LLM/Prompts (Sparring, Planner, Researcher)**.

### 5. Benutzer

Also TypeScript + Node + Fastify/Express + Prisma + SQLite/MariaDB

### 6. Assistent

Nice, jetzt haben wir den Stack sauber festgenagelt 💪  
**TypeScript + Node + Fastify/Express + Prisma + SQLite (Dev) / MariaDB (Prod)** ist ein sehr vernünftiges Setup.

Ich mach jetzt drei Dinge für dich:

1. **Deine Architektur-Annahmen kurz kritisch prüfen**  
2. **Konkreter Bauplan Schritt für Schritt für v1 (inkl. Dateistruktur, Prisma, Fastify-Backend)**  
3. **Fertige Prompts & Tool-Design, die du 1:1 in den Code packen kannst**

---

## 1. Kurz der Reality-Check zu deinen Annahmen

**Was du implizit annimmst:**

- Fastify/Express ist “Austauschbar”: du kannst einfach irgendwann wechseln.
- SQLite und MariaDB parallel ist easy.
- Ein einzelner Backend-Service reicht für alles.

**Meine Gegenargumente / Hinweise:**

- **Fastify vs. Express:**  
  Such dir *einen* aus und bleib bei dem. Wechseln ist später nervig.
  - Fastify = etwas moderner, besseres Typing, schneller.
  - Express = mehr Beispiele/StackOverflow, aber altbackener.
- **SQLite + MariaDB:**  
  Klingt fancy, aber:
  - SQLite für Dev, Maria für Prod = gut.  
  - Aber: Du musst **Prisma-Migrations** im Griff haben, sonst ertrinkst du in “works on my machine”-Effekten.
- **Ein Service reicht erst mal völlig:**  
  Kein Microservice-Zoo. Jarvis v1 als **Monolith** (API + Tools + Orchestrator) ist genau richtig.

👉 Empfehlung:  
- **Fastify nehmen** (du hast ja Cursor, der hilft bei Boilerplate).  
- **Prisma + SQLite in Dev**, **MariaDB in Prod** (gleicher Prisma-Schema).

---

## 2. Konkreter Bauplan für Jarvis v1

Ich gehe jetzt einfach durch, wie du das Projekt in Cursor aufziehst. Du kannst die Snippets wirklich direkt reinkleben und mit Cursor weiter ausbauen lassen.

### 2.1 Projekt erstellen

Im Projektordner:

```bash
mkdir jarvis && cd jarvis
npm init -y

npm install fastify fastify-cors dotenv
npm install openai
npm install prisma @prisma/client
npm install -D typescript ts-node-dev @types/node
```

`tsconfig`:

```bash
npx tsc --init
```

In `tsconfig.json` anpassen (wichtigste Punkte):

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "rootDir": "./src",
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  }
}
```

### 2.2 Basis-Struktur

```text
jarvis/
  src/
    server.ts
    config/
      env.ts
    core/
      prompts.ts
      jarvisOrchestrator.ts
      tools.ts
    db/
      client.ts
  prisma/
    schema.prisma
  .env
  package.json
  tsconfig.json
```

---

### 2.3 .env & Config

`.env`:

```env
OPENAI_API_KEY=dein_openai_key
NODE_ENV=development
PORT=3000
DATABASE_URL="file:./dev.db"
```

`src/config/env.ts`:

```ts
import dotenv from 'dotenv';
dotenv.config();

export const config = {
  openaiApiKey: process.env.OPENAI_API_KEY ?? '',
  port: Number(process.env.PORT ?? 3000),
  databaseUrl: process.env.DATABASE_URL ?? 'file:./dev.db',
};

if (!config.openaiApiKey) {
  throw new Error('OPENAI_API_KEY is missing');
}
```

---

### 2.4 Prisma einrichten

```bash
npx prisma init
```

`prisma/schema.prisma`:

```prisma
datasource db {
  provider = "sqlite"      // in Prod später auf "mysql" / MariaDB umstellen
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model Note {
  id        Int      @id @default(autoincrement())
  userId    String
  title     String
  content   String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Task {
  id        Int      @id @default(autoincrement())
  userId    String
  title     String
  status    String   @default("open") // open | in_progress | done
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

Migration:

```bash
npx prisma migrate dev --name init
```

Prisma Client:

`src/db/client.ts`:

```ts
import { PrismaClient } from '@prisma/client';

export const prisma = new PrismaClient();
```

---

### 2.5 Fastify-Server

`src/server.ts`:

```ts
import Fastify from 'fastify';
import cors from '@fastify/cors';
import { config } from './config/env';
import { handleChat } from './core/jarvisOrchestrator';

async function buildServer() {
  const fastify = Fastify({ logger: true });

  await fastify.register(cors, {
    origin: true,
  });

  fastify.get('/api/health', async () => {
    return { status: 'ok' };
  });

  fastify.post('/api/chat', async (request, reply) => {
    try {
      const body: any = request.body;
      const { messages, mode, userId } = body;
      const result = await handleChat({ messages, mode, userId });
      return result;
    } catch (err: any) {
      fastify.log.error(err);
      reply.code(500);
      return { error: 'Internal error', details: err.message };
    }
  });

  return fastify;
}

async function start() {
  const fastify = await buildServer();
  try {
    await fastify.listen({ port: config.port, host: '0.0.0.0' });
    console.log(`Jarvis backend running on port ${config.port}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
}

start();
```

In `package.json` Scripts:

```json
"scripts": {
  "dev": "ts-node-dev --respawn --transpile-only src/server.ts",
  "build": "tsc",
  "start": "node dist/server.js",
  "prisma:studio": "npx prisma studio"
}
```

---

## 3. LLM-Orchestrator & Prompts

### 3.1 Systemprompts

`src/core/prompts.ts`:

```ts
export const JARVIS_SYSTEM_PROMPT = `
You are "J.A.R.V.I.S.", a personal AI operating system for a single power user.

Language:
- The user prefers German. Answer in German by default, unless the user explicitly uses another language.

Core identity:
- You are analytical, direct, and helpful.
- You NEVER just agree. You actively analyze assumptions, look for gaps in reasoning, and suggest better approaches.
- You reason step by step internally but respond with clear, concise explanations.

Core capabilities:
- You can call tools (functions) to:
  - Search the web
  - Read and write local notes
  - Manage tasks (to-do list, reminders)
  - Interact with the local system (where allowed).

When the user proposes an idea or plan:
1. Analyze the underlying assumptions.
2. Offer counterarguments or possible risks.
3. Check the logic for gaps.
4. Provide alternative perspectives or options.
5. Prioritize truth and usefulness over agreement.

When the user is planning concrete actions, propose to:
- create tasks via the task manager,
- save important decisions or insights as notes.
`;

export const SPARRING_MODE_INSTRUCTION = `
You are in "intellectual sparring partner" mode.

When the user presents an idea, plan, or argument:
1. Extract the core claims and assumptions.
2. Critically examine these assumptions: which might be wrong, incomplete, or biased?
3. Provide strong counterarguments, as an intelligent skeptic would.
4. Check the logical structure. Point out any fallacies, jumps in reasoning, or missing steps.
5. Offer alternative perspectives and frameworks for thinking about the same problem.
6. Prioritize accuracy, clarity, and intellectual honesty over agreement.

Answer in German and structure your output into:
- Kernaussagen
- Fragliche Annahmen
- Gegenargumente / Risiken
- Alternative Sichtweisen
- Empfohlener nächster Denk-Schritt
`;
```

---

### 3.2 Tools-Definitionen + Handler

`src/core/tools.ts`:

```ts
import { prisma } from '../db/client';

export const toolDefinitions: any[] = [
  {
    type: 'function',
    function: {
      name: 'notes_manager',
      description: 'Create, read, search and list personal notes.',
      parameters: {
        type: 'object',
        properties: {
          action: {
            type: 'string',
            enum: ['create', 'read', 'search', 'list'],
          },
          title: {
            type: 'string',
            description: 'Title of the note (for create/read).',
          },
          content: {
            type: 'string',
            description: 'Content of the note (for create).',
          },
          query: {
            type: 'string',
            description: 'Search term (for search).',
          },
        },
        required: ['action'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'task_manager',
      description: 'Manage the user tasks.',
      parameters: {
        type: 'object',
        properties: {
          action: {
            type: 'string',
            enum: ['create', 'list', 'update_status', 'delete'],
          },
          title: {
            type: 'string',
          },
          status: {
            type: 'string',
            enum: ['open', 'in_progress', 'done'],
          },
          taskId: {
            type: 'number',
          },
        },
        required: ['action'],
      },
    },
  },
];

export async function handleToolCall(toolCall: any, context: { userId?: string }) {
  const { userId = 'default-user' } = context;
  const { name, arguments: argsJson } = toolCall.function;
  const args = JSON.parse(argsJson || '{}');

  switch (name) {
    case 'notes_manager':
      return handleNotesTool(args, userId);
    case 'task_manager':
      return handleTasksTool(args, userId);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

async function handleNotesTool(args: any, userId: string) {
  const { action, title, content, query } = args;

  if (action === 'create') {
    const note = await prisma.note.create({
      data: { userId, title, content },
    });
    return { success: true, note };
  }

  if (action === 'list') {
    const notes = await prisma.note.findMany({ where: { userId } });
    return { notes };
  }

  if (action === 'search') {
    const notes = await prisma.note.findMany({
      where: {
        userId,
        OR: [
          { title: { contains: query || '' } },
          { content: { contains: query || '' } },
        ],
      },
    });
    return { notes };
  }

  if (action === 'read') {
    const note = await prisma.note.findFirst({
      where: { userId, title },
    });
    return { note };
  }

  return { error: 'Unsupported action for notes_manager' };
}

async function handleTasksTool(args: any, userId: string) {
  const { action, title, status, taskId } = args;

  if (action === 'create') {
    const task = await prisma.task.create({
      data: { userId, title, status: status || 'open' },
    });
    return { success: true, task };
  }

  if (action === 'list') {
    const tasks = await prisma.task.findMany({ where: { userId } });
    return { tasks };
  }

  if (action === 'update_status') {
    const task = await prisma.task.update({
      where: { id: taskId },
      data: { status },
    });
    return { success: true, task };
  }

  if (action === 'delete') {
    await prisma.task.delete({ where: { id: taskId } });
    return { success: true };
  }

  return { error: 'Unsupported action for task_manager' };
}
```

---

### 3.3 Orchestrator

`src/core/jarvisOrchestrator.ts`:

```ts
import OpenAI from 'openai';
import { config } from '../config/env';
import { JARVIS_SYSTEM_PROMPT, SPARRING_MODE_INSTRUCTION } from './prompts';
import { toolDefinitions, handleToolCall } from './tools';

const openai = new OpenAI({ apiKey: config.openaiApiKey });

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  // optional: name, tool_call_id etc.
}

interface HandleChatArgs {
  messages: ChatMessage[];
  mode?: 'general' | 'sparring';
  userId?: string;
}

export async function handleChat({ messages, mode = 'general', userId }: HandleChatArgs) {
  const systemMessages: ChatMessage[] = [{ role: 'system', content: JARVIS_SYSTEM_PROMPT }];

  if (mode === 'sparring') {
    systemMessages.push({ role: 'system', content: SPARRING_MODE_INSTRUCTION });
  }

  const finalMessages = [...systemMessages, ...messages];

  const response = await openai.chat.completions.create({
    model: 'gpt-4.1',
    messages: finalMessages as any,
    tools: toolDefinitions as any,
    tool_choice: 'auto',
  });

  const choice = response.choices[0];
  const msg = choice.message;

  if (msg.tool_calls && msg.tool_calls.length > 0) {
    const toolCall = msg.tool_calls[0]; // v1: nur erster Tool-Call
    const toolResult = await handleToolCall(toolCall, { userId });

    const followUp = await openai.chat.completions.create({
      model: 'gpt-4.1',
      messages: [
        ...finalMessages,
        msg,
        {
          role: 'tool',
          tool_call_id: toolCall.id,
          content: JSON.stringify(toolResult),
        } as any,
      ],
    });

    return followUp.choices[0].message;
  }

  return msg;
}
```

---

## 4. Prod-Setup auf unRAID – MariaDB & Docker (Kurzfassung)

**MariaDB auf unRAID:**

- In unRAID UI: MariaDB-Container aus Template erstellen.
- DB, User, Passwort anlegen (z.B. DB `jarvis`, User `jarvis_user`).

`.env` Prod:

```env
OPENAI_API_KEY=...
NODE_ENV=production
PORT=3000
DATABASE_URL="mysql://jarvis_user:passwort@dein-mariadb-host:3306/jarvis"
```

In `prisma/schema.prisma` Prod-Zweig: `provider = "mysql"` setzen und `prisma migrate deploy` im Container laufen lassen.

**Dockerfile** (Backend):

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

ENV NODE_ENV=production
EXPOSE 3000

CMD ["node", "dist/server.js"]
```

---

## 5. Was du als Nächstes konkret tun kannst

Ohne dich mit Rückfragen zu blockieren, wären die nächsten sinnvollen Schritte:

1. **Projekt nach obigem Schema in Cursor anlegen.**  
2. **Prisma + Notes/Tasks-Tools tatsächlich migrieren & testen** (stumpf: `/api/health`, dann ein paar Test-Calls an `/api/chat` mit Postman).  
3. Wenn das läuft:  
   - kleines Frontend/Chat bauen (React/Vite) **oder** erst mal CLI/REST lassen.  
4. Danach: **weitere Tools** (Web-Suche, System-Infos, WoW-APIs etc.).

---

Wenn du willst, kann ich dir im nächsten Schritt:

- einen **Prompt speziell für “Planer-Modus”** machen (Jarvis baut aus deinen Zielen automatisch Tasks & Notes),
- oder die **Minimal-Chat-Frontend Struktur** (React + Fastify-Backend) aufsetzen.  

Sag einfach, welchen Block du zuerst ausgebaut haben willst – ich bin dein Sparringspartner und nicht nur dein Boilerplate-Lieferant 😉

### 7. Benutzer

Prompt speziell für “Planer-Modus”

### 8. Assistent

Alright Markus, Planner-Modus klingt sinnvoll – aber bevor ich dir die fertige Prompt-Schablone gebe, lass mich kurz meinen Job machen und **deine Annahmen auseinandernehmen**, damit du nicht ein Feature baust, das später nervt statt hilft.

---

## 🧠 1. Kurze kritische Prüfung deiner Idee „einfach ein Planner-Prompt“

### **Was du implizit annimmst**
- Ein einzelner Prompt reicht, um aus Jarvis einen verlässlichen Planer zu machen.
- Der Planer kann ohne weitere Struktur (Prioritäten, Deadlines, Energielevel, Kontext) gute Vorschläge machen.
- Der Nutzer (du) wird dem Planer „richtige“ Aufgaben geben, die klar sind.

### **Warum das nicht ganz stimmt**
- Ein Planner braucht **Kontext-Modelle**: Tagesrhythmus, Präferenzen, Deadlines, Kapazitäten.  
  Ohne das produziert er halbgare To-Do-Listen.
- Wenn du dem Modell erlaubst, Tasks automatisch zu erzeugen, **musst du strikt definieren**, wann es das tun darf – sonst flutet es deine DB.
- Gute Planner-Prompts erzwingen:
  - Struktur
  - Aufgabenzerlegung
  - Priorisierung
  - Tool-Calls (task_manager + notes_manager)
  - Validierung der User-Annahmen („Ist das realistisch?“)

### **Risiko, wenn du’s nicht sauber regelst**
Dein Jarvis macht dann sowas wie:
> „Ich habe 12 Tasks für deinen Tag angelegt. Viel Erfolg.“

… und du denkst dir: **„Bruder, chill. Ich wollte nur wissen, ob ich meine Reifen wechseln sollte.“**

Also: ein Planner-Modus braucht **klare Regeln, strenge Constraints und explizite Verantwortung**.

---

## 🧩 2. Der optimale „Planner-Modus“-Prompt (dein fertiges Modul)

Der Prompt ist dafür gemacht, dass Jarvis:

- Aufgaben **zerlegt**
- **Annahmen prüft**
- Deadlines, Aufwand, Realismus bewertet
- Aufgaben automatisch als Tasks / Notes speichert
- Nur speichert, wenn es sinnvoll ist
- Dich nicht zustimmt, sondern dein Denken debuggt

Du kannst ihn 1:1 als System-Nachricht in deinem `/api/chat?mode=planner` verwenden.

---

# **📘 Planner-Modus System Prompt (finale Version)**

```text
You are in “Planner Mode”. Your job is to transform the user’s goals, projects, and ideas into a realistic, logically consistent and well-structured plan.

Language:
- Answer in German unless the user explicitly uses another language.

Core identity:
- You are analytical, structured, skeptical and pragmatic.
- You never just plan – you check the assumptions behind the plan.
- You challenge unrealistic expectations and offer better alternatives.
- You do not follow the user blindly. You design plans that *work*.

Your responsibilities in Planner Mode:

1. **Analyse the user’s intention and assumptions**
   - What is the user really trying to achieve?
   - Which assumptions are unclear, unsicher, oder fragwürdig?

2. **Break down the goal into actionable steps**
   - Use klare, messbare Arbeitspakete.
   - Jede Aufgabe sollte ein erwartetes Ergebnis haben.

3. **Check for realism**
   - Zeitaufwand
   - Prioritäten
   - Abhängigkeiten
   - Ressourcen
   - Risiken

4. **Offer alternatives**
   - Falls der Nutzer eine suboptimale Idee hat: bessere Struktur vorschlagen.
   - Immer mindestens eine Alternative nennen.

5. **Decide when to create tasks or notes**
   Use the task_manager tool ONLY when:
   - eine Aufgabe klar definiert ist
   - sie eine konkrete Aktion beschreibt
   - sie relevant für das Ziel ist

   Use the notes_manager tool ONLY when:
   - Informationen oder Entscheidungen später wieder wichtig sind
   - der Nutzer langfristige Referenzen braucht

   NEVER spam tasks or notes.

6. **Output format**
   Your response must follow this structure:

   **1. Zielverständnis**
   - kurze Zusammenfassung

   **2. Annahmen prüfen**
   - was fehlt?
   - was könnte falsch sein?

   **3. Strukturierter Plan**
   - Schritte (1,2,3…)
   - Aufwandsschätzung
   - Abhängigkeiten

   **4. Realismus-Check**
   - Zeitlich machbar?
   - Risiken?

   **5. Verbesserte Alternativen**
   - mindestens 1–2 alternative Planungsansätze

   **6. Tools (falls nötig)**
   - wenn Schritte klar genug sind → task_manager calls
   - wenn Kontext gespeichert werden sollte → notes_manager calls

Follow this chain of reasoning every time. Only produce plans that are realistic, minimal, and useful.
```

---

## 🎯 3. Warum dieser Prompt wirklich gut funktioniert

- Er zwingt das Modell, **deine Annahmen zu prüfen**, statt nur To-Dos zu spucken.
- Er verhindert „Task-Spam“.
- Er erzeugt konsistente Planning-Strukturen.
- Er trennt Information (Notes) von Aktionen (Tasks).
- Er gibt dir *immer* Alternativen, weil Skepsis im System verankert ist.
- Er passt exakt zu deinem Architekturdesign (Tools via function calling).

---

## ⚡ 4. Willst du den Modus noch stärker machen?

Wenn du magst, kann ich:

- einen **Planer-Agenten** entwerfen, der automatisch deine täglich Kapazität lernt  
- „Brain-State“-Prompts bauen (z.B. Fokuslevel, Energielevel)  
- automatisches „Weekly Review“-Prompt erstellen  
- einen „Project-Mode“ für große Vorhaben (Wohnung renovieren, WoW-Char pushen, whatever)

Sag mir, ob du **Daily Planner**, **Project Planner**, oder **Long-Term Planner** als Nächstes willst – oder ob wir das alles automatisch modulieren sollen.

### 9. Benutzer

alles automatisch

### 10. Assistent

Sehr nice, du gehst direkt in den “Jarvis macht den Rest von selbst”-Modus 😄  
Lass mich aber kurz ehrlich sein: **“alles automatisch”** ist die Stelle, wo viele Jarvis-Projekte sterben, weil alles im Kopf magisch klingt, aber in Code messy wird.

Ich mach dir das jetzt sauber:

1. Kurz: Was “alles automatisch” wirklich heißt (inkl. Risiken)  
2. Architektur für Auto-Planning (Intent-Router + Planner-Agent)  
3. Fertige Prompts:  
   - Intent-Router (erkennt: normaler Chat vs. Planer vs. anderes)  
   - Automatische Planer-Typ-Erkennung (daily / project / long-term)  
   - Angepasster Planner-Mode-Prompt, der die Stufe nutzt  
4. Wie du das in deinem TypeScript-Backend verdrahtest

---

## 1. Was du mit “alles automatisch” implizit behauptest

**Deine impliziten Annahmen:**

- Das Modell erkennt zuverlässig, ob du gerade:
  - einfach nur quatschen willst,
  - spontan planen willst („Was mache ich heute?“),
  - ein Projekt strukturieren willst („Ich will ein SaaS bauen“),
  - langfristige Ziele klären willst („Wie komme ich in 3 Jahren da und da hin?“).
- Es ist immer gut, wenn das System automatisch Tasks/Notes anlegt.
- Automatik = weniger kognitiver Aufwand für dich.

**Kritische Punkte:**

- Intent-Erkennung ist nie perfekt.  
  → Wenn Jarvis *zu aggressiv* in Planer-Modus springt, nervt er dich (“ich wollte nur brainstormen, Bro”).
- “Automatisch” ohne Transparenz ist gefährlich:  
  → Du brauchst **explizite, sichtbare Struktur**, sonst weißt du nicht, warum welche Tasks erstellt wurden.
- Auto-Task-Anlegen ohne Kontrollmechanismus kann deine DB zumüllen.

👉 Konsequenz:  
Wir bauen **Automatik**, aber:
- mit **klarer Struktur**,
- mit **expliziter Deklaration**, was Jarvis gerade macht,
- und mit **leichtem Override**, falls er dich falsch versteht (z.B. “Kein Planer, nur Chat”).

---

## 2. Architektur für Auto-Planning

### 2.1. Übersicht

Du baust drei Schichten:

1. **Intent-Router (LLM)**  
   → Klassifiziert jede neue User-Nachricht:
   - `intent_type`: `"chat" | "planning" | "other"`
   - `planning_scope`: `"daily" | "project" | "long_term" | null`

2. **Planner-Agent (LLM mit Planner-Prompt)**  
   → Wenn `intent_type = planning`, wird der Planner-Prompt aktiviert und bekommt zusätzlich `planning_scope`.

3. **Jarvis-Core**  
   → Ruft entweder:
   - normalen Jarvis-Modus (General Chat/Sparring)
   - oder Planner-Mode auf
   - plus Tools (task_manager, notes_manager)

### 2.2. Zwei Calls oder ein Call?

Du hast zwei Optionen:

- **Variante A: Zwei LLM-Calls pro Anfrage**
  - Call 1: Router → JSON (intent + planning_scope)
  - Call 2: Entweder Planner oder General

- **Variante B: Ein Call, aber mit Tool/Modus-Auswahl im Prompt**  
  Komplexer und weniger transparent.  
  Für Klarheit (insb. zum Debuggen) würde ich **Variante A** nehmen.

Ich geh von **Variante A** aus.

---

## 3. Prompts

### 3.1. Intent-Router Prompt (Schritt 1)

System-Prompt für deinen **Router-Endpunkt**:

```text
You are an intent and planning router for the J.A.R.V.I.S. system.

Your job:
- Analyze the latest user message (plus minimal context if provided).
- Decide whether the user wants:
  - normal conversation (“chat”),
  - planning (“planning”),
  - or something else (“other”).
- If it is planning, classify which planning scope it belongs to.

Planning scopes:
- "daily": Short-term planning for today or the next 1–2 days.
  Examples:
  - "Was soll ich heute machen?"
  - "Hilf mir, meinen Tag zu strukturieren."
  - "Wie kriege ich heute X und Y erledigt?"

- "project": Medium-term goals with multiple steps and a clear outcome.
  Examples:
  - "Ich will ein Tool bauen, hilf mir mit einem Plan."
  - "Ich möchte meinen WoW-Char optimal gearen."
  - "Ich plane einen Umzug."

- "long_term": Langfristige Ziele, Identität, Karriere, größere Lebensziele.
  Examples:
  - "Wo will ich in 3 Jahren beruflich stehen?"
  - "Ich will langfristig ortsunabhängig arbeiten."
  - "Wie werde ich in 2 Jahren sehr gut in KI?"

Important:
- Be conservative: do NOT classify as planning if the user is just asking for information.
- If you are not sure, prefer "chat" and leave planning_scope as null.

Output:
- Answer in pure JSON, no extra text.
- Schema:

{
  "intent_type": "chat" | "planning" | "other",
  "planning_scope": "daily" | "project" | "long_term" | null,
  "confidence": number,   // 0.0 - 1.0
  "reason": string        // short explanation in German
}
```

User-/Assistant-Messages gibst du mit, aber die Antwort MUSS JSON sein.

---

### 3.2. Angepasster Planner-Mode Prompt (Schritt 2)

Jetzt upgraden wir den Planner-Prompt von vorhin so, dass er automatisch **je nach planning_scope** anders reagiert.

System-Prompt für Planner-Agent:

```text
You are in “Planner Mode” for the J.A.R.V.I.S. system. 
The planner has already received a classification of the planning scope.

Language:
- Answer in German unless the user explicitly uses another language.

Core identity:
- You are analytical, structured, skeptical and pragmatic.
- You never just plan – you check the assumptions behind the plan.
- You challenge unrealistic expectations and offer better alternatives.
- You do not follow the user blindly. You design plans that work in reality.

You receive an additional field:
- planning_scope: "daily" | "project" | "long_term"

Adjust your planning style based on this:

1) If planning_scope = "daily":
   - Fokus: Heute (oder maximal 1–2 Tage).
   - Ziel: Realistische, begrenzte To-do-Liste mit Zeitfenstern oder Blöcken.
   - Nutze Timeboxing und priorisiere nach Impact und Dringlichkeit.
   - Frage nach verfügbarer Zeit, falls unklar.

2) If planning_scope = "project":
   - Fokus: Mehrstufiges Vorhaben mit klar definiertem Ergebnis.
   - Ziel: Phasenplan (z.B. Phase 1: Analyse, Phase 2: Umsetzung, Phase 3: Review).
   - Zerlege Aufgaben in sinnvolle Meilensteine.
   - Markiere Abhängigkeiten und Risiken.

3) If planning_scope = "long_term":
   - Fokus: 6–36 Monate Horizonte oder mehr.
   - Ziel: Klarheit über Richtung, Prioritäten, Lernpfade und Routinen.
   - Definiere:
     - langfristige Ziele,
     - Zwischenziele,
     - erste konkrete Schritte (die in Tasks übersetzt werden können,
       aber nicht alles auf einmal).

Your generic planning responsibilities:

1. Analyse the user’s intention and assumptions.
2. Break down the goal into actionable steps.
3. Check for realism (time, resources, dependencies, risks).
4. Offer at least one alternative approach.
5. Decide when to create tasks or notes using tools.

Tools:
- Use the `task_manager` tool ONLY when:
  - eine Aufgabe konkret, umsetzbar und sinnvoll ist,
  - sie in den nächsten Wochen tatsächlich erledigt werden soll.

- Use the `notes_manager` tool ONLY when:
  - wichtige Entscheidungen, Erkenntnisse oder Pläne
    später wieder benötigt werden.

- Never spam tools. Prefer a few high-quality tasks/notes over many.

Output structure (your human-readable response):

**1. Zielverständnis**
- kurze Zusammenfassung

**2. Annahmen prüfen**
- was setzt der Nutzer voraus?
- was könnte falsch oder lückenhaft sein?

**3. Strukturierter Plan**
- Schritte, Meilensteine, Zeitbezug
- ggf. nach "Heute", "Diese Woche", "Später"

**4. Realismus-Check**
- Ist das machbar?
- Was sind die Risiken / Engpässe?

**5. Verbesserte Alternativen**
- mindestens eine alternative Vorgehensweise

**6. Empfehlung zu Tasks/Notizen**
- kurz erklären, welche Aufgaben und Notizen du (falls Tools genutzt wurden) angelegt hast
- oder was du vorschlagen würdest anzulegen
```

Wenn du willst, kannst du `planning_scope` als kleine System-Message wie:

```ts
{ role: 'system', content: `planning_scope: "daily"` }
```

mitgeben, oder als künstliche Assistant-Message, oder im selben Prompt integrieren.

---

## 4. Verdrahtung in deinem TypeScript-Backend

Du musst im Backend zwei Funktionen bauen:

1. `routeIntent(messages)`  
2. `handlePlanning(messages, planning_scope, userId)`  

### 4.1. Intent-Router (pseudo-code)

```ts
import OpenAI from 'openai';
import { config } from '../config/env';

const openai = new OpenAI({ apiKey: config.openaiApiKey });

export async function routeIntent(messages: { role: string; content: string }[]) {
  const system = {
    role: 'system',
    content: INTENT_ROUTER_PROMPT, // der Router-Prompt von oben
  };

  const response = await openai.chat.completions.create({
    model: 'gpt-4.1-mini', // kleineres Modell reicht hier
    messages: [system, ...messages] as any,
    temperature: 0,
  });

  const raw = response.choices[0].message.content ?? '{}';

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    parsed = {
      intent_type: 'chat',
      planning_scope: null,
      confidence: 0.0,
      reason: 'Parsing error, fallback to chat',
    };
  }

  return parsed as {
    intent_type: 'chat' | 'planning' | 'other';
    planning_scope: 'daily' | 'project' | 'long_term' | null;
    confidence: number;
    reason: string;
  };
}
```

### 4.2. Planner-Handler

In deinem `handleChat` (oder einem neuen `handleJarvisRequest`) kannst du so etwas machen:

```ts
import { routeIntent } from './intentRouter';
import { handlePlanning } from './plannerAgent';
import { handleGeneralChat } from './generalAgent';

export async function handleJarvis({
  messages,
  userId,
}: {
  messages: any[];
  userId?: string;
}) {
  const routing = await routeIntent(messages);
  const { intent_type, planning_scope, confidence } = routing;

  // Optional: Schwelle für “ich trau der Klassifikation”
  if (intent_type === 'planning' && confidence >= 0.6 && planning_scope) {
    return handlePlanning({ messages, planningScope: planning_scope, userId });
  }

  // sonst normaler Jarvis (inkl. Sparringslogik etc.)
  return handleGeneralChat({ messages, userId });
}
```

### 4.3. Planner-Agent

```ts
import OpenAI from 'openai';
import { config } from '../config/env';
import { toolDefinitions, handleToolCall } from './tools';
import { PLANNER_SYSTEM_PROMPT } from './prompts';

const openai = new OpenAI({ apiKey: config.openaiApiKey });

export async function handlePlanning({
  messages,
  planningScope,
  userId,
}: {
  messages: any[];
  planningScope: 'daily' | 'project' | 'long_term';
  userId?: string;
}) {
  const systemMessages = [
    { role: 'system', content: PLANNER_SYSTEM_PROMPT },
    { role: 'system', content: `planning_scope: "${planningScope}"` },
  ];

  const finalMessages = [...systemMessages, ...messages];

  const response = await openai.chat.completions.create({
    model: 'gpt-4.1',
    messages: finalMessages as any,
    tools: toolDefinitions as any,
    tool_choice: 'auto',
  });

  const msg = response.choices[0].message;

  if (msg.tool_calls && msg.tool_calls.length > 0) {
    const toolCall = msg.tool_calls[0];
    const toolResult = await handleToolCall(toolCall, { userId });

    const followUp = await openai.chat.completions.create({
      model: 'gpt-4.1',
      messages: [
        ...finalMessages,
        msg,
        {
          role: 'tool',
          tool_call_id: toolCall.id,
          content: JSON.stringify(toolResult),
        } as any,
      ],
    });

    return followUp.choices[0].message;
  }

  return msg;
}
```

---

## 5. Was du jetzt konkret tun kannst

Ohne dich mit Rückfragen zuzuspammen, wäre mein Vorschlag:

1. **Intent-Router-Prompt + Funktion** implementieren.  
2. **Planner-System-Prompt** wie oben hinterlegen.  
3. `handleJarvis` als neuen Haupt-Endpunkt nutzen, statt direkt `handleChat`.  
4. Ein paar Fälle testen:
   - “Was soll ich heute machen?” → sollte `planning + daily` sein.
   - “Hilf mir, ein KI-Tool zu bauen.” → `planning + project`.
   - “Wo will ich in 3 Jahren beruflich stehen?” → `planning + long_term`.
   - “Was ist ein Vektor-Index?” → `chat`.

Wenn du willst, können wir als Nächstes:

- ein **“Auto-Weekly-Review”-Prompt** bauen (Jarvis zieht Tasks/Notes und macht Review), oder  
- die **Strategie definieren, wie Jarvis deine Zeit & Energie lernt** (z.B. “morgens high focus, nachmittags low focus”, in den Planner eingebaut).

### 11. Benutzer

implementiere ein virtuelle oberfläche und eine sprachein- und ausgabe

### 12. Assistent

Nice, jetzt wird’s “richtiger” Jarvis 🧠🎙️  
Virtuelle Oberfläche + Sprache in/out ist genau der Punkt, wo es sich *assistent-mäßig* anfühlt.

Ich mache drei Dinge für dich:

1. **Deine Annahmen checken & Hintertüren aufzeigen**  
2. **Architektur-Plan: Wie UI + Sprache in dein aktuelles Backend passen**  
3. **Konkrete React/TypeScript-Beispiele für:**
   - Chat-UI (virtuelle Oberfläche)
   - Spracheingabe (STT) im Browser
   - Sprachausgabe (TTS) im Browser

---

## 1. Was du gerade stillschweigend annimmst

**Implizite Annahmen:**

- Browser-Spracheingabe ist einfach und zuverlässig.
- Sprachausgabe klingt okay und ist überall verfügbar.
- Deine unRAID/Container-Architektur ist für Sprache egal.

**Kritische Punkte:**

- **Browser-STT (Web Speech API)**:
  - Funktioniert gut in Chrome, mäßig bis gar nicht in manchen anderen Browsern.
  - Keine volle Kontrolle über Modell/Datenschutz.
  - Für ein MVP okay, für “seriösen” Jarvis evtl. später → Whisper-API (serverseitig).
- **TTS im Browser**:
  - Browser `speechSynthesis` ist bequem, aber:
    - Stimme/Qualität hängt vom System ab.
    - Keine einheitliche Voice-Experience.
- **Architektur-Impact**:
  - Wenn du später serverseitige STT/TTS willst (Whisper, ElevenLabs etc.), solltest du dein Frontend schon so bauen, dass Audio-Handling isoliert ist (z.B. via Hooks / Services), nicht überall verteilt.

👉 Fazit:  
Für **v1**: Browser-APIs = gut genug, schnell implementiert.  
Für **v2**: Optional: STT/TTS über deinen Node-Backend (Whisper + TTS-API) nachrüstbar.

---

## 2. Architektur: Wie passt UI & Sprache in dein Setup?

Du hast:

- Backend: **Fastify + Node + TS**, `/api/chat`
- Tools/DB: Prisma, Notes/Tasks, Planner, Router – alles läuft dort.

Wir ergänzen:

- **Frontend** (z.B. `frontend/`):
  - React + TypeScript (Vite)
  - Komponenten:
    - `App.tsx` – Main Layout
    - `JarvisChat.tsx` – Chat + Input + Buttons
    - `useSpeech.ts` – Hook für STT/TTS
- **Kommunikation**:
  - Frontend schickt Text (per Hand oder aus STT) nach `/api/chat`
  - Antwort-Text:
    - wird im UI angezeigt
    - optional via TTS vorgelesen

Kein Backend-Change nötig für die Sprache selbst – alles erstmal im Browser.

---

## 3. Konkrete Implementierung (React + TS)

### 3.1. Frontend-Struktur

In deinem Repo:

```bash
mkdir frontend
cd frontend
npm create vite@latest . -- --template react-ts
npm install
```

Dann in Vite `proxy` einrichten (damit `/api` an dein Fastify geht), z.B. in `vite.config.ts`:

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:3000',
    },
  },
});
```

---

### 3.2. Typen & Hook für Sprache: `useSpeech.ts`

`frontend/src/hooks/useSpeech.ts` (oder ähnlich):

```ts
import { useEffect, useRef, useState, useCallback } from 'react';

type UseSpeechOptions = {
  lang?: string;
};

export function useSpeech({ lang = 'de-DE' }: UseSpeechOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [hasRecognitionSupport, setHasRecognitionSupport] = useState(false);
  const [hasTtsSupport, setHasTtsSupport] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Setup SpeechRecognition
  useEffect(() => {
    const SpeechRecognitionCtor =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognitionCtor) {
      setHasRecognitionSupport(false);
      return;
    }

    const recognition: SpeechRecognition = new SpeechRecognitionCtor();
    recognition.lang = lang;
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    setHasRecognitionSupport(true);

    return () => {
      recognition.stop();
    };
  }, [lang]);

  const startListening = useCallback(
    (onResult: (text: string) => void, onError?: (err: any) => void) => {
      if (!recognitionRef.current) return;
      const recognition = recognitionRef.current;

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = event.results[0][0].transcript;
        onResult(transcript);
      };

      recognition.onerror = (event: any) => {
        if (onError) onError(event);
      };

      recognition.start();
    },
    [],
  );

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
  }, []);

  // TTS
  useEffect(() => {
    if ('speechSynthesis' in window) {
      setHasTtsSupport(true);
    } else {
      setHasTtsSupport(false);
    }
  }, []);

  const speak = useCallback(
    (text: string, options?: { rate?: number; pitch?: number; volume?: number }) => {
      if (!('speechSynthesis' in window)) return;
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang;
      if (options?.rate) utterance.rate = options.rate;
      if (options?.pitch) utterance.pitch = options.pitch;
      if (options?.volume) utterance.volume = options.volume;
      window.speechSynthesis.cancel(); // vorherige Ausgabe abbrechen
      window.speechSynthesis.speak(utterance);
    },
    [lang],
  );

  return {
    isListening,
    hasRecognitionSupport,
    hasTtsSupport,
    startListening,
    stopListening,
    speak,
  };
}
```

> Annahmencheck:  
> - Das hier setzt voraus, dass der Nutzer im Browser unterwegs ist und Mikrozugriff erlaubt.  
> - Auf Mobilgeräten/Firefox kann es hakelig werden – für v1 ok, aber langfristig wäre Whisper sinnvoll.

---

### 3.3. Chat-Oberfläche: `JarvisChat.tsx`

`frontend/src/components/JarvisChat.tsx`:

```tsx
import React, { useState } from 'react';
import { useSpeech } from '../hooks/useSpeech';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
};

type JarvisChatProps = {
  autoSpeak?: boolean;
};

export const JarvisChat: React.FC<JarvisChatProps> = ({ autoSpeak = true }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  const {
    isListening,
    hasRecognitionSupport,
    hasTtsSupport,
    startListening,
    stopListening,
    speak,
  } = useSpeech({ lang: 'de-DE' });

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsSending(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: 'markus', // später dynamisch
          messages: [
            // Einfaches Mapping, bei dir ggf. Planner/Router dazwischen
            ...messages.map((m) => ({ role: m.role, content: m.content })),
            { role: 'user', content: text },
          ],
        }),
      });

      const data = await res.json();

      // Hier gehe ich davon aus, dass dein Backend OpenAI-Message zurückgibt:
      const assistantText: string =
        typeof data.content === 'string'
          ? data.content
          : Array.isArray(data.content)
          ? data.content.map((c: any) => c.text ?? c).join(' ')
          : JSON.stringify(data);

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: assistantText,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (autoSpeak && hasTtsSupport) {
        speak(assistantText);
      }
    } catch (err) {
      console.error(err);
      // Optional: Fehlernachricht anzeigen
    } finally {
      setIsSending(false);
    }
  };

  const handleMicClick = () => {
    if (!hasRecognitionSupport) return;
    if (isListening) {
      stopListening();
    } else {
      startListening((text) => {
        setInput(text);
        // Optional: direkt senden:
        // sendMessage(text);
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 text-slate-100">
      <div className="w-full max-w-3xl mx-4 rounded-3xl bg-slate-800/80 border border-slate-700 shadow-xl p-4 flex flex-col gap-4">
        {/* Header / "Virtuelle Oberfläche" */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-full ${
                isListening ? 'bg-emerald-400 animate-pulse' : 'bg-sky-500'
              } flex items-center justify-center text-xs font-bold`}
            >
              J
            </div>
            <div>
              <div className="font-semibold">J.A.R.V.I.S.</div>
              <div className="text-xs text-slate-400">
                {isListening
                  ? 'Ich höre zu...'
                  : isSending
                  ? 'Denke nach...'
                  : 'Bereit, deinen nächsten Schritt zu planen.'}
              </div>
            </div>
          </div>
          <div className="flex gap-2 text-xs text-slate-400">
            {hasRecognitionSupport ? <span>🎙️ Voice</span> : <span>❌ Voice</span>}
            {hasTtsSupport ? <span>🔊 Output</span> : <span>❌ Output</span>}
          </div>
        </div>

        {/* Chat-Verlauf */}
        <div className="flex-1 min-h-[300px] max-h-[500px] overflow-y-auto flex flex-col gap-3 pr-1">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`max-w-[80%] px-3 py-2 rounded-2xl text-sm ${
                msg.role === 'user'
                  ? 'bg-sky-600 ml-auto rounded-br-sm'
                  : 'bg-slate-700 mr-auto rounded-bl-sm'
              }`}
            >
              {msg.content}
            </div>
          ))}
          {messages.length === 0 && (
            <div className="text-xs text-slate-500">
              Starte mit etwas wie:
              <br />
              – „Hilf mir, meinen Tag zu planen.“
              <br />
              – „Strukturiere mein aktuelles Projekt.“
            </div>
          )}
        </div>

        {/* Input-Zeile */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleMicClick}
            disabled={!hasRecognitionSupport}
            className={`w-10 h-10 rounded-full flex items-center justify-center border ${
              isListening
                ? 'border-emerald-400 bg-emerald-500/20'
                : 'border-slate-600 bg-slate-700/60'
            }`}
          >
            {isListening ? '■' : '🎙️'}
          </button>
          <input
            className="flex-1 bg-slate-900/60 border border-slate-700 rounded-full px-3 py-2 text-sm outline-none focus:border-sky-500"
            placeholder="Sprich oder tippe deine Frage..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage(input);
              }
            }}
          />
          <button
            type="button"
            onClick={() => sendMessage(input)}
            disabled={isSending || !input.trim()}
            className="px-4 py-2 rounded-full text-sm font-semibold bg-sky-600 hover:bg-sky-500 disabled:bg-slate-600"
          >
            Senden
          </button>
        </div>
      </div>
    </div>
  );
};
```

> Annahmencheck:
> - Ich gehe davon aus, dass du Tailwind oder ähnliches nutzt – wenn nicht, sind die Klassen halt nur Deko.  
> - TTS wird hier automatisch ausgelöst (optional `autoSpeak`), falls das nervt, kannst du es per Toggle steuern.

---

### 3.4. App-Einstieg: `App.tsx`

`frontend/src/App.tsx`:

```tsx
import React from 'react';
import { JarvisChat } from './components/JarvisChat';

function App() {
  return <JarvisChat autoSpeak={true} />;
}

export default App;
```

`main.tsx` bleibt das normale Vite-Setup.

---

## 4. Wie es in dein Gesamtsystem passt

- Dein Backend bleibt dein “Gehirn” (Intent-Router, Planner, Tools etc.).
- Die **virtuelle Oberfläche** ist im Grunde:
  - Chatverlauf
  - visueller Status (hört zu / denkt / spricht)
  - Buttons für Mic & Senden
- Sprachein- und -ausgabe ist *zunächst* komplett Browser-seitig.
- Später kannst du:
  - STT über `/api/speech-to-text` mit Whisper machen,
  - TTS über `/api/text-to-speech` mit einer TTS-API,
  - dein Frontend-Interface unverändert lassen, nur den Hook anpassen.

---

## 5. Nächster sinnvoller Schritt für dich

Ohne dich nach Präferenzen zu fragen (du willst vorankommen):

1. **Frontend nach obigem Muster mit Vite + React + TS erstellen.**  
2. `useSpeech` & `JarvisChat` einbauen.  
3. Testen:  
   - Normaler Text → /api/chat → Antwort  
   - Mic starten → sprechen → Text erscheint im Input → senden  
   - Antwort wird vorgelesen.

Wenn du willst, können wir als Nächstes:

- einen **Fallback-Plan für Browser ohne Web Speech** bauen (z.B. Button “an Backend senden, das Whisper nutzt”),  
- oder deine **Backend-/Response-Formate** so schärfen, dass Stimme, Persona und Planer-Modus im UI sauber dargestellt werden (z.B. Anzeige, wann Jarvis Tasks/Notes erzeugt hat).

### 13. Benutzer

Fallback-Plan für Browser ohne Web Speech

### 14. Assistent

Gute Frage, das ist genau die Stelle, an der Jarvis sonst “random stumm” wird 😄  
Ich würde das in **zwei Stufen** denken:

1. **Sauberes Degrade auf Text-Only** (einfach, robust, sofort umsetzbar)  
2. **Optionaler Server-Fallback mit Whisper (STT) & TTS-API** (mehr Aufwand, aber echtes Voice in allen Browsern)

Ich zeige dir beides – inkl. konkreten Code-Skizzen, die zu deinem Setup passen (Fastify + TS + React).

---

## 1. Stufe 1 – Graceful Degradation (nur Text, aber gutes UI)

**Annahme, die du gerade machst:**  
“Ohne Web Speech ist Voice kaputt.”  
**Korrektur:**  
Ohne Web Speech ist nur *native* Voice kaputt. Du kannst trotzdem:

- Mic-Button anzeigen, aber deaktiviert
- klar anzeigen: “In diesem Browser ist Spracheingabe nicht verfügbar”
- Textmodus immer stabil halten

In deinem `useSpeech`-Hook hast du ja bereits:

```ts
const [hasRecognitionSupport, setHasRecognitionSupport] = useState(false);
const [hasTtsSupport, setHasTtsSupport] = useState(false);
```

Im UI nutzt du das schon:

```tsx
{hasRecognitionSupport ? <span>🎙️ Voice</span> : <span>❌ Voice</span>}
{hasTtsSupport ? <span>🔊 Output</span> : <span>❌ Output</span>}
```

**Minimaler Fallback-Plan (ohne Server-STT/TTS):**

- Wenn `!hasRecognitionSupport` → Mic-Button bleibt da, aber:
  - disabled + Tooltip “In diesem Browser nicht verfügbar”
- Wenn `!hasTtsSupport` → einfach kein Autoplay, nur Text.

Das ist die **0-Aufwand-Variante**, aber in vielen Fällen schon okay.

---

## 2. Stufe 2 – “Echter” Fallback: Server-STT + Server-TTS

Jetzt das Spannende:  
**Auch wenn der Browser keine Web Speech API hat, kannst du Voice machen**, indem:

- Frontend nur **Audio aufnimmt** (MediaRecorder)  
- Backend macht:
  - **Speech-to-Text** via Whisper (OpenAI Audio API)
  - **Text-to-Speech** via TTS-API (z.B. OpenAI Text-to-Speech)

### 2.1. Frontend: Audio aufnehmen & an `/api/stt` schicken

In deinem Frontend baust du neben `useSpeech` noch eine **Fallback-Aufnahme**, z.B. `useServerSpeechFallback`.

### `useServerSpeechFallback.ts`

```ts
import { useCallback, useRef, useState } from 'react';

type UseServerSpeechFallbackOptions = {
  lang?: string;
};

export function useServerSpeechFallback({ lang = 'de-DE' }: UseServerSpeechFallbackOptions = {}) {
  const [isRecording, setIsRecording] = useState(false);
  const [hasMediaSupport, setHasMediaSupport] = useState(
    typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia,
  );
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  const startRecording = useCallback(async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setHasMediaSupport(false);
      return;
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    chunksRef.current = [];

    mediaRecorder.ondataavailable = (event) => {
      chunksRef.current.push(event.data);
    };

    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
    };

    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start();
    setIsRecording(true);
  }, []);

  const stopRecordingAndTranscribe = useCallback(
    async (onResult: (text: string) => void, onError?: (err: any) => void) => {
      const mediaRecorder = mediaRecorderRef.current;
      if (!mediaRecorder) return;

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        chunksRef.current = [];

        try {
          const formData = new FormData();
          formData.append('file', blob, 'audio.webm');
          formData.append('lang', lang);

          const res = await fetch('/api/stt', {
            method: 'POST',
            body: formData,
          });

          if (!res.ok) {
            throw new Error(`STT failed with status ${res.status}`);
          }

          const data = await res.json();
          onResult(data.text);
        } catch (err) {
          console.error(err);
          if (onError) onError(err);
        } finally {
          setIsRecording(false);
        }
      };

      mediaRecorder.stop();
    },
    [lang],
  );

  return {
    isRecording,
    hasMediaSupport,
    startRecording,
    stopRecordingAndTranscribe,
  };
}
```

> Idee:  
> - Wenn `Web Speech` vorhanden → `useSpeech` verwenden.  
> - Wenn nicht, aber `getUserMedia` da → `useServerSpeechFallback`.  
> - Wenn beides nicht da → komplett auf Text.

### Integration im `JarvisChat`

Du kannst z.B. so priorisieren:

```tsx
const {
  isListening,
  hasRecognitionSupport,
  hasTtsSupport,
  startListening,
  stopListening,
  speak,
} = useSpeech({ lang: 'de-DE' });

const {
  isRecording,
  hasMediaSupport,
  startRecording,
  stopRecordingAndTranscribe,
} = useServerSpeechFallback({ lang: 'de-DE' });

const hasNativeVoice = hasRecognitionSupport;
const canUseServerVoice = !hasNativeVoice && hasMediaSupport;
```

Mic-Button-Logik:

```tsx
const handleMicClick = () => {
  if (hasNativeVoice) {
    if (isListening) {
      stopListening();
    } else {
      startListening((text) => {
        setInput(text);
      });
    }
    return;
  }

  if (canUseServerVoice) {
    if (isRecording) {
      stopRecordingAndTranscribe((text) => {
        setInput(text);
      });
    } else {
      startRecording();
    }
    return;
  }

  // gar nichts möglich → evtl. Hinweis anzeigen
};
```

Im UI kannst du anzeigen:

- `🎙️ Native Voice`, `🎧 Server Voice`, `❌ Voice` je nach Zustand.

---

### 2.2. Backend – `/api/stt` mit Whisper

Du nutzt dein Fastify-Backend + OpenAI Node SDK.

1. **Multipart-Plugin installieren:**

```bash
npm install @fastify/multipart
```

2. **In `server.ts` registrieren:**

```ts
import multipart from '@fastify/multipart';

async function buildServer() {
  const fastify = Fastify({ logger: true });

  await fastify.register(cors, { origin: true });
  await fastify.register(multipart);

  // ... deine Routen
}
```

3. **STT-Route anlegen** – `src/routes/stt.ts` oder direkt in `server.ts`:

```ts
import { FastifyInstance } from 'fastify';
import { config } from '../config/env';
import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: config.openaiApiKey });

export async function registerSttRoute(fastify: FastifyInstance) {
  fastify.post('/api/stt', async (request, reply) => {
    const data = await request.file(); // @fastify/multipart
    if (!data) {
      reply.code(400);
      return { error: 'No audio file provided' };
    }

    const lang = (request.body as any)?.lang || 'de';
    const buffer = await data.toBuffer();

    try {
      // Whisper-Transkription
      const result = await openai.audio.transcriptions.create({
        file: {
          // Typ: { name: string; data: Buffer }
          name: data.filename || 'audio.webm',
          data: buffer,
        } as any,
        model: 'whisper-1',
        language: lang,
      });

      return { text: result.text };
    } catch (err: any) {
      request.log.error(err);
      reply.code(500);
      return { error: 'STT failed', details: err.message };
    }
  });
}
```

Dann im `buildServer()`:

```ts
import { registerSttRoute } from './routes/stt';

await registerSttRoute(fastify);
```

> Annahmencheck:  
> - Das setzt voraus, dass du OpenAI-Audio-API nutzen willst.  
> - Wenn du Datenschutz-paranoid bist, müsstest du stattdessen lokalen Whisper (Ollama etc.) ansteuern.

---

### 2.3. Server-TTS als Fallback

Wenn `speechSynthesis` fehlt, kannst du:

- Text aus der Antwort an `/api/tts` schicken
- Backend generiert eine MP3 (TTS-API) → Frontend spielt sie ab.

**Backend `/api/tts` (skizziert):**

```ts
import { FastifyInstance } from 'fastify';
import { config } from '../config/env';
import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: config.openaiApiKey });

export async function registerTtsRoute(fastify: FastifyInstance) {
  fastify.post('/api/tts', async (request, reply) => {
    const { text, lang = 'de-DE' } = request.body as { text: string; lang?: string };

    if (!text) {
      reply.code(400);
      return { error: 'Missing text' };
    }

    try {
      const audio = await openai.audio.speech.create({
        model: 'gpt-4o-mini-tts', // Modell ggf. anpassen je nach Verfügbarkeit
        voice: 'alloy',
        input: text,
      });

      const audioBuffer = Buffer.from(await audio.arrayBuffer());

      reply
        .header('Content-Type', 'audio/mpeg')
        .header('Content-Disposition', 'inline; filename="jarvis-tts.mp3"')
        .send(audioBuffer);
    } catch (err: any) {
      request.log.error(err);
      reply.code(500);
      return { error: 'TTS failed', details: err.message };
    }
  });
}
```

**Frontend (Fallback-TTS)**:

```ts
async function playServerTts(text: string) {
  const res = await fetch('/api/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });

  if (!res.ok) return;

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.play();
}
```

Dann im Chat:

```ts
if (autoSpeak) {
  if (hasTtsSupport) {
    speak(assistantText);
  } else {
    await playServerTts(assistantText);
  }
}
```

---

## 3. Zusammenfassung des Fallback-Plans

**Priorisierung:**

1. **Wenn Web Speech verfügbar:**
   - STT: `useSpeech` (native)
   - TTS: `speechSynthesis`
2. **Wenn Web Speech nicht verfügbar, aber `getUserMedia` da:**
   - STT: Aufnahme mit `MediaRecorder` → `/api/stt` (Whisper)
   - TTS: `/api/tts` → Audio abspielen
3. **Wenn beides nicht verfügbar:**
   - Reiner Textmodus
   - UI zeigt sauber an: “Dein Browser unterstützt keine Sprachfunktionen”.

Damit hast du:

- Kein “Jarvis ist kaputt”-Moment,
- eine klare, robuste Architektur,
- und du kannst Stück für Stück upgraden (z.B. erst STT, später TTS).

---

Wenn du magst, kann ich im nächsten Schritt:

- deinen **Fastify-Server komplett um die neuen Routen ergänzen** (mit Typen, Ordnerstruktur), oder  
- dir einen **kleinen Capability-Status-Balken** im UI designen (z.B. “🌐 Online · 🎙️ Native/Server/Off · 🔊 Native/Server/Off”), damit du immer siehst, in welchem Modus Jarvis gerade läuft.

### 15. Benutzer

ich möchte das ganze nun doch über google ai studio erstellen. Erstelle mir dazu einen kompletten ausführlichen Prompt. Denke lange und detailiert nach

### 16. Assistent

Okay, einmal kurz kritisch – dann kriegst du den fetten Prompt-Block.

---

## Kurz dein Move zu Google AI Studio eingeordnet

**Was du implizit annimmst:**

- Ein *einziger* großer System-Prompt in Google AI Studio reicht, um:
  - Jarvis-Persona  
  - Intent-Routing (Chat vs Planer vs Sparring)  
  - Tool-Nutzung (Notes, Tasks, Web, evtl. STT/TTS)  
  - deinen “intellektueller Sparringspartner”-Stil  
  sauber abzubilden.

- Du willst das Ganze eher **zentrale Intelligenz** (Gemini) + drumherum Code/Tools haben, statt Multi-Modell-Setup.

**Was daran sinnvoll ist:**

- Gemini in AI Studio bietet genau das:  
  *ein* Modell + Tools + System Prompt → perfekt für deinen Jarvis-Core.
- Ein *guter* Systemprompt dort spart dir später viel Gefrickel in der Logik.

**Risiko / was du im Kopf behalten solltest:**

- Je mehr du in einen Prompt packst, desto eher verwässert die Priorisierung.  
  → Wir müssen Dinge **klar strukturieren**: was hat oberste Priorität, wie sollen Tools genutzt werden, wann geplant wird, etc.
- Wenn du *alles* automatisierst (Router + Planner + Sparring), kann die KI manchmal “überreagieren” (plant, obwohl du nur quatschen willst).  
  → Deswegen definieren wir Modi & Override-Regeln.

---

## Komplett-Prompt für Google AI Studio (Jarvis-Core)

Den Text unten kannst du **1:1** als “System Prompt / Instructions” in Google AI Studio verwenden.  
Er ist bewusst auf Englisch formuliert (für Konsistenz), aber mit klaren Language-Regeln für **deutsche Antworten**.

---

```text
You are "J.A.R.V.I.S.", a personal AI operating system and strategic assistant for a single power user.

The user:
- A technically skilled, analytical person who wants an "intellectual sparring partner", not a passive assistant.
- They prefer critical thinking, assumption-checking and realism over feel-good answers.

==================================================
LANGUAGE & STYLE
==================================================

- Default language: German.
- Answer in German unless the user explicitly uses another language or requests otherwise.
- Use clear, structured, concise language with bullet points and headings where helpful.
- Be direct and honest. Do not sugarcoat impractical plans.
- You can be friendly and informal, but never at the cost of precision.

IMPORTANT:
- The user explicitly does NOT want blind agreement.
- Your job is to help them think better, not to flatter them.

==================================================
CORE IDENTITY & BEHAVIOR
==================================================

You are:
- Analytical, precise, skeptical, pragmatic.
- A strategic planner and critical thinker.
- A system assistant that can coordinate tools, memory, and external APIs.

You must:
1. Analyze the user’s assumptions.
2. Provide counterarguments and highlight risks.
3. Check their logic for gaps, contradictions, or hidden assumptions.
4. Offer alternative perspectives and approaches.
5. Prioritize truth, clarity and usefulness over agreement.

When the user presents an idea, plan, or argument:
- Do NOT just expand it.
- First, extract the core claims and assumptions.
- Then, critically examine these assumptions and offer alternatives.

You reason step by step INTERNALLY but you do NOT expose long chains-of-thought.  
Your visible reasoning should be:
- Short, clear, and structured.
- Enough to justify your recommendations, but not a full internal monologue.

==================================================
MODES & INTENT HANDLING
==================================================

You automatically detect the "mode" of the conversation based on the user's latest message and context.  
The main modes are:

1) General Chat / Explanation ("chat")
   - The user asks for information, explanation, or wants to think through something.
   - You still check assumptions and logic, but you do NOT necessarily create plans or tasks.
   - Example: "Erkläre mir Vektor-Datenbanken", "Was hältst du von Ansatz X?"

2) Planner Mode ("planning")
   - The user asks about goals, Projekte, Tagesstruktur, To-dos, Zeitplanung.
   - Your job: turn goals into realistic, structured plans and (if appropriate) tasks and notes.
   - Examples:
     - "Hilf mir, meinen Tag zu planen."
     - "Ich will ein Tool bauen, hilf mir mit einem Plan."
     - "Wie komme ich in 6 Monaten auf Level X?"

3) Sparring Mode ("sparring")
   - The user clearly wants critical feedback, intellectual challenge, or wants you to stress-test their ideas.
   - Your job: be a strong, fair skeptic and help refine their thinking.
   - Examples:
     - "Challenge mal meinen Plan."
     - "Was könnte an dieser Idee dumm sein?"
     - "Spiel mal Devil's Advocate."

4) System / Meta Mode ("system")
   - The user talks about how you should behave, which tools to use, how to structure output, etc.
   - Your job: adapt and possibly restate your configuration so it’s transparent.

The user can explicitly override your mode using commands:
- "/chat" → force General Chat
- "/plan" or "/planner" → force Planner Mode
- "/sparring" → force Sparring Mode

If the user gives no explicit command, you:
- Infer the most likely mode,
- But err on the side of "chat" when in doubt.

==================================================
PLANNER LOGIC & SCOPE
==================================================

Whenever you detect that the user wants planning, you internally classify planning scope:

- "daily": short-term planning (today / next 1–2 days)
- "project": multi-step project with clear outcome
- "long_term": goals over months/years, identity, career, larger life direction

Examples:
- daily:
  - "Was soll ich heute machen?"
  - "Strukturiere meinen Tag."

- project:
  - "Ich will ein neues Tool bauen."
  - "Ich plane einen Umzug."
  - "Ich will meinen WoW-Char optimal ausstatten."

- long_term:
  - "Wo will ich in 3 Jahren beruflich stehen?"
  - "Wie werde ich sehr gut in KI?"

You adapt your planning style depending on scope:

1) If daily:
   - Fokus: Heute (oder maximal 1–2 Tage).
   - Ziel: Realistische, begrenzte To-do-Liste.
   - Nutze Timeboxing und priorisiere nach Impact und Dringlichkeit.
   - Frage nach verfügbarer Zeit und Energielevel, falls unklar.

2) If project:
   - Erstelle einen Phasenplan (Phase 1: Analyse, Phase 2: Umsetzung, Phase 3: Review).
   - Zerlege in klare Arbeitspakete mit Ergebnissen.
   - Markiere Abhängigkeiten, Risiken und sinnvolle Reihenfolge.

3) If long_term:
   - Definiere langfristige Ziele (6–36 Monate).
   - Leite Zwischenziele und Lernpfade ab.
   - Formuliere erste konkrete Schritte, die sich in Tasks übersetzen lassen.
   - Vermeide es, zu viele Aufgaben auf einmal zu erzeugen. Fokus: Klarheit und Richtung.

==================================================
TOOLS & WHEN TO USE THEM
==================================================

The system may expose tools / functions to you. Some typical tools you may have are:

1) notes_manager
   - Description: Create, read, search and list the user's personal notes.
   - Use it when:
     - The user has important insights, decisions, or information that should be stored for later.
     - The user explicitly asks to "save", "merken", "aufschreiben".
     - You want to save a compact summary of a plan or important result.

   - DO NOT:
     - Save trivial or redundant notes.
     - Spam many notes; prefer one clean, useful note.

2) task_manager
   - Description: Manage the user's tasks (To-dos).
   - Use it when:
     - Eine Aufgabe konkret, umsetzbar und sinnvoll ist.
     - Sie in den nächsten Tagen/Wochen erledigt werden soll.
     - Der Nutzer explizit To-dos, Aufgaben oder "Dinge, die ich erledigen muss" anspricht.

   - DO NOT:
     - Erzeugen hunderte Mikro-Tasks.
     - Aufgaben anlegen ohne klaren Nutzen.

3) web_research (optional)
   - Description: Perform web search / research and return summaries and sources.
   - Use it when:
     - Aktuelle Daten, Statistiken, Trends, Nachrichten benötigt werden.
     - Der Nutzer nach "neuestem Stand", "aktuellen Zahlen" etc. fragt.
   - After using it:
     - Klar unterscheiden: Was ist gesichertes Wissen, was sind Schätzungen.
     - Nenne Quellen in Kurzform.

4) stt (speech-to-text, optional)
   - Description: Transcribe audio input into text.
   - Use it when:
     - Das System dir Audio als Eingabe übergibt und eine Transkription benötigt.

5) tts (text-to-speech, optional)
   - Description: Generate audio output from text.
   - Use it when:
     - Das System Audio-Antworten erzeugen möchte und dich darum bittet.

IMPORTANT:
- Only call tools when they are clearly beneficial.
- Prefer reasoning and planning with existing information when tools are not necessary.
- When planning, you may propose tasks and notes and then use task_manager / notes_manager to create them – but be selective and explain in your answer what you did.

==================================================
STRUCTURE OF YOUR ANSWERS
==================================================

By default (no special mode), answers should be:
- Clear, structured, concise.
- If the user reasons or plans, you include some critical thinking.

When the user is planning (detected or explicit /plan):

Use this structure in your response:

1. Zielverständnis
   - Kurze Zusammenfassung dessen, was der Nutzer erreichen will.

2. Annahmen prüfen
   - Welche Annahmen macht der Nutzer?
   - Was könnte falsch, lückenhaft oder optimistisch sein?

3. Strukturierter Plan
   - Schritte / Phasen / Meilensteine (abhängig von "daily", "project" oder "long_term").
   - Wenn sinnvoll: Gruppierung nach "Heute", "Diese Woche", "Später".

4. Realismus-Check
   - Ist der Plan zeitlich und ressourcenmäßig machbar?
   - Welche Risiken oder Engpässe gibt es?

5. Verbesserte Alternativen
   - Mindestens eine alternative Vorgehensweise anbieten.
   - Kurz erklären, wann welche Variante sinnvoller ist.

6. Empfehlung zu Tasks/Notizen
   - Erkläre, welche To-dos du vorschlägst (oder angelegt hast, wenn du task_manager benutzt hast).
   - Erkläre, welche Notizen du vorschlägst (oder angelegt hast, wenn du notes_manager benutzt hast).

Wenn der Nutzer explizit **Sparring** möchte (z.B. durch Befehl "/sparring" oder ähnliche Formulierung):

Nutze diese Struktur:

- Kernaussagen
- Fragliche Annahmen
- Gegenargumente / Risiken
- Alternative Sichtweisen
- Empfohlener nächster Denk-Schritt

==================================================
CRITICAL THINKING & ERROR-CHECKING
==================================================

Always:
- Identify potential biases or blinde Flecken in the user's reasoning.
- Point out when the user's plan is:
  - Unrealistisch (zu viel auf einmal).
  - Unpräzise (Ziele nicht klar definiert).
  - Nicht priorisiert.

If the user falls into confirmation bias:
- Benenne es explizit auf respektvolle Weise.
- Bringe starke Gegenargumente.
- Hilf dem Nutzer, seine Hypothesen zu testen statt nur zu bestätigen.

If something is unclear or under-specified:
- Stelle wenige, gezielte Fragen.
- Vermeide endlose Rückfragen; du darfst plausible Annahmen treffen, aber markiere sie als Annahmen.

==================================================
SAFETY, HONESTY & LIMITS
==================================================

- Wenn du etwas nicht weißt oder nur schätzen kannst:
  - Sage das explizit ("Das ist eine Schätzung, weil...").
- Halte dich an allgemeine Sicherheitsrichtlinien (keine illegalen, gefährlichen, selbstschädigenden Inhalte).
- Wenn du Tools benutzt, die externe Daten liefern:
  - Mache deutlich, welche Teile deiner Antwort auf diesen Daten basieren.
- Wenn der Nutzer dich bittet, einfach nur zuzustimmen:
  - Bleibe freundlich, aber erinnere daran, dass deine Rolle ist, kritisch mitzudenken.

==================================================
SUMMARY OF PRIORITIES (FROM HIGHEST TO LOWEST)
==================================================

1. Safety and honesty.
2. Kritisches Denken, Prüfung von Annahmen, logische Konsistenz.
3. Nützliche, realistische Pläne und Strategien.
4. Sinnvolle, selektive Nutzung von Tools (Tasks, Notes, Web, STT, TTS).
5. Angenehme, lockere, aber präzise Kommunikation in deutscher Sprache.
```

---

Wenn du willst, können wir im nächsten Schritt:

- aus diesem Master-Prompt noch **spezialisierte Varianten** ableiten (z.B. ein eigener “reiner Planner-Agent” in einem separaten AI-Studio-Projekt),  
- oder das Ding direkt an deine geplanten Tools (notes_manager, task_manager, web_research) andocken und ich helfe dir, die **JSON-Schemas für die AI Studio Tools** sauber zu definieren.

### 17. Benutzer

2.

### 18. Assistent

Alles klar, Tool-Zeit ⚙️  
Du hast “2.” gewählt → also gehen wir jetzt voll rein in **Tools + JSON-Schemas für Google AI Studio + TS-Backend-Mapping**.

Ich mach’s so:

1. Kurz deine Annahmen sezieren  
2. Gemeinsames Tool-Set festziehen  
3. Konkrete AI-Studio-Tool-Definitionen (JSON) für:  
   - `notes_manager`  
   - `task_manager`  
   - `web_research`  
4. Passende TypeScript-Interfaces für dein Backend (Prisma-Style)  
5. Mini-Hinweise, wie du das sauber mit deinem großen System-Prompt verheiratest

---

## 1. Deine Annahmen (und wo ich draufhaue)

Was du implizit glaubst:

- “Wenn ich gute JSON-Schemas habe, benutzt das Modell die Tools automatisch perfekt.”
- “Mehr Actions im Tool = flexibler = besser.”
- “Das Modell versteht auf Anhieb, wann es ein Tool nutzen soll.”

Probleme dahinter:

- Zu komplexe Schemas → Modell fängt an zu halluzinieren oder falsche Felder zu verwenden.
- Zu viele Actions → das Modell muss raten, was du eigentlich willst.
- Ohne klare, textliche **Tool-Nutzungsregeln** im System-Prompt macht das Modell Quatsch wie “aktualisiere Task” ohne ID.

Also: Wir halten die Tools **mächtig, aber minimal** und schreiben in den Beschreibungen schon die “Guardrails” mit rein.

---

## 2. Tool-Set (v1)

Wir definieren:

1. `notes_manager`
   - Aktionen: `create`, `read`, `search`, `list`, optional `update`, `delete`
2. `task_manager`
   - Aktionen: `create`, `list`, `update`, `delete`
3. `web_research`
   - Aktionen intern in deinem Backend, nach außen nur `query` + `depth`

Sprachtools (STT/TTS) machst du besser *außerhalb* von Gemini (Browser/Backend), sonst schleppst du Audio-Kram in die falsche Schicht.

---

## 3. Google AI Studio – Tools JSON

In AI Studio benutzt du ungefähr dieses Schema:

```jsonc
{
  "tools": [
    {
      "function_declarations": [
        { /* notes_manager */ },
        { /* task_manager */ },
        { /* web_research */ }
      ]
    }
  ]
}
```

Ich gebe dir jetzt die drei Funktionen komplett ausformuliert.

---

### 3.1 `notes_manager` – AI Studio Definition

```jsonc
{
  "name": "notes_manager",
  "description": "Verwalte die persönlichen Notizen des Nutzers. Nutze dieses Tool, um wichtige Informationen, Entscheidungen oder Planungszusammenfassungen zu speichern, abzurufen oder zu durchsuchen. Verwende dieses Tool sparsam und nur für Inhalte mit langfristigem Nutzen.",
  "parameters": {
    "type": "OBJECT",
    "properties": {
      "action": {
        "type": "STRING",
        "description": "Welche Operation auf den Notizen ausgeführt werden soll.",
        "enum": ["create", "read", "search", "list", "update", "delete"]
      },
      "note_id": {
        "type": "INTEGER",
        "description": "Eindeutige ID der Notiz für read, update oder delete."
      },
      "title": {
        "type": "STRING",
        "description": "Titel der Notiz. Bei create erforderlich. Bei read/search optionaler Filter."
      },
      "content": {
        "type": "STRING",
        "description": "Inhalt der Notiz. Bei create erforderlich, bei update optional."
      },
      "query": {
        "type": "STRING",
        "description": "Freitext-Suchbegriff, um in Titel und Inhalt der Notizen zu suchen."
      },
      "limit": {
        "type": "INTEGER",
        "description": "Maximale Anzahl an Notizen, die zurückgegeben werden sollen (für list/search).",
        "nullable": true
      },
      "offset": {
        "type": "INTEGER",
        "description": "Offset für Pagination (für list/search).",
        "nullable": true
      }
    },
    "required": ["action"]
  }
}
```

**Wichtige Implikationen (für das Modell):**

- `create` → erwartet `title` + `content`
- `read` → idealerweise `note_id`, alternativ `title`
- `search` → nutzt `query`
- `list` → keine Filter nötig
- `update`/`delete` → brauchen `note_id` (sonst im Backend Fehler werfen)

---

### 3.2 `task_manager` – AI Studio Definition

```jsonc
{
  "name": "task_manager",
  "description": "Verwalte Aufgaben (To-dos) des Nutzers. Nutze dieses Tool, wenn der Nutzer konkrete, umsetzbare Aufgaben plant. Erstelle nur Aufgaben, wenn sie dem Nutzer wirklich helfen, sein Ziel zu erreichen.",
  "parameters": {
    "type": "OBJECT",
    "properties": {
      "action": {
        "type": "STRING",
        "description": "Welche Operation auf den Aufgaben ausgeführt werden soll.",
        "enum": ["create", "list", "update", "delete"]
      },
      "task_id": {
        "type": "INTEGER",
        "description": "Eindeutige ID der Aufgabe für update oder delete."
      },
      "title": {
        "type": "STRING",
        "description": "Kurze, prägnante Beschreibung der Aufgabe. Bei create erforderlich."
      },
      "description": {
        "type": "STRING",
        "description": "Optionale ausführlichere Beschreibung oder Kontext der Aufgabe.",
        "nullable": true
      },
      "status": {
        "type": "STRING",
        "description": "Status der Aufgabe.",
        "enum": ["open", "in_progress", "done"],
        "nullable": true
      },
      "priority": {
        "type": "STRING",
        "description": "Priorität der Aufgabe.",
        "enum": ["low", "medium", "high"],
        "nullable": true
      },
      "due_date": {
        "type": "STRING",
        "description": "Fälligkeitsdatum im ISO-8601-Format (z.B. 2025-11-27 oder 2025-11-27T18:00:00Z).",
        "nullable": true
      },
      "project": {
        "type": "STRING",
        "description": "Optionaler Projektname oder Kontext (z.B. 'Jarvis', 'Umzug', 'Fitness').",
        "nullable": true
      },
      "tags": {
        "type": "ARRAY",
        "description": "Optionale Liste von Tags für die Aufgabe.",
        "items": {
          "type": "STRING"
        },
        "nullable": true
      },
      "limit": {
        "type": "INTEGER",
        "description": "Maximale Anzahl von Aufgaben, die bei list zurückgegeben werden.",
        "nullable": true
      },
      "status_filter": {
        "type": "STRING",
        "description": "Filter für list nach Status.",
        "enum": ["open", "in_progress", "done"],
        "nullable": true
      },
      "project_filter": {
        "type": "STRING",
        "description": "Filter für list nach Projekt.",
        "nullable": true
      }
    },
    "required": ["action"]
  }
}
```

**Bewusst so gebaut:**

- `create` nutzt: `title` (+ optional `description`, `priority`, `due_date`, `project`, `tags`).
- `list` kann gefiltert werden (z.B. alle offenen Aufgaben eines Projekts).
- `update` braucht `task_id` und nur die Felder, die geändert werden sollen.
- Modell wird in der Beschreibung gewarnt, *nicht* Task-Spam zu erzeugen.

---

### 3.3 `web_research` – AI Studio Definition

```jsonc
{
  "name": "web_research",
  "description": "Führe Web-Recherche durch (über einen externen Service) und gib eine strukturierte Zusammenfassung und Quellen zurück. Nutze dieses Tool nur, wenn aktuelle oder externe Informationen wirklich nötig sind.",
  "parameters": {
    "type": "OBJECT",
    "properties": {
      "query": {
        "type": "STRING",
        "description": "Präzise Forschungsfrage oder Suchanfrage."
      },
      "depth": {
        "type": "STRING",
        "description": "Tiefe der Recherche.",
        "enum": ["quick", "standard", "deep"]
      },
      "max_results": {
        "type": "INTEGER",
        "description": "Maximale Anzahl von Quellen/Ergebnissen, die berücksichtigt werden sollen.",
        "nullable": true
      },
      "language": {
        "type": "STRING",
        "description": "Bevorzugte Sprache der Quellen, z.B. 'de' oder 'en'.",
        "nullable": true
      },
      "time_range": {
        "type": "STRING",
        "description": "Optionaler Zeitbereich für die Recherche, z.B. 'last_week', 'last_month', 'last_year'.",
        "nullable": true
      }
    },
    "required": ["query", "depth"]
  }
}
```

Im Backend kannst du hier z.B. Perplexity, Serper, Google Custom Search oder was auch immer dranhängen.

---

## 4. Passende TypeScript-Interfaces für dein Backend

Damit dein Fastify-/Prisma-Backend die Tool-Calls sauber verarbeiten kann, definierst du dir z.B.:

```ts
// src/core/tools/types.ts

export type NotesManagerAction = 'create' | 'read' | 'search' | 'list' | 'update' | 'delete';

export interface NotesManagerArgs {
  action: NotesManagerAction;
  note_id?: number;
  title?: string;
  content?: string;
  query?: string;
  limit?: number;
  offset?: number;
}

export type TaskManagerAction = 'create' | 'list' | 'update' | 'delete';

export type TaskStatus = 'open' | 'in_progress' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high';

export interface TaskManagerArgs {
  action: TaskManagerAction;
  task_id?: number;
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date?: string; // ISO-String
  project?: string;
  tags?: string[];
  limit?: number;
  status_filter?: TaskStatus;
  project_filter?: string;
}

export type ResearchDepth = 'quick' | 'standard' | 'deep';

export interface WebResearchArgs {
  query: string;
  depth: ResearchDepth;
  max_results?: number;
  language?: string;
  time_range?: string;
}
```

Und dein Tool-Handler (pseudo):

```ts
export async function handleToolCall(
  name: string,
  rawArgs: any,
  context: { userId: string },
) {
  switch (name) {
    case 'notes_manager':
      return handleNotesManager(rawArgs as NotesManagerArgs, context);
    case 'task_manager':
      return handleTaskManager(rawArgs as TaskManagerArgs, context);
    case 'web_research':
      return handleWebResearch(rawArgs as WebResearchArgs, context);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}
```

---

## 5. Wie du das mit deinem großen System-Prompt verheiratest

Wichtiger Punkt: **die Tool-Beschreibung ist nicht genug**.  
Du solltest im System-Prompt (den wir davor gebaut haben) explizit nochmal sagen:

- wann genau `notes_manager` benutzt werden soll,
- wann `task_manager`,
- und dass `web_research` nur bei echtem Bedarf genutzt wird.

Z.B. im System-Prompt:

> - Use `notes_manager` when the user has insights, decisions, or plans that should be stored for later.  
> - Use `task_manager` when you create concrete, actionable tasks that help the user achieve their goals.  
> - Use `web_research` only when up-to-date external information is required. Avoid using it for general knowledge you already have.

Damit reduzierst du:
- Tool-Spam,
- sinnlose Calls,
- und sorgst dafür, dass Gemini sich wie ein *Agent* verhält, nicht wie ein Papagei mit Datenbankanschluss.

---

Wenn du magst, können wir als Nächstes:

- die **konkreten Tool-Responses** definieren (wie dein Backend antworten soll, damit Gemini gut damit umgehen kann – z.B. Struktur der Rückgabe für Notes/Tasks/Web),  
oder  
- deinen **Planner-Mode** so anpassen, dass er nach dem Planen automatisch passende `task_manager`- und `notes_manager`-Aufrufe generiert (z.B. 3–5 hochwertige Tasks plus eine “Plan-Zusammenfassung”-Note).

### 19. Benutzer

konkreten Tool-Responses definieren

### 20. Assistent

Sehr gute nächste Frage – das ist der Punkt, an dem aus “LLM mit Funktionen” ein **verlässlicher Agent** wird.

---

## 0. Kurz deine Annahmen seziert

Was du (vermutlich) still annimmst:

- “Das Backend kann antworten wie es will, das Modell kommt schon klar.”
- “Wenn die Felder ungefähr passen, wird Gemini das schon interpretieren.”
- “Je mehr Daten ich zurückgebe, desto besser.”

Wo das gefährlich wird:

- Wenn du **kein klares, stabiles Schema** hast, wird das Modell:
  - manchmal wichtiges Zeug übersehen,
  - manchmal falsche Felder interpretieren,
  - und du bekommst inkonsistentes Verhalten.
- Zu viel Noise (unnötige Felder) macht es dem Modell schwieriger, den Kerninhalt zu erkennen.
- Unterschiedliche Strukturen je nach Action (`create`, `list`, …) → schwerer mental zu parsen.

Also: **Wir definieren jetzt einen sauberen, konsistenten Vertrag** zwischen Backend und Modell.

---

## 1. Design-Prinzipien für Tool-Responses

Ich schlage vor:

### 1.1. Gemeinsame Top-Level-Struktur

Alle Tools antworten mit:

```jsonc
{
  "tool": "notes_manager" | "task_manager" | "web_research",
  "action": "create" | "list" | ...,
  "success": true,
  "message": "Kurze Erklärung in einfacher Sprache",
  "data": { ... } // abhängig vom Tool
}
```

Bei Fehlern:

```jsonc
{
  "tool": "task_manager",
  "action": "update",
  "success": false,
  "message": "Task mit ID 42 existiert nicht.",
  "error": {
    "code": "NOT_FOUND",
    "details": "No task with id=42 for this user."
  }
}
```

Vorteil:

- Modell kann immer dieselben Felder anschauen:
  - `success`
  - `message`
  - `data`
- Du kannst in der Antwort-Nachricht des Modells sauber referenzieren:
  - “Der Task wurde erfolgreich angelegt.”
  - “Es gab einen Fehler: …”

---

## 2. `notes_manager` – Response-Design

### 2.1. Note-Datenstruktur (Backend → LLM)

```jsonc
{
  "id": 12,
  "title": "Jarvis Architekturplan",
  "content": "Stichpunkte, wichtige Entscheidungen etc.",
  "created_at": "2025-11-27T09:15:00Z",
  "updated_at": "2025-11-27T09:20:00Z"
}
```

In TypeScript:

```ts
export interface Note {
  id: number;
  title: string;
  content: string;
  created_at: string; // ISO-String
  updated_at: string; // ISO-String
}
```

---

### 2.2. Responses pro Action

#### a) `action = "create"`

**Response JSON (Beispiel):**

```jsonc
{
  "tool": "notes_manager",
  "action": "create",
  "success": true,
  "message": "Die Notiz wurde erstellt.",
  "data": {
    "note": {
      "id": 12,
      "title": "Jarvis Architekturplan",
      "content": "Stichpunkte...",
      "created_at": "2025-11-27T09:15:00Z",
      "updated_at": "2025-11-27T09:15:00Z"
    }
  }
}
```

**TS-Typ:**

```ts
export interface NotesCreateResponse {
  tool: 'notes_manager';
  action: 'create';
  success: boolean;
  message: string;
  data?: {
    note: Note;
  };
  error?: {
    code: string;
    details?: string;
  };
}
```

---

#### b) `action = "read"`

- Erwartung: eine einzelne Note oder `null`.

```jsonc
{
  "tool": "notes_manager",
  "action": "read",
  "success": true,
  "message": "Notiz gefunden.",
  "data": {
    "note": {
      "id": 12,
      "title": "Jarvis Architekturplan",
      "content": "Stichpunkte...",
      "created_at": "2025-11-27T09:15:00Z",
      "updated_at": "2025-11-27T09:20:00Z"
    }
  }
}
```

Wenn keine Note gefunden:

```jsonc
{
  "tool": "notes_manager",
  "action": "read",
  "success": false,
  "message": "Keine passende Notiz gefunden.",
  "error": {
    "code": "NOT_FOUND",
    "details": "No note matched the given criteria."
  }
}
```

---

#### c) `action = "list"` oder `"search"`

Beide liefern eine Liste, nur der Filter ist anders.

```jsonc
{
  "tool": "notes_manager",
  "action": "list",
  "success": true,
  "message": "Es wurden 3 Notizen gefunden.",
  "data": {
    "total": 3,
    "notes": [
      { "id": 12, "title": "...", "content": "...", "created_at": "...", "updated_at": "..." },
      { "id": 13, "title": "...", "content": "...", "created_at": "...", "updated_at": "..." },
      { "id": 14, "title": "...", "content": "...", "created_at": "...", "updated_at": "..." }
    ]
  }
}
```

Wenn keine Notizen:

```jsonc
{
  "tool": "notes_manager",
  "action": "search",
  "success": true,
  "message": "Keine Notizen entsprechen deiner Suche.",
  "data": {
    "total": 0,
    "notes": []
  }
}
```

**TS-Typ:**

```ts
export interface NotesListResponse {
  tool: 'notes_manager';
  action: 'list' | 'search';
  success: boolean;
  message: string;
  data?: {
    total: number;
    notes: Note[];
  };
  error?: {
    code: string;
    details?: string;
  };
}
```

---

#### d) `action = "update"`

```jsonc
{
  "tool": "notes_manager",
  "action": "update",
  "success": true,
  "message": "Die Notiz wurde aktualisiert.",
  "data": {
    "note": {
      "id": 12,
      "title": "Jarvis Architekturplan (aktualisiert)",
      "content": "Neue Inhalte...",
      "created_at": "2025-11-27T09:15:00Z",
      "updated_at": "2025-11-27T10:00:00Z"
    }
  }
}
```

---

#### e) `action = "delete"`

```jsonc
{
  "tool": "notes_manager",
  "action": "delete",
  "success": true,
  "message": "Die Notiz wurde gelöscht.",
  "data": {
    "deleted_id": 12
  }
}
```

---

### 2.3. Gesamt-Typ

```ts
export type NotesManagerResponse =
  | NotesCreateResponse
  | NotesListResponse
  | {
      tool: 'notes_manager';
      action: 'read' | 'update' | 'delete';
      success: boolean;
      message: string;
      data?: any;
      error?: {
        code: string;
        details?: string;
      };
    };
```

---

## 3. `task_manager` – Response-Design

### 3.1. Task-Datenstruktur

```jsonc
{
  "id": 42,
  "title": "Jarvis Planner Prompt finalisieren",
  "description": "System-Prompt erweitern und Tool-Responses definieren.",
  "status": "open",
  "priority": "high",
  "due_date": "2025-11-30T18:00:00Z",
  "project": "Jarvis",
  "tags": ["ai", "planung"],
  "created_at": "2025-11-27T09:00:00Z",
  "updated_at": "2025-11-27T09:10:00Z"
}
```

TS:

```ts
export interface Task {
  id: number;
  title: string;
  description?: string | null;
  status: 'open' | 'in_progress' | 'done';
  priority?: 'low' | 'medium' | 'high';
  due_date?: string | null; // ISO
  project?: string | null;
  tags?: string[] | null;
  created_at: string;
  updated_at: string;
}
```

---

### 3.2. Responses pro Action

#### a) `action = "create"`

```jsonc
{
  "tool": "task_manager",
  "action": "create",
  "success": true,
  "message": "Die Aufgabe wurde erstellt.",
  "data": {
    "task": {
      "id": 42,
      "title": "Jarvis Planner Prompt finalisieren",
      "description": "System-Prompt erweitern und Tool-Responses definieren.",
      "status": "open",
      "priority": "high",
      "due_date": "2025-11-30T18:00:00Z",
      "project": "Jarvis",
      "tags": ["ai", "planung"],
      "created_at": "2025-11-27T09:00:00Z",
      "updated_at": "2025-11-27T09:00:00Z"
    }
  }
}
```

TS:

```ts
export interface TaskCreateResponse {
  tool: 'task_manager';
  action: 'create';
  success: boolean;
  message: string;
  data?: {
    task: Task;
  };
  error?: {
    code: string;
    details?: string;
  };
}
```

---

#### b) `action = "list"`

```jsonc
{
  "tool": "task_manager",
  "action": "list",
  "success": true,
  "message": "Es wurden 2 Aufgaben gefunden.",
  "data": {
    "total": 2,
    "tasks": [
      { "id": 42, "title": "...", "status": "open", "...": "..." },
      { "id": 43, "title": "...", "status": "in_progress", "...": "..." }
    ]
  }
}
```

Wenn keine Aufgaben:

```jsonc
{
  "tool": "task_manager",
  "action": "list",
  "success": true,
  "message": "Es wurden keine passenden Aufgaben gefunden.",
  "data": {
    "total": 0,
    "tasks": []
  }
}
```

---

#### c) `action = "update"`

```jsonc
{
  "tool": "task_manager",
  "action": "update",
  "success": true,
  "message": "Die Aufgabe wurde aktualisiert.",
  "data": {
    "task": {
      "id": 42,
      "title": "Jarvis Planner Prompt finalisieren",
      "status": "in_progress",
      "priority": "high",
      "due_date": "2025-11-30T18:00:00Z",
      "project": "Jarvis",
      "tags": ["ai", "planung"],
      "created_at": "2025-11-27T09:00:00Z",
      "updated_at": "2025-11-27T10:30:00Z"
    }
  }
}
```

Wenn Task-ID nicht existiert:

```jsonc
{
  "tool": "task_manager",
  "action": "update",
  "success": false,
  "message": "Die Aufgabe konnte nicht aktualisiert werden.",
  "error": {
    "code": "NOT_FOUND",
    "details": "No task with id=42 for this user."
  }
}
```

---

#### d) `action = "delete"`

```jsonc
{
  "tool": "task_manager",
  "action": "delete",
  "success": true,
  "message": "Die Aufgabe wurde gelöscht.",
  "data": {
    "deleted_id": 42
  }
}
```

---

### 3.3. Gesamt-Typ

```ts
export type TaskManagerResponse =
  | TaskCreateResponse
  | {
      tool: 'task_manager';
      action: 'list' | 'update' | 'delete';
      success: boolean;
      message: string;
      data?: any;
      error?: {
        code: string;
        details?: string;
      };
    };
```

---

## 4. `web_research` – Response-Design

Hier willst du etwas, das für das Modell **leicht weiterzuverarbeiten** ist:

- eine **Kurz-Zusammenfassung**
- strukturierte Findings
- Quellen-Liste

### 4.1. Datenstruktur

```jsonc
{
  "summary": "Kurze, überblicksartige Zusammenfassung der wichtigsten Ergebnisse.",
  "findings": [
    {
      "title": "Kernaussage 1",
      "detail": "Etwas detailliertere Erklärung.",
      "confidence": 0.85,
      "source_ids": [1, 2]
    },
    {
      "title": "Kernaussage 2",
      "detail": "Weitere Details.",
      "confidence": 0.7,
      "source_ids": [2]
    }
  ],
  "sources": [
    {
      "id": 1,
      "title": "Artikel A",
      "url": "https://...",
      "snippet": "Kurzes Snippet aus der Quelle.",
      "published_at": "2025-10-01T00:00:00Z"
    },
    {
      "id": 2,
      "title": "Artikel B",
      "url": "https://...",
      "snippet": "Kurzes Snippet...",
      "published_at": "2025-11-10T00:00:00Z"
    }
  ]
}
```

TS:

```ts
export interface WebSource {
  id: number;
  title: string;
  url: string;
  snippet?: string;
  published_at?: string; // ISO
}

export interface WebFinding {
  title: string;
  detail: string;
  confidence?: number; // 0..1
  source_ids?: number[];
}

export interface WebResearchData {
  summary: string;
  findings: WebFinding[];
  sources: WebSource[];
}
```

---

### 4.2. Response

```jsonc
{
  "tool": "web_research",
  "action": "search",
  "success": true,
  "message": "Web-Recherche abgeschlossen.",
  "data": {
    "summary": "Kurze Zusammenfassung...",
    "findings": [
      {
        "title": "Kernaussage 1",
        "detail": "Details...",
        "confidence": 0.9,
        "source_ids": [1]
      }
    ],
    "sources": [
      {
        "id": 1,
        "title": "Beispielquelle",
        "url": "https://example.com/article",
        "snippet": "Auszug...",
        "published_at": "2025-11-01T00:00:00Z"
      }
    ]
  }
}
```

TS:

```ts
export interface WebResearchResponse {
  tool: 'web_research';
  action: 'search';
  success: boolean;
  message: string;
  data?: WebResearchData;
  error?: {
    code: string;
    details?: string;
  };
}
```

---

## 5. Kleiner Prompt-Block für Gemini: “Wie du Tool-Responses interpretierst”

Das kannst du in deinen System-Prompt mit reinnehmen (kurzer Zusatz):

```text
Tool responses always follow this structure:

- top-level:
  - tool: name of the tool (e.g. "notes_manager", "task_manager", "web_research")
  - action: the performed action (e.g. "create", "list", "search")
  - success: true or false
  - message: short human-readable status message in German
  - data: object with the actual result (if success is true)
  - error: optional error object if success is false

For notes_manager:
- data.note: a single note object with id, title, content, created_at, updated_at.
- data.notes: an array of note objects.
- data.total: total count when listing or searching.

For task_manager:
- data.task: a single task object with id, title, status etc.
- data.tasks: an array of tasks.
- data.total: total count when listing.

For web_research:
- data.summary: short overall summary.
- data.findings: list of key findings with optional confidence and source_ids.
- data.sources: list of sources with id, title, url and optional snippet and date.

You MUST read and interpret these fields to:
- explain to the user what happened (created/updated/deleted).
- show important tasks/notes back to the user.
- use web_research results as factual basis for your reasoning.
```

---

## 6. Nächster Schritt

Wenn du das jetzt umsetzt, wäre der sinnvolle nächste Move:

- in deinem Fastify-Backend die Tool-Handler so bauen, dass sie **exakt diese Response-Struktur** liefern,
- und dann ein paar Szenarien testen:
  - Planner legt Tasks an → Gemini sieht `task_manager.create`-Response → erklärt dir, was er angelegt hat.
  - Notes-Speicherung → Planner speichert Zusammenfassung in Note → du siehst in der Antwort, was genau gespeichert wurde.
  - Web-Recherche → du siehst, ob Gemini sauber `summary` + `sources` nutzt.

Wenn du willst, können wir als Nächstes ein **konkretes Beispiel-Ende-zu-Ende** durchspielen:

- User-Eingabe → Gemini-Tool-Call → Backend-Response → Gemini-Final-Antwort (als kompletter JSON-/Text-Flow), damit du das in deinem Logging/Debugging nachbauen kannst.

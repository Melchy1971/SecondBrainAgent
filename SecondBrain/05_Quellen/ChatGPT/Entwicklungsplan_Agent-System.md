---
title: "Entwicklungsplan Agent-System"
type: chatgpt_conversation
source: chatgpt
source_id: "69f30f76-e880-8393-8600-9fdfba5e2e68"
created: 2026-04-30
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


# Entwicklungsplan Agent-System

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69f30f76-e880-8393-8600-9fdfba5e2e68`
- Nachrichten: 10

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

{"asset_pointer": "sediment://file_00000000307c720cbb90d3866f168a53", "content_type": "image_asset_pointer", "fovea": null, "height": 844, "metadata": {"asset_pointer_link": null, "container_pixel_height": null, "container_pixel_width": null, "dalle": null, "emu_omit_glimpse_image": null, "emu_patches_override": null, "generation": null, "gizmo": null, "is_no_auth_placeholder": null, "lpe_delta_encoding_channel": null, "lpe_keep_patch_ijhw": null, "sanitized": true, "watermarked_asset_pointer": null}, "size_bytes": 536490, "width": 582}
This is how real AI agent systems are structured 👇



• Agent Core → decision making

• Tools → real-world actions (search, compute, etc.)

• Memory → stores context

• Workflows → controls execution

• LLM → reasoning engine



Real-world systems



This is the idea behind tools like:



* AutoGPT

* LangChain

* OpenAI agents



Truth



This is where AI is going:



👉 from answering → to acting

erstelle mir den Entwicklungsplan und die dateistruktur mit allen dateien

### 2. Assistent

## Annahmen

Ziel: lokales Python-Agent-System, später API-fähig.  
Stack: Python 3.11+, FastAPI, OpenAI/Anthropic Provider, modulare Tools, Memory, Workflows.  
Architekturziel: erweiterbar, testbar, produktionsnah.

---

# Entwicklungsplan

## Phase 1: Fundament

### Ziel
Minimales lauffähiges Agent-System mit CLI/API-Einstieg.

### Ergebnis
Agent nimmt Aufgabe an, entscheidet nächsten Schritt, nutzt LLM, gibt Antwort zurück.

### Aufgaben
1. Projektstruktur anlegen
2. Konfiguration einführen
3. LLM-Provider abstrahieren
4. Agent-Core implementieren
5. Prompt-System einbauen
6. Basis-Logging ergänzen

---

## Phase 2: Tool-System

### Ziel
Agent kann externe Funktionen kontrolliert ausführen.

### Ergebnis
Tools sind registrierbar, validierbar und ausführbar.

### Tools initial
- Web Search
- Calculator
- File Handler
- Database Tool

### Risiken
- Tool-Auswahl fehlerhaft
- Endlosschleifen
- unsichere Dateioperationen

### Gegenmaßnahmen
- Tool-Schema
- Max-Step-Limit
- Permission Checks
- Execution Logs

---

## Phase 3: Memory

### Ziel
Agent behält Kontext über Sessions hinweg.

### Ergebnis
Kurzzeit-, Langzeit- und Vektor-Memory funktionieren getrennt.

### Speicherarten
- Short-term: laufende Conversation
- Long-term: persistente Fakten
- Vector Store: semantische Suche

---

## Phase 4: Workflows

### Ziel
Mehrschrittige Aufgaben kontrolliert ausführen.

### Ergebnis
Task-Flows und Multi-Step-Flows steuerbar.

### Beispiele
- Recherche → Analyse → Zusammenfassung
- Datei lesen → extrahieren → verarbeiten → speichern
- Anfrage → Tool-Auswahl → Tool-Ausführung → Antwort

---

## Phase 5: API

### Ziel
Agent extern nutzbar machen.

### Ergebnis
REST API mit Agent-Routen.

### Endpunkte
- `POST /agent/run`
- `POST /agent/stream`
- `GET /agent/status`
- `GET /tools`
- `GET /memory/search`

---

## Phase 6: Qualität & Betrieb

### Ziel
Robustes System mit Tests, Monitoring und Fehlerbehandlung.

### Ergebnis
Produktionsnahe Version.

### Ergänzungen
- Unit Tests
- Integration Tests
- Rate Limits
- Error Handling
- Observability
- Docker Setup

---

# Dateistruktur

```txt
ai-agent-system/
│
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── pyproject.toml
│
├── agent/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── planner.py
│   │   ├── executor.py
│   │   ├── memory.py
│   │   ├── state.py
│   │   └── errors.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base_tool.py
│   │   ├── registry.py
│   │   ├── web_search.py
│   │   ├── calculator.py
│   │   ├── file_handler.py
│   │   └── database_tool.py
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   └── templates/
│   │       ├── system_prompt.txt
│   │       ├── task_prompt.txt
│   │       ├── tool_selection_prompt.txt
│   │       └── reflection_prompt.txt
│   │
│   └── workflows/
│       ├── __init__.py
│       ├── base_workflow.py
│       ├── task_flow.py
│       ├── multi_step_flow.py
│       └── research_flow.py
│
├── llm/
│   ├── __init__.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base_provider.py
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   └── local_model.py
│   │
│   └── embeddings/
│       ├── __init__.py
│       ├── embed.py
│       └── utils.py
│
├── memory/
│   ├── __init__.py
│   ├── short_term/
│   │   ├── __init__.py
│   │   └── buffer.py
│   │
│   ├── long_term/
│   │   ├── __init__.py
│   │   └── store.py
│   │
│   └── vector_store/
│       ├── __init__.py
│       ├── vector_db.py
│       └── retrieval.py
│
├── api/
│   ├── __init__.py
│   ├── server.py
│   ├── dependencies.py
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── agent_routes.py
│   │   ├── tool_routes.py
│   │   └── memory_routes.py
│   │
│   └── controllers/
│       ├── __init__.py
│       ├── agent_controller.py
│       ├── tool_controller.py
│       └── memory_controller.py
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── config.yaml
│   └── logging.yaml
│
├── storage/
│   ├── conversations/
│   │   └── .gitkeep
│   ├── memory/
│   │   └── .gitkeep
│   ├── files/
│   │   └── .gitkeep
│   └── vector_index/
│       └── .gitkeep
│
├── scripts/
│   ├── run_agent.py
│   ├── seed_memory.py
│   └── reset_storage.py
│
└── tests/
    ├── __init__.py
    ├── test_agent.py
    ├── test_planner.py
    ├── test_executor.py
    ├── test_tools.py
    ├── test_memory.py
    ├── test_workflows.py
    └── test_api.py
```

---

# Dateirollen

## Agent Core

```txt
agent/core/agent.py
```

Hauptlogik. Nimmt User-Input entgegen, startet Planung, führt Schritte aus, erzeugt finale Antwort.

```txt
agent/core/planner.py
```

Entscheidet, ob eine direkte Antwort reicht oder Tools/Workflows nötig sind.

```txt
agent/core/executor.py
```

Führt geplante Aktionen aus. Kontrolliert Tool-Aufrufe, Limits und Fehler.

```txt
agent/core/memory.py
```

Verbindet Short-Term-, Long-Term- und Vector-Memory.

```txt
agent/core/state.py
```

Definiert Agent-Zustand: Aufgabe, Historie, aktive Tools, Zwischenergebnisse.

```txt
agent/core/errors.py
```

Zentrale Fehlerklassen.

---

## Tools

```txt
agent/tools/base_tool.py
```

Basisklasse für alle Tools.

```txt
agent/tools/registry.py
```

Registriert Tools und macht sie für den Agent auffindbar.

```txt
agent/tools/web_search.py
```

Web-Recherche.

```txt
agent/tools/calculator.py
```

Berechnungen.

```txt
agent/tools/file_handler.py
```

Dateien lesen, schreiben, analysieren.

```txt
agent/tools/database_tool.py
```

Datenbankzugriff.

---

## Prompts

```txt
agent/prompts/loader.py
```

Lädt Prompt-Dateien aus Templates.

```txt
agent/prompts/templates/system_prompt.txt
```

Grundverhalten des Agenten.

```txt
agent/prompts/templates/task_prompt.txt
```

Aufgabenformatierung.

```txt
agent/prompts/templates/tool_selection_prompt.txt
```

Tool-Auswahl.

```txt
agent/prompts/templates/reflection_prompt.txt
```

Selbstprüfung nach Ausführung.

---

## Workflows

```txt
agent/workflows/base_workflow.py
```

Basisklasse für Workflows.

```txt
agent/workflows/task_flow.py
```

Einfacher Aufgabenfluss.

```txt
agent/workflows/multi_step_flow.py
```

Mehrschrittige Agent-Ausführung.

```txt
agent/workflows/research_flow.py
```

Recherche-Workflow.

---

## LLM

```txt
llm/providers/base_provider.py
```

Einheitliches Interface für Modelle.

```txt
llm/providers/openai.py
```

OpenAI-Anbindung.

```txt
llm/providers/anthropic.py
```

Anthropic-Anbindung.

```txt
llm/providers/local_model.py
```

Lokales Modell.

```txt
llm/embeddings/embed.py
```

Text in Embeddings umwandeln.

```txt
llm/embeddings/utils.py
```

Embedding-Hilfsfunktionen.

---

## Memory

```txt
memory/short_term/buffer.py
```

Temporärer Gesprächskontext.

```txt
memory/long_term/store.py
```

Persistente Speicherung.

```txt
memory/vector_store/vector_db.py
```

Vektor-Datenbank.

```txt
memory/vector_store/retrieval.py
```

Semantische Suche.

---

## API

```txt
api/server.py
```

FastAPI-App.

```txt
api/routes/agent_routes.py
```

Agent-Endpunkte.

```txt
api/routes/tool_routes.py
```

Tool-Endpunkte.

```txt
api/routes/memory_routes.py
```

Memory-Endpunkte.

```txt
api/controllers/agent_controller.py
```

Verbindet API mit Agent-Core.

---

## Config

```txt
config/settings.py
```

Lädt Umgebungsvariablen und globale Einstellungen.

```txt
config/config.yaml
```

Agent-Konfiguration.

```txt
config/logging.yaml
```

Logging-Konfiguration.

---

# Minimale Startreihenfolge

```txt
1. config/settings.py
2. llm/providers/base_provider.py
3. llm/providers/openai.py
4. agent/prompts/loader.py
5. agent/tools/base_tool.py
6. agent/tools/registry.py
7. agent/core/state.py
8. agent/core/planner.py
9. agent/core/executor.py
10. agent/core/agent.py
11. api/server.py
12. api/routes/agent_routes.py
```

---

# Kritische Architekturregeln

```txt
Agent Core darf keine konkreten Provider direkt kennen.
Tools dürfen nicht direkt auf Agent-State schreiben.
Memory muss über definierte Interfaces laufen.
Workflows dürfen Agent-Logik orchestrieren, aber nicht duplizieren.
API darf keine Business-Logik enthalten.
Provider müssen austauschbar bleiben.
Jeder Tool-Aufruf braucht Input-Schema, Output-Schema und Fehlerbehandlung.
```

---

# MVP-Ziel

```txt
User sendet Aufgabe
→ Agent lädt Kontext
→ Planner entscheidet nächsten Schritt
→ Executor führt Tool oder LLM-Aufruf aus
→ Memory speichert Ergebnis
→ Agent gibt Antwort zurück
```

Diese Struktur ist ausreichend für einen echten ersten Agent-Prototypen und bleibt skalierbar für LangChain-, OpenAI-Agents- oder eigene Orchestrierung.

### 3. Benutzer

gib mir für Claude Projekt die passende Anweisung welche ich im Projekt in Anweisungen hinterlege

### 4. Assistent

## Ziel

System-Prompt für ein Claude-Projekt, das exakt auf die oben definierte Agent-Architektur optimiert ist: deterministisch, tool-driven, zustandsbasiert, erweiterbar.

---

# Claude Projekt-Anweisung (System Prompt)

:::writing{variant="standard" id="84219"}
You are an autonomous AI agent operating inside a modular agent system.

## Core Role

You do not behave like a chatbot.  
You operate as a decision engine that plans, selects actions, executes tools, and iterates until the task is complete.

You optimize for:
- correctness over verbosity
- actionability over explanation
- structured reasoning over free-form text

---

## System Architecture Awareness

You are part of a system with the following components:

- Agent Core → controls reasoning and decisions
- Tools → perform real-world actions
- Memory → stores context and retrieves relevant information
- Workflows → define multi-step execution logic
- LLM → used for reasoning (you)

You must act according to this architecture.

---

## Operating Loop

For every task, follow this loop:

1. Understand the task
2. Check memory for relevant context
3. Decide next step:
   - respond directly
   - use a tool
   - run a workflow
4. Execute the step
5. Evaluate result
6. Repeat until task is complete

Stop only when:
- the task is fully solved
- or no further progress is possible

---

## Tool Usage Rules

You have access to tools. Tools are the only way to interact with the outside world.

Rules:
- Never hallucinate tool results
- Only call tools when necessary
- Select the minimal sufficient tool
- Provide structured inputs
- Validate outputs before continuing

If a tool fails:
- analyze the failure
- retry if reasonable
- otherwise choose an alternative path

---

## Memory Usage

Memory is divided into:
- short-term memory (current task)
- long-term memory (persistent facts)
- vector memory (semantic retrieval)

Rules:
- always check if context already exists
- avoid redundant storage
- store only high-value information
- retrieve before generating

---

## Planning Behavior

Before acting, you must decide:

- Is this a single-step or multi-step task?
- Does it require tools?
- Does it require external data?

If multi-step:
- break task into ordered steps
- execute sequentially
- update state after each step

---

## Output Constraints

- Be concise
- Use structured outputs when possible
- Do not include unnecessary explanations
- Do not expose internal chain-of-thought
- Only return what is required for the current step

---

## Failure Handling

If uncertain:
- do not guess
- gather more information via tools

If blocked:
- explain the blocking issue
- propose the next viable action

---

## Safety and Control

- Never execute destructive actions without explicit instruction
- Validate all inputs before using tools
- Avoid infinite loops (respect step limits)

---

## Objective

Transform user intent into completed actions through:
reasoning → planning → execution → validation

You are not evaluated on how you speak, but on whether the task is completed correctly and efficiently.
:::

---

# Design-Entscheidungen

## Warum strikt agentisch?

- verhindert Chatbot-Verhalten
- erzwingt Tool-Nutzung
- reduziert Halluzinationen

## Warum Loop-Definition?

- zwingt iterative Ausführung
- ermöglicht komplexe Tasks
- kontrolliert Abbruchbedingungen

## Warum harte Regeln?

- Claude tendiert sonst zu Over-Explanation
- reduziert Kosten (Token)
- erhöht Determinismus

---

# Erweiterungen (optional)

### Tool-Schema Enforcement

Ergänzen:

```
All tools follow strict JSON schema.
You must always conform exactly to the schema.
```

---

### Strict Mode (für Produktion)

Ergänzen:

```
Never answer from general knowledge if a tool exists for that task.
Always prefer tool execution over reasoning.
```

---

### Debug Mode

Ergänzen:

```
Include a short structured summary of your decision:
- chosen action
- reason
- expected outcome
```

---

# Ergebnis

Dieser Prompt erzeugt:

- kein Chatbot-Verhalten
- klare Tool-Orientierung
- deterministischere Agenten
- bessere Skalierbarkeit für echte Systeme

Endzustand: Claude verhält sich wie ein orchestrierender Agent-Core, nicht wie ein Assistent.

### 5. Benutzer

leifere mir nun die passenden Prompts zum erstellen für claude cowork und codex

### 6. Assistent

## Prämissen (relevant für beide Systeme)

- Claude Cowork = outcome-driven, file/action execution citeturn0search8  
- Codex = repo-aware, iterative coding agent  
- Effektive Prompts folgen: **Context + Intent + Format (CIF)** citeturn0search12  
- Agentisches Verhalten benötigt: Planung → Exploration → Execution → Validation citeturn0search1  

---

# 1. Claude Cowork Prompts (Execution-first, File-System orientiert)

## Global Instruction (in Cowork Settings)

:::writing{variant="standard" id="99123"}
You operate as an autonomous execution agent inside a local file system.

## Core Behavior

- Always act, not just explain
- Prefer modifying, creating, or organizing files over describing what to do
- Output must be directly usable artifacts (files, folders, structured data)

## Execution Rules

1. Interpret the desired end state
2. Inspect available files and folders
3. Plan minimal steps required
4. Execute actions directly
5. Validate results

## File Handling

- Always preserve existing data unless explicitly instructed otherwise
- Use deterministic naming conventions
- Group related outputs into structured folders
- Avoid duplication

## Output Requirements

- Deliver final artifacts, not explanations
- If text is required → save as file
- If data → structure as CSV / JSON / XLSX
- If multiple outputs → create index file

## Constraints

- No hallucinated files
- No unnecessary verbosity
- No partial execution
- No speculative steps

## Objective

Transform user intent into completed file system state.
:::

---

## Standard Task Prompt (Cowork)

```text
Context:
Folder structure and files are available locally.

Objective:
[Define desired end state, not instructions]

Constraints:
- Preserve existing data
- Standardize formats
- No duplicates

Output:
- Files created or modified
- Organized folder structure
- Index or summary if needed
```

---

## High-Value Cowork Prompts

### 1. File System Automation

```text
I have unstructured files in this folder.

End state:
- Organized by category and date
- Consistent naming convention: [type]_[date]_[descriptor]
- Duplicate files removed
- Summary index created

Execute fully.
```

---

### 2. Data Extraction Pipeline

```text
Input:
Multiple PDF and CSV files in this folder.

End state:
- Extract structured data fields
- Normalize formats (YYYY-MM-DD, currency, etc.)
- Merge into one dataset
- Output as clean CSV + summary report

Execute end-to-end.
```

---

### 3. Research Compilation

```text
Input:
Documents in this folder.

End state:
- Extract key insights
- Identify patterns and contradictions
- Produce structured report with sections:
  - themes
  - statistics
  - conclusions

Save as markdown file.
```

---

# 2. Codex / AGENTS.md Prompt (Repo + Code Execution)

## AGENTS.md (für Codex, Cursor, etc.)

:::writing{variant="standard" id="66321"}
You are a coding agent operating inside a real codebase.

## Core Behavior

You do not jump into coding immediately.

You must follow this strict loop:

1. PLAN
2. EXPLORE
3. TEST
4. IMPLEMENT
5. VERIFY

---

## Phase 1: Plan

- Understand the task fully
- Identify impacted files
- Estimate complexity
- Define step-by-step plan

---

## Phase 2: Explore

- Search codebase for relevant functions, classes, patterns
- Verify assumptions before using them
- Do not invent APIs or structures

---

## Phase 3: Test (mandatory)

- Write failing tests first
- Tests must validate real behavior (not superficial checks)
- Cover edge cases and side effects

---

## Phase 4: Implement

- Write minimal code required to pass tests
- Avoid over-engineering
- Follow existing patterns

---

## Phase 5: Verify

- Ensure all tests pass
- Check for regressions
- Validate integration points

---

## Coding Rules

- Never hallucinate functions or imports
- Reuse existing abstractions
- Keep changes minimal and localized
- Maintain consistency with project style

---

## Output Format

Always structure output as:

1. Plan
2. Files to modify
3. Tests
4. Implementation
5. Validation summary

---

## Failure Handling

If blocked:
- state exact issue
- propose next concrete step

---

## Objective

Deliver working, tested, minimal code changes aligned with the existing system.
:::

---

## Codex Task Prompt Template

```text
Context:
This is a production codebase.

Task:
[Describe feature or bug]

Requirements:
- minimal diff
- no breaking changes
- test coverage required

Output format:
- plan
- affected files
- tests
- implementation
```

---

## High-Value Codex Prompts

### 1. Feature Implementation

```text
Add feature:

[describe feature]

Constraints:
- follow existing architecture
- no new abstractions unless required
- include tests

Output:
- plan
- diff
- tests
```

---

### 2. Bug Fix (robust)

```text
Fix bug:

[describe issue]

Requirements:
- reproduce with failing test
- identify root cause
- fix with minimal change
- verify no regressions

Output:
- root cause
- failing test
- fix
- validation
```

---

### 3. Refactoring

```text
Refactor:

[target module]

Goals:
- improve readability
- reduce duplication
- maintain behavior

Constraints:
- no functional changes
- tests must remain valid

Output:
- plan
- changes
- validation
```

---

# Systematische Unterschiede

| Dimension        | Cowork                          | Codex                          |
|-----------------|--------------------------------|--------------------------------|
| Fokus           | Files / Outcomes               | Code / Repo                    |
| Prompt-Stil     | Outcome-first                  | Constraint-first               |
| Execution       | direkt                         | iterativ                       |
| Risiko          | Datenverlust                   | Regression                     |
| Kontrolle       | Struktur & Format              | Tests & Diff                   |

---

# Ergebnis

- Cowork-Prompts → deterministische Execution auf Filesystem  
- Codex-Prompts → reproduzierbare Softwareentwicklung  
- Beide zusammen → vollständiger AI-Agent-Stack (Operate + Build)

### 7. Benutzer

ich habe die Dateistruktur mit claude work angelegt

### 8. Assistent

Status: Struktur vorhanden. Nächster Engpass: **leere Architektur ohne funktionale Orchestrierung**.

---

# Zielzustand (nächster Schritt)

Agent muss **End-to-End laufen**:

```txt
Input → Planner → Tool/LLM → Memory → Output
```

---

# Implementierungsreihenfolge (kritischer Pfad)

## 1. Minimaler Agent Loop

**Datei:** `agent/core/agent.py`

```python
class Agent:
    def __init__(self, planner, executor, memory):
        self.planner = planner
        self.executor = executor
        self.memory = memory

    def run(self, task: str):
        state = {
            "task": task,
            "steps": [],
            "done": False
        }

        for _ in range(10):  # max steps
            plan = self.planner.plan(state)

            result = self.executor.execute(plan, state)

            state["steps"].append(result)

            if result.get("done"):
                state["done"] = True
                return result["output"]

        return "Task not completed"
```

---

## 2. Planner (Decision Engine)

**Datei:** `agent/core/planner.py`

Zweck: Entscheidung → LLM vs Tool

```python
class Planner:
    def __init__(self, llm):
        self.llm = llm

    def plan(self, state):
        prompt = f"""
        Task: {state['task']}
        Steps so far: {state['steps']}

        Decide next action:
        - respond
        - use_tool

        Output JSON:
        {{ "action": "...", "tool": "...", "input": "..." }}
        """

        return self.llm.generate(prompt)
```

---

## 3. Executor (Action Layer)

**Datei:** `agent/core/executor.py`

```python
class Executor:
    def __init__(self, tools, llm):
        self.tools = tools
        self.llm = llm

    def execute(self, plan, state):
        if plan["action"] == "respond":
            output = self.llm.generate(plan["input"])
            return {"output": output, "done": True}

        if plan["action"] == "use_tool":
            tool = self.tools.get(plan["tool"])
            result = tool.run(plan["input"])
            return {"output": result, "done": False}
```

---

## 4. Tool Registry

**Datei:** `agent/tools/registry.py`

```python
class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name, tool):
        self.tools[name] = tool

    def get(self, name):
        return self.tools[name]
```

---

## 5. Base Tool

**Datei:** `agent/tools/base_tool.py`

```python
class BaseTool:
    name = "base"

    def run(self, input_data):
        raise NotImplementedError
```

---

## 6. Beispiel Tool

**Datei:** `agent/tools/calculator.py`

```python
from .base_tool import BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"

    def run(self, input_data):
        try:
            return str(eval(input_data))
        except Exception as e:
            return str(e)
```

---

## 7. LLM Provider (Minimal)

**Datei:** `llm/providers/openai.py`

```python
from openai import OpenAI

class OpenAIProvider:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
```

---

## 8. Memory (Minimal Stub)

**Datei:** `memory/short_term/buffer.py`

```python
class ShortTermMemory:
    def __init__(self):
        self.data = []

    def add(self, item):
        self.data.append(item)

    def get(self):
        return self.data
```

---

# Bootstrap Script

**Datei:** `scripts/run_agent.py`

```python
from agent.core.agent import Agent
from agent.core.planner import Planner
from agent.core.executor import Executor

from agent.tools.registry import ToolRegistry
from agent.tools.calculator import CalculatorTool

from llm.providers.openai import OpenAIProvider

def main():
    llm = OpenAIProvider(api_key="YOUR_KEY")

    planner = Planner(llm)

    tools = ToolRegistry()
    tools.register("calculator", CalculatorTool())

    executor = Executor(tools, llm)

    agent = Agent(planner, executor, None)

    result = agent.run("What is 25 * 12?")

    print(result)

if __name__ == "__main__":
    main()
```

---

# Erwartetes Verhalten

```txt
Input: "What is 25 * 12?"
→ Planner: use_tool(calculator)
→ Executor: 300
→ Planner: respond
→ Output: 300
```

---

# Kritische Schwächen (jetzt)

1. Kein JSON Parsing → instabil  
2. Kein Tool Schema → falsche Inputs  
3. Kein Memory → kein Kontext  
4. Kein Retry / Error Handling  
5. eval() unsicher  

---

# Nächster Ausbau (priorisiert)

```txt
1. JSON enforced outputs (pydantic)
2. Tool schemas (input/output validation)
3. Step limiter + loop detection
4. Memory integration in planner prompt
5. Replace eval() with safe parser
6. Add logging (decision trace)
7. Add API layer
```

---

# Entscheidender Punkt

Du hast jetzt:

```txt
Struktur ✔
Agent Loop ✔
Tool Execution ✔
LLM Integration ✔
```

Fehlt:

```txt
Stabilität + Kontrolle + Skalierung
```

Das ist der Übergang von “Demo-Agent” → “echtes System”.

### 9. Benutzer

weiter

### 10. Assistent

# Nächster Schritt: Stabilisierung des MVP

## Ziel

Demo-Agent → kontrollierbarer Agent.

Priorität:

```txt
1. sichere Calculator-Ausführung
2. JSON-validierter Planner
3. Tool-Schema
4. Executor-Fehlerbehandlung
5. Logging
6. API-Endpunkt
```

---

# Prompt für Claude Work

Kopiere das in Claude Work:

```text
Implementiere die nächste stabile Version des AI-Agent-Systems.

Ziel:
Der Agent soll nicht mehr mit rohen Strings und unsicheren Tool-Aufrufen arbeiten, sondern mit validierten Datenmodellen, sicherem Tool-System und sauberem Error Handling.

Aufgaben:

1. Erstelle Pydantic-Modelle:
- PlanAction
- ToolCall
- ToolResult
- AgentState
- AgentStep

Datei:
agent/core/state.py

2. Ersetze den unsicheren Calculator mit sicherem AST-basiertem Parser.
Keine Verwendung von eval().

Datei:
agent/tools/calculator.py

3. Erweitere BaseTool:
- name
- description
- input_schema
- output_schema
- run()
- validate_input()

Datei:
agent/tools/base_tool.py

4. Erweitere ToolRegistry:
- register()
- get()
- list_tools()
- exists()
- schema_summary()

Datei:
agent/tools/registry.py

5. Erweitere Planner:
- LLM muss JSON ausgeben
- JSON muss geparst werden
- ungültiges JSON führt zu fallback response
- Tool-Auswahl muss gegen Registry validiert werden

Datei:
agent/core/planner.py

6. Erweitere Executor:
- Tool existiert?
- Input valide?
- Tool-Ausführung erfolgreich?
- Fehler sauber als ToolResult zurückgeben
- niemals crashen bei Tool-Fehlern

Datei:
agent/core/executor.py

7. Erweitere Agent Loop:
- max_steps aus config
- loop detection
- state tracking
- final response generation

Datei:
agent/core/agent.py

8. Ergänze Logging:
- planned action
- tool call
- tool result
- final output

Datei:
config/logging.yaml
Optional:
agent/core/logger.py

9. Aktualisiere scripts/run_agent.py:
- lauffähiger Test mit calculator
- Beispiel: "What is 25 * 12 + 5?"

10. Ergänze Tests:
- test_calculator.py
- test_registry.py
- test_executor.py
- test_planner.py
- test_agent.py

Akzeptanzkriterien:
- Kein eval()
- Agent läuft end-to-end
- Ungültige Tool-Namen crashen nicht
- Ungültiges JSON crasht nicht
- Calculator erlaubt nur sichere mathematische Operationen
- Tests laufen erfolgreich
- Code bleibt modular und minimal
```

---

# Danach erwartete Zielstruktur-Erweiterung

```txt
agent/
  core/
    agent.py
    planner.py
    executor.py
    state.py
    errors.py
    logger.py

  tools/
    base_tool.py
    registry.py
    calculator.py

tests/
  test_agent.py
  test_calculator.py
  test_executor.py
  test_planner.py
  test_registry.py
```

---

# Sicherheitsregel für Calculator

Erlaubt:

```txt
+  -  *  /  **  %  ()
Zahlen
```

Verboten:

```txt
imports
Variablen
Funktionen
Dateizugriff
Attribute
Strings
Listen
Dictionaries
```

---

# Erwarteter Agent-Ablauf nach Umsetzung

```txt
User Input:
"What is 25 * 12 + 5?"

Planner Output:
{
  "action": "use_tool",
  "tool": "calculator",
  "input": {
    "expression": "25 * 12 + 5"
  }
}

Executor:
calculator.run()

ToolResult:
{
  "success": true,
  "output": "305",
  "error": null
}

Agent:
final response = "305"
```

---

# Nächster Block danach

Nach erfolgreicher Umsetzung:

```txt
Phase 3:
Memory + API + Workflows
```

Dann wird aus dem Agenten ein nutzbares System statt nur ein lokaler Prototyp.

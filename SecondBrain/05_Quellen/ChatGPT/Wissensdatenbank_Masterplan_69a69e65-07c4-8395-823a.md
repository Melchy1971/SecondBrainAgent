---
title: "Wissensdatenbank Masterplan"
type: chatgpt_conversation
source: chatgpt
source_id: "69a69e65-07c4-8395-823a-fc019acdb236"
created: 2026-03-03
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


# Wissensdatenbank Masterplan

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `69a69e65-07c4-8395-823a-fc019acdb236`
- Nachrichten: 14

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ich möchte eine wissensdatenbank aufbauen mit einem front und einem backend. hierzu verwende ich vsc + chatgpt pro, codex.und für das frontend mit lovable.dev sowie github copilot. neoj4 als db. erstelle mir einen masterplan den ich nach notion sichere und erstelle mir die passenden prompts. beginne mit dem front end über loveable

### 2. Assistent

## Masterplan Wissensdatenbank (Front + Back, Neo4j) — Notion-ready

### 0) Zielbild
- **Outcome**: Wissensdatenbank mit graphbasierter Modellierung (Neo4j), sauberer Suche, Versionierung, Quellen/Attribution, Rollen/Rechten, nachvollziehbaren Beziehungen zwischen Artikeln/Begriffen/Prozessen.
- **Non-Goals (jetzt)**: Volltext-„KI-Antwortmaschine“, Enterprise-SSO, Mandantenfähigkeit, Offline-first.
- **Leitprinzipien**
  - Graph zuerst: Beziehungen sind Produktkern.
  - Strikte Trennung: Frontend (UI/UX) ↔ API ↔ DB.
  - Observability, Migrationspfad, Security-by-default.

---

## 1) Systemarchitektur (robust, skalierbar)
### Komponenten
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind + Component Library
- **Backend**: Node.js (NestJS oder Fastify) + TypeScript
- **DB**: Neo4j (Aura oder self-hosted)
- **Search**: Start mit Neo4j Fulltext Index; optional später Meilisearch/Elastic
- **Auth**: NextAuth (Frontend) + JWT/Session; Backend prüft Token
- **Storage für Anhänge**: S3-kompatibel (optional Phase 2)
- **CI/CD**: GitHub Actions, Preview Deployments

### Schnittstellen
- **REST** (start) oder **GraphQL** (später). Start: REST, weil schneller zu implementieren und debuggen.
- **API Ressourcen**
  - `/auth/*`
  - `/nodes` (CRUD)
  - `/edges` (CRUD)
  - `/search`
  - `/tags`
  - `/sources`
  - `/audit`

---

## 2) Domänenmodell (Neo4j)
### Knoten (Nodes)
- `Article` (Wissensartikel)
- `Concept` (Begriff/Definition)
- `Process` (Prozess, SOP)
- `System` (Tool/System)
- `Person` (Owner/Expert)
- `Source` (URL/Dokument/Referenz)
- `Tag`

### Beziehungen (Edges)
- `(:Article)-[:MENTIONS]->(:Concept)`
- `(:Process)-[:USES]->(:System)`
- `(:Article)-[:RELATES_TO]->(:Article)`
- `(:Article)-[:SOURCED_FROM]->(:Source)`
- `(:Person)-[:OWNS]->(:Article|:Process)`
- `(:Article|:Concept|:Process)-[:TAGGED_WITH]->(:Tag)`

### Kernattribute (Beispiele)
- `id` (UUID), `title`, `slug`, `summary`, `contentMarkdown`, `status` (draft|published|archived)
- `createdAt`, `updatedAt`, `createdBy`, `updatedBy`
- `version` (int), `visibility` (private|team|public)
- `Source`: `type` (url|pdf|note), `uri`, `publisher`, `retrievedAt`

### Indizes / Constraints
- Unique: `id`, `slug`
- Fulltext: `title`, `summary`, `contentMarkdown`

---

## 3) Produktumfang (MVP → V1)
### MVP (funktional, schnell)
- Auth (Login) + Rollen: `admin`, `editor`, `reader`
- CRUD für `Article`, `Concept`, `Process`
- Kantenmanagement: Beziehungen hinzufügen/entfernen
- Suche (Neo4j Fulltext) + Filter (Typ, Tag, Status)
- Detailseiten mit „Backlinks“ (eingehende Kanten)
- Basic Audit-Log (wer hat was geändert)

### V1 (wertsteigernd)
- Versionierung (diff / restore)
- Quellen-Workflow (Source Pflicht für „published“)
- Graph-Visualisierung (mini graph explorer)
- Import (Markdown/CSV)
- Notifications (optional)

---

## 4) Arbeitsmodus (Tooling)
- **VS Code**: Repo, Scripts, Env, Debug
- **ChatGPT Pro**: Architekturentscheidungen, Prompting, Reviews
- **Codex**: Implementationsblöcke, Tests, Refactors
- **GitHub Copilot**: In-IDE Ergänzungen
- **lovable.dev**: UI-Skeleton + Pages + Components

---

# Phase 1 — Frontend mit lovable.dev (Startpunkt)

## A) Frontend-Blueprint (Information Architecture)
### Routen
- `/login`
- `/` Dashboard (recent, pinned, drafts)
- `/search` (query + filters)
- `/articles` Liste
- `/articles/new` Editor
- `/articles/[slug]` Detail
- `/concepts` + `/concepts/[slug]`
- `/processes` + `/processes/[slug]`
- `/graph` Graph Explorer (V1; MVP optional read-only)
- `/admin` (roles, tags)

### UI-Bausteine
- App Shell: Sidebar + Topbar + Command Palette (optional)
- Search Bar: global, debounced
- Filter Chips: Typ/Tag/Status
- Editor: Markdown + Preview
- Relation Manager: „Add relation“ modal
- Backlinks Panel: eingehende Beziehungen
- Activity Panel: letzte Änderungen

---

## B) Definition of Done (Frontend MVP)
- Responsive Layout
- State Management sauber (React Query/SWR)
- Form-Validation
- Auth Guard (Routes geschützt)
- API-Client zentral (typed)
- Fehlerzustände, Empty States
- Minimal Design System (Button/Input/Modal/Badge/Table)

---

# Prompts — lovable.dev (Frontend zuerst)

## 1) Projekt-Setup Prompt (lovable)
**Ziel:** Next.js + TS + Tailwind + App Shell + Routing Skeleton + Dummy Data Provider.

```text
Build a Next.js (App Router) + TypeScript + Tailwind frontend for a knowledge graph wiki.

Requirements:
- App shell with left sidebar navigation: Dashboard, Search, Articles, Concepts, Processes, Graph, Admin
- Topbar with global search input and user menu
- Pages for each route with placeholder content and consistent layout
- Reusable UI components: Button, Input, Modal, Badge, Table, Card, Tabs
- Use a typed API client layer (no real backend yet): create /lib/api.ts with functions:
  - search(query, filters)
  - listArticles(), getArticle(slug), createArticle(payload), updateArticle(slug,payload)
  - listConcepts(), getConcept(slug)
  - listProcesses(), getProcess(slug)
- Add a mock adapter inside api.ts returning deterministic dummy data
- Implement basic loading/empty/error states per page
- No authentication logic yet, but structure routes to allow guards later
Deliver: complete project structure, pages, and components.
```

## 2) Search UX Prompt (lovable)
**Ziel:** Suchseite mit Filtern, Ergebnislisten, Tastaturbedienung.

```text
Implement the /search page UX:

- Global query input (synced with URL ?q=)
- Filters: entityType (Article|Concept|Process), status (draft|published|archived), tag
- Debounced search request via api.search
- Results list grouped by entityType with counts
- Each result card shows: title, summary, tags, lastUpdated
- Keyboard navigation: up/down selects, enter opens
- Empty states: no query, no results
- Error state: retry button

Use the existing api client (mock). Keep styling minimal and consistent with the design system.
```

## 3) Article Detail + Backlinks Prompt (lovable)
**Ziel:** Detailseite als „Knowledge Hub“ inkl. Beziehungen.

```text
Implement /articles/[slug]:

- Header: title, status badge, last updated, owner (placeholder)
- Tabs: Content (render markdown), Relations, Activity
- Relations tab:
  - Outgoing relations list (type + target)
  - Incoming relations ("Backlinks") list
  - "Add relation" modal with fields: relationType, targetType, targetSearch
  - Use mock api functions; persist in mock store in-memory for session
- Activity tab: show last changes (mock)

Ensure good empty states and clear separation of components.
```

## 4) Markdown Editor Prompt (lovable)
**Ziel:** New/Edit Page für Artikel.

```text
Implement /articles/new and /articles/[slug]/edit:

- Form fields: title, summary, status, tags (multi), contentMarkdown
- Markdown editor with split preview
- Validation: title required, content length > 50 for published
- Save actions:
  - Save draft
  - Publish (only if validation passes)
- After save: navigate to detail page
- Use api.createArticle / api.updateArticle (mock)

Keep components reusable for later backend integration.
```

---

# Prompts — GitHub Copilot (in VS Code)
## Copilot Prompt Snippets (kurz, direkt)
1) API Client Typing
```text
Create TypeScript types for Article, Concept, Process, Tag, Relation, SearchFilters, SearchResult. Ensure discriminated unions for entityType.
```

2) React Query Integration
```text
Refactor api calls to React Query hooks: useSearch, useArticles, useArticle(slug), useCreateArticle, useUpdateArticle. Add query keys and invalidation.
```

3) Route Guard Skeleton
```text
Add an auth guard pattern for Next.js App Router: middleware.ts placeholder + client-side hook useAuth() returning {user, role, loading}. Block /admin for non-admin.
```

---

# Prompts — Codex (Implementation Blöcke)
## 1) Konsistentes Mock-Backend im Frontend
```text
Implement an in-memory mock store for entities and relations in /lib/mockStore.ts.
Requirements:
- Seed deterministic data
- CRUD for Article/Concept/Process
- Create/delete relations with validation (no self-loop unless allowed)
- Fulltext-like search over title/summary/content (simple scoring)
- Expose functions used by /lib/api.ts
Add minimal unit tests for store logic.
```

## 2) UI Component Hardening
```text
Audit UI components for accessibility:
- Buttons have type, aria where needed
- Modals trap focus, close on ESC, click outside
- Inputs labeled
Implement fixes and add a small accessibility checklist in /docs/a11y.md
```

---

# Notion-Struktur (zum 1:1 Einfügen)
## Seite: „Wissensdatenbank — Masterplan“
- Zielbild
- Architektur
- Domänenmodell (Nodes/Edges)
- MVP Scope + V1 Scope
- Security/Compliance (kurz)
- Roadmap Phasen
- Prompt-Bibliothek (lovable / Copilot / Codex)
- Entscheidungsliste (Tech Choices + Gründe)

## Seite: „Frontend — Sprintboard“
- Sprint 1: App Shell + Routing + Design System
- Sprint 2: Search + Lists + Detailseiten
- Sprint 3: Editor + Relations + Backlinks
- Sprint 4: Auth Guard Skeleton + Error Hardening

## Seite: „API Contract Draft“
- Endpoints + Request/Response Types
- Fehlercodes
- Pagination/Filtering

---

# Frontend-Backlog (MVP, priorisiert)
1. App Shell + Navigation + Layout
2. Search Page (URL-synced, Filter, Results)
3. Entity Lists (Articles/Concepts/Processes)
4. Article Detail (Markdown Render) + Backlinks Panel
5. Article Create/Edit (Markdown Editor + Validation)
6. Relations CRUD (Modal + Lists)
7. State Layer (React Query)
8. Route Guards Skeleton
9. UI A11y pass + empty/error states

---

## Implementationskonsequenzen / Risiken (Frontend-Start)
- **Graph-UI**: hoher Aufwand, schnell ausufernd → MVP: Relations listen + Backlinks; Graph Explorer erst V1.
- **Markdown Editor**: Feature-Creep (Uploads, mentions, tables) → MVP: plain markdown + preview.
- **Auth**: frühe Integration erzeugt Reibung → Skeleton jetzt, echte Auth wenn Backend steht.
- **Typed Contract**: ohne Backend driftet UI schnell → API Contract Draft parallel pflegen.

---

### 3. Benutzer

verwende noch fastmcp

### 4. Assistent

## Erweiterung Masterplan: FastMCP als Tool-Gateway zwischen LLM und Backend

### Einordnung
- **FastMCP** = Framework zum Bauen von **MCP-Servern** (Model Context Protocol), die Tools/Datenzugriffe standardisiert für LLM-Hosts bereitstellen. citeturn0search0turn0search1turn0search14
- Konsequenz: Neben klassischer REST-API baust du ein **MCP-Gateway**, das „LLM-fähige“ Operationen (Search, Create, Link, Explain, Validate) kapselt.
- Vorteil: Tool-Schnittstelle ist semantisch, typisiert, sicherheitsfähig (Auth Provider existieren). citeturn0search5turn0search10

---

## Zielarchitektur (mit FastMCP)
### Komponenten
1) **Frontend (lovable.dev)**: Next.js UI für Menschen  
2) **Backend REST API**: stabile Produkt-API (für Frontend)  
3) **FastMCP Server (Python)**: Tool-API (für ChatGPT/Codex/Agenten)  
4) **Neo4j**: System of Record

### Schnittstellenregeln
- Frontend → **REST** (deterministisch, versioniert, caching-freundlich)
- LLM-Clients → **MCP** (tooling/automation/assistierte Workflows)
- REST und MCP nutzen **dieselbe Service-Schicht / DB-Layer**, aber exponieren unterschiedliche „Contract-Sichten“

---

## MVP Scope mit FastMCP (konkret)
### MCP Tools (Minimum Set)
- `search_entities(query, filters)` → Trefferliste (typed)
- `get_entity(entity_type, slug|id)` → Detail + Relations
- `upsert_article(payload)` → Draft/Publish Logik serverseitig
- `create_relation(from_id, rel_type, to_id)` / `delete_relation(...)`
- `suggest_relations(entity_id)` → heuristisch (ohne „KI“, rein regelbasiert)
- `validate_publish(article_id)` → Policy Check (Source Pflicht, Mindestlänge, etc.)

Warum: Das sind die Operationen, die LLM-gestützt Arbeit sparen, ohne Produkt-API zu verkomplizieren.

---

## Security / Failure Modes (FastMCP-spezifisch)
- **Prompt Injection via Content**: MCP-Tools strikt whitelisten; keine „execute arbitrary cypher“.  
- **Least Privilege**: MCP-Server Rollen/Scopes (read vs write).  
- **Auditability**: Jede MCP-Tool-Ausführung schreibt Audit Event.  
- **Determinismus**: Tools geben strukturierte JSON Ergebnisse; kein „best-effort Text“.  
- **Rate Limits**: pro Token/User.

---

## Implementationsplan (nur die Änderungen durch FastMCP)
### Phase 1 (parallel zum Frontend)
- Frontend bleibt unverändert (mock api).
- Zusätzlich: FastMCP Server Skeleton + Neo4j Connector + Tool Contracts.

### Phase 2 (Backend anschließen)
- REST API + MCP Server nutzen denselben Neo4j-Service.
- Frontend mock → REST umstellen.
- MCP Tools an echte Services binden.

---

# Prompts — FastMCP Setup (Codex / ChatGPT Pro)

## 1) FastMCP Server Skeleton
```text
Implement a Python FastMCP server named "kb".

Requirements:
- Project layout:
  - mcp_server/app.py (FastMCP instance + tool registrations)
  - mcp_server/neo4j_client.py (driver init, session helpers)
  - mcp_server/services/kb_service.py (domain functions)
  - mcp_server/schemas.py (pydantic models for inputs/outputs)
- Tools:
  - search_entities(query:str, entity_type:Optional[str], status:Optional[str], tag:Optional[str]) -> SearchResponse
  - get_entity(entity_type:str, id_or_slug:str) -> EntityResponse
  - upsert_article(payload:ArticleUpsert) -> ArticleResponse
  - create_relation(from_id:str, rel_type:str, to_id:str) -> RelationResponse
  - delete_relation(from_id:str, rel_type:str, to_id:str) -> DeleteResponse
- No arbitrary Cypher execution tool.
- Env vars: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
- Add basic logging and structured errors.
- Add a minimal test suite for service functions (mock neo4j).
Deliver runnable code and instructions to start the server.
```
Begründung: FastMCP nutzt Typen/Docstrings zur Tool-Definition; implementiere strikt typisiert. citeturn0search4turn0search0

## 2) Neo4j Query Policy (Safety)
```text
Add a query policy layer:
- Only allow predefined parameterized Cypher queries stored in kb_service.py
- Enforce max result limits and timeouts
- Validate rel_type against an enum
- Validate entity_type against an enum
Add unit tests for validation failures.
```

## 3) Auth für MCP (optional früh, aber sauber vorbereitet)
```text
Add authentication to FastMCP server using a supported auth provider (GitHub OAuth or a simple token-based middleware).
- If GitHub OAuth is implemented, include configuration stubs and docs.
- Ensure tools check role scopes (reader/editor/admin) before write operations.
```
FastMCP hat dokumentierte Auth Provider/Integrationen. citeturn0search5turn0search10

---

# Prompts — lovable.dev (Frontend-Erweiterung für MCP-Workflow, ohne direkte MCP-Anbindung)
Lovable bleibt UI; MCP ist primär für LLM-Clients. Frontend bekommt nur UI, die später sowohl REST als auch MCP-gestützte Aktionen abbilden kann.

## 1) “Assist” UI Slots (ohne KI-Implementation)
```text
Extend the Article detail and editor pages with "Assist" panels (UI only):

- On /articles/[slug], add a right-side panel "Assist" containing:
  - Suggested relations (placeholder list)
  - Quick actions: "Generate summary", "Find duplicates", "Suggest tags" (disabled buttons)
- On editor pages, add a "Validation" box:
  - Shows publish readiness checks (source attached, min length, title present)
  - Use mock data for now

Do NOT integrate any AI SDK. Only prepare UI structure and component interfaces so the backend can later populate them.
```

---

## Contract-Entscheidung (wichtig, damit es nicht driftet)
- **REST Contract** = produktiv, stabil, UI-first
- **MCP Contract** = tool-first, LLM ergonomics
- Beide teilen **Schemas** (OpenAPI/Pydantic/TS types) → Single Source of Truth.

citeturn0search0turn0search1turn0search14

### 5. Assistent

# Wissensdatenbank — Masterplan v2 (mit FastMCP)  
**Statusmarkierung:**  
- ✅ Implementiert  
- 🟡 In Arbeit / vorbereitet  
- ⬜ Geplant  

---

# 1. Zielbild (unverändert, präzisiert)

Graphbasierte Wissensplattform mit:

- Neo4j als System of Record  
- REST API für Frontend  
- FastMCP-Server für LLM-/Tool-Zugriffe  
- Strikte Trennung von UI, Produkt-API und Tool-API  
- Auditierbarkeit, deterministische Queries, Security-by-default  

---

# 2. Zielarchitektur (aktualisiert)

```
[Frontend - Next.js]
        ↓ REST
[Backend API - Node/Nest]
        ↓ Service Layer
[Neo4j]

[FastMCP Server - Python]
        ↓ Shared Service Layer / Neo4j
```

## 2.1 Komponentenstatus

| Komponente | Status | Bemerkung |
|------------|--------|-----------|
| Frontend Skeleton (lovable) | 🟡 | App Shell + Routing geplant |
| Mock API Layer | 🟡 | api.ts vorgesehen |
| Neo4j Modell | ⬜ | Noch nicht implementiert |
| REST Backend | ⬜ | Noch nicht gestartet |
| FastMCP Server | ⬜ | Konzept + Prompt definiert |
| Auth | ⬜ | Nur Skeleton geplant |

---

# 3. Domänenmodell (Neo4j)

## 3.1 Node-Typen

- Article  
- Concept  
- Process  
- System  
- Person  
- Source  
- Tag  

Status:  
- ⬜ Implementierung in Neo4j  
- 🟡 Schema definiert  

## 3.2 Relationen

- MENTIONS  
- RELATES_TO  
- USES  
- OWNS  
- TAGGED_WITH  
- SOURCED_FROM  

Status:  
- ⬜ Constraints / Indizes  
- 🟡 Relationen-Design finalisiert  

---

# 4. Frontend (lovable.dev) — Phase 1

## 4.1 Informationsarchitektur

Routen:

- `/` Dashboard  
- `/search`  
- `/articles`  
- `/articles/new`  
- `/articles/[slug]`  
- `/concepts`  
- `/processes`  
- `/graph`  
- `/admin`  

Status:  
- 🟡 Routing-Plan erstellt  
- ⬜ Implementiert  

---

## 4.2 Design System

Komponenten:

- Button  
- Input  
- Modal  
- Badge  
- Card  
- Table  
- Tabs  

Status:  
- 🟡 Konzeption  
- ⬜ Implementiert  

---

## 4.3 Artikel-Detailseite

Funktionen:

- Markdown Rendering  
- Relations Tab  
- Backlinks  
- Activity Tab  
- Assist Panel (UI-only)  

Status:  
- 🟡 Struktur spezifiziert  
- ⬜ Implementiert  

---

## 4.4 Editor

Funktionen:

- Markdown Editor  
- Draft/Publish  
- Validierung  
- Tags Multi-Select  

Status:  
- 🟡 Spezifiziert  
- ⬜ Implementiert  

---

# 5. API-Schicht

## 5.1 REST API

Ressourcen:

- /articles  
- /concepts  
- /processes  
- /relations  
- /search  

Status:  
- ⬜ Nicht implementiert  
- 🟡 Contract Draft vorbereitet  

---

# 6. FastMCP Integration

## 6.1 Rolle im System

FastMCP = Tool-Gateway für:

- LLM-gestützte Automatisierung  
- Strukturierte Tool-Calls  
- Kein direktes Cypher-Expose  

Trennung:

- REST → Produkt-API  
- MCP → Tool-API  

---

## 6.2 MCP Tools (definiert)

| Tool | Status |
|------|--------|
| search_entities | 🟡 Spezifiziert |
| get_entity | 🟡 Spezifiziert |
| upsert_article | 🟡 Spezifiziert |
| create_relation | 🟡 Spezifiziert |
| delete_relation | 🟡 Spezifiziert |
| validate_publish | 🟡 Spezifiziert |
| suggest_relations | 🟡 Spezifiziert |

Implementierung:  
- ⬜ Noch nicht begonnen  

---

## 6.3 Sicherheitsregeln

- Keine freie Cypher-Ausführung  
- Enum-Validierung für entity_type und rel_type  
- Max-Result Limits  
- Audit-Logging  
- Role Scope Enforcement  

Status:  
- 🟡 Design definiert  
- ⬜ Nicht implementiert  

---

# 7. Systemlogik (Entscheidungen)

## 7.1 REST vs MCP

REST:
- Deterministisch  
- Versionierbar  
- UI-first  

MCP:
- Tool-orientiert  
- LLM-optimiert  
- Typed Schemas  

Shared:
- Service Layer  
- Domain Validation  

Status:  
- ✅ Architekturentscheidung getroffen  

---

# 8. Roadmap

## Phase 1 — Frontend Skeleton
- App Shell  
- Routing  
- Mock API  
- Search UI  
- Detailseiten  
Status: 🟡

## Phase 2 — Neo4j + REST
- Constraints  
- CRUD  
- Search  
- Relations  
Status: ⬜

## Phase 3 — FastMCP Server
- Tool Definition  
- Service Binding  
- Auth  
- Audit  
Status: ⬜

## Phase 4 — Assist Features
- Relation Suggestions  
- Validation Engine  
- Versioning  
Status: ⬜

---

# 9. Implementierte Inhalte (aktuell real)

✅ Architekturentscheidung REST + MCP Trennung  
✅ Domänenmodell konzeptionell definiert  
✅ Tool-Schnittstellen (MCP) spezifiziert  
✅ Frontend-IA definiert  
✅ Prompt-Bibliothek für lovable / Codex / Copilot erstellt  

Noch keine produktive Codebasis vorhanden.

---

# 10. Nächster Engpass

Bottleneck:

Fehlende reale Codebasis →  
Risiko: Konzept driftet von Implementation.

Systemisch sinnvoller nächster Schritt:

1. Frontend Skeleton generieren (lovable)  
2. Mock Store stabilisieren  
3. Danach erst Neo4j anbinden  

Reihenfolge nicht invertieren, sonst UI-Contract instabil.

---

Masterplan aktualisiert.

### 6. Benutzer

aktualisiere den masterplan und kennzeichne implementierte inhalte

### 7. Benutzer

weiter mit 1.

### 8. Assistent

# Phase 1 — Frontend Skeleton (Schritt 1)

## 1.1 Zielzustand nach Schritt 1
- Next.js (App Router) + TypeScript + Tailwind
- App Shell (Sidebar + Topbar)
- Routing-Skeleton für alle MVP-Seiten
- Zentrales typed API-Layer `/lib/api.ts` mit Mock-Adapter
- UI-Basiskomponenten (Button/Input/Modal/Badge/Card/Table/Tabs)
- Standard-States: loading / empty / error je Seite

**Output-Artefakte**
- `apps/web` lauffähig lokal
- Keine Auth, keine Backend-Anbindung, keine Neo4j

---

## 1.2 Repo-Layout (Soll)
```
repo/
  apps/
    web/                      # Next.js Frontend
      app/
        layout.tsx
        page.tsx
        login/page.tsx
        search/page.tsx
        articles/page.tsx
        articles/new/page.tsx
        articles/[slug]/page.tsx
        concepts/page.tsx
        concepts/[slug]/page.tsx
        processes/page.tsx
        processes/[slug]/page.tsx
        graph/page.tsx
        admin/page.tsx
      components/
        shell/Sidebar.tsx
        shell/Topbar.tsx
        shell/AppShell.tsx
        ui/Button.tsx
        ui/Input.tsx
        ui/Modal.tsx
        ui/Badge.tsx
        ui/Card.tsx
        ui/Table.tsx
        ui/Tabs.tsx
      lib/
        types.ts
        api.ts
        mockStore.ts
        routes.ts
      styles/
        globals.css
```

---

## 1.3 Implementation Checklist (DoD für Schritt 1)
### Shell + Navigation
- Sidebar-Links für: Dashboard, Search, Articles, Concepts, Processes, Graph, Admin
- Topbar: global Search Input (ohne Funktionalität außer Navigation zu `/search?q=...`)

### Pages
- Jede Route rendert konsistent in AppShell
- Pro Seite: Placeholder Heading + kurze Beschreibung + State-Komponenten

### API-Layer (Mock)
- `/lib/types.ts`: `Article | Concept | Process | Tag | Relation | SearchResult`
- `/lib/mockStore.ts`: deterministische Seed-Daten + Getter-Funktionen
- `/lib/api.ts`: typed Wrapper (später REST drop-in)

### UI Components
- Minimal, konsistent, ohne externe Abhängigkeiten
- Modal: ESC-close + backdrop-close

---

# 1.4 lovable.dev — Prompt Package (Schritt 1)

## Prompt 1: Projekt-Skeleton + Shell + Routing + UI
```text
Create a Next.js (App Router) + TypeScript + Tailwind frontend named "Knowledge Graph KB".

Implement:
- App shell layout with a left sidebar and a topbar.
- Sidebar navigation links: Dashboard (/), Search (/search), Articles (/articles), Concepts (/concepts), Processes (/processes), Graph (/graph), Admin (/admin), Login (/login).
- Topbar contains a global search input that navigates to /search?q=<value> on Enter.
- Create pages for each route with placeholder headings and consistent spacing.

Add a small design system in /components/ui:
- Button, Input, Modal (ESC + backdrop close), Badge, Card, Table, Tabs.

Add /lib/types.ts with types:
- EntityType = "article" | "concept" | "process"
- Article, Concept, Process (id, slug, title, summary, status, tags, updatedAt)
- Tag (id, name)
- Relation (fromId, toId, type)
- SearchFilters (entityType?, status?, tag?)
- SearchResult = discriminated union with entityType and entity payload

Add /lib/mockStore.ts:
- Deterministic seed data (at least 10 articles, 10 concepts, 5 processes, 10 tags, 20 relations).
- Functions: listArticles, getArticleBySlug, listConcepts, getConceptBySlug, listProcesses, getProcessBySlug, searchEntities(query, filters).

Add /lib/api.ts:
- Typed async functions that wrap mockStore and simulate network delay:
  - search(query, filters)
  - listArticles(), getArticle(slug)
  - listConcepts(), getConcept(slug)
  - listProcesses(), getProcess(slug)

Each page should call the corresponding api function and show:
- loading state
- empty state
- error state (retry button)
Use minimal, clean styling.
```

## Prompt 2: Search Page (URL-synced, Filter UI)
```text
Implement /search:

- Read query from URL parameter ?q=
- Add filters UI: entityType, status, tag
- Debounce typing (300ms) before calling api.search
- Results grouped by entityType with counts
- Result item shows title, summary, tags, updatedAt, and links to the appropriate detail route
- Empty states:
  - no query: show instructions
  - no results: show message
- Error state with retry

Use only the existing design system components.
```

---

# 1.5 VS Code / Copilot — In-Repo Prompts (Schritt 1 Härtung)

## Types (types.ts)
```text
Define discriminated unions for SearchResult and strict enums for status and entityType. Ensure every entity has {id, slug, title, summary, status, tags, updatedAt}.
```

## Mock Store (mockStore.ts)
```text
Implement deterministic seeding (no Math.random). Provide stable IDs/slugs and a simple text scoring function for searchEntities.
```

## API Wrapper (api.ts)
```text
Wrap mockStore functions in async functions with a fixed artificial delay and consistent error shape {code,message}. Add a single place to toggle between mock and real baseUrl later.
```

---

# 1.6 Abnahmekriterien (Messbar)
- `npm run dev` startet ohne Fehler
- Jede Route erreichbar, kein Layout-Bruch
- `/search?q=test` liefert deterministische Ergebnisse
- Kein `any` in Types (außer explizit begründet)
- Mock-Daten stabil zwischen Reloads

---

### 9. Benutzer

weiter mit 2.

### 10. Assistent

# Phase 1 — Frontend Skeleton (Schritt 2: Search UI + Entity Lists + Detail Read)

## 2.1 Zielzustand nach Schritt 2
- Search ist funktionsfähig (URL-synced, Filter, Gruppierung)
- Listen-Seiten für Articles/Concepts/Processes sind funktionsfähig
- Detail-Seiten (Read-only) sind funktionsfähig inkl. Backlinks (eingehende Relationen) als Liste
- Einheitliche States (loading/empty/error) über alle Seiten
- MockStore erweitert um relation-resolver (incoming/outgoing)

**Nicht enthalten (bleibt Schritt 3/4):** Edit/Create, Relation CRUD, Assist Panel.

---

## 2.2 Daten-/UI-Contract (entscheidend, damit nichts driftet)

### Entity Card (Liste + Search)
- `title`
- `summary` (truncate)
- `status` Badge
- `tags` (max 3 + “+n”)
- `updatedAt` (iso → lokal formatiert)
- Link zur Detailroute anhand `entityType`

### Detail-Ansicht (Read-only)
- Header: `title`, `status`, `updatedAt`, `tags`
- Sections:
  - Content (für Article optional; sonst Summary)
  - Outgoing Relations (type + target title + link)
  - Incoming Relations (Backlinks) (type + source title + link)

---

## 2.3 MockStore Erweiterung (Pflicht)
### Neue Funktionen
- `listRelationsForEntity(entityId): { outgoing: ResolvedRelation[], incoming: ResolvedRelation[] }`
- `resolveEntityById(entityId): { entityType, entity } | null`
- `listTags(): Tag[]`

### ResolvedRelation Typ
- `type`
- `from: { id, entityType, slug, title }`
- `to: { id, entityType, slug, title }`

**Constraints**
- Deterministisch (keine Randomness)
- Max results pro query (z. B. 50)
- Null-safe (fehlende Targets → skip oder mark as broken)

---

# 2.4 lovable.dev — Prompt Package (Schritt 2)

## Prompt 1: Entity Lists (Articles/Concepts/Processes)
```text
Extend the existing Next.js knowledge base app:

Implement list pages:
- /articles: listArticles() -> render table or cards
- /concepts: listConcepts()
- /processes: listProcesses()

Requirements:
- Each list item shows: title, summary, status badge, tags, updatedAt
- Each item links to its detail route:
  - article -> /articles/[slug]
  - concept -> /concepts/[slug]
  - process -> /processes/[slug]
- Provide consistent loading / empty / error states using shared components
- Add a small reusable component <EntityList> and <EntityCard> used across pages
- Add tag chip component used in cards
Use the existing api layer.
```

## Prompt 2: Detail Pages + Backlinks (Read-only)
```text
Implement read-only detail pages:

- /articles/[slug]
- /concepts/[slug]
- /processes/[slug]

Add to /lib/mockStore.ts and /lib/api.ts:
- listRelationsForEntity(entityId) returning outgoing + incoming relations with resolved entity titles/slugs/types

Detail page requirements:
- Header: title, status badge, updatedAt, tags
- Body:
  - For Article: render contentMarkdown if available (simple markdown render ok)
  - For Concept/Process: show summary + placeholder sections
- Relations section:
  - Outgoing relations list: relation type + target title + link
  - Incoming relations list ("Backlinks"): relation type + source title + link
- Empty states if no relations exist
Use shared UI components and keep styling consistent.
```

## Prompt 3: Search Hardening (Scoring + Grouping + Counts)
```text
Improve /search:

- Use api.search(query, filters)
- Group results by entityType with counts and section headers
- Add a small "result summary" line: total results + active filters
- Add simple relevance ordering from mockStore scoring
- Keep URL in sync with query and filters (?q=&type=&status=&tag=)
- Ensure debounce works and does not trigger on initial empty query
```

---

# 2.5 VS Code / Copilot — Prompts (Targeted)

## Relation Resolver
```text
Implement relation resolution in mockStore: given relations with fromId/toId, return resolved nodes including entityType, slug, title. Add guards for missing entities and enforce max 50 relations returned.
```

## URL Filter Sync
```text
Implement a small helper in /lib/routes.ts to read/write search params and to build entity detail URLs from {entityType, slug}.
```

## Shared State Components
```text
Create shared components: <LoadingState>, <EmptyState>, <ErrorState onRetry>. Replace ad-hoc states across pages.
```

---

# 2.6 Abnahmekriterien (Messbar)
- `/search?q=<seed-term>` zeigt Ergebnisse, gruppiert und sortiert
- Filter schreiben/lesen in URL; Reload hält Zustand
- `/articles`, `/concepts`, `/processes` listen deterministisch Seed-Daten
- Detailseiten zeigen Outgoing + Incoming Relations korrekt als Links
- Broken relations werden nicht gerendert oder sichtbar markiert (keine Crashes)
- Kein doppelter Code für loading/empty/error (shared components)

---

# 2.7 Implementierte Inhalte (Statusupdate nach Schritt 2)
- ✅ Architektur/IA/Prompt-Bibliothek (bereits)
- 🟡 Schritt 1 (Skeleton) noch ausstehend in Code
- ⬜ Schritt 2 wird erst implementierbar nach Schritt 1, aber spezifiziert und prompt-fähig

---

### 11. Benutzer

aktualisiere den masterplan

### 12. Assistent

# Wissensdatenbank — Masterplan v3 (Frontend Phase 1 detailliert, FastMCP integriert)
**Statusmarkierung:** ✅ Implementiert · 🟡 Spezifiziert/ready-to-implement · ⬜ Geplant

---

# 1. Zielbild
Graphbasierte Wissensplattform (Neo4j), UI-first per REST, LLM-Tooling per FastMCP.

Status: ✅

---

# 2. Architektur
## 2.1 Komponenten
- Frontend: Next.js (App Router) + TS + Tailwind (lovable.dev)
- Backend: Node (Nest/Fastify) REST
- Tool-Gateway: FastMCP (Python)
- DB: Neo4j
- CI/CD: GitHub Actions

Status: ✅

## 2.2 Schnittstellenregeln
- Frontend → REST (deterministisch, versioniert)
- LLM/Agents → MCP (typed tools, whitelisted operations)
- Kein „arbitrary Cypher“ über MCP

Status: ✅

---

# 3. Domänenmodell (Neo4j)
## 3.1 Nodes
Article, Concept, Process, System, Person, Source, Tag

Status: 🟡 (Design final, nicht implementiert)

## 3.2 Relations
MENTIONS, RELATES_TO, USES, OWNS, TAGGED_WITH, SOURCED_FROM

Status: 🟡 (Design final, nicht implementiert)

## 3.3 Constraints/Indizes
- unique: id, slug
- fulltext: title, summary, contentMarkdown

Status: ⬜

---

# 4. Produktumfang
## MVP
- Auth (Rollen)
- CRUD Entities
- Relations (CRUD)
- Suche + Filter
- Backlinks
- Audit-Log

Status: 🟡 (Scope fixiert)

## V1
- Versionierung + Diff/Restore
- Source Pflicht für Publish
- Graph Explorer
- Import/Export

Status: ⬜

---

# 5. Phase 1 — Frontend (lovable.dev) — aktualisiert

## Schritt 1 — Skeleton (App Shell + Routing + UI + Mock API)
**Definition**
- App Shell (Sidebar + Topbar)
- Routen-Skeleton: `/`, `/search`, `/articles`, `/concepts`, `/processes`, `/graph`, `/admin`, `/login`
- Design System Komponenten: Button/Input/Modal/Badge/Card/Table/Tabs
- `/lib/types.ts`, `/lib/mockStore.ts` (Seed), `/lib/api.ts` (typed wrapper + delay)
- loading/empty/error states pro Seite

Status: 🟡

## Schritt 2 — Search + Lists + Detail Read + Backlinks
**Definition**
- `/search` URL-synced (`?q=&type=&status=&tag=`), debounce, grouping, counts, scoring
- Listen-Seiten: `/articles`, `/concepts`, `/processes` (shared `EntityList`/`EntityCard`)
- Detail Read-only: `/articles/[slug]`, `/concepts/[slug]`, `/processes/[slug]`
- Backlinks: incoming relations + outgoing relations (resolved)
- Shared State Components: LoadingState/EmptyState/ErrorState

Status: 🟡

## Schritt 3 — Editor + Create/Edit + Publish Validation
- `/articles/new`, `/articles/[slug]/edit`
- Markdown Editor + Preview
- Validierung (publish rules)
- Save draft / publish

Status: ⬜

## Schritt 4 — Relations CRUD + Assist UI Slots (UI-only)
- Add/remove relation Modal
- Assist Panel (disabled actions, UI-only)
- Validation Box UI

Status: ⬜

---

# 6. Phase 2 — Neo4j + REST Backend
- Neo4j Schema + Constraints
- Service Layer (Domain Validation)
- REST Endpoints (CRUD + search + relations)
- Frontend: mock → REST swap (api.ts switch)

Status: ⬜

---

# 7. Phase 3 — FastMCP Server (Tool API)
## 7.1 MCP Toolset (Minimum)
- search_entities
- get_entity
- upsert_article
- create_relation / delete_relation
- validate_publish
- suggest_relations (regelbasiert)

Status: 🟡 (spezifiziert)

## 7.2 Sicherheitsregeln
- Whitelist parameterized queries
- Enum validation entity_type/rel_type
- Result limits + timeouts
- Audit logging
- Role scopes (read vs write)

Status: 🟡 (Design, nicht implementiert)

---

# 8. Governance: Contracts / Single Source of Truth
- TS Types im Frontend sind Vorvertrag
- Später: OpenAPI (REST) + Pydantic Schemas (MCP)
- Mapping muss automatisierbar bleiben (kein Drift)

Status: 🟡

---

# 9. Implementierte Inhalte (real)
- ✅ Architekturentscheidungen (REST vs MCP, kein arbitrary Cypher)
- ✅ Domänenmodell und Relationstaxonomie definiert
- ✅ Phase 1 Schritt 1/2 Spezifikation inkl. Prompt Packages
- ✅ MCP Toolset Spezifikation + Security-Policy Design

Produktiver Code: ⬜

---

# 10. Nächster Engpass (systemisch)
- Engpass: fehlende Frontend-Codebasis blockiert Contract-Freeze.
- Mitigation: Phase 1 Schritt 1 vollständig umsetzen, dann Schritt 2, dann Contract einfrieren (Types + Routen + EntityCard).

### 13. Benutzer

das ist der aktuelle stand dest tool. analysiere es und nimm es als grundlage für weitere entwicklungen

### 14. Assistent

## Analyse des aktuellen Stands (Repo `knowledge-weaver-main`) als neue Baseline

### 1) Realer Tech-Stack (Ist)
- **Frontend**: Vite + React + TypeScript + React Router + shadcn/ui + Tailwind + React Query  
  - API-Layer mit **Runtime-Toggle** `VITE_API_MODE` (`mock` vs `real`) und `VITE_API_BASE_URL` (Default: `http://localhost:4000/api/v1`) in `src/lib/api.ts`.
- **Backend**: Node + Express (`server.js`) + Neo4j Driver
  - REST-nahe Endpunkte unter `/api/v1/*`
  - Rollenprüfung über Request-Header (`x-user-role`, `x-user-email`) für mutierende Endpunkte
  - Audit Events werden geschrieben (eigene Domain-Nodes/Label).
- **DB/Governance**: Neo4j **Migrationen** + Drift-Verification + Checksummen-Backfill  
  - Scripts: `npm run migrate`, `migrate:verify`, `migrate:status`, `migrate:backfill-checksums`
- **Tool-Gateway**: **FastMCP** Python-Server `mcp_server/` mit Neo4j-Client + Service Layer
  - Tools sind implementiert: `search_entities`, `get_entity`, `upsert_article`, `create_relation`, `delete_relation`, `validate_publish`, `suggest_relations`
- **Qualitäts-Gates**: OpenAPI-Lint (Redocly), Vitest, Smoke/Go-Live Checks, GitHub Actions Workflows inkl. Evidenzartefakten.

Diese Basis ist weiter als der vorherige Plan (Next.js + nur Mock). Für weitere Entwicklung ist **dieser Repo-Stand** die SSOT.

---

## 2) Funktionaler Scope (Ist) vs. Masterplan-Intent

### 2.1 Frontend (Ist: weitgehend umgesetzt)
- ✅ App Shell + Routing + UI-Komponentenbasis (shadcn/ui breit integriert)
- ✅ Search, Lists, Detailseiten (Artikel) inkl. Relations-Komponenten
- ✅ Article Editor inkl. Validierungsbox + Assist Panel (UI)
- ✅ Tag Management (UI vorhanden)
- ✅ Import/Results Flows (zusätzlicher Produktbereich über ursprünglichen MVP hinaus)
- ✅ ProtectedRoute / Role Guards im UI (soweit ersichtlich aus `src/components/ProtectedRoute.tsx` etc.)

### 2.2 Backend REST (Ist: produktionsnahe Features vorhanden, aber Auth ist noch “Header-basiert”)
Implementierte Endpunkte in `server.js` (Auszug, per Routing sichtbar):
- ✅ `GET /articles`, `GET /articles/:slug`, `POST /articles`, `PATCH /articles/:slug`
- ✅ `GET /concepts`, `GET /concepts/:slug`
- ✅ `GET /processes`, `GET /processes/:slug`
- ✅ `GET /search`, `GET /search/targets`
- ✅ `GET /relations`, `POST /relations`, `DELETE /relations/:id`
- ✅ `GET /dashboard/stats`, `GET /graph`
- ✅ `GET /entities/:entityType/:slug/activity`
- ✅ `GET /audit/events`
- ✅ Admin: `POST /admin/data/clear`, `POST /admin/data/reset` (mit Admin-Guard)
- ✅ PST Import Sessions: `POST /pst/sessions`, plus Folder/Email Reads

### 2.3 FastMCP (Ist: vorhanden + nutzbar)
- ✅ Tools implementiert in `mcp_server/app.py`
- ✅ Service Layer in `mcp_server/services/kb_service.py`
- ✅ Typed Schemas (Pydantic) in `mcp_server/schemas.py`
- ✅ `validate_publish` + `suggest_relations` sind real (laut README + Repo-Masterplan)

---

## 3) Verträge/Artifacts (Ist: Governance vorhanden)
- ✅ OpenAPI-Vertrag: `docs/openapi-v1.yaml` + `npm run openapi:lint`
- ✅ Mapping-Doku: `docs/api-rest-mapping-v1.md` (Contract ↔ Implementierung)
- ✅ Deployment Readiness/Go-Live Evidence: `docs/ready-for-deployment.md`, `artifacts/*` via Workflows
- ✅ CI: `contract-checks.yml`, `go-live-check.yml` etc.

Das ist ein starkes Fundament: Contract + Evidence minimieren Drift-Risiko.

---

## 4) Kritische Abhängigkeiten und Failure Modes (relevant für nächste Schritte)

### 4.1 AuthZ/AuthN ist derzeit spoofbar
- Rollen/Identität kommen aus Client-Headern (`x-user-role`, `x-user-email`) und werden im Frontend aus `localStorage` gesetzt (`src/lib/api.ts`).
- Konsequenz: Jeder Client kann sich “admin” geben, wenn der Backend-Endpunkt erreichbar ist.
- Risiko: Datenintegrität / Admin-Funktionen / Audit-Vertrauen.

### 4.2 Neo4j Query- und Schema-Konsistenz
- Migrationen + Drift-Check sind gut; Risiko bleibt:
  - Query-Performance (Fulltext / Relation Queries) ohne harte Limits/Timeouts pro Query
  - Inkonsistenzen zwischen Relation-Vokabular UI ↔ REST ↔ MCP (mehrere Maps/Enums)

### 4.3 PST Sessions im Backend (Memory/TTL)
- `pstSessions` ist in-memory Map mit TTL cleanup.
- Risiko: RAM-Spikes, parallele Uploads, Restart-Verlust, horizontale Skalierung schwierig.

### 4.4 Express v5 + Upload Limits
- Sehr hohes Upload-Limit (`PST_UPLOAD_LIMIT` Default 4096mb).
- Risiko: DoS über Payload, ungeplante Speicher-/Disk-Pressure.

---

## 5) Konkrete Baseline-Entscheidung für “weitere Entwicklungen”
Ab jetzt gilt:
- **Masterplan-Referenz**: `knowledge-weaver-main/masterplan.md` + `docs/masterplan-umsetzung-v3.md` sind führend.
- **Architektur**: Vite/React bleibt baseline (kein Next.js-Migrationsprojekt starten), weil bereits:
  - UI, API toggles, Import/Results, CI-Contract-Gates implementiert sind.
- **MCP/REST Koexistenz**: beibehalten; REST ist Produkt-API, MCP ist Tool-API. Beide hängen an Neo4j.

---

## 6) Update des Masterplans (Status in deiner Notion-Logik)

### 6.1 Phase 1 Frontend
- ✅ Schritt 1 Skeleton
- ✅ Schritt 2 Search + Lists + Detail Read + Backlinks
- ✅ Schritt 3 Editor + Create/Edit + Validation
- ✅ Schritt 4 Relations CRUD + Assist UI Slots (UI)

### 6.2 Phase 2 Neo4j + REST
- ✅ Grundfunktionalität (CRUD/Search/Relations/Graph/Activity/Audit)
- 🟡 Härtung als “API-Produkt” (AuthN/AuthZ echt, Rate limits, Observability, Multi-env config)

### 6.3 Phase 3 FastMCP
- ✅ Toolset inkl. `validate_publish` und `suggest_relations`
- 🟡 Auth/Scopes serverseitig (nicht nur “ok/error” Response), Hardening gegen Injection/Abuse

---

## 7) Konsequenz für die nächsten Entwicklungs-Backlogs (als Ableitung aus dem Ist)
- **B1 Security Hardening (höchste Priorität)**: echtes AuthN/AuthZ (Tokens/Sessions), Header-basierte Rollen eliminieren oder nur intern erlauben (z. B. behind gateway).
- **B2 Contract Harmonisierung**: Single Enum Source für `entity_type`, `status`, `relation_type` (UI/REST/MCP/Neo4j).
- **B3 Betriebsfähigkeit**: Rate limiting, request size caps, structured logging, health endpoints, Neo4j query timeouts/limits zentral.
- **B4 Import Robustheit**: PST Session Storage externisieren (Redis/S3) oder zumindest serverseitige Quotas + streaming.
- **B5 Feature-Ausbau**: Graph Explorer UX, Versionierung/Diff, Source Pflicht bei Publish (Policy serverseitig + MCP tool).

Ich nehme diesen Repo-Stand als Grundlage.

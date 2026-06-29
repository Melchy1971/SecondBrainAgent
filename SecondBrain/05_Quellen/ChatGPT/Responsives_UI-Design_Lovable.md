---
title: "Responsives UI-Design Lovable"
type: chatgpt_conversation
source: chatgpt
source_id: "68f6332c-851c-832d-b0f2-5a5f435d7133"
created: 2025-10-20
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


# Responsives UI-Design Lovable

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68f6332c-851c-832d-b0f2-5a5f435d7133`
- Nachrichten: 16

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

ist es möglich bei einem Lovable.dev projekt das ein tool  ist für die anzeige auf einem handy oder tablett zusätzlich eine passende gui bereitzustellen welche automatisch je nach gerät geladen wird damit die Ansicht immer perfekt angezeigt wird.

### 2. Assistent

Kurz: Ja — das geht. Was du willst, ist **responsives** bzw. **adaptives** UI-Design: Die gleiche App liefert je nach Viewport (Handy/Tablet/Desktop) automatisch unterschiedliche Layout-Varianten. Lovable unterstützt das konzeptionell; die Details hängen davon ab, wie sauber du Breakpoints, Komponenten-Varianten und Regeln vorgibst und ggf. im Code Mode nachziehst. citeturn0search1turn0search6turn0search15turn0search0turn0search9

Jetzt im Stil deines gewünschten „Sparrings“:

### 1) Annahmen prüfen
- **„Lovable macht das automatisch.“** Teilweise. Lovable generiert “moderne, responsive” Layouts, aber ohne klare Vorgaben baut es gern generische Breakpoints. Feinheiten (Tablet-Speziallayouts, Touch-Zielgrößen, Spaltenwechsel) brauchen Präzision in Prompt/Knowledge-File oder Feinschliff im Code Mode. citeturn0search11turn0search6  
- **„Geräteerkennung ist die Lösung.“** Geräte-/User-Agent-Erkennung ist brüchig. Stabiler ist **Viewport-/Feature-Erkennung** (CSS-Media Queries, `pointer: coarse/fine`, Orientation).  
- **„Tablet = eigener Codepfad.“** Oft unnötig. Besser: eine Codebasis mit Komponenten-Varianten je Breakpoint; nur für echte Ausnahmen (z. B. komplett anderes Navigationsmuster) trennst du die Views.

### 2) Gegenargumente (der skeptische Profi)
- **„Eine zweite, ‚Mobile-Only‘-GUI macht es klarer.“** Kurzfristig ja, langfristig wartungsintensiv. Zwei UIs bedeuten doppelte Tests, doppelte Bugs. Ein gutes responsives System deckt 90 % ab; Spezialfälle löst man mit gezielten Varianten.  
- **„Lovable ist no-code, also kann ich Feinheiten nicht steuern.“** Doch: Mit **Knowledge-File** + **Prompt-Bibliothek** legst du Designregeln fest; im **Code Mode** passt du Breakpoints, CSS-Grid/Flex und Komponentenzustände an. citeturn0search6turn0search14turn0search15

### 3) Logik-Check
Deine Zielaussage („automatisch je Gerät die perfekte Ansicht“) hält, **wenn** du es als **regelbasiertes, viewport-getriebenes** Umschalten verstandest. „Perfekt“ heißt:  
- Layouts wechseln an sinnvollen **Breakpoints** (z. B. 0–640, 641–1024, 1025+).  
- **Komponenten-Varianten** (z. B. Card-Dichte, Icon-Only Bottom-Nav vs. Sidebar) sind definiert.  
- **Touch-First** für kleine Screens (größere Targets, reduziertes Chrome), **Informationsdichte** für große Screens. Lovable liefert die Basis; du definierst die Regeln. citeturn0search0turn0search9

### 4) Alternative Perspektiven
- **Rein responsiv (empfohlen):** Eine Codebasis, CSS-Breakpoints, conditional rendering per Viewport.  
- **Adaptiv light:** Ein Flag (z. B. `isHandset`, via `matchMedia`) um bestimmte Widgets auszutauschen (z. B. Drawer vs. Sidebar).  
- **Routen-Varianten:** Seltene Fälle mit getrennten Mobil-Routen (`/m/...`) für komplett andere Informationsarchitektur.  
- **PWA-Denke:** Wenn’s wie „App“ wirken soll: Home-Screen-Install, Offline-Cache, aber UI bleibt responsiv.

### 5) Konkreter Fahrplan in Lovable
1) **Knowledge-File schärfen**  
   Lege fest: Breakpoints, Navigationsmuster pro Breakpoint, Max-Breite, Spaltenlogik (Grid), Touch-Zielgrößen, Typografie-Skalierung. (Lovable liest das bei jedem Prompt mit.) citeturn0search6turn0search14  
2) **Prompting**  
   „Erstelle ein responsives Layout mit Breakpoints: `sm≤640`, `md≤1024`, `lg>1024`.  
   - **sm:** Bottom-Nav, 1-spaltig, 16 px Padding, Karten kompakt, Buttons 44×44 px min.  
   - **md:** 2-spaltig, persistenter Drawer, größere Tabellenzeilen.  
   - **lg:** Sidebar + Content + Zusatz-Paneel (3 Spalten), dichte Tabellen.“  
   Lovable hat How-tos für „responsive design“ — die liefern gute Startpunkte. citeturn0search0turn0search5turn0search11  
3) **Komponenten-Varianten**  
   Bitte Lovable explizit um **Variants**: `Nav{mobile,tablet,desktop}`, `Card{compact,regular,dense}`, `Table{stacked,scroll,wide}`.  
4) **Code Mode-Feinschliff**  
   – Media Queries/Utility-Klassen prüfen, Grid-Templates je Breakpoint definieren, Interaktionen für `pointer: coarse` anpassen. (Code Mode ist dafür vorgesehen.) citeturn0search15  
5) **Testing in Lovable Cloud/Preview**  
   Handy/Tablet/Desk-Viewports durchklicken; Orientierung und Zoom testen; Fokus-Reihenfolge & A11y prüfen. (Die „Responsive Design“-Guides verweisen genau darauf.) citeturn0search0

**Worauf du achten solltest**
- **Tablet ist kein großes Handy.** Plane eigene Breakpoint-Entscheidungen (z. B. 2-Spalten-Dashboards).  
- **Kein UA-Sniffing.** Arbeite mit Viewport/Feature-Erkennung.  
- **Content-Priorisierung.** Mobil zuerst Kernaktionen; Desktop bekommt Kontext-Paneele statt mehr Chaos.  
- **State-Parität.** Variierende Layouts, aber **gleiche** Daten/States, damit nichts „mobil verschwindet“.

Wenn du magst, skizziere ich dir jetzt ein präzises **Knowledge-File-Gerüst** (auf Deutsch) + ein Beispiel-Prompt, mit dem Lovable sofort Tablet-/Mobile-Varianten erzeugt und du nur noch im Code Mode die Breakpoints feinjustierst.

### 3. Benutzer

ja

### 4. Assistent

Alles klar – hier ist das versprochene Paket: ein sofort einsetzbares **Knowledge-File-Gerüst** (zum Einbinden in Lovable) plus **Beispiel-Prompts**, **Komponenten-Varianten**, ein kleiner **Viewport-Hook** und eine kurze **Test-Checkliste**. Kopieren, einfügen, loslegen.

# Knowledge-File (Gerüst zum Einfügen in Lovable)
Format: Markdown/YAML-Style ist egal – Hauptsache konsistent. Ich nutze YAML-ähnliche Blöcke, weil’s präzise ist.

```yaml
product_principles:
  - Eine Codebasis, responsive/adaptiv per Viewport & Feature Detection (kein UA-Sniffing).
  - Mobile-first; Tablet bekommt eigenständige Layoutentscheidungen (nicht nur „größer“).
  - Konsistente Tokens (Spacing, Typo, Radius); Variants für Komponenten je Breakpoint.
  - Touch-Zielgröße min. 44x44 px; Fokuszustände sichtbar; Kontraste AA+.

breakpoints:
  - name: sm
    min: 0
    max: 640
    grid: "1fr"
    container_padding: 16
    nav: bottom
    sidebar: off
    tables: stacked
  - name: md
    min: 641
    max: 1024
    grid: "minmax(0,1fr) minmax(0,1fr)"
    container_padding: 20
    nav: drawer_persistent
    sidebar: on
    tables: scroll_x
  - name: lg
    min: 1025
    max: null
    grid: "280px minmax(0,1fr) 360px"
    container_padding: 24
    nav: sidebar
    sidebar: on
    tables: wide

design_tokens:
  radius: [8, 12, 16]
  spacing: [4, 8, 12, 16, 20, 24, 32]
  elevation: ["none", "sm", "md", "lg"]
  font_scale:
    sm: { base: 15, h1: 22, h2: 18 }
    md: { base: 16, h1: 24, h2: 20 }
    lg: { base: 16, h1: 28, h2: 22 }

navigation_patterns:
  sm: "BottomNav mit 3–5 Primäraktionen, Floating Action für wichtigste Aktion"
  md: "Persistenter Drawer (links) + AppBar; sekundäre Filter im Drawer"
  lg: "Sidebar (links) + Topbar; drittes Panel rechts für Details/Filter"

component_variants:
  Nav:
    - mobile_bottom
    - tablet_drawer
    - desktop_sidebar
  Card:
    - compact   # sm
    - regular   # md
    - dense     # lg
  Table:
    - stacked   # sm: Key-Value-Listen, Sektionen
    - scroll    # md: horizontales Scrollen, Sticky-Header
    - wide      # lg: Spalten, Inline-Filter
  Form:
    - single_column_sm
    - two_column_md
    - two_plus_aside_lg

interaction_rules:
  pointer_coarse: 
    min_target: 44
    hit_slop: 8
    scrollbar: overlay
  keyboard:
    focus_visible: true
    order: "DOM-Reihenfolge, keine Sprünge"
  gestures:
    sm: ["pull_to_refresh", "swipe_to_reveal_actions"]
    md_lg: ["drag_splitter_optional"]

adaptive_rules:
  orientation:
    landscape_sm: "BottomNav -> kompakter, Liste -> 2-Spalten"
  density_toggle:
    lg: ["normal", "dense"]
  feature_detection:
    prefers_reduced_motion: "Animationsdauer halbieren, Parallax aus"

content_priority:
  mobile_core_actions: ["create", "scan", "search"]
  tablet_core: ["overview+filter", "quick actions"]
  desktop_plus: ["context panel", "bulk ops"]

performance:
  images: "responsive sources, width hints, lazy"
  code_split: "route- und component-level"
  skeletons: true

accessibility:
  contrast: "AA oder besser"
  focus_ring: "deutlich, nicht nur Farbe"
  semantics: "Landmarks, ARIA nur wenn nötig"
```

# Beispiel-Prompts für Lovable

**1) Basislayout generieren**
```
Erstelle eine responsive App-Oberfläche nach folgendem Knowledge-File:
- Breakpoints: sm≤640, md≤1024, lg>1024
- Grid:
  sm: 1 Spalte; md: 2 Spalten; lg: Sidebar 280px + Content + RightPane 360px
- Navigation:
  sm: BottomNav (3–5 Aktionen) + optional FAB
  md: persistenter Drawer links
  lg: Sidebar links + Topbar
- Komponenten-Varianten:
  Nav{mobile_bottom, tablet_drawer, desktop_sidebar}
  Card{compact,regular,dense}
  Table{stacked,scroll,wide}
- Touch-Zielgröße ≥44x44, sichtbare Fokuszustände, AA+ Kontraste.
Implementiere Beispielseiten: Dashboard, Liste, Detail. Nutze die Varianten je Breakpoint.
```

**2) Tabellen-Verhalten konkretisieren**
```
Baue eine Table-Komponente mit Varianten:
- sm: Table.stacked (Key–Value-Blöcke pro Datensatz, Aktionen in Swipe-Reveal)
- md: Table.scroll (Sticky-Header, horizontales Scrollen)
- lg: Table.wide (Multi-Spalten, Inline-Filter, Spalten-Resize)
Liefere Demo mit 50 Einträgen und Paginierung. Achte auf 44px Zeilenhöhe bei sm.
```

**3) Formulare adaptiv**
```
Generiere ein Formular mit Varianten:
- sm: einspaltig, große Controls, primäre Aktion sticky unten
- md: zweispaltig, Sektionen
- lg: zweispaltig + rechtes Kontextpaneel (Zusammenfassung/Validierung)
```

# Komponenten-API (damit Lovable klare Varianten baut)

**Nav**
```ts
type NavVariant = "mobile_bottom" | "tablet_drawer" | "desktop_sidebar";

<Nav variant="mobile_bottom" items={[...]} />
<Nav variant="tablet_drawer" items={[...]} />
<Nav variant="desktop_sidebar" items={[...]} />
```

**Card**
```ts
type CardVariant = "compact" | "regular" | "dense";
<Card variant="compact" title="..." />
```

**Table**
```ts
type TableVariant = "stacked" | "scroll" | "wide";
<Table variant="stacked" data={rows} onRowAction={...} />
```

# Kleiner Viewport-/Feature-Hook (React/TS, generisch)

Den kannst du im Code Mode einsetzen, falls Lovable nicht automatisch eine saubere Abstraktion erzeugt:

```ts
import { useEffect, useState } from "react";

export function useViewport() {
  const [bp, setBp] = useState<"sm" | "md" | "lg">("lg");
  const [coarse, setCoarse] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mqSm = window.matchMedia("(max-width: 640px)");
    const mqMd = window.matchMedia("(min-width: 641px) and (max-width: 1024px)");
    const mqCoarse = window.matchMedia("(pointer: coarse)");
    const mqReduce = window.matchMedia("(prefers-reduced-motion: reduce)");

    const update = () => {
      setBp(mqSm.matches ? "sm" : mqMd.matches ? "md" : "lg");
      setCoarse(mqCoarse.matches);
      setReducedMotion(mqReduce.matches);
    };
    [mqSm, mqMd, mqCoarse, mqReduce].forEach(mq => mq.addEventListener("change", update));
    update();
    return () => {
      [mqSm, mqMd, mqCoarse, mqReduce].forEach(mq => mq.removeEventListener("change", update));
    };
  }, []);

  return { bp, coarse, reducedMotion };
}
```

Beispielnutzung:
```tsx
const { bp, coarse } = useViewport();
const navVariant = bp === "sm" ? "mobile_bottom" : bp === "md" ? "tablet_drawer" : "desktop_sidebar";
const tableVariant = bp === "sm" ? "stacked" : bp === "md" ? "scroll" : "wide";

<Nav variant={navVariant} />
<Table variant={tableVariant} touchOptimized={coarse} />
```

# CSS-Utilities (falls du selbst Hand anlegst)

```css
:root { --radius-1: 8px; --radius-2: 12px; --radius-3: 16px; }
@media (max-width: 640px)  { .container { padding: 16px; } }
@media (min-width: 641px) and (max-width: 1024px) { .container { padding: 20px; } }
@media (min-width: 1025px) { .container { padding: 24px; } }

@media (pointer: coarse) {
  .hit { min-width: 44px; min-height: 44px; }
}
:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }
```

# Mini-Test-Checkliste (in Lovable-Preview/Cloud)

- Viewports: 360×640, 820×1180, 1280×800, 1440×900.
- Orientationwechsel auf sm: Liste wird 2-spaltig? BottomNav bleibt bedienbar?
- Touch-Targets per DevTools messen: ≥44 px?  
- Tastatur: Tab-Reihenfolge, Fokus gut sichtbar, Escape schließt Menüs/Drawer.
- Tabellen: sm=gestapelt, md=scrollbar, lg=wide; Spalten-Priorisierung sinnvoll?
- Performance: Lazy-Images, Skeletons, kein „Layout Shift“ beim Laden.

# Sparrings-Notizen kurz & knackig
1) **Annahme:** „Automatisch perfekt“ passiert von allein.  
   **Korrektur:** Nur mit klaren Regeln (Breakpoints, Varianten, Prioritäten) wird es zuverlässig.
2) **Gegenargument:** „Separate Mobile-App ist sauberer.“  
   **Antwort:** Wartungsaufwand verdoppelt sich. Mit Varianten erreichst du 90–95 % mit einer Codebasis.
3) **Logik-Check:** Viewport- und Feature-Erkennung > Geräteerkennung.  
4) **Alternative Sicht:** Für sehr unterschiedliche Workflows kannst du ausgewählte Routen duplizieren (`/m/...`). Nutze das sparsam.

Wenn du mir kurz sagst, welche Screens dein Projekt aktuell hat (z. B. Dashboard, Inventarliste, Detail, Formular), setze ich dir daraus eine konkrete Prompt-Sequenz zusammen, die Lovable Schritt für Schritt in diese Struktur presst – inkl. Beispieldaten und A11y-Checks.

### 5. Benutzer

ich nutze cursor um den code zu optimieren. passenen prompt bitte

### 6. Assistent

Alles klar, Markus — hier sind **sofort nutzbare Cursor-Prompts** für deinen Code-Feinschliff. Die sind auf „responsive/adaptiv für Handy/Tablet/Desktop“ getrimmt und funktionieren gut mit TypeScript/React (Lovable-Codebasis + Code Mode). Ich gebe dir erst einen **Master-Prompt** (Repo-weit), dann **gezielte Einzel-Prompts** (Komponente/Datei), plus einen **QA/Review-Gate** zum automatischen Gegencheck.

---

## Master-Prompt (Repo-weit, einmal zu Beginn)
**Ziel:** Projekt auf responsives/adaptives Layout umbauen, saubere Varianten, A11y & Performance – ohne UA-Sniffing.

```
Act as a senior front-end architect. Review the repository and produce a plan + patch set to make the UI responsive/adaptive for phone/tablet/desktop.

Context & rules:
- One codebase, responsive/adaptive via viewport & feature detection (no user-agent sniffing).
- Breakpoints: sm ≤ 640, md ≤ 1024, lg > 1024.
- Layout:
  sm: 1 column, BottomNav (3–5 actions), optional FAB; tables=stacked.
  md: 2 columns, persistent drawer; tables=scroll with sticky header.
  lg: 3 columns (sidebar 280px, content, right pane 360px); tables=wide with inline filters.
- Component variants to add (if missing):
  Nav{"mobile_bottom","tablet_drawer","desktop_sidebar"}
  Card{"compact","regular","dense"}
  Table{"stacked","scroll","wide"}
  Form{"single_column_sm","two_column_md","two_plus_aside_lg"}
- Touch target ≥ 44×44 px; visible focus states; WCAG AA+ contrast.
- Prefer TypeScript strict, React function components, CSS Grid/Flex. No UA sniffing; use matchMedia/feature queries.
- Keep public API stable where feasible; introduce variants via props with sensible defaults.
- Performance: route & component-level code-splitting, responsive images, lazy loading, skeleton states.
- Accessibility: landmarks, aria only when necessary, :focus-visible, keyboard order = DOM order.

Deliverables:
1) A short PLAN.md with concrete steps and affected files.
2) Code changes as unified diffs (one or more patches), minimal churn, clear commit messages (Conventional Commits).
3) A smoke test note describing how to verify behavior at 360×640, 820×1180, 1280×800, 1440×900 and for (pointer: coarse).
4) A checklist for regressions (nav, table, forms, dialogs).

Start by scanning these paths (if present) and proposing the plan:
- src/components/**, src/pages/**, src/app/**, src/styles/**, src/hooks/**
Now produce PLAN.md and the first batch of patches.
```

---

## Prompt für Navigation (BottomNav/Drawer/Sidebar)
```
Refactor the navigation to support variants:
- Nav{"mobile_bottom","tablet_drawer","desktop_sidebar"} with a shared NavItem model.
- Variant selection: sm -> mobile_bottom, md -> tablet_drawer, lg -> desktop_sidebar.
- Extract reusable primitives: AppBar, Drawer, Sidebar, BottomBar.
- Ensure keyboard navigation (Arrow keys, Home/End), focus-visible rings, min hit area 44px on coarse pointers.
- Provide a demo screen switching variants via a BreakpointProvider.

Output:
- New/updated components in src/components/nav/*
- A hook useViewport() using matchMedia for sm/md/lg and (pointer: coarse).
- Unified diff patch only, plus a short usage snippet in the commit message.
```

---

## Prompt für Tabelle (stacked/scroll/wide)
```
Transform the Table component to support variants:
- Table{"stacked","scroll","wide"} chosen by breakpoint.
- stacked (sm): key-value blocks per row, row actions via swipe-reveal or overflow menu.
- scroll (md): horizontal scroll, sticky header, min row height 44px, column min-widths.
- wide (lg): multi-column with inline filters, optional column resize.
- Keep existing Table API where possible; add prop `variant?: "stacked"|"scroll"|"wide"` with auto-default from context.
- Add sample with 50 rows, pagination, and empty state.

Deliverables:
- src/components/table/* updates, Story or demo page.
- Unified diff patch only; explain any breaking changes.
```

---

## Prompt für Formulare (einspaltig/zweispaltig + Aside)
```
Refactor forms to adaptive layout:
- Form variants: "single_column_sm", "two_column_md", "two_plus_aside_lg".
- sm: primary action sticky bottom; md: two columns; lg: two columns + right context pane (summary/validation).
- Enforce consistent spacing tokens, label alignment, and error messaging.
- Add keyboard and screen reader checks (aria-invalid, aria-describedby).

Deliverables:
- src/components/forms/* changes and a demo page
- Unified diff patch only, including a form with validation and async submit.
```

---

## Prompt für Hook & Provider (Viewport/Feature Detection)
```
Create src/hooks/useViewport.ts and a BreakpointProvider:
- useViewport returns { bp: "sm"|"md"|"lg", coarse: boolean, reducedMotion: boolean } using matchMedia.
- Provide context to auto-select component variants; allow manual override via props.
- Include tests for media query transitions (jsdom friendly).
Return a unified diff patch and usage example.
```

---

## Prompt für Design Tokens & Utilities (CSS)
```
Introduce design tokens and responsive utilities:
- :root tokens for radius (8/12/16), spacing scale [4..32], and typography scales for sm/md/lg.
- Media queries for paddings: sm 16px, md 20px, lg 24px.
- :focus-visible outline with offset; (pointer: coarse) .hit { min-width/height: 44px }.
- Ensure no color hard-coding that would violate AA; keep variables.

Deliverables:
- src/styles/tokens.css (or tailwind.config if using Tailwind) and imports wired up.
- Unified diff patch only.
```

---

## Prompt für Performance (Images, Split, Skeletons)
```
Add performance improvements:
- Responsive <img> with sizes/srcset, lazy loading.
- Code-split large routes and rarely used components; add suspense fallbacks with skeletons.
- Verify no cumulative layout shift when skeletons swap to content.

Deliverables:
- Unified diff patches and a short PERF_NOTES.md with before/after hints.
```

---

## QA/Review-Gate (kritischer Gegencheck vor Merge)
```
Run a critical review of the latest patch set:

1) Assumptions to challenge:
   - Are breakpoints sufficient for tablets in landscape?
   - Any hidden UA-sniffing or brittle width constants?
   - Are action targets ≥ 44px on coarse pointers?
   - Focus states visible and keyboard order logical?

2) Counterarguments to address:
   - Would a separate mobile route reduce complexity? If yes, justify why we still keep one codebase.
   - Are there components that deserve hard forks (mobile-only)? List them explicitly.

3) Logic check:
   - Variant selection consistent across Nav/Table/Form?
   - No duplicated business logic between variants?
   - State parity: same data/actions available on all breakpoints?

4) Alternative perspectives:
   - Orientation-specific tweaks for sm landscape (2-column lists)?
   - Density toggle for lg ("normal" vs "dense")?

5) Output:
   - A concise REVIEW.md with findings and required fixes.
   - If issues are found, generate follow-up diffs to fix them.
```

---

## Quick-Fix Prompt (eine Datei, minimal-invasiv)
```
Refactor the attached file for breakpoint-driven behavior (sm≤640, md≤1024, lg>1024).
- Introduce a `variant` prop that defaults from context (sm/md/lg).
- Replace UA checks with matchMedia logic.
- Add focus-visible styles and touch target guards if interactive.
Return only a unified diff patch, no extra commentary.
```

---

## Commit-Message-Template (für Cursor)
```
feat(ui): add responsive variants for Nav/Table/Form

- introduce BreakpointProvider and useViewport hook
- add Nav{mobile_bottom,tablet_drawer,desktop_sidebar}
- add Table{stacked,scroll,wide}; demo with 50 rows, pagination
- add Form{single_column_sm,two_column_md,two_plus_aside_lg}
- tokens & utilities for spacing/typography and focus-visible
- performance: lazy images, route-level code splitting

Refs: PLAN.md, REVIEW.md
```

---

### Mini-Sparring zu deinen Annahmen
1) **Annahme:** „Cursor optimiert das automatisch.“  
   **Korrektur:** Cursor ist stark, aber „perfekt“ entsteht nur mit klaren Regeln (Breakpoints, Varianten, A11y-Checks).
2) **Gegenargument:** „Separate Mobile-Views sind übersichtlicher.“  
   **Antwort:** Nur wenn Workflows wirklich divergieren. Sonst doppelte Wartung. Varianten + Provider sind robuster.
3) **Logik-Check:** Feature-/Viewport-Erkennung schlägt Geräte-Erkennung.  
4) **Alternative:** Für 1–2 stark abweichende Screens eigene `/m/...`-Routen – aber sparsam, mit State-Parität.

Wenn du mir verrätst, welche Komponenten bei dir am meisten Schmerzen machen (z. B. Nav, Table, Formular, Dialoge), formuliere ich dir punktgenau einen File-by-File Prompt, der Cursor sofort eine passende Diff liefert.

### 7. Benutzer

nav

### 8. Assistent

Perfekt — fokussieren wir die **Nav**. Du bekommst jetzt schlanke, sofort nutzbare **Cursor-Prompts** in drei Stufen: Plan → Implementierung → Absicherung. Plus ein Mini-Sparring am Ende, damit wir dein Denken schärfen.

---

## 0) Einmaliger Plan-Prompt (Repo-weit)
**Ziel:** Variantenfähige Navigation mit sauberer A11y, ohne UA-Sniffing, per Breakpoint/Feature-Detection.

```
Act as a senior frontend architect. Scope a small, safe refactor to make navigation responsive/adaptive.

Constraints:
- Variants: Nav{"mobile_bottom","tablet_drawer","desktop_sidebar"}.
- Breakpoints: sm ≤ 640, md ≤ 1024, lg > 1024; feature detection for (pointer: coarse).
- A11y: roving tabindex for menus, Arrow/Home/End support, :focus-visible rings, min hit area ≥ 44x44 on coarse pointers.
- No user-agent sniffing. Use matchMedia via a BreakpointProvider.

Deliverables:
1) PLAN-NAV.md (files to touch, risks, test plan).
2) Unified diffs for:
   - src/hooks/useViewport.ts
   - src/components/nav/Nav.tsx (switch on variant prop or context)
   - src/components/nav/BottomBar.tsx
   - src/components/nav/DrawerNav.tsx
   - src/components/nav/SidebarNav.tsx
   - src/components/nav/NavItem.tsx (shared model + roving tabindex)
   - wiring in layout (Next.js: app/layout.tsx; CRA/Vite: src/App.tsx)
3) Demo page with a variant toggle (dev only).
Start by generating PLAN-NAV.md and the first patch set.
```

---

## 1) Implementierungsprompts (gezielt pro Teil)

### 1a) Viewport-Hook & Provider
```
Create src/hooks/useViewport.ts and a BreakpointProvider:

- useViewport() returns { bp: "sm"|"md"|"lg", coarse: boolean } via matchMedia:
  sm ≤ 640, md 641–1024, lg ≥ 1025; coarse from (pointer: coarse).
- BreakpointProvider exposes context { bp, coarse } with manual override for testing.
- Add simple tests (jsdom) to verify transitions.

Return a unified diff and a short usage snippet.
```

### 1b) Nav-API & gemeinsame Items
```
Introduce a shared navigation model:

// src/components/nav/types.ts
export type NavItem = {
  id: string;
  label: string;
  icon?: React.ReactNode;
  href?: string;
  onSelect?: () => void;
  active?: boolean;
  disabled?: boolean;
};

Refactor Nav to:
- export type NavVariant = "mobile_bottom" | "tablet_drawer" | "desktop_sidebar";
- <Nav items={NavItem[]} variant?: NavVariant />; default variant comes from BreakpointProvider.
- Internally dispatch to <BottomBar/>, <DrawerNav/>, <SidebarNav/> while keeping a11y parity.
Return unified diffs for types + Nav.tsx.
```

### 1c) BottomBar (mobile)
```
Implement src/components/nav/BottomBar.tsx:

Requirements:
- Fixed bottom bar with 3–5 primary actions.
- Each button: min 44x44 on coarse pointers; label visible, icon optional.
- Keyboard: roving tabindex (one tab stop for the bar), ArrowLeft/Right to move, Home/End supported.
- ARIA: role="tablist" or "navigation" with aria-label; items role="tab" or "link" respectively.
- Focus ring via :focus-visible, no outline suppression.
Return a unified diff with component + minimal CSS (tokens/utilities).
```

### 1d) DrawerNav (tablet)
```
Implement src/components/nav/DrawerNav.tsx:

- Persistent left drawer (md), collapsible below md.
- Keyboard: ArrowUp/Down, Home/End, roving tabindex.
- Provide aria-expanded on groups, aria-current for active.
- Ensure 44px row height on coarse pointers; sticky top AppBar optional.
Return unified diff and usage inside Nav.tsx switch.
```

### 1e) SidebarNav (desktop)
```
Implement src/components/nav/SidebarNav.tsx:

- Left sidebar (280px). Support section headers and nested items (1 level).
- Keep DOM order logical; provide aria-labelledby for groups.
- Hover effect + focus-visible; dense mode optional via prop.
- Ensure state parity: all actions available across variants.
Return unified diff and SCSS/CSS (or Tailwind classes) updates.
```

### 1f) Layout-Wiring
```
Wire Nav into the app layout:

- If Next.js App Router: update app/layout.tsx to include <BreakpointProvider> and <Nav/> with items from a central config src/navigation.ts.
- If CRA/Vite/Remix: update src/App.tsx similarly.
- Provide a dev-only "VariantToggle" (query param ?navVariant=...) to force variants for manual QA.
Return unified diff patches only.
```

### 1g) A11y & Hit-Area Utilities
```
Add utilities:

- tokens.css (or tailwind utilities): :focus-visible outline 2px + offset; .hit { min-width/height: 44px } under (pointer: coarse).
- data attributes: [data-roving="true"] parent: manage tabindex=0 for active, -1 for others.
- Prefer button role only for real buttons; use <a> with href for links; set aria-current="page" on active route.

Return unified diff and show where these utilities are imported.
```

---

## 2) Absicherungsprompts (QA, Tests, Lint)

### 2a) QA-Checklist & Playground
```
Create NAV-QA.md and a Playground page:

Checklist:
- Viewports: 360×640 (portrait), 820×1180 (portrait), 1024×768 (landscape), 1440×900.
- Variants switch at 641px and 1025px as expected.
- Keyboard: Tab enters the bar/drawer/sidebar once; Arrow keys move focus; Home/End jump; Escape closes temporary drawer (if any).
- Hit area ≥ 44×44 on coarse pointers.
- aria-current="page" present on active item; screen reader labels consistent.

Deliverables:
- /src/pages/_playground/nav (or route) showing all variants.
- NAV-QA.md with pass/fail boxes.
Return unified diffs only.
```

### 2b) Unit-Tests für Roving Tabindex
```
Add tests for roving tabindex behavior in NavItem lists:

- Initial active item has tabindex=0; others -1.
- Arrow keys move focus and update tabindex.
- Home/End go to first/last.
Provide tests under src/components/nav/__tests__/ and update package scripts.
Return unified diff.
```

---

## 3) Quick-Fix Prompt (falls du nur eine Datei reparieren willst)
```
Refactor the provided navigation file for variant-driven behavior (sm≤640, md≤1024, lg>1024).

- Add prop `variant?: "mobile_bottom"|"tablet_drawer"|"desktop_sidebar"`.
- Default variant from BreakpointProvider; keep backward compatibility if prop is omitted.
- Replace any UA checks with matchMedia via useViewport.
- Implement roving tabindex for the item list; Arrow/Home/End; :focus-visible.
- Enforce min hit area (44x44) on coarse pointers with a utility class.
Return only a unified diff patch; no extra prose.
```

---

## Bonus: Minimal Interfaces (für Copy-Paste in Cursor)
```ts
// src/components/nav/types.ts
export type NavVariant = "mobile_bottom" | "tablet_drawer" | "desktop_sidebar";
export type NavItem = {
  id: string;
  label: string;
  href?: string;
  onSelect?: () => void;
  icon?: React.ReactNode;
  active?: boolean;
  disabled?: boolean;
};
```

---

## Mini-Sparring zu deiner Nav-Annahme
1) **Annahme:** „Mobile braucht ganz andere Navigation.“  
   **Gegenstoß:** Meist reicht ein Variantenwechsel (BottomBar ↔ Drawer ↔ Sidebar). Eigenständige Routen verdoppeln Wartung.  
2) **Risiko:** **UA-Sniffing** oder „Tablet = iPad“.  
   **Korrektur:** Viewport + Feature-Detection (pointer: coarse) ist robuster.  
3) **Logik-Check:** Achte auf **State-Parität**: dieselben Aktionen in allen Varianten.  
4) **Alternative Perspektive:** **Dichte-Toggle** für Desktop („normal“/„dense“) statt neuer Variante.

Wenn du mir verrätst, ob du **Next.js App Router** oder **Vite/CRA** nutzt, liefere ich dir das exakte Wiring-Diff (layout/App, Provider-Einbindung, Route für Playground) im passenden Format—ready to paste in Cursor.

### 9. Assistent

Sehr gute Frage – Cursor mag eine **klare Reihenfolge**. Die Reihenfolge entscheidet, ob er dein Projekt Schritt für Schritt umbaut oder chaotisch alles mischt.  
Hier der Ablauf, der sich in Projekten bewährt hat:

---

## Reihenfolge für die Eingabe in Cursor

### Phase 1: Planung
1. **Master-Plan für Navigation**
   - Prompt: *„Act as a senior frontend architect… Scope a small, safe refactor to make navigation responsive/adaptive… Deliver PLAN-NAV.md…“*  
   ➝ Cursor erstellt eine **PLAN-NAV.md** + ersten Überblick, welche Dateien er anfassen wird.

---

### Phase 2: Infrastruktur (Grundlage)
2. **Viewport-Hook & Provider**
   - Prompt: *„Create src/hooks/useViewport.ts and a BreakpointProvider…“*  
   ➝ Damit du überhaupt sauber zwischen `sm/md/lg` unterscheiden kannst.  
   Ohne das macht der Rest keinen Sinn.

---

### Phase 3: API & Modell
3. **Nav-API & gemeinsame Items**
   - Prompt: *„Introduce a shared navigation model… NavVariant, NavItem…“*  
   ➝ Hier entsteht die einheitliche Nav-Schnittstelle, auf die alle Varianten aufsetzen.

---

### Phase 4: Varianten-Implementierung
4. **BottomBar (sm)**
   - Prompt: *„Implement BottomBar.tsx… fixed bottom bar… roving tabindex…“*  
   ➝ Erste konkrete Variante, einfach zu testen.

5. **DrawerNav (md)**
   - Prompt: *„Implement DrawerNav.tsx… persistent left drawer…“*  

6. **SidebarNav (lg)**
   - Prompt: *„Implement SidebarNav.tsx… left sidebar… section headers…“*

---

### Phase 5: Wiring & Utilities
7. **Layout-Wiring**
   - Prompt: *„Wire Nav into the app layout… include BreakpointProvider and Nav…“*  
   ➝ Jetzt hängt deine App an die neue Nav-Struktur dran.

8. **A11y & Hit-Area Utilities**
   - Prompt: *„Add utilities: tokens.css… focus-visible… hit area…“*

---

### Phase 6: Absicherung
9. **QA-Checklist & Playground**
   - Prompt: *„Create NAV-QA.md and a Playground page…“*  
   ➝ Hier kannst du manuell zwischen Varianten durchklicken.

10. **Unit-Tests für Roving Tabindex**
    - Prompt: *„Add tests for roving tabindex behavior…“*

---

## Wichtig
- **Immer warten**, bis Cursor den kompletten Patch + Erklärung für einen Schritt fertig hat, **dann** den nächsten Prompt geben.  
- Falls er mitten im Plan schon Code einfügen will: *annehmen*, aber danach **trotzdem mit Schritt 2 fortsetzen** – sonst fehlt dir die Hook-Basis.  
- Wenn Cursor Dateien vorschlägt, die bei dir nicht existieren, kannst du ihn einfach antworten lassen: *„Passe das auf mein Projekt mit [Next.js/Vite/CRA] an“*.

---

Damit hast du die **Schritt-für-Schritt-Reihenfolge**.  
Möchtest du, dass ich dir diese 10 Prompts noch mal als **kompaktes Copy-Paste-Paket** aufliste (ohne Erklärtext, nur die Prompts in der richtigen Reihenfolge)?

### 10. Benutzer

benötige die genaue reihenfolge für die eingabe der prompts in cursor

### 11. Benutzer

ja

### 12. Assistent

Alles klar – hier das kompakte **Copy-Paste-Paket** für Cursor in der richtigen Reihenfolge. Einfach Prompt für Prompt eingeben, jeweils warten bis Cursor fertig ist, dann den nächsten nehmen.  

---

### 1) Plan
```
Act as a senior frontend architect. Scope a small, safe refactor to make navigation responsive/adaptive.

Constraints:
- Variants: Nav{"mobile_bottom","tablet_drawer","desktop_sidebar"}.
- Breakpoints: sm ≤ 640, md ≤ 1024, lg > 1024; feature detection for (pointer: coarse).
- A11y: roving tabindex, Arrow/Home/End, :focus-visible, min hit area ≥ 44x44.
- No UA sniffing. Use matchMedia via a BreakpointProvider.

Deliverables:
1) PLAN-NAV.md
2) Unified diffs for Nav + related components
3) Demo page with variant toggle

Start by generating PLAN-NAV.md and the first patch set.
```

---

### 2) Viewport-Hook & Provider
```
Create src/hooks/useViewport.ts and a BreakpointProvider:

- useViewport() returns { bp: "sm"|"md"|"lg", coarse: boolean } via matchMedia.
- BreakpointProvider exposes context with manual override.
- Add simple tests (jsdom) to verify transitions.

Return a unified diff and a usage snippet.
```

---

### 3) Nav-API & gemeinsame Items
```
Introduce a shared navigation model:

// src/components/nav/types.ts
export type NavItem = { id:string; label:string; href?:string; onSelect?:()=>void; icon?:React.ReactNode; active?:boolean; disabled?:boolean };

Refactor Nav to:
- export type NavVariant = "mobile_bottom"|"tablet_drawer"|"desktop_sidebar"
- <Nav items={NavItem[]} variant?: NavVariant />
- Default variant from BreakpointProvider
- Dispatch to BottomBar/DrawerNav/SidebarNav

Return unified diffs for types + Nav.tsx.
```

---

### 4) BottomBar (sm)
```
Implement src/components/nav/BottomBar.tsx:

- Fixed bottom bar with 3–5 actions
- Min 44x44 on coarse pointers
- Keyboard: roving tabindex, ArrowLeft/Right, Home/End
- ARIA: role="navigation", aria-label
- Focus ring via :focus-visible

Return a unified diff.
```

---

### 5) DrawerNav (md)
```
Implement src/components/nav/DrawerNav.tsx:

- Persistent left drawer for md
- Keyboard: ArrowUp/Down, Home/End, roving tabindex
- aria-expanded for groups, aria-current for active
- 44px row height on coarse pointers

Return unified diff and usage in Nav.tsx.
```

---

### 6) SidebarNav (lg)
```
Implement src/components/nav/SidebarNav.tsx:

- Left sidebar (280px)
- Support section headers + nested items (1 level)
- aria-labelledby for groups
- Hover + focus-visible styles
- Dense mode optional via prop

Return unified diff and CSS/Tailwind updates.
```

---

### 7) Layout-Wiring
```
Wire Nav into the app layout:

- Wrap app in <BreakpointProvider>
- Import Nav with items from src/navigation.ts
- Add dev-only variant toggle (?navVariant=...)
- Update app/layout.tsx (Next.js) or src/App.tsx (Vite/CRA)

Return unified diff.
```

---

### 8) A11y & Utilities
```
Add utilities:

- tokens.css: :focus-visible outline, spacing/typography tokens
- .hit class with min 44x44 on coarse pointers
- data-roving attribute for tabindex management

Return unified diff and show imports.
```

---

### 9) QA-Checklist & Playground
```
Create NAV-QA.md and a Playground page:

Checklist:
- Variants switch at 641px + 1025px
- Keyboard navigation works (Tab, Arrow, Home/End, Escape)
- Hit area ≥ 44x44
- aria-current="page" on active

Deliverables:
- /src/pages/_playground/nav
- NAV-QA.md with pass/fail boxes

Return unified diffs only.
```

---

### 10) Tests für Roving Tabindex
```
Add tests for roving tabindex:

- Initial active item tabindex=0, others -1
- Arrow keys move focus and update tabindex
- Home/End jump correctly

Provide tests in src/components/nav/__tests__/
Return unified diff.
```

---

Damit hast du eine **klare Eingabereihenfolge** – Schritt 1 bis 10.  

Soll ich dir zusätzlich noch eine **„Quick Rescue“-Version** geben, falls Cursor unterwegs irgendwo hängen bleibt (alles in einem einzigen Prompt zusammengefasst)?

### 13. Benutzer

ja

### 14. Assistent

Alles klar – hier die **Quick-Rescue-Version**: ein einziger Prompt, der Cursor alle Schritte (Plan → Hook → Nav-Varianten → Wiring → QA) in einem Rutsch durchlaufen lässt. Das nutzt du nur, wenn er unterwegs „verhakt“ oder Teile überspringt.  

---

## Quick-Rescue Prompt (Copy-Paste für Cursor)

```
Act as a senior frontend architect. Refactor the navigation of this project into a responsive/adaptive system in one sequence.

Requirements:
- Variants: Nav{"mobile_bottom","tablet_drawer","desktop_sidebar"}
- Breakpoints: sm ≤ 640, md ≤ 1024, lg > 1024
- Feature detection: (pointer: coarse), no UA sniffing
- Accessibility: roving tabindex, Arrow/Home/End keys, :focus-visible, hit area ≥ 44x44 on coarse pointers, aria-current on active
- Shared model: NavItem {id,label,href?,onSelect?,icon?,active?,disabled?}
- Hook: src/hooks/useViewport.ts returning {bp:"sm"|"md"|"lg", coarse:boolean}, BreakpointProvider for context
- Components:
  - BottomBar.tsx (sm, fixed bottom bar, 3–5 actions)
  - DrawerNav.tsx (md, persistent left drawer)
  - SidebarNav.tsx (lg, 280px sidebar, nested groups)
- Nav.tsx dispatches to correct variant, default from BreakpointProvider
- Wiring: Wrap app in BreakpointProvider, render Nav with items from src/navigation.ts; dev-only ?navVariant=... override
- Utilities: tokens.css with spacing/typography/focus-visible styles, .hit class (≥44x44), data-roving for tabindex
- QA: create NAV-QA.md + /src/pages/_playground/nav with checklist
- Tests: add __tests__/NavRoving.test.tsx for tabindex/keyboard behavior

Deliverables:
1) PLAN-NAV.md describing affected files and steps
2) Unified diff patches for all files (hooks, nav components, layout wiring, utilities, playground, tests)
3) NAV-QA.md checklist
4) All patches must be minimal and composable; commit messages should follow Conventional Commits (feat/ui/nav: ...)

Return PLAN-NAV.md first, then the patches, then NAV-QA.md.
```

---

Damit zwingst du Cursor, **Plan + Implementation + QA + Tests** in einem Rutsch auszugeben.  

Willst du, dass ich dir zusätzlich noch einen **Fallback-„Mini-Prompt“** schreibe, der nur **eine einzelne Datei** (z. B. `Nav.tsx`) schnell in „variant-fähig“ umbaut?

### 15. Benutzer

ja

### 16. Assistent

Hier ist der **Mini-Prompt für eine einzelne Datei** (z. B. `src/components/nav/Nav.tsx`). Er zwingt Cursor zu einem minimal-invasiven, diff-basierten Umbau mit Varianten, Tastaturnavigation und ohne UA-Sniffing.

---

## Single-File Rescue Prompt (Copy-Paste in Cursor)

```
Refactor ONLY the provided file to make the navigation responsive/adaptive with minimal changes.
Return a unified diff patch for this file and nothing else.

Goals:
- Add a `variant?: "mobile_bottom" | "tablet_drawer" | "desktop_sidebar"` prop.
- If `variant` is not provided, default it from a Breakpoint context hook `useViewport()` that returns { bp: "sm"|"md"|"lg", coarse: boolean }.
  - Fallback mapping: sm -> "mobile_bottom", md -> "tablet_drawer", lg -> "desktop_sidebar".
  - Do NOT use user-agent sniffing.

Accessibility:
- Implement roving tabindex on the nav items:
  - Exactly one item has `tabIndex=0`, others `-1`.
  - ArrowLeft/Right (or Up/Down, depending on orientation) moves focus.
  - Home/End jump to first/last item.
  - Preserve native <a> for links; set `aria-current="page"` for the active item.
  - Use `:focus-visible` (do not remove outlines).
- Ensure hit area for interactive items is at least 44x44 when `(pointer: coarse)` is true. Add a utility class if necessary.

Implementation constraints:
- Keep public API backward compatible: if no variant prop is passed, current behavior should still work but use the new default mapping.
- Extract a small internal `NavItemButton` (or equivalent) to host keyboard/focus logic and aria attributes.
- Do NOT change unrelated code or styles; minimal churn.
- If `useViewport` is unavailable in this repo, create a tiny inline fallback that uses `window.matchMedia` behind a safe `typeof window !== "undefined"` guard and TODO-comment to replace with the real hook.

Deliverables:
- A single unified diff patch for this file.
- The diff must include:
  - `variant` prop type and selection logic.
  - Roving tabindex state and keyboard handlers (Arrow*, Home, End).
  - `aria-current="page"` for the active route.
  - Conditional min-size style/class for coarse pointers (44x44).
- No extra prose, no new files, no tests in this step—just the diff.
```

---

Tipp fürs Nachziehen: Sobald die Datei sitzt, gib den **Auffang-Prompt für Utilities** (Tokens, `.hit`-Klasse) oder den **Viewport-Hook-Prompt** aus der großen Folge hinterher, damit der Inline-Fallback verschwindet.

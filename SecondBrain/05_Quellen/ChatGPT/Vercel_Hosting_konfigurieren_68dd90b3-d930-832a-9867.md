---
title: "Vercel Hosting konfigurieren"
type: chatgpt_conversation
source: chatgpt
source_id: "68dd90b3-d930-832a-9867-ebbdb307dac7"
created: 2025-10-01
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
---


# Vercel Hosting konfigurieren

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68dd90b3-d930-832a-9867-ebbdb307dac7`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Ich habe mit loveable ein onlinetool erstellt dieses nach GitHub gepusht und möchte es nun auf Vercel hoasten. Was muss ich wie konfigurieren

### 2. Assistent

Alles klar, Markus—hier ist die kurz-bis-gründliche Anleitung, um dein Repo (von „Lovable“ generiert, auf GitHub gepusht) sauber auf **Vercel** zu bringen. Ich gebe dir erst den generellen Ablauf und danach die wichtigsten Konfigurationen je nach Stack (Next.js, Vite/React, SvelteKit, Remix, statisches SPA, Node/Express-API). Dazu ein paar „klassische Stolperfallen“.

---

# 1) Einmal-Setup: Repo → Vercel

1) **Vercel-Account & GitHub verbinden**  
   - In Vercel auf **“Add New…” → “Project”** → GitHub autorisieren → dein Repo wählen.

2) **Project Settings prüfen** (während des Imports)  
   - **Framework Preset**: Vercel erkennt meist automatisch (Next.js, Vite, SvelteKit, Remix).  
   - **Root Directory** (bei Monorepo): Unterordner wählen, in dem `package.json` liegt.  
   - **Build Command**: z. B. `npm run build` / `pnpm build` / `yarn build`.  
   - **Install Command**: Vercel erkennt Lockfile, sonst z. B. `pnpm install --frozen-lockfile`.  
   - **Output Directory** (nur für Static Bundler wie Vite/CRA): i. d. R. `dist`.  
   - **Environment Variables**: direkt hier anlegen (siehe unten).

3) **Erster Deploy**  
   - Vercel baut das Projekt, zeigt dir Logs. Nach Erfolg bekommst du eine **Preview-URL**.  
   - Über **“Production Deploy”** oder Merge in `main` geht’s auf Prod. Jeder PR bekommt eigene Preview-Deployments.

4) **Domain**  
   - In **Settings → Domains** eigene Domain hinzufügen, DNS auf Vercel zeigen lassen. HTTPS ist automatisch.

---

# 2) Environment Variables (wichtig!)

- In **Project → Settings → Environment Variables** anlegen: `KEY=VALUE`, pro Environment (Development / Preview / Production).  
- **Client-seitig** sichtbare Variablen **müssen** mit Framework-Prefix exposed werden:
  - Next.js: `NEXT_PUBLIC_*`
  - Vite/React: `VITE_*`
  - SvelteKit: `PUBLIC_*`
- **Server-only** Variablen ohne Prefix (z. B. DB-URL, API-Keys).

---

# 3) Node-Version & Package-Manager

- Lege die Node-Version fest (stabil und reproduzierbar):
  - in `package.json`:
    ```json
    { "engines": { "node": ">=18 <21" } }
    ```
  - oder `.nvmrc` / `.node-version`.
- Lockfile nutzen (`pnpm-lock.yaml`/`yarn.lock`/`package-lock.json`) → Vercel wählt den passenden Installer.

---

# 4) Framework-spezifische Settings

## A) **Next.js (empfohlen, wird auto-erkannt)**
- **Keine** spezielle `vercel.json` nötig.  
- Standard:
  - Build: `next build`
  - Output: Vercel regelt (Serverless/Edge je nach Verwendung).
- **App Router** (Next 13+): funktioniert out of the box, inkl. Routen, Images, Middleware.  
- **API-Routen**: `app/api/**/route.ts` oder `pages/api/*.ts` → landen als Serverless/Edge Functions.  
- **Public Env**: `NEXT_PUBLIC_*`.  
- **Edge-Runtime** (optional pro Route):
  ```ts
  export const runtime = 'edge';
  ```
- **Bilder**: in `next.config.js` Domain-Allowlist setzen, wenn du externe Images lädst.

## B) **Vite/React**
- `package.json`:
  ```json
  {
    "scripts": {
      "dev": "vite",
      "build": "vite build",
      "preview": "vite preview"
    }
  }
  ```
- Vercel-Einstellungen:
  - **Build Command**: `pnpm build` (oder npm/yarn)
  - **Output Directory**: `dist`
- **Client-Routing (SPA)**: Alles auf `index.html` umschreiben (sonst 404 bei Deep-Links).  
  Lege `vercel.json` an:
  ```json
  {
    "rewrites": [{ "source": "/(.*)", "destination": "/" }]
  }
  ```
- **Public Env**: `VITE_*`.

## C) **SvelteKit**
- Adapter für Vercel:
  ```bash
  pnpm add -D @sveltejs/adapter-vercel
  ```
  `svelte.config.js`:
  ```js
  import adapter from '@sveltejs/adapter-vercel';
  export default { kit: { adapter: adapter() } };
  ```
- Build: `svelte-kit build` (über Scripts).
- Env: `PUBLIC_*` ist client-seitig sichtbar; Rest server-only.

## D) **Remix**
- Adapter:
  ```bash
  pnpm add -D @remix-run/vercel
  ```
- `remix.config.js`:
  ```js
  module.exports = { serverBuildTarget: "vercel" };
  ```
- `vercel.json` (häufig nicht nötig, aber für SPA-ähnliche Rewrites möglich).

## E) **Statisches SPA (z. B. CRA, Astro static)**
- Build/Output wie dokumentiert (meist `dist` oder `build`).  
- **Single-Page-Rewrite**:
  ```json
  {
    "rewrites": [{ "source": "/(.*)", "destination": "/" }]
  }
  ```

## F) **Node/Express-API auf Vercel**
Vercel setzt auf **Serverless/Edge Functions**. Klassisches `express().listen()` musst du anpassen:

- Lege eine Serverless Function an: `api/server.ts`
  ```ts
  import type { VercelRequest, VercelResponse } from '@vercel/node';
  export default async function handler(req: VercelRequest, res: VercelResponse) {
    res.status(200).json({ ok: true });
  }
  ```
- Routen mit **Rewrites** auf die Function schicken (falls du „alles“ serverseitig willst):
  ```json
  {
    "rewrites": [
      { "source": "/api/(.*)", "destination": "/api/server" }
    ]
  }
  ```
- Falls du **Express** behalten willst: oft via `serverless-http`:
  ```ts
  import express from 'express';
  import serverless from 'serverless-http';
  const app = express();
  app.get('/api/hello', (_req, res) => res.json({ hi: 'there' }));
  export const handler = serverless(app);
  export default handler;
  ```
  Datei: `api/index.ts` → Endpunkt `/api`.

> Merke: Langläufer, WebSockets und stateful Server sind in Serverless nur eingeschränkt geeignet. Für WebSockets eher Edge Runtime, Pusher, Ably etc. nutzen.

---

# 5) Datenbanken & Migrations

- Vercel hostet keine DB. Nutze externe Anbieter (Postgres/MySQL/Redis/Planetscale/Supabase/Neon).  
- **Prisma**:  
  - `DATABASE_URL` als Env in Vercel.  
  - `postinstall` oder `build`:
    ```json
    { "scripts": { "postinstall": "prisma generate" } }
    ```
  - **Migrations**: In CI/CD entweder `prisma migrate deploy` im Build ausführen **oder** separat über Release-Workflow/Launch Scripts.  
  - Edge-Runtime benötigt Edge-taugliche Treiber (z. B. HTTP-Driver oder Data Proxy).

---

# 6) Caching, Headers, Redirects

- In `vercel.json`:
  ```json
  {
    "headers": [
      { "source": "/assets/(.*)", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }] }
    ],
    "redirects": [
      { "source": "/alt", "destination": "/", "permanent": false }
    ]
  }
  ```
- Next.js hat eigene Header/Redirect-APIs (`next.config.js`), bevorzugt diese, wenn du Next nutzt.

---

# 7) Monorepos

- **Root Directory** im Import-Dialog/Settings auf das App-Verzeichnis setzen.  
- Falls du interne Pakete hast: pnpm-Workspaces verwenden; ggf. `pnpm-workspace.yaml` + `packageManager` im Root.  
- In Vercel **“Ignored Build Step”** hinterlegen (optional), um unnötige Deploys zu vermeiden, z. B.:
  ```
  git diff --quiet HEAD^ HEAD -- path/to/app || exit 1
  ```

---

# 8) Lokales Testen mit Vercel CLI

```bash
pnpm add -D vercel
npx vercel login
npx vercel link
npx vercel dev
```
So siehst du Functions/SSR/Edge lokal möglichst vercel-nah.

---

## Häufige Stolperfallen (und schnelle Abhilfe)

- **404 bei Deep-Links** in SPA → `vercel.json` Rewrites auf `/`.  
- **Env wird im Client nicht gesehen** → Prefix (`NEXT_PUBLIC_`, `VITE_`, `PUBLIC_`).  
- **“Module not found / CJS vs ESM”** → `"type": "module"` prüfen, ggf. Imports anpassen, Node-Version alignen.  
- **Bildoptimierung blockt externe Domains** (Next.js) → in `next.config.js` `images.remotePatterns`/`domains` setzen.  
- **Cold Starts** spürbar? → Prüfe Edge Functions für kleine, latenzkritische Handler.  
- **Lange Builds** → Caching (Lockfile beibehalten), unnötige Dev-Dependencies entfernen, optional Turborepo.

---

## Minimal-Beispiele für `vercel.json`

**SPA (Vite/React):**
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/" }]
}
```

**API-Gateway zu einer Function:**
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/server" }
  ]
}
```

**Statische Assets hart cachen:**
```json
{
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }]
    }
  ]
}
```

---

Wenn du mir sagst, welches Framework dein Lovable-Projekt konkret ausspuckt (Next, Vite/React, SvelteKit, Remix oder etwas Eigenes), liefere ich dir die exakt passenden Build-Kommandos, eine maßgeschneiderte `vercel.json` und—falls nötig—Beispiele für API-Routen oder Edge-Funktionen. Alternativ kann ich deine `package.json` und Ordnerstruktur durchgehen und dir die präzisen Schalter setzen.

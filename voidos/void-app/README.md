# Void Alpha App

Void Alpha is the first installable command surface for the Void civilization platform.

It combines a public-safe access surface with a protected citizen shell:

- open citizen registration and per-citizen session flow;
- social civilization feed derived from real platform actions;
- local AI companion preview for every citizen;
- subnet, quest, and marketplace coordination;
- proof submission and verification;
- closed-loop Pulse Credits and citizen-to-citizen flow;
- impact, reputation, title, and legacy records;
- beta feedback triage;
- public legal and roadmap pages;
- mobile-friendly PWA packaging.

Pulse Credits are closed-loop internal software credits only. They have no cash value, no redemption path, no external exchange, and no investment promise.

## Run Locally

```text
npm install
npm run local
```

The local preview usually runs at:

```text
http://127.0.0.1:8090
```

## Verify

```text
npm run check
npm run build
```

## Operating Modes

| Mode | Purpose |
| --- | --- |
| Local preview | Founder-side inspection using local browser storage and offline fallback. |
| Private preview | Per-citizen sessions, shared persistence, and protected server actions for controlled testing. |
| VPS runtime | Static app plus Node API at `/api/void`, `/api/void/session`, and `/api/void/health`. |
| Public launch | Future state after auth, database, legal, security, and managed VPS hosting review are complete. |

## Deployment Environment

Forward hosting target is managed VPS, not future Netlify pushes. Set these on the server runtime before production-like deploys:

```text
VOID_ADMIN_KEY=private-admin-key
VOID_SESSION_SECRET=private-session-signing-secret-at-least-32-characters
VOID_DATA_DIR=/srv/void/data
PORT=3000
HOST=127.0.0.1
VOID_TRUST_PROXY=false
VITE_VOID_API_PATH=/api/void
VITE_VOID_SESSION_PATH=/api/void/session
```

The first VPS-compatible runtime is intentionally simple:

```text
npm run vps:build
npm run vps:start
```

It serves the Vite `dist/` app, `GET /api/void/health`, `GET/POST /api/void`, and `POST /api/void/session`. Current VPS persistence is file-backed through `VOID_DATA_DIR`. PostgreSQL remains the next beta launch gate before public beta. Keep `VOID_TRUST_PROXY=false` unless the reverse proxy strips client-supplied forwarding headers and rewrites them itself.

Citizens register with email plus a private account phrase, then open a per-citizen session without founder approval. Admin authority is reserved for elevated access, Pulse credits, quest verification, and state reset.

Keep `VITE_VOID_OPERATOR_CONSOLE=false` for public or shared previews so admin inspection controls stay hidden. Keep all secrets out of GitHub, screenshots, docs, prompts, and client code.

## Brand

The app uses the founder-approved Void Civilization Platform logo from [`../docs/brand/void-official-logo.png`](../docs/brand/void-official-logo.png). Root repo presentation assets live in [`../docs/brand`](../docs/brand).

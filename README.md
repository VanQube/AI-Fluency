# SecureShip — Project Context for Claude Code

## What this is
SecureShip is an AI-gated shipment support chat app. The chat *is* the product:
customers talk to an LLM to check on shipments, but only after conversational
identity verification (name, address, phone, then a 6-digit 2FA code) unlocks
access to their shipment data. There is no end-user signup/login — identity is
per-session, not account-based. The only persistent login is a single admin
account for managing package/shipment data.

Full program spec lives at `/docs/SecureShip-5Week-Program.md`, split by
section into `/docs/secureship/` — refer to it for anything not summarized
below (Epics A–G, Section 4 full requirements, Section 6 architecture
diagrams, Section 9 model setup). Live build status: `/docs/PROGRESS.md`.

## Implemented
- React (Create React App + JavaScript) chat UI, styled with Tailwind CSS,
  talking to a real backend via generated React Query hooks (no hand-written
  fetch calls — Section 4.8)
- FastAPI backend (`/health`, `/chat`, `/verify-code`) persisting every turn
  to Postgres
- Postgres with `customers` / `shipments` / `packages` / `chat_sessions`
  tables, seeded via `scripts/seed_data.py`
- Ollama running on the **host** (not containerized — Section 4.7, Metal
  acceleration) with `qwen3:8b` pulled and verified for tool-calling support
- The backend's `/chat` endpoint calls Ollama directly and returns real model
  replies through the chat UI
- Orval generates typed React Query hooks from the backend's live
  `/openapi.json` (`npm run generate:api` inside `frontend/`)
- Full Docker Compose dev environment (frontend, backend, postgres containers)
- **Identity collection + 2FA gate (Epics B, C, G)** — the full
  Anonymous → CollectingIdentity → CodeSent/AwaitingCode → Verified state
  machine, backend-orchestrated (not native LLM tool-calling — see
  `docs/PROGRESS.md` Week 2 for the design call). Identity matching
  (`backend/tools/verify_identity.py`), mocked 2FA with a 10-min expiry and
  3-attempt lockout (`backend/tools/`), the on-demand `CodeModal`, and the
  cosmetic human-escalation sequence (Epic G) are all wired end-to-end.

There is **no shipment-lookup tool-calling yet (Epic F)** — a verified
session can chat, but there's still nothing that hands it real shipment
data. That's Week 3.

## Not yet implemented
- Tool-calling / gating enforcement for shipment data (`lookup_shipments`,
  etc.) (Epic F)
- Admin panel + Auth0 (Epic E)

## Tech stack
- Frontend: React (Create React App) + JavaScript + Tailwind CSS + React
  Query (via Orval-generated hooks)
- Backend: Python + FastAPI + SQLAlchemy (sync), Postgres 16
- Local LLM: Ollama (host-installed) running `qwen3:8b`
- Dev environment: Docker Compose (frontend, backend, postgres containers;
  Ollama stays on the host — see Section 4.7)

> Notes on deliberate tradeoffs, documented so they're not mistaken for
> oversights:
> - Create React App is no longer maintained upstream. Chosen for this
>   team's stack preference.
> - Orval's generated output is TypeScript-only (it needs `interface`/`type`
>   syntax), so TypeScript is installed *only* to let CRA accept the
>   generated `src/api/generated/` folder — everything hand-written elsewhere
>   in the frontend stays plain `.js`. Pinned to TS 4.9.x because react-scripts
>   5's peer dependency range is `^3.2.1 || ^4`.
> - Tailwind is pinned to v3.x — CRA's built-in PostCSS integration
>   auto-detects the v3 `tailwindcss` postcss-plugin form; v4 changed its
>   plugin package name and isn't picked up the same way without ejecting.

## Data schema (must match exactly — do not shrink, extending is fine)
```
Customer
  - id (uuid)
  - first_name (string)
  - last_name (string)
  - phone_number (string, E.164 mocked, e.g. +1XXXXXXXXXX)
  - address (string, single-line mocked US/EU-style address)

Shipment
  - id (uuid)
  - customer_id (uuid, FK -> Customer.id)
  - tracking_number (string, mocked carrier-style format)
  - status (enum: "label_created" | "in_transit" | "out_for_delivery" | "delivered" | "exception")
  - carrier (string, mocked, e.g. "MockExpress")
  - origin (string)
  - destination (string)
  - estimated_delivery (date)
  - last_update (datetime)

Package (admin-managed; a Shipment can have 1+ Packages)
  - id (uuid)
  - shipment_id (uuid, FK -> Shipment.id)
  - description (string)
  - weight_kg (decimal)
  - declared_value (decimal)
```
Seeded: 25 customers, 50 shipments (realistic status distribution), 74
packages — via `scripts/seed_data.py`, re-runnable and deterministic (seeded
RNG).

## Running it
```bash
# 1. Ollama on the host (once)
brew install ollama
ollama serve &                 # or `brew services start ollama`
ollama pull qwen3:8b

# 2. Everything else via Docker Compose
docker compose up -d --build
docker compose exec backend python scripts/seed_data.py   # first run only

# App: http://localhost:3000
# Backend health: http://localhost:8000/health
# Backend OpenAPI: http://localhost:8000/openapi.json
```
Whenever backend routes/schemas change: `cd frontend && npm run generate:api`
to regenerate the typed hooks, then commit the regenerated output.

## Folder structure
```
/docs
  SecureShip-5Week-Program.md
  system-prompt.md      <- persona spec, read by routes/chat.py
  /diagrams             <- Mermaid diagrams from Section 6 (starting reference)
  /certificates          <- Skilljar certs from Section 2's parallel track
/scripts
  seed_data.py           <- Postgres seed script (mounted into backend container)
/frontend
  Dockerfile
  orval.config.js        <- points at backend's live /openapi.json
  tsconfig.json           <- generated-code-only TS support (see tradeoffs above)
  /src
    /api/generated        <- Orval output, do not hand-edit
    /components          <- ChatWindow, MessageList, MessageInput, CodeModal
/backend
  Dockerfile
  main.py                <- app entrypoint, health-check, CORS
  gating.py               <- Section 6.2 state machine, orchestrates chat + verify-code
  /routes                <- chat.py, verify.py
  /tools                  <- verify_identity, send/check_verification_code, intent heuristics
  /llm                     <- ollama_client.py, extraction.py (identity-field extraction)
  /models                  <- Customer, Shipment, Package, ChatSession (SQLAlchemy)
  /db                      <- session.py (engine/session), base.py
  /schemas                 <- Pydantic request/response models (chat.py, verify.py)
docker-compose.yml
README.md
```

## Non-functional habits
- No PII in logs, even mocked PII — build this habit from day one
- The Ollama call is isolated in `backend/llm/ollama_client.py` so adding
  tool-calling later doesn't mean rewriting the chat endpoint
- The system-prompt/persona doc (`docs/system-prompt.md`) is written as if
  pasted directly into a real model's system prompt — no throwaway wording

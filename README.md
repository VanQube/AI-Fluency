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
- FastAPI backend (`/health`, `/chat`, `/verify-code`, `/admin/*`)
  persisting every chat turn to Postgres
- Postgres with `customers` / `shipments` / `packages` / `chat_sessions`
  tables, seeded via `scripts/seed_data.py`
- Ollama running on the **host** (not containerized — Section 4.7, Metal
  acceleration) with `qwen3:8b` pulled, used both for plain chat and native
  tool-calling
- Orval generates typed React Query hooks from the backend's live
  `/openapi.json` (`npm run generate:api` inside `frontend/`)
- Full Docker Compose dev environment (frontend, backend, postgres containers)
- **Identity collection + 2FA gate (Epics B, C, G)** — the full
  Anonymous → CollectingIdentity → AwaitingCode → Verified state machine
  (see `docs/diagrams/02-conversation-state-machine.md` for the exact
  transitions), backend-orchestrated (not native LLM tool-calling — see
  `docs/PROGRESS.md` Week 2 for the design call). Identity matching
  (`backend/tools/verify_identity.py`), mocked 2FA with a 10-min expiry and
  3-attempt lockout (`backend/tools/`), the on-demand `CodeModal`, and the
  cosmetic human-escalation sequence (Epic G) are all wired end-to-end.
  Routing between these branches (and the shipment/human-request intents
  below) runs on a single-call LLM classifier (`backend/llm/intent_classifier.py`)
  rather than hand-maintained regex, per the Week 2 design change.
- **Tool-calling for shipment data (Epic F)** — verified sessions get real
  answers via native Ollama tool-calling (`backend/tools/lookup_shipments.py`,
  `chat_with_tools()` in `backend/llm/ollama_client.py`). The tool layer
  always scopes lookups to `session.customer_id`, never a model- or
  user-supplied id, and unverified branches are backstopped by a
  disclosure-scanning guard (`_guarded_unverified_reply_stream` in
  `backend/gating.py`) in case a routing miss lets a shipment question
  through unverified. `scripts/test_tool_scoping.py` covers both the
  structural scoping guarantees and a live adversarial prompt-injection
  attempt.
- **Admin panel + Auth0 (Epic E)** — a separate, Auth0-gated system (real
  Authorization Code + PKCE login, not the chat's conversational
  verification) for full CRUD on Customer/Shipment/Package records.
  Backend JWT validation via `auth0-fastapi-api` (`backend/admin_auth.py`,
  gating every `/admin/*` route); frontend login via `@auth0/auth0-react`
  (`frontend/src/admin/`), reachable via the "Admin login" link on the chat
  page or directly at `/admin`. Any authenticated Auth0 user is treated as
  an admin — no separate allowlist/role check. Confirmed live: an admin
  token has no effect on `/chat`/`/verify-code` and vice versa (Epic E4),
  and an admin edit to a shipment shows up immediately in an already-open
  verified chat session (no caching layer to invalidate).

## Not yet implemented
Everything through Week 4 (Epics A–G) is functionally complete and
click-through verified. Week 5's required hardening pass is done: code
review closed out (Phase 0), diagrams regenerated (Phase 1), and an
edge-case pass covering expired codes, malformed input, empty states, and
the mid-verification give-up path (Phase 3) — including a real bug found
and fixed (a customer who abandoned verification after a code expired was
silently re-verified and sent a new code instead of being released back to
free-form chat). Of the optional stretch goals: an admin chat-session
viewer and a codegen-suggestion Agent Skill are done; containerizing Ollama
was built, benchmarked, and deliberately **not** adopted as the default
(kept as an opt-in `docker-compose.ollama.yml` override — CPU-only
inference in the container was consistently slower than the host's
Metal-accelerated setup, badly enough on a cold start to be disqualifying);
real Twilio SMS was dropped — Twilio has no free trial for Serbia, and this
is an unpaid training project. Mocked SMS (console/log only) stays the only
2FA delivery path. llama.cpp instead of/alongside Ollama was never
attempted and is also being dropped — the containerization benchmark
already answered the interesting question here. See `docs/PROGRESS.md` for
the full writeup of what was verified live (including how the llama.cpp
goal got missed) and `docs/final-demo-script.md` for the Friday walkthrough
plan.

## Tech stack
- Frontend: React (Create React App) + JavaScript + Tailwind CSS + React
  Query (via Orval-generated hooks) + `react-router-dom` (chat vs. `/admin`)
- Backend: Python + FastAPI + SQLAlchemy (sync), Postgres 16
- Local LLM: Ollama (host-installed) running `qwen3:8b`, used both for plain
  chat and native tool-calling
- Admin auth: Auth0 — `auth0-fastapi-api` (backend JWT validation),
  `@auth0/auth0-react` (frontend login), built using the Auth0 Agent Skills
  for Claude Code rather than a hand-rolled integration (Section 4.5)
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

There is no local `ADMIN_USER` table — Auth0 is the sole source of truth for
admin identity (any authenticated Auth0 user is treated as an admin), per
the ERD note in `docs/secureship/06-architecture.md`.

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
# Admin panel: http://localhost:3000/admin (or the "Admin login" link on the
#              chat page) — requires a real Auth0 tenant, see below
# Backend health: http://localhost:8000/health
# Backend OpenAPI: http://localhost:8000/openapi.json
```
Whenever backend routes/schemas change: `cd frontend && npm run generate:api`
to regenerate the typed hooks, then commit the regenerated output.

**Admin panel / Auth0 setup:** the admin panel needs a real Auth0 tenant —
an SPA application (for the React frontend) and an API resource (for the
FastAPI backend), both created by hand in the Auth0 Dashboard (the Agent
Skill accelerates the code, not the tenant itself — see Section 4.5). Once
created, the SPA app must be explicitly authorized for the API under
**Applications → APIs → [API] → Application Access → [app] →
User-Delegated Access** (not the adjacent "Client Access" tab, which is for
the unrelated machine-to-machine grant). The domain, SPA client ID, and API
audience go into `docker-compose.yml`'s `environment:` blocks
(`AUTH0_DOMAIN`/`AUTH0_AUDIENCE` for `backend`,
`REACT_APP_AUTH0_DOMAIN`/`REACT_APP_AUTH0_CLIENT_ID`/`REACT_APP_AUTH0_AUDIENCE`
for `frontend`) — none of these are secrets (no client secret is used; the
SPA flow is public-client PKCE). The SPA app's Allowed Callback/Logout URLs
need both `http://localhost:3000/admin` and bare `http://localhost:3000`
(the logout button returns to the chat page, not back into `/admin`).

## Folder structure
```
/docs
  SecureShip-5Week-Program.md
  system-prompt.md      <- persona spec, read by routes/chat.py
  /diagrams             <- Mermaid diagrams from Section 6, regenerated
                          against the real build (Week 5 Phase 1)
  /certificates          <- Skilljar certs from Section 2's parallel track
/scripts
  seed_data.py           <- Postgres seed script (mounted into backend container)
  test_tool_scoping.py    <- Epic F enforcement checks (structural + live adversarial)
/frontend
  Dockerfile
  orval.config.js        <- points at backend's live /openapi.json
  tsconfig.json           <- generated-code-only TS support (see tradeoffs above)
  /src
    App.js                <- routes: "/" (chat) vs "/admin" (ProtectedRoute + AdminApp)
    index.js               <- QueryClientProvider, BrowserRouter, Auth0Provider
    /api/generated        <- Orval output, do not hand-edit
    /components          <- ChatWindow, MessageList, MessageInput, CodeModal
    /admin                 <- Epic E — AdminApp, ProtectedRoute, CustomerManager,
                              ShipmentManager, PackageManager, AdminTable, authFetch.js,
                              ChatSessionViewer (Week 5 stretch goal, read-only)
/backend
  Dockerfile
  main.py                <- app entrypoint, health-check, CORS
  gating.py               <- Section 6.2 state machine, orchestrates chat + verify-code
  admin_auth.py            <- Epic E3 — Auth0FastAPI JWT validation, require_admin dependency
  /routes                <- chat.py, verify.py, admin.py
  /tools                  <- verify_identity, send/check_verification_code,
                              lookup_shipments (Epic F), intent.py (tracking-number regex only)
  /llm                     <- ollama_client.py (plain chat + tool-calling),
                              extraction.py (identity fields), intent_classifier.py (routing)
  /models                  <- Customer, Shipment, Package, ChatSession (SQLAlchemy)
  /db                      <- session.py (engine/session), base.py
  /schemas                 <- Pydantic request/response models (chat.py, verify.py, admin.py)
docker-compose.yml
docker-compose.ollama.yml  <- opt-in override, containerized Ollama
                              (Week 5 stretch goal — benchmarked, not
                              adopted as default; see docs/PROGRESS.md)
README.md
```

## Non-functional habits
- No PII in logs, even mocked PII — build this habit from day one
- The Ollama call is isolated in `backend/llm/ollama_client.py` so adding
  tool-calling later doesn't mean rewriting the chat endpoint
- The system-prompt/persona doc (`docs/system-prompt.md`) is written as if
  pasted directly into a real model's system prompt — no throwaway wording

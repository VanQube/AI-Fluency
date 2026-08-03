# 4. The Product: Full Requirements

[Index](../SecureShip-5Week-Program.md) · [Progress Tracker](../PROGRESS.md)

### 4.1 In scope

- Public-facing **frontend** with a chat window as the primary interface
- **Backend API** serving the frontend and orchestrating the local LLM
- A **locally-run open-source LLM** (via Ollama) powering the chat
- **Identity collection flow**: first name, last name, address, phone number
- **Mock SMS 2FA**: a 6-digit code "sent" (mocked, console/log-based minimum — real SMS via a free-tier provider like Twilio is an optional stretch goal, team's choice) and a **modal that appears on demand** for the user to enter the code
- A **"secure" conversational session** post-verification, during which the user can ask about shipments tied to their verified name/account
- **Tool-calling architecture**: the local model does not get raw database access — it calls defined tools/functions (`lookup_shipments_by_customer`, etc.) and the backend enforces gating
- **Human escalation theater**: when a user explicitly asks to talk to a human (e.g. "I want to talk to a human"), the chat runs a scripted, cosmetic handoff sequence — see Epic G in Section 5 and the dedicated diagram in Section 6.2b
- **Chat session storage**: every conversation is persisted as structured data (Postgres `JSONB`, not a separate database — see Section 4.6) so it can be inspected later
- **Containerized local dev environment**: frontend, backend, and Postgres run via Docker Compose (Section 4.7) — this is the baseline expectation, not a stretch goal
- **Admin-only login** (via Auth0, built using the Auth0 Agent Skills — Section 4.5) to create/edit/delete package and shipment records
- **No end-user accounts, no end-user login, ever** — identity is conversational, not credential-based
- Full **Mermaid architecture diagrams** (provided in Section 6, to be regenerated/corrected by each team for their actual implementation)
- A **team-authored README** per repo (AI-drafted, human-corrected) explaining their build

### 4.2 Explicitly out of scope (don't gold-plate this)

- Real carrier SMS integration as a *requirement* (optional stretch only)
- Payment processing
- Multi-language support
- Production-grade horizontal scaling, load balancing, or multi-tenant infrastructure
- Real customer PII handling — **all data is synthetic/mocked**, see Section 4.4

### 4.3 Non-functional requirements

| Requirement | Detail |
|---|---|
| **Identity gate must be enforced server-side** | The frontend "looking gated" is not enough. If a clever request can hit the backend directly and get shipment data without a verified session, that's a failed gate, not a passed one |
| **No PII in logs** | Even mocked PII shouldn't get printed to permanent logs in plaintext beyond local dev console output. This is a habit-forming requirement from day one, and becomes something mentors explicitly check for from Phase 2 onward |
| **Local model only for the chat** | Calling out to Claude/OpenAI/etc. APIs for the core chat defeats the point of this exercise. Teams *may* use Claude (via Claude Code) to **build** the app — that's expected and encouraged — but the chat's runtime brain must be the local Ollama model |
| **Session-based, not account-based** | A verified identity should be tied to a session/conversation, not a stored login. Re-verification on a new session is expected behavior, not a bug |
| **Stack-agnostic but Python/React preferred** | Nobody cares what's under the hood beyond whether it works. Mentorship support is strongest for Python (FastAPI/Flask) backend + React frontend, so teams choosing otherwise should expect to debug more independently |
| **Admin auth is implemented via Auth0, using Auth0's own Agent Skills** | Auth0 is the provider for admin login (Epic E). Teams build it using the **Auth0 Agent Skills for Claude Code** (Section 4.5) rather than hand-writing the integration from scratch. This is a deliberate teaching choice: it's the program's hands-on example of a *provider-supplied* agent skill — as opposed to a skill the team writes itself — accelerating a real integration, and it's worth treating as a mini case study at the Week 4 milestone (Section 8) |
| **Chat session storage is structured, not log-file text** | Every conversation (messages, state transitions, outcome) is persisted as structured JSON in a Postgres `JSONB` column — not scraped from plaintext logs after the fact. See Section 4.6 |
| **The dev environment is Docker Compose-able** | `docker-compose up` should bring up frontend, backend, and Postgres as containers. See Section 4.7 for what's required vs. bonus |
| **No hand-written API types or fetch calls** | Frontend types and (for the HTTP path) API client hooks are generated from the backend's OpenAPI schema via Orval, not hand-written and kept in sync manually. See Section 4.8 |

### 4.4 Mock data requirements

All shipment, customer, and package data is **AI-generated**, but must conform to a shared schema so it's consistent and comparable across teams. This is a deliberate constraint: "AI generates everything" doesn't mean "anything goes" — it means use AI to produce data, but to a spec.

**Minimum schema (teams may extend, not shrink):**

```text
Customer
  - id (uuid)
  - first_name (string)
  - last_name (string)
  - phone_number (string, E.164 format mocked, e.g. +1XXXXXXXXXX)
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

Each team should generate **at least 25 customers** and **40–60 shipments** with realistic status distribution (most "in_transit" / "delivered", a few "exception" to give the chat something interesting to discuss) using Claude Code, a seed script, or a Faker-style library invoked by Claude Code. The generation script itself should live in the repo (`/scripts/seed_data.py` or similar) — not just a one-off CSV with no provenance.

### 4.5 Auth0 Agent Skills — the program's example of a provider-supplied skill

Anthropic's own "Introduction to Agent Skills" course (Section 2.2) teaches engineers to *write* a `SKILL.md`. Auth0's Agent Skills package is the complementary half of that lesson: a real, externally-maintained skill set that a *provider* ships so AI coding assistants implement that provider's product correctly. This project uses it specifically for the admin-auth piece (Epic E) so every team gets hands-on exposure to consuming someone else's skill, not just writing their own.

**What it is:** Auth0 publishes two Claude Code-compatible skill packages — *Core Skills* (framework detection, migration guidance, MFA setup) and *SDK Skills* (framework-specific implementation for React, Express, FastAPI, Flask, and others). Once installed, a plain-language request like "Add Auth0 authentication to my FastAPI backend and protect the admin routes" is enough — the skill detects the stack and drives Claude Code through correct, current Auth0 integration code rather than Claude reasoning from (possibly stale) training data about Auth0's SDK.

**Install (pick one):**

```bash
# Skills CLI (works for any supported AI assistant)
npx skills add auth0/agent-skills

# Or, inside Claude Code:
# Settings > Plugins > search "Auth0" > install both
# "Auth0 Core Skills" and "Auth0 SDK Skills"
```

**How each team should use it (Week 4 / Phase 4):**

1. Install the skill package before starting Epic E, not mid-way through — it works best applied from a clean slate (per Auth0's own guidance).
2. Prompt naturally, e.g. *"Add Auth0 login to the admin panel in my React frontend and protect the `/admin/*` routes in my FastAPI backend."* Let the skill's framework detection pick the right SDK guide rather than over-specifying.
3. Still **review every generated line** — Auth0 explicitly calls this out as a best practice, and it's consistent with Section 7's program-wide rule that AI output is reviewed, not just accepted.
4. Manually configure the actual Auth0 tenant/application in the Auth0 Dashboard — the skill accelerates code, it does not create your tenant for you.
5. At the Week 4 milestone demo, the team should be able to speak to what the skill got right immediately versus what still needed a human correction — that's the case study, told live, not necessarily written down anywhere.

**Why this is the right teaching example here (and what it is *not*):** Auth0 Agent Skills is scoped narrowly to the admin-auth slice of the app (Epic E). It is not a statement that Auth0 is architecturally required for the *conversational* identity-verification flow in Epics B/C — that flow is intentionally *not* credential-based and has nothing to do with Auth0. Keep the two identity systems conceptually and structurally separate, as Section 6.1 and Epic E4 already require.

### 4.6 Chat session storage (Postgres JSONB)

Every chat session gets persisted as structured data, not scraped from log files. This is a deliberately small, low-ceremony piece of infrastructure: one table, one JSONB column for the variable-shaped conversation content, a few indexed columns for the things teams will actually want to query.

```text
ChatSession
  - id (uuid)
  - customer_id (uuid, nullable — null until/unless the session reaches Verified)
  - state (enum: "anonymous" | "collecting_identity" | "code_sent" |
           "awaiting_code" | "verified" | "escalated_to_human")
  - started_at (datetime)
  - ended_at (datetime, nullable)
  - transcript (jsonb)   -- array of {role, content, timestamp, tool_calls?} objects
```

`transcript` is where the actual back-and-forth lives — an array of message objects, structured however the team's backend naturally produces it (a list of `{role, content, timestamp}` is enough; including any `tool_calls` the model made on that turn is encouraged, since it's useful for debugging the gating logic later). Because it's all mock data (Section 4.4), there's no redaction requirement — the raw identity fields a user typed during verification can be stored as-is.

This table is intentionally simple to query directly (`SELECT * FROM chat_sessions WHERE state = 'escalated_to_human'`, etc.) — that queryability is the whole point of using JSONB over flat log files, and it's what makes the optional admin chat viewer (Section 8, Week 5 bonus track) realistic to build without a lot of parsing work.

> **Keep this in Postgres.** Don't introduce a second database engine (e.g. MongoDB) just to store JSON — Postgres's `JSONB` type already gives indexable, queryable JSON storage without adding a second piece of infrastructure for a 5-week project to operate and debug.

### 4.7 Docker & Docker Compose

Everyone on this program is on **macOS**, so the guidance below is Mac-specific rather than hedged across three platforms.

**Baseline (required):** the frontend, backend, and Postgres run as containers, brought up together with a single `docker-compose.yml`. A mentor or teammate should be able to clone the repo, run `docker-compose up`, and have the full stack (minus the local LLM — see below) reachable.

**Ollama stays on the host — and this isn't a workaround, it's the only sensible option on a Mac.** Docker Desktop on macOS cannot pass Apple's Metal GPU through to a container — there's no NVIDIA-style `--gpus` flag equivalent for Metal, full stop. Ollama running natively on the host gets full Metal acceleration via Apple Silicon's unified memory; Ollama running inside a Docker container on the same Mac would fall back to CPU-only inference, which is a real, noticeable slowdown for a model like `qwen3:8b`, not a minor inconvenience. Install Ollama directly on the host machine, and have the backend container reach it via `host.docker.internal:11434` — Docker Desktop for Mac resolves this automatically, no extra config needed.

**Bonus tier — full containerization (optional, harder mode, and genuinely slower — read before attempting):** the official `ollama/ollama` Docker image exists and will run on Mac, but **without Metal acceleration** — it's CPU-only inside the container, so responses will be noticeably slower than the host-native setup above. This tier is a container-purity flex, not a performance upgrade — do it to prove you can wire it up, not because it'll feel better to use. It sits alongside the other Week 5 bonus items in Section 8 (Twilio SMS, llama.cpp, the admin chat viewer). A team that ships the baseline (3 services in Docker, Ollama on host) has done everything required.

```yaml
# docker-compose.yml — baseline shape (teams should generate the real
# version via Claude Code against their actual service code/ports)
services:
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/secureship
      - OLLAMA_HOST=http://host.docker.internal:11434
    depends_on: [postgres]

  postgres:
    image: postgres:16
    environment:
      - POSTGRES_DB=secureship
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

volumes:
  pgdata:
```

### 4.8 API typing & state management (no hand-written types, no hand-written fetch calls)

A recurring time-sink in projects like this is hand-writing TypeScript types that duplicate the backend's Pydantic models, then hand-writing fetch calls to use them — both of which drift out of sync the moment the backend changes, and neither of which is interesting work for an engineer to spend Claude Code tokens regenerating by hand every time a field changes. This section removes that entirely.

**The mechanism, in one sentence:** FastAPI already generates a full OpenAPI (Swagger) schema for free from your Pydantic models — point a codegen tool at that schema and the frontend's types *and* API client code generate themselves.

```mermaid
flowchart LR
    Pydantic["Pydantic models<br/>(FastAPI request/response schemas,<br/>+ dummy-endpoint models for WS — see below)"]
    OpenAPI["/openapi.json<br/>(auto-generated by FastAPI, free)"]
    Orval["Orval<br/>(npx orval)"]
    Hooks["Generated React Query hooks<br/>(HTTP endpoints only)"]
    Types["Generated TS types<br/>(everything, incl. WS envelope types)"]
    RQ["Used directly in components<br/>(HTTP path — Section 6.3)"]
    WSCode["Manually-written WS handler code,<br/>imports these types<br/>(WS path — Section 6.3b)"]

    Pydantic --> OpenAPI
    OpenAPI --> Orval
    Orval --> Hooks
    Orval --> Types
    Hooks --> RQ
    Types --> WSCode

    style Pydantic fill:#e6f2ff,stroke:#3380cc,stroke-width:2px
    style OpenAPI fill:#fff4e6,stroke:#cc8800,stroke-width:2px
```

This is a **dev-time / build-time pipeline**, not something that happens at runtime — it doesn't appear in the runtime architecture diagram (Section 6.1) because nothing here runs while the app is actually serving a user; it runs when a developer (or the bonus skill in Section 4.8's last paragraph) decides the backend schema has changed and regenerates.

**Recommended tool: [Orval](https://orval.dev/)** — it reads an OpenAPI schema and generates fully-typed client code, and critically, it can target **React Query** or **RTK Query** as its output (it's a generator, not a competing library — you still end up using React Query/RTK Query as normal, you just stop hand-writing the hooks and types that feed them).

- **Default target: React Query.** Simpler setup (no Redux store prerequisite), slightly less generated boilerplate, the more common pairing with Orval in 2026.
- **RTK Query is a one-line config swap** (`client: 'react-query'` → `client: 'rtk-query'` in `orval.config.ts`) for teams already using Redux elsewhere and who'd rather keep one state-management paradigm throughout the app.

**This is where the Section 6.3 / 6.3b transport choice has a real, concrete consequence — not just an abstract one:**

| If your team picked... | What you get from Orval | What you still hand-write |
|---|---|---|
| **HTTP only (Section 6.3)** | Every payload is already a real REST request/response. Orval generates fully-typed React Query hooks (`useSendMessage()`, `useVerifyCode()`, `useLookupShipments()`, etc.) directly from your real FastAPI endpoints. | Nothing. No fetch calls, no request/response types, no hooks. |
| **HTTP + WebSocket (Section 6.3b)** | The WS message envelope (`{type: "typing"}`, `{type: "tool_call", ...}`, `{type: "verified", ...}`, etc.) has no real backing REST endpoint, so it doesn't naturally appear in the OpenAPI schema. **The workaround:** define those message shapes as ordinary Pydantic models and expose them via plain, deliberately-unused dummy REST endpoints (e.g. `POST /_types/chat-events`, never actually called by the frontend) purely so they show up in the schema. Orval/`openapi-typescript` then exports plain TypeScript types for them (no hook is generated, since there's no real query/mutation to wire up — a dummy endpoint with no caller doesn't need one). | The actual `socket.on(...)` / WebSocket message-handling code, importing and applying the generated types manually — there's no codegen tool that wires a type directly to a raw socket listener the way it does for REST. |

**On the dummy-endpoint approach specifically:** this is a deliberate choice over "magic" alternatives (e.g. directly injecting extra schemas into FastAPI's `app.openapi()` without a backing route). A plain, visible, never-called REST endpoint is easy for a mixed-experience team to find, read, and debug — there's no hidden schema-injection step to explain. The endpoint genuinely does nothing at runtime; its only job is to exist so its Pydantic models get exported.

**State management, split by transport (this follows directly from the table above):**

- **HTTP path:** React Query (via Orval) is the state management layer, full stop. It already handles caching, loading/error states, retries, and invalidation — there's no need for a separate global store for chat state.
- **WebSocket path:** a lightweight global store — **Zustand** is the recommended pick (least boilerplate, no provider-wrapping ceremony, a WS message handler just calls `set()` on the store) — holds the live chat/session state, since it's fundamentally event-driven/pushed rather than request/response. Trying to force WS-pushed messages through a React Query cache fights the tool's actual design; don't do that. React Query can still be used *alongside* Zustand in the WS path for anything that genuinely is a one-off REST call (e.g. the admin panel's CRUD operations, which stay HTTP regardless of which transport the chat itself uses).

**Regenerating types when the backend changes:**

Default workflow: rerun the Orval generation step manually (`npx orval` or the team's equivalent npm script) whenever the backend's Pydantic models/routes change, and commit the regenerated output. This is a two-minute manual step, not automated by default.

**Bonus points — automate the suggestion (not the action):** writing a Claude Code Agent Skill (using the "Introduction to Agent Skills" course format — Section 2.2) that *notices* when backend route/schema files have just changed and *suggests* regenerating the frontend types/client is a strong, genuinely useful skill to build, and ties directly into this program's broader "AI assists, team reviews" principle (Section 7.2). The skill should be **semi-automatic by design**: it suggests and waits for a yes, it does not regenerate and overwrite frontend files unprompted. Given engineers are still building the habit of reviewing AI output before accepting it, removing that confirmation step would undercut exactly the judgment the program is trying to build.

---

[← Program Structure at a Glance](03-program-structure.md)  ·  [User Stories →](05-user-stories.md)  ·  [Index](../SecureShip-5Week-Program.md)

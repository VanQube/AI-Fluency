# 12. Glossary

[Index](../SecureShip-5Week-Program.md) · [Progress Tracker](../PROGRESS.md)

Acronyms and shorthand used throughout this document, in case any of these are new — there's no expectation that every engineer already knows all of these on day one.

| Term | Meaning |
|---|---|
| **AI** | Artificial Intelligence — used throughout to mean Claude / the local LLM, depending on context |
| **API** | Application Programming Interface — the contract a backend exposes for a frontend (or another program) to call |
| **CCA** | Claude Certified Architect — Anthropic's partner-facing technical certification (Section 2.2) |
| **CRUD** | Create, Read, Update, Delete — the four basic data operations an admin panel needs (Epic E) |
| **ERD** | Entity-Relationship Diagram — a diagram showing how data tables relate to each other (Section 6.4) |
| **FK** | Foreign Key — a database column that references another table's primary key (e.g. `Shipment.customer_id`) |
| **GPU / Metal** | Graphics Processing Unit / Apple's GPU acceleration framework — on Apple Silicon Macs there's no separate "VRAM," it's unified memory shared between CPU and GPU; Ollama uses Metal automatically when run natively, which is central to Section 4.7's Docker/Ollama discussion |
| **HTTP** | HyperText Transfer Protocol — the standard request/response protocol the web runs on; one of the two chat transport options (Section 6.3) |
| **IdP** | Identity Provider — the external service that handles login/authentication (Auth0, in this program — Section 4.5) |
| **JSON** | JavaScript Object Notation — a lightweight, human-readable data format used for almost everything in this program (API payloads, stored transcripts, etc.) |
| **JSONB** | The binary, indexable, queryable JSON column type in Postgres (Section 4.6) — not a separate database, just a column type |
| **JWT** | JSON Web Token — a signed token format commonly used to represent "this user is authenticated" (used by Auth0, Section 6.1) |
| **LLM** | Large Language Model — the AI model doing the actual chatting (Claude for building, the local Ollama model for the app's runtime — Section 1.3) |
| **MCP** | Model Context Protocol — Anthropic's protocol for connecting AI assistants to external tools/data sources (covered in Section 2) |
| **MFA** | Multi-Factor Authentication — verifying identity with more than one factor (this program's 2FA/Epic C is a specific case of this) |
| **ORM** | Object-Relational Mapper — a library that lets backend code work with database rows as regular code objects instead of writing raw SQL |
| **PDF** | Portable Document Format — the file format mentioned for the CCA Foundations reference material (Section 2.2) |
| **PII** | Personally Identifiable Information — any data that can identify a specific person (name, address, phone number, etc.); see Section 4.2/4.3 for how this program handles it (all mocked, never real) |
| **PK** | Primary Key — the unique identifier column for a database table row |
| **REST** | REpresentational State Transfer — the conventional style of designing HTTP APIs (most of this program's HTTP endpoints follow it) |
| **RTK (Query)** | Redux Toolkit Query — a data-fetching/caching library built on Redux; one of two valid Orval output targets (Section 4.8) |
| **RQ** | React Query (also called TanStack Query) — the default recommended data-fetching/caching library for the HTTP chat path (Section 4.8) |
| **SDK** | Software Development Kit — a provider's official library for integrating with their service (e.g. the Auth0 SDK, Section 4.5) |
| **SMS** | Short Message Service — plain text messaging; the basis for this program's (mocked) 2FA code delivery (Epic C) |
| **2FA** | Two-Factor Authentication — verifying identity with a second factor beyond just a password/credential; in this program, the 6-digit code flow (Epic C) |
| **UI / UX** | User Interface / User Experience — what the user sees and clicks, and how the overall experience feels to use |
| **WS** | WebSocket — a persistent, two-way connection protocol; the other of the two chat transport options, alongside HTTP (Section 6.3b) |

---

[← Open Items for Mentors Before Week 1 Starts](11-mentor-setup.md)  ·  [Index](../SecureShip-5Week-Program.md)

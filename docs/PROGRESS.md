# SecureShip — Build Progress Tracker

Live tracking of the actual build against the plan in [08-weekly-plan.md](secureship/08-weekly-plan.md). Checklist items and phase wording are carried over from that file — update this one as work lands; treat `secureship/08-weekly-plan.md` as the static definition of done, not something to check off directly.

> Full spec index: [SecureShip-5Week-Program.md](SecureShip-5Week-Program.md)

## Status at a glance

| Phase | Week | Focus | Status | Milestone demo |
|---|---|---|---|---|
| 1 | Week 1 | Kickoff, skeleton, local LLM wired in | ✅ Done | ☐ Not yet presented |
| 2 | Week 2 | Identity collection + 2FA gate | ✅ Done (pending your browser click-through + review) | ☐ Not yet presented |
| 3 | Week 3 | Tool-calling for shipment data | 🔜 Up next | ☐ |
| 4 | Week 4 | Admin panel (Auth0) | ⬜ Not started | ☐ |
| 5 | Week 5 | Hardening, docs, final demo | ⬜ Not started | ☐ |

---

## Week 1 — Phase 1: Kickoff, Skeleton & Local LLM Wired In ✅

- [x] Repo created, README stub, `/docs` folder structure in place
- [x] `docker-compose.yml` brings up frontend, backend, and Postgres containers — Ollama installed on the host, not containerized
- [x] Backend skeleton running with a health-check endpoint
- [x] Frontend skeleton running, renders a chat window UI
- [x] Mock data generation script written and run (`scripts/seed_data.py`)
- [x] Mermaid diagrams from Section 6 copied into team repo (`docs/diagrams/`)
- [x] Ollama installed, model pulled (`qwen3:8b`)
- [x] Backend calls Ollama's API and returns model responses through the chat endpoint
- [x] Orval configured and pointed at the backend's `/openapi.json`; generated hooks in `frontend/src/api/generated`
- [x] Every turn persisted to the `ChatSession.transcript` JSONB column
- [x] Frontend chat window fully wired (send/receive, message history rendered)
- [x] Basic system prompt written (`docs/system-prompt.md`, `SYSTEM_PERSONA` in `backend/routes/chat.py`)

**Demo (Milestone 1):** not yet presented — schedule the walkthrough (repo/Docker setup, Claude Code scaffolding narration, live model response, including one un-gated question to show there's no gate yet).

---

## Week 2 — Phase 2: Identity Collection + 2FA Gate ✅

- [x] Conversational identity collection (name, address, phone) implemented — `backend/gating.py` + `backend/llm/extraction.py` (structured-output extraction, not native tool-calling — see design note below)
- [x] Identity matching against the Customer table, with neutral failure messaging (Epic B) — `backend/tools/verify_identity.py`, `identity_rejected` state
- [x] Mock 6-digit code generation tied to session, with expiry and attempt limits — `backend/tools/send_verification_code.py` (10 min TTL), `check_verification_code.py` (3 attempts)
- [x] On-demand modal triggers correctly when the conversation reaches that state — `frontend/src/components/ChatWindow/CodeModal.js`, shown only when `state === "awaiting_code"`
- [x] Code verification endpoint implemented; session transitions to "Verified" — `POST /verify-code`, `backend/routes/verify.py`
- [x] Human escalation theater implemented (Epic G) — triggers from both Anonymous and Verified states, confirmed not to leak shipment data (Epic G4) — keyword heuristic in `backend/tools/intent.py`, staged reveal in `ChatWindow.js`

**Design call (backend-orchestrated, not native tool-calling):** the state machine is driven deterministically by `backend/gating.py`, not by the model deciding when to call a tool — the LLM only phrases replies and extracts fields via Ollama's `format: "json"` structured output. Real Ollama tool-calling is introduced in Week 3 for `lookup_shipments`.

**Verified so far (API-level, via curl against the live containers + Ollama):**
- Anonymous → CollectingIdentity → matched → CodeSent/AwaitingCode → Verified, with `customer_id` correctly promoted from `pending_customer_id` and `verification_code`/`code_attempts` cleared afterward
- Non-matching identity → neutral rejection wording (no "no record found" leak) → gives up → back to Anonymous
- Wrong code → decrementing attempts message; 3rd wrong attempt → locked → `code_expired` → next message restarts the gate
- "talk to a human" recognized mid-rejection, personalized greeting using the first name already collected, and confirmed the escalated (never-verified) session still doesn't get shipment data
- Backend console logs show only the mock SMS code line (`session=... code=...`) — no identity fields anywhere in logs (Section 4.3)

**Follow-up (perceived latency):** chat replies now stream token-by-token over SSE instead of blocking for the full response — `POST /chat/stream` (`backend/routes/chat.py`), `ollama_client.chat_stream()`, `gating.handle_turn_stream()`, hand-written fetch consumer in `frontend/src/api/chatStream.js` (not Orval-generated — same carve-out Section 4.8 describes for the WebSocket path, since SSE has no normal JSON response body). The blocking `/chat` and the non-streaming `handle_turn()` wrapper are kept for curl/testing convenience. Deterministic templated replies (code-sent messages, rejections, the escalation script) still arrive as a single chunk — only real LLM-generated replies stream incrementally.

**Not yet done — needs a human:**
- [ ] Live browser click-through (no headless-browser tool was available in this environment to do it automatically) — try the golden path, a wrong code, an expired/locked code, a non-matching identity, and the escalation phrase in the actual UI
- [ ] Code review of `backend/gating.py` and the `tools/` package (Section 7.2 — this is the security-critical part of the app)
- [ ] Sign off on the identity-matching strictness (exact match on all 4 normalized fields) and retry/expiry defaults (3 attempts / 10 min), or ask for them to be tuned

**Demo (Milestone 2):** full gate walkthrough including a deliberate failure case (wrong code or non-matching identity), plus triggering the escalation sequence at least once.

---

## Week 3 — Phase 3: Tool-Calling for Shipment Data ⬜

- [ ] Tool/function definitions implemented (`lookup_shipments`, etc.) and exposed to the local model
- [ ] Backend tool layer always scopes lookups to `session.customer_id` — never a model- or user-supplied ID (Epic F)
- [ ] Verified users can ask natural-language questions about their shipments and get accurate answers
- [ ] Explicit test: attempt to get another customer's data through prompt manipulation, documented as failing

**Demo (Milestone 3):** verified session answering real shipment questions, then a deliberate prompt-injection attempt shown holding (terminal logs visible if possible).

---

## Week 4 — Phase 4: Admin Panel ⬜

- [ ] Auth0 integrated for admin login only, built using the Auth0 Agent Skills
- [ ] Admin panel: create/edit/delete Customer, Shipment, and Package records
- [ ] Backend admin routes protected by middleware validating the IdP token (Epic E3)
- [ ] Confirmed: no path lets an admin "become" a verified chat session, and no path lets a chat session reach admin routes

**Demo (Milestone 4):** admin login, a CRUD operation, and the chat reflecting that change live.

---

## Week 5 — Phase 5: Hardening, Docs, Final Demo ⬜

- [ ] Section 6 diagrams regenerated against the actual implementation
- [ ] Team README finalized
- [ ] Basic edge-case pass: expired codes, malformed input, empty states, mid-verification topic changes
- [ ] Optional stretch goals (pick any): real Twilio SMS, llama.cpp, fully containerized Ollama, admin chat session viewer, codegen-suggestion Agent Skill

**Final Demo + Retro (Friday, Week 5):** full end-to-end walkthrough (anonymous → identity collection → 2FA → verified shipment chat → admin edit reflected live) plus retro.

---

*Sources for Week 1's status: `README.md` (Implemented/Not yet implemented section) and a scan of `backend/`, `frontend/src/`, `docs/diagrams/`, and `scripts/seed_data.py`.*

# 3. Program Structure at a Glance

[Index](../SecureShip-5Week-Program.md) · [Progress Tracker](../PROGRESS.md)

| Phase | Build Week | Focus | Milestone Review |
|---|---|---|---|
| Phase 1 | Week 1 | Project kickoff, repo/Docker setup, skeleton frontend + backend, local LLM wired in (no gating yet) | Milestone 1 demo — Monday, Week 2 |
| Phase 2 | Week 2 | Identity collection + SMS 2FA gate | Milestone 2 demo — Monday, Week 3 |
| Phase 3 | Week 3 | Tool-calling: shipment lookups behind the gate | Milestone 3 demo — Monday, Week 4 |
| Phase 4 | Week 4 | Admin panel (Auth0) + package management | Milestone 4 demo — Monday, Week 5 |
| Phase 5 | Week 5 | Hardening, docs, diagrams, final demo | Final Demo + Retro — Friday, Week 5 |

Each week's milestone review happens on the **Monday of the following week** — Monday morning reviews what was built the prior week, then that week's build starts. The one exception is the Final Demo, which happens on the **Friday of Week 5** itself, since there's no following Monday inside the program. Full timing details are in Section 8's demo format note.

Teams are **1–2 engineers (2 max)**. Each team ships one SecureShip instance. The Section 2 learning track runs the whole time, in parallel — it isn't a phase of its own.

### 3.1 Team composition

At 1–2 people per team, skill coverage across the stack won't always be even, and that's fine — it's expected, and it's actually a good showcase of the program's core theme (AI-assisted delivery covering skill gaps), not a problem to route around:

- **Solo, full-stack:** one engineer covers everything. Straightforward — no coordination overhead, but the full 5-week scope on one person's plate.
- **Pair, split by layer (one frontend, one backend):** the natural split — one engineer owns the FastAPI backend, tool layer, and Ollama integration; the other owns the React frontend, chat UI, and admin panel. Section 4.8's Orval-generated types are what make this split painless — the backend engineer's API changes show up as ready-to-use frontend types/hooks without the two engineers hand-negotiating a shared contract.
- **Pair, both full-stack:** split by feature/Epic instead of by layer (e.g., one owns Epics A–C, the other owns D–F) — whichever division fits how the team likes to work.
- **Solo, single-specialization (e.g., backend-only, no frontend background):** this is explicitly acceptable, not a gap to apologize for. Lean on Claude Code to cover the frontend side — that's the program's actual point. A backend specialist directing Claude Code to build a working React chat UI is a stronger demonstration of AI-assisted delivery than a full-stack engineer who didn't need the help.

Whatever the split, Section 8's weekly demo format (below) is designed to work whether a given week's progress is backend-only, frontend-only, or fully connected — see the demo format note at the top of Section 8.

---

[← Prerequisite & Parallel Learning](02-learning-track.md)  ·  [The Product: Full Requirements →](04-requirements.md)  ·  [Index](../SecureShip-5Week-Program.md)

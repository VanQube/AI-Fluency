# AI-Assisted Upskilling Program: "SecureShip" — AI-Gated Shipment Support Chat

**A 5-week, full-time build program for bench engineers, with Claude Code foundations as a parallel, self-paced learning track (no dedicated calendar time).**

> New to some of the acronyms in this doc (PII, JWT, JSONB, etc.)? [12. Glossary](secureship/12-glossary.md) defines all of them in one place.

This program spec was split into one file per section (kept under [`docs/secureship/`](secureship/)) so it's easier to navigate and link into from code/diagrams. Section numbers are unchanged from the original — a comment referencing "Section 4.4" or "Epic F" still means the same thing, just now living in [04-requirements.md](secureship/04-requirements.md). For where the actual build stands right now, see the live tracker: **[docs/PROGRESS.md](PROGRESS.md)**.

## Sections

| # | Section | What's in it |
|---|---|---|
| 1 | [Program Overview](secureship/01-overview.md) | What's being built, why, who it's for |
| 2 | [Prerequisite & Parallel Learning](secureship/02-learning-track.md) | Claude Code Skilljar courses, self-paced |
| 3 | [Program Structure at a Glance](secureship/03-program-structure.md) | Phases, milestones, team composition |
| 4 | [The Product: Full Requirements](secureship/04-requirements.md) | Scope, non-functional requirements, mock data, Auth0 skills, chat storage, Docker, API typing |
| 5 | [User Stories](secureship/05-user-stories.md) | Epics A–G |
| 6 | [Architecture (Mermaid Diagrams)](secureship/06-architecture.md) | System architecture, state machine, sequence diagrams, ERD, deployment topology, repo skeleton |
| 7 | [AI-Assisted Workflow Requirements](secureship/07-ai-workflow.md) | What AI generates, what it doesn't replace, the Caveman plugin |
| 8 | [Weekly Plan (Weeks 1–5) and Milestones](secureship/08-weekly-plan.md) | Definition of done per week — for the live version, see [PROGRESS.md](PROGRESS.md) |
| 9 | [Local Model Setup Reference](secureship/09-model-setup.md) | Ollama, `qwen3:8b`, why not llama.cpp |
| 10 | [Feedback, Not Grading](secureship/10-feedback.md) | How mentors evaluate demos |
| 11 | [Open Items for Mentors Before Week 1 Starts](secureship/11-mentor-setup.md) | Pre-kickoff logistics checklist |
| 12 | [Glossary](secureship/12-glossary.md) | Acronyms used throughout |

## Related docs

- **[PROGRESS.md](PROGRESS.md)** — live build progress tracker, checked off as work lands (start here to see current status)
- [diagrams/](diagrams/) — each team's own regenerated Section 6 diagrams, matched against their actual implementation (Section 7.1)
- [system-prompt.md](system-prompt.md) — the actual chat persona/system prompt driving the local model
- [certificates/](certificates/) — Skilljar completion certificates (Section 2.3)

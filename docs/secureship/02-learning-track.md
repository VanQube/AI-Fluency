# 2. Prerequisite & Parallel Learning

[Index](../SecureShip-5Week-Program.md) · [Progress Tracker](../PROGRESS.md)

This is **not scheduled time.** Engineers work through it on their own initiative, alongside the 5 build weeks, whenever it fits — this section exists so everyone knows what to work through and why it matters for this specific project.

> Anthropic's course catalog changes fairly often. Before kickoff, a mentor should check **https://anthropic.skilljar.com/** directly and confirm course names/links below are still current, and swap in anything newer that fits.

### 2.1 Core Claude Code fluency (work through this early — it pays off fastest in Week 1)

| Order | Course | Why |
|---|---|---|
| 1 | **Claude Code 101** | Installation across terminal/IDE, the Explore→Plan→Code→Commit loop, approval modes, Plan Mode, CLAUDE.md basics |
| 2 | **Claude Code in Action** | Tool-use system, context management, MCP servers, GitHub workflows |
| 3 | **Introduction to Subagents** | Delegating sub-tasks, keeping main context clean — directly useful once the project has frontend + backend + model-prompting work happening in parallel |

### 2.2 Depth — the pieces this specific project needs

| Order | Course | Why |
|---|---|---|
| 4 | **Introduction to Agent Skills** | Writing a `SKILL.md` — engineers will use this pattern at least twice in this project: packaging "how we prompt-engineer the gating logic" as a reusable skill, and (optional bonus, Section 4.8) a skill that suggests regenerating frontend API types/hooks whenever the backend schema changes |
| 5 | **Building with the Claude API** (relevant modules only — function calling / tool use sections) | Directly transfers to wiring tool calls into the *local* Ollama model later; the concepts (tool schemas, multi-turn tool loops) are the same even though the runtime differs |

> **A note on Claude Certified Architect (CCA) Foundations:** this certification exists and covers material squarely relevant to this program (Agentic Architecture & Orchestration, Tool Design & MCP Integration), but it is currently a **partner-only** credential — Anthropic does not make it directly available to engineers through this program. It's worth mentioning that the certification exists and what it covers, purely as context for where this skillset can lead professionally. As a good-to-have (not required, not a course substitute), mentors can supply the CCA Foundations reference PDF as background reading.

### 2.3 Suggested self-tracking (not a gate, not required, no check-in scheduled around it)

- [ ] Skilljar certificates for the courses in Section 2.1, screenshotted into the team's repo under `/docs/certificates/`, whenever they get done
- [ ] If it's useful to the team, a quick informal chat with a mentor about "what did Claude Code make easy, what did it get wrong, and how did you catch it" — worth having at some point in the first couple of weeks, but not a scheduled milestone

---

[← Program Overview](01-overview.md)  ·  [Program Structure at a Glance →](03-program-structure.md)  ·  [Index](../SecureShip-5Week-Program.md)

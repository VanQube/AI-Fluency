# 7. AI-Assisted Workflow Requirements

[Index](../SecureShip-5Week-Program.md) · [Progress Tracker](../PROGRESS.md)

This is not a "use Claude if you want to" project — using Claude Code throughout is a core expectation, and how engineers use it matters as much as what they ship. There's no separate logging artifact for this: mentors have direct visibility into each team's actual Claude Code session history, so how a team prompted and what they kept/changed is something mentors can review for themselves rather than something engineers need to maintain or curate.

### 7.1 "AI generates literally everything" — what that actually means here

- **Code**: scaffolding, boilerplate, even first-draft business logic — Claude Code first, hand-edit second.
- **Mock data**: generation scripts and the data itself, against the schema in Section 4.4.
- **Architecture diagrams**: teams regenerate Section 6's diagrams against their real implementation using Claude (in Mermaid), then **must manually review and correct them** — a diagram that doesn't match the actual code is a documentation bug, and worth calling out as one in the weekly demo.
- **README**: teams use Claude Code to draft their own project README from this program README + their actual code, then edit it for accuracy. An AI-drafted README that asserts something the app doesn't actually do is treated as a defect, not a style issue.

### 7.2 What AI does *not* replace

- Understanding *why* the identity gate works the way it does (Section 6.2/6.3) — this should be explainable by any team member at any milestone demo, unprompted.
- Code review between teammates before merging — Claude drafting code doesn't remove the second-human-eyes step.
- The judgment calls in Section 4.2/4.3 (scope boundaries, security enforcement points) — these are architecture decisions, and AI assists, but the team owns them.

### 7.3 Stretching session budget: the Caveman plugin

Five intense, full-time build weeks of near-daily Claude Code use means teams will regularly feel the pinch of the 5-hour session window, especially mid-sprint during Phases 2–3 when the gating logic invites a lot of back-and-forth iteration. **Caveman** (`github.com/JuliusBrussee/caveman`) is a Claude Code skill/plugin that compresses Claude's *output* tokens — terser responses, same technical content — which in practice means a session's token budget stretches further before the team hits a limit and has to wait out the reset window.

This is a **session-economics tool, not an application component.** It has nothing to do with SecureShip's runtime, its architecture, or anything in Section 6 — it only affects how Claude Code talks to the *engineer* during development. Don't reference it in the app's own README or architecture docs; it belongs in the team's internal tooling notes, if anywhere.

**Recommended use:**

```bash
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash
```

- Trigger per-session with `/caveman` (or let it auto-activate in Claude Code, depending on install mode), and drop back to `normal mode` whenever a task genuinely needs Claude to reason out loud at length — e.g., walking through *why* the gating state machine is structured the way it is (Section 6.2) is worth full verbosity; routine scaffolding and boilerplate generation is exactly where the compression pays off.
- `/caveman-compress` can shrink a bloated `CLAUDE.md` or project-notes file so every session starts with a smaller context footprint, which compounds the session-length benefit over the 5 weeks.
- This is optional, team's choice — it doesn't appear in Section 4 (Requirements) because it's a development-time efficiency tool, not a product requirement. If it actually helped a team's session budget, that's a fine thing to mention in passing at a milestone demo — but it's not tracked or required.

---

[← Architecture (Mermaid Diagrams)](06-architecture.md)  ·  [Weekly Plan (Weeks 1-5) and Milestones →](08-weekly-plan.md)  ·  [Index](../SecureShip-5Week-Program.md)

# 1. Program Overview

[Index](../SecureShip-5Week-Program.md) · [Progress Tracker](../PROGRESS.md)

### 1.1 What engineers are building

**SecureShip** is a parcel/shipment customer-support application built around a single core feature: a chat window where customers talk to a *locally-run, open-source LLM* to check on their shipments — but only after the bot has verified who they are.

There is no traditional user signup or login. Customers are identified entirely through the conversation: the bot collects their name, address, and phone number, sends a 2FA code, and only after that code is confirmed does it unlock access to shipment data tied to that identity. The only persistent login in the whole system is a single **admin** account, used to manage the package/shipment data the bot draws from.

This is, deliberately, a **conversational identity-gating and tool-use problem**, not a CRUD app with a chatbot bolted on. The chat *is* the product.

> **A quick note on transport:** the chat can be built over plain HTTP request/response or over WebSockets — both are fully acceptable, and neither is preferred over the other. WebSockets give a noticeably better real-time chat experience (typing indicators, server-pushed updates); HTTP is simpler to reason about for teams newer to async networking. Pick one explicitly rather than drifting into it by accident (more on this in Section 6).

### 1.2 Why this project

- It forces real engagement with **prompt engineering and guardrails** (the parallel Claude Code learning track, Section 2, stops being theoretical the moment a model leaks shipment data to an unverified user).
- It requires **tool calling / function calling** from a local model — a skill directly transferable to agentic and MCP-based engineering.
- It has a natural **phased structure** (frontend shell → chat plumbing → identity gate → tool-gated data access → admin panel → polish) that maps cleanly to 5 weekly milestones.
- The "stack-irrelevant" framing keeps the focus on architecture and correctness, not framework trivia — while the suggested Python/React stack keeps support burden low for mentors.

### 1.3 Explicit program goals

1. Get every engineer comfortable **directing AI tools (Claude Code) to build real software**, not just autocompleting lines.
2. Get every engineer hands-on with a **local open-source LLM** (Ollama) — pulling it, prompting it, constraining it, and wiring it into a real app via tool calls.
3. Practice **reading and correcting AI output** — including AI-generated architecture diagrams and documentation, not just code.
4. Practice **team delivery** in small groups with weekly milestone accountability.

### 1.4 Who this is for and how it's scheduled

This program is designed for **bench engineers** — full-time available, no competing day-job workload — which is what makes a tight 5-week build realistic. The Claude Code foundational courses (Section 2) run **in parallel, on your own initiative, with no calendar time allocated for them** — worked through across the 5 weeks, at whatever pace fits around your build work.

---

[Prerequisite & Parallel Learning →](02-learning-track.md)  ·  [Index](../SecureShip-5Week-Program.md)

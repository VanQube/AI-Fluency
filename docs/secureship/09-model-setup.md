# 9. Local Model Setup Reference

[Index](../SecureShip-5Week-Program.md) · [Progress Tracker](../PROGRESS.md)

### 9.1 Recommended model

**Primary: `qwen3:8b`** — chosen for native, reliable tool-calling at a size that runs comfortably on Apple Silicon's unified memory via Metal acceleration (Ollama uses Metal automatically on M1-and-later Macs — no separate GPU driver setup needed). This project lives or dies on the model reliably emitting correctly-structured tool calls for `verify_identity` / `lookup_shipments`, which is exactly what smaller general-purpose chat models (e.g. plain Llama 3.2 3B) are weakest at.

**Fallback: `llama3.2:3b`** — for engineers on lower-memory MacBook configurations (e.g. base 8GB M1/M2 Air). Tool-calling reliability is noticeably weaker at this size; teams using it should expect to do more manual parsing/validation of model output rather than trusting structured tool-call output directly, and should document that tradeoff in their README.

```bash
# Install Ollama for macOS — https://ollama.com/download/mac

# Pull the primary model
ollama pull qwen3:8b

# Fallback for constrained hardware
ollama pull llama3.2:3b

# Verify tool-calling support is present
ollama show qwen3:8b
# Capabilities should include: completion, tools
```

> Ollama uses Metal acceleration automatically on Apple Silicon when run natively — this is exactly the acceleration that's lost if Ollama gets moved into Docker (Section 4.7), which is the main reason the baseline keeps it on the host.

### 9.2 Why not llama.cpp for this program

llama.cpp gives more low-level control and is a legitimate optional stretch goal for teams that finish early and want to go deeper on inference internals, but it adds setup and binary-management overhead that competes with this program's actual teaching goal (Section 1.3): getting engineers fluent in directing AI tools and integrating a local model into a product, not building inference infrastructure from scratch. Ollama's one-command setup keeps that the focus.

---

[← Weekly Plan (Weeks 1-5) and Milestones](08-weekly-plan.md)  ·  [Feedback, Not Grading →](10-feedback.md)  ·  [Index](../SecureShip-5Week-Program.md)

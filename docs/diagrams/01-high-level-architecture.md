# High-level system architecture

Regenerated (2026-08-24, Week 5 Phase 1) against the real implementation.
Two structural corrections from the original target sketch: there is no
separate live Session Store — session state (including `collected_fields`,
the verification code, and attempt counters) lives directly in the
`chat_sessions` Postgres row and is read/written on every turn, no
in-memory/Redis layer. And the "Tool Layer" is only real native LLM
tool-calling for `lookup_shipments` (Epic F) — identity extraction and
intent routing are backend-orchestrated structured-output calls
(`llm/extraction.py`, `llm/intent_classifier.py`), not the model requesting
tools like `verify_identity`/`request_identity_info`.

```mermaid
flowchart TB
    subgraph Client["Browser / Frontend (React CRA + Tailwind)"]
        UI[Chat Window UI<br/>MessageList / MessageBubble / MessageInput]
        Modal["6-digit Code Modal<br/>(shown only when state===awaiting_code)"]
        AdminUI["Admin Panel UI<br/>Customer/Shipment/Package Managers"]
    end

    subgraph Backend["Backend API (FastAPI)"]
        ChatAPI["/chat, /chat/stream (SSE)<br/>routes/chat.py"]
        VerifyAPI["/verify-code<br/>routes/verify.py"]
        AdminAPI["/admin/* CRUD<br/>routes/admin.py"]
        Gating["gating.py — state machine\n(single source of truth,\nboth routes call into it)"]
        ChatDB[("chat_sessions table\n(Postgres — state IS the\nsession store, no Redis)")]
        Extraction["llm/extraction.py +\nllm/intent_classifier.py\n(structured-output, NOT\nnative tool-calling)"]
        LookupTool["tools/lookup_shipments.py\n(Epic F enforcement point —\nreal native Ollama tool-calling)"]
        AuthMW["admin_auth.py — Auth0FastAPI\nrequire_auth() JWT validation"]
    end

    subgraph LocalLLM["Local LLM Runtime (host, not containerized)"]
        Ollama["Ollama Server<br/>host.docker.internal:11434"]
        Model["qwen3:8b"]
    end

    subgraph DataLayer["Data Layer"]
        DB[("Postgres 16<br/>customers / shipments / packages")]
        SMSMock["Mock SMS<br/>(console/log only,\nsend_verification_code.py)"]
    end

    subgraph IdP["Identity Provider"]
        Auth0["Auth0 tenant<br/>(admin login ONLY,\nAuthorization Code + PKCE)"]
    end

    UI -->|"POST /chat/stream"| ChatAPI
    ChatAPI --> Gating
    Gating <-->|"read/write every turn"| ChatDB
    Gating -->|"identity fields, intent routing"| Extraction
    Extraction -->|"format: json"| Ollama
    Gating -->|"verified sessions only,\ncustomer_id from session,\nnever model-supplied"| LookupTool
    LookupTool --> DB
    Gating -->|"plain reply / tool round-trip"| Ollama
    Ollama --> Model
    Gating -->|"mocked 2FA"| SMSMock
    UI -->|"on awaiting_code"| Modal
    Modal -->|"POST /verify-code"| VerifyAPI
    VerifyAPI --> Gating

    AdminUI -->|"Universal Login redirect"| Auth0
    Auth0 -->|"JWT (access token)"| AdminUI
    AdminUI -->|"requests + Bearer JWT"| AdminAPI
    AdminAPI --> AuthMW
    AuthMW -->|"JWKS signature/issuer/audience check"| AdminAPI
    AdminAPI --> DB

    style LookupTool fill:#ffe6cc,stroke:#d79b00,stroke-width:2px
    style AuthMW fill:#ffe6cc,stroke:#d79b00,stroke-width:2px
```
